---
title: Research: which platforms and brokers give which markets and data, and how QMX connects to them
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [his 30 Oct seeds: "How am I trading futures? Can I trade futures on cTrader? With order flow and stuff? Then of course, Hyperliquid"; "that external connection of QMX is also important, but also inside the trading node"]
---

## Question

For each market type QMX now aims at (FX, gold and metals, index CFDs, real futures, stocks or stock CFDs, crypto spot, crypto perps), which platforms and brokers can he actually trade it through from his country and account size, and what live data each one gives: quotes, depth, a trades tape, volume, open interest, funding? Specifically: can cTrader (IC Markets) trade real futures or only CFDs, and what does its Open API expose live? Which routes give real futures with order flow at retail size (for example NinjaTrader with Rithmic or CQG, Tradovate, Interactive Brokers, TopstepX and others), with what costs, minimums, API access and machine needs (Windows, Linux, Docker)? What does Hyperliquid's API give for perps (rate and action limits, history depth, order types, keys and signing)? What does MT5 add or block? How does live data reach QMX for each route (one connection per account, sharing between the PC and the node, token refresh rules), and what does the trading node therefore need to hold?

Keep two questions apart (his 30 Oct point): **data providers** (who sells or gives order flow, depth, trades tape, volume, open interest and funding, live and historical, per class: exchanges, vendors such as Databento or Tardis, platform feeds) and **execution routes** (which broker or venue places the order: cTrader, MT5, futures brokers, CCXT for crypto, Hyperliquid). A unit may read data from one and trade through another.

## Why it matters

He widened the domain to futures, perps, indices and more. Order flow, open interest and funding only exist on some routes, so the MIS's data classes, the dictionary's coverage and the node's design all depend on which routes are real for him. The node and PC split ticket and the instruments-first ticket wait on this, beside research 31 and 32.

## Start from

- `research/02-instruments-and-traders.md`, `research/12-data-feeds-lookback.md`, `research/18-grounding-today.md` §7-8, `research/21-old-system-loose-ends.md` §3 (cTrader has quotes and depth, no public trade tape).
- `seeds.md` "Trading node = a trading server" (cTrader on Linux, MT5 on Windows, token refresh rule).
- Vendor docs, read live: cTrader Open API, MT5, NinjaTrader, Rithmic, CQG, Tradovate, Interactive Brokers, Hyperliquid, Binance, Bybit.

## What would settle it

A table: market type × route, with what can be traded, live data given, history given, costs and minimums, API shape and limits, machine needs, and the source for each cell. A short list of the routes that cover the most of his domain for the least setup, as options, not a choice.

## Output

`research/38-venue-connectivity.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Vendor facts come from vendor docs read live, never from old repo notes.
- Keep apart from research 32 (contract facts per instrument) and 33 (history depth); point to them instead of repeating.
- Options and evidence, not a design. Prices and limits are the vendor's, not QMX caps.
- Label every claim CHECKED (URL) or INFERRED. Never read, print or copy keys, tokens or passwords; never sign in anywhere.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute.

## Resolution (2026-10-30)

cTrader cannot trade real futures; real futures with order flow need a futures broker, each with catches (Tradovate data licence, TopstepX bans server orders, IBKR manual login). Eligibility depends on his country, an open question (research 38).
