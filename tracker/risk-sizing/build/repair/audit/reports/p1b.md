VERDICT: REPAIR

## 1. What this part is for

This part gives every unit one answer to "is this edit a new version or a new unit", and one record of where it stands on each market (draft, tested, paper, live, stopped), where only his click moves it toward money. It keeps a unit honest across restarts and checker changes. It holds the dictionary's new page form, the checker for those pages, the search agents use before writing code, the port of the 239 old entries, and the one click that publishes them. It records instrument, venue and account facts as versioned Library items. It also writes the risk session's socket: the contracts a risk block must pass, and the list of everything that is still a stand-in. It does this as pure functions in QML, small scripts under `tools/`, and one host route.

## 2. Counts

35 of 35 files opened. About 7,750 lines read in those files, plus the design and the code they call. 76 test functions read. 5 tests could go now, 7 more if p1b-7, p1b-9 and p1b-10 are cut. Findings: 1 must, 16 should (4 of them test deletions), 5 leave. Lines that could go: 526, of which 449 only if he agrees to cut the three unused scripts. Plain-version guess: about 3,400 lines of product against 3,925 today. That is a judgement, not a measurement.

## 3. Paths traced

**A dictionary exit block to a closed trade.** Entry, checker, compile, running unit, exit intent. This is where the serious problem is. Six of the nine shipped exit blocks pass the checker, the compiler and the slot contract test, and then do nothing in a running unit. Three never fire, three stop the unit trading. Only the placeholders the dummy uses, the stop, the target and the time exit, work. See p1b-1 to p1b-4.

**A Stats record to a page an agent finds.** Frozen seed, port, 239 drafts, one collection, his click, `blocks_find`. The port and publish are sound. What agents then get is weaker: every page shows status None (p1b-14), the matcher attaches ordinary sentences to wrong pages (p1b-13), and a colliding name can be saved (p1b-15).

**His click to a lifecycle move.** Host door, `PRINCIPAL`, the route, `fold`. Sound. Only the principal `operator` moves anything toward paper or live, and a later stop is never cleared by an earlier click. One narrow clock corner is left at p1b-16.

**A checker change or a restart to what the unit does.** Restart is sound: `restore_unit` starts cold with its reason and the node calls it (`qmn/app/runtime.py:1390`). A checker change is not: nothing is ever stored for the re-check to read (p1b-7), and it would not notice a changed rule anyway (p1b-6). The warm-up seam check has no caller (p1b-8).

## 4. Sections

All sections here are in the original 73, or a fix. None is marked ADDED, so keep, fold or cut does not arise, apart from the fix below.

| Id | Kind | Verdict | Blast-radius fact, and how far proved |
| --- | --- | --- | --- |
| A9 | original | partly. Rows, `classify`, `diff` and the machine all work; the table decides nothing, because nothing calls it (p1b-5) | His click is principal `operator`: held, level 4. `context.py:59-70` read; `test_publish_collection.py` shows `Caller("user")` publishes and five others get 403; `test_lifecycle.py` 25 passed |
| A10 | original | partly. Cold start met; seam, environment and upgrade are written with no caller; re-check works only on a folder nothing writes | QML's tests stay green with the changed `protocol/unit.py`: held for `test_runtime_care.py` (28 passed), level 4; whole QML suite is under Needs a long run |
| C-02 | original | met. The record files stay run artifacts, which ruling TR:49 and `venue_records.py:17` cover | New kinds are schema files with no code change: held for `test_market_kinds.py` (16 passed), level 4; the shipped Library suite was not rerun by me |
| A11 | original | partly. Model, checker, status script, roles, data levels, index and rows exist; the checker skips QML-01 and QML-03 for most agent paths, status is not written, matching is wrong at full size | Other components save as today: held, level 4. A plain `component` saved on a real store, and a marked one claiming `native` with no source was refused with the reason |
| fix-phase0 | fix | met; keep | The rename cleared the clash: level 4, `test_unit_identity.py` 28 passed, nothing in `qml` or `tools` names the old file |
| A12 | original | met. 239 parsed, 239 drafts, 0 lost, rerun the same, one click publishes | Same per-item publish and checker: held, level 4. `test_publish_collection.py` 4 passed, and my real store published 239 of 239 in 11.6 s, a unit member refused as his single publish refuses it |
| A15 | original | partly. Contracts and the rip-out list exist; passing the exit contract does not mean an exit can run (p1b-1, p1b-2) | The dummy checks with zero errors: held, level 4. `exit_proof.py` shows `errors=[]` |

A15 says five placeholder bindings and the code has four. That is the plan's slip, not the code's; the PR says so and my real-store run agrees.

## 5. What is fine

- `qml/lifecycle/machine.py`. Every move by every actor matches the design's table. Only `operator` moves toward paper or live, whatever the kind of actor claims. Replayed journals fold to the same answer. A stop stepping back on one writer's clock is handled.
- `qml/identity/diff.py` and `table.py`. I walked every field of the unit model: each is diffed or deliberately left out. A label his table lacks counts as a new unit. The labels are correct; only the caller is missing.
- `restore_unit` and its cold reasons. A snapshot from another fingerprint, schema or interpreter, or of the wrong shape, starts cold and equals a fresh start.
- `tools/dictionary/port_stats.py`. `test_dictionary_port.py` 8 passed. Nothing is lost, no role is guessed, no class is claimed `native`, and a CRLF checkout gives the same result.
- `land_port` and `land_seed`. Once per store, a landing cut short finishes, his edits are kept.
- `publish_collection.py`. Refuses every principal but his before reading anything, a second click writes nothing, an unknown id answers 404.
- `tools/qml/placeholders.py`. Its test uses a hand-built Library, so I ran it on a real store: one published unit, 4 bindings, 4 numbers, drafts left out. Those match `RISK-SIZING-PLACEHOLDERS.md` rows 1 to 4.
- `refresh.py`. No keys, reads prices from text never binary floats, skips inverse contracts with a counted reason, and a failing exchange fails the whole step.
- `catalogue/datalevel.py`, `roles.py`, and the kinds' key parity. Correct and small.
- The compiler refuses bound halts loudly (`halts_not_built`), so a unit cannot believe a halt is running when it is not.

## 6. Must and should findings

- p1b-1 must. Three shipped exits pass the checker and compiler and never fire in a running unit.
- p1b-2 should. The slot contract test passes them on evidence no host gives.
- p1b-3 should. Shipped trailing stops, bound as the stop, stop the unit trading at all, and none can trail. Fails safe.
- p1b-4 should. No exit block can ask for a partial close or a stop move, though the contract and the risk session's list say it can.
- p1b-5 should. The identity table in Settings decides nothing; no later plan section gives it a caller.
- p1b-6 should. The checker's version does not change when a rule changes, so the re-check says "current".
- p1b-7 should. The re-check script reads a folder nothing writes; wire it or cut it.
- p1b-8 should. Nothing calls `seam_check`, so a bad warm-up join is never flagged.
- p1b-11 should. A block with no golden cases earns `implemented` with no cut test.
- p1b-12 should. The settle check, QML-03, is not in the entry checker.
- p1b-13 should. The sentence matcher is wrong at full dictionary size; the test narrows its corpus to pass.
- p1b-14 should. All 343 published pages show status None while QMX runs.
- p1b-15 should. An entry can be saved under a name another entry holds.
- p1b-19 to p1b-22 should. Five tests to delete.

These cluster into three repairs. p1b-1 to p1b-4 are one exit-host change, with one test fed what the host really passes. p1b-11, p1b-12 and p1b-15 are one checker change. p1b-6 and p1b-7 fall together if the script is cut.

## 7. Test verdict

Worth having, mostly. These are behaviour tests with literal expected values, and the lifecycle, port and publish tests would catch real defects. No test passes on nothing. The weakness is in three places where a test proves less than its name says. The socket test feeds evidence no host gives (p1b-2). `test_entry.py:151-154` narrows its corpus, so the matcher and search look right (p1b-13). The re-check test invents a checker version (p1b-6). 5 tests can go now, for repeating another test or pinning a list (p1b-19 to p1b-22). 7 more go only if the unused scripts are cut: 3 re-check, 2 upgrade, 2 environment. I ask for no new test beyond one for p1b-1, which has none: drive a unit with a bound `exit_action` block and assert it fires.

## 8. Golden and reference data

- `talib-0.7.1.json` (6 cases) is independent: TA-Lib itself, except the rolling percentile, which is numpy. I did not regenerate it.
- `indicators/talib-0.7.1.json` (71 cases). About 50 come from TA-Lib calls, some composed from them (MACD, Hull). About 20 are formulas the builder wrote in the generator (FrAMA, VIDYA, Alligator, VWAP, Heikin Ashi). The second group is separate code from the block, by the same author reading the same source.
- `statistics/reference.json` (27 cases). `arch` and `statsmodels` where named, independent; the rest are formulas in numpy, same author.
- `beyond-fx`. Clocks are built from `zoneinfo`, independent; range pressure from TA-Lib, independent; market-profile cases are the builder's rebuild of a published rule, per bar.
- `exits-and-halts/reference.json`. No outside library at all. Separate code that recomputes from the whole history, not a separate source, so a misread rule would be misread in both. I regenerated it in memory and it equals the committed file.

## 9. The ten edge-case functions walked

`fold`, `_refusal`, `diff` with `classify`, `recheck`, `compute_status` with `_implementation`, `match`, `publish_collection`, `land_port`, `instrument` in `refresh.py`, `published` with `uses` in `placeholders.py`. Their unhandled paths are p1b-16, p1b-6, p1b-11, p1b-12 and p1b-13. The other five had none that reach him.

## 10. Set aside for him

- Parked is one way in the design: once a version is parked, even to admit a newer one, it can never return to paper or live, so rolling back means making a new version. I assumed that stays as designed.
- Whether to wire the re-check script to his Library, or cut it, since publish and compile already re-check every time. I assumed it stays until he says.

## 11. Needs a long run

- `source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && "$AUDIT_ROOT_ENV" -m pytest qml/tests -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p1b/long1` proves A10's fact whole.
- `source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-library && "$AUDIT_AGENTS_ENV" -m pytest tests -q -p no:cacheprovider --basetemp=D:/Temp/audit/p1b/long2` proves C-02's fact whole.
- `source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-host && "$AUDIT_AGENTS_ENV" D:/Temp/audit/p1b/lib_proof.py` reprints the evidence for p1b-13, p1b-14 and p1b-15. It may pass 2 minutes. Its first complete pass through those lines printed the values in the findings file; I did not keep that output in a file.

## 12. Not read

Nothing in `files.tsv` was left unread. As the method says, the seed data and wave entries in `not-read.tsv` were not read line by line, and of the golden JSON files I read only the headers and case counts.

## 13. Skills that changed a decision

- `blast-radius`: ran the rip-out and publish on a real store rather than trusting the hand-built fixture, and both held.
- `lens-verification-gap`: its missing-adoption shape found p1b-5, p1b-8 and p1b-14, where the code is right and nothing uses it.
- `lens-edge-case-hunter`: walking `fold` by clock produced p1b-16 and cleared the promised case.
- `principle-prove-it-works`: driving a real unit with a swapped exit turned a suspicion into p1b-1, the only must.
- `principle-test-behavior-not-implementation`: decided the five test deletions and kept the rest.
- `principle-laziness-protocol`: led to "wire or cut" on the three scripts with no caller.
- `code-review`, Spec axis: holding the socket to `CONTRACTS.md` section 4.3 found p1b-4.
- `principle-minimize-reader-load`: changed nothing; `machine.py` and `diff.py` read well.
