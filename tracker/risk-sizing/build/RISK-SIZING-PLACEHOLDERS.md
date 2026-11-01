# Risk and sizing placeholders the unit system build leaves

For the risk and sizing session. Every stand-in the build ships for sizing, exits, halts, the kill switch and the money-adjacent facts around them, with where it sits, which PR in `build/UNIT-PLAN.md` puts it there, and what the risk session must replace or decide. Nothing here designs the maths (ledger R-01, R-04). His words, "risk and sizing, that's already out of scope for now, but it's part of the unit" (T3:904).

Sources. Level 0 "For the risk session" (`architecture/level-0/ARCHITECTURE-SPINE.md`), the three parts' `RISK-SIZING-POINTS.md`, Part A `CONTRACTS.md` section 4.3 (the slot contracts) and Part C lead's call LC-C-28. The pack of his own words is `RISK-SIZING-PACK.md`.

## How the placeholders behave

- Each stand-in is an ordinary block or a named setting whose card says `origin: placeholder` and names the risk session as owner (Level 0 AD-15). The unit card, the promotion card, every intent (`placeholder_labels` in CT-23 format 3) and every trade row show the label.
- Nothing refuses a placeholder. His click decides, and a live promotion of a unit with placeholders needs his tick on that line.
- `tools/qml/placeholders.py` (A15) lists every published unit and binding that uses a placeholder. That query is the rip-out list. A risk-session block must pass the four slot contracts in `qml/tests/test_socket_contracts.py` (A15) to replace one.

## The placeholders

| # | Placeholder | What it does today | Where it sits | PR | What the risk session replaces or decides |
| --- | --- | --- | --- | --- | --- |
| 1 | Sizer `fixed-fraction-at-stop@1` | risks 0.5% of equity at the stop, rounds down to the lot step, skips with a reason below the minimum lot | `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/1/`, bound in the dummy | A4, A2 | the sizing method and its inputs, house money, size growing back after a cut, Kelly ceilings, the old relentless system against the Book and BMS (PACK §2.2) |
| 2 | Stop `swing-stop-buffer@1` | a protective stop beyond the last swing point plus 0.02% of price | `qml/src/qml/blocks/stdlib/swing-stop-buffer/1/` | A4, A2 | stop methods |
| 3 | Target `target-r-multiple@1` | a 2R target | `qml/src/qml/blocks/stdlib/target-r-multiple/1/` | A4, A2 | targets, time-varying targets, profit caps, give-back from peak |
| 4 | Time exit `time-exit-bars@1` | closes after 48 bars | `qml/src/qml/blocks/stdlib/time-exit-bars/1/` | A4, A2 | time-based exits |
| 5 | Halts at position, unit and account scope | empty, shown as a warning on the card | the dummy's `halts` slot | A2 | daily loss limits, streak halts, equity kill switches, which halts flatten and which stop entries |
| 6 | The cross-unit hook before every order | passes every order | QMB's unit handler and the node's order path, step 3 | B5b, C-12a | correlation and book control, same-bet limits, the pod's share; it may read the MIS's dispersion and herding readings |
| 7 | Motion of risk numbers | no risk number moves; every placeholder number is `fixed` | `NumberSpec.kind` and `motion` | A3, A5 | which sizing and exit numbers follow the market and which follow the record, and with what minimum count |
| 8 | Moved values and open positions | `applies_to_open_positions` is false | `NumberSpec` | A3 | whether a moved number may change an open trade's exits |
| 9 | Stop amendments | may tighten, never widen | `amend_protection` in CT-23 format 3 | A1 | whether widening is ever allowed |
| 10 | Partial closes | available to exit blocks; the placeholders do not use them | `close_partial` in CT-23 format 3 | A1 | scale-out ladders |
| 11 | A unit with no price stop | `protection.stop = none_declared`; R is undefined and results are flagged; a trade without initial risk carries `r_missing` | CT-23 format 3, the `trade` kind | A1, B15 | whether such units are allowed and how they are judged |
| 12 | Lot rounding and the minimum lot | round down to the lot step, skip below the minimum, residue recorded in R | QMB's unit runner, the node's order path | B5b, B10, C-12a | the rounding rule on small accounts ($300 with one or two units, PACK §2.8) |
| 13 | A gap through the stop | fills at the first tradable price; the loss is recorded in R as it fell, never capped at 1R; `gap_through_stop` flagged | QMB's fill model, the node's journal | B10, C-12a | how the sizer treats gap risk |
| 14 | Margin and liquidation | values from the account and instrument records; liquidation at the record's maintenance level on mark price; a stop past the liquidation price is refused at entry as a fact check | QMB's margin port, the node's protection gate | B10, C-12a | margin per session, leverage policy |
| 15 | Leverage and spec changes at a venue | the node never changes leverage; it reads it into the account record, and a change stands that symbol's units down until his click | records, the stand-down table | C-02, C-12c | whether the node sets leverage, and the margin rule |
| 16 | Perps funding and swaps | recorded as costs at their times; no rule | QMB's carry adapter, readings | B10 | whether funding changes size, whether units avoid funding times |
| 17 | Account facts the sizer reads | the bound account's equity (cTrader balance plus unrealised P&L, since it gives no equity field; Hyperliquid account value), each with its time and source | the node's account facts per binding | C-12a, C-16 | the budget share per unit |
| 18 | Kill-switch effects per level | YELLOW stops new entries at the scope; ORANGE also cancels resting entry orders; RED also closes positions at the scope, reduce-only; BLACK closes everything and pauses the node. Escalation is escalate-only and resume is his | `qmn/src/qmn/protection/effect_matrix.py` | C-12a | the values, and which triggers escalate how far |
| 19 | Protection that cannot be placed | after 3 failed placements within 2 s each, close that position reduce-only and raise a protection-escalation alarm | the node's order path | C-12a | close, hedge, or alarm only |
| 20 | The kill line's verb after the shell cut | a breach stops new entries for that binding, leaves exits and broker stops, and is a risk stop waiting for his resume | `qmn/src/qmn/capital/kill_line.py` | C-20 | flatten or stop, and the floor's number |
| 21 | Two units on one symbol of a netting account | refused at deploy, naming the fix (a hedging account or another account); a hedging account keeps one virtual position per unit | the deploy preflight | C-23 | how shared protection and attribution work on netting accounts |
| 22 | The numbers a live deployment starts from | paper starts from the unit's defaults; live starts from the paper lane's last calibrated values and their watermark, the calibrator's statistics restarting there | the promote route's deployment builder | C-23 | whether sizing numbers carry from paper to live, restart, or carry full state |
| 23 | The one automatic move | only an explicit halt block's `flatten` or `no_new_entries` counts as a risk stop; it lands one `lifecycle` event with `by: risk_rule` | `qml.lifecycle`, the node's stand-down | A9, C-12c | which rules count, and whether a stop may land a unit on paper directly |
| 24 | Paper after a risk stop | his click | the lifecycle machine | A9, C-12c | direct, or his click |
| 25 | Risk events in journals | `risk_event` kinds labelled `origin: placeholder` | the journal kinds | B8 | the real event kinds |
| 26 | Judging with the unit's sizer and with fixed size | both always shown; fixed size is the baseline | the judge and its baseline card | B13 | which one a verdict uses |
| 27 | Correlated exposure in judging | correlated markets count as one record | the judge's try clustering | B13 | the cross-unit control |
| 28 | The decay check's alarm | informs only (OK, Watch, Alarm), with tighten-only proposal cards | the decay template | B20 | the action after an alarm |
| 29 | Fields to replay any sizing later | trade rows carry equity before, session, streak, the tuned values in force and the placeholders used; stopped units write would-have rows | the `trade` kind version 2, the journal kinds | B8, B9, B15 | the replay method, including the old "radioactive" sizing |
| 30 | The size the venue receives | the sent quantity equals the sizer receipt's after lot rounding (a fact check, kept) | QMB fills, the node's order path | B5b, B6, C-12a | none, it stays |
| 31 | Pods | designed, unbuilt (Lab AD-10 to AD-12) | not in this build | none | whether pods compile into socket blocks |

## What the slots accept (Part A `CONTRACTS.md` section 4.3)

| Slot | Inputs | Output |
| --- | --- | --- |
| sizer | entry reference price, stop price, instrument facts, account facts `{equity, balance, open_risk}`, the unit's own record in R, market statistics from bound blocks, his limits | `{quantity (lots, exact), receipt}` or `{skip: reason}` |
| exit block | the position (quantity, average price, stop, targets, opened by, opened at, bars held, MFE and MAE in R), market evidence | zero or more of `close_full`, `close_partial`, `amend_protection`, each with a reason |
| halt | unit and account statistics (losses in R this session, streaks), his limits | `none`, `no_new_entries`, or `flatten`, each with scope and reason |
| cross-unit hook (called by the host) | the proposed intent, the account's open positions across units, the board's dispersion reading (optional) | `pass` or `refuse` with a reason |

## Questions the session meets in the code (pointers, not answers)

- Whether the cross-unit hook stays a host call or becomes a slot in the unit document.
- Whether an account-scope exit belongs to one unit's document or to a pod that compiles into socket blocks.
- Whether a sizer's own numbers may be calibrated from the unit's record, and with which minimum count.
- Where risk and sizing lives, on the unit, in the pod or central, and the Book against the BMS. His statements still conflict (PACK §2.10), and the socket presumes no answer.
