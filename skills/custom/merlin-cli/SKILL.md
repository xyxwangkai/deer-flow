---
name: merlin-cli
description: |
  字节跳动merlin内部部署自动化CLI工具。支持部署管理、环境管理、流水线管理、配置管理、监控集成、集群管理、权限管理等功能。
  当用户需要执行部署、回滚、环境切换、配置管理、监控集成等操作时使用。
  触发词：/merlin、merlin部署、环境管理、流水线管理、配置管理、监控集成、集群管理、权限管理、bytedcli-merlin。
---

# Merlin 部署管理

字节跳动merlin内部部署自动化CLI工具，提供完整的部署生命周期管理。
merlin部署的服务一定要用merlin-cli，不能用bytedcli。

## 前置条件

```bash
# 安装 merlin-cli
merlin-cli 在当前技能根目录下 skills/custom/merlin-cli/merlin-cli

# 认证（如果需要）
merlin-cli login
```

---

## 1. 部署管理

### 1.1 部署应用

**输入**
- 应用名称
- 环境（development/staging/production）
- 版本号
- 部署策略（rolling/canary/blue-green）

**CLI 命令**

```bash
# 滚动部署
merlin-cli bytecli deploy --json '{
  "app_name": "order-service",
  "environment": "production",
  "version": "v1.2.3",
  "strategy": "rolling",
  "config_file": "configs/production.yaml"
}'

# 金丝雀部署（10%流量）
merlin-cli bytecli deploy --json '{
  "app_name": "payment-service",
  "environment": "production",
  "version": "v2.0.0",
  "strategy": "canary",
  "canary_percentage": 10,
  "duration": 300,
  "auto_promote": true,
  "promotion_criteria": {
    "error_rate": 1.0,
    "latency_p95": 200,
    "success_rate": 99
  }
}'

# 蓝绿部署
merlin-cli bytecli deploy --json '{
  "app_name": "user-service",
  "environment": "production",
  "version": "v3.1.0",
  "strategy": "blue-green",
  "traffic_split": "blue:0,green:100",
  "switch_timeout": 600
}'
```

### 1.2 查看部署状态

```bash
# 查看部署状态
merlin-cli bytecli status --json '{
  "app_name": "order-service",
  "environment": "production"
}'

# 查看详细部署信息
merlin-cli bytecli get-deployment --json '{
  "deployment_id": "order-service-v1.2.3"
}'

# 查看部署历史
merlin-cli bytecli history --json '{
  "app_name": "order-service",
  "environment": "production",
  "limit": 10
}'
```

### 1.3 回滚操作

```bash
# 回滚到指定版本
merlin-cli bytecli rollback --json '{
  "app_name": "order-service",
  "environment": "production",
  "target_version": "v1.2.2",
  "reason": "部署失败，紧急回滚"
}'

# 查看回滚状态
merlin-cli bytecli rollback-status --json '{
  "rollback_id": "rb-20240330-001"
}'
```

---

## 2. 环境管理

### 2.1 环境操作

```bash
# 创建新环境
merlin-cli bytecli env-create --json '{
  "env_name": "new-feature-env",
  "template": "production",
  "region": "cn-beijing",
  "cluster": "k8s-cluster-2",
  "description": "新功能测试环境"
}'

# 切换环境
merlin-cli bytecli env-switch --json '{
  "env_name": "staging"
}'

# 查看环境列表
merlin-cli bytecli env-list --json '{}'

# 查看环境详情
merlin-cli bytecli env-get --json '{
  "env_name": "production"
}'

# 删除环境
merlin-cli bytecli env-delete --json '{
  "env_name": "test-env",
  "force": true
}'
```

### 2.2 环境变量管理

```bash
# 设置环境变量
merlin-cli bytecli env-set --json '{
  "env_name": "production",
  "variables": {
    "DB_HOST": "postgres-prod.cluster.local",
    "REDIS_URL": "redis://redis-prod:6379",
    "LOG_LEVEL": "info"
  }
}'

# 获取环境变量
merlin-cli bytecli env-get-vars --json '{
  "env_name": "production"
}'

# 删除环境变量
merlin-cli bytecli env-unset --json '{
  "env_name": "production",
  "keys": ["TEST_VAR"]
}'
```

---

## 3. 流水线管理

### 3.1 CI/CD流水线

```bash
# 创建流水线
merlin-cli bytecli pipeline-create --json '{
  "pipeline_name": "order-service-cicd",
  "stages": [
    {
      "name": "build",
      "type": "docker-build",
      "image": "order-service:${VERSION}",
      "registry": "registry.bytedance.com"
    },
    {
      "name": "test",
      "type": "unit-test",
      "commands": ["npm test"],
      "timeout": 300
    },
    {
      "name": "deploy-staging",
      "type": "deploy",
      "environment": "staging",
      "auto_approve": true
    },
    {
      "name": "deploy-production",
      "type": "deploy",
      "environment": "production",
      "requires_approval": true,
      "approvers": ["team-lead", "sre-engineer"]
    }
  ],
  "trigger": {
    "type": "git-push",
    "branch": "main"
  }
}'

# 触发流水线
merlin-cli bytecli pipeline-trigger --json '{
  "pipeline_id": "order-service-cicd",
  "parameters": {
    "VERSION": "v1.2.3",
    "COMMIT_SHA": "abc123def456"
  }
}'

# 查看流水线状态
merlin-cli bytecli pipeline-status --json '{
  "pipeline_id": "order-service-cicd",
  "run_id": "run-20240330-001"
}'

# 查看流水线历史
merlin-cli bytecli pipeline-history --json '{
  "pipeline_id": "order-service-cicd",
  "limit": 10
}'
```

### 3.2 测试执行

```bash
# 执行单元测试
merlin-cli bytecli test-unit --json '{
  "app_name": "order-service",
  "version": "v1.2.3",
  "test_files": ["test/unit/*.test.js"],
  "coverage": true
}'

# 执行集成测试
merlin-cli bytecli test-integration --json '{
  "app_name": "order-service",
  "environment": "staging",
  "test_suite": "integration",
  "timeout": 600
}'

# 执行端到端测试
merlin-cli bytecli test-e2e --json '{
  "app_name": "order-service",
  "environment": "staging",
  "scenarios": ["checkout-flow", "payment-flow"],
  "parallel": 3
}'
```

---

## 4. 配置管理

### 4.1 配置文件管理

```bash
# 导入配置
merlin-cli bytecli config-import --json '{
  "environment": "production",
  "config_file": "configs/production.yaml",
  "validate": true,
  "backup": true
}'

# 导出配置
merlin-cli bytecli config-export --json '{
  "environment": "production",
  "output_file": "configs/production-backup.yaml"
}'

# 验证配置
merlin-cli bytecli config-validate --json '{
  "config_file": "configs/production.yaml",
  "strict": true
}'

# 比较配置差异
merlin-cli bytecli config-diff --json '{
  "env1": "staging",
  "env2": "production",
  "format": "table"
}'
```

### 4.2 密钥管理

```bash
# 创建密钥
merlin-cli bytecli secret-create --json '{
  "name": "db-password",
  "value": "${DB_PASSWORD}",
  "environment": "production",
  "description": "数据库密码",
  "rotation_days": 90
}'

# 获取密钥
merlin-cli bytecli secret-get --json '{
  "name": "db-password",
  "environment": "production",
  "decrypt": true
}'

# 更新密钥
merlin-cli bytecli secret-update --json '{
  "name": "db-password",
  "new_value": "${NEW_DB_PASSWORD}",
  "environment": "production",
  "rotate": true
}'

# 列出密钥
merlin-cli bytecli secret-list --json '{
  "environment": "production",
  "show_values": false
}'
```

### 4.3 配置热更新

```bash
# 热更新配置
merlin-cli bytecli config-hot-update --json '{
  "app_name": "order-service",
  "environment": "production",
  "config_changes": {
    "logging.level": "debug",
    "cache.ttl": 300
  },
  "restart_pods": false,
  "dry_run": false
}'

# 查看热更新历史
merlin-cli bytecli config-update-history --json '{
  "app_name": "order-service",
  "environment": "production",
  "limit": 20
}'
```

---

## 5. 监控集成

### 5.1 部署监控

```bash
# 查看部署指标
merlin-cli bytecli metrics-deployment --json '{
  "app_name": "order-service",
  "environment": "production",
  "time_range": "1h",
  "metrics": ["error_rate", "latency_p95", "throughput", "success_rate"]
}'

# 查看资源使用
merlin-cli bytecli metrics-resource --json '{
  "app_name": "order-service",
  "environment": "production",
  "time_range": "24h",
  "resources": ["cpu", "memory", "network", "disk"]
}'

# 查看业务指标
merlin-cli bytecli metrics-business --json '{
  "app_name": "order-service",
  "environment": "production",
  "time_range": "7d",
  "indicators": ["order_count", "revenue", "conversion_rate", "user_active"]
}'
```

### 5.2 日志管理

```bash
# 查看部署日志
merlin-cli bytecli logs-deployment --json '{
  "app_name": "order-service",
  "environment": "production",
  "tail": 100,
  "follow": false,
  "filter": "ERROR|WARN",
  "since": "10m"
}'

# 查看容器日志
merlin-cli bytecli logs-container --json '{
  "pod_name": "order-service-abc123",
  "container_name": "app",
  "tail": 50,
  "timestamps": true
}'

# 导出日志
merlin-cli bytecli logs-export --json '{
  "app_name": "order-service",
  "environment": "production",
  "start_time": "2024-03-30T00:00:00Z",
  "end_time": "2024-03-30T23:59:59Z",
  "output_file": "logs/order-service-20240330.log"
}'
```

### 5.3 告警管理

```bash
# 创建告警规则
merlin-cli bytecli alert-create --json '{
  "name": "deployment-error-rate-high",
  "condition": "error_rate > 5%",
  "duration": "5m",
  "severity": "critical",
  "notifications": ["slack", "feishu"],
  "environment": "production",
  "app_name": "order-service"
}'

# 查看告警列表
merlin-cli bytecli alert-list --json '{
  "environment": "production",
  "status": "firing",
  "severity": ["critical", "warning"]
}'

# 查看告警历史
merlin-cli bytecli alert-history --json '{
  "alert_name": "deployment-error-rate-high",
  "limit": 20
}'

# 禁用告警
merlin-cli bytecli alert-disable --json '{
  "alert_id": "alert-001",
  "reason": "维护期间"
}'
```

---

## 6. 集群管理

### 6.1 集群操作

```bash
# 查看集群列表
merlin-cli bytecli cluster-list --json '{}'

# 查看集群详情
merlin-cli bytecli cluster-get --json '{
  "cluster_name": "k8s-cluster-1"
}'

# 查看集群状态
merlin-cli bytecli cluster-status --json '{
  "cluster_name": "k8s-cluster-1",
  "check_nodes": true,
  "check_resources": true
}'

# 添加节点
merlin-cli bytecli cluster-add-node --json '{
  "cluster_name": "k8s-cluster-1",
  "node_type": "gpu-worker",
  "count": 2,
  "instance_type": "gpu-v100-16g"
}'
```

### 6.2 节点管理

```bash
# 查看节点列表
merlin-cli bytecli node-list --json '{
  "cluster_name": "k8s-cluster-1",
  "show_labels": true
}'

# 查看节点详情
merlin-cli bytecli node-get --json '{
  "node_name": "node-001",
  "cluster_name": "k8s-cluster-1"
}'

# 排空节点
merlin-cli bytecli node-drain --json '{
  "node_name": "node-001",
  "cluster_name": "k8s-cluster-1",
  "force": false,
  "timeout": 300
}'

# 删除节点
merlin-cli bytecli node-delete --json '{
  "node_name": "node-001",
  "cluster_name": "k8s-cluster-1",
  "force": true
}'
```

### 6.3 自动扩缩容

```bash
# 创建HPA策略
merlin-cli bytecli autoscale-create --json '{
  "app_name": "order-service",
  "environment": "production",
  "min_replicas": 2,
  "max_replicas": 10,
  "metrics": [
    {
      "type": "cpu",
      "target_utilization": 80
    },
    {
      "type": "memory",
      "target_utilization": 85
    },
    {
      "type": "custom",
      "name": "requests_per_second",
      "target_value": 1000
    }
  ],
  "behavior": {
    "scale_down": {
      "stabilization_window_seconds": 300,
      "policies": [
        {
          "type": "pods",
          "value": 1,
          "period_seconds": 60
        }
      ]
    },
    "scale_up": {
      "stabilization_window_seconds": 0,
      "policies": [
        {
          "type": "pods",
          "value": 2,
          "period_seconds": 60
        }
      ]
    }
  }
}'

# 查看扩缩容状态
merlin-cli bytecli autoscale-status --json '{
  "app_name": "order-service",
  "environment": "production"
}'

# 更新扩缩容策略
merlin-cli bytecli autoscale-update --json '{
  "app_name": "order-service",
  "environment": "production",
  "min_replicas": 3,
  "max_replicas": 15
}'
```

---

## 7. 权限管理

### 7.1 RBAC权限控制

```bash
# 创建角色
merlin-cli bytecli role-create --json '{
  "role_name": "deploy-manager",
  "permissions": [
    "deploy:create",
    "deploy:read",
    "deploy:update",
    "deploy:delete",
    "rollback:create",
    "config:read",
    "config:update"
  ],
  "description": "部署管理员角色"
}'

# 分配角色
merlin-cli bytecli role-assign --json '{
  "user_id": "user-001",
  "role_name": "deploy-manager",
  "environment": "production",
  "scope": "app:order-service"
}'

# 查看用户权限
merlin-cli bytecli permissions-list --json '{
  "user_id": "user-001",
  "environment": "production"
}'

# 验证权限
merlin-cli bytecli permissions-check --json '{
  "user_id": "user-001",
  "action": "deploy:create",
  "resource": "app:order-service",
  "environment": "production"
}'
```

### 7.2 审批流程

```bash
# 创建审批流程
merlin-cli bytecli approval-create --json '{
  "workflow_name": "production-deployment",
  "steps": [
    {
      "name": "team-lead-approval",
      "approvers": ["team-lead"],
      "timeout_minutes": 60,
      "required": true
    },
    {
      "name": "sre-approval",
      "approvers": ["sre-engineer"],
      "timeout_minutes": 30,
      "required": true
    }
  ],
  "notifications": ["slack", "feishu"],
  "auto_escalate": true
}'

# 发起审批
merlin-cli bytecli approval-request --json '{
  "workflow_id": "production-deployment",
  "initiator": "user-001",
  "context": {
    "app_name": "order-service",
    "version": "v1.2.3",
    "environment": "production",
    "reason": "新功能发布"
  },
  "attachments": ["deployment-plan.md", "test-report.pdf"]
}'

# 审批操作
merlin-cli bytecli approval-action --json '{
  "approval_id": "approval-001",
  "action": "approve",
  "approver": "team-lead",
  "comment": "测试通过，可以发布"
}'

# 查看审批状态
merlin-cli bytecli approval-status --json '{
  "approval_id": "approval-001"
}'
```

### 7.3 审计日志

```bash
# 查看审计日志
merlin-cli bytecli audit-list --json '{
  "time_range": "24h",
  "user_id": "user-001",
  "action_type": "deploy",
  "limit": 50
}'

# 导出审计日志
merlin-cli bytecli audit-export --json '{
  "start_time": "2024-03-30T00:00:00Z",
  "end_time": "2024-03-30T23:59:59Z",
  "output_format": "csv",
  "output_file": "audit/20240330.csv"
}'

# 查看详细审计记录
merlin-cli bytecli audit-get --json '{
  "audit_id": "audit-20240330-001"
}'
```

---

## 8. 批量操作

### 8.1 批量部署

```bash
# 批量部署多个应用
merlin-cli bytecli batch-deploy --json '{
  "deployments": [
    {
      "app_name": "order-service",
      "environment": "production",
      "version": "v1.2.3",
      "strategy": "rolling"
    },
    {
      "app_name": "payment-service",
      "environment": "production",
      "version": "v2.0.0",
      "strategy": "canary",
      "canary_percentage": 10
    },
    {
      "app_name": "user-service",
      "environment": "production",
      "version": "v3.1.0",
      "strategy": "blue-green"
    }
  ],
  "parallel": 2,
  "continue_on_error": false,
  "timeout": 1800
}'

# 查看批量操作状态
merlin-cli bytecli batch-status --json '{
  "batch_id": "batch-20240330-001"
}'
```

### 8.2 批量回滚

```bash
# 批量回滚
merlin-cli bytecli batch-rollback --json '{
  "rollbacks": [
    {
      "app_name": "order-service",
      "environment": "production",
      "target_version": "v1.2.2"
    },
    {
      "app_name": "payment-service",
      "environment": "production",
      "target_version": "v1.9.0"
    }
  ],
  "reason": "系统故障，紧急回滚",
  "parallel": 1
}'
```

### 8.3 批量配置更新

```bash
# 批量更新配置
merlin-cli bytecli batch-config-update --json '{
  "updates": [
    {
      "app_name": "order-service",
      "environment": "production",
      "config_changes": {
        "cache.ttl": 600,
        "logging.level": "info"
      }
    },
    {
      "app_name": "payment-service",
      "environment": "production",
      "config_changes": {
        "timeout": 30,
        "retry_count": 3
      }
    }
  ],
  "dry_run": false,
  "validate": true
}'
```

---

## 9. 故障排除

### 9.1 部署诊断

```bash
# 诊断部署问题
merlin-cli bytecli diagnose-deployment --json '{
  "deployment_id": "order-service-v1.2.3",
  "checks": [
    "health",
    "resources",
    "network",
    "dependencies",
    "configuration"
  ],
  "verbose": true
}'

# 查看部署事件
merlin-cli bytecli deployment-events --json '{
  "deployment_id": "order-service-v1.2.3",
  "limit": 50
}'

# 检查依赖服务
merlin-cli bytecli check-dependencies --json '{
  "app_name": "order-service",
  "environment": "production",
  "services": ["postgresql", "redis", "kafka"]
}'
```

### 9.2 性能分析

```bash
# 性能分析
merlin-cli bytecli performance-analysis --json '{
  "app_name": "order-service",
  "environment": "production",
  "time_range": "1h",
  "metrics": ["cpu", "memory", "latency", "throughput"],
  "generate_report": true,
  "report_format": "html"
}'

# 瓶颈识别
merlin-cli bytecli identify-bottlenecks --json '{
  "app_name": "order-service",
  "environment": "production",
  "include_logs": true,
  "include_traces": true
}'
```

### 9.3 修复建议

```bash
# 获取修复建议
merlin-cli bytecli get-fix-suggestions --json '{
  "issue_type": "deployment-failure",
  "error_code": "ERR_DEPLOY_TIMEOUT",
  "context": {
    "app_name": "order-service",
    "environment": "production",
    "strategy": "rolling"
  }
}'

# 自动修复
merlin-cli bytecli auto-fix --json '{
  "issue_id": "issue-001",
  "fix_type": "rollback",
  "confirm": false
}'
```

---

## 10. 最佳实践

### 10.1 部署工作流

```bash
# 完整的部署工作流
#!/bin/bash

# 1. 验证配置
merlin-cli bytecli config-validate --json '{
  "config_file": "configs/production.yaml"
}'

# 2. 预检查
merlin-cli bytecli precheck --json '{
  "app_name": "order-service",
  "environment": "production",
  "checks": ["resources", "dependencies", "quota"]
}'

# 3. 金丝雀部署
merlin-cli bytecli deploy --json '{
  "app_name": "order-service",
  "environment": "production",
  "version": "v1.2.3",
  "strategy": "canary",
  "canary_percentage": 10,
  "duration": 300
}'

# 4. 监控金丝雀
merlin-cli bytecli monitor-canary --json '{
  "deployment_id": "order-service-v1.2.3",
  "duration": 300,
  "check_interval": 30,
  "promotion_criteria": {
    "error_rate": 1.0,
    "latency_p95": 200,
    "success_rate": 99
  }
}'

# 5. 全量部署
merlin-cli bytecli promote --json '{
  "deployment_id": "order-service-v1.2.3"
}'

# 6. 验证部署
merlin-cli bytecli verify-deployment --json '{
  "deployment_id": "order-service-v1.2.3",
  "checks": ["health", "functionality", "performance"]
}'

# 7. 清理旧版本
merlin-cli bytecli cleanup --json '{
  "app_name": "order-service",
  "environment": "production",
  "keep_versions": 3
}'
```

### 10.2 配置管理

```bash
# 配置版本控制
merlin-cli bytecli config-version --json '{
  "action": "create",
  "config_file": "configs/production.yaml",
  "message": "增加缓存TTL配置",
  "tag": "v1.2.3"
}'

# 配置回滚
merlin-cli bytecli config-rollback --json '{
  "config_file": "configs/production.yaml",
  "version": "v1.2.2",
  "environment": "production"
}'

# 配置对比
merlin-cli bytecli config-compare --json '{
  "file1": "configs/staging.yaml",
  "file2": "configs/production.yaml",
  "output_format": "diff"
}'
```

### 10.3 监控告警

```bash
# 监控仪表板
merlin-cli bytecli dashboard-create --json '{
  "dashboard_name": "order-service-production",
  "panels": [
    {
      "title": "错误率",
      "metric": "error_rate",
      "threshold": 5.0
    },
    {
      "title": "延迟P95",
      "metric": "latency_p95",
      "threshold": 200
    },
    {
      "title": "吞吐量",
      "metric": "throughput",
      "threshold": 1000
    }
  ],
  "refresh_interval": 30
}'

# 告警升级
merlin-cli bytecli alert-escalate --json '{
  "alert_id": "alert-001",
  "escalation_level": 2,
  "additional_approvers": ["sre-manager"]
}'
```

---

## 使用建议

1. **JSON-first 调用**：推荐使用 `--json` 参数进行调用，避免命令行参数解析问题
2. **参数验证**：在执行前使用 `--schema` 查看参数格式，使用 `--dry-run` 预览请求
3. **错误处理**：使用 `--verbose` 获取详细错误信息，结合审计日志进行排查
4. **批量操作**：对于多个应用的部署，使用批量操作提高效率
5. **监控集成**：部署后立即设置监控告警，及时发现和解决问题

## 故障排查

如果遇到问题：

1. 检查认证：`merlin-cli login`
2. 查看帮助：`merlin-cli bytecli --help`
3. 查看参数格式：`merlin-cli bytecli <command> --schema`
4. 预览请求：`merlin-cli bytecli <command> --json '{...}' --dry-run`
5. 查看日志：`merlin-cli logs --json '{"component": "bytecli"}'`

---

**注意**：生产环境操作需要相应权限，部分操作需要审批流程。请确保你有足够的权限并遵循公司的部署规范。