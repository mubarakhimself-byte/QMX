# For the repair program: what the risk session decided that you were waiting on

From the risk-and-sizing session, 6 Nov 2026. Source: `architecture/SPINE.md` on branch `plan/risk-core` (sections 4.3 to 4.6 and 9). Everything here is decided in that spine; nothing here is a value. Where a value is named it is the shape the number takes, and the numbers lens owns it.

## 1. The exit socket ("agree the socket with it first")

Your guesses 1, 2, 3 and 8 (`A/reports/ground-unit.md:45-50,98`) are accepted.

- **Step 2** feeds every per-bar exit a `PositionFacts` object: the `OwnPosition` as today plus `stop_held`, `stop_at_entry`, `targets`, `bars_held`, `mae_r`, `mfe_r`, `realized_r`, `side_price` (bid for a long, ask for a short) and the exit numbers stamped at entry. R10's MAE and MFE (`unit_handler.py:97-99, 249-250`) move into it. `timer()` passes the side. Several per-bar exits may run on one bar; a pure `safest_exit` picks the winner: closes beat amends, safety beats strategy. The answer type widens beyond `Signal` to `CloseAnswer(mechanism, fraction=1)` and `AmendAnswer(new_stop)`; at step 2 only `CloseAnswer(fraction=1)` and `Signal` map to an intent, `close_full`. The compiler lifts `exit_not_built` for a per-bar exit reading position facts or whole bars; one stop per unit stays; `stop_not_built` stays (no unit without a price stop at go-live). Format bumps once for this.
- **The disaster stop** is the unit's `ExitUse.STOP`, venue-resident on every live entry; `require_venue_resident_protective_stop` stays. R is measured to it. Its distance is a number with a derivation in the profile's `exit_numbers`.
- **Step 3** (trails, partial closes, stop moves, about 250 lines) waits for the signed stop (section 3 below) and for R24's fact on what the venue holds. It lifts `AmendAnswer` and `fraction < 1` to `amend_protection` and `close_partial`, and restores a lost stop from the latest accepted amend row rather than the send row. A partial that leaves a rest under `min_lot` closes in full (`runtime.py:1722-1723` stays). Trails are shadow catalogue entries until then.

## 2. The trade row and `net_r`

- `r` is gross: the planned loss at the disaster stop at entry, the judge's `trade_r`. `net_r = r − costs_r`. The code field `r_after_costs` (`unit_handler.py:724`, which holds gross today) is renamed `net_r`. Brakes, the money ledger, the CUSUM and the admission gate read `net_r`; the judge and the logic record read gross. Our call; his B9 reservation stands.
- The trade row (`qmb/src/qmb/results/journal.py:412`, kind in `journal_kinds/unit.py`) gains `exit_mechanism`, `r`, `net_r`, `costs_r` split into spread, commission, slippage and swap, `mae_r`, `mfe_r`, `bars_held`, `profile_version`, `level_at_entry`, `labels`, `session`, `equity_before`, `stage`, `world`. `exit_mechanism` is a closed code: `stop`, `fi_cut`, `thesis_fi`, `backstop`, `breakeven`, `time`, `signal`, `target`, `target_backstop`, `trail`, `forced_flat`, `kill_close`, `risk_close`, `liquidation`, `roll`, `hand`, `unknown`.
- The guard's money ledgers read broker deals (R20), not trade rows, so the record holes (`S/BACKLOG.md:64,66`) cannot hide a loss from a brake.

## 3. The signed stop

A stop is an absolute price at every internal seam: units, intents, journals, status and the guard carry the level. Only the venue encoder derives a distance, signed by side (`_LEVEL_RULES`, `packages/qmf-venue/src/qmf/venue/encode.py:115-120`). Stops only tighten. `seats/dispatch.py:917-930` goes with C-20. R21's `Blocked` for a stop past entry (`runtime.py:1279`) and `abs(entry − new_stop)` (`:1320`) lift together at step 3, when `_move_stop` takes an absolute level and the encoder signs it. Stops past entry are therefore **out of scope for the first demo** and in scope for step 3, momentum families first.

## 4. Targets

Targets rest at the venue. QMB books a target at its level (`qmb/execution/fill.py:1327`); the node today closes at market a bar later (`runtime.py:1757-1772`), and one wicked bar read +2.00R against −0.55R (seams-7). "Backtest and live run the same rules" decides it. The entry carries a target distance beside `protective_stop_distance` (the encoder writes `relativeTakeProfit` beside `relativeStopLoss`); until that lands, one amend with `ProtectionSide.TARGET` right after the fill (`encode.py:1029` already writes `takeProfit`). The node's market close stays only as a labelled backstop (`target_backstop`) a bar after the level is passed with no venue fill. R24 must prove the venue's close kind for a take-profit fill. This is one PR after R24; it does not change QMB's fill.

## 5. Kill level meanings

Replaces `PLACEHOLDER_KILL_EFFECTS` (`qmn/src/qmn/protection/effect_matrix.py:137-143`). YELLOW: no new entries at scope. ORANGE: no new entries, resting cancelled, amends tighten only. RED: close this node's positions at scope (`_close_scope`), no entries. BLACK: close everything and pause; resume only by his hand. While the node sends market entries only, YELLOW and ORANGE act alike; both are shown. Brakes never set a kill level: they raise stand-downs (`Kind.RISK_RULE`, self-clearing on the guard's word; `Kind.RISK_STOP` for a lockout that waits for his resume). Whether the portfolio day stop may raise YELLOW itself is his question Q5; the default is a stand-down and a one-tap card. `Runtime.risk_stop` (`runtime.py:2602`) gets its first producer.

## 6. Where SQS sits

Inside the guard package (`packages/qmf-risk/src/qmf/risk/guard/spread.py`), as a gate in the rank table, entries only, exits never checked. Not a line in `Runtime.guard`. The rule text of `decision_root.py:493-510` is unchanged and is already saved in `grounding/G12-audit-and-repair-for-risk.md` section 2. The baseline producer moves from `qmn/host/sqs_baseline_producer.py` to the guard, fed by `feed_keeper.py` quotes and R19's minute rows; the eight named settings in `registry_catalog.py:158-241` become ledger rows with derivations from the spread histogram's percentiles. DEC-0230 stands: a demo-conditioned baseline never satisfies a live environment, so the first live entry waits hours for a live-account baseline. The claims in `FOR-REPAIR-CLAIMS-BEFORE-C20.md` stand, plus `qmf-risk/control_rank.py`, `control_action.py`, `qmf-risk/sizing`, `qmf-risk/versioning`, `qmn/protection/effect_matrix.py` and `qmf-data/calendar_feed.py`.

## 7. The guard and the hook

`CrossUnitHook`, `PASS_EVERY_ORDER` (`qml/blocks/api.py:196-218`) and the node's static `cross_unit_hook` (`runtime.py:1018, 1066-1069`) go. The one call site is `UnitSliceHandler.mint_intents` (`qmb/host/unit_handler.py:484`), which both hosts run; the guard answers `before_order(UnitEntryIntent, open_positions, facts)` with pass, shrink or refuse and a closed reason code. `Runtime.guard` (`runtime.py:2531`) stays as the node's health check. The guard needs one fact the node does not have today: a timed re-read of the balance (`ctrader_account.py:698` reads it once at sign-in; R22 adds the wait, the guard adds the timer).

## Which repair PRs this touches

| PR | How |
|---|---|
| R10 | `r_after_costs` renamed `net_r`; MAE and MFE move into `PositionFacts` |
| R15 | every guard answer and brake text needs a code in `REASON_CODES`; `Skip` gains a code so no brake files as `kill_switch` |
| R17 | the profile and group documents travel beside the unit through `_admit` and `_deployment`; the bound click's capability check sits there |
| R20 | ledgers read its deals; a close while down becomes a trade fact |
| R21 | `Blocked` and the `abs()` lift at step 3; `_close_scope` is RED's verb; the lost stop restores from the latest amend row at step 3 |
| R22 | the risk status file sits beside the unit snapshot under `data/deployments/<id>/`, written whole then replaced the same way; the balance wait is the guard's first fact |
| R23 | the clock and market-hours stand-downs are facts the guard reads |
| R24 | must answer: does a fill carry the stop; deal fields; a close on a gone position; the venue's close kind for a take-profit |
| C-20 and deletion-4 | the claimed files above move first |

## Not asked of the repair

Nothing here changes a repair PR before it lands. The risk session's slices start on landed tips and rebase. Risk and sizing rules stay with the risk session.
