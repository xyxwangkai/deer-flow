# 排查无法登录到 Worker

## 适用场景

- 在开发机终端执行 `ssh <worker_ip>` 失败
- 登录 Worker 时提示 `Permission denied` 或其他 SSH 错误

## 前提

用户已创建并尝试连接至少一个 Worker。

## 排查步骤

### 1. 检查开发机 SSH 服务状态

使用 `merlin-cli devbox execute-script` 在开发机上执行：

```bash
ssh -p 9000 localhost
```

如果执行失败，说明开发机自身的 SSH 服务端配置有问题，需检查 `~/.ssh/` 目录下配置文件的权限和内容。

### 2. 检查 SSH 密钥认证

- 经用户同意后，检查 `~/.ssh/id_rsa` 是否被意外修改
- 如果怀疑密钥不匹配，将公钥追加到 authorized_keys：
  ```bash
  cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
  ```
- 如果密钥文件丢失或损坏，引导用户重新生成：
  ```bash
  ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa <<< y
  cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
  ```

## 注意事项

- 修改或重新生成 SSH 密钥是敏感操作，必须获得用户明确同意
- 操作前应提醒用户备份 `~/.ssh` 目录

## 兆底

修复密钥后仍无法登录，问题可能在 Worker 端的 SSH 服务配置。由于通常无法直接操作 Worker，建议用户删除并重建 Worker 实例。
