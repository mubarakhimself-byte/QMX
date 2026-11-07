# The fold's walks, against `SPINE.md` and the code at `D:\QMX-worktrees\bld-repair-24` (`351e7521`)

The 13 walks of `round-2/arch/ARENA-BRIEF.md`. **Verdict words.** HOLDS: works in this shape. STRAINS: works, at a cost named. FAILS: this shape can't do it. MISSING: needs something outside this design. Where the fold's verdict differs from V1's (`V1-unit-owns/WALKS.md`) or from COMPARE §3, it says so and names the graft. Nothing here ran; mechanism checks are COMPARE's, V1's and `CHECK.md`'s. Verdicts are on the design after `FIXES.md`; each fix's proof is a K9 test owed by its slice, not yet a result.

## 1. A newcomer installs and gets a unit on paper

1. Install and first start: not this design's. E5 G1 to G3 stand (no installer a stranger can run; the desktop app it hands over to is unfound). MISSING, release lane.
2. Picks `canary`. A complete document appears; no pod, no group, no Lab.
3. Check and compile: warnings only, in plain words; every number labelled.
4. Instrument records: the template ships records for its markets, labelled `source: shipped`, so a backtest runs before a broker exists (closes E5 G8 if `unit_check` accepts them; `[ASSUMPTION]`).
5. Backtest on the shipped practice month (RC-17); G record on the logic fingerprint. No judge run; a judge's `too_thin` would move nothing anyway.
6. His click: `DRAFT -> PAPER` on G's safety half (AD-24). Before this row the real `fold` answered `not_in_table` (`CHECK` B3).
7. Paper on the `practice` venue on day one: a production builder over `ConformanceAccount` and shipped bars (slice 5), no broker. On cTrader after Spotware's approval of about a day (`connect_node.py:8-9`). `canary` reads 15-minute bars, and slice 9's roll-up (AD-25) opens every other bar size.
8. SPINE section 6 walks the rest; K7 runs it in CI from zero.

**Verdict: HOLDS** for the unit, from the design's side; the installer stays MISSING. The newcomer meets one document and never meets a pod. **Strain, unchanged from V1:** someone who later wants one edit across several units must learn the recipe; the drift report (G10) at least tells them when members have wandered from it.

## 2. A gold scalper with fast invalidation and no fixed stop

1. Template `scalper-mr`, market gold. Exit stack: `fast-invalidation-cut`, time exit. Sizer: `Amount(money_at_risk, basis="tail_budget")`.
2. The declared basis passes all thirteen places in AD-22's table: compile, `enter`, handler and node entry, the veto, `_protected`, **each tick's `_restore_stops` (`runtime.py:2358-2386`), which `CHECK` B9 ran and which closed the position**, `adopt`, the reconcile, `safe_to_restart`, `_money` and `_close`, the venue adapter, and the other order paths. The send row's `stop_kind: none_declared` is what each one asks.
   A 1-minute feed is no longer an obstacle: `scalper-mr`'s bars roll up from the base bar (AD-25).
3. The converter divides money at risk by the declared distance. The trade row marks the basis.
4. Cold: the cut uses a fixed labelled distance until N winners, then the winners' MAE.

**Verdict: STRAINS, in three places.** `CHECK` found this walk FAILED as first written (B9, B4); the fixes bring it here.
- **"Fast" is capped by the bar.** A unit steps on closed bars (`compiler.py:976-981`). On 1m bars the cut acts once a minute. The exit answer is shaped so a quote clock can feed it later (AD-13), but the stream widening is deferred. No shape escapes this.
- **Thirteen places change for no-stop.** That is honest about the cost, and the shipped default stays a far disaster stop with the cut in front; the true no-stop form is expressible and warned. K9 test 12 holds one for N bars and through a restart.
- **UNKNOWN whether cTrader accepts a no-stop market order.** A demo probe in R24. If it refuses, capability refuses this form at compile on that venue, by name.

## 3. An ORB unit across several opens, one bet counted once

1. One unit, `orb` variant of `intraday-trend`. `sessions` lists London and New York opens (S9, slice 9). `position_limit` per open (S17). Markets: index and gold.
2. Each intent carries bet key `family:session` and driver tags (I9).
3. A second open fires while the first is held: the unit chain's own cap reads `own.open_risk_by_bet_key`, which is this unit's own facts and so belongs in the unit chain by AD-9's test, and shrinks or refuses by the row. Same bet, counted once.
4. Several ORB units in one family: the bet key crosses units, so the group cap counts it in the node chain, in pass 2's order, and an unknown outcome keeps its room (AD-8), so two units at one bell cannot both take the last room.
5. Tolerates `open`, so an `open` sticker doesn't block it.

**Verdict: HOLDS** inside one unit, and for many units given a group. **Strain, smaller than V1's:** at the same bell the group's `rank` decides who gets the room, so the first in rank takes it. "Take the best of those firing this bar" waits for an additive order slot (SPINE section 11). COMPARE §3 gave V1 "Holds; first in rank takes the room"; the fold is the same.

## 4. A futures week with the copilot from papers and videos, ending in units with their own sizing

Assume the route exists.

1. A desk mini app, jobs and agents run for a week. Each output lands in the Library by the `library-items` lander (slice 14).
2. The copilot drafts blocks and saves them through `blocks_save` with a contract test. Mini and micro are two instrument rows.
3. The copilot writes each unit with `unit_new`: exits, logic and its own risk section in the document. "Units with their own sizing" is literally the document.
4. A pod draft for the family is optional; `expand` stamps it if used. A group for the family's money and parent limit is one document with a tag selector (G8), so joining a new unit to the family is a tag on the unit, not a group edit.
5. Paper on his yes; each unit has its G record.

**What else is missing, beyond the route:** `roll` compiled and the futures feed (`roll` stays refused until a route exists, Q2); a copilot that takes raw video (M51) and the methodology behind it; the agentic upgrade; volume on bars if any block wants it (Q2).

**Verdict: HOLDS** on this design's part. **MISSING** the route, the methodology, the agent harness.

## 5. A very aggressive setup with few units on one basket, then a stage change as capital grows

1. Recipe `best-basket-press`: sizer at a large fraction or a Kelly block; press modifier on; controls empty except the kill switch's effect; stages `small` and `grown`, each with its own sizer, modifiers and limits; selector `group.money`; anchor day boundary; hysteresis. Warned and graded; never refused (V9).
2. Group with no parent limit, or a loose one; its limits are facts, so loosening later is one click on the group row, no plan.
3. Few units stamped. Their logic is untouched. One click covers plan and every stage.
4. Stage move: at the anchor the selector crosses the line. Each member reads `group.money`, picks the stage's compiled sizer, writes `stage_move`. No new version, no recompile, no record loss. Going up: a card by template default; `rule` is one field away.
5. After a restart that crosses the anchor, the stage is re-derived once, and a raise earned before the restart waits for the next anchor (G12). A cut stands.

**Verdict: HOLDS** for sizing rows, as V1. **Strains:**
- A stage nobody declared is a pod edit, a plan and a click. Acceptable.
- A stage that should change an exit **block**, or an exit number not declared at birth, needs a new logic fingerprint per member, a G run and a drain of open positions. F5 A's cost; it stays.
- Where the aggressive setup's limit is a group number rather than a stage row, the live-fact path (G6) makes it one click with no plan at all; where it is which sizer runs, the stage row is needed. Builders must know which is which: AD-2's three tiers say it.

## 6. A unit made in the Lab, one from a workflow, one from a mini app

- **Lab.** No Lab package exists (`qmx_control/lab.py` docstring). A Lab pod is a `qmx.pod/1`; the Lab previews `expand(sample, pod)` and drives the hosted unit on replay through the same `AdmitPort` and `FactSource` seams (S15), so the size trail on screen is the decision row. It emits a finished unit document.
- **Workflow.** `d3`, `l1`, `b-build-and-prove` write a draft through `unit_new`. Same check, same G.
- **Mini app.** The lander drops a `unit` and its blocks at publish. Its sizer is its own; it may list `risk_locks`.

All three have the same document and the same path (M49). A block the node can't run shows as an unmet need by name.

**Verdict: HOLDS.** **Strain:** a unit with `risk_locks` joining a pod makes a mixed pod. The drift report (G10) and the plan's `locked` outcome make the card say "12 of 14 follow the recipe", so the small lie V1 worried about is shown rather than hidden.

## 7. A mini app feeding another, and a desk publishing a reading a unit reads

1. App to app: roads A and B, built (`qmx_apps/artifacts.py`, `triggers/event.py`).
2. The desk publishes a reading; the host stamps `source: app:<id>`, with `valid_until` and named inputs.
3. `feed_relay.py` carries it to the node (no production importer today; wired in slice 14). Its 5-second pass is fine for slow readings.
4. The unit's `reads` pins publisher, fallback, stale limit. A block reads `reading:<id>:<market>` with its age.
5. The desk stops: the reading ages; the fallback runs; the unit trades home markets or stands aside as declared. The trade row shows source, age, version.

**Verdict: HOLDS.** **Strain, as V1:** adding a `reads` row is a risk-section edit, so a new reading for 200 units is a plan and a click. A reading used by a logic slot is a logic edit and costs G.

## 8. 200 units: one pod edit, the fleet watch, herding on one volatility shift, one node's limits

**One pod edit.** `roll_plan` stamps every member (200 expansions took 0.54 s in V1's probe) and compiles each (746 ms median, about 150 s on one worker; off the node this can run on several). The plan shows counts by outcome and diffs. One click. The node compiles 200 on its one worker behind the tick, then one tick flips all with `move_risk`; open positions keep exits because `opened_by` is the logic fingerprint. **Cost unchanged from V1:** 200 new document versions and two compile rounds per edit. **Cheaper now for the common case:** a limit edit (parent limit, day stop line, share) is a group fact (G6), one click, no plan, no compile. Only a change of which blocks run costs the plan.

**The fleet watch.** Scripted `fleet-fold` reading the fold: one ranked row per unit, two lists, one incident one card, no agent; decay card off (E5 1.1: about 91 a night otherwise). The app read door widens past `market` (`supervisor.py:891`). Rows carry family id, type tag, pod, drift. **HOLDS.**

**Herding on one volatility shift.** Each unit's numbers move by themselves. Filters: E5 measured 21% of units moving at peak with the built engine (MODEL; the mechanism behaved as described, nothing more). Sizes: untested. A `scaled` size on a volatility fact cuts 200 units in the same bar, probably right. A press rising together is caught only by the group's total-risk cap; the fold reports a `move_share`. **STRAINS.**

**One node's limits.** QML step about 55 to 60 ms for 200 units on 2 markets (V1's probe, COMPARE's rerun). **The real limit is order sends:** `client.send` holds a lock and waits up to 5 s (`ctrader_account.py:110, 679`). **Changed from V1 by G1 and F1/F2:** exits all go in pass 1 before any entry, so an entry's wait never delays another unit's exit. The first draft said a budget check meant a long bell could not trip the 30 s watchdog (`healing.py:64`); `CHECK` S1 ran it and that was false: one entry takes 26 s at the venue's worst, and pass 1 had no budget, so 6 closes at the 5 s wait used all 30 s. Now pass 2 starts an entry only if its worst case fits, and each exit send and finished entry resets the watchdog as a progress beat, so it times one stuck step. Stops at the venue hold through any restart. Leftover entries carry to the next tick and re-check caps on fresh facts. **Not fixed:** exits are serial too (F10), and 200 positions closing one venue call at a time is still 200 round trips; the meter stays, and sends off the thread reopen if measured. A parked entry no longer reads "warming up" (F7), can't be minted twice (B2), and expires at its market's next bar.

**Verdict: STRAINS,** less than V1 at the bell (COMPARE gave V1 "Strains: serial sends, first-come caps"). What remains: serial sends, measured only after the demo; first in rank takes the room until an order slot is added; the pod edit's bulk versions; **a compile pool in the same process shares the interpreter lock with the node thread during a roll, not measured (`CHECK`).**

## 9. Swapping a placeholder on a unit with a record and an open position

**Sizer, a risk-section swap: HOLDS.** Forwarding map `fixed-fraction-at-stop@1 -> real@1` with a parameter transform (R17). New version, plan of one, his click. G record stays valid on the logic fingerprint. `move_risk`: the open position keeps exits and R; the next entry uses the new sizer. The logic record continues; the money record starts a new line. `r_after_costs` gaining costs is a declared change because calibrated numbers read it.

**Exit placeholder, a logic-section swap: STRAINS.** New logic fingerprint, a G run, a counted try. It can't be in place: the old deployment drains (`withdrawn` then flat, `runtime.py:2746-2748`), the new one enters under `succeeds` on the deployment, on a hedging account only (`_netted` refuses two on a netting symbol, `runtime.py:2888-2906`). Before the first deployment this is free, which is why slice 17 precedes the first live deploy.

## 10. A brand-new brake, a brand-new instrument class, a new sizing base

- **Brake.** One folder and a row (section 7). If it reads a fact the host doesn't provide: one registry row and two adapters, said plainly. If it reads several units: a group cap with a `group_run` test. Account-wide atomic: it runs in the node chain on the one thread, so any Library brake may be atomic at the account; this is where the fold beats V3's "stdlib only in the boundary". **HOLDS.**
- **Instrument class.** Rows and keys; `instrument_class` is read in two files today (E5 4.2); a test fails on branching in the money path. **HOLDS** for CFD-like; **MISSING** for a venue with no adapter.
- **Sizing base.** A block answering `Amount`. Notional or a fixed contract count is a kind, not a socket change. **HOLDS.**

Promise check: "one folder, zero core edits" rests on the Library path, UNKNOWN until slice 14 traces it; a stdlib block bumps the money app and needs his signature.

## 11. The MIS down mid-session; a guard or chain failure with open positions; a hung stage; a restart past an anchor

- **MIS down.** Readings age; each `reads` row takes its fallback; home markets. A sticker publisher down: `fail` row, a card, `prefer_not`. No shipped template needs the MIS. **HOLDS.**
- **A raising block in a logic slot or the sizer (`CHECK` B1, which found this walk FAILED).** AD-23's plain `try`s: that market takes no entry, `exits` still runs, the unit's entries go off with a row and a card, the next unit runs, no heal. K9 test 2 runs it for 12 bars.
- **Chain failure with open positions.** A raising link: a plain `try` refuses that entry with `link_fault`, stands the link's scope down, writes a row; exits were already sent in pass 1 and skip both chains; the import test proves exit code cannot reach the chain (G3). A refused frontier no longer sets STOPPED and ends exits (F3): the fault is caught inside the chain and never returns to `close_frontier`. A faulty exit block: next rank, then a `Fault` on the step and the host's `close_scope` port. **HOLDS.**
- **A hung stage.** **STRAINS, as V1.** By the lead's trim (AD-9) no wrapper answers a hang. A block that never returns stalls that node's thread, exits included, until `StuckWatch` (`healing.py:64`, `os._exit`) acts at 30 s; the supervisor restarts, adoption brings positions back, and venue-resident stops protect in the gap. The same block can hang again until its owner stands it down. V3's worker process is the named next step if a hang is seen.
- **Restart past an anchor.** Snapshot as a cache, then the catch-up rule: anchors settled once by a pure anchor id, stickers expired, stage selector re-read, control words rebuilt from `risk_event` and restore rows (G9), group ledger rebuilt from member journals and broker deals; until done the group cap reads UNKNOWN and refuses entries, exits free. **Cuts stand; raises wait one anchor** (G12). Each section judged by its own fingerprint. Only `risk_stop` has a restart test today; each state needs one. **HOLDS on paper; tests owed.**

## 12. House money, reverse house money and a press after wins, on and off, per pod

1. One rule, one ledger: `cushion-rule` modifier reading profit since an anchor. Fixed anchor presses and brakes; running peak only brakes.
2. Anchor, clock and scope are rows. Scope `unit` reads `own.*`; scope `group` reads `group.cushion` from the ledger.
3. Press after wins: a `press-gate` block in front, or a persistence press modifier. Raises read `group.raise_ok`.
4. **On and off per pod, changed from V1:** the recipe's modifier row may bind `enabled` to a group fact (AD-8). Flipping that fact is one click on the group row and reaches every member at its next decision, with no plan. Where no group exists, or the recipe did not bind `enabled`, turning it off is a plan across members as in V1.
5. Cold: at the anchor profit is zero, factor 1. Scalper template ships it on, day anchor, because he asked (M5, M39); intraday off.

**Verdict: HOLDS.** COMPARE gave V1 "Holds; flip is a plan" and V4 "Holds best: one live fact flips it"; the fold takes V4's answer through one optional field. **Strain:** a Pod 5-style slot ledger inherited on rotation needs a ledger key by tag; expressible, not pretty.

## 13. Backtest against live on the same unit: where can they differ?

Same arithmetic by construction: the same `HostedUnit`, `price` and handler in both hosts, through the same `AdmitPort`. Allowed differences: fills, costs, latency. Others, stated:

| Where | Backtest | Live | Status |
|---|---|---|---|
| A target on a wicked bar | Bar check | Node closes it (`runtime.py:1849-1857`) | F5 A's cost; waits on R24 |
| Group caps | Solo run sees only itself (`group: none`); `group_run` sees a chosen set in the node's order | All real members | **This shape's own gap,** stamped on the run; `group_run` lands in slice 12 |
| Order at a bell | Declared order in `group_run`, no budget | Same order, a time budget, leftovers to the next tick | Latency; it moves fills; QMB may model the budget as a setting |
| Entry timing | Rests for the next bar's open | Sent in pass 2 at bar close | Built; allowed as fills |
| Equity and cash | Handler's cash port | Live surface after slice 8 | Facts differ, arithmetic doesn't |
| Readings | As-of tape (R13) | Live, with age | Must be as-of or it flatters |
| Stickers | Calendar tape | Real table | Same record |
| Partials | Filled | Refused until step 3 (`runtime.py:1807-1808`) | Compile refuses by venue capability |
| Costs | Stated profile | Measured cells | Two residuals kept apart |
| Restart, heal | None | Real | Only on the node |

**Verdict: STRAINS** only on group caps, where one-unit backtests do not see the book, on wicks, and now on the pass-2 budget, which QMB does not model unless told to. A size search that replays proposals is methodology's (AD-18); the QMB rerun is the evidence.

## Summary against COMPARE §3

| # | Walk | V1 (COMPARE) | The fold | What changed it |
|---|---|---|---|---|
| 1 | Newcomer | Holds | Holds; installer missing | Shipped records (assumption); `DRAFT -> PAPER`; `practice` venue |
| 2 | Gold scalper, no stop | Strains | Strains, three places | F6, B9: thirteen places named; B4: roll-up |
| 3 | ORB, one bet | Holds; first in rank | Holds; first in rank | An unknown outcome keeps its room; `rank`; own bet-key fact |
| 4 | Futures week | Holds best | Holds | G8 tag membership |
| 5 | Aggressive, stage change | Holds | Holds | G6: limit edits need no plan |
| 6 | Lab, workflow, mini app | Holds | Holds | G10: mixed pod shown |
| 7 | App feeds app | Holds | Holds | None |
| 8 | 200 units | Strains | Strains less | G1 budget with beats, G6 live limits, F7 and B2 parked fix |
| 9 | Swap with open trade | Sizer holds, exit strains | Same | `succeeds` on the deployment |
| 10 | New brake, class, base | Holds | Holds | Atomic account brake from any Library block |
| 11 | MIS down, fault, hang, restart | Holds except hang: strains hard | Holds; hang strains | AD-23 fault wall, plain `try`, G3 import test, G9, G12 |
| 12 | House money per pod | Holds; flip is a plan | Holds; one fact | `enabled` by fact |
| 13 | Backtest vs live | Strains on group caps, wicks | Same, plus the budget | `group_run` in slice 12 |
