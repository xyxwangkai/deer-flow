# chrome-devtools-mcp / Usage

## 适用场景

当目标不是普通浏览器自动化，而是调试一个真实 Chrome 会话时，优先使用本技能。

典型任务：
- 看 console 报错
- 看 network 失败请求
- 看 runtime 状态
- 对已打开页面做 live debugging
- 排查“浏览器里才会出现的问题”

## 推荐调用思路

1. 确认目标是“调试”不是“自动化”
2. 确认已有 Chrome 会话或允许启用 remote debugging
3. 连接 DevTools MCP
4. 先查最小闭环：console -> network -> runtime
5. 必要时再扩展到 performance

## 典型任务表达

下面这些表达通常应该路由到这里：
- "帮我看看当前 Chrome 页签的 console error"
- "这个请求为什么 500/403/超时"
- "排查页面白屏"
- "检查 network waterfall 和 runtime 错误"
- "调试已经打开的浏览器页面"

## 使用建议

### Step 1: 检查环境

```bash
chrome-devtools-mcp --help
```

### Step 2: 确认 Chrome 可调试

需要用户批准的 remote debugging 会话，或环境中已有可附着目标。

### Step 3: 先看最关键的三类信息

优先顺序：
1. console
2. network
3. runtime state

## 什么时候不要优先用

以下情况更适合别的技能：
- 普通点点点、填表单、截图：`playwright-cli`
- 想降低 token 开销做反复交互：`agent-browser`
- 远程/沙盒 browser-connect 更关键：`browser-use-cli`

## 常见失败处理

### 无法连接 Chrome

先确认：
- Chrome 是否开启 remote debugging
- MCP server 是否安装
- 目标页签/target 是否存在

### 只有自动化需求，没有深度调试需求

不要硬上 DevTools MCP，直接降级到：
- `playwright-cli`
- 或 `agent-browser`

## 输出建议

优先输出结构化结论：
- 发现的 console 错误
- 失败请求列表
- 可复现步骤
- 最可能根因
- 建议修复方向
