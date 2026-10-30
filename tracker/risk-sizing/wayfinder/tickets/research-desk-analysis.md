---
title: Research: how trading desks analyse markets and strategies, by style and rhythm
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L15-01, L03-15, L20-06, L03-20, L11-02]
---

## Question

How do human and quant desks analyse markets and strategies day by day, and how does the rhythm differ for scalpers, intraday and swing traders (when they review, recalibrate, pick markets)? Is a daily review done from numbers, chart images, or both? Is weekly market selection backed by evidence, and how? Are session habits (gold at the New York open) an honest almanac or look-ahead? Do fundamentals enter, through what, and with what proof?

Second part, his "multiple experiences" (30 Oct: his own user experience): how does a retail algo trader use today's tools day to day (MT5 with its Strategy Tester and Wizard, cTrader Automate, TradingView, QuantConnect, StrategyQuant, NinjaTrader), from idea to backtest to live to review? Where does each break or stall? Which of those steps would units, QMX workflows, the MIS and self-configuring change, and which would they not? Evidence from user forums, docs and reviews, not marketing pages.

## Why it matters

QMX agents as analysts is a seed to expand (STATE 10-29/30). He: "A human trader who's a scalper will not wake up at the same time to look at charts as a person who day trades" (T2:132). Feeds the analyst-workflows ticket.

## Start from

- `research/19-grounding-old-system.md` §8 (Cartographer Week-Map, Coroner, Crowd Watcher) and §2 (weekly pair selection on evidence).
- `research/42-grounding-shipped-code.md` (45 templates at the stack tip; 22 run, 23 are drafts) and `research/funnel7-workflows/party-brainstorm/workflows-field.md` (57 candidate templates, the Hermes workflows to take and enhance).
- `research/18-grounding-today.md` §1.5 (46 templates: `morning-market-brief`, `morning-digest`, `weekly-review`, `trade-journal-in-risk-units`).
- `research/11-papers-llm-quant.md` (news sentiment, the units-agree study).
- Trader journaling practice; prop-desk morning and end-of-day routines.

## What would settle it

A catalogue of analyses by style and cadence, with inputs and outputs, mapped onto shipped templates, marking which wait on missing doors.

## Output

`research/30-desk-analysis.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).

## Resolution (2026-10-30)

Session habits are an honest almanac for activity, not profit; six places where today's tools stall, five of which units, journals, workflows and the MIS address (research 30).
