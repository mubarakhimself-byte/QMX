---
title: Harness H3: a relayed single request without a CLI
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
owner: harness owner
---

## Question

`Harness.complete(profile, account, messages, schema)` served by the relay for key and GPT profiles only. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant later: the fallback (one-turn tool-less Background chat) works; grant when RAM on Contabo bites (ruling 76).

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H3; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution (2026-10-18 evening, re-centralize)

Moved into HARNESS-REQUESTS HG4 after review 41 M13 (`Harness.complete` on key and GPT lanes for mini-app `llm_complete` and native video). The grant is his call G: ticket "Decision G: grant the HG4 rows outside the pool exception".
