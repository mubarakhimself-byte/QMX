# Swap chart: what replaces the unit's placeholders, from the plans and the code

Read 7 Nov 2026. Code tip: `D:\QMX-worktrees\bld-repair-24`, branch `build/repair-24`, `255f3bbf` (Sat Nov 7 16:08:17 2026 +0300), clean worktree. 118 PRs stacked, 0 merged.

**Path short names.** Code paths are relative to the tip. `P` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing`. `S` = `D:\QMX-worktrees\repair-ship`. "Plan" = `P\build\UNIT-PLAN.md`, cited by PR id, which is the section heading. "PH n" = row n of `P\build\RISK-SIZING-PLACEHOLDERS.md`. "CONTRACTS" = `P\architecture\parts\A-qml-dictionary-unit\CONTRACTS.md`. "L0" = `P\architecture\level-0\ARCHITECTURE-SPINE.md`. "App F" = `P\build\repair\plan-parts\90-appendices.md`, Appendix F. "Call n" = its Appendix D.

**How this was checked.** I read the code and ran one in-memory probe through QML's real `compile_unit` and `construct_unit`, with fake blocks. Probe ids (S1, T2, M6...) point at section 2.6. The probe wrote nothing to the repo. It did not run in QMB or on the node, and no test suite was run. UNKNOWN means I did not verify it. The whole-repo run at this tip has no summary: `S\evidence\whole\fix-tip\SUMMARY.txt` holds only two sync lines, so its result is UNKNOWN.

**The verdict words.**

- **SWAP**: a replacement goes in by changing only the block or the setting.
- **WIDEN**: the socket must change first. The cell says which input, refusal or call.
- **WIRE**: the piece exists, or is declared, but no host calls it.
- **KEEP**: stays as it is.

A row can hold two verdicts, because a socket often takes a narrow replacement today and refuses a wider one.

**The short answer for "they just swap it out".** It holds for one narrow shape: a sizer reading equity, entry, stop and instrument record; a stop computed from bars and read once at entry; a target computed once at entry; a per-bar exit that reads nothing. Halts, the hook, trails, partials, moving risk numbers and account facts are WIDEN or WIRE. Repair lifted none of these. It turned silent gaps into named refusals, which is honest and is also the list of what must change.

---

## Section 1. The placeholder table

### 1a. The 31 rows

| # | Placeholder | What the plan promised | What the tip does | Verdict, and exactly what | Proof by test |
|---|---|---|---|---|---|
| 1 | Sizer `fixed-fraction-at-stop@1` | A2, A4. L0 AD-24. CONTRACTS 4.3: entry, stop, instrument facts, account `{equity, balance, open_risk}`, own record in R, market statistics from bound blocks, his limits. Answer: quantity and receipt with residue, or skip | Called at entry only, `qml/src/qml/protocol/unit.py:785-793`, with `equity`, `entry_price`, `stop_price`, `record` and its own params. No side. No bars: the sizer has no per-bar update. `Account` is equity alone, `unit.py:140-142`. Receipt is literal, `unit.py:827-830` | **SWAP** for a sizer reading only those four things (S1, S1b). **WIDEN** for anything else: lift `/sizer/inputs` refusal `compile/compiler.py:930-936`; add evidence at `unit.py:785-793`; grow `Account`; add residue to `Size` `blocks/api.py:104-109`; write the receipt from the sizer's answer at `unit.py:827-830`. To size on ATR a sizer needs a fed input, or bars, which it does not get | `test_the_dummys_sizer_answers_the_lot_rule_at_half_a_percent`; `test_a_risk_session_sizer_that_is_not_a_placeholder_meets_the_sizer_contract` is a fake on the contract only (`qml/tests/test_socket_contracts.py:411,446`). No repo test runs a swapped sizer through a host. Probe S1b ran it in QML only |
| 2 | Stop `swing-stop-buffer@1` | A2, A4. CONTRACTS 4.3 exit block: reads the position and market evidence | Fed `{"series": bid bar}` plus params each bar, `unit.py:570-576`; read with `update({})` at entry, `unit.py:756-760`. Then fixed: nothing moves it. Bid bars on both sides | **SWAP** for a bars-only stop read once at entry (T1). **WIDEN** for a stop reading the position: refused `compiler.py:358-363` (T2). A stop fed another binding: refused `compiler.py:482-487`. So an ATR stop must compute ATR inside itself. Moving it is row 9 | Compile and drive through the dummy in `qml/tests/test_compile_dummy.py`. T1 is compile only |
| 3 | Target `target-r-multiple@1` | A2, A4. PH: targets, time-varying targets, profit caps, give-back | One target, read once at entry from entry and stop, `unit.py:773-781`, always `fraction: "1/1"`. Handler keeps `targets[0]` only, `qmb/src/qmb/host/unit_handler.py:574`. A level reading a port named `stop_price` is a target by shape, `compiler.py:340-347` | **SWAP** for one fixed level at entry. **WIDEN** for a second target (`compiler.py:492-495`, T4), a fraction, or any time-varying target or cap (needs row 9's amend path) | Same dummy tests. A replacement target has no test of its own |
| 4 | Time exit `time-exit-bars@1` | A2, A4. A13d adds time-varying exits | `timer()` builds it long-side only with default numbers, `unit.py:444-452`. `update({})`, `unit.py:686`. The host writes "time exit after N bars" and reason `time-exit` whatever the block is, `unit.py:690,701`. `protection.time_exit_bars` reads a param named `bars`, `unit.py:799-803` | **SWAP** only for a no-input exit, and it still files as a time exit (P1). **WIDEN** for every other: pass `side` at `unit.py:450`, real evidence at `:686`, the block's own reason at `:690,701`; lift `compiler.py:358-363` | `test_the_per_bar_exit_closes_at_bar_48_through_the_host_and_a_capped_exit_refuses` (`test_socket_contracts.py:464`) |
| 5 | Halts at position, unit, account | A2 (slot), A13d (blocks), A15 (contract). CONTRACTS 4.3 | Any halt refuses, `compiler.py:902-903` (H1). In a logic slot it refuses too, `binding_not_read` (H2). `HaltInstance` has no caller, `blocks/api.py:182-186`: "No host runs halts yet". The checker still says "add a halt", `check/layers.py:684-690`. Five blocks ship: `account-daily-loss-halt`, `equity-drawdown-halt`, `losing-days-halt`, `session-fill-limit-halt`, `session-loss-limit-halt` | **WIRE and WIDEN.** Lift `halts_not_built`. Build `plan.halts` in `compiler.py`. Add a host loop in `unit.py` or the handler. Compute `session_loss_r`, `loss_streak`, `losing_day_streak`, `session_fills`, `equity`, `day_start_equity`; none is computed today. Route the answer to `Runtime.risk_stop` on the node; QMB has no equivalent | `test_a_halt_answers_none_or_a_halt_with_its_reason`, `test_a_halt_matches_its_reference`: block level only. Nothing proves a halt in a host |
| 6 | Cross-unit hook | B5b, C-12a. L0 AD-24: "the host that drives the unit (the node live, QMB in replay)" calls it. CONTRACTS 4.3 | Node: static stub taking a `Command`, answering a string or None, `qmn/src/qmn/app/runtime.py:1100,1147-1151`. QMB: no call anywhere (git grep). `CrossUnitHook.before_order` and `PASS_EVERY_ORDER`, `blocks/api.py:196-218`, have no production caller | **WIDEN** on the node: the call site passes no intent, no open positions across units, no dispersion. **WIRE** in QMB, and on the node to the `blocks/api.py` shape. Reason code `cross_unit_hook` already exists | `test_the_cross_unit_hook_placeholder_passes_and_a_bad_hook_breaks_the_contract` tests the unused API object, not either host |
| 7 | Motion of risk numbers | A3, A5. L0 AD-22 | Refused for sizer, stop, target and per-bar numbers (M1 to M5). `_bound_on` looks only in logic slots, `compiler.py:510-516`, used at `:599`. Calibrated needs a slot binding that stamps it, `:620-643`. See 2.5 | **WIDEN.** Let `_motion` take exit and sizer bindings as hosts, or say which slot output feeds them. Block authors must read moved values from `evidence`, because `make` gets starting values only. A per-bar exit never gets moved values at all, `unit.py:450-452,686` | Probe only. `min_trend_strength` and `rsi_low` motion is proven in `test_compile_dummy.py`, for logic numbers |
| 8 | Moved values and open positions | A3. CONTRACTS 2.1: "the risk session may change the default" | `applies_to_open_positions: true` refuses, `compiler.py:996-1000` (M7). Calibrated moves only flat, `unit.py:541-543`, `motion/engine.py:139-141` | **WIDEN.** Lift the refusal; add a path from a moved number to an amend intent (row 9). Flipping the default changes nothing today | `test_each_part_format_2_does_not_run_refuses_with_a_pointer` (`qml/tests/test_unit_refuses.py:401`, part at `:193`) |
| 9 | Stop amendments | A1. CONTRACTS 4.4: tighten, never widen | Law: `check_amendment_tightens`, `packages/qmf-risk/src/qmf/risk/unit_intent.py:725-757`. Handler moves it, `unit_handler.py:636-649`. Node sends it, `runtime.py:1818-1840`, and answers `Blocked` past entry, `:1360-1369`. **No unit can ask:** `unit.py` mints only `close_full`, `:691-704`; `ExitInstance` answers a level or a `Signal`, `blocks/api.py:160-165` | **WIRE and WIDEN.** Add an answer type to `blocks/api.py`, map it to `amend_protection` in `unit.py`. Sign the distance: `abs(entry - new_stop)` still at `runtime.py:1402-1403`. Widening is a law in code, not a setting | `test_an_amendment_that_widens_the_stop_by_one_tick_is_refused`; `test_a_tightened_stop_is_held_and_fills_without_closing_at_the_amendment`; `test_a_stop_amendment_that_widens_is_refused_and_one_that_tightens_moves_the_venue_stop`; `test_amend_answers_the_brokers_stop_and_a_past_entry_stop_is_blocked...`. All hand-made intents; none from a block |
| 10 | Partial closes | A1. "Available to exit blocks" | QMB fills them, `unit_handler.py:621-635`. **Node refuses:** "the venue cannot close part of a position", `runtime.py:1807-1808`. No block can ask, as row 9 | **WIRE** (unit host), **WIDEN** (node close with a quantity). Backtest and node differ today | `test_a_partial_close_closes_its_lot_rounded_quantity_and_the_rest_stays_held`, QMB only |
| 11 | A unit with no price stop | A1, B15. `protection.stop = none_declared`, `r_missing` | Refused, `compiler.py:500-506` (T7, Call 1). Wire format holds it, `unit_intent.py:69-72,131`. The host skips with no stop, `unit.py:764-766`. Handler and node read the stop as `Decimal`, `unit_handler.py:560`, `runtime.py:1065`, which `none_declared` would not parse (my reading, not run). `r_missing` is real, `qmx_host/records.py:619,639` | **WIDEN** in four places: compile, `enter`, handler, node entry. The node's protection gate is on every order, `runtime.py:1102-1106`. Needs a sizer that takes no stop | `test_unit_intent.py:80` round-trips the wire only |
| 12 | Lot rounding, minimum lot | B5b, B10, C-12a | `qml/numbers/convert.py:88` rounds down and refuses below min and above max. Applied again by handler `unit_handler.py:550-556` and node `runtime.py:1745`. `Fill.residue_r` is real, `unit_handler.py:556`, but a sizer already on the step leaves 0. Receipt residue is literal `"0/1"`, `unit.py:829` | **WIDEN.** A block cannot change the rule, since the hosts re-round. Changing it means `convert.py` or a host call. Residue: as row 1 | `test_0_037_lots_trades_0_03_with_the_residue_journaled_and_0_004_skips`; `test_a_receipt_of_0_037_lots_fills_0_03_and_journals_the_0_007_residue_in_r` |
| 13 | Gap through the stop | B10, C-12a | QMB `qmb/execution/fill.py:1303`. Flag set `unit_handler.py:699`, journalled `qmb/results/journal.py` `_trade`. Node takes the venue's close and its gap, `runtime.py:1846-1848` | Mechanism **KEEP**. "How the sizer treats gap risk" is **WIDEN**, row 1: no gap fact reaches a sizer | `test_a_weekend_gap_through_the_stop_fills_at_the_gap_and_records_minus_1_7_r` |
| 14 | Margin and liquidation | B10, C-12a: "a stop past the liquidation price is refused at entry" | QMB: `MarginRule`, `qmb/execution/risk.py:56-80`, used `fill.py:1313`. **Entry refusal not found:** no `liquidat` in `qmn/src/qmn/app`, `unit.py` or the order path's `_entry` (`runtime.py:1043-1145`). Record holds `leverage`, `margin` as opaque maps, `qml/numbers/records.py:62-63` | **WIRE** the entry fact check. **WIDEN** for margin per session or a margin-aware sizer: no margin input reaches it | `test_a_perp_past_its_maintenance_margin_is_liquidated_at_the_records_level`, QMB only |
| 15 | Leverage and spec changes | C-02, C-12c | Node reads leverage into the record row, `qmn/app/server.py:897-912`. Table row exists, `stand_down.py:93,177-178`. **Nothing raises it:** `self.stand_down(` is called only with `REPEATED_FAULT`, `runtime.py:2127,2222` | **WIRE.** A record change must call `Runtime.stand_down(Kind.SPEC_CHANGE, ...)`. UNKNOWN: whether any test drives this row; none is named for it in `test_app_stand_down.py` | None found |
| 16 | Funding and swaps | B10 | QMB `CarrySchedule`, `qmb/execution/financing.py:1153,1367`; moves QMB equity, `unit_handler.py:372`. Node passes no cash port, by design, `unit_handler.py:19-21` | Mechanism **KEEP**. "Whether funding changes size" is **WIDEN**, row 1 and `reads` (E1) | Plan's Wednesday and perp cases, `qmb/tests/test_realism.py`. Exact names not read |
| 17 | Account facts | C-12a, C-16. PH: "cTrader balance plus unrealised P&L" | cTrader `equity()` returns `balance`, `qmn/venue/ctrader_account.py:706-707`. Read once at start, `runtime.py:1614,2843`. Then start plus closed trades, `unit_handler.py:370-372`. Node has no cash port, so swap and commission never move it. CCXT answers 0 on failure, `ccxt_client.py:597-601`. No `balance`, `open_risk`, budget | **WIDEN.** Add a live account surface on the node; add fields to `Account`; a budget share needs both. Marked equity does not exist | No test asserts marked equity. UNKNOWN beyond grep |
| 18 | Kill effects per level | C-12a. LC-C-28 | Table `qmn/protection/effect_matrix.py:137-146`. Read for closes only, `runtime.py:2511,2555-2559`. **Entries ignore it:** YELLOW and up block by rank, hard-coded, `runtime.py:2628`; BLACK's pause by level, `:2502`. `cancel_resting_entries` unread, `:2519-2520` writes 0 | **SWAP** (a code table, no setting) for close flags only. **WIDEN** for `stop_entries` and `cancel_resting_entries`: `guard` must read the table. Triggers: no automatic escalation found | `test_each_kill_level_applies_its_placeholder_effect_and_only_his_resume_lifts_it`; `test_red_closes_a_position_no_unit_holds` |
| 19 | Protection that cannot be placed | C-12a | `PROTECT_RETRY_MAX`, `PROTECT_CONFIRM_NS`, `CLOSE_REFUSALS_ALARM`, `runtime.py:179-187`, code constants though their docstrings name `[node]` settings. Always close and alarm, `_escalate` `:1223-1237` | **WIDEN.** Close, hedge or alarm-only is a branch that does not exist. The numbers are a code edit | `test_a_stop_the_venue_does_not_hold_after_three_tries_is_closed_and_alarmed`; `test_an_unprotected_position_whose_close_is_refused...` |
| 20 | Kill line's verb | C-20, L0 AD-36 | **Not on the path.** Git grep: `qmn.capital` has no importer in `qmn/app`, the apps or the packages; only the old shell. PH's behaviour "a breach stops new entries" is not built. It needs marked virtual equity, which the new node lacks. `kill_line.py:38` imports old paper demotion | **WIRE**, plus row 17. C-20's plan line says the new node "never calls the kill line" | Old-shell tests only. Not read |
| 21 | Two units on one netting symbol | C-23 preflight. L0 risk table | At host time on the node, live lane only, `runtime.py:2888-2906`, called `:2801`. Not a deploy preflight. From R22 | **WIDEN** to allow shared protection: a hard-coded refusal, no setting | `test_a_second_unit_on_a_netting_symbol_is_refused` (`test_app_deployed_runs.py:434`) |
| 22 | Numbers a live deployment starts from | C-23 | `starting()` `qmx_host/promote.py:255-272`. Node takes only calibrated, `runtime.py:1995-2007`, and a fresh `SlowState` restarts statistics, `unit.py:286-288` | **SWAP** for calibrated numbers already. A sizing number cannot be calibrated (row 7), so this waits on **WIDEN** there | `test_paper_to_live_onto_a_demo_account_carries_the_last_calibrated_values` |
| 23 | The one automatic move | A9, C-12c | `Runtime.risk_stop`, `runtime.py:2696-2720`, `stand_down.py:559-580`: real. **No production caller** (git grep). Halts do not run, row 5. Table has `risk`, `lifecycle/machine.py:110-112` | **WIRE.** Needs a producer. `flatten` has no path from a halt. Flatten by his op closes without stopping, `runtime.py:2561-2584` | `test_a_risk_stop_lands_one_lifecycle_event_and_waits_for_his_resume`; `test_a_risk_stop_survives_a_restart...`. These call `risk_stop` directly |
| 24 | Paper after a risk stop | A9, C-12c | `Transition(STOPPED, PAPER, click)`, `machine.py:113` | **SWAP** by a table edit in QML, not a setting. Nothing reaches it until row 23 | `test_every_move_by_every_actor_is_allowed_or_refused_as_the_table_says` |
| 25 | Risk events in journals | B8: `risk_event` labelled placeholder | Kind declared, `packages/qmf-data/.../journal_kinds/unit.py:180`. **No writer.** Reason codes `risk_stop`, `halt_slot`, `spread_wide`, `margin` exist unused, `:43-74`. A risk stop's text says "as the kill switch would", `stand_down.py:194-195`, and the table files it as `kill_switch`, `qmb/results/journal.py:57` | **WIRE.** New brake text needs a code, or a live row reads `unlisted` and a QMB run fails (R15) | Census test per R15, not read |
| 26 | Judging with unit sizer and fixed size | B13: "both always shown" | Judge reads one R, `trade_r`, `qmx_judge/judge.py:251`. No fixed-size run found in `qmx_judge`, `qmb/host` or `apps/qmb` (git grep). B13's own Build and Verify lines do not name it | **WIRE**: not built as far as I can see. UNKNOWN outside those folders | None found |
| 27 | Correlated exposure in judging | B13 | Correlated runs join one cluster of tries, `qmx_judge/tries.py:112-150`. This counts tries, not positions | **KEEP** for tries. The cross-unit control is row 6 | `test_the_verdict_counts_51_variants_of_one_family_as_...` (`test_judge_verdicts.py:237`) |
| 28 | Decay alarm | B20 | Script read, Watch and Alarm, tighten-only cards, `templates/dc-decay-and-limit-report/`. Settings are card settings | **SWAP** for its numbers. **WIRE** for any action: nothing joins it to `risk_stop` | `test_the_decay_check_alarms_on_a_fading_record_and_proposes_only_to_tighten` (`test_templates.py:1854`) |
| 29 | Fields to replay any sizing | B8, B9, B15. L0: equity before, session, streak, tuned values, would-have rows | Journal trade body has none of them, `qmb/results/journal.py` `_trade` (read at lines 428-448). `records.py:658` copies `equity_before` if present, and nothing writes it. `would_have` kind declared, no writer, `journal_kinds/unit.py:181`. Decision rows do carry `numbers_in_force`, `unit.py:720` | **WIRE.** Handler must know equity at entry and carry it to `UnitTrade`, `unit_handler.py:131-155`; writer adds it; stopped units need a would-have writer | None for these fields |
| 30 | Size the venue receives | B5b, B6, C-12a | `runtime.py:1745-1757`, receipt `:1117`, handler `:550-556` | **KEEP** | `test_every_entry_reaches_the_venue_with_its_stop_after_its_journal_row`; plan's lanes. Exact equality test name not read |
| 31 | Pods | None. L0: designed, unbuilt | Shell kind, `qmx_library/kinds/pod.schema.json`: `slots` is a bare object. `qmx_control/lab.py` docstring: "Pods are not part of this backend" | **Not built.** No compile path | None |

### 1b. Sockets and limits the code has that the list misses

| # | What | Where | Verdict |
|---|---|---|---|
| E1 | `reads` refused, so no reading reaches a unit. L0 AD-24 and AD-40 assume it does | `compiler.py:900-901` (O1). `unit.py:875-880` refuses extra surfaces, so `reading:` and `weights:` surfaces from CONTRACTS 4.5 are refused at construct | **WIDEN** |
| E2 | Eleven roles do not run, including `sizing_modifier`, `veto`, `cooldown`, `timeout`, `invalidation`, `arming`, `re_entry`, `regime_detector` | `compiler.py:107-117,438-443` (O2), `unit/model.py:89-109` | **WIDEN** per role |
| E3 | Exits at unit or account scope refuse | `compiler.py:472-477` (T6) | **WIDEN**. Also PH question 2 |
| E4 | One position per market | `compiler.py:958-961` (O3), `unit.py:746-747`, `unit_handler.py:547-549` | **WIDEN** |
| E5 | Per-market settings refuse, so no per-market risk number | `compiler.py:944-957` (O4) | **WIDEN** |
| E6 | `sessions`, `context_needs`, `routes`, `plain_python`, `roll` refuse | `compiler.py:904-929,938-943` | **WIDEN** |
| E7 | Spread, SQS and news: `guard` has no such check, though L0 AD-39 lists spread and windows | `runtime.py:2623-2675`. Call 19: "SQS has no gate built now". No `spread` in `runtime.py` | **WIRE** |
| E8 | The sizer slot has no type check and no ceiling: a trigger-typed block compiles there (S3), and 5000 lots passes the QML host (S1c). `lots()` refuses only past the record's `max_lot` | `compiler.py:1049` binds with no face check. `unit.py:794-797` checks only `Size` | **WIDEN** if a ceiling is wanted. "His limits" in CONTRACTS 4.3 do not exist |
| E9 | The sizer contract test holds a fixed bound: `_CEILING = 0.005`. A shipped sizer that risks more on those trades fails CI | `test_socket_contracts.py:57,126-134` | **WIDEN** the test before a real sizer lands |
| E10 | Exit contract test feeds evidence the host refuses to give: series, entry and stop together | `test_socket_contracts.py:233-237`. So six exits pass the slot test and refuse at compile | Test proves less than it reads |
| E11 | Library-only blocks are not enrolled in the contract test, which globs the stdlib | `test_socket_contracts.py:96-110` | **WIDEN** |
| E12 | Motion rule gets only `{strength, r}` per trade, and the stamp is a slot output | `engine.py:142-147`, `unit_handler.py:223-231` | **SWAP** for a new rule on those inputs, **WIDEN** beyond |
| E13 | `r_after_costs` holds R with no costs | `unit_handler.py:724`, `:669-673`; the judge's one-line flip is `judge.py:251`, a separate read | Decision, App F |
| E14 | Market entries only | `unit.py:761`, `runtime.py:1056-1057` | **WIDEN** |
| E15 | `OwnPosition` lacks stop, targets, bars held, MFE, MAE. Handler has MAE and MFE, for results only | `unit.py:128-137`, `unit_handler.py:97-100,238-251` | **WIDEN**: feed `HeldPosition` facts through `own_position` |
| E16 | Identity table is unwired, so a block swap is not classified "new unit" by any code | No `classify(` in `qmx-host`, `qmx-judge`, `qmx-tools` (git grep). App B leaves `p1b-5` out on purpose. CONTRACTS section 7 says otherwise | **WIRE** |
| E17 | Too-thin count, a judge value | `qmx_judge/presets.py:45` (`min_trades=100`) | Value |
| E18 | Motion defaults are constants | `engine.py:39-44`. No `min_trades`, `shrink_k` or `seam_jump_scale` in `qmx-control` (git grep), against CONTRACTS section 9 "all editable" | **WIDEN** |

---

## Section 2. How a swap works today, step by step

### 2.1 Write the block

- A block is `block.py` exporting `BLOCK` with `make(params, inputs, side)`, and an `entry.json` face (`blocks/api.py:1-27,142-148`, `parse_entry` `:375-416`).
- The face decides the use, by shape, never by name (`compiler.py:340-364`):
  - `output.type: exit_action`: per-bar.
  - `level` with `measure: price` and a port named `stop_price`: target.
  - Any other price level: stop.
- `component_type` must be `exit`, or nothing reads the level (`:356-357`). A sizer's face is not checked at all (S3).
- The instance rules a new block must obey, which the plan does not state:
  - A stop must answer its current level on `update({})` (`unit.py:757`).
  - A sizer gets one update per entry signal, never one per bar.
  - A moved number arrives in `evidence` under the param's name (`unit.py:575,778,792`). `make` gets starting values only, and the placeholders read `make`'s, for example `fixed-fraction-at-stop/1/block.py:24`. So a placeholder copied as a template would ignore motion (M6: `made=30`, `evidence=52.97`).
  - The sizer has no side; `make` gets the default long (`unit.py:331-333`). It infers direction from entry and stop.
- Layer F scans the source for unsafe code (`check/layers.py:785-816`).

### 2.2 Register it

Two real doors, one gap:

- **Stdlib folder.** `qml/src/qml/blocks/stdlib/<id>/<v>/`. `gather` reads it first (`qmx_tools/gather.py:78-84,185`). Auto-enrolled in the contract test. The family's golden test wants a golden case per block (`qml/tests/test_wave1_exits.py:143`). Dictionary page beside it in `qml/catalogue-seed/wave-1/exits-and-halts/`. QML is a library in the trading node's lock, so this bumps the money app's version and needs his signature (Call 11).
- **Library `component` with an entry and a `code` blob.** `gather._library` reads it (`gather.py:87-96`). The put check is `entry_problems` (`qmx_host/host.py:888`).
- **The gap: no catalog row saves a block.** `library_save` maps unknown kinds to `artifact` (`qmx_control/library.py:36,184`) and refuses units (`service.py:1520-1525`). The catalog has `unit_*` and `blocks_*` rows (`catalog.py:408-470`), and `blocks_check` only checks. The `u3` template's README says: "He saves a draft he wants from the run's ref". So an agent can draft and check a block and cannot land it. `tools/tests/test_placeholders.py:98` proves the rip-out query drops a Library sizer, on a store the test writes directly.

### 2.3 Bind, check, compile

1. Change the binding in the document and add the pin with its fingerprint. `unit_new` pins only blocks the template names (`gather.py:216-225`), and `door.new` sets fields by JSON pointer and does not refresh pins (`qml/door.py:55-72`). The skill says "Keep every block you use in `pins`".
2. `unit_check` runs layers A to F (`qmx_tools/unit_check.py:46-52`). Per R04, every door reaches the compiler, so refusals show there. Plain-language rule: check green means it compiles.
3. `compile_unit` (`compiler.py:1017-1104`) returns all problems at once. The fingerprint covers the document, the lock and the format version (`:1072-1079`).
4. **What widening costs.** `COMPILER_FORMAT_VERSION` is 4 (`:100`). A bump moves every unit's compiled fingerprint, and the node refuses a compiled fingerprint its G record did not test (`runtime.py:559-565,2756`). So every deployed unit needs a new G record after a socket change. A census test fails on any new schema field until someone decides run, refuse or label (`test_every_field_of_the_schema_is_in_the_census`, `test_unit_refuses.py:457`).

### 2.4 The refusals in the way, and what repair did

| Refusal | Line | Blocks | Repair |
|---|---|---|---|
| `exit_not_built` by shape | `compiler.py:350-364,491` | Six shipped exits: `unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop`, `profit-fraction-trailing-stop` | R04 added. Silent before |
| `exit_not_built`, second of a use | `:492-495` | Ladders, two per-bar exits | R04 added |
| `exit_not_built`, scope | `:472-477` | Unit and account exits | R04 added |
| `inputs_not_built` on an exit | `:482-487` | Feeding an exit a binding | R04 added |
| `stop_not_built` | `:500-506` | Unit with no stop | R04 added, Call 1 |
| `halts_not_built` | `:902-903` | All halts | R04 kept, with new reason |
| `inputs_not_built` on the sizer | `:930-936` | All sizer inputs | R04 added |
| `reads_not_built` | `:900-901` | Readings | R04 |
| `open_positions_not_built` | `:996-1000` | Row 8 | R04 added |
| `motion_not_built`, `motion_source` | `:592-613,632-643,1002-1007` | Row 7 | R04 tightened |
| `role_not_built` | `:438-443` | `sizing_modifier` and others | R04 added |
| `limit_not_built`, `settings_not_built`, others | `:904-961` | E3 to E6 | R04 added |

**What repair lifted for risk:** nothing on sizing, exits or halts. Real gains beside them:

- R04: a unit with no time exit no longer crashes (`unit.py:447-449`).
- R05: 78 of 112 blocks could not hold a slot, and the rule is now by shape, with `value-above@1`, feeders (`compiler.py:712-745`) and whole-bar checks (`:666-685`). `trend-floor-from-record@2` reads shorts properly. Prices round to the record's tick (`unit.py:206-209`).
- R06: session blocks at `@2` get the market's clock (`unit.py:591`); `BLOCKS_NOT_BUILT` keeps the `@1`s out (`compiler.py:120-138`). A save checks names across the store.

### 2.5 How the numbers move

**Kinds** (`unit/model.py:163-166`, L0 AD-22):

| Kind | Modes that run | Modes that refuse | How |
|---|---|---|---|
| `fixed` | `fixed` | | Default for ever. Refused if nothing binds it, `compiler.py:585-590` |
| `derived` | `percentile_of_own_history`, the one row in `DERIVED_BLOCKS`, `compiler.py:146-148` | `scaled`, `state_table` (M8) | Each bar, per side, a motion block is fed the named slot binding's output. Clamped to range (`unit.py:607-616`). Warm-up counted (`compiler.py:804-813`) |
| `calibrated` | `shrink_from_own_trades` | `learned` (M8) | A pinned rule block runs every N closed trades read, only when flat, `motion/engine.py:127-159`. Rule gets `{trades: [{strength, r}], current}`. Row goes to the journal, `unit.py:855-872`. A rule is any pinned block with that answer shape, so a new rule is a SWAP |

**Already real for "self-configuring".** The dummy's `rsi_low` and `rsi_high` follow their own history every bar. `min_trend_strength` follows its own record, with cadence, minimum count, shrink toward default, step limit and range. Motion runs identically in QMB and on the node, because both drive one handler. It can be turned off per run (`MotionSwitch`, `unit.py:97-101`). Calibrated values survive restart in the snapshot (`unit.py:353-361`), which R22 writes when one moves (`runtime.py:2919-2922`). Live starts from paper's values (row 22).

**Not real.** Cadence `at` alone refuses (`compiler.py:1008-1014`). `authority` is one label, read by nothing. Range edge cards (CONTRACTS section 9): UNKNOWN.

**Can sizing and exit numbers use it today? No, by the document.** M1 to M5 all refuse. The cause is one function: `_bound_on` (`compiler.py:510-516`) and the `stamp` search (`:620-631`) look only in logic slots, while `_bound_numbers` (`:536-551`) already counts exits and the sizer.

**A narrow side door exists, by accident.** A sizer may bind a number a logic slot also binds, with a matching measure. M6 compiled and the sizer read a moving value (`evidence=30`, `52.97`, `62.08`). A calibrated number shared the same way would be stamped by the slot's output, not by anything about sizing. The same door opens for the stop and the target, which receive numbers in evidence (`unit.py:575,778`). The per-bar exit stays shut (`:450-452,686`). I would not call this a design. It is what the code allows.

### 2.6 Run it

**QMB.** The host compiles with `gather` (`qmx_host/host.py:1967-1990`), writes a run folder, and `load_unit_folder` compiles again from `unit.json` and `blocks/<pin>/` (`qmb/host/unit_runner.py:441-466`). `UnitSliceHandler` holds position, equity and protection (`unit_handler.py:260`). On each slice, in order: cash; resting fills; bar read with stop, liquidation or target checked; unit steps (`:8-17`). Intents rest for the next bar. A swapped block needs no QMB change if it fits the shape. Read, not run.

**Node.** `promote._files` stages every pinned block by fingerprint (`promote.py:656-678`). The runtime compiles the staged bytes (`runtime.py:1943-1973`), refuses a fingerprint its G record did not test (`:2756`), and starts `NodeUnit` over the same handler (`:1587-1596`). Every entry passes `guard`, the hook stub and the protection gate (`:1750-1758,1100-1106`). Exits never pass a guard (`:1277-1280`). Differences from QMB a swap meets:

- Partial closes refuse (`:1807-1808`).
- A stop past entry refuses (`:1360-1369`).
- A target is closed by the node, not rested at the broker (`:1849-1857`), so one wicked bar reads differently in the two (App F, `seams-7`).
- No cash port.
- Equity is read once.

Never run against a real broker. R24's demo probes wait for his sign-in (`S\STACK-LIST.md`, "What still needs him").

**Probe results** (through QML's compiler and host, fake blocks, synthetic month):

| Id | Tried | Result |
|---|---|---|
| S1 | New sizer, same face | Compiles. Drops from `placeholders`. Evidence keys: `entry_price, equity, fraction, record, stop_price` |
| S1b | Sizer answers 0.10 | 25 entries, labels drop it. Receipt still says `inputs_used` the four names and residue `0/1` |
| S1c | Sizer answers 5000 lots | 25 entries at 5000 from the QML host |
| S2 | Sizer with an input | `inputs_not_built` |
| S3 | Trigger-typed block in the sizer slot | Compiles |
| T1 | New stop, same face | Compiles |
| T2 | Stop reads the position | `exit_not_built` |
| T3 | Stop fed a binding | `unknown_input` (`trend` is in no earlier place) |
| T4, T5 | Second target, second per-bar | `exit_not_built` |
| T6 | Exit at unit scope | `exit_not_built` |
| T7 | No stop | `stop_not_built` |
| T8 | Shipped trailing stop | `exit_not_built`, naming the risk session |
| P1 | New per-bar, no inputs, on a short position | Compiles. `close_full`, reason code `time-exit`, row "time exit after 1 bars": value 1 means the block was built long |
| H1, H2 | Halt in `/halts`, halt in a slot | `halts_not_built`, `binding_not_read` |
| M1 to M5 | Sizer, stop, target, per-bar numbers made to move | `motion_source` or `motion_not_built` |
| M6 | Sizer shares `rsi_low` with a slot | Compiles. `made=30`, `evidence` moves |
| M7 | `applies_to_open_positions` | `open_positions_not_built` |
| M8 | `scaled`, `state_table`, `learned` | `motion_not_built` |
| O1 to O4 | Reads, `sizing_modifier`, limit 2, market settings | Each refused by name |

---

## Section 3. Customization: what a user or copilot can change without code

| Thing | State | Evidence |
|---|---|---|
| `unit_new(template, overrides, title)` | **Real.** JSON-pointer overrides, saves a draft | `qmx_tools/functions.py:843-861`, `catalog.py:408` |
| `unit_check(document, item, previous_problem_set)` | **Real.** Saves the draft, checks A to F, `no_progress` | `functions.py:863-885` |
| `unit_explain` | **Real** | `functions.py:887-895` |
| `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match` | **Real.** Read and check only | `functions.py:1071-1134` |
| Save a block | **Missing.** No row | Section 2.2 |
| `library_save` of a unit | **Refused by design** | `service.py:1520-1525` |
| Unit templates | **One:** `dummy-trend-pullback.json` | `qml/unit/templates/`. `_templates()` lists the folder, `functions.py:811`, so a new JSON there is a new template with no other change, if it compiles |
| `template` Library kind | **Shell**, about 700 bytes, not the unit templates above | `kinds/template.schema.json` |
| `unit` kind | **Real**, generated, 42 KB | `kinds/unit.schema.json` |
| `component` kind with entry | **Real** | `kinds/component.schema.json`, `host.py:259,888` |
| `instrument`, `venue`, `account` | **Real**, margin and swap keys. No commission (G12, not re-read) | `kinds/instrument.schema.json` |
| `bms`, `book`, `board`, `binding`, `logic` | **Shells**, about 700 bytes each | `kinds/` listing |
| `pod`, `pod-block` | **Shells** | `kinds/pod.schema.json` |
| Hook on write | **Real.** Checks a unit file after Write or Edit, without the Library | `qmx-agents/plugin/hooks/hooks.json` |
| `build-unit` skill | **Real** | `qmx-agents/plugin/skills/build-unit/SKILL.md` |
| Backtest and judge rows | **Real** | `functions.py` tool groups, R14's check 18 per `S\STACK-LIST.md` |
| Publish | **His yes.** Agents hold drafts | Skill text, CONTRACTS section 11 |
| Promote | **His click only.** Not a catalog row | C-23, `promote.py` |
| Risk presets, `role: preset` | **Design only.** Judge presets are pass thresholds | System map section 3 |
| Lab pods | **Design.** `lab.py`: "on no model's surface" | `qmx_control/lab.py` docstring |

**What a copilot can change today, in the document, with no code:**

- Markets that have records. Direction. Time bars.
- Which blocks sit in logic slots, of 113 stdlib blocks less those refused by shape and the 17 in `BLOCKS_NOT_BUILT`.
- Combiners `all`, `any`, `k_of_n`.
- Every fixed number's default and range. Derived and calibrated settings on logic numbers.
- A different block in the sizer, stop, target or per-bar place, if one exists in the stdlib or Library with the narrow shape. Today only the placeholders fit: all five halts and six other exits refuse. So **a copilot has no real risk choice to make from the shelf.** It can change `risk_fraction`, `stop_buffer`, `target_r` and `time_out_bars` as fixed numbers.

**What it cannot change:** halts, reads, sessions as a field, per-market numbers, routes, scope, a second exit, moving risk numbers, or the kill table and hook, which are code.

**Not traced:** a Library-held block through `unit_new` to a QMB run to a node deploy. Each hand-off is read (`gather._library`, `host.unit`, `promote._files`). Whether it has been run end to end: UNKNOWN.

---

## Section 4. Plan against code, and what repair changed

### 4.1 Disagreements

| # | Plan says | Code says |
|---|---|---|
| 1 | L0 AD-24: "each slot is a typed contract that today's placeholder blocks already implement"; the risk design need not "force a rework" | The placeholders implement a narrower contract than CONTRACTS 4.3. Halts and hook have no host. Section 1 |
| 2 | A15: query "lists the dummy's five placeholder bindings" | Four bindings and four numbers, `tools/tests/test_placeholders.py:73-95`. Halts are an empty list, so nothing to list. The query cannot see rows 5, 6, 18, 19, 20 and others, which are not blocks. So "that query is the rip-out list" (PH) covers rows 1 to 4 and numbers only |
| 3 | PH intro: "Nothing refuses a placeholder" and a real block "must pass the four slot contracts" | True of placeholders. But compile refuses most replacements by shape, and passing the slot contract proves nothing about the host (E10) |
| 4 | L0 AD-15: every trade row shows the label | Only the intent carries `placeholder_labels`, `unit.py:833`. `_trade` body has no label. Numbers' origin never reach it |
| 5 | PH 5: halts empty, a warning | Layer E says "add a halt", `layers.py:684-690`; compile refuses it |
| 6 | PH 6: hook in QMB and node | Node stub only, different shape from `blocks/api.py` |
| 7 | PH 12: residue recorded | Fill residue real, sizer receipt literal |
| 8 | PH 14: stop past liquidation refused at entry | Not found |
| 9 | PH 15: change stands units down | Row exists, no producer |
| 10 | PH 17: balance plus unrealised | Balance only, once at start |
| 11 | PH 18: table holds effects | Closes read the table; entries do not |
| 12 | PH 20 and C-20 Build: after the cut a breach acts through a placeholder | Nothing evaluates a breach, and the new node never calls it. The plan's text says both |
| 13 | PH 21, C-23: deploy preflight | Node host step, R22. A promote can still be accepted, then refused on the node |
| 14 | PH 26: both shown | Not found |
| 15 | PH 29: fields exist | Schema has optional slots. Nothing writes them |
| 16 | CONTRACTS 4.4: limit and stop orders | Market only |
| 17 | CONTRACTS 4.5: `weights:`, `reading:` surfaces | Refused as extras, `unit.py:908-916`. `account` is a surface the table omits |
| 18 | CONTRACTS section 7: identity table decides | Unwired |
| 19 | CONTRACTS section 8, section 9, A9: `lifecycle.auto_paper` | Deleted, Call 7 |
| 20 | CONTRACTS section 9: "all editable" | `min_trades`, `shrink_k`, `slow_cadence`, `seam_jump_scale` are constants |
| 21 | A13d: exits "pass A15's slot contracts later" | They pass, and refuse at compile, by R04 |
| 22 | App F: "needs nothing from this program" | True for resuming. But `A/REPAIR-SCOPE.md:76` says agree the socket first (per system map) |
| 23 | App F line numbers: `compiler.py:493`, `runtime.py:2269-2314` | Tip: `_shape_problems` at `:896`, `guard` at `:2623-2675`. C-20's `runtime.py:2078` is now `:2511` |
| 24 | `test_socket_contracts.py` docstring: "checked on the evidence the host really passes" | `_exit_breaks` yes; `_never_acts` no |

**Cross-check against the prior map (`review-2026-11-07\system-map.md`).** Every fact I re-read held: 18 roles and 7 run, 17 refused pins, sizer inputs, literal residue, the hook, `kill_line`, the shell kinds, one template. It did not record the guard ignoring the kill table, the make-versus-evidence trap, the per-bar reason being hard-coded, no slot type check, or `_CEILING`. **G12** read earlier tips: its "not reviewed" notes on R16, R19 and R21 are now out of date, since `S\STACK-LIST.md` marks all 24 CLEAN. Its J and N line numbers no longer match.

### 4.2 What R01 to R24 changed that this session builds on

"Read" means I saw the code at the tip. "Body" means I took it from the plan part or from G12's PR-body reading.

| PR | What to build on | Source |
|---|---|---|
| R01, R02 | Dead code and gates. A red now means something | Plan part |
| R03 | A library repair bumps the money app, and he signs | Call 11 |
| R04 | Every refusal in 2.4. Census test. Format 4 | Read |
| R05 | Slots by shape, feeders, `value-above@1`, `trend-floor@2`, tick rounding | Read, partly |
| R06 | Session clock, name checks across the store, `auto_paper` gone | Read, partly |
| R07 | A backtest reads his Library record, so a record change reaches a run | Body |
| R08, R09 | Real data reader. Real-month lanes still owed | `S\STACK-LIST.md` |
| R10 | `mae_r`, `mfe_r`, `risk`, `money`, drawdown (`unit_handler.py:97-100,391-398`). Stated cost profile. `trade_r` single read | Read |
| R11 | Version pull: a same-trades version pays, a moved one may escape. A pure sizer swap reads the parent (G12's reading) | Body |
| R12, R13 | One verdict. Check says what it cannot see without the Library (`unit_check.py:40-44`) | Read, partly |
| R14 | Foundation proof, 18 checks | `S\STACK-LIST.md` |
| R15 | Reason census: new brake text needs a code. Live writes `unlisted`, QMB stays strict (`journal.py`, `journal_kinds/unit.py:73`). Node trades reach the Library | Read, partly |
| R16 | Alarms reach him. Push list stays closed | Body |
| R17 | `_admit`, `_leave`, outbox | Body |
| R18 | MIS publishes. Board stays unwired | Body |
| R19 | Market `minute` row with spread. No fees or slippage | Body |
| R20 | Broker wins at reconcile. Hand part-close leaves full size (`S\BACKLOG.md:64`) | Body |
| R21 | `_close_scope` one closer (`runtime.py:2451`), kill and flatten act, stop past entry `Blocked` (`:1360`), `stop_differs` alarm. Restores a lost stop at the send row, which trails must change | Read |
| R22 | `_netted`, WAITING until session (`runtime.py:2786-2789`), snapshot when a slow number moves | Read |
| R23 | Clock stand-down wired (`runtime.py:2121`), market-hours, paper positions survive | Read, partly |
| R24 | Demo probes will answer whether a fill carries the stop, deal-history fields, what a close on a gone position answers. Not run | Body |

### 4.3 Repair hand-offs still open

**From App F:**

- The signed stop distance (`known-1`, `triage-1`).
- Whether a stop may widen.
- Scale-out and R (`p1b-4`, `p5a-17`).
- Target at broker or node (`seams-7`).
- Unit with no stop (`p0a-8`).
- Moved numbers and open trades.
- Which exit wins on one bar.
- Which position facts exits read.
- The exits socket: step 2 (real evidence and side, `unit-n2`, about 60 lines) and step 3 (trails, partials, stop moves, `p1b-3`, about 250 lines; not on the node before the signed distance).
- `p1a-8`: a long wick gives a stop above the close.
- R and costs (`p0b-13`, `p2-6`, `seams-10`).
- Kill level meanings.
- SQS seat (Call 19, `plan-check-2`), with the rule text at `qmn/host/decision_root.py:496-510` and `sqs_baseline_producer.py` to move before C-20.
- Sizer socket (`plan-check-7`, `p0a-12`).
- Drawdown halt silent at zero equity (`p1a-7`).
- USDJPY sizer error (`fixed-fraction-at-stop/1/block.py:52-53`, `p0a`).

**From `S\BACKLOG.md`:** version pull (`:51`), `too_thin` number (`:55`), u2 cannot answer "holds" on a real run (`:69`), push list closed (`:65`), hand part-close and protection-close record holes (`:64,66,67`).

**Written for this session and not on a list:**

- R10 low 1: a check with no orders records a pass (`S\lows.md:447`, "put it in BACKLOG.md for the risk session").
- R21's "a lost stop returns at the entry's level once trails ship" (`S\RESUME.md:163`, per G12).
- The undelivered stop note `unit-ship\RISK-NOTE-2026-11-04.md`, per G12.

**Blocked on others:** his demo sign-in (R24 lanes 5 and 6), C-20 (after G-DEMO), the landing itself (0 merged).

**From App B, waiting on this session:** "After the risk session agrees the socket: exits really run".

---

## Section 5. Every file a swap will touch, by owning lane

Lane names follow the part that built each file. Whether the recut keeps them is his call. "Crowded" means App C lists many repair PRs on it.

**QML (Part A)**

- `qml/src/qml/blocks/api.py`: `Size`, `ExitInstance` answers, `HaltInstance`, `CrossUnitHook`.
- `qml/src/qml/compile/compiler.py`: every refusal in 2.4, `_motion`, `_exit_gap`, `Plan`, format bump.
- `qml/src/qml/protocol/unit.py`: `Account`, `OwnPosition`, `enter`, `exits`, `timer`, `_required_keys`, receipts, snapshot shape (state schema version).
- `qml/src/qml/motion/engine.py`: if rules read more than stamp and R.
- `qml/src/qml/unit/model.py`, `unit/qmx.unit.1.schema.json`, `unit/schema.py`, `unit/parse.py`, `unit/upgrade.py`: any new field. Generated schema; census test.
- `qml/src/qml/unit/templates/dummy-trend-pullback.json` and any new template.
- `qml/src/qml/check/layers.py`: halts wording, new warnings, slot type checks.
- `qml/src/qml/numbers/convert.py`, `numbers/records.py`: rounding rule, new record facts.
- `qml/src/qml/lifecycle/machine.py`: row 24.
- `qml/src/qml/identity/`: if the table is wired.
- `qml/src/qml/blocks/stdlib/<new blocks>/`, and the six exits and five halts as they go live.
- `qml/catalogue-seed/wave-1/exits-and-halts/`: dictionary pages.
- Tests: `qml/tests/test_socket_contracts.py`, `test_unit_refuses.py`, `test_compile_dummy.py`, `test_wave1_exits.py`, `golden/exits-and-halts/`, `test_lifecycle.py`.

**Contract package (`packages/qmf-risk`)**

- `src/qmf/risk/unit_intent.py`: sign of distance, widening law, reason codes on exits, none_declared.
- `tests/test_unit_intent.py`.
- `src/qmf/risk/door.py` must stay untouched for format 3 (A1).

**QMB (Part B)**

- `qmb/src/qmb/host/unit_handler.py`: shared with the node. Equity, position facts, halts, `ClosedTrade`, `r_after_costs`, new trade fields. Crowded.
- `qmb/src/qmb/host/unit_runner.py`, `host/behaviour.py`.
- `qmb/src/qmb/execution/fill.py`, `execution/risk.py`, `execution/financing.py`: only if rules change.
- `qmb/src/qmb/results/journal.py`: `_trade`, reason table, risk events.
- `qmx-agents/apps/qmb/jobs/backtest.py`: result fields.
- Tests: `qmb/tests/test_unit_handler.py`, `test_unit_runner.py`, `test_realism.py`, `test_run_journal.py`.

**Node (Part C)**

- `qmn/src/qmn/app/runtime.py`: hook, `guard`, `_exit`, `amend`, `_move_stop`, `risk_stop` producer, equity feed, constants, `_netted`. Most crowded.
- `qmn/src/qmn/app/stand_down.py`: rows, reason texts, spec-change producer.
- `qmn/src/qmn/app/paper_lane.py`: partial close, equity.
- `qmn/src/qmn/app/operations.py`: kill scopes.
- `qmn/src/qmn/protection/effect_matrix.py`: kill table.
- `qmn/src/qmn/capital/kill_line.py`: repoint or wire.
- `qmn/src/qmn/venue/ctrader_account.py`, `venue/ccxt_client.py`: live equity, partial close.
- `packages/qmf-venue/src/qmf/venue/encode.py`: stop sign.
- `qmx-agents/apps/trading-node/app.toml`: version bump, his signature.
- Tests: `qmn/tests/test_app_runtime.py`, `test_protection_every_order.py`, `test_app_every_way_out.py`, `test_app_stand_down.py`, `test_app_deployed_runs.py`.

**Journals (`packages/qmf-data`)**

- `src/qmf/data/journal_kinds/unit.py`: risk events, reason codes, would-have rows.

**Host, tools, Library, judge, engine (`qmx-agents/packages`)**

- `qmx-tools/src/qmx_tools/functions.py`: a block-saving row, if wanted. `gather.py`, `unit_check.py`.
- `qmx-control/src/qmx_control/catalog.py`, `service.py`: new rows, settings defaults.
- `qmx-host/src/qmx_host/records.py`: trade fields. `promote.py`: starting numbers. `host.py`: crowded. `venue_records.py`: margin and leverage.
- `qmx-library/src/qmx_library/kinds/`: `trade`, `pod`, `template`, `book`, `bms` if they gain shape.
- `qmx-judge/src/qmx_judge/judge.py`: `trade_r`, fixed-size baseline. `presets.py`: too-thin. `paper.py`.
- `qmx-engine/src/qmx_engine/templates/dc-decay-and-limit-report/`; `rk2`, `rk5`, `p1`, `pp` wait on risk rows (G12).
- `qmx-agents/plugin/skills/build-unit/SKILL.md`, `plugin.manifest.json`: if rows change.

**Tools**

- `tools/qml/placeholders.py`: widen past blocks and numbers, if the rip-out list should cover hook and tables. `tools/tests/test_placeholders.py`.
- `tools/money_path_scan.py`: runs over new money code.

**Reference only, do not edit from a build branch**

- `P\build\UNIT-PLAN.md`; `P\build\RISK-SIZING-PLACEHOLDERS.md`.

**Not touched by a swap, as far as read**

- UI: `UI-NOTES-UNITS.md` says no separate risk screens (per system map).
