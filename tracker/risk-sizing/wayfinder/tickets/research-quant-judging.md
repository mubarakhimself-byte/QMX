---
title: Research: how quant desks judge and iterate without overfitting
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L08-05, L08-06, L08-09, L07-05]
---

## Question

How do professional quant desks iterate a strategy without overfitting, and which habits fit agents? In what order should historical and paper judging run? How can QMB's What-If scenarios improve? How is a change to an exit or a block (not just a number) counted as a try, so the tries ledger at QMB's door stays honest (the open weak point in research 43)? How do desks judge when the unit owns its exits, so an exit change and an entry change are judged the same way?

Out of scope here: replaying the old sizing (enhanced Kelly, house money). That belongs to the risk session (`RISK-SIZING-PACK.md` §6); this ticket only notes what QMB must record so that session's sizing can be replayed later.

## Why it matters

STATE says judging is the product, should use history and paper both, and must account for the old sizing (operator round 10-27, "Judging"). This feeds the ticket on where default numbers come from.

## Start from

- `STATE.md` sections "Judging" and "QMB (testing)".
- `research/03-strategyquant.md`, `research/08-old-qmx-testing-and-decay.md`, `research/11-papers-llm-quant.md`, `research/14-design-idea-studies.md` §9.3.
- `research/18-grounding-today.md` §2 (What-If projection, robustness, sweeps); `research/19-grounding-old-system.md` §5.
- QMB was mostly settled in the 20-28 Oct session: start from `research/08`, `research/12`, `research/14` and the backtest-door section of `STATE.md`, and do not redo them. Holdouts are his choice per study, off by default (rulings 136-137).
- `research/43-convergence.md` (the try ledger at QMB's door, foundation F5).
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

## Resolution (2026-10-30)

An 8-step judging order, cheapest first; exit and block changes counted as tries by how much they change the trades; correlated variants counted by clusters; What-If split into views and counted reruns (research 26).
