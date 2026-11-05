VERDICT: FIX

Reviewer plan-review-b, sections R15 to R24 and Appendices B, E, F, G. Code at `50c83a4e`. Proofs in `D:/Temp/audit/plan-review-b/`. "Edit" means an edit to the plan only. The shape of R15 to R24 is right. Four boxes would break something as written, and each needs only a few plan lines.

## 1. Findings

**plan-review-b-1. R22. blocker.** R22 says "`_markets` skips refused deployments" (Build, `node-n1`). That undoes R21's kill. A position on a refused deployment's market is then a market the session does not know, so `_reconciled` returns it with no market and no client order id (`ctrader_account.py:699-705`). It reads as a twin, the whole account stands down, and RED cannot close it. What goes wrong for him: a code update refuses a unit that holds gold, he presses RED, gold stays open, and the alarm blames a twin. R21's W10 cannot see this, because its rig trades `fx.eurusd`, the self-test market, which `_markets` always keeps. R22's lane 1 does not run R21's tests, and no whole-repo run falls between R20 and R24.
Evidence, level 4, `p1_orphan_market.py`, with R21's kill sketch on. Market kept: claim mine, broker empty, kill row 1. Market left out: `[('twin', '')]`, alarm twin, broker holds 9001, kill row 0, closes 0.
Edit: delete "skips refused deployments". With `_authorise` keeping the listed markets, the skip cures nothing. Keep "takes only the markets he chose". Add a test with the orphan on a market other than the self-test's. Add `test_app_every_way_out.py` and `test_app_broker_wins.py` to lane 1 of R22 and R23.

**plan-review-b-2. R17. blocker.** `p5d-3` says "deploy again without recording a move, pointing at the existing move". A park can then never reach that deployment. `_leave` withdraws only what `deployment_of(move)` names (`promote.py:417,433`), and that is computed from the old move's own event id (`:162-166`). A new click has a new digest, so a new `dep-` id that no move names. The code's own words at `promote.py:392` are "its move is not recorded, so no park can reach it". Reusing the old id fails too: the node skips any id it already hosts (`runtime.py:2367`), and the same op id answers its first answer. What goes wrong for him: he clicks promote again after a refusal, it trades, he clicks park, the screen says done, and the node keeps trading. The plan's test stops at "deploys with no new move".
Evidence, level 3, the lines above.
Edit: add to the `p5d-3` box "`_leave` also withdraws every deployment the node's `deployments` read shows on this market and unit, not only those its moves name". Add `test_a_park_after_a_redeploy_withdraws_it`. R17's files already cover this.

**plan-review-b-3. R19. blocker.** The plan names the trap and then its own box walks into it. "A round tells it which keys it committed, and it reads those keys whole" hands `_paper` one month. A closed month is never committed again. So any paper lane older than a month has its score rewritten from the open month alone. What goes wrong for him: the paper score he promotes on quietly drops its older trades at the first round after a month ends. The plan's test does three rounds in one month, so it passes with this in place.
Evidence, level 4, `test_r19_months.py`, the real job with the projection handed only committed keys. Round 1 commits `2026-09` and `2026-11`, paper-run 3 trades. Round 2 commits `2026-11` only, four trades exist, and paper-run reads `(2, '2.0')`.
Edit: change the box to "a committed key names the lanes it touches, and each lane is scored from every month of its series in the store". Make `test_a_second_and_third_round_score_the_same_paper_run` span a month end. Also say a key whose projection failed is told again, because a frozen month is committed only once, and lane 6 (mid-round restart) moves from the menu to the proving set.

**plan-review-b-4. R20. blocker.** `node-n4`, "the journal's sends without an exit", has no working meaning, and no sketch ever ran it. The safety fact's level 4 covers `read_back` only. Walked:
(a) The node journal holds no exit for a stop that fired. Only `OrderPath._close` writes a `closed` row (`runtime.py:1204`). A stop goes through the handler into the unit journal. So every past stop-out reads as "no exit" at every restart.
(b) `journal_sends` returns every `node` folder's sends, paper too, with no world or account in the body (`reconciler.py:87-104`). Paper sends are never on the broker's list. Rejected sends never opened anything. With two bound accounts, each reads the other's as missing.
(c) W9 asks for a trade row. The reconciler holds only the node journal, and a unit journal has one writer.
(d) The closing deal is asked for by position id, and no journal row holds a position id, so after a restart that request cannot be made.
What goes wrong for him: an alarm and a phantom close for each old trade at every restart, and a doubled paper score.
Edit: replace the box with these four. A send counts only if it is `kind` entry, in this account's demo world, has a `filled` row or a resolved unknown, and its unit journal has no `trade` row for that position. The close goes through the hosted unit, which adopts the position with `_closed` set, so the handler writes the trade; with no hosted unit, alarm only. Journal `positionId` in the `filled` note from this PR on, and with no id use `ProtoOADealListReq` over the send's time window, or the guess alarm. Add a test: two old stop-outs and one paper send, restart, no alarm and no new row.

**plan-review-b-5. R23. fix.** `p5a-11` rests on a false claim, "already writes `road/host/facts.json`" and "only adds two facts to a file it already writes". `keep_facts` runs only after a Settings write (`host.py:2019-2026`), and the clock is probed in the heartbeat loop, which never refreshes facts (`:1472-1475`). With the plan's "a stale reading reads None", a real node reads None within a minute and the clock stand-down still never fires. The plan's test writes the file by hand, so it passes while the row is still true.
Evidence, level 3. Edit: add "the probe loop calls `refresh_facts` after each probe", and a crossing test with a real supervisor where a drift reaches the node's volume with no Settings write.

**plan-review-b-6. R15. fix.** The new code the box adds lives in a closed list R15 does not touch. `RunJournal` is not the only gate: the writer checks `reason` against `REASON_CODES` (`packages/qmf-data/src/qmf/data/journal_kinds/unit.py:43-74`). With the code added only in `journal.py`, the writer refuses the row, `_refused` is set, and the journal dies exactly as today.
Evidence, level 4, `p2_small.py`: `_signal` answers "reason is one of ... not 'unlisted'". Edit: add that file to Files, and `packages/qmf-data/tests` to lane 1.

**plan-review-b-7. R20, R24, Appendix B. fix.** The brief's question: what can the real broker do that the sketch assumes away? `venuewins.py` never asks for history. It books every missing position at the held stop. So the only run says nothing about the history path. Against the pinned definitions and the catalogue:
- `ProtoOADeal` has no kind field, only `orderId` (level 4, `p3_defs.py`). "Fill `_closed` with its price and kind" needs a join to `ProtoOAOrderListByPositionIdReq`. The fake must answer only pinned fields, or the test is kinder than the wire.
- `ProtoOADealListByPositionIdRes` has `hasMore`, and the time window is optional with no stated default. A position with several deals may not show its closing deal on the first page. Named on the demo list: no.
- One missing row is taken as closed. The catalogue's own rule is "a missing report is not flat" (`catalogue.md:628`). On the silent branch the box says "never leave a position held". If the position comes back at the next session, `_reconciled` refills `_open` but `_closed[name]` stays, so `closed()` keeps answering and R21's kill skips it (`runtime.py:2130`). Named on the demo list: no.
- "Read `stopLoss` on every non-closing event" has no rule for an absent field. `_amend` keeps the old stop when it is absent (`ctrader_account.py:1348`), but this box does not say so. If a real event omits it, the stop reads gone. Named on the demo list: no.
- Named already, and right: stop on the fill, close on a gone position, `clientMsgId`, deal fields, `AccountDisconnect`.
- Nothing acts on the answers. Lane 6 says they are "saved". `node-n5` appears in R23 and Appendix E but not in Appendix B, so it has no home.
Edit: in R20, say the silent branch asks reconcile once more first, a later listing clears `_closed` with an alarm, and an absent `stopLoss` on an event keeps the held stop. Only a reconcile row may clear it. Add three questions to R24's demo list. Add to Appendix B, After G-DEMO, "read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5`". Add the same line to Appendix G.

**plan-review-b-8. R21. fix.** `p5a-7` acts only "after `adopt`", which skips any name already in `placed` (`runtime.py:1447`). R20 now makes a stop lost during a dropped connection visible, as `held.stop = None`, and nothing acts on it. What goes wrong for him: the position sits with no stop at the broker after a reconnect, the same process. This breaks "every order carries its stop". W9 tests only a restart.
Evidence, level 3. Edit: run the put-back-or-close steps for every position a unit holds whose stop reads None after a reconcile run, not only at adoption. Add a test on a reconnect.

**plan-review-b-9. R21. fix.** "Add a refused unit exit to the existing retry set" does not say which refusals. Partial closes and stop moves also answer `Blocked` through the same branch, including this PR's new past-entry `Blocked`. In the retry set, a refused stop move closes the whole position. The sketch excludes both (`reach.py:43`), but the box does not.
Evidence, level 2. Edit: add "a full close only, never `ClosePartial` or `AmendProtection`", and one test that a blocked stop move leaves the position open.

**plan-review-b-10. R23. fix.** `p5a-16` rebuilds paper positions "from the send, filled and closed rows". A paper stop that fires writes no node journal row (`paper_lane.py:88-90`). Only the unit journal has its trade. So each past stopped paper trade comes back as an open position at restart, then may close a second time. That is the paper record he judges by, and it is the fault this row exists to end.
Evidence, level 3. Edit: drop any send whose position has a `trade` row in the unit journal. Add that case to the test.

**plan-review-b-11. Appendix F. fix.** The brief's question: would the risk session have what it needs from this list alone? Nearly. Placeholder numbers 8, 9, 10, 11 and 18 check out against the file. Three holes:
- It never names `P/build/RISK-SIZING-PLACEHOLDERS.md`. The plan holds no mention of it, so "placeholder 9" points nowhere for a session in another worktree. Likewise `CONTRACTS.md`, `ground-unit` and `seams/wick.py` have no path.
- `A/REPAIR-SCOPE.md:132`'s hand-off includes the placeholder sizer being wrong on USDJPY (`reports/p0a.md:99`: it divides account money by a loss in the quote currency). It appears nowhere in this plan.
- It does not say what R04 now refuses at compile, the six exits by name, or that flatten does not stop a unit (call 13).
Edit: three lines at the top of Appendix F: the paths, the USDJPY item, and the refused list with its pointer.

**plan-review-b-12. R24. fix.** The C-15 marks rehearse "against the conformance venue", copied from the old plan. `ConformanceAccount` takes a `Ticket` and speaks no cTrader wire. So each probe's wire code (`label` with `relativeStopLoss`, a part-volume close, the order list) first runs on his demo. A rehearsal PASS proves the script's shape, not the crossing, which goes against rule 8. What goes wrong for him: the first G-DEMO run can fail on a probe bug and read as a broker fact.
Evidence, level 2. Edit: rehearse the marks on R20's harsher fake cTrader over the real codec, and teach it a part-volume close, because `_on_ProtoOAClosePositionReq` pops the whole position today (`test_app_binding.py:312-313`).

**Notes. True and small.**
- plan-review-b-13, R21. The new method must join `unit.venue_open()` and the orphans. `reconciler.mine` is a snapshot from the last run, so it misses positions opened since, and paper positions. W10 would catch this. "The same `covers` test" cannot apply to an orphan, because `instrument_scopes` needs a unit. Name `same_market`.
- plan-review-b-14, R21. "Read those rows the way `journalled_resumes` does" copies its failure rule, where a refused folder reads as holding none (`runtime.py:1823`). For a flatten that replays old ops on new positions. A refused read must hold the op, not act on it. Also name the row kind; `kill_level` is the one that exists.
- plan-review-b-15, R21. The kill row's `positions_closed` is written once, at the rising tick (`runtime.py:2185-2190`). A RED pressed with the session down, or held across a restart before the first reconcile, reads 0 and then closes. "Counts them truthfully" holds only when the first close succeeds. Say so, or add a done row as flatten has.
- plan-review-b-16, R16. `test_qmn_alerts.py:40,60` asserts the old `FAILURES.md` path, and `containment_limit.py:425` reads it. Neither is in Files or lane 1, so the red waits for R19's whole-repo run.
- plan-review-b-17, R15. The census as written checks only `Blocked` and `Skip`, so it cannot see `Unprotected`, the class of `:1609`. Add `Unprotected`. `:1186` cannot reach a journal row at all, since a close's `Blocked` writes no `Skip`, so "an entry blocked with each of the four texts" would need a planted row. Make it three, plus the census for `:1186`.
- plan-review-b-18, R23. `Backoff` starts at 1 s with a 60 s cap (`healing.py:57-59`), about 60 sign-ins an hour, above the 40 rule. "Top wait 5 minutes" needs `cap_s=300`, and "first retry at once" needs a small wrapper. Separately, `market_hours` raises `LookupError` for a market no deployment names, such as the self-test's, so `StandDowns` must read that as open, as the push sender does. Lane 1 would catch it. The "no stop at the broker" word lands in `reconciler.py:_shown`, which is not in Files.
- plan-review-b-19, R24. "`_dummy_version` goes", yet `--unit` still needs a version lookup, so keep it under a general name.
- plan-review-b-20, R20. "Take volume from the broker's row" changes `_open`, not the handler's `OwnPosition.quantity`. After a part close by hand, the trade row books full size. Close orders are right. The Library's money field is not, until R21 or later feeds it.
- plan-review-b-21, R21, `known-1`. "Alarm if they differ" should compare after rounding to the symbol's digits, or a trail on an unrounded indicator value alarms each time. The handler keeps the asked stop whatever `Placed` says (`unit_handler.py:605-607`).
- plan-review-b-22, R22. `symbol_facts_missing` still refuses the whole session for one symbol (`ctrader_account.py:820-826`), the same class as `node-n1`. Treat it as unlisted. Widening also costs running units on that account one bar with no row, because `_shut` clears `_building`. That is known and accepted only implicitly, so name it in You see.

## 2. Sound

**`known-1`, the brief's question: the line is right.** A stop past entry answering `Blocked` adds no risk beyond the held stop, which is his ruling (R:28, TR:9). No shipped unit can reach it. The signed distance stays with the risk session, and Appendix F says so. Conditions: finding 9 and note 21. The silence is cured for past-entry only. A venue-refused or widening amend still leaves no row, because `execute_resting` writes one for entries only. Harmless until the exits socket. One row there would cover all cases, cheap if a builder is on that line anyway. A stop exactly at entry is not refused and is not past entry, so it goes through (level 4, `p4_entry.py`). That is correct.

**R24 and the old plan lines.** All six rows of Appendix B match `plan-current.md` at the lines named. `landed_refusal`, `_deployed` and `_trade_rows` read as the plan says. `_journal` and `_trade_rows` do not depend on a deployment, so the plain path can pass. Nothing else reads `world.deployment`. `--landed-on` defaulting to `engine/base` fits his words and `US:282`. Call 18's owner lane is rightly fenced.

**Safety facts rerun at this commit.**
- R20: `test_app_binding.py -p venuewins`, 17 passed. It holds for `read_back`, not for `node-n4`.
- R21: the RED reach, kept case above, kill row 1, broker empty.
- R15: `p1_trade_account.py`, trades 0 and paper runs 0 as written, 1 and 1 with the account set. Census prints `no code 3`.
- R16: `alarm_wheel.py`, today refused and `push: None`, inside gives `PushSender`.

**Sections right as written, apart from the above.**
- R15's strict and tolerant split; `guard.check` stopping entries with exits free; `journal_problem` at `operations.py:843-871` is already the status path.
- R16 whole, including call 15 and call 16. `doctor_line`, `record_of` and `telemetry.py` read as claimed.
- R17's `tool_timeout` line and its R03 trap, which R03's `start-n1` box truly sets up. `p5d-6`.
- R18: `source` is per market in `mis_core.py:552,573`, so one configure call fits. `instruments()` exists. Not on the order path. It adds only what his "nothing calls configure" row needs.
- R19's harvester bound and minute row. `_row` stores the whole record, so projection from the store can work (`records.py:298-300`). `journals_open` is true on This PC.
- R20's `p5a-9`, `node-n2`, `node-n3`.
- R21's `p5a-6` flow, the trap at `trading_node_app_test.py:258-260`, and the subtraction list.
- R22's `_host` wait and `_authorise` change. `chief-1` in R23: six literal facts and three from the session, as claimed.

**Size.** Each section's tests are few and cross a connection. I would cut nothing. Ten lanes per PR is the plan's frame, and only four run.

**Appendix E, ten rows drawn by shuffle, plus out rows.** A real Build box exists for `p5a-3`, `p2-4` (must), `p5a-11`, `triage-5`, `triage-8`, `plan-check-5`, `p0a-7`, `p5a-18`, `p34-2`, `known-12`. Out rows `known-7`, `p5a-17`, `p5b-4`, `deletion-7` and `p6-8` hold the reason shown and sit in Appendix B. So the table is honest about placement. One of the ten, `p5a-11`, is placed and not cured (finding 5). That is the gap the brief warned of.

**Appendix G.** Fair. The one missing risk is in finding 7.

## 3. Rows

- `p5a-4` (must): cured by R21, then broken again by R22 for any market but the self-test's (finding 1).
- `p5a-2` and `node-n4`: the connected half cured, the process-down half not as written (finding 4).
- `p34-1` (must): the row is cured at R15. R19 as written then corrupts the paper-run half (finding 3).
- `known-1` (must): cured in part as the table says, with no shipped unit able to reach it.
- `seams-5` and `p2-4`: "in part" is true and honestly labelled.
- Should rows: `p5a-11` not cured (finding 5). `p5a-16` trades one wrong record for another (finding 10). `p5d-3` closes one hole and opens a worse one (finding 2).

## 4. For the chief engineer

**What the old-node cut waits on.** The two logs and moving `sqs_baseline_producer.py`. By the letter that is `VAL:45`, "C-14's real run and C-15". The substance narrowed, and the plan says so plainly. `test_trade` is a binding-level trade (`ctrader_account.py:1351`), which never crosses `OrderPath`, the handler or `_drive`, and C-15's marks do not either. So after G-DEMO the unit's real order path has still never met the real broker, and the old node could be deleted with no unit ever having traded on demo. The census shows the new node loads none of the old code, so no fallback is lost, and I would not change the gate. But "as he ruled" is too strong: he ruled when C-14's real run meant a unit trading, and `VAL:45` itself says "decided here without asking".
Set aside for him: may the old node be deleted before any unit has traded on demo? Default assumed: yes, on the two logs. Edit: one sentence in Close the program's G-DEMO message, so he hears it.

**Nothing else** in the shape's calls is contradicted. Calls 13, 14, 15, 16, 17, 18 and 19 hold against the code. Rule 5's schedule leaves R21 to R23, three money PRs on one file, without a whole-repo run. Finding 1 is what that costs. Adding each earlier PR's new test file to lane 1 is cheaper than moving the schedule.

## 5. Not reached

- `truth2.py` g6, g7 and g9 for R22 and `proof_waiting.py` for R17 were not rerun; I relied on the grounding reports. `mis_real.py` was run and printed nothing I could read, so R18's "4 readings" is not re-proved here.
- R22's snapshot trigger, "when a slow number moves": whether one clear signal exists.
- Whether the C-15 refresh drill, run from a separate process, invalidates the running node's session. It touches `qmn/secrets/rotation.py` and only demo can settle it. Worth adding to the demo list.
- R23's `seam_check` shape, and `test_app_env_data.py` with real uv.
