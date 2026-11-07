# V4 walks: thirteen cases against the contracts and the code

Each walk names the steps, the contract rows they lean on (`SPINE.md` sections and `AD`s), and plainly where the shape strains or fails. Code lines are from `D:\QMX-worktrees\bld-repair-24` at `351e7521`, or a `SWAP` row. UNKNOWN means not verified. No test ran.

## 1. A newcomer installs and gets a unit on paper

1. `python -m qmx_host first-start` makes the folder (`qmx_host/first_start.py`). Installer and launcher are the release lane's (E5 G1 to G3); the first wall is theirs, not this shape's.
2. `unit_new("scalper-mr")` writes the draft with every risk field filled by the template (SPINE 5 step 2). The template ships `instrument` records for its markets labelled `source: shipped`, so `unit_check` has a record per market without a broker.
3. `unit_check` passes A to F; compile (format 5) accepts; the needs check finds every fact the blocks read in the registry.
4. `backtest_run` on synthetic bars through `UnitSliceHandler`; G passes; the card says "a shape, not an edge".
5. Promote to paper: his click; the node refuses nothing, since the fingerprint is in the G record (`runtime.py:2756`).
6. First entry: SPINE 5 steps 6 and 7, on the fake broker in the rehearsal, on the paper lane with a real feed once cTrader approves the app (about a day, `connect_node.py:8-9`).
7. The fleet digest shows one row, "too thin to judge".

**Strains.** The shipped-records stand-in is an assumption (E5 G8). "Tomorrow" is honest as day one on history and replay, day two on paper with a broker. A stranger reads skills written for one person ("his yes"); wording is the agentic upgrade's.

## 2. A gold scalper with fast invalidation and no fixed stop

1. The unit declares `r_basis: tail_budget` with a `tail_budget_r` number (I13) and no stop exit block in its logic sense. The sizer `money_at_risk` reads the tail budget instead of a stop distance.
2. `invalidation` role block (runs under AD-1; refused today, `compiler.py:438-443`) watches a condition after entry; when it fires it answers an exit `close_full(reason: thesis_invalid)` on the exit path (AD-6).
3. The node's protection gate requires a venue-resident stop on every order (`runtime.py:1102-1106`, kept). The compiled unit therefore carries a *disaster* stop exit computed from the tail budget (far, labelled), so "no fixed stop" means no logic stop, not no venue stop.
4. The cost hurdle veto reads `spread_now` and `cost_cell(hour)` facts against the unit's allowance in R, with R defined by the tail budget; warns while the cell is `uncalibrated`.
5. Several positions per market if the template sets `position_limit` (S17); each intent carries a bet key.
6. Record: trade rows carry `exit_mechanism: invalidation`, MAE and MFE; the fast-invalidation cut's winner-catch caveat (C1) stays on the block.

**Strains.** Compile refuses a unit with no stop in four places today (`SWAP 11`); V4 lifts compile and `enter` (`unit.py:764-766`) but keeps the node's venue stop rule, so a truly stopless live unit is not expressible on this node. That is the node's own safety rule, not a fixed line; I would keep it and say so in large type. The handler and node parse the stop as `Decimal` (`unit_handler.py:560`, `runtime.py:1065`), so `none_declared` on the wire needs the disaster stop filled before send. A unit without a price stop cannot use SQS-2's "cost in R at this stop" without the tail budget standing in for the stop; fine, but say it on the card.

## 3. An ORB unit across several opens, one bet counted once

1. `sessions` compiled (S9): one session per open (Tokyo, London, New York cash), each with its calendar and windows; flat before the window closes by a time exit at session end.
2. `position_limit` per market and per open (S17); each open is one family tag on the intent (I9), so the fleet fold pools the opens.
3. Bet key `(underlying, direction, day)` on every intent (I9). A unit-scope halt `same-bet-cap@1` reads `open_risk_by_bet_key` and answers `no_new_entries` while the key holds risk, so two opens on correlated indices count once; at account scope it also binds at place (AD-5) across units.
4. Per-open numbers through `settings_record` keyed `session:<name>` (I16); the compiler resolves them per session.
5. The unit `tolerates: ["open"]`, so an `open` sticker (caution window at the bell) does not hold it back while it holds a scalper back.
6. Its volume gate waits on bars carrying volume or a tick count (I7, Q2); it ships with the tick-rate stand-in from the node sensor.

**Strains.** "Per open" is a limit keyed on the session, so the position key must carry the session; S17 as written says per market and per open, and the handler's one-position check (`unit_handler.py:547-549`) must learn that key. `open_risk_by_bet_key` across units is only atomic on one node (AD-5). QMB sees one unit, so the cross-unit same-bet count is live-only until the Lab's multi-unit replay (Deferred).

## 4. A futures week with the copilot, ending in units with their own sizing

Assume a futures route exists. The desk is a mini app with agents (`risk = "runs"`, `[profiles]` per contract family, `supervisor.py:852-865` built).

1. Its jobs land research notes and readings (`roll_days`, `exchange_session`, `contract_tier`) as reading records under `source: app:futures-desk`, host-stamped (AD-9), through the generalised relay.
2. It drafts a **preset** `futures-orb`: sizer `vol-target@1`, modifiers `gap-factor`, `margin-headroom` halt, `roll-stand-down` halt with `on_fire: stand_down(instrument, no_new_entries)`, exits, numbers with ranges and reasons found by replay (E5's find step), `tolerates: ["open"]`.
3. It drafts a **group** row `futures-desk`: selector `tags: ["futures"]`, place, share, allocation `opening_range_priority` (a block publishing `budget_share`), limits.
4. It drafts units from a logic template with the preset applied (`unit_new`), checks, backtests (QMB), lands them as drafts.
5. A plan lists the units; he clicks once (AD-11); the node deploys to paper, then live on a second click.
6. Stop the desk: units keep trading; its readings age out to their fallbacks (V7).

**Still missing, in every shape:** the route itself (Q2); `roll` compiled (`compiler.py:938-943`, reserved on I4); instrument rows for mini and micro with margin facts in the fold; an exchange session calendar extension; the `library-items` lander and the blocks save row (E2 rows 1 to 5, slice 6); a methodology for what counts as a valid unit; a copilot that cannot take raw video (M51); the agentic upgrade's doors (K2). **V4 adds nothing at trade time for this walk**: the desk ships presets, groups, blocks and readings, all design-time or published, which is the point.

## 5. A very aggressive setup with few units on one basket, then a stage change as capital grows

Mechanics only.

1. Group row `core`: selector three units, allocation `best_basket` (publishes `budget_share` by a feasibility ranking, I17), limits left wide, `share_cap` off.
2. Preset `full-press`: sizer `kelly@1` at its full setting, halts only `kill-line@1`, no cost gate, `tolerates` everything but `hand`. Compile warns in the largest type (AD-13), runs.
3. The sizer reads `equity` and `budget_share`; the converter's feasibility verdict (I17) says which instruments one minimum lot fits at this share; the shed rule is a block.
4. **Stage change, two ways.** (a) Motion: the fraction is a `state_table` number keyed on the `equity` fact (`{below 5000: a, at or above: b}`) inside its range; when equity crosses the line the number moves at its anchor, journalled, no version, no click (AD-8). (b) Structure: a second preset `stage-two` with different blocks; a plan over the group's selector; one click (AD-11).
5. House money per the group: the cushion rule with a day anchor reads `realised_since_anchor` on scope `group:core`; press enabled is a group fact.

**Strains.** `state_table` is refused today (`SWAP` M8) and keyed motion on a fact needs `reads` open; both are slice 1. Which stage line, which fraction: numbers talk. "Best basket" ranking by recent results chases noise (A1-103); the block carries that warning.

## 6. A unit made in the Lab, one from a workflow, one from a mini app

All three land a `unit` document plus pins in the Library and take one path: `unit_check`, compile, G, promote. There is no pod reference to resolve and no second fingerprint, so there is no special case.

1. **Lab:** the Lab's replay driver (AD-14) drives `UnitSliceHandler` over recorded bars; the "Pods bench" edits a preset over the unit's own fields; Save publishes the unit version; Send to paper is his click.
2. **Workflow:** an engine template lands a `unit` draft through a lander; `unit_check` runs on it (the Write hook already checks a unit file, `qmx-agents/plugin/hooks/hooks.json`).
3. **Mini app:** lands a unit, a preset and blocks through the `library-items` lander (missing today, E2 rows 1 to 3); nothing it lands reaches a node except through compile and his click.

**Strains.** The lander and the blocks save row are missing (slice 6). A Library block's path to a live node is UNKNOWN (`SWAP` section 3) and is traced before the promise is made.

## 7. A mini app feeding another, and a desk publishing a reading a unit reads

1. App A's job returns an artifact under `[provides.x]`; the host validates and stores it; B's workflow takes the ref under `[feeds.x]` (road A, built, `qmx_apps/artifacts.py`); or A lands in the Library and an `event` trigger fires B (road B, built).
2. The desk publishes a reading record `source: app:macro-desk` (host-stamped, AD-9); the relay (generalised from `feed_relay.py`) writes it to the node's feeds with its age.
3. A unit declares `reads: [{reading: macro-regime, publisher: app:macro-desk, fallback: treat_as_absent, stale_after_s}]`; a `filter` or `veto` block reads it; the decision row records publisher, version and age.
4. The desk stops: the reading ages past its limit; the fallback applies; the unit trades on (V7).

**Strains.** `reads` is refused today (`compiler.py:900-901`) and the relay carries the MIS board only (`feed_relay.py:1-14`), with no production importer (E2 (e) row 7). Both are slice 1 and 2 work. Whether the supervisor has a capability for an app reading another app's readings is UNKNOWN (E1 section 1).

## 8. Two hundred units: one pod edit, the fleet watch, herding on one volatility shift, one node's limits

1. **One edit.** (a) A value: edit the group row's limit, his click on the row version; 200 units read the new fact at their next decision; no recompile, no G (AD-2, AD-10). (b) Structure: re-apply the preset or patch over the selector; a plan with 200 diffs; the re-test batch runs G on each recorded slice and lists which units changed behaviour; one click; the node deploys (AD-11). Identity: a sizer-only change keeps each logic record (AD-12).
2. **Fleet watch.** Scripts fold one row per unit from the fold (R9); two lists (rank for looking, a strict bar under one fleet budget for acting); one incident one card by root-cause key; the decay rule's card per unit is off (D44). Agents read the top K plus incidents; his screen is one digest at any size.
3. **Herding.** One volatility shift moves every unit's `derived` stop and every ATR-sized trade together: the correct response per E5 2.6. A group `share_cap` fact plus a `group-cap@1` modifier reading `group.size_moves_today` can damp it where a group wants that; content on the facts registry.
4. **One node.** One `node-runtime` thread (`runtime.py:2157`); each entry adds about ten pure block evaluations over facts folded once per bar; latency UNKNOWN, expected under the venue round trip. Shared caps are atomic on that thread (AD-5); across places they are stickers at anchors.

**Strains.** 200 G runs per structural edit is real machine time (UNKNOWN per run); the funnel's two-fingerprint seat avoids it by not re-testing, which I judge the wrong saving for a risk change, but it is the honest cost of this shape. Drift: a member that was edited after the preset was painted is caught only by a fleet report over pins and lineage, not by structure. The herding cap is content, not shipped.

## 9. Swapping a placeholder on a unit with a record and an open position

1. The forwarding map declares `fixed-fraction-at-stop@1 -> fixed-fraction-money@1` with a parameter transform (AD-12); the identity table classifies the swap `sizer-only`: the logic record in R continues, the money record starts per version.
2. A plan (one unit); G on its recorded slice; his click; the deployment gains `succeeds: <old deployment>`.
3. The node starts the new version; the old version stops minting entries and keeps its exits for the position it opened (the handler closes only positions its fingerprint opened, `unit_handler.py:14-15`); when flat, the old deployment ends.
4. The receipt on the next decision names the new sizer; `explain_size` shows both fingerprints across the swap.

**Strains.** Two compiled versions of one unit on one deployment lineage is new node work (today a second live deployment of one version is refused, `promote.py:424-447`); every shape pays it. What old trade rows mean after `r_after_costs` gains costs (R17) is a migration note, not code.

## 10. A brand-new brake, a brand-new instrument class, a new sizing base

1. **Brake.** One halt block folder: `entry.json` with `reads: [losing_day_streak]`, verbs, `on_fire` allowed; `block.py` answering `Halt | None`; a dictionary page. Auto-enrolled in the contract test; a shadow test. Bind it in a template or preset. If it needs a fact the fold lacks (say `fills_per_minute`), that is a registry row and a fold function per host, said on the page (AD-15).
2. **Instrument class.** Rows on the `instrument` kind and `records.py` (class, bucket, tick tier, calendars, commission, margin, capability); a calendar extension; a cost profile in QMB; the converter reads the record and branches nowhere; a test fails on `instrument_class` branching in the money path.
3. **Sizing base.** One block with `output: amount`, declaring its facts; the face check admits it to the sizer slot; the converter does the rest; the same-decision-both-hosts table gains a row.

**Strains.** A stdlib block bumps the money app and needs his signature (`SWAP` 2.2); the Library path is the way round and is UNKNOWN end to end until slice 6 traces it. A class needing a venue adapter (a second broker) is a route, Q2.

## 11. The MIS down mid-session; a guard or chain failure with open positions; a hung stage; a restart past an anchor

1. **MIS down.** Its readings age past each read's limit; each unit's fallback applies (`compute_here`, `treat_as_absent`, `no_new_entries`, `stand_aside`); every shipped template stands alone (V7); the active-market list falls back to home markets, never every listed market (AD-9).
2. **A faulty halt or veto block with open positions.** The halt runner catches it: that unit reads `no_new_entries` with a card (fail closed for entries); exits are untouched (AD-6). A faulty sizer skips with a reason (as today, `unit.py:794-797`). A faulty exit block falls to the next rank, then `_close_scope` (S3). A stale fold reads UNKNOWN, which the entry path treats as not calm.
3. **A hung stage.** There is no stage. A hung node thread is the watchdog's (`gw-guard-watchdogs`) and the venue holds every position's stop (the protection gate), so a hang cannot leave a position unprotected.
4. **Restart past an anchor.** The fold's catch-up rule (R9): rebuild from journals and the broker's deals (R20 reconcile), apply anchors passed while down (day boundary restores, cushion anchor reset), settle stickers that expired, restore calibrated values from R22's snapshot (`runtime.py:2919-2922`); a cold restore from calibration rows is UNKNOWN.

**Strains.** "Fail closed for entries" on a faulty block is my choice; a reckless preset may set `on_error: warn_and_pass` per binding (V9), labelled. Restart state for the five derived words is a read over the fold, so it needs no persistence of its own; the fold's own restart test is the one to write (only `risk_stop` has one today, `SWAP 23`).

## 12. House money, reverse house money and a press after wins, on and off, per pod

1. One block, `cushion-rule@1`, a `sizing_modifier` reading `realised_since_anchor(anchor)` on a scope; params: `anchor: day | week | fixed | running_peak`, `scope: unit | group | account`, shape `straight | curve | sigmoid`. A fixed or day anchor presses with winnings and brakes on the way down; a running-peak anchor only brakes (`FUNNEL` D13). A `press-gate@1` block decides when pressing is allowed.
2. Reverse house money is the same block with the brake half on and the press half off; both halves are numbers with ranges.
3. The cushion ledger is a scope of the fold (R9): realised and marked series since each anchor type, per unit, group and account.
4. **On and off per pod.** The shape (which block, which anchor) is structure: a preset per group, a plan, one click. The switch is a fact: `group.limit.press_enabled` on the group row, read by the block; his click on the row flips it live for every member without a recompile (AD-2). A press after N wins is a `state_table` number keyed on `loss_streak` or `win_streak` facts (motion).
5. Receipt: the factor and its reason on every decision row; report with and without motion.

**Strains.** The fold must carry a high-water series per scope for the running-peak anchor; cheap, but a fold change. Whether a press that applies itself is "an agent touching money" does not arise: no agent is in the path; an agent's de-risk sticker can only cut.

## 13. Backtest against live on the same unit: where can they differ?

Same handler, same blocks, same arithmetic (AD-14, V10). What can differ, by source:

| Where | QMB | Live | Why |
|---|---|---|---|
| account and group facts | the unit's own equity and open risk; group facts only if replayed | the account's, with other units' risk | QMB runs one unit; multi-unit replay is the Lab driver (Deferred) |
| place-time halts | the mint-time answer only | re-checked at place on the fresh fold (AD-5) | one thread, in-flight risk |
| cost cells | QMB's cost profile until fills exist | measured cells, `uncalibrated` fallback | costs are observed, not assumed (I2) |
| spread and tick facts | recorded minute rows (R19) where they exist, else the cell | the node sensor live | data |
| stickers | none unless the news calendar is replayed | the stand-down table | stickers are live state; a replay can carry a recorded sticker tape (content) |
| readings | as-of query over stamped records (R13; the query UNKNOWN) | the relay's last landed value with its age | stamping |
| fills | QMB's fill model, partial closes fill, target at the bar | the venue; partial close refused until step 3; target closed by the node until R24 | `SWAP` 2.6 |
| equity timing | moves with trades and cash events | read live from the account (slice 2) | today the node reads it once (`SWAP 17`) |

The arithmetic from facts to quantity never differs; the conformance tape proves it. The decision row records which facts were used, so any gap has a named cause. **Strain:** account-scope and group-scope rules cannot be proven in QMB alone; say so on the card and send the proof to the Lab's replay over recorded intents.
