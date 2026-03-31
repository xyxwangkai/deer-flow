# browser-ops / Usage

## 作用

`browser-ops` 是统一入口，不直接强调某一个具体工具，而是先判断任务意图，再路由到最适合的浏览器技能。

管理的目标技能：
- `playwright-cli`
- `agent-browser`
- `chrome-devtools-mcp`
- `browser-use-cli`

## 默认路由原则

### 1. 普通自动化

例如：
- 打开网页
- 点击按钮
- 填写表单
- 截图
- 抓取页面信息

默认路由：`playwright-cli`

### 2. AI agent 低 token 循环交互

例如：
- 连续验证 UI
- 反复 snapshot -> click -> re-snapshot
- 希望减少上下文消耗

默认路由：`agent-browser`

### 3. 深度调试

例如：
- 看 console
- 查 network 请求
- 看 runtime/performance
- 调试已经打开的 Chrome

默认路由：`chrome-devtools-mcp`

### 4. 远程 / 沙盒 / Browser Use 指定路径

例如：
- 用 Browser Use
- 在 sandbox 环境操作浏览器
- 通过 connect/CDP 接已有浏览器

默认路由：`browser-use-cli`

## 快速示例

- “打开这个页面并截图” -> `playwright-cli`
- “低 token 成本反复检查按钮状态” -> `agent-browser`
- “看一下我当前 Chrome 页签为什么报错” -> `chrome-devtools-mcp`
- “在远程沙盒里帮我操作浏览器” -> `browser-use-cli`

## 失败降级原则

### 一般自动化失败

`playwright-cli` -> `agent-browser` -> `browser-use-cli`

### AI 轻量交互失败

`agent-browser` -> `playwright-cli` -> `browser-use-cli`

### Live debugging 失败

`chrome-devtools-mcp` -> `playwright-cli` 复现 -> `agent-browser`

### Remote/sandbox 路径失败

`browser-use-cli` -> `playwright-cli` -> `agent-browser`

## 使用建议

如果用户没有明确指定工具，先判断以下 5 个问题：
1. 是自动化还是调试？
2. 是否存在已经打开的 Chrome 会话？
3. 是否强调 token 成本或 AI-friendly loop？
4. 是否是远程/沙盒环境？
5. 是否点名某一工具？

根据答案选一个工具，不要一上来就混用多个浏览器技能。
