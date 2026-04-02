# Grafana 监控链接

获取任务的 Grafana 监控看板链接。

```bash
merlin-cli job get-grafana --json '{"job_run_id": "<id>"}'
```

也支持通过 `job_url`、`trial_id`、`robust_run_id`、`instance_id` 查询。
