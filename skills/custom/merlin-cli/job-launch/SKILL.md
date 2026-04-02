---
name: job-launch
description: 创建并启动 merlin, seed 训练任务，支持从零创建（基于代码仓库）和基于基线任务 fork 复制两种方式。当用户说"创建任务/发起训练/启动任务/从零开始/fork 任务/复制任务/提交新任务"时使用。
---

# 任务创建与启动

创建并启动 Merlin 训练任务。根据用户的输入选择对应方式：

| 场景 | 方式 | 详细步骤 |
|------|------|----------|
| 有基线任务可 fork | 基于基线复制 | 阅读 `references/fork-and-submit.md` |
| 从零开始，提供代码仓库 | 直接创建 | 阅读 `references/launch-from-scratch.md` |

## 前置条件

- `merlin-cli` 可用

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

## 通用流程

无论哪种方式，都需要：

1. **选择资源**：调用 `job-resource` 技能选择合适的集群与队列
2. **创建任务**：调用对应的创建工具
3. **监控状态**：`merlin-cli job get-run --json '{"job_run_id": "<id>", "wait_until_running": true}'`
4. **失败处理**：调用 `job-troubleshoot-failure` 分析根因

## 必须向用户确认的关键配置

对于以下配置项，如果用户未明确提供，必须主动询问确认：

| 配置项 | 说明 |
|--------|------|
| 产品线类型 | 个人（cn 控制面）或 Seed（cn-seed 控制面） |
| 镜像 | 训练使用的 Docker 镜像 |
| 入口命令 | 训练启动命令/脚本路径 |
| GPU 型号与数量 | 训练所需的 GPU 类型和卡数 |
| 分支名称 | 代码仓库的分支（从零创建时） |

## 任务链接格式

根据控制面使用对应 URL：
- cn：`https://ml.bytedance.net/development/instance/jobs/{job_run_id}`
- cn-seed：`https://seed.bytedance.net/development/instance/jobs/{job_run_id}`
- i18n-tt：`https://ml.tiktok-row.net/development/instance/jobs/{job_run_id}`
- i18n-bd：`https://ml-i18nbd.byteintl.net/development/instance/jobs/{job_run_id}`

---

## 关联技能

- `job-resource`：资源配额查询与选择
- `job-troubleshoot-failure`：任务失败与 hang 诊断
- `companion-eval`：创建伴生评估
