# Grounding: the unit, QML and the dictionary

Code read at `50c83a4e` in `D:/QMX-worktrees/audit-head`. Nothing changed. Trials patch the real code in memory only. Scripts: `D:/Temp/audit/ground-unit/` (`p2.py` to `p6.py`, `plug/refuse_trial.py`). Levels are the audit's: 2 pointed at the line, 3 walked, 4 ran.

## 1. What this area is and how it really works
A unit is one JSON document. `qml.check` runs layers A to F on it, and `compile_unit` (`qml/compile/compiler.py`) turns it into a `Plan`. `construct_unit` or `restore_unit` (`qml/protocol/unit.py`) host that plan, and `on_instant` returns format-3 orders, decision rows and calibration rows. QMB and the node both drive it through one file, `qmb/host/unit_handler.py`, so there is one meaning of a fill. The dictionary is 112 stdlib blocks with code plus 104 wave and 239 ported pages, landed as Library drafts on first start.

The runtime was written around the dummy's exact shape: one slot rule (a Signal, or a price the block's input is beyond), one stop read at entry, one target, and one per-bar exit fed nothing. Everything outside that shape passes check and compile and then does nothing. The compiler already refuses `reads`, halts and extra streams, so the right pattern is there and was not applied to the rest.

Under it sits the older bot world: `construct_bot`, `HostedBot`, `accept_intents`, `qml.conformance`, `qmf.risk.door`, `qmb.host.adapter`, `book_handler` and `runner`. The unit path does not call the bot door, but it does import it (section "The old QML" below). Risk and sizing are labelled placeholders by design, and that is not a defect.

## 2. What must not break
- The dummy: 25 entries on the shipped month, close at bar 48 on both sides, its number moving from long trades. Guard: `qml/tests/test_compile_dummy.py` (12 passed here). Every trial below was compared against it.
- `qml/tests/test_check_layers.py` (364), which includes the corpus gate `tools/ci.py:59` runs.
- `qml/tests/test_socket_contracts.py`, `test_lifecycle.py`, `test_stdlib_blocks.py` and the golden files.
- `qmb/tests/test_unit_handler.py`: it already executes `close_partial` and `amend_protection`, so that half needs no new work.
- The Book door refusing format 3: `qmf/risk/door.py` unchanged, `qml/protocol/factory.py`, `intents.py`, `test_protocol.py`, `test_state.py`, `test_surface_old_law.py`.
- `restore_unit` starting cold with a reason, and first-start landing keyed by fingerprint (`qmx_host/first_start.py:689,765,803`).
- The Library's every-kind save (`qmx-library/tests/test_view.py`): save checks shape only.

## 3. Problems, grouped by cause
### A. Accepted and not run: p0a-1, p0a-3, p0a-2, p0a-5, p0a-6, p0a-7, p0a-8, p0a-9, p1a-5
**Real cause.** `_shape_problems` (`compiler.py:493`) refuses only three things. `_Wiring.side` (`:289`) builds a side whether or not `direction` trades it. `_warm_up` (`:449`, `:464`) calls `make` unguarded, and the slow rule is first made in `_Core.__init__` (`unit.py:279`). `unit.py:433` uses a bare `next()`, so no per-bar exit means a crash. All rerun and confirmed (`p0a/proof1.py`).  
**What is around it.** `check` calls `compile_unit` when layers pass (`check/run.py:68`) and turns refusals into `not_compiled` errors. So one change here reaches every door: `unit_check`, publish, QMB and deploy. Readers of `sessions` and `settings`: layer D and number checks only.  
**Three traps a plain "refuse at compile" falls into, each run:**
1. **Direction.** Dropping the unwanted side makes `new(dummy, {"/direction": "long"})` refuse with `motion_source` at `/numbers/rsi_high/motion/source`, because `_motion` (`:371`) wants every derived number bound. With the short side and `rsi_high` removed by hand it runs: 2 long, 0 short (`p2.py`, level 4). So `_motion` must also skip numbers bound only on a dropped side.
2. **Cadence `at`.** The dummy itself declares `"at": "market_day_close"`, as do three corpus twins and the `b-build-and-prove` fixture. Refusing it fails `test_compile_dummy` at once (2 failed, stopped at first failure, level 4). My call: warn when `at` is present beside `every_closed_trades`, refuse it only when it is the sole cadence. No document changes and no fingerprint moves.
3. **Sessions.** Refusing sessions fails one shipped test, `test_a_session_on_either_market_calendar_is_not_an_error` (`test_check_layers.py:240`), which asserts through `check`. Point it at `check_layers`. It tests layer D and stays true.  
**Safety fact.** No shipped unit document uses the other fields. With refusals for sessions, settings, position limit above 1, stream price other than `bid_ask`, unbuilt roles and the six unrunnable exits: `test_compile_dummy` 12 passed, `test_check_layers` 363 of 364 (the one above). Level 4 for those two files; whole QML under Needs a long run.  
**Repair shape.** One place, `compiler.py`.
- `_shape_problems` grows into the list of what format 1 runs.
- Sides follow `direction`.
- Compile makes every instance once inside one guard, including slow rules, and turns `ValueError` and `KeyError` into a problem with a pointer. That closes p0a-6 and p1a-5 together.
- More than one stop, target or per-bar exit refuses (p0a-5).
- No stop refuses (p0a-8), with the rule staying the risk session's.
- `next(..., None)` lets a unit have no time exit (p0a-2), since UT-18 calls that a warning.
- Roles that run are context, location, setup, trigger, confirmation, filter and entry_order; others refuse (p0a-7, my call).
- p0a-9 is a layer B check of `face.mirroring`. 102 of 112 blocks say `not_applicable`, so a side-neutral block under `mirror_of` will refuse; the hint says state both sides. QML-17's own line asks for this.  
**Fingerprint.** Refusals change no decision for a unit that still compiles. The direction change does, so bump `COMPILER_FORMAT_VERSION` to 2. Nothing pins it (`git grep`: compile package only). Nothing has landed on his machine. Level 2.  
**Proof.** `p0a/proof1.py` and `p1a/proof_units.py` give a refusal or a working trade on each section; they fail today. **Order:** first, needs nothing. **Files:** `compile/compiler.py`, `check/layers.py`, `protocol/unit.py:433`, `tests/test_check_layers.py`. **Size:** about 120 lines. **Whose:** ours. p0a-8's rule (may a unit have no stop) is the risk session's.

### B. Exits that never fire: p1a-2, p1b-1, p1b-2, p1b-3, p1b-4, p5a-17, known-1, triage-1
**Real cause.** The exit host is one timer. `_Core.timer` (`unit.py:433`) takes the first per-bar exit, `exits` feeds it `{}` (`:658`), and the only intent written is `close_full` labelled `time-exit` (`:663-676`). A stop is read once at entry with `update({})` (`:729`) and fed `{"series": ...}` each bar with no `entry_price` (`:558`). The trailing blocks treat that as "no position", forget their best price and answer nothing (level 3, block source read). The compiler sorts a level as stop or target by whether it reads `stop_price` (`compiler.py:329`), so a trail counts as a stop.  
**What is around it.** QMB already handles partial closes and tighten-only moves (`unit_handler.py:583-611`), and format 3 already parses both. On the node, `_exit` blocks partial closes (`runtime.py:1623`) and `_close` closes `held.volume` only (`ctrader_account.py:1263`). Nothing reads `protection.time_exit_bars` except the parser.  
**Safety fact, proved.** Feeding every per-bar exit real evidence (`series`, `entry_price`) and the position's side changes nothing for the dummy: close at bar 48 long and short, 25 entries the same. The cap then fires long and short (`p2.py`, level 4). This holds because `time-exit-bars` ignores its evidence.  
**A trap the audit did not name.** `timer()` makes the exit with no side, so it is always long. A short up 10% built that way reads `Signal(False, -0.1)`; built with its side it reads `Signal(True, 0.1)` (`p2.py`, level 4). A repair that only feeds evidence would give shorts exits that never fire. Also: `m.timers` holds one instance per position, so `load`, `shape_gap` and `STATE_SCHEMA_VERSION` move with it (restart then starts cold with a reason, which is safe). Keep the reason code `time-exit` for that block.  
**Three steps.**
1. **Refuse now** (in PR 1, needs nobody). Any exit with position or bar inputs, and any second exit of a use, gets `exit_not_built`. Removes the false belief about protection.
2. **Run every per-bar exit** with evidence and side. One file, about 60 lines. Agree the socket first.
3. **Trails, partial closes and stop moves.** A new exit use in the compiler, an answer type beyond `Signal` in `blocks/api.py`, and mapping to the existing intents. Then the node's partial close (p5a-17) and the signed stop.

p1b-2: replace the `_exit_breaks` evidence with one test through `compile_unit` and `on_instant`, in step 1.  
**What the risk session must decide (rules):**
- May a stop go past entry, and how is that sent? The signed distance is theirs by his ruling (R:28, TR:9). It decides whether trails on the node can lock in profit.
- Whether a stop may ever widen (placeholder 9).
- Scale-out ladders, and what a partial close means for R (10).
- Whether a target rests at the broker or the node closes it (seams-7).
- May a unit have no price stop (11, p0a-8).
- Whether a moved number changes an open trade's exits (8).
- Which exit wins when two fire on one bar.
- Which position facts exits read: `bars_held`, `mfe_r`, `mae_r` from `CONTRACTS.md` 4.3. None is computed today.  
**What is plumbing we can do first:**
- The refusals in step 1, including p0a-2 and p0a-5.
- The side and the evidence in step 2, once the socket is agreed.
- The false report: `amend` returns `Placed(new_stop)` (`runtime.py:1253`) whatever was sent.
- p1b-2's test. The partial close on the node, once a block can ask for one.  
**The stop sign (known-1, triage-1).** Cause: `abs(entry - new_stop)` at `runtime.py:1223`, then `_LEVEL_RULES` in `qmf/venue/encode.py` always applies the loss-side sign. Rerun: asked 1.1020, venue is sent 1.09800 (level 4). No shipped unit can reach this today, because nothing emits an amend. It is live the day step 3 lands, so step 3 must not ship on the node before the risk session answers. Plumbing now: when the new stop is past entry, `amend` answers `Blocked` with that reason instead of sending a level nobody asked for. C-37's tests were not read, so that may need a test change.  
**Proof.** A QMB run with cap and time exit both bound, long and short, closes at whichever comes first with the binding named; then the same on the fake cTrader. **Order:** step 1 in PR 1, steps 2 and 3 after agreeing with the risk session. **Files:** `protocol/unit.py`, `compile/compiler.py`, `blocks/api.py`, `qmn/app/runtime.py`, `qmn/venue/ctrader_account.py`, `tests/test_socket_contracts.py`. **Size:** step 2 about 60 lines, step 3 about 250. **Whose:** shared, as above.

### C. Blocks that cannot act: p1a-1, p1a-3, p1a-6 (p1a-4 is in E, p1a-5 in A, p1a-7 below)
This has four separate causes, not two.  
1. **Time (15 blocks).** Blocks read `bar.get("time")`, the bar's close in UTC. `QuoteBar.knowable_at` already holds it, and `resolve` (`unit.py:574`) drops it. One line. No new data.
2. **Volume (7 blocks, VWAP in both lists, 21 in all).** `OHLC` has no volume. QMB's bar builder has a volume field that never reaches `QuoteBar` (`runloop/bars.py:266`, `:1434`), and the node builds bars from quotes with no count (`ctrader_account.py:1061`, `feed_keeper.py:235`). Dukascopy's number and a cTrader tick count are different things, so feeding both silently breaks "same code in research and live" (QML-09). This half needs p0a-14 first. Until then compile refuses these blocks.
3. **Price levels fed whole bars (14 blocks), which the audit did not count.** `condition` (`unit.py:615`) looks for a Decimal input to compare. A block fed `m15` gets a table, so the slot is absent. Alligator, Heikin Ashi, Ichimoku, FrAMA, price channel and the session levels all give 0 entries today. Comparing the bar's close brings six to life (1,154 to 1,595 entries) with the dummy unchanged (`p4.py`, level 4). The other eight need time or volume.
4. **Values with no comparison (p1a-3).** REPAIR-SCOPE says one new comparator block. **That is not enough.** I wrote one and bound it as the door allows (`p3.py`, level 4):
   - ADX plus comparator in one slot under `all`: check passes, 0 entries.
   - The same under `any`: 25 entries, and 0 at level 99, so it does gate. No agent would guess this.

   The feeder counts as an absent condition. With a value that only feeds a later binding no longer counted, `all` gives 25 and 0, and the dummy stays identical, because its EMA is a price and stays a condition (`p6.py`, level 4).  
**Safety fact.** Bars gaining fields and slots gaining these two rules change nothing for the dummy: entries identical in each trial above. `QuoteBar` takes the new field with a default, so the four constructors and `layer_g.py:267` stay valid (level 2).  
**Trap, order.** Feeding time turns on p1a-6: ten session blocks start acting on a fixed UTC second, an hour wrong most of the year. Silence becomes a wrong trade. So time lands with new block versions taking a market zone, or those ten refuse at compile until then. My call: refuse first. Also, compile refuses a binding that can neither hold nor feed, which removes the remaining false comfort.  
**Repair shape.** Mark feeders in `SlotPlan` at compile, so the runtime decides nothing new. Add `time` in `resolve`, bars-fed compare in `condition`, and one comparator entry with golden cases. **Proof:** `p1a/proof_units.py a`, `proof_conditions.py`, and the new sweep in section 5. **Order:** after PR 1. Volume after p0a-14. **Files:** `compile/compiler.py`, `protocol/unit.py`, one new stdlib folder. **Size:** about 100 lines; volume about 150 across QMB and the node. **Whose:** ours. No sizing or exit rule.  
**p1a-7.** The halt's silence at zero equity is one line in a new block version. Compile refuses all halts today, so it cannot bite. Hand to the risk session with the halts.

### D. The number that tunes itself: p0a-4, p0a-13
**Cause.** `_edge` clamps negative strengths into bucket 0 (`trend-floor-from-record/1/block.py`), and a short's stamp is negative. Rerun: a long journal moves 0 to 0.0001, its mirror in shorts stays at 0 (level 4). `statistic` holds only a count (`unit.py:837`).  
**Around it.** The block is pinned by value in `b-build-and-prove/fixtures/recorded/build.json` and `qmx_judge/conformance_pack/fixture.json`. Fix it as a new block version: the contract's `block_fix` row, and the lock moves the compiled fingerprint by itself. A fix in the motion engine would change decisions with no fingerprint change. **Safety fact:** the layer G test pins 8 trades, below the 20 needed for a move, so its counts hold (level 3). **Shape:** take the size of the strength, add a mirrored journal test. `calibrate` adds the mean R and mean stamp to the row; `results/journal.py:334` already carries it. **Size:** under 30 lines plus regenerated fixtures. **Whose:** ours. The design calls this a logic number, not an exit or size. REPAIR-SCOPE places neither row; put them with PR 2.

### E. The dictionary's own checks: p1a-4, p1b-11, p1b-12, p1b-13, p1b-14, p1b-15
- **Settle (p1a-4, p1b-12).** QML-03 lives only in `test_stdlib_blocks.py:130`, and only 2 of 112 entries record a length (`ema`, `rsi-cross-back`). A length holds for one parameter set. Shape: record length per period in `entry.json`, which is outside the block fingerprint, so no pin moves; compile scales it. Add the check to `check_entry`. Warm-ups grow for new units. The dummy's should not, since its slow blocks are recorded and its derived window is longer; unproven, and `test_compile_dummy` will show it. Size M. This bump also moves the format.
- **p1b-11.** `entry.py:815-818` returns no problem with no golden. Limit the repair to agent and human origins: QML's own are covered by tests, and 17 stdlib entries would otherwise drop status. Size S.
- **p1b-15.** `entry_check` sees one entry; `corpus_problems` already does the job. Close over the store as `unit_problems(store)` does (`host.py:853`). **Safety fact, level 4:** across all 455 pages first start lands (112, 104, 239), `corpus_problems` finds 0 clashes, so the check cannot refuse the landing (`p6.py`). Unproven: cost per save over 455 rows. Look names up rather than scan.
- **p1b-14.** `write_entry_statuses` exists and rerunning writes the same (`functions.py:845`). Nothing calls it in a running host. Call it after landing, after publish and per entry after a put, using the post-put hook at `host.py:770`. Size S.
- **p1b-13.** `index.py` matches when a name's words are all in the sentence, and 229 names are one word. A false "known" loses an idea silently; a false "new" makes an append request someone reviews. So one-word names stop matching alone, and `test_entry.py:151-154` tests full size. Size S. Used by `blocks_match` and `u3-dictionary-expansion`.

### F. Small true things: p0a-11, p0a-12, p0a-14
- **p0a-11.** `_price` rounds to digits (`unit.py:207`). Rounding to the record's tick leaves every dummy stop identical on real ticks (EURUSD 0.00001, XAUUSD 0.01; `p3.py`, level 4). Size S, PR 2. Plumbing, not a rule.
- **p0a-12.** The literal receipt is real but nothing reads `sizer_receipt` (grep: writer and parser only). Row 12 is the risk session's. Do it with their sizer, by adding the residue to `Size`.
- **p0a-14.** `parse_entry` drops fallback, transfer and splits, so layer D compares numbers only. Includes one false refusal of a declared fallback. Extend `Port` and compare. Size M. Must land before volume.

### G. Written but unwired: p1b-5, p1b-6, p1b-7, p1b-8
- **p1b-6, p1b-7.** Publish and compile re-check live, so no bad unit gets through. The script reads a folder nothing writes. My call: cut `tools/qml/recheck_units.py` and its three tests. Then p1b-6 has no reader; keep `checker_version` and bump the format by hand. Reverse if AD-119's card is ever wanted.
- **p1b-5.** `classify` and `diff` are correct and tested, with no caller. Every test run is already a counted try, so harm today is small. My call: no repair until the Lab or judge needs it. See Set aside, because the table sits on his Settings screen.
- **p1b-8.** Wire `seam_check` with cluster 1's history warm-up in `qmn/app/runtime.py`, since that is where a seam first occurs in normal use. A restart gap in the node's own recording is the only case today. Size S.

### H. plan-check-5: `lifecycle.auto_paper`
Confirmed. `machine.py:111`, `:177`, `:186`, `host.py:863`, `qmx_control/service.py:427`. It is a lead's call (LC-A1-18) against "every move toward paper or live is his click" (US:46, US:200). **Safety fact:** it ships off and nothing writes it on; judge moves are draft to tested or parked only (`record_judge_moves` in `qmx_host/host.py`, level 2). **Shape:** delete the row, the parameter, the setting and `test_lifecycle.py:123,157`. About 30 lines removed. **Whose:** his rule, our delete.

## The two old packages: qmf-indicators and qmf-structure
**Who imports them.** Only `qmb/_backends.py:16,19`, for a version number shown on screen. But `qmb/__init__.py` imports that file, so importing the unit path or `qmn.app.runtime` loads them **and native TA-Lib** (`p5.py`, level 4). QML itself loads neither.  
**Did the blocks replace them?** Mostly yes for indicators, no for structure. Against TA-Lib on one seeded walk, last 300 values (`p3.py`, level 4):

| Old wrapper | Block | Worst gap |
| --- | --- | --- |
| SMA | `moving-average-simple` | 2e-15 |
| EMA | `ema` | 5e-12 |
| WMA | `moving-average-linear-weighted` | 5e-12 |
| RSI | `rsi-series` | 5e-11 |
| ROC | `roc-of-series` | 5e-15, as a fraction where the wrapper gives percent |
| MOM | none | `momentum-ratio` is a different formula |

The blocks do not wrap the old code, though `2-unit-template` section 6 says they do. They are separate step-by-step code, which also fixes QML-04's recompute-all-history problem. The port of the 239 ported prose, not this code.  
**What is lost if they go:**
- Plain momentum, a few lines if ever wanted.
- The swing-point family, whose rule differs from the swing stop's pivot: "confirmed when a later bar closes beyond the pivot bar's opposite extreme", against a fixed two-bars-late pivot.
- Structure objects with knowledge time, lifecycle fold, emission invariant and research lane. No block or caller uses them, but no dictionary block offers this, and 56 location and structure pages have no code.
- The `ta-lib==0.7.1` pin as a declared dependency. Goldens are safe: tests read committed files, and `tools/dictionary/golden_talib.py` names its own pin.  
**What is gained:** the node and QMB stop needing a native library at install, which is real on a server.  
**To remove them:** `_backends.py`, `qmb/doors/api`, three pyprojects, root `pyproject.toml` (14 lines), `tools/workspace_meta.py`, `release/install.py`, `tools/release_gate.py`, app locks, `qa/tests/epic_07`, `epic_09`, and `test_workspace_structure`, `test_app_env_fresh`, `test_runtime_wheel_closure`, `test_qmb_surface`.  
**Call:** safe to go, on his word, as its own PR. Structure's ideas should be written down as a dictionary note first.

## The old QML under the unit
| Piece | Still runs for | Must a unit repair leave it alone? |
| --- | --- | --- |
| `qml/protocol/factory.py`, `intents.py`, `contract.py` (`construct_bot`, `HostedBot`, `accept_intents`) | No product path calls them. Old `qmb.host.adapter`, `qmn.seats.host`, `qml.conformance.harness`. **Imported by the unit path** through `qmb/host/__init__.py` | Yes. A break stops every QMB job at import (`p5.py`, level 4) |
| `qml.conformance.layer2`, `scan` | **Live.** Layer G calls `evaluate_layer2`; layers and `checker_version` use the scan | Yes, unchanged by design |
| `qmf/risk/door.py` | **Live.** `unit_intent.py:43` imports from it; old node order paths use it | Yes. Format 3 stays outside it |
| `qmb.host.adapter`, `runner`, `book_handler` | Old QMB door and tests; imported at load. Jobs use `unit_runner` | Yes for now. Later cut needs his word |
| `qmb/runloop`, `host/replay.py` | **Live.** `unit_runner` and the node's handler | Yes |
| `qmn.host`, `qmn.seats` | Only `python -m qmn.host.supervise`, the old shell C-20 cuts. `qmn.app` imports neither, and neither loaded in `p5.py` | Yes, C-20 owns it |
| `qml/host/` (graduation, seed_cite) | Tests only; no product import (grep) | Leave. Part of the later cut |
| `qml_run` tool row (`catalog.py:338`, `functions.py:373`) | Listed, but nothing fills `ctx.bots`, so it always answers "Unknown bot_ref" | See New defects |
| `UnitFactory`, `CompiledUnit.factory` | BR-A4's fail-closed proof; tests only | Keep. It proves the wrong door refuses |

## Seams an order-flow track will touch (noted, not planned)
`compiler.py:496` refuses `reads`. `compiler.py:494` allows one stream. `unit.py:119` `QuoteBar` is bars of bid and ask, and `resolve` at `:574` passes only those. `_required_keys` at `:843` and `_core` at `:877` refuse any surface beyond bars, position, journal and account. `readings_used` is always empty (`:162`). `layers.py:533` accepts tick input by level, but nothing runs it. QMB's `unit_handler` steps on closed bars and has no trades or book replay. Group C's volume field touches `OHLC`, `QuoteBar` and `resolve`, so design that field knowing these come later.

## 4. Corrections to the audit
- **p1a-3 understated.** 64 blocks is about 78: 14 price series fed whole bars also never hold.
- **REPAIR-SCOPE "one new comparator block" is wrong.** It gives 0 entries under `all`.
- **REPAIR-SCOPE "about 60 lines, refuse at compile" misses three things:** refusing cadence `at` kills the dummy, dropping a side refuses the dummy unless `_motion` changes, and one shipped test pins sessions.
- **p1a-1 is two repairs of different size.** Time is one line, volume is a data question. Fixing time alone switches on p1a-6.
- **p1b-1 and p1a-2 fix shape** misses the side bug in `timer()`.
- **known-1, triage-1:** the bug is real, but no shipped path reaches it today. It is a gate on step 3, not a first repair. The false report is the same.
- **p5a-17 overstated for today.** No unit can ask for a partial close until p1b-4 lands.
- **p0a-12 overstated.** Nothing reads the receipt. True, `leave` until the risk session's sizer.
- **`reports/deletion.md:13`** "ran with neither loaded" holds only in its overlay. Plainly importing QMB's unit path loads both, and TA-Lib. Its conclusion stands.
- **p0a-4 and p0a-13** are placed in no REPAIR-SCOPE cluster; neither are p0a-12, p0a-14, p1b-5 to p1b-8. Placed here.
- **Confirmed as written, rerun:** p0a-1, -2, -3, -5, -6, -7, -8, -9, p1b-1 shape, known-1.

## 5. What "works" means here
Each is a real run across a real connection, using the hard cases in `funnel/edge-cases/catalogue.md`.  
1. **Nothing silent (UT-01, QML-08).** Sweep every stdlib block as a trigger and as an exit through the real door and a month's drive. Each one either acts or refuses with a pointer. Never "check pass, zero signal, no reason". Fails today.
2. **A trader's plain rule.** An agent writes "ADX above 25" through `unit_new` and `unit_check`, and a QMB job runs it. Trades appear, and level 99 gives none. Fails today.
3. **What he reads is what it trades (UT-15).** A long-only unit through a QMB job: zero short fills, one position per market.
4. **Exits on both sides (UT-18, UT-16).** Cap and time exit bound, long and short, through QMB and then the fake cTrader: whichever comes first closes, the row names it, and the two worlds agree.
5. **Restart mid-position (UT-09, UT-10).** Two exits held, snapshot through `restore_unit`, continue: no double fire, no lost timer, or a cold start with its reason.
6. **Honest tuning (UT-05).** A QMB run with short trades moves the number as its long mirror does, and the journal row shows why.
7. **Backtest and node agree (QML-03, QML-09).** Same days through QMB and the node's handler give the same decisions, and a volume block on a mismatched feed refuses by name.
8. **The dictionary at full size.** Fresh store, first start, one publish: 455 pages, none with status None; a clashing save refused; "The trend is your friend" comes back unmatched.

## 6. PR clusters, in order
1. **What it cannot run, it refuses.** Group A, step 1 of B, p1b-2, refusal of volume and session blocks. Needs nothing. About 120 lines. Removes every false comfort at once.
2. **Slots tell the truth.** Group C parts 1, 3 and 4, group D, p0a-11. Format bump. About 130 lines. Lands `time` only with session blocks still refused.
3. **The dictionary's checks.** Group E, group H, cut of p1b-6 and p1b-7. About 200 lines, about 150 removed.
4. **Session blocks follow the market's clock.** p1a-6, new versions of ten blocks. Medium.
5. **Exits really run.** Steps 2 and 3 of B with known-1, triage-1, p5a-17. After agreeing the socket with the risk session. About 300 lines.
6. **Volume.** p0a-14, then part 2 of C. Touches QMB and the node, so it shares files with REPAIR-SCOPE clusters 2 and 4.
7. **Remove the two old packages.** On his word.

p1b-8 goes with cluster 1's warm-up. p0a-12 and p1a-7 go to the risk session.

## 7. New defects
- **N1.** 14 price series fed whole bars never hold a slot, and check stays green. `unit.py:615`. `p4.py`, today all 0, level 4. `must` with p1a-3, same harm.
- **N2.** `_Core.timer` builds exits on the long side only. `unit.py:433`. `p2.py`, level 4. Harmless today, because only the time exit runs. `should`, repair with step 2.
- **N3.** The copilot's `qml_run` row can never succeed: no code fills `ctx.bots` (grep, level 2). What goes wrong: an agent that tries it gets a dead end. `leave` unless C-20's cut takes it. Check `test_tools.py` first.

## 8. Set aside for him
- May I delete `qmf-indicators` and `qmf-structure` (about 14,000 lines)? Lost: unused swing and structure code and plain momentum. Gained: no native TA-Lib on the node. I assumed they stay until he says.
- His Settings screen shows an identity table that decides nothing today (p1b-5). I assumed it stays, unwired, until the Lab or judge calls it.

## 9. Needs a long run
Trial refusals over all of QML, which shows every shipped pin the first PR moves:
```bash
source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && GROUND_TRIAL=sessions,settings,limit,price,roles,exits PYTHONPATH="D:/Temp/audit/ground-unit/plug;$PYTHONPATH" timeout 1200 "$AUDIT_ROOT_ENV" -m pytest qml/tests -q -p refuse_trial -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-unit/long1/t
```
The same over the QMB unit path:
```bash
source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && GROUND_TRIAL=sessions,settings,limit,price,roles,exits PYTHONPATH="D:/Temp/audit/ground-unit/plug;$PYTHONPATH" timeout 900 "$AUDIT_ROOT_ENV" -m pytest qmb/tests/test_unit_handler.py qmb/tests/test_run_journal.py -q -p refuse_trial -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-unit/long2/t
```
C-37's amend tests, to see what `Blocked` past entry moves:
```bash
source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && timeout 600 "$AUDIT_ROOT_ENV" -m pytest qmn/tests -q -k amend -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-unit/long3/t
```

## 10. Not reached
- No trial crossed QMB's job or the fake cTrader. Every trial here is the real compiler and hosted unit, with a test helper's surfaces.
- C-37's tests, `test_block_tools.py`, the host and engine tests that pin the dummy under the trial refusals.
- p1a-6's new block shape: whether the agent scan allows a zone import. The clock blocks compute daylight saving without one.
- The settle-per-period idea is not tried, so the claim about the dummy's warm-up is unproven.
- `plain_python`, `context_needs`, `routes`: not traced.

Principles that changed a decision: `blast-radius` made me run each repair as a trial, which found every trap in A and C. `subtract-before-you-add` set the cuts of `auto_paper` and the recheck script. `prove-it-works` is why REPAIR-SCOPE's comparator was built and driven rather than accepted.
