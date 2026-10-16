---
title: Harness H1: export wait_turn for Background chats
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

Export `Harness.wait_turn(sid) -> TurnEnded` (or make `live()` yield a terminal item) so the engine knows when a Background turn ended. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant: it exposes an existing internal (`Chat.next_end()`); the fallback polling is slower and racy.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H1; ruling 24 (harness untouched), ruling 39 (pool exception).
