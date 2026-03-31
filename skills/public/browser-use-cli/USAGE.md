# browser-use-cli / Usage

## 适用场景

当浏览器控制发生在远程、沙盒、托管或 agent-native 环境中时，优先考虑 `browser-use-cli`。

典型场景：
- 没有稳定本地 GUI 假设
- 需要连接已有浏览器
- Browser Use 本身就是目标技术栈的一部分
- 更偏向 agentic browser control，而不是传统测试脚本

## 推荐调用思路

1. 判断环境是不是远程/沙盒
2. 判断是不是明确要求 Browser Use
3. 优先走 connect/open 模式
4. 以短回路执行操作
5. 必要时输出截图或结果摘要

## 示例

### 查看 CLI 能力

```bash
browser-use --help
```

### 连接/启动思路

```bash
browser-use --connect open
```

## 什么时候优先用它

- 用户直接说用 Browser Use
- 需要 remote browser control
- 需要在 sandbox 环境里做浏览器操作
- 需要 browser-connect / CDP 风格接入

## 什么时候不要优先用

以下情况更适合其他技能：
- 普通本地自动化：`playwright-cli`
- 低 token 快照式 agent 操作：`agent-browser`
- 对真实 Chrome 做深度调试：`chrome-devtools-mcp`

## 常见失败处理

### CLI 不存在

```bash
browser-use --help
```

如果命令不存在，说明环境未安装或没有暴露到 PATH。

### connect 失败

检查：
- 目标浏览器是否存在
- CDP/连接参数是否正确
- 当前环境网络与权限是否允许

### 只是普通网页自动化

若不需要 Browser Use 特性，应主动降级到：
- `playwright-cli`
- 或 `agent-browser`

## 输出建议

优先返回：
- 当前连接方式
- 是否成功接入目标浏览器
- 关键动作执行结果
- 如失败，给出缺失依赖或连接阻塞点
