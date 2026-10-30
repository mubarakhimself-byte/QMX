---
title: Research: data depth per class, quality checks, and keeping downloaded history
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L08-15, L09-07, L09-10]
---

## Question

How deep does free and paid history go per instrument class, so "no lookback cap" is real? How is data quality checked for each feed? Do Dukascopy's terms allow QMX to keep the history it downloads for personal use?

## Why it matters

Contradiction C30: he wants QMX to stack the data it collects; Dukascopy's terms forbid bots and databases (STATE "For his awareness"). Feeds the data-recording ticket.

## Start from

- `research/12-data-feeds-lookback.md`, `research/18-grounding-today.md` §8.
- dukascopy-node; Dukascopy's terms page; Binance Vision; Databento and Tardis pricing pages.

## What would settle it

A depth table per class and source, a list of quality checks, and a plain statement on the terms with the clause cited (quote under 15 words).

## Output

`research/33-data-depth-and-terms.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
