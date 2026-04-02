# 停止任务

当用户想停止、取消或终止一个或多个 HDFS 跨洋传输任务时，读取本文件。

## 典型触发词

- 停止传输
- 取消同步
- 终止这个任务
- 停掉这条跨洋迁移
- kill 这个同步

## 目标

帮助用户安全地停止一个或多个已有 HDFS 传输任务，并在停止后通过 `references/query.md` 再次查询任务状态，确认是否真的停掉。

## 最小必要信息

必须优先确认：

- `task_id`
- 或 `task_id` 列表

如果用户没有 `task_id`，先查出候选任务并让用户确认，不能直接停。

先读取 `references/common-fields.md`，尤其关注高风险动作的确认要求。

## 使用的工具

停止任务时，使用 `merlin-cli resource batch-stop-governance-instances`。

这个工具的输入参数：

- `resource_type`：固定传 `hdfs`
- `instance_ids`：要停止的任务 ID 列表

这是一个批量停止工具。即使只停一个任务，也按批量格式传 `instance_ids`；如果用户一次给了多个 `task_id`，优先一次性批量停止。

单任务示例：

```bash
merlin-cli resource batch-stop-governance-instances --json '{
    "resource_type":"hdfs",
    "instance_ids":["<task_id>"]
  }'
```

批量停止示例：

```bash
merlin-cli resource batch-stop-governance-instances --json '{
    "resource_type":"hdfs",
    "instance_ids":["<task_id_1>","<task_id_2>"]
  }'
```

注意：

- 即使只停一个任务，也用 `instance_ids` 列表传入
- 如果用户一次提供多个 `task_id`，尽量一次性批量停止，不要拆成多次调用
- 这个工具没有可依赖的输出字段，因此不能只看停止命令本身是否执行成功
- 停止之后必须继续用 `references/query.md` 的查询流程再次确认任务状态

## 权限限制

只能停止创建人为当前用户自己的传输任务。

这意味着在真正停止前，必须先通过 `references/query.md` 查询目标任务，确认：

- `creator` 等于当前用户自己

如果查询结果显示任务创建人不是当前用户自己，不要继续停止，直接告诉用户当前无权停止该任务。

## 批量停止场景

当用户明确说：

- “把这几个任务都停掉”
- “批量停止这些同步”
- “把今天失败前还在跑的几个任务一起停掉”

优先按批量停止处理。

如果用户没有直接给出多个 `task_id`，而是给了一组候选条件，先通过 `references/query.md` 查出候选任务，再把待停止任务按 Markdown 表格展示给用户确认，确认后一次性批量停止。

## 推荐流程

1. 确认用户确实要“停止任务”而不是“查看任务”
2. 获取一个或多个 `task_id`
3. 如果用户给的是筛选条件而不是 `task_id`，先通过 `references/query.md` 查出候选任务
4. 先通过 `references/query.md` 查询当前状态和创建人，判断这些任务是否可停止
5. 把最终待停止的任务按 Markdown 表格整理出来，发给用户做二次确认，尤其是运行中任务或批量停止场景
6. 调用 `merlin-cli resource batch-stop-governance-instances`
7. 停止后再次通过 `references/query.md` 查询这些任务，确认状态是否变为 `STOPPED`
8. 向用户返回停止结果和最新查询结果

## 二次确认原则

在真正停止前，先按 `references/query.md` 的主任务表格格式展示待停止任务，让用户核对后再继续。

推荐表格格式：

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| `<job_instance_id>` | `<status>` | `<finished_task_count>/<total_task_count>` | `[hdfs://foo/bar]` | `<created_at>` | `<creator>` |

以下情况建议再次确认：

- 任务处于 `RUNNING`
- 任务影响线上业务或大批量数据
- 同时存在多个名字相似的候选任务
- 一次要停止多个任务
- 候选任务里混有非当前用户创建的任务

确认话术要简短直接，例如：

- 请先核对下面这张任务表，确认这些任务都需要停止；我会按这份列表一次性提交停止请求
- 该任务当前正在运行，停止后本次传输会中断，确认是否继续
- 这些任务里如果有你不想停止的，请先告诉我移除哪些 `task_id`

## 执行结果要告诉用户什么

至少包含：

- 本次实际停止的任务 ID 或任务 ID 列表
- 对应的任务列表 Markdown 表格

推荐表格格式：

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| `<job_instance_id>` | `<status>` | `<finished_task_count>/<total_task_count>` | `[hdfs://foo/bar]` | `<created_at>` | `<creator>` |

示例回复结构：

```text
操作类型：停止任务
已识别信息：task-123
缺失信息：无
执行结果：
本次已停止的任务 ID：task-123

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | STOPPED | 1/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
```

批量停止示例：

```text
操作类型：停止任务
已识别信息：task-123、task-456
缺失信息：无
执行结果：
本次已停止的任务 ID：task-123、task-456

| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | STOPPED | 1/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |
| task-456 | STOPPED | 0/1 | [hdfs://foo/baz] | 2026-01-29T13:10:00Z | alice |
```

## 注意事项

- 没有 `task_id` 时不要直接停止
- 对已经完成或已经失败的任务，先说明“无需停止”或“不可停止”
- 这个工具没有输出字段，停止后一定要再走一次 `references/query.md` 查询确认结果
- 只有 `creator` 为当前用户自己的任务才能停止
- 如果候选任务里混有他人创建的任务，先过滤掉或明确提示用户无权停止
- 批量停止时，先把待停止的 `task_id` 列表发给用户确认
- 二次确认时优先展示和 `references/query.md` 一致的 Markdown 表格，而不只是列出 `task_id`
- 批量停止时优先一次性提交，不要无必要拆成多次停止请求
- 不要把“停止”误解成“重试”或“删除任务记录”
