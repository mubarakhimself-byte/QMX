# Final fix round: what `CHECK.md` found and what changed

7 Nov 2026. Every blocker and should-fix of `CHECK.md`, in `SPINE.md`, `SOLUTION.md`, `WALKS.md` and `OPEN.md`. Code lines were re-read at `D:\QMX-worktrees\bld-repair-24` (`351e7521`, unchanged). AD ids are stable; AD-23, AD-24 and AD-25 are new.

**Nothing here ran.** These are design fixes. Each one's proof is a K9 test owed by the slice named, on top of the runs `CHECK.md` already did. `lint_spine.py` reports 0 findings. The reviewer subagents the skill asks for were not run, because the brief forbids subagents; `CHECK.md` is the independent review.

**Result:** 9 of 9 blockers closed in contract, slice and test. 17 of 17 should-fixes applied, none rejected; S8 and S14 changed form, as noted. PRs go from 44 to 52. Stop points move: A about PR 18, B about PR 37, C about PR 50.

## Blockers

| # | Finding | Root cause | Contract and where | Slice | Acceptance test |
|---|---|---|---|---|---|
| B1 | One raising block stops exits, in its unit and every unit after it | No guard per unit in `_drive` (`runtime.py:3013-3018`); logic runs before exits in one call (`unit.py:530-536`) | **New AD-23:** phases in `_Run.step`, plain `try` per unit, `Fault` on `UnitStep`, entries off and back by rule, phase stays `TRADING`, `close_scope` port last. SPINE section 3; AD-9; WALKS 11; SOLUTION "A block that raises" | 3 | K9 2: raising logic slot and raising sizer, units behind them, 12 bars, every unit driven, zero heals, exits fire |
| B2 | A parked entry crossing a bar sends twice; it has no lifetime | `own_position` reads `None` while parked, so `_Run.entries` mints again (`unit.py:746-749`); `not_before` is an earliest time and never expires | **AD-17:** `Parked(expires_at)` beside `Unknown`; `parked:<market>` surface; `suppressed_limit` on open plus parked; expiry at start of pass 1 writes `Skip`, `budget_expired`. SPINE section 3; OPEN row 19 | 11 | K9 11: one signal, one send, one position in venue and handler; expiry row |
| B3 | From zero, nothing reaches paper | The table has no draft-to-paper row (`machine.py:105-117`), and `TESTED` needs a judge `pass` | **New AD-24:** `Transition(DRAFT, PAPER, HIS_CLICK)`; `promote.py:565-578` already demands G's safety half on every lane. SPINE section 6; WALKS 1. The first start script's header changes too | 5 | K9 7, K7 with no judge run reaches a filled paper entry |
| B4 | One account's feed builds one bar size | `_host` compares stream to feed exactly (`runtime.py:2774`); stream ids are market ids (`unit_handler.py:261`) | **New AD-25:** one base bar, labelled default 60 s; pure `roll_up`; `(stream, market)` keys; `plan.streams` with a `primary`. Module map; WALKS 1, 2 | 9 | K9 17: 1m, 5m and 15m units trade on one account; no look-ahead; rolled bars match direct bars |
| B5 | USDJPY risks the figure in JPY | `value_per_point` is in quote currency, and neither the block nor `to_quantity` has a rate | **AD-10, section 3:** `rate: Fact` on `to_quantity`; `conversions` on the record; host subscribes; named skips; exits never read it; `_money` stamps the rate; `_account()` converts; QMB reads replay. **`fixed-fraction-at-stop@2` answers money at risk, because `Size(lots)` would have skipped the converter and left the fault in place** | 2 | K9 16: known answers on four markets; stale rate skips; exit still closes; hosts agree |
| B6 | AD-21's diagram breaks a package rule | Arrow `qmf-data --> qml`; `DecisionRow` placed in `qmf-data` | **AD-21:** arrow removed, data goes to hosts only; shapes in `qml` or `qmf-risk`; `fold` and `explain_size` take plain mappings. Section 3 heading; module map | 1 onward | `tools/tests/test_workspace_structure.py:138`, already there, keeps failing any such import |
| B7 | Slice 4 depends on slice 6 | Fold placed after its first reader | **Section 10:** `fold.py` at unit scope moved to slice 4, slice 6 uses it. Soft dependency named: account halts labelled one-unit until slice 8 re-tests them | 4, 8 | K9 9 in slice 4; two-unit re-test in slice 8 |
| B8 | AD-1 and AD-17 disagree on when size is computed | AD-1 said right after `on_instant` | **AD-1:** pass 2, with the interim call site stated until slice 11. **Section 12:** slice 11's half PR removed; switch price now about 4 to 6 PRs, OPEN row 1 | 2, 11 | K9 13 tape, exits-first test |
| B9 | A stopless entry is still closed | Each reader treats a missing stop as a fault, and "six places" missed seven | **AD-22:** retitled, a thirteen-row table with file and line, `stop_kind: none_declared` asked by each reader; UNKNOWN venue answer named with a fallback. Section 5 PH 11; WALKS 2; SOLUTION; OPEN rows 24 and Repair | 11 | K9 12: held N bars on the fake broker, through a restart, no `protection_escalation`, closed by its own cut |

## Self-configuration, end to end

`CHECK.md`'s "Does a number really move" found five breaks. **AD-14** now has six numbered steps; **K9 test 15** proves them for one sizing number (`fraction`) and one exit number (`multiple`), in **slice 7**.

| Break | Closed by |
|---|---|
| Risk numbers refuse the engine (`motion_not_built`) | `_bound_on` and stamp search widened |
| Compiled but doesn't move: no stamp, `engine.py:122` skips every trade | Stamp `number:<name>` from `numbers_in_force`; trade row carries it from slice 7 |
| The shipped sizer ignores a moved value (`block.py:24`) | `@2` in slice 2; exits in slice 3. The same fault sits in `target-r-multiple`, `time-exit-bars` and `swing-stop-buffer`, so all are fixed and K9 6 fails any block that repeats it |
| No shipped rule block for a risk number | `own-r-step@1`, labelled placeholder |
| `flat` across all markets starves a cadence | No flat needed for a sizer or exit number, since positions keep `numbers_at_entry`; logic numbers read flat per market |
| Restart loses `SlowState.read` | `_OwnJournal` seeded from trade rows; watermark drops what was read |
| No receipt | `numbers_in_force` with the calibration row id; `explain_size` prints it; the close row names `numbers_at_entry` |

## Should-fixes

| # | Finding | Decision | What changed and where | Slice |
|---|---|---|---|---|
| S1 | The budget misses what takes the time | Applied | AD-17: start an entry only if its worst case fits; `watch.began` beat per exit send and entry; refused at start if a worst case exceeds the limit. WALKS 8 corrected | 11 |
| S2 | Core rows with no slice | Applied | Section 4 rebuilt, one row per core row with a Slice column: I17, K5, R8, I7, I9 named. R8's arms and part of I7 marked additive with the reason | Each named |
| S3 | Placement test against walk 3 | Applied, by narrowing the fact | New `own.open_risk_by_bet_key`: own facts, so the unit chain is right. Cross-unit stays the group cap. WALKS 3, section 3 | 9 |
| S4 | Partition holes | Applied | AD-2: anything not named as risk is logic; `reads` in a logic slot is logic; exit `stage_values` make the selector logic | 1, 13 |
| S5 | "Once" against "each changed decision" | Applied | AD-19, section 3 stack, section 7 versions, SOLUTION: free bumps until first live deploy, one per changed decision | 1 onward |
| S6 | Tape through four drivers can't be built | Applied | Section 6, K9 13, S15 row: three now, Lab joins when it exists; section 11 row | 2, 11 |
| S7 | "Only five things refuse" | Applied | AD-20 table with each refusal's way out; veto rows gain `enabled`. SOLUTION corrected | 11 |
| S8 | Fake broker isn't a product path | Applied, one of two options | `practice` venue kind in slice 5, chosen over "day one ends at backtest" because M49 asks for a stranger's use. Section 6, module map. Release owner: OPEN 8b, his call with a default | 5 |
| S9 | Slice 9 too small, no multi-position contract | Applied | AD-25 positions; slice 9 split into 4 named PRs | 9 |
| S10 | `_close_scope` out of reach from QML | Applied | `Fault` and `HostPort.close_scope`; AD-13, AD-23, section 3 | 3 |
| S11 | Node links in `qml` | Applied | AD-9: runner and protocol in `qml`, links in `qmn/app/node_links.py`, injected. Module map | 11 |
| S12 | Self-configuration gaps | Applied | See above | 7 |
| S13 | Contract words diverge | Applied | AD-9 `block`, `wait`; AD-16 sticker `flatten`; AD-5 `logic_touch`; AD-7 stage card | 10, 11, 13 |
| S14 | A hung block burns a thread | Applied, changed | One shared pool; `link_hung` marks a restart at the next point `safe_to_restart` allows, not "when flat", since 200 units may never all be flat. AD-9, WALKS 11. The bar-step wrap now has a slice instead of "once tested" | 10 |
| S15 | Short stops read bid bars | Applied | AD-13: closing quote's bars; contract comment; a changed decision, so it bumps | 3 |
| S16 | Fleet watch isn't a mini app | Applied | Section 8, module map, slice 15: `fleet-watch` through the manifest | 15 |
| S17 | His signature has no column | Applied | Section 10 preamble: one signed release per stop point; OPEN 8a. UNKNOWN gate named | Each stop point |

## Other findings in `CHECK.md`

| Finding | Decision |
|---|---|
| FUNNEL 3.8: second deployment of one version lost its seat | Fixed: section 4's S14 row keeps a deployment key; slice 13 tests it |
| Part C items not holding (H-01, H-06, H-08, H-17, H-43; H-21, H-33; H-30, H-31; H-50; H-98) | Closed through the fixes above, except the installer in H-01 and H-43's stranger path, which stay with release. SOLUTION says so |
| Compile pool shares the interpreter lock during a roll | Named in WALKS 8, unmeasured |
| "Too much machine": group `order` block, reservations as a type, proposal tape, `run_budgeted` on every row, "The pieces" | Not changed in the fix round; the lead then trimmed them, see "The lead's trims" below |
| Older list: breakeven, System 1, multiple Books, N8N or white label | Not touched; `CHECK.md` did not call them faults |

## Left open, stated

Whether cTrader takes a no-stop market order (OPEN 24). Real send times and real 200-unit throughput (OPEN 9, 20). The base bar's real feed load (OPEN 23). Whether a judge `fail` should allow his click to paper, handed to methodology with the default `PARKED` stays parked. PR counts remain estimates.

## The lead's trims, 7 Nov (`RUN.md` decisions log, on `CHECK.md`'s "Too much machine")

Applied to `SPINE.md` and `SOLUTION.md`. AD ids are unchanged. `WALKS.md` and `OPEN.md` were corrected afterwards by `build/FINAL-CHECK.md` (OPEN rows 14, 21 and 22, WALKS 3, 8, 11 and 13). Older rows above still describe the design before these trims; `SPINE.md` wins.

| Trim | What changed and where | Slice | Cost, named |
|---|---|---|---|
| The group `order` block goes, a `rank` field stays | AD-8, AD-17, section 3 `Group`, module map, slice 12, section 11 row, section 12 | 12 | "Best of those firing" waits for an additive slot |
| Reservations are not a type | AD-8 rule "an unknown outcome keeps its room"; removed from AD-9, section 3, section 6, section 7, section 9, slice 12, section 12; section 11 row | 12 | None on one thread; reopens if caps ever run off it |
| The proposal tape goes to methodology, row shape reserved | AD-18, section 3 rows, PH 26, slice 15, section 11 row | 15 | The fixed-size rerun and the size search are methodology's. K9 13's conformance tape is a test fixture and stays |
| The Lab driver waits until a Lab exists | Already so since S6; no change | none | None |
| `run_budgeted` is not on every row | AD-9 retitled, a plain `try` on every block, time budget on the entries pass only (AD-17), hung-link protection deferred with the worker process; section 3, conventions, stack, section 4 S6, module map, K9 2, slice 10, section 11, section 13 | 3, 10, 11 | **Risk named in AD-9:** a block that never returns stalls that node's thread, exits included, until `StuckWatch` restarts it at 30 s. Venue stops hold. FUNNEL S6's "a hung link refuses entries only" is not met; `CHECK` said this one needed the lead's call, and he made it |
| `SOLUTION.md`'s "The pieces" stays | No change, for his reading | none | None |

The PR count in SPINE section 10 now points at `round-2/build/PLAN.md`: 69 PRs, with stop points at RC-20, RC-48 and RC-66. SOLUTION's and section 10's slice numbers still hold.
