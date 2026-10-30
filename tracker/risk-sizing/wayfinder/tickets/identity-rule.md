---
title: What makes two units the same unit
type: grilling
mode: HITL
status: open
blocked_by: [unit-structure]
claimed_by: ""
created: 2026-10-24
updated: 2026-10-30
covers: [C2, C3, Q5, Q6, Q7, Q8, Q9, L01-05, L01-10, L01-07, L02-11, L02-15, Q52, L19-08]
---

## Question

Under System 1, is the same logic on a new instrument a sibling unit, the same unit with per-market settings, a child record, or only a tag? Does his 27 Oct "yes" to sibling units still stand after 28 Oct? Is a timeframe change a coordinate, a logic change, a calibration or a style change, and does that differ for tick or volume bars? Does the type of edit decide identity mechanically, so no agent judges it? What counts as a logic change, and what happens to children when the parent gets a new logic version? Is a swapped sizing module the same unit? Can one unit hold several logics and stay one unit? What is a "family"? Whatever wins: where do the journal, the try count and his click go when a unit starts on a second market?

## Why it matters

Every downstream rule (tries, journals, sizing records, his click, the family tree) needs this, and the 28 Oct shift broke the old instrument-based answer (`research/funnel3/cis/problem-solving.md` §3.1).

## Read first

`research/funnel3/cis/problem-solving.md` step 5b rows C2 and C3; `research/funnel3/cis/glossary-draft.md` "variant", "sibling", "child", "parent", "family", "timeframe"; `research/10-hermes-stats-goldmine.md` (the edit-type rule).

## Was (24 Oct)

When is a change a new strategy, a variant (instrument, timeframe, window) or a new risk-profile version? Lineage rules.

## How to run it

With him, live, using the `grilling` and `domain-modeling` skills. Before the session the lead converges this ticket's research into options and an explainer page (STATE planning run, step 4). Never answer for him.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
