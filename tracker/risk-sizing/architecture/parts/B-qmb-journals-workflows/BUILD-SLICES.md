# Part B build slices

Ordered, PR-sized slices a builder takes one at a time. Every PR keeps the shipped tests green (`just ci` on Windows, STATE midday ruling 52); a shipped test that a slice changes on purpose is named in that slice. Commands run from the repository root unless they say `qmx-agents`. "Part A" and "Part C" dependencies name their slice by what it delivers, because their slice ids are theirs. Amended after R1 (`architecture/review/R1-FIXES-X1-B.md`): B5b is new, B18 is three slices, and B6, B7, B8, B9, B13 to B16, B19 and B20 changed.

**The smallest thing that runs end to end** is B6: the copilot, a workflow or he asks QMB to backtest the dummy unit on one month of EURUSD, and a `backtest-result` lands with money and R, a core run id and its try rows, readable by `backtest_results`. B1 to B5b are what B6 needs; everything after B6 widens it. Nothing in B1 to B15 waits on the trading node.

## B1. Jobs take inputs and return a result

- **Goal.** A workflow's `app_op` can tell an app's job what to do and get its answer back (mini-app core change 1 of Level 0 AD-33's six).
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (`run_job`), `bootstrap.py` (`run_job`, `jobs`), `qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/app_op.py`, `qmx-agents/packages/qmx-control/src/qmx_control/service.py` (`app_job` passes `inputs` and `principal`); new test `qmx-agents/packages/qmx-engine/tests/test_app_op_inputs.py` (from `scratchpad/l1b/tests/test_job_inputs.py`).
- **Depends on.** nothing.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_app2a_app_op.py packages/qmx-engine/tests/test_app2b_routing.py packages/qmx-engine/tests/test_app_op_inputs.py packages/qmx-apps/tests/test_apps.py`, then `just ci`. Already proven on an overlay copy: 36 passed (`mini-app-core.md` §5).
- **He sees.** Nothing yet on screen; a workflow can now pass a request to an app.

## B2. Example apps that run, tested in CI

- **Goal.** Every example and first-party app installs, starts and answers (MA-03), and no shipped app or template takes a core name (CA-12).
- **Files.** `examples/apps/macro-daily-bias/macro_bias.py`, `examples/apps/weekend-watcher/server.py` (rewritten on the current runtime), `examples/apps/README.md`; new `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` (installs each folder in `examples/apps/` and `qmx-agents/apps/`, calls each operation with its example input, runs each job once, and asserts no app id, provides name or template id equals a core kind, catalog row, toolset or template id).
- **Depends on.** B1 (jobs with fixture inputs).
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-apps/tests/test_shipped_apps.py`, then `just ci`.
- **He sees.** The four example apps start from the Apps screen without crashing.

## B3. The scoring core package and the result's new shape

- **Goal.** `qmx-judge` exists with the run record and the lander (`open`, `close`, `fail`), the `try` kind and `backtest-result` version 2; PR 204's `land` moves in and its old home goes in the same PR.
- **Files.** new `qmx-agents/packages/qmx-judge/` (`pyproject.toml`, `src/qmx_judge/landing.py`, `runs.py`, `tries.py`, tests); `qmx-agents/packages/qmx-library/src/qmx_library/kinds/try.schema.json` (new), `backtest-result.schema.json` (version 2); `qmb/src/qmb/host/library_landing.py` and `qmb/tests/test_library_landing.py` (moved into `qmx-judge`); `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` and `qmx-tools/tests/test_tools.py` (import from `qmx_judge`); workspace `pyproject.toml` and `uv.lock`.
- **Depends on.** nothing.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-judge packages/qmx-library/tests packages/qmx-tools/tests` (the lander with a fake tester: open lands one `try`, close lands one `backtest-result` with its three edges, fail lands `status = killed` with no measures, a second close changes nothing), then `just ci`.
- **He sees.** Nothing yet.

## B4. QMB can trade from Library data and a request written as data

- **Goal.** The trading replay takes typed partitions and execution inputs named in a request (handoff "What QMB needs" items 1 and 2).
- **Files.** `qmb/src/qmb/host/replay_execution.py` (a typed-partition entry beside the CT-10 receipts path), `qmb/src/qmb/host/replay_request.py`, `qmb/src/qmb/execution/binder.py`, `adapters.py`; tests `qmb/tests/test_typed_execution.py`.
- **Depends on.** nothing (the fixture bot proves the path; units come with the shared handler, the next slice but one).
- **Verify.** `uv run pytest qmb/tests/test_typed_execution.py qmb/tests/test_replay_execution.py qmb/tests/test_qmb_scaffold.py` (the fixture bot's trades over two typed months equal the receipts path's on the same rows; a request built only from JSON trades it; house rules hold), then `just ci`.
- **He sees.** Nothing yet.

## B5. The lander joins the supervisor

- **Goal.** Any app whose `provides` names a lander has every job opened and closed by it (mini-app core change 2).
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`Contract.lander`), `supervisor.py` (the `Landers` port: open before queueing, fail on error, stop or death), `artifacts.py` (a job answer's leave goes through `save`; the landing carries the lander name); `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (composes `qmb-run`, the sink routing and the `run_job` callable the lander uses for a behaviour check first); tests `qmx-agents/packages/qmx-apps/tests/test_landers.py`.
- **Depends on.** B1, B3.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-apps/tests packages/qmx-host/tests -k "artifact or lander or app"` (an app with no lander lands a plain `artifact` exactly as today; a fixture tester with `lander = "qmb-run"` lands a `backtest-result` and two `try` items; a job killed mid-run lands `status = killed`; install refuses an unknown lander name), then `just ci`.
- **He sees.** Nothing yet.

## B5b. The shared unit handler and the behaviour check

- **Goal.** Units run through Part A's unit door in one run-slice handler that QMB and the node both import (R1-L0-02, A-C3); layer G runs as QMB code (R1-B-01); the sizer's quantity reaches the fill (CA-03).
- **Files.** new `qmb/src/qmb/host/unit_handler.py` (`run_slice`'s five hooks over a `HostedUnit` its host built; execution and journal ports injected; the read surfaces `own_position`, `own_journal` and readings fed from the run), `qmb/src/qmb/host/unit_runner.py` (loads the unit document and pinned blocks from a run folder through Part A's block loader, checks the compiled fingerprint, builds the `HostedUnit` with `construct_unit`, drives the handler over typed partitions; results with R and the `zero_trades` label), `qmb/src/qmb/host/behaviour.py` (Part A's G collector and behaviour report in QMB's sandbox runner over a recorded slice of the derived warm-up plus `[qmb] g_slice_margin`); tests `qmb/tests/test_unit_handler.py`, `test_unit_runner.py`, `test_behaviour_check.py`. QMB's banned words stay out of the new files (`qmb/tests/test_qmb_scaffold.py:47` bans `snapshot`, so the node, not the handler, calls `restore_unit`).
- **Depends on.** B4; Part A's compiler, unit door and motion engine (its first end-to-end slice) and layer G's functions (its checker slice).
- **Verify.** `uv run pytest qmb/tests/test_unit_handler.py qmb/tests/test_unit_runner.py qmb/tests/test_behaviour_check.py qmb/tests/test_qmb_scaffold.py` (the dummy over a one-month EURUSD fixture trades through the handler; every fill's quantity equals its intent's sizer quantity rounded down to the lot step; exits only for positions it opened; no entry before warm-up; a compiled-fingerprint mismatch refuses at start; no file under `qmb/src/qmb/host/` imports `construct_bot`; the dummy and its three broken twins give behaviour reports naming `one_side_only`, `exits_unfired` and `signal_constant`), then `just ci`.
- **He sees.** Nothing yet.

## B6. QMB, the first mini app: the dummy unit backtested end to end

- **Goal.** The smallest run that works: a `backtest` job that trades a compiled unit, reached by the copilot's row, a workflow's `app_op` and the Lab's adapter, with the behaviour check run first when the unit has no G record.
- **Files.** new `qmx-agents/apps/qmb/` (`app.toml` with `[breaker] restart = "backoff"`, `server.py` with `capabilities` and `instruments`, `jobs/backtest.py`, `jobs/behaviour_check.py`, `jobs/conformance.py` stub that refuses "conformance pack arrives in B12", `pyproject.toml`, `uv.lock`; every job returns a `failed` bundle for a domain failure and raises only on a crash); `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py` (open's G lookup by compiled fingerprint, the behaviour check first through the injected `run_job`, its `test-report` with Part A's G fields and its `check` try); `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` and `qmx-tools/src/qmx_tools/service.py`, `functions.py` (`backtest_run`, `backtest_status`, `backtest_results`, `backtest_compare` reshaped; `[qmb] agent_wait_s`); the first-start card's one click enables `qmb`; the copilot home preset lists `app:qmb` (LC-A0-17). The shipped per-server tool count (`qmx-tools/tests/test_tools.py:374-376`) keeps `backtest` at 4: the four rows are reshaped, none is added.
- **Depends on.** B1, B3, B4, B5, B5b; Part A's Library additions (the `test-report` G fields, and the dummy unit landed on first start); Part C's opt-in restart core change.
- **Verify.** `uv run pytest qmb/tests/test_unit_runner.py qmx-agents/packages/qmx-tools/tests qmx-agents/packages/qmx-judge/tests qmx-agents/apps/qmb/tests` (the dummy unit over a one-month EURUSD fixture lands a `backtest-result` whose trades carry R and whose filled quantities equal the sizer receipts' after lot rounding; a unit with no G record runs `behaviour_check` first and lands one `test-report` and one `check` try before the `backtest` opens, and a second run of the same fingerprint skips it; a failing safety verdict refuses the run with the report linked; a compiled-fingerprint mismatch lands a `failed` result and the app's `job_errors` stays 0; after a forced crash trips the breaker, the lander fails the running job and QMB starts again by back-off; `backtest_run` returns the run id after the wait; the result reads back by id; an `app_op` workflow fixture lands the same object; the tool count test passes unchanged), then `just ci`. Live lane: on a fresh QMX folder with one month of Dukascopy EURUSD downloaded, ask the copilot "backtest the dummy unit on EURUSD for January" and save the answer.
- **He sees.** The copilot answers with a run number and the result: trades, money and R. The result is in the Library with "Who ran it".

## B7. The windowed reader and three fidelities

- **Goal.** Memory stays flat however long the run (QB-01); quotes, trades and bars replay as the card declares (QB-02); daily bars close in the venue's day (QB-21).
- **Files.** `qmb/src/qmb/host/replay.py` (windowed frames served through QML's kept `ReadSurface.at`, `qml/src/qml/protocol/__init__.py:112`), `qmb/src/qmb/runloop/bars.py`; tests `qmb/tests/test_windowed_reader.py`, `test_fidelity.py`.
- **Depends on.** B6.
- **Verify.** `uv run pytest qmb/tests/test_windowed_reader.py qmb/tests/test_fidelity.py qmb/tests` (peak memory for 10,000 and 200,000 steps within `[qmb] window_memory_tolerance`; one golden per fidelity; a week of ticks gives the venue's daily closes), then `just ci`.
- **He sees.** A twenty-year backtest on one-minute bars finishes on his PC.

## B8. The journal envelope, kinds and writer library

- **Goal.** One envelope and typed kinds; the in-process append path for journal records and store-kind series rows; record ids that survive a re-run; the read-only committed reader; staging months as journal partitions (AD-208, AD-209).
- **Files.** `packages/qmf-data/src/qmf/data/journal_envelope.py`, `journal_kinds/` (schemas per kind, `lifecycle` and `state` from Part A's shapes, `node_lifecycle`, the reading body's `source`), `journal_writer.py` (append, append_series, the record-id rule and repeat drop, the key-token rule, bundle mode, stage), `journal_reader.py` (the committed reader); `packages/qmf-data/src/qmf/data/store/engines/typed.py` (the `record` text column; the writer closes its file when a row is refused, fixing the shipped Windows refusal bug), `series.py` (the `journal-*` rule); tests `packages/qmf-data/tests/test_journal_writer.py`, `test_journal_partition.py` (from `scratchpad/l1b/tests/`), `test_refused_row.py` (from `scratchpad/l1b/refused_row_windows.py`), `test_committed_reader.py` (from `scratchpad/x1b/br_reader_truncates.py`).
- **Depends on.** nothing.
- **Verify.** `uv run pytest packages/qmf-data/tests` (already proven on an overlay: 584 passed plus the round trip; the refused-row test now returns a typed refusal on Windows; a second writer on a stream is refused; a refused append is never dropped silently; a slice's `signal`, `calibration` and `state` rows appended twice land once, and a repeat with a different body is kept out with a `determinism_break` warning; the committed reader leaves a stream with a line in flight byte for byte as it was, where the shipped reader truncated it; an id with `@` maps to its fixed token), then `just ci`.
- **He sees.** Nothing yet.

## B9. Every QMB run keeps the unit's journal

- **Goal.** A run's `signal` rows (taken, skipped with reason, blocked), `calibration`, `state`, `guard`, `trade` and `data_event` rows land in the result's `journal/*` blobs; motion on and off (MIS-10, JR-04, AD-22); the dummy's slow number moves on real trades.
- **Files.** `qmb/src/qmb/host/unit_runner.py`, `qmb/src/qmb/results/`; `qmx-agents/apps/qmb/jobs/backtest.py`.
- **Depends on.** B6, B8; Part A's motion engine for the dummy unit's moving numbers.
- **Verify.** `uv run pytest qmb/tests/test_run_journal.py` (every decision is one `signal` row with its readings' value, source and version; `rsi_low` moves every bar; a run over EURUSD and XAUUSD long enough to close the dummy's `min_count` trades on each market (the test window, default three months of fixture data, and the test first asserts that count, so a short window fails loudly) shows at least one `calibration` row for `min_trend_strength` from those trades, R1-A-01; `motion = both` reports both), then `just ci`.
- **He sees.** A result's "Journal" tab: what the unit did and why it skipped, and the moment its trend floor moved.

## B10. Realism: fills, sizes, costs, carry, margin, holes

- **Goal.** QB-03, QB-04, QB-07, QB-08, QB-16, QB-17, QB-18, RS-13, LD-13.
- **Files.** `qmb/src/qmb/execution/fill.py` (gap rule), `cost.py`, `spread.py`, `slippage.py` (profiles from the market journal; `costs_uncalibrated`), `financing.py` (swaps with the triple day, index financing, perps funding, dividends as cash events), `risk.py` (margin and liquidation port), `qmb/src/qmb/data/generate.py` (by class), `qmb/src/qmb/data/gap_check.py` (preflight), the unit runner (lot rounding, residue in R); `qmx-agents/apps/qmb/server.py` (priority).
- **Depends on.** B6, B9; Part C's instrument records (carry, dividends, margin, calendars).
- **Verify.** `uv run pytest qmb/tests/test_realism.py` (a weekend gap records -1.7R where the stop was 1R; 0.037 lots trades 0.03 with the residue journaled and 0.004 skips; a Wednesday rollover carries three days; a perp held 24 h pays three fundings; a three-day hole lands a `failed` result unless `allow_gaps`; a crypto request gets the crypto generator; the app's priority reads below normal), then `just ci`.
- **He sees.** Results that say "costs uncalibrated" until real fills exist, and losses through gaps shown as they were.

## B11. Futures and the data cards' new facts

- **Goal.** QB-05, LD-03, LD-04, LD-16, LD-01: contract-by-contract futures replay; `dataset` version 2 (source clock, seams, stitching, calendar); the stamp check at import; the shared data-quality check.
- **Files.** `qmx-agents/packages/qmx-library/src/qmx_library/kinds/dataset.schema.json` (version 2); `packages/qmf-data/src/qmf/data/importers/` and the download templates' scripts (stamp check, source clock, seams); `qmb/src/qmb/host/replay.py`, `runloop/stream.py` (rolls as events); new `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/data-quality/`.
- **Depends on.** B7.
- **Verify.** `uv run pytest packages/qmf-data/tests qmb/tests/test_futures_rolls.py qmx-agents/packages/qmx-library/tests` (a microsecond file lands with its seam; a two-contract fixture shows the roll event and no back-adjusted price; an empty open hour stays unfrozen), then `just ci`.
- **He sees.** Each data card says its clock and where its data changed shape.

## B12. Conformance, the default tester and variants

- **Goal.** AD-206, QB-13, QB-14, MA-07, MA-10.
- **Files.** `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance.py` and the pack (fixture dataset, the dummy unit's golden trade-list hashes); `qmx-agents/apps/qmb/jobs/conformance.py`; the `[qmb] default_tester` setting's check; `backtest_compare` parity diff; a second tester fixture app in tests.
- **Depends on.** B6, B10.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-judge/tests/test_conformance.py` (the shipped tester passes its pack; a variant that rounds differently fails with a diff; setting the default to it is refused; two results of one request compare trade by trade), then `just ci`.
- **He sees.** A versions panel: which QMB is the default and which passed its check.

## B13. The judge

- **Goal.** AD-207: study specs, the default chain, presets, shrinkage, effective tries, verdicts, baseline cards, proposal cards, death certificates, forecasts; the `judge` subworkflow and `judge_run` row; the host's lifecycle writer, which records the judge's draft-to-tested or draft-to-parked move when a verdict lands (R1-B-06).
- **Files.** `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py`, `presets.py`, `shrink.py`, `tries.py` (clustering); kinds `study-spec` (with its registered checker that lands a `spec_edit` try), `verdict`, `baseline-card`, `proposal-card`, `death-certificate`, `forecast`; `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/judge/`; the `judge_run` row; new `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py` (`record_move(event)`, This PC's one `lifecycle` writer, refusing a move Part A's fold rejects). The shipped tool count `backtest` 4 becomes 5 on purpose (`qmx-tools/tests/test_tools.py:374-376`).
- **Depends on.** B3, B6, B8; Part A's lifecycle machine (its `qmx.lifecycle/1` body and `fold`).
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-judge packages/qmx-host/tests/test_lifecycle.py packages/qmx-tools/tests` (the luckiest-market simulation; 51 variants cluster to 11 effective tries; a zero-trade result never passes; a spec edit after a result lands one try; a judge version bump lands a second verdict beside the first; a passing verdict on a draft lands one `lifecycle` row `draft` to `tested` with `by.kind = judge`, and landing it again adds nothing; `backtest` lists 5 tools), then `just ci`.
- **He sees.** A verdict on the dummy unit in plain words, with the number of tries behind it.

## B14. The other run kinds and the nightly replay

- **Goal.** `sweep`, `walk_forward`, `robustness`, `optimize`, `whatif` as counted jobs (QB-22's split); `replay_check` (QB-23). The behaviour check moved to B5b and B6.
- **Files.** `qmx-agents/apps/qmb/jobs/*.py`; `qmb/src/qmb/optimize/`, `robustness/`, `sweep/`, `analysis/` (wrapped, not rewritten); the lander's "worsen only" check.
- **Depends on.** B12, B13.
- **Verify.** `uv run pytest qmb/tests qmx-agents/apps/qmb/tests` (a 6-cell sweep lands 6 try rows; a "worsen only" scenario that improves is refused; a recorded fixture day replays with a per-decision diff), then `just ci`.
- **He sees.** "Run on every market" works, and each night's live day can be replayed against the test.

## B15. Journals readable by agents and him; the harvester on every machine

- **Goal.** AD-211 and the local half of AD-210: the host is the one harvester of every app's append streams on its machine (closed months once; open months of bars and reading history on `[records] open_harvest_s`, journals too on This PC; ticks on `[records] tick_harvest_s`), `journal_query`, `notes_write` (`note` version 2), `trade` version 2 projection, `paper-run` version 2 with the judge's paper scoring, the test that nothing here writes `bot` or `strategy` (R0-17).
- **Files.** new `qmx-agents/packages/qmx-host/src/qmx_host/records.py` (local half: the harvester, by the committed reader and `born_on = node`), `qmx_host/maintenance.py` (list the job), `qmx_host/host.py` (start it beside backups); `qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py`, `functions.py`; `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`; kinds `note`, `paper-run`, `trade` (version 2); `qmx-agents/packages/qmx-judge/src/qmx_judge/paper.py`; tests `qmx-agents/packages/qmx-host/tests/test_harvest.py`, `qmx-agents/packages/qmx-judge/tests/test_no_bot_writes.py`. The shipped tool count `research` 3 becomes 5 on purpose (`qmx-tools/tests/test_tools.py:374-376`).
- **Depends on.** B8.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-host/tests/test_harvest.py packages/qmx-tools/tests packages/qmx-judge/tests packages/qmx-library/tests` (a fixture app volume with journal, reading and bar streams: a closed journal month is committed once; the open month of bars lands as one `open.parquet` and holds 60 then 120 rows after two rounds; ticks wait for their cadence; an unchanged stream is skipped by its fingerprint, because the store reports `idempotent = False` on an unchanged re-commit (`packages/qmf-data/src/qmf/data/series.py:429-430`); the app's stream files are byte for byte unchanged by a round; a query without a window is refused; past the data says where it stops; backfilled rows excluded by default; a re-projected trade lands nothing new; a trade without initial risk carries `r_missing`; no write path lands `bot` or `strategy`; every new row is on the default copilot surface; `research` lists 5 tools), then `just ci`. The check on the practice node's real journal is Part C's first real start (R1-B-04).
- **He sees.** He can ask "why didn't the dummy unit trade this morning?" and get the reason with the spread at that minute.

## B16. Records come home from servers

- **Goal.** AD-210 across machines: the records host job's remote half (JR-16, QB-23's recorded feed), with Part C's fingerprint confirmation (R1 CF-5, B-CC7).
- **Files.** `qmx-agents/packages/qmx-host/src/qmx_host/records.py` (remote half: watermarks, `data.list` with `confirmed`, `data.fetch` of closed partitions and of due open ones, `journal_tail`); `qmx-agents/packages/qmx-host/src/qmx_host/market_data.py` (`commit` pins a `node`-born partition on a door whose placement is not `pc`; `verify` unchanged); `qmx-agents/packages/qmx-host/src/qmx_host/host_route.py` (Part C's `data.list` handler passes `confirmed` to the door's built `verify`, one call); tests `qmx-agents/packages/qmx-host/tests/test_records.py`.
- **Depends on.** B8, B15; Part C's host route with `data.list`, `data.fetch` and `apps.ask journal_tail`.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-host/tests/test_records.py packages/qmx-host/tests -k "market or records"` (a fake server with three closed months and an open one: all three commit and the watermark advances; the next `data.list` carries their three fingerprints as `confirmed`; on the server's door each was pinned until then and is unpinned and kept after; the open month lands as This PC's open file and is fetched again only when its fingerprint changed and its pull is due; its frozen month later replaces it; a resend changes nothing; an unreachable node is skipped and named; one `maintenance-result` per round; the shipped door tests pass unchanged, because the downloader templates pass the door's own placement), then `just ci`. Live lane: with a server node on demo, turn This PC off for a night and on again; save the next round's `maintenance-result`.
- **He sees.** "Bring node records home" on the maintenance list, with the last round's counts, what is still pinned on each node, and its off switch.

## B17. Workflow agent steps that can write (AGW) and the `library` node kind

- **Goal.** AD-214: AGW as engine AD-60 designed it; the `library` kind marked unavailable.
- **Files.** `qmx-agents/packages/qmx-engine/src/qmx_engine/policy.py` (the AGW form), `ports/harness_adapter.py` (policy args with the overlay and `disallowed_tools` for undeclared `Bash` and `PowerShell`), `nodes/agent.py` (commit only `outputs.files`), `definition/registry.py:94`; tests `qmx-agents/packages/qmx-engine/tests/test_agw.py` (from `scratchpad/l1b/agw_offered_tools.py`), the P-PERM probe rerun script.
- **Depends on.** nothing.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_agw.py packages/qma-harness/tests packages/qmx-engine/tests` (a step declaring `Write` and `Edit` is offered no `Bash` and no `PowerShell`; a write outside the overlay is refused; only declared outputs commit; a definition using `library` is refused with its reason), then `just ci`. Live lane: rerun P-PERM on the real engine launch path with `haiku`; save its log; pass when A3 and A3W cannot run.
- **He sees.** A workflow's agent can now save the file it was asked to write, and nothing else.

## B18a. The shared pieces the build family needs

- **Goal.** The unit-check step, the proposal card, the death certificate, the lineage writer and the conveyor (AD-213; R1-B-08).
- **Files.** `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/` (`unit-check/`, `proposal-card/`, `death-certificate/`, `lineage/`, `conveyor/`); tests in `qmx-agents/packages/qmx-engine/tests/test_shared_build.py`.
- **Depends on.** B13; Part A's `unit_check` row.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_shared_build.py packages/qmx-engine/tests -k "template or shared"` (the dummy's broken twin loops once through the unit-check step and passes; the same problem set twice stops the loop; a self-firing conveyor fires once; a failed unit lands one death certificate and one `dead_end` memory row; a run's lineage walks from source to result; a proposal lands as a card, never as a state change), then `just ci`.
- **He sees.** Nothing new on screen yet; the build template's parts exist.

## B18b. The shared pieces the slow lane needs

- **Goal.** The receipts grader, marked sources, the digest, the calendar-open check and the forecast ledger with its scorer (AD-211, AD-213; R1-B-08). The data-quality check is B11's.
- **Files.** `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/` (`receipts-grader/`, `marked-sources/`, `digest/`, `calendar-open/`, `forecast/`); tests in `qmx-agents/packages/qmx-engine/tests/test_shared_slow_lane.py`.
- **Depends on.** B13, B15; Part C's calendars as data.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_shared_slow_lane.py` (an uncited number fails the grader; a fixture source carrying an instruction is quoted, not followed; a fixture day's digest has fixed numbers; a crypto calendar check opens on a Saturday and an FX one does not; a forecast is scored by the script, never by its author), then `just ci`.
- **He sees.** Nothing new on screen yet; the slow-lane templates' parts exist.

## B18c. The surgical fixes to shipped templates

- **Goal.** `workflows.md` §4's fixes (R1-B-08).
- **Files.** `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/scripts/spec.py` (holdout and split as study settings, off), `d3`, `l4`, `d4` (loop counts on the card), the gate scripts in `b` and `d3` removed in favour of `_shared/judge`, the builder model default.
- **Depends on.** B13.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_templates.py packages/qmx-engine/tests -k template` (`b` has no holdout by default; `d3`, `l4` and `d4` read their loop counts from card settings; no template keeps a copied gate script), then `just ci`.
- **He sees.** Template cards show their loop counts as numbers he can change.

## B19. The build-and-prove family

- **Goal.** Build and prove a unit; run on every market; where its rules hold; overnight loop; dictionary expansion; librarian.
- **Files.** `templates/b-build-and-prove/`, `l1-idea-to-first-result/`, `d3-iterate-against-qmb/`, `d4-variant-comparison/`, `l4-overnight-lab-loop/` (enhanced; `meta.needs` cleared); new template folders; `templates/catalog.py`; the shipped tests that pin these drafts' old status (`qmx-engine/tests/test_templates.py:613-620`, `test_install_through_host.py:34-38`) updated on purpose.
- **Depends on.** B14, B18a, B18c; Part A's dictionary authoring door for dictionary expansion.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_templates.py packages/qmx-engine/tests/test_install_through_host.py`, then `just ci`. Live lane: test-run "Build and prove a unit" on `haiku` from a one-line idea; save the run's trace; pass when it lands a verdict or a death certificate.
- **He sees.** "Turn a strategy idea into a tested strategy" runs from a sentence to a verdict.

## B20. The slow lane on This PC

- **Goal.** Unit review, decay check, market review and almanac, pre-session shortlist, tagging units to markets, MIS check, daily data review, nightly live-day replay (STATE midday ruling 44).
- **Files.** `templates/t7-trade-journal-review/`, `dm-demo-monitor/`, `dc-decay-and-limit-report/`, `db-desk-brief/`, `rv-weekly-review/` (read scripts replaced, `meta.needs` honest); new template folders for the shortlist, tagging, MIS check, data review and live-day replay; `templates/catalog.py`; pinned-status tests updated on purpose.
- **Depends on.** B15, B18b; Part C's reading history, `readings_query` row and board for the shortlist, tagging and MIS check.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests -k template`, then `just ci`. Live lane: test-run the unit review on the practice node's journal with `haiku`; save the note; pass when every number in it cites a receipt.
- **He sees.** Each morning a short note per unit (traded, skipped, missed, why), a market almanac, and a shortlist before each session, all marked as proposals.

## B21. The node watcher and the node-dependent drafts

- **Goal.** The node watcher (heartbeats, node journal, guard rows; proposals and alerts, never presses); the remaining `needs: trading-node` drafts freed where their door now exists.
- **Files.** `templates/gw-guard-watchdogs/`, `rk8-incident-post-mortem/` (enhanced), `templates/catalog.py`.
- **Depends on.** B16; Part C's node read operations through AD-46.
- **Verify.** `cd qmx-agents && uv run pytest packages/qmx-engine/tests -k template`, then `just ci`. Live lane: with the practice node running, stop its feed for two minutes; save the watcher's alert; pass when it names the stale feed and proposes nothing that acts.
- **He sees.** A watcher that tells him when a node is unwell and why, and never touches it.

## Coverage

| Spine decision | Slices |
| --- | --- |
| AD-201, AD-202 | B5, B6 |
| AD-203 | B1, B2, B5, B6 (QMB opts into Part C's restart) |
| AD-204, AD-205 | B4, B5b, B6, B7, B9, B10, B11, B14 |
| AD-206 | B12 |
| AD-207 | B3, B13, B14, B15 |
| AD-208, AD-209 | B8, B9, B13, B15 |
| AD-210 | B15, B16 |
| AD-211 | B15, B18b |
| AD-212 | B3, B11, B13, B15 |
| AD-213 | B18a, B18b, B18c, B19, B20, B21 |
| AD-214 | B17 |
| AD-215 | B6, B10, B16 |
| AD-216 | every slice that adds a setting |

**What other parts consume from these slices.** Part C's node runtime imports B5b's unit handler; Part C's recorder and MIS app write through B8's writer library (series rows, reading records with `source`); Part C's MIS app reads the bars B15 harvests; Part C's promote action writes his clicks through B13's `qmx_host/lifecycle.py`; Part C's `data.list` handler gains B16's one `verify` call.
