---
title: Harness H14: per-chat model_scope enforced by the relay
type: grilling
mode: HITL
status: open
blocked_by: [harness-h10-route-by-model]
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

`NewChat.model_scope` lists the providers a Background chat may address; the relay enforces it. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant with H10; without it the relay only logs.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H14; ruling 24 (harness untouched), ruling 39 (pool exception).
