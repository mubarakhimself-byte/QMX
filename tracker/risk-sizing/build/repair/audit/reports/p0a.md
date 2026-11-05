VERDICT: REPAIR

## 1. What this part is for

This part is the written form of a unit and the library that makes it run. A unit is one JSON document saying what it trades, which blocks decide entries, and how each number may move. QML checks that document in layers, loads the pinned blocks by fingerprint, and compiles it. A hosted unit then takes one instant at a time and returns exact format-3 orders, decision rows and calibration rows. The dummy trend pullback proves it end to end, including one number that tunes itself from its own closed trades. Size travels as its own contract, so the old Book door can never drop it.

## 2. Counts

Files opened 47 of 47 (two by diff), lines read about 9,000, test functions read 102, hollow or deletable tests 6, findings 4 must, 14 should (4 of them test-delete rows), 6 leave, lines that could go 70 (all tests), plain-version guess about 5,500 of the about 6,300 new product lines (labelled guess).

The size is honest. No slop in my sections reaches 30 lines. The largest candidate, `shape_gap` in `protocol/unit.py` at about 90 lines, is A10's and left to its auditor.

## 3. Paths traced

1. **Document to compiled unit** (`parse`, `check_layers`, `compile_unit`). Shape, references, numbers and fingerprints are sound. The defect is what falls between check and compile: the compiler refuses some things it does not run and silently drops others (p0a-1, p0a-3, p0a-7).
2. **Bar to format-3 order** (`on_instant`, `update`, `exits`, `entries`, `enter`, `accept_unit_intents`). On the dummy this is right: exits before entries, warm-up suppressed, opposite signals dropped, only its own positions exited, quantity exact, `not_before` set, stop on the loss side. Off the dummy's exact exit shape it breaks (p0a-2, p0a-5, p0a-8).
3. **Closed trade to moved number** (`own_journal`, `calibrate`, `trend-floor-from-record`, the floor on ROC). Cadence, minimum count, shrink, one step, inside the range, wait for flat and motion off all work, and the arithmetic matches the design's worked example. Short trades are not bucketed by strength (p0a-4). The tests feed long trades only.
4. **Block source to running code** (`check_block`, `load`). Fingerprint before compile, LF normalising and every problem at once are sound. The agent rules rest on a word the author writes, and `check` itself runs the code (p0a-10).

## 4. Sections

| id | origin | verdict | blast-radius fact | keep/fold/cut |
| --- | --- | --- | --- | --- |
| A0 | original | met | BR-A3, no top-level caller of the 23 names: held, level 4 (`test_surface_old_law.py`, 26 passed, its repo scan reads over 1,000 files) | n/a |
| A2 | original | met | BR-A1, the Library's every-kind test saves its smallest unit: held, level 4 (`test_view.py` 4 passed; `test_unit_model.py` passed) | n/a |
| A1 | original | met | Level 0 item 1, Book door unchanged: held, level 4 (`door.py` diff empty; cases C to F passed in the 32 of `test_unit_intent.py`) | n/a |
| A3 | original | met | QML's 385 shipped tests stay green: not rerun whole, see section 11; the new numbers tests pass, level 4 | n/a |
| A4 | original | met | The loader alone runs block source, and the scan bans importlib and exec in agent blocks: held. Level 2 for the loader (grep: `loader.py:112` is the only `exec` in QML; QMB's `importlib` in `operator_replay.py` loads old bots, not block source). Level 4 for the scan (`test_check_layers.py`, 364 passed) | n/a |
| A5 | original | partly: the dummy compiles, runs deterministically and moves its number on a long-only journal, but `direction` is ignored, short trades are misread, and day-close cadence is not built (disclosed) | BR-A4, `construct_bot` refuses at the first sized intent: held, level 4 (`test_compile_dummy.py`, 12 passed) | n/a |
| A6 | original | partly: layers A to F, counts first, grouping, `problem_set`, `no_progress`, layer G and the corpus gate all work (`tools/ci.py:59`), but `check` can throw (p0a-6) and layer D is short (p0a-14) | `evaluate_layer2` unchanged and pure: held, level 4 (`layer2.py` diff empty; twins pass in `test_layer_g.py`) | n/a |
| fix-mockscan | fix | met: six comment markers and two reflows, nothing else | `test_main_is_clean_on_the_real_workspace` passed, level 4 | keep |

No section in this part is ADDED. Measured: `check` on the dummy 2.2 s against the 8 s budget; one month drive 1.3 s.

## 5. What is fine

- **The format-3 contract** (`unit_intent.py`). Strict parser, unknown keys refused, floats impossible, quantity exact to the last digit, sides checked, tighten-only amendment with a real caller at `qmn/src/qmn/app/runtime.py:1646`. Its size is justified. Its tests are good.
- **The old-law subtraction** (A0). The 23 names are gone from the top level and still import from their submodules.
- **The document model, parser and schema** (`unit/`). One model drives both, so they cannot drift. It is the best-designed piece here.
- **The numbers layer** (`numbers/`). Measures, records, conversions, exact range checks and clear errors. `distance`, `atr_multiple`, `from_atr` and `value_factor` have no product caller yet, but A3's done line asks for them, so they stay.
- **The loader**. Mismatched source never runs. CRLF and LF share a fingerprint. Every problem comes back at once.
- **The ten blocks**. Goldens, cuts, settle lengths and state bounds pass. Nothing grows with history.
- **The result shape**. Counts lead, a 200-problem answer shows its head in 2,000 characters, and `no_progress` works.
- **Layer G**. The fill model is small, and determinism, restore and the shuffled control are real drives.
- **Restore across a snapshot**. It resumes bar for bar, and another fingerprint starts cold with a reason.
- **Determinism**. Two drives over a month give identical steps.

## 6. Must and should

Must:

- p0a-1: a long-only unit still trades short while the checker says that side never runs.
- p0a-2: any unit with no time exit crashes at its first open position.
- p0a-3: sessions, per-market settings, position limit, stream price and cadence `at` are accepted and silently not run.
- p0a-4: short trades are not sorted by strength, so the self-tuning number moves on a wrong reading.

Should:

- p0a-5: a second stop or per-bar exit is ignored, and two targets refuse every step with an entry.
- p0a-6: `check` throws instead of naming a bad number or rule setting.
- p0a-7: slot roles mean nothing at run time, so a veto works backwards (my reading of veto).
- p0a-8: a unit with no stop passes every check and then never trades.
- p0a-9: `mirror_of` on blocks that cannot mirror passes the checker.
- p0a-10: `check` runs block code in process, and the agent-only rules rest on a self-written label.
- p0a-11: stops round to digits and not to the tick size.
- p0a-12: the sizer receipt always claims zero rounding cost.
- p0a-13: a calibration receipt holds only a trade count, not the statistic.
- p0a-14: layer D does not read transfer status, volume splits or fallbacks.
- p0a-21 to p0a-24: six tests to delete.

p0a-1, p0a-2, p0a-3, p0a-5, p0a-6, p0a-7 and p0a-9 are one cluster: make the compiler refuse what format 1 does not run, and wrap block construction. That is one small PR, about 60 lines. p0a-4 is a few lines on its own.

## 7. Test verdict

These tests are worth having. Of 102 functions, none is truly hollow. Almost all call the real door and assert literal results, and 6 could go (about 70 lines): constant pins and duplicates. His suspicion of too many does not hold for this part. The real weakness is coverage shape: the tests are built around the dummy's exact shape, which is why four must findings passed 102 tests. Journals are long only, every exit set is the dummy's three, and no test sets `direction` to anything but `both` on a two-sided document. The layer G test pins counts its own code produced (8 trades, 85 in the control), so it guards against change and is not independent evidence.

## 8. Golden and reference data

Independent. `qml/tests/golden/talib-0.7.1.json` is written by `tools/dictionary/golden_talib.py`, which imports `talib` and `numpy` and no QML (level 2, I did not rerun it). The committed file names its generator, TA-Lib version and seed, and `test_stdlib_blocks.py` compares against it. The synthetic month is a seeded walk labelled "not evidence", as the plan allowed. Instrument records are fixtures, replaced by Part C's.

## 9. Edge-case functions walked

1. `_Run.enter`
2. `_Run.exits` with `_Core.timer`
3. `_Run.entries`
4. `calibrate` with `_read`
5. `_TrendFloor._edge` and `update`
6. `_FixedFraction.update` with `lots`
7. `parse_unit_intent` with `_check_sides`
8. `check_amendment_tightens`
9. `compile_unit` with `_motion` and `_warm_up`
10. `restore_unit` with `_cold_reason` and `load`

Clean: 6, 7, 8 and 10. One small note on 4: a trade reported late, with a close time before the last one read, is passed over for good. Low harm, no row.

## 10. Set aside for him

- Should a unit be able to trade with no price stop at all, as UT-08 says? Today's sizer needs a stop, so it also needs another sizer. I assumed yes, and that the risk session supplies that sizer.
- For the risk session, not a finding: the placeholder sizer divides account money by a loss in the quote currency, so it is right for EURUSD and XAUUSD on a USD account and wrong for USDJPY. It belongs on the rip-out list.

## 11. Needs a long run

- QML's shipped tests (A3's fact): `source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && timeout 1200 "$AUDIT_ROOT_ENV" -m pytest qml/tests -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p0a/long/t`

## 12. Not read

Nothing in `files.tsv`. Data in `not-read.tsv` was only sampled: the dummy template read whole, the USDJPY record and twin number names checked, the golden header read. What a real agent can reach through the `unit_check` row is A8's and was not walked.

## 13. Skills that changed a decision

- `blast-radius`: made me run each review-gate fact rather than trust the section's lanes, and grade by what reached.
- `lens-edge-case-hunter`: walking implicit branches of exit use and `direction` found p0a-1, p0a-2 and p0a-5.
- `lens-verification-gap`: "what would the tests miss" sent me to shorts in the journal, which found p0a-4.
- `principle-test-behavior-not-implementation`: set which six tests to delete and kept the rest.
- `principle-laziness-protocol`: turned the seven findings into one refuse-at-compile fix rather than seven repairs.
- `principle-minimize-reader-load`: kept `shape_gap` out of my slop list as another section's, and I found nothing else near the bar.
- `principle-prove-it-works`: moved the must findings to running scripts.
- `code-review`: gave the two axes. The smell baseline produced no finding of 30 lines or more.
