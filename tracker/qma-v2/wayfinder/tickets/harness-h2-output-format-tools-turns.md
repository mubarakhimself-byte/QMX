---
title: Harness H2: output_format, tools and max_turns per chat
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
owner: harness owner
---

## Question

`NewChat` gains optional `output_format`, `tools` (allow-list) and `max_turns` for Background and Child chats. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant: pass-through to SDK options the harness already builds; `llm` and `agent` nodes need it.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H2; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution (2026-10-18 evening, re-centralize)

Superseded by HARNESS-REQUESTS HG3 H2 (rewritten by 36 C1: the SDK `tools` list; no `output_format` and no `max_turns`, because ruling 106 removes every QMX turn cap). The grant is his call D: ticket "Decision D: grant the HG3 harness round, narrowed".
