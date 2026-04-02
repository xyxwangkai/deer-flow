---
name: tools-merlin-cli
description: |
  本 skill 是 merlin, seed 相关需求的**兜底 skill**。当用户询问「merlin-cli 怎么用」「有哪些 merlin-cli 命令」「用命令行做 X」且没有更具体的 skill（如 job-launch、devbox-manage、eval-query、insight 等）覆盖时，应使用本 skill，通过 list-tools、--schema、分组命令查找并执行 merlin-cli。也适用于 MCP 不可用时的替代、调试、批量操作与 Agent 的 JSON 调用。
---

# Merlin CLI

## 摘要

Merlin CLI 是一个命令行工具，用于调用 Merlin MCP Server 提供的各种 API。工具按领域自动分组（job, devbox, eval, insight, ...），支持 JSON-first 输入模式。

**兜底角色**：本 skill 是 Merlin 相关 skills 的兜底。若用户需求未命中 job-launch、devbox-manage、eval-query、insight 等更具体的 skill，或用户明确问「merlin-cli 有什么命令」「怎么用命令行做 X」，应优先通过本 skill 查找并执行 merlin-cli（`list-tools`、`<group> --help`、`--schema`、`--json`）。

## 适用场景

- 用户问「merlin-cli 有哪些命令」「怎么用 merlin-cli 做 X」且无其它 skill 覆盖
- 当 MCP 工具不可用时，作为替代方案
- 调试和测试 MCP 工具
- 批量操作
- Agent 自动化调用（推荐使用 --json 模式）

## 安装

```bash
curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

## Agent 推荐工作流

1. **发现工具**：`merlin-cli list-tools` 或 `merlin-cli <group> --help`
2. **查看 Schema**：`merlin-cli <group> <command> --schema`
3. **预览请求**：`merlin-cli <group> <command> --json '{...}' --dry-run`
4. **执行调用**：`merlin-cli <group> <command> --json '{...}'`

## 使用方法

### JSON-first 调用（推荐）

```bash
# 查看参数 Schema
merlin-cli job get-run --schema

# JSON 字符串传参
merlin-cli job get-run --json '{"job_run_id": "xxx"}'

# 从文件读取参数
merlin-cli job create-run-fork --from-file params.json

# 预览请求（不执行）
merlin-cli job get-run --json '{"job_run_id": "xxx"}' --dry-run
```

### 分组命令

```bash
# 查看分组帮助
merlin-cli job --help
merlin-cli devbox --help
merlin-cli eval --help

# 分组调用示例
merlin-cli devbox list --json '{}'
merlin-cli insight get --json '{"insight_sid": "xxx"}'
merlin-cli arena get-evaluation --json '{"sid": "xxx"}'
merlin-cli tracking list-run-entities --json '{"project_name": "xxx", "experiment_name": "yyy"}'
```

### 工具发现

```bash
# 列出所有可用的工具（按分组显示）
merlin-cli list-tools

# 按名称过滤工具
merlin-cli list-tools --filter job

# 查看特定工具的帮助和可用参数
merlin-cli job get-run --help
```

## 工具分组

| 分组 | 说明 | 示例命令 |
|------|------|----------|
| `job` | 训练任务管理 | `job get-run`, `job list-run`, `job create-run-fork` |
| `devbox` | 开发机管理 | `devbox list`, `devbox get`, `devbox start` |
| `tracking` | 实验跟踪与指标 | `tracking list-run-entities`, `tracking get-timeseries` |
| `exercise` | 评估 Exercise 管理 | `exercise get`, `exercise get-version` |
| `collection` | 评估 Collection 管理 | `collection get`, `collection get-version` |
| `eval` | 伴生评估 | `eval get-companion-job`, `eval create-companion-job-fork` |
| `arena` | Arena 评估 | `arena get-evaluation`, `arena list-case` |
| `insight` | Insight 分析与用例搜索 | `insight get`, `insight create`, `insight search-case` |
| `checkpoint` | Checkpoint 查询 | `checkpoint get`, `checkpoint get-step` |
| `data` | 数据卡片 | `data get-eval-data`, `data get-field-stat`, `data create`, `data list` |
| `model` | 模型卡片 | `model get` |
| `knowledge` | 知识库搜索 | `knowledge search` |
| `service` | 推理服务 | `service get` |

## 认证

如果出现认证错误（401/403），请运行：

```bash
merlin-cli login
```

### 海外员工（TT）登录

海外 TT 员工无法使用 SSO 单点登录，会出现 "Login method isn't allowed" 错误。请使用 `--oauth2` flag 切换到 OAuth2 Device Code 登录方式：

```bash
# TikTok i18n 控制面登录
merlin-cli login --control-panel i18n-tt --oauth2

# ByteIntl 控制面登录
merlin-cli login --control-panel i18n-bd --oauth2
```

登录时 CLI 会显示一个浏览器验证链接和用户码，在浏览器中打开链接并使用账号密码或 passkey 完成认证即可。

## 注意事项

- 推荐使用 `--json` 传参，尤其是 Agent 调用场景
- 使用 `--schema` 查看工具的参数 JSON Schema
- 使用 `--dry-run` 预览请求不执行
- 复杂参数（对象、数组）使用 JSON 格式传递
