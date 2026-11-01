# R1 fixes for part B (fixer X1-B)

Fixer X1-B, 2026-11-01, per `architecture/briefs/X1-B-fix.md`. Applies `architecture/review/R1-findings.md` to `architecture/parts/B-qmb-journals-workflows/`. One line per finding and per settlement in part B's share. Labels: CHECKED (path:line, or a command run) and INFERRED. "Spine" is that folder's `ARCHITECTURE-SPINE.md`; "slices" its `BUILD-SLICES.md`; "calls" its `LEAD-CALLS.md`. Code paths are on `D:\QMX-worktrees\engine-base-read\` (`origin/engine/base` `c93407ca`).

Status: done. Every finding below is fixed; none was rejected.

## Findings for part B

| Finding | What was done |
| --- | --- |
| R1-B-01 | Fixed. Spine AD-202 names the G record (Part A's `test-report`, `check = "qml-g/1"`, by `compiled_fingerprint`, A CONTRACTS §3.3) and how it is made: with none, the lander runs `behaviour_check` first on the same tester through a host-injected `run_job`, and opens only on a passing safety verdict. The behaviour check moved from B14 into new slice B5b (QMB code, depending on Part A's checker slice) and B6 (the job and the lander's rule, depending on Part A's Library additions); CONTRACTS §3 lander port; `judge.md` §2; `qmb.md` §4; LC-B-33. |
| R1-B-02 | Fixed and widened to the pull. Spine AD-209: the host is the one harvester of every app's append streams on its machine (closed months once; open months of bars and reading history every `[records] open_harvest_s` 60, journals too on This PC; ticks every `tick_harvest_s` 3,600), committing with `born_on = node`; apps write their recorded feed as series rows through the writer library. AD-210: This PC also pulls open bars and readings (`open_pull_s` 3,600) and ticks (`tick_pull_s` 86,400), so the nightly replay and the slow lane see the current month. Slice B15 builds the harvester; `journals.md` §4, §5, §7; CONTRACTS §4, §6, change 12; LC-B-31. Safety fact: one `open.parquet` per open month (`packages/qmf-data/src/qmf/data/series.py:6-9`, CHECKED; run by R1). |
| R1-B-03 | Fixed. Spine AD-210 uses Part C's `confirmed` fingerprint list; the server's door pins `node`-born partitions until listed (the built `verify` clears pins by fingerprint, `qmx_host/market_data.py:603-617`, CHECKED); nothing prunes. Slice B16 builds the PC side, the pin in `market_data.py` and the one `verify` call in Part C's `data.list` handler; LC-B-13, LC-B-34. |
| R1-B-04 | Fixed. Slice B15 depends on B8 only and tests a fixture app volume; the practice node's real-journal check is noted as Part C's (its first real start). |
| R1-B-05 | Fixed. Slice B7 builds the windowed reader against QML's kept `ReadSurface.at` (`qml/src/qml/protocol/__init__.py:112`, CHECKED) and drops the Part A dependency; CONTRACTS §9 row changed. |
| R1-B-06 | Fixed. Spine AD-208 and `journals.md` §3: unit-journal kinds `lifecycle` (Part A's `qmx.lifecycle/1`) and `state` (Part A's state events); node kind `node_lifecycle`. Writers: This PC's host for his clicks and the judge's move (new `qmx_host/lifecycle.py`, slice B13), the node for risk stops; `lifecycle` partitions carry the writer's role in the variant so two writers on This PC never share one; LC-B-30. |
| R1-B-07 | Fixed. The reading body carries `source`; `journal-readings` subject is `<source>.<market id>` (machine is already in the variant). Spine AD-208, AD-209; CONTRACTS §4, change 9; `journals.md` §3, §4. |
| R1-B-08 | Fixed. B18 split by consumer into B18a (unit-check step, proposal card, death certificate, lineage writer, conveyor), B18b (receipts grader, marked sources, digest, calendar-open check, forecast ledger) and B18c (the surgical template fixes); B19 and B20 depend on their halves. One correction to the review's list: the data-quality step is built in B11 already, so it is in neither half. |
| R1-B-09 | Fixed. Spine AD-201, AD-204: QMB's jobs return `failed` bundles for domain failures and raise only on a crash (the bootstrap counts a job error only on a raise, `qmx_apps/bootstrap.py:195-211`; the trip, `supervisor.py:817`; CHECKED); QMB opts into `[breaker] restart = "backoff"`. Slice B6 tests both and the restart-after-trip interaction; `qmb.md` §3, §8; `mini-app-core.md` §6; `UI-NEEDS.md` §1; LC-B-28. |
| R1-B-10 | Fixed. Spine AD-208, CONTRACTS §4 and `journals.md` §3: `signal` and `calibration` rows take Part A's `row_id`, `state` rows fp1 over scope id, instant and ordinal, `lifecycle` rows their `event_id`, fills and trades their venue ids; the writer drops a repeat and flags a differing body as `determinism_break`. Rows that read the machine's state keep sequence ids (Deferred; LC-B-29). Slice B8 tests it. The node commits its cursor only after a whole slice (`qmn/src/qmn/loop/driver.py:66-73`, CHECKED). |
| R1-B-11 | Fixed. `fidelity` replaces "data level" everywhere in part B, mapped onto Part A's levels (`bars` 1, `quotes` 2, `trades` 4). Spine AD-204; CONTRACTS §1, §2; `qmb.md` §4, §9; slice B7; LC-B-35. |

## Clash settlements that name a part B file

| Settlement | What was done |
| --- | --- |
| A-C3 | Applied. Spine AD-205: one run-slice handler `qmb/src/qmb/host/unit_handler.py` over `HostedUnit`, the five `run_slice` hooks (`qmn/src/qmn/loop/driver.py:409-417`, CHECKED), imported by QMB's runner and the node runtime; built in new slice B5b, used in B6; `qmb.md` §4 no longer says `construct_bot` accepts a unit; CONTRACTS §9, §10 C12. |
| A-C6 (5) | Applied. Spine AD-208 takes Part A's decision row id as the record id (with R1-B-10). |
| B-D1 to B-D6 | No part B file named; part B's "Conflicts with the parent" table now records each as accepted, and CONTRACTS' change list carries the settlement. |
| B-CC5, B-CC8, B-CC10, B-CC11 | No part B file named; CONTRACTS changes 5, 8 (with R1-C-12's guard), 10 and 11 carry the settlement. |
| B-CC7 | Applied. Spine AD-210 (fingerprint list, the pin, nothing prunes), Deferred (the prune slice), LC-B-13 and LC-B-27 rewritten, slice B16; the `[records] node_retention_days` setting is removed; CONTRACTS §6 and change 7. |
| B-CC9 | Applied. CONTRACTS §4 and change 9: `source` in the reading body, subject `<source>.<market id>`. |
| B-CC12 | Applied and widened as R1-B-02 above: spine AD-209, AD-210, slice B15. |
| C-CC9 | Applied: spine AD-209, AD-210, slice B15 (bars every 60 s, ticks hourly). |
| CF-4 | Applied. Spine AD-203 is now "two of the six" core changes; B1 and B5 are unchanged; QMB opts into change 3; the trip-then-restart interaction test is in B6, where QMB opts in, because B5 has no restart to test against; `mini-app-core.md` §3, §6. |
| CF-5 | Applied: slice B16 builds the pin of `node`-born partitions on a non-PC door and the `confirmed` path; spine AD-210; `journals.md` §5. Safety fact from Part C's run (C `BLAST-RADIUS.md` C5): `born_on`'s callers pass the door's own placement, so a `node` branch changes none of them. |

## Findings in other groups whose fix lands in a part B file

Only this fixer writes part B's folder, so these are applied here.

| Finding | What was done |
| --- | --- |
| R1-L0-01 | Part B's case table adds AG-10 (Library branch and merge as built), CA-05 (one error shape, every problem) and CA-12 (reserved names, tested in B2); LC-B-19 amended. CHECKED by `scratchpad/r1/cases.py` after the fix: no non-risk case is missing from every part's table. |
| R1-L0-02 | Part B owns the shared handler, as the review asked (B5b; spine AD-205). |
| R1-L0-03 | Spine AD-202: his click is caller kind `user`, principal `operator` (`qmx_engine/service/context.py:59-70`, CHECKED). |
| R1-L0-08 | WF-06's line in the spine and `workflows.md` §5 follows: verified by parse at a paired server, a real two-host run in Part C's server slice. |
| R1-A-01 | Slice B9's check runs the dummy on EURUSD and XAUUSD long enough to close its `min_count` trades on each, asserts that count first, then at least one `calibration` row for `min_trend_strength`. |
| R1-A-05 | Slice B6 depends on Part A's Library additions landing the dummy on first start. |
| R1-C-01 | The host's lifecycle writer (`qmx_host/lifecycle.py`, slice B13, CONTRACTS §3) is the function Part C's promote action calls to record his click. |
| R1-C-08 | Slices B5b and B6 assert every fill carries the sizer receipt's quantity after lot rounding; spine AD-205; `qmb.md` §4; `RISK-SIZING-POINTS.md`. Part B's case table does not claim CA-03, which A and C share. |
| R1-C-10 | CONTRACTS §1: `instrument_classes[]` takes the one enum of Part A §2.3 (`spot_crypto`, `stock_cfd`, `stock` added; `crypto_spot` gone); LC-B-35. |
| R1-C-11 | Spine conventions name `qmx-tools/tests/test_tools.py:374-376` (CHECKED); slices B6 (`backtest` stays 4), B13 (4 to 5) and B15 (`research` 3 to 5) name it; CONTRACTS §7. |
| R1-C-12 | The handover line R0-01 and CONTRACTS change 8 carry the guard (`apps.job` refuses an agent on a `money` app). |
| R1-C-03, R1-C-04 | No change needed: part B already names `readings_query` and `instrument_get` Part C's rows and expects `inputs` on `apps.job`; B20's dependency now names `readings_query`. |

## Found while fixing

| Item | What |
| --- | --- |
| X1B-NEW-1 | The shipped CT-13 reader changes a writer's file: `read_stream` rebuilds the index, and a torn tail (a line in flight) is moved to a `.torn` sidecar and the data file truncated, even from an unlocked reader in another process (`packages/qmf-data/src/qmf/data/store/engines/jsonl.py:363-398`, `:510-547`). CHECKED by running `scratchpad/x1b/br_reader_truncates.py` in the scratch export's environment: "before=96 during=126 after_read=96; torn sidecars=['000000.jsonl.torn']". A harvester reading a node's live journal every minute with it could cut a journal-before-dispatch line. Fixed in the design: every reader but the writer uses the writer library's committed reader (spine AD-209 and its blast-radius table, `journals.md` §4, slice B8's test, LC-B-32). |
| X1B-NEW-2 | Standing order 7 says the only automatic transition is a risk stop, but Part A's lifecycle has the judge move a unit from draft to tested or parked automatically, and R1-B-06 names the judge as a writer. Kept as designed, because neither state trades and paper and live still need his click; logged as LC-B-30 for the lead with its undo. |

## For the other fixers and the lead (part B cannot edit these)

- Part C's node runtime imports `qmb/src/qmb/host/unit_handler.py` (B5b), so its runtime slice depends on B5b.
- Part C's recorder writes bars and ticks as series rows, and its MIS app writes reading records (kind `reading`, `source` in the body), through B8's writer library.
- Part C's `journal_tail` must read with the committed reader (X1B-NEW-1).
- Part C's host-route slice should not build the `confirmed` to `verify` call: B16 owns it (LC-B-34).
- Part C's promote action calls `qmx_host/lifecycle.py` from B13.

## Checks run before finishing

| Check | Result |
| --- | --- |
| `python .claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <part B folder>` | 0 findings |
| `python -I scratchpad/x1b/quotecheck_b.py <part B folder>` (every quote of his against its transcript line) | 27 quotes checked, 0 missing; the same script on a planted fake quote exits 1 |
| `python -I scratchpad/x1b/slices_check.py BUILD-SLICES.md` (every slice has goal, files, dependency, a pytest check and what he sees; no slice depends on a later one; coverage names real slices) | 24 slices, 0 problems |
| `python -I scratchpad/r1/cases.py` | every non-risk catalogue case is claimed by a part; AG-10, CA-05 and CA-12 now by B |
| `scratchpad/x1b/br_reader_truncates.py` (blast radius, step 4) | PROVEN, as quoted above |
| Memlog | ten entries appended to the part's `.memlog.md` through `_bmad/scripts/memlog.py` |
