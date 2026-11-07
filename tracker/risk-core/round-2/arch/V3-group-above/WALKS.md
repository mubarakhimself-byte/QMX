# V3 walks

Each walk runs against `SPINE.md`'s contracts and a code reading at tip `351e7521`. **Holds** means the contracts cover it. **Strains** means it works and costs something. **Fails** means it cannot be done in this shape as drawn. Nothing was run, except one pipe check noted in AD-7.

## 1. A newcomer installs and gets a unit on paper

1. Installer and launcher: not this session (E5 G1 to G3). **Missing, not mine.**
2. The newcomer picks a template in the copilot or Lab. `unit_new("canary")`, or `scalper-mr`.
3. They never meet the word "pod" unless they look. Promote to paper generates a pod of one from the template's pod template (AD-2).
4. History and replay run with no broker, if G8 turns out true (UNKNOWN). `replay_group` uses the same evaluator.
5. Day two: cTrader approval, about a day (E5 G6). Paper deployment; `SPINE.md` section 7, steps 5 to 10.
6. Why this size? `pod_explain` answers from the first trade.

**Holds.** The pod of one hides the machinery. **Strains:** a newcomer who opens the Portfolio tab finds a pod they did not make. It needs one line of UI words. A "canary" is one row of brakes off.

## 2. A gold scalper with fast invalidation and no fixed stop

1. Unit document: entries, plus exit stack with a fast cut (a per-bar exit reading `PositionFacts`), and `basis: tail_budget`. `compiler.py:500-506` lifts.
2. Each 1m bar: exits run first, in phase one, with no ask. The cut answers `CloseFull(reason)`.
3. Proposal carries no stop. Pod sizer must accept `tail_money`. `pod_check` compares needs: a sizer reading only `stop` against a no-stop member warns and names the row. At run time it refuses, with a code, rather than guess.
4. Boundary: the protection gate (`runtime.py:1102-1106`) accepts the declared basis. `_entry` computes `distance` from the stop today (`:1074-1076`) and must branch on the basis.
5. Venue: `require_venue_resident_protective_stop` must be relaxed by row. **A fixed-line check:** exits are unblocked, but with no stop at the venue, a node death leaves the position naked. It warns in large type (AD-18) and is expressible.

**Strains in four places.**
- The cut is one bar late at best. A true sub-bar cut needs a tick clock (I7), deferred, and sits outside the two-phase bar.
- R lives in two documents: the unit says "tail budget", the pod holds the money. The needs check is what keeps them honest.
- The worker round trip adds latency at entry. Pipe cost small; chain cost UNKNOWN.
- A scalper's brake sits one process away from it (candidate 3's objection stands). Cut logic stays on the unit, which is the part that must be fast. A bench reads marks through the relay, one tick late.

The cut catching winners (C1) stays open and is not a shape question.

## 3. An ORB unit across several opens, one bet counted once

1. Unit: one logic, `sessions` compiled (S9), `position_limit` per open (S17), family tag, tolerates `open` by a pod tolerations row.
2. London and New York open within a window; the unit proposes on DAX and NAS, with `bet_key` `equities:long`.
3. Both land in the pod's batch. `open_risk` by key is in the evaluator's state, and a same-bet cap link counts them as one. Second shrinks or refuses, with the clamp named on the trail.
4. A second ORB unit in the same pod on a third index: same key, same cap, no extra work.
5. Records split per open by slice on trade row v2.

**Holds, and this is the shape at its best.** Same-bet counting needs no cross-unit mechanism, because the pod already sees everything. **Strains:** a same-bet cap across two pods on one account is either a boundary row (signed stdlib only) or a soft row with an age. Volume gate waits on I7 and Q2.

## 4. A futures week with the copilot, ending in units with their own sizing

Assume the route exists. The week produces a futures mini app (desk), research notes, a `futures` pod draft (method, vol target or margin-aware sizer, worst-step reserve, roll stand-down, per-contract rows for mini and micro) and several unit drafts.

**Missing, not this shape's:** `roll` compile; instrument records for contracts; the methodology; copilot video ingestion (M51); the agentic upgrade; a `build-pod` skill. Road D for its readings is S8.

**This shape's reading of his sentence.** "Units with their own sizing" in the literal sense does not exist. What exists: units in a pod that owns their sizing, with per-tag overrides for mini and micro. If the week's result truly is one unit-specific sizing rule, it lands either as an `/ask` block with `sizing: ask`, or as its own pod.

**Strains:** a week's work has two kinds of output: unit versions (G, counted tries) and pod versions (no G, click). The copilot must know which is which. Clean for a developer, one more idea for a copilot skill. **Better than other shapes:** the optimising loop over sizing replays proposal tapes against pod drafts with no re-run of logic, so a hill climb over sizing is cheap and each try counted.

## 5. A very aggressive setup with few units on one basket, then a stage change

1. Pod `best-basket`: high fraction, caps removed, allocation `few best by feasibility`. `pod_check` warns and grades. It runs (AD-18). Kill switch remains.
2. Few members, one basket. Feasibility verdict per member at each anchor.
3. Capital grows. Stage change, two forms:
   - **A stage row inside one pod version:** a stage-line fact at the anchor selects numbers or a member set. No click, since the owner clicked the version containing the table. A raise waits for the anchor.
   - **A new pod version:** a new method, one click bound to its hash, every member moves, no unit version moves, no G, the logic record continues, a new money record starts.
4. Open positions keep their stamps.

**Holds, and strongly:** a stage change costs units nothing. D31's seat is simply the document. **Strains:** tighter exits by stage are not reachable: exits are on the unit, so that is a unit version (F5 C deferred). The scalper voice in E2 does not accept this, and neither walk here settles it. **Honest risk:** one mistyped pod edit hits every member at once; the click shows the diff, and there is no canary unless a second paper or partial pod deployment is used.

## 6. A unit from the Lab, a workflow, a mini app

- **Lab:** the Lab's stack is the pod document, natively. Lab emits unit plus pod. Lab replay is a driver. The cleanest origin.
- **Workflow:** lands a unit through `unit_new` and optionally a pod; none means the template's pod of one.
- **Mini app, plain unit:** needs S16's lander (only `qmb-run` registered today, `qmx_host/host.py`, per E2). With it, same as workflow.
- **Mini app, its own sizer (the hard case):**
  1. The app lands a unit whose `/ask` binds its block, and the block as a Library `component`, pinned.
  2. Alone: promote generates a pod of one with `sizing: ask`. The ask replaces only the sizer link: stickers, gate, controls, converter and boundary still run. It trades with its own arithmetic in the unit's step, with a receipt.
  3. Joining a pod: member row `sizing: pod` by default, and the join screen says "this unit's own sizing will not be used". `lower_of` or `ask` is one field.
  4. A sizer that reads the unit's private bars runs fine: it stays on the unit's step, where those are.
  5. A sizer that wants pod facts reads the `account` surface and last-answer facts, with their age. It does not get the batch view.

**Strains:** an `ask` member makes "one document sizes every unit" untrue for that member, and the pod's edit no longer changes that member's base. The fleet view marks it. An old-style unit with its sizer in `/sizer` is upgraded to a pod of one with the block in the pod. **Fails:** a mini-app unit that insists on placing with no evaluator. Not expressible; deliberate.

## 7. A mini app feeding another, and a desk publishing a reading a unit reads

1. App to app: road A (artifact feed) or road B (Library landing as event). Built, unchanged by this shape.
2. Desk to unit: road D. The desk writes a reading with host-stamped `source: app:<id>`. A unit's `reads` pins publisher, fallback, stale limit, or a pod's `reads` pins the same for a sizing input.
3. Relay carries it to the node (today's relay is MIS only, unwired, `feed_relay.py`): S8.
4. Desk stops: the reading ages; fallback applies; trading continues.

**Holds.** **Choice this shape adds:** a reading that changes size is better read by the pod, one read for 200 units. A reading that changes entry logic stays on the unit. A copilot must choose. **Strains:** a new app-published reading used by a gate link goes through facts `readings`, fine; a new fast sensor does not: AD-16.

## 8. 200 units

**One pod edit.** Draft through `pod_patch`. `pod_check` diff. `pod_replay` on tapes as a preview. One click. The worker applies at the next anchor (or at once if a cut). Compiled fingerprints do not move, G unchanged. **Holds: the main promise of this shape.** A partial rollout means moving ten members to a second pod deployment first; a little ceremony.

**Fleet watch.** About a dozen pods; agents and scripts read `fleet_read` by pod, drill to members. One incident, one card. From zero every row reads "too thin to judge". Decay's per-unit nightly card is off. **Holds.** **Strains:** a pod with 200 members is no easier to read than 200 units, so the rank inside the pod matters. A sensible user splits by style.

**Herding on one volatility shift.** Facts are live: every `scaled` number follows one vol fact at once, and every member's sizes step together. Numbers on the sheet all move at one anchor. This is F2 B's stated cost. In this shape it is one decision, visible once: one sheet, one receipt, one `pod_state` change. The parent limit sits above in the same evaluator. A `NumberGuard` holding a sheet that moves too far is a row. **Strains:** all members really do move together; there is no staggering across a pod unless a row says so. Whether that is good is a numbers question.

**One node's limits.**
- Evaluation: one worker per pod, so many cores are usable. Mechanism check: batch of 200 through a pipe about 2 ms with a stand-in chain. Real chain UNKNOWN.
- **The real choke is unit stepping on one thread:** `_drive` walks hosted units serially (`runtime.py:3013`), with a slice latency limit of 0.5 s (`:189`). 200 units on one thread at 1m bars is UNKNOWN, slice 0 measures it. This shape does not help that, since units stay in the node process. If it fails, units must also move out, which is a large rework and the most likely surprise in this design.
- Bell queue: the batch can stamp `not_before` offsets per rank (S18). Order rate is a boundary row.

## 9. Swapping a placeholder on a unit with a record and an open position

**Sizer swap (PH 1).** Pod version with a new sizer, one click. Unit fingerprint untouched; logic record in R continues; the money record starts a new `pod_hash` era. Open position keeps stop, target and entry size; next proposal uses the new sizer. No forwarding needed. **Holds, trivially.**

**Halt swap (PH 5).** Same. A state in force under the old row: a benched member stays benched until its restore rule, or, if the row was removed, at the first anchor, since that is a raise.

**Stop or exit swap (PH 2 to 4).** Unit version: identity table classifies it (wired under R17); a counted try; G; click. **Open position:** the handler closes only what this fingerprint opened (`unit_handler.py`, `opened_by`). So the rule is drain: the old version keeps running exit-only until flat, and the new one takes proposals. Two deployments on a market for a while, allowed by AD-2's key. **Strains:** on a netting account or one-position market, new proposals wait for the drain. The forwarding map could adopt a position under the new exit stack when the owner chooses; then the row says who governed what.

**Old rows.** `r_after_costs` gaining costs shifts anything calibrated from it (E13, R17). Stated on the migration.

## 10. A brand-new brake, instrument class, sizing base

- **Brake.** One folder, one row, one code. Runs in the worker, reads the fold. No unit, compiler or node change. Cold behaviour on the row. **Holds.** If it needs a fact not in `Facts`: a kernel PR, three providers, tape catches a miss (C50).
- **Brake that must be atomic across pods on an account.** Signed stdlib block on the boundary list (AD-8), since Library code cannot run on the node's thread. **This fails the promise "one folder, zero core edits" for that one case.** The soft form works, with an age, and the row says so.
- **Instrument class.** Rows and records, no branch. New venue if needed. Worker needs nothing. **Holds.**
- **Sizing base.** One folder, one line in a pod. New `Amount.kind` only if a new kind of amount, one converter case. **Holds.**

## 11. Failures

**MIS down mid-session.** No template reads it. A pod row reading it takes its fallback; `stand aside` if declared. Worker notices age only. **Holds.**

**Guard or chain failure with open positions.**
- A block raises: its row's `fail_mode`; trail records it; default `no_new_entries` at row scope.
- Evaluator bug raises for the whole pod: worker answers nothing, or dies. Node marks SILENT. All entries of that pod refuse. Exits were already sent in phase one, every bar. Venue stops stand. Other pods trade. Alarm and card with the root-cause key.
- **The cost:** one bug in the evaluator or in one common block halts entries for all that pod's members at once. A unit-owned design loses one unit. Blast radius is the pod. Its mitigations are splitting pods and that nothing is lost but entries. **Correlated failure is this shape's central weakness.**

**A hung stage.** `ask` waits at most `ask_deadline`. First miss marks SILENT, supervisor kills and respawns, `recover` folds. During that one deadline the runtime thread is waiting; exits of this bar already went out, but next bar's exits wait, so the deadline must stay well under a bar. Boundary rows are signed code with no I/O, because a hang there would stall exits on the thread. Node watchdog (`watch.began`, `runtime.py:2192`) covers the rest. **Holds with a bounded delay, and "never blocked" here means never by the evaluator.**

**A restart past an anchor.** Node restarts: stand-downs and kill rebuilt (built). Worker respawned: `recover` folds, then `advance` derives latest anchor once with `restart_late`. Bench and cuts stand; earned raises wait one anchor. Expired stickers settled from the table. Unsettled reservations dropped only where no position exists (AD-9). No new entry until `recover` ends: pod word UNKNOWN. **Holds on paper; only `risk_stop` has a restart test today (`SWAP 23`), so K9 must add this.**

**Worker dead, node alive, position hits a brake's flatten condition.** No flatten from the pod until it is back. Venue stop and exit stack still act, and the account line and kill switch still work. **Strains: a pod-level `flatten` is only as live as its worker.**

## 12. House money, reverse house money, a press after wins, per pod

1. One row: `cushion-rule` modifier reading the cushion ledger, with anchor type, clock and scope as rows (R9). A fixed day anchor presses and brakes; a running-peak anchor only brakes.
2. Per pod on and off: one row in the pod's document, one click if live. Members need nothing. Different pods, different anchors.
3. Timing by AD-10: the rule's shape and bounds freeze on the sheet; the live ledger moves the multiplier between anchors, downward at once. Permission above one is a raise, set at the anchor, and the raise gate row (default on, removable) blocks it while a brake holds.
4. Press after wins: a block, with a press gate block as an option. Reads realised profit since anchor.
5. Per-member cushion or pod-pool cushion: the ledger's `scope` field. Old pair (`E2` Pod 5) needs a slot identity: a pod-level ledger gets that with no unit change.

**Holds, and it suits this shape:** a pod-pool cushion is natural here, and hard elsewhere. **Strains:** mid-anchor, a recovering day cannot re-press until the anchor if permission lapsed. For a scalper that may read as slow. A row can set an intra-day clock, since anchors are clocks.

## 13. Backtest against live on one unit: where can they differ?

**Same by construction:** the unit step, exit stack, chain arithmetic, sheet derivation, rank, converter, batch sort. Conformance tape holds them.

**May differ, and labelled:**
| Where | Why | Label or fix |
|---|---|---|
| Fills and slippage | Facts | Fill record, markouts |
| Costs | Calibration | `uncalibrated`, world on the cell |
| Wick on a target | Node-held target until R24 | `target_held: node` (AD-21) |
| Partial closes | Node refuses until step 3 | Refused at compile against capability, so it cannot compile in one and fail in the other |
| Relay age | Inline driver has age zero | QMB can inject an age; default stated in run stamp |
| Pod SILENT | Live only | Rows; a stress tape injects it |
| Marks between bars | Node ticks, QMB bars | A control on marks reads less often in QMB. Run stamp says so |
| Peers | **A one-unit backtest in a many-member pod sees no peers, so caps and allocation read differently** | `replay_group` over all members, or tape replay. Run stamp lists members |
| Baseline | Live quotes against recorded minute rows | `sqs:bar_sampled` |
| Equity | Live balance against start plus closed | Live surface; `basis` label |
| Account line | A one-pod backtest does not see other pods | Root pod's rows run with a labelled relayed series or off, stated |

**Strains: the peers row.** Here a unit's money result is meaningless apart from its pod. That is the honest consequence: the unit's evidence is logic in R with would-haves, and money evidence belongs to the pod. Methodology must accept two proof objects: a unit, and a pod. A proposal tape replay is for exploring only: a refused entry changes what the unit would have done next, and it cannot see larger fills. A `replay_group` rerun is the evidence.
