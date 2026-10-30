---
title: Prototype: one unit's spec, journals and family tree
type: prototype
mode: HITL
status: open
blocked_by: [identity-rule]
claimed_by: ""
created: 2026-10-30
covers: [L09-01, L09-02, L09-05, L09-06, L09-11, L10-01, L10-02, L10-03, L10-07, L11-12, L17-04, L17-08]
---

## Question

How should one unit's records look? Which fields go in the unit journal, the market journal and a router journal without duplication? How are signals not taken and missed trades recorded without a flood of rows? One journal kind written by QMB, paper and live, or several? How are market labels stamped at entry and never recomputed? Does an idea record come before the unit, so lineage starts at the source, and how is "where winners come from" counted? What does the family tree show in preview and in detail? What may agents write into a journal? What must always be explainable in plain words, and what would the unit have earned last week on his account size?

## What to make

Rough example records for one unit from a YouTube source through backtest, paper and a week live: the spec, a few journal rows of each kind, the lineage links, and a sketch of the preview and the detail view. Use the `prototype` skill.

## Why it matters

Journals are the unit's DevOps layer (STATE 10-27). The Library has a `unit` kind with no fields and no `journal` kind (`research/18-grounding-today.md` §6).

## Read first

`STATE.md` operator round 10-27 "Lineage and history" and "Journal"; `research/12-data-feeds-lookback.md` (market journal); `research/10-hermes-stats-goldmine.md` (the A-I record, family tree).

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
