# 查看任务

当用户想查看 HDFS 跨洋传输任务的状态、进度、失败原因、详情或任务列表时，读取本文件。

## 典型触发词

- 查看任务
- 查一下这个同步
- 看状态 / 看进度
- 列出最近的传输任务
- 为什么失败了
- 看下这个任务详情

## 目标

帮助用户查询单个任务或一组任务，并在需要时继续下钻查看单个传输任务下的传输子任务状态、失败原因、目标路径以及对应的 `Tiansuan` / `Zeus` 任务 ID。

## 目录

- [最小必要信息](#最小必要信息)
- [使用的工具](#使用的工具)
- [子任务详情工具](#子任务详情工具)
- [分页规则](#分页规则)
- [时间格式](#时间格式)
- [推荐流程](#推荐流程)
- [推荐命令](#推荐命令)
- [返回结构](#返回结构)
- [输出时重点展示](#输出时重点展示)
- [补问模板](#补问模板)
- [示例回复结构](#示例回复结构)
- [注意事项](#注意事项)

## 最小必要信息

优先需要：

- `task_id`
- 或 `task_id` 列表

如果用户没有 `task_id`，则至少补齐一组可筛选条件：

- `creator`（如果用户没有明确指定别人，默认用当前用户自己）
- 任务创建时间范围
- 状态
- HDFS 源路径

先读取 `references/common-fields.md`，明确字段含义后再补问。

## 使用的工具

查看任务列表或任务概览时，优先使用：

```bash
merlin-cli resource list-applied-governance-job-instances --schema
```

查看单个传输任务下的传输子任务详情时，使用：

```bash
merlin-cli data get-governance-job-instance-progress --schema
```

这个工具支持的核心过滤字段包括：

- `job_instance_id`：单个任务实例 ID
- `job_instance_id_list`：多个任务实例 ID
- `creator`：创建人
- `job_status`：任务状态列表，支持 `WAITING`、`RUNNING`、`SUCCEEDED`、`FAILED`、`STOPPED`
- `trigger_time_from` / `trigger_time_to`：任务创建时间范围，时间格式例如 `"2026-03-13 16:23"`
- `resource_identity`：HDFS 源路径，只支持搜索单个路径
- `resource_type`：资源类型，这里固定为 `hdfs`
- `govern_strategy_type`：治理方式类型，这里固定为 `hdfs_distcp_in_batch`
- `limit` / `offset`：分页参数

这里的 `job_instance_id` 就是本 skill 里说的 `task_id`。

当用户一次提供多个 `task_id` 时，使用 `job_instance_id_list` 做批量查询。

当用户想按 HDFS 源路径筛选时，优先把该条件映射到 `resource_identity`。

如果使用 HDFS 源路径筛选，只传单个路径，不要一次传多个路径。

`tiansuan_task_id` 和 `zeus_task_id` 不是这个工具的直接过滤字段。用户如果提供的是这两类 ID，先说明需要额外做一次映射或补充 `task_id`，不要假设它们可以直接代替 `job_instance_id`。

如果没有出现在上述说明里的 key，默认不需要传。

## 子任务详情工具

当用户想看以下信息时，不要只停留在任务列表接口，要继续调用 `merlin-cli data get-governance-job-instance-progress`：

- 单个传输任务下各个传输子任务的状态
- 某个传输子任务为什么失败
- 传输子任务对应的目标 HDFS 路径和目标机房
- `tiansuan_task_id`
- `zeus_task_id`
- 传输子任务传输了多少数据、还剩多久

这个工具的输入参数很简单：

- `job_instance_id`：任务 ID，必需
- `resource_type`：固定传 `hdfs`

推荐命令：

```bash
merlin-cli data get-governance-job-instance-progress --json '{
    "job_instance_id":"<task_id>",
    "resource_type":"hdfs"
  }'
```

返回结构里，重点关注：

- `hdfs_distcp_in_batch_job_instance_progress_detail.items`
- `source_hdfs_path_list`：该子任务的 HDFS 源路径列表
- `items`：该子任务下按目标路径拆开的更细粒度传输子任务列表

每个传输子任务里，优先关注这些字段：

- `target_hdfs_path`：目标 HDFS 路径
- `target_dc`：目标机房
- `status`：传输子任务状态，仅包含 `RUNNING`、`SUCCEEDED`、`FAILED`、`STOPPED`
- `progress`：传输子任务进度，例如 `75.75%`
- `failed_reason`：失败原因，传输子任务失败时可能返回
- `zeus_job_id`：Zeus 任务 ID
- `tiansuan_job_id`：Tiansuan 任务 ID
- `transport_physical_size`：已传输 / 总需传输数据量
- `estimated_remaining_time`：预估剩余时间，运行中任务可能返回

## 分页规则

使用筛选条件列任务时，一定要带分页参数：

- 默认 `limit=20`
- 用户可以显式指定修改 `limit`
- `limit` 不能超过 `100`
- 分页翻页时使用 `offset`

如果用户没有特别说明，先返回第一页结果，再问是否继续翻页。

## 时间格式

`trigger_time_from` 和 `trigger_time_to` 使用 `YYYY-MM-DD HH:mm` 格式，例如：

- `"2026-03-13 16:23"`

如果用户给的是自然语言时间，比如“昨天晚上”或“上周一下午”，先帮他换算成明确时间范围再查询。

## 推荐流程

1. 判断用户是要查单个任务，还是列一批候选任务
2. 如果有 `task_id`，用 `job_instance_id` 精确查询单任务
3. 如果有多个 `task_id`，用 `job_instance_id_list` 批量查询，并按用户给定顺序或统一表格整理结果
4. 如果没有 `task_id`，优先组合 `creator`、`job_status`、`trigger_time_from`、`trigger_time_to` 和 HDFS 源路径对应的 `resource_identity` 列任务
5. 如果用户没有明确指定别人，默认把 `creator` 设为当前用户自己
6. 查询列表时默认 `limit=20`，除非用户指定更小或更大的页大小；任何情况下都不要超过 `100`
7. 提炼关键结果：`task_id`、状态、HDFS 源路径列表、同步进度（`finished_task_count` / `total_task_count`）、任务创建人、任务创建时间，以及是否需要进一步排查
8. 如果用户继续追问失败原因、目标路径、传输子任务状态、`tiansuan_task_id` 或 `zeus_task_id`，再用 `merlin-cli data get-governance-job-instance-progress` 下钻查看单个任务的传输子任务详情
9. 如果结果异常，再建议下一步动作，如停止、重试或继续排查

## 推荐命令

查询单个任务：

```bash
merlin-cli resource list-applied-governance-job-instances --json '{
    "resource_type":"hdfs",
    "govern_strategy_type":["hdfs_distcp_in_batch"],
    "job_instance_id":"<task_id>"
  }'
```

批量查询多个任务：

```bash
merlin-cli resource list-applied-governance-job-instances --json '{
    "resource_type":"hdfs",
    "govern_strategy_type":["hdfs_distcp_in_batch"],
    "job_instance_id_list":["<task_id_1>","<task_id_2>","<task_id_3>"]
  }'
```

按创建人、状态、时间范围列任务：

```bash
merlin-cli resource list-applied-governance-job-instances --json '{
    "resource_type":"hdfs",
    "govern_strategy_type":["hdfs_distcp_in_batch"],
    "creator":"<current_user>",
    "job_status":["WAITING","RUNNING","SUCCEEDED","FAILED","STOPPED"],
    "trigger_time_from":"2026-03-13 16:23",
    "trigger_time_to":"2026-03-14 16:23",
    "resource_identity":"<hdfs_source_path>",
    "limit":20,
    "offset":0
  }'
```

如果只想看参数 schema：

```bash
merlin-cli resource list-applied-governance-job-instances --schema
```

查询单个任务下的传输子任务详情：

```bash
merlin-cli data get-governance-job-instance-progress --json '{
    "job_instance_id":"<task_id>",
    "resource_type":"hdfs"
  }'
```

## 返回结构

工具返回结果主要包含两部分：

- `count`：符合条件的任务总数，可用于分页
- `job_instances`：任务列表

单个 `job_instance` 中，只需要关注这些字段：

- `job_instance_id`：任务 ID
- `status`：任务状态
- `applied_resource_identity`：HDFS 源路径列表
- `strategy_conf.hdfs_distcp_in_batch_conf.distcp_confs`：每个传输子任务的源路径 / 目标路径配置
- `creator`：任务创建人
- `created_at`：任务创建时间，格式类似 `"2026-01-29T12:52:06Z"`
- `progress.total_task_count`：总子任务数
- `progress.finished_task_count`：已完成子任务数

如果用户关心“同步进度”，优先从 `progress.finished_task_count` 和 `progress.total_task_count` 计算和描述。

如果用户关心“传输子任务详情”，继续看 `merlin-cli data get-governance-job-instance-progress` 的返回：

- `source_hdfs_path_list`：这个子任务分组对应的源路径
- `items[].target_hdfs_path`：每个传输子任务的目标路径
- `items[].target_dc`：每个传输子任务的目标机房
- `items[].status`：传输子任务状态
- `items[].progress`：传输子任务进度
- `items[].failed_reason`：失败原因
- `items[].zeus_job_id` / `items[].tiansuan_job_id`：底层任务 ID
- `items[].transport_physical_size`：传输数据量
- `items[].estimated_remaining_time`：预估剩余时间

## 输出时重点展示

不管是单任务还是多任务，都优先用 Markdown 表格展示以下信息：

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| `<job_instance_id>` | `<status>` | `<finished_task_count>/<total_task_count>` | `[hdfs://foo/bar]` | `<created_at>` | `<creator>` |

字段映射关系：

- 任务 ID 对应返回里的 `job_instance_id`
- 当前状态对应返回里的 `status`
- 同步进度优先展示为 `finished_task_count/total_task_count`
- HDFS 源路径列表对应返回里的 `applied_resource_identity`
- 任务创建时间对应返回里的 `created_at`
- 任务创建人对应返回里的 `creator`

如果用户还想看失败原因、目标路径或更细的子任务配置，再在表格之后补充说明，不要把这些信息混进主表格里。

如果用户明确要看单个传输任务下的传输子任务详情，表格之后再追加一个“传输子任务详情”表格，建议展示这些列：

| HDFS 源路径列表 | HDFS 目标路径 | 目标机房 | 传输子任务状态 | 传输子任务进度 | Tiansuan 任务 ID | Zeus 任务 ID | 传输数据量 | 预估剩余时间 | 失败原因 |
|------|------|------|------|------|------|------|------|------|------|
| `[hdfs://foo/bar]` | `hdfs://target/path` | `cn` | `RUNNING` | `75.75%` | `distcp-xxx` | `9234` | `750.8 GB / 991.1 GB` | `20m7s` | `` |

如果字段缺失，比如失败任务没有 `zeus_job_id`，就留空，不要猜值。

## 补问模板

- 请提供任务 ID，我直接帮你查详情
- 如果你要一次查多个任务，请直接给我 `task_id` 列表，我会批量查询
- 如果没有任务 ID，请给我任务创建时间范围、状态和 HDFS 源路径；如果你没有特别指定别人，我默认按你自己创建的任务来筛
- 时间范围请尽量按 `YYYY-MM-DD HH:mm` 提供，例如 `2026-03-13 16:23`
- 状态只支持这些大写值：`WAITING`、`RUNNING`、`SUCCEEDED`、`FAILED`、`STOPPED`
- 如果你手上只有 `tiansuan_task_id` 或 `zeus_task_id`，请先补充对应的 `task_id`，或者告诉我我先帮你做映射
- 如果你要看某个传输任务下的传输子任务状态、失败原因或 `Tiansuan/Zeus` 任务 ID，请直接给我这个 `task_id`
- 默认每页返回 20 条；如果你想改页大小可以告诉我，但单页最多只能查 100 条
- 你是想看状态进度，还是想看失败原因和报错详情

## 示例回复结构

```text
操作类型：查看任务
已识别信息：task-123
缺失信息：无
执行结果：
| task_id | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | RUNNING | 1/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
下一步：如果你需要，我可以继续帮你筛同时间段任务，或进一步看失败重试条件
```

批量查询示例：

```text
操作类型：查看任务
已识别信息：task-123、task-456、task-789
缺失信息：无
执行结果：
| task_id | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | RUNNING | 1/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
| task-456 | RUNNING | 2/2 | [hdfs://foo/baz] | 2026-01-29T13:10:00Z | alice |
| task-789 | FAILED | 1/2 | [hdfs://foo/qux] | 2026-01-29T13:25:00Z | alice |
下一步：如果你需要，我可以继续展开失败任务的详细信息，或帮你判断是否适合重试
```

查看单个任务下传输子任务详情的示例：

```text
操作类型：查看任务
已识别信息：task-123
缺失信息：无
执行结果：
| task_id | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | RUNNING | 1/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |

传输子任务详情：
| HDFS 源路径列表 | HDFS 目标路径 | 目标机房 | 传输子任务状态 | 传输子任务进度 | Tiansuan 任务 ID | Zeus 任务 ID | 传输数据量 | 预估剩余时间 | 失败原因 |
|------|------|------|------|------|------|------|------|------|------|
| [hdfs://foo/bar] | hdfs://target/path-a | cn | FAILED | 0.00% |  |  |  |  | some error message |
| [hdfs://foo/bar] | hdfs://target/path-b | my | RUNNING | 75.75% | distcp-d85f9fa9d24145b5 | 9234 | 750.8 GB / 991.1 GB | 20m7s |  |
```

## 注意事项

- 没有唯一标识时，不要擅自把某条候选任务当成目标任务
- 看到多个候选任务时，先列给用户确认
- `task_id` 在工具参数里对应 `job_instance_id`
- 多个 `task_id` 查询时使用 `job_instance_id_list`
- HDFS 源路径筛选优先映射到 `resource_identity`
- `resource_identity` 只支持单个 HDFS 源路径
- `resource_type` 固定传 `hdfs`
- `govern_strategy_type` 固定传 `hdfs_distcp_in_batch`
- 查看传输子任务详情时使用 `merlin-cli data get-governance-job-instance-progress`
- 传输子任务详情查询只支持单个 `task_id`
- 传输子任务状态只包含 `RUNNING`、`SUCCEEDED`、`FAILED`、`STOPPED`
- 时间范围字段 `trigger_time_from` / `trigger_time_to` 使用 `YYYY-MM-DD HH:mm` 格式
- 返回结果里的总数在 `count`，任务列表在 `job_instances`
- 状态值使用大写枚举：`WAITING`、`RUNNING`、`SUCCEEDED`、`FAILED`、`STOPPED`
- 不要把 `tiansuan_task_id` 或 `zeus_task_id` 直接当成 `job_instance_id`
- 列任务时默认 `limit=20`，且不要超过 `100`
- 不要只贴原始 JSON，优先做状态摘要和异常解释
