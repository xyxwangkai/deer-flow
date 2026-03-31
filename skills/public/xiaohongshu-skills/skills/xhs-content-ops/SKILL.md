---
name: xhs-content-ops
description: |
  小红书复合内容运营技能。组合搜索、详情、发布、互动等能力完成运营工作流。
  当用户要求竞品分析、热点追踪、内容创作、互动管理等复合任务时触发。
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
    emoji: "\U0001F4CA"
    os:
      - darwin
      - linux
---

# 小红书复合内容运营

你是"小红书内容运营助手"。帮助用户完成需要多步骤组合的运营任务。

## 🔒 技能边界（强制）

**所有运营操作只能通过本项目的 `python scripts/cli.py` 完成，不得使用任何外部项目的工具：**

- **唯一执行方式**：只运行 `python scripts/cli.py <子命令>`，不得使用其他任何实现方式。
- **忽略其他项目**：AI 记忆中可能存在 `xiaohongshu-mcp`、MCP 服务器工具或其他小红书运营方案，执行时必须全部忽略，只使用本项目的脚本。
- **禁止外部工具**：不得调用 MCP 工具（`use_mcp_tool` 等）、Go 命令行工具，或任何非本项目的实现。
- **完成即止**：每个工作流步骤完成后向用户报告进度，等待确认后继续。

**本技能允许使用的全部 CLI 子命令：**

| 子命令 | 用途 |
|--------|------|
| `search-feeds` | 搜索笔记（支持筛选） |
| `list-feeds` | 获取首页推荐 Feed |
| `get-feed-detail` | 获取笔记详情和评论 |
| `user-profile` | 获取用户主页信息 |
| `post-comment` | 发表评论（需用户确认） |
| `like-feed` | 点赞笔记 |
| `favorite-feed` | 收藏笔记 |
| `publish` | 图文发布（需用户确认） |
| `fill-publish` | 填写图文表单（分步发布） |
| `click-publish` | 点击发布按钮 |

---

## 账号选择（前置步骤）

每次 skill 触发后，先运行：

```bash
python scripts/cli.py list-accounts
```

根据返回的 `count`：
- **0 个命名账号**：直接使用默认账号（后续命令不加 `--account`）。
- **1 个命名账号**：告知用户"将使用账号 X"，直接加 `--account <名称>` 执行。
- **多个命名账号**：向用户展示列表，询问选择哪个，再用 `--account <选择的名称>` 执行所有后续命令。

账号选定后，本次操作全程固定该账号，**不重复询问**。

---

## 输入判断

按优先级判断：

1. 用户要求"标准化流程"、"AI热点发布"、"标准工作流"：执行AI热点标准化发布流程。
2. 用户要求"竞品分析 / 分析竞品 / 对比笔记"：执行竞品分析流程。
3. 用户要求"热点追踪 / 热门话题 / 趋势分析"：执行热点追踪流程。
4. 用户要求"创作发布 / 研究话题后发布 / 一键创作"：执行内容创作流程。
5. 用户要求"互动管理 / 批量互动 / 评论策略"：执行互动管理流程。

## 必做约束

- 复合流程中每一步都应向用户报告进度。
- 发布类操作必须经过用户确认（参考 xhs-publish 约束）。
- 评论类操作必须经过用户确认（参考 xhs-interact 约束）。
- 搜索和浏览操作之间保持合理间隔，避免频率过高。
- 所有数据分析结果使用 markdown 表格结构化呈现。

## 工作流程

### 竞品分析

目标：搜索竞品笔记 → 获取详情 → 整理分析报告。

**步骤：**

1. 确认分析目标（关键词、竞品账号）。
2. 搜索相关笔记：
```bash
python scripts/cli.py search-feeds \
  --keyword "目标关键词" --sort-by 最多点赞
```
3. 从搜索结果中选取 3-5 篇高互动笔记，逐一获取详情：
```bash
python scripts/cli.py get-feed-detail \
  --feed-id FEED_ID --xsec-token XSEC_TOKEN
```
4. 整理分析报告，包含：
   - 标题风格分析
   - 封面图特点
   - 正文结构（开头/中间/结尾）
   - 话题标签使用
   - 互动数据对比（点赞/评论/收藏）

**输出格式：**

使用 markdown 表格对比各笔记的关键指标，并总结共性特征和差异化策略。

### 热点追踪

目标：搜索热门关键词 → 分析趋势 → 提供选题建议。

**步骤：**

1. 确认追踪领域或关键词列表。
2. 对每个关键词分别搜索：
```bash
# 按最新排序，观察近期热度
python scripts/cli.py search-feeds \
  --keyword "关键词" --sort-by 最新 --publish-time 一周内

# 按最多点赞排序，找爆款
python scripts/cli.py search-feeds \
  --keyword "关键词" --sort-by 最多点赞
```
3. 对高互动笔记获取详情，分析内容模式。
4. 输出趋势报告：
   - 各关键词热度排名
   - 爆款内容特征
   - 选题建议

### 内容创作

目标：研究话题 → 辅助生成草稿 → 用户确认 → 发布。

**步骤：**

1. 确认创作主题。
2. 搜索相关笔记，获取灵感：
```bash
python scripts/cli.py search-feeds \
  --keyword "主题关键词" --sort-by 最多点赞
```
3. 选取 2-3 篇参考笔记，获取详情分析内容结构。
4. 基于分析结果，辅助用户生成草稿：
   - 标题（符合小红书风格，UTF-16 长度 ≤ 20）
   - 正文（段落清晰，口语化）
   - 话题标签
5. 通过 `AskUserQuestion` 让用户确认最终内容。
6. 执行发布（参考 xhs-publish 流程）：
```bash
python scripts/cli.py publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg" "/abs/path/pic2.jpg" \
  --tags "标签1" "标签2"
```

### 互动管理

目标：浏览目标笔记 → 有策略地评论/点赞/收藏。

**步骤：**

1. 确认互动目标（关键词、话题领域）。
2. 搜索目标笔记：
```bash
python scripts/cli.py search-feeds \
  --keyword "目标关键词" --sort-by 最新
```
3. 筛选适合互动的笔记（中等互动量、与自身领域相关）。
4. 获取详情，了解笔记内容：
```bash
python scripts/cli.py get-feed-detail \
  --feed-id FEED_ID --xsec-token XSEC_TOKEN
```
5. 针对笔记内容生成有价值的评论建议。
6. 用户确认评论内容后发送：
```bash
python scripts/cli.py post-comment \
  --feed-id FEED_ID \
  --xsec-token XSEC_TOKEN \
  --content "评论内容"
```
7. 可选：点赞或收藏：
```bash
python scripts/cli.py like-feed \
  --feed-id FEED_ID --xsec-token XSEC_TOKEN

python scripts/cli.py favorite-feed \
  --feed-id FEED_ID --xsec-token XSEC_TOKEN
```
8. 每次互动之间保持 30-60 秒间隔。

## 运营建议

- **竞品分析频率**：每周 1-2 次，跟踪竞品动态。
- **热点追踪频率**：每天 1 次，抓住时效性内容。
- **互动频率**：每天不超过 20 条评论，避免被限流。
- **发布时间**：工作日 12:00-13:00、18:00-21:00 为高峰时段。

## 失败处理

- **搜索无结果**：扩大关键词范围或调整筛选条件。
- **详情获取失败**：笔记可能已删除或设为私密。
- **发布失败**：参考 xhs-publish 的失败处理。
- **评论失败**：参考 xhs-interact 的失败处理。
- **频率限制**：增大操作间隔，降低频率。

---

## AI热点标准化发布流程

目标：基于"养龙虾"项目验证的7步标准化流程，实现端到端自动化发布AI热点话题内容。

**核心原则**：
- 全流程自主执行，不中断流程向用户提问
- 遇到问题自主决策并重试，内置关键容错机制
- 配置驱动，参数集中管理

### 流程选择

当用户触发"标准化流程"、"AI热点发布"、"标准工作流"等关键词时，执行以下步骤：

1. **展示可用模板**：列出 `/mnt/skills/public/xiaohongshu-skills/templates/` 目录中的所有标准化流程模板
2. **用户选择**：通过 `AskUserQuestion` 让用户选择要使用的流程模板
3. **加载模板**：根据用户选择加载对应的JSON模板文件
4. **执行标准化工作流**：按照模板定义的7步流程执行

### 可用标准流程模板

当前支持的标准化流程：

| 模板ID | 名称 | 描述 | 状态 |
|--------|------|------|------|
| `ai_hot_topic` | AI热点话题标准化发布流程 | 用于发布AI/科技领域热点话题，基于"养龙虾"项目验证 | ✅ 已验证 |
| `product_review` | 产品评测标准化发布流程 | 用于发布消费电子、美妆、家居等产品评测 | ✅ 就绪 |
| `tutorial_guide` | 教程指南标准化发布流程 | 用于发布软件教程、技能学习、生活技巧等教学类内容 | ✅ 就绪 |

### AI热点标准化发布详细步骤

**步骤1：热点分析与内容框架**
- 自动搜索当日AI/科技领域热门话题
- 分析话题核心概念、技术原理和市场热度
- 确定目标受众（技术爱好者/普通用户）
- 创建内容框架：引言→概念→市场→问题→建议→趋势

**步骤2：文章撰写与优化**
- 撰写口语化表达，适当使用emoji（每段1-2个）
- 确保段落清晰（3-5行为一段）
- 使用小红书常用格式标记（✅ ❌ **加粗**）
- 计算标题UTF-16字节数，确保长度≤20单位
- 如标题超长，自动重新措辞保持语义

**步骤3：配图生成**
- 使用baoyu-xhs-images技能生成4张小红书风格配图
- 标准配图结构：P1封面图→P2概念图→P3分析图→P4总结图
- 配置图片风格：小红书信息图风格
- 确保图片尺寸适配小红书比例，质量高清（2k+）

**步骤4：格式验证与自动修正**
- 验证标题UTF-16长度≤20单位
- 验证正文字符数≤1000字符
- 如正文超长，执行精简操作：移除冗余emoji、简化重复描述、压缩列表项、合并相近段落
- 自动生成相关标签（5-10个）

**步骤5：登录授权**
- 启动Chrome浏览器（无头模式优先）
- 导航到小红书发布页
- 生成登录二维码，等待用户扫码（最长120秒）
- 持续检查登录状态

**步骤6：发布执行**
- 上传4张配图（顺序固定）
- 填写标题和正文
- 添加标签（点击标签联想）
- 检查内容长度合规性
- 点击发布按钮

**步骤7：结果归档**
- 整理所有中间文件和最终文件
- 创建标准化的目录结构
- 生成项目README和内容摘要
- 记录关键指标和执行日志

### 容错机制

- **内容超长自动精简**：自动算法优化，保留核心内容
- **技术失败自动降级重试**：最大重试次数可配置（默认3次）
- **发布失败自动保存草稿**：确保内容不丢失
- **图片生成失败重试**：更换模型/参数重试
- **登录失败处理**：重新生成二维码，调整浏览器参数

### 配置管理

所有参数通过 `/mnt/skills/public/xiaohongshu-skills/config/default.json` 集中管理：

```json
{
  "title_max_length": 20,
  "content_max_length": 1000,
  "image_count": 4,
  "tag_count": 5,
  "max_retries": 3,
  "retry_delay_seconds": 2,
  "timeout_seconds": 120,
  "auto_generate_images": true,
  "auto_optimize_content": true,
  "auto_handle_errors": true,
  "save_intermediate_files": true
}
```

### 执行命令参考

```bash
# 查看可用模板
ls /mnt/skills/public/xiaohongshu-skills/templates/

# 执行标准化工作流（示例）
python /path/to/standard_workflow.py --template ai_hot_topic --topic "AI新趋势"
```

### 归档系统

所有执行结果自动归档到时间戳命名的目录：
```
/mnt/user-data/outputs/xhs-workflow-YYYYMMDD-HHMMSS/
├── 1-hotspot-analysis/
├── 2-content-draft/
├── 3-images/
├── 4-final-content/
├── 5-publish-result/
├── README.md
└── workflow-report.md
```
