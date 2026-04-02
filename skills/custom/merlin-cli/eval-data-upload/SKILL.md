---
name: eval-data-upload
description: 上传评估数据集到 Seed 平台。当需要将 HDFS 上的数据文件（parquet/json/csv）作为评估集上传到 Seed DataCard 时使用。触发词：上传评估数据、upload eval data、data upload、评估集上传、DataCard 上传、parquet 上传、数据集导入、HDFS 数据上传、导入评估数据、注册评估集、导入数据到 Seed、新建 DataCard、创建数据表。即使用户没有明确说"上传"，只要涉及将数据文件注册到 Seed 平台作为评估集或 DataCard，都应使用本 skill。注意：本 skill 仅处理 HDFS 数据源，本地文件需先通过 `hdfs dfs -put` 上传到 HDFS。
---

# 评估数据集上传

通过 `merlin-cli data upload` 将 HDFS 上的数据文件上传为 Seed 平台的评估集 DataCard。

## 前置条件

- 数据文件已在 HDFS 上（本地文件需先通过 `hdfs dfs -put` 上传）
- `merlin-cli` 已安装并完成认证：

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果遇到 401/403 认证错误，运行 `merlin-cli login` 重新登录。

## 上传命令

```bash
merlin-cli data upload --json '{
  "database_name": "<库名>",
  "table_name": "<表名>",
  "file_config": {
    "hdfs_path": "hdfs://haruna/home/byte_data_seed/<你的路径>",
    "hdfs_file_format": "parquet"
  },
  "write_mode": "create",
  "datacard_dataset_type": "eval"
}'
```

参数较多时也可以写到文件里：

```bash
merlin-cli data upload --from-file upload_params.json
```

### 必须由用户提供的参数（禁止猜测）

| 参数 | 说明 | 为什么不能猜 |
|------|------|------------|
| `database_name` | Seed 上的库名 | 每个团队/项目的库名不同 |
| `table_name` | Seed 上的表名 | 表名由用户决定，写错会创建错误的表 |
| `file_config.hdfs_path` | HDFS 数据路径 | 路径因用户和场景而异 |
| `write_mode` | 当用户要用 `overwrite` 时必须确认 | `overwrite` 会**清空已有数据**再写入，属于破坏性操作 |

### 关键参数

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `datacard_dataset_type` | 数据集类型。设为 `"eval"` 后 DataCard 才会出现在 Seed 评估界面，也才能关联到 Exercise | `train`, `eval`, `normal` | - |
| `write_mode` | 写入模式。首次创建表用 `create`，后续更新用 `append` 或 `overwrite` | `create`, `overwrite`, `append` | `append` |
| `hdfs_file_format` | 文件格式 | `parquet`, `json`, `csv`, `eval_image_tar`, `vlm_video`, `multi_modal` | `parquet` |
| `datacard_dataset_modal` | 数据模态 | `TEXT`, `VISION`, `VIDEO`, `SPEECH`, `MULTIMODAL` | - |
| `catalog` | 数据目录 | - | `seed` |
| `target_branch` | Iceberg 表分支 | - | `main` |
| `wait` | 设为 `true` 则阻塞等待任务完成 | `true`, `false` | `false` |
| `resource` | 自定义资源队列配置（见下方说明）。不传则使用公共资源池 | object | 公共资源池 |

### 自定义资源队列（resource）

> **⚠️ 使用自定义资源需要用户确认**：`resource` 涉及团队资源配额，agent 不得自行填写。必须向用户确认具体的资源组（`group_id`）和集群（`cluster_id`）后再传入。如果用户没有主动指定资源，一律使用公共资源池（不传 `resource`）。

默认情况下上传任务使用公共资源池，无需传 `resource`。当用户明确要求使用自定义资源时，结构如下：

```json
"resource": {
  "group_id": 12345,
  "cluster_id": 67890,
  "quota_pool": "default"
}
```

| 字段 | 说明 | 必填 |
|------|------|------|
| `group_id` | 资源组 ID | 是 |
| `cluster_id` | 集群 ID | 是 |
| `quota_pool` | 资源池类型（`default`、`hybrid`、`hybrid_share`、`third_party`） | 否 |
| `group_name` | 资源组名称（仅标识用途） | 否 |
| `cluster_name` | 集群名称（仅标识用途） | 否 |

用户可以在 Merlin 平台的资源管理页面查看自己有权限的资源组和集群 ID。

查看完整参数 schema：

```bash
merlin-cli data upload --schema
```

## 等待任务完成

**方式一**：在上传参数中加 `"wait": true`，命令会阻塞直到任务结束。

**方式二**：手动轮询任务状态：

```bash
# 查询单个上传任务状态
merlin-cli data get-job --json '{"sid": "<上传返回的 sid>"}'

# 列出所有上传任务
merlin-cli data list-jobs --json '{}'
```

状态流转：`LAUNCHING` → `STARTED` → `RUNNING` → `DONE`（成功）或 `FAILED`（失败）。

上传任务通常耗时 5-20 分钟，视数据量而定。使用 `wait: true` 时应预留足够等待时间，不要因为等待较长而判断为异常。

## 完整示例

将 HDFS 上的 parquet 文件作为评估集上传：

```bash
# 1. 上传评估数据集（阻塞等待完成）
merlin-cli data upload --json '{
  "database_name": "<your_database>",
  "table_name": "<your_table>",
  "file_config": {
    "hdfs_path": "hdfs://haruna/home/byte_data_seed/<your_path>",
    "hdfs_file_format": "parquet"
  },
  "write_mode": "create",
  "datacard_dataset_type": "eval",
  "wait": true
}'

# 2. 查看 DataCard
# https://seed.bytedance.net/seed/data/warehouse/seed.<database_name>.<table_name>
```

## 解读上传结果

上传完成后（`wait: true` 或手动查询），返回的 JSON 中关键字段：

| 字段 | 说明 |
|------|------|
| `sid` | 任务 ID，用于后续查询 |
| `status` | 最终状态，`DONE` 表示成功 |
| `full_table_name` | 完整表名（如 `seed.test.mmlu_dev`），用于拼接 DataCard URL |
| `merlin_job_id_url` | Merlin 任务详情页链接，上传失败时可直接分享给用户排查 |

向用户展示结果时，重点呈现：DataCard URL 和任务状态。失败时附上 `merlin_job_id_url`。

## DataCard 地址

上传完成后，DataCard 详情页地址为：

```
https://seed.bytedance.net/seed/data/warehouse/seed.<database_name>.<table_name>
```

## 常见问题

| 现象 | 原因和处理 |
|------|-----------|
| 任务状态 `FAILED` | 查看任务详情 `merlin-cli data get-job --json '{"sid": "..."}'`，检查错误信息；常见原因：HDFS 路径不存在、文件格式不匹配 |
| `write_mode: create` 报错表已存在 | 该表已被创建过，改用 `overwrite`（清空重写）或 `append`（追加数据） |
| 401 / 403 认证错误 | 运行 `merlin-cli login` 重新登录 |
| `AccessResourceDenied` | 没有目标库/表的写权限，联系管理员授权 |

更多排查参考：[导入失败错误排查手册](https://bytedance.larkoffice.com/wiki/JexdwRKaliJByFk4HyecleHUnBe)

## 相关 Skills

- **下一步**: `eval-exercise-create` — 从 DataCard 创建 Exercise
