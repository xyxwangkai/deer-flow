# Hang 诊断（Mega/Xray）

适用于任务状态为 `RUNNING` 但训练无进展（hang）的场景。

Mega/Xray 工具以 `trial_id` 为核心参数（不是 `job_run_id`），需先从 `job get-run` 提取 trial_id。

## 第一步：获取 hang triggers

```bash
merlin-cli job get-mega-hang-nccl-triggers --json '{"trial_id": "<trial_id>"}'

merlin-cli job get-mega-hang-pyspy-triggers --json '{"trial_id": "<trial_id>"}'
```

## 第二步：深入分析具体 trigger

从 triggers 返回中提取 `run_id` 和 `trigger_timestamp`，再获取进程树或 pyspy trace：

```bash
merlin-cli job get-mega-hang-process-tree --json '{"trial_id": "<trial_id>", "run_id": "<run_id>", "trigger_timestamp": <ts>}'

merlin-cli job get-mega-hang-pyspy-trace --json '{"trial_id": "<trial_id>", "run_id": "<run_id>", "trigger_timestamp": <ts>}'
```

诊断思路：先查 NCCL triggers 确认是否为通信 hang，再用 process tree 和 pyspy trace 定位卡住的调用栈。

## Mega Trial 告警与事件

```bash
merlin-cli job get-mega-trial-alerts --json '{"trial_id": "<trial_id>"}'

merlin-cli job get-mega-trial-events --json '{"trial_id": "<trial_id>"}'

merlin-cli job get-mega-trial-robust-events --json '{"trial_id": "<trial_id>"}'
```

## Karl 事件

Karl 按 `trial_id` 过滤（也支持 `ip`、`event_type` 等条件）：

```bash
merlin-cli job get-karl-events --json '{"trial_id": "<trial_id>"}'
```

## Grafana 监控

获取任务 Grafana 看板链接辅助诊断：

```bash
merlin-cli job get-grafana --json '{"job_run_id": "<id>"}'
```
