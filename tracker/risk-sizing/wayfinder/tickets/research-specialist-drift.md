---
title: Research: when an earned specialist's market changes
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L02-04, Q24, Q25, L08-08, L15-05]
---

## Question

How does an earned specialist notice that its market changed after it was earned, and what are the options for what happens then? Can a short backtest on QMX's own recorded live data (a week, a month) add evidence, or is it too short? How long is "no rush" before a specialist is earned? What is the shortest window of QMX's own data worth testing on?

## Why it matters

His own case (T2:216): a specialist made on a pair the unit rarely traded, then the market's structure changes. He also said "backtesting across a week makes no sense. Unless I'm wrong" (T2:216). Earning and expiring share one clock.

## Start from

- `research/08-old-qmx-testing-and-decay.md` (CUSUM on R, the cone, cost and fill drift).
- `research/12-data-feeds-lookback.md` (QMX recording its own data, the market journal).
- `research/05-academic.md`; literature on structural breaks and concept drift in trading strategies.

## What would settle it

Drift detectors with their lag in trades, and a plain evidence statement on short windows. Numbers named with starting defaults only.

## Output

`research/25-specialist-drift.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).

## Resolution (2026-10-30, scope revision)

Merged into `research-earning-a-specialist` (research 24). Earning and expiring share one clock, so one agent studies both.
