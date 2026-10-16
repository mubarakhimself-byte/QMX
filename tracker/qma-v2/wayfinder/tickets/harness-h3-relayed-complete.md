---
title: Harness H3: a relayed single request without a CLI
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

`Harness.complete(profile, account, messages, schema)` served by the relay for key and GPT profiles only. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant later: the fallback (one-turn tool-less Background chat) works; grant when RAM on Contabo bites (ruling 76).

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H3; ruling 24 (harness untouched), ruling 39 (pool exception).
