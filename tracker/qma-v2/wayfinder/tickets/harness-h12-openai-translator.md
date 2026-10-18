---
title: Harness H12: OpenAI chat-completions translator lane
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

A translator lane for `KeyProvider` rows flagged `wire: openai_chat`, reusing `qma/gpt/translate.py`, so OpenCode rows join the pool (ruling 63). Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant: ruling 63 says the pool must take OpenCode; reuses existing code.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H12; ruling 24 (harness untouched), ruling 39 (pool exception).

## Resolution (2026-10-18 evening, re-centralize)

Designed in the rerun: HARNESS-REQUESTS HG4 H12, the in-house chat lane (pool exception; no opencodex, ruling 99), with the mapping specified (41 M9). Built in the ROUTER packet, checked by probe P3.
