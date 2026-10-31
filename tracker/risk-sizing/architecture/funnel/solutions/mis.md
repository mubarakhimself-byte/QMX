# The MIS: reading every market, publishing what it saw

**What this part is.** The market intelligence service: the readings of market state (volatility, spread and activity against usual, trend against range, calendar states, funding and open interest, order flow where the data exists), their defaults for every instrument class in scope, the room for models he trains later, where its readings are published, and how a unit uses them without ever needing them to trade.

**Verdict: split.** The readings are **core**: they are catalogue blocks that a unit, QMB and the MIS all run with the same code. The process that runs them across many markets and publishes the board and the history is **a mini app** (`mis`) with two instances: one on each trading node for its own markets' fast tier, one on his PC for the slow tier, the cross-market board and models. His ruling that the node sets up the MIS (STATE mid r35) is the node's setup installing that instance.

## His words

- "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264) "So the MIS itself is incomplete." (T3:1264)
- "What I wanted was the MIS just reads and outputs." (T1:1951)
- "you are not going to put an HMM inside a scalper's MIS" (T2:219)
- "categorizing by instrument type" (T1:1999)
- "They should be using the logs from the MIS." (T3:903)
- "the MIS can be upgraded as the agent see fit, obviously with my approval" (T1:1951)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| `qmn/src/qmn/mis/`, 12,654 lines, inside the node | BUILT, never run on a venue | G1 §6.1 |
| Rule producers: identity, spread state, gap event, feed state, SQS (spread quality: baseline over live spread), degraded sensors | BUILT | G1 §6.1 |
| `liquidity_stress_v1`: an exact quantile fit, "not a trained model" | BUILT | G1 §6.1 |
| `regime_classifier_v1`: volatility only (quiet, normal, elevated, stressed), "never a direction claim"; corpus must cover three FX sessions; training backend `lightgbm` absent | BUILT, never run | G1 §6.1 |
| Publishing to a closed set: the Book door and the kill switch, "never bots"; a publish-only shadow lane | BUILT | G1 §6.1 |
| QMB imports nothing from QMN, so backtest trades carry no MIS readings | BUILT (absence) | G1 §6.1 |
| On the agent side: no MIS tool and no MIS log | MISSING | G2 §3 |
| Templates that expect the node's MIS state, waiting on `needs: trading-node` | BUILT as drafts | G4b §0 item 6 |
| Four homes that could hold MIS output: market-data store partitions with a derived kind (as `rsi-v1` already is), Library records with event triggers, a mini app's `provides` contract with `stale_after`, OpenTelemetry into OpenObserve | BUILT (homes) | G4b Q6 |
| The Lab's PC training placement: a GPU slot, a free-disk check, exactly the partitions it needs; the model lands with data fingerprints, code version and seed | BUILT, never run | G2 §5.2 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? |
| --- | --- | --- |
| The "telescope": readings are library code; the MIS runs them across markets on per-tier clocks, stores stamped history, publishes a board and match lists; no unit needs it to trade | research 43 §3.3 | Yes (M-01) |
| Readings stored with the moment they were made: id, version, compute time, input receive times, health; append-only; as-of queries; backfill flags; a golden replay checks one code in QMB and live | research 43 F2; funnel5 intent item 2 | Yes |
| His order (style, then timeframe, then data) as three labels on every reading: its clock tier, its horizon, its minimum data level; an asset class as a pack | research 43 §3.3; funnel5 intent frame | Yes (M-04) |
| Three outputs per reading: the raw number, its percentile against the usual for that instrument and minute of the session, and a word | research 43 §3.3 | Yes |
| Speeds: a 50% volatility jump shows in about 27 bars from closes, about 8 from bar ranges; strong trend or mean reversion takes about 4 hours on 1m or 5m bars, weak a day or more; so direction labels live on session and day tiers | research 22 §2 (simulated) | Yes |
| The rule that sorts readings is lag against the unit's holding time; an HMM belongs on the day tier | research 43 §3.3 (research 22 §6) | Yes, sharpening his HMM line |
| Bounce check before a price-only mean-reversion reading goes live; a direction label gates trades only where states outlast the window by a set ratio | research 22 §2, §4 | Yes |
| One shared word set with sensors per class and a same-meaning check; readings keyed by underlying, each venue a data ladder; fitted models do not transfer across assets | research 23 §2, §3 | Yes (M-11) |
| Market state reveals tradeable patterns that decay about 58% after publication | research 37 §7 | Yes, as a source of units, not a part |
| The finder, not the filter: for units whose rules already state their context, the MIS answers "where else is this true now" | funnel5 intent item 1 | Yes |
| Dispersion, herding counts and dated pair readings published for the risk session; description, not control | funnel5 intent item 6; research 43 §3.3 | Yes |
| One live version per reading, new ones in shadow, live only with his yes | research 43 §3.3 (his August "constant") | Yes (M-10) |
| Dark-MIS run, shuffled-readings run, hindsight-premium run as optional judge stages | research 43 §3.3 | Yes, in `judging.md` |
| One meaning for "regime" | research 43 §3.3 and decision 8; research 29 F7 | Settled below as a lead's call |

## 3. The shapes

### Shape A. Readings in the catalogue; the MIS as a mini app with two instances publishing into homes that exist (recommended)

- **What.** Every reading is a catalogue block with a reading card (§5). A unit computes the readings its rules need from its own feed. The `mis` app runs the default reading pack across the markets a machine can see, on tier clocks, and publishes: history into market-data partitions (`source = mis`), events as Library records, the current board as a `provides` contract with `stale_after`, its own health into OpenObserve.
- **Reuses.** QMN's labelers (moved out of the node into the catalogue, not rewritten), the four homes, the mini-app core, the Lab's training placement for models.
- **Hard cases.** MIS down (units unaffected; the board goes stale and placement falls back); a new reading (shadow first, his yes); a market without depth (the data level refuses or falls back); 24/7 crypto (sessions from measured activity); his own model (a model reading in shadow).
- **Explain.** "The MIS looks at every market and writes down what it sees, with the time it saw it. Units can do the same sums themselves, so they never wait for it."

### Shape B. Keep the MIS inside the node and open its consumer list to units

- **Why not.** QMB on the PC could not run the same code, so backtest trades would still carry no readings; the PC's slow tier and his models have no home; templates would wait on the node.

### Shape C. No MIS process at all: readings as code only, computed on demand

- **Why not.** It loses the history agents read (his ruling that templates read the MIS's logs), the cross-market readings only a shared service can make (currency strength, dispersion), and the board. It stays the floor every unit stands on, which is Shape A's point.

**Pick: Shape A.** The MIS as a mini app from the first build (party P17 clash; lead's call), because templates need its logs and the node's setup installs it. How to undo: ship only the reading blocks and add the app later.

## 4. Defaults for every class (his ruling 11)

Each reading has a tier (tick, bar, session, day), a minimum data level (1 bars, 2 quote ticks, 3 depth, 4 tape with aggressor side, 5 derivatives fields, 0 calendar), and the classes where it is valid. Levels follow research 45's ladder splits.

| Reading | Tier | Data level | Classes | Source |
| --- | --- | --- | --- | --- |
| Range volatility against usual (bar ranges, seasonal baseline by minute of session) | bar | 1 | all | research 22 §3 (about three times faster than closes) |
| Volatility state (quiet, normal, elevated, stressed) | bar and session | 1 | all | the shipped classifier's words, renamed (§7) |
| Spread against usual; SQS | tick and bar | 2 | FX, CFDs, metals, crypto with quotes | QMN `spread_state`, `sqs` |
| Tick rate against usual | tick and bar | 2 | FX, CFDs, metals, crypto | research 43 §3.3 fast tier |
| Quote gaps, feed state, degraded sensors | tick | 2 | all with quotes | QMN producers |
| Liquidity stress | bar | 2 | all with quotes | QMN `liquidity_stress_v1` |
| Small change detectors (CUSUM on returns, two-scale volatility, Kalman level) | bar | 1 | all | research 22 §6 |
| Efficiency ratio (trend against noise) | session | 1 | all | research 45 §5 |
| Variance ratio, Hurst (with minimum sample) | day | 1 | all | research 43 §3.2 (Hurst at least about 1,000 points) |
| Trend against range state (his meaning of regime) | session and day | 1 | all | §7 |
| Calendar states (session open and close windows, holidays, dead zones; news states parked since news is out) | calendar | 0 | all | QMN calendars; research 43 §4 L20-03 |
| Top-of-book depth against usual; depth imbalance | tick | 3 | cTrader instruments (broker depth), crypto books | research 43 §3.3 |
| Order-flow pressure (delta, imbalance) with fallbacks to depth imbalance, tick rule, range pressure | tick, 30-second horizon | 4, falling back to 3, 2, 1 | crypto (free tape), futures (when a route exists), CFDs as broker-side estimates | research 22 §5; research 37 E06 |
| Funding state and its extreme tail; open interest change; mark against last; basis | bar and session | 5 | perps (Hyperliquid, Binance, Bybit) | research 37 E34; research 45 §3 |
| Roll state, days to expiry, price-limit state, session in the exchange's zone | calendar and session | 0 and 5 | futures | research 54 §3.3 |
| Cash open, opening drive, initial balance, overnight range | session | 1 | indices | research 45 §3 |
| London fix windows (10:30 and 15:00 London) | calendar | 0 | gold | research 45 §3 |
| Currency strength, dispersion, herding counts, dated pair readings | session and day | 1 | FX first, then any class | research 43 §3.3 (cross-sectional, PC instance) |
| Activity sessions measured for 24/7 markets, plus the funding clock | session | 1 and 5 | crypto | research 43 §4 L03-24 (research 37 E33) |

The fast tier runs where the feed lands (the node's instance for its markets); the session and day tiers and the cross-sectional readings run on the PC's instance (M-08; research 43 §4 L03-17).

## 5. The reading card

Every reading carries: id, version, tier, clock, minimum data level and fallback chain with expected loss, lag and horizon, minimum sample, the classes where it is valid (transfer status), its three outputs, its health word (fresh, stale, degraded, shadow, retired), and for direction labels the published state-length-to-window ratio (research 22 §4). A reading goes live only with his yes; new versions run in shadow beside the live one.

## 6. Where it publishes, and the link back to his PC

| Home (all BUILT) | Holds | How templates and agents read it |
| --- | --- | --- |
| Market-data store partitions, `source = mis`, a derived kind per reading and version | the stamped history | `data_features` through the market door; script steps; QMB's `materialise` |
| Library records on a stream | events: a state changed, a sensor degraded | event triggers (PR 160); `library_*` tools |
| The `mis` app's `provides.board` with `stale_after` per tier | the current board | `app_op`; the landed artifact plus an event trigger |
| OpenTelemetry into OpenObserve | the MIS process's own health | the `ops` toolset |

**The real gap is the link from a node back to the PC** (G4b Q6). The node's instance writes its partitions locally; the same one-way shipping job the journals use sends them to the PC's Library when it is reachable (`journals.md` §5). Built once for both.

## 7. The word "regime" (lead's call)

The shipped classifier's "regime" means volatility (quiet, normal, elevated, stressed); he uses "regime" for trending against ranging. Until one meaning is picked, an agent comparing itself with the MIS compares two different things (research 29 F7). Lead's call: "regime" takes his meaning (trend against range); the volatility buckets are renamed "volatility state" in code and on screens. Why: these are the words he reads every day. How to undo: keep "regime" for volatility and name the trend reading "trend state".

## 8. How a unit uses the MIS, in code (owed, ledger C-04)

1. **Rule inputs and vetoes** bind reading blocks inside the unit's own compiled graph; the unit computes them from its own feed, with the same code the MIS runs. Nothing changes when the MIS is down.
2. **Placement** (which of his ticked markets is in the unit's condition now) may read the board through an optional read surface with `stale_after`. With the board stale or missing, placement falls back to every ticked market and the unit's own conditions decide (research 43 decision 2, recommended).
3. **The context receipt** on each trade references the readings the unit saw (ids, versions, ages), or keeps the value it computed itself, so the trade replays without the MIS (research 43 F1).
4. **One input, two roles.** A unit binding the same indicator the MIS publishes is one input in two roles: marked once in lift studies, try counts and herding counts (research 23 §4).

## 9. Room for his models

A `model` reading kind: a learned block with its weights as an artifact (loaded through an injected read surface, since QML's scan forbids file reads), trained through the Lab's PC training placement (BUILT), landing with data fingerprints, code version and seed. It runs in shadow beside the live reading; it goes live only with his yes. Fitted models are pooled by class or underlying and refit in shadow (research 23 §5). Labels he and the copilot write ("mostly mean reverting this week") are stored dated with what was visible, and may train a shadow version only.

## 10. Numbers (starting defaults, all editable; from research 43 §5)

| Number | Default |
| --- | --- |
| Seasonal baseline | same minute of the session, in venue session time, last 20 weeks, refreshed nightly and at each session close |
| False-alarm spacing per reading per market | one alarm episode per 10 trading days |
| Volatility reading window | 10 bars of ranges; 30 bars of closes as fallback |
| State length against reading window before a direction label may gate trades | at least 5 |
| Bounce ratio | flag above 0.1; block price-only mean-reversion readings above 0.25 |
| Order-flow reading horizon | 30 seconds |
| Regime-model refit in shadow | monthly |
| Funding extreme tail | bottom and top 10% of the trailing 180 days |
| Freshness per tier (`stale_after`) | tick 2 s; bar one bar; session one session; day one day |
| Lag-to-hold admission | lag at most a third of the unit's median hold |
| Sensor retire card | unread for 8 weeks (placeholder) |

## 11. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Catalogue | unit, QMB, MIS | reading blocks by id and version |
| MIS app (node instance) | market-data store on the node | stamped history, fast tier |
| MIS app (PC instance) | market-data store, Library, `provides.board` | slow tier, cross-market readings, events, the board |
| Node | PC Library | the node's MIS partitions, one way (shared with journals) |
| Unit (in the node) | board | optional placement read with `stale_after` |
| Workflow templates | MIS logs | partitions through `data_features`; events through triggers |
| Lab | MIS | trained model readings, in shadow |

## 12. Open for the architecture step

1. The as-of query's single function for QMB and live, with the golden replay as its test (research 43 §7 low level 12).
2. Whether the PC instance and the node instance share one app version pin.

## 13. Parked

- News readings (news is out for now, CC-21).
- Fundamentals as slow context entries with release time and vintage (when a source uses them).
- Vision-model chart readings; market twins.
