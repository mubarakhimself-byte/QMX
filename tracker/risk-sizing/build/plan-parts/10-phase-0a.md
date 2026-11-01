## Take the old law off QML's top-level surface (A0)

Phase 0, the dummy unit end to end. Part A slice A0 (`architecture/parts/A-qml-dictionary-unit/BUILD-SLICES.md`), Part A AD-120, Level 0 AD-20. Rulings 24 and 32 (surgical, not frozen). Real step none. Done when the 23 old-law names leave `qml.__all__`, each still imports from its submodule, and no top-level importer exists anywhere in the repo.

**Depends on.** Nothing. It is the first PR on `build/unit-system`.

**Files.**

- [ ] Edit `qml/src/qml/__init__.py`.
- [ ] Create `qml/tests/test_surface_old_law.py`.

**Build.**

- [ ] Remove the 23 refusal functions and the `GAP_*` and `*_EPIC(S)` constants from `qml.__all__` and from the top-level imports. Each stays importable from its submodule for its own tests.
- [ ] Write Part A's AST scan (`blast-radius.md` BR-A3) as the test's helper, so a top-level importer anywhere in the repo fails the test.

**You see.**

- [ ] Nothing changes for him. Builders and agents stop reading the old refusals as current rules.

**Verify, unit.**

- [ ] The new test asserts that none of the 23 names is on `qml.__all__`, that each imports from its submodule, and that the scan finds no top-level importer. Run `uv run pytest qml/tests -q` (385 shipped tests pass) and `uv run pytest qmb/tests -q -k "not slow"`.

**Verify, live.**

@lane1
- [ ] Lane 2. The AST scan over the whole repo at the head. Save `a0-scan.log`. Pass when it lists no importer of the 23 names from the `qml` top level.
- [ ] Lane 3. `uv run pytest qml/tests -q` at the parent and the head. Save `a0-qml.log`. Pass when both pass the 385 shipped tests and the head adds only the new test.
- [ ] Lane 4. Import each of the 23 names from its submodule in a fresh interpreter. Save `a0-imports.log`. Pass when all 23 import.
- [ ] Lane 5. `uv run pytest qmn/tests -q -k "not slow"` at the parent and the head. Save `a0-qmn.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 6. Grep `docs/` and `qmx-agents/plugin/skills/` for the 23 names. Save `a0-mentions.log`. Pass when no hit is a code import and every doc hit is listed in `findings-backlog.md` for the doc pass.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds to import `qml` in a fresh interpreter.
- [ ] Probe. `python -X importtime -c "import qml"` at the parent and the head, interleaved.
- [ ] Baseline. The parent's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is BR-A3, no top-level caller of the 23 names.

@merge

## Let a workflow tell an app's job what to do (B1)

Phase 0, the dummy unit end to end. Part B slice B1 (`architecture/parts/B-qmb-journals-workflows/BUILD-SLICES.md`), mini-app core change 1 of Level 0 AD-33, engine AD-64. Rulings 46, 49 and 53 (the core changes only where it truly blocks). Real step none. Done when `app_op` passes `inputs` to an app's job and carries its `result` back, and a job request with only a name works exactly as today.

**Depends on.** Nothing.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (`run_job`) and `qmx-agents/packages/qmx-apps/src/qmx_apps/bootstrap.py` (`run_job`, `jobs`).
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/app_op.py` and `qmx-agents/packages/qmx-control/src/qmx_control/service.py` (`app_job` passes `inputs` and the caller's principal).
- [ ] Create `qmx-agents/packages/qmx-engine/tests/test_app_op_inputs.py`, written from the overlay proof in `parts/B-qmb-journals-workflows/mini-app-core.md` section 5 (36 passed there).

**Build.**

- [ ] Add optional `inputs` to a job request and a `result` to its answer, through the supervisor, the bootstrap and `app_op`. A request that is only `{"job": job}` (`qmx_apps/supervisor.py:1022`) behaves as today.
- [ ] `app_job` stamps the caller's principal on the request.

**You see.**

- [ ] Nothing on screen yet. A workflow can now tell an app's job what to do and read its answer.

**Verify, unit.**

- [ ] `test_app_op_inputs.py` covers a job that gets its inputs and returns its result, and a job asked with no inputs. Run `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_app2a_app_op.py packages/qmx-engine/tests/test_app2b_routing.py packages/qmx-engine/tests/test_app_op_inputs.py packages/qmx-apps/tests/test_apps.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. A fixture app with an echo job on a throwaway folder, and a workflow whose one `app_op` step passes `{"x": 1}`. Save `b1-echo.log`. Pass when the step's output holds the job's result with `x` equal to 1.
- [ ] Lane 3. The same job asked with no inputs. Save `b1-noinputs.log`. Pass when the answer equals the parent's.
- [ ] Lane 4. `uv run pytest packages/qmx-apps/tests -q` in `qmx-agents` at the parent and the head. Save `b1-apps.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 5. A job that raises. Save `b1-raise.log`. Pass when the step fails with the job's error and the app's `job_errors` counts it once.
- [ ] Lane 6. `app_job` called from a chat. Save `b1-principal.log`. Pass when the app's log records the principal `agent:<id>`.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds from `app_op` start to its result for the echo job.
- [ ] Probe. Lane 2 at the head and the no-inputs form at the parent, interleaved.
- [ ] Baseline. The parent's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that a job request with only a name still runs, and the shipped `app_op` tests pass unchanged.

@merge

## Carry a unit's own size as CT-23 format 3 (A1)

Phase 0, the dummy unit end to end. Part A slice A1, Part A AD-108, Level 0 AD-18. Ruling corrections 2 (the unit sizes itself). Real step none. Done when `qmf.risk.unit_intent` parses only format 3, keeps the quantity exact, and the Book door is untouched.

**Depends on.** Nothing.

**Files.**

- [ ] Create `packages/qmf-risk/src/qmf/risk/unit_intent.py` and `packages/qmf-risk/tests/test_unit_intent.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/__init__.py` (the export only). `packages/qmf-risk/src/qmf/risk/door.py` stays untouched.

**Build.**

- [ ] Write `UnitEntryIntent`, `UnitExitIntent` and `parse_unit_intent` with the fields of Part A `CONTRACTS.md` section 4.4. The quantity is an exact lot value, never a float, because `tools/money_path_scan.py` fails a float that reaches a quantity or a price.
- [ ] An amendment may tighten a stop and never widen it.

**You see.**

- [ ] Nothing yet. The size a unit chooses can now travel to the node without being dropped.

**Verify, unit.**

- [ ] A format-3 entry with quantity, protection and `not_before` round-trips with its size intact. Formats 1 and 2 are refused by the unit parser. The Book door still refuses format 3 and still drops an unknown key (Level 0 `blast-radius.md` item 1, cases C, D, E and F kept as tests). A widening amendment is refused. Run `uv run pytest packages/qmf-risk/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Parse ten format-3 intents generated from the contract table, with every optional field set and then missing. Save `a1-roundtrip.log`. Pass when each round-trips with its quantity unchanged to the last digit.
- [ ] Lane 3. Send one format-3 intent to the Book door's `parse_inbound_intent` and `accept_intents`. Save `a1-bookdoor.log`. Pass when both refuse it as an unsupported capability, as at the parent.
- [ ] Lane 4. `tools/money_path_scan.py` over `packages/qmf-risk/`. Save `a1-moneypath.log`. Pass when it finds no float reaching a quantity or a price.
- [ ] Lane 5. An amendment that widens the stop by one tick. Save `a1-widen.log`. Pass when it is refused with a reason that names the rule.
- [ ] Lane 6. `uv run pytest packages/qmf-risk/tests -q` at the parent and the head. Save `a1-risk.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds to parse one intent.
- [ ] Probe. 10,000 parses of lane 2's intents.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on the money path. The blast-radius fact is Level 0 item 1, the Book door drops an unknown key and refuses format 3, unchanged.

@merge

## Start the scoring core and the result's new shape (B3)

Phase 0, the dummy unit end to end. Part B slice B3, Part B AD-207, Level 0 AD-25 and AD-34 (the core keeps the one lander). Ruling 43 (QMB is a mini app; the referee stays home). Real step none. Done when `qmx-judge` holds the run record and the lander, the `try` kind and `backtest-result` version 2 exist, and PR 204's `land` lives only in `qmx-judge`.

**Depends on.** Nothing.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-judge/` with `pyproject.toml`, `src/qmx_judge/landing.py`, `src/qmx_judge/runs.py`, `src/qmx_judge/tries.py` and `tests/`.
- [ ] Create `qmx-agents/packages/qmx-library/src/qmx_library/kinds/try.schema.json` and edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/backtest-result.schema.json` (version 2, additive).
- [ ] Move `qmb/src/qmb/host/library_landing.py` and `qmb/tests/test_library_landing.py` into `qmx-judge`, and delete the old files in this PR.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` and `qmx-agents/packages/qmx-tools/tests/test_tools.py` (imports from `qmx_judge`), `qmx-agents/pyproject.toml` and `qmx-agents/uv.lock`.
- [ ] Edit `tools/test_all.py` and `tools/ci.py` so `just ci` runs the new package's tests and its `fmt-check`, `lint` and `types`. Both files list every suite by name, so a new package is otherwise never run (CHECKED, `tools/test_all.py`, `tools/ci.py`).

**Build.**

- [ ] Write the run record and the lander with `open`, `close` and `fail`, the `try` kind, and `backtest-result` version 2.
- [ ] Move `land` in, migrate its callers, and delete its old home in the same PR.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] With a fake tester, open lands one `try`, close lands one `backtest-result` with its three edges, fail lands `status = killed` with no measures, and a second close changes nothing. Run `cd qmx-agents && uv run pytest packages/qmx-judge packages/qmx-library/tests packages/qmx-tools/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. The fake tester's open, close and a repeated close on a throwaway folder. Save `b3-land.log`. Pass when the Library holds one `try` and one `backtest-result` with three edges, and the repeat adds nothing.
- [ ] Lane 3. An old version 1 `backtest-result` read back at the head. Save `b3-v1read.log`. Pass when it reads unchanged.
- [ ] Lane 4. Grep the repo for importers of `qmb.host.library_landing`. Save `b3-importers.log`. Pass when none is left.
- [ ] Lane 5. `backtest_results` from a chat for the landed result. Save `b3-tool.log`. Pass when it answers with the result id.
- [ ] Lane 6. `just ci`'s suite list at the head. Save `b3-suites.log`. Pass when `qmx-judge` appears in the suite table with its count.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one close.
- [ ] Probe. Lane 2 at the head, and PR 204's `land` on the same fixture at the parent, interleaved.
- [ ] Baseline. The parent's `land`, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the moved `land` passes its shipped test in its new home.

@merge

## Write the unit document and its schema (A2)

Phase 0, the dummy unit end to end. Part A slice A2, Part A AD-102, Level 0 AD-21. Midday ruling 1 (a dummy unit on the real template, any strategy the lead picks). Real step none. Done when `qmx.unit/1` has its typed model, a layer A parser that returns every problem with JSON pointers, a committed generated schema, and the dummy document.

**Depends on.** Nothing. The unit document names no intent type, so it lands in either order with the format-3 PR (R1-A-03).

**Files.**

- [ ] Create `qml/src/qml/unit/{model,parse,schema}.py` and `qml/src/qml/unit/qmx.unit.1.schema.json`.
- [ ] Create `qml/src/qml/unit/templates/dummy-trend-pullback.json` and `qml/tests/test_unit_model.py`.

**Build.**

- [ ] Write the model of Part A `CONTRACTS.md` section 1, the parser, and `schema()`, whose output is committed.
- [ ] Write the dummy unit. It trades EURUSD and XAUUSD on M15. An EMA trend filter, an RSI cross back from a low that follows its own history, entry at the next bar's open, a stop beyond the last swing, a 2R target, a 48-bar time-out, a 0.5% fixed-fraction sizer, and a trend floor that follows its own record. Its sizer and exits are labelled placeholders.

**You see.**

- [ ] The written form of a unit exists, with a real example he can read.

**Verify, unit.**

- [ ] The dummy parses with zero problems. Ten malformed documents give the expected problem kinds and pointers. The committed schema equals `schema()`. The schema accepts the smallest document that `qmx-library/tests/test_view.py`'s `filled_from` builds. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Parse the dummy at the head. Save `a2-dummy.log`. Pass when it has zero problems.
- [ ] Lane 3. The ten malformed documents. Save `a2-malformed.log`. Pass when each gives its expected problem kinds with pointers, all at once.
- [ ] Lane 4. Validate the dummy and the Library's schema-minimal unit against the committed schema with the `jsonschema` package's 2020-12 validator. Save `a2-schema.log`. Pass when both validate.
- [ ] Lane 5. Regenerate the schema and diff it with the committed file. Save `a2-regen.log`. Pass when the diff is empty.
- [ ] Lane 6. `uv run pytest packages/qmx-library/tests/test_view.py` in `qmx-agents` at the head. Save `a2-libview.log`. Pass when it passes unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds to parse the dummy.
- [ ] Probe. Lane 2 repeated 1,000 times.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is BR-A1, the Library's every-kind test saves its schema-minimal unit.

@merge

## Let QMB trade from Library data and a request written as data (B4)

Phase 0, the dummy unit end to end. Part B slice B4, Part B AD-204, AD-205, handoff `tracker/qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md` "What QMB needs" items 1 and 2. Ruling 38 (enhance QMB, keep what works). Real step none. Done when the trading replay takes typed partitions and execution inputs named in a JSON request, and its trades equal the receipts path's on the same rows.

**Depends on.** Nothing. The fixture bot proves the path, and units arrive later with the shared unit handler.

**Files.**

- [ ] Edit `qmb/src/qmb/host/replay_execution.py` (a typed-partition entry beside the CT-10 receipts path) and `qmb/src/qmb/host/replay_request.py`.
- [ ] Edit `qmb/src/qmb/execution/binder.py` and `qmb/src/qmb/execution/adapters.py`.
- [ ] Create `qmb/tests/test_typed_execution.py`.

**Build.**

- [ ] Add the typed-partition entry and a request that names its data and execution inputs as JSON. The receipts path stays as built.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] The fixture bot's trades over two typed months equal the receipts path's on the same rows. A request built only from JSON trades. QMB's house rules hold. Run `uv run pytest qmb/tests/test_typed_execution.py qmb/tests/test_replay_execution.py qmb/tests/test_qmb_scaffold.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. The fixture bot over two typed fixture months through both paths. Save `b4-parity.log`. Pass when the two trade lists are identical.
- [ ] Lane 3. A request built only from a JSON file. Save `b4-json.log`. Pass when it trades the same list.
- [ ] Lane 4. `uv run pytest qmb/tests/test_qmb_scaffold.py` at the head. Save `b4-scaffold.log`. Pass when QMB's house rules pass.
- [ ] Lane 5. A request naming a partition that does not exist. Save `b4-missing.log`. Pass when it refuses by name before any trade.
- [ ] Lane 6. `uv run pytest qmb/tests -q -k "not slow"` at the parent and the head. Save `b4-qmb.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the two-month replay.
- [ ] Probe. Lane 2, both paths, interleaved.
- [ ] Baseline. The receipts path, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the CT-10 receipts path is unchanged, by its shipped replay tests.

@merge

## Give every number a measure and a market (A3)

Phase 0, the dummy unit end to end. Part A slice A3, Part A AD-103, Level 0 AD-9 and AD-22. Ruling 10 (QML first, "a small mistake in there is very costly"). Real step none. Done when `qml.numbers` holds `NumberSpec`, the measure vocabulary, conversions through an instrument record and checker layer C, with fixture records.

**Depends on.** A2.

**Files.**

- [ ] Create `qml/src/qml/numbers/` and `qml/tests/test_numbers.py`.
- [ ] Create `qml/tests/fixtures/records/{eurusd,usdjpy,xauusd}.json` with the keys of Part A `CONTRACTS.md` section 2.3 and the nine-value class enum. Part C's real records replace them in A7's wiring.

**Build.**

- [ ] Write `NumberSpec`, the measure vocabulary with its `UnitKind` table, conversions through an instrument record, and layer C.

**You see.**

- [ ] Nothing on screen. A stop can no longer mean ten times what was intended on another market.

**Verify, unit.**

- [ ] Broken documents 1 and 3 give one typed error each at the right pointer. A 20-pip stop converts on EURUSD and errors on XAUUSD. One distance through the EURUSD, USDJPY and XAUUSD records compares equal in ATR multiples (QML-05). Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Convert a 20-pip stop on each fixture record. Save `a3-pips.log`. Pass when EURUSD converts and XAUUSD answers a typed error that names the missing pip definition.
- [ ] Lane 3. One distance through the three records in ATR multiples. Save `a3-atr.log`. Pass when the three are equal.
- [ ] Lane 4. Broken documents 1 and 3. Save `a3-broken.log`. Pass when each gives exactly one typed error at its expected pointer.
- [ ] Lane 5. Compare the fixture records' keys with Part A `CONTRACTS.md` section 2.3 and Part C `RECORDS.md` section 2 by script. Save `a3-keys.log`. Pass when every key QML reads appears in both under the same name.
- [ ] Lane 6. `uv run pytest qml/tests -q` at the parent and the head. Save `a3-qml.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds for one conversion.
- [ ] Probe. Lane 2 repeated 10,000 times.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on units of measure. The blast-radius fact is that QML's 385 shipped tests stay green.

@merge

## Give journals one envelope, typed kinds and one writer (B8)

Phase 0, the dummy unit end to end. Part B slice B8, Part B AD-208 and AD-209, Level 0 AD-27. Ruling 51 (the Library is the centre; do not ruin its core) and ledger J-01 (journals in depth). Real step none. Done when one envelope, the typed kinds, the append path with record ids that survive a re-run, and the read-only committed reader exist in `qmf-data`, and the shipped Windows refused-row bug is fixed.

**Depends on.** Nothing.

**Files.**

- [ ] Create `packages/qmf-data/src/qmf/data/journal_envelope.py`, `packages/qmf-data/src/qmf/data/journal_kinds/`, `packages/qmf-data/src/qmf/data/journal_writer.py` and `packages/qmf-data/src/qmf/data/journal_reader.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/store/engines/typed.py` (the `record` text column, and the writer closes its file when a row is refused) and `packages/qmf-data/src/qmf/data/series.py` (the `journal-*` rule).
- [ ] Create `packages/qmf-data/tests/test_journal_writer.py`, `packages/qmf-data/tests/test_journal_partition.py`, `packages/qmf-data/tests/test_refused_row.py` and `packages/qmf-data/tests/test_committed_reader.py`.

**Build.**

- [ ] Write the envelope with Level 0 AD-27's fields, and the kinds, `lifecycle` and `state` from Part A's contract shapes, `node_lifecycle`, and the reading body's `source`.
- [ ] Write `append`, `append_series`, the record-id rule with its repeat drop and `determinism_break` warning, the key-token rule, bundle mode, staging months as journal partitions, and the committed reader.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] A second writer on a stream is refused. A refused append is never dropped silently. A slice's `signal`, `calibration` and `state` rows appended twice land once. The refused-row test returns a typed refusal on Windows. The committed reader leaves a stream with a line in flight byte for byte as it was. An id with `@` maps to its fixed token. Run `uv run pytest packages/qmf-data/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. Two writers on one stream in two processes. Save `b8-twowriters.log`. Pass when the second is refused.
- [ ] Lane 3. Rows appended twice, then a repeat with a changed body. Save `b8-repeat.log`. Pass when the rows land once and the changed repeat is kept out with a `determinism_break` warning.
- [ ] Lane 4. On Windows, a refused row followed by deleting its file. Save `b8-refused.log`. Pass when the delete succeeds, where the parent's writer held the file open.
- [ ] Lane 5. The committed reader on a stream with a line in flight. Save `b8-reader.log`. Pass when the file's hash is unchanged afterwards.
- [ ] Lane 6. `uv run pytest packages/qmf-data/tests` at the parent and the head. Save `b8-qmfdata.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Rows per second for `append`.
- [ ] Probe. 100,000 `signal` rows appended at the head, and the same rows through the shipped typed store at the parent, interleaved.
- [ ] Baseline. The parent's typed store, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because journals record trades. The blast-radius fact is that the shipped reader truncated a stream with a line in flight and the committed reader does not (Part B's `br_reader_truncates` proof, `R1-FIXES-X1-B.md`).

@merge

## Load blocks one way and build the dummy's blocks (A4)

Phase 0, the dummy unit end to end. Part A slice A4, Part A AD-109, Level 0 AD-47 (one block loader). Ruling 10. Real step none. Done when the block protocol, the one loader and the dummy's ten blocks exist with golden tests, and placeholder blocks carry `origin: placeholder`.

**Depends on.** A3.

**Files.**

- [ ] Create `qml/src/qml/blocks/api.py` and `qml/src/qml/catalogue/loader.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/<entry>/1/block.py` and `entry.json` for `ema@1`, `roc-of-series@1`, `rsi-cross-back@1`, `market-next-open@1`, `swing-stop-buffer@1`, `target-r-multiple@1`, `time-exit-bars@1`, `fixed-fraction-at-stop@1`, `percentile-of-own-history@1` and `trend-floor-from-record@1`.
- [ ] Create `qml/tests/test_loader.py`, `qml/tests/test_stdlib_blocks.py`, the golden fixtures in `qml/tests/golden/`, and their generator `tools/dictionary/golden_talib.py`, which alone imports TA-Lib 0.7.1.

**Build.**

- [ ] Write the protocol and the loader. The loader checks every pinned source against its fingerprint (line endings ignored), then compiles it, and returns every problem at once.
- [ ] Write the ten blocks. The sizer and the three exits are placeholders.

**You see.**

- [ ] Nothing on screen. The dummy's parts exist as tested pieces.

**Verify, unit.**

- [ ] A missing block, a fingerprint mismatch, a CRLF copy (same fingerprint as LF) and a module without `BLOCK` each give their problem kind, all at once. Golden values within the golden tolerance, the cut-against-full test at sampled bars, warm-up values missing and not zero, the settle length recorded, and a week of replayed M1 updates inside each block's state bound with the last tenth's median time per update within `update_time_growth_tolerance` (1.5 times) of the first tenth's, both medians printed (QML-04). Run `uv run pytest qml/tests -q` and `uv run pytest packages/qmf-indicators/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Load the ten blocks from a folder with one missing, one mismatched, one CRLF copy and one module without `BLOCK`. Save `a4-loader.log`. Pass when all four problems come back at once and the CRLF copy matches its LF fingerprint.
- [ ] Lane 3. Each block against its committed TA-Lib golden values. Save `a4-golden.log`. Pass when every value is within the golden tolerance.
- [ ] Lane 4. A week of replayed M1 updates through every block. Save `a4-bounds.log`. Pass when no block's state passes its bound and every growth ratio is under 1.5.
- [ ] Lane 5. Cut against full at 50 sampled bars. Save `a4-cut.log`. Pass when they are equal at each bar.
- [ ] Lane 6. `uv run pytest packages/qmf-indicators/tests -q` at the parent and the head. Save `a4-indicators.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Median microseconds per update in the first and last tenth of a week of M1.
- [ ] Probe. Lane 4.
- [ ] Baseline. The first tenth's median.
- [ ] Rule. Fails when the last tenth's median is more than 1.5 times the first tenth's (`update_time_growth_tolerance`).

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is that the loader is the only code that uses `importlib` or `exec` on block source, and the scan still bans them in agent-written blocks (Level 0 AD-47).

@merge
