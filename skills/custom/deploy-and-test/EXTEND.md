# deploy-and-test / EXTEND

本文档补充 `deploy-and-test` Skill 在 PPE 场景下最常用、最容易复用的执行细节，重点覆盖五部分：

1. `heartbeat` 推荐请求模板
2. 测试会话常量初始化步骤
3. 双集群排障路径
4. `idl_version` 选择与纠偏方法
5. `log_id` 关联日志观测与版本确认 SOP

默认适用对象：
- 目标 PSM 已明确
- 已有或即将部署到 PPE 泳道
- 需要通过 `bytedcli api-test rpc-call` 验证运行中服务
- 需要结合日志平台 / Argos / 部署面确认实际运行版本

---

## 1. heartbeat 推荐请求模板

### 1.1 适用场景
优先在以下情况下使用 `heartbeat`：

- 刚完成 PPE 部署，需要做**最低风险冒烟验证**
- 需要先确认请求是否命中目标泳道
- 需要拿到 `log_id`，用于后续日志追踪
- 暂时没有合适的业务入参，不适合直接打写接口或复杂读接口
- 正在排查是 cluster 问题、IDL 问题还是服务逻辑问题

### 1.2 使用原则
- 所有 test case **复用同一组会话常量**
- **只变更 `req_body`**
- 顶层 `env` 与 `Base.TrafficEnv.Env` 必须一致
- `message_id` 建议每次唯一，方便日志定位
- `service_name` 建议填写当前验证场景名，便于回看

### 1.3 最小可用 heartbeat req_body

```json
{
  "message_id": "hb-20260402-001",
  "service_name": "deploy-and-test",
  "Base": {
    "LogID": "",
    "Caller": "deerflow",
    "Addr": "",
    "Client": "deerflow",
    "TrafficEnv": {
      "Env": "ppe_duoshan_hamlet"
    }
  }
}
```

### 1.4 推荐完整 rpc-call 参数模板

```bash
bytedcli api-test rpc-call \
  --psm vai.cvcg.aigc_editor \
  --func heartbeat \
  --env ppe_duoshan_hamlet \
  --cluster default \
  --idc lf \
  --zone cn \
  --idl-source 2 \
  --idl-version 1.0.18 \
  --online false \
  --body-file ./templates/heartbeat-body.json
```

### 1.5 字段填写建议

| 字段 | 建议 | 说明 |
|------|------|------|
| `message_id` | `hb-<date>-<seq>` | 便于日志检索与多次调用区分 |
| `service_name` | `deploy-and-test` / 当前项目名 | 用于区分来源 |
| `Base.Caller` | `deerflow` | 统一调用身份标记 |
| `Base.Client` | `deerflow` | 与 Caller 保持一致即可 |
| `Base.TrafficEnv.Env` | 目标 PPE 环境名 | 必填，决定请求路由目标 |

---

## 2. 测试会话常量初始化步骤

### 2.1 目标
在一轮测试会话开始时，一次性收集后续所有 case 可复用的公共参数，避免每次调接口前重新查环境。

### 2.2 必备会话常量

| 常量 | 含义 | 必需性 |
|------|------|--------|
| `psm` | 服务标识 | 必需 |
| `func_name` | RPC 方法名，默认 `heartbeat` | 必需 |
| `env` | PPE 泳道环境名 | 必需 |
| `cluster` | 请求目标集群 | 必需 |
| `zone` | 可用区 / 地域 | 必需 |
| `idc` | 机房 | 必需 |
| `online` | 是否线上 | 必需 |
| `idl_source` | IDL 来源 | 必需 |
| `idl_version` | IDL 版本 | 必需 |
| `runtime_unit` | 运行单元 / 实例标识 | 强烈建议 |
| `log_entry` | 日志检索入口或日志平台信息 | 强烈建议 |

### 2.3 初始化顺序（推荐）

```text
1. 确认 psm
2. 确认 PPE env / lane
3. 查询实例分布，确认 cluster / zone / idc / online
4. 记录 Running pod / runtime_unit
5. 确认日志检索入口（Argos / 项目日志平台 / TCE 日志）
6. 确认 func_name（默认 heartbeat）
7. 查询并锁定 idl_version
8. 记录 idl_source
9. 形成会话常量表，后续直接复用
```

### 2.4 初始化结果记录模板

```json
{
  "psm": "vai.cvcg.aigc_editor",
  "func_name": "heartbeat",
  "env": "ppe_duoshan_hamlet",
  "cluster": "default",
  "zone": "cn",
  "idc": "lf",
  "online": false,
  "idl_source": 2,
  "idl_version": "1.0.18",
  "runtime_unit": "dp-482d9fed8d-68d9dbf654-6dkqc",
  "log_entry": "Argos / TCE logs"
}
```

---

## 3. 双集群排障路径

### 3.1 背景
同一 PSM 在 PPE 下可能同时存在多个 cluster，例如：
- `default`
- `asset_library_server`

它们可能同时 Running，也可能一个正常一个异常，因此**不能把一个 cluster 的失败等价成整个服务失败**。

### 3.2 推荐排障顺序

```text
1. 列出所有实例
2. 按 cluster 分组
3. 看每组实例是否 Running
4. 优先验证 Running 且更基础的 cluster（通常 default）
5. 若失败，再看是 cluster 选错、IDL 不匹配，还是服务内部失败
6. 再对其他 Running cluster 做独立验证
7. 保留每个 cluster 的 pod / request_address / log_id / biz_status_code
```

### 3.3 关键经验

#### 情况 A：`61003`
优先怀疑：
- cluster 选错
- 对应 cluster 没有可用实例
- 路由参数不匹配

#### 情况 B：`1701 upstream request failed`
说明：
- 请求已经更接近真实实例
- 但服务内部或上游链路失败
- 此时应立即进入日志观测，而不是继续盲改路由参数

#### 情况 C：某 cluster 修复后恢复正常
说明：
- 先前失败并不一定是请求构造问题
- 也可能是该 cluster 本身实例状态或发布状态异常

### 3.4 推荐记录表

| cluster | pod | 状态 | idl_version | biz_status_code | 摘要 | log_id |
|---------|-----|------|-------------|-----------------|------|--------|
| default | `<pod>` | Running | `1.0.18` | `0` | 成功 | `<log_id>` |
| asset_library_server | `<pod>` | Running | `1.0.18` | `61001` | upstream request failed | `<log_id or empty>` |

---

## 4. IDL 版本选择与纠偏方法

### 4.1 基本原则
- `idl_version` 必须使用**明确具体版本号**
- 不要因为服务版本是 `1.0.0.909`，就想当然把 IDL 写成 `1.0.0`
- 服务运行版本与 IDL 版本不是一个概念

### 4.2 常见误区

#### 误区 1：把服务版本当 IDL 版本
错误表现：
- 用镜像版本、分支版本、发布版本直接填 `--idl-version`

正确做法：
- 用接口 schema 对应的真实 IDL 版本

#### 误区 2：遇到字段缺失就判定服务异常
错误表现：
- `required field missing`
- `reader error`
- 响应结构解析失败

正确做法：
- 第一反应应是 **IDL 版本不匹配**
- 尝试切换到可用的准确版本再复测

### 4.3 当前案例可复用经验

已验证结论：
- `idl_version=1.0.0` 调用失败，出现 `required field (2/status_msg) missing`
- `idl_version=1.0.18` 调用成功，`biz_status_code=0`

可沉淀的规则：
1. 当返回结构解析异常时，先切换 IDL 版本
2. 一旦出现成功样本，应固定成功版本做后续日志分析
3. 不要在 IDL 未打通前就做业务问题归因

---

## 5. log_id 关联日志观测与版本确认 SOP

### 5.1 目标
把“接口请求是否成功”升级成“请求是否真实命中目标服务、进入了哪一层逻辑、运行的是哪个版本”的闭环验证。

### 5.2 标准步骤

#### 步骤 1：发起 RPC 请求
优先使用 `heartbeat`，拿到最稳定的链路样本。

#### 步骤 2：提取 `log_id`
优先从以下位置提取：
- 响应显式字段中的 `log_id`
- `BaseResp` 中的链路字段
- 框架自动返回的 trace / meta 字段

#### 步骤 3：进入日志平台
推荐入口：
- Argos
- 项目日志平台
- TCE Pod 日志
- 部署面启动日志

#### 步骤 4：按 `log_id` 搜索
如搜不到，再降级按以下顺序搜索：
1. `message_id`
2. request_id / trace_id
3. pod + 时间窗口

#### 步骤 5：提取关键证据
重点记录：
- 是否命中目标 pod
- 是否进入应用层 handler
- 是否有 service / dao / downstream 调用痕迹
- 是否出现 `WARN` / `ERROR` / `panic`
- 启动日志中的版本号 / 镜像 tag / 构建信息

### 5.3 版本确认优先级
当目标是确认服务是否运行 `1.0.0.909` 时，证据优先级如下：

1. **启动日志明确打印版本号**
2. **TCE / 部署面显示镜像 tag 或发布版本**
3. **构建信息 / git commit 可映射到 1.0.0.909**
4. **功能行为符合预期**（辅助证据）

### 5.4 日志观测输出模板

```markdown
### 日志观测结果

- runtime_unit: `<pod>`
- log_entry: `Argos`
- 检索关键字: `<log_id>`
- 是否命中目标服务: 是 / 否
- 是否进入 handler: 是 / 否
- 日志级别异常: 无 / WARN / ERROR / panic
- 服务端调用链: `<handler -> service -> dao -> downstream>`
- 版本证据:
  - 启动日志版本: `<version or empty>`
  - 镜像 tag: `<tag or empty>`
  - 构建信息: `<build info or empty>`
- 结论: `<是否可确认当前运行版本为 1.0.0.909>`
```

### 5.5 当前案例推荐落地动作
针对当前 `vai.cvcg.aigc_editor` 场景，建议固定用以下路径：

1. 用已验证成功的参数打 `default` 集群 heartbeat
2. 使用 `idl_version=1.0.18`
3. 复用成功 `log_id=2026040211535182759AB72BF69BA02546` 进 Argos 搜索
4. 检查请求是否进入 handler
5. 检查启动日志中的版本 / 镜像 tag / 构建信息
6. 去 TCE / 部署面核对 pod 镜像版本
7. 最终给出是否运行 `1.0.0.909` 的结论

---

## 6. 最小闭环建议

在只想快速确认“PPE 部署是否生效、当前版本是不是目标版本”时，优先走这条最小闭环：

```text
1. 查询实例分布
2. 选 Running 的 cluster
3. 锁定 idl_version
4. 打 heartbeat
5. 提取 log_id
6. 去 Argos / TCE 搜日志
7. 看 handler / 启动日志 / 镜像 tag
8. 输出版本结论
```

这条路径的优势是：
- 风险低
- 排障快
- 证据链完整
- 适合版本验证场景
