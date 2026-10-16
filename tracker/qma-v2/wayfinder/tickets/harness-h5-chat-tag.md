---
title: Harness H5: a chat tag carried into ChatRecord
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
owner: harness owner
---

## Question

`NewChat.tag` carried into `ChatRecord` and `GET /api/chats`, so a chat is found by `run:node:attempt`. Answered by the harness owner (grant or refuse); the engine has a fallback, so none blocks the first build.

## Recommended answer

Grant: small, and it removes a second lookup after a crash.

## Sources

`architecture/workflow-engine/HARNESS-REQUESTS.md` row H5; ruling 24 (harness untouched), ruling 39 (pool exception).
