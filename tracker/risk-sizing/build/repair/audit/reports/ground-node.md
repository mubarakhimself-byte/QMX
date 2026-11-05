# Grounding: the trading node as a running thing

Code at `50c83a4e`. Proof scripts are in `D:/Temp/audit/ground-node/`: F1 to F5 are `truth.py`, G1 to G9 are `truth2.py`, H1 and H2 are `truth3.py`. "Sketch" means real node code patched in memory by my script, with no file changed. Levels are from the system prompt. `runtime.py`, `server.py`, `operations.py` and the like are under `qmn/src/qmn/app/`. `ctrader_account.py` is under `qmn/src/qmn/venue/`.

## 1. What this area is and how it really works

The node is one mini-app process with two working threads. Operations write his wishes into `data/node.sqlite`, and they never touch the broker. One runtime thread ticks every 200 ms (`runtime.py:2078`). Each tick folds the wishes into a target, applies kills, starts deployments, pumps each account's feed, reconciles once per session, then drives units on closed bars. Each unit runs through the same handler QMB uses (`qmb/host/unit_handler.py`), and an order leaves through `OrderPath`, which writes the journal before it sends. On cTrader, `CTraderVenue` holds one socket and a memory of open positions (`_open`), and that memory is what the rest of the node asks. The older organs under it are real and in use: the live client and codec, the order and protection laws, the ledger, the stop gate, the kill table, the loop driver, the clock bands, the grant rotation rule and the alarm senders. A census of what the node actually loads shows 35,578 lines of `qmn`, and none from `host`, `seats`, `promotion`, `paper`, `doors`, `bench` or `capital` (level 4, `census.py`). The old `qmn/reconcile` is not loaded either: the design said to keep it, but the build wrote a new `reconciler.py`. The design is sound. The weakness has one shape: the node trusts its own memory where it should ask the broker, and the fakes never made it pay for that.

## 2. What must not break

- Every order carries its stop at the broker: `qmn/tests/test_protection_every_order.py`.
- Journal before send, one send per client order id, no resend on UNKNOWN: `test_app_unknown_drill.py`, `test_app_reconcile_filled.py`.
- Partial fills book the broker's size: `test_app_partial_fill.py`.
- Positions without his node's tag are never touched: `test_app_attribution.py`. A kill repair must close only `Claim.MINE`.
- Operations answer fast and never raise, and deploy answers before compile: `qmx-agents/apps/trading-node/tests/trading_node_app_test.py`, `test_app_operations.py`. Note that `trading_node_app_test.py:258-260` pins the flatten bug, so that one line must change.
- Kill is escalate-only and his resume brings it down. Status never reads Trading under a kill: `test_app_kill_scopes.py`, `test_app_status_truth.py`.
- Healing, crash-loop fold and risk stops survive restarts: `test_app_healing.py`.
- Demo-only binding and grants: `test_app_binding.py`, `test_app_grants.py`.
- The closed push list: `test_app_alarms.py`.
- QMB and the node decide alike, 63 of 63. No repo test holds this, only `D:/Temp/audit/seams/parity.py`. Rerun it after any change to `NodeUnit`.

## 3. Problems

### Cause A. Broker wins on reconnect (p5a-2, part of p5a-7, and new cases)

**Real cause.** The finding is right and understated. `_reconciled` (`ctrader_account.py:689-690`) returns its own memory for any position it already holds and ignores the broker's row. So a reconcile can never see a stop that fired, moved or was removed, or a size that changed. The missing-position case is only the loudest. F1 proved it: broker stop 1.07522 and half the size, node stop 1.08022 and full size, and the reconcile row writes the node's memory under `venue_stop`. H2 proved a stop he moves by hand while connected is not read either, because `_execution` (`:1095-1101`) updates only volume. G3 proved a stop fired while the process was down leaves no trade row and no alarm, and status reads Ready.

**Around it.** `read_back` is called only by `Reconciler.run`. `closed()` drives `NodeUnit.protective`, `venue_open`, `_orphans` and the kill. So one truthful `_closed` entry heals all of them.

**Safety fact, level 4.** Broker-wins `read_back` breaks no shipped test and heals the rest. `venuewins.py` patched it in: `test_app_binding.py` 17 pass, `test_app_reconcile_filled.py` and `test_app_partial_fill.py` 11 pass. On the outage case (G2), today gives closed None, handler holds, trade rows 0, entries after 0. The sketch gives closed STOP, trade rows 1, safe to restart true, entries after 2.

**Repair shape.** One place, `CTraderVenue.read_back`. For each held position, take stop and volume from the broker's row. For each held position the broker no longer lists, ask `ProtoOADealListByPositionIdReq` (present in the pinned definitions, F5) for the closing deal, then fill `_closed` with its price and kind. If history gives nothing, close it at the held stop and raise an alarm that says the price is a guess. In `_execution`, read `stopLoss` on every non-closing event. For the process-down case, the reconciler compares the journal's sends without an exit with the broker's list and writes the missing close. `_position_row` skips a send with no stop (p5a-9, proved by the auditor, same file).

**Proof.** `truth2.py g2`, `truth2.py g3`, `truth.py f1`, `truth3.py h2`, moved into a test against the fake. Each fails today.

**Order, files, size.** First. `ctrader_account.py`, `reconciler.py`, fake in `test_app_binding.py`. About 90 product lines, 60 test and fake. Ours.

### Cause B. Every way out must act (p5a-3, p5a-4, p5a-6, p5a-7, known-1, p5a-21, p5b-3)

**Real cause.** There are three separate closers and none is complete. `_enact` (`runtime.py:2231-2235`) walks hosted units only. `_apply_flatten` (`operations.py:549`) returns a constant, and `Target.fold` has no flatten branch. `execute_resting` (`runtime.py:1521-1530`) marks a refused exit done. `NodeUnit.adopt` (`:1464`) feeds the journal's stop to the handler and sends nothing to the broker.

**Around it.** `_protect` (`runtime.py:2255`) already closes on every tick until the broker shows closed, and it is tested. `close` already counts refusals and raises the alarm at the third. `_orphans` already names the unhosted positions. `amend` already moves a stop on the real wire. Nothing new is needed but joining them.

**Safety facts, level 4.**
- `OrderPath.close` reaches an orphan on the real binding, because `_reconciled` filled `_open` (F2). With the sketch, RED leaves the broker empty and the kill row reads 1. Today it stays open and the row reads 0 (`truth4.py`).
- Adding a refused exit to the existing retry set books the trade: today 1 close, 0.75 still open, 2 trades. Sketch: 2 closes, flat, 3 trades (`truth4.py`).
- `amend` puts a missing stop back on an adopted position at the journal's level (G5). If the price is already past the stop, cTrader refuses it (fake reads `TRADING_BAD_STOPS`), so the shape must fall through to a close and an alarm, which is what `_protected` does for a new entry.
- With the sketches and the harsher conformance venue, `test_protection_every_order.py` and `test_app_status_truth.py` pass 26 of 26.

**Repair shape.** One runtime method closes every `Claim.MINE` position in a scope, hosted or not. Kill calls it each tick while the level holds. Flatten calls it for each flatten op not yet journalled done, keyed by op id the way `journalled_resumes` does, so a restart never replays an old flatten on new positions. A refused unit exit joins the retry set. After `adopt`, a position with no stop goes through the `_protected` steps (put it back, then close and alarm). `amend` returns the broker's stop instead of the asked one, and an alarm if they differ. Runtime passes the current quote as the close's reference, which is harmless on cTrader and clears p5b-3 at the same lines.

**Whose.** What each level does is the risk session's (placeholder row 18). See "Kill effects" below. The signed distance is theirs.

**Proof.** `truth4.py`, and a flatten check added to it. Fails today.

**Order, files, size.** After A, since the kill leans on `closed()`. `runtime.py`, `operations.py`, the test line above. About 120 product lines, 80 test lines. seams-3 (cluster 3) must land before or with this PR: the orphan guard text at `runtime.py:2301` and the text at `:1609` are the two that silence the unit journal, and this PR makes both more reachable.

### Cause C. What he deployed runs (p5a-1, seams-4, p5a-5, seams-6, p5a-8, p5a-20, p5b-6, p5a-15, seams-11)

**Real cause.** `_host` assumes the world is ready when the compile ends. It reads equity whether or not the session is up (`runtime.py:2448`, balance starts 0 at `ctrader_account.py:587`), throws the compile away when no venue is bound (`:2403`, and `_deployments` retries only COMPILING), never tells the feed about a new market (`server.py:570,584` read `_markets` once), never checks netting, and never reads a saved calibration.

**Around it.** p5a-5 and p5a-8 are one fault, the same `_host` step. `_markets` (`server.py:852`) walks every market of every kept deployment. The reconnect path is tested and already resets feed, books and reconcile.

**Safety facts, level 4.**
- Holding the compiled unit until `feed.ready` fixes both: `truth2.py g7` shows waiting during the outage, then equity 10000.00, trading, 2 entries. Deploy before bind moves from waiting to warming once bound.
- Widening through the existing reconnect needs no new protocol: `truth2.py g6` subscribed `['1','41']`, bars arrive, the EURUSD position stayed held at broker and node, and the last reconcile reads `reconnect`.
- The unit's own snapshot survives JSON and restores identically: `truth2.py g9`, 37,988 bytes.

**The trap this repair must not fall in, level 4.** New defect N1 below. `_authorise` refuses the whole session if one symbol is unlisted, so widening without a check would kill a working account.

**Repair shape.** `_host` waits with a plain reason and keeps the compiled unit until the session is ready. Widening adds the market and drops the session once, and the deployment is refused by name if the symbol is unlisted. `_authorise` keeps the listed markets and reports the others instead of refusing all. A one-rule refusal for a second unit on a symbol where `position_model` nets, the same rule for a Hyperliquid coin (p5a-20 and p5b-6, one seam). Calibration: write `hosted_unit.snapshot()` under `data/deployments/<id>/` when a slow number moves, pass it to `unit.start`, which already calls `restore_unit` and writes its cold reason when it cannot resume.

**Order, files, size.** After B. `runtime.py`, `server.py`, `ctrader_account.py`. About 110 product lines, 60 test lines. Calibration content belongs to the unit, but saving it is plumbing and ours.

### Cause D. The bars he tested on (seams-5, p5a-18, seams-12, p5a-19)

**Real cause.** `BAR_NS` is one number per binding (`ctrader_account.py:114`), and `Recording` is keyed by market only. Warm-up reads only the node's own recording (`runtime.py:2459-2463`). AD-317 promises broker history after it, and no code requests it in the node.

**Corrections to the easy reading.** History is not one call. `ProtoOATrendbar` holds low and deltas of one side only, and `QuoteBar` needs bid and ask. The PC already decodes these at `qmx_broker/adapters.py:265-290`. The rest of the gap, retention and which side, can only be read on demo (EX-04). The same reader fills bars lost during an outage, a hole the unit sees today with no row (walked, level 2, `_shut` clears `_building`).

**Safety fact.** Unproven for history, needs the demo. Level 2 for the refusal: QMB already parses stream names (`unit_runner.py:244`).

**Repair shape.** Step 1, 15 lines: `_host` compares the stream's seconds with the venue's and refuses by name. Step 2: `_building` and `Recording` keyed by market and size, the bar row gains its size, one feed serves all sizes. Step 3: broker history at `_host`, with the ask built from the current spread and labelled so.

**Proof.** `D:/Temp/audit/seams/feed.py bars` flips to a refusal after step 1, then to 5-minute spacing after step 2.

**Order, files, size.** Step 1 joins C. Steps 2 and 3 are their own PR, about 200 product lines and 60 test and fake lines. Ours.

### Cause E. Bad connections and honest words (p5a-10, p5a-11, p5a-14, p5a-16, p5a-22, chief-1)

- **p5a-10.** `FeedKeeper.pump` (`feed_keeper.py:286`) reopens on every tick. Reuse `Backoff` from `healing.py`, first retry at once so `test_app_feed_reconnect.py` keeps its meaning. About 15 lines. Level 2.
- **p5a-22.** `watch_feed` ignores the calendar. `alarms.market_hours` (`alarms.py:575`) already answers open or shut, and alarms use it. Pass it to `StandDowns`. About 10 lines. Unproven whether a test runs across a weekend.
- **p5a-11.** `StandDowns` takes `clock_offset_ns`, and the clock row passed in `test_app_stand_down.py` with an injected probe, so only the wiring is missing. The design has the node import `qmx_host/clock_probe.py`, but that imports the harness and engine. I made the call: the host already probes every 60 s and already writes `road/host/facts.json` into the volume, so the facts gain the offset and its time, and a stale reading reads None. No new network from the money process. About 30 lines.
- **p5a-16.** Paper positions are memory only (`paper_lane.py:55`). Rebuild from the node journal's `paper` partition (send, filled, closed rows) and call `adopt`. Stops crossed while down fire on the next bar, which I accept. About 60 lines. Level 2, not run.
- **p5a-14.** Word only. See "Set aside".
- **chief-1.** See corrections. Change the `detail` text on the six literal facts. The verdict must stay VERIFIED, because `verify.py:270` refuses anything else and the client would never trade. About 10 lines. The passport line waits for C-15, as its plan says.

**Order, files, size.** After C. `feed_keeper.py`, `stand_down.py`, `runtime.py`, `paper_lane.py`, `qmx_host/host.py`, `ctrader_account.py`. About 130 lines. Ours.

### Venues, later gate (p5b-1 to p5b-7)

| Row | What | Shared with cTrader, or waits |
| --- | --- | --- |
| p5b-3 | Close limit set from entry | Shared seam. Fixed by Cause B at the runtime's lines. Hyperliquid's real refusal still needs testnet |
| p5b-6 | Two units on one coin | Shared rule with p5a-20. Cause C |
| p5b-4, p5b-5 | Restart reads a hand trade as the node's, stop id reused | Only `ccxt_client.py`. Provable on the shipped fake. Wait with the wallet, about 20 lines |
| p5b-2 | No binding path, no key window | Truly waits. A slice nobody owns, about 300 lines. Cause A to C keep the `VenueAccount` seam, so nothing here blocks it |
| p5b-1, p5b-7 | Reads on This PC | Not the node. p5b-7 is one line and could go any time. p5b-1 waits |

### The fakes

**Conformance venue.** Harsher means one thing: answer as the real binding does when the session is down. Four lines. `harsh.py` did this in memory. Result: `test_app_stand_down.py` 1 red of 11, the `venue_not_ready` case at line 245, which is exactly the false green in p5a-21. `test_app_healing.py` 0 red of 16. With Cause B's sketches, `test_protection_every_order.py` and `test_app_status_truth.py` 0 red of 26. The red case should change to say the exit goes once the session is back. `test_app_runtime.py` and `test_app_kill_scopes.py` are under long runs.

**Fake cTrader.** About 80 lines added to its 470, all opt-in flags, so they turn nothing red by themselves:
- lose events while down (the scripts do this now by clearing `_out`)
- refuse the socket N times (`Flaky`, 5 lines)
- answer deal history and trendbars (about 40 lines)
- put the stop on a later event, not the fill (`StopLater`, 20 lines)
- answer a close by `ProtoOAErrorRes`, not an order error (5 lines)
- a symbol the account does not list (exists as `SYMBOLS`)

Its reconcile already reads what it truly holds, which is why venue-wins passed.

**What only his demo account settles (C-15).** C-15 is unbuilt: `qmn/probes/` holds only `hyperliquid_testnet`. Its plan marks are `label` survival, repeated `clientOrderId`, attribution, the network-cut and refresh drills. Also, from the code:
- Whether a fill carries the stop. H1 lowers this worry: with the stop on a later event, the node waits 2 s, sends one amend, and ends protected with no alarm. That still spends one amend per entry.
- What a close on a gone position answers. `_close` waits only for trade events (`ctrader_account.py:1291`), so a `ProtoOAErrorRes` costs 5 s and reads UNKNOWN.
- Whether events carry the request's `clientMsgId`, which `_close` and `_amend` depend on.
- Deal-history fields for a stop, trendbar retention and side, `traderId` against `ctid`, and the six literal facts.
- What `ProtoOAAccountDisconnectEvent` does to a session (N5).

### The old node shell and the SQS gate

**What the new node uses.** Level 4 census above agrees with `reports/deletion.md`. Only `qmn/observability/__init__.py` pulls in old code (`health`, `logging`, `metrics`), and C-20 rewrites it. C-20's list holds. deletion-4, -11, -12 stand.

**SQS, a correction.** SQS is the Spread Quality Sensor: baseline divided by live spread, with a hard block (`qmf-readings/labelers.py:3-4,331`). The audit named `qmn/host/runtime_risk_gate.py` as its home. That file is a proof harness: it cites a fixture slot at `:972-975` and has no production caller. The gate that blocked entries is `qmn/host/decision_root.py:496-510` ("hosted entry requires the same frontier's ready, non-blocked SQS reading"), reached only from `host/sealed_runtime.py`. The baseline comes from `qmn/host/sqs_baseline_producer.py` (641 lines).

**What the new node has instead.** Nothing for spread. `Runtime.guard` (`runtime.py:2269-2314`) checks kill, pause, withdrawal, board, session, reconcile, orphans and stand-downs, and "spread" does not appear in `runtime.py`. AD-39 and NODE.md section 6 name "spread against the unit's cost target" as a guard and AD-40 puts it inside the node, so this is an unbuilt line of the design as well as his ruling (RC:320).

**What must stay until the risk session places it.** `sqs_baseline_producer.py`, moved out of `qmn/host` by C-20 and not deleted (it imports `host._refuse` and `host.admission_artifacts`, so a small repoint). The rule text in `decision_root.py:496-510`, which can live in the handoff. `evaluate_sqs` and `qmf-risk` are outside C-20 and safe. `runtime_risk_gate.py` need not stay, which frees those 1,969 lines the deletion report held back. Hand this to the risk session, and build no gate now. The seat is one line in `guard`.

### Kill effects: what is plumbing

All of "RED does not close it" and all of "flatten does nothing" are plumbing, ours. The table of what each level means, which levels close, YELLOW to BLACK, is the risk session's and stays a placeholder. Whether a position no unit holds is within scope is not a value, it is the word "at the scope" in that same row, plus TR:39. The close, its retries, its journal row and the true `positions_closed` are ours. Flatten has no number at all.

## 4. Corrections to the audit

- **p5a-2** understated. The cause is broader than a missed comparison: see Cause A. Also, the `reconcile` row itself misreports.
- **known-1** partly overstated. `positions` shows the broker's truth (1.06916, G8). The false value is in the `Placed` answer, the handler and the journal row (1.06800). Understated elsewhere: a stop far past entry is refused as "widens" and lost with no row or alarm (G8). The distance is the risk session's, the silence is ours.
- **chief-1** overstated. `_measured` never reaches the passport: neither `operations.py` nor `server.py` reads it. Its effect is that the stop gate's "proof" of the stop form is a literal. The real protection is the read after the fill, and that holds. Keep it as `should`, about words.
- **plan-check-2 and deletion report** name the wrong file for SQS. See above.
- **p5a-19, seams-12** look like one request. They are not (Cause D).
- **p5a-1, seams-4** sized M and S. S is right if the symbol check comes with it.
- **My own guess, refuted:** a kill's repeated closes do not flood the journal, 25 ticks wrote 1 row (F4). The broker does see 5 requests a second per position.

## 5. What "works" means here

Each runs the real node over the real codec against the harsher fake, then the last on his demo.

1. Drop the socket, fire the stop, reconnect. The trade books at the broker's price, nothing is phantom, and the unit trades again. (TN-02, TN-15)
2. Restart with a position whose stop is gone. It is back, or closed with an alarm, before any entry. Restart with a position already closed. The trade row exists. (TN-02, TN-13)
3. RED with the deployment refused, and flatten with a unit trading. The broker ends flat, the rows say so, and a restart replays nothing. (TN-03)
4. Reboot with no network. The unit says it waits, then trades at the real balance. (TN-13)
5. Deploy a second market after bind with a position open. Bars arrive and the position holds. Deploy an unlisted symbol. It is refused by name and the account keeps trading.
6. Refuse the socket for an hour of clock. Sign-ins stay under a set count and the status reads the cause. Across a weekend, it reads closed and not stopped. (TN-06, TN-19, TN-20)
7. A 5-minute unit gets 5-minute bars or a refusal, and `parity.py` still reads 63 of 63.
8. On demo, `c14-real.log` and `c15-demo.log` read all PASS, including the cut and refresh drills. (TN-01, TN-05)

## 6. PR clusters, in order

1. **Broker wins.** Cause A, with the fake's lost events and deal history.
2. **Every way out acts.** Cause B, seams-3 before it or inside it, harsher conformance venue.
3. **What he deployed runs.** Cause C, N1, Cause D step 1.
4. **Connections and words.** Cause E.
5. **The bars he tested on.** Cause D steps 2 and 3, last because retention needs a demo look. It can follow C-15's first run.

Total about 680 product lines and 300 test and fake lines, close to the scope's guess. The 9 tests p5a-29 to p5a-34 name and p5a-23's 85 lines can go in the same PRs, subtracting first.

## 7. New defects

- **N1, must, level 4.** One deployment naming a symbol the broker does not list kills the whole account after a restart: session down, one sign-in per tick, and RED sends 0 closes with a position open (`truth2.py g1`). `_markets` includes refused deployments and markets he did not choose (`server.py:855-866`), and `_authorise` refuses all (`ctrader_account.py:800-805`). A broker naming gold `XAUUSD.pro` is enough. The refusal is marked no-retry and is retried anyway.
- **N2, should, level 4.** The `reconcile` row writes the node's memory under `venue_stop` (F1). Fixed by Cause A.
- **N3, should, level 4.** A stop he moves by hand in cTrader is never read (H2). Fixed by Cause A.
- **N4, should, level 4.** A stop fired while the process is down leaves an entry with no exit and no alarm (G3). Fixed by Cause A.
- **N5, should, level 2.** `_absorb` ignores `ProtoOAAccountDisconnectEvent`, `ProtoOATraderUpdatedEvent` and `ProtoOASymbolChangedEvent`, all in the pinned definitions. The balance is read only at connect (`:791`), and TN-25 has no reader. What the first does to a session is a guess until demo.

## 8. Set aside for him

- The node shows "not ours, protected" beside a position with no stop. I assumed "not ours, never touched", with "no stop at the broker" added when true.
- Flatten closes positions. I assumed it does not stop the unit, so a unit may enter again on its next signal, and RED is how he gets out and stays out.

## 9. Needs a long run

From `D:/QMX-worktrees/audit-head`, after sourcing `tools/env.sh` and `export PYTHONPATH="$PYTHONPATH;D:/Temp/audit/ground-node"`:

```bash
"$AUDIT_ROOT_ENV" -m pytest qmn/tests/test_app_kill_scopes.py -q -p reach -p harsh -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-node/l1
"$AUDIT_ROOT_ENV" -m pytest qmn/tests/test_app_runtime.py qmn/tests/test_app_unknown_drill.py -q -p reach -p harsh -p venuewins -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-node/l2
```

## 10. Not reached

- A kill across a node that is away, and server paths.
- `CcxtClient.read_back` was not checked for the Cause A fault. p5b walked its `_poll` and `read_back` for other faults, and I did not trace them for this one.
- Not run: the back-off, weekend, clock and paper-restart shapes, and Cause D steps 2 and 3. The flatten shape is run only through its shared close.
- p5a-17 (partial close dropped) sits at `runtime.py:1623` beside Cause B, but scope puts it in cluster 5, so I left it there.
- Twin and take-over paths were read and not exercised. No real broker was reached.
