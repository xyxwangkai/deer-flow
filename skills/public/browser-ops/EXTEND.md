# browser-ops 扩展说明

本文件用于补充 `browser-ops` 的路由边界、冲突判定、降级策略和维护建议。`SKILL.md` 负责主入口触发与核心规则，`EXTEND.md` 负责更细的解释层。

## 一、设计目标

`browser-ops` 不是另一个具体浏览器执行器，而是一个统一入口路由器。

它的目标是：
- 避免同一个浏览器任务被多个技能同时抢占
- 在不牺牲稳定性的前提下，优先把任务送到最合适的工具
- 当环境或依赖受限时，能有可解释的降级路径
- 让 Agent 在“自动化 / 调试 / 远程连接 / 低 token 控制”之间做出稳定选择

## 二、总路由原则

统一遵循以下判断顺序：

1. **先看用户意图**：自动化、调试、远程连接、低 token agent loop
2. **再看环境形态**：本地 GUI、已打开 Chrome、远程/沙盒、CDP 可用性
3. **再看用户显式偏好**：是否明确点名 Browser Use / DevTools / Playwright / agent-browser
4. **最后才看默认优先级**：P0/P1/P2/P3 只在同类意图里生效

也就是说，`P0 = playwright-cli` 不代表所有情况都先走 Playwright。

## 三、技能定位边界

### 1. playwright-cli

定位：
- 默认通用浏览器自动化技能
- 最适合 open/click/fill/submit/screenshot/scrape/test 这类稳定流程

应优先触发的场景：
- 没有明显调试诉求
- 没有明显 remote/sandbox 约束
- 没有明显 token-sensitive agent loop 诉求
- 用户只想“把网页操作做完”

不应优先触发的场景：
- 用户真正想看 console/network/runtime/perf
- 用户明确要求 Browser Use
- 用户明确强调低 token snapshot/ref 驱动

### 2. agent-browser

定位：
- 面向 AI agent 的轻量浏览器控制
- 核心优势是 snapshot + refs + 低上下文成本

应优先触发的场景：
- 多轮 verify/fix/reload
- 需要反复 snapshot 后再操作
- 用户提到低 token、紧凑控制、AI-friendly browser loop
- 任务偏 agentic，但并不需要深度 DevTools 调试

不应优先触发的场景：
- 明确是调试现有 Chrome 页签
- 用户只是标准网页自动化，没有 token 成本诉求
- 需要完整 DevTools 级别的网络/性能检查

### 3. chrome-devtools-mcp

定位：
- 深度调试技能，不是默认自动化技能
- 核心是 attach 到 live Chrome session 做 console/network/runtime/perf 诊断

应优先触发的场景：
- 用户说“当前 Chrome 页签”“console error”“抓请求”“网络失败”“performance 问题”
- 故障只在真实浏览器里复现
- 任务目标是诊断原因，而不是完成表单操作

不应优先触发的场景：
- 普通导航/点击/填表单/截图
- 用户并没有现成的 live Chrome session
- 只是想快速复现网页路径

### 4. browser-use-cli

定位：
- 偏 remote/sandbox/hosted/agent runtime 的浏览器控制
- 适合 Browser Use 指定流程与连接型工作流

应优先触发的场景：
- 用户明确说 Browser Use
- 环境中本地 GUI 不稳定或不存在
- 任务更像“在沙盒/远程 agent 环境里连上浏览器并操作”
- 依赖 connect / remote / hosted browser 语义

不应优先触发的场景：
- 本地环境标准自动化完全可以直接走 Playwright
- 用户真正要的是 live debugging，而不是 remote control
- 用户更在意低 token snapshot/ref，而不是 Browser Use runtime

## 四、常见冲突案例

### 案例 A：用户说“打开页面并检查报错”

拆解：
- “打开页面”像 Playwright
- “检查报错”像 DevTools

推荐策略：
- 若重点是**复现流程**，先 `playwright-cli`
- 若重点是**看 console/network 具体错误**，先 `chrome-devtools-mcp`

不要只因为句子里有“打开页面”就固定走 Playwright。

### 案例 B：用户说“帮我持续检查页面，每次改完代码都验证一下”

推荐：
- 首选 `agent-browser`

原因：
- 这是典型 agent loop
- 需要低成本重复 snapshot / verify
- 不应默认走更重的 Playwright 或 DevTools

### 案例 C：用户说“在当前 Chrome 标签页看网络请求为什么 500”

推荐：
- 首选 `chrome-devtools-mcp`

原因：
- 已明确是 live tab + network diagnosis
- 这不是普通自动化任务

### 案例 D：用户说“在沙盒里帮我连一个浏览器完成登录流程”

推荐：
- 首选 `browser-use-cli`

原因：
- 已明确 sandbox + connect 语义
- 优先 remote/browser-connect 路线

### 案例 E：用户说“打开网页截图给我”

推荐：
- 首选 `playwright-cli`

原因：
- 典型稳定自动化任务
- 无需引入更特殊的浏览器栈

## 五、降级策略细化

### 1. 同意图内降级

优先做同意图内替代，而不是跨意图乱跳。

例如：
- 一般自动化：`playwright-cli -> agent-browser -> browser-use-cli`
- 低 token loop：`agent-browser -> playwright-cli -> browser-use-cli`
- live debugging：`chrome-devtools-mcp -> playwright-cli(用于复现) -> agent-browser`
- remote/sandbox：`browser-use-cli -> playwright-cli -> agent-browser`

### 2. 为什么不建议直接多工具并用

除非第一条执行路径失败，否则不要一上来同时混用多个浏览器工具。原因包括：
- 容易重复打开页面和重复消耗上下文
- 会让状态来源混乱
- 容易出现“在 A 工具里点了，在 B 工具里查不到”的 session 偏差
- 会降低路由规则的可预测性

### 3. 何时允许工具切换

允许切换的情况：
- 当前工具不存在或无法启动
- 当前工具能做，但明显不适合当前目标
- 用户目标从“自动化”切换成“深度调试”
- 需要先自动化复现，再进入 live debugging

不建议切换的情况：
- 只是因为另一个工具“也许也能做”
- 当前工具已能稳定完成任务
- 没有新证据表明需要更深能力

## 六、显式用户偏好处理

如果用户明确指定某工具：
- 优先尊重用户偏好
- 但若该工具与任务目标明显冲突，应提示“可执行，但不是最佳路径”
- 如果工具不可用，再回退到同意图最优替代

### 示例

用户说：
- “用 Browser Use 打开这个站点” -> 优先 `browser-use-cli`
- “用 Playwright 帮我填表” -> 优先 `playwright-cli`
- “用 DevTools 看当前页 console” -> 优先 `chrome-devtools-mcp`

## 七、触发词优化建议

### 更适合 `browser-ops` 统一入口触发的表达

- 操作浏览器
- 帮我测试网页
- 浏览器自动化
- 检查这个页面
- 调试浏览器问题
- 自动选择合适的浏览器工具
- 用浏览器完成这个任务

### 不应让 `browser-ops` 抢得过重的情况

如果用户已经非常明确地说：
- “用 Browser Use”
- “用 DevTools MCP”
- “用 Playwright”
- “用 agent-browser”

则对应的具体技能应优先被命中，`browser-ops` 更像兜底统一入口，而不是覆盖所有明确指令。

## 八、维护建议

后续如果继续新增浏览器相关技能，建议仍然遵守以下方式：

1. 先定义技能的**主意图**，而不是只写工具名
2. 明确“应该优先触发”和“不应优先触发”的边界
3. 补充 3~5 个与其它浏览器技能容易冲突的例子
4. 在 `browser-ops` 中增加意图车道和 fallback 说明

## 九、推荐心智模型

把这四个技能理解成四条车道：

- `playwright-cli`：默认稳定自动化车道
- `agent-browser`：低 token agent loop 车道
- `chrome-devtools-mcp`：live debugging 车道
- `browser-use-cli`：remote/sandbox/browser-connect 车道

`browser-ops` 的职责不是亲自开车，而是把任务送上正确车道。
