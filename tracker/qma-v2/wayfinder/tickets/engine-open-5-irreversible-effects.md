---
title: Engine OPEN-5: what counts as an irreversible external effect
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
---

## Question

The only steps that may wait for the inbox (engine AD-8, AD-22, ruling 57). Which effects count?

## Recommended answer

Messages, posts, webhooks, outbound calls to non-QMX systems, desktop actions that submit or send, and app operations an app marks so. Model spend, Library writes and file changes never count.

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 5; engine AD-8, AD-22; engine DOC-CHANGES row 14.

## Resolution (2026-10-18 evening, re-centralize)

Closed by the rerun (engine OPEN-DECISIONS "Closed by the rerun", old 4): the recommended list stands. Messages, posts, webhooks, outbound calls to non-QMX systems, desktop actions that submit or send, and app operations an app marks so count; model spend, Library writes and file changes never count.
