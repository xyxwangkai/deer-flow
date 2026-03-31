# agent-browser / Usage

## 适用场景

当任务需要浏览器自动化，但又希望：
- token 开销更低
- 用快照元素引用而不是脆弱的 selector
- 适合 AI agent 连续操作与反复验证

优先考虑 `agent-browser`。

## 推荐调用方式

典型流程：

1. 打开页面
2. 获取快照
3. 使用 `@e1`、`@e2` 这类引用执行交互
4. 页面变化后重新 snapshot
5. 按需保存截图或 PDF

## 示例

### 打开页面并检查可交互元素

```bash
agent-browser open https://example.com
agent-browser snapshot
```

### 点击和输入

```bash
agent-browser click @e2
agent-browser fill @e3 "hello@example.com"
agent-browser press Enter
```

### 页面变化后重新获取引用

```bash
agent-browser snapshot
```

### 保存产物

```bash
agent-browser screenshot /mnt/user-data/outputs/agent-browser-page.png
agent-browser pdf /mnt/user-data/outputs/agent-browser-page.pdf
```

## 什么时候不要优先用

以下场景优先切换：
- 要做最稳妥、最通用的自动化：`playwright-cli`
- 要看 console/network/runtime 深度调试：`chrome-devtools-mcp`
- 远程/沙盒/browser-connect 流程更重要：`browser-use-cli`

## 常见失败处理

### 元素引用失效

现象：页面刷新、跳转、局部 rerender 后，`@e2` 无法继续使用。

处理：

```bash
agent-browser snapshot
```

重新获取引用后再操作。

### 命令不存在

先检查：

```bash
agent-browser --help
```

如果环境没有全局安装，尝试项目内 wrapper、`npx` 或由宿主环境提供的别名。

## 输出建议

如果用户没有明确要求，不必默认生成截图；优先返回：
- 当前页面状态
- 关键交互是否成功
- 下一步建议
