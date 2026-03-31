---
name: feishu-cli-auth
description: >-
  飞书 OAuth 认证、User Access Token 状态检查、scope 排错与登录流程管理。当用户请求“登录飞书”、
  “获取 User Token”、“OAuth 授权”、“Token 过期了”、“刷新 Token”、“搜索为什么没权限”、
  “99991672/99991679 是什么问题”、“检查飞书认证状态”时使用。也适用于其他 feishu-cli 技能
  需要 User Token 但当前授权缺失、过期或 scope 不足的场景。创建应用、批量申请 scope、改写本地认证配置
  都属于高影响操作，执行前必须先获得用户明确确认。
user-invocable: true
allowed-tools: Bash, Read
---

# 飞书认证与 Token 管理

用于管理 feishu-cli 所需的 **User Access Token**，以及排查 scope、过期时间、回调流程等认证问题。

## 适用范围

这个技能主要处理：
- 检查当前是否已登录
- 判断 token 是否过期
- 判断 scope 是否缺失
- 引导用户完成两步式 OAuth 登录
- 解释常见认证报错

这个技能**不负责**：
- 搜索文档/消息本身（请用 `feishu-cli-search`）
- 浏览聊天记录或群管理（请用 `feishu-cli-chat`）
- 文档读写、导入导出、权限管理（请用对应 feishu-cli 子技能）

## 操作原则

1. 优先做只读检查：先看 `auth status`，再决定是否需要登录。
2. 只有在用户明确要登录或修复认证时，才进入 OAuth 流程。
3. 创建应用、申请 scope、改写本地认证配置属于高影响动作，必须先确认。
4. 如果只是搜索权限不足，先解释缺哪个 scope，再决定是否重新授权。

## 常用检查

先检查当前状态：

```bash
feishu-cli auth status -o json
```

重点看这些字段：
- `logged_in`
- `access_token_valid`
- `refresh_token_valid`
- `scope`

常见判断：
- `logged_in=false` → 还没登录，需要授权
- `access_token_valid=false` 且 `refresh_token_valid=true` → 下次调用时通常可自动刷新
- `access_token_valid=false` 且 `refresh_token_valid=false` → 需要重新登录
- scope 缺少目标权限 → 需要重新授权并补 scope

## 两步式登录流程

当需要登录或重新授权时，优先使用非交互两步式流程。

### 第一步：生成授权链接

```bash
feishu-cli auth login --print-url --scopes "offline_access search:docs:read search:message drive:drive.search:readonly wiki:wiki:readonly calendar:calendar:read calendar:calendar.event:read calendar:calendar.event:create calendar:calendar.event:update calendar:calendar.event:reply calendar:calendar.free_busy:read task:task:read task:task:write task:tasklist:read task:tasklist:write im:message:readonly im:message.group_msg:get_as_user im:chat:read im:chat.members:read contact:user.base:readonly drive:drive.metadata:readonly"
```

执行后：
1. 读取输出中的 `auth_url` 和 `state`
2. 让用户在浏览器中打开 `auth_url`
3. 用户授权后，把浏览器地址栏中的完整回调 URL 发回来

### 第二步：用回调 URL 换取 Token

```bash
feishu-cli auth callback "<用户提供的回调URL>" --state "<第一步输出的state>"
```

成功后 token 会被 feishu-cli 保存到本地认证目录中。

## 常见错误排查

### 99991679 / Unauthorized
通常表示 **scope 不足**，不是 token 一定失效。

处理顺序：
1. 先 `auth status -o json`
2. 检查 scope 是否包含目标能力
3. 缺 scope 再引导用户重新授权

### 99991672 / Access denied
通常表示：
- 应用后台没开对应权限
- 当前身份没有访问目标资源的权限

先区分是：
- token 问题
- scope 问题
- 飞书应用后台权限问题
- 文档/群/资源本身没授权给当前身份

### code expired / state mismatch
属于 OAuth 回调阶段问题：
- `code expired`：用户完成授权太慢，重新生成链接
- `state mismatch`：回调 URL 与当前这次登录流程不匹配，重新开始一次完整流程

## 高影响操作

下面这些操作不要默认执行，必须先得到用户明确确认：
- `feishu-cli config create-app`
- `feishu-cli config add-scopes`
- 改写本地认证配置文件
- 清空或覆盖现有 token

## 何时把用户引导到别的技能

- 用户要“搜索飞书文档/消息/应用” → `feishu-cli-search`
- 用户要“看聊天记录/群里最近说了什么/管理群成员” → `feishu-cli-chat`
- 用户要“发飞书消息” → `feishu-cli-msg`

## 最小工作流

### 场景：用户说“飞书搜索没权限”
1. 运行 `feishu-cli auth status -o json`
2. 判断 token 是否有效
3. 判断缺少哪个 scope
4. 向用户解释原因
5. 如用户同意，再走两步式重新授权

### 场景：用户说“帮我登录飞书”
1. 生成授权链接
2. 提示用户打开链接并完成授权
3. 接收回调 URL
4. 换取 token
5. 再次检查 `auth status -o json`
