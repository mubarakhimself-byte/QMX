---
title: Research: the broker and instrument facts a unit must have checked
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L05-01, L05-05, L05-12, L05-07, Q80]
---

## Question

Which slow facts per broker, account type and instrument must a unit have checked: tick and lot size, trading hours, spread and commission by hour, swap or funding, expiry and roll, rationed order actions, data available? How do early CFD expiries and rolls reach a unit that holds a position through them? How does a unit learn it is on a venue that rations order actions?

The domain widened on 30 Oct: cover FX, gold and metals, index CFDs, real futures, stocks and stock CFDs, crypto spot and perps. Taken over from the closed small-account ticket: per instrument and venue, the minimum lot, lot step, money per point and margin, so the risk session can work out what a small account can trade. Give the facts only; no risk percentages or account sizes (those are the risk session's). ("Terrain" was a brainstorming name, not a QMX word.)

## Why it matters

These facts are half the model and have no home (research 16). Research 43 proposes one record per instrument per broker (foundation F6); this ticket fills its field list. Contract specs are MISSING in code (research 18 §8). Feeds the instruments ticket and the journey prototype.

## Start from

- `research/02-instruments-and-traders.md`, `research/16-fable-advice-system1-context.md` §2, `research/12-data-feeds-lookback.md` (market journal), `research/18-grounding-today.md` §8.
- `research/43-convergence.md` foundation F6.
- IC Markets contract specifications; Hyperliquid docs; CME and other exchange contract specs for the futures in scope. Keep apart from research 38 (who gives which data and how QMX connects) and 33 (history depth).

## What would settle it

A field list per instrument class with where each fact comes from (broker API, document, measured), plus the expiry and roll cases.

## Output

`research/32-terrain-and-venues.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
