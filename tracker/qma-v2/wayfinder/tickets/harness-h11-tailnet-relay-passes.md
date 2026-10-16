---
title: Harness H11: relay on the tailnet with run-pass bearers
type: grilling
mode: HITL
status: open
blocked_by: [central-relay-ruling-75]
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

The relay listens on the tailnet as well as loopback and accepts a signed run pass as bearer for non-chat callers (engine AD-28). Replaces H9. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant under ruling 39, shaped by the central-relay decision (one relay machine, or one per host).

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H11; ruling 24 (harness untouched), ruling 39 (pool exception).
