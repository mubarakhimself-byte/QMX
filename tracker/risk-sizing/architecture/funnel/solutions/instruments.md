# The instrument record: one page of facts per market per venue

**What this part is.** He did not name it, but nearly every other part reads it. One record per instrument per venue: what one point is worth, the smallest size, the hours in the market's own zone, swap or funding, expiry and roll, margin, which data levels the venue offers, measured costs, the data licence. Plus the account record beside it (netting or hedging) and the venue's rules row (rate limits, rationed actions). It is how QMX is "designed for futures accounts and every instrument now" (STATE mid r29) without trading them yet.

**Verdict: core.** A Library kind with a snapshot on every trading machine, so a unit's sizer and exits have contract facts with the Library down (standing order 10).

## His words

- "Let's go with FX, futures, metals, of course CFDs." (T3:903)
- "For now, let's trade them the way they come." (T3:1099)
- "I think I'll use CME, man." (T3:1562) "When the app is live, I'll be spoiled for choice" (T3:1562)
- "No limits, okay? That's why nothing is capped." (T3:1105)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| A stored per-broker instrument record | MISSING; `symbol_info` returns the raw venue document | G1 §5 |
| `ValueFactor` (money per price step per quantity), "sourced only from a venue instrument-metadata record" | BUILT (type only) | G1 §5 |
| QMB's replay metadata is the instrument plus a price scale; lot step and value factor arrive on each run's Book input | BUILT | G1 §5; `07-qmb-lineage.md` §3 |
| Calendars: only the `forex-17NY` market-hours provider | BUILT (forex only) | G2 §9; G3 §1.1 |
| CT-03 instrument identity; DEC-0015 "no futures and no options ever" | BUILT; DEC-0015 contradicts the rulings | research 43 F6 |
| cTrader has no expiry field and no money-per-tick field; money per point is computed with a conversion symbol; an ending arrives as a change to close-only | venue fact | research 43 F6 (research 32 §1.3, §1.7) |
| The account's netting or hedging mode from `ProtoOAAccountType` | venue fact | research 43 F6 |
| `tzdata` pinned at 2025.2 (latest 2026.6) | BUILT | G3 §5 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? |
| --- | --- | --- |
| One record per instrument per venue: identity, contract facts, measured costs, calendar in venue and broker server time with DST, carry (swap, perps funding interval and history, roll and expiry), data levels, licence; the account's netting or hedging beside it; a snapshot on the trading machine | research 43 F6 | Yes |
| The full field list per class and venue, each with where the fact comes from (venue API, broker or exchange documents, or only by measuring) | research 32 §1 | Yes, as the field list |
| Refresh from the venue, never typed once: API facts daily plus every change event; broker documents weekly; exchange documents monthly | research 43 F6 (research 32 §6) | Yes |
| Rationed order actions in a venue rules row, with a live counter in the market journal where the venue offers one | research 43 F6 (research 32 §4) | Yes |
| Data levels with three splits: volume kind, depth grade, the clock and history depth of each derivatives field; each level with its licence | research 45 §2; research 33 §3 | Yes |
| LEAN's symbol-properties schema as the model: venue, symbol, type, quote currency, contract multiplier, tick size, lot size, minimum order size, plus swap, funding, margin tiers, expiry and roll | `07-qmb-lineage.md` §8 B-L1 | Yes |
| What a unit needs to trade futures: contract size and tick value, the live contract and roll date, expiry and settlement, sessions in the exchange's zone with halts and holidays, intraday against overnight margin, a data entitlement check, price-limit state | research 54 §3.3 | Yes |

## 3. The shapes

### Shape A. A Library kind per instrument at venue, a venue rules row, an account record, refreshed from the venue (recommended)

- **What.** `instrument` items keyed by (venue, symbol), versioned, with a card and a page; a `venue` item with its rules (rate limits, rationed actions, cancel-on-disconnect behaviour, trigger price basis); the account record (broker, account id, type, netting or hedging, demo or live). A refresh job per venue writes new versions when facts change.
- **Hard cases.** A wrong conversion symbol (a conversion check: money per point computed two ways must agree); a cTrader futures CFD that silently turns close-only (the change event lands a new version and a flag three trading days before); Binance's minimum order value moving (refreshed daily); funding intervals per symbol; Hyperliquid's open-order cap.
- **Explain.** "Every market QMX can trade has one page of facts, kept fresh from the broker. Units and the backtester read the page; nobody types a number in by hand."

### Shape B. A static table in code per venue

- **Why not.** Venue facts move (research 32 §0: a minimum order value read 50 against 5 in an older example); a code release per fact change is wrong.

### Shape C. Read the venue live every time (`symbol_info`)

- **Why not.** A unit would need the broker's metadata call to answer before it can size, and QMB could never replay what the facts were on a past date.

**Pick: Shape A.**

## 4. The fields, by class

| Group | FX and metals CFDs | Index CFDs | Perps | Futures | Spot crypto |
| --- | --- | --- | --- | --- | --- |
| Identity | symbol, venue, quote currency, digits | same | same, plus the oracle and mark source | exchange, root, contract month, symbol per month | same |
| Size | lot size, lot step, minimum lot, maximum exposure | same | contract unit (1 underlying), size step, minimum order value | multiplier (ES 50, MES 5 dollars a point), minimum 1 contract | size step, minimum order value |
| Price | tick size; money per point computed with a conversion check | same | tick size | tick size and tick value (ES 0.25 = 12.50 dollars) | tick size |
| Hours | weekly schedule in its own zone, holidays, breaks; broker server time (IC at GMT+2 winter, GMT+3 summer) | per-index daily breaks | 24/7; the funding clock | sessions in the exchange zone (CME Sunday to Friday, 17:00 to 16:00 Chicago, a daily break), halts | 24/7 |
| Carry | swap long and short, the triple-swap day | financing, three times on Friday; dividend cash events | funding interval (Hyperliquid hourly; Binance 1, 4 or 8 hours) and rate history | none; roll cost by spread between months | none |
| Ending | none, except futures CFDs: expiry from documents, close-only by event | same | none | expiry, last trade time, settlement, roll date (CME usual: the Monday before the third Friday) | none |
| Margin | leverage tiers, margin estimate | same | margin tiers, maximum leverage, liquidation rule | intraday and overnight margin, price limits (7%, 13%, 20% for index futures) | none |
| Data levels | 1 bars; 2 quote ticks; 3 broker depth with sizes; no tape, no real volume, no open interest | same | 1 to 5: candles, quotes, 20-level book, trades with taker side, funding and open interest | 1 to 5 when a route is on: trades with aggressor side, depth MBP-10 or MBO, open interest end of day | 1 to 4 |
| Licence | the broker's terms (IC's terms on keeping quotes: not yet read, research 43 §3.5) | same | the venue's terms | the exchange's per-month fees through a vendor | the exchange's terms; Binance Vision non-commercial since 26 Aug 2026 |
| Measured (from the market journal) | spread, slippage, fill latency and rejections by hour | same | same | same | same |

## 5. The data-level table is the one table three parts read (insight I4)

For every instrument at every venue, the data levels it offers (with the splits) and their licence. Three readers:
- **The unit checker** (layer D, `qml.md` §7): a block's minimum level must be offered on every market in the unit's list, or a fallback must be declared.
- **The MIS defaults** (`mis.md` §4): which readings a market can have.
- **The futures seam** (`external.md`): a futures data route switched on raises that underlying's levels; nothing else changes.

## 6. Futures accounts, designed now

Without spending anything: the futures fields above exist in the kind; futures instrument records can be written from CME's specifications as `specified` (no live data); the account record has a `futures` account type with intraday and overnight margin; continuous-contract history carries how it was stitched (real prices with a jump at each roll, or back-adjusted) and where each roll falls, so a unit never trains on shifted prices without knowing (research 54 §3.1). A unit for ES or MES can be written, checked and backtested on bar data the moment history exists. Live futures trading waits for a futures broker route he picks (`external.md` §5).

## 7. Numbers (starting defaults, all editable)

| Number | Default | Origin |
| --- | --- | --- |
| API facts refresh | daily plus every change event | research 32 §6 |
| Broker documents refresh | weekly | same |
| Exchange documents refresh | monthly | same |
| A broker calendar older than this is suspect | 31 days | research 54 §4.3 |
| Flag before close-only | 3 trading days | research 43 §5 |
| Conversion check tolerance (money per point computed two ways) | 0.1% | INFERRED |
| Stale symbol (no new entries) | 30 s without a quote for FX majors, counted only inside the open calendar | research 43 §5 (placeholder) |

## 8. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Venue adapters (PC reads) | `instrument` and `venue` items | refreshed facts as new versions |
| Feed keeper | market journal | measured costs that fill the record's measured fields over time |
| Instrument record | QML checker | units of measure, data levels |
| Instrument record | QMB | contract facts, calendars, carry, cost profiles |
| Instrument record | node | a snapshot for every market its units trade |
| Instrument record | MIS | which readings a market can have |

## 9. Open for the architecture step

1. Whether the account record is its own kind or a field group on the existing connections registry.
2. How a contract month rolls in the record (one item per month linked by `rolls-to`, or one root item with month rows).

## 10. Parked

- Options chains (options as context only, later).
- Stocks through MT5, which needs a Windows trading host (research 38 §3.2).
