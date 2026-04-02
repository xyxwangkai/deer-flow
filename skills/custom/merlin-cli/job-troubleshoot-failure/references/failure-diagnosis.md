# 任务失败根因分析

适用于状态为 `FAILED` 或 `FAILED_TO_LAUNCH` 的任务。

## 步骤

### 1. 解析任务信息

从 URL 中提取 `job_run_id` 与 `trial_id`。若未提供 `trial_id`，通过任务信息定位最新一次失败的 Trial。

### 2. 获取任务总体状态

```bash
merlin-cli job get-run --json '{"job_run_id": "<id>"}'
```

- `FAILED_TO_LAUNCH`：优先查看 `errMsg` 字段；如包含权限或队列提示，调用 `job-resource` 技能评估可用资源

### 3. 拉取 Trial 级失败信息与退出码

```bash
merlin-cli job list-trial-exit-info --json '{"job_run_id": "<id>", "trial_id": "<trial_id>"}'
```

### 4. 获取并分析关键日志

```bash
merlin-cli job list-trial-logs --json '{"job_run_id": "<id>", "trial_id": "<trial_id>", "pod_name": "<pod>"}'
```

通过 Bash 下载并提取关键片段：`no_proxy=* curl -sS $LOG_URL | tail -n 80`

常见错误模式：
- `raise Exception('failed to execute user script with exit code ...')` — 用户脚本错误
- stderr 前几行平台初始化报错（如 `chmod: cannot access '/opt/tiger/mlx_deploy'`）通常可忽略

无法明确修复路径时，调用 `merlin-cli knowledge search` 检索相似案例。

### 5. 生成结构化诊断结论

- 失败概述：一句话描述
- 关键信息：任务 ID/Trial ID、退出码、失败时间
- 诊断依据：关键日志行与退出信息要点
- 日志摘录：最具代表性的报错行

### 6. 修复建议与诊断性 Fork

对可修复的问题给出明确建议（资源/入口/依赖）。满足以下任一条件触发"诊断性 fork"：

- Trial 退出信息含 `failed to execute user script` 或退出码非 0
- 原因不明

诊断性 fork 流程：
1. `merlin-cli job create-run-fork`，entrypoint 设为 `sleep 1d`
2. `merlin-cli job get-run`，`wait_until_running=true`
3. `merlin-cli job execute-script`，进入容器检查依赖/代码
4. 修复后 `git push` 并更新 `commit_sha` 重试

最多 1 次诊断性 fork + 1 次重试。

### 7. 资源与权限问题

若 `errMsg` 包含权限提示或 `arnoldDiagnoseInfo` 显示资源/队列问题：
- 调用 `job-resource` 技能获取可用资源
- 选择替代队列并生成推荐 `resource_config`

## 注意事项

- 日志中可能含敏感信息，展示时适当脱敏
- 多 Trial 时优先分析最近一次失败
- 平台级故障避免频繁自动重试
- 下载日志注意 `no_proxy=*`
