# For the repair program: what the risk session decided that you were waiting on

From the risk-and-sizing session, 6 Nov 2026, corrected after its independent check the same day. Source: `architecture/SPINE.md` on branch `plan/risk-core` (sections 4.3 to 4.6, 4.8 and 9), checked in `architecture/CHECK.md`. Everything here is decided in that spine; nothing here is a value. Where a value is named it is the shape the number takes, and the numbers lens owns it.

Names are what bind. Lines are at R23 `697aafc6` for `runtime.py`, `ctrader_account.py` and `feed_keeper.py`, at R18 `337b2cc5` for `qmx_control`, and at J `a4f64510` for `qml`, `qmb` and `encode.py`. `runtime.py` is still moving, so find the name first.

## Asked of the repair

Two things. Both are small, and neither touches a rule.

1. **R24, one more demo question.** Add to the demo run's questions, printing what it found: **does an amend of a position with only `takeProfit` set keep the venue's `stopLoss`, and does an amend with only `stopLoss` set keep `takeProfit`?** Today's encoder writes one field (`encode.py:1029-1036`). cTrader's page lists both as optional and says nothing about an omitted one; one forum reply treats leaving it out as a way to remove it, unconfirmed. If so, an amend could wipe the disaster stop. The risk session sends no amend with a resting target until this is answered. Today the node rests no target, so nothing live is exposed.
2. **R10 and anything touching `r_after_costs`: do not rename it to `net_r`.** An earlier version of this note said to. That was wrong (section 2).

Everything else below is a shape to build against, or a line for your list.

## 1. The exit socket ("agree the socket with it first")

Your guesses 1, 3 and 8 (`A/reports/ground-unit.md:45-50,98`) are accepted, and guess 2 with one change: the socket runs several per-bar exits on one bar, so `exit_not_built` for a second per-bar exit lifts at step 2. One stop per unit stays.

- **Step 2** feeds every per-bar exit a `PositionFacts` object: the `OwnPosition` as today plus `stop_held`, `stop_at_entry`, `targets`, `bars_held`, `mae_r`, `mfe_r`, `realized_r`, `side_price` (bid for a long, ask for a short) and the exit numbers stamped at entry. `HostedUnit.exits` builds it with no guard call. R10's MAE and MFE (`unit_handler.py:97-99, 249-250`) move into it. `timer()` passes the side. A pure `safest_exit` picks the winner: closes beat amends, safety beats strategy. The answer type widens beyond `Signal` to `CloseAnswer(mechanism, fraction=1)` and `AmendAnswer(new_stop)`; at step 2 only `CloseAnswer(fraction=1)` and `Signal` map to an intent, `close_full`. The compiler lifts `exit_not_built` for a per-bar exit reading position facts or whole bars; `stop_not_built` stays (no unit without a price stop at go-live). Format bumps once for this.
- **The disaster stop** is the unit's `ExitUse.STOP`, venue-resident on every live entry; `require_venue_resident_protective_stop` stays. One R is measured to it. Its distance is a number with a derivation in the profile's `exit_numbers`.
- **Step 3** (trails, partial closes, stop moves, about 250 lines) waits for the signed stop (section 3) and for R24's facts on what the venue holds. It lifts `AmendAnswer` and `fraction < 1` to `amend_protection` and `close_partial`, and restores a lost stop from the latest accepted amend row rather than the send row. A partial that leaves a rest under `min_lot` closes in full (`ClosePartial` in `_exit` stays). Trails are shadow catalogue entries until then.

## 2. The trade row and `net_r`

- One R is the planned loss at the disaster stop at entry. `r = money / risk` is the gross result the judge's `trade_r` reads. `net_r = (money + cash) / risk`, the form `qmx-agents/apps/qmb/jobs/backtest.py` already computes. Money is at fill prices, which already hold spread and slippage; cash is commission and swap. Brakes, the money ledger, the CUSUM and the admission gate read `net_r`, against the holdout's `net_r`. The judge and the logic record read gross. Our call; his B9 reservation stands.
- **`r_after_costs` holds gross.** `unit_handler.py:724` sets it to `held.realized_r + trade.r`, and `qml/motion/engine.py:57,120` reads it. It keeps its value. The risk session's slice 1 renames it `gross_r` and adds `net_r` as a new field. It is never `net_r`: a brake reading a gross value under that name, or a value with spread and slippage taken off a second time, sends a healthy unit to paper.
- The trade row (`qmb/src/qmb/results/journal.py:412`, kind in `journal_kinds/unit.py`) gains `exit_mechanism`, `r`, `net_r`, `costs_r` split into spread, commission, slippage and swap (display only, never subtracted again), `mae_r`, `mfe_r`, `bars_held`, `profile_version`, `level_at_entry`, `labels`, `session`, `equity_before`, `stage`, `world`. `exit_mechanism` is a closed code: `stop`, `fi_cut`, `thesis_fi`, `backstop`, `breakeven`, `time`, `signal`, `target`, `target_backstop`, `trail`, `forced_flat`, `kill_close`, `risk_close`, `liquidation`, `roll`, `hand`, `unknown`.
- The guard's money ledgers read R20's deals, not trade rows, so the record holes (`S/BACKLOG.md:64,66`) cannot hide a loss from a brake. Until R24 proves deal money those deals give price and kind only: the ledger derives money from price, converts it to USD and labels it.

## 3. The signed stop

A stop is an absolute price at every internal seam: units, intents, journals, status and the guard carry the level. Only the venue encoder derives a distance, signed by side (`_LEVEL_RULES`, `packages/qmf-venue/src/qmf/venue/encode.py:115-120`). Stops only tighten. `seats/dispatch.py:917-930` goes with C-20. R21's `Blocked` for a stop past entry (`_past_entry`, `runtime.py:1356`) and `abs(entry - new_stop)` (`_move_stop`, `:1398`) lift together at step 3, when `_move_stop` takes an absolute level and the encoder signs it. Stops past entry are therefore **out of scope for the first demo** and in scope for step 3, momentum families first.

## 4. Targets

Targets rest at the venue. QMB books a target at its level (`qmb/execution/fill.py:1328`); the node today closes at market a bar later (`protective`, `runtime.py:1838`), and one wicked bar read +2.00R against -0.55R (seams-7). "Backtest and live run the same rules" decides it. The entry will carry a target distance beside `protective_stop_distance`. `relativeTakeProfit` is in the proto, not yet in the encoder, so that is new work.

**There is no amend after the fill until R24 answers the question at the top.** Once a target can rest, every amend sends both levels and reads `stop_of` back, step 3's stop amend included. Until the entry carries a target, the node's market close stays as it is, labelled `target_backstop`. R24 must also prove the venue's close kind for a take-profit fill. This is one PR after R24; it does not change QMB's fill.

## 5. Kill level meanings

Replaces `PLACEHOLDER_KILL_EFFECTS` (`qmn/src/qmn/protection/effect_matrix.py:137-143`). YELLOW: no new entries at scope. ORANGE: no new entries, resting cancelled, amends tighten only. RED: close this node's positions at scope (`_close_scope`), no entries. BLACK: close everything and pause; resume only by his hand. While the node sends market entries only, YELLOW and ORANGE act alike; both are shown. Brakes never set a kill level: they raise stand-downs (`Kind.RISK_RULE`, self-clearing on the guard's word; `Kind.RISK_STOP` for a lockout that waits for his resume). Whether the portfolio day stop may raise YELLOW itself is his question Q5; the default is a stand-down and a one-tap card. `Runtime.risk_stop` (`runtime.py:2690`) gets its first producer, the lockout.

## 6. Where SQS sits

Inside the guard package (`packages/qmf-risk/src/qmf/risk/guard/spread.py`), as a gate in the rank table, entries only, exits never checked. Not a line in `Runtime.guard`. The rule text of `decision_root.py:493-510` is unchanged and is already saved in `grounding/G12-audit-and-repair-for-risk.md` section 2. The baseline producer moves from `qmn/host/sqs_baseline_producer.py` to the guard, fed by `feed_keeper.py` quotes and R19's minute rows; the eight named settings in `registry_catalog.py:158-241` become ledger rows with derivations from the spread histogram's percentiles. DEC-0230 stands: a demo-conditioned baseline never satisfies a live environment, so the first live entry waits hours for a live-account baseline. DEC-0153 stands: a bar-sampled reading never satisfies a live decision; QMB's bar spread serves the harness only. The claims are in `FOR-REPAIR-CLAIMS-BEFORE-C20.md`.

## 7. The guard and the hook

`CrossUnitHook`, `PASS_EVERY_ORDER` (`qml/blocks/api.py:196-218`) and the node's static `cross_unit_hook` (`runtime.py:1096, 1144`) go. The one call site is `UnitSliceHandler.mint_intents` (`qmb/host/unit_handler.py:484`), which both hosts run; the guard answers `before_order(UnitEntryIntent, open_positions, facts)` with pass, shrink or refuse and a closed reason code. `Runtime.guard` (`runtime.py:2619`) stays as the node's health check.

**The wrapper rule: a guard failure can never stop exits.** Every guard call and every status write goes through one wrapper in the risk session's port. Any raise or refusal becomes `guard_unavailable` on entries; exits mint; the unit stays TRADING; `_step` and `mint_intents` still return `Ok`. It has to, because a refusal from `loop.close_frontier()` sets `Phase.STOPPED` (`_drive_one`, `runtime.py:3032-3037`), `_drive` then skips the unit, and protective reads and per-bar exits end. A test runs a guard that raises on every call and the per-bar exit still closes. **Please keep that path as it is, or tell the risk session if it changes.** The wrapper is the risk session's to build; nothing here is asked of you.

**What the guard needs that the node does not have today:**

- a timed re-read of the balance (`ctrader_account.py:706` reads it once at sign-in; R22 adds the wait, the guard adds the timer);
- the SQS reading, from `feed_keeper.py` quotes and R19's minute rows;
- margin used and free, computed by the kernel from open lots and the record's margin rule;
- the conversion market's quote: `feed_keeper.py` and `host.py` `_bars` load only the markets asked for, so USDJPY and EURJPY money has no USD rate unless both ports load the record's new `conversion_market`;
- deal money, once R24 proves the fields.

**A line for your list, your call.** `_write_snapshot` (`runtime.py:2911`, called at `:3043`) has no guard around `os.replace`. On this Windows machine `os.replace` raised `PermissionError` while a reader held the target (`architecture/check/out-windows-replace.txt`). A raise there goes to the heal path. The risk status file is inside the wrapper, and tools read rows, not the file; the unit snapshot is yours.

## Which repair PRs this touches

| PR | How |
|---|---|
| R10 | `r_after_costs` stays as it is, value and name; the risk session renames it `gross_r` after you land. MAE and MFE move into `PositionFacts` |
| R15 | every guard answer and brake text needs a code in `REASON_CODES`; `Skip` gains a code so no brake files as `kill_switch` |
| R17 | the profile and group documents travel beside the unit through `_admit` and `_deployment`; the bound click's capability check sits there |
| R18 | the risk session adds `risk-profile` and `risk-group` beside `unit` in `library_save` and `_his_click` (`service.py:1519,1673-1679`) after you land; this is its slice 3, not your triage-3 |
| R20 | ledgers read its deals, price and kind until R24 proves their money; a close while down becomes a trade fact |
| R21 | `Blocked` and the `abs()` lift at step 3; `_close_scope` is RED's verb; the lost stop restores from the latest amend row at step 3 |
| R22 | the risk status file sits beside the unit snapshot under `data/deployments/<id>/`, written whole then replaced the same way; the balance wait is the guard's first fact |
| R23 | the clock and market-hours stand-downs are facts the guard reads; the path that stops a refused unit stays as it is |
| R24 | must answer: does a fill carry the stop; deal fields; a close on a gone position; the venue's close kind for a take-profit; **what an amend with one level does to the other** |
| C-20 and deletion-4 | the claimed files move first |

## Not asked of the repair

Nothing else here changes a repair PR before it lands. The risk session's slices start on landed tips and rebase. Risk and sizing rules stay with the risk session.
