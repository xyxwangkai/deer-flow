# 查询时间线与 Pod 退出信息

## 任务时间线

```bash
merlin-cli job get-timeline --json '{"job_run_id": "<id>", "trial_id": "<trial_id>"}'
```

返回事件列表，事件类型包括：`RobustHotUpdate`、`TrialCreated` 等。

## Pod 退出信息

```bash
merlin-cli job list-trial-exit-info --json '{"job_run_id": "<id>", "trial_id": "<trial_id>"}'
```

返回 Pod 状态、退出码、错误信息。
