---
title: Harness H2: output_format, tools and max_turns per chat
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

`NewChat` gains optional `output_format`, `tools` (allow-list) and `max_turns` for Background and Child chats. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant: pass-through to SDK options the harness already builds; `llm` and `agent` nodes need it.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H2; ruling 24 (harness untouched), ruling 39 (pool exception).
