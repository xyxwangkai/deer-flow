---
name: job-resource
description: 查询 merlin, seed 资源配额并为任务选择合适的资源组、集群与队列。当用户说"查看资源配额/GPU 资源/选择资源/队列资源不足/权限不足/quota 问题/选择合适的队列"时使用。
---

# 任务资源查询与选择

查询 Merlin 上的资源配额，并根据权限与队列状态为任务选择合适的资源组、集群与队列。

## 前置条件

- `merlin-cli` 可用

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

---

## 1. 查询资源配额

```bash
merlin-cli job list-my-resource --json '{"filters": {"type": "gpu", "gpu_type": "A100-SXM-80GB", "cluster_name": "hl"}}'
```

输出各队列的剩余 CPU、内存、GPU 资源。结果会过滤掉 federation 集群。

---

## 2. 为任务选择合适资源

当任务创建/运行失败（权限不足、quota 问题、队列异常），或不清楚可用资源时，按以下步骤选择：

### 步骤

1. **确定目标 GPU 型号与卡数**
   - 优先使用用户明确指定的 GPU 型号与卡数
   - 如存在 baseline trial，调用 `merlin-cli job get-run` 读取其资源配置作为默认目标，同时记录其用户组、cluster、queue_name 作为"优先对齐目标"
   - 均无法确定时，以"可用性最强的资源"为目标（剩余卡数最多、队列最健康）

2. **拉取可用资源**
   - 调用 `merlin-cli job list-my-resource` 获取可用资源组、集群与队列清单
   - 提取每个候选的 GPU 型号、可用卡数、用户组、cluster、queue_name、队列健康度

3. **过滤与选择**（带 baseline 优先级）
   - 过滤无权限的资源组/队列
   - 优先满足"目标 GPU 型号 + 卡数需求"的候选
   - 存在 baseline 时，优先选择与 baseline 相同用户组且相同 cluster 的候选
   - 次优先选择与 baseline 相同 queue_name 的候选
   - 多个候选时，优先队列健康度更好、剩余卡数更多者
   - 队列冻结/配额冻结/拥塞时降低该队列优先级

4. **生成推荐配置**
   - 输出结构化 `resource_config`：资源组/用户组、cluster、queue_name、GPU 型号、卡数
   - 同时输出选择依据

5. **发起任务**（如用户已提供任务）
   - 调用 `merlin-cli job create-run-retry` 使用推荐配置重试

6. **监控任务状态**
   - 调用 `merlin-cli job get-run`，设置 `wait_until_running=true`，`timeout=10`
   - `PENDING/STARTING/STARTED`：已加入队列，检查 `arnoldDiagnoseInfo`
   - `RUNNING`：任务成功启动
   - `FAILED/FAILED_TO_LAUNCH`：输出失败原因并再次调整资源配置

## 注意事项

- 权限不足时，明确给出替代资源组与申请权限的建议路径
- 推荐结果需附带依据，便于用户审阅与复用
- 若无匹配资源：输出最接近的候选与调整建议（降低需求或更换队列）

---

## 关联技能

- `job-launch`：创建并启动任务（从零创建 + fork 复制）
- `job-troubleshoot-failure`：排查任务运行失败
