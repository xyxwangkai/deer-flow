
# 任务热更新审计

## 摘要

使用 `merlin-cli job get-timeline` 工具查询指定 Job Run 和 Trial 的热更新历史，对比配置变更，并将审计结果（包含时间、Diff 详情、Diff 简介）导出为 CSV 文件。如用户有需求，还可进一步生成包含详细审计表格的飞书文档。

## 适用场景

- 用户怀疑任务运行过程中参数被修改，需要确认。
- 需要排查任务热更新是否生效。
- 审计任务的完整配置变更历史并归档。
- 只有开启了 Robust Training 的任务才支持此功能。

## 前置条件

- 目标任务必须开启了 Robust Training。
- 获取到任务的 `job_run_id` 和 `trial_id`或者`resource_group_names`。

## MCP 工具使用

当 MCP 工具不可用时，可以使用 merlin-cli CLI 作为替代。merlin-cli 会动态从 MCP 服务获取所有可用工具。

```bash
# 检查 merlin-cli 是否已安装，如未安装则下载
# 检查 merlin-cli 是否已安装
merlin-cli --help &>/dev/null

# 如未安装，执行以下命令下载安装
curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash

# 查看所有可用工具
merlin-cli list-tools

# 按关键词过滤工具
merlin-cli list-tools --filter job

# 查看特定工具的帮助信息
merlin-cli <tool-name> --help

# 调用工具示例
merlin-cli job get-run --json '{"job_run_id": "xxx"}'
merlin-cli job list-trial-exit-info --json '{"job_run_id": "xxx", "trial_id": "xxx"}'
merlin-cli job get-timeline --json '{"job_run_id": "xxx", "trial_id": "xxx"}'
```

如果出现认证错误（401/403），请运行：`merlin-cli login`

## 输入

- `job_run_id`: Merlin Job Run ID。
- `trial_id`: Trial ID (通常可以从任务链接中获取)。
- `resource_group_names`: 资源组名称，用于批量审计该资源组下的任务。

## 输出

- 一个或多个 CSV 文件（针对每个任务生成一个），包含所有热更新记录。
- CSV 列定义：
  - `Update Time`: 更新时间。
  - `Diff Summary`: 变更简介（如 "修改了 LR", "Worker +1"），以表格的形式呈现。
- （可选）飞书文档链接，包含审计表格。

## 步骤

1.  **获取任务信息**:

                  --- Current meta.jobRunParams.entrypointFullScript
                  +++ Hot Update meta.jobRunParams.entrypointFullScript
                  @@ -10,2 +10,2 @@
                   python train.py \
                  -  --lr 0.01
                  +  --lr 0.005
                  ```
                - `-` 开头的行表示旧配置。
                - `+` 开头的行表示新配置。
            - **生成摘要**: 基于上述 Diff 内容，按照模版的表格形式展示变更，注意只展示diff中出现且有变更的参数，并注意要把变更的参数的名称写全，比如`trainer.val_kwargs.val_check_interval`你不要省略成`val_check_interval`（如 "将 learning_rate 从 0.01 修改为 0.005"）。
        - **获取step和token信息**，可以使用 `merlin-cli checkpoint get-step` 根据 `job_run_id` 和 `hdfs_dir_path` 查询特定训练任务每个 step 产出的 Checkpoint，`hdfs_dir_path` 可以通过`merlin-cli job get-run`获取，返回结果中的meta信息中，会有`entrypointFullScript`,这是一个字符串，里面会有`trainer.checkpoint_kwargs.default_hdfs_dir`,根据这个字段的值获取`jobRunParams.resource.arnoldConfig.hdfsVolumes`中对应`mnt`的path，作为`hdfs_dir_path`。每次热更新的step和token，是热更新创建时间后的第一个mod_time对应的step和token信息，得到每次热更新的 Step 和 Token。
        - **填写报告内容**: 根据处理的数据，按照模版结构填写审计报告：
            - **审计概览**: 填写任务基本信息和审计摘要
            - **热更新历史记录**: 按时间顺序填写详细的变更记录，每个变更作为一个二级标题，二级标题下有一个单行 markdown 表格代表这次变更的记录，表格列应包含：更新时间、Step、Token、变更简介、表格形式的具体 Diff。
            - **入口命令变更分析**: 分析并记录入口命令的变更，以表格形式展示。
            - **配置变更趋势分析**: 分析参数变更趋势，以表格形式展示。
            - **审计结论**: 总结发现的问题和建议
        - **保存报告**: 将生成的报告保存为 `audit_{job_run_id}_{trial_id}.md` 文件

3.  **生成飞书文档（可选）**:
    - 如果用户明确要求生成飞书文档或在线文档。
    - **具体指令**:
        - 整合上一步生成的多个 MD 文件，将每次变更整理为一个二级标题，二级标题下有一个单行 markdown 表格代表这次变更的记录。
        - 表格每一行对应一次热更新记录。
        - 表格列应包含：更新时间、变更简介、表格形式的具体 Diff。
        - 本地编辑一个 markdown 文件（文件名可以为 `audit_{job_run_id}_{trial_id}.md`），内容为飞书文档格式。
        - 调用技能: `lark-doc-create-from-markdown` 将本地 markdown 文档上传至飞书，注意上传之前，将文档中的操作人名替换为飞书格式，你可以通过 `get_user_open_id` 脚本工具根据用户名查询用户的 open_id，并替换为<mention-user id="{open_id}" />这种格式。

4.  **结果交付**:
    - 告知用户审计完成，概括扫描了多少个任务，发现了多少次热更新。
    - 提供生成的 Markdown 文件路径或飞书文档链接。

## 约束与注意事项

- 该功能仅适用于 Robust Training 任务。
- 不能跳过step和token信息的获取，因为这是审计的基础。
- 填写文档时，你必须要严格按照`hot_update_audit_template.md`的格式填写，不能遗漏任何一项，特别是step和token信息。
- 每次热更新的step和token，是热更新时间后距离最近的产出时间的step和token
- step和token信息，每个详细变更记录的地方也要写
- 你一定要根据用户名查询用户的 open_id，然后在模版中填写<mention-user id="{open_id}" />这种格式，这是用户的强制要求，你不能省略，省略这个文档就没意义了。
- 一个任务的热更新审计，包括`merlin-cli job get-timeline`和`merlin-cli checkpoint get-step`两个工具的调用，执行完成填写好step和token信息后，再执行下一个任务的步骤，否则计算的时候会混乱。
- 每个任务的热更新审计的diff详情都要严格按照模版中的表格形式展示，这是用户的强制要求
- 填写任务链接的时候，注意用https://seed.bytedance.net/development/instance/jobs/{job_run_id}?tabState=run_info&trialId={trial_id}，不要用https://ml.bytedance.net/，这是强制要求，因为目前只有seed控制面的请求。

## 失败与兜底

- **参数缺失**: 如果用户未提供 `trial_id`，询问用户或尝试查找默认 Trial。
- **工具报错**: 如果调用失败，检查 `job_run_id` 和 `trial_id` 是否有效。


