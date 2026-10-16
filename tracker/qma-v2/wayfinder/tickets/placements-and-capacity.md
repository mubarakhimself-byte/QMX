---
title: Placements and capacity: PC and Contabo first
type: task
mode: AFK
status: open
blocked_by: [engine-open-4-server-check]
claimed_by: ""
created: 2026-10-16
---

## Question

Write the first placement-registry rows (PC, Contabo) and their concurrency defaults. Engine AD-25 sets a semaphore of 20 on the server; ruling 76 says 12 GB RAM holds about 4-6 Claude sessions. Derive `max_sessions` from measured RAM and fix the default.

## Unblocks

Contabo setup (sizing).

## Sources

Rulings 55, 74, 76; engine AD-20, AD-25, AD-30; SOLUTION-DESIGN section 17.

## Update (27c/27d, 2026-10-16 night)

Rows and formula designed in engine AD-30 (27c fix 6): Contabo `overhead_mb` 6,144 gives 4 sessions on 12 GB. Still owed: the measured RAM of one session on the box.
