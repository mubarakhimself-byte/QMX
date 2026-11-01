# The MIS

Part C, area 2. The market intelligence service reads markets and publishes what it saw; units pick from it; none needs it to trade. Rules: spine AD-313, AD-314, AD-319, AD-320 under Level 0 AD-2, AD-5, AD-40. Shapes: `CONTRACTS.md` §7 and §8.

**Verdict: the readings are core, the publisher is a mini app.** Reading blocks and the reading runner are core library code (`packages/qmf-readings`), because a unit, QMB and the MIS must run one code (MIS-04). The `mis` app (risk `shows`) is the publisher, because it is a long-running job with its own schedule, volume and health, exactly what the mini-app core gives.

## 1. His visions, kept as seeds

- "What I wanted was the MIS just reads and outputs." (T1:1951) The core is a reader and a publisher, nothing more. Units pick.
- "we need a trading style, firstly" (T2:219) and "we are going to consider variables that each market has" (T2:219). His order (style, then timeframe, then the data a market offers) becomes three labels on every reading: its tier (the clock it runs on, set by style and timeframe), its time base, and its minimum data level (set by what the venue offers). Instruments matter through their data.
- "you are not going to put an HMM inside a scalper's MIS" (T2:219). A scalper's readings are fast indicators on tick and bar tiers; HMMs and other fitted regime models sit on the day tier, where the slow switch they need is affordable (research 22 §6).
- "categorizing by instrument type" (T1:1999). One shared set of reading words, with a default pack per instrument class; fitted models are pooled by class or by underlying, never shared across classes (research 23 §2).
- "It means that specificity is simpler." (T1:1999) and, on 31 Oct, the levels of specificity, "how the MIS can work on one market alone" (log 2026-10-31T10:50). Specificity is a configuration: the same runner reads one market, a class, or everything. A reading's usual level is that market's own (same minute of its session, its own history), so a one-market MIS is the general MIS named with one market, never a separate design.
- "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264) and "So the MIS itself is incomplete." (T3:1264). Defaults for every class now; a model slot behind the same reading shape.
- "They should be using the logs from the MIS." (T3:903). Workflows and agents read reading history, never a model.
- "the MIS can be upgraded as the agent see fit, obviously with my approval" (T1:1951). Agents propose new readings in shadow; his yes makes one live (ruling 50: agents only in the slow lane).

## 2. What exists

| Piece | State | Where |
| --- | --- | --- |
| `qmn/src/qmn/mis/`, 12,654 lines: identity, spread state, gap event, feed state, SQS, degraded sensors, a quantile liquidity fit, an untrained volatility classifier | BUILT, never run on a venue | G1 §6.1 |
| Its consumers closed to the Book door and the kill switch | BUILT (to change) | `qmn/src/qmn/mis/signal_snapshot.py:1-4` |
| Its register imports the promotion hub, which the cut deletes | BUILT (to move) | `qmn/src/qmn/mis/regime_register.py:60-61` |
| "Regime" labels that measure volatility only | BUILT | `qmn/src/qmn/mis/regime_design.py:72-78` |
| Four homes for its output: market-data partitions, Library records, a `provides` contract with `stale_after`, OpenObserve | BUILT (homes) | G4b Q6 |
| The Lab's PC training placement (GPU slot, disk check, exact partitions, fingerprints) | BUILT, never run | `qmx_control/lab.py:13-18` |
| An app's `data_reads` capability | declared, logged, not enforced | `qmx_apps/manifest.py:78`; `supervisor.py:700` |
| Apps cannot write outside their volume | BUILT | `qmx_apps/bootstrap.py:93-100` |
| The market-data store's open month is one file replaced on each commit | BUILT | `packages/qmf-data/src/qmf/data/series.py:1-20`, `:564` |

## 3. Where each reading runs

| Tier | Runs in | Reads | Writes | Why there |
| --- | --- | --- | --- | --- |
| Tick (spread against usual, SQS, quote gaps, feed state, tick rate, depth against usual and imbalance, order-flow pressure, liquidity stress) | the node, on a trading machine | the feed keeper's events in process | reading records `source = node` in the node's append store | only the node holds the live connection (AD-8); the execution-health ones are its guards (Level 0 AD-40) |
| Bar (range volatility against usual, volatility state, small change detectors) | the `mis` app's instance on that machine | the open month of bars Part B's records job harvests into that machine's store every `[records] open_harvest_s` (60) | records `source = mis` in its volume | needs only bars; lag of one harvest is fine for a bar-tier published history |
| Session and day (efficiency ratio, variance ratio, Hurst, trend against range, calendar states, funding, open interest, roll, cash open, fixes) | the `mis` instance on that machine for its markets; This PC's instance for every other market | bars and derivatives fields from the store | records `source = mis` | slow; never on the order path |
| Cross-market (currency strength, dispersion, herding counts, dated pair readings) and the board | This PC's instance | the Library's history of every market | records and the board artifact | needs every market at once |
| Models in shadow | This PC's instance | Library history; a pinned weights file | shadow records | training and shadow runs belong to the PC and the Lab |

One writer per series: the series key carries source, reading id and version, market id, instrument and machine. This PC's instance never computes a tier a trading machine publishes for its own markets; for a market no node trades, the PC computes it.

**How the `mis` app reads data.** The supervisor hands an app whose manifest declares `data_reads = ["market"]` one more variable, `QMX_MARKET_ROOT`, the machine's market-data store root; the app reads partitions with `qmf.data.series` readers. It cannot write there, because the bootstrap refuses writes outside the volume. This is item 4 of Level 0's list of core changes (R1 CF-4, slice C-05b): without it no app can read market data at all. The raw root bypasses the door's holdout and its read log, so the app reads the `holdout` in its host facts (`road/host/facts.json`, the Settings `[data]` seal) and skips every month it seals; no reading over a sealed month lands in history (R1-C-13).

**How the `mis` app is told what to read.** An operation `configure` (`domain_write`, `state = "instance"`) takes the markets, each instrument record's snapshot (calendar, data levels), and the pack ids@version. This PC's node link calls it when deployments change on a node's machine; This PC configures its own instance from his admitted universe.

## 4. The default packs

Each reading has a tier, a minimum data level in Part A's `qmx.data-level/1` (0 calendar, 1 bars, 2 quote ticks, 3 depth, 4 tape with aggressor side, 5 derivatives fields; 6, outside data, has no default reading yet), a price input (mid, bid, ask or trade) and a fallback chain. A market gets only what its levels allow. Every class of the instrument record's enum (`RECORDS.md` §2) has a pack, named `<class>-<n>` and pinned by id and version: `fx-1`, `metal-1`, `index_cfd-1`, `future-1`, `perp-1`, `spot_crypto-1` follow the columns below; `commodity_cfd-1`, `stock_cfd-1` and `stock-1` take every row marked for all six columns, and `stock_cfd-1` and `stock-1` add the cash-open rows.

| Reading | Tier | Level | `fx` | `metal` | `index_cfd` | `future` | `perp` | `spot_crypto` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Range volatility against usual (bar ranges, same minute of session, 20 weeks) | bar | 1 | yes | yes | yes | yes | yes | yes |
| Volatility state (quiet, normal, elevated, stressed) | bar, session | 1 | yes | yes | yes | yes | yes | yes |
| Spread against usual; SQS | tick | 2 | yes | yes | yes | yes | yes | yes |
| Tick rate against usual (never called volume) | tick | 2 | yes | yes | yes | yes | yes | yes |
| Quote gaps, feed state, degraded sensors | tick | 2 | yes | yes | yes | yes | yes | yes |
| Liquidity stress | bar | 2 | yes | yes | yes | yes | yes | yes |
| Change detectors (CUSUM on returns, two-scale volatility, Kalman level) | bar | 1 | yes | yes | yes | yes | yes | yes |
| Efficiency ratio | session | 1 | yes | yes | yes | yes | yes | yes |
| Variance ratio, Hurst (minimum 1,000 points; mid prices; bounce check) | day | 1 | yes | yes | yes | yes | yes | yes |
| Trend against range (his "regime") | session, day | 1 | yes | yes | yes | yes | yes | yes |
| Calendar states (session windows, holidays, dead zones) | calendar | 0 | yes | yes | yes | yes | yes (activity sessions) | yes (activity sessions) |
| Depth against usual; depth imbalance | tick | 3 | cTrader broker depth | cTrader | cTrader | with a route | yes | yes |
| Order-flow pressure (delta, imbalance; 30 s horizon) with fallbacks to depth imbalance, tick rule, range pressure | tick | 4, falling to 3, 2, 1 | estimate | estimate | estimate | with a route | yes | yes |
| Funding state, extreme tail, open interest change, mark against last, basis | bar, session | 5 | | | | open interest end of day | yes | |
| Roll state, days to expiry, price-limit state, session in the exchange zone | calendar, session | 0, 5 | | | futures-style CFDs | yes | | |
| Cash open, opening drive, initial balance, overnight range | session | 1 | | | yes | index futures | HIP-3 index perps | |
| London fix windows (10:30, 15:00 London) | calendar | 0 | | gold | | gold futures | HIP-3 gold | |
| Currency strength, dispersion, herding counts, dated pair readings | session, day | 1 | yes (PC) | any (PC) | any (PC) | any (PC) | any (PC) | any (PC) |

"Estimate" means a broker-side estimate from cTrader ticks and depth, labelled so on every record (spine AD-311).

## 5. The reading record and freshness

The record is spine AD-314's (`CONTRACTS.md` §7). Freshness per tier (`stale_after`): tick 2 s, bar one bar, session one session, day one day. A consumer that finds a record older than its `stale_after` treats the reading as absent and takes its declared fallback (`compute_here`, `treat_as_absent`, `no_new_entries`, from Part A's `reads` list). Health words: fresh, stale, degraded (a fallback step taken), thin (too little history, for example a baseline after a DST change, CK-10), shadow, retired.

## 6. The board, and why units do not need it

The board is This PC's answer to "which of his admitted markets are in a given condition now", one artifact per tier with `stale_after`, for the slow-lane shortlist, his screens and agents. In this build it does not reach a trading node: a unit on a node trades every market he admitted on its own conditions (MIS-09), and his shortlist reaches a node only as a deployment change he clicks. The board read inside the node (connections C25) is slice C-22, a Should, through a host feed relay.

## 7. The word "regime"

"Regime" means trend against range on screens and in code; the shipped buckets become "volatility state" (Level 0 LC-A0-20, his word to veto). The rename is one module and its tests in the move to `packages/qmf-readings`.

## 8. Models, shadow, his yes, and agents

- A model reading is a learned catalogue block with its weights as a pinned file with a fingerprint, loaded through Part A's one block loader (Level 0 AD-47); a retrain inside declared bounds is a calibration.
- Trained in the Lab's PC training placement on Library history; it lands with data fingerprints, code version and seed.
- It runs in This PC's instance beside the default, writing shadow records. His yes on the MIS tab flips it live: the next configuration names it. No unit changes, because the reading's id and shape stay; its version moves.
- Agents: a slow-lane template ("check on the MIS") reads reading history through the core row `readings_query` (`CONTRACTS.md` §12, slice C-24) and writes its own dated reading in the MIS's words before a session, scored later against what happened; disagreements land as notes with examples for him (ruling 50). Agents never write reading records.

**One code, checked (MIS-04).** A golden replay runs one recorded day through a dummy unit that binds a reading, through QMB's replay and through the reading runner, and compares the three per reading id and version to the last digit.

## 9. Settings with their starting defaults

| Setting | Default | Origin |
| --- | --- | --- |
| Seasonal baseline | same minute of the session, in venue session time, 20 weeks, refreshed nightly | research 43 §5 |
| False-alarm spacing per reading and market | one episode per 10 trading days | research 22 |
| Volatility window | 10 bars of ranges; 30 bars of closes as fallback | research 22 §3 |
| State length against window before a direction reading may gate | at least 5 | research 22 §4 |
| Bounce ratio | flag above 0.1; block price-only mean-reversion readings above 0.25 | research 22 §2 |
| Order-flow horizon | 30 s | research 37 |
| Funding extreme tail | bottom and top 10% of 180 days | research 37 |
| `[records] open_harvest_s` (Part B's setting, read here) | 60 | R1-B-02 |
| Model refit in shadow | monthly | research 43 §5 |
| Retire card for an unread reading | 8 weeks unread | placeholder |

## 10. What must not break, and checks

| Must not break | Check |
| --- | --- |
| A unit trades with the MIS stopped | a test stops the `mis` app and the node's tick runner and asserts a dummy unit still enters on its own conditions |
| Readings never block the order path | the node's reading runner runs off the feed keeper's fan-out with drop-oldest; a test floods it and asserts slice latency stays under `max_slice_latency` |
| One code | the golden replay of §8 |
| No reading rewritten | the writer refuses to replace a record; a correction is a new linked record (test) |
| The move keeps the labelers' tests | `qmn/tests` for `mis` move with the code into `packages/qmf-readings/tests` and stay green |

## 11. Ledger rows, growth seam

- Binds: M-01 to M-14, M-09, CC-12, L-02, L-03, W-01 (templates read logs).
- Growth seam: a reading is a catalogue block plus a reading card; a class is a pack; a model is a learned block in shadow; a new source of data is a data level on the instrument record.
