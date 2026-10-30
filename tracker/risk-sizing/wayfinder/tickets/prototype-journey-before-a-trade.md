---
title: Prototype: the steps before one trade, and with each part down
type: prototype
mode: HITL
status: open
blocked_by: [unit-structure]
claimed_by: ""
created: 2026-10-30
covers: [L13-01, L13-02, L13-04, L13-05, L13-06, L13-08, Q77, Q4, L14-03, L05-02, L05-03, C38, Q66, L06-07, Q53]
---

## Question

How should the path from a signal to an order behave? Which steps run, in what order, who vetoes first, which are local to the unit and which central, and which may be skipped when the router, the MIS, the feed, the PC or the broker is down? What happens before a unit's first trade on a new market (indicator warm-up), when its MIS input is late, when a market fits but its spread is too high (SQS, a broker-facts check, the unit or the router), and when two of his units want opposite trades on one symbol?

## What to make

A rough walkthrough for one example unit (a 1m mean-reversion scalper): a table of steps, each with what it reads, where it runs, how long it may take, what it logs, and what happens with each part down. Use the `prototype` skill. It is a sketch to react to, not a design.

## Why it matters

He asked for the full list of steps a unit takes before a trade (T2:216). Independence is one rule seen from operations and from the trade path (playing-field cross-map).

## Read first

`research/funnel3/cis/design-thinking.md` journey J2; `research/19-grounding-old-system.md` §2 (Intent Aggregator); `research/18-grounding-today.md` §5 (SQS, KSA, news windows).

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
