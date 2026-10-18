---
title: Harness H14: per-chat model_scope enforced by the relay
type: grilling
mode: HITL
status: closed
blocked_by: [harness-h10-route-by-model]
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
owner: harness owner
---

## Question

`NewChat.model_scope` lists the providers a Background chat may address; the relay enforces it. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant with H10; without it the relay only logs.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H14; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution (2026-10-18 evening, re-centralize)

Designed and widened in the rerun: HARNESS-REQUESTS HG4 H14 (pool exception). Every grant and run pass carries `model_scope`, enforced by the router on every lane (engine AD-38, AD-28). Built in the ROUTER packet.
