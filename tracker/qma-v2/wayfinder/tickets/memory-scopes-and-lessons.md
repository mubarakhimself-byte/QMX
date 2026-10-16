---
title: Memory scopes and lessons
type: grilling
mode: HITL
status: closed
blocked_by: [session-homes, workflow-engine-contract, memory-candidates-facts]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 8."
closed: 2026-10-16
---

## Question

The memory layers QMX keeps: scopes, what writes to each, size limits, who consolidates, and the lessons and negative-results store that unmanaged workflows read before their first step.

## Why it matters

The operator: memory matters most for autonomous workflows, which must run unmanaged. Today the only memory is Claude's per-workspace auto memory; the scoped provider is deleted; the `lessons` table exists only in a superseded revision (`05` gap 11). BuildAlpha's point stands: revolution 400 is only smarter than revolution 4 if dead ends are stored and read back.

## Candidates

| Candidate | What must be true |
|---|---|
| (a) Files for curated memory (BMad sanctum style, under 200 lines, outside the skill) plus a namespaced SQLite store for scopes `run`, `workflow`, `home`, `operator`, with hard size limits, one writer per scope, and a scheduled consolidation step. Negative results and lessons are rows with tags (signal pool, market, timeframe). | The engine can namespace stores and homes exist. |
| (b) Claude auto memory only. | Only if workflows never share lessons across workspaces. They must. |
| (c) A hosted memory product (Mem0, Hindsight). | Only after the bake-off (B40). The pluggable layer keeps the door open. |

## Recommended answer

(a) now, with the provider interface from B51 so (c) can be tested later. Writes to shared scopes go through consolidation; an overflow errors instead of truncating; session logs are curated, never loaded.

## What the session does

Grilling on what he wants remembered about himself (operator scope) and what a loop may write on its own. Output: the scope table, the lessons schema, the write rules.

## Unblocks

Self-improvement loop, methodology umbrella.

## Sources

`03-workflow-engines.md` §9.3, §10 idea 10; `01-bmad.md` memory agents, idea 11; `BACKLOG.md` B40, B41, B51, B53; `05-qmx-today.md` §7; clipping "The Loop Runs While You Sleep".

## Resolution

Resolved. Engine AD-18 scopes and the `refs/memory/*` owners (Library ENGINE-REQUESTS-ANSWERED L1, L2). (Map rewrite 2026-10-16.)
