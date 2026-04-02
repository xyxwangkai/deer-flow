# 重试任务

当用户想对失败、中断或需要重新执行的 HDFS 跨洋传输任务做重试时，读取本文件。

## 典型触发词

- 重试这个任务
- 重新传一下
- 失败了再跑一次
- 重跑这个同步
- 按原配置重新发起

## 目标

帮助用户安全地重试一个或多个已有 HDFS 传输任务，并在重试后通过 `references/query.md` 再次查询任务状态，确认是否已经重新进入执行流程。

## 最小必要信息

必须优先确认：

- `task_id`
- 或 `task_id` 列表

如果用户没有 `task_id`，则至少需要一组可唯一定位历史任务的条件，例如：

- 创建人
- 时间范围
- 源路径和目标路径
- 失败状态或失败时间

先读取 `references/common-fields.md`，统一字段和风险确认规则。

## 使用的工具

重试任务时，使用 `merlin-cli resource batch-retry-governance-instances`。

这个工具的输入参数：

- `resource_type`：固定传 `hdfs`
- `instance_ids`：要重试的任务 ID 列表

这是一个批量重试工具。即使只重试一个任务，也按批量格式传 `instance_ids`；如果用户一次给了多个 `task_id`，优先一次性批量重试。

单任务示例：

```bash
merlin-cli resource batch-retry-governance-instances --json '{
    "resource_type":"hdfs",
    "instance_ids":["<task_id>"]
  }'
```

批量重试示例：

```bash
merlin-cli resource batch-retry-governance-instances --json '{
    "resource_type":"hdfs",
    "instance_ids":["<task_id_1>","<task_id_2>"]
  }'
```

注意：

- 即使只重试一个任务，也用 `instance_ids` 列表传入
- 如果用户一次提供多个 `task_id`，尽量一次性批量重试，不要拆成多次调用
- 这个工具没有可依赖的输出字段，因此不能只看重试命令本身是否执行成功
- 重试之后必须继续用 `references/query.md` 的查询流程再次确认任务状态

## 权限限制

只能重试创建人为当前用户自己的传输任务。

这意味着在真正重试前，必须先通过 `references/query.md` 查询目标任务，确认：

- `creator` 等于当前用户自己

如果查询结果显示任务创建人不是当前用户自己，不要继续重试，直接告诉用户当前无权重试该任务。

## 批量重试场景

当用户明确说：

- “把这几个任务都重试一下”
- “批量重跑这些同步”
- “把失败的几个任务一起重试”

优先按批量重试处理。

如果用户没有直接给出多个 `task_id`，而是给了一组候选条件，先通过 `references/query.md` 查出候选任务，再把待重试任务按 Markdown 表格展示给用户确认，确认后一次性批量重试。

## 推荐流程

1. 先确认用户是要“重试旧任务”，不是单纯“查看失败原因”
2. 获取一个或多个 `task_id`
3. 如果用户给的是筛选条件而不是 `task_id`，先通过 `references/query.md` 查出候选任务
4. 先通过 `references/query.md` 查询当前状态和创建人，判断这些任务是否适合重试
5. 把最终待重试的任务按 Markdown 表格整理出来，发给用户做二次确认
6. 调用 `merlin-cli resource batch-retry-governance-instances`
7. 重试后再次通过 `references/query.md` 查询这些任务，确认状态是否重新进入执行流程
8. 向用户返回重试结果和最新查询结果

## 二次确认原则

在真正重试前，先按 `references/query.md` 的主任务表格格式展示待重试任务，让用户核对后再继续。

推荐表格格式：

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| `<job_instance_id>` | `<status>` | `<finished_task_count>/<total_task_count>` | `[hdfs://foo/bar]` | `<created_at>` | `<creator>` |

以下情况建议再次确认：

- 一次要重试多个任务
- 候选任务里混有不是用户真正想重试的任务
- 当前状态看起来不像失败或中断任务
- 用户只说“重试一下”，但没有明确是按原任务直接重试
- 候选任务里混有非当前用户创建的任务

确认话术可以简短直接，例如：

- 请先核对下面这张任务表，确认这些任务都需要重试；我会按这份列表一次性提交重试请求
- 这些任务里如果有你不想重试的，请先告诉我移除哪些 `task_id`

## 执行结果要告诉用户什么

至少包含：

- 本次实际重试的任务 ID 或任务 ID 列表
- 对应的任务列表 Markdown 表格

推荐表格格式：

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| `<job_instance_id>` | `<status>` | `<finished_task_count>/<total_task_count>` | `[hdfs://foo/bar]` | `<created_at>` | `<creator>` |

示例回复结构：

```text
操作类型：重试任务
已识别信息：task-123
缺失信息：无
执行结果：
本次已重试的任务 ID：task-123

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | RUNNING | 0/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
```

批量重试示例：

```text
操作类型：重试任务
已识别信息：task-123、task-456
缺失信息：无
执行结果：
本次已重试的任务 ID：task-123、task-456

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | RUNNING | 0/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
| task-456 | WAITING | 0/1 | [hdfs://foo/baz] | 2026-01-29T13:10:00Z | alice |
```

## 注意事项

- 没有 `task_id` 时不要直接重试
- 这个工具没有输出字段，重试后一定要再走一次 `references/query.md` 查询确认结果
- 只有 `creator` 为当前用户自己的任务才能重试
- 如果候选任务里混有他人创建的任务，先过滤掉或明确提示用户无权重试
- 批量重试时，先把待重试的任务列表发给用户确认
- 批量重试时优先一次性提交，不要无必要拆成多次重试请求
- 二次确认时优先展示和 `references/query.md` 一致的 Markdown 表格，而不只是列出 `task_id`
- 不要默认“重试”一定等于“原配置重发”
- 如果原任务其实仍在运行，不要把它当成失败任务直接重试
