# 停止任务

停止运行中的任务。仅允许停止由 Agent fork 创建的任务（带 `MERLIN_AGENT_FORK=true` 环境变量）。

```bash
merlin-cli job stop-run --json '{"job_run_id": "<id>"}'
```

## 注意事项

- 停止操作不可逆，执行前需确认
- 任务停止后资源会被释放
