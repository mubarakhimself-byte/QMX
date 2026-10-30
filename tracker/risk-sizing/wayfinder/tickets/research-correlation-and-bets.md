---
title: Research: how many independent bets a set of units really holds
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L06-01, L06-02, L06-06, Q13, Q54, Q10]
---

## Question

What should a correlation control measure: currency legs, return correlation, a shared context label, dated by method and horizon? On a day when 20 markets match one unit's context, how many independent bets are there by pairwise correlation, by effective number of bets, and by shared label, and do they agree? Is a simple bet counter (units entering on the same label within some minutes count as one) as safe? When the 1m and 5m versions of one logic move together, is that one bet or two? Which of the correlation controls he remembers existed, and in what form (research 19 and the CIS census may already close this; confirm)?

## Why it matters

He says the correlation ledger exists (T2:322); agents found the name reused for order lineage. Breadth is not independence (research 16, break 3). Feeds the correlation-control ticket.

## Start from

- `research/funnel3/cis/problem-solving.md` knot (c) (the six-era census and ten options).
- `research/19-grounding-old-system.md` §2 (Intent Aggregator), §4; `research/18-grounding-today.md` §5.
- Shipped maths: the draft hourly workflow `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/rk2-correlation-drift/` and `packages/qmf-risk/src/qmf/risk/door.py:315-347` on `origin/engine/base`.
- Literature: effective number of bets, correlation instability in FX.

## What would settle it

A replay of one or more past days with many matching markets, bets counted three ways, and whether the counts agree. A list of which control jobs the evidence supports.

## Output

`research/27-correlation-and-bets.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).

## Resolution (2026-10-30, scope revision)

Moved to the risk-and-sizing session. His 30 Oct ruling put the book and correlation control there (`STATE.md`, corrections 30 Oct evening). The questions are carried in `RISK-SIZING-PACK.md` §6. This run keeps only what the unit records for that session: the readings stamped at entry and exit (research 43, foundation F1).
