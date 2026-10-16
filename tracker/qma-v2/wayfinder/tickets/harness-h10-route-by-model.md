---
title: Harness H10: relay routing by model id
type: grilling
mode: HITL
status: open
blocked_by: [probe-e24-mixed-providers]
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

`resolve_model` grows into a model-to-provider table; one chat may hold several provider grants; usage teed per provider (engine AD-29, ruling 62). Part of the load-balancer exception (ruling 39). Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant under ruling 39 once probe E24 shows the CLI forwards a full non-Claude model id; else the engine fan-out fallback.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H10; ruling 24 (harness untouched), ruling 39 (pool exception).
