---
name: feishu-cli-vc
description: >-
  飞书视频会议与妙记只读查询。适用于搜索历史会议、查看会议纪要、读取逐字稿、查看妙记基础信息。
  当用户请求“搜索会议”、“查看会议记录”、“读取会议纪要”、“看妙记”、“找逐字稿”、
  “最近有哪些会议”时使用。这个技能主要做会议资料的检索和阅读；如果用户是在查聊天记录，
  请优先使用 `feishu-cli-chat`。如果用户是在搜索普通文档或消息关键词，请优先使用 `feishu-cli-search`。
user-invocable: true
allowed-tools: Bash, Read
---

# 飞书视频会议与妙记

用于查询飞书视频会议历史、会议纪要和妙记内容。

## 适用范围

优先用于这些场景：
- 找最近开过哪些会议
- 查看某次会议纪要
- 获取逐字稿或妙记摘要
- 根据会议号或时间范围筛选会议记录

这个技能**不负责**：
- 聊天记录浏览（请用 `feishu-cli-chat`）
- 普通文档或消息搜索（请用 `feishu-cli-search`）
- 日历创建和会议安排（请用 `feishu-cli-toolkit` 中的日历能力）

## 使用原则

1. 这是一个以只读为主的技能。
2. 先定位会议，再读取纪要或妙记。
3. 如果用户给的是模糊描述，优先按时间范围或会议号缩小范围。

## 常见命令

### 搜索历史会议

```bash
feishu-cli vc search
```

常见筛选：
- `--start <timestamp>`
- `--end <timestamp>`
- `--meeting-no <meeting_no>`
- `--meeting-status 2`

### 获取会议纪要

```bash
feishu-cli vc notes --meeting-id <meeting_id>
```

或：

```bash
feishu-cli vc notes --minute-token <minute_token>
```

### 获取妙记基础信息

```bash
feishu-cli minutes get <minute_token>
```

## 最小工作流

### 场景：用户说“看看最近有哪些会议”
1. 先执行 `feishu-cli vc search`
2. 必要时加时间范围缩小范围
3. 返回会议列表

### 场景：用户说“把这次会议纪要总结一下”
1. 先定位会议 ID 或 minute token
2. 获取 notes 或妙记信息
3. 再对内容做总结

### 场景：用户说“找某个项目的会议记录”
1. 先按时间或会议号筛一轮
2. 若结果较多，先返回候选项
3. 再读取用户指定那一场的纪要
