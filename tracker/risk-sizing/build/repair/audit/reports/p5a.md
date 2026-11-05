VERDICT: REPAIR

Part p5a, Phase 5: the trading node itself, at commit 50c83a4e.

## 1. What this part is for

The trading node is a mini app, the only thing in QMX that sends an order. He tells it what he wants (deployments, kills, pauses), it writes that down in a small database, and one background thread keeps steering towards it. That thread hosts each unit through the same handler QMB uses, sends each order with its stop at the broker and a journal row first, and reads the broker back at every session. It heals itself after faults, stands down when health checks fail, and wakes his phone through ntfy. The design is sound and the order path is careful. The defects sit where the fake venues do not behave like a real broker on a bad connection.

## 2. Counts

Files opened 41 of 41, plus `ctrader_account.py` and parts of `unit_handler.py`, `promote.py` and `journal_writer.py` to trace paths. Lines read about 18,000. Test functions read 161 (more once parametrized). Hollow tests 0, deletable 9. Findings: must 7, should 22, leave 5. Lines that could go 216 (85 of code and test in p5a-23, 131 of tests). `qmn/src/qmn/app/` holds 8,839 lines. My guess at a plain version is about 6,000; the design guessed 3,000 to 5,000 before C-12d, C-22 and C-35 added work. `runtime.py` at 2,648 lines does six jobs and should be split for the reader, but that removes no lines (judgement call).

## 3. Paths traced

1. **His click to a live order and its stop.** Sound against the conformance venue and the fake cTrader: tags, journal before dispatch, the stop gate, lost answers, partial fills. Broken in one place: the feed's markets are fixed at bind, so a unit on any market but EURUSD never gets a bar (p5a-1).
2. **His kill and flatten to a closed position.** Sound for positions a hosted unit holds, with retries on refusal. It misses positions no unit holds (p5a-4). Flatten is a no-op (p5a-6). A position already gone at the broker is closed for ever (p5a-2).
3. **A restart or a dropped connection back to a true picture.** Attribution and the UNKNOWN drill are sound. Three gaps: a stop fired during the outage is never noticed (p5a-2), a position with no stop is adopted silently (p5a-7), and a restart before the network is up starts the unit with equity 0, so it never trades and still reads "Trading" (p5a-5).
4. **A unit's exit while the venue is unhappy.** One refusal loses the exit for good, silently (p5a-3). The test that claims otherwise uses a fake that ignores the session state (p5a-21).

## 4. Sections

| Id | Origin | Verdict | Blast-radius fact, held or not, level | Keep, fold, cut |
| --- | --- | --- | --- | --- |
| C-10 | original | met, except flatten (p5a-6), which no section built | Operations answer inside 30 s: held at level 2 by reading; `trading_node_app_test.py` not rerun, see section 11; a stalled sign-in is a guess at 40 s (p5a-28) | - |
| fix-node-proofs | fix | met; proofs and own suite present | Road test not rerun, see section 11 | - |
| C-12a | original | met on its done line against the conformance venue | One handler serves QMB and the node: held, level 4 (my proofs traded through it; `runtime.py` imports `UnitSliceHandler`) | - |
| C-12b | original | partly: "protected" is only a word (p5a-14) | Kept organs pass shipped tests: not rerun whole, level 2; `test_app_unknown_drill` and `test_app_reconcile_filled` pass, 8 of 8 | - |
| C-12c | original | partly: exits lost when the venue refuses (p5a-3), clock row cannot fire (p5a-11), paper positions lost on restart (p5a-16) | Every stand-down keeps exits, broker stops and the kill: NOT held for exits, level 4; broker stops and kill held | - |
| C-18 | original | met; setup cards with a test send present in `connect_node.py` | Closed push list unchanged: held, level 4 (empty git diff, list printed) | - |
| C-13 | original | partly: heal, crash-loop, frozen exit and risk stops are sound; a process restart does not restore (p5a-15), equity 0 (p5a-5), missing stop (p5a-7) | `CrashLoopFold` callers moved: held, level 2 (grep; `_supervision.py` imports it from `qmn.app.healing`) | - |
| C-12d | added | partly: the four operations and the demo-only binding are sound; feed fixed at bind (p5a-1), 15-minute bars only (p5a-18) | Hosts keep refusing live grants: held, level 2 (no change to those lines in `adapters.py`) | keep: without it no real trade |
| C-12e | added | partly: all three done-line fixes work; its "You see" line fails (p5a-2) | QMB backtest unchanged: level 2, `filled` defaults to None | keep: money path |
| C-30 | added | partly: calendars, escalation memory and the 2027 data work; `rotate_keys` in production re-reads the old copy (p5a-12, disclosed) | Closed push list unchanged: held, level 4 | keep: alarms were dead without it |
| C-35 | added | met for every hosted position; the kill gap is p5a-4 | Kill at `all` as at the parent: held at level 4 for hosted units; `test_app_status_truth` 8 of 8; `test_app_kill_scopes` did not finish under 110 s, see section 11 | keep: the kill must tell the truth |
| C-29 | added | partly: met on the conformance venue, refused row and dropped refusals work; on a real binding see p5a-1 | Click-only promote: held, level 2 | keep |
| C-38 | added | met as far as I could run it: first-party restart and calendars read; the `--no-editable` env test needs a long run | Pin and no extension imported: level 2; `find_spec` imports nothing | keep |

**Invariants.** AD-301 process shape holds. AD-302 closed never-raising operations hold; `flatten` breaks the promise of its row. AD-305 identity and tags hold; `take_over` is a stub. AD-306 grants hold; the demo-only gate is firm in three places. AD-308 cTrader stop rule holds; the netting refusal is missing (p5a-20). AD-315 holds, with `safe_to_restart` stricter than designed: any open position reads unsafe. AD-317 refuses only some of its named preflights; broker-history warm-up is absent (p5a-19). AD-319 is not wired on the node (p5a-11). Only the node sends orders: holds.

## 5. What is fine

- The order path: guards, stop gate, journal before dispatch, one send per client order id, no resend on UNKNOWN. Careful and well tested.
- Store and operations: arrival order, `superseded`, repeated and reused op ids, clock-skew refusal. Sound.
- Identity and attribution: mine, twin, foreign, untagged. Sound and small.
- Grants: store before discard, one refresher, tokens never printed, live-capable discarded, demo host only. Sound.
- Healing: back-off, crash-loop fold, stuck exit, the kill level and risk stops surviving restarts. Sound.
- Risk-stop lifecycle rows, including a row that cannot land at once. Sound.
- Alarm senders: failures never touch trading; waiting and pushed rows survive restarts. Sound.
- Status truth (C-35): never "Trading" while a kill, pause or stop holds, apart from the two silent cases above.
- C-29 market filter, `starting` numbers and the refused-deploy row. Sound.
- Manifest, app entry and road proofs. Sound.

## 6. Must and should findings

Must:
- p5a-1: a unit on any market but EURUSD after bind never gets a bar.
- p5a-2: a stop fired during an outage is never noticed; the position stays open for the node for ever.
- p5a-3: a refused unit exit is lost silently.
- p5a-4: the kill does not close a position no unit holds.
- p5a-5: a restart before the network is up starts the unit with equity 0; it never trades and reads "Trading".
- p5a-6: flatten says accepted and does nothing.
- p5a-7: a restart adopts a position with no stop, with no repair and no alarm.

Should:
- p5a-8: a deployment made before the bind waits for ever.
- p5a-9: a self-test trade left open sends the node into a healing loop.
- p5a-10: five full sign-ins a second when a session cannot open.
- p5a-11: the clock stand-down never fires on a real node.
- p5a-12: `rotate_keys` re-reads the old keys.
- p5a-13: polling `journal_tail` loses order rows.
- p5a-14: "not ours, protected" on a position with no stop.
- p5a-15: a process restart loses calibration silently.
- p5a-16: paper positions vanish on restart.
- p5a-17: partial closes dropped on the node, booked in QMB.
- p5a-18: 15-minute bars for every unit, whatever it was tested on.
- p5a-19: broker-history warm-up missing, so the first demo trade is about two market weeks away.
- p5a-20: two units on one symbol of a netting account not refused.
- p5a-21: the stand-down test's "exits still go" rests on a fake.
- p5a-22: every weekend reads "Stopped by a health check".
- p5a-23: code for journal rows that never existed.
- p5a-29 to p5a-34: eight tests to delete; p5a-23 takes a ninth with it.

## 7. Test verdict

These tests are worth having. They call the real node, compare literal values and catch real failures; none is hollow. The 7,538 lines are large mainly because of a good fake broker (about 470 lines) and full recorded runs. He is right to doubt them in one way, and it is not the number: both fakes are too kind. The conformance venue ignores session state, and the fake cTrader never loses an execution event or refuses a socket, so every must above passes green. Nine tests could go (about 195 lines, counting the test in p5a-23). Each must has no test today, and each needs one.

## 8. Golden and reference data

No golden files of their own. `proofs/*.json` are hand-written literal cases. The numbers tests pin (1.72, 1.08, 0.75 lots, the 1.06858 price) come from running this code over QML's synthetic month, so they are regression pins, not independent truth. The independent check is the relation CA-03: sent quantity equals the sizer receipt after lot rounding. `openapi-91.pb` is Spotware's file with a pinned hash (mine read `044991dd5fd4ea99...`; the pin test itself is in section 11).

## 9. The ten edge-case functions walked

`CTraderVenue.read_back` and `_reconciled`, `NodeUnit.execute_resting`, `NodeUnit.adopt`, `Runtime._enact`, `Runtime._host`, `FeedKeeper.pump`, `Reconciler.run` with `_position_row`, `Target.fold`, `answer_change`, `Grants.refresh`.

## 10. Set aside for him

- Flatten: keep it beside RED, or cut it? I assumed keep and make it close.
- A kill on a position no unit holds: close it as well? I assumed yes, since it carries the node's tag.
- Fetch broker history so the dummy can trade soon after bind, or accept about two market weeks of warm-up? I assumed fetch.

## 11. Needs a long run

Each from `D:/QMX-worktrees/audit-head` after `source D:/QMX-worktrees/audit-ship/tools/env.sh`:

- `"$AUDIT_ROOT_ENV" -m pytest qmn/tests/test_app_kill_scopes.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p5a/k` (did not finish beside `test_app_status_truth` in 110 s).
- `"$AUDIT_ROOT_ENV" -m pytest tools/tests/test_app_env_data.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p5a/e` (C-38's installed env).
- From `qmx-agents`: `"$AUDIT_AGENTS_ENV" -m pytest apps/trading-node/tests packages/qmx-broker/tests/test_protocol_default.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p5a/n` (real supervisor, the road, the pinned hash).

My proofs: `D:/Temp/audit/p5a/proof1.py`, `proof2.py` and `proof3.py`. Each runs with `"$AUDIT_ROOT_ENV"` under `timeout 120`. Results are quoted in `D:/QMX-worktrees/audit-ship/findings/p5a.tsv`.

## 12. Not read

Nothing in `files.tsv`. `proofs/*.json` and `uv.lock` are in `not-read.tsv`. No real broker behaviour was tested. Whether cTrader's fill event carries `stopLoss` and how it answers a close on a gone position are unproven until C-15's demo probes.

## 13. Skills that changed a decision

- blast-radius: made me run the C-12c fact, which failed for exits, instead of trusting its test.
- lens-verification-gap: made me ask what the fakes cannot do, which led to p5a-1, p5a-2 and p5a-21.
- lens-edge-case-hunter: the empty branches in `Runtime._host` and `NodeUnit.adopt` led to p5a-5, p5a-7 and p5a-8.
- principle-test-behavior-not-implementation: kept the delete list short, because almost all tests assert literal results.
- principle-laziness-protocol: p5a-23, compatibility for rows that never existed.
- principle-minimize-reader-load: the judgement on `runtime.py`, recorded without a finding because splitting removes no lines.
- principle-prove-it-works: every must was run against the real node code at level 4.
- code-review: two axes kept "tests green" apart from "promised line works".
