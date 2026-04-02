---
name: eval-collection-create
description: 从一个或多个 Exercise Version 创建评估 Collection。当需要将多个已存在的 Exercise Version 组织为 Seed 平台的 Collection 时使用。触发词：创建 collection、create collection、评估集合、exercise 组装 collection、collection version、组合 exercise、合并 exercise、collection 创建。即使用户没有明确说"collection"，只要涉及将多个 Exercise 组合到一起进行统一评估管理，都应使用本 skill。
---

# 创建评估 Collection

通过 `merlin-cli collection create-from-exercises`（推荐一步完成），或底层的 `collection create` / `collection create-version` 命令，将一个或多个 Exercise Version 组织成 Seed 平台的评估 Collection。

## 前置条件

- `merlin-cli` 已安装并完成认证：

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果遇到 401/403 认证错误，运行 `merlin-cli login` 重新登录。

- 目标 Exercise 与 Exercise Version 已存在（可通过 `eval-exercise-create` skill 创建）
- 已知每个 Exercise 的评估指标名称（可通过 `eval-get-result` 的 `metrics` 字段获取）

## 推荐方式：一条命令创建

```bash
merlin-cli collection create-from-exercises --json '{
  "collection": {
    "name": "<collection_name>",
    "type": "TEST"
  },
  "version": {
    "name": "<version_name>"
  },
  "items": [
    {
      "exercise_sid": "<exercise_sid>",
      "exercise_version_sid": "<exercise_version_sid>",
      "metrics": ["<metric_name_1>", "<metric_name_2>"]
    }
  ]
}'
```

参数较多时也可以写到文件里：`merlin-cli collection create-from-exercises --from-file params.json`

该命令内部会自动执行三步：创建 Collection → 创建 Version → 写入 Exercise Items 并生成默认 tree。

### 参数说明

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `collection.name` | Collection 名称 | 是 | - |
| `collection.type` | Collection 类型 | 否 | `TEST` |
| `collection.owners` | 所有者列表，省略则自动获取当前用户 | 否 | 自动检测 |
| `version.name` | Collection Version 名称 | 是 | - |
| `items[].exercise_sid` | Exercise SID | 是 | - |
| `items[].exercise_version_sid` | Exercise Version SID | 是 | - |
| `items[].metrics` | 要加入 Collection 的指标名称列表 | 是 | - |
| `items[].exercise_name` | Exercise 展示名，用于生成更友好的 tree 节点名 | 否 | - |
| `items[].exercise_version_name` | Exercise Version 展示名 | 否 | - |

### metrics 字段说明

`metrics` 应填 exercise 评估输出的**指标名称**，即 `get-result` 返回的 `metric_name` 值。例如：

```json
"metrics": ["avg_accuracy", "invalid_rate"]
```

如果不确定 exercise 有哪些指标，先用 `eval-get-result` 查询一次该 exercise 的评估结果：

```bash
merlin-cli exercise get-result --json '{"exercise_version_sid": "<exercise_version_sid>", "latest": true}'
```

从返回的 `metrics` 列表中选取需要的 `metric_name`。

查看完整参数 schema：`merlin-cli collection create-from-exercises --schema`

## 底层命令（按需分步操作）

需要手动分步排错或编排时，可以使用底层命令：

### 第一步：创建 Collection

```bash
merlin-cli collection create --json '{
  "name": "<collection_name>",
  "type": "TEST"
}'
```

返回 `collection.sid`。

### 第二步：创建 Collection Version

```bash
merlin-cli collection create-version --json '{
  "collection_sid": "<collection_sid>",
  "name": "<version_name>"
}'
```

返回 `version.sid`。

查看底层命令 schema：

```bash
merlin-cli collection create --schema
merlin-cli collection create-version --schema
```

## 解读创建结果

`create-from-exercises` 返回完整的 Collection Version 信息，关键字段：

| 字段 | 说明 |
|------|------|
| `collection_sid` | Collection ID，用于拼接 URL 和后续操作 |
| `version.sid` | Collection Version ID |
| `version.name` | 版本名称 |
| `version.tree` | Exercise 的树形结构，用于 Seed 界面展示 |

向用户展示结果时，重点呈现：Collection URL 和包含的 Exercise 列表。两个 SID 都需要保存，后续管理 Collection 时会用到。

## 完整示例

将两个已有 Exercise Version 组合成一个测试 Collection：

```bash
merlin-cli collection create-from-exercises --json '{
  "collection": {
    "name": "<collection_name>",
    "type": "TEST"
  },
  "version": {
    "name": "v1"
  },
  "items": [
    {
      "exercise_sid": "<exercise_sid_1>",
      "exercise_version_sid": "<exercise_version_sid_1>",
      "exercise_name": "math",
      "exercise_version_name": "v1",
      "metrics": ["avg_accuracy", "invalid_rate"]
    },
    {
      "exercise_sid": "<exercise_sid_2>",
      "exercise_version_sid": "<exercise_version_sid_2>",
      "metrics": ["pass_at_1"]
    }
  ]
}'
# 返回: {"collection_sid": "<collection_sid>", "version": {"sid": "<version_sid>", ...}}

# 查看 Collection
# https://seed.bytedance.net/seed/evaluation/collections/<collection_sid>?collection_version_sid=<version_sid>
```

## Collection 地址

创建完成后，Collection 详情页地址为：

```
https://seed.bytedance.net/seed/evaluation/collections/<collection_sid>?collection_version_sid=<collection_version_sid>
```

## 常见问题

| 现象 | 原因和处理 |
|------|-----------|
| Exercise SID 或 Exercise Version SID 无效 | SID 拼写错误或 Exercise 不存在，用 `eval-query` skill 查询正确的 SID |
| metrics 名称错误导致 Collection 指标为空 | `metrics` 必须与 exercise 实际输出的 `metric_name` 完全匹配（区分大小写），通过 `eval-get-result` 确认可用的指标名 |
| Collection 名称重复 | 同名 Collection 已存在，换一个名称；或用 `eval-query` skill 查询已有 Collection |
| 401 / 403 认证错误 | 运行 `merlin-cli login` 重新登录 |
| `items` 为空 | 至少需要一个 Exercise Version，确保 `items` 数组非空 |

## 相关 Skills

- **前置**: `eval-exercise-create` — 创建 Exercise 和 Exercise Version
- **查询指标**: `eval-get-result` — 查看 exercise 有哪些 metrics 可用
- **查询**: `eval-query` — 查询已有 Collection 信息
