# Every place risk and sizing plugs into Part A, with today's placeholder

Part A, 31 Oct 2026, for the risk-and-sizing session. Nothing here designs exit or sizing maths (ledger R-01, R-04; his words: "risk and sizing, that's already out of scope for now, but it's part of the unit" (T3:904)). The pack of his own words is `RISK-SIZING-PACK.md`; the Level 0 list is `level-0/ARCHITECTURE-SPINE.md` "For the risk session". Slot contracts: `CONTRACTS.md` §4.3.

## 1. The plug-in points

| Point | Where in Part A | Today's placeholder | What the risk session decides |
| --- | --- | --- | --- |
| The sizer slot | the unit document's `sizer` binding; contract §4.3 | `fixed-fraction-at-stop@1`: 0.5% of equity at risk at the stop, rounded down to the lot step, skipped with a reason below the minimum lot | the sizing method, its inputs, house money, size growing back, Kelly ceilings |
| The exit set, at position, unit and account scope | `exit_set` bindings; contract §4.3 | `swing-stop-buffer@1` (beyond the last swing point plus 0.02% of price), `target-r-multiple@1` (2R), `time-exit-bars@1` (48 bars) | exit families, stops, time-varying targets, give-back, probability exits |
| Halts, at three scopes | `halts` bindings | empty (a warning on the card) | daily loss limits, streak halts, equity kill switches, which halts flatten and which stop entries |
| The cross-unit hook before every order | called by the host (QMB, the node); contract §4.3 | passes every order | correlation control, the book or pod's share, same-bet limits |
| Which numbers move, and how fast | `NumberSpec.kind` and `motion` (AD-103) | no risk number moves; every placeholder number is `fixed` | which sizing and exit numbers follow the market and which follow the record |
| Moved values and open positions | `applies_to_open_positions` (default false) | false | whether a moved number may change an open trade's exits |
| A unit with no price stop | `protection.stop: none_declared` in CT-23 format 3 | R is undefined and results are flagged | whether such units are allowed and how they are judged (UT-08) |
| Stop amendments | `amend_protection` in CT-23 format 3 | may tighten, never widen | whether widening is ever allowed |
| Partial closes | `close_partial` in CT-23 format 3 | available to exit blocks; the placeholders do not use it | scale-out ladders |
| Placeholder labels on every intent and trade | `placeholder_labels` | the five dummy bindings above | the rip-out: `tools/qml/placeholders.py` lists every published unit and binding using a placeholder |
| Inputs a sizer may read | contract §4.3 | entry and stop prices, instrument facts, account equity and balance, open risk, the unit's own record in R, market statistics, his limits | which ones its method uses |
| Recording for later replay | decision rows stamp numbers in force; Part B's trade rows carry equity, session, streak | as built by Part B | replaying the old "radioactive" sizing on recorded trades |
| The lifecycle's one automatic move | `qml.lifecycle`: live or paper to stopped by a risk rule | only an explicit halt block's `flatten` or `no_new_entries` counts | which rules count, and whether a stop may land a unit on paper directly |
| A risk-session block's contract tests | `qml/tests/test_socket_contracts.py` (slice A15) | the placeholders pass them | its blocks must pass them too |

## 2. Questions the session meets in Part A's code (pointers, not answers)

1. Whether the cross-unit hook stays a host call or becomes a slot in the document.
2. Whether an account-scope exit belongs to one unit's document or to a pod that compiles into socket blocks (Lab AD-10 to AD-12, still unbuilt).
3. Whether a sizer's own numbers may be calibrated from the unit's record, and with which minimum count.
4. Netting accounts: on a netting account or a Hyperliquid subaccount, at most one unit per symbol, refused at deploy by Part C and labelled a placeholder, because per-unit broker stops cannot sit on one netted position (L0 risk table, R1 settlement CF-7); a hedging account keeps one virtual position per unit; the rule for conflicts is the session's.
