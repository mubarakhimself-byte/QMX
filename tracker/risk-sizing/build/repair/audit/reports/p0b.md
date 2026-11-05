VERDICT: REPAIR

## 1. What this part is for

This part lets anyone ask QMX to backtest a unit and get an honest, filed answer. QMB is a mini app with jobs. The core, not QMB, issues the run number, counts the try, checks the unit's behaviour first, lays out the run's files and files the result in the Library. Inside QMB, one shared handler drives the unit bar by bar, the same handler the trading node uses. Every decision and fill is written to one typed journal, with row ids that survive a re-run. Units reach `main` only by his click, after every check passes. The machinery is well built. The real gaps are at its edges: what data and contract terms get into a run, and one silent failure on the live journal.

## 2. Counts

Files opened 67 of 67; lines read about 10,550 (6,167 product, 4,388 test); test functions read 125; hollow or deletable tests 10 (5 of them only if B4 is cut); findings 4 must, 19 should (5 of them test-delete rows), 5 leave; lines that could go 725 product and 547 test; plain-version guess about 5,400 product lines against 6,167 today (a guess, and these files also hold B10, B13 and B14 code).

## 3. Paths traced

- **He asks for a backtest and gets a filed result** (`backtest_run` or `app_op`, then `run_job`, `QmbRun.open`, `Lander.open`, behaviour check, lay-out, job, `close`). The run number, try rows, principal, fingerprint check and landing are sound. The inputs are not: wrong contract record (p0b-1), no record for other markets (p0b-2), no route from his data (p0b-3), no run id during a slow check (p0b-6).
- **A unit trades through the shared handler** (`run_slice`, five hooks, fills, stop, target, partial close, tighten-only amend). Sound. Fills, lot rounding, own positions only and gap fills all hold. R leaves out cash costs (p0b-13).
- **A decision becomes a journal row** (`RunJournal`, `JournalWriter`, bundle files or live stream, committed reader). Sound in QMB, where a refusal fails the run. On the node one refusal silently stops the journal (p0b-4).
- **A crash in the middle of a run** (raise or kill, `fail`, breaker, back-off restart). Sound for a process kill. A host restart leaves the run open for ever (p0b-14). A raising block is treated as a crash (p0b-16).
- **A unit reaches `main`** (`_admit` on branch, merge, advance and resolve; `put` refuses it on `main`; `his_click` at the control door). Sound.

## 4. Sections

| Id | Origin | Verdict | Blast-radius fact, held or not, level | Keep/fold/cut |
| --- | --- | --- | --- | --- |
| B3 | original | met | Moved `land` passes its test in its new home: held, level 4 (2 passed). It has had no production caller since B6 (p0b-18) | - |
| B8 | original | met | Committed reader leaves a line in flight alone: held, level 4 (test passed). Shipped reader truncates: not rerun, level 2 (`jsonl.py`, cited in `journal_reader.py:5-7`). Refused row: level 4 | - |
| B4 | original | met as written; nothing real calls it (p0b-17) | Receipts path unchanged: level 4 for the parity test (5 passed); `test_replay_execution.py` is in section 11 | - |
| B1 | original | met | A name-only request still runs: held, level 4 (`test_app2a_app_op.py`, 3 passed, unchanged) | - |
| C-05a | original | met | An app with no restart stays down: level 2 (`supervisor.py:900-906`). Its test installs an app, see section 11 | - |
| B5 | original | met; AD-202's restart reconcile was never planned (p0b-14) | App with no lander lands as today: level 2 (`supervisor.py:1299-1300`, `artifacts.py:235-242`). C-27a's "never land a ref twice" changed this path later and is its auditor's | - |
| A7 | original | met | Kinds patched, Library holds: level 4 for `test_unit_library.py` (8 passed), read for the rest | - |
| B5b | original | met, except `adapter.py` still imports `construct_bot` (p0b-21) | `run_slice` drives the handler through five hooks: held, level 4 (9 passed) | - |
| A8 | original | met; the plan's exact CLI line fails on the raw template, disclosed (p0b-28) | Harness keeps its baseline with derived groups: level 2. `test_unit_tools.py` level 4 (8 passed). CLI 3.5 s against the 8 s budget | - |
| B6 | original | partly: must p0b-1, p0b-2, p0b-3; should p0b-6, p0b-8, p0b-9, p0b-12, p0b-16 | Tool count keeps `backtest` at 4: held when B6 landed. At this commit the toolset has 5 rows, because B13 added `judge_run` on purpose. Level 2 (`catalog.py`) | - |
| B9 | original | partly: `motion = both` fails from the doors (p0b-5); journal blobs and calibration rows are sound | Writer drops a repeated row by id: level 3 (`journal_writer.py:364-369`, read with its test) | - |
| fix-qmbapp | fix | met, but its precedence goes against [TR:57] (p0b-10) | Its PR's tests read; suite in section 11 | keep, it made the app suite honest |
| fix-judge-types | fix | met | No behaviour change, by reading the diff of `_fields` | keep, one helper replaced two copies |

No section here was marked ADDED. The Lab's adapter in B6's done line: no Lab code exists in this build. By design its default adapter is `app_op`, which is tested, so I count that half as met.

**Invariants.** Held: a tester mints no run id, and the lander refuses a bundle that answers another run. Held: one run path through `run_job`. Held: a chat's principal is kept and the writer is the operator. Held: only his door publishes. Held: one writer per stream, repeats dropped, nothing truncated by readers. Not held: AD-202 step 1 (data through the market-data door with the study's holdout), LD-05 and LD-08 (p0b-3, p0b-8, p0b-11). Not held: JR-13 on the node (p0b-4). Not held: AD-15 on results (p0b-12).

**Scope.** No scope creep found. Dead code: p0b-17 and p0b-18.

## 5. What is fine

- **The lander.** Open, close and fail are idempotent by run id, a retry writes nothing, it refuses every problem at once before any try lands, and a killed run lands `killed` with no measures.
- **Layer G gate.** It keys on the fingerprint the core compiles, so a caller's pin can fail a run but cannot poison or skip a G record. A failed check gives no verdict and the next run checks again.
- **Run folder safety.** A bundle path outside the folder is refused and every file is checked against its fingerprint.
- **The shared handler's money mechanics.** Round down to lot step, skip below minimum with a journaled reason, close only own positions, tighten-only stop, partial close keeps the rest and adds up to the position's R. The handler tests use numbers I checked by hand.
- **The adoption path on the node.** I suspected duplicate position ids after a restart. Cleared: adopted positions carry the venue's own name (`qmn/app/runtime.py:1442-1461`).
- **Intents on a market with no bar in the slice.** Suspected lost. Cleared: the unit acts only on markets with a fresh bar, so a minted intent always has its stream in the slice (`qml/protocol/unit.py:512-524`).
- **The journal writer.** Key token rule, record ids, gapless sequence, repeat and determinism break, month files that never reopen, a failed partition that keeps the others. The reason-code table covers every text QML and the handler can write today (checked against `protocol/unit.py` and `numbers/convert.py`).
- **The committed reader.** It only reads, and it leaves a tail line alone.
- **The refused-row fix on Windows.** Writer closes before the refusal, the folder can be removed.
- **The mini-app core changes.** `inputs`, `result`, the lander port and back-off are small and opt-in. A job with `run()` runs as before. Money apps restart only their signed version.
- **A7's kind checks.** Every problem listed, first message kept, a missing checker refuses, and every door to `main` is covered. `Store.put` refuses a unit on `main`.
- **A8's rows and command.** Seven rows on the surface, drafts only, no `bot` or `strategy`, exit 0 and 1 with every problem.
- **CI lists** (`tools/ci.py`, `tools/test_all.py`) include the new suites.

Standards axis, judgement calls with no row because each saves under 30 lines: possible primitive obsession in `_REASON_WORDS`, free text matched back to a code that QML could hand over directly. It is also the easy trigger of p0b-4.

## 6. Must and should

Must:
- p0b-1: QMB trades on QML's fixture contract terms, not his Library record, with no warning.
- p0b-2: a market with a Library record and no fixture cannot be backtested.
- p0b-3: data he downloads can never be backtested; the refusal points at a template that does not make what QMB reads.
- p0b-4: on the node's live journal, one refused row silently stops every later row.

Should:
- p0b-5: `motion = both` fails from the copilot and on a first workflow run.
- p0b-6: first run with a slow check answers no run id.
- p0b-7: the behaviour check holds the whole window in memory.
- p0b-8: results do not say which data they read.
- p0b-9: he cannot backtest one market of a unit.
- p0b-10: a chat's `allow_gaps` beats the study, against [TR:57].
- p0b-11: a study's holdout is not honoured by a run.
- p0b-12: results do not list placeholder blocks, against [US:185].
- p0b-13: R leaves out swap, funding and commission that net money includes.
- p0b-14: a host restart leaves a run open for ever.
- p0b-15: no drawdown, MAE or MFE in R.
- p0b-16: a block that raises crashes the job instead of landing a failed result.
- p0b-17: B4's typed entry has no real caller (650 lines).
- p0b-18: `land` has no real caller (75 lines).
- p0b-23 to p0b-27: test-delete rows, section 7.

## 7. Test verdict

These tests are worth having. Almost all call real code through its public door and assert plain values, and many use a real Library store and a real supervised app. I found none that would pass if the code returned nothing. Only 5 should go regardless (one catalog table pin, one column pin, one duplicate full backtest, two on dead `land`), plus 5 if B4 is cut.

Two warnings. First, several green tests stand just beside a bug: `test_qmb_app.py` has no instrument item in its store (p0b-1), runs a backtest first so the wait test never meets the check (p0b-6), and `test_run_journal.py:347` calls the job past the lander (p0b-5). Second, the big literals in `test_unit_runner.py` and `test_run_journal.py` (8 trades, -114.97, 123 trades, 2168 changes) came from running this code on synthetic data. They catch change, not error, and `test_run_journal.py` says so itself ("Not evidence").

## 8. Golden and reference data

No golden file sits in this part. `not-read.tsv` holds locks, kind schemas, the plugin manifest and a skill. `unit.schema.json`'s fields are compared to QML's generated schema, a relation test that is sound. The handler tests' numbers are independent (hand-checkable). The runner and journal numbers are not independent: the code under test produced them. The conformance pack's goldens are B12's.

## 9. The ten edge-case functions walked

1. `Lander.open`: bad fields, pins, family, run id all refused; `motion = both` passes into the check (p0b-5).
2. `Lander.close`: wrong run id, retry after a partial close, bad file, counted kinds: handled.
3. `Lander.fail`: repeat, after a close, check job: handled.
4. `Supervisor.run_job` and `_job`: raise, no leave, two leaves, app dies, refused close: all fail the run. Host death: unhandled (p0b-14).
5. `QmbRun._bars`: p0b-3, p0b-9.
6. `QmbRun._lay_out`: p0b-1, p0b-2, p0b-10, p0b-11, p0b-22.
7. `UnitSliceHandler._fill_entry`: open position, below minimum, partial fill, gap past stop: handled, the last only costs a spread.
8. `UnitSliceHandler._close`: partial, whole, zero risk, gap: handled; costs outside R (p0b-13).
9. `RunJournal._write`: p0b-4.
10. `JournalWriter.append` with `_BundleSink.write`: refused body, repeat, changed repeat, month roll, failed partition: handled.

## 10. Set aside for him

Nothing. The cut-or-wire choice on B4 follows from how p0b-3 is fixed, and the lead can make it.

## 11. Needs a long run

These install an app environment or run longer than 2 minutes, so I did not run them. Prefix each with `source D:/QMX-worktrees/audit-ship/tools/env.sh && `, and add `-q -x -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p0b/long/t`.

- `cd D:/QMX-worktrees/audit-head/qmx-agents && timeout 1500 "$AUDIT_AGENTS_ENV" -m pytest apps/qmb/tests/test_qmb_app.py`
- `cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-apps && timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_landers.py`
- `cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-apps && timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_restart_backoff.py`
- `cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-engine && timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_app_op_inputs.py` (run once with a node id under a short limit, it printed `OSError: [Errno 22]` from a worker; the shipped `test_app2a_app_op.py` then passed alone. I did not chase it)
- `cd D:/QMX-worktrees/audit-head && timeout 900 "$AUDIT_ROOT_ENV" -m pytest qmb/tests/test_run_journal.py`
- `cd D:/QMX-worktrees/audit-head && timeout 600 "$AUDIT_ROOT_ENV" -m pytest qmb/tests/test_behaviour_check.py`
- `cd D:/QMX-worktrees/audit-head && timeout 600 "$AUDIT_ROOT_ENV" -m pytest qmb/tests/test_replay_execution.py`
- `cd D:/QMX-worktrees/audit-head && timeout 300 "$AUDIT_ROOT_ENV" -m pytest packages/qmf-data/tests/test_journal_writer.py`
- `cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qma-harness && timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_unit_surface.py`

## 12. Not read

Nothing in `files.tsv`. For `how = diff` files I read what changed and around it. I also read parts of `host.py`, `supervisor.py`, `functions.py`, `qmn/app/runtime.py`, `qml/protocol/unit.py` and `replay.py` to trace paths.

## 13. Skills that changed a decision

- `blast-radius`: made me run the host's real lay-out, which turned a guess about records into the level 4 p0b-1.
- `lens-verification-gap`: sent me to what each green test primes, which found the hidden paths in p0b-5 and p0b-6.
- `lens-edge-case-hunter`: the walk of `RunJournal._write` found p0b-4.
- `principle-test-behavior-not-implementation`: kept the list of deletions short, because few tests fail its check.
- `principle-laziness-protocol`: the deletion test on `land` and B4 gave p0b-17 and p0b-18.
- `principle-minimize-reader-load`: read the lander and handler layers and found them acceptable, so no slop row.
- `principle-prove-it-works`: made me time and run the plan's exact CLI line, which gave p0b-28.
- `code-review`: Standards and Spec axes run one after the other, without sub-agents.
