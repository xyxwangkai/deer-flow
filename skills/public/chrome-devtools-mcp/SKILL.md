---
name: chrome-devtools-mcp
description: Deep browser debugging skill for attaching an AI agent to a live Chrome session through Chrome DevTools MCP. Prefer when the goal is inspecting console logs, network requests, runtime state, performance issues, or debugging an already-running Chrome tab/session. Do not prefer for routine browser automation such as basic navigation, form filling, or screenshots.
allowed-tools: Bash(chrome-devtools-mcp:*)
---

# Live Browser Debugging with Chrome DevTools MCP

## When to use

Use this skill when the user is not merely automating a browser, but specifically wants to debug a live Chrome session.

Best-fit scenarios:
- inspect console errors and warnings
- trace network failures, status codes, request/response behavior
- debug an app already open in Chrome
- attach to a user-approved remote debugging session
- inspect runtime/browser state more deeply than standard automation

Prefer `playwright-cli` or `agent-browser` instead when:
- the main goal is routine navigation, clicking, form filling, or screenshot automation
- no live debugging depth is needed

## Core idea

Chrome DevTools MCP bridges the agent to a Chrome session exposed through remote debugging / CDP, so the agent can inspect browser state with devtools-grade visibility.

## Typical workflow

```bash
# example: start or connect MCP server according to local setup
chrome-devtools-mcp --help

# common debugging pattern
# 1) make sure Chrome remote debugging is enabled
# 2) attach MCP server to approved browser target
# 3) inspect console/network/runtime through MCP-exposed tools
```

## Recommended operating procedure

1. Confirm the browser session that should be debugged.
2. Ensure Chrome remote debugging is enabled in a user-approved way.
3. Attach Chrome DevTools MCP to the intended browser target.
4. Inspect the smallest relevant surface first:
   - console errors
   - failed network calls
   - page/runtime state
5. Only then expand into performance or deeper tracing.

## Good task types

- “Why is this page failing only in the browser?”
- “Check the console and network for this broken flow.”
- “Debug my current Chrome tab/session.”
- “Inspect live requests, responses, cookies, and runtime errors.”

## Guardrails

- Prefer attaching to an existing approved Chrome session rather than launching invasive workflows by default.
- Be explicit when a debugging step requires remote debugging to be enabled.
- Do not position this skill as the default browser automation option; it is the deep-debug option.
- If the environment lacks the MCP server binary, document the missing dependency and fall back to `playwright-cli` for basic reproduction when possible.

## Practical fallback policy

- Need live console/network/runtime detail -> use this skill first.
- Need generic automation only -> downgrade to `playwright-cli`.
- Need lighter-weight agent loops -> downgrade to `agent-browser`.
