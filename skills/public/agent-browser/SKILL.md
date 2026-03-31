---
name: agent-browser
description: Token-efficient browser automation skill optimized for AI agents using lightweight accessibility snapshots and element refs. Prefer when the user wants low-context browser control, stable ref-based interaction, repeated verification loops, or an AI-friendly alternative to heavier browser automation. Do not prefer for deep live debugging of Chrome sessions.
allowed-tools: Bash(agent-browser:*)
---

# Browser Automation with agent-browser

## When to use

Use this skill when the task is browser automation, but you want lower token overhead and more AI-friendly interaction than DOM-heavy approaches.

Best-fit scenarios:
- fast verify/fix/reload loops on web apps
- repeated UI checks where snapshot refs are stable enough
- low-context browser control for coding agents
- quick screenshots, PDF export, and accessibility-tree inspection
- connecting to an existing browser over CDP when needed

Prefer `playwright-cli` instead when:
- you need broader, more established command coverage
- you need richer storage/network/devtools helpers already documented
- the environment already standardizes on Playwright workflows

Prefer `chrome-devtools-mcp` instead when:
- the main goal is live debugging of an existing Chrome session
- you need console/network/runtime inspection depth over generic automation

## Core workflow

```bash
# open or navigate
agent-browser open https://example.com
# inspect page in AI-friendly form
agent-browser snapshot
# click/fill using refs like @e2
agent-browser click @e2
agent-browser fill @e3 "hello"
agent-browser press Enter
# capture artifacts
agent-browser screenshot
# close
agent-browser close
```

## Common commands

### Navigation and sessions

```bash
agent-browser open https://example.com
agent-browser goto https://example.com
agent-browser back
agent-browser forward
agent-browser reload
agent-browser close
agent-browser close --all
```

### Snapshot-driven interaction

```bash
agent-browser snapshot
agent-browser click @e2
agent-browser click @e2 --new-tab
agent-browser dblclick @e4
agent-browser focus @e3
agent-browser type @e3 "hello@example.com"
agent-browser fill @e3 "hello@example.com"
agent-browser clear @e3
agent-browser press Enter
agent-browser key Tab
agent-browser hover @e5
agent-browser select @e6 "value"
agent-browser check @e7
agent-browser uncheck @e7
agent-browser drag @e8 @e9
agent-browser scroll down
agent-browser scroll up
agent-browser scroll --selector @e10 down
agent-browser scrollinto @e10
agent-browser upload @e11 /absolute/path/file.pdf
```

### Evaluation and artifacts

```bash
agent-browser eval "document.title"
agent-browser screenshot
agent-browser screenshot /mnt/user-data/outputs/page.png
agent-browser annotate
agent-browser pdf
agent-browser pdf /mnt/user-data/outputs/page.pdf
```

### CDP and runtime streaming

```bash
agent-browser connect ws://127.0.0.1:9222/devtools/browser/...
agent-browser enable-stream
agent-browser stream-status
agent-browser disable-stream
```

## Working style

1. Open page.
2. Run `snapshot`.
3. Use returned refs such as `@e1`, `@e2` for actions.
4. Re-snapshot after major page changes.
5. Save screenshots only when the user explicitly needs visual artifacts.

## Notes

- This tool is designed around compact accessibility/snapshot output, which is usually more token-efficient for agents than full DOM-based workflows.
- If refs become stale after navigation or rerender, run `agent-browser snapshot` again.
- Use absolute paths for uploads and saved artifacts.
- If the binary is not globally installed, check whether the environment provides it through `npx`, project-local install, or wrapper scripts before giving up.
