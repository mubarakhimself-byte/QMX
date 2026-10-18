---
title: Library build plan (qmx_library, Hub, migration)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Check whether `ENGINE-PLAN.md`'s data track carries the Library build (`qmx_library`, kind schemas, port, Hub, MIGRATION steps 0-n). If it does, close this with a link; if not, write the Library packet plan in the same QMA v2 style and link it from `ENGINE-PLAN.md`. Do not duplicate its PRs.

## Unblocks

Contabo setup (Hub, vault, qmx-node).

## Sources

`architecture/library-and-data/`MIGRATION.md, LLD.md; ruling 73 (coding can start), 81 (data first); `ENGINE-PLAN.md`.

## Update (2026-10-18 evening, re-centralize)

`ENGINE-PLAN.md` moved to `../../archive/2026-10-18-engine-program/`; its data track (DP1) was removed by ruling 91. The Library packet is LIB in `../../research/methodology/40-retriage.md` §3.1 row 17; the Hub design comes first. Write the Library packet plan as part of the next program.
