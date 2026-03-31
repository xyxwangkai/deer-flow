# EXTEND.md

`eat` 是一个知识吸收元技能。这里定义更细的落库策略、评分规则和可执行转换约束。

## 1. 吸收成熟度分级

把知识源按成熟度划分为 4 级：

### L1：见闻
特征：只有观点，没有结构化方法。
处理：只做记录，不进入核心技能库。

### L2：套路
特征：有明确步骤、框架或模板，可在相似任务复用。
处理：进入 `references/` 或 `examples/`。

### L3：能力
特征：已能映射为稳定 SOP、命令流程、脚本模板。
处理：进入 `SKILL.md`、`EXTEND.md` 或 `scripts/`。

### L4：基础设施
特征：可长期复用，能显著增强 agent 的完成能力。
处理：优先升级为独立 skill，或成为现有技能的关键子模块。

## 2. 吸收评分框架

建议按 5 个维度各打 1~5 分：

- **复用性**：是否能跨任务复用
- **稳定性**：是否不是一次性技巧
- **可验证性**：是否能被测试、演示、对照
- **实现性**：是否能落到文档、脚本或 skill
- **增益性**：是否明显提升 agent 能力上限

### 判定建议
- 总分 ≤ 10：只做摘要，不落库
- 11~17：写入 `references/` 作为备忘知识
- 18~22：转为模板 / 示例 / EXTEND 策略
- 23~25：优先升级为新 skill 或核心扩展

## 3. GitHub 仓库吸收指南

分析仓库时，优先阅读：

1. `README*`
2. `package.json` / `pyproject.toml` / `requirements.txt`
3. `src/`、`app/`、`core/`、`scripts/`
4. `examples/`、`docs/`
5. CI/CD 与配置文件（如 `.github/workflows/`, `Dockerfile`）

### 重点提炼项
- 模块划分
- 主入口
- 数据流 / 控制流
- 依赖外部系统的位置
- 最值得借鉴的 3 个设计决定

## 4. 图片/长图吸收指南

如果用户提供的是截图：

1. 先说明是否可读
2. 尽量提取标题、分段、流程箭头、关键短语
3. 标出不确定部分
4. 如信息缺失严重，要求用户补 OCR 或原文

## 5. 技能化落地模板

当判断值得技能化时，建议生成以下结构：

```text
<skill-name>/
├── SKILL.md
├── EXTEND.md
├── references/
│   ├── concepts.md
│   └── patterns.md
├── scripts/
│   └── transform.py
└── examples/
    ├── input.md
    └── output.md
```

## 6. 吸收结果 JSON Schema

可将吸收结果标准化为：

```json
{
  "source_type": "repo|article|image|doc|mixed",
  "title": "",
  "summary": "",
  "score": {
    "reusability": 0,
    "stability": 0,
    "verifiability": 0,
    "implementability": 0,
    "leverage": 0,
    "total": 0
  },
  "principles": [],
  "patterns": [],
  "assets": {
    "skills": [],
    "references": [],
    "scripts": [],
    "examples": []
  },
  "next_actions": []
}
```

## 7. 与现有技能库的关系

不要为了“新”而强行创建新 skill。

优先顺序：
1. 补充现有 skill 的 `references/` 或 `EXTEND.md`
2. 给现有 skill 增加 `scripts/` 或 `examples/`
3. 只有在形成独立触发意图、独立工作流时，才创建新 skill

## 8. 推荐联动模式

- 与 `skill-creator` 联动：把吸收结果转成 skill skeleton
- 与 `deep-research` 联动：对外部主题做多轮研究后再吸收
- 与 `github-deep-research` 联动：对 GitHub 项目做深入理解后再沉淀

## 9. 输出建议

如果用户没有指定格式，建议输出：

1. 吸收结论
2. 值得沉淀的 5 条知识
3. 应写入哪些文件
4. 我可以继续帮你做什么
