---
name: service-query
description: 查询 merlin, seed 线上服务（Bernard）的配置详情。当用户说"查看线上服务/查询服务配置/Bernard 服务详情/service 信息/部署服务查询"时使用。
---

# 线上服务查询

查询 Merlin 线上服务（Bernard）的配置详情。

## 前置条件

- `merlin-cli` 可用
- 知道 `service_id`

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

---

## 查询服务详情

```bash
merlin-cli service get --json '{"service_id": "<service_id>"}'
```

返回服务的配置详情，包括部署状态、资源配置、端点信息等。

服务 URL 格式：`https://ml.bytedance.net/serviceList/<service_id>`

---

## 关联技能

- `job-launch`：创建训练任务
- `eval-run-exercise`：运行评估
