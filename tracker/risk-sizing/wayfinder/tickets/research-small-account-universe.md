---
title: Research: what a $300 account can trade, and whether breadth amplifies a weak edge
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L05-07, Q80, L18-04]
---

## Question

With $300, which instruments can a unit trade at safe risk at the minimum lot, per venue (cTrader on IC Markets, Hyperliquid)? Can one unit hold more than two or three markets at once at safe risk? Does trading breadth amplify a weak edge, as he says, and how would that be shown?

## Why it matters

"$300 picks the universe before the MIS does" (research 16 §7.3). Contradiction C36: grow $300 with one or two units, or compound across breadth. This blocks the ticket on what QMX does first.

## Start from

- `research/02-instruments-and-traders.md`, `research/16-fable-advice-system1-context.md` §7.3, `research/funnel3/cis/innovation-strategy.md` (H2).
- IC Markets cTrader contract specifications; Hyperliquid docs (minimum order size, margin).
- Literature on breadth and edge (the fundamental law of active management) and on Kelly with many simultaneous bets.

## What would settle it

A table per instrument: minimum lot, money per point, risk at the minimum lot as a share of $300 at typical stop distances; how many can run at once; the breadth argument with its assumptions named. Risk levels are named defaults, not rulings.

## Output

`research/28-small-account-universe.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
