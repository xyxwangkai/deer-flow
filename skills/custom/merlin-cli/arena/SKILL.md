---
name: arena
description: Seed Arena 评估数据拉取与失败排查。当用户说"拉取评估任务数据/导出 Arena 评估明细/根据 evaluation_task_sid 获取 case 得分/下载 arena evaluation 结果/给我这个评估链接的详细数据/Arena 任务失败怎么查/帮我定位 Arena 失败原因/根据 Arena 链接修复"时使用。
---

# Arena 评估

Arena 评估数据拉取和失败任务排查。

## 前置条件

```bash
merlin-cli --help &>/dev/null || \
  curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash
```

如果出现认证错误（401/403），运行 `merlin-cli login`。

---

## 1. 评估数据拉取

给定 Arena 评估任务链接（带 `evaluation_task_sid`）或直接给 `evaluation_task_sid`，拉取评估概览、exercise 得分和 case 明细。

### 输入

- 完整链接：`https://seed.bytedance.net/evaluation/arena/<arena_sid>?evaluation_task_sid=<sid>`
- 或直接给 `evaluation_task_sid`（如 `3k5ywg90c169a972be`）

### CLI 命令

```bash
merlin-cli arena get-evaluation --json '{"sid": "<evaluation_task_sid>"}'

merlin-cli arena list-case --json '{"evaluation_task_sid": "xxx", "exercise_version_sid": "yyy", "limit": 50}'

merlin-cli arena export-case-detail --json '{"evaluation_task_sid": "xxx", "exercise_version_sid": "yyy"}'
```

### 推荐：使用脚本

脚本自动解析 URL、拉取概览、聚合 exercise 得分，可选拉取 case 明细。

只拉取概览与 exercise 得分：

```bash
python3 skills/arena/scripts/fetch_arena_evaluation.py \
  --url "USER_URL_OR_SID" \
  --out-dir "./arena_eval_export"
```

同时拉取 case 明细：

```bash
python3 skills/arena/scripts/fetch_arena_evaluation.py \
  --url "USER_URL_OR_SID" \
  --out-dir "./arena_eval_export" \
  --fetch-cases \
  --max-exercises-for-cases 10 \
  --cases-per-exercise 50
```

全量导出时，把 `--max-exercises-for-cases` 设为 `0`。

### 输出文件

- `arena_evaluation.raw.json`：原始输出
- `exercises.csv`：每个 exercise 的基础信息与得分
- `report.md`：可读摘要
- `cases/*.jsonl`：（开启 `--fetch-cases` 时）每个 exercise_version_sid 一个文件

交付时给出 `report.md` 要点摘要和文件路径。

---

## 2. 失败任务排查

通过 Arena URL 定位关联的 Merlin Job，委托 `job-troubleshoot-failure` 完成根因分析。

### 步骤

1. **解析 Arena URL → Merlin Job**

```bash
merlin-cli arena get-job-from-url --json '{"arena_url": "<arena_page_url>"}'
```

从返回中提取 `result.job_url` 或 `result.job_run_id`，拼接为 Job 链接：
`https://ml.bytedance.net/development/instance/jobs/<job_run_id>`

兆底（MCP 工具不可用时）：

```bash
merlin-cli arena get-evaluation --json '{"sid": "<evaluation_task_sid>"}'
```

多个候选时，用 `merlin-cli job get-run` 对比 `status` 与 `startTime`，选最近失败的 Job。

2. **委托 troubleshoot-failure**

将解析到的 Merlin Job 链接传给技能 `job-troubleshoot-failure`，由其完成失败信息拉取、根因归因和修复建议。

### 输出格式

1. **失败概述**：一句话总结
2. **关键信息**：Job ID、Trial ID、退出码、失败时间
3. **诊断依据**：关键日志摘录
4. **修复建议**：具体到资源/入口/依赖
5. **自动修复结果**（如有）：新任务链接与结果

---

## 3. Arena 配置查询

可以查询 Merlin Arena 的配置列表或获取指定配置的详细信息。

### CLI 命令

列出 Arena 配置：

```bash
merlin-cli arena list-config --json '{"limit": 10, "offset": 0}'
```

获取指定 Arena 配置的详情：

```bash
merlin-cli arena get-config --json '{"sid": "<arena_sid>"}'
```

## 4. 复制（Fork）评估任务

基于已有 `evaluation_task_sid` 创建一个新评估任务，可按需覆盖 Arena 版本、模型、分支/commit、评估集合、生成参数、资源、env 等。

```bash
merlin-cli arena fork-evaluation --json '{
  "source_evaluation_task_sid": "<evaluation_task_sid>",
  "arena_sid": "<target_arena_sid>",
  "titan_model_sids": ["<titan_model_sid_1>"]
}'
```

不想改动的字段不传即可（默认复用原任务）。

---

## 常见排错

- `merlin-cli: command not found`：先安装/升级 merlin-cli
- 401/403：运行 `merlin-cli login`
- case 太多导致慢：先只导出 `exercises.csv`，再指定 `--exercise-version-sid` 精准拉取

## 关联技能

- `job-troubleshoot-failure`：Merlin Job 失败排查与修复建议
- `insight`：Insight 分析与案例查询
- `eval-get-result`：获取评估实例指标结果
