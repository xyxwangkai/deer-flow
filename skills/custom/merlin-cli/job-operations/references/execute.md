# Pod 内执行命令

在运行中的任务 Pod 内执行诊断命令或脚本。仅限 agent fork 创建的任务。

```bash
merlin-cli job execute-script --json '{"trial_id": "<trial_id>", "pod_name": "worker-0", "cmd": "nvidia-smi"}'
```

需要 `trial_id` 和 `pod_name`（可通过 `job get-run` 获取）。

## 注意事项

- 只能在 fork 之后的任务中执行
- 确保任务处于运行状态
- 敏感操作请谨慎执行
