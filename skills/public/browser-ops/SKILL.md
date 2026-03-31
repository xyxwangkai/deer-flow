---
name: browser-ops
description: Unified browser operations entry skill that routes tasks across Playwright CLI, Agent Browser, Chrome DevTools MCP, and Browser Use using intent-first routing, environment awareness, and fallback rules. Prefer when the user broadly asks to operate, test, inspect, debug, or automate a browser without naming a specific tool, and the agent should choose the best browser skill automatically.
---

# Unified Browser Operations Router

This skill is the single entry point for browser work. It does not replace specialized skills; it chooses among them.

## Managed skills

- `playwright-cli` — P0 default for stable, broad browser automation
- `agent-browser` — P1 for token-efficient AI-agent browser control
- `chrome-devtools-mcp` — P2 for deep live debugging of Chrome sessions
- `browser-use-cli` — P3 for sandboxed/remote/Browser Use specific flows

## Core routing principle

Always choose by **task intent first**, then refine by **environment constraints**, then apply **priority and fallback**.

In short:
1. Identify whether the task is automation, lightweight agent control, deep debugging, or remote/sandbox browser operation.
2. Honor explicit user tool preference if it is viable.
3. Avoid mixing multiple browser tools in the same path unless the first route is blocked or clearly insufficient.

## Intent routing

### Route to `chrome-devtools-mcp` first when

- the user says debug, debugging, console, network, request, response, runtime, performance, memory, or devtools
- the task is about an already-running Chrome session or a live browser tab
- the user explicitly mentions DevTools MCP, Chrome DevTools, or remote debugging
- the main value is diagnosis, not navigation

### Route to `browser-use-cli` first when

- the user explicitly asks for Browser Use
- the environment is sandboxed, remote, hosted, or agent-runtime centric
- the task depends on browser-connect / CDP-style connection workflows
- local GUI assumptions are weak or unavailable

### Route to `agent-browser` first when

- the task is repetitive browser interaction in an AI loop
- token efficiency matters
- compact page snapshots and ref-based actions are better than selector-heavy control
- the user wants a lightweight agent-friendly path instead of full automation machinery

### Route to `playwright-cli` first when

- the user asks for normal browser automation with no stronger signal
- the task is open / click / fill / submit / scrape / screenshot / basic E2E flow
- a stable and broad default is preferred

## Trigger phrase hints

These are hints, not hard rules.

### Likely `playwright-cli`
- 打开网页
- 点击按钮
- 填表单
- 截图
- 跑一个自动化流程
- scrape / crawl page content
- test a web flow

### Likely `agent-browser`
- 低 token
- AI agent friendly
- snapshot / refs / @e1
- 连续检查页面状态
- verify after each change
- compact browser control

### Likely `chrome-devtools-mcp`
- console error
- network request
- runtime state
- performance issue
- 当前 Chrome 页签
- devtools
- remote debugging
- why page is broken only in browser

### Likely `browser-use-cli`
- Browser Use
- sandbox browser
- remote browser
- hosted browser
- connect to browser
- CDP connect in agent environment

## Environment-aware adjustments

### If the user already has a live Chrome session
Prefer `chrome-devtools-mcp` for debugging tasks.
If the task is only to reproduce a simple action, `playwright-cli` may still be sufficient.

### If the environment is remote or sandboxed
Prefer `browser-use-cli` unless the task is clearly standard automation and Playwright is already known to work in that environment.

### If command availability is uncertain
Prefer the best-intent route first, but fail fast and downgrade cleanly instead of forcing a broken tool.

## Priority model

This skill uses a priority model, but only **inside the correct intent lane**.

- P0: `playwright-cli` for general/stable automation
- P1: `agent-browser` for AI-agent optimized interaction
- P2: `chrome-devtools-mcp` for deep debugging
- P3: `browser-use-cli` for remote/sandbox-specific workflows

Do **not** interpret P0 as “always use Playwright first”. Intent overrides global priority.

## Fallback matrix

| Task type | First choice | Second choice | Third choice | Notes |
|---|---|---|---|---|
| General automation | `playwright-cli` | `agent-browser` | `browser-use-cli` | Prefer broad and stable automation first |
| Lightweight AI loop | `agent-browser` | `playwright-cli` | `browser-use-cli` | Use snapshot/ref flow before heavier tooling |
| Live debugging | `chrome-devtools-mcp` | `playwright-cli` | `agent-browser` | Reproduce with Playwright if devtools path unavailable |
| Remote/sandbox browser control | `browser-use-cli` | `playwright-cli` | `agent-browser` | Browser Use is favored in remote agent environments |
| Explicit user preference | named tool | best intent fallback | next best fallback | Respect user preference unless blocked |

## Failure handling rules

### Tool missing from environment
- report the missing binary or unavailable runtime clearly
- switch to the next tool in the same intent lane
- keep the user’s goal unchanged while changing only the execution path

### Tool works but is a poor fit
Example: using Playwright when the actual need is live network debugging.
- stop escalating with the wrong tool
- reroute to the correct specialized skill

### Partial success only
Example: automation works, but debugging detail is still missing.
- complete the reproducible automation step first
- then hand off to `chrome-devtools-mcp` if deep diagnostics are still required

## Decision checklist

Before acting, classify the request using these questions:

1. Is the main task automation or debugging?
2. Is there an existing browser session to inspect?
3. Does the user care about token efficiency or repeated AI-agent loops?
4. Is the environment remote, sandboxed, or connection-oriented?
5. Did the user explicitly name a browser tool?
6. Is the current tool actually available in this environment?

Then choose the routed skill and proceed.

## Example mappings

- “Open this page and fill the signup form.” -> `playwright-cli`
- “Continuously verify my UI after each code change with low context cost.” -> `agent-browser`
- “Check console and network errors in my current Chrome tab.” -> `chrome-devtools-mcp`
- “Use a remote/sandbox browser to test this app.” -> `browser-use-cli`
- “Use Browser Use to connect to the running browser.” -> `browser-use-cli`
- “This only fails in Chrome, inspect the live tab.” -> `chrome-devtools-mcp`

## Design principle

Prefer one tool per task path. Do not stack multiple browser tools unless the first-choice tool is missing, blocked, or clearly weaker for the user’s actual goal.
