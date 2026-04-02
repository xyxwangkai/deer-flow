---
name: experiment-panel-monitor
description: 查找 Experiment 看板中的图表曲线，检测异常（骤降/骤升、剧烈震荡）并发送告警通知。
---

# Experiment 看板监控

## 摘要

本技能用于监控 Experiment 看板中的图表曲线，使用 LOESS 回归和统计方法检测异常，如检测到异常则使用 SendNotification 工具发送飞书通知。

**核心设计理念**：脚本层聚焦于提供丰富、原始的统计特征与局部判据建议，将最终的决策权上移给 Agent。

## 输入参数

- `experiment_group_sid`: 实验组的唯一标识 ID（必需）
- `insight_sids`: 需要监控的图表 insight_sid 列表（可选，如果用户指定了关注的图表）
- `legends`: 需要监控的曲线名称列表（可选，如果用户指定了关注的曲线）

**💡 提示**：如果用户指定了只关注某些图表或曲线（如"关注评测相关图表"、"关注 M12 模型"），可以：
1. 先使用 `extract_metadata.py` 脚本搜索匹配的 insight_sid 或 legend
2. 再将搜索结果传入 `single_analysis.py` 的 `--insight-sids` 或 `--legends` 参数

## 数据来源

**⚠️ 要求：Agent 必须通过 merlin-cli 拉取看板数据并生成 `case.csv`，再交给后续分析脚本使用。**

1. **调用 merlin-cli**（二选一或组合使用）：
   - **`merlin-cli tracking search-panel`**：根据实验组 ID 与图表 ID（insight_sid）查询每个图表的 legends 列表；
   - **`merlin-cli tracking list-run-entities`**：若上下文是任务维度（有 job_run_id），可先调用以获取 run 相关信息。
2. **生成 CSV**：使用脚本 `scripts/fetch_panel_csv.py` 封装上述逻辑，根据 search-panel 与 get-timeseries 的结果生成 `case.csv`（见下方「生成 case.csv」步骤）。也可在拿到 panel/legends 与时序数据后，自行按同名字段组装 CSV。

CSV 表头必须包含以下列（与 `single_analysis.py` / `cross_curve_analysis.py` 一致）：
- `insight_sid`: 图表的 experiment_group_insight_sid（如 8puzm1u1qe697c293f）
- `legend`: 曲线名称
- `x`: 数据点的 x 坐标值
- `y`: 数据点的 y 坐标值
- `is_new`: 是否为新增数据点（0=存量，1=增量）。首次拉取不传 baseline 时全部为 1；第二次及以后传入上次 CSV 作 `--baseline-csv` 时，上次已有的点为 0，新出现的点为 1。

## 异常类型定义

本技能基于 LOESS（局部加权回归）算法检测以下几类曲线异常：

### 1. 点异常 (Point Anomaly)
- **定义**: 新增数据点与 LOESS 预测值的偏差超过阈值
- **检测方法**: 计算 z-score，当连续多个点的 z-score 超过阈值时触发告警
- **适用场景**: 评估指标突然变化、训练过程中的异常波动等

### 2. 下跳变点 (Step Down)
- **定义**: 曲线出现明显的下降阶跃
- **检测方法**: 结合 z-score 异常检测和变点检测（t-statistic）
- **适用场景**: 模型性能突然下降、评估配置错误等

### 3. 上跳变点 (Step Up)
- **定义**: 曲线出现明显的上升阶跃
- **检测方法**: 同下跳变点，但方向相反
- **适用场景**: 指标异常升高、数据异常等

## 多维特征输出

脚本输出多维统计特征，供 Agent 进行更智能的决策：

| 特征名 | 说明 | 用途 |
|--------|------|------|
| `robust_volatility_mad` | 鲁棒波动率 (MAD) | 衡量曲线波动程度，对异常值不敏感 |
| `relative_deviation_rate` | 相对偏差率 | 衡量偏差的业务显著性 |
| `hf_energy_ratio` | 高频能量比 | 判断"剧烈抖动"，FFT 分析 |
| `consecutive_hit_rate` | 连续窗口命中率 | 反映异常的持续性 |
| `sample_size` | 样本量 | 判断统计指标的置信度 |
| `z_score_max` | 最大 z-score | 当前告警的最大 z-score 值 |
| `pearson_corr_with_peer` | Peer 相关系数 | 与 Peer Group 的平均相关性 |

### 局部判据建议 (local_suggestion)

脚本会基于多维特征输出局部判据建议，供 Agent 参考：

| 建议值 | 触发条件 |
|--------|----------|
| `high_confidence_anomaly` | 高置信度异常（多指标同时超阈值） |
| `potential_fluctuation` | 潜在波动（部分指标超阈值） |
| `normal` | 正常（无明显异常） |

**Agent 决策说明**：Agent 可以根据上下文（如用户需求、历史告警模式）灵活组合这些特征，覆盖或参考 `local_suggestion` 进行最终决策。

## 执行流程

**📋 分析流程概览**：本技能需要结合两种分析方法：
1. **纵向分析**（`single_analysis.py`）：检测单条曲线相对于自身历史趋势的异常（骤降/骤升）
2. **横向分析**（`cross_curve_analysis.py`）：检测同一图表内相对于其他曲线表现异常的曲线（震荡过大）

两种分析互为补充，应同时执行以获得完整的异常检测结果。

### 0. 生成 case.csv（必须）

**🚨 必须先得到 `case.csv` 再执行后续分析。** 数据来源为 merlin-cli，由脚本 `fetch_panel_csv.py` 封装拉取逻辑。

从实验看板 URL 或用户输入中提取：
- `experiment_group_sid`：实验组 ID（如 URL 中 `experiment/dashboard/<experiment_group_sid>`）
- `insight_sids`：要拉取的图表 ID 列表（如 URL 参数 `experiment_group_insight` 或看板内多个图表的 insight_sid）

执行：

```bash
# 确保 merlin-cli 已安装且已登录（认证失败时执行 merlin-cli auth login 或 merlin-cli login）
python3 skills/experiment-panel-monitor/scripts/fetch_panel_csv.py \
  --experiment-group-sid <experiment_group_sid> \
  --insight-sids <insight_sid_1> [insight_sid_2 ...] \
  --output case.csv
```

- **首次拉取**：不传 `--baseline-csv`，每条 legend 按 x 排序后，后 30% 的点标 `is_new=1`（新增），前 70% 标 `is_new=0`（历史）；可用 `--first-new-ratio 0.3` 调整比例。
- **第二次及以后**：传 `--baseline-csv case_prev.csv`（指向上次输出的 CSV），脚本会将上次已有的点标为 `is_new=0`（存量），本次新出现的点标为 `is_new=1`（增量）。
- 脚本内部会依次调用 `merlin-cli tracking search-panel` 与 `merlin-cli tracking get-timeseries`，输出 CSV 表头：**insight_sid, legend, x, y, is_new**。

若需任务维度信息，可先执行：

```bash
merlin-cli tracking list-run-entities --json '{"job_run_id": "<job_run_id>"}'
```

再将得到的上下文与看板 URL 结合，确定要拉取的 `experiment_group_sid` 与 `insight_sids`。

### 1. （可选）提取元数据并筛选关注范围

如果用户提出了额外需求（如"重点关注评测相关图表"、"关注 M12 模型表现"），可以先使用 `extract_metadata.py` 脚本提取 CSV 中的图表和曲线信息，根据关键词搜索匹配的 insight_sid 或 legend：

```bash
# 查看所有图表和曲线
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv

# 搜索包含关键词的图表/曲线
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv -s "评测"
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv -s "M12"
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv -s "mmlu"

# 只查看图表列表
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv --insights-only

# 输出到 JSON 文件
python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv -o metadata.json
```

脚本会输出匹配的 insight_sid 和 legend，以及可直接用于 `single_analysis.py` 的参数格式。

### 2. 纵向分析：使用 single_analysis.py 检测趋势异常

**🎯 推荐：使用自动阈值调整模式**，脚本会通过二分查找自动找到合适的 z_threshold，使告警数量在 2~8 个之间：

```bash
# 默认输出 CSV 格式（推荐，节省 token）
python3 skills/experiment-panel-monitor/scripts/single_analysis.py case.csv \
  --auto \
  --output ./analysis_result \
  --plot-dir ./alert_plots/

# 输出 JSON 格式
python3 skills/experiment-panel-monitor/scripts/single_analysis.py case.csv \
  --auto \
  --output ./analysis_result \
  --output-format json \
  --plot-dir ./alert_plots/
```

如需手动指定阈值，可以不使用 `--auto` 参数：

```bash
python3 skills/experiment-panel-monitor/scripts/single_analysis.py case.csv \
  --output ./analysis_result \
  --plot-dir ./alert_plots/ \
  --z-threshold 4.0
```

脚本参数说明：
- `input`: 输入 CSV 文件路径（必需），使用 `case.csv`
- `--output, -o`: 输出结果路径（不含扩展名）
- `--output-format, -f`: 输出格式（`csv`/`json`/`both`，默认 `csv`）
- `--plot-dir, -p`: 输出告警图片目录
- `--auto, -a`: **自动阈值调整模式**，使用二分查找找到合适的 z_threshold
- `--target-min`: 自动模式下的目标告警数量下限，默认 2
- `--target-max`: 自动模式下的目标告警数量上限，默认 8
- `--insight-sids, -i`: **只关注的 insight_sid 列表**，多个用空格分隔，不指定则分析所有曲线
- `--legends, -l`: **只关注的 legend 列表**，多个用空格分隔，不指定则分析所有曲线
- `--z-threshold, -z`: z-score 阈值，默认 4.0（手动模式时使用）
- `--consecutive, -c`: 连续点数阈值，默认 3
- `--min-deviation, -m`: 最小绝对偏差阈值，默认 0.02
- `--min-new-points`: 最少新增数据点数量，默认 2
- `--no-local-suggestion`: 关闭局部判据建议输出
- `--quiet, -q`: 安静模式，不打印详细信息

**检测原理**：
1. 根据 `is_new` 字段区分历史数据（is_new=0）和新增数据（is_new=1）
2. 使用历史数据训练 LOESS 模型
3. 对新增数据点进行预测，计算残差和 z-score
4. 当连续多个点的 z-score 超过阈值且绝对偏差超过最小阈值时，触发告警
5. 使用变点检测（t-statistic）判断是否为阶跃变化
6. **告警按 z_score 绝对值降序排列**，最显著的异常排在最前面
7. 计算多维特征并输出局部判据建议

### 3. 横向分析：使用 cross_curve_analysis.py 检测相对异常

**🔍 横向对比分析**：识别同一图表内相对于其他曲线表现异常的曲线（如震荡特别明显的曲线）。

**Peer 选取机制**：脚本会计算每条曲线与图表内其他曲线在历史窗口的皮尔逊相关系数，选择相关性高的曲线组成 Peer Group，横向对比仅在 Peer Group 内进行，避免与不相关趋势曲线的错误比较。

```bash
# 基础用法（默认输出 CSV）
python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv \
  -o ./cross_analysis_result \
  -p ./comparison_plots/

# 输出 JSON 格式
python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv \
  -o ./cross_analysis_result \
  -f json \
  -p ./comparison_plots/

# 调整 Peer 选取参数
python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv \
  --peer-method pearson \
  --peer-threshold 0.8 \
  --min-peer-size 3 \
  -p ./comparison_plots/
```

脚本参数说明：
- `input`: 输入 CSV 文件路径（必需）
- `-o, --output`: 输出结果路径（不含扩展名）
- `-f, --output-format`: 输出格式（`csv`/`json`/`both`，默认 `csv`）
- `-p, --plot-dir`: 输出对比图片目录
- `-t, --percentile-threshold`: 百分位阈值，默认 90
- `--peer-method`: Peer 选取方法（`pearson`/`dtw`，默认 `pearson`）
- `--peer-threshold`: Peer Group 筛选阈值，默认 0.8
- `--min-peer-size`: 最小 Peer Group 规模，默认 3
- `--min-new-points`: 最少新增数据点数量，默认 2
- `--no-local-suggestion`: 关闭局部判据建议输出
- `-q, --quiet`: 安静模式

**检测原理**：
1. 计算每条曲线的波动率、方向变化频率、残差标准差等指标
2. 基于历史窗口计算曲线间的皮尔逊相关系数，筛选 Peer Group
3. 将每条曲线的指标与其 Peer Group 内的曲线比较，计算百分位排名
4. 当某曲线的指标显著高于 Peer Group（z > 1.5 且百分位 > 90%）时触发告警
5. 计算多维特征并输出局部判据建议

**告警类型**：
- `high_volatility`: 波动率显著高于其他曲线（曲线震荡剧烈）
- `unstable`: 方向变化频率显著高于其他曲线（曲线频繁上下波动）

### 4. 阈值调整建议

**纵向分析（single_analysis.py）**：

**🎯 推荐使用 `--auto` 参数**，脚本会自动通过二分查找调整 z_threshold，使告警数量在目标范围内（默认 2~8 个）。

如果不使用自动模式，可以手动调整阈值：

| 检测结果 | 建议操作 |
|---------|---------|
| 告警数量 = 0 | 降低 z-threshold（如 4.0 → 2.5）或降低 consecutive（如 3 → 2） |
| 告警数量 > 10 | 提高 z-threshold（如 4.0 → 5.0）或提高 min-deviation（如 0.02 → 0.05） |
| 告警数量 2-8 | 数量合理，继续下一步 |

**横向分析（cross_curve_analysis.py）**：

| 检测结果 | 建议操作 |
|---------|---------|
| 告警数量 = 0 | 降低 percentile-threshold（如 90 → 80）或调整 peer-threshold |
| 告警数量 > 5 | 提高 percentile-threshold（如 90 → 95）或提高 peer-threshold |

### 5. 告警复核与决策

**📊 告警排序说明**：检测结果已按显著程度（z_score 绝对值）降序排列，排在前面的告警变化最显著，应优先关注。

**决策流程**：
1. **优先关注最显著的告警**：告警列表已按 z_score 从大到小排序，重点审查靠前的项
2. **参考多维特征和局部建议**：结合 CSV/JSON 中的 `features` 和 `local_suggestion` 字段辅助判断
3. **综合判断**：结合 z-score、置信度、绝对偏差幅度与 `local_suggestion` 决定是否发送告警
4. **过滤误报**：若 `relative_deviation_rate` 很小或 `local_suggestion` 为 normal，可判定为误报不发送

**判断标准**：
- ✅ **应发送告警**：`local_suggestion` 为 `high_confidence_anomaly`，且 z-score、偏差幅度较大
- ✅ **应发送告警**：类型为 step_down/step_up，且 message 描述明显阶跃
- ⚠️ **需谨慎判断**：`local_suggestion` 为 `potential_fluctuation`，可结合 features 再决定
- ❌ **不发送告警**：z-score 较高但绝对偏差很小（如 min_abs_deviation 未触发）
- ❌ **不发送告警**：曲线样本量过小或波动在合理范围内

告警图片已写入 `--plot-dir` 指定目录，可按需自行打开查看；发送通知时可在正文中引用图片路径（见下文 SendNotification 格式）。

### 6. 处理结果并输出报告

#### 无异常情况

**如果检测结果为 0 个告警**，也需要发送通知告知用户检测已完成：

```markdown
## 实验看板异常检测完成

检测时间：2025-02-01 10:00:00
检测曲线数：33
检测结果：**未发现异常**

[点击查看实验看板](https://seed.bytedance.net/experiment/dashboard/{experiment_group_sid})
```

#### 有异常情况

**⚠️ 前提条件：结合第 5 步告警复核，确认异常真实存在后再输出告警报告。**

#### 输出方式

根据可用工具选择输出方式：

1. **如果有 `SendNotification` 工具**：使用该工具发送飞书通知，通知正文使用中文
2. **如果没有 `SendNotification` 工具**：将报告写入本地 markdown 文件 `alert_report.md`

#### SendNotification 图片引用格式

**⚠️ 重要：使用 `SendNotification` 工具发送告警时，正文中引用图片必须使用 `sandbox://` 协议加绝对路径格式。**

```markdown
![曲线名称](sandbox:///Users/bytedance/IdeaProjects/skills/alert_plots/curve_xxx_alert.png)
```

**格式说明**：
- 使用 `sandbox://` 协议前缀（注意是三个斜杠 `sandbox:///`）
- 后面跟图片的**绝对路径**
- 示例：`sandbox:///absolute/path/to/image.png`

**错误示例**：
```markdown
<!-- 错误：使用相对路径 -->
![曲线名](./alert_plots/curve_xxx_alert.png)

<!-- 错误：使用 file:// 协议 -->
![曲线名](file:///path/to/image.png)
```

**正确示例**：
```markdown
<!-- 正确：使用 sandbox:// 协议 + 绝对路径 -->
![曲线名](sandbox:///Users/bytedance/IdeaProjects/skills/alert_plots/curve_xxx_alert.png)
```

#### 图表链接格式

可以通过以下链接直接跳转到有问题的图表：
```
https://seed.bytedance.net/seed/share-link?experiment_group_insight_sid={insight_sid}&experiment_group_sid={experiment_group_sid}
```

#### 告警报告必要信息

报告中必须包含以下信息：

1. **图表链接**（必需）：每个异常图表的链接，格式：
   ```
   https://seed.bytedance.net/seed/share-link?experiment_group_insight_sid={insight_sid}&experiment_group_sid={experiment_group_sid}
   ```

2. **看板链接**（必需）：实验看板的链接，格式：
   ```
   https://seed.bytedance.net/experiment/dashboard/{experiment_group_sid}
   ```

3. **异常信息**：根据检测结果描述异常情况，包含曲线名称、异常类型、严重程度、具体数值等

4. **告警图片**：使用 markdown 格式引用告警图片，格式：`![曲线名称](./alert_plots/xxx.png)`

#### 本地报告示例（alert_report.md）

```markdown
# 异常检测告警报告

## 概要

- 检测时间：2025-02-01 10:00:00
- 总曲线数：33
- 异常数量：2

## 看板链接

[点击查看实验看板](https://seed.bytedance.net/experiment/dashboard/{experiment_group_sid})

## 异常详情

### 1. M12devb_2b5_fsdp 模型的 code 能力出现明显下降

从下图可以看到，在 step 8149 附近，该曲线出现了一个明显的下跳，从约 0.87 下降到约 0.80，降幅约 7.5%。这个下降持续到了最新的数据点，没有恢复迹象。

**特征摘要**：
- 局部建议：high_confidence_anomaly
- 高频能量比：0.12
- 连续命中率：1.0
- Peer 相关性：0.92

**可能原因**：训练配置变更、数据质量问题或模型退化。建议检查该时间点前后的训练日志。

- **图表链接**：[查看原始图表](https://seed.bytedance.net/seed/share-link?experiment_group_insight_sid=xxx&experiment_group_sid=yyy)

![M12devb_2b5_fsdp-code](./alert_plots/curve_M12devb_2b5_fsdp_code_alert.png)

### 2. M13P4_D10_6B 模型的综合能力出现异常波动

从下图可以看到，在 step 9659 之后，该曲线开始明显偏离历史趋势（绿色虚线），实际值持续低于预测值约 0.06，偏离程度较大。

**特征摘要**：
- 局部建议：potential_fluctuation
- 高频能量比：0.68
- 连续命中率：0.7
- Peer 相关性：0.85

**可能原因**：评估数据变化或模型在某些能力上出现退化。建议对比其他模型在同一时间段的表现。

- **图表链接**：[查看原始图表](https://seed.bytedance.net/seed/share-link?experiment_group_insight_sid=xxx&experiment_group_sid=yyy)

![M13P4_D10_6B-综合能力](./alert_plots/curve_M13P4_D10_6B_alert.png)
```

### 7. 返回分析结果

将分析结果返回给用户，包括：
- 纵向分析检测到的异常列表（趋势异常）
- 横向分析检测到的异常列表（相对异常）
- 各曲线的状态摘要
- 是否已发送通知

## 脚本与工具

### 看板数据拉取脚本（生成 case.csv）

- 位置：`skills/experiment-panel-monitor/scripts/fetch_panel_csv.py`
- 作用：调用 `merlin-cli tracking search-panel` 与 `merlin-cli tracking get-timeseries`，将看板图表时序数据汇总为 CSV，供 single_analysis / cross_curve_analysis 使用。
- 使用场景：**执行分析前必须先生成 case.csv**；从实验看板 URL 或用户提供的 experiment_group_sid、insight_sids 出发运行本脚本。
- 输出 CSV 表头：`insight_sid`, `legend`, `x`, `y`, `is_new`。其中 `insight_sid` 为图表的 experiment_group_insight_sid；is_new：0=存量，1=增量。
- 参数说明：
  - `--experiment-group-sid`, `-g`：实验组 ID（必需）
  - `--insight-sids`, `-i`：要拉取的图表 insight_sid 列表（必需，可多个）
  - `--output`, `-o`：输出 CSV 路径，默认 `case.csv`
  - `--baseline-csv`, `-b`：上次输出的 CSV 路径；不传则本次全部 is_new=1（首次），传入则与上次对比得到存量/增量
  - `--quiet`, `-q`：安静模式
- 使用示例：
  ```bash
  # 从看板 URL 提取 experiment_group_sid=11z86vnx0l697c293f, insight_sid=nyhzw6lb1c697c293f
  python3 skills/experiment-panel-monitor/scripts/fetch_panel_csv.py \
    -g 11z86vnx0l697c293f -i nyhzw6lb1c697c293f -o case.csv
  ```

### 元数据提取脚本

- 位置：`skills/experiment-panel-monitor/scripts/extract_metadata.py`
- 作用：从 CSV 文件中提取图表（insight）和曲线（legend）的元数据，支持关键词搜索
- 使用场景：当用户提出"关注某类图表"或"关注某个模型"等需求时，用于筛选目标
- 参数说明：
  - `input`: 输入 CSV 文件路径（必需）
  - `-s, --search`: 搜索关键词，返回匹配的 insight_sid 和 legend
  - `-o, --output`: 输出 JSON 文件路径
  - `--insights-only`: 只输出图表列表
  - `--legends-only`: 只输出曲线列表
  - `-q, --quiet`: 安静模式，只输出 JSON
- 使用示例：
  ```bash
  # 搜索包含 "M12" 的图表/曲线
  python3 skills/experiment-panel-monitor/scripts/extract_metadata.py case.csv -s "M12"
  
  # 搜索结果会输出可用于 single_analysis.py 的参数格式：
  # --insight-sids xxx yyy
  # --legends "曲线名称"
  ```

### 横向对比脚本

- 位置：`skills/experiment-panel-monitor/scripts/cross_curve_analysis.py`
- 作用：对同一图表下的不同曲线进行横向对比，识别相对于其他曲线表现异常的曲线
- 检测方法：
  - **Peer 选取**：计算每条曲线与图表内其他曲线在历史窗口的皮尔逊相关系数，筛选 Peer Group
  - **曲线指标计算**：计算每条曲线的波动率、方向变化频率、残差标准差等指标
  - **组内比较**：将每条曲线的指标与 Peer Group 内曲线比较，计算百分位排名
  - **z-score 检测**：当某曲线的指标显著高于 Peer Group（z > 1.5 且百分位 > 90%）触发告警
- 告警类型：
  - `high_volatility`: 波动率显著高于其他曲线（曲线震荡剧烈）
  - `unstable`: 方向变化频率显著高于其他曲线（曲线频繁上下波动）
- 使用场景：当需要识别"相对于其他曲线震荡特别明显"的曲线时使用
- 参数说明：
  - `input`: 输入 CSV 文件路径（必需）
  - `-o, --output`: 输出结果路径（不含扩展名）
  - `-f, --output-format`: 输出格式（`csv`/`json`/`both`，默认 `csv`）
  - `-p, --plot-dir`: 输出对比图片目录
  - `-t, --percentile-threshold`: 百分位阈值，默认 90
  - `--peer-method`: Peer 选取方法（`pearson`/`dtw`，默认 `pearson`）
  - `--peer-threshold`: Peer Group 筛选阈值，默认 0.8
  - `--min-peer-size`: 最小 Peer Group 规模，默认 3
  - `--min-new-points`: 最少新增数据点数量，默认 2
  - `--no-local-suggestion`: 关闭局部判据建议
  - `-q, --quiet`: 安静模式
- 使用示例：
  ```bash
  # 基础用法（输出 CSV）
  python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv -o comparison -p ./comparison_plots/
  
  # 输出 JSON 格式
  python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv -o comparison -f json
  
  # 调整 Peer 选取参数
  python3 skills/experiment-panel-monitor/scripts/cross_curve_analysis.py case.csv --peer-threshold 0.7 --min-peer-size 5
  ```

### 异常检测脚本

- 位置：`skills/experiment-panel-monitor/scripts/single_analysis.py`
- 作用：对单个 CSV 快照进行异常检测，基于 LOESS 回归和 z-score 统计方法
- 检测方法：
  - **LOESS 预测**：使用历史数据拟合局部加权回归模型，预测新增数据点的期望值
  - **z-score 检测**：计算实际值与预测值的标准化残差，超过阈值视为异常
  - **变点检测**：使用 t-statistic 判断是否存在阶跃变化
  - **MAD 鲁棒估计**：使用中位数绝对偏差估计尺度，对异常值更鲁棒
  - **多维特征计算**：计算高频能量比、连续命中率等多维特征
- 使用示例：
  ```bash
  # 基础用法（输出 CSV，推荐）
  python3 scripts/single_analysis.py case.csv -o result -p ./plots/
  
  # 输出 JSON 格式
  python3 scripts/single_analysis.py case.csv -o result -f json -p ./plots/
  
  # 调整阈值
  python3 scripts/single_analysis.py case.csv -z 3.0 -c 2 -m 0.05
  
  # 安静模式
  python3 scripts/single_analysis.py case.csv -o result -q
  ```

### 输出格式

**📊 默认输出 CSV 格式（推荐，节省 token）**

#### 纵向分析输出

**alerts.csv 格式示例**：
```csv
legend,insight_sid,type,x_start,x_end,message,robust_volatility_mad,relative_deviation_rate,hf_energy_ratio,consecutive_hit_rate,sample_size,z_score_max,pearson_corr_with_peer,local_suggestion
【M12devb_2b5_fsdp】-综合能力|code,unqb1ia141697c293f,step_down,8149.24,9155.79,检测到下跳变点,0.031,0.087,0.12,1.0,5,-57.41,0.92,high_confidence_anomaly
【M13P4_D10_6B】-综合能力,hus6dvlai3697c293f,high_volatility,9659.07,10162.34,检测到剧烈波动,0.015,0.045,0.68,0.7,10,-7.57,0.85,potential_fluctuation
```

**summary.txt 格式示例**：
```
total_curves=33,total_alerts=2,z_threshold=4.00,consecutive_threshold=3
```

#### 横向分析输出

**cross_alerts.csv 格式示例**：
```csv
legend,insight_sid,insight_name,type,score,percentile,message,robust_volatility_mad,relative_deviation_rate,hf_energy_ratio,consecutive_hit_rate,sample_size,z_score_max,pearson_corr_with_peer,local_suggestion
【M12devb_2b5_fsdp】-综合能力|code,unqb1ia141697c293f,综合能力图表,high_volatility,2.35,95.5,波动率显著高于同图表其他曲线,0.031,0.087,0.12,1.0,5,2.35,0.92,high_confidence_anomaly
```

**cross_summary.txt 格式示例**：
```
total_insights=5,total_alerts=2,percentile_threshold=90.0
```

#### JSON 格式（可选）

使用 `--output-format json` 或 `--output-format both` 可以输出 JSON 格式：

```json
{
  "input_file": "case.csv",
  "total_curves": 33,
  "total_alerts": 2,
  "parameters": {
    "z_threshold": 4.0,
    "consecutive_threshold": 3,
    "min_abs_deviation": 0.02
  },
  "alerts": [
    {
      "legend": "【M12devb_2b5_fsdp】-[Evalset3.0]-综合能力|code",
      "insight_sid": "unqb1ia141697c293f",
      "type": "step_down",
      "x_start": 8149.24,
      "x_end": 9155.79,
      "y_observed": 0.8166,
      "y_predicted": 0.8671,
      "z_score": -57.41,
      "confidence": 0.99,
      "message": "检测到下跳变点: x=8149.24, 幅度=-0.0753",
      "features": {
        "robust_volatility_mad": 0.031,
        "relative_deviation_rate": 0.087,
        "hf_energy_ratio": 0.12,
        "consecutive_hit_rate": 1.0,
        "sample_size": 5,
        "z_score_max": -57.41,
        "pearson_corr_with_peer": 0.92
      },
      "local_suggestion": "high_confidence_anomaly"
    }
  ]
}
```

**字段说明**：
- `type`: 异常类型（point/step_down/step_up/trend_change）
- `x_start/x_end`: 异常区间的起止位置
- `y_observed`: 异常起始点的实际观测值
- `y_predicted`: LOESS 模型的预测值
- `z_score`: 标准化残差，绝对值越大表示越异常
- `confidence`: 置信度，基于 z-score 计算
- `message`: 人类可读的异常描述
- `features`: 多维统计特征
- `local_suggestion`: 局部判据建议

### 告警图片说明

生成的告警图片包含以下元素：
- **蓝色圆点**：历史数据点（用于训练 LOESS 模型）
- **红色方块**：新增数据点（被检测的点）
- **绿色实线**：LOESS 拟合曲线（基于历史数据）
- **绿色虚线**：LOESS 预测曲线（外推到新增数据区域）
- **紫色竖线**：历史数据与新增数据的分界线
- **红色阴影**：检测到的异常区间

## 完成后返回

返回 JSON 结构：

```json
{
  "status": "success",
  "experiment_group_sid": "实验组ID",
  "anomalies_detected": 2,
  "notification_sent": true,
  "anomaly_summary": {
    "step_down": 1,
    "point": 1
  },
  "check_time": "2025-02-01T10:00:00Z"
}
```

## 注意事项

- 只关注图表曲线异常检测，不要执行其他任务
- **必须先通过 merlin-cli（search-panel / list-run-entities）与 `fetch_panel_csv.py` 生成 `case.csv`，再执行分析**
- 发送告警前结合告警列表与 `local_suggestion` 复核，避免误报
- 初始阶段（如训练刚开始）数据不稳定，可适当放宽阈值或忽略部分告警
- 区分训练指标和评估指标，两者的异常模式可能不同
- `min_abs_deviation` 参数用于过滤绝对偏差很小的告警，避免对平稳曲线的微小波动产生误报
- **默认使用 CSV 输出格式**，可显著节省 token 消耗（约 40-50%）
- **参考 `local_suggestion` 字段**，但 Agent 可根据上下文覆盖决策