# Instrument, venue and account records

Part C, area 4 (Level 0 P4). One page of facts per market per venue, kept fresh from the venue, read by the checker, QMB, the node and the MIS. Rules: spine AD-312, AD-320 under Level 0 AD-9, AD-26. Shapes: `CONTRACTS.md` §9.

His words: "Let's go with FX, futures, metals, of course CFDs." (T3:903); "For now, let's trade them the way they come." (T3:1099).

**Verdict: core.** Three Library kinds and refresh templates; nothing is a mini app, because every part needs the same facts and a sizer must have them with the Library down (a snapshot travels with each deployment).

## 1. What exists

| Piece | State | Where |
| --- | --- | --- |
| A stored per-broker instrument record | MISSING; `symbol_info` returns the raw venue document | G1 §5 |
| `ValueFactor` as a type, "sourced only from a venue instrument-metadata record" | BUILT (type) | G1 §5 |
| The connections registry (one row per broker connection) | BUILT | engine AD-67; `qmx_broker/models.py` |
| Capability check at connect: timestamp unit, daily boundary, bar basis, pip formula, money exponent, netting or hedging | BUILT, never run | `qmn/src/qmn/venue/verify.py` |
| Calendars: only `forex-17NY` | BUILT | `extensions/qmf-calendar-forex/` |
| Governed Library kinds land as drafts; record kinds land directly | BUILT | `qmx_library/landing.py:1-18` |

## 2. The three kinds

Exact keys, so every part reads one spelling (R1-C-10). Keys marked A are the ones Part A's `CONTRACTS.md` §2.3 reads, under the same names; Part A's fixture records (slice A3) use them too. A key-parity test in slice C-02 pins this list against Part A's.

**The class enum (one spelling, underscores, used by records, packs and every part):** `fx`, `metal`, `index_cfd`, `commodity_cfd`, `stock_cfd`, `future`, `perp`, `spot_crypto`, `stock`.

**`instrument`**, one per (venue, symbol), a record kind (no governance: facts, not decisions):

| Key | A | Meaning |
| --- | --- | --- |
| `venue`, `symbol`, `market_id` | A | identity; `market_id` names the underlying (EX-06) |
| `class` | A | the class enum above |
| `currency` | A | the quote currency |
| `digits`, `tick_size` | A | price precision and step |
| `pip` | A | optional `{size, source}`; a pips conversion without it is a checker error |
| `contract_size` | A | units of the underlying per lot (for a future, its multiplier) |
| `value_per_point` | A | money per price unit per lot, with `value_conversion` `{symbol, method}` and `conversion_check` (computed two ways, agreeing within `conversion_tolerance`, default 0.1%, else `status = suspect`) (QML-06) |
| `lot_step`, `min_lot` | A | size steps |
| `max_lot` | A | optional; the venue's largest order |
| `calendar_ref`, `zone` | A | calendar id@version (AD-320) and the market's zone |
| `day_boundary` | A | the broker's daily boundary as measured (CK-05); `server_zone` beside it |
| `data_levels` | A | what the market offers, in Part A's `qmx.data-level/1` (levels 0 to 6 with the volume, depth, derivatives-clock and history splits and the licence, A `CONTRACTS.md` §5.2) |
| `expiry` | A | futures and futures-style CFDs; with `last_trade`, `settlement`, `at_expiry_action` (QB-06, EX-14), `root` and `rolls_to` (§3) |
| `funding_interval` | A | perps; with `funding_source` |
| `leverage`, `margin` | A | versioned leverage tiers; `{intraday, overnight}` margin; with `liquidation_rule` (RS-18, RS-09) |
| `record_version` | A | the Library version, set by the Library |
| `swap` | | `{long, short, triple_day}` for CFDs and forex |
| `financing`, `events` | | financing terms; dated cash events such as `{kind: dividend, at, amount_per_lot, side}` (LD-13) |
| `measured` | | spread, slippage, fill latency and rejections by hour, refreshed from the market journal |
| `status` | | `specified` (written from documents, no live data), `live`, `suspect`, `delisted` |

No record carries a roll rule: the unit names its root and its roll rule (§3), so Part A's §2.3 drops `roll_rule` (R1-C-10).

**`venue`**, one per venue id: `venue`, `rate_limits`, `rationed_actions` (with budgets), `cancel_on_disconnect`, `protective_stop_form` (per order type), `trigger_basis` (`mark`, `last`), `heartbeat_bound_s`, `history_limits` and `retention_measured`, `maintenance_calendar_ref`, `unattended` (`allowed`, `manual_login`, `server_banned`), `needs_desktop_app`, `sandbox` (`demo`, `testnet`, none), `data_levels` (offered, `qmx.data-level/1`), `region` where the venue states it (cTrader at IC: London LD5).

**`account`**, one per (venue, account id): `venue`, `account_id`, `broker`, `world` (`demo` or `live`, proven by the venue), `position_mode` (`netting`, `hedging`), `account_type` (`cfd`, `futures`, `perps`, `spot`), `subaccount` (Hyperliquid), `base_currency`, `leverage`, `owner` (the owning node's `{install_id, tag}`, or none), `grant_scope` (the scope it was read under).

**One market, two venues (EX-06).** `market_id` names the underlying (`gold`, `sp500`, `eurusd`, `btc`); gold at two CFD brokers and the GC future share `gold`. Cross-venue comparisons and the cross-source offset check key on it.

## 3. Futures, designed now

Each contract month is its own `instrument` (it is what trades), with `root` (`ES`, `MES`, `GC`), `expiry`, `last_trade`, `settlement` and `rolls_to` the next month. A unit names a root and a roll rule (calendar, volume or open interest); the rule is the unit's, because a unit picks its roll, and the record only lists the months; the runtime and QMB resolve the live contract from the calendar and record which contract every trade used (EX-13). Records are `specified` from CME's documents until a futures route is on. History carries how contracts were stitched and where each roll falls (Part B's data card).

Index CFD dividends are dated cash events on the record (`events: [{kind: dividend, at, amount_per_lot, side}]`), versioned, which QMB replays as cash events (LD-13).

## 4. Refresh, versions and who notices a change

| Source | Cadence | Writes |
| --- | --- | --- |
| Venue API facts (cTrader symbols, CCXT markets) | daily and on every change event | new `instrument` and `venue` versions |
| Broker documents (swap tables, holiday notices) | weekly | new versions |
| Exchange documents (contract specs, calendars) | monthly | new versions |
| The market journal's measured costs | daily | the measured fields |

Refresh runs as workflow templates on This PC with the host's read grant (`refresh-ctrader-records`, `refresh-ccxt-records`, `refresh-calendars`), each a script step through the shipped template shape; an empty or failing refresh keeps the last version in force and flags a record older than its maximum age.

**A broker change while units trade (TN-25, TN-26, RS-18, EX-22).** On the trading machine the node is the authoritative detector for its own symbols: a cTrader symbol change event, a CCXT market reload, or a re-verification that finds a different lot step, margin, digits, leverage or trading mode, or a delisting, writes a spec-change event in the node journal and stands that symbol's units down (Level 0 AD-38's row) until his click on the change card, which shows the old and new facts and the checker's rerun. This PC's next refresh lands the matching record version; the node's deployments keep their snapshot until he redeploys with the new one.

**Calendars (CK-12, LD-02).** Each calendar is data with an id, a version and `calendar_max_age_days` (31). Completeness of history and staleness of feeds are judged against each instrument's own calendar.

## 5. Snapshots

A deployment carries the snapshot of every record it uses (instrument per market, venue, account). The node never reads the Library to trade. A snapshot is the record's content plus its id@version and fingerprint. Agents, templates and the checker on This PC read a record through the core row `instrument_get` (`CONTRACTS.md` §12, slice C-24), the version in force at an instant.

## 6. What must not break, and checks

| Must not break | Check |
| --- | --- |
| A unit's risk in R is the same at two brokers for one market | a test sizes the dummy unit on two `gold` records (100 oz and 1 oz contracts) and asserts equal R |
| Pips | a conversion in pips without a pip definition on the record is a checker error (Part A layer C reads the record) |
| No silent fact change | a test feeds a changed lot step event to the node and asserts the stand-down and the change card |
| Library additions only | the new kind files load; the shipped kind tests stay green |
| One spelling across parts | the key-parity test (slice C-02): the instrument kind holds every key of Part A's §2.3 list, its class enum equals §2's, and no record carries `roll_rule` |

## 7. Ledger rows, growth seam

- Binds: X-01, X-02, X-07, B-04 (all instrument types by default), CC-07.
- Growth seam: a new class is records, a calendar and a pack; a new venue is a `venue` record plus its refresh adapter.
