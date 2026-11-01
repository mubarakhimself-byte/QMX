# QMB: the first mini app, and what happens inside it

Part B, sub-area 1. Decisions: spine AD-201, AD-202, AD-204, AD-205, AD-206, AD-215. Shapes: `CONTRACTS.md` §1 and §2. Slices: `BUILD-SLICES.md` B3 to B12 (with B5b) and B14. Amended after R1 (`architecture/review/R1-FIXES-X1-B.md`).

**In plain words.** QMB is an app inside QMX. An agent, a workflow or he asks it to test a unit on chosen markets and dates, and waits for the answer, the way a test suite runs. QMX itself issues the run's number, counts it as a try, hands QMB exactly the data the study allows, and files the result. He can install a second QMB beside the first and compare them; the score never depends on which one ran.

His words: "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383); "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383); "It runs the same way you run your tests." (T2:135); "I hope you haven't confused QMB and live trading." (T1:1177); "it is run on every bot across multiple instruments" (T1:442); "there is no point in me being refused that" (T1:1574).

Ledger rows that bind: B-00, B-01, B-02 (seed, honoured), B-03, B-04, B-05, B-07 (lead's call), B-08, B-12, MA-05, CC-26, CC-07, CC-08.

## 1. Verdict: a mini app, with the honesty parts in the core

| In the QMB app (swappable) | In the core (one copy, `qmx-judge` and the host) |
| --- | --- |
| replay, fills, costs, carry, rolls, margin, sizing inside the unit's socket | the run id, the try row, the materialised inputs, the landing |
| results in money and R, slices, receipts, the run's unit journal | the judge, study specs, verdicts, baseline cards |
| robustness, walk-forward, sweeps, optimisation, what-if computations | which tester is the default, and the conformance runner |
| synthetic series, the behaviour check run (checker layer G) | `status`, `results`, `compare` (core rows over landed results) |

Why core for the right column: a variant that issued its own run ids, counted its own tries or landed its own results could change the score (QB-13, QB-24); a variant that reported its own status could disagree with the Library. Why app for the left column: he must be able to run several testers at once.

## 2. What exists today (CHECKED unless marked)

| Piece | State | Where |
| --- | --- | --- |
| `qmb/` 91,252 lines, 113 test files; 173 replay and robustness tests pass on Windows | BUILT | G1 §4.1 |
| House rules: banned imports outside allowed homes; banned words | BUILT | `qmb/tests/test_qmb_scaffold.py:33-47` |
| Replay paths: `execute_recorded_replay_request` (re-resolves CT-10 receipts, refuses other sources); `read_typed_replay_source` (typed monthly partitions, quotes only) | BUILT, not joined | `qmb/src/qmb/host/replay_execution.py:68`, `replay.py:608-626` |
| Cumulative frames: every frame holds every sample so far | BUILT (the only lookback limit) | `replay.py:557-571` (read this session) |
| Run loop over event slices, never forked; the node drives `run_slice` | BUILT | `qmb/src/qmb/runloop/loop.py:780`; `qmn/src/qmn/loop/driver.py` |
| Fill, cost, spread, slippage, financing, commission ports; calibration empty (GAP-0048) | BUILT, content missing | `qmb/src/qmb/execution/` |
| Results: 27 money measures; R only inside CT-29 exit records | BUILT | `qmb/src/qmb/results/measures.py:58-86` |
| Optimiser, robustness batteries, sweeps, analysis, synthetic (forex only) | BUILT | `qmb/src/qmb/optimize/`, `robustness/`, `sweep/`, `data/generate.py:175` |
| Sandbox runner for QML's Layer 2 | BUILT | `qmb/src/qmb/host/runner.py` (`run_sandbox`), `host/sandbox.py` |
| One landing function for a `backtest-result`, with three edges | BUILT (in `qmb/`) | `qmb/src/qmb/host/library_landing.py:1-80` |
| PR 204: host door, child process, silent runner, `app_op` special case for `qmb` | STACKED, open | `origin/build/wu4`, `git diff --stat` 16 files +1,113 -81 |
| The `backtest` toolset rows `run`, `status`, `results`, `compare`; `run` takes only `config_ref` and refuses | BUILT | `qmx-control/src/qmx_control/catalog.py:284-317`; `qmx-tools/src/qmx_tools/service.py:114-117` |
| Seven templates that declare `qmb-door` | BUILT as drafts | template census (this session) |

**PR 204, judged.** Keep: `backtest_and_land`'s landing and edges, the read-back by object id (`landed_backtest`), the principal stamp, the `operator` against `run:<id>` refs. Replace: the host-side door and child process (the mini-app runtime is the process boundary, and the child broke QMB's house rules and was POSIX-only for memory); the `app_op` special case for `qmb` (the job path of AD-202 serves every door); `<home>/backtests/<ref>.json` run configs (study specs in the Library replace them). Not merged as is; its landing code moves into `qmx-judge` (slice B3).

## 3. The app

**Folder.** `qmx-agents/apps/qmb/` (Level 0 LC-A0-16): `app.toml`, `server.py` (the MCP server the manifest requires, serving `capabilities` and `instruments`), `jobs/<kind>.py` (one per run kind, each `def run(inputs)`), `pyproject.toml` and `uv.lock` (the manifest requires both, `qmx_apps/manifest.py:330-332`), and nothing else. The jobs import the `qmb` library; the app spawns nothing of its own.

**Manifest, in outline** (field by field in `CONTRACTS.md` §1):

```toml
id = "qmb"
name = "QMB"
version = "1.0.0"
risk = "runs"
kind = "headless"
[entrypoints]
mcp = "server.py"
jobs = ["jobs/backtest.py", "jobs/sweep.py", "jobs/walk_forward.py", "jobs/robustness.py",
        "jobs/optimize.py", "jobs/whatif.py", "jobs/replay_check.py",
        "jobs/behaviour_check.py", "jobs/conformance.py"]
[operations.capabilities]
approval = "read"
state = "none"
[operations.instruments]
approval = "read"
state = "none"
[provides.backtest-result]
lander = "qmb-run"
[breaker]
max_errors = 3
restart = "backoff"
```

The `[provides.backtest-result]` schema is `qmx.qmb.result-bundle/1`. It declares no `stale_after`, because a result never goes stale (the field is optional and must be above zero when given, `qmx_apps/manifest.py` `Contract`, CHECKED). `lander` is part B's one new manifest field (`mini-app-core.md` §3); `restart = "backoff"` is Part C's core change 3, which QMB opts into (R1-B-09): the breaker counts every raised job over the process life (`qmx_apps/bootstrap.py:195-211`, `supervisor.py:817`, CHECKED), so QMB's jobs return a `failed` bundle for every domain failure and raise only on a crash, and a crash heals by restart instead of stopping research until someone clicks.

**Doors.**

| Door | How it reaches QMB | Who | Waits |
| --- | --- | --- | --- |
| `backtest_run` row (core toolset `backtest`, default on the copilot) | calls `ControlService.app_job("qmb", "backtest", inputs=request, principal=chat)` on a background thread | the copilot, agents with the toolset, REST | up to `[qmb] agent_wait_s` (240 s), then answers the run id; the agent polls `backtest_status` |
| `app_op {app: qmb, job: backtest, inputs}` | the supervisor's `run_job` | workflows | the whole job; the node takes no engine slot (engine AD-58) |
| the Lab's `QmbPort` | its default adapter is the same `app_op` (Lab AD-5, amended) | the Lab | as `app_op` |
| AD-46 `apps.job` | a remote home's supervisor `run_job` | This PC asking a server-homed tester | as `app_op`; an unreachable home waits `placement` |
| `app:qmb` tools (`capabilities`, `instruments`) | supervisor `call` | the copilot (home preset lists `app:qmb`, LC-A0-17) | under the 30 s call timeout, answers in milliseconds |

The rows `backtest_status`, `backtest_results` and `backtest_compare` are reshaped to read the core: status from the try rows of that run id, results from the landed `backtest-result` (PR 204's `landed_backtest`), compare as a parity diff of two results' trade lists and measures by object id (fixes "compare reads only old artifacts", handoff "Smaller gaps").

**Out of the box.** The first-start card's one click enables QMB, the MIS and the practice node (Level 0 AD-33). QMB's first run needs data: a run with none refuses at open and names each missing month and the template that downloads it (LD-06).

## 4. Inside QMB: rebuild, extend, keep

Every row names the files it touches and the check that proves it. "Unit" means a compiled unit hosted through Part A's unit door (`construct_unit`, `HostedUnit.on_instant -> UnitStep`), never `construct_bot`, which refuses a unit's format 3 intent (Part A BR-A4, run; R1 A-C3).

| Part | Verdict | What it does | Touches | Check |
| --- | --- | --- | --- | --- |
| Typed-partition entry into the trading replay | **new** | `execute_recorded_replay_request` takes the run folder's typed partitions (by fingerprint) as its source, beside today's CT-10 receipts path | `qmb/host/replay_execution.py:68`, `:120`, `:762-806` | a fixture bot trades over two typed months and its trade list equals the receipts path's on the same rows |
| Execution inputs as data | **new** | the run request names fill, cost, slippage, carry and margin adapters with versions, and the instrument records; QMB builds `BoundExecution` from them; `BookAdmissionContext` stays for the Book path only | `qmb/execution/binder.py`, `adapters.py`; `host/replay_request.py` | the 38 fixture tests still pass; a request built only from JSON trades the fixture bot |
| The shared unit handler | **new** | one run-slice handler over a `HostedUnit`: `run_slice`'s five hooks feed the read surfaces, call `on_instant`, pass intents to the host's execution port and rows to the journal writer; the node runtime imports the same file (R1-L0-02) | `qmb/host/` new `unit_handler.py`; `runloop/loop.py` unchanged | the dummy trades through it in QMB; Part C's runtime tests drive the same handler |
| Runner that trades a unit | **rebuild** (replaces `silent`) | loads the unit document and pinned blocks from the run folder through Part A's one block loader (AD-47), compiles, checks the compiled fingerprint equals the request's, builds the `HostedUnit` with `construct_unit` and drives the shared handler with the unit's risk socket | `qmb/host/` new `unit_runner.py` | the dummy unit trades a recorded month and lands; a fingerprint mismatch lands a `failed` result |
| Windowed reader | **rebuild** | per stream a window of the unit's derived warm-up (`derive_horizon`) plus its declared lookback; frames are views into the window, never whole-history copies; no step cap | `qmb/host/replay.py:540-606`; Part A's read surface (`qml` `MappingReadSurface`, `evidence.py:875-885`) | peak memory (tracemalloc) for 10,000 and 200,000 steps differs by less than a setting (default 10%); a 20-year 1-minute run completes on This PC |
| Fidelity | **extend** | quotes (ticks, or a bid and an ask bar series), trades (prints with aggressor side, a declared spread model, label `fidelity = trades`), bars (a declared spread model and a bar-path fill rule, label `fidelity = bars`); "fidelity" is what QMB replays and maps onto Part A's data levels as bars 1, quotes 2, trades 4 (R1-B-11) | `replay.py:608-626`; `runloop/bars.py` | one golden per fidelity on the dummy unit |
| Bars from ticks in the venue's day | **new** | daily and higher bars close at the instrument record's day boundary (for example 17:00 New York at most FX CFD brokers) | `runloop/bars.py` | a week of ticks gives the venue's daily closes, not UTC midnight ones |
| Gap fills | **new rule** | a stop or limit that a gap jumps fills at the first tradable price after the gap; the loss is the R it was | `qmb/execution/fill.py` | a weekend-gap fixture records -1.7R where the stop was 1R away |
| Lot rounding | **change** | round down to the lot step; below the minimum lot the order is skipped with a reason; the residue is journaled in R; the filled quantity always equals the sizer receipt's quantity after this rounding (CA-03) | the unit socket host in QMB; `book_handler.py` sizing path untouched for the Book | a size of 0.037 lots with step 0.01 trades 0.03 and journals the 0.007 residue; 0.004 lots skips; every fill of the dummy's run equals its receipt's quantity after rounding (B5b, B6) |
| Costs | **extend** | cost profile per (broker, account type, instrument, hour of week) read from the market journal's `minute` rows; with fewer than a setting's fills (default 50) the result is labelled `costs_uncalibrated` | `qmb/execution/cost.py`, `spread.py`, `slippage.py` | two runs on the same data with two profiles differ only in costs; the label appears with an empty journal |
| Carry | **new** | swap long and short with the triple day, index financing, perps funding at each funding time from recorded rates, index dividends: scheduled cash events at venue time from the instrument record and the funding series | `qmb/execution/financing.py`; a funding source on the data recipe | a held position through a Wednesday rollover carries three days of swap; a perp held 24 h pays three 8-hour fundings |
| Futures | **new** | replay contract by contract from the card's stitching record; the roll is a `data_event` the unit sees and acts on with its exits; at expiry the instrument record's action applies (Part C's records) | `replay.py`, `runloop/stream.py` | a two-contract fixture shows the roll event and no back-adjusted price |
| Margin and liquidation | **new port** | buying power from the account record's leverage; a position past maintenance margin on mark price is liquidated at the venue's rule; values from records | `qmb/execution/risk.py` (port) | a perp fixture liquidates at the record's maintenance level |
| Data holes | **new** | a preflight counts missing minutes per read against the instrument's calendar; a hole longer than a setting (default 3 bars of the unit's bar spec) inside open time fails the run (a `failed` bundle naming the hole) unless the study allows gaps, and then the unit sees a `data_event` gap and the result lists it | `qmb/data/gap_check.py` (EXISTS), the runner | a three-day hole in an open market fails by default and runs with `allow_gaps` |
| Results | **extend** | per trade: money, R, MAE and MFE in R, costs split, entry and exit receipts (reading ids, versions and ages), tuned values in force, placeholder blocks used; per run: measures in money and R, slices by session and by readings state, the daily R stream, `zero_trades`, `costs_uncalibrated` | `qmb/results/measures.py`, `ct29.py`, `ct32.py` | the 27 money measures are unchanged on the fixture; R measures match CT-29's `realized_r` |
| Motion | **wire** | calibrated numbers move inside the replay exactly as live; `motion = both` runs twice and reports both | runner; Part A's motion engine | the dummy unit's one moving number moves in the journal's `calibration` rows |
| Synthetic series | **extend** | the generator takes the instrument record's class | `qmb/data/generate.py:175` | a crypto perp request no longer gets the forex-CFD generator |
| Determinism | **keep and prove** | sorted iteration, seeded randomness, exact money; a rerun matches | everywhere | the conformance pack's reruns |
| Priority | **new, in the app** | the app lowers its own process priority at start | `apps/qmb/server.py` and each job's start | the process's priority class reads below normal on Windows |
| Optimiser, robustness, sweeps, walk-forward, what-if computations, ledger lines, fingerprints | **keep, wrap as jobs** | each becomes a job over the same request shape; every candidate, cell or rerun that can improve a result is its own counted try | `qmb/optimize/`, `robustness/`, `sweep/`, `analysis/` | existing tests pass; a sweep of 6 cells lands 6 try rows |

**The behaviour check job** (`behaviour_check`, Part A's checker layer G, R0-03; slices B5b and B6, R1-B-01). It runs QML's unchanged `evaluate_layer2` in QMB's sandbox runner and the behaviour report beside it (trade count or the declared "may not trade on this slice", each exit kind fired or unfired, a constant signal, a shuffled-day control) on a recorded slice of at least the derived warm-up plus a margin (setting, default 20% more). Its result lands as Part A's `test-report` (`check = "qml-g/1"`, `compiled_fingerprint`, `safety`, `behaviour`, `run_id`; A CONTRACTS §3.3) linked `tests` to the unit version. The lander runs it first, on the same tester, whenever a run's unit has no such record for its compiled fingerprint, and opens the run only on a passing safety verdict (`CONTRACTS.md` §3, the lander port).

**The nightly live-day replay** (`replay_check`, QB-23). Inputs: a unit deployment, a day, the quotes and bars the node recorded for its markets (pulled home by the records job, AD-210). It replays the day through the same compiled unit and returns a per-decision diff against the unit journal's `signal` rows: matched, live only, replay only, with the reason codes. A workflow template runs it after each market's session close (`workflows.md` §3).

## 5. Variants and versions

- **A new version.** Same app id `qmb`, higher version. Pinned calls to the old version fail with `pin_stale` (built, `supervisor.py:964-976`); unpinned calls use the active one.
- **A variant beside it.** Its own app id (for example `qmb-lean`), its own `app.toml` with `[provides.backtest-result] lander = "qmb-run"`. The lander records `tester = {app: "qmb-lean", version}`. Its provides are namespaced by app id (MA-10).
- **The default.** `[qmb] default_tester = "qmb@1.0.0"`. Changing it is refused unless a passing conformance `test-report` exists for that exact app and version (AD-206), so the default never silently moves to a tester that computes differently.
- **Comparing two testers.** `backtest_compare` on two results of the same request fingerprint shows the parity diff: trades only in one, price or size differences, measure differences.

## 6. Edge cases handled here, by id

QB-01, QB-02, QB-03, QB-04, QB-05, QB-07, QB-08, QB-14, QB-15, QB-16, QB-17, QB-18, QB-19, QB-20, QB-21, QB-23, QB-24 (each in the spine's case table with its handling), plus QB-06 and LD-13 consumed from Part C's instrument records (at-expiry action and dividend events), and RS-13 (gap through the stop, R as it fell).

## 7. What must not break

- QMB's own test suite (`pytest qmb` in `just ci`), its house rules (`test_qmb_scaffold.py`, whose banned words include `snapshot`, so the handler leaves `restore_unit` to the node) and the node's loop over `run_slice` (`qmn/src/qmn/loop/driver.py`), which must keep driving the same `run_slice` unforked, now through the shared unit handler.
- The Book path (`BookAdmissionContext`, formats 1 and 2) stays for the risk session.
- The `backtest-result` objects already landed stay readable (schema version 1 readers keep working; AD-6).

## 8. Numbers (starting defaults, all editable)

| Setting | Default | Origin |
| --- | --- | --- |
| `[qmb] agent_wait_s` | 240 | below the prompt cache's five minutes (WF-07); replaces LC-A0-21's 600 |
| `[qmb] default_tester` | `qmb@1.0.0` | the first shipped version |
| `[qmb] process_priority` | `below_normal` | QB-17 |
| `[qmb] default_window_start` | 2020-03-01 | research 12; any start allowed, never a cap |
| `[qmb] gap_bars_refuse` | 3 bars of the unit's bar spec | QB-18 |
| `[qmb] calibrated_min_fills` | 50 | GAP-0048 open until then |
| `[qmb] g_slice_margin` | 20% beyond the derived warm-up | AD-17 |
| `[qmb] window_memory_tolerance` | 10% | the windowed reader's test |
| app memory | unset (unlimited) | `qmx_apps/manifest.py:86-104` |
| breaker `max_errors` | 3 (shipped default), with `restart = "backoff"` (5 s doubling to 300 s, Part C's defaults) | by design, for monitoring (T3:1562); restart so a crash heals (R1-B-09) |
| conformance match | identical trade list for the same request fingerprint | determinism |

## 9. Growth seams

A new run kind is a job plus a field in the request's `params` (addable, AD-6). A new fidelity, fill model or carry adapter is an adapter QMB registers and lists in `capabilities`. A new tester is an app implementing `qmb/1` that passes the pack. A faster engine (a GA sampler, a compiled path) is a variant, never an edit to the core.
