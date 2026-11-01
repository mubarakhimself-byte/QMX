## Keep memory flat on any run length and replay each data kind as declared (B7)

Phase 2, QMB in depth. Part B slice B7, Level 0 AD-35, cases QB-01, QB-02 and QB-21. Ledger CC-07 (nothing capped, no lookback limit). Real step none. Done when peak memory stays flat from 10,000 to 200,000 steps, quotes, trades and bars replay as the data card declares, and daily bars close in the venue's day.

**Depends on.** B6.

**Files.**

- [ ] Edit `qmb/src/qmb/host/replay.py` (windowed frames served through QML's kept `ReadSurface.at`, `qml/src/qml/protocol/__init__.py:112`) and `qmb/src/qmb/runloop/bars.py`.
- [ ] Create `qmb/tests/test_windowed_reader.py` and `qmb/tests/test_fidelity.py`.

**Build.**

- [ ] Keep only the unit's derived warm-up plus its declared lookback in memory, with no step cap. Add the three fidelities and the venue-day close. `[qmb] window_memory_tolerance` is a named setting.

**You see.**

- [ ] A twenty-year backtest on one-minute bars finishes on his PC.

**Verify, unit.**

- [ ] Peak memory for 10,000 and 200,000 steps stays within `[qmb] window_memory_tolerance`. One golden per fidelity. A week of ticks gives the venue's daily closes. Run `uv run pytest qmb/tests/test_windowed_reader.py qmb/tests/test_fidelity.py qmb/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy over 10,000 and 200,000 M1 steps with peak memory sampled. Save `b7-memory.log`. Pass when the two peaks differ by less than the tolerance.
- [ ] Lane 3. One golden run per fidelity (quotes, trades, bars). Save `b7-fidelity.log`. Pass when each matches its golden trade list.
- [ ] Lane 4. A week of ticks through the bar builder. Save `b7-venueday.log`. Pass when the daily closes fall on the venue's day boundary.
- [ ] Lane 5. Twenty years of synthetic M1 on one market. Save `b7-twentyyears.log`. Pass when it finishes and peak memory stays inside the tolerance.
- [ ] Lane 6. `uv run pytest qmb/tests -q -k "not slow"` at the parent and the head. Save `b7-qmb.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Peak megabytes at 10,000 and at 200,000 steps.
- [ ] Probe. Lane 2.
- [ ] Baseline. The 10,000-step peak, measured first.
- [ ] Rule. Fails when the 200,000-step peak passes the 10,000-step peak by more than `[qmb] window_memory_tolerance`.

**Review gate.** Lens edge-case. The blast-radius fact is that `ReadSurface.at` (`qml/src/qml/protocol/__init__.py:112`) is kept unchanged, so QML's shipped tests pass.

@merge

## Make fills, sizes, costs, carry and margin behave like a real market (B10)

Phase 2, QMB in depth. Part B slice B10, Level 0 AD-35, cases QB-03, QB-04, QB-07, QB-08, QB-16 to QB-18, RS-13 and LD-13. Ledger CC-19 (a trader's lens on every step). Real step none. Done when gaps fill past the stop and record their real loss in R, sizes round down with the residue journaled, swaps, index financing, perps funding and dividends land as cash events, a hole in the data fails the run unless allowed, and results say "costs uncalibrated" until real fills exist.

**Depends on.** B6, B9, C-02.

**Files.**

- [ ] Edit or create `qmb/src/qmb/execution/fill.py` (the gap rule), `qmb/src/qmb/execution/cost.py`, `qmb/src/qmb/execution/spread.py`, `qmb/src/qmb/execution/slippage.py` (profiles from the market journal, `costs_uncalibrated`), `qmb/src/qmb/execution/financing.py` and `qmb/src/qmb/execution/risk.py` (the margin and liquidation port).
- [ ] Edit `qmb/src/qmb/data/generate.py` (by class), `qmb/src/qmb/host/unit_runner.py` (lot rounding, residue in R) and `qmx-agents/apps/qmb/server.py` (process priority below normal).
- [ ] Create `qmb/src/qmb/data/gap_check.py` (preflight) and `qmb/tests/test_realism.py`.

**Build.**

- [ ] Write each rule from the instrument records C-02 lands, with QMB's exact money kept, so `tools/money_path_scan.py` stays clean.

**You see.**

- [ ] Results say "costs uncalibrated" until real fills exist, and a loss through a gap shows as it was, never capped at 1R.

**Verify, unit.**

- [ ] A weekend gap records -1.7R where the stop was 1R. 0.037 lots trades 0.03 with the residue journaled, and 0.004 skips. A Wednesday rollover carries three days. A perp held 24 h pays three fundings. A three-day hole lands a `failed` result unless `allow_gaps`. A crypto request gets the crypto generator. The app's priority reads below normal. Run `uv run pytest qmb/tests/test_realism.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. A weekend gap through the dummy's stop on a fixture. Save `b10-gap.log`. Pass when the trade records -1.7R with `gap_through_stop`.
- [ ] Lane 3. Sizes of 0.037 and 0.004 lots. Save `b10-lots.log`. Pass when the first trades 0.03 with the residue in R and the second skips with its reason.
- [ ] Lane 4. A Wednesday rollover on EURUSD and a perp held 24 h. Save `b10-carry.log`. Pass when the swap is three days and the perp pays three fundings.
- [ ] Lane 5. A run over a fixture with a three-day hole, with and without `allow_gaps`. Save `b10-hole.log`. Pass when it lands `failed` without and runs with.
- [ ] Lane 6. `tools/money_path_scan.py` over `qmb/`. Save `b10-moneypath.log`. Pass when it is clean.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the dummy's three-month run with the realism adapters on.
- [ ] Probe. B9's lane 3 request at the parent and the head, interleaved.
- [ ] Baseline. The parent's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on the money path. The blast-radius fact is that QMB's exact money types carry every quantity and price, so the money-path scan stays clean.

@merge

## Replay futures contract by contract and give data cards their facts (B11)

Phase 2, QMB in depth. Part B slice B11, cases QB-05, LD-01, LD-03, LD-04 and LD-16. Rulings 29 and 40. Real step none. Done when futures replay contract by contract with rolls as events and no back-adjusted price, `dataset` version 2 carries the source clock, seams, stitching and calendar, imports check stamps, and the shared data-quality step exists.

**Depends on.** B7.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/dataset.schema.json` (version 2, additive).
- [ ] Edit `packages/qmf-data/src/qmf/data/importers/` and the download templates' scripts in `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-dukascopy/`, `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-binance/` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-ccxt/` (stamp check, source clock, seams).
- [ ] Edit `qmb/src/qmb/host/replay.py` and `qmb/src/qmb/runloop/stream.py` (rolls as events).
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/data-quality/` and `qmb/tests/test_futures_rolls.py`.

**Build.**

- [ ] Write the contract-by-contract replay, the card's new facts, the stamp check at import and the shared data-quality step.

**You see.**

- [ ] Each data card says its clock and where its data changed shape.

**Verify, unit.**

- [ ] A microsecond file lands with its seam. A two-contract fixture shows the roll event and no back-adjusted price. An empty open hour stays unfrozen. Run `uv run pytest packages/qmf-data/tests qmb/tests/test_futures_rolls.py qmx-agents/packages/qmx-library/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. Import a microsecond-stamped fixture file. Save `b11-seam.log`. Pass when its card records the seam and the source clock.
- [ ] Lane 3. A two-contract futures fixture replayed. Save `b11-roll.log`. Pass when the roll is one event and no price is back-adjusted.
- [ ] Lane 4. A fixture month with an empty open hour. Save `b11-open.log`. Pass when the month stays unfrozen.
- [ ] Lane 5. The data-quality step on a fixture month with a gap and a clock jump. Save `b11-quality.log`. Pass when both are listed with their minutes.
- [ ] Lane 6. A version 1 `dataset` card read at the head. Save `b11-v1.log`. Pass when it reads unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Seconds to import one fixture month with the stamp check on.
- [ ] Probe. Lane 2 at the parent and the head, interleaved.
- [ ] Baseline. The parent's import, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on data seams. The blast-radius fact is that the shipped downloader templates still pass their tests with the stamp check added.

@merge

## Prove a QMB version before it becomes the default, and run variants side by side (B12)

Phase 2, QMB in depth. Part B slice B12, Part B AD-206, cases QB-13, QB-14, MA-07 and MA-10. Ruling 22 ("build a new QMB version, improve it, or run several variants"). Real step none. Done when the shipped tester passes its conformance pack, a variant that rounds differently fails with a diff, a failing variant cannot become the default, and two results of one request compare trade by trade.

**Depends on.** B6, B10.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance.py`, the pack in `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance_pack/` (fixture dataset, the dummy's golden trade-list hashes), `qmx-agents/packages/qmx-judge/tests/test_conformance.py` and a second tester fixture app in `qmx-agents/packages/qmx-judge/tests/fixtures/variant-tester/`.
- [ ] Edit `qmx-agents/apps/qmb/jobs/conformance.py` (the real job replaces the stub), `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (`backtest_compare` parity diff) and `qmx-agents/packages/qmx-control/src/qmx_control/service.py` (the `[qmb] default_tester` setting's check).

**Build.**

- [ ] Write the conformance run, which the core runs and no variant reports for itself, the default-tester check, and the parity diff.

**You see.**

- [ ] The copilot can say which QMB version is the default and which passed its check. The versions panel is the UI session's.

**Verify, unit.**

- [ ] The shipped tester passes its pack. A variant that rounds differently fails with a diff. Setting the default to it is refused. Two results of one request compare trade by trade. Run `cd qmx-agents && uv run pytest packages/qmx-judge/tests/test_conformance.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. The conformance job on the shipped QMB. Save `b12-pass.log`. Pass when every golden hash matches.
- [ ] Lane 3. The conformance job on the variant fixture. Save `b12-variant.log`. Pass when it fails with a per-trade diff.
- [ ] Lane 4. Set `[qmb] default_tester` to the failing variant. Save `b12-default.log`. Pass when the setting is refused with the reason.
- [ ] Lane 5. One request on both testers, then `backtest_compare`. Save `b12-compare.log`. Pass when the diff lists the trades that differ and nothing else.
- [ ] Lane 6. Two QMB versions installed side by side, each called with its pin. Save `b12-pins.log`. Pass when each call lands a result stamped with its own app and version.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one conformance run.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because a variant must never report its own score. The blast-radius fact is that results, status and comparisons stay the core's `backtest` rows, never QMB operations (Level 0 AD-34).

@merge

## Judge every result with its tries counted (B13)

Phase 2, QMB in depth. Part B slice B13, Part B AD-207, Level 0 AD-25. STATE correction 10 (judging is the product), ledger "the picking the luckiest market trap", and STATE "How standing order 7 reads". Real step none. Done when study specs, the default chain, presets, shrinkage, effective tries, verdicts, baseline, proposal and death cards and forecasts exist, the `judge` subworkflow and `judge_run` row work, and the host's one lifecycle writer records the judge's draft-to-tested or draft-to-parked move.

**Depends on.** B3, B6, B8, A9.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py`, `qmx-agents/packages/qmx-judge/src/qmx_judge/presets.py` and `qmx-agents/packages/qmx-judge/src/qmx_judge/shrink.py`, and edit `qmx-agents/packages/qmx-judge/src/qmx_judge/tries.py` (clustering).
- [ ] Create `qmx-agents/packages/qmx-library/src/qmx_library/kinds/{study-spec,verdict,baseline-card,proposal-card,death-certificate,forecast}.schema.json`. The study-spec kind names a registered checker that lands a `spec_edit` try.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/judge/`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` (`judge_run`), `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` and `qmx-agents/packages/qmx-tools/tests/test_tools.py`, where `backtest` goes from 4 to 5 tools on purpose (`:374-376`).
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py` (`record_move(event)`, This PC's one `lifecycle` writer, refusing a move Part A's `fold` rejects) and `qmx-agents/packages/qmx-host/tests/test_lifecycle.py`, and edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` to register the study-spec checker and compose the writer.

**Build.**

- [ ] Write the judge, its presets and shrinkage, effective tries by clustering, the cards, the subworkflow and the lifecycle writer. Scripts decide. Agents explain.

**You see.**

- [ ] A verdict on the dummy unit in plain words, with the number of tries behind it.

**Verify, unit.**

- [ ] The luckiest-market simulation. 51 variants cluster to 11 effective tries. A zero-trade result never passes. A spec edit after a result lands one try. A judge version bump lands a second verdict beside the first. A passing verdict on a draft lands one `lifecycle` row from `draft` to `tested` with `by.kind = judge`, and landing it again adds nothing. `backtest` lists 5 tools. Run `cd qmx-agents && uv run pytest packages/qmx-judge packages/qmx-host/tests/test_lifecycle.py packages/qmx-tools/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. The luckiest-market simulation, the best of 30 random markets. Save `b13-luckiest.log`. Pass when the judge does not pass the best-looking market on luck.
- [ ] Lane 3. 51 fixture variants. Save `b13-tries.log`. Pass when they cluster to 11 effective tries.
- [ ] Lane 4. A passing verdict on the dummy's draft, landed twice. Save `b13-lifecycle.log`. Pass when one `lifecycle` row from `draft` to `tested` with `by.kind = judge` lands once.
- [ ] Lane 5. A zero-trade result, then a spec edit after a result. Save `b13-rules.log`. Pass when the first never passes and the second lands one try.
- [ ] Lane 6. Ask the copilot on `haiku` "judge the dummy unit's last backtest". Save `b13-copilot.log`. Pass when it calls `judge_run` and quotes the verdict with its try count.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one judge run over the dummy's three-month result.
- [ ] Probe. Lane 6's request from a script.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because the referee must not be gamed. The blast-radius fact is that the tool count test now pins `backtest` at 5, changed on purpose in this PR.

@merge

## Count sweeps, walk-forwards and the other run kinds, and replay a live day (B14)

Phase 2, QMB in depth. Part B slice B14, cases QB-22 and QB-23, Level 0 AD-5 (the nightly replay). Real step none. Done when `sweep`, `walk_forward`, `robustness`, `optimize` and `whatif` run as counted jobs, a "worsen only" scenario that improves is refused, and `replay_check` replays a recorded day with a per-decision diff.

**Depends on.** B12, B13.

**Files.**

- [ ] Create `qmx-agents/apps/qmb/jobs/{sweep,walk_forward,robustness,optimize,whatif,replay_check}.py` and their tests in `qmx-agents/apps/qmb/tests/`.
- [ ] Edit the entry points in `qmb/src/qmb/optimize/`, `qmb/src/qmb/robustness/`, `qmb/src/qmb/sweep/` and `qmb/src/qmb/analysis/`, wrapped and not rewritten.
- [ ] Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py` (the "worsen only" check).

**Build.**

- [ ] Wrap each kept battery as a job that the lander counts, one try per cell or fold.

**You see.**

- [ ] "Run on every market" works, and each night's live day can be replayed against the test.

**Verify, unit.**

- [ ] A 6-cell sweep lands 6 try rows. A "worsen only" scenario that improves is refused. A recorded fixture day replays with a per-decision diff. Run `uv run pytest qmb/tests qmx-agents/apps/qmb/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. A 6-cell sweep of the dummy. Save `b14-sweep.log`. Pass when 6 try rows land.
- [ ] Lane 3. A "worsen only" scenario that improves the result. Save `b14-worsen.log`. Pass when it is refused with its reason.
- [ ] Lane 4. `replay_check` on a recorded fixture day. Save `b14-replay.log`. Pass when the diff lists each decision that differs, and none when the day matches.
- [ ] Lane 5. A three-fold walk-forward. Save `b14-walk.log`. Pass when 3 tries land and the judge counts them.
- [ ] Lane 6. Ask the copilot on `haiku` "run the dummy on every market you have data for". Save `b14-every.log`. Pass when one try lands per market.
@menu

**Verify, perf.**

- [ ] Metric. Seconds per sweep cell.
- [ ] Probe. Lane 2.
- [ ] Baseline. One single backtest of the same window.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the kept optimiser, robustness batteries and sweeps pass their shipped tests unchanged.

@merge
