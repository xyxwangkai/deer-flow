---
name: feishu-cli-chat
description: >-
  浏览飞书单聊/群聊消息、查看聊天记录、总结群里最近讨论、搜索群聊、查看消息详情，以及管理与消息互动相关的操作。
  当用户请求“看看群里最近在聊什么”、“查看聊天记录”、“总结最近消息”、“看和某人的对话”、
  “搜索群聊”、“查群成员”、“Pin/Reaction/删除消息”时使用。适用于需要浏览会话上下文和按群查看消息的场景；
  如果用户只是要发消息、回复、转发或发卡片，请优先使用 `feishu-cli-msg`。所有修改消息状态、群信息或成员的操作，执行前必须先获得用户明确确认。
user-invocable: true
allowed-tools: Bash, Read
---

# 飞书会话浏览与群聊管理

用于查看飞书聊天记录、按群浏览消息、查看消息详情，以及处理与消息互动和群管理相关的操作。

## 适用范围

优先用于这些场景：
- 看某个群最近在聊什么
- 查和某人的消息记录
- 总结群聊最近讨论内容
- 根据群名找 chat_id
- 查群成员
- 对已有消息做 pin / reaction / 删除等互动操作
- 查看群信息、更新群信息、管理群成员

这个技能**不负责**：
- 主动发送消息、回复、转发、发送卡片（请用 `feishu-cli-msg`）
- 关键词全文搜索整个飞书（请用 `feishu-cli-search`）
- OAuth 登录与 token 排错（请用 `feishu-cli-auth`）

## 前置条件

大多数核心命令依赖 **User Token**。

先检查认证状态：

```bash
feishu-cli auth status -o json
```

如果未登录、token 过期或 scope 不足，先切到 `feishu-cli-auth`。

## 使用原则

1. 优先读消息，不要默认做写操作。
2. 如果用户只是想知道“最近聊了什么”，先获取最近消息，再做总结。
3. 对 pin / reaction / 删除消息 / 群更新 / 成员变更 这类操作，必须先确认。
4. 如果用户只是说“发个消息给某人”，不要走这个技能，应切到 `feishu-cli-msg`。

## 常见工作流

### 场景一：查看某个群最近消息

如果用户给的是群名，先找群：

```bash
feishu-cli msg search-chats --query "群名关键词" -o json
```

拿到 `chat_id` 后查看最近消息：

```bash
feishu-cli msg history --container-id <chat_id> --container-id-type chat
```

适合：
- “看看这个群最近在聊什么”
- “总结下这个群今天的讨论”

### 场景二：查看某条消息详情

```bash
feishu-cli msg get <message_id>
```

适合：
- 用户已经提供 message_id
- 需要看某条消息的完整内容或结构

### 场景三：查看群信息或成员

```bash
feishu-cli chat get <chat_id>
feishu-cli chat member list <chat_id>
```

适合：
- “查下这个群是谁在里面”
- “看看这个群的配置”

## 高影响操作

以下操作执行前必须先获得用户明确确认：

### 消息互动 / 状态修改
```bash
feishu-cli msg pin <message_id>
feishu-cli msg unpin <message_id>
feishu-cli msg reaction add <message_id> --emoji-type THUMBSUP
feishu-cli msg reaction remove <message_id> --reaction-id <reaction_id>
feishu-cli msg delete <message_id>
```

### 群信息修改
```bash
feishu-cli chat update <chat_id> --name "新群名"
feishu-cli chat member add <chat_id> --id-list id1,id2
feishu-cli chat member remove <chat_id> --id-list id1,id2
feishu-cli chat delete <chat_id>
```

## 什么时候切到别的技能

- 用户要“发消息 / 回消息 / 转发 / 发卡片” → `feishu-cli-msg`
- 用户要“按关键词搜整个飞书消息或文档” → `feishu-cli-search`
- 用户要“登录飞书 / token 过期 / scope 不够” → `feishu-cli-auth`

## 最小工作流

### 场景：用户说“看看群里最近聊了什么”
1. 先确认是否已登录
2. 若用户给的是群名，先 `search-chats`
3. 用 `msg history` 拉最近消息
4. 汇总重点内容返回给用户

### 场景：用户说“把这条消息置顶”
1. 先确认目标消息 ID
2. 明确征求用户确认
3. 再执行 pin 命令

### 场景：用户说“发个消息给这个群”
不要继续用本技能，改切到 `feishu-cli-msg`。
