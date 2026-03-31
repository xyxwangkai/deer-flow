---
name: browser-use-cli
description: Browser Use based browser control skill for sandboxed, remote, or agent-runtime workflows, including browser-connect patterns via CDP. Prefer when the user explicitly wants Browser Use or needs AI-native browser control in hosted, remote, or sandbox environments. Do not prefer as the default path for ordinary local browser automation.
allowed-tools: Bash(browser-use:*)
---

# Browser Automation with Browser Use

## When to use

Use this skill when the user specifically wants Browser Use, or when the environment is more aligned with remote/sandboxed/browser-agent workflows than traditional local browser automation.

Best-fit scenarios:
- sandboxed agent environments with no direct GUI
- Browser Use specific workflows or CLI 2.0 usage
- connecting to a running Chrome/browser through CDP-style flows
- remote browser or hosted browser control
- AI-agent-driven navigation where Browser Use is already part of the stack

Prefer `playwright-cli` instead when:
- you need the safest default and most explicit general-purpose command set
- the task is straightforward browser automation in a normal local environment

Prefer `agent-browser` instead when:
- token efficiency and ref-based snapshot interaction are the main priority

Prefer `chrome-devtools-mcp` instead when:
- the goal is deep debugging of a live Chrome session rather than general web task execution

## Typical workflow

```bash
# inspect local CLI
browser-use --help

# common idea: open/connect, interact, inspect, capture artifacts
browser-use --connect open
```

## Recommended operating procedure

1. Detect whether the environment is local GUI, sandboxed, or remote.
2. If sandboxed/remote, prefer Browser Use connection-oriented flows.
3. Open or connect browser.
4. Perform task in short loops.
5. Save screenshots/artifacts only when needed.

## Best-fit task examples

- “In this sandbox, open the site and test the flow.”
- “Use Browser Use to connect to the running browser.”
- “I need remote browser control from an agent environment.”
- “Operate a browser where direct local GUI assumptions do not hold.”

## Notes

- Browser Use is often a better fit than raw CDP when the user wants an agent-friendly browser control layer, not protocol-level debugging.
- Browser Use may depend on its own runtime, browser setup, or hosted/cloud assumptions. If missing, report dependency gaps clearly.
- If direct CDP connection fails or is unstable, fall back to `playwright-cli` for reproduction or `chrome-devtools-mcp` for targeted live debugging, depending on user intent.
