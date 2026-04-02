---
name: checkpoint-query
description: 查询 HDFS Checkpoint 卡片信息。当需要获取训练 Checkpoint 的详细信息时使用。
---

# Checkpoint 查询

## 摘要

查询 HDFS Checkpoint 卡片信息，支持等待卡片创建完成。

## 适用场景

- 获取训练 Checkpoint 的详细信息
- 等待 Checkpoint 卡片创建完成
- 查看 Checkpoint 的关联任务和同步信息

## 前置条件

- 知道 HDFS Checkpoint 的路径

## 包含的脚本

### get_hdfs_checkpoint.py

查询 HDFS Checkpoint 卡片信息。

- **脚本路径**: `scripts/get_hdfs_checkpoint.py`
- **参数**:
  - `path`: HDFS Checkpoint 路径（必需）
  - `--wait`: 是否等待卡片创建完成（最长 5 分钟）
- **用法示例**:
  ```bash
  python3 scripts/get_hdfs_checkpoint.py "hdfs://path/to/checkpoint"
  python3 scripts/get_hdfs_checkpoint.py "hdfs://path/to/checkpoint" --wait
  ```

## 输出

返回 Checkpoint 卡片信息，包括：
- `path`: HDFS 路径
- `name`: 卡片名称
- `owners`: 所有者列表
- `stage`: 训练阶段
- `repo`: 代码仓库
- `modal`: 训练模态
- `ckpt_count`: Checkpoint 数量
- `min_step` / `max_step`: 步数范围
- `jobs`: 关联的 Merlin 任务
- `source_sync` / `target_syncs`: 同步信息

## MCP 工具使用

当 MCP 工具不可用时，可以使用 merlin-cli CLI 作为替代。

```bash
# 检查 merlin-cli 是否已安装
merlin-cli --help &>/dev/null

# 如未安装，执行以下命令下载安装
curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash

# 查看工具帮助
merlin-cli checkpoint get --help

# 查询 Checkpoint 卡片信息
merlin-cli checkpoint get --json '{"path": "hdfs://path/to/checkpoint"}'

# 等待卡片创建完成
merlin-cli checkpoint get --json '{"path": "hdfs://path/to/checkpoint", "wait_until_creation": true}'
```

如果出现认证错误（401/403），请运行：`merlin-cli login`

## 约束与注意事项

- 如果开启等待且返回 `should_retry: true`，说明卡片尚未创建完成，需要再次调用
- 等待模式最长轮询 5 分钟
