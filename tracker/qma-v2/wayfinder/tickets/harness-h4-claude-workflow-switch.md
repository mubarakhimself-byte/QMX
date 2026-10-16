---
title: Harness H4: per-chat switch for the Claude Code Workflow tool
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

A per-chat switch for `CLAUDE_CODE_DISABLE_WORKFLOWS` on `NewChat` (plan profile only), default off. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Refuse for v1: the `claude_workflow` node kind is off in v1 and the engine's own fan-out covers it. Engine DOC-CHANGES row 9 then stays 'no change'.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H4; ruling 24 (harness untouched), ruling 39 (pool exception).
