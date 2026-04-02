---
name: companion-eval
description: 管理和监控 merlin, seed 训练任务的伴生评估（Companion Evaluation）：查询伴生任务、复制伴生任务、从零创建伴生评估（绑定 Checkpoint）、获取评估结果并创建 Insight 分析。当用户说"伴生评估/companion job/查看伴生任务/创建伴生评估/复制伴生任务/Checkpoint 评估结果/Auto Evaluation"时使用。
---

# 伴生评估管理

管理 Merlin 训练任务的伴生评估（Companion Evaluation），覆盖查询、复制、从零创建、监控结果与 Insight 分析。

## 前置条件

- `merlin-cli` 可用
- 知道训练任务的 `job_run_id` 或伴生任务的 sid

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

---

## 1. 查询伴生评估任务

获取训练任务关联的伴生评估列表：

```bash
merlin-cli eval get-companion-job --json '{"job_run_id": "<job_run_id>"}'
```

返回包含：`step`（Checkpoint 步数）、`evaluation_sid`、`collection_sids`、`status`（DONE/FAILED 等）。

---

## 2. 复制伴生评估任务

基于现有伴生任务复制到新 HDFS 目录：

```bash
merlin-cli eval create-companion-job-fork --json '{
  "companion_job_id": "sid123",
  "target_dir_path": "hdfs://path/to/dir",
  "fork_name": "my-new-eval"
}'
```

**注意**：目标 HDFS 目录必须存在；不指定新名称可能因名称重复而失败。

---

## 3. 从零创建伴生评估

当基于基线任务派生新训练任务后，需要为新任务创建伴生评估。典型流程：

1. 通过 `merlin-cli eval get-companion-job` 获取基线训练任务的伴生评估配置
2. 通过 `merlin-cli checkpoint get` 并设置 `wait_until_creation=true`，等待新训练任务的 HDFS checkpoint 卡片创建完成
3. 从返回结果提取 `result.hdfs_ckpt_dir.path`（对应 `output_dir_path`）和 `result.hdfs_ckpt_dir.hash`（对应 `target_dir_hash`）
4. 创建伴生评估：

```bash
merlin-cli eval create-companion-job --json '{
  "job_run_id": "<new_job_run_id>",
  "output_dir_path": "<hdfs_ckpt_dir_path>",
  "target_dir_hash": "<hdfs_ckpt_dir_hash>",
  ...基线伴生任务的其他配置...
}'
```

创建前建议调用 `job-resource` 技能选择合适的集群与队列。

---

## 4. 监控评估结果与 Insight 分析

获取评估完成的 Checkpoint 结果并创建 Insight 进行深度分析。

### 获取评估结果

```bash
merlin-cli eval get-companion-job --json '{"job_run_id": "<job_run_id>"}'
```

从返回中筛选 `status=DONE` 的条目，提取 `evaluation_sid` 和 `collection_sids`。

### 创建 Insight

```bash
merlin-cli insight create --json '{
  "name": "Job_<job_id>_Step<step>_Analysis",
  "evaluation_sids": {"cn": ["<evaluation_sid>"]},
  "collection_sids": [{"collection_sid": "<col_sid>", "collection_version_sid": "<ver_sid>"}]
}'
```

region 选择：国内用 `cn`，海外用 `sg`。

### 调用 insight 技能分析

创建 Insight 后，调用 `insight` 技能进行能力分析和显著性对比。

---

## 注意事项

- `evaluation_sid` 和 `collection_sids` 来自伴生评估列表的返回结果
- 创建 Insight 时 region key 需匹配环境（cn 或 sg）
- 同一 step 的评估已处理过则跳过（去重）
- 必须先 `insight create` 获取 `insight_sid`，再调用 `insight` 技能分析

---

## 关联技能

- `insight`：Insight 深度分析（能力分析、显著性、案例查询）
- `job-launch`：创建并启动训练任务
- `job-resource`：选择合适的资源配置
- `checkpoint-query`：查询 Checkpoint 卡片信息
