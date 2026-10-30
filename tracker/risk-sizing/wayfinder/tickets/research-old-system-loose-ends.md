---
title: Research: old-system loose ends (WF4, the pillars, the tick-data fix)
type: research
mode: AFK
status: closed
resolution: resolved
blocked_by: []
claimed_by: ""
created: 2026-10-30
updated: 2026-10-30
covers: [L20-04, L04-04, Q68]
---

## Question

Three short checks against the old sources:
1. Is the old WF4 "Ecological + feature mutation" the same thing as today's domain expansion?
2. Which strategy pillars hold now? He recalls event, trigger, risk and sizing; the ruled Stats baseline is location, context, trigger and confirmation.
3. He said tick data was "an API problem we solved in older versions" (T2:322). Was it solved, how, or is it a broker limit?

## Why it matters

The pillars decide the dictionary's skeleton (the QML and dictionary ticket). The tick-data answer decides whether order-flow sensors are possible on cTrader.

## Start from

- `research/19-grounding-old-system.md` §1 (WF4), §6 (dictionary); `research/10-hermes-stats-goldmine.md`.
- `C:/Users/Mubarak/Desktop/Stats/schema/strategy-dna.md`.
- The old vault `C:/Users/Mubarak/Documents/Claude/QMX-discussion/`, read only, especially `07-Source-Material/gpt-trading-algorithm-research.md`.
- Warning: old Hermes logs contain credentials. Never print or copy them.

## What would settle it

Three answers, each with a CHECKED citation, or "not found" with the searches run.

## Output

`research/21-old-system-loose-ends.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).

## Resolution (2026-10-30, resolved)

Research 21 (Codex, group A): WF4 only partly matches domain expansion; the Stats lock has four pillars (location, context, trigger, confirmation), and his October recollection was uncertain, so the 'four became seven' memory is still unconfirmed; cTrader's Open API gives quotes and depth but no public trade tape. `research/21-old-system-loose-ends.md`.
