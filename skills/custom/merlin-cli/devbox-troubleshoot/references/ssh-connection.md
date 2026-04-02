# 排查无法通过 SSH 连接到开发机

## 适用场景

- 从本地终端执行 `ssh <devbox_alias>` 失败
- SSH 连接报错 `Permission denied`、连接超时

## 排查步骤

### 1. 检查开发机 SSH 服务端状态

使用 `merlin-cli devbox execute-script` 在开发机上执行：

```bash
ssh -v -p 9000 -o PreferredAuthentications=publickey -o PasswordAuthentication=no localhost
```

- 如果输出包含 `Authenticated to localhost` 和 `Entering interactive session`，说明开发机 SSH Server 配置正常，问题在本地客户端。
- 如果出现 `Permission denied (publickey)`，检查开发机内部 SSH 服务配置：
  - 查看 `~/.ssh` 目录及文件权限：`ls -la ~/.ssh`
  - 检查 sshd 服务：`ps auxxww | grep sshd`，正常输出应包含 `/usr/sbin/sshd -D -h ... -p 9000`

### 2. 检查用户本地 SSH 配置

- 询问用户是否按照《Merlin 开发机 SSH 使用文档》配置了公钥和 `~/.ssh/config`
- 请求用户提供 `~/.ssh/config` 内容，检查 `Host`、`HostName`、`ProxyJump` 等配置

### 3. 排查认证问题

- 如果报错为 `Permission denied (gssapi-with-mic)`，通常是 Kerberos 认证问题
- 引导用户执行 `kinit` 命令，并通过 `ssh jump.byted.org` 测试 Kerberos 是否生效

## 注意事项

- 检查 `~/.ssh/config` 时注意保护用户隐私
- `kinit` 认证有时效性，连接再次失败时可提醒用户重新执行

## 兆底

以上步骤均无法解决时，可能涉及更复杂的网络环境或权限问题，建议用户寻求 IT 或 Merlin 平台支持。
