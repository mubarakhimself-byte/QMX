---
title: Harness H6: usage readings per account
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
owner: harness owner
---

## Question

`Harness.usage()` returns readings per account once the pool exists. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H6; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution

Resolved. Lands with the account pool, the one sanctioned harness extension (ruling 39, engine AD-12); no separate answer needed. (Map rewrite 2026-10-16.)
