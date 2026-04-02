# evaluation_task_conf 高级配置

`exercise run` 的 `evaluation_task_conf` 字段支持丰富的评估配置。本文档覆盖 SKILL.md 中未详述的高级选项。

## 目录

- [模型配置 (model)](#模型配置-model)
- [推理引擎 (inference_engine)](#推理引擎-inference_engine)
- [预计算来源 (precompute_source)](#预计算来源-precompute_source)
- [配置类型 (config_type)](#配置类型-config_type)
- [环境变量与启动参数](#环境变量与启动参数)
- [开关类选项](#开关类选项)
- [资源配置详细字段](#资源配置详细字段)

## 模型配置 (model)

通过 `evaluation_task_conf.model` 控制模型加载方式：

```json
"model": {
  "model_provider": "megatron",
  "template": "llama3",
  "model_structure": "M8",
  "model_format": "megatron",
  "generation": {
    "temperature": 0.7,
    "generate_topk": 50,
    "generate_topp": 0.9
  }
}
```

| 字段 | 说明 |
|------|------|
| `model_provider` | 模型提供方（如 `megatron`、`hf`） |
| `template` | 模型对话模板（如 `llama3`、`qwen`） |
| `model_structure` | 模型结构（如 `M8`、`M12`、`QwenMoe`） |
| `model_format` | 模型文件格式（如 `megatron`、`hf`） |
| `generation` | 生成参数：`temperature`、`generate_topk`、`generate_topp`、`generate_config_override` |

## 推理引擎 (inference_engine)

指定评估使用的推理引擎：

```json
"inference_engine": "xperf_gpt"
```

常见值：`xperf_gpt`（默认）。Server mode 场景下会使用不同引擎配置。

## 预计算来源 (precompute_source)

当已有模型预测结果（无需重新推理，只需计算指标）时使用：

```json
"precompute_source": {
  "source_type": "evaluation_instance_sid",
  "evaluation_instance_sid": "xxx",
  "custom_model_name": "my-model"
}
```

| 字段 | 说明 |
|------|------|
| `source_type` | 来源类型：`lark_sheet`、`evaluation_instance_sid`、`hdfs` |
| `evaluation_instance_sid` | 复用已有评估实例的预测结果 |
| `hdfs_path` | HDFS 上的预测结果文件 |
| `model_prediction_lark_url` | 飞书表格中的预测结果 |
| `custom_model_name` | 自定义模型显示名 |

## 配置类型 (config_type)

控制评估配置的来源：

| 值 | 说明 |
|------|------|
| `FORM` | 通过表单字段配置（默认） |
| `TEMPLATE` | 使用预定义模板 |
| `HDFS` | 从 HDFS 加载配置文件，需配合 `config_hdfs_path` |

```json
"config_type": "HDFS",
"config_hdfs_path": "hdfs://path/to/eval_config.yaml"
```

## 环境变量与启动参数

| 字段 | 说明 | 示例 |
|------|------|------|
| `env` | 注入到评估任务的环境变量 | `{"CUDA_VISIBLE_DEVICES": "0,1"}` |
| `extra_flags` | 追加到启动命令的额外参数 | `"--timeout 3600 --verbose"` |

## 开关类选项

| 字段 | 说明 | 默认 |
|------|------|------|
| `is_cot` | 启用 Chain-of-Thought 模式 | `false` |
| `is_dev` | 开发模式（影响日志级别等） | `false` |
| `use_cache` | 使用 Ray job 缓存 | `false` |
| `is_high_priority` | 高优先级任务（插队） | `false` |

## 资源配置详细字段

SKILL.md 中介绍了 `resource` 的核心字段（`group_id`、`cluster_id`、`queue_name`）。完整字段：

| 字段 | 说明 |
|------|------|
| `group_id` | 资源组 ID（必填） |
| `cluster_id` | 集群 ID（必填） |
| `queue_name` | Arnold 队列名称 |
| `gpuv` | GPU 类型（如 `A100`、`V100`） |
| `cpu` | CPU 核数 |
| `memory` | 内存大小（MB） |
| `quota_pool` | 资源池类型（`default`、`hybrid` 等） |
| `ray_num_replicas` | Ray worker 副本数 |
| `ray_num_gpus` | 每个 Ray worker 的 GPU 数 |
| `queue_priority` | 队列优先级 |
| `auto_public_resource` | 是否自动使用公共资源 |
| `server_roles` | Server mode 角色配置列表 |
