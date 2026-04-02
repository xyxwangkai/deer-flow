# bytecli-deploy - 字节跳动内部部署自动化CLI工具

## 概述

`bytecli-deploy` 是字节跳动内部部署自动化CLI工具，基于 `merlin-cli` 平台开发，提供完整的部署生命周期管理功能。该工具支持多种部署策略、环境管理、监控集成、权限控制等高级功能，适用于字节跳动内部微服务架构的部署需求。

## 功能特性

### 核心功能
- **部署管理**: 支持滚动更新、金丝雀部署、蓝绿部署等多种策略
- **环境管理**: 支持开发、测试、生产等多环境配置
- **流水线管理**: 完整的CI/CD流水线集成
- **配置管理**: 配置版本控制和热更新
- **监控集成**: 与Slardar、Grafana等监控系统集成
- **集群管理**: 支持多集群部署和资源管理
- **权限管理**: 基于角色的权限控制和审批流程

### 高级功能
- **批量操作**: 支持批量部署、批量回滚、批量配置更新
- **自动化运维**: 自动扩缩容、自动故障恢复、自动监控告警
- **审计日志**: 完整的操作审计和日志记录
- **故障诊断**: 智能故障诊断和修复建议
- **性能分析**: 部署性能分析和优化建议

## 安装与配置

### 前提条件
- 已安装 `merlin-cli` (>= 1.0.0)
- 具有相应的部署权限
- 网络可访问字节跳动内部部署平台

### 安装步骤
1. 确保已安装 `merlin-cli`:
   ```bash
   curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
   ```

2. 验证安装:
   ```bash
   merlin-cli --version
   ```

3. 登录认证:
   ```bash
   merlin-cli login
   ```

## 快速开始

### 单应用部署
```bash
# 部署应用到生产环境
merlin-cli bytecli deploy --json '{
  "app_name": "order-service",
  "environment": "production",
  "version": "v1.2.3",
  "strategy": "canary",
  "canary_percentage": 10
}'
```

### 查看部署状态
```bash
# 查看部署状态
merlin-cli bytecli status --json '{
  "deployment_id": "order-service-v1.2.3"
}'
```

### 回滚部署
```bash
# 回滚到指定版本
merlin-cli bytecli rollback --json '{
  "app_name": "order-service",
  "environment": "production",
  "target_version": "v1.2.2",
  "reason": "新版本发现问题"
}'
```

## 示例脚本

### Python 示例
```bash
# 运行Python部署脚本
python3 scripts/deploy_example.py \
  --app order-service \
  --env production \
  --version v1.2.3 \
  --strategy canary \
  --monitor
```

### Bash 工作流
```bash
# 运行完整的部署工作流
./scripts/deploy_workflow.sh \
  --app order-service \
  --env production \
  --version v1.2.3 \
  --strategy canary \
  --config scripts/config_example.yaml
```

### 批量部署
```bash
# 批量部署多个应用
./scripts/deploy_workflow.sh \
  --batch scripts/batch_deployments.json
```

## 配置说明

### 配置文件格式
部署配置使用YAML格式，支持以下配置项:

```yaml
# 应用基本信息
app_name: order-service
app_version: v1.2.3
environment: production

# 部署策略
deployment_strategy: canary
strategy_config:
  canary:
    percentage: 10
    duration_minutes: 5

# 资源配额
resources:
  cpu:
    request: "1000m"
    limit: "2000m"
  memory:
    request: "2Gi"
    limit: "4Gi"

# 监控配置
monitoring:
  enabled: true
  alerts:
    - name: high_error_rate
      condition: error_rate > 5%
      severity: critical
```

### 批量部署配置
批量部署使用JSON格式，支持并行部署和错误处理:

```json
{
  "deployments": [
    {
      "app_name": "order-service",
      "environment": "production",
      "version": "v1.2.3",
      "strategy": "canary"
    }
  ],
  "parallel": 2,
  "continue_on_error": false
}
```

## 命令参考

### 部署管理
```bash
# 创建部署
merlin-cli bytecli deploy --json '{...}'

# 查看部署状态
merlin-cli bytecli status --json '{...}'

# 停止部署
merlin-cli bytecli stop --json '{...}'

# 回滚部署
merlin-cli bytecli rollback --json '{...}'

# 批量部署
merlin-cli bytecli batch-deploy --json '{...}'
```

### 环境管理
```bash
# 创建环境
merlin-cli bytecli environment-create --json '{...}'

# 查看环境列表
merlin-cli bytecli environment-list --json '{...}'

# 更新环境配置
merlin-cli bytecli environment-update --json '{...}'

# 删除环境
merlin-cli bytecli environment-delete --json '{...}'
```

### 配置管理
```bash
# 验证配置
merlin-cli bytecli config-validate --json '{...}'

# 应用配置
merlin-cli bytecli config-apply --json '{...}'

# 查看配置历史
merlin-cli bytecli config-history --json '{...}'

# 回滚配置
merlin-cli bytecli config-rollback --json '{...}'
```

### 监控管理
```bash
# 查看部署指标
merlin-cli bytecli metrics-deployment --json '{...}'

# 创建监控告警
merlin-cli bytecli alert-create --json '{...}'

# 查看告警列表
merlin-cli bytecli alert-list --json '{...}'

# 获取监控链接
merlin-cli bytecli monitoring-links --json '{...}'
```

### 权限管理
```bash
# 验证权限
merlin-cli bytecli permissions-check --json '{...}'

# 查看审批流程
merlin-cli bytecli approval-status --json '{...}'

# 审批操作
merlin-cli bytecli approval-action --json '{...}'

# 查看审计日志
merlin-cli bytecli audit-list --json '{...}'
```

## 故障排除

### 常见问题

#### 1. 认证失败
```bash
# 重新登录
merlin-cli login

# 检查令牌有效期
merlin-cli token-status
```

#### 2. 部署超时
```bash
# 增加超时时间
merlin-cli bytecli deploy --json '{
  "timeout": 3600,
  ...
}'

# 查看详细日志
merlin-cli bytecli status --json '{
  "deployment_id": "...",
  "verbose": true
}'
```

#### 3. 资源不足
```bash
# 检查资源配额
merlin-cli bytecli resource-quota --json '{
  "environment": "production"
}'

# 调整资源配置
merlin-cli bytecli deploy --json '{
  "resources": {
    "cpu": "500m",
    "memory": "1Gi"
  },
  ...
}'
```

#### 4. 网络问题
```bash
# 检查网络连通性
merlin-cli network-check --json '{
  "target": "deployment-service"
}'

# 使用代理配置
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### 诊断工具
```bash
# 诊断部署问题
merlin-cli bytecli diagnose-deployment --json '{
  "deployment_id": "...",
  "checks": ["health", "resources", "network"]
}'

# 性能分析
merlin-cli bytecli performance-analysis --json '{
  "app_name": "...",
  "environment": "..."
}'

# 获取修复建议
merlin-cli bytecli get-fix-suggestions --json '{
  "issue_type": "deployment-failure",
  "error_code": "..."
}'
```

## 最佳实践

### 部署策略选择
1. **开发环境**: 使用滚动更新，快速迭代
2. **测试环境**: 使用蓝绿部署，确保测试环境稳定
3. **生产环境**: 使用金丝雀部署，逐步验证新版本

### 监控告警配置
1. **关键指标**: 错误率、延迟、成功率
2. **告警级别**: 根据业务影响设置不同级别
3. **通知渠道**: 飞书、Slack、电话等多渠道通知

### 回滚策略
1. **自动回滚**: 配置自动回滚条件
2. **手动回滚**: 保留手动回滚能力
3. **回滚验证**: 回滚后验证系统状态

### 批量部署
1. **并行控制**: 控制并行部署数量
2. **错误处理**: 配置错误处理策略
3. **进度监控**: 实时监控批量部署进度

## 版本历史

### v1.0.0 (2024-03-30)
- 初始版本发布
- 支持基本部署功能
- 提供Python和Bash示例脚本
- 完整的文档和配置示例

## 支持与反馈

### 问题报告
- 内部工单系统: 部署平台技术支持
- 飞书群组: `bytecli-deploy-support`
- 邮件: `deploy-support@example.com`

### 文档资源
- 官方文档: https://docs.example.com/bytecli-deploy
- API参考: https://api.example.com/bytecli-deploy
- 示例仓库: https://git.example.com/bytecli-deploy-examples

## 许可证

内部使用，仅限字节跳动员工使用。

---

**注意**: 生产环境操作需要相应权限，请确保你有足够的权限并遵循公司的部署规范。