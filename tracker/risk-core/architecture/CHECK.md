# Last independent check of the risk-and-sizing architecture

Opus, 6 Nov 2026. Paths are under `tracker/risk-core/` unless they name a tip. `SP` is `architecture/SPINE.md`, `FU` is `funnel/FUNNEL.md`, `NOTE` is `handoff/FOR-REPAIR-SOCKET.md`, `A` is `D:\QMX-worktrees\audit-ship`. Tips: J `a4f64510`, N `ef011af4`, R `7ada84ed`. Newest read: R18 `bld-repair-18` at `337b2cc5`, R23 `bld-repair-23` at `697aafc6` (still moving). My scripts and outputs are in `architecture/check/`. Model numbers are model numbers. **[judgment]** marks my opinion.

## Verdict

The shape holds and fits the code: 61 of 62 bindings read true, exits and kill levels are safe by type, `fold_sim.py` reproduces `out-fold.txt` exactly.
It is not ready to explain as final: ten blockers, and two of them (`net_r`, the admission gate) would stop a healthy unit at go-live with no sim noticing.
Nearly all are a few lines in the spine, so one fix round closes them; hold `NOTE` until then, and tell him 38 to 45 PRs, not 31 **[judgment]**.

## Blockers

**B1. `net_r` counts spread and slippage twice, and the card's basis is unset.**
- Where: SP:70, SP:171, SP:281, NOTE:15.
- What: `net_r = r − costs_r` with `costs_r{spread, commission, slippage, swap}`. But `r` is money at fill prices that already hold spread and slippage. The CUSUM reads `net_r` "against the card", and nothing says which R the card is in. "Rename `r_after_costs` to `net_r`" puts a gross value under a net name, in a field the motion engine reads, while AD-12 says the logic record stays gross.
- Evidence: J `qmb/src/qmb/execution/fill.py:1297,1301`, `unit_handler.py:668`, `qmx-agents/apps/qmb/jobs/backtest.py:96` (the true form, `(money + cash) / risk`), `qml/src/qml/motion/engine.py:57,120`. `check/out-check-main.txt` arms G, H: brakes reading 0.16R a trade under the card send 93 to 100 % of healthy units to paper (share kept 0.15 to 0.38); 0.08R sends 61 to 76 %.
- Fix: `net_r = (money + cash) / risk`; spread and slippage in `costs_r` are display. The CUSUM's reference is the holdout's `net_r`. `r_after_costs` keeps its value and is renamed for gross, never `net_r`. Test: a healthy replay's CUSUM does not drift.

**B2. The admission gate refuses the worked healthy unit at every hour at go-live. M7 is back.**
- Where: SP:215, SP:70, SP:227, `ledger/v1/core.md:98`.
- What: the gate is "band low end minus the cost cell above zero this hour", and at go-live the only cell is the stressed default. Nothing exempts it.
- Evidence: net +0.10R, cost 0.16R, low end −0.05 (`funnel/working/review/core_sim.py:48`, `:110`). Gross band minus stressed cost: 0.21 − 0.32. Net band as AD-12 says: 0.05 − 0.16. The ledger's ratio of 2: 0.21 / 0.16 = 1.3. All three refuse. FU:113: "a cell refuses only after fills show net edge below zero". `fold_sim.py` runs no gate.
- Fix: one sentence in 4.4: admission reads the holdout's net low end; an hourly cell refuses only when measured from fills; `cost:uncalibrated` passes. Bind or drop `edge_to_cost_ratio_min`.

**B3. A guard failure blocks exits. This is the fault the design introduces.**
- Where: SP:51 step 1, SP:204 against SP:262, SP:62, SP:76.
- What: `_step` calls `guard.advance` before the unit steps; `Guard.position_facts` feeds exits (4.6 says `HostedUnit.exits` builds them, so two answers); the status write is on the runtime thread. AD-4's test covers guard states, not a guard that fails.
- Evidence: R23 `qmn/src/qmn/app/runtime.py:3035-3037`: a refused frontier sets `Phase.STOPPED`, and `:3005-3008` drives no stopped unit, so protective reads and per-bar exits end. A raise goes to `:2193`, then back-off, again on each bar. `_write_snapshot` at `:3043` is unguarded, and `check/out-windows-replace.txt` shows `os.replace` raising `PermissionError` on this machine while a reader holds the file; SP:308 has tools reading the status file.
- Fix: one wrapper: any raise or refusal from `advance`, `before_order`, `on_event` or a status write becomes `guard_unavailable` on entries; exits mint; the unit stays TRADING. Drop `Guard.position_facts`. Tools read RiskState rows, never the file. Test: a guard that raises on every call, and the per-bar exit still closes.

**B4. An agent can publish a lower floor.**
- Where: SP:26-29, SP:63, SP:310, SP:315, slice 3 at SP:403.
- What: profile, group and preset are Library kinds. Only `unit` needs his click, and `library_save` refuses only `unit`. An agent can put a `risk-group` on main, and `_deployment` carries it. "Value edits are immediate" names no door.
- Evidence: R18 `qmx-agents/packages/qmx-control/src/qmx_control/service.py:1519,1673-1679`. `A/REPAIR-SCOPE.md:88` parks this as triage-3. No slice claims it.
- Fix: slice 3 treats `risk-profile`, `risk-group` and the preset `template` as `unit` in both places; immediate edits come only through his door.

**B5. USDJPY is fixed only in the sizer.**
- Where: SP:181, SP:192, SP:221, SP:223.
- What: the record's `value_per_point` and the handler's money are in quote currency. QMB's `equity_balance` adds yen to dollars. The ledger's price-derived fallback, the node's only source until R24, does the same, so one USDJPY loser reads as hundreds of dollars and can fire the day stop. A cross has no conversion source at all: EURJPY has no USDJPY quote in either host.
- Evidence: `qmx_host/venue_records.py:226,231`, `qml/src/qml/numbers/convert.py:112`, J `unit_handler.py:216-220,370-372`, R23 `feed_keeper.py:351`, `host.py` `_bars` (asked markets only); `ctrader_account.py` reads no deal money.
- Fix: the kernel converts every money figure, including `_account()`. The tape includes USDJPY and a cross. The record names a `conversion_market`, both ports load it, and a missing one refuses in plain words.

**B6. The resting target's fallback may wipe the disaster stop.**
- Where: SP:279, NOTE:25.
- What: "one amend with `ProtectionSide.TARGET` right after the fill". The encoder writes one field. cTrader's page lists both as optional and is silent on an omitted one; one forum reply treats leaving it out as a way to remove it, unconfirmed. If so, the stop is gone. The same applies to a stop amend with a target resting, at step 3.
- Evidence: J `packages/qmf-venue/src/qmf/venue/encode.py:1029-1036`; `unit-plan/tracker/risk-sizing/build/repair/plan-parts/r24.md:37` does not ask it. Sources: [cTrader messages](https://help.ctrader.com/open-api/messages/), [forum thread](https://community.ctrader.com/forum/connect-api-support/40940/).
- Fix: add the question to R24. Once a target can rest, the amend sends both levels and reads `stop_of` back. No fallback until proved.

**B7. A restart or a version can reset the brakes.**
- Where: SP:59, SP:76, SP:463, SP:77, `ledger/v1/core.md:253`.
- What: AD-1's generation holds the anchor id and "starts cold"; AD-18 rebuilds and never resets; the walk says the generation "matches" across a missed anchor, which AD-1 forbids. AD-19 restarts the money record on a version, and nothing says a bench, lockout, drift lock, stand-down or paper state survives. So an agent's draft and one click may clear a bench.
- Fix: generation is the spec fingerprint and schema; anchor id is a separate field; "starts cold" becomes "rebuilds through `recover`". Rule: a version never clears those states, and `state_carry_rule` takes that value.

**B8. The choke test cannot see a refusal.**
- Where: SP:74, SP:361-363, `fold_sim.py:176-181,196-197`, `ledger/v1/core.md:268`.
- What: size/base counts trades taken, so a benched day, a stopped day, paper or a gate leaves it unchanged. Also, 23 things bind, not 15: 14 live rows (SP:171), plus reserve, cost denominator, B, the open-risk share (SP:179), level, lot shed, round-down, resets and the buffer stop (SP:382). The sim runs 10. Not run: open-risk share, clip, bet key, per-trade, sanity band, margin, order rate, stop side, SQS, news, admission, resets, buffer stop. And the baseline already holds 0.7225 of reserve and cost (`core_sim.py:51`).
- Evidence: `check/out-check-main.txt`. Healthy at N = 1, 5, 10: the spine's metric 0.86, 0.89, 0.88; share kept on every opportunity 0.80, 0.89, 0.88; with a guessed 15 % of opportunities refused 0.72, 0.76, 0.75. So N = 1 has room for about 6 % refused. Against the raw formula N = 1 is 0.58. This is M3's fix half done.
- Fix: the ledger's metric is dollars risked over baseline on every opportunity; the CI test runs all 23; say what the denominator already holds.

**B9. Row verbs have no block shape, so "a new brake needs no code" is false.**
- Where: SP:151, SP:161, SP:346, SP:348.
- Walk 1, a brake that halves size: `HaltInstance` answers `Halt` or None, and `HaltAction` holds only `NO_NEW_ENTRIES` and `FLATTEN` (J `qml/src/qml/blocks/api.py:168-174`). A multiply, cap, gate or raise has no return type, so `reducing-p10`, `burn-tiers`, `weekend-scale`, `kelly-ceiling` and the press do not fit. A derivation block has no answer type either. Block state (`export_state`) has no slot in the status (SP:147).
- Walk 2, a class quoted in EUR: SP:348 says no rework; it needs B5's conversion leg in both ports. Whole-contract classes are already admitted.
- Fix: in 4.2, `GuardRowInstance.update(evidence) -> Refuse | Factor | CapLots | Trip | None` and `DerivationInstance.update(inputs) -> Recommendation | None`; `HaltInstance` serves `trip` only; a `block_state` slot per row.

**B10. "How does it self configure" has a rule for 2 of 107 numbers.**
- Where: SP:63, SP:118, slice 4 at SP:404, `ledger/v1/core.md`.
- What: the shape is real (SP:53) and one rule is worked (4.3). But a preset number may not have `derivation: None`, AD-5 refuses a blank, and slice 4 names two rules. The core has 107 numeric rows, 94 with no default and 49 with basis `open`; 153 of 207 ids appear nowhere in the spine. The numbers lens brings values, not rule blocks, so no builder can write the first preset.
- Fix: one `preset-default@1` rule and a table generated from the ledger before slice 3: number, rule, rung, clock, cautious direction, row.

## Should-fix

1. **Baseline clock.** SP:175 says the allocation anchor (weekly); SP:459 and the sim use the day. Weekly as written: healthy medians 4371 → 3486 at N = 5, 5076 → 3902 at N = 10; survival about the same (arm B). Fix: cushion on `day`, N and B on `allocation` (FU:98).
2. **Freed swing.** No formula in the spine ("B from 4.4" at SP:175; 4.4 is silent; only `fold_sim.py:53`). It raises units above the flat baseline by rule, under a caution, against FU:455. Bleeding book half-cushion 25 % against 16 % at N = 5 and 21 % against 18 % at N = 10 (`out-check-freed.txt`, 300 paths); healthy medians up 20 to 28 % (arms A, E). Write the formula and put it to him.
3. **`two_live_readers` refuses the go-live rows.** SP:66 refuses a second live reader; day stop and taper both read the group ledger (SP:171). Make them one row.
4. **Blank user rows.** AD-5 and SP:118 refuse compile; SP:147 compiles and blocks the click. Keep SP:147.
5. **Preset rung up-sizes.** SP:192's fixed share has no B: at N = 10, $0.76 against $2.00 at 1 %. Rung is the smaller of last in force and share ÷ B.
6. **Lockout.** AD-11 waits for him; the sim returns after 20 days (`fold_sim.py:232-234`). About one healthy unit in three hits one per 120 days at N = 1 (0.29 per 100 days). Decide, and tell him.
7. **`before_order` must be pure.** It runs during warm-up (R23 `runtime.py:1724-1728`), SP:457 has it adding risk to the key, and `on_event` has no event for a blocked order (SP:206), so risk would leak. Read risk from facts only.
8. **31 PRs is the low end.** R19 to R22 are 246 to 559 source lines each. Slice 10 holds 11 shadow rows, card, tiers and agent rows in 2 PRs; slice 4 holds the derivations in 3. The fold added 16 items (SP:425) for +2 PRs over the base (PICK:19). Say 38 to 45 **[judgment]**, or land 8 shadow rows after go-live. The machine: 14 live and 11 shadow rows is more than a first increment needs; the rest of the shape earns its place.
9. **A new derivation rule has no door.** SP:350 is real for a pin, ladder, inputs or clock when the rule exists. A new one is a repo folder, or `blocks_check` then stdio-only `library_save` (`catalog.py:497`); 4.8 names neither. Add one propose row (QMA flag). Expressions stay deferred.
10. **Small.** `stop_side`, `order_rate` are refusals in the cap band (SP:247). `margin_free` from "the record" (SP:232) must be computed or every entry refuses. Level floor (FU:123) is in the sim, not the spine; no effect at a $0.50 lot (arms C, D), matters at coarse lots. `applies_to_open_positions` sits on the number, not `Authority` (SP:122, J `compiler.py:998`). QMB's `sqs:bar_sampled` (SP:229) against "refused at the door" (`G12:186`). `k_own_p1`'s draw belongs in the harness, not on the runtime thread (SP:60, SP:470). Ledger against spine: modes (`core.md:20`), never-self-tune (`core.md:19`). `SYNTHESIS.md:24` fire rates are stale.
11. **One plain go-live list; the spine has none, and FU:437-445 is stale.** Add:
    - No trails, breakeven or partials at first go-live (`seeds/operator-words-2026-11-03.md:97`; SEEDS lens items 16, 46).
    - Every unit on 15-minute bars until after G-DEMO, so the cut and scalper behind every model number cannot run on the node before then (SP:419).
    - At $500, about 3 of 10 proved units trade, 1 or 2 of a weak ten (arm A `live` 0.20). His frequency thesis waits on the cushion.
    - Freed swing (item 2). Lockouts wait for his click (item 6).
    - Drift: third warning to paper, each warning locks 20 days. Q1 (FU:455) still says second, and FU:437's "two brakes" omits it.
    - Target at the venue overrules the node-closes stance (SP:375).
    - One position per market (SEEDS lens 19). `session_loss_limit_r` (`core.md:70`; lens 23) has no row, shadow or deferred: a silent drop.
    - Bleeding book of 5 or 10: half the cushion in about a quarter of runs; re-entry with no cooling (SP:457). First entry waits hours (SP:383). Kubernetes in its simplest modes (SP:338).
12. **`NOTE`.** True and decided except: B1's rename (NOTE:15, NOTE:43); B6's fallback (NOTE:25); "guess 2" (NOTE:7, SP:259) contradicts SP:323, which lifts one-per-use; "one fact" (NOTE:37) undercounts SQS, margin and deal money; "ledgers read deals" (NOTE:17, NOTE:46) is price and kind only until R24 (SP:223); line numbers name no tip, and `runtime.py` has moved +70 to +80. "Nothing here changes a repair PR" (NOTE:55) makes it safe once B1 and B6 are edited.

## Held up

- **Code truth.** 61 of 62 bindings hold at the tips (`check/out-bindings.txt`). The miss: `relativeTakeProfit` is not in the encoder (SP:279), only in the proto; it reads as present and is future work. Every named thing still exists at the newest heads.
- **Entry trace.** Bar, handler, sizer, `lots` floors, `OrderPath.entry` with `blocked_by`, venue stop: fits with one seam at `unit_handler.py:484`.
- **Exit trace.** `place` sends exits to `_exit` with no `blocked_by` (R23 `runtime.py:1753,1762`). No normal guard state touches an exit.
- **Kill level.** `Effect` has no lowering variant (SP:212). **Agent order.** The guard answers and never sends; demo tools are stated (SP:315).
- **Rounding.** `lots` floors and refuses under minimum (`convert.py:88-93`), and the node floors again. Nothing rounds up.
- **Wrong side.** `enter` refuses before the sizer (J `unit.py:768`); `abs` stays blocked until step 3.
- **Sizer on USDJPY.** The formula is right for a quote-currency `value_per_point`.
- **Stale facts.** They refuse; the restart walk is sound apart from B7's wording.
- **Handbrake numbers.** Appendix A is transcribed right. Rerun at 100 paths: healthy paper 5 to 9 %, half-cushion 23 to 28 % on the bleeding book, no floor touches. The healthy unit stays above 0.75 on every reading I could run, start level included, and at 2 and 4 trades a day (0.83 to 0.87, `out-check-rate.txt`), subject to B8.
- **Extensions that pass.** Swapping a base rule, a style preset, shadow to live, a version keeping the record.
- **`REVIEW.md`.** M1, M2, M4, M5, M6, M8, M9 to M12 have not come back. M3 and M7 are half back (B8, B2).
- **Fidelity.** The hard lines are all carried; no silent override beyond item 11's list.
