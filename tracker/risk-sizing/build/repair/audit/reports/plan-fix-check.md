VERDICT: FIX

Check of the fix round, at `50c83a4e`. The fix log is honest: every line I opened says what the log says. Five of the seven blockers are truly cured. One is half cured, and one edit made a new money fault. Two blockers, one fix, five notes, each a few plan lines. Proofs are in `D:/Temp/audit/plan-fix-check/`. Levels: 2 pointed at the line, 3 walked, 4 ran.

## 1. Not cured, or newly broken

**plan-fix-check-1. R22, with R20 and R21. Blocker.** "Treat `symbol_facts_missing` as unlisted" is not safe for a market a running unit holds. The join can close a position whose stop is fine. When: a reconnect where cTrader's symbol answer omits a held market's facts, or lists it no longer.
Walk: `_authorise` empties `self.symbols` first (`ctrader_account.py:813`), and the market is now skipped instead of the session being refused. `_open` keeps the position. R20's read (`venuewins.truthful:27`) calls `_execution_price`, which answers None with no facts (`:1117`). So the stop reads None while the broker holds it. Line 31 of that same read raises `KeyError`, as does `_execution:1100` on a fill. R21 then sees stop None, cannot put it back, marks it `unprotected`, and closes it. `_close` reads only `held.volume` (`:1260-1282`), so the close goes through, with a false alarm.
Evidence: level 4 to the stop reading None, `held_market.py`: with facts 1.08022, market dropped None, broker holds 1.08022. Level 3 from there. No section test has this case.
Smallest edit, R22's `node-n1` box: "A market a held position sits on keeps the `SymbolFacts` it has, because `_authorise` empties them first. Otherwise R20 reads its stop as None and R21 closes a protected position." Add `test_app_deployed_runs.py::test_facts_missing_on_a_held_market_keeps_the_position`, with the stop held, no close and no alarm. After a restart `_open` is empty, so such a position reads as a twin and the account stands down. That is no worse than today's refused session, so name it in You see.

**plan-fix-check-2. R17. Blocker. `plan-review-b-2` is half cured.** The box says `_leave` withdraws what the node's `deployments` read shows "on this market and unit". That read holds no market.
- The row is id, unit, state, detail, accepted_at (`operations.py:969-975`, and `node_link.py:_refused_row` matches). One unit on two markets is normal, with one deployment per market (`promote.py:547`, `Click.key`). So a builder matching what the row holds parks EURUSD and also withdraws the unit's gold, which he did not ask for. The named test has one market, so it passes.
- The box is silent when the node is down or slow. `NodeLink.read` raises `AppError` after up to 30 s (`node_link.py:408`), and `_leave` catches only its own `Refused`. It does not hang, but a builder who catches that and carries on tells him done while the redeploy keeps trading.
- `_admit`'s "holds no live deployment" needs the same market. Adding the field to the node's row would add `operations.py` and a money bump to R17, and end the R16 and R17 pair.
Evidence: level 3.
Smallest edit: replace the read with the host's own record. "`_leave` also withdraws every `deploy` row in `self.nodes.outbox` whose `deployment` names this unit version and this market, through a small `Outbox.deploys(place)` beside `refused_deploys`." The deployment id is the op id (`promote.py:380`), and nothing deletes outbox rows (grep). This needs no node read, so a node that is down queues the withdraw as today. In `_admit`, map each live row to its market through `outbox.get(deployment_id)`. Extend `test_a_park_after_a_redeploy_withdraws_it`: the unit's second market stays, and a park with the node down queues and lands once it returns.

**plan-fix-check-3. R04, PR mechanics. Fix.** The bump's list of QMB pins misses `qmx-judge/tests/test_conformance.py`. `World.conformance` defaults to version `1.0.0` (`:97`) and runs the shipped app, and `run_conformance` refuses any other version (`conformance.py:445-447`). R04 bumps QMB, so that file goes red. R04's lane 1 does not run it. R05's lane 1 compares against a parent already red, so it passes. The red first shows in the whole-repo run after R05 and costs a fix round on a PR already stacked. Level 3.
Edit: add the file to R04's Files and lane 1, have `World.conformance` and the literals at `:173`, `:185`, `:252` and `:307` read `apps/qmb/app.toml`, and name it beside `test_qmb_app.py:191` in PR mechanics. Lines 223 and 234 stay, because `default_tester` stays.

**plan-fix-check-4. R13. Note.** `compile_unit` never raised on 18 whole and half-written documents (`offline2.py`, level 4). It does double-report, because it reruns the layers: `missing_field` thirteen times twice, and a halt on EURUSD reads `not_compiled` and `halts_not_built`. The agent reads each error twice. Edit: "Call it only when `checked` left no errors after the five kinds move, and keep it out of a check that already reached the compiler."

**plan-fix-check-5. R06. Note.** R04 and R05 say what happens to `READ_NEVER_FIRED`. R06 widens the sweep to `@2` and does not, so an `@2` read and never fired is a surprise red. Edit, in R06's sweep box: "Add any such `@2` to `READ_NEVER_FIRED`, on purpose." Level 2.

**plan-fix-check-6. R21. Note.** "Every position a unit holds whose stop reads None" also matches a closed one, because `stop_of` reads None once a position leaves `_open` (`ctrader_account.py:654`). `adopt` also runs each tick from a snapshot, and compile runs in a thread (`runtime.py:2379`, `:2117`), so a restart's reconcile can come before the unit is hosted. Edit: "Walk `unit.venue_open()` each tick after `adopt`." Level 3. The test `test_a_restart_puts_a_missing_stop_back_before_any_entry` should catch a slip on the second.

**plan-fix-check-7. Head, R19. Note.** R19's lane 6 says it is in the proving set, while the head, the Verdict box and PROMPT rule 3 and loop step 4 say lanes 1 to 4 and one menu lane. A coordinator reading its section runs it, and one working from the head alone would not. Edit, head: "R19 also runs lane 6." Level 2.

**plan-fix-check-8. R23. Note.** The box does not say how the loop calls `refresh_facts`. Called on the event loop, it waits on the supervisor's lock, the hazard the comment at `host.py:1478` names. Edit: "through `asyncio.to_thread`, as `keep_facts` does." Level 2.

## 2. Checked and true

**The other five blockers.**
- `a-1`, level 3. Environments install as wheels and `BUILT_FROM` digests `src`, so a bump reaches him only as a new hash. The test asserts uv is not called. Lane 5 holds.
- `a-2`, level 2. The sentence, the bindings, at least one trade, and `says()`: `"{word} by the {preset} preset."` (`judge.py:408`), so "before ' by the '" is right. `value-above@1` comes from R05.
- `a-3`, level 4 on a throwaway target. Arming's real `haiku` turn remains unproven, and that box stops and reports.
- `b-1`, level 3. The skip is gone and `_markets` keeps the market, so `node-n1` is cured and W11 can read true for a symbol he never held. Finding 1 is the held case.
- `b-3`, level 2. The box, the month-end test and the told-again rule match the proof `test_r19_months.py`.
- `b-4`, level 3. `kind` entry is real (`runtime.py:1033`), and the self-test writes `self_test` (`ctrader_account.py:1393`), so it is rightly excluded. The four boxes answer the four faults.

**The fixes and notes.** `a-4` to `a-16`, `b-5` to `b-22` and the G-DEMO sentence match the log, level 2, apart from `b-22`, which is finding 1. `bad_mirror` exists (`parse.py:80`). Every test R14 names is added by an earlier section (grep). All 50 `S/proofs` paths exist, in folders the Arm box copies.

**Section C.** Items 3 to 6, 10, 11 and 12 also lead to findings 1, 2, 4, 5, 6, 7 and 8.
1. Level 4, `row.py`. The real writer takes a `kill_level` row with no `level`. `journalled_resumes` reads its op id, which is harmless because op ids differ. `gw` and `rk8` both test `level not in (None, "GREEN")`. Status reads memory.
2. Level 3. `parse_spec` ignores `source`, `quick_spec` does not hold it, and a study naming it does not equal `quick_spec`, so it gets no exemption. Another source's run still lands a counted try. No door reopens.
3. Level 3, apart from the findings. A missing-position guess books `_closed` and sends no order. A position with no tag cannot enter, because `mine` holds only `Claim.MINE` with a send, and lane 5 tests it.
7. `bump_check.py` reads ok on all 24, and all app folders have their `app.toml` (`app_scan.py`). He gets one version to sign when he lands the stack at once, because only the tip's folder is on disk. Nothing but the unread `trading_node_app_test.py:69` pins the node's version, and neither the first-start script nor `owner_lane_c14.py` does (grep). R03's table starts from the true 1.0.0, 1.0.0 and 0.1.0, level 2.
8. Level 4 on a throwaway target, `junction.py`, no login folder opened. `ensure_homes` accepts the junction and adds `claude-relayed/projects` through it, twice without error. `shutil.rmtree` of the folder with no `rmdir` first left the target whole. `os.walk` and `rglob` do follow it, but backups use `_walk`, which skips junctions (`snapshot.py:519`, level 2). `first_start.py:1018` only asks whether files exist. `disk.clear` touches four expendable folders, none of them this. Nothing refuses, wipes or copies.
9. Level 2. Every tool and route exists, `/api/events/{topic}` serves sessions, and `title` is required on a new chat. Lane 4 is in the proving set and a skip counts as FAIL, so check 18 must truly run. A test that skips still collects.
12. Level 2. `refresh_facts` holds the lock only to list volumes, then writes one small file per app.
13. Appendices C, E and G read true. `p5d-3`'s "nothing left over" becomes true only once finding 2 lands.

**Section D.** Every path the Arm box copies exists, and `S` does not exist yet, as it should not. The plan, prompt, brief and `repair_check.py` agree on names and order. Builder skills match. The reviewer's script adds `principle-prove-it-works` and `ground-core.md`, which the reviewer template opens. The money-adjacent list is identical. The fix round left no false line in them, apart from finding 7. A fresh coordinator can start once the edits above land.

## 3. Not reached
- R09, R10, R12 and R18 were checked only through the bump scripts, the appendices and greps, not against their code.
- Whether the login target exists, by the rule. Arming proves it.
- The reviewers' proofs were not rerun, because no cure exists to run them against. I ran six proofs.
