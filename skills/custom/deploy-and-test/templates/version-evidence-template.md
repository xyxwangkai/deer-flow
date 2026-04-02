# version evidence template

适用场景：
- 目标是确认某个 PPE 服务当前运行版本是否为指定版本
- 已经拿到 `log_id`，准备结合日志、镜像、构建信息、部署面证据形成最终结论
- 需要输出可复核、可追溯的版本确认记录

## 1. 目标信息
- PSM:
- env / lane:
- cluster:
- zone:
- idc:
- expected version:
- verification time:
- verifier:

## 2. 请求样本信息
- func_name:
- idl_version:
- message_id:
- log_id:
- request time:
- biz_status_code:
- request_address / pod:

## 3. 证据优先级检查

### Evidence A: 启动日志版本号（最高优先级）
- 检索入口:
- 日志时间范围:
- 命中 pod:
- 原始日志摘录:
```
<在这里粘贴启动日志中的版本号相关内容>
```
- 是否明确出现目标版本号:
- 初步结论:

### Evidence B: 镜像 tag / 部署面版本
- TCE / 部署面入口:
- pod / workload:
- image repository:
- image tag:
- release version:
- 截图或记录:
- 是否与目标版本一致:

### Evidence C: 构建信息 / git commit 映射
- build id:
- git commit:
- build time:
- 发布记录链接或来源:
- 是否可映射到目标版本:
- 映射说明:

### Evidence D: 业务行为（辅助证据）
- heartbeat / 业务接口表现:
- 与目标版本预期是否一致:
- 说明:

## 4. 日志链路检查
- [ ] 请求已命中目标 pod
- [ ] 已进入应用层 handler
- [ ] 已看到 service / dao / downstream 调用痕迹
- [ ] 无关键 ERROR
- [ ] 无 panic
- [ ] 若有 WARN，已说明是否影响版本判断

## 5. 证据汇总结论

| evidence type | available | supports target version? | confidence | note |
|---|---|---|---|---|
| startup log version |  |  | high / medium / low |  |
| image tag / release version |  |  | high / medium / low |  |
| build info / git commit |  |  | high / medium / low |  |
| business behavior |  |  | high / medium / low |  |

## 6. 最终结论
- 是否可确认当前运行版本为目标版本：是 / 否 / 暂不能确认
- 最强证据来源：
- 仍存在的不确定性：
- 建议下一步：

## 7. 推荐结论话术
> 已基于 `log_id` 关联到目标请求，并结合启动日志、镜像 tag、构建信息与业务表现进行交叉确认。目前可以 / 不可以确认 `PSM=<...>` 在 `env=<...>` 的实际运行版本为 `<expected version>`。最强证据为 `<evidence>`；剩余不确定性为 `<uncertainty>`。
