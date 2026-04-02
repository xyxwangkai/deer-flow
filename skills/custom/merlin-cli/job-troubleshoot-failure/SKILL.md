---
name: job-troubleshoot-failure
description: 排查并定位 merlin, seed 任务运行失败或 hang 的根因，输出结构化结论与可执行修复方案；支持 Mega/Xray hang 诊断（NCCL hang、pyspy trace）、Karl 事件分析、Grafana 监控。当用户询问"为何任务失败/如何修复/任务 hang 了/训练卡住了/NCCL 超时/任务告警"时使用。
---

# 任务诊断

排查 Merlin 任务运行失败或 hang 的根因。根据任务状态选择对应的诊断流程。

## 前置条件

- `merlin-cli` 可用
- 知道任务的 URL 或 `job_run_id`

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

## 诊断分流

首先获取任务状态：

```bash
merlin-cli job get-run --json '{"job_run_id": "<id>"}'
```

根据状态选择诊断路径：

| 任务状态 | 诊断路径 |
|----------|----------|
| `FAILED` / `FAILED_TO_LAUNCH` | 阅读 `references/failure-diagnosis.md` — 失败根因分析 |
| `RUNNING` 但无进展（hang） | 阅读 `references/hang-diagnosis.md` — Mega/Xray hang 诊断 |
| `RUNNING` 正常 | 任务未失败，建议使用 `job-operations` 查看日志 |
| `PENDING` | 任务排队中，建议稍后再查 |
| `SUCCEEDED` / `TERMINATED` | 任务已完成/被终止，无需诊断 |

## 通用工具

```bash
merlin-cli job get-run --json '{"job_run_id": "<id>"}'
merlin-cli job list-trial-exit-info --json '{"job_run_id": "<id>", "trial_id": "<trial_id>"}'
merlin-cli job list-trial-logs --json '{"job_run_id": "<id>", "trial_id": "<trial_id>"}'
merlin-cli job get-grafana --json '{"job_run_id": "<id>"}'
merlin-cli knowledge search --json '{"query": "<error_keyword>"}'
```

## 输出

- 结构化诊断结论：失败类别、最可能原因、关键信息、日志摘录
- 可执行修复方案：资源/入口命令/依赖改动建议
- （如有）自动修复后的新任务链接

- **非中国区域 TOS 访问**：如果下载日志时遇到 `tosv.byted.org` 域名无法访问的问题，将 URL 中的 `tosv.byted.org` 替换为 `cdn-tos-cn.bytedance.net` 即可。该域名在全球所有区域可用，无需 CN VPN。参考：[说明文档](https://bytedance.us.larkoffice.com/docx/U6vLdvE1RoLB4lx1RNhubX2NsRf)

---

## 关联技能

- `job-operations`：任务运维（日志、时间线、Pod 执行）
- `job-resource`：资源配额查询与选择
- `job-launch`：创建并启动任务
