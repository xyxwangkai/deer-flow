---
name: devbox-troubleshoot
description: 排查 merlin, seed 开发机的各类故障，包括 SSH 连接失败、启动失败、Worker 登录失败、Notebook 无法连接远程 Worker、CPU/内存性能问题等。当用户说"开发机连不上/SSH 失败/Permission denied/开发机启动失败/一直启动中/Worker 登录不了/Notebook 连接 Worker 无响应/开发机卡顿/白屏/VSCode 连不上"时使用。
---

# 开发机故障排查

排查 Merlin 开发机的连接、启动和性能问题。根据用户描述的症状分流到对应的排查流程。

## 前置条件

- 拥有目标开发机的访问权限
- `merlin-cli` 可用（用于远程执行诊断命令）

### 环境检测

```bash
if [ -n "$ARNOLD_WORKSPACE_ID" ]; then
    echo "当前在开发机中，资源 ID: $ARNOLD_WORKSPACE_ID"
else
    echo "当前不在开发机中，需要使用 merlin-cli 远程执行"
fi
```

### merlin-cli 安装检查

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

## 场景分流

根据用户描述的症状，阅读对应的 reference 文件获取详细排查步骤：

| 症状 | 排查文档 |
|------|----------|
| 从本地 SSH 连接开发机失败、`Permission denied`、连接超时 | 阅读 `references/ssh-connection.md` |
| 开发机启动失败、长时间"启动中"、被自动关机 | 阅读 `references/startup-failure.md` |
| 在开发机中 SSH 到 Worker 失败、`Permission denied` | 阅读 `references/worker-login.md` |
| Notebook "Connect to remote worker" 无响应、无法选择 Worker | 阅读 `references/remote-worker-connection.md` |
| 开发机卡顿、白屏、VSCode 无法连接、SSH 频繁断开 | 阅读 `references/performance-issues.md` |

## 通用工具

在非开发机环境中执行诊断命令的通用方式：

```bash
merlin-cli devbox execute-script --json '{"resource_id": "<resource_id>", "cmd": "<诊断命令>"}'
```

获取开发机信息：

```bash
merlin-cli devbox get --json '{"resource_id": "<resource_id>"}'
merlin-cli devbox list --json '{}'
```

## 兆底

如果对应的排查流程无法解决问题，建议用户联系 Merlin 平台支持团队。

## 关联技能

- `devbox-manage`：查询、生命周期管理、远程执行
- `job-troubleshoot-failure`：任务运行失败排查
