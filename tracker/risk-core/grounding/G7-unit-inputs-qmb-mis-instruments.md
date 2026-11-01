# G7: what a unit receives from QMB and the MIS, plus instruments and costs

Grounding for the risk core session, 2026-11-01, round 2. Facts only, no design. It extends `G2-unit-plan-risk-state.md` (rulings, the socket table, the placeholders) and does not repeat it. G3 holds the old system's session, RVOL, physics and microstructure multipliers. G4 holds the Book door's sizing ladder.

**Labels.** BUILT means merged on `origin/engine/base` at c93407ca; much of it has never run on a venue. BUILT (branch) means coded on a `build/us-*` branch, reviewed CLEAN and stacked, not merged (`US/RESUME.md:18-41`). PLANNED means written in a plan file and not coded. DOCS means the older docs corpus only, written for the Book world; the unit plan overrides it where they differ. [judgment] marks my own reading.

**Paths.** `UP/` is `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\` (branch `plan/unit-system` at 09d36ab7). Inside it, `A/`, `B/` and `C/` are `architecture/parts/A-qml-dictionary-unit/`, `architecture/parts/B-qmb-journals-workflows/` and `architecture/parts/C-node-mis-external/`, and `L0` is `architecture/level-0/ARCHITECTURE-SPINE.md`. `EB/` is `D:\QMX-worktrees\engine-base-read\`. `QMX/` is `C:\Users\Mubarak\Desktop\QMX\`. `US/` is `D:\QMX-worktrees\unit-ship\`. `QV2/` is `D:\QMX-worktrees\agent-system\tracker\qma-v2\`. `RC/` is `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `STATS/` is `C:\Users\Mubarak\Desktop\Stats\dictionary\`, the old 239-entry dictionary outside the repo. `build/us-a5:path` is a file at that branch tip, read with `git show` at about 21:30.

---

## 0. Short answers

1. QMB hands a unit to paper with a verdict, a baseline card and a proposal card. All three are PLANNED (slice B13, phase 2, not started). None of their numbers reaches the sizer at trade time. A paper lane starts from the unit's own defaults, and the sizer's "own record" holds only trades closed after that start (`UP/A/CONTRACTS.md:120`, `:167`). [judgment]
2. Of his list, trade count, win rate, expectancy and drawdown exist in money today (BUILT). Their R versions are PLANNED. No field holds average win and average loss in R. PBO is deferred in code and appears only in the `old-qmx` preset.
3. The MIS publishes stamped readings: a value, a percentile against the market's own usual for that minute of its session, a word, a health word and a freshness limit. It also publishes a board of states per tier. All PLANNED. The MIS app itself (C-08, C-09) is not started. Today's MIS commits are the plan page and three CLEAN prerequisites (C-05a, C-05b, C-05c).
4. A unit widens to new markets only by a new version and his click. The MIS never turns a unit on or off. A board read on the node (C-22) can only narrow within admitted markets [judgment].
5. Market physics ships as the persistence family (efficiency ratio, variance ratio, Hurst), PLANNED. Ising and Lyapunov are not planned anywhere. RVOL is not an MIS reading. It is a dictionary concept for real-volume markets only. Tick-tier microstructure readings are PLANNED in the node, and SQS is BUILT. Sessions exist as a unit field (BUILT (branch)) and as planned calendars. No code knows Tokyo, London or New York hours [judgment, from searches].
6. The planned instrument record carries tick, pip, contract size, value per point, lot step, minimum and maximum lot, swap, margin and measured costs by hour. It has no commission key. The sizer's key list leaves out swap, measured costs and the currency conversion.
7. Built code turns a stop distance into lots in two places. The Book door divides and refuses inexact sizes (BUILT). The unit path's placeholder sizer divides and rounds down to the lot step (BUILT (branch)).
8. A unit holds one position per instrument by default and can hold positions on several markets at once. No basket or pair order shape exists. Records split per market, never per session or timeframe [judgment].

---

## 1. What leaves QMB for paper

### 1.1 The records QMB writes (PLANNED unless marked)

`B CONTRACTS` below is `UP/B/CONTRACTS.md`.

| Record | Fields that touch sizing | Where | State |
| --- | --- | --- | --- |
| `backtest-result` v2, one per run | `measures`: money, the 27 shipped measures; R, `trades`, `expectancy_r`, `win_rate`, `payoff_r`, `max_drawdown_r`, `mae_median_r`, `mfe_median_r`, `exit_capture`, `entry_edge_ratio`. `labels`: `zero_trades`, `costs_uncalibrated`, `fidelity`, `placeholders[]`, `data_seams[]`, `gaps[]`, `motion`. Blobs `trades`, `equity`, `daily_r`, `slices`, `receipts`, `journal/*` | Library kind, written only by the lander (`B CONTRACTS:46-62`) | Field list PLANNED. The kind shell is BUILT (branch) on `build/us-b3:qmx-agents/packages/qmx-library/src/qmx_library/kinds/backtest-result.schema.json`, where `measures` and `labels` are open objects beside the seven blob slots |
| `verdict` | `per_market[]` with `market`, `trades`, `raw_r`, `shrunk_r`, `steps[]`; `overall` (`pass`, `fail`, `too_thin`, `no_trades`); `effective_tries`; `preset`; versions | Library, package `qmx-judge` | PLANNED (`B CONTRACTS:72`), slice B13 |
| `baseline-card` | `record_r` (a summary), `cone` (percentiles by trade count), `cost_assumptions`, `fill_assumptions`, `trade_rate`, `readings_range` (per reading, the min, max and percentiles seen when earned) | Library | PLANNED (`B CONTRACTS:73`); frozen when a unit passes (`UP/B/judge.md:86`) |
| `proposal-card` | `ask` (`paper`, `live`, `admit_market`, `drop_market`, `tighten`, `bench`), `evidence[]`, `verdict`, `tries`, `preset`, `placeholders[]` | Library | PLANNED (`B CONTRACTS:74`) |
| `paper-run` v2, one per unit per market | `record_r`, `sequential_score`, `status`, `journal[]` | Library, the judge's paper scoring script | PLANNED (`B CONTRACTS:122`) |
| `trade` v2, one per round trip | `mae_r`, `mfe_r`, `costs` (`spread`, `commission`, `swap`, `funding`, `slippage`), `equity_before`, `session`, `streak`, `r_missing`, `gap_through_stop` | Library, the records host job | PLANNED (`B CONTRACTS:123`) |
| `study-spec`, written before any run | `claim` (`edge`, `horizon`, `sessions[]`, `conditions[]`), `markets`, `record_needed`, `preset`, `shrinkage`, `cost_rule`, `fill_model` | Library | PLANNED (`B CONTRACTS:71`) |

### 1.2 His list against those fields

| He asked for | Field | State |
| --- | --- | --- |
| Trade count | `measures.trades`; `verdict.per_market[].trades`; money `total_trades`, `winning_trades`, `losing_trades` | R list PLANNED. Money BUILT (`EB/qmb/src/qmb/results/measures.py:313-317`) |
| Win rate | `measures.win_rate`; money `win_rate`, `long_win_rate`, `short_win_rate` | PLANNED. Money BUILT (`measures.py:319-327`) |
| Average win and loss in R | No R field. `payoff_r` is named and never defined [judgment: probably average win over average loss]. Money `average_win`, `average_loss`, `largest_win`, `largest_loss` | Money only, BUILT (`measures.py:333-339`) |
| Expectancy | `expectancy_r`; money `expectancy`; expectancy at 1.5x costs as a gate | R PLANNED. Money BUILT (`measures.py:331`). The gate script is BUILT and not wired (§1.4) |
| Drawdown | `max_drawdown_r`; money `max_drawdown`, `max_drawdown_recovery`; `winning_streak`, `losing_streak` | R PLANNED. Money BUILT (`measures.py:303-311`, `:347-349`) |
| Walk-forward | The procedure is a sequence of split-manifest runs with a read-time aggregation. It ships no default windows and no pass threshold (`EB/qmb/src/qmb/robustness/walkforward.py:1-40`). The gate is efficiency (validation Sharpe over in-sample Sharpe) of at least 0.5 | Procedure BUILT. Gate BUILT in a template script. Judge step 4 PLANNED (`UP/B/judge.md:55`) |
| Monte Carlo | A trade shuffle of realised money P&L (`EB/qmb/src/qmb/robustness/shuffle.py:1-22`) and a candle perturbation (`perturbation.py`). The gate is the 5th percentile of total R above 0. The baseline card's `cone` | Procedures and gate BUILT. Cone PLANNED |
| PBO | Code names PBO and CSCV only as a deferred battery (`walkforward.py:205`; `EB/qmb/src/qmb/robustness/summary.py:71`). The `old-qmx` preset passes below 0.25 and calls a unit dead above 0.50 (`UP/B/judge.md:66`). The docs call it a candidate only (`QMX/docs/gap-report.md:177`) | Not built. PLANNED as a preset value |
| Cost assumptions | `execution.cost_profile`, `slippage`, `carry`, `margin` on the run request (`B CONTRACTS:37`); `labels.costs_uncalibrated`; the study's `cost_rule`; the baseline card's `cost_assumptions` and `fill_assumptions`; cost stress 1.5x in `shipped`, 2x in `old-qmx` | PLANNED. The cost ports are BUILT with no rates (§4.3) |
| By market | `verdict.per_market[]`. Each market's R is shrunk toward the unit's whole result by n/(n+k). Markets whose trade results correlate above 0.6 count as one record (`judge.md:59`, `:100`) | PLANNED |
| By session | Per run, "slices by session and by readings state" (`UP/B/qmb.md:108`). Every trade row carries `session`. A what-if that filters by session is a counted try with its own run (`judge.md:79`). In the docs, `analysis.project` saved views filter by hours, days and session windows and never count as admission evidence (`QMX/docs/components/qmb.md:221`); it exists as `EB/qmb/src/qmb/analysis/project.py` | Slices PLANNED. Projections BUILT |
| By timeframe | No field. A bar change is a new version (`UP/A/CONTRACTS.md:218`), so each timeframe is its own version or unit [judgment]. One unit on one pair at 1m and 5m counts as one idea (G2-17) | none |
| Confidence | Deflated Sharpe of at least 0.95 over the family's effective tries (template gate; judge step 5). The sequential score passes at 20, with bets of 0.025 to 0.2 on trade R after costs (`judge.md:105`). `too_thin` after 6 months without the record (`:103`). `shrunk_r`; `effective_tries` | Gate BUILT in a script. The rest PLANNED |

### 1.3 What travels to paper, and what the sizer then sees (PLANNED)

- His click calls `POST /api/units/promote` with `unit {id, version}`, `market_id`, `to = paper`, `node`, `account` and `placeholders_acknowledged`. It refuses with `no_g_record` or `placeholders_unacknowledged` among other codes (`UP/C/CONTRACTS.md:157-170`).
- The deployment carries the unit version, its compiled fingerprint, the block folder, and snapshots of the instrument, venue and account records. "The node never reads the Library to trade" (`UP/C/RECORDS.md:80-82`).
- A QMB run and a paper lane start from the unit's defaults. A live deployment starts from the paper lane's last calibrated values and watermark (`UP/A/CONTRACTS.md:120`).
- The sizer's "own record in R" is the `own_journal` surface. It holds only trades "this hosted unit closed in its own run or deployment after its starting watermark" (`UP/A/CONTRACTS.md:167`).
- So the verdict, the baseline card and the QMB measures stay on This PC. They feed the proposal card, the judge's paper rule (the later of 30 trades or 4 weeks, `judge.md:104`) and the nightly decay check. No socket input carries them [judgment]. A Kelly-style sizer that wants QMB's edge estimate has no input for it in the plan [judgment].
- Each unit gets its own paper lane per market on a demo account, as a `paper-run` item. Level 0 lifts DEC-0261's "no per-bot paper" for units (`UP/L0:383`).

### 1.4 What the shipped code hands over today (BUILT)

- Template `b-build-and-prove` lives at `EB/qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/`. Its gate script sets the verdict from 100 trades, walk-forward efficiency 0.5, a Monte Carlo 5th percentile of total R above 0, expectancy at 1.5x costs above 0 and a deflated Sharpe of 0.95. A daily Sharpe above 2 holds the verdict for a lookahead audit (`scripts/gates.py:4-7`, `:14-16`, `:23-62`).
- A survivor gets a "start paper trial?" card whose risk profile is "fixed, the smallest step" and "tighten-only" (`scripts/card.py:15`).
- The QMB call is not wired. `scripts/qmb.py` "refuses to guess" and exits 1 until QMB's doors for agents exist (`scripts/qmb.py:10`, `:16`). Its docstring promises a "regime and session breakdown" that no shipped result shape holds (`:3-4`).
- The node's promotion code is a precondition battery. It shows passed or refused checks and is never a trade grant (`EB/qmn/src/qmn/promotion/battery.py:1-6`).

### 1.5 What the docs say (DOCS, Book world)

- QMB "may never bench, promote, or bind". It publishes raw measures and never stores a pass or fail (`QMX/docs/components/qmb.md:25`, `:79`).
- Until GAP-0048 rules fidelity and calibration, every fill carries an `optimistic` taint, and such runs cannot claim edge (`qmb.md:87`).
- The Book's `admission_bar` is a set of requirements. Each has a measure, a unit, a comparison, a threshold that is ruled or "not yet ruled", and evidence requirements. No paper role may gate live money (`QMX/docs/contracts/ct-22-book-charter.yaml:20`, `:25`, `:61-63`). The grammar is BUILT with blank thresholds (`EB/packages/qmf-risk/src/qmf/risk/admission_bar.py:1-20`).
- Node-paper is Book-level demo routing with no per-bot paper lane (`qmb.md:209`, `:229`). The unit plan reverses this for units (§1.3).

---

## 2. MIS output, and how a unit uses it

### 2.1 What it publishes (PLANNED)

One stamped reading record per reading, market and instant, kind `reading` under Part B's journal envelope (`UP/C/CONTRACTS.md:107-128`). Its fields:

- identity: `reading {id, version, fingerprint}`, `source` (`node` or `mis`), `machine`, `market_id`, `instrument`
- clock: `tier` (`tick`, `bar`, `session`, `day`, `calendar`) and `time_base` (`clock`, `ticks`, `volume`)
- outputs: `value`, `percentile` against the market's own usual for that minute of its session, and `word` from the reading card
- quality: `health` (`fresh`, `stale`, `degraded`, `thin`, `shadow`, `retired`), `data_level`, `fallback_step`, and `estimate` (`broker-side` for cTrader order-flow estimates)
- times: `inputs_received_at`, `computed_at`, `stale_after_s`; `corrects` links a correction to the record it replaces

"Regime" now means trend against range. The shipped volatility buckets become "volatility state", with the words quiet, normal, elevated and stressed (`UP/C/MIS.md:83-85`; `EB/qmn/src/qmn/mis/regime_design.py:72-78`). The files I read fix no word list for trend against range [judgment].

The `mis` app also provides a `board` per tier, `{tier, at, markets: [{market_id, states: {reading id: word}}]}`, with `stale_after`. It answers `configure` (markets with instrument snapshots, pack ids, shadow readings) and `status` (`UP/C/CONTRACTS.md:132`).

### 2.2 The default packs (PLANNED)

Every class gets range volatility against usual, volatility state, spread against usual and SQS, tick rate against usual, quote gaps and feed state, liquidity stress, change detectors (CUSUM on returns, two-scale volatility, a Kalman level), efficiency ratio, variance ratio and Hurst, trend against range, and calendar states. This PC adds currency strength, dispersion, herding counts and dated pair readings (`UP/C/MIS.md:52-71`).

| Class | Adds |
| --- | --- |
| `fx`, `metal`, `index_cfd` | cTrader broker depth and depth imbalance; order-flow pressure as a broker-side estimate. Gold adds the London fix windows (10:30, 15:00 London). Index CFDs add cash open, opening drive, initial balance and overnight range |
| `future` | roll state, days to expiry, price-limit state, sessions in the exchange zone, open interest at end of day; depth and real order flow once a route exists |
| `perp`, `spot_crypto` | real depth and trade flow; perps add funding state and its tails, open interest change, mark against last and basis; activity sessions replace clock sessions |
| `commodity_cfd`, `stock_cfd`, `stock` | the shared rows; `stock_cfd` and `stock` add the cash-open rows |

Packs are named `<class>-<n>` and pinned by version. A market gets only the readings its data levels allow (`UP/C/MIS.md:50`).

### 2.3 Where it runs and how often (PLANNED)

| Tier | Runs in | Fresh for | How often |
| --- | --- | --- | --- |
| tick | the node on the trading machine, fed by the feed keeper's fan-out with drop-oldest | 2 s | as quotes and trades arrive (`UP/C/MIS.md:36`, `:77`, `:116`) |
| bar | the `mis` app beside the node | one bar | over the open month, which the records job harvests every 60 s (`[records] open_harvest_s`, `UP/C/MIS.md:37`) |
| session, day | the `mis` app for the node's markets; This PC for every other market | one session, one day | per session and per day (`UP/C/MIS.md:38`) |
| cross-market and the board | This PC | per tier | per tier (`UP/C/MIS.md:39`) |

The pre-session shortlist runs 30 minutes before each session open, from each market's calendar (`UP/B/workflows.md:73`). The baseline is the same minute of the session over 20 weeks, refreshed nightly. False alarms are spaced at one per 10 trading days. Shadow models refit monthly (`UP/C/MIS.md:100-108`).

### 2.4 How a unit consumes it

- The unit's `reads` list holds `{reading: entry_id@version, market: market_id or "*", fallback: compute_here, treat_as_absent or no_new_entries, stale_after_s}` (`UP/A/CONTRACTS.md:28`). It is BUILT (branch) as `Read` in `build/us-a2:qml/src/qml/unit/model.py:391-396`.
- `context_needs` lists words the unit requires, warns on or blocks on (`UP/A/CONTRACTS.md:30`). PLANNED.
- The host injects each reading as the surface `reading:<entry_id>@<version>:<market_id>` (`UP/A/CONTRACTS.md:169`). Every decision row records `readings_used` with value, source, version and `knowable_at` (`:129`). PLANNED.
- A record older than its `stale_after` counts as absent, and the unit takes its fallback (`UP/C/MIS.md:77`).
- The cross-unit hook may read the board's dispersion reading (`UP/A/CONTRACTS.md:140`).
- A build test stops the MIS and asserts that the dummy still enters (`UP/C/MIS.md:115`).

### 2.5 Widening a unit's scope (PLANNED)

- A unit trades the markets on its own document. Each market has its own lifecycle state, and only his click moves one toward paper or live (`UP/A/CONTRACTS.md:229`).
- Adding a market is a `markets_change`. That is a new version, a counted try, and his click before live (`UP/A/CONTRACTS.md:218`). The proposal card's `admit_market` ask carries it (`B CONTRACTS:74`).
- The board reaches a node only "as a deployment change he clicks" (`UP/C/MIS.md:81`). The shortlist lands a note and a `shortlist` try per market on This PC. A missing shortlist changes nothing on the node (`UP/B/workflows.md:73`, case MIS-09).
- Slice C-22 (a Should, phase 5) relays the board to the node. A unit with a placement read uses it, and a stale board falls back to every admitted market (`UP/build/UNIT-PLAN.md:3726`).
- The MIS amplifies a unit and never switches one on or off (`UP/architecture/MIS-PAGE-CONTENT.md:32`).
- [judgment] His seed says the unit "widens its scope to those markets" (`RC/STATE.md:62`). In the plan, widening is a new version plus his click. The MIS can only narrow within admitted markets, through C-22.

### 2.6 Built, and being built today

- BUILT, never run on a venue: `EB/qmn/src/qmn/mis/`, 12,654 lines. Six rule-based labelers (identity, spread state, gap event, feed state, SQS, degraded sensors) (`labelers.py:1-6`); a liquidity-stress quantile fit (`liquidity.py:1-6`); an untrained regime classifier pipeline (corpus, design, train, eval, register, shadow). Its output goes to "the Book door and the KSA, never bots" (`signal_snapshot.py:1-4`).
- DOCS: "MIS V1 is a seam only", a per-instant snapshot with SQS, feed state and degraded sensors, which bots never consume (`QMX/docs/components/trading-node.md:404`).
- Since 28 Oct, every MIS commit on every ref is planning (`git log --all --since=2026-10-28`). `3a08283f` published the MIS page and `db6b60ea` wrote its content (1 Nov). `b24cca80` is Level 1 part C (31 Oct).
- Code landed today for the MIS's prerequisites, all CLEAN and stacked: C-05a (an app restarts itself with back-off, PR 242), C-05b (a read-only market root for apps that declare `data_reads = ["market"]`, PR 244), C-05c (host facts written into every app volume, PR 246) (`US/RESUME.md:34-36`).
- Four MIS slices are not started. They are C-08 (move `qmn.mis` into `packages/qmf-readings`, the reading runner, the records), C-09 (the `mis` app, its packs and the board), C-24 (`readings_query`) and C-22 (the node's board read). They sit in phases 4 and 5 (`UP/build/UNIT-PLAN.md:99-101`, `:123`, `:2400-2510`). No MIS branch exists on origin (`git ls-remote --heads origin`, 21:25).
- [judgment] "Built and shipped today" fits the published page and the prerequisites. It does not fit the MIS app itself.

---

## 3. Context measures

| Measure | BUILT | PLANNED | Research and docs | Old system |
| --- | --- | --- | --- | --- |
| Market physics (Ising, Lyapunov, Hurst and kin) | None. A word search for Hurst, Ising, Lyapunov, variance ratio and efficiency ratio over `EB/` and `build/us-a6` finds no code | The persistence family as readings: efficiency ratio (session tier), variance ratio and Hurst (day tier, at least 1,000 points, mid prices, a bounce check) in every pack (`UP/C/MIS.md:61-63`). A13b writes Hurst, variance ratio, efficiency ratio, half-life and change points as entries with code (`UP/build/UNIT-PLAN.md:1514`, `:1525`). No pack holds Ising or Lyapunov | "Ising-type measures have no trading evidence found"; physics readings get no separate home (`UP/research/23-mis-organisation.md:128`; `UP/research/37-mis-academic.md:133`). Party idea: old Chaos and Ising code as a quarry to retest (`UP/research/funnel5-mis/party-brainstorm/mis-field.md:139`) | A physics multiplier blocked at Ising of 1.0 or more (`RC/grounding/G3-old-system.md:81`). The sentinel built its regime from "Chaos + Ising Regime + News" (`UP/research/19-grounding-old-system.md:106`) |
| Relative volume (RVOL) | None | Not an MIS reading. The FX stand-in is "tick rate against usual (never called volume)" (`UP/C/MIS.md:57`). RVOL is a dictionary concept for the content wave, which covers every concept research 45 §3 lists (`UP/A/4-dictionary.md:71`). That row reads as a filter on level-1 volume for stocks, index futures and crypto spot, with a 20-day median by minute of day (`UP/research/45-dictionary-beyond-fx.md:183`) | ORB evidence is strongest on stocks "in play" by RVOL; for FX and gold the open is London or New York (`UP/research/02-instruments-and-traders.md:519`). The liquidity input is RVOL where real volume exists and tick rate otherwise (`:536`). The old RVOL gate is MISSING in code (`UP/research/18-grounding-today.md:244`) | An RVOL multiplier that blocked below 0.5 (`G3-old-system.md:80`) |
| Microstructure (spread, depth, tick rate, order flow) | SQS as baseline over live spread, plus spread state, gap event, feed state and degraded sensors (`EB/qmn/src/qmn/mis/labelers.py:1-6`). Liquidity stress from spread and depth quantiles (`EB/qmn/src/qmn/mis/catalog.py:171`). QMB's synthetic spread keyed by instrument, hour (UTC) and session (`EB/qmb/src/qmb/execution/spread.py:1-9`, `:140-142`) | Tick-tier readings in the node: spread against usual, SQS, tick rate against usual, quote gaps, depth against usual, depth imbalance, and order-flow pressure falling back to depth imbalance, tick rule and range pressure (`UP/C/MIS.md:36`, `:56-66`). A local guard checks spread against the unit's cost target before every order (`UP/L0:383`). Data routes per venue (`UP/C/EXTERNAL.md:57-66`) | Order flow predicts seconds and fades by 30 to 60 s. Spot FX has no tape; its tick count tracks volume at the hourly scale (`UP/architecture/MIS-PAGE-CONTENT.md:138`) | A microstructure multiplier from spread and depth (`G3-old-system.md:84`) |
| Sessions and time windows | One forex calendar with the 17:00 New York rollover. Its "session window" is the whole trading day between weekend gaps and holidays (`EB/extensions/qmf-calendar-forex/src/qmf/calendar_forex/_provider.py:5-6`, `:39`, `:155-180`). The MIS corpus tags rows `asia`, `london`, `new_york` as classifier inputs (`EB/qmn/src/qmn/mis/regime_design.py:81-86`; `regime_train.py:1634-1638`). The node's CT-31 windows stop entries during news blackouts and two dead-zone kinds, `daily_dead_zone` and `session_handover_buffer`, with widths as settings (`EB/qmn/src/qmn/protection/windows.py:1-10`). BUILT (branch): the unit's `sessions`, each `{name, calendar_ref, zone, windows [{from, to}]}` (`build/us-a2:qml/src/qml/unit/model.py:306-316`) | Calendars for CME sessions, index breaks and 24/7 markets with funding clocks (C-03, `UP/build/UNIT-PLAN.md:2234-2236`). Rules run in the market's zone (`UP/C/ARCHITECTURE-SPINE.md:254`). MIS calendar states (session windows, holidays, dead zones), cash open, opening drive, initial balance, overnight range and fix windows (`UP/C/MIS.md:64`, `:69-70`) | The old dictionary, which A12 ports, has `trading-session` (Tokyo, London, New York, Sydney, hours as published convention), `session-overlap` (London and New York about 13:00-16:00 UTC; London and Tokyo about 08:00-09:00 UTC), `session-open-price` and `time-of-day-window` (`STATS/context-regime-and-intermarket/context-filters-confirmations.md:440-498`), plus `session-range` and `opening-range` (`STATS/market-structure-and-location/locations-and-structure.md:296`, `:371`). Hour-of-day liquidity is "a placement window for every type", beside sniping windows (`UP/research/02-instruments-and-traders.md:521`, `:538`) | A session multiplier from 0.5 to 1.2 (`G3-old-system.md:78`) |

[judgment] No built or planned code holds named Tokyo, London or New York hours or their overlaps. A unit states its own windows in its market's zone. `session_handover_buffer` is the only built piece shaped like his "caution window at session opens" (`RC/STATE.md:101`).

---

## 4. Instruments

### 4.1 Classes covered

The one class enum is `fx`, `metal`, `index_cfd`, `commodity_cfd`, `stock_cfd`, `future`, `perp`, `spot_crypto`, `stock` (`UP/C/RECORDS.md:24`). It is BUILT (branch) in `build/us-a3:qml/src/qml/numbers/records.py:25-35`. His words were "Let's go with FX, futures, metals, of course CFDs" (`UP/C/RECORDS.md:5`).

| Class | Order route in this build | Records | Market data |
| --- | --- | --- | --- |
| `fx`, `metal`, `index_cfd` | cTrader at IC Markets. Orders are BUILT and never run (`UP/C/EXTERNAL.md:14`); demo probes are owed in C-15 | refreshed daily from cTrader symbols (`UP/C/RECORDS.md:69`) | bars, quotes, broker depth; order flow as estimates only |
| `commodity_cfd` | not named in the files I read [judgment] | records and a pack exist | |
| `stock_cfd` | none [judgment]. IC offers stock CFDs on MT5 only (`UP/research/32-terrain-and-venues.md:151`), and MT5 stays a declaration (`UP/build/UNIT-PLAN.md:4250`) | records and a pack exist | |
| `future` | none. Paid futures data and native clients (Rithmic, CQG) are out of this program (`UP/build/UNIT-PLAN.md:4250`) | `specified` from CME documents until a route exists; one record per contract month (`UP/C/RECORDS.md:61`) | a file adapter for Databento-format trades and MBP-10 as a placeholder (`UP/C/EXTERNAL.md:66`) |
| `perp` | Hyperliquid through CCXT, testnet first (C-16) | CCXT markets daily | real tape free (level 4) |
| `spot_crypto` | the CCXT read adapter is BUILT, spot only, and is PLANNED to open to contract markets (`UP/C/EXTERNAL.md:17`, `:84`); I found no spot order slice in the 73 PRs [judgment] | | real tape |
| `stock` | none found [judgment] | enum and pack only | |

### 4.2 How specs are held

| Fact | Planned record key (`UP/C/RECORDS.md:26-50`) | In the sizer's key list (`UP/A/CONTRACTS.md:72`) | BUILT (branch) in QML (`build/us-a3:qml/src/qml/numbers/records.py:46-70`) |
| --- | --- | --- | --- |
| Tick, point, pip | `digits`, `tick_size`, `pip {size, source}`; a pips conversion without a pip is a checker error | yes | yes |
| Value per point | `value_per_point` (money per price unit per lot), with `value_conversion {symbol, method}` and a `conversion_check` at 0.1% tolerance | `value_per_point` only | `value_per_point` only |
| Contract size | `contract_size` (for a future, its multiplier) | yes | yes |
| Lots | `lot_step`, `min_lot`, optional `max_lot` | yes | yes |
| Commission | no key | no | no |
| Swap and carry | `swap {long, short, triple_day}`, `financing`, dated `events` such as dividends | no | no |
| Margin | versioned `leverage` tiers, `margin {intraday, overnight}`, `liquidation_rule` | `leverage`, `margin` | kept as given |
| Measured costs | `measured`: spread, slippage, fill latency and rejections by hour, from the market journal | no | no |
| Calendar | `calendar_ref`, `zone`, `day_boundary` | yes | yes |
| Futures, perps | `expiry`, `last_trade`, `settlement`, `root`, `rolls_to`; `funding_interval`, `funding_source` | yes, except settlement and funding source | yes, optional |

- The records themselves (C-02, phase 1) are not started. Fixture records ship for EURUSD, USDJPY and XAUUSD with `status = specified` (`build/us-a3:qml/tests/fixtures/records/`). EURUSD has tick 0.00001, pip 0.0001, contract 100,000, lot step and minimum 0.01, leverage 30. XAUUSD has tick 0.01, contract 100, value per point 100, leverage 20. These are fixtures, not broker facts.
- Records refresh from venue facts daily and on each change event, from broker documents weekly, from exchange documents monthly, and from measured costs daily (`UP/C/RECORDS.md:67-72`). A node that sees a changed lot step, margin, digits or leverage stands that symbol's units down until his click (`:76`).
- The BUILT code stores no per-broker record, and `symbol_info` returns the raw venue document (`UP/C/RECORDS.md:13`). A connect-time verifier checks timestamp unit, daily boundary, bar basis, pip formula, money exponent and netting or hedging. It has never run (`EB/qmn/src/qmn/venue/verify.py:1-15`).
- DOCS: the value factor comes only from venue instrument metadata, and an absent one refuses (`QMX/docs/contracts/ct-18-venue-capabilities.yaml:25`).

### 4.3 Costs per instrument and time of day

| Layer | What exists | State |
| --- | --- | --- |
| Record | `measured` by hour from the market journal, refreshed daily (`UP/C/RECORDS.md:48`, `:72`). Costs are calibrated per world; a demo pass never stands in for live calibration (`UP/C/EXTERNAL.md:74`) | PLANNED |
| QMB | Cost profiles from the market journal; results say "costs uncalibrated" until real fills exist (B10, `UP/build/UNIT-PLAN.md:1788`, `:1794`, `:1804`). Trade rows split spread, commission, swap, funding and slippage (`B CONTRACTS:123`) | PLANNED |
| QMB ports | A synthetic spread from a per-broker calibration keyed by instrument, hour (UTC) and session; real quotes take precedence; a missing calibration refuses, never zero (`EB/qmb/src/qmb/execution/spread.py:1-9`). Commission adapters (zero, percent of notional, per lot, notional with a minimum) (`cost.py:1-8`, `:339-447`). Swap as a rollover cash event (`financing.py:1-11`). Slippage adapters (zero, constant percent, spread crossing, gap volatility, size tiered) (`slippage.py:351-493`) | BUILT, every rate deferred to GAP-0048 |
| MIS and node | Spread against usual at the same minute of the session over 20 weeks (`UP/C/MIS.md:100`). The node's guard checks spread against the unit's cost target (`UP/L0:383`) | PLANNED |
| Docs | Calibration, never invention: spread from QMX's own recorded bid and ask per venue, hour and session; slippage from fill journals; financing from the broker's schedule (`QMX/docs/components/qmb.md:87`) | DOCS |
| Research | FX spread moves by hour, spikes at the 17:00 New York rollover, and the quote currency can differ from the account's (`UP/research/32-terrain-and-venues.md:146`). Cost as round trip over the unit's average target, for example about 0.8 pips on IC EURUSD and about 0.09% taker on Hyperliquid (`UP/research/02-instruments-and-traders.md:534`) | research |

[judgment] He ruled that costs per market, instrument, timeframe and time must be known to the unit and feed Kelly (`RC/STATE.md:75`). No planned socket input carries a cost to the sizer, and commission has no record key.

### 4.4 Code that turns a stop distance into lots

- BUILT, Book door (old law). `_quantity_from_risk_amount` divides the frozen risk amount by distance times value factor. It refuses a size that is not exact at the scale instead of rounding (`EB/qmn/src/qmn/order/door.py:278-310`). G4 covers it.
- BUILT (branch), unit path. `distance` turns ticks or pips into a price distance on the record's tick grid and refuses pips without a pip definition (`build/us-a3:qml/src/qml/numbers/convert.py:28-62`). `lots` rounds down to the lot step and refuses below the minimum or above the maximum lot (`:88-108`). `value_factor` gives money per price unit per lot in the record's currency (`:111-114`).
- BUILT (branch), placeholder sizer `fixed-fraction-at-stop@1`. Lots are equity × fraction ÷ (|entry − stop| × value_per_point), rounded down through `lots`; below the minimum it skips with the reason (`build/us-a4:qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/1/block.py:1-5`, `:37-59`). It reads equity, entry, stop and the record. It reads no costs and does no currency conversion.
- PLANNED: a test that the sent quantity equals the sizer receipt's after rounding (CA-03, slices B5b, B6, C-12a).

---

## 5. Unit shape, as it touches sizing

### 5.1 Positions at once

- The rule is that exits run before entries on one instant, and "a unit holds one position per instrument unless it declares more" (`UP/L0:263`). The field is `position_limit.per_instrument`, an integer with default 1 (`UP/A/CONTRACTS.md:23`), from the unintended-pyramiding case UT-15 (`UP/architecture/funnel/edge-cases/catalogue.md:122`).
- BUILT (branch): `PositionLimit.per_instrument` defaults to 1, minimum 1 (`build/us-a2:qml/src/qml/unit/model.py:320-321`). The hosted unit's surface `own_position:<market_id>` holds one position or none per market (`build/us-a5:qml/src/qml/protocol/unit.py:11`, `:452-454`). On `build/us-a6`, `per_instrument` appears only in the model and the identity diff, not in the runtime (`git grep`).
- A unit holds positions on several markets at once. The hosted unit steps every market on its document each instant (`build/us-a5:qml/src/qml/protocol/unit.py:15-19`, `:452`). The dummy trades EURUSD and XAUUSD on one 15-minute stream (`build/us-a5:qml/src/qml/unit/templates/dummy-trend-pullback.json`).
- On a netting account or a Hyperliquid subaccount, at most one unit per symbol, refused at deploy (a placeholder). A hedging account keeps one virtual position per unit (`UP/L0:733`; `UP/A/RISK-SIZING-POINTS.md:29`).
- One sizer serves all of a unit's markets (`UP/A/CONTRACTS.md:26`). Its budget is the bound account's equity (`UP/C/RISK-SIZING-POINTS.md:12`).

### 5.2 Trading several instruments together

- A unit lists many markets. A stream is bound to every market (`"*"`) or to one market id (`UP/A/CONTRACTS.md:20`). [judgment] A stream on one market id lets a unit read another market's bars, but each intent names one instrument (`UP/A/CONTRACTS.md:151`). I found no basket, pair or multi-leg order shape in Part A, Level 0, or the funnel's unit and QML files.
- Units reading other units live is parked (`UP/architecture/funnel/solutions/unit.md:232`). Intraday pairs and stat-arb are "later" (`UP/research/02-instruments-and-traders.md:530`).

### 5.3 Scope, and records per context

| Context | What the plan keeps | Source |
| --- | --- | --- |
| Market (instrument) | A lifecycle state per unit per market. One admitted version per unit per market. A position belongs to the version that opened it until flat | `UP/A/CONTRACTS.md:229`; `UP/A/2-unit-template-numbers-lifecycle.md:42` |
| Market settings | `markets[].settings` and an optional `settings_record`, an earning-record ref | `UP/A/CONTRACTS.md:19` |
| Calibrated numbers | Per market, with a thin market shrunk toward the unit's pooled value across its markets. At least 60 trades, shrink k of 100, every 20 closed trades or at the day close | `UP/A/2-unit-template-numbers-lifecycle.md:35`; `UP/A/CONTRACTS.md:245-247` |
| Judging | One rule for every market; each market shrunk toward the unit's whole result; correlated markets count as one record | `UP/B/judge.md:59` |
| Underlying | `market_id` names the underlying, so gold at two brokers and the GC future share `gold`. A test asserts equal R on 100 oz and 1 oz gold records | `UP/C/RECORDS.md:57`, `:88` |
| Session | The unit's `sessions` windows; `session` on every trade row; QMB slices by session. No record or calibration is kept per session [judgment] | `UP/A/CONTRACTS.md:21`; `B CONTRACTS:123`; `UP/B/qmb.md:108` |
| Timeframe | The bar size belongs to the version. No record per timeframe [judgment] | `UP/A/CONTRACTS.md:218` |
| Class | MIS models pool by class or underlying, never one per market | `UP/architecture/MIS-PAGE-CONTENT.md:96` |

### 5.4 Socket inputs beyond G2's table

G2 §2 lists each slot's inputs. These facts add to it.

- The host injects four read surfaces (`UP/A/CONTRACTS.md:164-169`). `own_position:<market_id>` carries quantity, average price, stop, targets, opened by, opened at, bars held, and MFE and MAE in R. `own_journal` carries closed trades with `trade_id`, `opened_at`, `closed_at`, `side`, `market_id`, `world`, `r_after_costs` and `entry_stamps`. The other two are `weights:<entry>@<version>` and `reading:<entry>@<version>:<market_id>`.
- The instrument facts are §4.2's sizer key list. They leave out commission, swap, measured costs and the currency conversion [judgment].
- Account equity on cTrader is derived as balance plus unrealised P&L, because cTrader gives no equity field. On Hyperliquid it is the account value. Each carries its time and source (`UP/C/RISK-SIZING-POINTS.md:12`).
- "Market statistics from bound blocks" means the sizer sees market data only through blocks bound in the unit, and readings only through `reads` [judgment from `UP/A/CONTRACTS.md:28`, `:137`].
- The cross-unit hook reads open positions across units and an optional dispersion reading (`UP/A/CONTRACTS.md:140`).
- A risk-session block must pass `qml/tests/test_socket_contracts.py`, slice A15, phase 1, not started (`UP/A/RISK-SIZING-POINTS.md:22`).
- The inputs leave out the QMB verdict and baseline card, costs, and the session or time of day except through bound blocks [judgment].

---

## 6. Facts that pull against each other

1. The docs forbid per-bot paper on the node (DEC-0261, `QMX/docs/components/qmb.md:209`). Level 0 gives every unit a paper lane per market (`UP/L0:383`).
2. The docs and the built snapshot say bots never consume the MIS (`QMX/docs/components/trading-node.md:404`; `EB/qmn/src/qmn/mis/signal_snapshot.py:1-4`). The plan lets units read readings through `reads`. C-08 moves the code and changes its consumers.
3. His seed has a unit widen its scope from MIS context (`RC/STATE.md:62`). The plan makes widening a new version and his click (§2.5).
4. His ruling has costs feed Kelly (`RC/STATE.md:75`). The sizer has no cost input, and commission has no record key (§4.3).
5. QMB's edge numbers do not reach the sizer. Paper starts from defaults, and `own_journal` starts at the watermark (§1.3).
6. PBO sits only in the `old-qmx` preset. Code defers it, and the docs call it a candidate (§1.2).
7. The R measure list has no average win or average loss in R. Records split per market only, never per session or timeframe (§1.2, §5.3).
8. The shipped template promises a regime and session breakdown. The docs' result contract has no breakdown field (`QMX/docs/contracts/ct-32-performance-result.yaml`, a search for session, regime and per-market found none).

---

## 7. Not covered

- Read only the cited sections, not whole files: research 02, 22, 23, 26, 32, 37 and 45; Part C `NODE.md`; Part B `qmb.md`; `QV2/architecture/lab-and-pods/` (the pods' paper soak with its five readiness checks, `ARCHITECTURE-SPINE.md:165-169`, belongs to G6); the docs' CT-29 and CT-32 contracts.
- Ran no code. Branch facts come from `git show` and `git grep` at the branch tips at about 21:30, and the stack moves every hour.
- Did not read the old QMX-discussion sources (G3 covers them) or the seed register the Fable agent is writing.
- Did not check whether IC Markets' cTrader offers stock CFDs today. The claim rests on research 32.
