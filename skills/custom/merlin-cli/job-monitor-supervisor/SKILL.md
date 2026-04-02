---
name: job-monitor-supervisor
description: 任务监控总调度，自动调度子代理监控日志、Tracking 指标和伴生评估。
---

# 任务监控 Supervisor

## 摘要

本技能作为 Supervisor，负责分析任务配置并调度子代理执行具体监控。

## ⚠️ 核心要求：必须使用 Task 工具调度子代理

**你必须使用 Task 工具来调度子代理执行监控任务，禁止自己直接执行所有监控逻辑。**

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor (你)                          │
│  - 分析任务配置，确定监控类型                                  │
│  - 使用 Task 工具调度子代理                                   │
│  - 等待子代理完成，汇总结果                                    │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ job-operations  │ │ tracking-       │ │ companion-eval  │
│                 │ │ experiment      │ │                 │
│                 │ │                 │ │                 │
│ 独立 Skill      │ │ 独立 Skill      │ │ 独立 Skill      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 可用的子 Skills

| Skill 名称 | 用途 |
|-----------|------|
| `job-operations` | 监控任务日志，分析训练进度 |
| `tracking-experiment` | 监控 Tracking 指标趋势 |
| `companion-eval` | 监控伴生评估结果 |

## 执行流程

### 步骤 1：任务分析与初始化

```
1. 调用 `merlin-cli job get-run` 获取任务详情
2. 分析入口命令参数，确定需要的监控类型：
   - 日志监控：所有任务都需要 → 调度 job-operations
   - Tracking 监控：入口命令包含 trainer.project_name → 调度 tracking-experiment
   - 伴生评估：入口命令包含 trainer.default_hdfs_dir → 调度 companion-eval
3. 创建输出目录: /tmp/job_monitor_{job_run_id}_{timestamp}/
```

### 步骤 2：调度子代理（必须使用 Task 工具）

根据任务配置，**使用 Task 工具并行调度**对应的子代理。

#### 调度日志监控子代理

```
Task({
  "subagent_type": "general_purpose_task",
  "description": "日志监控",
  "query": "请使用 job-operations skill 监控任务日志。\n\n任务参数：\n- job_run_id: \"{job_run_id}\"\n- output_file: \"{output_dir}/log_report.md\"\n\n请按照 skill 的指引执行监控。",
  "response_language": "zh-CN"
})
```

#### 调度 Tracking 监控子代理

```
Task({
  "subagent_type": "general_purpose_task",
  "description": "Tracking监控",
  "query": "请使用 tracking-experiment skill 监控 Tracking 指标。\n\n任务参数：\n- job_run_id: \"{job_run_id}\"\n- output_file: \"{output_dir}/tracking_report.md\"\n\n请按照 skill 的指引执行监控。",
  "response_language": "zh-CN"
})
```

#### 调度伴生评估监控子代理

```
Task({
  "subagent_type": "general_purpose_task",
  "description": "伴生评估监控",
  "query": "请使用 companion-eval skill 监控伴生评估。\n\n任务参数：\n- job_run_id: \"{job_run_id}\"\n- output_file: \"{output_dir}/eval_report.md\"\n\n请按照 skill 的指引执行监控。",
  "response_language": "zh-CN"
})
```

### 步骤 3：等待子代理完成并汇总结果

等待所有 Task 子代理完成后：

1. 读取各子代理的输出文件 (log_report.md, tracking_report.md, eval_report.md)
2. 合并为统一的监控报告
3. 检查是否有需要关注的问题（alerts/issues）
4. 调用 lark-doc-create-from-markdown 发布飞书文档

## 完整执行示例

```
用户输入: 监控任务 job-123456 的进度

Supervisor 执行:

1. merlin-cli job get-run --json '{"job_run_id": "job-123456"}'
   返回: 入口命令包含 trainer.project_name=proj1, trainer.default_hdfs_dir=hdfs://xxx
   
2. 确定监控类型: 日志 ✓, Tracking ✓, 伴生评估 ✓

3. 创建输出目录: /tmp/job_monitor_job-123456_20240114/

4. 并行调用 Task 工具调度三个子代理:
   
   Task({
     "subagent_type": "general_purpose_task",
     "description": "日志监控",
     "query": "请使用 job-operations skill 监控任务日志。\n\n任务参数：\n- job_run_id: \"job-123456\"\n- output_file: \"/tmp/job_monitor_job-123456_20240114/log_report.md\"\n\n请按照 skill 的指引执行监控。",
     "response_language": "zh-CN"
   })
   
   Task({
     "subagent_type": "general_purpose_task", 
     "description": "Tracking监控",
     "query": "请使用 tracking-experiment skill 监控 Tracking 指标。\n\n任务参数：\n- job_run_id: \"job-123456\"\n- output_file: \"/tmp/job_monitor_job-123456_20240114/tracking_report.md\"\n\n请按照 skill 的指引执行监控。",
     "response_language": "zh-CN"
   })
   
   Task({
     "subagent_type": "general_purpose_task",
     "description": "伴生评估监控", 
     "query": "请使用 companion-eval skill 监控伴生评估。\n\n任务参数：\n- job_run_id: \"job-123456\"\n- output_file: \"/tmp/job_monitor_job-123456_20240114/eval_report.md\"\n\n请按照 skill 的指引执行监控。",
     "response_language": "zh-CN"
   })

5. 等待所有子代理完成

6. 读取输出文件，汇总结果，生成最终报告

7. 调用 lark-doc-create-from-markdown 发布飞书文档
```

## 输入

- 一个或多个 Merlin 任务的 ID 或 URL

## 输出

- 一个包含任务全方位进度信息的飞书文档链接

## 注意事项

1. **子代理使用独立 Skill**：每个子代理引用对应的 skill (job-operations, tracking-experiment, companion-eval)
2. **并行调度**：可以同时调用多个 Task 工具，让子代理并行执行
3. **参数替换**：调用 Task 时，需要将 {job_run_id}、{output_dir} 等占位符替换为实际值
