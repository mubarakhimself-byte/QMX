---
title: Harness H8: per-chat sandbox tool server and disallowed tools
type: grilling
mode: HITL
status: open
blocked_by: [probe-e23-runner-outside]
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

A per-chat extra MCP server (the engine's sandbox tool server) plus per-chat `disallowed_tools` for `Bash`, `Write`, `Edit`, `NotebookEdit`. The central request of AD-25 (`runner_outside`). Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant if probe E23 shows the sandbox tools hold task quality; else `cli_inside` stays the fallback.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H8; ruling 24 (harness untouched), ruling 39 (pool exception).
