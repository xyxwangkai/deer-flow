# 日志查看与分析

获取任务日志链接，下载并分析训练进度。

## 获取日志链接

```bash
merlin-cli job get-run --json '{"job_run_id": "<job_run_id>"}'
merlin-cli job list-trial-logs --json '{"job_run_id": "<job_run_id>", "trial_id": "<trial_id>"}'
```

可选过滤：`--filter '{"log_type": "ray_log"}'`（Ray 汇总日志）或 `instance_log`（实例日志）。

## 获取 TLS Log

TLS Log 可以保存最长约 60 天的日志，并支持关键词查询。当上方的日志链接获取为空时，可尝试使用 TLS Log 获取日志。

```bash
merlin-cli job get-tls-log --json '{
  "job_run_id": "<job_run_id>",
  "trial_id": "<trial_id>",
  "query": "trial_id='<trial_id>' AND kubernetes_pod_name='<pod_name>' AND stream='stdout'",
  "start": 1773759186,
  "end": 1773759286,
  "limit": 100,
  "offset": 0
}'
```

参数说明：

- `job_run_id`：Job Run ID（必填）
- `trial_id`：Trial ID（可选；不传则取最新的 `trial_id`）
- `query`：streamlog 查询语句（必填）。注意 `trial_id` 必须添加；`kubernetes_pod_name` 建议添加用于定位具体 Pod；`stream` 可填 `stdout` / `stderr`
- `start` / `end`：起止时间戳（秒）。可从 `job get-run` 的 `pod_list` 中取 `start_time` / `stop_time`；如果看到的是毫秒（13 位），需要除以 1000 转为秒
- `limit` / `offset`：分页参数（可选）。`limit` 默认 100（如果传参过大，注意日志过大导致上下文溢出问题）；`offset` 从 0 开始，最大值为 total_pages - 1（此时会返回最后一行日志）

获取 `kubernetes_pod_name`：通过 `merlin-cli job get-run` 返回的 `pod_list` 里的 `pod_name` 获取。

完整 query 字符串示例：

`trial_id='328690959' AND kubernetes_pod_name='trial-328690959-trialrun-328690959-worker-0' AND stream='stdout'`

关键词查询示例：

`trial_id='328690959' AND kubernetes_pod_name='trial-328690959-trialrun-328690959-worker-0' AND stream='stdout' AND _msg CONTAINS('这是关键词')`

## 下载并压缩日志

使用脚本下载日志并生成压缩片段，支持增量模式（固定复用 `--out_dir` 和 `--state_dir`）：

```bash
python3 skills/job-operations/scripts/download_and_compress_logs.py \
  --out_dir ./logs --state_dir ./logs/.state \
  jobA https://ml.bytedance.net/log-proxy/yg?xxx --max_lines 400
```

调整参数：`--context 2 --head 80 --tail 160 --max_lines 500`

兜底方式：

```bash
bash skills/job-operations/scripts/batch-get-jobs.sh {job_run_id} {log_url} -n 50
```

## 日志分析关注点

- `Epoch X/Y` / `Step X/Y` — 训练进度
- `loss=X.XXX` — 损失值变化
- `ERROR` / `Exception` / `Traceback` / `OOM` / `CUDA` / `Killed` — 错误
- `Saving checkpoint` / `Load checkpoint` — 检查点

## 输出

报告应包含：增量压缩日志片段 + 原始日志保存路径（便于追溯）。
