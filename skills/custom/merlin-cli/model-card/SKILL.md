---
name: model-card
description: 查询和管理 Seed/Titan 模型卡片 (Model Card)。支持查询模型列表 (model list)、基础元信息 (model get) 和完整运行时配置 (model get-config)。当用户需要了解模型信息、获取 model_evaluation_config 或查找模型时使用。
---

# 模型卡片 (Model Card)

查询和管理 Seed/Titan 平台上的模型卡片。通过 `merlin-cli` 提供以下常用命令：

| 命令 | 用途 |
|------|------|
| `merlin-cli model list` | 查询模型卡片列表，支持关键字、creator 过滤 |
| `merlin-cli model get` | 获取基础元信息（名称、SID、owner、发布时间） |
| `merlin-cli model get-config` | 获取完整运行时配置（评估配置、推理参数、API 端点、VIT 参数等） |

## 前置条件

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login` 重新登录。

---

## 1. 查询模型卡片列表 (model list)

支持通过模型名称关键字、所有者、创建者等进行过滤，获取模型卡片列表。

### CLI 命令

```bash
merlin-cli model list --json '{"model_name_keyword": "doubao", "creator": "chenyirong.33", "limit": 10, "offset": 0}'
```

### 参数说明

- `model_name_keyword`: 模型名称关键字过滤
- `creator`: 创建者过滤
- `limit`: 返回数量限制，默认10
- `offset`: 偏移量，默认0
- `skip_detail`: 是否只返回基本信息，避免接口过慢
- `review_passed`: 是否通过审核
- `like`: 是否收藏

---

## 2. 基础信息查询 (model get)

```bash
merlin-cli model get --json '{"model_card_name_or_sid": "<名称或SID>"}'
```

### 参数

| 参数 | 说明 | 必填 |
|------|------|------|
| `model_card_name_or_sid` | 模型名称或 SID | 是 |

### 返回字段

| 字段 | 说明 |
|------|------|
| `model_sid` | 模型 SID |
| `model_name` | 模型名称 |
| `model_id` | 模型 ID |
| `owners` | 模型 owner 列表 |
| `model_type` | 模型类型 |
| `release_company` | 发布公司 |
| `release_time` | 发布时间 |

### 示例

```bash
# 通过名称查询
merlin-cli model get --json '{"model_card_name_or_sid": "gpt-4"}'

# 通过 SID 查询
merlin-cli model get --json '{"model_card_name_or_sid": "qrpadva5216990840f"}'
```

---

## 3. 完整配置查询 (model get-config)

```bash
merlin-cli model get-config --json '{"model_sid": "<model_sid>"}'
```

支持直接传入 ModelCard 页面 URL，自动提取 SID：

```bash
merlin-cli model get-config --json '{"model_sid": "https://seed.bytedance.net/model/modelcard/<model_sid>?tab=config_info"}'
```

### 参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `model_sid` | 模型 SID 或 ModelCard 页面 URL | 是 | - |
| `field` | 只返回指定字段（如 `model_evaluation_config`） | 否 | 返回全部字段 |
| `parse_eval_config` | 自动解析 `model_evaluation_config` JSON 字符串为结构化对象 | 否 | `false` |

### 关键返回字段

| 字段 | 说明 |
|------|------|
| `model_sid` | 模型 SID |
| `name` | 模型全名（含 namespace，如 `external-api/Doubao-2.0-lite`） |
| `model_type` | 模型类型（`EXTERNAL_API` / `CHECKPOINT` 等） |
| `model_source` | 模型来源 |
| `model_modal` | 模型模态（`MultiModal` / `Text` 等） |
| `model_evaluation_config` | **核心字段** — 评估配置（API 端点、重试策略、VIT 参数等），默认为 JSON 字符串，加 `parse_eval_config: true` 可解析 |
| `model_extra_config` | 额外配置 |
| `hdfs_path` | HDFS 模型路径（Checkpoint 类型时有值） |
| `owners` | 模型 owner 列表 |
| `model_url` | ModelCard 页面链接（自动注入） |

### 示例

```bash
# 查询完整配置
merlin-cli model get-config --json '{"model_sid": "qrpadva5216990840f"}'

# 通过 URL 查询
merlin-cli model get-config --json '{"model_sid": "https://seed.bytedance.net/model/modelcard/qrpadva5216990840f?tab=config_info"}'

# 只查询评估配置（自动解析 JSON 字符串）
merlin-cli model get-config --json '{"model_sid": "qrpadva5216990840f", "field": "model_evaluation_config", "parse_eval_config": true}'

# 查询模型名称
merlin-cli model get-config --json '{"model_sid": "qrpadva5216990840f", "field": "name"}'
```

### 评估配置返回示例

使用 `field: "model_evaluation_config"` + `parse_eval_config: true`：

```json
{
  "external_api": {
    "provider": "general",
    "family": "doubao",
    "model": "ep-xxx",
    "api_key": "sk-a****",
    "url": "https://ark-cn-beijing.bytedance.net/api/v3/chat/completions",
    "base_url": "http://ark-cn-beijing.bytedance.net/api/v3",
    "http_timeout": 7200,
    "stream": true
  },
  "model": {
    "max_position_embeddings": "131072",
    "vit": { "img_size": 672, "max_pixels": 501760 }
  }
}
```

---

## 安全注意事项

返回结果中可能包含 `api_key` 等敏感信息。向用户展示时应脱敏处理：

- 只显示 `api_key` 的前 4 位 + `****`（如 `sk-a****`）
- 不要将完整 `api_key` 写入聊天记录、日志或共享文档

## 常见问题

| 现象 | 原因和处理 |
|------|-----------|
| `merlin-cli: command not found` | 先安装/升级 merlin-cli |
| 401 / 403 认证错误 | 运行 `merlin-cli login` 重新登录 |
| `cannot extract model_sid` | SID 格式不正确，请检查 URL 或直接传入纯 SID |
| `model_evaluation_config` 是字符串而非对象 | 加上 `"parse_eval_config": true` 参数自动解析 |
| 只想看基础信息不需要完整配置 | 用 `merlin-cli model get` 即可 |

## 关联技能

- `eval-run-exercise`：对模型运行评估
- `insight`：模型能力分析与对比
