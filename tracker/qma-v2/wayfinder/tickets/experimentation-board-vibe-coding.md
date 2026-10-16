---
title: Experimentation Board as vibe coding
type: prototype
mode: HITL
status: closed
blocked_by: [decision-6-board-on-backend, decision-5-checks-bind-agents-only, workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Run scope was kept, not deleted (study 24); the Board is the Lab node editor saved in the session (ruling 31); blocked on superseded decision 6."
closed: 2026-10-16
---

## Question

How the Experimentation Board takes a non-technical person from a rough idea to the thing he meant in the fewest iterations, and what the board object holds.

## Why it matters

Correction C: the board is vibe coding for trading, and its design goal is fewer round trips. The docs keep it client-only; `run_scope` was designed once and deleted (`05` §3, §7). BMad-style method (elicitation up front, a spec card, gates) is the lever.

## Recommended answer

The eight levers in `12` section (e): numbered question rounds with recommended answers; a "what I understood" card before anything runs; options side by side (arena) instead of drafts; gates that run on every "run this section"; run scope (one step, a section, all); an operator memory of rejected ideas; templates from boards that reached paper; a visible iteration counter per idea that the weekly review lowers. The board is a small backend object (notes, questions, charts, unfinished pieces, runnable sections, a workflow draft) and overrides the docs' client-only rule. Promotion out of the board goes only through the funnel's gates.

## What the session does

Prototype three board layouts on demo data with the same rough idea driven to a term sheet; count the round trips in each; he picks. Output: the board object fields, the elicitation script, the promotion rule, a note to update ADR-0024.

## Unblocks

Lab overnight loop; feeds the build plan.

## Sources

`12` section (e); `05-qmx-today.md` §3, §7; `01-bmad.md` elicitation, idea 17; `02-pocock-pstack.md` grilling, arena, prototype; correction C.

## Resolution

Resolved. Ruling 31, engine AD-11 (saved draft; selected-subgraph test runs kept) and Lab AD-2 (one draft; Graph and Code are projections). (Map rewrite 2026-10-16.)
