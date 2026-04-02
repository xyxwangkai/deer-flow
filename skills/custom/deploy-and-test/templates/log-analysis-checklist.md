# log analysis checklist

适用场景：
- 已拿到成功或失败请求的 `log_id`
- 需要到 Argos / TCE / 项目日志平台确认请求是否进入应用层
- 需要确认运行版本是否为目标版本（如 `1.0.0.909`）

## 1. 基本信息记录
- PSM:
- env:
- cluster:
- zone:
- idc:
- pod / runtime_unit:
- idl_version:
- log_id:
- message_id:
- request time:

## 2. 检索顺序
1. 先搜 `log_id`
2. 搜不到则搜 `message_id`
3. 仍搜不到则按 pod + 时间窗口检索

## 3. 重点检查项
- [ ] 请求是否命中目标 pod
- [ ] 是否进入应用层 handler
- [ ] 是否出现 service / dao / downstream 调用痕迹
- [ ] 是否出现 WARN
- [ ] 是否出现 ERROR
- [ ] 是否出现 panic
- [ ] 启动日志是否打印版本号
- [ ] 是否能看到镜像 tag
- [ ] 是否能看到构建信息 / git commit

## 4. 版本确认证据
- 启动日志版本号：
- 镜像 tag：
- 构建信息：
- TCE / 部署面截图或记录：
- 是否可确认版本为目标版本：是 / 否

## 5. 结论模板
> 请求已 / 未命中目标服务；已 / 未进入 handler；日志中存在 / 不存在 ERROR/WARN/panic；当前能 / 不能根据启动日志、镜像 tag、构建信息确认运行版本为目标版本。
