# 排查开发机启动失败

## 适用场景

- 开发机启动失败
- 开发机一直处于"启动中"状态
- 开发机被自动关机

## 排查步骤

### 1. 获取开发机 K8s 名称

- 如果用户提供了资源 ID（纯数字如 `12345`），调用 `merlin-cli devbox get` 获取 K8s 名称
- 如果用户提供了开发机名称（如 `my-devbox`），调用 `merlin-cli devbox list` 查找对应开发机
- 如果用户提供了 K8s 名称（如 `mlxlabkrzjfwux69415ba2-20251216131618-nqknsj`），直接使用

### 2. 检查 K8s 事件

```bash
merlin-cli devbox get-k8s-events --json '{"k8s_name": "<k8s_name>"}'
```

分析事件 `Reason` 和 `Message`，寻找：
- `FailedScheduling` — 资源不足
- `ImagePullBackOff` — 镜像拉取失败
- `MountVolume` — 挂盘问题
- `CreateContainerError` — 容器创建失败

如果事件明确指出了原因，直接给出相应建议。

### 3. 检查启动日志

如果 K8s 事件未提供明确原因：

```bash
merlin-cli devbox get-logs --json '{"k8s_name": "<k8s_name>"}'
```

- 优先检查 `wsinitv2`（init 容器）的日志
- 其次检查 `-master`（主容器）的日志
- 使用 `curl` 下载日志，用 `tail`、`grep` 分析末尾的关键信息

## 注意事项

- 主容器名称以 `-master` 结尾，初始化容器以 `wsinitv2` 结尾
- 宿主机故障（如 `TopologyAffinityError`）通常需上报平台管理员

## 兆底

日志和事件均无明显错误时，可能是更深层次的平台问题，建议用户联系 Merlin 平台支持团队。
