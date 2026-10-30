---
title: "Research: the trader's vocabulary beyond FX, per asset class and data level"
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [his 30 Oct calls: "the dictionary must expand far beyond FX"; QML takes priority; the trading lens must be strong]
---

## Question

The dictionary is being rebuilt (lead ruling in the 30 Oct fix round, `research/44-review-of-convergence.md`): the 239 entries are kept as seeds, every entry stays role-neutral, and it must expand far beyond FX and crypto spot. Research 36 measured coverage against MQL5 articles only, which lean towards FX and MetaTrader. What do practitioners in the other classes actually use, by name: index CFDs and real index futures, metals and energy, stocks, crypto spot, crypto perps, and order flow wherever a venue gives it (depth, a trades tape, footprint and delta, volume profile, open interest, funding, basis, liquidations)? For each concept: which family it belongs to (indicator, price action, order flow, context, session, entry, exit, trade management, filter, statistics and models), which data level it needs (calendar, bars, real volume, depth, trades tape, open interest and funding, outside data), which classes it applies to, and what settings it has. Which concepts mean different things across classes under the same name (volume on spot FX versus futures; sessions on 24/7 markets; rollover on CFDs versus futures)? Which statistics and model entries (Hurst, variance ratio, efficiency ratio, hidden Markov and switching models, volatility models) do practitioners use as strategy parts rather than as evaluation words?

## Why it matters

QML is what a unit is made of, and QML takes priority (his 30 Oct correction). Agents building units need one vocabulary so they are never confused (his 25 Oct explanation of deep modules and designing out ambiguity). The QML ticket and the MIS organisation ticket wait on knowing what the expanded vocabulary contains.

## Start from

- `research/34-grounding-qml-and-dictionary.md` (why the dictionary looks the way it does, the pillars history, today's 239 entries).
- `research/36-dictionary-vocabulary-census.md` and its scripts in `research/census36/` (44% coverage, the top missing concepts, MetaTrader built-ins missing). Do not redo the MQL5 census; extend past it.
- `research/funnel4-qml/` (the five parts of a rule, number kinds that work on every instrument, the status ladder per entry), `research/39-gold-mine-session.md` (primitive, role binding and graph as three layers; roles beyond four).
- The dictionary itself: `C:/Users/Mubarak/Desktop/Stats/dictionary/`.
- Practitioner sources, read live: exchange education pages (CME Group, Eurex), platform indicator and study references (TradingView built-ins, NinjaTrader, Sierra Chart, Bookmap, ATAS, Quantower), Hyperliquid and Binance docs for perps terms, and serious practitioner books or articles for order flow and volume profile.

## What would settle it

A table of concepts not in the dictionary today, each with its family, data level, classes, settings and one source. A list of names that mean different things across classes. A list of class packs (which concepts each class needs before a unit can trade it), as options for which pack comes first, not a choice.

## Output

`research/45-dictionary-beyond-fx.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Settings get a starting default only, never a ruling.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute.
