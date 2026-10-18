---
title: Harness H13: per-machine plan homes and qmx node login
type: grilling
mode: HITL
status: closed
blocked_by: [engine-open-3-plan-logins]
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
owner: harness owner
---

## Question

A plan account row carries `machine`; the CLI's `/login` runs once on that machine; the pool refuses plan leases elsewhere. Part of the pool extension. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant under ruling 39 if Engine OPEN-3 is yes.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H13; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution (2026-10-18 evening, re-centralize)

Designed (engine AD-28) and part of the pool extension, so no separate grant; engine OPEN-3 closed yes. Built with the pool in the ROUTER packet.
