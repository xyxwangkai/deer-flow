---
name: tracking-experiment
description: 查询和分析 merlin, seed Tracking 实验数据：获取 Metrics 列表与数据、搜索实验图表面板、获取图表时序数据、分析 loss/accuracy 等指标趋势。当用户说"查看 Tracking 指标/loss 趋势/训练曲线/实验图表/experiment panel/metrics 分析/指标对比"时使用。
---

# Tracking 实验与指标分析

查询和分析 Merlin Tracking 实验数据，包括 Metrics 获取、实验图表搜索、趋势分析。

## 前置条件

- `merlin-cli` 可用

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

---

## 1. 获取 Metrics 列表

查询任务关联的所有 Tracking Metrics。使用 `job_run_id` 参数（不要用 `project` 和 `experiment` 参数）。

```bash
merlin-cli tracking list-run-entities --json '{"job_run_id": "<job_run_id>"}'
```

---

## 2. 获取 Metrics 数据

针对关键 Metrics（loss、eval_loss、accuracy 等）获取详细数据：

```bash
merlin-cli tracking get-run-entity-step-auto --json '{
  "project_id": "<project_id>",
  "experiment_id": "<experiment_id>",
  "entity_name": "loss"
}'
```

返回包含 TOS URL 的 CSV 数据，下载后可用分析脚本处理。

---

## 3. 搜索实验图表面板

查询实验图表（Experiment Insight）的基础信息，包括图表名称、x 轴范围、legends 列表：

```bash
merlin-cli tracking search-panel --json '{
  "insights": "[{\"insight_sid\": \"<id>\", \"experiment_group_sid\": \"<group_id>\"}]"
}'
```

每个 legend 是图表中一条线的唯一标识，可用于后续获取该线的详细数据。

---

## 4. 获取图表时序数据

获取实验图表中特定 legend 的详细时序数据：

```bash
merlin-cli tracking get-timeseries --json '{
  "insight_sid": "<id>",
  "legend": "<legend_id>"
}'
```

---

## 5. 趋势分析

下载 CSV 数据后，使用分析脚本进行趋势与波动分析：

```bash
python3 skills/tracking-experiment/scripts/analyze_metrics_csv.py \
  loss_data.csv --state_dir ./metrics_state --metrics loss --smooth 21 --out ./loss_report.html
```

固定复用 `--state_dir` 支持增量分析，避免重复处理已分析区间。

---

## 脚本

| 脚本 | 路径 | 作用 |
|------|------|------|
| CSV 指标分析 | `scripts/analyze_metrics_csv.py` | 趋势与波动分析 + HTML 曲线图 |
| CSV 处理工具 | `scripts/csv_metrics_utils.py` | CSV 列裁剪与多文件拼接 |
| 旧版分析脚本 | `scripts/analyze_metrics.py` | 兼容用途 |

### 使用示例

```bash
# 输出摘要
python3 scripts/analyze_metrics_csv.py https://example.com/metrics.csv --metrics loss accuracy

# 生成可视化报告
python3 scripts/analyze_metrics_csv.py ./metrics.csv --out ./metrics_report.html --smooth 21

# 对比多个 run
python3 scripts/analyze_metrics_csv.py run1.csv run2.csv --metrics loss --out compare.html --ema 0.2

# CSV 列裁剪
python3 scripts/csv_metrics_utils.py select ./metrics.csv --columns step,loss,accuracy --out ./small.csv

# 拼接多个 run
python3 scripts/csv_metrics_utils.py concat run1.csv run2.csv --out ./all_runs.csv
```

---

## 注意事项

- 使用 `tracking list-run-entities` 时必须用 `job_run_id` 参数
- 如果某个指标获取失败，跳过并记录
- 关注异常波动（如 loss 突然上升）

---

## 关联技能

- `job-monitor-supervisor`：任务监控总调度
- `job-operations`：查看任务日志
