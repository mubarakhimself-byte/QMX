---
title: Engine amendment: chunked fan-out, compaction, caching, hooks
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
---

## Question

Ruling 78 (after the engine architecture): fan-out is per chunk of items, not one agent per item; 1M-context models take large chunks; compaction near 40%; context compaction, caching, tool calls and hooks are critical in the engine. Amend engine AD-4/AD-5 and SOLUTION-DESIGN (a `chunk` setting on `broadcast` edges, compaction and cache policy per agent node), or confirm `ENGINE-PLAN.md` already carries it.

## Sources

Ruling 78; engine AD-4, AD-5; `ENGINE-PLAN.md`.

## Resolution

Resolved. Engine AD-34 (chunked fan-out by a share of the model's window, compaction at 0.40, cache-stable prompt order with per-node lease affinity, per-chat hooks, one span per tool call), harness requests H15/H16 with fallbacks, live checks E29-E31 (27c fix 1).
