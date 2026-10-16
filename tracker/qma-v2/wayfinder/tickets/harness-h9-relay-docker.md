---
title: Harness H9: relay reachable from the Docker network
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

The relay reachable from the Docker network with a per-attempt grant for non-chat callers. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H9; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution

Superseded. Replaced by H11 (relay on the tailnet with run passes), per HARNESS-REQUESTS. (Map rewrite 2026-10-16.)
