---
title: Build prerequisites: rebuild/base merge, D1-D4, B1
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. HP merge, D1-D4 and B1 are still real prerequisites; drop the wave 1 framing (ruling 33)."
---

## Rewrite (2026-10-16, map rewrite)

Still real; the wave framing is dropped (ruling 33). The HP stack #81-#90 awaits his merge; D1-D4 have not run; the B1 SQLite one-writer fix is not in (33 section 5). `ENGINE-PLAN.md` stacks on `qma/hp17` meanwhile. HITL: the merge click is his.

The text below is the earlier charting; where it disagrees with this section or with `26`, they win.

## Question

Record when the three prerequisites outside this map are done: the HP stack (#81-#90) merged into `rebuild/base`, the deletion program D1-D4 run, and BACKLOG B1 fixed (one writer per SQLite file). No harness source edits may happen before this (`DELETION-PLAN.md:43`).

## What the session does

HITL placeholder: he merges and signs off; the orchestrator session runs D1-D4 and B1; this ticket closes with the commit ids.

## Unblocks

Harness extensions, the thin engine, wave 0 UI wiring.

## Sources

`20-review-b` findings 1 and 10; `21` B1; `DELETION-PLAN.md`; memory `agent-system-map`.

## Update (2026-10-18 evening, re-centralize)

Current (replaces the 10-16 rewrite above): the engine stack is merged into `engine/base` (`132169c7`, ruling 103). `rebuild/base` (`4345eafa`) holds HP2 and two test fixes that `engine/base` lacks. **His click:** merge `engine/base` into `rebuild/base` before any harness packet (CAP-H, HG3, ROUTER). D1-D4 have not run, and `DELETION-PLAN.md` must be rewritten first (stale premises; banner at its top). The B1 SQLite one-writer fix is not in. The red `just ci` line is P0 hygiene.
