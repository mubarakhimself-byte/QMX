# 01: Ground truth of the algo-facing side

Written 2026-10-24. Research only. Nothing here is ratified, and nothing was changed in any repo.

Ticket: `wayfinder/tickets/ground-truth-algo-side.md`. It builds on `grounding/09-original-design-recovery.md` (G09). G09's Job C (QMB today) is not redone. It is rechecked only where the data round changed the code after G09 was written.

## How to read this

**Labels.**
- **CHECKED**: I read it at the cited path and line on 2026-10-24.
- **REMEMBERED**: the operator said it (in `seeds.md`, `decisions.md` or a transcript), but no code or ratified doc backs it.
- **INFERRED**: my reading or proposal.

**Numbers.** Line counts and file sizes are facts about the code. Every threshold, limit or setting named here is configurable. None is a fixed value.

**Short paths.**

| Alias | Path |
|---|---|
| `EB` | engine/base at `f05fc64b` (the merged trunk after PR #197), read from the detached checkout `D:\Temp\wrapup-read`. This is the newest merged code. |
| `RB` | `C:\Users\Mubarak\Desktop\QMX-worktrees\rebuild` (rebuild/base `195d1f88`, 12 Oct). It is older than `EB`: the data round since changed `qmf-data` and `qmb` (35 files, +5,110/−3,907 lines; `git diff --stat 195d1f88 f05fc64b -- qml qmb qmn packages`). So `EB` is the code truth below. |
| `RL` | `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\` (`seeds.md`, `decisions.md`, `grounding\`) |
| `DOCS` | `C:\Users\Mubarak\Desktop\QMX\docs\` on `main` (`c3e8ec5e`). Its QMF, QML and node pages are newer than the code line's copy. |
| `DW` | `C:\Users\Mubarak\Desktop\QMX\_docwork\` |
| `WB` | `C:\Users\Mubarak\Desktop\QMX\_bmad-output\planning-artifacts\architecture\architecture-QMX-2026-09-14\` (the 14 Sep "experimentation workbench" spine: QMB's last intended design before QMA v2) |
| `T` | `D:\QMX-worktrees\agent-system\tracker\qma-v2\` |
| `LP` | `T\architecture\lab-and-pods\` |
| `M` | `T\research\methodology\` |
| `DS` | `D:\QMX-worktrees\qma-ship\data\` (the data round's build store) |

---

## 0. The answer in twelve lines

1. **The algo side is four libraries that work in tests and do almost no real work yet:** QMF (7 toolbox packages), QML (bot authoring), QMB (backtesting) and QMN (the trading node). There are no real bots, no market data on the real home, no node running, and no agent backtest door merged. CHECKED (`M\50-backend-packages-and-data-today.md:13-21`; `T\HANDOFF-2026-10-24.md:18-25`).
2. **The data round (PRs 171-197, merged 24 Oct) added the first real plumbing:** one market-data door with a sealed holdout, typed monthly price files, downloaders for Dukascopy, Binance and CCXT, fill importers for cTrader, MT5 and CCXT, a QMB reader for those files, and one landing step that puts every backtest into the Library. CHECKED (`git log 195d1f88..f05fc64b`).
3. **Agents can call almost none of it today.** On `EB` the backtest tool refuses because no host binds the door, and it accepts only a pre-registered config, not a strategy. PR #204 (WU4, open) binds the door but keeps that config-only shape. CHECKED (`EB qmx-agents/packages/qmx-tools/src/qmx_tools/service.py:280-298`; `T\WRAPUP-PLAN.md:428`).
4. **QMB can only backtest bid/ask quote data, which means FX and CFD-style Dukascopy data.** Crypto lands as trade prints and trade bars, which QMB's reader refuses. Perps and futures have no contract, funding or margin model anywhere. CHECKED (`EB qmb/src/qmb/host/replay.py:744-778`); the crypto consequence is INFERRED.
5. **QMB cannot yet hold a month of one-minute data.** Its reader grows with the square of the bar count: about 16 GB for one month of M1. This blocks scalper research at scale. CHECKED (`DS\BACKLOG.md:26`).
6. **The MIS is six rule labelers plus one fitted model inside the node,** read only by the Book door and the kill switch. No router exists in docs or code. CHECKED (`DOCS\glossary.md:556-558`; `EB qmn/src/qmn/mis/labelers.py:1-7`).
7. **The Book and BMS are rich shapes that never sized a real trade.** The sizing ladder is "defined-unwired", and the bot never sizes. CHECKED (`EB packages/qmf-risk/src/qmf/risk/sizing.py:1-37`; `DOCS\components\qml.md:92`).
8. **The unit, pod and bot kinds already exist in the Library, with empty field schemas.** They are ready slots for the unit design. CHECKED (`EB qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json:1-10`).
9. **The anti-luck maths is already written, but in workflow templates, not in QMB.** Deflated Sharpe over every trial in a family, the family trial count and the pairwise correlation of variants all exist there, idle, because those templates wait on QMB doors that do not exist. CHECKED (`EB .../templates/_shared/overfit-gates/scripts/deflated_sharpe.py:1-9`; `.../b-build-and-prove/scripts/qmb.py:1-15`).
10. **The Lab backend that shipped is a workspace** (projects, levels, workspace state, a data panel, PC training). Pods, the pod simulator and the 17 Lab copilot tools are designed and unbuilt. CHECKED (`EB qmx-agents/packages/qmx-control/src/qmx_control/catalog.py:586-674`).
11. **Docs contradict the new intent at the root.** Docs say: no futures and no options ever, the Book owns exits, the bot never sizes, the MIS never reaches bots, and there is no per-bot paper. The docs never mention the Lab, pods or units. CHECKED (§6).
12. **Most of the money-path code (QMN, about 98k lines) has never been deployed,** and QMB's cost calibration is deliberately empty (GAP-0048). So nothing QMB produces today counts as evidence under its own rules. CHECKED (§1.4, §1.3).

---

## 1. Per component

Each block gives:
- intended purpose (docs first, then intent)
- what exists, with paths
- what agents can call today
- what is missing.

### 1.1 QMF: the toolbox (7 packages)

**Intended.** A toolbox, not an application: exact money and time, fingerprints, data rules, indicators, chart structure, risk rules and the broker connection. No loops and no schedules. Everything else must use it instead of re-doing it. CHECKED (`M\50…:75`, citing `DOCS\AGENTS.md:52-57`).

**Exists** (`EB packages/`):

| Package | What it does | State |
|---|---|---|
| `qmf-core` | Exact money, prices and time, one fingerprint function, and a typed "refused, and why" answer. `Instrument` = (venue, opaque symbol). | Used by everything. CHECKED (`DOCS\glossary.md:448-450`) |
| `qmf-data` | The store. New since 22 Oct: typed monthly price partitions keyed `source/subject/kind/variant/month`, freeze rules per kind, and corrections (`series.py:1-24`). Kinds: `ticks` (bid, ask, bid/ask volume), `bar-m1` (OHLCV, variant bid/ask/trade), `fill`, `trades`, `book` (`series.py:80-92`; `store/engines/typed.py:56-58`). Also the holdout seal with his click and splits with a gap (`seal.py`, `splits.py`, DR3B), importers for CSV bars, raw Dukascopy files and broker fills (`importers/`), the Binance Vision reader (`binance_vision.py`) and the Dukascopy fetcher (`dukascopy.py`). | Works in tests. The real home holds no imported data yet. CHECKED (`T\HANDOFF-2026-10-24.md:23`) |
| `qmf-indicators` | 15 formulas are named and owned (SMA, EMA, WMA, RSI, ATR, MACD, BBANDS, ADX, STOCH, OBV, MOM, ROC, VWAP, session-anchored VWAP, session range), but **only 6 have runnable wrappers** (SMA, EMA, WMA, RSI, MOM, ROC). | CHECKED (`indicators/arithmetic.py:111-131`; `indicators/wrappers.py:148-183`) |
| `qmf-structure` | Look-ahead-safe chart objects. One family only: swing points. | CHECKED (`structure/families.py:1-34`) |
| `qmf-registry` | Fingerprinted records for bots, Books, BMS, bindings and results, with lineage and a human-signed promotion path. | 38 source files in qmb/qml/qmn import it (`git grep -l qmf.registry`). The data-round design replaces its "room" with the Library (`M\55-data-round-architecture.md:63`). Both stand today. CHECKED |
| `qmf-risk` | Book, BMS, binding, door, admission, exits, control windows, paper, performance in R (24 modules, about 17.7k lines). | Shape only. `sizing.py` declares the ladder units (capital → runway → period budget → r_unit_price) and is stamped "defined-unwired". CHECKED (`qmf-risk/src/qmf/risk/sizing.py:1-37`) |
| `qmf-venue` | The cTrader protocol, connection manager, capabilities and error map, plus CCXT-style spot metadata normalisation. | CHECKED (`qmf-venue/src/qmf/venue/spot.py:1-5`). Used by the node and by `qmx-broker` (reads), though its README says only the node may use it. CHECKED (`M\50…:71`) |
| `extensions/qmf-calendar-forex` | Forex market hours only. | CHECKED (`M\50…:88`) |

**Agents can call:** four data rows (`data.instruments`, `data.bars`, `data.features`, `data.calendar`). They read through the market-data door, which the harness now binds (`EB qma-harness/src/qma/harness/harness.py:405-407`; `qmx_tools/service.py:242-261`). They return nothing until data is imported and he names the seal month. CHECKED (`T\HANDOFF-2026-10-24.md:32`). There are no rows for indicators, structure, risk or the registry. CHECKED (`catalog.py:237-278`).

**Missing:**
- An instrument and contract table (lot step, contract size, tick value, funding, margin) for any asset class.
- Runnable ATR, VWAP, Bollinger and session indicators, which scalpers use.
- Any structure beyond swing points.
- A calendar for anything but forex.
- Live wiring of the sizing ladder.

### 1.2 QML: the strategy library

**Intended (docs, ratified 21 Aug).**
- A governed bot is two artifacts: a CT-33 declaration (identity, parameters with ranges, footprint of streams and indicators, warm-up) and plain Python logic.
- The logic receives only declared evidence and returns intents. It never sizes, never sends orders, never reads a clock.
- Confluences (CT-34) carry legs with roles level, trigger, confirmation and filter.
- Exactly one strategy family per bot. The Book owns exits. No DSL in V1.
- CHECKED (`DW\feature_inventory.yaml:390-404`, FEAT-0030; `DOCS\glossary.md:220-228, 1025-1027`).

**Intended (operator, 13 Oct), replacing the above:**
- QML is rebuilt from scratch as a fixed contract, any code inside and a growing block catalogue.
- Signals carry reasons and optional strength.
- Exits are part of the strategy.
- Stage tags run from open (research, backtest, optimise) to compiled (stress, paper, live).
- REMEMBERED/agreed (`RL\decisions.md:41-62`).

**Exists** (`EB qml/src/qml/`, last change 7 Oct). About 14k lines in nine packages:
- `declaration` (bot, confluence, parameters, versioning, and `alternative.py` for ATC/PolicyPair authoring)
- `footprint`
- `protocol` (factory, evidence, intents, state)
- `conformance` (layer 1, layer 2, prediction linter, registration)
- `families`
- `generation` (structure generation, FEAT-0039)
- `research` (Stage 0 mill)
- `host`
- `logic`

There is one example bot (`qml/examples/conformant_bot/bot.py`) and no real bot anywhere. CHECKED (file listing; `RL\grounding\05-findings-2026-10-13.md:31`).

**Agents can call:** `research.qml_run`, which refuses: "Unknown bot_ref; ask the host to register a QML HostedBot". CHECKED (`catalog.py:276`; `T\LAUNCH-AND-CLEANUP-MAP.md:166-175`). Every chat has Bash and Python, so an agent can `import qml` directly. That is the raw-Python path he wants to avoid. CHECKED (`T\LAUNCH-AND-CLEANUP-MAP.md:179`).

**Missing:**
- The block catalogue. The STRATS dictionary (239 entries, 9 name collisions, about 7 runnable) sits outside QMX in `C:\Users\Mubarak\Desktop\Stats\dictionary\`. CHECKED (`RL\grounding\05…:56-61`). Ruling 16 calls the Stats design "reference only". CHECKED (`M\26-operator-rulings-and-alignment.md:25`).
- Signal strength, strategy-owned exits, stage tags, the librarian and GAP-0085's mechanism nouns.
- Any agent door that takes a strategy and validates or compiles it.

### 1.3 QMB: the backtester and evaluator

**Intended, in three layers:**
1. **Founding (20 Aug):** his own LEAN-CLI-shaped tool with Jesse's quant features: MCP, Monte Carlo, significance tests, optimisation, multi-symbol × multi-timeframe permutations, synthetic data and agent-readable reports. CHECKED (G07 §1, `RL\grounding\07-qmb-lineage.md:37-40`). Ratified as spine B-1..B-15: one config-compiled run, one loop for backtest and live, process per run, a ledger and a validation ladder. CHECKED (`DW\feature_inventory.yaml:368-372`, FEAT-0029).
2. **Workbench (14 Sep, `WB`).** This is the QMB intent `_docwork` explains:
   - three lanes chosen by which door you call (ungoverned value, governed run, agent-coordinated run)
   - two named analysis methods: **projection** (a filtered view of one result's trades, never a new result) and **rerun** (any change of size, Book or costs is a new run)
   - "generation is not search": QML authors new strategies and QMB only searches parameters
   - a candidate set is a query, not a copied table
   - the paper trinity: research-paper in QMB, node-paper on a demo account, no agent paper.

   CHECKED (`WB\ARCHITECTURE-SPINE.md:65-99`). StrategyQuant was a donor of shapes only (fixed and variable slots, databank as a query, Custom Projects as procedures, the robustness ladder); its genetic engine was refused. CHECKED (`WB\CAPABILITY-EXPANSION.md:41-49`). This design routed agents through `qma-daemon`, which has since been deleted.
3. **QMA v2 (Oct):**
   - Backtests run on one dedicated QMB machine that agents call (ruling 68).
   - QMB is a tool agents call but cannot edit (`RL\decisions.md:64`).
   - The Lab compiles a "setup" and calls `qmb.run/sweep/walk_forward/robustness/optimize` through one port. CHECKED (`M\26…:149`; `LP\ARCHITECTURE-SPINE.md:120-124`).

**Exists** (`EB qmb/src/qmb/`, about 76k lines in 14 packages; last change 23 Oct):
- the run loop, config compiler and orchestrator with a ledger
- fill, spread, slippage, commission and swap ports
- Optuna optimisation with train and test splits
- robustness (trade shuffle, candle perturbation, rule significance, walk-forward)
- sweeps (instruments × timeframes × parameters for one bot), ranking and compare
- `analysis/project.py` and `analysis/rerun.py`: the workbench's two methods are in code
- ATC/PolicyPair execution (`execution/alternative.py`): a run whose risk policy is not a Book or BMS
- the `qmb` CLI.

New since 22 Oct:
- a typed-partition replay reader (`host/replay.py`, DR4)
- `host/library_landing.py`, which lands one `backtest-result` per run with `consumed`, `uses` and `tests` edges
- registry reads through the Library's ten kinds (commit `1690df1f`).

CHECKED (file listing; `git show --stat 7e3833f4 c2bd18de`).

**G09 Job C, rechecked on `EB`.** Still true:
- The grid is partial: one bot per sweep, CLI only.
- There is no similar-market search.
- No correction for the number of tries is applied. PBO/CSCV is named and deferred (`robustness/summary.py`, `walkforward.py`).
- Nothing feeds a registry of where bots belong.

New facts that change the picture:
- **The replay reader takes only ticks with bid and ask, or a bid and an ask `bar-m1` series of the same month. "Half a pair is refused."** CHECKED (`replay.py:744-778`, `:388-412`).
- **Every cost model refuses without a calibration artifact, and calibration content is deferred to GAP-0048.** That covers spread, slippage, commission and swap. CHECKED (`execution/cost.py:1-8`, `spread.py:1-9`, `slippage.py:1-7`, `financing.py:1-11`). All fills stay `optimistic`-tainted. Replay verdicts cannot gate live money (L20). CHECKED (`execution/fill.py:1-7`; `WB\ARCHITECTURE-SPINE.md:147`).
- **The reader is quadratic in frontier count: about 16 GB for one month of M1.** The probe stops at 1,000 frontiers. CHECKED (`DS\BACKLOG.md:26`; `T\WRAPUP-PLAN.md:443`).
- **Results are in money.** Per-trade `realized_r` exists only in `qmf-risk` and the node, not in QMB's measures. CHECKED (`git grep realized_r`; `RL\grounding\05…:37`).

**Agents can call (`EB`):**
- `backtest.run` refuses: "This host binds no qmb_backtest door", and it takes only a `config_ref` someone registered beforehand.
- `backtest.status` and `backtest.results` read old-shape objects, of which there are none.
- `backtest.compare` diffs two stored CT-32s.
- There are no rows for sweep, optimise, robustness, walk-forward, projection or rerun.

CHECKED (`catalog.py:242-275`; `service.py:280-298`). PR #204 (WU4, open) binds the door in process, "local by default", plus the landing and "the recorded run configurations". CHECKED (`T\WRAPUP-PLAN.md:428-440`). INFERRED: after WU4 an agent can rerun a registered setup but still cannot hand QMB its own strategy.

**Missing:**
- a strategy-in, result-out door (the "sealed package in" door)
- non-quote data replay (crypto trades and bars)
- an instrument table, perps and futures mechanics, and more than one settlement asset per run
- R-denominated results
- a windowed reader for M1 and tick months
- applied trial correction
- the standing every-bot × every-instrument job
- the similar-market search and the registry writer
- calibration content.

### 1.4 QMN: the trading node

**Intended (docs).**
- One supervised Linux process near the broker, paper or live, with no command line.
- It records the broker stream, runs bots through QMB's loop, applies the Book's rules, the kill switch (KSA, five levels GREEN to BLACK, de-escalation only by a human) and the per-Book kill line, reconciles, and backs everything up.
- CHECKED (`DOCS\glossary.md:484-512`; `M\50…:127-133`).

**Intended (operator, 21 Oct):**
- A trading server where trusted bots live.
- Cut to its basics, holding only the MIS router and the kill switches.
- It connects back to his PC and self-tests on connect.
- REMEMBERED (`RL\seeds.md:107-116`).

**Exists** (`EB qmn/`). About 98k lines plus 5k deploy planners, unchanged in substance since 7 Oct:
- the cTrader live client
- the recording loop
- order identity with the protective-stop rule
- KSA and news windows
- the kill line, breakeven ratchet and bench
- the virtual ledger, reconciliation and seats
- the MIS
- Book-level paper to a paired demo account
- human promotion
- about 11k lines of proof campaigns
- an 8.7k-line MIS training pipeline
- a spot paper simulator (`qmn/venue/spot_paper.py`).

It has never been deployed. CHECKED (`M\50…:332-372`).

**Agents can call:** `node.state`, which refuses with "No node configured". `node.propose_order` writes an unsigned proposal and always asks. CHECKED (`catalog.py:232, 277`).

**Missing:**
- a connect-back to the PC (its doors are localhost and a Unix socket)
- any execution venue beyond cTrader (no Hyperliquid, no futures broker, no MT5 execution)
- a deployment.

CHECKED (`M\50…:372`; grep `hyperliquid` = 0 files in `EB`).

### 1.5 MIS and SQS

**Intended (docs).**
- The node's labeler layer folds labelers into one compute-once signal snapshot for a closed consumer set: the Book door and the KSA, never bots (DEC-0204).
- The catalogue has eight labelers. Six are rule-based: identity, spread state, gap event, feed state, SQS and degraded sensors. One is fitted: `liquidity_stress_v1`. One is trained: `regime_classifier_v1`, with no ratified model.
- HMM, BOCPD, MS-GARCH and Kronos are candidates without authority (DEC-0262).
- SQS = historical average spread for the session window ÷ live spread, with per-instrument-class hard blocks, hysteresis and an outlier guard. It blocks only, never sizes, and its baseline is keyed (venue, environment, instrument). All parameters are UI-editable with no defaults.
- CHECKED (`DOCS\glossary.md:556-558, 985-991`).

**Intended (operator).**
- 20 Oct: a router that places proven bots where they are proven. Bots never read it. REMEMBERED (`RL\seeds.md:13-26`).
- Also 20 Oct, the earlier "lean": the MIS becomes TA blocks that bots may read. It is still written in `decisions.md:85-92` as "NOT agreed", and `seeds.md` reverses it.

**Exists** (`EB qmn/src/qmn/mis/`): the six labelers and the snapshot fold (`labelers.py:1-7`, `signal_snapshot.py`), liquidity stress (`liquidity.py`), a shadow lane for candidates (`shadow.py`), and six `regime_*` modules of training pipeline. QMB has a modelled-spread series that non-live SQS can read (`qmb/execution/spread.py:5-8`). QMB applies no MIS label to a backtest. CHECKED (`RL\grounding\05…:49`).

**Agents can call:** nothing.

**Missing:**
- the router
- per-bot regime fit
- the premium-session detector
- the RVOL gate
- the multi-timeframe sentinel
- any scalper-specific labeler
- MIS labels on backtest trades (needed for the "states" a registry would prove).

CHECKED for absence in docs (G09 Job B items 1-14).

### 1.6 The Book and BMS

**Intended (docs).**
- Authority runs bot → Book → BMS → operator.
- The Book is admission, sizing, doors, leash, exit policy and profiles. The BMS is per account: accounting, constraints, journals and KSA policy.
- Both are versioned templates whose every variable carries a unit kind and a `ui-editable` flag.
- A new Book proves itself by linters, a demo shakedown and one signature.
- Book and BMS are "the default implementations, not the only ones" (DEC-0448).
- CHECKED (`DOCS\glossary.md:112-124`).

**Intended (operator).** The unit replaces the Book as the place where sizing lives: sizing tuned from the bot's own record. The account guard (kill line, budget, correlation, kill switch, news) stays outside. REMEMBERED/agreed (`RL\decisions.md:30-39`; `RL\seeds.md:28-32`).

**Exists.** `qmf-risk` (shape and grammar). In the node: the kill line, ratchet, bench fold and ledger. In QMB: a Book handler that refuses any size that is not an exact lot-step multiple. And ATC/PolicyPair as a non-Book policy seam in QMB and QML. CHECKED (`RL\grounding\05…:38-44`; `qmb/execution/alternative.py:1-6`; `qml/declaration/alternative.py:1-6`).

**Agents can call:** nothing.

**Missing:**
- any run where sizing comes from the ladder (r_unit_price is a fixed input)
- house money and reverse house money
- market correlation
- per-bot self-tuning.

### 1.7 The Lab and Pods

See §4.

---

## 2. Every seed in `seeds.md`

Status means: EXISTS = built and usable, or ratified in docs where the seed is a rule. PARTIAL = some parts are built or designed. MISSING = neither.

| # | Seed (`RL\seeds.md` line) | Status | Source |
|---|---|---|---|
| 1 | Two sides: algo-facing (QMB, QML, QMF, QMN) and human-facing; agents between (6-10) | EXISTS | Two uv workspaces split exactly this way; the catalog is the one bridge. CHECKED (`T\LAUNCH-AND-CLEANUP-MAP.md:161-165`) |
| 2 | Algo side due a clean refactor, QMN especially (11) | MISSING | No algo-side refactor has started. Only deletions of the old agent runtime touched it. CHECKED (`git log --since=2026-10-03 -- qmn qml/src`) |
| 3 | MIS is a router (load balancer: bots = servers, markets = traffic) (13-17) | MISSING | MIS = labelers for the Book door and KSA. CHECKED (`DOCS\glossary.md:556`). The old router existed only in lost pre-crash code. CHECKED (G09 A.1) |
| 4 | Bots never read the MIS (18) | EXISTS | DEC-0204, a closed consumer set. CHECKED (`DOCS\glossary.md:556`) |
| 5 | Node keeps only the MIS and the kill switch (19) | PARTIAL | Both exist in the node, beside about 98k other lines. CHECKED (§1.4) |
| 6 | Bots watch their own proven pair; extra pairs arrive through the MIS (20) | MISSING | A bot's footprint declares fixed streams. Nothing adds pairs. CHECKED (`DOCS\glossary.md:396-398`) |
| 7 | Unit = bot + its own risk and sizing tuned from its own record (28-30) | MISSING | The Library `unit` kind exists with empty fields (`kinds/unit.schema.json:1-10`). ATC/PolicyPair is the nearest code seam. CHECKED |
| 8 | Today that sizing is the BMS/Book (30) | EXISTS (shape only) | `qmf-risk/sizing.py:1-37` "defined-unwired". CHECKED |
| 9 | MIS stays outside the unit (31) | EXISTS in docs | DEC-0204. CHECKED |
| 10 | Best risk/sizing per bot type from research and the bot's record (32) | MISSING | No per-type or per-bot calibration code. INFERRED from §1.6 |
| 11 | Registry "preferred": markets, sessions, states with proof from QMB's run-on-every-bot (34-36) | MISSING | No per-market proof records. The `unit` kind's page has an empty "Markets" tab (`unit.schema.json`, tab source `fields.markets`). CHECKED |
| 12 | Registry "hypotheticals": look-alike markets to test (37) | MISSING | No market-similarity code. CHECKED (G09 C.2; grep on `EB`) |
| 13 | Registry = key-value data filled by an agent or workflow (38-39) | MISSING | No writer. CHECKED (G09 C.4) |
| 14 | 1m and 5m of one logic = two registry variants (40) | PARTIAL | Library lineage edges (`variant-of`, `branches-from`, `derived-from`) exist. The identity-rule table (`settings.lab.identity_rule`, timeframe → `variant-of`) is designed, not built. CHECKED (`LP\ARCHITECTURE-SPINE.md:186-190`) |
| 15 | Correct for the number of tries (41) | PARTIAL | QMB ledgers every trial (`role=trial`) but applies no correction. Deflated Sharpe over all family trials exists in template scripts that wait on QMB doors. CHECKED (`templates/_shared/overfit-gates/scripts/deflated_sharpe.py:1-9`; `b-build-and-prove/scripts/qmb.py:9-15`) |
| 16 | Domain expansion: instrument × timeframe × window (44-49) | PARTIAL | QMB sweep axes are instruments × timeframes × parameters, for one bot, CLI only. There is no window axis, and non-quote instruments cannot replay. CHECKED (G09 C.1; `replay.py:744-778`) |
| 17 | A domain-expansion workflow, designed after QMX is live (51-52) | MISSING (by design, later) | REMEMBERED |
| 18 | The correction scales with the number of variants; 1m and 5m of one pair is one bet (53-55) | MISSING | The "correlation ledger" in docs is now command lineage. The d4 template's pairwise-correlation step is a draft. CHECKED (`DOCS\components\trading-node.md:297`; `templates/d4-variant-comparison/scripts/compare.py:5`) |
| 19 | Funnel level 1: any source (article, video, book, transcript) (58) | EXISTS | The video-to-ideas, paper-scout, literature-review, source-to-card and feed templates run. The upload door and the `source` kind are merged. CHECKED (`templates/catalog.py:69-124, 434-439`; `M\55…:68-71`) |
| 20 | Funnel level 2: build in QML → test in QMB (59) | PARTIAL | Intake works. "Turn a strategy idea into a tested strategy", "Source to a Lab test" and "First backtest from an idea" are drafts that need `qmb-door`. CHECKED (`templates/catalog.py:243-283`) |
| 21 | Pass branch: iterate, then expand (60) | PARTIAL | `d3-iterate-against-qmb` and `d4-variant-comparison` are drafts. `revolution-loop` (loop until plateau) runs. CHECKED (`templates/catalog.py:301-348`) |
| 22 | Fail branch: find why it failed, then a context where its rules hold (61-65) | PARTIAL | `rs6-hypotheses-from-dead-ends` is a draft that needs the real Library. Dead-end memory rows are designed (Lab AD-18). There is no "find a context" analysis. CHECKED (`templates/catalog.py:259-267`; `LP\ARCHITECTURE-SPINE.md:198-202`) |
| 23 | Rewrite branch: cheap models do the bulk, a strong model rewrites (66) | PARTIAL | The router, provider rows, sub-agents on any provider and `delegate` are merged. There is no rewrite workflow. CHECKED (`T\HANDOFF-2026-10-24.md:15`) |
| 24 | Every node a variant in a lineage tree (68) | PARTIAL | Edges and a "Family tree" tab on the `unit` and `bot` pages exist. No rule says what makes a variant (the open identity question). CHECKED (`unit.schema.json` tabs) |
| 25 | Needs agent memory of failures and conditions (70) | PARTIAL | Hindsight memory is merged. The `memory-row` kind exists. `dead_end` tagging is designed. CHECKED (`T\HANDOFF-2026-10-24.md:15`; `kinds/` listing) |
| 26 | "When to expand" as a numeric stopping rule (72-76) | MISSING | Claude's proposal only. REMEMBERED |
| 27 | A decoupling workflow when architecture starts (78-79) | MISSING | Process seed. REMEMBERED |
| 28 | Sniping: bot × pair × premium window with its own sizing profile (81-85) | MISSING | The old premium-session detector is not in docs or code. `qmf-risk/control_window.py` holds protection windows (news blackouts), not premium windows. CHECKED (G09 A.5, B.3) |
| 29 | Breadth compounding across instruments and sessions (87-91) | PARTIAL | A one-bot sweep across instruments exists (CLI). There is no market correlation and no compounding principle in docs. CHECKED (G09 B.6, B.8) |
| 30 | SQS guards whether the edge survives each instrument's costs (91) | PARTIAL | SQS exists (node, block-only, spread vs its own normal). The after-cost expectancy gate per bot × instrument does not. QMB costs refuse without calibration. CHECKED (§1.3, §1.5) |
| 31 | Scalper-specific MIS, from a taxonomy of scalper types (93-97) | MISSING | A 9-type draft taxonomy exists in G09 Job E only, unreviewed. CHECKED |
| 32 | Fundamentals as an MIS input; the news kill switch exists (99-101) | PARTIAL | KSA trigger `scheduled_news`, news windows and the Forex Factory calendar exist. Fundamentals do not. CHECKED (`DOCS\glossary.md:504`; `M\50…:181-190`) |
| 33 | Horizons: scalpers first, then intraday; spot-only later (103-105) | n/a | Intent |
| 34 | Node = trading server where trusted bots live; simplify QMN (107-109) | MISSING | 98k lines, never deployed. CHECKED (§1.4) |
| 35 | Install the node, the MIS sets itself up, it connects back and self-tests (110-111) | PARTIAL | "Connect a machine" exists for workflow workers: the Contabo server, `qmx_control/node.py`, remote runs. The trading node has no connect-back and no self-test on connect. CHECKED (`M\50…:376`; `T\HANDOFF-2026-10-24.md:15`) |
| 36 | Kill switches with levels; some fire without his PC (112) | PARTIAL | KSA has five levels in code (`qmn/protection/`). Which levels fire alone is open. It has never run. CHECKED (`DOCS\glossary.md:504`) |
| 37 | Brokers: cTrader and MT5 today, crypto via CCXT (113) | PARTIAL | cTrader: live client (node) and read adapter. CCXT: reads and spot paper. MT5: declared type and fill importer only, no reads and no execution. The cTrader sign-in is PR #205, open. CHECKED (`qmx_broker/adapters.py:1, 59-76`; `qmf-data/importers/journal.py:1, 60`) |
| 38 | Broker accounts and connections live in QMX (114) | PARTIAL | The Connections list with health is merged (DR5A). The cTrader half waits for his demo sign-in. CHECKED (`T\HANDOFF-2026-10-24.md:22`) |
| 39 | Where the MIS sits and how bots are routed (115) | MISSING | Open. REMEMBERED |
| 40 | QMB redesign: grid, similar markets, registry feed, trial correction (119-125) | PARTIAL | Grid partial; the other three missing. CHECKED (G09 Job C, rechecked §1.3) |

G09 Job F's 12 candidate seed additions and its 9-type scalper draft are still unreviewed by him. CHECKED (`RL\seeds.md:137`).

---

## 3. Instrument coverage today

### 3.1 In docs

- **Identity is asset-neutral.** `Instrument` = (venue, opaque symbol). Asset class is a dated metadata record with an open value set, but the same line says "**no futures and no options ever (DEC-0015)**". CHECKED (`DOCS\contracts\ct-03-instrument-identity.yaml:46`; `DOCS\gap-report.md:360`).
- **Venues.** cTrader Open API is the first and only adapter, and IC Markets is configuration. Honest FX node-paper needs a cTrader demo. Spot crypto appears via the CONNECT increment (ccxt-shaped spot metadata). CHECKED (`DOCS\components\qmf-venue.md:87`; `DOCS\components\trading-node.md:189, 201`).
- **Words absent from `docs/`:** CFD, perp, Hyperliquid and MT5 (0 files). Futures appears only in the DEC-0015 ban. CHECKED (grep over `DOCS`).
- **Costs.** QMB's spread, slippage and financing are FX "ORIGINAL" content: daily swap on a rollover calendar, one settlement asset per run (`MixedSettlementAsset`). CHECKED (`DOCS\components\qmb.md:113`; G07 §3).
- **Instrument class** drives SQS thresholds per class. A missing class record means a block. CHECKED (`DOCS\glossary.md:452-454`).
- **Liquidation** exists only as a close reason (`venue_liquidation`), not as a margin model. CHECKED (`DOCS\glossary.md:1137-1139`).

### 3.2 In code (`EB`)

| Area | What exists | What does not |
|---|---|---|
| Data sources | Dukascopy ticks by QMX's own fetcher (`dukascopy-node` failed its probe), covering forex, metals, indices and CFDs (ruling 122). Binance Vision `trades`, `aggTrades`, `bookDepth` and `bookTicker`. CCXT one-minute trade bars. CSV bar importer. Raw Dukascopy importer for the old 10 GB. Broker fills from cTrader, MT5 and CCXT. Broker bars through `qmx-broker`, paged by the provider's own limit. Databento declared as a provider. CHECKED (`templates/download-dukascopy/README.md:28-33`; `templates/download-binance/README.md:6-11`; `templates/download-ccxt/README.md:1-14`; `qmx_broker/providers/__init__.py`; `M\26…:230`) | Paid futures data (later, ruling 122), order flow for spot FX (not available, ruling 128), funding-rate history |
| Data held on his real home | None in the door yet. The old 10 GB (EURUSD, USDJPY ticks 2003-2026) is saved on the server with checksums, and its import is a real step not yet run. The risk-lab M1 CSVs (EURUSD, BTCUSD 2021-2025) sit outside the door. CHECKED (`T\HANDOFF-2026-10-24.md:16, 23, 33`; `M\50…:173`) | — |
| Series kinds | `ticks` (bid, ask, volumes), `bar-m1` (OHLCV, variant `bid` / `ask` / `trade`), `fill`, `trades`, `book` (level, notional), `derived`. CHECKED (`qmf-data/series.py:80-92`; `typed.py:56-58`) | Depth snapshots beyond Binance's book files; bars above M1 are derived, not stored |
| QMB replay | Ticks with bid/ask, or a bid + ask `bar-m1` pair. CHECKED (`qmb/host/replay.py:744-778`) | Trade-only series, so **no crypto backtest from the data QMX downloads**. INFERRED from that line plus `download-ccxt/README.md:7` (variant `trade`) and `binance_vision.py:9-25` |
| Contract specs | `lot_step` and `value_factor` per run, supplied by the caller. `tick_size` in the spot normaliser. `pip_size` in the cTrader probe. CHECKED (grep on `EB`) | `InstrumentSpec`, `contract_size`, `contract_multiplier`, `funding_rate`, `margin_rate`: 0 files each. CHECKED (grep on `EB`) |
| Cost models | Commission, synthetic spread per instrument × hour × session, FX slippage catalogue, swap financing on the broker's market-hours calendar. All refuse without a calibration artifact. CHECKED (`qmb/execution/*.py` headers) | Maker/taker crypto fees, perps funding, exchange fee tiers, futures commissions and exchange fees |
| Calendars | Forex market hours (`extensions/qmf-calendar-forex`). The Lab design treats crypto's day as 00:00 UTC. CHECKED (`LP\ARCHITECTURE-SPINE.md:166`) | Exchange calendars for futures and index cash sessions |
| Execution venues | cTrader live (node). Spot paper simulator (node, testing). Read-only CCXT and cTrader. CHECKED (`M\50…:338`; `qmx_broker/adapters.py:1`) | Hyperliquid (0 files), any futures broker, MT5 execution, testnets |

INFERRED summary: today QMX can store FX, metals, indices, CFDs and crypto history, but can backtest only quote-based (FX and CFD-style) history, on FX-shaped costs that carry no numbers until calibrated.

---

## 4. The Lab, Pods and mini-app templates

### 4.1 What they are meant to be

- **The Lab** is "QMX's core feature": notebooks, a node editor and a VS Code-like space for strategies, models, components, variants, MIS versions and workflows. CHECKED (`M\26…:13`, ruling 6).
- In the design, one subject has one draft with two views (graph and code).
- Every Lab button is an engine run, and every result lands in the Library.
- Templates cover backtest, sweep, walk-forward, robustness, optimise, training, pod test, stress and paper.
- Honesty rules: every run is a trial in its family, the sealed year opens once per family, and gate thresholds can be tightened by the copilot, never loosened. CHECKED (`LP\PLAIN-WORDS.md:3-13`).
- **Pods** are a stack of pure blocks in seven fixed slots: inputs, guards, allocator, sizer, throttles, caps and ledger.
  - One simulator serves every pod screen: size trail, replay over bots, stress board, drawdown fan, head-to-head and mixes.
  - A pod compiles to the default Book + BMS through `PodCompilerPort`. Blocks the node cannot run come back as `unsupported_blocks` and stay Lab-only.
  - The node is read through `NodePort`.
  - Paper is a daily chain of engine runs on a server paper ledger. Promotion is two human clicks in Portfolio.
  - CHECKED (`LP\ARCHITECTURE-SPINE.md:150-166`).
- **Units** are read as "a list of parts (bot + pod + MIS needs)", so the unit design can change them without touching the Lab. CHECKED (`LP\PLAIN-WORDS.md:23`).
- **Docs.** `docs/` never mentions the Lab, pods or units (0 files each); the old name "Authoring" remains in 16 files. CHECKED (grep over `DOCS`).

### 4.2 What recent PRs built

- **Lab, DR13 (PR #194):**
  - A project is a `collection`.
  - "New…" installs a template at one of four levels: quick idea, experiment, study or campaign.
  - Workspace state is an annotation on the project.
  - There is a data panel through the market-data door, PC training with a GPU slot and a free-disk check, and `model` landing with data fingerprints, code version and seed.
  - Seven `lab.*` rows exist, all `agent=False` (screens only), and "pods are not among them".
  - CHECKED (`catalog.py:586-674`; `git show --stat fface86d`).
- **Library kinds that the Lab and Pods need already exist:** `pod`, `pod-block`, `unit`, `bot`, `book`, `bms`, `setup`, `backtest-result`, `model`, `stress-scenario`, `paper-run`, `test-report`, `dataset`, `hypothesis` and `trade`. Their field schemas are mostly empty (`unit`: no properties; `pod`: one `slots` object). CHECKED (`qmx_library/kinds/*.schema.json`).
- **Not built:**
  - the 17 Lab copilot tools
  - the pod simulator, `PodCompilerPort` and `NodePort`
  - the paper template
  - the identity-rule table
  - the families ledger
  - the setup-compiling QMB door
  - notebooks on `KernelPort`.

  CHECKED (`LP\ARCHITECTURE-SPINE.md:204-208`, AD-19: "pods are not in it"; `catalog.py`).
- **UI** (`ui-review/repair`, demo data only): Strategies bench (Build, Test, Train, Compare), Pods bench (Design, Test, Paper), 10 pod templates (Paper starter, Classic Book, Vol-targeted core, Trend rider, Alt scalper, Kelly-lite, Risk-parity, Capital guard, Canary, Model-sized hybrid) and a Portfolio MIS tab. CHECKED (`LP\UI-TO-BACKEND-MAP.md:87-92, 123`).

### 4.3 Mini apps and their templates

- **Built:**
  - Mini apps are Claude plugins.
  - Publishing lands a `mini-app` Library item (`qmx_apps/road/__init__.py:1-5`).
  - The `build-mini-app` and `debug-app` skills.
  - Four example apps: `exchange-status`, `macro-daily-bias`, `mql5-articles`, `weekend-watcher`. Two still import the deleted runtime. CHECKED (`EB examples/apps/`; `T\HANDOFF-2026-10-24.md:100`)
  - Two engine templates, `mini-app-lifecycle` and `connect-mini-apps`, are drafts that need `sandbox` and `app-op`. CHECKED (`templates/catalog.py:325-340`)
  - The lifecycle template refuses a money tool. CHECKED (`templates/ma-mini-app-lifecycle/README.md:15`)
- **Still open:** app tools never reach a chat. PR #198 (WU1, open) wires them. CHECKED (`T\HANDOFF-2026-10-24.md:52`).

### 4.4 How they relate to QML, QMB and the Book

- The Lab is the human and agent front. QML is what it edits (bot logic), and QMB is what its runs call (`QmbPort` → the `qmb_backtest` door). A setup cannot compile without a composition (a pod or a default pod). CHECKED (`LP\ARCHITECTURE-SPINE.md:124`).
- A pod is the Lab's form of risk and sizing. Its only route to trading is compiling into the Book/BMS the node knows. INFERRED: pods and the unit overlap almost completely. Pods give a sizing stack beside a bot. The unit puts sizing inside the bot's own record. `decisions.md:75` puts it a third way: "a pod = the frame (account guard + router), with units inside". These three readings are not reconciled.
- Ruling 125: for now QMB is the backend tool that matters to agents, and the rest reaches agents through the Lab and mini apps. CHECKED (`M\26…:233`).
- Mini apps cannot run backtests or touch money. They reach QMB only through workflows. INFERRED from §4.3 and the catalog.

---

## 5. Shipped in the last three weeks: must not be removed casually

Merged into `EB` between 3 and 24 Oct. Each row names what it is and where it lives. CHECKED (`git log --since=2026-10-03`; PR list #171-197).

| What | Where | Why the unit design must respect it |
|---|---|---|
| Market-data door: one way in, seal by his click, split gap, purpose-scoped reads, `materialise` for QMB | `qmx-host/src/qmx_host/market_data.py`; `qmf-data/src/qmf/data/{seal,splits,series}.py`; `store/engines/typed.py` (DR3A-C) | Every price read for backtests, the Lab and agents goes through it. A registry proof must come through it, or the holdout leaks |
| Typed monthly partitions and per-kind freeze rules | `qmf-data/series.py` | The address scheme (`source/subject/kind/variant/month`) is what any instrument table must key on |
| QMB typed replay reader and the one landing step | `qmb/src/qmb/host/replay.py`, `data/policy.py`, `host/library_landing.py` (DR4) | One result shape (`backtest-result`) with `consumed`, `uses` and `tests` edges is where registry proof would hang |
| Importer for QMB's old result files | `qmx-library/src/qmx_library/migrate/from_qmb_results.py` (DR4) | Old evidence enters the same shape |
| QMB registry reads through the Library's ten kinds; QMB host on `qmx_host` | commits `1690df1f`, `9782ea2e` | QMB already reads bot, Book and BMS from the Library |
| Downloaders as scheduled workflows | templates `download-dukascopy`, `download-binance`, `download-ccxt`, `feed`; `qmf-data/binance_vision.py`, `dukascopy.py` (DR6) | The data supply for the instrument grid |
| Fill importers for cTrader, MT5 and CCXT, with one `trade` item per round trip | `qmf-data/importers/journal.py` (DR12) | The live and paper record a self-tuning unit would learn from |
| Connections with health; broker paging without a cap | `qmx-broker` (DR5A, DR11) | Brokers and accounts already live in QMX |
| Lab workspace and PC training | `qmx-control/src/qmx_control/lab.py`; `d6-ml-training-run` (DR13) | The Lab's first slice. Pods must build on it, not beside it |
| Steps placed next to their data; run pass data scope | DR14; `qmx-router/src/qmx_router/passes.py` (DR3B) | Where a grid of backtests can run (PC, server, rented machines) |
| Library store: 38 kinds, edges, marks, branches, blame, upload door, `source` kind | `qmx-library`; DR7, DR8 | Already holds `unit`, `pod`, `pod-block`, `bot`, `book`, `bms`, `setup`, `model`, `paper-run`, `stress-scenario` |
| Engine with about 40 templates, including the QMB-door drafts with deflated-Sharpe and family-trial gates and the d4 variant comparison | `qmx-engine/src/qmx_engine/templates/` | The anti-luck code the registry needs is here already |
| One catalog as the only bridge | `qmx-control/src/qmx_control/catalog.py` | Every new door becomes one row here, not a side path |

Older work in the same family, from before the window but load-bearing:
- QMB `analysis.project` / `rerun` and ATC/PolicyPair (QMB and QML, 1-7 Oct)
- `qmf-risk`
- QML conformance
- the node's live path (`M\50…:360`).

In flight, not merged: PRs #198-205 (WU1-WU8). WU4 edits `qmx-tools`, the engine's `app_op` and `qmb/host/`, the same files any agent door into QMB will touch. CHECKED (`gh pr list`; `T\WRAPUP-PLAN.md:432-442`).

---

## 6. Contradictions and stale docs

| # | Topic | Side A | Side B | Label |
|---|---|---|---|---|
| 1 | Exits | Book owns exit policy; a bot only proposes (DEC-0147; `DOCS\glossary.md:116`) | "Exits are part of the strategy" (`RL\decisions.md:60`) | CHECKED both |
| 2 | Sizing | Bot never sizes; the Book resolves `requested_r` (`DOCS\components\qml.md:92`) | The unit sizes itself from its own record (`RL\seeds.md:28-30`) | CHECKED both |
| 3 | MIS role | Labelers for the Book door and KSA only (DEC-0204) | Router that places bots (`seeds.md:13-20`) vs the 20 Oct "MIS = TA blocks bots may read" lean, still written in `decisions.md:85-92` | CHECKED. `decisions.md` was not updated when `seeds.md` reversed it |
| 4 | Asset classes | "No futures and no options ever" (DEC-0015, `ct-03:46`) | CFDs, perps, futures and spot (`decisions.md:12-17`); paid futures data later (ruling 122) | CHECKED |
| 5 | Per-bot paper | None; Book-level demo only (DEC-0261, `trading-node.md:216`) | Paper per unit (G09 B.15; `decisions.md:122` backlog) | CHECKED |
| 6 | Correlation ledger | In docs: command lineage, the `enacts` edge set (`trading-node.md:297`) | Market correlation between live bots (`seeds.md:90`) | CHECKED |
| 7 | Where the unit lives | "The unit lives INSIDE the trading node" (ruling 14, `M\26…:23`) | The node keeps only the MIS and kill switches (`seeds.md:19`); the Lab reads units as a parts list (`LP\PLAIN-WORDS.md:23`) | CHECKED. INFERRED: compatible only if "inside" means "hosted by" |
| 8 | Pods vs units | Pod = a sizing stack compiled to Book + BMS (`LP` AD-10, AD-11) | Pod = frame (account guard + router) with units inside (`decisions.md:75`) | CHECKED. Unresolved |
| 9 | QMB agent door | Lab AD-5: "Prevents the pre-registered-config-only door" | `EB` and WU4 key on a registered `config_ref` (`service.py:287-291`; `WRAPUP-PLAN.md:428`) | CHECKED |
| 10 | Where backtests run | One dedicated QMB machine (ruling 68; Lab AD-5 default adapter = engine `app_op` on `qmb`) | WU4: QMB "in process … local by default" (`WRAPUP-PLAN.md:437`) | CHECKED |
| 11 | Registry home | `qmf-registry` is the governed store (`DOCS\components\qmf-registry.md`); 38 backend files import it | The Library replaces the registry room (`M\55…:63`) | CHECKED. Both stand in code |
| 12 | QMF venue use | README: only the node may import it | `qmx-broker` imports it (`M\50…:71`) | CHECKED |
| 13 | Stats dictionary | "A good seed, rebuilt and enhanced" (`decisions.md:53`) | Stats design is "reference only" (ruling 16) | CHECKED. Compatible if "seed" means reference |
| 14 | Risk authority | His rule: risk and sizing authority = GitBook + node docs; QMX-discussion barred (`T\HANDOFF-2026-10-24.md:284`) | G09 recovered house money, slots and premium sessions from the QMX-discussion vault | CHECKED. Treat G09's risk items as history, not authority |

**Stale docs (docs behind code):**
- `DOCS\components\qmb.md:237` says sweep batch/rank CLI wiring is missing. The CLI has it. CHECKED (G09 C.1).
- `qmb.md:303` says ATC is "not in code". It is (`qmb/execution/alternative.py`). CHECKED.
- `DW\feature_inventory.yaml` lists FEAT-0033..0039 (workbench connect wave) as `planned`. `qmb/analysis/project.py:371` and `rerun.py:143` exist. CHECKED.
- `WB` (the 14 Sep workbench) routes agents to QMB through `qma-daemon`, the CT-47 ExperimentSpec and its Experiment Ledger. The daemon is deleted, and the Library `setup` object now holds the CT-47 shape (Lab AD-5). CHECKED (`WB\ARCHITECTURE-SPINE.md:101-105`; `M\50…:142`).
- `docs/` has no page for the host, engine, Library, router or tools, and none for the Lab, pods or units. `docs/AGENTS.md` still describes the retired factory. CHECKED (`T\LAUNCH-AND-CLEANUP-MAP.md:205-212`).
- `DW\enhancements.yaml` holds 71 documentation-precision rows, all deferred post-V1 on 21 Aug. They are not features. CHECKED (`enhancements.yaml:1-4`).
- `RL\decisions.md` still lists the pain floor as unanswered. He answered it on 6 Oct by rejecting the question. CHECKED (G09 A.11).

---

## 7. What the operator may not be seeing

1. **Crypto cannot be backtested yet, even though QMX now downloads it.** Binance and CCXT data land as trade prints and trade bars. QMB replays only bid/ask pairs. Perps and futures have no model at all. CHECKED (`replay.py:744-778`); consequence INFERRED.
2. **Scalper-scale backtests do not fit in memory yet.** One month of one-minute bars needs about 16 GB in QMB's reader, and ticks need more. The run-every-bot-on-every-instrument grid needs a windowed reader first. CHECKED (`DS\BACKLOG.md:26`).
3. **"Agent backtests" after WU4 means rerunning setups someone registered.** No door yet takes a strategy an agent wrote and returns a result. The funnel's step "build in QML → test in QMB" needs that door, and the Lab design already names it (`qmb.compile` → `setup`). CHECKED (`service.py:287-291`; `LP\ARCHITECTURE-SPINE.md:124`).
4. **By QMB's own rules, nothing it produces today can serve as proof.** The cost, spread, slippage and swap models are built but hold no numbers (GAP-0048). Fills are tainted optimistic, and replay verdicts may never gate live money (L20). A registry built on "proof from QMB" needs calibration artifacts per broker and instrument, or a rule change. CHECKED (`qmb/execution/*.py` headers; `WB\ARCHITECTURE-SPINE.md:147`).
5. **The anti-luck machinery exists twice in plan and once in code, in the wrong place.** Deflated Sharpe and family trial counts are written in workflow template scripts. QMB has PBO/CSCV named and deferred. The Lab designs a third home (`families.ledger`). One home needs choosing before the registry is built on it. CHECKED (§2 row 15; `LP\ARCHITECTURE-SPINE.md:126-130`).
6. **The unit already has a slot waiting.** The Library has `unit`, `bot`, `pod` and `pod-block` kinds with empty fields, and the `unit` page already has "Markets" and "Family tree" tabs. ATC/PolicyPair in QMB and QML already runs a policy that is not a Book or BMS. Both are ready seams, so the unit need not start by rewriting `qmf-risk`. CHECKED (§4.2, §1.6). INFERRED: the cheapest unit path.
7. **Risk and sizing have never sized a real trade anywhere.** The ladder is shape-only, the backtest takes `r_unit_price` as a fixed input, and the lot-step rule refuses real sizes. The "self-tuning" design starts from zero working sizing, not from a working Book. CHECKED (`RL\grounding\05…:38-40`).
8. **The scalper toolbox is thin.** Six runnable indicators. VWAP (his named exit), ATR, Bollinger, MACD and session range are named in code but not runnable. Structure is swing points only. CHECKED (`arithmetic.py:111-131`; `wrappers.py:148-183`).
9. **The MIS states a registry would prove against are not computed on backtests.** QMB attaches no MIS label to a trade. "Preferred states" therefore need either the labelers in QMB or the labels stored beside price partitions. CHECKED (`RL\grounding\05…:49`); the remedy is INFERRED.
10. **The Portfolio MIS tab in the UI design shows labelers that do not exist** (volatility state, session, news state, Regime HMM). The code has spread state, gap, feed, SQS, degraded sensors and liquidity stress. CHECKED (`LP\UI-TO-BACKEND-MAP.md:123`; `qmn/mis/labelers.py:1-7`).
11. **Pods, units and "frames" are three readings of one idea,** and the Lab has already designed one of them (`PodCompilerPort`, seven slots). Settling the unit settles pods too. CHECKED (§6 row 8).
12. **Docs still ban futures and options "permanently"** (DEC-0015). Any instrument expansion overrules a ratified decision and should be recorded as one. CHECKED (`ct-03:46`).
13. **Everything since 20 Oct was built and checked by DeepSeek only.** Nothing has run on his real home. The first real boot is the first independent check of the data door, the QMB reader and the Lab workspace. CHECKED (`T\HANDOFF-2026-10-24.md:18`).
14. **Every copilot chat still has a shell and Python.** Until the QMB and QML doors exist, an agent that wants a backtest writes raw Python against the libraries and skips the seal. That is the path he wants closed. CHECKED (`T\LAUNCH-AND-CLEANUP-MAP.md:179`; the store applies the seal only when a caller passes it, `M\50…:287`).

---

## Not verified

- QMB, QML and QMN behaviour was read in code and docs, not run.
- The 16 GB figure is the data store's backlog estimate, not my measurement.
- WU1-WU8 were read in the plan and as open PR titles only, not reviewed as diffs.
- The UI (`ui-review/repair`) was read through `UI-TO-BACKEND-MAP.md`, not clicked through.
- `DW\ledger.yaml` and `extractions.yaml` (about 1.8 MB together) were sampled by search only.
