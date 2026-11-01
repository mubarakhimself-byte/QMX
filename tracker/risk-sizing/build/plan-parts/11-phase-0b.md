## Put the one lander on every app job's path (B5)

Phase 0, the dummy unit end to end. Part B slice B5, mini-app core change 2 of Level 0 AD-33, Level 0 AD-34. Rulings 46 and 53. Real step none. Done when any app whose `provides` names a lander has every job opened and closed by it, and an app with no lander lands exactly as today.

**Depends on.** B1, B3.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`Contract.lander`), `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (the `Landers` port, open before queueing, fail on error, stop or death) and `qmx-agents/packages/qmx-apps/src/qmx_apps/artifacts.py` (a job answer's leave goes through `save` and carries the lander's name).
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (composes `qmb-run`, the sink routing and the `run_job` callable the lander uses for a behaviour check first).
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_landers.py`.

**Build.**

- [ ] Add the lander port to the supervisor's job path, so every door that starts a job crosses it.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] An app with no lander lands a plain `artifact` exactly as today. A fixture tester with `lander = "qmb-run"` lands a `backtest-result` and two `try` items. A job killed mid-run lands `status = killed`. Install refuses an unknown lander name. Run `cd qmx-agents && uv run pytest packages/qmx-apps/tests packages/qmx-host/tests -k "artifact or lander or app"`.

**Verify, live.**

@lane1
- [ ] Lane 2. A fixture app with no lander, one job. Save `b5-plain.log`. Pass when its artifact equals the parent's, field for field.
- [ ] Lane 3. A fixture tester with `lander = "qmb-run"`. Save `b5-land.log`. Pass when one `backtest-result` and two `try` items land.
- [ ] Lane 4. Kill the tester's process mid-job. Save `b5-killed.log`. Pass when the result lands with `status = killed`.
- [ ] Lane 5. Install an app that names an unknown lander. Save `b5-unknown.log`. Pass when install refuses by name.
- [ ] Lane 6. The apps and host suites at the parent and the head. Save `b5-suites.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds the lander adds to one fixture job.
- [ ] Probe. Lane 3 against lane 2, interleaved.
- [ ] Baseline. Lane 2's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that an app with no lander lands exactly as today.

@merge

## Compile the dummy and run it inside QML (A5)

Phase 0, the dummy unit end to end. Part A slice A5, Part A AD-103, AD-106 and AD-107, Level 0 AD-16 and AD-22. Midday ruling 1 and ledger U-06 (show a number moving by its declared rule). Real step none. Done when the dummy compiles to a stable fingerprint, runs over a recorded month inside QML, trades format-3 intents, and moves `min_trend_strength` by its rule from its own closed trades.

**Depends on.** A4.

**Files.**

- [ ] Create `qml/src/qml/compile/`, `qml/src/qml/protocol/unit.py` (`construct_unit`, `restore_unit`, `HostedUnit`, `UnitStep`) and `qml/src/qml/motion/`.
- [ ] Create `qml/tests/test_compile_dummy.py` and the recorded slice in `qml/tests/fixtures/slices/`. The slice is one month of EURUSD and XAUUSD M15 bid and ask, cut from Dukascopy data saved once in `D:/QMX-worktrees/unit-ship/data/` by the shipped download template (never from his real QMX folder), git-ignored if the licence requires. The committed fallback is a synthetic month labelled "not evidence".

**Build.**

- [ ] Write `compile`, which returns a `CompiledUnit` with its compiled fingerprint, the unit door, and the motion engine. A calibrated number moves one step, only after its `min_count` (20 for the dummy), shrunk toward its default by n/(n+k), and never mid-position.

**You see.**

- [ ] The first unit runs inside QML and tunes one of its own numbers from its own trades, with the receipt.

**Verify, unit.**

- [ ] The dummy compiles to a stable fingerprint. Two drives over the slice give identical `UnitStep` sequences. Entries are format-3 intents with quantity, protection and `not_before`. No entry before the derived warm-up. Exits only for positions it opened. `rsi_low` is stamped on every decision row. With a hand-fed `own_journal`, the calibration row for `min_trend_strength` appears at the first cadence instant after the 20th closed trade and not before it, and motion off leaves it at its default. `construct_bot` on the same factory refuses at the first sized intent (BR-A4 as a test). Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Compile the dummy in two separate processes. Save `a5-fingerprint.log`. Pass when both compiled fingerprints are equal.
- [ ] Lane 3. Drive the dummy twice over the recorded month. Save `a5-determinism.log`. Pass when the two step sequences are identical and no entry comes before warm-up.
- [ ] Lane 4. Feed `own_journal` 25 closed trades. Save `a5-motion.log`. Pass when the `min_trend_strength` row appears after trade 20 and not before, moves one shrunk step, and stays at its default with motion off.
- [ ] Lane 5. `construct_bot` on the dummy's factory. Save `a5-botdoor.log`. Pass when it refuses at the first sized intent.
- [ ] Lane 6. Read `rsi_low` from every decision row. Save `a5-rsilow.log`. Pass when every row carries it and its value changes over the month.
@menu

**Verify, perf.**

- [ ] Metric. Seconds to drive the dummy over one month of M15 on two markets.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap, on the unit runtime. The blast-radius fact is BR-A4, `construct_bot` fails closed at a unit's first sized intent.

@merge

## Let an app restart itself with back-off when it opts in (C-05a)

Phase 0, the dummy unit end to end. Part C slice C-05a, mini-app core change 3 of Level 0 AD-33. Rulings 35 (the node heals itself), 46 and 53. QMB opts in at B6, so three failed runs never stop research for good (R1-B-09). Real step none. Done when a tripped app with `[breaker] restart = "backoff"` starts again with back-off, every other app stays down as today, and a `money` app restarts only its active signed version.

**Depends on.** Nothing. It shares the supervisor file with two earlier PRs, so Appendix C keeps it from running beside them.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`Breaker.restart`, default `never`) and `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (the trip path).
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py`.

**Build.**

- [ ] Add the opt-in restart. The wait starts at 5 s and doubles to 300 s, both named settings. Each trip and each start is logged.

**You see.**

- [ ] Nothing yet. An app that crashes comes back by itself when it opted in.

**Verify, unit.**

- [ ] A tripped app with `restart = "backoff"` starts again after 5 s, and a second trip waits 10 s. An app without it stays down. A `money` app restarts only its active signed version. Run `uv run pytest qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py -q` and `uv run pytest qmx-agents/packages/qmx-apps/tests -q` with the shipped breaker tests unchanged.

**Verify, live.**

@lane1
- [ ] Lane 2. A fixture app with `restart = "backoff"`, tripped twice. Save `c05a-backoff.log`. Pass when it starts again after 5 s and then after 10 s, with each trip and start in its log.
- [ ] Lane 3. A fixture app without it, tripped. Save `c05a-stays.log`. Pass when it stays down, as at the parent.
- [ ] Lane 4. A fixture `money` app with a signed active version and an unsigned newer one, tripped. Save `c05a-money.log`. Pass when only the signed version restarts.
- [ ] Lane 5. Trip it eight times. Save `c05a-ceiling.log`. Pass when the wait reaches 300 s, holds there, and the restarts never stop.
- [ ] Lane 6. The shipped breaker tests at the parent and the head. Save `c05a-breaker.log`. Pass when they pass unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from a trip to the first restart.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails when the first restart takes more than 7 s (the 5 s wait plus 2 s).

**Review gate.** Lens edge-case. The blast-radius fact is that an app that sets no restart stays down after a trip, as `qmx_apps/supervisor.py:826-829` does today.

@merge

## Check a unit at every layer and name every problem at once (A6)

Phase 0, the dummy unit end to end. Part A slice A6, Part A AD-101 and AD-110, Level 0 AD-17. Midday ruling 12 (feedback while an agent writes, no false positives) and standing order 18. Real step none. Done when the checker runs layers A to F, returns `qmx.check/1` with counts first, runs layer G's functions over a `HostedUnit`, and the corpus gate is part of `just ci`.

**Depends on.** A5.

**Files.**

- [ ] Create `qml/src/qml/check/`, `qml/tests/test_check_layers.py`, `qml/tests/test_layer_g.py` and the known-good documents in `qml/tests/corpus/`.
- [ ] Write `qml/src/qml/door.py` with the five verbs.
- [ ] Edit `tools/ci.py` to run the corpus gate. `just ci` runs `uv run python tools/ci.py` (CHECKED, `justfile:208-209`), so the step goes there and not in the `justfile`.

**Build.**

- [ ] Write layers A to F, the result with counts first, grouping, `problem_set` and `no_progress`, the G collector over `HostedUnit`, the behaviour report, and the corpus gate.

**You see.**

- [ ] A unit gets every mistake named at once, and a unit that would trade nonsense is flagged before any backtest.

**Verify, unit.**

- [ ] The dummy checks with zero errors and its placeholder warnings. The three broken documents give exactly their three errors. The three twins pass the unchanged `evaluate_layer2`, and their reports name `one_side_only`, `exits_unfired` and `signal_constant`. The same problem set twice returns `no_progress: true`. A 200-problem document's first 2,000 characters hold the counts and the first errors (AG-15). Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Check the dummy. Save `a6-dummy.log`. Pass when it has zero errors and only its placeholder warnings.
- [ ] Lane 3. The three broken documents and the three twins. Save `a6-broken.log`. Pass when the broken documents give exactly their three errors and the twins' reports name `one_side_only`, `exits_unfired` and `signal_constant`.
- [ ] Lane 4. Add one error to a corpus document and run `tools/ci.py`'s corpus step. Save `a6-corpus.log`. Pass when the step fails and names the document.
- [ ] Lane 5. A 200-problem document. Save `a6-long.log`. Pass when its first 2,000 characters hold the counts and the first errors.
- [ ] Lane 6. The same problem set sent twice. Save `a6-noprogress.log`. Pass when the second answer carries `no_progress: true`.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for layers A to F on the dummy in a fresh process.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails above 8 s, the hook's budget (connections C4).

**Review gate.** Lenses verification-gap and edge-case. The blast-radius fact is that `evaluate_layer2` is unchanged and pure (Level 0 item 3).

@merge

## Run units through one handler and check their behaviour (B5b)

Phase 0, the dummy unit end to end. Part B slice B5b, Level 0 AD-5 (one run-slice handler for QMB and the node), R1-L0-02, R1-B-01, case CA-03. Ruling 22 (QMB's own depth). Real step none. Done when QMB runs a compiled unit through `qmb/src/qmb/host/unit_handler.py`, every fill's quantity equals the sizer receipt's after lot rounding, and layer G runs as QMB code.

**Depends on.** B4, A5, A6.

**Files.**

- [ ] Create `qmb/src/qmb/host/unit_handler.py` (`run_slice`'s five hooks over a `HostedUnit`, execution and journal ports injected, `own_position`, `own_journal` and readings fed from the run).
- [ ] Create `qmb/src/qmb/host/unit_runner.py` (loads the document and pinned blocks through Part A's loader, checks the compiled fingerprint, builds the `HostedUnit` with `construct_unit`, results with R and the `zero_trades` label) and `qmb/src/qmb/host/behaviour.py` (layer G in QMB's sandbox over the derived warm-up plus `[qmb] g_slice_margin`).
- [ ] Create `qmb/tests/test_unit_handler.py`, `qmb/tests/test_unit_runner.py` and `qmb/tests/test_behaviour_check.py`.

**Build.**

- [ ] Write the handler, the runner and the behaviour check. QMB's banned words stay out of the new files (`qmb/tests/test_qmb_scaffold.py:47` bans `snapshot`), so the node and not the handler calls `restore_unit`.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] The dummy trades through the handler over a one-month EURUSD fixture. Every fill's quantity equals its intent's sizer quantity rounded down to the lot step. Exits only for positions it opened. No entry before warm-up. A compiled-fingerprint mismatch refuses at start. No file under `qmb/src/qmb/host/` imports `construct_bot`. The dummy and its three twins give behaviour reports naming `one_side_only`, `exits_unfired` and `signal_constant`. Run `uv run pytest qmb/tests/test_unit_handler.py qmb/tests/test_unit_runner.py qmb/tests/test_behaviour_check.py qmb/tests/test_qmb_scaffold.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy over one month of EURUSD M15 through the handler. Save `b5b-trades.log`. Pass when it trades and every fill's quantity equals its sizer receipt's after lot rounding (CA-03).
- [ ] Lane 3. Start a run with a compiled fingerprint that differs from the document's. Save `b5b-mismatch.log`. Pass when it refuses before the first bar.
- [ ] Lane 4. The behaviour check on the dummy and its three twins. Save `b5b-behaviour.log`. Pass when each twin's report names its fault and the dummy's names none.
- [ ] Lane 5. Grep `qmb/src/qmb/host/` for `construct_bot`. Save `b5b-nobot.log`. Pass when no file imports it.
- [ ] Lane 6. Seed a position the unit did not open. Save `b5b-own.log`. Pass when the unit never closes it.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the one-month run.
- [ ] Probe. Lane 2, and the fixture bot over the same month through B4's path, interleaved.
- [ ] Baseline. The fixture bot's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on the unit runtime and the money path. The blast-radius fact is that `run_slice` drives any handler through its five hooks (`qmb/src/qmb/runloop/loop.py:778-801`, Level 0 item 15), which is why one handler serves QMB and the node.

@merge

## Store units in the Library and land the dummy on first start (A7)

Phase 0, the dummy unit end to end. Part A slice A7, Part A AD-111, AD-112 and AD-118, Level 0 AD-29 (the Library changes only by addition). Rulings 51 and 52. Real step none. Done when a unit he publishes has passed every check, a refusal lists every problem with the first message kept, and a fresh QMX folder holds exactly one dummy draft whose check has zero errors.

**Depends on.** A6.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/__init__.py`, `qmx-agents/packages/qmx-library/src/qmx_library/store.py` (the publish check call), `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`, `qmx-agents/packages/qmx-library/src/qmx_library/kinds/component.schema.json` and `qmx-agents/packages/qmx-library/src/qmx_library/kinds/test-report.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (checker registration at composition) and `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` (the dummy's landing, find-then-put on the draft ref only, the pattern of `qmx_library/migrate/from_apps.py:52-57`, never `place`'s merge onto main).
- [ ] Create `qmx-agents/packages/qmx-tools/src/qmx_tools/gather.py` (builds the check context from the Library, and reads the fixture records with a warning until C-02 lands).
- [ ] Add tests in `qmx-library`, `qmx-control` and `qmx-host`.

**Build.**

- [ ] Every problem on a refusal, the first message kept as its head. Kind-file `checks`. The `unit` kind at schema version 2 with the generated shape and a publish check. The `component` entry face with its put check. The `test-report` fields for layer G. The host registers `qml.unit/1` and `qml.entry/1`.
- [ ] On first start the host lands the dummy as a `unit` draft once per store, keyed by its fingerprint. Its blocks are QML's own. The broken twins stay test fixtures and never land.

**You see.**

- [ ] The dummy unit waits in his Library as a draft on first start, with its checks passed and one yes to publish. A unit he publishes has always passed every check.

**Verify, unit.**

- [ ] BR-A1's patched-copy run as tests. The Library suite (101 tests) and the control suite pass. A broken unit saves as a draft with its shape problems listed, then refuses to publish with every A to F problem. The dummy publishes. A mini app's provides component still saves unchecked. An entry draft with a broken face refuses on save. A store with no registered checker refuses an entry save with `checker_unavailable`. A fresh QMX folder made by `make_new` lists exactly one `dummy-trend-pullback` draft, and a second start adds nothing. Run `cd qmx-agents; uv run pytest packages/qmx-library/tests packages/qmx-control/tests packages/qmx-host/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A fresh QMX folder made by `make_new`, opened by the host, started twice. Save `a7-firststart.log`. Pass when it lists exactly one `dummy-trend-pullback` draft with zero check errors after both starts.
- [ ] Lane 3. Save a broken unit, then publish it. Save `a7-publish.log`. Pass when it saves as a draft with its shape problems and the publish refuses with every A to F problem.
- [ ] Lane 4. A mini app's provides component, then an entry draft with a broken face. Save `a7-component.log`. Pass when the first saves unchecked and the second refuses on save.
- [ ] Lane 5. A store with no registered checker saving an entry. Save `a7-nochecker.log`. Pass when it refuses with `checker_unavailable`.
- [ ] Lane 6. The 28 shipped lines that compare message text (Level 0 item 6). Save `a7-messages.log`. Pass when they pass unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one unit publish with the full check.
- [ ] Probe. Lane 3's publish of the dummy.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is BR-A1, the Library's 101 tests and the control suite pass with the patched kinds.

@merge

## Make QMB the first mini app and backtest the dummy end to end (B6)

Phase 0, the dummy unit end to end. Part B slice B6, Part B AD-201 to AD-203, Level 0 AD-34. Rulings 22, 23, 25 and 43 (QMB as a tool and the first mini app). Real step none. Done when the copilot, a workflow's `app_op` and the Lab's adapter each start a `backtest` job that trades the compiled dummy and lands a `backtest-result` with money and R, a core run id and its try rows.

**Depends on.** B1, B3, B4, B5, B5b, A7, C-05a.

**Files.**

- [ ] Create `qmx-agents/apps/qmb/` with `app.toml` (`[breaker] restart = "backoff"`, kind `headless`), `server.py` (`capabilities`, `instruments`), `jobs/backtest.py`, `jobs/behaviour_check.py`, `jobs/conformance.py` (a stub that refuses with "conformance pack arrives in B12"), `pyproject.toml`, `uv.lock` and `tests/`. Every job returns a `failed` bundle for a domain failure and raises only on a crash.
- [ ] Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py` (open's G lookup by compiled fingerprint, the behaviour check first through the injected `run_job`, its `test-report` and its `check` try).
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (`backtest_run`, `backtest_status`, `backtest_results`, `backtest_compare` reshaped, `[qmb] agent_wait_s`).
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` (one click enables `qmb`) and `tools/test_all.py` (the app's tests run in `just ci`).
- [ ] The default copilot home lists `app:qmb` (LC-A0-17). First check whether a chat already lists `app:qmb` operations, since the harness serves every running app's operations (`qma-harness/src/qma/harness/tools.py:536-557`). If it does, change nothing there. If not, add enabled first-party apps to the fallback in `qmx-agents/packages/qma-harness/src/qma/harness/surface.py` (`home_preset`, `:484-489`) and log the call.

**Build.**

- [ ] Write the app and its jobs, reshape the four `backtest` rows without adding one, and run the behaviour check first when the unit has no G record.

**You see.**

- [ ] He asks the copilot "backtest the dummy unit on EURUSD for January" and gets a run number and the result in money and R. The result is in his Library with who ran it.

**Verify, unit.**

- [ ] The dummy over a one-month EURUSD fixture lands a `backtest-result` whose trades carry R and whose filled quantities equal the sizer receipts' after lot rounding. A unit with no G record runs `behaviour_check` first, and a second run of the same fingerprint skips it. A failing safety verdict refuses the run with the report linked. A fingerprint mismatch lands a `failed` result and `job_errors` stays 0. After a forced crash trips the breaker, the lander fails the running job and QMB starts again by back-off. `backtest_run` returns the run id after the wait. An `app_op` fixture lands the same object. The tool count test keeps `backtest` at 4 (`qmx-tools/tests/test_tools.py:374-376`). Run `uv run pytest qmb/tests/test_unit_runner.py qmx-agents/packages/qmx-tools/tests qmx-agents/packages/qmx-judge/tests qmx-agents/apps/qmb/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. On a fresh throwaway folder with the fixture month (or January from `D:/QMX-worktrees/unit-ship/data/`), ask the copilot on `haiku` "backtest the dummy unit on EURUSD for January". Save `b6-copilot.log`. Pass when the answer has a run number and the result's trades carry money and R.
- [ ] Lane 3. The same request from a workflow's `app_op` step. Save `b6-appop.log`. Pass when it lands a result with the same trade-list hash.
- [ ] Lane 4. A unit with no G record, run twice. Save `b6-gfirst.log`. Pass when the first run lands one `test-report` and one `check` try before the backtest opens, and the second run skips them.
- [ ] Lane 5. Force a crash that trips QMB's breaker mid-run. Save `b6-crash.log`. Pass when the lander fails the running job, QMB starts again by back-off, and the next run lands.
- [ ] Lane 6. A run with a compiled-fingerprint mismatch. Save `b6-mismatch.log`. Pass when a `failed` result lands and the app's `job_errors` stays 0.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from the copilot's ask to the run id, and from the run id to the landed result.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. The run id or its handle comes back within `[qmb] agent_wait_s` (240 s). No fail rule on the run itself.

**Review gate.** Lenses edge-case and adversarial. The blast-radius fact is that the shipped tool count test keeps `backtest` at 4.

@merge

## Let the copilot write and check a unit (A8)

Phase 0, the dummy unit end to end. Part A slice A8, Part A AD-117, Level 0 AD-17 and AD-31. Midday rulings 8 (the copilot can do what agents can) and 12. Real step none. Done when the `unit` and `blocks` toolsets with seven rows are on the default copilot surface, the harness derives its domain groups from the catalog, `python -m qmx_tools.unit_check` exits 0 or 1 with every problem, and the `build-unit` skill exists.

**Depends on.** A7.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qma-harness/src/qma/harness/tools.py` (`:668`, derive the domain groups from the catalog) and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (`unit_new`, `unit_check`, `unit_explain`, and the four `blocks_*` rows stubbed until A11).
- [ ] Create `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py` and `qmx-agents/plugin/skills/build-unit/SKILL.md`, and regenerate `qmx-agents/plugin/plugin.manifest.json`.
- [ ] Add tests in `qma-harness`, `qmx-tools` and `qmx-control`, including the copilot-surface parity test and the test that the unit path writes no `bot` or `strategy`.

**Build.**

- [ ] Add the two toolsets and their rows, the one-line harness change, the entry point, and the skill, which tells an agent to check, read every problem, fix and check again.

**You see.**

- [ ] He can ask the copilot for a unit and watch it get written and checked, every problem fixed in a loop.

**Verify, unit.**

- [ ] BR-A2's patched-copy run as tests. The harness, tools and control suites give their baseline results. A copilot chat's surface lists the seven rows. `python -m qmx_tools.unit_check qml/src/qml/unit/templates/dummy-trend-pullback.json` prints a passing result and exits 0, and a broken document exits 1 with every problem. `test_the_shipped_plugin_manifest_is_what_the_code_generates` passes. Run `cd qmx-agents; uv run pytest packages/qma-harness/tests packages/qmx-tools/tests packages/qmx-control/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A copilot chat on `haiku` on a throwaway folder lists its tools. Save `a8-surface.log`. Pass when the seven rows are on the default surface.
- [ ] Lane 3. `python -m qmx_tools.unit_check` on the dummy and on a broken document. Save `a8-cli.log`. Pass when the first exits 0 with a passing result and the second exits 1 with every problem.
- [ ] Lane 4. Ask the copilot on `haiku` "write a unit like the dummy that trades XAUUSD only". Save `a8-write.log`. Pass when it calls `unit_new` and `unit_check`, fixes every problem in a loop, and saves a draft whose check has zero errors.
- [ ] Lane 5. The plugin manifest test at the head. Save `a8-manifest.log`. Pass when it passes.
- [ ] Lane 6. Grep the unit path for writes of the `bot` or `strategy` kinds. Save `a8-nobot.log`. Pass when the pinned test passes and the grep finds none.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one `unit_check` from the command line.
- [ ] Probe. Lane 3 in a fresh process.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails above 8 s, the hook's budget.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is BR-A2, the harness suites give their baseline results with the derived domain groups.

@merge

## Keep the unit's journal in every QMB run and prove phase 0 (B9)

Phase 0, the dummy unit end to end, and its closing proof. Part B slice B9, Level 0 AD-22 and AD-27, cases MIS-10, JR-04, R1-A-01 and R1-B-10. Midday ruling 1 and ledger U-02, U-05 and U-06 ("does a unit actually make sense?"). Real step none. Done when a run's `signal`, `calibration`, `state`, `guard`, `trade` and `data_event` rows land in the result's `journal/*` blobs, and lanes 2 to 4 show the whole chain on one fresh folder.

**Depends on.** B6, B8, A8, A5.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_runner.py`, `qmb/src/qmb/results/` and `qmx-agents/apps/qmb/jobs/backtest.py`.
- [ ] Create `qmb/tests/test_run_journal.py`.

**Build.**

- [ ] Write every decision as one `signal` row (taken, skipped with its reason, or blocked) with its readings' value, source and version, plus the calibration, state, guard, trade and data-event rows, through B8's writer. A unit-journal row's record id is its decision row id, so a re-run slice writes nothing twice.
- [ ] Report motion on and off when the request asks for both.

**You see.**

- [ ] A backtest result now has the unit's journal. The copilot can say what the dummy did on a given day, why it skipped, and when its trend floor moved. The Journal tab itself is the UI session's.

**Verify, unit.**

- [ ] Every decision is one `signal` row with its readings' value, source and version. `rsi_low` moves every bar. A run over EURUSD and XAUUSD long enough to close the dummy's `min_count` trades on each market (default three months of fixture data, and the test first asserts that count, so a short window fails loudly) shows at least one `calibration` row for `min_trend_strength`. `motion = both` reports both. Run `uv run pytest qmb/tests/test_run_journal.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. The authoring door. On a fresh throwaway folder, run `python -m qmx_tools.unit_check` on the dummy draft the first start landed, then publish it as principal `operator`. Save `b9-author.log`. Pass when the check has zero errors and the publish succeeds.
- [ ] Lane 3. The backtest. Ask the copilot on `haiku` to backtest the dummy on EURUSD and XAUUSD over three months (fixture months, or real ones from `D:/QMX-worktrees/unit-ship/data/`). Save `b9-backtest.log`. Pass when a `backtest-result` lands with trades in money and R, a core run id and its try rows.
- [ ] Lane 4. The number that moved. Read that result's journal blobs by script. Save `b9-motion.log`. Pass when the script first counts at least 20 closed trades on each market (FAIL otherwise) and then finds a `calibration` row for `min_trend_strength` with its old value, new value and receipt.
- [ ] Lane 5. The same request with `motion = both`. Save `b9-both.log`. Pass when both runs are reported and they differ only after the first calibration row.
- [ ] Lane 6. Run the same request twice. Save `b9-rerun.log`. Pass when the journal rows carry the same record ids and nothing lands twice.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the three-month, two-market run with the journal on and with it off.
- [ ] Probe. Lane 3, and the same run with journal writes stubbed, interleaved.
- [ ] Baseline. The run with the journal off, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap, because journals record trades. The blast-radius fact is that B8's writer drops a repeated row by record id, so a re-run slice writes its decisions once (R1-B-10).

@merge
