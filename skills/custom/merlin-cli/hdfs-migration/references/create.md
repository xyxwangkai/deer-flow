# 发起任务

当用户想新建一条 HDFS 跨洋传输或数据同步任务时，读取本文件。

## 典型触发词

- 发起传输
- 创建同步任务
- 把 A 传到 B
- 同步一份数据到海外
- 新建跨洋迁移
- 拉起一个 HDFS 传输任务

## 目标

帮助用户创建一条新的 HDFS 到 HDFS 传输任务，并返回任务 ID、初始状态和后续查看方式。

实际发起任务时，使用的命令是 `merlin-cli resource batch-data-migration`。

## 目录

- [最小必要信息](#最小必要信息)
- [发起前必须先查配置](#发起前必须先查配置)
- [常见交互场景](#常见交互场景)
- [发起任务使用的工具](#发起任务使用的工具)
- [推荐流程](#推荐流程)
- [配置查询示例](#配置查询示例)
- [发起命令示例](#发起命令示例)
- [返回结构](#返回结构)
- [补问模板](#补问模板)
- [执行结果要告诉用户什么](#执行结果要告诉用户什么)
- [注意事项](#注意事项)

## 最小必要信息

必须先确认以下字段，禁止猜测：

- `source_path`
- `target_path`

以下字段如未提供，可在必要时继续确认：

- `target_dc`（非必需，优先通过 `target_path` 和配置推断；只有推断不出来时再补问）
- `yarn_resource`（非必需；只有用户明确指定 Yarn 集群和队列时才传）

先读取 `references/common-fields.md`，用统一术语与用户对齐字段含义。

## 发起前必须先查配置

在真正发起同步任务之前，先调用 `merlin-cli batch get-data-migration-config`，获取当前允许的：

- HDFS 源路径前缀
- 目标机房列表
- 每个目标机房允许的 HDFS 目标路径前缀

这个工具不需要输入参数：

```bash
merlin-cli batch get-data-migration-config --json '{}'
```

返回结果里，只需要关注这些字段：

- `supported_prefix_for_source_path`：允许的 HDFS 源路径前缀列表
- `supported_target_dcs`：支持的目标机房列表
- `supported_prefix_by_dc`：每个目标机房允许的 HDFS 目标路径前缀列表

校验规则：

- `source_path` 必须以 `supported_prefix_for_source_path` 中的某个前缀开头
- `target_path` 必须命中某个目标机房对应的允许前缀
- 如果用户没有提供 `target_dc`，优先根据 `supported_prefix_by_dc` 和 `target_path` 反推 `target_dc`
- 如果 `target_path` 只能命中一个目标机房的前缀，就直接使用该 `target_dc`
- 如果 `target_path` 无法命中任何目标机房前缀，或同时命中多个目标机房前缀，不要继续发起，先让用户确认
- 如果用户提供了 `target_dc`，则还要继续校验它是否在 `supported_target_dcs` 中，且 `target_path` 是否命中 `supported_prefix_by_dc[target_dc]` 中的某个前缀

如果上述任一条件不满足，不要继续发起任务，先告诉用户哪一项不合法，并让用户调整机房或路径。

## 常见交互场景

### 只给了目标机房，没给目标路径

如果用户只说“把 xxx 同步到某个机房”，但没有给完整的 `target_path`，不要直接发起。

先读取 `merlin-cli batch get-data-migration-config` 的返回，并根据用户给的 `target_dc`，把该机房允许的目标路径前缀告诉用户，让用户补充完整的 `target_path`。

例如可以这样问：

- 你给了目标机房 `dallas`，但还没有给完整的目标路径。这个机房只允许使用这些前缀下的路径：`<supported_prefix_by_dc[target_dc]>`。请补充完整的 `target_path`。

如果用户连 `target_dc` 也没给，只给了“同步到海外”这类模糊表述，就先让用户补充完整的 `target_path`，或者至少先确认目标机房。

### 源 / 目标 路径对很多

如果要传输的源 / 目标 路径对很多，不要要求用户一条一条口述。优先让用户用结构化方式一次性提供。

推荐用户直接用 Markdown 表格提供，格式如下：

```text
| source_path | target_path | target_dc |
|------|------|------|
| hdfs://source/a | hdfs://target/a | dallas |
| hdfs://source/b | hdfs://target/b | my |
```

如果用户不方便用表格，也可以让他按 JSON 列表提供：

```json
[
  {
    "source_path": "hdfs://source/a",
    "target_path": "hdfs://target/a",
    "target_dc": "dallas"
  },
  {
    "source_path": "hdfs://source/b",
    "target_path": "hdfs://target/b",
    "target_dc": "my"
  }
]
```

拿到批量路径对后：

- 先逐条做配置校验
- 再按 `source_path` 分组
- 每个 `source_path` 单独发起一个传输任务

不要把多个不同 `source_path` 混到同一个传输任务里。

### 发起前必须确认路径对

真正执行 `merlin-cli resource batch-data-migration` 之前，一定要把最终要发起的源 / 目标 路径对整理出来，明确展示给用户确认，避免传错数据或传错路径。

推荐用 Markdown 表格做最终确认：

```text
| source_path | target_path | target_dc |
|------|------|------|
| hdfs://source/a | hdfs://target/a | dallas |
| hdfs://source/b | hdfs://target/b | my |
```

确认话术可以直接用：

- 请确认以上源 / 目标 路径对是否正确；我会严格按这份列表发起传输任务

在用户明确确认之前，不要执行真实发起。

## 发起任务使用的工具

发起同步任务时，使用 `merlin-cli resource batch-data-migration`。

这个工具的核心输入结构：

- `resource_type`：固定传 `hdfs`
- `hdfs_resource`：传输数据配置列表
- `yarn_resource`：可选；只有用户明确指定 Yarn 资源时才传

其中：

- 一个 `source_path` 对应一个传输任务
- `hdfs_resource` 虽然是列表，但建议每次调用只传一个元素，也就是一次只对一个 `source_path` 发起一个传输任务
- 一个传输任务可以包含多个目标路径，也就是 `targets` 可以有多个元素

推荐输入结构：

```json
{
  "resource_type": "hdfs",
  "hdfs_resource": [
    {
      "source": "hdfs://haruna/example_source_path",
      "targets": [
        {
          "target_dc": "dallas",
          "target_hdfs_path": "hdfs://harunava/example_target_path"
        }
      ]
    }
  ]
}
```

如果用户明确指定了 Yarn 资源，再加上：

```json
"yarn_resource": {
  "yarn_cluster": "example_cluster",
  "yarn_queue": "root.example_yarn_queue"
}
```

如果用户没有明确指定 Yarn 集群和队列，不要替用户猜，也不要传 `yarn_resource`。

## 推荐流程

1. 判断用户是否明确是在做 HDFS 到 HDFS 的跨地域传输
2. 收集源路径、目标路径；`target_dc` 优先通过 `target_path` 推断
3. 先调用 `merlin-cli batch get-data-migration-config` 获取支持的机房和路径前缀
4. 校验 `source_path` 是否合法，并根据 `target_path` 推断或校验 `target_dc`
5. 如果有多组源 / 目标 路径对，先让用户用表格或 JSON 列表一次性提供，并逐条校验
6. 把最终要执行的源 / 目标 路径对整理成表格，发给用户做最终确认
7. 组装 `merlin-cli resource batch-data-migration` 所需参数；如果用户没有指定 Yarn 资源，就不要传 `yarn_resource`
8. 在真正执行前，先再次自检参数是否与已确认的源 / 目标 路径对一致，不要假设存在额外的命令参数
9. 执行创建命令
10. 返回任务 ID、初始状态和查询方式

## 配置查询示例

先查当前允许的同步配置：

```bash
merlin-cli batch get-data-migration-config --json '{}'
```

拿到返回结果后，重点做三步判断：

1. `source_path` 是否命中 `supported_prefix_for_source_path`
2. `target_path` 是否命中某个 `supported_prefix_by_dc[dc]`
3. 如果用户给了 `target_dc`，再校验它是否在 `supported_target_dcs` 中，且是否与 `target_path` 匹配；如果用户没给，则根据第 2 步推断

## 发起命令示例

最小可用示例：

```bash
merlin-cli resource batch-data-migration --json '{
    "resource_type":"hdfs",
    "hdfs_resource":[
      {
        "source":"<source_path>",
        "targets":[
          {
            "target_dc":"<target_dc>",
            "target_hdfs_path":"<target_path>"
          }
        ]
      }
    ]
  }'
```

如果用户明确指定了 Yarn 资源：

```bash
merlin-cli resource batch-data-migration --json '{
    "resource_type":"hdfs",
    "hdfs_resource":[
      {
        "source":"<source_path>",
        "targets":[
          {
            "target_dc":"<target_dc>",
            "target_hdfs_path":"<target_path>"
          }
        ]
      }
    ],
    "yarn_resource":{
      "yarn_cluster":"<yarn_cluster>",
      "yarn_queue":"<yarn_queue>"
    }
  }'
```

## 返回结构

`merlin-cli resource batch-data-migration` 返回结果里，重点关注：

- `job_instance_list`：发起成功后的任务列表

单个结果里，优先关注这些字段：

- `job_instance_id`：任务 ID
- `status`：任务状态
- `strategy_conf.hdfs_distcp_in_batch_conf.distcp_confs`：实际发起的传输配置
- `creator`：任务创建人
- `created_at`：任务创建时间
- `progress.total_task_count`：传输子任务总数
- `progress.finished_task_count`：已完成的传输子任务数

如果用户指定了 `yarn_resource`，它也会出现在 `distcp_confs[].yarn_resource` 里。

## 补问模板

当字段不全时，可以直接这样问：

- 请补充源路径
- 请补充目标路径
- 我会先帮你检查这个源路径和目标路径是否在当前允许的同步范围内，并尽量从目标路径推断目标机房
- 如果你希望指定 Yarn 资源，请补充 `yarn_cluster` 和 `yarn_queue`
- 如果你有很多组源 / 目标 路径对，建议直接按表格或 JSON 列表发给我，我可以一次帮你校验和整理

如果用户给的路径或机房可能不合法，可以直接这样问：

- 这个源路径前缀可能不在允许范围内，我先帮你核对支持的源路径前缀
- 你现在只给了目标机房，还没有给完整的目标路径。请在该机房允许的目标路径前缀下补充完整的 `target_path`
- 这个目标路径当前无法唯一推断出目标机房，请确认你要同步到哪个目标机房
- 这个目标机房当前可能不支持，请确认是否要改成支持的目标机房
- 这个目标路径前缀和目标机房不匹配，请确认目标路径是否要调整到该机房允许的前缀下

发起前确认时，可以直接这样问：

- 请确认以下源 / 目标 路径对是否正确；我会严格按这份列表发起传输任务

## 执行结果要告诉用户什么

成功时至少返回：

- 用 Markdown 表格展示任务信息
- 如果用户指定了 Yarn 资源，说明实际使用的 `yarn_cluster` 和 `yarn_queue`
- 下一步如何查看进度

推荐表格格式：

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

示例回复结构：

```text
操作类型：发起任务
已识别信息：源路径 /foo/bar，目标机房 B，目标路径 /baz/qux
缺失信息：无
执行结果：
| 任务 ID | 当前状态 | 同步进度 | HDFS 源路径列表 | 任务创建时间 | 任务创建人 |
|------|------|------|------|------|------|
| task-123 | WAITING | 0/2 | [hdfs://foo/bar] | 2026-01-29T12:52:06Z | alice |

补充说明：目标机房为 B，目标路径为 /baz/qux
下一步：可继续查询 task-123 的进度和失败原因
```

## 注意事项

- 发起前一定先调用 `merlin-cli batch get-data-migration-config` 做校验
- 不要跳过源路径前缀、目标机房、目标路径前缀的合法性检查
- 发起任务时使用 `merlin-cli resource batch-data-migration`
- `resource_type` 固定传 `hdfs`
- 建议每次调用只对一个 `source_path` 发起一个传输任务
- 如果有多组路径对，优先让用户用 Markdown 表格或 JSON 列表一次性提供
- 真正发起前，必须把最终的源 / 目标 路径对列表发给用户确认
- 如果用户没有明确指定 Yarn 资源，不要传 `yarn_resource`
- 不要在未确认路径的情况下直接发起
- 如果用户只描述“把这份数据同步过去”，但没有给完整路径，先补问，不要假设默认路径
- `target_dc` 不是必需；能从 `target_path` 唯一推断时，优先自动推断
