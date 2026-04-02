# 从零创建任务（基于代码仓库）

用户没有可 fork 的任务，根据代码仓库与分支直接创建新的 Merlin 训练任务。

## 输入

- 二选一：MLX 仓库 ID 或代码仓库地址（Repo URL）
- 分支名称
- 入口命令（entrypoint）
- 镜像信息
- 资源配置（通过 `job-resource` 技能选出）

## 步骤

### 1. 收集并确认必要信息

检查用户提供的信息是否完整。对缺失的关键配置（镜像、分支、入口命令、GPU 型号/数量、依赖安装方式），必须向用户确认，不得猜测。

### 2. 准备 MLX 仓库

- 若有 MLX 仓库 ID，直接使用
- 否则用 Repo URL 调用 `merlin-cli job create-mlxlab-repo` 注册仓库

### 3. 选择资源

调用 `job-resource` 技能选择集群与队列。

### 4. 创建任务

```bash
merlin-cli job create-run-by-mlx-repo --json '{
  "mlx_repo_id": <id>,
  "branch": "<branch>",
  "entrypoint": "<command>",
  "image": "<image>",
  ...resource_config...
}'
```

Robust 任务的角色名应该是 `executor` 而不是 `worker`。

### 5. 监控与错误处理

```bash
merlin-cli job get-run --json '{"job_run_id": "<id>", "wait_until_running": true}'
```

- 成功运行 → 报告任务链接
- 失败且原因明确（资源不足）→ `merlin-cli job create-run-retry` 重试
- 失败且原因不明 → 调用 `job-troubleshoot-failure` 分析

最多 1 次自动重试。

## 其他创建方式

也支持通过任务模板创建：

```bash
merlin-cli job create-def --json '{"name": "my-job", "entrypoint_full_script": "python train.py"}'
merlin-cli job create-def-version --json '{"job_def_name": "my-job", ...}'
merlin-cli job create-run-def --json '{"job_def_name": "my-job", "job_def_version": 1}'
```
