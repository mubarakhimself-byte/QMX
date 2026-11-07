---
name: 'The fold: the unit owns it, with thirteen grafts'
type: architecture-spine
purpose: build-substrate
altitude: feature
paradigm: 'Self-contained cell with a recipe stamped in at design time; one thin shared ledger whose limits are live facts; one node thread in two passes, exits first'
scope: 'Risk and sizing of the unit, the pod and the group level; MIS, SQS, node, QML and shipping where they touch them. The first baseline and the layer anyone customizes'
status: final
created: '2026-11-07'
updated: '2026-11-07'
binds: ['FUNNEL section 3 core rows (51)', 'FUNNEL section 4 first baseline', 'COMPARE section 4 grafts 1-13', 'COMPARE section 5 findings 1-12', 'SWAP-CHART rows 1-31 and E1-E18', 'SEEDS-2 Part C', 'final/CHECK.md blockers B1-B9 and should-fixes S1-S17']
sources: ['round-2/arch/COMPARE.md', 'round-2/arch/V1-unit-owns (base)', 'round-2/arch/V2-pod-by-scope, V3-group-above, V4-premise (grafts)', 'round-2/funnel/FUNNEL.md', 'round-2/funnel/QUESTIONS.md', 'round-2/expand/E1, E2, E5', 'unit-baseline/SWAP-CHART.md', 'round-2/SEEDS-2.md', 'D:/QMX-worktrees/bld-repair-24 at 351e7521']
companions: ['SOLUTION.md', 'WALKS.md', 'OPEN.md', 'FIXES.md']
---

# The fold: the unit owns it, with thirteen grafts

Written headless, 7 Nov 2026, as the fold of four architecture versions under `round-2/arch/COMPARE.md`, then corrected by the final fix round against `CHECK.md` (`B n` and `CHECK S n` name its findings; `FIXES.md` lists each one). Base is V1; the thirteen grafts and twelve findings of COMPARE sections 4 and 5 are taken, each named where it lands. Paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\` unless they start with a package name; package paths are under `D:\QMX-worktrees\bld-repair-24\`, tip `351e7521`, where every code line cited here was re-read today. `PH n` is a row of `RISK-SIZING-PLACEHOLDERS.md`; `SWAP n` and `En` are rows of `unit-baseline/SWAP-CHART.md`; `S1`, `I2`, `R9`, `K7`, `V1` are core rows of `round-2/funnel/FUNNEL.md` section 3; `G n` is a graft of COMPARE section 4; `F n` is a finding of COMPARE section 5; `Mn` is his message. Numbers are labelled placeholders, owner "numbers talk"; none is argued here. `[ASSUMPTION]` marks an inference nobody confirmed; UNKNOWN marks what was not verified.

**Fork answers held (from V1, grafts in brackets):** F1 A compiled in plus a thin group [G6: group limits as live facts; G13, trimmed by the lead: a `rank` field, the slot later]; F2 C find, track, correct; F3 B node sensor, unit gate slot, one curve; F4 A one process, one node thread [G1: time budget; G2, trimmed by the lead: a plain `try`, no wrapper]; F5 A exits on the unit, fixed order, the node closes targets; F6 B small core widened in slices; F7 C two chains [G4: one decision row written before the send].

## 1. The paradigm in a sentence

**A unit carries every rule it obeys inside its own document, split into a logic part and a risk part with a hash each; a pod is a recipe stamped into each member before it runs; the one thing above the units is a thin group on the node that holds shared caps as live facts and a shared ledger and can only cut; the node drives all units on one thread in two passes per bar, exits first.**

Why this is a fair reading of what exists: the unit document already has seats for `sizer`, `exit_set`, `halts`, `reads`, `numbers`, `sessions`, `position_limit`, `context_needs` and per-market settings (`qml/src/qml/unit/model.py:470-492`), and the compiler refuses most of them by name (`compile/compiler.py:896-1014`). This design turns refusals into running code, adds a handful of optional document fields, puts one small thing above the unit, and reorders one loop on the node. His words: "look at what exactly is already there in the unit" (M49); "Design for complexity. Don't design a complex system." (M8).

### What runs where at trade time

```mermaid
flowchart TB
  subgraph PC["PC, off the order path"]
    POD["Pod recipe: a Library document"]
    ROLL["Roll plan: stamp, check, compile each member"]
    CLICK["Owner's click on the plan hash"]
    GROUPDOC["Group document: selector by name or tag, caps, money, rank"]
    APPS["Mini apps, desks, agents publish readings; drafts and cards only"]
    POD --> ROLL --> CLICK
  end
  subgraph NODE["Node process, one node-runtime thread"]
    subgraph PASS1["Pass 1: every unit, exits first"]
      UNIT["One compiled unit (also runs in QMB)<br/>logic section: slots, exits, logic numbers<br/>risk section: sizer, modifiers, gates, control rows, reads, tolerations, stages"]
      XO["Exit intents: skip every chain, go now"]
      PROP["Entry proposals: parked in the outbox"]
      UNIT --> XO
      UNIT --> PROP
    end
    subgraph PASS2["Pass 2: parked entries by rank, under a time budget"]
      UC["Unit chain (in the unit): stickers tolerated, gate slot, own caps, sizer, modifiers, converter"]
      NC["Node chain (in the host): kill effects, group caps as live facts, order veto"]
      ROW["One decision row, written before the send"]
      UC --> NC --> ROW
    end
    PROP --> UC
    LED["Group ledger: one fold over journals"]
    SENS["Node sensor and curve"]
    XO --> V["Venue"]
    ROW --> V
    V -->|"fills"| LED
    LED -->|"group facts, read as facts"| UNIT
    SENS -->|"readings"| UC
  end
  CLICK -->|"new risk section, moved in place"| UNIT
  GROUPDOC -->|"limits as facts, at the next decision"| LED
  APPS -->|"readings with publisher, age, fallback"| UC
```

## 2. Decisions

Each is a call two builders could make incompatibly. `[ADOPTED]` means the code or his words already settled it. `[G n]` names the graft taken; `[F n]` the finding answered.

### AD-1 The unit owns its size and its own brakes

- **Binds:** S1, S2, S4, S6, S13, S14, V7, V10.
- **Prevents:** a second evaluator above the unit; a size computed in two places; "no pod" as a special case.
- **Rule:** at trade time everything a member obeys that reads only its own facts or market facts is in its compiled document and runs in `HostedUnit`, the code QMB and the node already share through `UnitSliceHandler` (`qmb/src/qmb/host/unit_handler.py:1-7`). Nothing above a unit computes a size. A template or a mini-app unit with no pod and no group is the normal case. **Sizing is pass 2 [B8]:** sizing is a separate call, `HostedUnit.price(proposal, facts, admit)`, made by the host in pass 2 (AD-17), never in pass 1, so account facts stay out of the exit pass and a parked entry is sized on fresh facts. Until slice 11 lands the outbox, the host makes that call straight after the unit's exits went out, where placing happens today (`runtime.py:1727-1733`); slice 11 moves the one call site. QMB's one-unit run and `qml/check/layer_g.py` call it the same way. If he later picks a pod that governs (section 12), only what `price` receives changes.

### AD-2 One document, two sections, two fingerprints; three tiers of change

- **Binds:** S14, I9, R17, `qml/unit/sections.py` (new), every builder who asks "does this need a click?" [G7, V4 AD-2].
- **Prevents:** builders disagreeing about what a pod edit may touch; a size edit re-proving logic; a live edit that bypasses the click by calling itself configuration.
- **Rule:** one function partitions the document. **Logic section:** `markets`, `streams`, `direction`, `logic`, `exit_set`, `sessions`, `position_limit`, and every number bound by a logic slot or an exit, with their pins. **Risk section:** `sizer`, `modifiers`, `gates`, `halts`, `reads`, `tolerations`, `stages`, and every number bound only there. **Anything not named as risk is logic,** so a new or forgotten field can't fall between the two (`baseline`, `claim_card`, `context_needs`, `family_id`, `lineage`, `plain_python`, `routes`, `title`, `unit_id` included); only `recipe` sits outside both. A number bound in both is logic. A `reads` row bound by a logic slot is logic. A `stages` selector with any exit in its `stage_values` is logic, so a risk edit can never move an exit number unproven [CHECK S4]. `compiled_fingerprint = H(logic_fingerprint, risk_fingerprint, format, options)` (today the whole document hashes in at `compiler.py:1072-1079`). **Three tiers, the builders' rule:** a *fact* changes live and reaches the unit at its next decision with its age; a *number* moves by its own rule inside its declared range with no click; a change of *structure* (a block, a binding, a range, a default) is a new version. Group limit values are facts (AD-8). A thing that must flip live is a fact; a thing that changes what runs is a version.

### AD-3 The node tests logic and trusts a click for risk; never a new fingerprint over a held trade

- **Binds:** `runtime.py:2756`, `promote.py`, `unit.py:672-674` (`opened_by`), `unit_handler.py` [F4, F5].
- **Prevents:** a pod edit that re-proves 200 units; a pod edit that changes live risk unclicked; a held position whose per-bar exits go silent after a recompile (COMPARE's rerun: 0 exit intents in 60 bars against 1).
- **Rule:** a deployment names `logic_fingerprint` (its G record must cover this), `risk_fingerprint`, and the click that covered it; the node refuses when either fails. `opened_by` on positions becomes the logic fingerprint. **No host ever runs a different compiled fingerprint over a held trade except by `move_risk` (AD-6), which keeps the logic fingerprint, or by a drain (`withdrawn` then flat, `runtime.py:2640-2641, 2746-2748`, mostly built).** A compiler format bump moves the logic fingerprint on purpose and pays K8. The pod's blocks pass their own contract tests and G's safety half (`qml/check/layer_g.py`: determinism, restore, state bound) per distinct risk fingerprint.

### AD-4 A pod is a recipe; stamping is a pure function; drift is reported

- **Binds:** S14, S16, `qml/pods/expand.py`, the fleet fold [G10, V4 W8].
- **Prevents:** a pod at run time; a pod reaching into logic; rework when a unit leaves a pod; hand edits after stamping going unseen.
- **Rule:** `expand(unit_document, pod_document) -> stamped_document | named refusal`. Filled pod slots replace the risk section's matching rows; empty slots leave the unit's own. The stamped document records `recipe` (pod id, version, hash, and `displaced`, the rows replaced, so leaving a pod restores them). A unit may list `risk_locks` (for example `sizer`): the pod does not replace those and the plan shows the member as `locked`. A recipe row touching a logic-bound number or an exit is refused by name. `expand` is deterministic and idempotent. **Drift report:** the fleet fold lists every member whose risk section differs from its recipe at its version, by row; the pod card says "12 of 14 follow the recipe". A pod owns its sizing method because it fills the sizer slot; several methods side by side are several recipes.

### AD-5 One pod edit is one plan and one click; a group edit is its own click

- **Binds:** S14, K5, V4, Q6, `qml/pods/roll.py`, `qmx_host/roll.py`.
- **Prevents:** 200 hand moves; drafts reaching a live deployment; a click on something that has since changed.
- **Rule:** `roll_plan(pod@new, members)` stamps, checks and compiles every member off the node and sorts each into `risk_only`, `unchanged`, `locked`, `logic_touch` or `refused`. The plan hash is `H(pod hash, sorted (deployment, new risk fingerprint))`. The owner's one click binds to that hash through the money door (K5); a stale plan is refused. `refused` and `locked` members stay on their old version and are named. A `logic_touch` member is handled the same way: it stays out of the plan hash, stays on its old version, and is named as needing its own new version and G run; the click never carries it [CHECK S13]. A plan may cover a subset, which is a canary. Each member gets a new unit version; the identity table (R17) gets a section column so a risk-section edit keeps the logic record and starts a new money record. A group document edit (AD-8) is a separate click on that row's version and touches no member document. Agents and the copilot write drafts and plans only.

### AD-6 A risk move happens in place

- **Binds:** `qml/protocol/unit.py` `_Core`, `_cold_reason` (`unit.py:990-991`); `runtime.py` `_deployments` [F5].
- **Prevents:** a cold start of logic state for a size edit; a mixed pod for minutes.
- **Rule:** `HostedUnit.move_risk(new_compiled)` works only when the logic fingerprint matches. Logic instances, derived numbers, calibrated logic numbers and open positions stay; risk instances are rebuilt. A control row keeps its state if its row id, pin and params match, or else starts by its declared cold behaviour; since states are derived from the fold (AD-12), nothing is copied. Snapshots carry two parts and `_cold_reason` judges each by its own fingerprint. The node compiles a plan's members on its one compile worker (`runtime.py:2098`), then flips all of them in one tick. An open position keeps its exits and its R; the next entry uses the new risk section.

### AD-7 Stages are compiled in

- **Binds:** I10, S2, S13, `qml/unit/model.py` `Stages`.
- **Prevents:** a stage change that mints a new identity or wipes a record; "at 5,000 the math changes" (M51) needing a new unit.
- **Rule:** a risk section may declare `stages`: a selector (a fact, or a block), the anchor it is read at, hysteresis, and for each stage the sizer, modifiers, control rows and number values in force. All stages compile into the plan, so the risk fingerprint covers them and one click covered them. A stage move is a state change at an anchor with a `stage_move` row, never a new version. `move` is `rule` or `card`, per direction; templates ship `card` going up and `rule` going down (COMPARE §6 row 2 default). While a `card` waits, the old stage keeps trading; only his answer moves it [CHECK S13]. An undeclared stage is a pod edit (AD-5). Exit numbers may vary by stage but sit in the logic section, so adding them costs a G run per member once.

### AD-8 The thin group: caps as live facts, a ledger, a rank; nothing else

- **Binds:** I10, S6, R9, D31, D35, `qmx.group/1`, `qmf/risk/group.py` (types), `qml/group/caps.py` (runner) [G6 V4 AD-10, G8 V4 3.8; G13 and G5 trimmed by the lead, 7 Nov].
- **Prevents:** the group growing into an evaluator; a cap edit touching 200 documents; a shared cap overrun by two units on one bar; whoever was hosted first always winning the room.
- **Rule:** a group is a document with `display_name`, `parent`, `selector` (unit ids and/or tags, many-to-many), `place`, `side`, `money`, `limits`, `caps`, `ledger`, `rank`, `alarm_budget`, `share_cap`. **Membership** is by selector; a deployment may also name `group_id`; the member document is untouched either way. **Limits are facts:** every number in `limits` and `money` is published on scope `group:<id>` at edit and at each anchor; a member's cap row or modifier row reads it at its next decision, so one edit reaches 200 units with no recompile; the edit is the owner's click on the group row's version. **Caps** are control rows of scope `group` whose block answers `pass`, `shrink(quantity)` or `refuse`, plus `on_fire`; a cap never raises; it runs at two moments: on an entry in pass 2, and after each ledger fold, so a day stop fires with no entry pending. **An unknown outcome keeps its room:** on one thread a place answers at once, so there is no reservation type; an entry whose venue answer is unknown keeps counting in `group.open_risk` until the venue settles it, and a warming unit counts nothing. **Rank** is a field on each member's row in the group (`rank`, then a per-bar hash for ties); it sorts the outbox's entries for this group. An order slot arrives when content needs one ("take the best of those firing this bar"), as an additive field beside `rank` (section 11). The ledger exposes group facts (`group.day_pnl`, `group.open_risk`, `group.raise_ok`, `group.cushion`, `group.members`, `group.limit.<name>`) on each member's fact surface. **A row may bind `enabled` to a fact**, so a recipe can switch a modifier on and off for a whole pod through one group fact (walk 12). Allocation modes: `own size under a parent limit` (default) is no share plus a cap; `split` is a member-side derivation reading `group.members`; anything that ranks members runs off the path and publishes a share as a reading (AD-16). **Places:** a group lives on one place (one node process); a group spanning places (the PC and a server) is several groups whose caps read a published fact with an age, eventual by construction; the PC holds everything first and a server stands in or expands, never replaces.

### AD-9 Two chains, one receipt, a plain `try` on every block, one row before the send

- **Binds:** S6, V1, R1, `qml/protocol/entry_chain.py` (unit chain), `qml/chain/node_chain.py` (node chain runner), `qmf/risk/chain.py` (verdict types) [G2 V2 AD-9 trimmed by the lead, G3 V2 AD-8, G4 V2 AD-6; F3, F8].
- **Prevents:** a link with no home; two receipts that cannot be joined; a chain that can stop an exit; a refused frontier ending that unit's exits (`runtime.py:3040-3046` sets STOPPED today); a crash between stages leaving a row with no order or an order with no row.
- **Rule:** the unit chain runs inside the unit; the node chain in the host. **Placement test:** a link that reads only this unit's facts and market facts it may tolerate goes in the unit chain (stickers not tolerated, the gate slot, its own caps). A link that reads the account or other units goes in the node chain (kill effects, group caps, order veto: margin headroom, worst-step reserve, size band, order rate, venue stop or declared no-stop basis). **The runner and the `AdmitPort` protocol live in `qml`; links that need `qmn` (kill effects, protection) live in `qmn/app/node_links.py` and are injected,** so `qml` imports nothing from the node [CHECK S11]. The node chain is called from one seam, `UnitSliceHandler.mint_intents`, through an injected `AdmitPort`, so both hosts call it; the node's `guard`, `cross_unit_hook` and protection gate become links or stay directly behind it (`runtime.py:1100-1106, 2623-2675`). **A plain `try` on every block:** a chain link or control row that raises refuses that entry with `link_fault`, stands that link's scope down, and never returns a refusal into `close_frontier`, the same way AD-23 treats a raise in a slot. Time is budgeted once, on the entries pass (AD-17). **Hung-link protection is deferred with the worker process (section 11), by the lead's call on `CHECK`'s "Too much machine". The risk, named:** a block that never returns stalls that node's one thread, exits included, until `StuckWatch` (`healing.py:64`, 30 s) restarts the process; stops resting at the venue hold through the gap; after the restart the same block can hang again until its owner stands it down. A raise is the common fault and costs nothing else; a hang is the rare one and costs a node restart. **Words:** a gate's `block` is the chain verdict `refuse`; `shrink` rewrites the wire quantity; `wait` keeps the proposal parked until its `expires_at` (AD-17), with no send; `warn`, `shadow` and `none` pass with a row [CHECK S13]. **One row:** both chains append to one in-memory trail; the decision row is journalled once, after the last link and before any order leaves, with every input stored (facts as read with age and source, group facts included), so it replays alone. **Import test:** exit code (`qml/protocol/exits.py`) imports nothing from `entry_chain`, `node_chain`, `fold` or the readings feed; a test parses its imports. Exits never enter either chain, by property test including a faulty block, a raising logic slot and a raising sizer.

### AD-10 A sizer answers a typed amount; one converter spells the venue's quantity

- **Binds:** S1, I1, PH 1, 12, 30, `qml/blocks/api.py` `Amount`, `qml/numbers/convert.py`.
- **Prevents:** a socket change per base; lots in design; a 5,000-lot answer passing (`SWAP` S1c); a trigger bound as a sizer (`SWAP` S3); the USDJPY fault, where a size meant in the account's currency loses that figure in JPY (`fixed-fraction-at-stop/1/block.py:52-53`, ran in `CHECK` B5); two builders each solving conversion their own way; a stale rate with no stated behaviour.
- **Rule:** a sizer returns `Amount(kind: money_at_risk | notional | quantity, value, basis)` or a `Skip`. Today's `Size(lots)` reads as `quantity`, so the placeholder still passes. One converter reads the amount, the declared R basis, the instrument record (value per point, lot step and bounds) and a **rate** and spells the venue's quantity, rounding down by default with real residue; hosts stop re-rounding after their first check. **Currency [B5]:** `value_per_point` is in the record's quote currency (`records.py:51`), so `quantity = money / (distance * value_per_point * rate)`, where `rate` is account currency per one unit of quote currency. The rate is an ordinary `Fact` (`market.rate:<quote>`). The record gains `conversions: Mapping[account_currency, ConversionRef(market_id, invert)]`; quote equal to account is rate 1 with no lookup. The host subscribes each named market beside the unit's traded ones and never drives the unit on it, so a cross such as EURJPY needs no `context_needs`. A stale (past `rate_stale_s`, a labelled placeholder) or absent rate gives a named skip, `rate_stale` or `rate_absent`, on that entry. **Exits never read it:** a close is sent regardless; `_money` (`unit_handler.py:216-220`) keeps the quote-currency figure and stamps the last rate with its age on the row, and `_account()` (`:372`) sums converted money. QMB reads the same fact from the conversion market's replay bars; a backtest missing them skips by the same name and says so on its run stamp. `Size(lots)` skips the converter because it states a quantity, so **every shipped template binds `fixed-fraction-at-stop@2`, which answers `Amount(money_at_risk)`;** `@1` stays only as the old row forwarded by R17. The compiler checks the slot's face (`output: amount`). The size band and per-trade cap live in one row, applied after the converter. A sizer gets `side` and reads moved numbers from `evidence` (AD-14). **Why lots (M49):** lots are the venue's word for a quantity of one instrument; a rule speaks in money at risk or notional, which is the same across instruments; the converter is the only place lots exist, and the wire already says `quantity`.

### AD-11 Named modifiers; the level is one of them

- **Binds:** S2, D4, D13, D14, `sizing_modifier` role.
- **Prevents:** hidden multipliers; a ladder law; press and brake on two ledgers.
- **Rule:** `modifiers` is an ordered list on the risk section. Each block answers a factor inside its declared range with a reason on the receipt. Default combination is product, or a declared combiner; a `cap` row takes the lowest. The level is one named modifier with no ladder law. A modifier may raise. The raise permission gate is a default row reading `group.raise_ok` and unit state, removable by a reckless recipe. House money and reverse house money are one `cushion-rule` modifier reading one cushion ledger (R9 scope): a fixed anchor presses and brakes, a running-peak anchor only brakes; the press gate is a block in front.

### AD-12 A control row runs in the unit; states are read from the fold; the snapshot is a cache

- **Binds:** S4, S10, S11, S12, PH 5, 18 to 20, 23 to 25, 28 [G9 V4 3.4, V2 AD-16; F9].
- **Prevents:** each brake as custom code; a brake that needs the node to exist in a backtest; a brake state lost on restart because the snapshot writes only when a calibrated number moves (`runtime.py:2919-2927`); state copied by hand on a pod edit.
- **Rule:** `halts` stays the seat and each entry is a control row: required `reads`, `scope`, `verb` (`none`, `no_new_entries`, `reduce(factor)`, `flatten`), `on_fire` (stand down at a scope, raise a kill level, card), `restore` (rule or hand), `until_n` (cold behaviour: warn, shadow, or a fixed labelled fallback), `shadow`; the rest defaulted (attack, release, counting, fail mode, money series, class, healthy fire rate). FUNNEL's `placement` field is struck: a row runs where its document says, the unit or the group. The control runner in `_Run.step` feeds each row its declared facts and writes `risk_event` (and `would_have` when shadowed or when it refused). **The five words ACTIVE, REDUCING, BENCHED, HALTED, RESTORE per scope are derived by the fold (AD-18) from `risk_event` and restore rows; the node keeps the fold incrementally and the snapshot caches it; a restart or a `move_risk` rebuilds state from rows and copies nothing.** A row that says `wait for hand` calls `Runtime.risk_stop` (`runtime.py:2696`), its first producer. Only that row and the kill switch wait for a person. `flatten` mints exit intents through the unit's own exit path. The shipped five halts bind unchanged once their `own.*` statistics exist. Slice 4 lands the fold at unit scope, because it is what these words come from.

### AD-13 Exits stay on the unit in a fixed order; shaped for a quote clock

- **Binds:** S3, I13, V1, V6, F5, PH 2 to 4, 9 to 11 [F12].
- **Prevents:** a pod changing what R means under a record; a faulty exit stopping an exit; a later tick lane reworking the exit answer.
- **Rule:** every exit in `exit_set` runs per bar, fed `PositionFacts` and market evidence, on its side: **an exit reads the bars of the quote that closes it, bid for a long, ask for a short,** so a short's stop sees the spread (today both sides get bid, `unit.py:574-576`) [CHECK S15]. Answers: `close_full`, `close_partial`, `amend_protection`, each with a reason code; a `target_position` type is reserved. On one bar, full beats partial beats amend, and the earlier binding breaks a tie; this is compiled, not configured. The node closes targets as today (`runtime.py:1849-1857`). A raising exit block is skipped with a row and the next runs; if none can run, the step answers a `Fault` and the host's `close_scope` port acts on it: `_close_scope` on the node (`runtime.py:2451`), a close at the next bar's open in QMB. `qml` never imports node code [CHECK S10]. R is a declared basis on the sizer row, gross at the disaster stop by default; stops tighten unless `allow_widen` is set. A pod never touches `exit_set`. **Step 2 now:** stack, `PositionFacts`, side, reasons, fault fall-through. **Step 3 after the demo facts:** signed stop distance, amends, partials on the node, trails, venue-resting targets. **Shaped for later:** `ExitInstance.update` takes an `evidence` mapping whose clock is a field, so a quote clock feeds it later with no answer-type change; the stream input widening (`compiler.py:976-981`) is deferred, not designed around.

### AD-14 Numbers: find, track, correct, on the built engine; authority on every number

- **Binds:** S13, I16, D15 to D17, PH 7, 8, 22, E12, E18.
- **Prevents:** a second moving part; a number nobody can explain; unbounded memory (`engine.py:124`); a learned number touching open trades unasked.
- **Rule:** no applier object. **Find** is a replay in the Lab or at birth, ending in a new version with `Origin.found_by_replay`. **Track** is a `scaled` number, fact times multiple, computed each bar. **Correct** is the built engine (`qml/motion/engine.py`), widened: `_bound_on` and the stamp search (`compiler.py:510-516, 620-631`) accept sizer, control and exit bindings; a bounded window on `SlowState.read`; takes `cadence.at`; its constants (`min_trades`, `shrink_k`, cadence) are editable rows.
- **The whole path, so a number truly moves [CHECK "Does a number really move"]:**
  1. **Stamp.** For a sizer, exit or control number the stamp is the number's own value in force at entry, `number:<name>`, written to the decision row's `numbers_in_force` and carried to the trade row's `entry_stamps`. Today `_stamps` reads logic slots only (`unit_handler.py:223-231`), and `engine.py:122` skips every trade without the stamp, so a compiled risk number would never move. The rule's evidence gains `stamp` beside today's `strength` (`engine.py` `calibrate`) and its declared facts (E12).
  2. **Rule.** One rule ships: `own-r-step@1`, a labelled placeholder that moves its number one step inside its range by the mean R of its own trades, toward `cautious` when that is below zero. It binds to a sizing number and an exit number alike, so slice 7 has something real to run. Presets still ship motion off for size; turning it on is a pointer edit.
  3. **Block.** A block reads every number from `evidence`; `make` only seeds. The shipped `fixed-fraction-at-stop`, `target-r-multiple`, `time-exit-bars` and `swing-stop-buffer` hold the `make` value and ignore a moved one (`block.py:24`, ran in `CHECK`); slices 2 and 3 replace them with new versions, and K9 test 6 fails any block, stdlib or Library, whose answer doesn't change when a bound number in `evidence` changes.
  4. **Receipt.** `numbers_in_force` carries value, default and the calibration row id that set it. `explain_size(row)` prints them, for the sizer's numbers and for the exits' numbers fixed at this entry. The close row names the exit's reason code and the `numbers_at_entry` it used.
  5. **Open positions.** A held position keeps `numbers_at_entry` (`applies_to_open_positions` false), so a sizer or exit number needs no flat unit and moves on its cadence with other markets held. A logic number keeps today's flat rule, read per market, not across all markets (`unit.py:543`), so a many-market scalper can't starve its cadence.
  6. **Restart.** `_OwnJournal` (`runtime.py:1479-1491`) is seeded from the unit's trade rows at start; the engine's watermark drops what the snapshot already read, so `SlowState.read` comes back whether or not a value moved (`runtime.py:2926-2927`).
- **Also in the rule:** **Every number carries:** `derivation` (rule block or fact), `range`, `authority` (`off`, `motion_inside_range`, `at_anchor`), `owner` (`user`, `template`, `learner`), `reason` on the resolved value, `cautious` direction, `guard` (revert and freeze after trips), `never_self_tune`, `applies_to_open_positions`, and a per-change record. A move inside range is a calibration row; outside it a new version. `MotionSwitch` reports with and without. Presets per type turn correct on for filters and off for size. **Evidence stated once:** E5's tables show only that the mechanism behaved as described and did not run away (MODEL); they do not prove the default.

### AD-15 One fact surface with a stated supply and a fail mode

- **Binds:** I1 to I4, I7, I17, `qmf/risk/facts.py` (names), adapters in `qmb/host/facts.py` and `qmn/app/facts.py`.
- **Prevents:** a fact computed differently in two hosts; three meanings of "missing".
- **Rule:** blocks declare the facts they read in `entry.json`; `facts` is one read surface on the unit (`_required_keys`, `unit.py:875`). The compiler compares a unit's needs with the host's provided list; an unmet need names its fallback or warns. Each fact has a timestamp, a source and a fail mode: `open`, `closed` or `neutral`. Facts from the unit's own journal are computed in QML, so they are the same in both hosts by construction. Host facts (equity, margin, cost cells, group facts) have two adapters and a known-answer test. A truly new host fact is a core change and is said to be. **Costs are observed facts:** cost cells per instrument, broker, hour, session and world are written from fills, labelled `uncalibrated` until N, with a class-pooled stressed fallback that decays to measured; the instrument record gains a commission key; two residuals are kept apart (signal before costs; cost against model).

### AD-16 Readings inform, stickers refuse, and neither commands

- **Binds:** S8, S9, S10, I5, I6, R13, F3, Q4, V3, V7.
- **Prevents:** forged `source`; a stale feed reading as calm; a dead desk parking the book; a wide unit trading its whole universe on a stale board (`runtime.py:366-369` docstring).
- **Rule:** `reads` compiles with `publisher`, `fallback` (`compute_here`, `treat_as_absent`, `no_new_entries`, `stand_aside`), stale limit and `valid_until`; the host stamps `source` (`node`, `mis`, `app:<id>`, `agent:<id>`); inputs are named on each record. The relay (`qmx_host/feed_relay.py`) carries any publisher's readings to the node. A node sensor publishes spread, tick rate and quote gaps with source `node`; an overnight job makes one curve artifact per world with an age word and a flagged borrowed cold start, read by SQS, node, MIS and QMB. **Three market lists:** `markets` (allowed), `home_markets`, and `active` as a reading; the fallback of any list or board is home markets, never every listed market. A sticker is a row in the stand-down table (`qmn/app/stand_down.py`) with scope key, kind, strength (`prefer_not`, `no_new_entries`, `flatten`), expiry, resume rule, why, who; a `flatten` sticker is executed by the control runner's `flatten` verb on each member it scopes, through the unit's own exit path (AD-12) [CHECK S13]; a unit's `tolerations` are in its risk section and a pod may stamp them. The kill switch is not a sticker. Each sticker source has a `fail` row; the default is a card and `prefer_not`. An agent-placed sticker can only reduce risk and must expire; under Q4's default it lands a card and applies nothing.

### AD-17 One thread, two passes, an outbox with a time budget

- **Binds:** F4, S18, `runtime.py:2157` (one thread), `:3013-3018` (`_drive`), `:1727-1733` (mint then place), `:1182-1190` (`_protected`), `:1701-1714` (parked entry), `healing.py:64` (30 s watchdog), `unit.py:746-749` (the mint) [G1 V2 AD-7; F1, F2, F7, F10; B2, CHECK S1].
- **Prevents:** a shared cap that needs a lock; an entry's venue wait delaying another unit's exit; a long bell killing the node; a parked entry reading as "warming up" and being dropped; a second order for one signal; a parked entry with no lifetime.
- **Rule:** per node, one `node-runtime` thread hosts all units; caps are atomic because nothing else runs. **Pass 1** steps every unit on every account and sends its exit intents at once; no chain, fold or feed is reachable from exit code (AD-9). Entry proposals are parked in the outbox with `not_before` (the bar's own time, an earliest time) and `expires_at`. **Pass 2** drains the outbox by bar time, then the group's `rank` (then a per-bar hash), calls `price` (AD-1), runs the unit chain and node chain on each, writes the row, sends, and **stops at a time budget** (a labelled placeholder); what is left waits for the next tick and passes both chains again on fresh facts. **Time, in what takes the time [CHECK S1]:** one entry on a venue answering at its limit takes 26 s (4 sends, 3 confirm waits, ran). So pass 2 starts an entry only if elapsed plus that entry's worst case, worked out from the same constants (`runtime.py:179-187`, `ctrader_account.py:110`), fits the budget; and `watch.began` (`runtime.py:2192`) is reset as a progress beat after each exit send and each finished entry, so the watchdog times one stuck step, not a long honest pass. A worst case longer than the watchdog's limit is refused at start, by name. **Parked entry [F7, B2]:** an entry not yet placed is neither skipped nor marked done. `_orders` gains a `Parked(expires_at)` state beside `Unknown`, and `execute_resting` returns `Ok(False)` for it (`runtime.py:1703-1704`); `None` keeps meaning warming up. `expires_at` defaults to the next bar of its market, a labelled placeholder. At the start of pass 1 for that market, an expired entry becomes `Blocked("budget_expired")`, which writes the `Skip` through the existing path (`:1705-1713`). **No second order:** while parked, `own_position` still reads `None`, so the unit would mint again (`unit.py:746-749`; ran in `CHECK` B2: 2 sends, 2 positions at the venue, 1 in the handler). So a `parked:<market>` surface joins the facts `_Run.step` reads (`unit.py:515`), and `_Run.entries` writes `suppressed_limit`, "an entry is parked", when open plus parked reaches the market's limit. The existing `self.unknown` refusal (`runtime.py:1059`) already covers an unknown answer. QMB's `group_run` driver uses the same order. **Known limit:** `client.send` holds a lock and waits up to 5 s (`ctrader_account.py:110, 679`), so entries and exits at one bell go out in series; the budget protects the node, not the fills; meters (pass 1 time, pass 2 time, entries left over, sends per bar) are plain rows, and sends off the thread reopen if measured delay harms fills (section 11).

### AD-18 One decision row and one fold; restart is no reset

- **Binds:** R1 to R4, R7 to R9, R13, S15 [G11 V3 RAT, G12 V3 AD-11].
- **Prevents:** "why this size?" with no answer; two risk states in two readers; a restart acting as a hidden accelerator.
- **Rule:** the size trail is the decision row. `explain_size(row)` is one pure function used by developer, copilot, UI and triage; `replay_decision(row)` re-runs the sizer on the row's stored inputs and must match, by test. `fold(rows, scope, clock) -> RiskState` is one pure function over journal rows, keyed by scope including `position`, `unit`, `pod`, `group`, `account`, `tag`; it derives control words, cushion ledgers, open risk by bet key, drawdowns and distances; UNKNOWN when any needed input is stale. It is used for the group ledger (in process), the pod card, the fleet read, agents, and restart replay. **Restart rules:** an anchor's id is a pure function of clock and time, so settling anchors is idempotent; recovery folds journals and broker deals before answering any entry; anchors passed while down are derived once, latest wins, marked `restart_late`; **cuts stand; a raise earned before the restart waits for the next anchor**; stickers expired while down are settled from the table; until the group ledger is rebuilt, group caps read UNKNOWN and refuse entries, exits free. **Proposal tape, handed to methodology:** a size search replaying a unit's entry proposals under a different risk section is methodology's tool. Only the row shape is reserved here (`proposal`: market, side, reference, stop or basis, tags, numbers in force); this build ships no writer and no search.

### AD-19 Land in slices; bump only on a changed decision

- **Binds:** F6, K7, K8, K9, D41.
- **Prevents:** half-shapes reaching a deployed unit; a frozen compiler.
- **Rule:** the order in section 10. Each slice ends in something a test or K7 shows. Format bumps are free until the first live deployment, and there is one per changed compiled decision, so no G record goes stale silently; format 5 lands in slice 1, and later slices bump when they change a decision (slice 3's side-correct bars and time exit do) [CHECK S5]. Step 3 lands before the first live deploy or pays a re-test through K8. Three stop points (A, B, C) each leave a whole baseline.

### AD-20 The fixed lines are tests; everything else warns

- **Binds:** V1 to V6, V9, K5, K9.
- **Prevents:** the lines resting on good behaviour; a canvas that refuses reckless paintings.
- **Rule:** exits never blocked (property test); only the owner lowers a kill level; agents never place, size up, lower a kill level or promote, by tool table (`tools/money_path_scan.py`); a click binds to a hash; no channel the copilot or agents can read carries the promote door; a protected field list (floor, kill level, `never_self_tune`, plan hash) has no agent write path. Every other reckless setting (no kill line, no caps, full Kelly, a widened stop, a stopless live unit) warns and grades in the largest type and never refuses. **What else refuses, each with its way out [CHECK S7]:**

| Refusal | Way out |
|---|---|
| Margin headroom, order rate and size band vetoes, a stop past liquidation (PH 14) | One row each in the node chain, with `enabled`; off makes it a warning |
| A stop past entry | `allow_widen` on the row |
| A recipe touching an exit or a logic-bound number (AD-4) | Not a safety line: it is a logic edit, so make a new version and G run |
| `routes`, `plain_python`, `roll` | Not built or no venue: `plain_python`'s door is a Library block; `roll` waits on Q2 |
| A minimum lot, a closed market, an order form the venue lacks, a missing rate on a size in money | What the venue or arithmetic can't do; a named skip, never a law |

### AD-21 Who owns what: block-running code lives in `qml`; `qmf-risk` holds types

- **Binds:** every module in section 7 [F8].
- **Prevents:** a runner in `qmf-risk` that cannot import `qml.blocks.api` (`packages/qmf-risk/pyproject.toml` depends only on `qmf-core`; `qml/pyproject.toml` depends on `qmf-risk`); `qml` gaining `qmf-data` and with it `pyarrow` and `duckdb` (`tools/workspace_meta.py:72` and `tools/tests/test_workspace_structure.py:138` forbid it, DEC-0180).
- **Rule:** the dependency direction is fixed as drawn. Verdict, fact, control-row and group types live in `qmf-risk` so both hosts and the wire share them. Anything that runs a block (the control runner, the unit chain, the node chain runner, group caps, `expand`, `roll_plan`, `explain_size`, `fold`) lives in `qml`. **`qml` allows only `qmf-core`, `qmf-registry` and `qmf-risk`. Row shapes live in `qml` (`DecisionRow`, `unit.py:153`, as today) or `qmf-risk`; `fold` and `explain_size` take plain mappings; hosts own journal kinds and reading [B6].** Hosts (`qmb`, `qmn`) import `qml` and `qmf-data` and adapt facts, ports, lanes and journals. `qmx-host` and apps import `qml` for plans and the fold, never the hosts.

```mermaid
flowchart LR
  CORE["qmf-core"] --> RISK["qmf-risk: wire, verdict, fact, row, group types"]
  CORE --> DATA["qmf-data: journal kinds, codes"]
  RISK --> QML["qml: document, compiler, HostedUnit, chains, controls, exits, convert, motion, pods, fold, explain_size"]
  QML --> QMB["qmb: UnitSliceHandler, replay facts, group_run"]
  QML --> QMN["qmn: runtime two passes, node facts, node links, sensor, stand-down, outbox"]
  QML --> HOST["qmx-host: promote, roll, relay, landers"]
  DATA --> QMB
  DATA --> QMN
  DATA --> HOST
  HOST --> APPS["qmx-apps, qmx-engine templates, copilot tools"]
```

### AD-22 The no-stop path is one declared basis through every place that reads a stop

- **Binds:** PH 11, I13, S6, and every place listed in the Rule [F6, B9].
- **Prevents:** a stopless entry compiling, sending, and then being closed by the protection wait, by the next tick's stop restore, or by the reconcile; a gate on another order path refusing what the entry path accepted; R with nothing to divide by.
- **Rule:** a unit with no price stop declares `basis: tail_budget` on its sizer row. The send row carries `stop_kind: none_declared` (already on the wire, `unit_intent.py:69-73`), and **every reader asks that field before it treats a missing stop as a fault**. "Six places" was wrong; `CHECK` B9 ran a stopless position through one real tick and it was closed. The list, each one with a test:

| # | Place | Today | With the declared basis |
|---|---|---|---|
| 1 | Compile, `compiler.py:500-506` | `stop_not_built` | Lifted for a declared basis |
| 2 | `enter`, `unit.py:764-766` | Skips on no stop | Proposes with no stop; target levels that need a stop are refused at compile |
| 3 | Handler entry, `unit_handler.py:560` | `Decimal(protection["stop"])` | Reads `none_declared` |
| 4 | Node entry, `runtime.py:1065` | Same, then measures a distance | Reads `none_declared`; no measured distance |
| 5 | Veto, `runtime.py:1102-1106` | Refuses unless the venue's stop form is proven | Accepts the basis; warns in large type |
| 6 | Post-send wait `_protected`, `runtime.py:1182-1190` | Closes and alarms | Not entered |
| 7 | Each tick, `_restore_stops`, `runtime.py:2358-2386`, calling `restore_stop(None)`, `:1192-1212` | **Closes, raises `protection_escalation` (ran)** | A declared position isn't `missing` |
| 8 | `NodeUnit.adopt`, `runtime.py:1636` | `send["stop"]` | Adopts with no stop, through a restart |
| 9 | Reconcile, `reconciler.py:379-390` | Unprotected: alarm and close | Declared on its send row counts as protected |
| 10 | `safe_to_restart`, `runtime.py:2288-2289` | "has no stop at the venue" | Names it "open, no stop by declaration" |
| 11 | `_money`, `_close`, `unit_handler.py:578, 669-673` | Risk from the stop | `held.risk` is the sizer's declared money at risk at fill, so R stands |
| 12 | Venue adapter, `ctrader_account.py:1454-1456`; `paper_lane.py`; `ConformanceAccount`, `runtime.py:698` | Rejects `no-stop` (the first) | Sends with no stop where the venue allows it |
| 13 | Other order paths, `order/path.py:561`, `venue/live.py:1012` | Gate | Each checked by one test |

The converter divides money at risk by the declared distance. **UNKNOWN: whether cTrader accepts a market order with no stop;** it joins R24's probes. If it does not, venue capability refuses the true no-stop form at compile on that venue, by name, and the far stop stays the form there. The shipped template default is a far disaster stop with the cut in front; the true no-stop form is expressible and warned. **The test (K9 12):** a stopless entry held for N bars on the fake broker, then through a restart, still open, with no `protection_escalation`, then closed by its own cut.

### AD-23 A fault costs its own unit's entries, never an exit, never another unit

- **Binds:** V1, `runtime.py:3013-3018, 3040-3046, 2193-2200`, `unit.py:530-536`, K9 test 2 [B1].
- **Prevents:** one raising block stopping exits in its own unit and in every unit hosted after it (`CHECK` B1 ran it: 12 bars, `dep-1` driven 11 times, `dep-2` zero times, 11 heals, both still read `trading`).
- **Rule:** plain `try`, no threads, from slice 3.
  1. **Inside the unit.** `_Run.step` runs `update`, `exits`, `entries` and `motion` as separate phases. A raise in `update`, `entries` or `motion`, and in `price` (sizer, modifier, converter), becomes a `Fault(block, phase, code)` on the answer: that market takes no entry on this bar, `exits` still runs, and its intents survive. Exit blocks hold their own instances, so a broken logic block can't corrupt them.
  2. **Across units.** `_drive` holds one `try` per unit. A raise past `_Run.step`, from host or handler code, is a `Fault` for that unit, and the next unit runs. A refusal from `close_frontier` caused by a fault is a `Fault`, not `Phase.STOPPED`, so the driver keeps stepping it (`runtime.py:3014-3015`). `step()`'s heal stays for what is outside `_drive`.
  3. **What a fault does.** It writes `risk_event` with code `unit_fault`, turns that unit's entries off inside `HostedUnit` (so both hosts behave alike), and lands one card per root-cause key. The fold reads the word BENCHED. The phase stays `TRADING`. Entries come back by rule after `fault_clean_bars` clean bars, a labelled placeholder; `hand` is one field away.
  4. **Last fall-through.** If a held position's exits could not run for `exit_fault_bars` bars in a row (a labelled placeholder), the host's `close_scope` port closes it (AD-13). Venue stops hold in the gap.
- **The test (K9 2):** one logic slot raises on `dep-1`, one sizer raises on `dep-3`, `dep-2` and `dep-4` hosted behind them, 12 bars on the fake broker. Every unit is driven on every bar, zero heals, `dep-1`'s own time exit fires, `dep-2`'s per-bar exit and node-closed target fire, `dep-1` mints no new entry, the fault row and the card exist, and entries come back after the clean bars.

### AD-24 A draft reaches paper on his click, with the safety half of G and no judge pass

- **Binds:** `qml/lifecycle/machine.py:105-117`, `promote.py:376, 565-578`, K7, section 6 [B3].
- **Prevents:** a template that "can trade" refused at its first promote (`CHECK` B3 ran it: `not_in_table`; `TESTED` needs a judge `pass`, whose default needs 100 trades, `presets.py:45`); his M49 line "All of them can trade. No one is refusing them" waiting on the methodology session.
- **Rule:** the table gains one row, `Transition(DRAFT, PAPER, HIS_CLICK)`. It needs what `Promoter._admit` already demands on every lane: a G record with `safety_passed` for this logic fingerprint (`promote.py:376, 565-578`). Paper touches no money. `TESTED` and the judge keep their meaning and path. `PAPER -> LIVE` stays his click with placeholders acknowledged (`machine.py:109`, `promote.py:390-395`). The card says "a shape, not an edge" either way. `tools/first_real_start.py`'s header, which says a unit reaches a node by passing the judge (`:8`), changes with it. **The test:** K7 with no judge run reaches a filled paper entry.

### AD-25 One feed builds one base bar; streams roll up; positions are keyed by position

- **Binds:** S17, E4, `streams_not_built`, `runtime.py:2774`, `ctrader_account.py:115, 1371`, `unit_handler.py:261, 286`, `runtime.py:1802`, `unit.py:517` [B4, CHECK S9].
- **Prevents:** a 1-minute and a 15-minute unit refusing each other on one account (`CHECK` B4 ran it both ways); templates that compile and then refuse at the node; two builders inventing two meanings of "second stream"; a second position overwriting the first in `_held`.
- **Rule:**
  - **Base bar.** An account's feed builds one base bar, `[node] ctrader_bar_s` (`ctrader_account.py:115`), whose labelled default moves from 900 to 60 seconds. `_host` refuses only a stream that isn't a whole multiple of the base, by name.
  - **Roll-up.** `qml/feed/rollup.py` is one pure function both hosts call: base bars in, a closed `QuoteBar` or nothing out. Both quote sides. Buckets align to epoch as the feed's own do (`:1371`). `knowable_at` is the bucket's end. A bucket closes on the first base bar at or past its end. A bucket not seen from its start (restart, reconnect, `:1317`) is dropped and never emitted, so no partial bar reaches a block.
  - **Keys.** Handler and node windows key by `(stream, market)`; the stream id on the accumulator names both. `plan.stream` becomes `plan.streams` with a `primary`, the fastest: the unit steps when the primary closes, and reads a slower stream at its last closed bar, with no look-ahead (`unit.py:524`). Warm-up counts per stream. A unit hosted on a bar it doesn't read isn't driven.
  - **Positions.** `_held` and `open_positions` key by position id. `own_position:<market>` answers a tuple. `position_limit` compares open plus parked (AD-17), per market and per open. Each exit intent carries its `position_ref` (`runtime.py:1802-1803` reads it already). `position_limit` above 1 on a netting venue is refused at compile by venue capability (`nets_positions`).
- **The test (K9 17):** a 1-minute, a 5-minute and a 15-minute unit on one account of the fake broker all trade from one feed; a two-stream unit reads no future bar; rolled bars match bars built directly; two positions on one market each get their own exits.

## 3. Contracts, sketched

Each lands in the package named (AD-21). New fields are additive on `qmx.unit/1`, passed through the census test and the upgrader chain.

### Sizer, modifiers, converter (`qml/blocks/api.py`, `qml/numbers/convert.py`)

```python
class Amount:                      # sizer answer; exactly one kind
    kind: Literal["money_at_risk", "notional", "quantity"]
    value: Decimal
    basis: Literal["gross_at_stop", "tail_budget"] | str
class Skip: reason: str
class SizerInstance(Instance):
    def update(self, evidence: Facts | Mapping) -> Amount | Skip | Size: ...   # Size = legacy quantity

class Factor: value: Decimal; range: tuple[Decimal, Decimal]; reason: str
class ModifierInstance(Instance):
    def update(self, evidence) -> Factor | None: ...        # None is neutral, with its fail mode

def to_quantity(amount, entry, stop_or_basis, record, rate: Fact, rule: RoundRule) -> Converted
class Converted: quantity: Decimal; residue_r: Decimal; skipped: str | None   # rate_stale, rate_absent, below_min_lot...
class ConversionRef: market_id: str; invert: bool
class InstrumentRecord: conversions: Mapping[str, ConversionRef] = {}         # key: account currency; records.py:46
```

### Exits (`qml/blocks/api.py`, `qml/protocol/exits.py`, new)

```python
class PositionFacts:               # widens OwnPosition (unit.py:128-137) from HeldPosition
    position_id; side; quantity; average_price; stop; targets; bars_held; mfe_r; mae_r
    opened_by_logic; stage; numbers_at_entry
class ExitAction:
    kind: Literal["close_full", "close_partial", "amend_protection", "target_position"]   # last reserved
    fraction: Decimal | None; new_stop: Decimal | None; reason_code: str
class ExitInstance(Instance):
    def update(self, evidence) -> Decimal | Signal | ExitAction | None: ...   # evidence.clock is a field; series is the closing quote's side
```

### Controls (`qmf/risk/controls.py` types; runner in `qml/protocol/controls.py`, new)

```python
class ControlRow(ScopedBinding):   # lands in Halts; scope gains GROUP, TAG
    reads: tuple[str, ...]; verb: Verb; on_fire: OnFire; restore: Restore
    until_n: ColdRule; shadow: bool; enabled: str | bool = True   # a fact name gates the row
    # defaulted: attack, release, counting, fail_mode, money_series, klass, healthy_fire_rate
class Answer: verb: Verb; factor: Decimal | None; reason: str; code: str
class ScopeState: word: Literal["ACTIVE","REDUCING","BENCHED","HALTED","RESTORE"]; since; reason   # derived by fold
class Fault: block: str; phase: Literal["update","entries","price","motion","exit","host"]; code: str   # on UnitStep; AD-23
class HostPort(Protocol):
    def close_scope(self, unit: str, why: str) -> None: ...   # node: _close_scope; QMB: close at the next bar's open
```

`HaltInstance` keeps `update(evidence) -> Halt | None`; `Halt.action` gains `reduce` (`blocks/api.py:168-179`).

### Numbers (`qml/unit/model.py`, `qml/motion/engine.py`)

```python
class NumberSpec:                  # existing fields stay
    derivation: BlockRef | FactRef | None
    authority: Literal["off", "motion_inside_range", "at_anchor"]
    owner: Literal["user", "template", "learner"]
    reason: str; cautious: Literal["down", "up", "hold"]; guard: Guard | None
    never_self_tune: bool; applies_to_open_positions: bool = False
    stage_values: Mapping[str, str] = {}
class Motion:                      # adds
    scaled_fact: str | None; window: int | None; anchor: CadenceAt | None
    min_trades: int; shrink_k: Decimal        # were constants (engine.py:39-44)
class SlowState: read bounded to Motion.window
class SlowNumber: stamp: str                  # a slot binding name, or number:<name> for a sizer, exit or control number
# rule evidence: trades [{stamp, strength, r}], current, declared facts      # own-r-step@1 ships; strength stays for trend-floor
```

### Document additions (`qml/unit/model.py`, `qml/unit/sections.py`)

```python
class Unit:                        # new optional fields only
    modifiers: tuple[Binding, ...] = ()
    gates: tuple[Binding, ...] = ()           # gate slot; verbs block, shrink, wait, warn, shadow, none
    tolerations: tuple[str, ...] = ()
    stages: Stages | None = None
    risk_locks: tuple[str, ...] = ()
    recipe: RecipeRef | None = None           # pod id, version, hash, displaced; outside both fingerprints
    home_markets: tuple[str, ...] = ()        # allowed = markets; active arrives as a reading
    tags: tuple[str, ...] = ()                # group selectors, fold scope
class Read: publisher: str; valid_until_s: int | None; fallback gains STAND_ASIDE     # model.py:391
class Stages: selector: str; anchor: CadenceAt; hysteresis: Decimal
              move_up: Literal["rule","card"]; move_down: Literal["rule","card"]; rows: Mapping[str, StageRow]
class StageRow: sizer: Binding | None; modifiers; controls; numbers
def sections(document) -> tuple[LogicSection, RiskSection]      # the one partition
class CompiledUnit: logic_fingerprint; risk_fingerprint          # beside compiled_fingerprint
class HostedUnit:
    def on_instant(...) -> tuple[ExitIntents, Proposals]        # pass 1
    def price(self, proposal, facts, admit: AdmitPort) -> Decision   # pass 2; a raise is a Fault (AD-23)
    def move_risk(self, new_compiled) -> Moved | Refused
class UnitStep: faults: tuple[Fault, ...]                         # beside today's fields, unit.py:187
class Parked: expires_at: Instant                                 # beside Placed, Blocked, Unknown in _orders (qmn)
def roll_up(base_bars, seconds) -> QuoteBar | None                # qml/feed/rollup.py, AD-25
# surfaces: bars:<stream>:<market>, own_position:<market> (a tuple), parked:<market>
```

### Pod and group (`qml/pods/`, `qmf/risk/group.py` types, `qml/group/caps.py` runner; Library kinds `pod`, `group`, `template`)

```python
class Pod:   # qmx.pod/1, a real schema behind kinds/pod.schema.json
    pod_id; version; method: str; slots: PodSlots; notes
class PodSlots: sizer; modifiers; gates; controls; reads; numbers; tolerations; stages   # empty = unit's own

def expand(unit, pod) -> Unit | Refusal
class MemberPlan: deployment_id; outcome: Literal["risk_only","unchanged","locked","logic_touch","refused"]
                  old_risk: str; new_risk: str; diff: tuple[Edit, ...]; problem: str | None
class RollPlan: pod_hash; members: tuple[MemberPlan, ...]; plan_hash: str; made_at; expires_at
def drift(members, pod) -> tuple[Drift, ...]           # member, row, recipe value, found value

class Group:   # qmx.group/1, replaces the book and bms shells; "Classic Book" stays a recipe name
    group_id; display_name; parent: str | None; selector: Selector; place; side; version
    money: Money; limits: Mapping[str, Decimal]          # published as facts on group:<id>
    caps: tuple[ControlRow, ...]; ledger: LedgerSpec
    rank: Mapping[str, int]                              # by member; ties by a per-bar hash; an order slot is added when content needs it
    alarm_budget; share_cap
class Selector: units: tuple[str, ...]; tags: tuple[str, ...]
class LedgerSpec: anchors; series: Literal["realised","marked","committed"]; keys: tuple[str, ...]
class CapAnswer: Pass | Shrink(quantity, reason) | Refuse(reason)
class Preset:  # Library kind `template`, un-retired: overrides only
    template_id; base: str | None; overrides: tuple[PointerEdit, ...]; pins; label; lineage; version
```

### Chains and facts (`qml/protocol/entry_chain.py`, `qml/chain/node_chain.py`, `qmf/risk/chain.py`, `qmf/risk/facts.py`)

```python
class Verdict: link: str; verb: Literal["pass","shrink","wait","warn","shadow","refuse","none"]; reason; code
               inputs: tuple[FactUsed, ...]           # name, value, at, source, state
class AdmitPort(Protocol):
    def admit(self, wire: Mapping, at: Instant) -> Admitted | Refused: ...    # wire quantity rewritten on shrink
# Facts: Fact(value, ts, fail_mode, source, state: ok | stale | absent | uncalibrated)
# account.* currency, equity, balance, open_risk, open_risk_by_bet_key, margin_headroom, liquidation_distance,
#           budget_share, realised_since(anchor), basis
# own.*     session_loss_r, loss_streak, losing_day_streak, session_fills, spread_r, edge_band,
#           cut_distribution, trade_rate, record_n, open_risk_by_bet_key
# market.*  rate:<quote>, quote, spread, tick_rate, quote_gap, cost_cell(hour, world), curve, gap_factor,
#           sticker(kind), session_state, event_clock
# group.*   day_pnl, open_risk, members, cushion, raise_ok, share, stage, limit.<name>
# node.*    kill_level, paused, venue_ready
def fold(rows, scope, clock) -> RiskState
```

### Status and records (shapes in `qml` and `qmf-risk`; journal kinds in `qmf-data`, read and written by hosts, AD-21)

```python
class RiskState: scope; word; since; reason; stamp; money; open_risk; drawdowns; control_distances
                 cushion; stage; unknown: tuple[str, ...]
class DecisionRow:   # existing, qml/protocol/unit.py:153, adds
    numbers_in_force: Mapping[str, NumberUsed]   # value, default, calibration row id
    inputs: Mapping[str, Fact]; steps: Wanted, Approved, Filled; verdicts: tuple[Verdict, ...]; binding: str
    logic_fp; risk_fp; recipe; group_id; stage; readings_used; trace_id; propensity; placeholders
    written_before_send: bool
```

Rows written: decision row v2, trade row v2 (R2 plus `stage`, `pod_version`, `risk_fp`, `target_held_by`, `entry_stamps` and `numbers_at_entry`, those two from slice 7), `would_have` (with `propensity`), `risk_event` (root-cause key, event id, alert fields, appendable codes, `unit_fault` first, in slice 3), calibration row, `stage_move`, `risk_move` (plan hash, member, old and new risk), fill record (R7: decision quote, arrival quote, fill, partial, reject, requote, markouts), reading record (R13, stamped at compute, as-of query), run stamp (R8, `group: none | alone | merged`), `drift`. The `proposal` row's shape is reserved with no writer (AD-18). `explain_size(row) -> Trail` lives in `qml/receipt.py`.

### Consistency conventions

| Concern | Convention |
|---|---|
| Time | Every fact and row carries an `Instant`; readings carry `knows_at` beside event time; an anchor id is a pure function of clock and time |
| Money | `Decimal`; the account's currency at the seam; one conversion, by the `market.rate` fact (AD-10); every money figure passes it, `_account()` included; rows keep the quote figure and the rate used |
| Codes | Closed, appendable reason codes; a new family per user block; a new text without a code fails QMB as R15 says; live writes `unlisted` |
| Writers | Spec is written by people and drafts; status, rows and the fold by the runtime; `source` by the host, never the publisher |
| Failure | Typed refusals in the block protocol; a raise is a `Fault` by plain `try` (AD-9, AD-23); a block that never returns is `StuckWatch`'s, a restart (AD-9); nothing raises into `close_frontier` |
| Labels | Every shipped value carries `origin: placeholder`, a reason, a range and the owner "numbers talk"; the card shows the label |
| Words | Unit, block, recipe (a pod document), pod (on screen: recipe plus group), pod version, method, group, desk, sticker, toleration, fold, trail. "Book + BMS" is a method name; "Classic Book" a recipe name |
| Windows | First class: `spawn` only, whole-then-replace file writes, no POSIX-only calls, `tzdata` pinned; the entries pass's time budget is tested on Windows |
| Clicks | A click binds to one hash (plan, group row version, deployment) and is refused when stale |

### Stack

No new runtime dependency.

| Name | Version |
|---|---|
| Python | 3.14, as pinned at the tip (`requires-python >=3.14,<3.15`) |
| QML compiler format | 4 at the tip; 5 in slice 1; free bumps, one per changed decision, until the first live deployment |
| uv build backend | 0.12, as pinned at the tip |

## 4. The core list, in this shape

Every live row of FUNNEL section 3 lands or is struck with a reason.

| Rows | Here | Slice | Struck or changed, and what replaces it |
|---|---|---|---|
| S1 | AD-10 | 2 | None |
| S2 | AD-11 | 6 | None |
| S3 | AD-13 | 3, 17 | None |
| S4 | AD-12 | 4 | `placement` struck: a row runs where its document says (unit or group). States derived by the fold, not a state machine |
| S6 | AD-9, AD-17 | 10, 11 | "One chain" struck: two chains, one row, a plain `try`. "Group stage" becomes the group-cap link in the node chain, slice 12. "A hung link refuses entries only" is deferred with the worker process, by the lead (AD-9, section 11) |
| S8 | AD-16 | 14 | None |
| S9 | `sessions` compiled and a window card kind | 9 | None |
| S10 | AD-16 | 10 | None |
| S11 | Scope list on rows and fold keys | 4; 10 stickers; 12 tag | None |
| S12 | Roles run in the logic section, except `sizing_modifier` (AD-11) and `derivation` (AD-14); `combiner` gains `product`, `min` | 6, 7, 9 | None |
| S13 | AD-14 | 7 | None |
| S14 | AD-2 to AD-7 | 1, 13 | Empty pod struck: no recipe is the default. Pod reference on the deployment struck: `recipe` in the document, `group_id` or selector on the group. **The deployment key stays, as unit version, market, lane and recipe hash, so a second deployment of one version keeps its seat for paper twins (FUNNEL 3.8, `promote.py:422-447`).** "Two fingerprints" are logic and risk. Slot composition rules live in `PodSlots` and AD-11. Click rule kept |
| S15 | `HostedUnit` plus `UnitSliceHandler` are the evaluator; node, paper and QMB are drivers through `AdmitPort`, `FactSource`, exec port; conformance tape in K9; `group_run` for multi-unit replay. Lab replay joins as a driver when a Lab exists | 2, 11, 12 | Needs list stays (AD-15) |
| S16 | `library-items` lander, real `pod`, `group`, `template` kinds, `blocks_save` door, Library block traced end to end before "one folder" is promised | 13, 14 | None |
| S17 | AD-25, `position_limit` per market and per open, second stream, per-market settings through I16's market key | 9 | None |
| S18 | `OrderSpec` on the intent, `not_before` as the timing offset, partial close on the node (step 3), netting as a setting, venue capability from I4 at compile | 9, 11, 17 | None |
| I1 | AD-15 | 2 (type, rate), 8 | None |
| I2 | AD-15 | 8 | None |
| I3 | AD-10 (conversion), section 5 PH 17 | 2, 8 | None |
| I4 | AD-10, shipped records, record keys | 2, 5, 8 | None |
| I5 | AD-16 three lists, home fallback | 14 | None |
| I6 | AD-16 one curve artifact (F3 B held) | 10 | None |
| I7 | `knows_at` beside event time on every reading record; bars gain time of day; volume or tick count on bars waits on Q2 with the field reserved | 14 | Additive: no core rework if the rest arrives later |
| I9 | Identity on every row | 1 fingerprints apart; 5 `tags`, family, world; 9 bet key and driver tags on intents; 14 provenance, claim, generation stamp with the save door | None |
| I10 | AD-7, AD-8 | 12, 13 | "Pod may change rows at an anchor" becomes compiled-in stages or a live group fact |
| I13 | AD-10, AD-22 | 2, 11 | None |
| I16 | Override chain's market key | 9 | None |
| I17 | A pure verdict (can one minimum lot at this stop fit the share, through the one converter), shown on the unit's card and re-run at anchors; its shed, concentrate or borrow rules are content | 8 | None |
| R1 | AD-18 | 2 | Gains `written_before_send`, stored inputs and `numbers_in_force` |
| R2 | AD-18 | 7 stamps, 8 | None |
| R3 | AD-18 | 4 | None |
| R4 | AD-18, AD-23 | 3 first writer, 4 | None |
| R7 | Fill record | 8 | None |
| R8 | Run stamp (`group`, quote source, gate settings, costs, real-tick share) on every run; arm id, link id and parent on run records | 5 stamp; 15 arms | Arms are additive; `tries.py` keeps counting until then |
| R9 | AD-18 | 4 unit, 12 group, 13 pod | None |
| R13 | AD-16 | 14 | None |
| R17 | AD-5 section column; forwarding map | 13, 16 | None |
| K2 | Section 8 doors: app read door widened to journals and the fold; card path to "Needs you" | 15 | None |
| K5 | AD-20: protected field list and channel isolation test on the promote door; extended to the group row's click and the plan hash | 5; 12, 13 | None |
| K7 | Section 6, AD-24 | 5; 10 every template | None |
| K8 | Section 7 | 16 | None |
| K9 | Section 7's list, each test named with its slice | 0 onward | Adds: import test on exit code; parked-entry test; no-stop survival; self-configuration; currency; one feed |
| V1 to V7, V9, V10 | AD-20, AD-1, AD-9, AD-13, AD-23 | With the tests above: V1 3, 11; V2 to V6 5, 12; V7 5; V9 2; V10 2 | V10 holds for arithmetic; group facts differ in a solo run (stamped `group: none`) |

Refusals (FUNNEL 3.8): all placed as that table says, with AD-20's way out for each; the census carries the table.

## 5. The swap: 31 placeholders and 18 extra sockets

**Verdict words** (SWAP's): SWAP, a block or setting changes; WIDEN, the socket changes first; WIRE, the piece exists and gets a caller; KEEP. Slice numbers are section 10's.

| PH | Placeholder | Verdict | How, in this shape | Slice |
|---|---|---|---|---|
| 1 | Sizer `fixed-fraction-at-stop@1` | WIDEN then SWAP | `Amount`, converter with its rate, face check, receipt from the answer; `@2` answers money at risk and reads `fraction` from evidence; grown block reads `account.*` and `market.cost_cell`; forwarding map `@1 -> real@1` (R17) | 2, 8, 16 |
| 2 | Stop `swing-stop-buffer@1` | WIDEN | An exit block fed `PositionFacts`, the closing quote's bars, its number from evidence; may `amend_protection` at step 3 | 3, 17 |
| 3 | Target `target-r-multiple@1` | WIDEN | Reads `multiple` from evidence, so a moved one lands on the next entry; second target and fractions after step 3; one fixed level stays valid | 3, 7, 17 |
| 4 | Time exit `time-exit-bars@1` | WIDEN | Side passed (`unit.py:450`), real evidence (`:686`), the block's own reason (`:690, 701`) | 3 |
| 5 | Halts | WIRE and WIDEN | Five shipped blocks bind as control rows; `own.*` statistics computed in QML; `risk_stop` producer | 4 |
| 6 | Cross-unit hook | WIDEN and WIRE | Replaced by `AdmitPort` and the node chain, called in both hosts; `PASS_EVERY_ORDER` deleted | 11 |
| 7 | Motion of risk numbers | WIDEN | AD-14's six steps; `own-r-step@1` ships | 7 |
| 8 | Moved values and open positions | WIDEN | `applies_to_open_positions` lifts once `amend_protection` runs | 7, 17 |
| 9 | Stop amendments | WIRE and WIDEN | `amend_protection` answer; `allow_widen` row; signed distance (repair's `known-1`) first | 3 (answer type), 17 |
| 10 | Partial closes | WIRE (QMB), WIDEN (node) | Answer type now; node close with a quantity at step 3 (`runtime.py:1807-1808`) | 3, 17 |
| 11 | No price stop | WIDEN | AD-22: all thirteen places | 11 |
| 12 | Rounding, minimum lot | WIDEN | The one converter with a `RoundRule` and a rate; hosts stop re-rounding after their first check; residue real | 2 |
| 13 | Gap through the stop | KEEP | `market.gap_factor` fact a sizer may read | 8 |
| 14 | Margin and liquidation | WIRE then WIDEN | `account.margin_headroom`, `liquidation_distance` facts; order veto refuses a stop past liquidation | 8, 11 |
| 15 | Leverage and spec changes | WIRE | Record change calls `Runtime.stand_down(SPEC_CHANGE, ...)`; writes a `spec_change` sticker | 10 |
| 16 | Funding and swaps | KEEP | Cost cell and a fact a block may read | 8 |
| 17 | Account facts | WIDEN | Live account surface on the node: timed balance re-read, open risk at stops, margin, `budget_share` on the deployment; marked equity when the venue gives it, `basis` stated | 8 |
| 18 | Kill effects per level | WIDEN | `guard` becomes a node-chain link reading the table for `stop_entries` and `cancel_resting_entries`; values open | 11 |
| 19 | Protection that cannot be placed | WIDEN | `protection_escalation` row: `close` or `alarm`; constants (`runtime.py:179-187`) become settings; `hedge` content | 11 |
| 20 | Kill line's verb | WIRE | A group cap reading `group.money` and a floor fact, `on_fire` per group; the floor survives restart (V5); `qmn/capital/kill_line.py` subtracted | 12 |
| 21 | Two units on one netting symbol | WIDEN | A setting in S18; stays refused until attribution is built | 17 |
| 22 | Starting numbers for live | SWAP | Works once risk numbers calibrate (PH 7); two-part snapshots carry | 7 |
| 23 | The one automatic move | WIRE | A control row with `wait for hand` calls `risk_stop`; `flatten` through the exit path | 4 |
| 24 | Paper after a risk stop | SWAP | Lifecycle table edit; a restore rule may send a member to paper | 4 |
| 25 | Risk events in journals | WIRE | Writers; new code family for user blocks (R15 census) | 4 |
| 26 | Judge with unit sizer and fixed size | WIRE | `MotionSwitch` here; the fixed-size rerun and the judge rule are methodology's, on the reserved `proposal` row | 15 |
| 27 | Correlated judging | KEEP | Tries; the live control is the bet key and group cap | 12 |
| 28 | Decay alarm | SWAP and WIRE | Template replaced by the fleet fold; nightly per-unit card off | 15 |
| 29 | Fields to replay sizing | WIRE | Decision row v2 with inputs, trade row v2, `would_have` writer | 2, 4, 8 |
| 30 | Size the venue receives | KEEP | The converter's quantity equals the sent quantity (test kept) | 2 |
| 31 | Pods | Built here | AD-4 to AD-7, slice 13 | 13 |

| E | Socket or limit | Verdict | How | Slice |
|---|---|---|---|---|
| E1 | `reads` refused | WIDEN | AD-16 `reads` with publisher, fallback, stale, `valid_until`; `reading:<id>:<market>` surface | 14 |
| E2 | Eleven roles do not run | WIDEN per role | `sizing_modifier` in the risk section (slice 6); `veto`, `cooldown`, `invalidation`, `re_entry`, `arming`, `timeout`, `regime_detector` in logic slots; `derivation`, `combiner` added | 6, 9 |
| E3 | Exits at unit or account scope | WIDEN / stays | Unit scope lifts with S17; account scope stays an exit refusal: it is the control verb `flatten` | 9 |
| E4 | One position per market | WIDEN | AD-25; `position_limit` per market and per open | 9 |
| E5 | Per-market settings | WIDEN | `settings_record` per market through I16's market key | 9 |
| E6 | `sessions` | WIDEN | Compiled with the record's clock; window card kind | 9 |
| E6 | `context_needs` | WIDEN | A read on a second instrument with aligned clocks; currency conversion doesn't wait for it (AD-10) | 14 |
| E6 | `routes`, `plain_python`, `roll` | stays refused | One venue; the Library block is the Python door; `roll` waits on a futures route (Q2); the record field is reserved on I4 | none |
| `streams_not_built` | Second stream | WIDEN | AD-25; template A's 1m and 5m | 9 |
| E7 | Spread, SQS, news in `guard` | WIRE | Gate slot in the unit chain; node sensor; stickers | 10 |
| E8 | Sizer slot has no type check or ceiling | WIDEN | Face check; size band in one row | 2 |
| E9 | `_CEILING = 0.005` in the contract test | WIDEN | Fixed first | 0 |
| E10 | Exit contract test feeds refused evidence | WIDEN | Fixed first | 0 |
| E11 | Library blocks not enrolled | WIDEN | Enrolled in the contract test | 0 |
| E12 | Motion rule gets only `{strength, r}` | WIDEN | Rule reads stamp, R and declared facts | 7 |
| E13 | `r_after_costs` holds no costs | WIDEN | Trade row v2; R17 says what old rows mean | 8 |
| E14 | Market entries only | WIDEN | `OrderSpec` on the intent; limit and stop entries at step 3 | 17 |
| E15 | `OwnPosition` lacks facts | WIDEN | `PositionFacts` from `HeldPosition`; `numbers_at_entry` filled in slice 7 | 3, 7 |
| E16 | Identity table unwired | WIRE | R17 forwarding map, `classify` called by promote and the judge | 16 |
| E17 | Too-thin count | value | Numbers talk and methodology | none |
| E18 | Motion constants | WIDEN | Editable rows on `Motion` | 7 |

`tools/qml/placeholders.py` widens past blocks to rows, so PH 5, 6, 18, 19, 20 are listed (`SWAP` 4.1 row 2), and `tools/tests/test_placeholders.py` proves the rip-out list empties.

## 6. The first baseline, from zero trades and zero fills

Empty store, fake broker (K7) or the practice venue (below), template `canary` first, then `scalper-mr`. `canary` reads 15-minute bars, so it runs before slice 9 changes the feed. Values are labelled placeholders, owner numbers talk; every card says "a shape, not an edge".

1. `unit_new("canary", {})`. No pod, no group. The template is a complete document: logic blocks, exits, a risk section (fixed money per trade, one position, kill switch only, labelled "no brakes" in the largest type), labelled numbers, `origin: placeholder`. Instrument records for the template's markets ship with it, labelled `source: shipped`, so day one needs no broker (`[ASSUMPTION]`: closes E5 G8; `unit_check` accepts a shipped record).
2. `unit_check`, then compile. `needs ⊆ provides` or a named fallback; two fingerprints.
3. `backtest_run` on synthetic bars. QMB runs G (`qmb/host/behaviour.py`) and the host writes the G record against the logic fingerprint; the run is stamped `group: none`. No judge run is needed, and a judge's `too_thin` moves nothing.
4. His promote click to paper: the `DRAFT -> PAPER` row (AD-24), on G's safety half. `Deployment(logic_fp, risk_fp, group_id: none, lane: paper, budget_share)`.
5. The node stages, compiles, warms up by the warm-up count.
6. First signal, pass 1: exits none; a proposal parks. Pass 2: unit chain (no stickers; gate warns on an `uncalibrated` cell; sizer answers money at risk; converter spells quantity or a named skip); node chain (kill GREEN, no group, veto passes); the row is written with every input; the send. The fake broker fills. Fill row; first measured cost in the cell; one row in the fleet fold reading "too thin to judge".
7. `scalper-mr` repeats the walk with control rows: session-loss and account-daily halts bind at zero; the own-percentile bench in shadow until N trades, writing `would_have`; the cushion rule at zero profit gives factor 1; the fast-invalidation cut uses a fixed labelled distance until N winners exist.
8. K7 ends with the owner's click on the fake broker's live lane, bound to both fingerprints.

**Shipped on, per FUNNEL 4.1 and 4.2:** sizer fixed fraction of a declared base at the stop with costs in the denominator; exits disaster stop, R target, side-correct time exit (plus the fast-invalidation cut in `scalper-mr`, the thesis exit in `intraday-trend`); halts `session-loss-limit-halt` at unit scope and `account-daily-loss-halt` at account scope, restore by rule at the day boundary; gate SQS-2 cost hurdle with SQS-1 as the floor, SQS-3 in shadow, SQS-4 off on the modifier chain; stickers from the news calendar, both FX legs tagged, a dead calendar lands a card and reads `prefer_not`; group row (when a group exists) with `own size under a parent limit`, a portfolio day stop `on_fire: stand_down(all) + card` expiring at the day boundary, raise gate on; numbers find, track, correct with per-type presets; the scripted fleet watch with the decay card off; records all written; kill effects read by entries.

**How anything changes.** Copilot or user: `unit_new(template, overrides)` by JSON pointer; `unit_patch` on a draft; `pod_draft` then `roll_plan` for many; `group_draft` for shared caps, money and the kill line; `blocks_save` for a new block; a new JSON in the templates folder or a `template` Library item for a new template. Live moves take the owner's click on one hash. Inside a range, numbers move by their own rule. A group limit edit is one click on the row and reaches members at their next decision.

**Day one for a stranger [CHECK S8].** Paper needs a bound venue and its prices (`paper_lane.py:1-9`, `runtime.py:2763`), and `ConformanceAccount` (`runtime.py:698`) has no production builder today. Slice 5 adds a venue kind, `practice`: a production builder over that account and a feed replaying the shipped synthetic bars, world `paper`, no broker and no sign-in. So day one reaches a filled paper entry and says plainly it is practice; a real broker's prices come on day two, after its approval. The installer itself is the release lane's (`OPEN.md`).

**One evaluator, three drivers now.** The evaluator is `HostedUnit` (`on_instant`, `price`, `move_risk`) behind `UnitSliceHandler`, the code QMB and the node already share. A driver supplies only an `AdmitPort` (the node chain), a `FactSource` (node facts or replay facts) and an execution port. Three drivers now: node live, paper lane, QMB; Lab replay joins when a Lab exists (`qmx_control/lab.py` says none does) [CHECK S6]. QMB with one unit uses an immediate admit and `group: none`, stamped on the run; several units replay through `group_run` with the node's pass-2 order. The Lab previews `expand(sample, pod)` and drives replay through the same seams, so its size trail is the decision row. One conformance tape (recorded proposals and facts) runs through every driver that exists in CI with an identical trail required; only fills, costs and latency may differ (V10). A block the Lab can run and the node cannot is an unmet need by name, never a Lab-only block by nature.

## 7. How a developer adds things, and keeps it maintainable

### Module map and owners

| Module | Package | Owns |
|---|---|---|
| `unit/model.py`, `unit/sections.py`, `unit/upgrade.py`, schema | `qml` | The document, the one partition, the upgrader chain |
| `compile/compiler.py`, `compile/group.py` | `qml` | Lifted refusals, needs check, face check, both fingerprints, format 5 |
| `protocol/unit.py`; new `exits.py`, `controls.py`, `entry_chain.py` | `qml` | `HostedUnit`, `on_instant`, `price`, `move_risk`; 1,134 lines today, split as it widens |
| `chain/node_chain.py` | `qml` | Node chain runner and `AdmitPort` protocol |
| `group/caps.py`, `group/ledger.py` | `qml` | Group cap runner, ledger fold, rank |
| `motion/engine.py` | `qml` | Correct, widened |
| `numbers/convert.py`, `numbers/records.py` | `qml` | The one converter; record keys; `conversions` |
| `feed/rollup.py` | `qml` | The one roll-up from base bars to a unit's streams (AD-25) |
| `receipt.py`, `fold.py` | `qml` | `explain_size`, `replay_decision`, `fold` |
| `pods/expand.py`, `pods/roll.py`, `pods/drift.py` | `qml` | Recipe stamping, plans, drift. Pure, no I/O |
| `blocks/stdlib/` and the Library | `qml`, host | Content; stdlib needs his signature (Call 11), Library does not |
| `risk/chain.py`, `risk/facts.py`, `risk/controls.py`, `risk/group.py`, `risk/unit_intent.py` | `qmf-risk` | Verdict, fact, row, group types; the wire (`none_declared`, signed stop) |
| `data/journal_kinds/unit.py` | `qmf-data` | Row kinds and appendable codes, used by hosts; `qml` never imports it |
| `host/unit_handler.py`, new `host/facts.py`, `host/group_run.py` | `qmb` | Admit seam, replay facts, multi-unit replay driver with the node's order |
| `app/runtime.py`, new `app/outbox.py`, `app/node_links.py`, `app/practice.py`, `app/facts.py`, `app/sensor.py`, `app/stand_down.py`, `protection/effect_matrix.py` | `qmn` | Two passes, outbox and budget, fault wall, injected node links, the practice venue, node facts, sensor, stickers, kill effects on entries |
| `promote.py`, new `roll.py`, `retest.py`, `feed_relay.py` | `qmx-host` | The click and its binding, re-test workflow, relay for any publisher |
| `kinds/pod`, `group`, `template` (un-retired), `pod-block` retired into `component` | `qmx-library` | Real schemas |
| templates `fleet-fold`, `curve-factory` | `qmx-engine` | Scripted watch's steps, curves; `fleet-fold` ships inside the `fleet-watch` mini app (section 8) |
| `catalog.py`, `functions.py` | `qmx-control`, `qmx-tools` | Tool rows in section 8 |

**One statement per `qmf-risk` module** says which world it belongs to (new risk through QML blocks, or the wire and accounting); what the swap retires (`qmn/capital/*`, old `control_*`) is subtracted in the owning lane once the conformance tape passes.

### Adding

| Adding | Files touched | Tests |
|---|---|---|
| **A sizer** | One folder in the Library (`component` with `entry.json` `output: amount`, `reads`, `block.py`) or `blocks/stdlib/<id>/1/` with a dictionary page. No core edit | Auto-enrolled contract test (its answer changes when a moved value in `evidence` changes), golden case, `same-decision-in-both-hosts`, `replay_decision` on a row |
| **A brake** | One folder; face declares `reads` and verbs; one row in a template or recipe; a reason code row (appendable) | Contract; `would_have` in shadow; cold behaviour; exits-never-blocked property |
| **A group cap** | One folder, `component_type: group_cap`; a row in a group document | Same, plus a two-member `group_run` case |
| **An instrument class** | Record rows and keys in `numbers/records.py`; a calendar package under `extensions/`; venue adapter only for a new venue; cost pool rows. No branch | A test that fails on `instrument_class` branching in the money path; known-answer cost check per class |
| **A new fact** | Name in `qmf/risk/facts.py`; two adapters (`qmb/host/facts.py`, `qmn/app/facts.py`); provided list. Own-journal facts need one function in QML | Known-answer test in both adapters; conformance tape. A core change, said plainly |
| **A template** | One JSON in `qml/unit/templates/` or a `template` Library item (overrides only) | K7 runs every template to a filled paper entry |
| **A pod or group** | One Library item | Gallery item compiles with `expand` against each template; group facts appear on the fold |

### Debugging one size

`explain_size(row_id)` prints each step: facts with age and source, base amount and basis, each modifier with range and reason, each chain verdict with its inputs, the binding link, the converter's residue, the fill and its gap. `replay_decision(row_id)` re-runs the sizer on the row's stored inputs and must match, by test. One function for developer, copilot, UI and triage; `TraceLevel.EVERY_BAR` in QMB for the bars around it. Logs stay apart from journals (`qmn/observability`); one trace id from reading to fill lands on both.

### Contract tests (K9), in order

Each test lands with the slice in brackets and stays on.

1. Same decision in both hosts, by socket (block, bar sequence, expected answer through QMB and the node). [2]
2. Exits never blocked, as a property, including a faulty exit block, a raising logic slot, a raising sizer, a dead fold; one unit's raise stops no other unit (AD-23's test). [3, widened 10, 11]
3. Exit code cannot import the chain, fold or feed. [3]
4. Every refused field runs, refuses with a reason, or is labelled; the census covers `authority` and `reads` now, and `tags`, `stages`, `recipe` when slice 1 adds them. [0, 1]
5. Every number has a reason and range at check. [7]
6. Motion: range, step, flat, bounded state, shuffled-outcome control; any block whose answer ignores a bound number moved in `evidence` fails. [7]
7. Every template reaches paper on rehearsal (K7), with no judge run. [5, 10]
8. No agent path to money, by tool table. [5]
9. `RiskState` from one fold in every reader. [4]
10. Known-answer cost check per cost block. [8]
11. A parked entry waits, never reads "warming up", is never minted a second time (one signal, one send, one position at the venue and in the handler), and past `expires_at` writes `Skip` with `budget_expired`. [11]
12. A stopless entry held for N bars on the fake broker, then through a restart, survives all of AD-22's places. [11]
13. The conformance tape through every driver that exists: node, paper, QMB. [2, widened 11]
14. `_CEILING` and the exit-evidence test faults fixed before any real block lands. [0]
15. **Self-configuration, end to end, one sizing number and one exit number.** On QMB and on the fake broker, bind `own-r-step@1` to the sizer's `fraction` and to the target's `multiple` and run scripted trades. A calibration row shows each move, inside its range. The next entry's quantity is the literal the converter gives at the moved `fraction`, through the shipped sizer. The next target is the literal at the moved `multiple`; a position already open keeps its old target. `explain_size` on that row prints both moved values and the calibration row ids. It moves with another market held. A restart in the middle of a count ends in the same move. [7]
16. **Currency.** Known answers: the loss at the stop equals the intended amount in the account's currency on a quote-is-account market, on gold, on USDJPY and on EURJPY. A stale or absent rate gives its named skip; an exit in the same state still closes; QMB and the node agree. [2]
17. **One feed.** AD-25's test. [9]

### Versions and migrations

`COMPILER_FORMAT_VERSION` 4 to 5 in slice 1, before any unit deploys, then one bump per changed decision until the first live deployment (AD-19). A census test fails on any new schema field until it is run, refused or labelled. The upgrader chain and the "newer than I read" refusal stay. Snapshots carry two parts, each judged by its own fingerprint; a cold restore of risk state is rebuilt from `risk_event` and calibration rows by the fold, so nothing is lost. A forwarding map (`qml/identity/forward.py`) declares `old@v -> new@v` with a parameter transform; the identity table is wired so promote and the judge classify a swap (sizer-only keeps the logic record; an exit change is a counted try). The deployment gains `succeeds` so a new version may enter while the old one keeps only its exits until flat. A `.qmxunit` or `.qmxpod` name for the JSON is tooling config, no core change. **Re-test workflow (K8):** after any format bump, rerun G per deployed unit on its recorded slice on a worker pool, report which units changed behaviour, and refuse the bump at the node until the report exists.

### `EXTENDING.md`

One page per thing added, each ending in the test that proves it. **Generated,** with a staleness test: the socket list and each slot's face; refused fields with their reasons (`_shape_problems`); block answer shapes; the fact registry with providers; reason codes and journal kinds; the module map above; the tool rows. **Written:** why each seat exists, the traps (`make` gets starting values and `evidence` carries moved ones; a stdlib block bumps the money app; two risk worlds), how to add each thing, debugging one size, and the three tiers of change.

## 8. Doors: copilot, agents, apps

**Copilot and user tools (catalog rows).** Existing: `unit_new(template, overrides)`, `unit_check`, `unit_explain`, `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match`, `backtest_run`, `judge_run`, `journal_query`, `library_save` (artifacts). New: `unit_patch(draft, pointer_edits)`; `blocks_save(entry, source)` with the contract test, Library `component` only (the Python path: a block is `block.py` behind a face, scanned by layer F, enrolled in the contract test; `plain_python` stays refused; stdlib needs his signature); `template_save(json)`; `pod_draft`, `pod_check`, `pod_explain`; `roll_plan(pod, members)`; `group_draft`, `group_check`; `risk_state(scope)`; `explain_size(row)`; `replay_decision(row)`; `fleet_read()`; `drift_report(pod)`; `sticker_propose(scope, kind, strength, expiry, why)` which lands a card; `card_land`. Every row declares direction (read, propose, run). **Money door:** promote, moving a live deployment to a plan, lowering a kill level, the floor: no row; his click in a channel no agent reads (K5).

**Agents.** Read: `risk_state`, `explain_size`, `fleet_read`, roll plans, drift. Propose: `pod_draft`, `group_draft`, cards with direction and expiry, de-risk stickers as cards (Q4 default). Run: unlimited on paper and replay. Protected fields: floor, kill level, `never_self_tune`, plan hash. Everything about who runs them, when, with which memory, Shepherd, departments, and whether a de-risk reading may apply itself is handed to the agentic session (OPEN.md).

**Apps.** `data_reads` widens past `market` (`supervisor.py:891`) to `journals` and `fold`; a card-landing path to "Needs you" is traced (K2; UNKNOWN today); `library-items` lander lands pods, presets, blocks and templates at publish; a published reading travels by the relay with host-stamped `source`.

**The scripted fleet watch** (replaces the decay flood): a mini app, `fleet-watch`, packaged through the manifest with `data_reads` on journals and the fold (`qmx_apps/manifest.py:113`), so it installs, stops and swaps like any other ("As a mini app also", M49) [CHECK S16]. Its engine template `fleet-fold` reads the fold once a night and on demand: one ranked row per unit (state, distance to lines, drift from recipe, money since anchor), two lists (who gets looked at, by rank under K; who gets acted on, by a strict bar under one fleet budget), one incident one card by root-cause key, a morning digest; no agent; the shipped decay rule's per-unit nightly card is switched off in the same slice. From zero every row reads "too thin to judge".

## 9. Observability

**Rows:** section 3. **The fold:** `fold(rows, scope, clock) -> RiskState`, pure; scopes position, unit, pod (rows carry `recipe.pod_id`), group, account, tag; series realised, marked, committed; the cushion ledger is one scope with an anchor. Readers: node (in process, incremental), restart catch-up, pod card, fleet template, agents, the UI (as data: at stake next trade, losses to kill line, room, daily loss, state word, drift). Word is UNKNOWN when any needed input is stale. **Node meters as plain rows:** pass 1 time, pass 2 time, entries left over, budget overruns, sends per bar, compile queue depth. Risk rows are evidence; no observability stack may drop them.

## 10. Build order, in slices

**69 PRs** in `round-2/build/PLAN.md`, stacked, one check per PR, light verification per PR. The PRs column below is the fold's first estimate of 52; the plan split to one builder's size and added release PRs, the templates PR, tool rows and the gallery. "Sign-in" is his demo sign-in (Q1). Three stop points each leave a whole baseline. **His signature:** QML in the node's lock bumps the money app and needs his signature (`SWAP` 2.2), and slices 2, 3 and 7 change stdlib blocks. One signed release per stop point covers everything up to it; a stop point isn't reached until he has signed [CHECK S17]. UNKNOWN: no gate for this found in `release_gate.py` or `build_release.py`.

| # | Slice | PRs | Ends in, verifiable | Sign-in |
|---|---|---|---|---|
| 0 | Tests first: `_CEILING`, exit evidence, Library enrol, census extended; one statement per `qmf-risk` module; `EXTENDING.md` skeleton with staleness test | 2 | CI honest; a real sizer passes | Before |
| 1 | Sections with AD-2's partition, two fingerprints, `opened_by` to logic, node and promote gates (`_g_record` on the logic fingerprint), format 5 | 2 | COMPARE's probe inverted: exits fire after a risk-only recompile | Before |
| 2 | `Amount`; converter with `rate`; the `Fact` type and `market.rate` in both hosts; `conversions` on the record, conversion markets subscribed; `fixed-fraction-at-stop@2`; `_money` stamped, `_account()` converted; face check, size band; `price` as its own call (AD-1), `layer_g` included; real receipt; decision row v2 with `numbers_in_force` and stored inputs written before send; `explain_size`, `replay_decision` | 4 | K9 1, 13, 16: same decision in both hosts; replay equals row; USDJPY and EURJPY lose the intended amount; a stale rate skips by name | Before |
| 3 | **Fault wall (AD-23):** phases in `_Run.step`, `try` per unit in `_drive`, `Fault`, `risk_event` kind with `unit_fault`, entries off and back, `close_scope` port. Exit step 2: stack, `PositionFacts`, side, closing quote's bars, reasons, fault fall-through; shipped exit blocks read numbers from evidence; import test | 3 | K9 2, 3: a raising logic slot and a raising sizer stop no exit and no other unit, over 12 bars, zero heals; six shipped exits compile that fit | Before |
| 4 | Control rows, `own.*` stats, `fold.py` at unit scope, words from the fold, restore, shadow, `risk_event` and `would_have` writers, `risk_stop` producer | 4 | K9 9; five halts run in QMB and on the fake broker; restart keeps a bench from rows. Account-scope halts read the account facts the node has today, labelled one-unit until slice 8 | Before |
| 5 | Template `canary` on 15-minute bars, shipped instrument records, the `DRAFT -> PAPER` row (AD-24), `practice` venue kind, run stamp, K5 protected list and channel test, K7 rehearsal | 3 | K9 7, 8: **first filled paper entry from zero with no judge run (RC-19). Stop point A: one unit trades on paper; brakes bind on any unit that declares them** | Before |
| 6 | Modifiers, cushion ledger as a scope of the fold, `enabled` by fact | 2 | Size trail with a press and a brake | Before |
| 7 | Number spec, engine widened, `scaled`, window, `authority`, editable constants, found-by-replay; **AD-14's six steps:** stamps, `own-r-step@1`, numbers from evidence enforced, receipt, no flat for sizer and exit numbers, `_OwnJournal` seeded | 3 | K9 5, 6, 15: **a sizing number and an exit number each move, the block reads it, the receipt shows it**, on QMB and the fake broker, through a restart; shuffle control | Before |
| 8 | Facts: account surface, record keys and commission, cost cells from fills, fill record, trade row v2, I17 verdict | 3 | K9 10; sizer reads a measured cell; slice 4's account halts re-tested across two units | Before; venue fields checked after |
| 9 | AD-25, four PRs: (a) base bar, `roll_up`, `(stream, market)` keys; (b) second stream compiled; (c) positions keyed by id, `position_limit`, bet key on intents; (d) sessions, window card, per-market settings, roles | 4 | K9 17: a 1m, a 5m and a 15m fixture unit trade on one account of the fake broker; templates A and B land in slice 10 and host there | Before |
| 10 | Unit chain: gate slot, stickers and tolerations, scope keys, node sensor, curve factory; a plain `try` on links and control rows; SQS rule and producer moved before C-20 | 3 | Hurdle warns then bites; a raising link stops no exit; `scalper-mr` and `intraday-trend` pass K7 | Before |
| 11 | Node chain with injected links, outbox two passes, time budget and beats, `Parked`, `parked:<market>`, kill effects on entries, order veto rows with `enabled`, no-stop path through all of AD-22's places | 4 | K9 11, 12: exits-first test; a long bell leaves entries over and the node lives; one signal, one send; a stopless entry survives bars and a restart. **Stop point B: the whole single-unit baseline, three templates, no group, no pod** (RC-48) | Before |
| 12 | Group: document with selector, limits as facts, caps, ledger, an unknown outcome keeping its room, `rank`, default parent limit and day stop, `group_run` driver, restart rules | 4 | Two-member and 200-member cap on the fake broker; one limit edit reaches members with no recompile; restart holds cuts and defers raises | Before |
| 13 | Pod: real kinds, `expand`, `roll_plan`, click, `move_risk`, stages, drift report, deployment key, gallery seed | 3 | One edit, 200 members, one click on the fake lane; drift listed; two deployments of one version | Before |
| 14 | Reads bus, publisher, home markets, reading record with `knows_at`, `library-items` lander, `blocks_save`, `template` un-retired, provenance and claim fields, Library block traced to a node deploy | 3 | A mini app's reading reaches a unit; a Library sizer trades on the fake broker | Before |
| 15 | `fleet-watch` mini app over the fold, app read door and card path, decay card off, run arms, `proposal` row shape reserved | 2 | One ranked row per unit, installed as a mini app | Before |
| 16 | R17 forwarding, identity table wired, `succeeds`, K8 re-test workflow | 1 | Placeholder rip-out keeps a record. **Stop point C: the whole baseline with group, pods, shipping** (RC-66) | Before |
| 17 | Step 3: signed stop, amends with read-back, partials on the node, trails, venue-resting targets per R24 | 2 | Wick and partial tests on demo | **After** |

Paper trading from `canary` starts after slice 5; `scalper-mr` after slice 10, which needs slice 9's feed. Nothing deploys live before slice 17 or K8. If "too much machine" turns out true at stop point B, slices 12 to 16 are opt-in and the single-unit baseline stands alone.

## 11. Deferred, and what reopens each

| Deferred | Reopens if |
|---|---|
| An order slot on the group beyond the `rank` field (best of those firing) | A recipe needs it; the slot is additive |
| Reservations as a type | Group caps ever run off the one thread |
| The proposal tape and its size search | Methodology hands a rule; the row shape is reserved |
| Sends off the tick thread, or a thread per account | Measured send delay at a bell harms fills, or exit delay exceeds what he accepts |
| Lab replay as a driver | A Lab package exists; the seams are ready |
| Hung-link protection, with a worker process per pod (V3 AD-7): today a block that never returns costs a node restart through `StuckWatch` | A hung block happens in practice, or a Library block arrives from outside |
| Group across places as one atomic cap | A second node holds one account |
| Applier object, bandits, pooled priors | A number needs motion between anchors that facts cannot give |
| Exit swap by a pod at an anchor (F5 C) | The scalper template's stage rows prove too rigid |
| Target resting at the venue | R24's facts show node-closed targets lose on wicks |
| Quote-clock exits (stream input widened) | Fast invalidation on 1m closes proves too slow |
| Netting shared protection, limit entries | A venue requires them |
| Rollout analysis, canary rules | Methodology hands a rule |
| Roll, futures route, volume on bars, order flow | Q2 |
| Stage from an agent; de-risk reading applying itself | Q4 answered and methodology rules |
| Observability stack choice | His later choice; rows are evidence either way |
| Lab UI, pod benches, desks, agent jobs | UI and agentic sessions |

## 12. If you want a pod that governs

COMPARE §4: "If you picture the pod as a live thing that governs its members, choose V2 and keep V1's slices as its order." Here is what that costs on this fold, slice by slice.

| Slice | Changes | Reused | Rework |
|---|---|---|---|
| 0 to 9 | Nothing. The second fingerprint is named `stack` instead of `risk`; the partition function is the same | All | None |
| 10 | Each row gains `runs_at: unit | group | anchor`, read by one function; links are the same | All links, wrapper, sensor | One field, one reader: under 1 PR |
| 11 | The node chain's link set becomes the pod's `runs_at: group` rows; `price` is already called from pass 2 (AD-1) | Outbox, budget, parked-entry fix, veto, no-stop path, the `price` call | None |
| 12 | The group document is absorbed into a house pod (a pod every other pod has as `parent`); limits-as-facts, caps, ledger, rank all stay | Caps runner, ledger, rank, `group_run` | 1 to 2 PRs: kind rename, selector becomes member rows |
| 13 | **The real fork.** `expand`, `roll_plan`, `move_risk` and the drift report are replaced by `resolve(unit, pod, house) -> Stack`, a stack fingerprint, a pod reference on the deployment, and a click on the pod hash | Kinds, click binding, stages (as pod rows), G on logic only | 3 PRs dropped, about 4 built |
| 14 to 17 | Nothing | All | None |

**Net:** about 4 to 6 PRs more than the 69, and a merge lane for multi-unit replay arrives a slice later. **Decide by stop point B.** Everything before it is shared; only slices 12 and 13 differ. What you gain: one pod is one document; a pod edit writes one document, not 200 versions; comparing two whole setups is plainer; a pod on screen is one thing on disk. What you lose: a unit alone pays one group call that answers nothing; the early stopping point stays, but the pod machinery is bigger once you pass it.

## 13. Assumptions and open items

See `OPEN.md` for every open item with the default the build runs on and who decides. Assumptions carried in this spine: G's behaviour half is not re-required under a new risk section (Q6 default); a stage move covered by the original click satisfies REVIEW M2; 200 unit versions per pod edit are acceptable to the Library; a 60-second base bar's extra feed work is small; shipped instrument records are accepted by `unit_check`; a G run per unit is cheap enough to batch for K8. UNKNOWN until measured: real node throughput at 200 units with journals and a venue; real compile time per member; whether a Library block reaches a live node end to end (slice 14 traces it); real send times (demo); whether cTrader accepts a market order with no stop (R24).
