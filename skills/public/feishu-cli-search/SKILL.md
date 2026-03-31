---
name: feishu-cli-search
description: >-
  搜索飞书文档、Wiki、消息和应用。当用户请求“搜索飞书文档”、“搜一下飞书里有没有 xxx”、
  “查聊天记录里的关键词”、“搜索飞书消息”、“找某个应用”、“有没有关于某主题的飞书资料”时使用。
  这个技能适合关键词检索与范围缩小；如果用户其实是想直接阅读具体文档，请优先用 `feishu-cli-read`。
  搜索依赖 User Access Token，若当前认证缺失或 scope 不足，应先切到 `feishu-cli-auth` 处理。
user-invocable: true
allowed-tools: Bash
---

# 飞书搜索

用于在飞书里搜索：
- 云文档 / Wiki
- 消息记录
- 应用

## 适用范围

优先用于这些场景：
- 用户知道主题，但不知道具体文档在哪
- 用户要按关键词找消息记录
- 用户要查某个飞书应用是否存在
- 用户想先缩小范围，再决定读哪个文档

这个技能**不负责**：
- 直接阅读具体文档内容（请用 `feishu-cli-read`）
- 聊天记录浏览、群消息总结、群管理（请用 `feishu-cli-chat`）
- 发消息（请用 `feishu-cli-msg`）

## 使用原则

1. 搜索前先确认 User Token 可用。
2. 若认证有问题，优先提示用户先完成认证，而不是盲目重试搜索。
3. 先给出最相关结果，再决定是否继续缩小范围。
4. 如果用户已经给出明确 document_id / url，就不该继续搜索，应改用读取技能。

## 搜索前检查

先检查认证状态：

```bash
feishu-cli auth status -o json
```

如果出现以下情况，先切到 `feishu-cli-auth`：
- `logged_in=false`
- token 已完全过期
- scope 缺失（例如缺少 `search:docs:read` 或 `search:message`）

## 常见搜索命令

### 搜索文档 / Wiki

```bash
feishu-cli search docs "关键词"
```

常见补充参数：
- `--docs-types doc,sheet`
- `--count 10`
- `--offset 0`

适用：
- “找关于 OKR 的文档”
- “有没有季度复盘”
- “搜一下某个项目的 wiki”

### 搜索消息

```bash
feishu-cli search messages "关键词"
```

可按 chat 缩小范围：

```bash
feishu-cli search messages "关键词" --chat-ids oc_xxx,oc_yyy
```

适用：
- “搜一下谁提过这个 bug”
- “查聊天记录里有没有某个决定”

### 搜索应用

```bash
feishu-cli search apps "关键词"
```

适用：
- “找一下审批应用”
- “看看有没有内部工具”

## 结果处理建议

### 用户只想知道“有没有”
返回最相关的前几条结果即可，不必展开太多。

### 用户要继续阅读
如果搜索结果已经定位到具体文档：
1. 给出候选项
2. 询问或判断最相关文档
3. 切到 `feishu-cli-read` 读取具体内容

### 用户要继续看聊天内容
如果用户不是做关键词搜索，而是想看某个群最近聊什么：
- 不继续用搜索硬做
- 直接改走 `feishu-cli-chat`

## 高概率排错场景

### 报 Unauthorized / 没权限
通常不是搜索命令本身坏了，而是：
- 没登录
- token 过期
- scope 不足

先检查认证状态，再决定是否重新授权。

### 有结果但不全
可能原因：
- 关键词太宽或太窄
- chat/doc 类型过滤过严
- 当前 User Token 对部分资源无权限

优先调整查询词，而不是默认判断系统异常。

## 最小工作流

### 场景：用户说“搜一下飞书里有没有 OKR 模板”
1. 先检查 `auth status -o json`
2. 若认证正常，执行 `feishu-cli search docs "OKR 模板"`
3. 返回最相关结果
4. 如果用户要打开其中一篇，切到 `feishu-cli-read`

### 场景：用户说“查聊天记录里谁提过这个需求”
1. 先检查 `auth status -o json`
2. 执行 `feishu-cli search messages "需求关键词"`
3. 返回匹配消息
4. 如果用户要看上下文或整段对话，切到 `feishu-cli-chat`
