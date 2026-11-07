# V1 walks, against `SPINE.md` and the code at `D:\QMX-worktrees\bld-repair-24`

**Verdict words.** HOLDS: works in this shape. STRAINS: works, at a cost named. FAILS: this shape can't do it. MISSING: needs something outside this design. Probe results are `D:\Temp\v1-arch\out-probe.txt`, mechanisms only.

## 1. A newcomer installs and gets a unit on paper

1. Install and first start: not this design's. `E5` G1 to G3 stand: no installer a stranger can run; the desktop app it hands over to is unfound. MISSING, release lane.
2. Picks `canary` or `scalper-mr`. A complete document appears; no pod, no group, no Lab (V7).
3. Check and compile: warnings only, in plain words. Numbers carry labels.
4. Instrument records need a bound account today (`E5` G8, UNKNOWN whether a backtest can run first). If the answer is no, shipped records for the template's markets are rows, not a core change.
5. Backtest on synthetic bars, G record on the logic fingerprint.
6. Paper, on the fake broker on day one; on cTrader after the approval of about a day (`connect_node.py:8-9`).
7. SPINE section 5 walks the rest. K7 runs it in CI from zero.

**Verdict: HOLDS** for the unit. This shape has the shortest path, because the newcomer meets one document and never meets a pod. **Strain:** a person who later wants one edit across several units must learn the recipe; nothing prepares them.

## 2. A gold scalper with fast invalidation and no fixed stop

1. Template `scalper-mr`, market gold. Exit stack: `fast-invalidation-cut`, time exit. Sizer: `Amount(money_at_risk, basis="tail_budget")`.
2. Compile: `stop_not_built` (`compiler.py:500-506`) lifts when a declared basis exists. `enter` must stop skipping on no stop (`unit.py:764-766`).
3. Wire: `none_declared` already round-trips (`unit_intent.py:69-72`). The handler and node must stop reading the stop as a `Decimal` (`unit_handler.py:560`, `runtime.py:1065`).
4. Node chain veto: accepts the declared no-stop basis where `require_venue_resident_protective_stop` would refuse (`runtime.py:1102-1106`). Warned in large type.
5. The converter divides money at risk by the declared distance. The R basis is on the row; trade rows mark it.
6. Cold: the cut uses a fixed labelled distance until N winners, then the winners' MAE. C1's warning is on the block.

**Verdict: STRAINS, in two places.**
- **"Fast" is capped by the bar.** A unit steps on closed bars (`input_not_built`, `compiler.py:976-981`). On 1m bars the cut acts once a minute and fills at the next open. Quote-clock exits need the stream input to widen, which FUNNEL S17 doesn't name. No shape escapes this; here it costs a socket widening in the unit.
- **Four places change for no-stop,** and the node gate exists to stop exactly this. A far disaster stop with the cut in front is the practical template default; the true no-stop form is expressible and warned.

## 3. An ORB unit across several opens, one bet counted once

1. One unit, `orb` template. `sessions` lists London and New York opens (S9). `position_limit` per open (S17). Markets: index and gold.
2. Each intent carries bet key `family:session` and driver tags (I9).
3. A second open fires while the first is held: the unit chain's own cap reads `account.open_risk_by_bet_key` and shrinks or refuses by the row. Same bet, counted once.
4. Several ORB units in one family: the bet key crosses units, so the group cap counts it at the node chain, in the outbox's order. If no group exists, the same-bet check across units has no home, and the fold only reports it.
5. Records split by session and slice (R2). Tolerates `open`, so an `open` sticker doesn't block it.

**Verdict: HOLDS** inside one unit, and for many units given a group. **Strain:** with several units firing at the same bell, whichever is first in rank takes the cap's room; a later, better signal is refused. See walk 8.

## 4. A futures week with the copilot from papers and videos, ending in units with their own sizing

Assume the route exists.

1. A desk mini app, jobs and agents run for a week. Each output lands in the Library by the `library-items` lander (slice 15).
2. Copilot drafts blocks, saved through `blocks_save` with a contract test. Mini and micro are two instrument rows.
3. Copilot writes each unit with `unit_new`: exits, logic and **its own risk section right there in the document**. This is where this shape is at home: "units with their own sizing" is literally the document.
4. A pod draft for the family is optional; `expand` stamps it if used.
5. Paper on his yes; each unit has its G record.

**What else is missing, beyond the route:** `roll` compiled; `routes` lifted (stays refused till now); a copilot that takes raw video (M51); a methodology (session of its own); the agentic upgrade; volume on bars, if any block wants it (Q2).

**Verdict: HOLDS** on this design's part.

## 5. A very aggressive setup with few units on one basket, then a stage change as capital grows

1. Recipe `best-basket-press`: sizer at a large fraction or a Kelly block; press modifier on; controls empty except the kill switch's effect; stages `small` and `grown`, each with its own sizer, modifiers and limits; selector `group.money`; anchor day boundary; hysteresis. Warned and graded; never refused (V9).
2. Group with no parent limit, or a loose one.
3. Few units stamped. Their logic is untouched. One click covers plan and every stage.
4. Stage move: at the anchor the selector crosses the line. Each member reads `group.money` from the ledger, picks the stage's sizer instance (already compiled), writes `stage_move`. No new version, no recompile, no new fingerprint, no record loss. Going up: a card by template default; `rule` is one field away.
5. Exit numbers by stage, if declared at birth, move too; trade rows carry `stage`.

**Verdict: HOLDS** for sizing rows. This is the hard part the brief named: **solved by compiling all stages in.** **Strains:**
- A stage nobody declared is a pod edit, a plan and a click. Acceptable.
- A stage that should change an exit **block**, or an exit number not declared at birth, needs a new logic fingerprint per member, so a G run and a drain of open positions. This is the scalper voice's objection in `E2` and F5 A's cost. It stays.
- Members may cross at the same anchor only if they share the group fact; a unit alone reads `account.equity`, fine.

## 6. A unit made in the Lab, one from a workflow, one from a mini app

- **Lab.** No Lab package exists (`qmx_control/lab.py` docstring). A Lab pod is a `qmx.pod/1`; the Lab previews `expand(sample, pod)` and drives the hosted unit on replay, so the trail on screen is the decision row. It emits a finished unit document.
- **Workflow.** `d3`, `l1`, and `b-build-and-prove` templates write a draft through `unit_new`. Same check, same G.
- **Mini app.** The lander drops a `unit` and its blocks at publish. Its sizer is its own; it may list `risk_locks`.

All three then have the same document and the same path (M49). A stack with a block the node can't run shows as an unmet need by name.

**Verdict: HOLDS.** No special case: a unit is a unit. **Strain:** a unit with `risk_locks` joining a pod makes a mixed pod: the card must say "12 of 14 follow the recipe". On the demo's picture of a pod owning its method, that is a small lie unless shown.

## 7. A mini app feeding another, and a desk publishing a reading a unit reads

1. App to app: roads A and B, built (`qmx_apps/artifacts.py`, `triggers/event.py`).
2. The desk publishes a reading; the host stamps `source: app:<id>`, with `valid_until` and named inputs.
3. `feed_relay.py` copies it to the node. Written, no production importer (`E2`), so wiring it is slice 15. Its 5 second pass is fine for slow readings.
4. The unit's `reads` pins publisher, fallback, stale limit. Surface `reading:<id>:<market>` on the unit; a block reads it with its age.
5. Desk stops: the reading ages; fallback runs; the unit trades home markets or stands aside as it declared. Trade row shows source, age, version.

**Verdict: HOLDS.** **Strain:** adding a `reads` row is a risk-section edit, so a new reading for 200 units is a plan and a click. Correct by the fixed lines; a little heavy for a harmless reading. A reading used by a logic slot is a logic edit, and that does cost G.

## 8. 200 units: one pod edit, the fleet watch, herding on one volatility shift, one node's limits

**One pod edit. The hard part: solved, with a price.**
1. Edit in draft. `roll_plan` stamps every member: 200 expansions and hash splits took 0.54 s (probe 2f). Compile each: 746 ms median, so about 150 s on one worker (probe 1; pins all 113 blocks, so an upper figure). Off the node, this can run on several workers.
2. Plan shows counts by outcome and diffs by member. A logic-touching row refuses at stamp time.
3. One click on the plan hash, by the money door. Stale refused.
4. Node gets staged files for 200 and compiles them on its one worker. A second full compile: about 150 s behind the tick; the tick carries on with the old version meanwhile. Then one tick flips all members with `move_risk`. Open positions keep exits because `opened_by` is now the logic fingerprint (probe 4 shows this breaks today).
5. Logic records stay. Money records start per risk fingerprint; the fold by unit and pod stays continuous.

**What it costs and the others don't pay:** 200 new document versions per edit, and two rounds of compile. A pod in Shape B costs one document and one rollout pointer. A shared-cap edit here is one document, because caps are on the group.

**The fleet watch.** Scripted template reading the fold: one ranked row per unit, two lists, one incident one card, no agent; decay card off (`E5` 1.1: about 91 a night otherwise). Needs the app read door (`supervisor.py:891`, market only today). Rows carry family id, type tag, pod. **HOLDS.** Agents later.

**Herding on one volatility shift.** Each unit's numbers move by themselves. Filters: `E5` measured 21% of units moving at peak with the built engine, 45% with facts; a daily cap only delayed a right response. Sizes: **untested** (F2 C's stated cost). A `scaled` size on a volatility fact cuts 200 units in the same bar, which is probably right. A press rising together is caught only by the group's total-risk cap. This shape can't coordinate motion across members; the fold shows a `move_share`, and a group cap may answer it. **STRAINS.**

**One node's limits.**
- QML step: 60 ms median, 104 ms p99 for 200 units on 2 markets (probe 3; no entries, no journal, no venue). Fine for bars.
- **The real limit is order sends.** `client.send` holds a lock and waits for an answer, up to 5 s (`ctrader_account.py:110,679`), on the runtime thread. At a shared bell, N entries are N round trips in series. The outbox puts exits first, which protects exits from entries, but not the next frontier from a slow venue. An entry-timing offset doesn't shrink the sum. UNKNOWN until R24's demo: the round-trip time.
- Compile worker: one (`runtime.py:2098`).
- Snapshot: 30 KB per unit (probe 3b), now also on control state changes.

**Verdict: STRAINS,** and this is where the shape strains most: serial sends (F4 A) and first-come caps. Caps at the same bell are filled in `rank` order, so **"take the best of those firing this bar" can't be said.** That one I can't solve without a batch stage, which is Shape B's group stage. Say so to him if a pod needs it.

## 9. Swapping a placeholder on a unit with a record and an open position

**Sizer, a risk-section swap: HOLDS.**
1. New block, forwarding map `fixed-fraction-at-stop@1 -> real@1` with a parameter transform (R17).
2. New version, plan of one, his click. G record stays valid on the logic fingerprint.
3. `move_risk`. Open position: exits and R unchanged. Next entry: new sizer.
4. Logic record continues in R; money record starts. Old rows keep their meaning; `r_after_costs` gaining costs is a declared change (R17) because calibrated numbers read it.

**Exit placeholder, a logic-section swap: STRAINS.**
1. New logic fingerprint, so a G run and a counted try.
2. It can't be in place. The old deployment drains (`withdrawn and flat`, `runtime.py:2747`), new entries wait or start under the new deployment, on a hedging account only (`_netted` refuses two on a netting symbol).
3. Before the first deployment this is free, which is why slice 18 precedes it.

## 10. A brand-new brake, a brand-new instrument class, a new sizing base

- **Brake.** One folder and a row: SPINE section 7. If it reads a fact the host doesn't provide, that is one kernel change and two adapters, said plainly (C50). If it reads several units: a group cap, with a `group_run` test. **HOLDS.**
- **Instrument class.** Rows and keys; `instrument_class` is read in only two files today (`E5` 4.2). A test fails on branching. Margin and calendar keys cover most. **HOLDS** for CFD-like; **MISSING** for a venue with no adapter.
- **Sizing base.** A block answering `Amount`. Notional or a fixed contract count is a kind, not a socket change. A base reading a new fact: as above. **HOLDS.**

Promise check: "one folder, zero core edits" rests on the Library path, UNKNOWN until slice 15 traces it; a stdlib block bumps the money app and needs his signature (Call 11).

## 11. The MIS down mid-session; a guard or chain failure with open positions; a hung stage; a restart past an anchor

- **MIS down.** Readings age; each `reads` row takes its fallback; home markets. A sticker publisher down: `fail` row, a card and `prefer not`. No shipped template needs the MIS. **HOLDS.**
- **Chain failure with open positions.** A raising link: wrapper refuses that entry with a row; exits are minted before entries (`unit.py:535-540`) and skip both chains. A faulty exit block: next rank, then `_close_scope`. Property test. **HOLDS.**
- **A hung stage.** **STRAINS hard.** One thread: a link that hangs stops every unit's step, including exits. There is no preemption. `StuckWatch` ends the process (`healing.py:375-399`, `os._exit`); the supervisor restarts, and adoption brings positions back (`runtime.py` `adopt`). During that gap, venue-resident stops protect; time exits and cuts don't run. Mitigations: blocks are scanned (`layers.py:785-816`), have no I/O and a declared `state_bound`. A block with an endless loop still takes down all 200 until restart. F4 B would isolate this; F4 A doesn't.
- **Restart past an anchor.** Snapshot, then the catch-up rule: anchors passed while down, stickers expired, stage selector re-read, control states restored by rule. Group ledger rebuilt from member journals and R20's broker deals; until it is done the group cap reads UNKNOWN and refuses entries, exits free. Each section judged by its own fingerprint. Only `risk_stop` has a restart test today, so each state needs one. **HOLDS on paper; test owed.**

## 12. House money, reverse house money and a press after wins, on and off, per pod

1. One rule, one ledger: `cushion-rule` modifier reading the ledger of profit since an anchor. Fixed anchor presses and brakes; running peak only brakes.
2. Anchor, clock and scope are rows. Scope `unit` reads `own.*`; scope `group` reads `group.cushion`, computed in the group ledger.
3. Press after wins: a `press-gate` block in front, or a persistence press modifier. Raises read `group.raise_ok`.
4. On and off per pod: a row in the recipe's `modifiers`; a roll flips all members. Risk-only, one click. Scalper template ships it on, day anchor, because he asked; intraday off.
5. Cold: at the anchor profit is zero, factor 1.

**Verdict: HOLDS.** **Strain:** turning it off for a pod is a plan across members, where a Shape B pod flips one row. Also a Pod 5-style "slot" ledger, inherited on rotation, needs a ledger key by tag. Expressible, not pretty.

## 13. Backtest against live on the same unit: where can they differ?

Same arithmetic by construction: the same `HostedUnit` and handler in both hosts. Allowed differences: fills, costs, latency. Others, stated:

| Where | Backtest | Live | Status |
|---|---|---|---|
| A target on a wicked bar | Bar check | Node closes it (`runtime.py:1849-1857`) | F5 A's cost; waits on R24 |
| Group caps | Solo run sees only itself; `group_run` sees a chosen set | All real members | **This shape's own gap.** Stamped on the run |
| Step order at a bell | Declared order in `group_run` | Same order, but a slow send delays later entries | Latency, but it moves fills |
| Entry timing | Rests for next bar's open (`unit_handler` header) | Sent at bar close | Built; allowed as fills |
| Equity and cash | Handler's cash port | No cash port; live surface after slice 9 | Facts differ, arithmetic doesn't |
| Readings | As-of tape (R13) | Live, with age | Must be as-of or it flatters |
| Stickers | Calendar tape | Real table | Same record |
| Partials | Filled | Refused until step 3 (`runtime.py:1807-1808`) | Compile refuses by venue capability |
| Costs | Stated profile | Measured cells | Two residuals kept apart |
| Restart and heal | None | Real | Only on the node |

**Verdict: STRAINS** only on group caps, where one-unit backtests do not see the book, and on wicks.
