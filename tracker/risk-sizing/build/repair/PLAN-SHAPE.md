# The repair plan's shape, decided by the chief engineer on 5 November 2026

This file holds the decisions. `REPAIR-PLAN.md` beside it turns them into PR sections. Where the two differ, this file wins until someone changes it on purpose, and his newest word wins over both.

Short paths: `A` = `D:/QMX-worktrees/audit-ship`, `P` = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing`.

## What the program is

Repair what the build shipped, foundation first, and leave nothing serious unplaced. All 30 must rows and the three new musts (`core-n1`, `node-n1`, `unit-n1`) have a home here. The old stack stays as it is. Repairs stack on top of it.

- **Root.** `build/us-c14` at `50c83a4e`. Branches `build/repair-NN`, worktrees `D:/QMX-worktrees/bld-repair-NN`, store `D:/QMX-worktrees/repair-ship/`.
- **Nothing lands by itself.** Nothing commits to `engine/base` or `main`. He lands the stack. Where it lands in the end is his, and it comes up only when landing nears.
- **Nothing runs live during repairs.** There is no live version to keep restarting. Real steps on his folder wait for him to land the code.

## Why this order

His word: fix the foundation, then the walls. His ruling: QML first, the node second, the MIS third, with the MIS built before the node. A unit that does what it says comes before a backtest of it. A backtest on real facts comes before a verdict on it. A true verdict comes before anything reaches a node.

## The PRs

Ids `R01` to `R24`. Rows are ids in `A/FINDINGS.tsv`. The source for each repair's cause, safety fact, shape, proof, files and size is the named block of the named grounding report under `A/reports/`. Those reports ran the shapes, so follow them, and check them against code when you build.

### Phase A. Clean ground

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R01 | Clear the dead weight | deletion-5, deletion-8, deletion-9, deletion-10. About 40,700 lines and 5,700 of tests. Touches no product file | `ground-core` K | root |
| R02 | Make the gates tell the truth | whole-repo-1 to 4. Review C-14's four unreviewed commits, 1,542 lines, and PR 327's own diff, and put any real finding in the right PR below | `ground-start` I and K | R01 |
| R03 | Let a repair reach him, and stop an install stalling everything | core-n1 (must), known-2, triage-7, triage-4, triage-5, triage-8, p5c-3, the supervisor stopping an app on a tool timeout (probe first, then decide against his breaker) | `ground-core` A and B, `ground-start` I and New defects | R02 |

A library repair never rebuilds a signed money app under its signed hash. It arrives as a new version for him to sign, so any PR that changes a library in `apps/trading-node`'s lock bumps that app's patch version (call 11).

### Phase B. The unit

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R04 | What a unit cannot run, it refuses | p0a-1, p0a-3, p0a-2, p0a-5, p0a-6, p0a-7, p0a-8, p0a-9, p1a-5, p1a-2 and p1b-1 by refusal, p1b-2, p1a-1 by refusal for volume blocks and session blocks. Bump the compiler format | `ground-unit` A, B step 1, C trap. The trial in `A/reports/ground-long.md` shows one test moves | R03 |
| R05 | Slots tell the truth | p1a-3, N1 of `ground-unit` (price series fed whole bars), the feeder rule and one comparator block, `time` in `resolve` with session blocks still refused, p0a-4, p0a-13, p0a-11, p1a-4 only if it lands here cleanly | `ground-unit` C, D, F | R04 |
| R06 | The dictionary's own checks, and session blocks that follow the market's clock | p1a-4, p1b-11, p1b-12, p1b-13, p1b-14, p1b-15, plan-check-5 (delete `auto_paper`), p1b-6 and p1b-7 (cut the re-check script), p1a-6 with ten new block versions, p1a-7 goes to the risk session | `ground-unit` E, G, H | R05 |

### Phase C. A backtest on his facts and data

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R07 | Backtests read his facts | seams-2, p0b-1, p0b-2, p6-2 (records half), p5d-5, p0b-10, p2-10, and the cached-records trap | `ground-qmb` "A run on his facts", "Study rules" first line | R06 |
| R08 | Backtests read his data | p0b-3, p2-4, p2-2 (label now, wire later), p0b-9, p0b-17 (cut B4's entry), p5d-4, p0b-8, p0b-11, triage-6, the sealed-copy trap | `ground-qmb` "A run on his data" and "Trap", three shapes table | R07 |
| R09 | Long history holds up | derived `bar-m1` beside ticks, p2-9 with triage-2 together (probe a real December first), p2-13, `data_short` | `ground-qmb` same block | R08 |
| R10 | Runs that report honestly | p2-1, p2-16, p0b-5, p0b-6, p0b-7, p2-14, p0b-12, p2-12, p0b-14, p0b-15, p0b-16, p2-15, and costs plumbing: seams-9, p2-8, a cash number beside R with R unchanged, `costs_uncalibrated` in the verdict | `ground-qmb` "Running well", "Costs" | R09 |
| R11 | A judge that cannot be talked round | p2-5, p2-11 | `ground-qmb` "Study rules" | R10 |

### Phase D. Agents can build a unit and backtest it

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R12 | One true verdict, one paper | p6-1, p6-7, p6-3, p6-4, p6-5, p6-15. No engine change | `ground-core` C, D | R11 |
| R13 | Checks with no Library say so, and slow-lane words | p6-2 (template half), p34-9, core-n2, p6-9, p6-12, p6-13 | `ground-core` E, F | R12 |
| R14 | The foundation proof | Add the checks in "What the foundation works means" below that no earlier PR added. Run them all. Then stop and tell him, in plain words, what now works and one thing he can ask the copilot to see it | below | R13 |

**Gate G-FOUNDATION.** The program stops after R14, reports to him and waits for his word. The risk session needs nothing from this program to resume, and he may resume it at any time.

### Phase E. Records and what reaches him

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R15 | The node's records are true | seams-3, p0b-4, p34-1, p34-10, plus a census test of every text the node can write | `ground-start` A | G-FOUNDATION |
| R16 | Alarms and deep logs reach him | chief-2 (must), known-10, known-11 (doctor row only), known-12, triage-9, p5a-12 as a plan-line change only | `ground-start` B, C, D | R15 |
| R17 | Promote's edges | p5d-1, p5d-3, p5d-6 | `ground-start` G, H | R15 |
| R18 | The MIS publishes | p34-2, p34-3, and the source lookup without which configure publishes 0 readings. p34-4 stays out, and p34-14 stays until someone decides it | `ground-start` E | R17 |
| R19 | Recording holds up over months | p34-8, p34-6, p34-5, plan-check-3, and the paper-score trap. Projection reads the store | `ground-start` F | R18 |

### Phase F. The node

| Id | Plain title | Rows and items | Source | Depends on |
| --- | --- | --- | --- | --- |
| R20 | The broker wins | p5a-2, N2, N3, N4 of `ground-node`, p5a-9, the harsher fake cTrader | `ground-node` A, The fakes | R19 |
| R21 | Every way out acts | p5a-3, p5a-4, p5a-6, p5a-7, known-1 (the false report only), p5a-21, the harsher conformance venue, p5a-23 and the test deletions | `ground-node` B | R20 |
| R22 | What he deployed runs | N1 of `ground-node` (must), p5a-1, seams-4, p5a-5, seams-6, p5a-8, p5a-20, p5a-15, seams-11, seams-5 by refusal (step 1) | `ground-node` C, D step 1 | R21 |
| R23 | Connections and honest words | p5a-10, p5a-11, p5a-14, p5a-16, p5a-22, chief-1, p1b-8 with warm-up if it fits | `ground-node` E | R22 |
| R24 | The first-start script's new job, and the demo proofs ready | plan-check-1, seams-1, p5c-1, seams-13, p5c-2, p5c-4, the login reader rule, and section C-15 of `P/build/UNIT-PLAN.md` built as planned | `ground-start` I, J | R23 |

**Gate G-DEMO.** After R24, his demo sign-in, the first-start script's real run, and the demo proofs. Nothing in the program needs it before then.

## After the gates, not in this body

Write these in an appendix with what each waits for. Do not write PR sections for them yet.

- **After G-DEMO.** The bars he tested on (`ground-node` D steps 2 and 3, seams-12, p5a-19, seams-5 in full). Replay against a recorded day (seams-8). The node's own cost data. Removing the live lanes (deletion-3). The old node cut (section C-20, deletion-2, -4, -11, -12) on `c14-real.log` and `c15-demo.log` reading all PASS, as he ruled, with `qmn/host/sqs_baseline_producer.py` moved out first and the rule text at `decision_root.py:496-510` handed to the risk session. `runtime_risk_gate.py` is not the gate, and it can go. Read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5`.
- **After the risk session agrees the socket.** Exits really run, steps 2 and 3 of `ground-unit` B, with p1b-3, p1b-4, p5a-17, the signed stop distance, p0a-12, p1a-7.
- **Volume blocks.** p0a-14, then part 2 of `ground-unit` C, after the bars work.
- **On his word.** `qmf-indicators` and `qmf-structure` (`ground-unit`, write the structure ideas down as a dictionary note first). The old QMB door: about 32,700 plain lines, about 15,500 of methods to read first, the Book path and the two test-used modules stay (`ground-qmb`).
- **G-SERVER.** plan-check-4, p5c-5, C-19, p5d-2, p34-7.
- **G-WALLET.** p5b-1 to p5b-7. p5b-3 and p5b-6 are mostly closed by R21 and R22.
- **Before any live account.** triage-3 (two doors, `ground-start` H), C-21.
- **Research phase.** p6-6, p6-8, p6-10, p6-11, p2-7, p2-3. One engine question for him then, the script read of a family's tries.

## Left out on purpose

- p6-14: the copies are the design, so no repair (`ground-core` H). Do not count those 1,900 lines.
- p1b-5: the identity table stays unwired until the Lab or judge calls it.
- known-5, known-7, p0a-15 to p0a-20, and every `leave` row, unless a PR above touches the line anyway.
- The market board stays unwired (TR:49).
- Rows no block above names stay in `FINDINGS.tsv`. A later session may pick them up. The plan lists them by id in an appendix, so nothing is silently lost.

## What the foundation works means

The planner owed this list. Each is one real run across a real connection, with a literal expected result. Each fails today. The PR named adds it, or R14 does.

| # | Check | Added by |
| --- | --- | --- |
| 1 | A repair lands. A changed first-party app and a changed library reach an installed app at the next start, and its data stays. On a money app neither touches the signed version, and the repair arrives as a new version for him to sign | R03 |
| 2 | While one app installs slowly, a running app answers within a second. A stuck install fails by name and the host carries on | R03 |
| 3 | Nothing silent. Every stdlib block, swept as a trigger and as an exit through the real door over a month, either acts or refuses with a pointer. Never "check pass, zero signal, no reason" | R04, R05, R06 |
| 4 | A long-only unit through a QMB job makes zero short fills | R04 |
| 5 | An agent writes "ADX above 25" through `unit_new` and `unit_check`, and a QMB job runs it. It trades, and level 99 gives none | R05 |
| 6 | A QMB run with short trades moves the tuned number as its long mirror does, and the row shows why | R05 |
| 7 | The dictionary at full size. Fresh store, first start, one publish: 455 pages, none with status None, a clashing save refused, an ordinary sentence unmatched | R06 |
| 8 | A fresh home with a market that has only a Library record and ticks in the market store lands a finished result that links its data and uses that record's lot step | R08 |
| 9 | With no month, the run is refused before any try, naming the month and the template | R08 |
| 10 | The same month through a CSV and through the store gives the same trades | R08 |
| 11 | A record moved on main shows in the next run with no host restart | R07 |
| 12 | A study forbidding gaps beats a chat allowing them. A sealed month is refused, and no sealed file sits in any run folder | R07, R08 |
| 13 | A stated cost profile changes net money, raw R stays, and the verdict says costs are uncalibrated | R10 |
| 14 | A real backtest of 200,000 steps stays flat in memory | R10 |
| 15 | Real QMB job, real lander, real judge, real scorecard, for one market and for a sweep: the trades counted, one paper, the right cause | R12 |
| 16 | A model's copy saying pass over a stored fail routes as fail | R12 |
| 17 | The script gate and the hook on a market only the Library knows: a clean unit reaches QMB, a broken one gets its error | R13 |
| 18 | **His own test.** A copilot chat on `haiku`, from one plain sentence, builds a unit from dictionary blocks, checks it, backtests it on data the download template stored, and gets a verdict in plain words. It runs through a real host on a scratch folder, over its chat routes. This is what he asked for: can agents build units, and can they backtest them | R14 |

The dummy's job is check 4 to 6 and 15. It does not need to pass the judge.

The walls get their own short list in the node phases, from section 5 of `ground-node` and `ground-start`.

## Calls already made, so no builder reopens them

1. A unit with no price stop refuses for now. Whether such units are allowed is the risk session's.
2. Cadence `at`: warn when it sits beside `every_closed_trades`, refuse only when it is the sole cadence. The dummy uses it.
3. Roles that run are context, location, setup, trigger, confirmation, filter and entry_order. Others refuse.
4. Session blocks refuse until R06 gives them the market's clock. `time` reaches blocks only with that refusal in place.
5. Volume blocks refuse until a later volume repair. Dukascopy's number and a cTrader tick count are different things.
6. The six exits refuse until the risk session agrees the socket.
7. `auto_paper` is deleted. `recheck_units.py` and its tests are cut.
8. `[qmb] bars` stays as the test and hand-saved route. Gather's fixture fallback stays, with a warning that reaches the run.
9. R stays as it is. A cash number sits beside it. Whether R includes costs is the risk session's, behind one named function.
10. No engine change anywhere in this program. His engine items (a), (b) and (f) are withdrawn, because the engine as built does them. A script read of a family's tries waits for the research phase, and he is asked then, once.
11. Supervisor changes in R03 are made for one reason: a repair must reach him, and his kill must never wait on an install. A library repair never rebuilds a signed money app under its signed hash, and it arrives as a new version for him to sign. So any PR that changes a library in `apps/trading-node`'s lock bumps that app's patch version. On those terms the changes break no promise in `ground-core` section 2. Every PR is checked against that list.
12. A stuck install fails at a named setting, default 30 minutes. It stops no usage, so the no-caps rule is not touched.
13. A kill closes every position carrying this node's tag at the scope, hosted or not. Flatten closes positions, does not stop the unit, and never replays after a restart. What each kill level means stays a placeholder for the risk session.
14. The word for a manual position with no stop becomes "not ours, never touched", with "no stop at the broker" added when true. His to change.
15. No keys are passed into a running node. A changed alarm address waits for the next safe restart, and the plan line changes to say so.
16. Waiting lines dropped during an OpenObserve outage are the design, so only the doctor row changes.
17. The first-start script's job is to prove this machine's node is ready to receive a unit. With no unit named it prints one plain line, and that is not a FAIL. The landing check takes the branch by option, default `engine/base`.
18. The uncommitted edit in `D:/QMX-worktrees/bld-us-c14` is left out. R24 writes the login reader's full rule, and the owner lane on a throwaway entry proves it.
19. SQS: no gate is built now. The seat is one line in `Runtime.guard`, and the risk session places it.
20. A failure of the safety fact a block names stops that PR and comes back to the coordinator. Nobody works around it.

## How this program runs, which is what changes from last time

These go in the plan's "How to read this" and in the builder and coordinator prompts. Each answers a measured failure of the last build.

1. **Skills are checked, not listed.** A script reads each builder's and reviewer's transcript and fails the PR if a required skill was not opened. It is `S/tools/repair_check.py check`, copied from `repair_check.py` in this folder. A fail goes back to the same agent once.
2. **Understand first, in writing.** A builder's first output is `evidence/<id>/owner-how.md`: what is really there, who depends on it, and the safety fact. Then an `architect` sketch in `owner-sketch.md`. Then a failing test, saved as `owner-red.log`. No code before those three. The script checks they exist and come in that order.
3. **No clock on builders.** The "open the PR within 15 minutes" line is gone.
4. **Every row gets its check lanes.** A PR with no lanes run does not stack. Lanes 1 to 4 are the proving set, run by the coordinator in the background, and R19 also runs lane 6. Lane 1 compares against `A/tests/SUMMARY.txt` for the first PR, then against the parent. Lane 2 is the PR's fail-today proof: run at the parent it fails, run at the head it passes.
5. **Whole-repo runs on a schedule that cannot lapse.** After every fifth PR and at each phase end, in the background, under a lock. A phase does not close without it.
6. **The plan cannot grow quietly.** Every status line shows the count: PRs done, PRs left, PRs added. A new PR needs his word. Findings are justified as real bugs before they go anywhere, and most do not become work.
7. **The stack-time question.** Before a PR stacks, its reviewer answers: does anything below this PR make a stop-gap, comment or setting in it false? Does this PR make one below it false? That is how instrument facts were lost.
8. **Real neighbours.** A test for a crossing runs both sides for real, or uses a fake at least as hard as the real neighbour. A test that plants a row the real path never writes is replaced when the PR touches it.
9. **Subtract first.** Each PR opens by deleting the test-delete rows and dead code in its own files. The rows are `kind = test-delete` in `A/FINDINGS.tsv`, 35 rows, 1,637 lines, grouped by file.
10. **The tick re-reads the prompt.** After every compaction and every tick the coordinator re-reads its own prompt, the plan's head and `RESUME.md`. Last time it re-read only its notes, and the rules faded.
11. **Long tests are the coordinator's.** A builder never waits on a long command.
12. **Fresh reviewer per PR**, Opus, with `code-review` both axes, `bmad-review` verification-gap lens, the edge-case lens on money-adjacent PRs, and `blast-radius` on the one fact the PR names, rerun for real.
