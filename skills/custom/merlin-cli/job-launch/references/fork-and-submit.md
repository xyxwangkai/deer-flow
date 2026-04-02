# 基于基线任务复制并提交新任务

基于已有的 Merlin 任务作为模板，创建并提交新任务，支持修改任意配置参数。

## 适用场景

- 复制任务创建相同或相似实例
- 修改参数后提交新任务
- 对比实验：同一基线尝试多组配置

## 输入

- 基线任务的 URL
- （可选）需要修改的参数及新值
- （可选）任务数量

## 步骤

### 1. 获取基线任务配置

从 URL 中解析任务 ID，获取完整配置：

```bash
merlin-cli job get-run --json '{"job_run_id": "<id>"}'
```

### 2. 选择资源

调用 `job-resource` 技能，输入 baseline trial 选择合适的集群与队列。

### 3. 生成新任务配置并提交

克隆基线配置，用新值覆盖对应参数，使用选好的 `resource_config`：

```bash
merlin-cli job create-run-fork --json '{
  "job_run_id": "<baseline_id>",
  "entrypoint_full_script": "<modified_command>",
  ...resource_config...
}'
```

### 4. 等待并验证

```bash
merlin-cli job get-run --json '{"job_run_id": "<new_id>", "wait_until_running": true}'
```

### 5. 汇总报告

整理所有新任务的 ID 和链接，报告成功/失败情况。

## 注意事项

- 提交数量可能受平台配额限制
- 失败时分析错误信息（配置错误、资源不足）并报告
- fork 时如需添加/修改全局环境变量，使用 create-run-fork 的 envs_list 参数，而非修改 entrypoint 脚本（除非明确是仅在 entrypoint 内使用的环境变量）
