---
title: Research: how quant desks judge and iterate without overfitting
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L08-05, L08-06, L08-09, L07-05]
---

## Question

How do professional quant desks iterate a strategy without overfitting, and which habits fit agents? In what order should historical and paper judging run? How can QMB's What-If scenarios improve? How is the old "radioactive" sizing (enhanced Kelly with house money) replayed when judging a unit?

## Why it matters

STATE says judging is the product, should use history and paper both, and must account for the old sizing (operator round 10-27, "Judging"). This feeds the ticket on where default numbers come from.

## Start from

- `STATE.md` sections "Judging" and "QMB (testing)".
- `research/03-strategyquant.md`, `research/08-old-qmx-testing-and-decay.md`, `research/11-papers-llm-quant.md`, `research/14-design-idea-studies.md` §9.3.
- `research/18-grounding-today.md` §2 (What-If projection, robustness, sweeps); `research/19-grounding-old-system.md` §5.
- QuantConnect LEAN and Jesse docs (current).

## What would settle it

A sequence of judging steps with what each one catches and what it costs, options for replaying a unit's own sizing in QMB, and a list of What-If gaps.

## Output

`research/26-quant-judging.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
