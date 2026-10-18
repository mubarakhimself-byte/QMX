---
title: Harness H7: per-chat sub-agent definitions and caps
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

Per-chat `agents` (SDK `AgentDefinition`s), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` and `max_budget_usd` on `NewChat` for Background chats. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant the definitions and the concurrency cap; drop `max_budget_usd` (ruling 27: no spending caps).

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H7; ruling 24 (harness untouched), ruling 39 (pool exception).

## Update (27c/27d, 2026-10-16 night)

Recommendation applied (27c fix 11): the per-chat `max_budget_usd` is dropped from H7 (ruling 27). The grant itself is still his.

## Resolution (2026-10-18 evening, re-centralize)

The `agents` part is superseded by HARNESS-REQUESTS HG4 H38 (registry-generated sub-agent definitions on `NewChat.agents` for Interactive, Background and Child chats); sub-agent parallelism is a setting, not a cap (ruling 106). The grant is his call G.
