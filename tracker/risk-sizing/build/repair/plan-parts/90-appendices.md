## Appendix A. Prototype evidence

The grounding agents ran each repair's shape against real code at `50c83a4e`, patched in memory, with no file changed. This table is what was proven by running. Script paths are under `D:/Temp/audit/` until the Arm box copies them to `S/proofs/`. Logs of the long runs are in `D:/Temp/audit/chief/ground-long/`.

| Question | Script | Result | Level |
| --- | --- | --- | --- |
| Does a repair reach an installed app? | `ground-core/sup_proof.py` C to G | No. A host start runs the old hash, env builds unchanged. The same bytes reinstall and rerun the build, and the volume's data stays | 4 |
| Does `run(timeout=3)` fix a stuck uv? | `ground-core/pipe_proof.py` | No. It raised after 25.3 s, waiting on the pipe | 4 |
| Does an install stall other apps? | `ground-core/stall_proof.py` | Yes. A plain call answered after 44.1 s | 4 |
| How fast does a running app grow the store? | `ground-core/sup_proof.py` B | 3.1 `apps` and 3.1 `aggregates` rows a second, about 200 MB a day, rough | 4 |
| Does the restart wait reset? | `ground-core/sup_proof.py` H | No. 5, 10, 20 and 40 s after calm runs | 4 |
| Is the answer-file race real? | `ground-core/done_race.py` | 2,943 of 3,000 tight rounds. It proves the window, not the rate | 4 |
| Does dead weight detach? | `ground-core/cut`, `chief/ground-long/cut.log` | 54 failed and 8 errors, of which 29 are the named deletions and the rest are what the scratch copy lacked | 4 |
| Do the unit refusals move shipped tests? | `ground-unit/plug/refuse_trial.py`, `chief/ground-long/unit-trial-qml.log`, `unit-trial-qmb.log` | QML 1,445 passed and 1 failed, the named session test. QMB's unit path 18 passed | 4 |
| Does a direction trim run? | `ground-unit/p2.py` A | The obvious form refuses with `motion_source`. Trimmed by hand, 2 long and 0 short | 4 |
| Is a comparator enough? | `ground-unit/p3.py`, `p6.py` | No. 0 entries under `all`. With the feeder rule, 25 at level 1 and 0 at level 99, with the dummy identical | 4 |
| Do price series fed whole bars come alive? | `ground-unit/p4.py`, rerun by this plan's writer | 6 of 14, with 1,154 to 1,595 entries. The dummy is unchanged | 4 |
| Does a bar with `time` change the dummy? | `ground-unit/p2.py` D | No | 4 |
| Does the save-time clash check refuse the landing? | `ground-unit/p6.py` | 0 clashes across 455 pages | 4 |
| Does a record on main reach the run? | `ground-qmb/records.py` | No today. With the one-place repair, same compiled fingerprint, and gold lot step 0.10 moved 29 trades, +22.84 to 21 trades, -169.04, on a planted record | 4 |
| Does a record moved on main show? | `ground-qmb/records.py` | Not in the same host, 0.01 version 1 against 0.05 version 2 | 4 |
| Do costs reach net with R unchanged? | `ground-qmb/records.py` | Commission 3.50 gave -249.91 with R at -4.3841, and swap gave -171.59 | 4 |
| Do ticks through the door match the CSV? | `ground-qmb/bridge.py` | Identical bars and "same trades True". The ticks were cut from those bars, so it proves the path | 4 |
| Does `materialise` honour a sealed month? | `ground-qmb/bridge.py` | No, "COPIED 1 file(s)", by its docstring | 4 |
| Is one market of two possible? | `ground-qmb/bridge.py` | Yes, 14 trades on `fx.eurusd` | 4 |
| Do real months read as holes? | `ground-qmb/holes.py` | 0 past the limit on January to March 2025, and 88 head bars on a window-end check | 4 |
| Do trades reach the Library? | `p34/p1_trade_account.py` | trades=0 as written, trades=1 with the account set | 4 |
| Which reason texts have no code? | `ground-start/census.py` | 3 of 32, plus the one reached through `Unprotected` | 4 |
| Does the alarm list load in a wheel layout? | `ground-start/alarm_wheel.py` | No today. Yes with the register inside the package, on a copied layout | 4 |
| Do the log shapes hold? | `ground-start/logs.py` | known-10 raises, severity INFO, telemetry raises, as filed | 4 |
| Does calling `configure` publish? | `ground-start/mis_real.py` | 0 readings silently with the record's venue, 4 with the right source | 4 |
| Does `tool_timeout` as a waiting code hold? | `ground-start/proof_waiting.py` | One move and one deployment on the rig's fake node | 4 |
| Does the login reader follow keyring? | `ground-start/bearer.py` | Two rows fail, neither reachable today | 4 |
| Does broker-wins break tests? | `ground-node/venuewins.py`, `chief/ground-long/node-runtime.log` | No. 17, 11 and 11 passed. Outage gives closed STOP and rows 1 | 4 |
| Does the kill reach an orphan? | `ground-node/truth4.py`, `reach.py`, `chief/ground-long/node-kill.log` | Yes with the sketch, kill row 1, and 17 passed on the harsher venue | 4 |
| Does a refused exit keep going? | `ground-node/truth4.py` | 2 closes, flat, 3 trades with the sketch | 4 |
| Does holding the compile fix the zero equity? | `ground-node/truth2.py g7` | Yes, equity 10000.00, trading, 2 entries | 4 |
| Does widening work by reconnect? | `ground-node/truth2.py g6` | Yes, subscribed `['1','41']` with the position held | 4 |
| Does one unlisted symbol kill the account? | `ground-node/truth2.py g1` | Yes, 0 closes under RED | 4 |
| Does a snapshot survive JSON? | `ground-node/truth2.py g9` | Yes, 37,988 bytes | 4 |
| Does a sweep's verdict lie? | `p6/test_sweep_verdict.py` | Yes, 6 trades and `no_trades` | 4 |
| Can a template read the real verdict with no engine change? | `ground-core/test_verdict_read.py` | Yes, on the real engine with a fake Library | 4 |
| Does a check with no Library see a real error? | `ground-core/template_facts.py` | Yes, `outside_range` is left after the five kinds | 4 |
| Do QMB and the node decide alike? | `seams/parity.py` | 63 of 63 | 4 |
| Does a same-bytes install change a signed money app? | `plan-review-a/money_env.py` | Yes. uv rebuilt the signed hash's environment, and start asked for no signature, so R03 keeps that branch off money apps | 4 |
| Can an older study edited after a result take a friendly k? | `plan-review-a/shrink2.py` | Yes. Honest study 0.0558 and weight 0.0000, edited study 0.2193, weight 1.0000 and 0 `spec_edit` tries | 4 |
| Does a Library-less check see what compile refuses? | `plan-review-a/offline.py` | Not on GBPUSD. `checked` stops at `no_record`, while `compile_unit` adds `halts_not_built`. The dummy on GBPUSD gives only `no_record` | 4 |
| Does leaving a refused deployment's market out undo RED? | `plan-review-b/p1_orphan_market.py` | Yes. Kept, kill row 1 and broker empty. Left out, a twin alarm, kill row 0 and closes 0 | 4 |
| Does a projection handed only committed keys keep a score? | `plan-review-b/test_r19_months.py` | No. 3 trades in round 1, then `(2, '2.0')` with four trades in the store | 4 |
| Does the writer accept a reason code only `journal.py` knows? | `plan-review-b/p2_small.py` | No. It answers that the reason is not one of `REASON_CODES` | 4 |
| Does a junction hold for the login folder's mechanics? | A throwaway target in the fix round's scratch folder, no login touched | Yes. A write reached the target, `cmd /c rmdir` removed only the link, and `rm -rf`, `Remove-Item -Recurse -Force` and `shutil.rmtree` of the parent each left the target whole | 4 |

These stay unproven until a PR runs them.

- Arming. A real `haiku` turn through the login junction, which the coordinator proves in the Arm box.
- R03. A real `uv` run through the new install shape, because every proof patched uv out. What a tool timeout does on a real opted-in app, because that was read, not run.
- R04. The `p0a-9` check over all of QML. The trial did not hold it, and `test_compile_dummy.py:272` is known to move. No unit trial crossed a QMB job or the fake cTrader.
- R06. The settle-per-period idea and the claim that the dummy's warm-up holds. The cost per save over the full store.
- R07 and R13. The Library-less gate words, `S/proofs/p6/gate_proof.py`'s before and after. `core-n2`'s path fix.
- R08 and R09. Real Dukascopy ticks against dukascopy-node bars. The real tick rate, which is a guess of 3.5M a month. Whether Christmas reads as a hole in a real month. The rule for which source a market reads, which rests on reading.
- R10 and R11. The shapes of `p0b-14`, `p2-5` and `p2-11` rest on reading.
- R12. `p6-5`'s memory row, and the `library` node's read of a verdict on the real store.
- R15. Whether `runtime.py:1007` reaches the journal, which the repair covers either way.
- R16. The real wheel build with a real alarm.
- R19. The bounded harvester, which `p34/p4_harvest_cost.py` must flip.
- R20. The history path and `node-n4`. `venuewins.py` books every missing position at the held stop and never asks for history, so its run says nothing about either.
- R21. Flatten, which ran only through its shared close.
- R23. The back-off, weekend, clock and paper-restart shapes.
- R24. The login reader on a real entry, which belongs to the builder's owner lane.
- G-DEMO only. `label` survival, repeated `clientOrderId`, attribution, the cut and refresh drills, whether a fill carries the stop, what a close on a gone position answers, whether events carry `clientMsgId`, deal-history fields, trendbar retention and side, `traderId` against `ctid`, the six literal facts, and what `ProtoOAAccountDisconnectEvent` does. Also `hasMore` and the default time window on a position's deal list, whether a position missing from one listing can come back, whether a non-closing event can omit `stopLoss`, and whether the refresh drill, run from a separate process, invalidates the running node's session.
- Not reached by anyone. A kill across a node that is away, the server paths, twin and take-over paths, and `CcxtClient.read_back` for Cause A's fault.

## Appendix B. Not in this program

These have no PR section, by `PLAN-SHAPE.md`. Each names what it waits for.

**After G-DEMO, on `c14-real.log` and `c15-demo.log` reading all PASS.**

- The bars he tested on, `ground-node` D steps 2 and 3, with `seams-12`, `p5a-19` and `seams-5` in full. `_building` and `Recording` keyed by market and size, then broker history at `_host`, with the ask built from the current spread and labelled so. It reads `start-n2` too.
- Replay against a recorded day, `seams-8`. The world filter at `route.py:32`, and recorded bars to CSV. It needs `seams-5` first.
- The node's own cost data. Swap and commission from cTrader's symbol, then a host step that turns `minute` rows and fills into a cost profile.
- Removing the live lanes, `deletion-3`.
- The old node cut, section C-20, with `deletion-2`, `deletion-4`, `deletion-11` and `deletion-12`. Move `qmn/host/sqs_baseline_producer.py` out first, and hand the rule text at `decision_root.py:496-510` to the risk session. `runtime_risk_gate.py` is not the gate, and it can go.
- Read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5`.

**After the risk session agrees the socket.**

- Exits really run, steps 2 and 3 of `ground-unit` B, with `p1b-3`, `p1b-4`, `p5a-17`, `unit-n2`, the signed stop distance, `p0a-12` and `p1a-7`.

**Volume blocks.**

- `p0a-14`, then part 2 of `ground-unit` C, after the bars work.

**On his word.**

- `qmf-indicators` and `qmf-structure`. Write the structure ideas down as a dictionary note first.
- The old QMB door, about 32,700 plain lines and about 15,500 of methods to read first, with `deletion-6`. The Book path and the two test-used modules stay.

**G-SERVER.**

- `plan-check-4`, `p5c-5`, section C-19, `p5d-2` and `p34-7`.

**G-WALLET.**

- `p5b-1` to `p5b-7`. `p5b-3` and `p5b-6` are mostly closed by R21 and R22.

**Before any live account.**

- `triage-3`, two doors, by `ground-start` H, and section C-21.

**Research phase.**

- `p6-6`, `p6-8`, `p6-10`, `p6-11`, `p2-7` and `p2-3`. One engine question for him then, the script read of a family's tries.

**Left out on purpose.**

- `p6-14`, because the copies are the design. Do not count those 1,900 lines.
- `p1b-5`, because the identity table stays unwired until the Lab or judge calls it.
- `known-5`, `known-7`, `p0a-15` to `p0a-20`, and every `leave` row, unless a PR touches the line anyway. R23 touches `p0a-20`.
- The market board stays unwired, by TR:49.
- Rows no block names stay in `A/FINDINGS.tsv`. Appendix E lists them, so nothing is silently lost.

**Lines of the old plan that change.** `A/plan-current.md` is the copy of `P/build/UNIT-PLAN.md` these line numbers read. Do not edit `UNIT-PLAN.md` from a build branch. Whoever picks up those sections reads these lines first.

| Section and line | It said | It now says |
| --- | --- | --- |
| C-14 You see, `:3787` | After he lands the stack and signs in once, his practice node trades the dummy unit on his demo account | After he lands the stack and signs in once, one script proves his node is ready to receive a unit. No unit reaches a node without passing the judge and his click |
| C-14 Build, `:3783` | "Code he has landed" means a commit on `origin/main` | The landing check takes the branch by `--landed-on`, default `engine/base` |
| C-14 lane 5, `:3799` | The real run on his folder, pass when every line reads PASS | The same, and every line reads PASS with the plain "no unit" line when no unit has passed the judge. It no longer implies any unit traded |
| C-15 Build, `:3837`, and its unit test, `:3845` | Each mark rehearses against the conformance venue | Each mark rehearses on R20's harsher fake cTrader over the real codec, because `ConformanceAccount` speaks no cTrader wire |
| C-20 gate, `:4169` | Dispatch when `c14-real.log` and `c15-demo.log` read all PASS, as evidence the new node "traded on demo" | The same two logs, as he ruled. `c14-real.log` proves this machine's node is ready and its test trade traded, and `c15-demo.log` proves attribution, duplicates, the cut and the refresh on demo. Neither implies a unit traded |
| C-20 Files, `:4173` | `qmn/FAILURES.md` stays, because `alerts.py:249-251` reads it | R16 moved it to `qmn/src/qmn/observability/FAILURES.md`, which is one of the kept files there. C-20 also moves `sqs_baseline_producer.py` out before it deletes `qmn/host` |
| C-30 lane 4, `:4654` | Pass when the next alarm uses the new key without a restart | Pass when the setup says the new key is read at the next safe restart, and the first alarm after that restart uses it |

## Appendix C. Files two PRs share

`assemble.mjs` generates this table from every Files block. Two PRs on one row never run at the same time, and the stack is linear, so the later one rebases on the earlier. The crowded ones are `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/host.py`, `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` and `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py`. A PR that adds a setting may also edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py` for its default, so the coordinator treats that file as shared by every such PR. A PR that changes an app folder also edits `test_shipped_apps.py`, which is why that file sits on so many rows. A PR that changes a library in the trading node's lock also edits `qmx-agents/apps/trading-node/app.toml`, by call 11.

@appendix-c

## Appendix D. The calls already made

These are the calls in `PLAN-SHAPE.md`, so no builder reopens them.

1. A unit with no price stop refuses for now. Whether such units are allowed is the risk session's.
2. Cadence `at` warns when it sits beside `every_closed_trades`, and refuses only when it is the sole cadence. The dummy uses it.
3. Roles that run are context, location, setup, trigger, confirmation, filter and entry_order. Others refuse.
4. Session blocks refuse until R06 gives them the market's clock. `time` reaches blocks only with that refusal in place.
5. Volume blocks refuse until a later volume repair. Dukascopy's number and a cTrader tick count are different things.
6. The six exits refuse until the risk session agrees the socket.
7. `auto_paper` is deleted. `recheck_units.py` and its tests are cut.
8. `[qmb] bars` stays as the test and hand-saved route. Gather's fixture fallback stays, with a warning that reaches the run.
9. R stays as it is. A cash number sits beside it. Whether R includes costs is the risk session's, behind one named function.
10. No engine change anywhere in this program. His engine items (a), (b) and (f) are withdrawn, because the engine as built does them. A script read of a family's tries waits for the research phase, and he is asked then, once.
11. Supervisor changes in R03 are made for one reason, that a repair must reach him and his kill must never wait on an install. A library repair never rebuilds a signed money app under its signed hash, and it arrives as a new version for him to sign. So any PR that changes a library in `apps/trading-node`'s lock bumps that app's patch version. On those terms the changes break no promise in `ground-core` section 2. Every PR is checked against that list.
12. A stuck install fails at a named setting, default 30 minutes. It stops no usage, so the no-caps rule is not touched.
13. A kill closes every position carrying this node's tag at the scope, hosted or not. Flatten closes positions, does not stop the unit, and never replays after a restart. What each kill level means stays a placeholder for the risk session.
14. The word for a manual position with no stop becomes "not ours, never touched", with "no stop at the broker" added when true. His to change.
15. No keys are passed into a running node. A changed alarm address waits for the next safe restart, and the plan line changes to say so.
16. Waiting lines dropped during an OpenObserve outage are the design, so only the doctor row changes.
17. The first-start script's job is to prove this machine's node is ready to receive a unit. With no unit named it prints one plain line, and that is not a FAIL. The landing check takes the branch by option, default `engine/base`.
18. The uncommitted edit in `D:/QMX-worktrees/bld-us-c14` is left out. R24 writes the login reader's full rule, and the owner lane on a throwaway entry proves it.
19. SQS has no gate built now. The seat is one line in `Runtime.guard`, and the risk session places it.
20. A failure of the safety fact a block names stops that PR and comes back to the coordinator. Nobody works around it.

The plan's writer made these smaller calls so a builder need not ask. Each is cheap to reverse.

- `p1a-4` lands in R06, not R05, because its settle check goes through `check_entry`.
- `p6-2`'s `check.py` and `ready.py` edits land in R13 with `offline_checked`, not in R07, so one PR owns those lines.
- `value-above@1` carries a `below` setting, so "RSI below 30" can be written with the one comparator block.
- The new session blocks take a `clock` of UTC, London or New York, on the clock blocks' civil-date functions, because `zoneinfo` appears nowhere under `qml/src/qml`.
- The app version table holds a line-ending-normal digest, because `core.autocrlf` is true on this PC.
- `known-1` takes both reports' shapes, `amend` answers the broker's stop and a stop past entry answers `Blocked` with its row.
- The setting names are `[apps] install_limit_s` and `[node] record_markets` with `records_refresh_s`.
- The trading node's bump covers a change under a library's `src`, because `path_sources` digests only that folder. A change to a library's tests or examples bumps nothing.
- A usable source for a market's month is the one the request or study names, or `dukascopy` when neither does, holding that month with a stated scale. So two usable sources means the request and the study name different sources, and a copy under any other source is not read.
- The flatten op's done row is a `kill_level` row with no `level`, because that is the row kind with an op id, and R13's watcher reads a row with no `level` as deciding nothing.
- A kill's `positions_closed` stays one count at the rising tick, with its limit named, and no done row is added.

## Appendix E. Every row and where it went

@appendix-e

## Appendix F. What the risk session gets

The risk session needs nothing from this program to resume. This is what the repairs hand it, in one list. Every value and rule here is theirs, and the plumbing around each is built or marked.

The paths, for a session in another worktree. The placeholder numbers below are in `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/RISK-SIZING-PLACEHOLDERS.md`. `CONTRACTS.md` is `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/architecture/parts/A-qml-dictionary-unit/CONTRACTS.md`. `ground-unit` is `D:/QMX-worktrees/audit-ship/reports/ground-unit.md`. `seams/wick.py` is `D:/Temp/audit/seams/wick.py`, and the Arm box copies it to `D:/QMX-worktrees/repair-ship/proofs/seams/wick.py`.

The placeholder sizer is wrong on USDJPY. It divides account money by a loss in the quote currency, so it is right for EURUSD and XAUUSD on a USD account and wrong for USDJPY (`D:/QMX-worktrees/audit-ship/reports/p0a.md:99`). It belongs on the rip-out list.

What compile refuses after R04, with the list in `_shape_problems` (`qml/src/qml/compile/compiler.py:493`), is a unit with no price stop, a second stop, target or per-bar exit, and the six exits by rule, which are `unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop` and `profit-fraction-trailing-stop`. An agent's block of the same shape refuses too. Flatten closes positions and does not stop a unit, by call 13.

- May a stop go past entry, and how is that sent? The signed distance is theirs by his ruling. R21 stops a wrong side being sent or reported, and it answers `Blocked` until they decide. This covers `known-1`, `triage-1` and whether trails on the node can lock in profit.
- Whether a stop may ever widen, placeholder 9.
- Scale-out ladders, and what a partial close means for R, placeholder 10. `p1b-4`, `p5a-17`.
- Whether a target rests at the broker or the node closes it, `seams-7`. One wicked bar read +2.00R against -0.55R in `seams/wick.py`. QMB's fill does not change meanwhile.
- May a unit have no price stop, placeholder 11. R04 refuses it for now, `p0a-8`.
- Whether a moved number changes an open trade's exits, placeholder 8.
- Which exit wins when two fire on one bar.
- Which position facts exits read. `bars_held`, `mfe_r` and `mae_r` from `CONTRACTS.md` 4.3 are not computed today. R10 tracks MAE, MFE and drawdown in R in the handler, adds only, for results.
- The exits socket itself. Step 2 of `ground-unit` B feeds every per-bar exit real evidence and the position's side, about 60 lines, with `unit-n2`, because `timer()` builds exits long-only. Step 3 is trails, partial closes and stop moves, about 250 lines, with `p1b-3`, and it must not ship on the node before the signed distance is answered. `p1a-8` is theirs, a long-wicked bar giving a stop above the close.
- Whether R includes costs, with the name `r_after_costs`, `p0b-13`, `p2-6` and `seams-10`. R10 puts the judge's read behind `trade_r`, so it is one line.
- What each kill level means, YELLOW to BLACK, placeholder 18. R21 makes whatever the table says act, on positions hosted or not.
- SQS, by call 19. The rule text is at `qmn/host/decision_root.py:496-510`, the baseline producer is `qmn/host/sqs_baseline_producer.py`, and the seat is one line in `Runtime.guard` (`runtime.py:2269-2314`). AD-39 and NODE.md section 6 name spread against the unit's cost target as a guard. This is `plan-check-2`.
- The sizer's socket, `plan-check-7`, which gives a sizer no costs and no edge numbers from QMB. The Kelly sizing he asked for needs them. `p0a-12`, the sizer's receipt, goes with their sizer, by adding the residue to `Size`.
- `p1a-7`, the drawdown halt's silence at zero equity, with the halts, which compile refuses today.

## Appendix G. Risks

| Risk | Where it lands | What the coordinator watches |
| --- | --- | --- |
| A proof script in `D:/Temp/audit/` is lost in a clean-up | every lane 2 | The Arm box copies them to `S/proofs/` before anything else |
| His `C:` drive fills, so 106 `qmx-home` backup tests go red | every whole-repo run | `TEMP` and `TMP` on `D:/Temp` before each run, and those reds read as the disk |
| `D:` fills with check worktrees, real months and envs | every lane | Remove each check worktree after its verdict. Below 3 GB free, stop and clean |
| A first-party app bump is forgotten | R04 to R12, R15, R16, R18 to R23 | R03's literal table fails CI when an app folder changes, and tests under an app folder count too. A library change with no bump does not change the folder, so the table cannot see it. The Files block names the bump, and on a real folder the node's status says a library repair waits |
| A money app's version moves with each library repair | R04 to R06, R08 to R11, R15, R16, R19 to R23 | On a real folder M5 waits for his signature, once, for the stack's last version. That is right, and the coordinator tells him at landing |
| The login junction fails at arming, or a clean-up reaches through it | the Arm box, every model lane | The coordinator stops and reports. The boot recipe removes the link first, and on this PC `rm -rf`, `Remove-Item -Recurse -Force` and `shutil.rmtree` left a throwaway target whole |
| A repair to a block changes the dummy's numbers | R04, R05, R06 | `test_compile_dummy.py`, 25 entries and bar 48. A moved warm-up stops the PR |
| The handler is shared, so a QMB change moves the node | R10, R15, R20 to R23 | `seams/parity.py` reads 63 of 63. No repo test holds this |
| Check 18 on `haiku` gives another answer on a rerun | R14 | One rerun, and a second fail counts. It asserts the path, the two bindings, at least one trade and the words, not which verdict |
| The real tick rate is far from the 3.5M guess | R08, R09 | R08's lane 4 records it. If a month through ticks takes over 10 minutes, name it to him as a finding |
| Past closures in a calendar disagree with real data | R09 | Step one's real December. Any hole left is named in the PR body |
| The bounded harvester rewrites a paper score | R19 | `test_a_second_and_third_round_score_the_same_paper_run` must fail against the naive form first |
| The kill's repeated closes hit broker limits | R21 | 5 requests a second per position is left as built. The demo proofs show if cTrader minds |
| A demo answer disagrees with what R20 assumes | after G-DEMO | Read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5` |
| Lanes that need a network find it down | R08, R09, R14, R18 | The lane logs "network down" and is rerun later, and a saved month stands in where the lane says |
| Templates have no path to his folder at a host start | R12, R13 | The fourth path is `python -m qmx_engine templates install`. R14's lane 6 runs it, and the landing message tells him. A new version waits beside his enabled trigger |
| An uncommitted edit or a venv edit leaks into a branch | every PR | No `git stash`. Worktrees are clean at dispatch, and venv files are never edited |
| The plan grows quietly | every status message | The count of PRs done, left and added ends each message. A new PR needs his word |
| A builder works around a failed safety fact | every PR | Call 20, and the reviewer reruns the fact for real |
