---
name: bits-mcp
description: Bits MCP 使用说明与环境对比测试（prod vs BOE）。在需要通过 MCP 调用 Bits 接口进行 RPC/HTTP 测试，或对比 prod 与 BOE 输出差异时使用。
metadata:
  short-description: Bits MCP + Env 对比
---

# Bits MCP 使用与环境对比测试

## 适用场景
- 需要通过 MCP 调用 Bits 接口进行 RPC/HTTP 测试
- 需要对比 prod 与 BOE 输出差异

- 可启动 `/agent` 执行对比流程；主AI线程仅感知最终基准结果与多环境输出差异

## 前置条件
- 已获取 Bits JWT token（首次登录 + 后续无头获取）
```bash
cd scripts
uv run python common/get_token.py --login
uv run python common/get_token.py --headless
```
代码位置参考：
`scripts/common/get_token.py:1`
`scripts/common/get_token.py:97`

## Bits MCP 基本用法
只需要使用 MCP 的 RPC 调用工具：
1. `mcp__bytedance-mcp-api_test_mcp__rpc_request`

其他 Bits MCP 工具本流程不需要调用。

## 与 scripts RPC 一致的关键字段
- RPC 请求体结构、默认配置：
`scripts/common/rpc.go:14`
`scripts/common/rpc.go:145`
- RPC 响应字段（包含 `resp_body`、`log_id` 等）：
`scripts/common/rpc.go:41`

## 环境切换与 Base.Extra["env"]
- scripts 中通过 `zone/idc/env/cluster` 覆盖目标环境：
`scripts/scan/main.go:29`
`scripts/scan/main.go:97`
- scripts 中通过 `Base.Extra["env"]` 控制 env：
`scripts/meta/main.go:60`
`scripts/meta/main.go:181`
注意：实际 `env` 是塞在 `Base.Extra["env"]` 中，特定泳道环境命名可能不同，但通常都在 BOE 环境内。

## 环境对比测试（prod vs BOE）
- 未明确要求线上时，默认都在 BOE 环境内进行（包括 `env=prod`）
- 默认将"自己的 env"视为 BOE（`zone=BOE`、`idc=boe`），并通过 `Base.Extra["env"]` 传入泳道环境名
- 对比流程与 JSON 结构化 diff 见：`references/compare_env.md`

## 示例：MGetAccountForSearch 调用流程与入参
适用于 `lark.intelligence.account_service` 的搜索读接口。

调用流程（RPC）：
1. 从用户输入中获取到env
2. `mcp__bytedance-mcp-api_test_mcp__query_clusters_by_env`（获取 zone/idc/cluster/online）
3. `mcp__bytedance-mcp-api_test_mcp__query_service_api_versions`（获取 idl_version）
   - **必须使用具体版本号**（如 `1.0.652`），**不要使用 `master`**。使用 `master` 会导致 "此接口在 BAM 平台上没有录入" 错误
   - 取返回数组中 `idl_branch=master` 的第一个 version 值
4. `mcp__bytedance-mcp-api_test_mcp__ai_recommend_api_test_history_traffic`（获取历史推荐入参）/通过用户输入提取
5. `mcp__bytedance-mcp-api_test_mcp__rpc_request`（发起 RPC 请求）

入参示例（重点：`Base.Extra["env"]` 指定泳道环境）：
```json
{
  "EntityName": "",
  "Ids": ["xxx"],
  "Fields": ["id", "name", "industry", "create_time", "update_time"],
  "ReadFrom": "PRIMARY",
  "Base": {
    "LogID": "",
    "Caller": "",
    "Addr": "",
    "Client": "",
    "TrafficEnv": {"Open": false, "Env": ""},
    "Extra": {"": "", "env": "<your_boe_env>"}
  }
}
```
