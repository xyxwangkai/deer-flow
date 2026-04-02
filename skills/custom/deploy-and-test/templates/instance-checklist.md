# instance checklist

适用场景：
- 在发起 RPC 前，先确认目标 PSM 在 PPE 环境中的实例分布
- 同一 PSM 存在多个 cluster，需要判断应优先验证哪个 cluster
- 需要记录 `Running / NotReady` 状态、pod、runtime_unit、路由参数，避免误打到错误集群

## 1. 验证目标
- PSM:
- env / lane:
- target version:
- query time:
- operator:

## 2. 实例分布总览

| cluster | zone | idc | total instances | running | not ready | selected for rpc? | note |
|---|---|---|---:|---:|---:|---|---|
| default | cn | lf |  |  |  |  |  |
| asset_library_server | cn | lf |  |  |  |  |  |

## 3. 实例明细记录

| cluster | pod / hostname | runtime_unit | status | ready | start_time | image tag | node | note |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

## 4. 首选 cluster 判断
- [ ] 已优先选择 `Running` 实例所在 cluster
- [ ] 已确认不是默认假设 `default` 必然可用
- [ ] 已记录每个 cluster 的实例状态差异
- [ ] 若 cluster A 不通，已计划继续验证 cluster B

### 结论
- 首选 cluster:
- 原因:
- 备选 cluster:
- 切换条件:

## 5. RPC 固定参数记录
- env:
- cluster:
- zone:
- idc:
- online:
- idl_source:
- idl_version:
- func_name:

## 6. 风险提示
- 若返回 `61003`，先排查是否选错 cluster / zone / idc
- 若实例列表中同时存在 `Running` 与 `NotReady`，不要混淆
- 若多个 cluster 行为不同，必须分别记录，不能合并成单一结论
