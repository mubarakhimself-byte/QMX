---
title: Engine OPEN-6: default self-improvement rule
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
---

## Question

What is the default `self_improve` setting per workflow (engine AD-26, ruling 79)?

## Recommended answer

`auto` for workflows he created or enabled, `propose_only` for templates he has not touched; challengers move `refs/champions/*`, never `main`.

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 6; engine AD-26; ruling 79; Library ENGINE-REQUESTS-ANSWERED mismatch 3.

## Resolution

Resolved by ruling 79 (ship a default): `self_improve: auto` for workflows he created or enabled, `propose_only` for untouched templates; engine OPEN-DECISIONS closed list (27c fix 15).
