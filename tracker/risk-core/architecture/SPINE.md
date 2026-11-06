---
name: qmx-risk-template-spine
type: architecture-spine
purpose: build-substrate
altitude: feature
paradigm: 'a typed document with spec and status, small control loops that move each number inside bounds the owner holds (the Kubernetes object and its Vertical Pod Autoscaler, run in its simplest modes); one guard above the position with two host adapters'
scope: 'first increment of the risk-and-sizing template: the twelve parts of FUNNEL.md 5.1, their fifteen binding factors, a named plug for everything later or shadow'
status: final
created: '2026-11-06'
updated: '2026-11-06'
binds: ['FUNNEL 5.1 parts 1-12', 'FUNNEL 5.2 factors 1-15', 'G12 hand-offs 1-37']
sources: ['architecture/PICK.md', 'funnel/FUNNEL.md', 'funnel/REVIEW.md', 'grounding/G12-audit-and-repair-for-risk.md', 'ledger/v1/', 'code at tips J bld-repair-10, N bld-repair-21 ef011af4, R bld-repair-19 7ada84ed']
companions: ['SYNTHESIS.md', 'fold_sim.py', 'out-fold.txt', 'out-verify-drift.txt', 'out-verify-b.txt', 'out-verify-k.txt', '.memlog.md', '../handoff/FOR-REPAIR-SOCKET.md']
---

# The risk-and-sizing template: the spine

Fable, fold of the arena, 6 Nov 2026. Fast path, headless: `[ASSUMPTION]` marks an inference nobody confirmed, **[judgment]** marks my opinion. Every file and line below was read at the tips named above; the repair is still moving `qmn/src/qmn/app/runtime.py`, `host.py` and `first_start.py`, so re-check a line before a slice is written. Model numbers are model numbers. Nothing committed; nothing run but the ledger build, its checker and the time-limited sims beside this file.

## 1. The shape in one page

**One mental model.** Every unit carries a **risk profile**: a document with a **spec** that people write and a **status** that only the runtime writes. Every number in the spec has a **derivation**, a fallback ladder, a receipt and an **authority mode**. At each **anchor** the derivation recomputes the number's recommendation from **facts**; one function, the applier, moves the value in force according to the number's mode. **Facts move live, numbers move at anchors.** Above every unit on an account sits one **guard**: it computes the facts, runs every brake, cap and gate above the position, applies one rank table, answers `before_order` with pass, shrink or refuse, and writes the status. Backtest and live run the same guard through two adapters. **Anything that cuts risk acts at once; anything that raises it waits for the anchor.**

| Part | What it is | Who writes it | Where it lives |
|---|---|---|---|
| Profile spec | sizer base, exit numbers, brake bindings, numbers with derivation and mode, needs, fail modes, `accepts_evidence` | him, presets, agent drafts through his click | Library kind `risk-profile`, schema `qmx.risk-profile/1`; `qml/src/qml/risk/profile.py` (new); embedded by `qml/src/qml/compile/compiler.py` |
| Group document | the one config above the units: floor, buffer, kill line, bet-key rule, rank table, never-self-tune list, group brakes, clocks | him | Library kind `risk-group`, schema `qmx.risk-group/1`; `display_name` is his screen word, `parent` reserved |
| Status | values in force, recommendations, receipts, level, brake states, anchors, ledgers, last RiskState | the guard only | `data/deployments/<id>/risk-status.json` beside R22's snapshot (unit); `data/risk-groups/<id>/status.json` (group); rebuilt from journals when missing |
| Presets | one `template` Library item per unit type over four chain keys: preset, class, instrument, unit | him; agents draft | `qmx_control/catalog.py` rows; children only tighten caps |
| Unit blocks | the sizer block and the unit's own exits, compiled in, so the unit stands alone for its own order and its own close | QML | `qml/src/qml/blocks/stdlib/*`, `qml/src/qml/protocol/unit.py` |
| Guard | one package, two ports: the fact kernel, every brake above the position, the registry, the rank table, the applier, `before_order`, RiskState, status | code on the node and in QMB; no agent write path | `packages/qmf-risk/src/qmf/risk/guard/` (new; the package G12 says stays) |
| Node fast lane | kill switch, stand-downs, feed and clock probes, the order path with its venue stop | the node; the kill level is his | N `qmn/src/qmn/app/runtime.py`, `stand_down.py`, `operations.py` |
| Harness | the light form over the ledger rows: sizing and brake replay, the integrated sim, the mandatory scenario block, the choke test, the dry chassis, the conformance tape | this session and the numbers lens; agents run it | `packages/qmf-risk/harness/` (new), seeded from `fold_sim.py` |
| Agents' door | read, run and propose rows, a direction on every operation | QMA (flagged, not designed) | catalog rows; the guard's read-only views |

```mermaid
flowchart LR
  L["Library: profile, group, preset<br/>spec: his, drafts, click"] -->|embed at compile| U
  subgraph host["host adapter: QMB UnitSliceHandler or node runtime"]
    U["compiled unit<br/>logic, sizer block, own exits"] -->|entry intent, wanted lots| G
    G["guard<br/>facts · anchors · applier · brakes · rank · status"] -->|pass / shrink / refuse| O["order path (node)<br/>venue stop and target"]
    G -.->|SizingFacts, PositionFacts| U
    N["node fast lane<br/>kill level · stand-downs · feed · clock"] -.->|facts| G
    G -->|stand-down at scope| N
    G -->|RiskState rows, status file| J[("journals + status")]
  end
  A["agents: read / run / propose"] -.->|read rows, evidence, cards| G
  A x--x O
```

**How an order flows.** 1. A bar closes; `UnitSliceHandler._step` first calls `guard.advance`, which opens any anchor that is due. 2. The unit's logic signals; its stop block gives the disaster stop as an absolute price. 3. `HostedUnit.enter` asks `guard.sizing_facts` for this market and calls the sizer block with the four inputs it gets today (`equity`, `entry_price`, `stop_price`, `record`; J `qml/src/qml/protocol/unit.py:787-789`) plus `SizingFacts`; the sizer answers `Size` with `wanted_lots` at level 1.00. 4. `mint_intents` (J `qmb/src/qmb/host/unit_handler.py:484`, which the node's unit delegates to) passes the entry intent to `guard.before_order`, which applies level, taper, caps and rounding once and answers `Pass`, `Shrink` or `Refuse`; the handler rewrites `quantity` or journals a skip with a closed code. 5. The node's `OrderPath.entry` keeps its own checks (venue ready, kill level, stand-downs) and sends the order with its venue-resident stop and target; QMB rests the intent to the next open. 6. Each bar the unit's per-bar exits read `PositionFacts`; the safest answer wins by the compiled order; exit intents never pass the guard. 7. Fills, closes and deals reach `guard.on_event`; the unit's running loss and the group's are each read once. 8. Every pass the guard emits one RiskState row and, when something moved, writes the status file whole and replaces it.

**How a number gets its value.** 1. The spec names the number: measure, default with its reason, range, `derivation` (rule block, inputs, ladder, clock, cautious direction, guard), `authority` (mode, owner). 2. At the anchor of its clock the derivation runs on facts and the record and writes a `Recommendation{target, low, high, rung}` with a receipt into status; the ladder is own record, pooled class, preset, user, refuse. 3. The applier moves the value in force only in the number's mode: `user_only` never; `off` writes `would_be`; `at_anchor` at that anchor; `at_flat` at the first flat after it. 4. A guard per derived number watches what the derivation assumed; a trip drops a rung with a reason code; after N trips the number freezes and a card flags him. 5. Every value in force carries one reason code: `user`, `default`, `calibrated`, `borrowed:<group>`, `capped_by:<rule>`, `stale_so_default`, `frozen_after_trips`. A blank key number refuses compile.

## 2. Invariants

Each is a call two builders one level down could make incompatibly. Binds / Prevents / Rule. Everything else is seed, or named under Deferred (section 12).

- **AD-1 Spec and status have separate writers.** Binds every document. Prevents the runtime and a person racing on one field. Rule: people and drafts write spec in the Library; only the guard writes status; every status row carries `generation` (the spec fingerprint, anchor id, revision); a status from another generation reads UNKNOWN and starts cold.
- **AD-2 One guard above the position.** Binds QMB and the node. Prevents two brake stacks that disagree. Rule: every brake, cap, gate and clamp above the position is a registry row the guard runs; the unit holds only its sizer and its own exits; both hosts build the same `Guard` from the same documents and reach it through `UnitSliceHandler`; the guard does no I/O, imports no host and no `qml`, and runs on the runtime thread only.
- **AD-3 Only the node sends orders.** Prevents a second order path. Rule: the guard answers, never sends; no agent surface reaches `before_order` or the order path; the Lab and the harness run the guard on a tape, never a venue.
- **AD-4 Exits and the kill level are safe by type.** Rule: `before_order` takes `UnitEntryIntent` only; exit intents go to the close and amendment paths untouched, and a contract test runs every exit through every guard state; the `Effect` union has no variant that lowers a kill level or clears a stand-down that waits for his hand; a venue refusal raises urgency, never a retry loop that hides it.
- **AD-5 Every number derives.** Prevents a blank or a magic number. Rule: a number carries `derivation` and `authority`; a key number with no derivation and no `user_only` value refuses compile (`number_blank`); every default carries a `why`; never-self-tune rows take no input from a record, an agent or a derivation; his derivation edits are versions, his value edits on `user_only` rows are immediate and journalled.
- **AD-6 Facts move live, numbers move at anchors.** Binds derivations, the kernel, the sizer. Prevents motion between anchors nobody can explain, and a second mechanism for a cost that changed. Rule: a fact is measured now and never chosen (equity, open risk, cost cell, spread, kill level, day P&L); a number has a derivation and reaches its readers through the value in force; modes at go-live are `user_only`, `off`, `at_anchor`, `at_flat`; `at_period_open` and `live` parse and refuse `authority_not_built`.
- **AD-7 Cuts act at once, raises wait for the anchor.** Rule: a transition that lowers risk (bench, level down, stand-down, shed) takes effect on its event; a transition that raises risk (level up, bench clear, stand-down expiry, dial release, press arming) takes effect at the first anchor after it is earned, at most one level per anchor; a multiplier may read a live ledger between anchors inside bounds frozen at the anchor, and permission to exceed 1.0 is itself a raise.
- **AD-8 One reading of the running loss per scope.** Prevents re-stacked cuts (REVIEW M3). Rule: at unit scope only the bench reads the unit's money ledger to trip; at group scope only the day stop and its taper read the group's ledger; a registry row declares `reads_ledger` and scope, and compile refuses a second `mode: live` row on the same pair (`two_live_readers`); the sizer reads no realised loss between anchors, only open risk; the guard holds the bet-key ledger.
- **AD-9 Anchors are clocks plus a closed trigger list.** Prevents ad-hoc recompute paths and a restart acting as a free reset. Rule: clocks at go-live are `day` (the class's day boundary from the instrument record) and `allocation` (weekly); triggers are `his_act`, `banker_act`, `version_change`, `world_switch`, `spec_change`, `cost_alarm`, `restart_late`, `admission_change`; `anchor_id` is a pure function of clock and time, so `advance` is idempotent and a late anchor is detected; N never rises under a caution or a bench.
- **AD-10 One scope vocabulary.** Binds stand-downs, kills, brakes, isolation, bet keys. Rule: keys are `all`, `account:<id>`, `deployment_id:<id>`, `unit:<dep>:<market>`, `instrument:<id>`, `class:<k>`, `region:<k>`, `currency:<k>`, `underlying:<k>`, `session:<k>`; strictest wins across scopes; down the levels as caps and states, up as events; a child in the chain may only tighten a cap.
- **AD-11 Brakes raise stand-downs, never a kill level.** Rule: a brake writes a stand-down row (`Kind.RISK_RULE`, self-clearing on the guard's word; `Kind.RISK_STOP` for a lockout that waits for his resume, N `stand_down.py:94`) with a cause and a clear rule; the kill level rises by his hand or his one-tap card and goes down only by his hand.
- **AD-12 R is gross; `net_r` sits beside it.** Rule: `r` is the planned loss at the disaster stop at entry; `net_r = r − costs_r`; brakes, the money ledger, the CUSUM and the admission gate read `net_r`; the judge and the logic record read gross `trade_r`; the money ledger reads broker deals (R20), not trade rows, so the record holes cannot hide a loss from a brake.
- **AD-13 A stop is an absolute level at every internal seam.** Prevents the wrong-side stop (`abs(entry − new_stop)`, N `runtime.py:1320`) and two sign conventions. Rule: units, intents, journals, status and the guard carry absolute stop and target prices; only the venue encoder derives a distance, signed by side (`_LEVEL_RULES`, J `packages/qmf-venue/src/qmf/venue/encode.py:115-120`); stops only tighten; every live entry carries a venue-resident stop.
- **AD-14 Registry rows.** Rule: every brake, clamp, gate, accelerator, sizer base and scope key is one row with kind, `brake_class` (tail or timing), `mode` (shadow, live), `direction`, scope, `reads`, `reads_ledger`, verb, rank band, fail mode, restore and the numbers it reads; a row is a `guard` section on the dictionary entry, so a new part is one folder; tail brakes may bind from day one, timing brakes ship shadow until the pooled report; a shadow row runs the same code with its action replaced by a `would_have` write and can never change an answer.
- **AD-15 One rank table per group.** Rule: bands fixed, rows append inside a band and never renumber; a refusal beats a shrink; caps smallest wins; multipliers multiply, each on its own ledger; the highest state is folded on every pass even when no intent came; the accelerator band acts only with everything above clear; a property test over random control states holds it equal to one table.
- **AD-16 Closed reason codes and the choke budget block shipping.** Rule: every guard answer, skip and brake text carries a code in `REASON_CODES` (R `packages/qmf-data/src/qmf/data/journal_kinds/unit.py:43-73`) or R15's census fails CI; the harness runs a healthy unit through every binding factor, and under 0.75 of baseline (`choke_budget_fire_rate`) CI fails for any change touching a binding factor; a cap binding on more than 90 % of trades is a defect.
- **AD-17 Backtest and live differ only in named facts.** Rule: the same guard, handler and blocks run in both hosts; both ports provide the same fact names from one kernel (`guard/facts/`, `PROVIDES`); a fact that differs carries a label (`sqs:bar_sampled`, `basis:unmarked`, `cost:uncalibrated`); the profile's needs must be a subset of `PROVIDES` at compile or each missing need names its fallback (`compute_here`, `treat_as_absent`, `no_new_entries`); one conformance tape runs through both ports in CI and must give the same verdicts.
- **AD-18 A restart changes nothing a brake can see.** Rule: the status file is written whole then replaced (the same move R22's snapshot uses); on start the guard reads it, and if it is missing or from another generation `Guard.recover` rebuilds it from journal rows and broker deals in deal order before any entry; until then and whenever a fact is past `risk_fact_staleness_limit`, `before_order` refuses with `guard_unavailable` and the word is UNKNOWN; the floor, the high-water mark and the day baseline never reset on a restart; exits are unaffected.
- **AD-19 Versions keep the record.** Rule: a profile change is a version with an identity label: `profile_sizing_change` (same unit, logic record continues, money record restarts, his click) or `profile_exit_change` (same unit, a counted try, his click); `_cold_reason` compares a `logic_fingerprint`, so a sizing-only version keeps logic state; adoption at the next flat; the click binds one hash, one level, these markets, until a date.
- **AD-20 Windows first-class.** Rule: `pathlib`, no signals, forks or POSIX paths; `tzdata` pinned in `qmf-risk`, because Windows has no system time-zone database; timers are the node's clock, never wall-clock sleeps.

| Convention | Rule |
|---|---|
| Money | `Decimal`; loss currency USD; conversion read live with a freshness limit |
| Facts | every fact carries a timestamp and a staleness limit; a stale fact takes the profile's fail mode; a stale green is impossible |
| Schema | unknown fields refused; a new field runs, refuses or labels by the census test (J `qml/tests/test_unit_refuses.py:457`, plus one census per new schema) |
| Reserved | the seven reserved chain keys (style, bucket, venue account, market, timeframe, session, event), `parent` on the group, `suggestions` and `packs` beyond one on the profile: parse, resolve to the parent or refuse `*_not_built` |

## 3. Vocabulary

One plain word each; no codenames. **Unit** the thing that trades. **Profile** its risk document: spec and status. **Preset** a profile with derivations instead of numbers, one per unit type. **Group** the units sharing one floor and cushion: the funnel's "one portfolio config"; a schema word only, so Book, BMS, cluster and portfolio stay open on screen until Q8. **Fact** a value measured now and never chosen. **Number** a value in the spec with a derivation. **Recommendation** what a derivation proposes, with bounds filled later. **In force** the value readers read. **Mode** who may move a number and when. **Anchor** the moment numbers refresh. **Receipt** the record on every resolved value and every order. **Guard** the one risk package above units. **Brake** a row that trips or tapers on a ledger; **clamp** limits one order and reads no evidence; **gate** says yes or no from one outside reading; **accelerator** a row that may raise. **Trip** a transition to a worse state. **Bench** no new entries for the rest of a window, exits run. **Stand-down** a hold at a scope with a clear rule. **Kill level** his switch, GREEN to BLACK. **Level** the size multiplier on the baseline: 0.25, 0.50, 0.75, 1.00. **Baseline** a unit's dollars at risk per trade at level 1.00. **Cushion** equity above the floor after the reserve and open risk. **Ledger** one running total at one scope. **Record** a unit's trades. **Card** a question for his click. **Scope** a key from AD-10.

## 4. Contracts

Python-shaped sketches; field names are ledger ids where one exists (`ledger/v1/core.md`). Paths are at tip J unless marked N or R.

### 4.1 The profile document and the group document

```python
class RiskProfile:                       # qml/src/qml/risk/profile.py; "qmx.risk-profile/1"; unknown fields refused
    profile_id: str; version: int; preset: Pin | None
    chain: Mapping[ChainKey, str]        # go-live: preset, class, instrument, unit; seven reserved keys resolve to the parent
    sizer: Pin                           # the sizer block; default money-at-stop@1
    numbers: Mapping[NumberId, NumberSpec]        # baseline_risk_usd and every other number, each with a derivation
    exit_numbers: Mapping[NumberId, NumberSpec]   # cut, disaster stop distance, time; a change is a counted try (AD-19)
    brakes: tuple[Binding, ...]          # unit-scope rows; group rows sit on the group; account scope refuses here
    needs: tuple[Need, ...]              # x1_needs_list: fact names each with a fallback (AD-17)
    fail_modes: Mapping[str, FailMode]   # x1_fail_mode per feed: board open, isolation closed, evidence neutral
    accepts_evidence: tuple[EvidenceRow, ...] = ()   # empty at go-live: kind, max cut, floor, ttl
    rank_table: str = "qmx-default@1"    # control_rank_table; the group may pin another
    packs: tuple[Pin, ...] = ()          # more than one refuses packs_not_built
    suggestions: tuple[()] = ()          # reserved; non-empty refuses suggestions_not_built

class NumberSpec:                        # widens qml/src/qml/unit/model.py NumberSpec; the Authority enum widens
    measure: Measure; level: Literal["unit", "group"]
    owner: Literal["user", "preset", "derivation"]     # x1_changed_by_class; user = the never-self-tune list
    range: Range | None                  # his bounds; the VPA's min and max allowed
    default: Decimal | str; why: str     # every default carries its reason
    authority: Authority
    derivation: Derivation | None        # None only on a user_only number with a value

class Authority:
    mode: Literal["user_only", "off", "at_anchor", "at_flat"]   # at_period_open, live: parse, refuse authority_not_built
    applies_to_open_positions: bool = False                     # stays refused when true (hand-off 8)

class Derivation:                        # x1_derivation_rule; the block is a dictionary entry of component_type "derivation"
    rule: Pin; inputs: Mapping[str, FactName | NumberId]        # compile checks the names and no cycle
    ladder: tuple[Rung, ...]             # derivation_fallback_order: own_record, pooled:<class>, preset, user, refuse
    min_count: int; shrink_k: int        # calibration_min_trades, calibration_shrink_k
    clock: Literal["day", "allocation"]  # AD-9
    cautious_direction: Literal["down", "up"]   # x1_cautious_direction: missing data moves this way or holds
    max_step: Decimal | None = None      # largest move per anchor
    guard: ValueGuard | None = None      # x1_tuned_value_guard: what must hold; a trip drops a rung; freeze after x1_guard_freeze_limit

class NumberStatus:                      # in the status file, written by the guard only
    in_force: Decimal | str; would_be: Decimal | None           # would_be under mode off
    recommendation: Recommendation       # target, low, high (None at go-live), rung
    receipt: Receipt                     # x1_derivation_receipt: rule, rung, inputs, prior, reason_code, generation, at
    guard: GuardStatus                   # trips, frozen

class RiskGroup:                         # "qmx.risk-group/1"; the deployment carries it beside the profile (promote.py _deployment, :502)
    group_id: str; version: int; display_name: str           # his screen word: Book, BMS, portfolio, cluster
    parent: str | None = None            # reserved; non-null refuses group_parent_not_built (Q8)
    clocks: Mapping[str, ClockRow]; numbers: Mapping[NumberId, NumberSpec]   # portfolio_floor, bms_buffer_before_floor, kill_line_floor: user_only
    brakes: tuple[Binding, ...]; rank: RankTable; bet_key_rule: str; shed_rank: str
    once_rules: tuple[OnceRule, ...] = ()   # his signed rules for Q4 and Q6
```

**Status** (`RiskProfileStatus`, `GroupStatus`): `generation`; `numbers` per id; `level` (now, start, cohort n and r, clean cohorts, CUSUM, warnings with trade counts); `brakes` per row id (state, since, window, bench days, lock top, lock until); `trading_state` per scope (`ACTIVE`, `REDUCING`, `BENCHED`, `HALTED`, `RESTORE`); `anchors` (day start equity per scope, high-water mark, budget used, N admitted, B); `money_ledger` per scope in `net_r` from broker deals; `last_risk_state`. The never-self-tune list at go-live: `portfolio_floor`, `bms_buffer_before_floor`, `kill_line_floor`, `kill_switch_level`, `floor_touch_tolerance`, `survival_horizon_rounds`. A blank user row compiles and blocks the live click (`x1_settable_by_levels`).

### 4.2 The registry row

A row is a `guard` section on the dictionary entry (`entry.json`), so a new part is one folder. A brake block keeps the shipped `HaltInstance.update(evidence) -> Halt | None` (J `qml/src/qml/blocks/api.py:182-186`), now hosted by the guard through a block factory the host passes in, so `qmf-risk` stays free of `qml`.

```python
class RegistryRow:                       # x1_brake_registry_row
    kind: Literal["brake", "clamp", "gate", "accelerator", "derivation", "scope_key"]
    brake_class: Literal["tail", "timing"] | None
    scope: str                           # AD-10 key pattern the row acts at
    reads: tuple[FactName, ...]          # compile: inside guard.PROVIDES or a named fallback
    reads_ledger: LedgerKey | None       # AD-8
    produces: NumberId | None            # a sizer base produces baseline_risk_usd
    verb: Literal["refuse", "multiply", "cap", "trip", "raise"] | None; rank_band: int | None
    mode: Literal["shadow", "live"]      # x1_brake_shadow_mode; "ramped" reserved
    direction: Literal["cut", "raise"]
    anchor: str; counting_rule: str; equity_basis: Literal["committed", "marked", "realised"]
    fail_mode: Literal["closed", "open", "neutral"]
    numbers: tuple[NumberId, ...]        # each with a Derivation
    restore: Pin | None                  # retry-then-lockout@1 at go-live; probes plug in here
    reason_codes: tuple[str, ...]; expected_fire_band: tuple[Decimal, Decimal]   # the harness's band, shown on the card
```

Go-live rows, live: `unit-money-bench@1` (tail, unit, reads `unit_money`, trip, band 400, restore `retry-then-lockout@1`); `drift-monitor@1` (unit, reads the unit's `net_r` stream against the card, a CUSUM warning steps one level down and locks the top there for `level_lockout_days`, the warning that reaches `drift_warnings_to_paper` inside `drift_warning_window_trades` is paper with `demotion_cause`; the same restore row as the bench, applied to drift); `group-day-stop@1` (tail, group, reads `group_day_money`, trip, stand-down at `all` expiring at the next day anchor, k from `day_stop_sigma_multiple`); `pair-taper@1` (multiply, group, the brake half into the day stop); `cushion-clip@1`, `bet-key-cap@1`, `per-trade-cap@1`, `sanity-band@1`, `margin-headroom@1`, `order-rate@1`, `stop-side@1` (caps); `sqs-gate@1`, `news-window@1`, `admission-gate@1` (gates); `horizon-floor-odds@1` (derivation, produces `baseline_risk_usd`); `class:`, `region:`, `currency:`, `underlying:`, `session:` (scope keys). Shadow: `house-money-press@1` (accelerator, switch-on by proof card and once-rule), `reducing-p10`, `loss-points`, `about-three`, `density`, `chorus`, `burn-tiers`, `class-isolation`, `kelly-ceiling`, `weekend-scale`, `upside-alarm`.

### 4.3 The sizer socket

**A sizer base is a derivation, not a socket.** `horizon-floor-odds@1` produces the number `baseline_risk_usd` (ledger `horizon_survival_risk_usd`) at the allocation anchor: `committed_cushion_usd ÷ (result_spread_r × z × √(trade_rate × survival_horizon_days) × B)`, with the reserve inside the committed cushion, the trade rate floored at the card's, and B from 4.4. The sizer block only turns dollars at risk into lots. Today the host hands four things (J `unit.py:787-789`) and the receipt is a literal (`:828`); `Size` has no residue (J `api.py:105-109`).

```python
class SizingFacts:                       # a host surface sizing:<market>, beside account and own_position (unit_handler.py:358-367)
    risk_usd: Decimal                    # baseline_risk_usd in force x (anchor cushion - open risk now) / anchor cushion
    cost_per_lot_usd: Decimal            # round trip plus stressed slippage for this instrument and hour; label cost:uncalibrated when pooled
    value_per_point: Decimal; usd_per_quote: Decimal; conversion_age_ns: int   # fixes USDJPY; a stale conversion answers a skip
    min_lot: Decimal; lot_step: Decimal; max_lot: Decimal
    labels: tuple[str, ...]              # basis:unmarked, cost:uncalibrated, stale_so_default

class Size:                              # widened; old callers read lots and skip_reason
    lots: Decimal | None; skip_reason: str | None = None
    wanted_lots: Decimal | None = None   # unrounded, at level 1.00; the guard applies every later factor to this
    risk_usd: Decimal | None = None; residue_r: Decimal = Decimal(0)   # rounding_residue_r
    reads: tuple[str, ...] = ()          # replaces the literal receipt; lands in SizerReceipt
```

`money-at-stop@1`: `wanted = risk_usd ÷ (|entry − stop| × value_per_point × usd_per_quote + cost_per_lot_usd)`; below `min_lot` a skip with `below_min_lot`. `fixed-fraction-at-stop@1` is ripped out through a migration-map row; when the horizon derivation's inputs are stale the ladder falls to the preset rung (a fixed share of the committed cushion) and the receipt says `stale_so_default`, so no second sizer block is needed. `/sizer/inputs/<port>` stays refused (`compiler.py:933`): a sizer reads host facts, never another block. Contract tests run long and short through two adapters per slot.

### 4.4 The guard: `before_order` and the fact set

Replaces `CrossUnitHook.before_order(intent, open_positions, dispersion)` and `PASS_EVERY_ORDER` (J `api.py:196-218`) and the node's static `cross_unit_hook(command)` (N `runtime.py:1066-1069`, called at `:1018`). `Runtime.guard` (N `:2531`) stays as the node's health check. `Runtime.risk_stop` (N `:2602`) gets its first producer: a lockout.

```python
class Guard:                             # packages/qmf-risk/src/qmf/risk/guard/
    @classmethod
    def recover(cls, plan: GroupPlan, rows: Iterable[Row], deals: Iterable[Deal], facts: AnchorFacts) -> Guard: ...
    def advance(self, now: Instant, facts: AnchorFacts) -> tuple[Effect, ...]: ...       # idempotent per anchor_id
    def sizing_facts(self, unit: UnitKey, market: str, entry: Decimal, stop: Decimal, facts: OrderFacts) -> SizingFacts: ...
    def position_facts(self, position: OwnPosition, bar: QuoteBar) -> PositionFacts: ...  # 4.6
    def before_order(self, intent: UnitEntryIntent, open_positions: Sequence[OpenRisk], facts: OrderFacts) -> Pass | Shrink | Refuse: ...
    def on_event(self, event: Fill | Close | Deal | BankerAct | HisAct | KillChange) -> tuple[Effect, ...]: ...
    def state(self, scope: str) -> RiskState: ...

class Pass:   lots: Decimal; trail: tuple[Step, ...]
class Shrink: lots: Decimal; code: ReasonCode; binding: str; trail: tuple[Step, ...]
class Refuse: code: ReasonCode; detail: str; trail: tuple[Step, ...]
Effect = RaiseStandDown | ClearOwnStandDown | WriteStatus | Row | Card | Push       # nothing lowers a kill level
```

**Inside `before_order`, on `wanted_lots`:** 1. refusals, named by rank: kill level and stand-downs at every scope of this unit; benched or locked; guard available, facts fresh, approval valid; SQS, news, admission (band low end minus the cost cell above zero this hour). 2. multiply: level, then the pair's taper on the group day ledger. 3. raises, only if nothing above is active and the raise gate passes: dial, press (shadow at go-live). 4. caps, smallest wins: bet key, cushion clip, per-trade worst case, sanity band, margin headroom, order rate, stop side. 5. round down to `lot_step`. 6. shadow rows run on the same inputs and write `would_have`; the answer does not change. The receipt names the binding clamp and counts it.

**The fact kernel** (`guard/facts/`, `PROVIDES`): a port builds `OrderFacts` per call and `AnchorFacts` per anchor. Node source, QMB source, fail mode:

| Fact | Node | QMB | Missing or stale |
|---|---|---|---|
| `equity_balance` | timed re-read in `ctrader_account.py` (today once at sign-in, `equity()` `:698`) plus R22's wait | start plus closed, `unit_handler.py:370` | refuse |
| `equity_marked` | none yet: `None` | `None` | label `basis:unmarked` |
| `deals` | R20 closes; deal money when R24 proves the fields | handler fills | price-derived, labelled |
| `open_risk_at_stop` by bet key, `open_risk_total`, `pending_risk` | `_mine()` and `stop_of` | `HeldPosition` | count at the entry stop |
| `foreign_open_risk` | the reconciler's not-ours positions (DP33 flag) | 0 | account numbers only |
| `day_start_equity`, `budget_used`, `high_water_mark_equity`, `money_ledger` per scope | the guard's own, persisted | same | rebuild from rows and deals |
| `cost_cell` | the hourly profile, else the pooled stressed class default | the stated profile (`host.py:2090-2125`) | `cost:uncalibrated`, never refuse |
| `quote`, `usd_per_quote`, `value_per_point`, lots | `venue.feed.quote`, the record | bar bid and ask, the record | refuse |
| `sqs_reading` | the producer on `feed_keeper.py` quotes and R19's minute rows | bar spread, `sqs:bar_sampled` | refuse (G12 section 2's rule text) |
| `calendar` | `qmn/data/news_calendar.py` | the recorded strip | refuse the affected legs |
| `kill_level`, `stand_downs` | `level_for`, `stand_downs.blocking` | adapter table | refuse |
| `margin_used`, `margin_free`, `leverage` | the record; `leverageId` after G-DEMO | the record | refuse |
| `clock_ok`, `feed_fresh` | R23 | true | refuse |
| `evidence` | agent records, later | none | 1.0, neutral |

The MIS board stays outside: it keeps publishing, fails open, and the router must not place into a stand-down. Three fail modes show together on the preflight: board open, isolation closed, evidence neutral.

### 4.5 The rank table

```yaml
rank:                     # on the group; bands fixed, rows append inside a band, never renumber
  100_operator:     [kill_level, flatten, pause, resume]
  200_protection:   [disaster_stop, protection_close, forced_flat, kill_close]
  300_health:       [guard_unavailable, feed, clock, reconcile, approval]
  400_tail_brake:   [day_stop, unit_bench, lockout]
  500_gate:         [sqs, news, admission]
  600_cap:          [bet_key, cushion_clip, per_trade_cap, sanity_band, margin, order_rate, stop_side]
  700_multiplier:   [level, taper]
  800_accelerator:  [dial, press]
  exit: [kill_close, risk_close, disaster_stop, thesis_fi, backstop, time, target]
```

Refuse beats shrink; caps smallest; multipliers product, each on its own ledger; band 800 only with everything above clear; the state folded is the highest, on every pass, even when the unit sent no intent (a benched unit under a day stop reads HALTED, not BENCHED). The `exit` row is read by the pure `safest_exit(answers, rank)` inside the unit: closes beat amends, safety beats strategy, the tightest stop wins among amends; compiler slot order decides evaluation order only. The property test (`tests/test_rank_property.py`, 20,000 random control states) holds the guard's fold equal to one table and proves no raise passes while any brake is active.

**Kill levels** (replaces `PLACEHOLDER_KILL_EFFECTS`, N `qmn/src/qmn/protection/effect_matrix.py:137-143`): YELLOW no new entries at scope; ORANGE no new entries, resting cancelled, amends tighten only; RED close this node's positions at scope (`_close_scope`, N `runtime.py:2359`), no entries; BLACK close everything and pause, resume only by his hand. While the node sends market entries only, YELLOW and ORANGE act alike; both are shown.

### 4.6 The exit socket

This answers "agree the socket with it first". G12's guesses 1, 2, 3 and 8 are accepted. Today a per-bar exit is fed `{}` (J `unit.py:686`), a stop reads `{}` once at entry, per-bar exits with inputs refuse (`compiler.py:474, 491`), and `timer()` builds long-only (`:444`).

```python
class PositionFacts:                     # OwnPosition (unit.py:129-138) stays; this is what an exit reads, built by HostedUnit.exits (:671)
    position: OwnPosition; stop_held: Decimal; stop_at_entry: Decimal; targets: tuple[Decimal, ...]
    bars_held: int; mae_r: Decimal; mfe_r: Decimal; realized_r: Decimal     # R10's MAE and MFE (unit_handler.py:97-99, 249-250) move here
    side_price: Decimal                  # bid for a long, ask for a short (hand-offs 12, 14)
    numbers_in_force: Mapping[NumberId, Decimal]   # the exit numbers stamped at entry (hand-off 8)

class CloseAnswer: mechanism: ExitMechanism; fraction: Decimal = Decimal(1); detail: str = ""
class AmendAnswer: new_stop: Decimal; mechanism: ExitMechanism            # an absolute level (AD-13); tighten only
ExitAnswer = CloseAnswer | AmendAnswer | Signal | Decimal | None           # Signal keeps time-exit-bars' reason code

class ExitMechanism(StrEnum):            # exit_mechanism on the trade row
    STOP; FI_CUT; THESIS_FI; BACKSTOP; BREAKEVEN; TIME; SIGNAL; TARGET; TARGET_BACKSTOP; TRAIL
    FORCED_FLAT; KILL_CLOSE; RISK_CLOSE; LIQUIDATION; ROLL; HAND; UNKNOWN
```

- **Step 2, about 60 lines plus tests.** `HostedUnit.exits` builds `PositionFacts` and feeds every per-bar exit; `timer()` passes the side; several per-bar exits may run and `safest_exit` picks; only `CloseAnswer(fraction=1)` and `Signal` map to an intent (`close_full`). Lifts `exit_not_built` for position facts and whole bars; one stop stays.
- **The disaster stop** is the unit's `ExitUse.STOP`: venue-resident on every live entry (`require_venue_resident_protective_stop`, N `runtime.py:1020` stays); R is measured to it; its distance is a number with a derivation in `exit_numbers`. `stop_not_built` (`compiler.py:502`) stays: no unit without a price stop at go-live (hand-off 7). The **cut** is `fast-invalidation-cut@1`, a per-bar close whose level derives from the winners' MAE percentile (`fi_cut_mae_percentile`), run as a counted two-arm trial per unit through the harness (F1 open).
- **The target rests at the venue** (hand-off 6; section 9). The entry carries a `protective_target_distance` beside `protective_stop_distance` (J `commands.py:361`; the encoder writes `relativeTakeProfit` beside `relativeStopLoss`, `encode.py:748-752`); until that lands, one amend with `ProtectionSide.TARGET` right after the fill (`encode.py:1029` already writes `takeProfit`). The node's `protective()` (N `runtime.py:1757-1772`) keeps its market close only as a backstop one bar after the level is passed with no venue fill, labelled `TARGET_BACKSTOP`. QMB keeps booking the target at its level (J `qmb/src/qmb/execution/fill.py:1327-1328`), which is now the same rule.
- **Step 3, about 250 lines, waits for the signed stop.** It lifts `AmendAnswer` and `fraction < 1`, maps them to `amend_protection` and `close_partial`, makes `_move_stop` (N `:1308-1329`) take an absolute level and lets the encoder sign it, replaces R21's `Blocked` (N `:1279`), restores a lost stop from the latest accepted amend row rather than the send row, and needs R24's fact on what the venue holds. A partial that leaves a rest under `min_lot` closes in full (N `:1722-1723` stays). Trails are shadow catalogue entries until then.
- **Trade row v2** (R `journal_kinds/unit.py`; body `qmb/src/qmb/results/journal.py:412`): adds `exit_mechanism`, `r` (gross), `net_r`, `costs_r{spread, commission, slippage, swap}`, `mae_r`, `mfe_r`, `bars_held`, `profile_version`, `level_at_entry`, `labels`, `session`, `equity_before`, `stage`, `world`. `r_after_costs` (J `unit_handler.py:724`, gross today) becomes `net_r`; the judge's `trade_r` stays gross. Ledgers read deals, not trade rows (AD-12).

### 4.7 The RiskState row

```python
class RiskState:                         # journal kind risk_state on the node stream; on change plus a heartbeat (risk_state_emit_interval)
    at: int; scope: str; generation: str; anchor_id: str; rev: int
    word: Literal["GREEN", "YELLOW", "ORANGE", "RED", "BLACK", "UNKNOWN"]   # risk_light_state; stale reads UNKNOWN
    state: Literal["ACTIVE", "REDUCING", "BENCHED", "HALTED", "RESTORE"]      # x1_trading_state, computed never stored
    equity: Mapping[str, Decimal | None]; basis: str                          # balance, marked, realised today
    cushion: CushionRow; sigma: SigmaRow                                      # committed, reserve, floor, buffer, kill_line_distance; budget, sized
    open_risk_usd: Decimal; open_risk_by_key: Mapping[str, Decimal]; budget_used: Decimal
    ledgers: Mapping[LedgerKey, Decimal]; level: Decimal | None; units_admitted: int; units_shed: tuple[str, ...]
    kill: KillRow; drift: DriftRow                                            # requested, enforced, observed
    brakes: tuple[BrakeMeter, ...]                                            # id, mode, class, state, distance_to_trip, fires, would_have
    binding_clamp: Mapping[str, int]; placeholders_live: tuple[str, ...]; fail_modes: Mapping[str, str]
    facts_age_s: Mapping[str, int]                                            # the staleness that made UNKNOWN, if any
```

Register `risk_state` beside `guard`, `risk_event` and `would_have` (R `journal_kinds/unit.py:179-181`). The screen, the copilot, agents and the Lab read one fold.

### 4.8 The agents' read, run and propose surfaces

Catalog rows (`qmx_control/catalog.py`), each with `direction ∈ {read, run, propose, cut, raise, money}`; the host admits `read`, `run`, `propose` and `cut` to agent principals; `raise` and `money` answer only to him. **QMA flag:** `direction` is a new catalog field beside `Approval`; CI fails a row without one; `admits` must read it. Flagged, not designed.

| Row | Direction | Reads or writes |
|---|---|---|
| `risk_state`, `risk_explain`, `risk_ledger_query`, `risk_placeholders_list` | read | the RiskState rows, the status file, a number's chain and receipt, the ledger row, the placeholders live |
| `risk_profile_check`, `derivation_preview`, `risk_resize_replay`, `risk_scenarios_run` | run | the same guard on a replay port: a profile checked, a derivation previewed, a unit's trades under another profile, the mandatory X4 block |
| `risk_profile_new` | propose | a draft; a card and plan on save; his click publishes |
| `risk_evidence_put` | cut | an expiring record of an accepted kind, max cut, floor; the guard's `evidence_cut` reads it; expired or malformed means 1.0; `accepts_evidence` is empty at go-live |
| `risk_card` for a loosening | raise | a card from an effect descriptor (hash, base version, scope, ledger ids, expiry); only his click acts; stale refused |
| promote, resume, kill-lower, once-rule sign | money | operator only, never an agent |

No row sends an order, lowers a kill level, blocks an exit, raises a level or moves a `user_only` number (AD-3, AD-4, AD-11). The fast loop never waits for a model; a dead agent changes nothing. On demo, agents' cTrader order tools stand by his ruling; the guard counts what they open as `foreign` (DP33).

### 4.9 Compiler refusals to lift, and the format bump

`COMPILER_FORMAT_VERSION` is 4 (J `compiler.py:100`); each slice that changes the compiled shape bumps it (exit step 2, the profile; step 3 later) and moves the fingerprint and `pack.json`. Nothing is live, so a cold start costs nothing.

| Refusal | Where | At go-live |
|---|---|---|
| `exit_not_built`: a per-bar exit with inputs; a second per-bar exit | `:474`, `:491-494` | **lifted** for position facts and whole bars; one stop stays |
| the six exits refused by shape | `:361-362` | three close-only run as shadow catalogue; three trails wait for step 3 |
| `stop_not_built` | `:502` | stays; the profile's disaster-stop number satisfies it |
| `halts_not_built` | `:903` | **stays**, message names the profile and the group (brakes are guard rows) |
| `inputs_not_built` on `/sizer/inputs/<port>` | `:484`, `:933` | stays; `sizing:<market>` is a host surface, not a block reference |
| `open_positions_not_built` | `:998` | stays (hand-off 8) |
| `cadence_not_built` on `cadence.at` | `:1011` | **lifted**: the anchor clocks read it |
| `motion_not_built` on the authority fields | `:869` `_MOTION_READ`, `:1004` | **widened** for `authority.mode` and `derivation` |
| `binding_not_read` for a halt in a logic slot | `:724` | stays; the needs list is the check for guard rows |
| `reads_`, `sessions_`, `limit_not_built`, `plain_python`, `settings`, `position_limit` other than 1 | `:900-961` | stay |

New refusals: `authority_not_built`, `packs_not_built`, `suggestions_not_built`, `group_parent_not_built`, `needs_not_met`, `two_live_readers`, `number_blank`, `rank_band_unknown`. New census rows: `risk_profile`, `risk_group`, `numbers.*.derivation`, `numbers.*.authority.mode`. A unit with no profile runs in QMB and paper; the live click refuses it.

## 5. The forks, settled

**F-A, the shape of the full model with the simple modes on.** The document, status and receipts carry the Kubernetes and VPA shape from day one: spec and status, a recommendation with bounds (filled later), an authority mode per number. At go-live the modes on are `user_only`, `off`, `at_anchor` and `at_flat` (the shipped motion engine already moves logic numbers when flat, G8 3.9); `at_period_open` and `live` parse and refuse. This costs nothing later and needs no reader changed, because every reader reads the value in force. The one argument for `live`, a cost cell after a broker change, is answered by AD-6: a cost cell is a fact the sizer reads, so it acts at once with no learned number moving; the `cost_alarm` trigger re-derives the admission gate the same day. Candidate 1's own sim showed `live` earning only on that case (+0.9 % to +3.3 % of the cushion on a lag day at scalper rates) and nothing on a healthy unit or on slow decay. **What would make `live` win:** lag money above about half a sized day sigma per broker cost event on real fills, or his wish to see a number move between anchors; then lift `authority_not_built` for that mode and nothing else changes. **He must hear plainly:** Kubernetes is the model; the first version runs it in its simplest modes.

**F-B, one guard above the position.** Every brake above the position runs in one package with one rank table and one fact set; brake blocks keep the shipped `HaltInstance` shape, hosted by the guard, so a later move of a unit's own brake into the unit is a move, not a rewrite. Candidate 3's version was serious: its fact kernel and its shadow rule are in this spine. Its cost was two arbitration stages and a fact round trip for every cross-unit brake. **What would make the unit-level home win:** units that run for long stretches on hosts with different guard versions, or on a third-party host; today one node owns an account and both hosts ship from one lockfile. The sub-choice: the guard ranks controls; the compiler's order ranks the unit's own exits, read by `safest_exit`.

## 6. The extension proof

| Change | Files | Rows | Guard or compiler code | Rework? |
|---|---|---|---|---|
| A new brake | one folder `stdlib/<brake>/1/` with `entry.json` (its `guard` section) and `block.py` implementing `HaltInstance` | a binding on the profile or group, `mode: shadow`; its numbers; one reason code | none, unless it reads a new fact: then one provider in the kernel and one port line per host (`needs_not_met` says so at compile) | no |
| A new sizer base | one derivation folder, `produces: baseline_risk_usd` | `numbers.baseline_risk_usd.derivation` pin; needs | none; the sizer block is unchanged | no |
| A new instrument class | venue port work outside this design (`CcxtClient.equity()` must stop answering 0 on a failed read, J `ccxt_client.py:597-601`) | a class diff in the preset, a day clock row, a cost default, a worst-step row, bet-key legs, `class:<x>`; feasibility decides live or paper | none; carry fields on the cost cell, later | no; whole-contract classes at $500 read infeasible until the contract ladder |
| A new style preset | a Library `template` item | bindings, derivation choices, exit family | none, unless a new exit block | no |
| He changes how one number derives | none | a new profile version: rule, ladder or rung order; the plan card shows the move; his click; in force at the next anchor after adoption; a `user_only` value edit is immediate and journalled | none | no; `profile_sizing_change` keeps the record, a number under `exit_numbers` is a counted try |
| An agent proposes a tighter limit | none | an evidence record if the unit declared that kind (cut only, expiring); or a draft version for a lasting limit, which is a card | none | no; neither touches a user row; enabling evidence is one spec row |
| The Lab simulates a variant | none in the guard | a variant profile | the same package on a replay port through `risk_resize_replay` | no; nothing the Lab writes is in any fact bundle (**QMA flag**: the Lab app is unbuilt) |
| A version rollout keeping the record | none | v2 pinned; a `would_have` sheet beside v1 for the shadow window; the bound click; the identity label | `logic_fingerprint` compare, built at go-live | no; the rip-out of `fixed-fraction-at-stop@1` is its first use, with a migration row |
| Class isolation, shadow to binding | none; the shadow row shipped | the group row flips `mode: shadow → live` after its precision report; his click (Q1) | none; `Kind.RISK_RULE` and the `class:` key exist from go-live | no |
| House money's press switching on | none; the shadow row computed the same multiplier | the proof card passes at an anchor; the once-rule signed (Q4); `press_armed` at the next anchor; the raise gate needs every brake clear | none | no |

Two findings fixed in the design: house money is intraday, so "raises wait" would have made the press a day-over-day compounding; fixed in AD-7 (a multiplier reads a live ledger inside bounds frozen at the anchor; permission to exceed 1.0 is the raise). A `Kind` per brake in `stand_down.py` would have been rework; fixed with one `Kind.RISK_RULE`. Admitted: a brake reading a truly new statistic is code in the kernel; registry rows do not make facts appear. `position_limit` above 1 stays refused and ledgers key on (unit, market).

## 7. The performance proof

Factor chain for every unit at go-live, in order (the fifteen of FUNNEL 5.2): 1 the cost denominator (in the sizer block, live); 2 B over admitted units, freed swing to units at level 1.00; 3 the level; 4 the pair's taper; 5 the bench (trip); 6 the lot-shed on N; 7 the cushion clip; 8 the bet-key cap; 9 the worst-case veto and sanity band; 10 margin headroom; 11 lot round-down; 12 SQS; 13 news; 14 the admission gate; 15 world and version resets. The unit's running loss is read once, by the bench (unit scope); the group's once, by the taper and the day stop (group scope); the edge stream by the cohorts and the CUSUM, which set the level; the cushion moves only at the anchor; the clip reads live usable cushion as a cap, not a running total; the sizer's live share reads open risk at the stops, which is exposure, not loss.

The fold's integrated check (`fold_sim.py`, `out-fold.txt`; appendix A has the table) reruns the funnel's harder sim with only what the fold changed: raises at the anchor, freed swing, the day stop on the sized sigma at a derived k, and the drift lockout (every warning one level down and locked there for the bench's lockout; the third inside the window is paper). **A healthy unit stays above the 0.75 choke budget at N = 1, 5 and 10** (0.87 to 0.89 of baseline), and 3 to 8 % of healthy units reach paper in 120 days against 25 to 37 % under the funnel's second-warning rule. The bleeding book of many units stays the funnel's open item; the pooled CUSUM (shadow) is the next test.

## 8. The scenario walks

Appendix B walks X4-01, X4-14, X4-66 and a mid-outage restart (X4-45 with X4-48 and X4-71) on these contracts. All meet their bar in the model. Stated gaps: no same-driver cooling time after stops fire (X4-01, the hours clause is shadow); the bleeding book at N = 5 and 10 (X4-66); the fire rate on clustered real days is unknown (X4-14).

## 9. The hand-offs

| # | Item | Answer | Status |
|---|---|---|---|
| 3 | Stop past entry | In scope at step 3 only; absolute levels at every seam, the encoder signs (AD-13); R21's `Blocked` stays until then | decided; R24 fact |
| 4 | Stop widening | Never; the law at `unit_intent.py:720` stands; the placeholder swing stop goes | decided |
| 6 | Target at the broker | **Rests at the venue.** QMB books a target at its level (`fill.py:1327`); the node closes at market a bar later (`runtime.py:1757-1772`), and one wicked bar read +2.00R against −0.55R (seams-7). "Backtest and live run the same rules" decides it; the node's close stays only as a labelled backstop. Candidate 1's "the node closes" is overruled | decided; R24 must prove the venue's close kind |
| 7 | A unit with no stop | Refused at go-live (`stop_not_built` stays); a stop-less base is a later plug with a declared worst case | decided |
| 8 | A moved number and open trades | Open trades keep their entry stamps; `applies_to_open_positions: true` stays refused | decided |
| 9 | Two exits on one bar | `safest_exit` on the rank's `exit` row; closes beat amends; the winner is the row's mechanism | decided |
| 5 | Partial close and R | R stays the planned loss; realised R piecewise; a rest under `min_lot` closes with the partial; ships at step 3 | decided |
| 22 | R and costs | AD-12; our call, his B9 reservation stands | decided |
| 23 | Kill level meanings | Section 4.5; the day stop raising YELLOW itself is Q5, default a stand-down and a card | decided; Q5 his |
| 24-26 | Refusal alarm count, unplaceable protection, kill line | A number; close, as built; no new entries at the buffer, automatic reduce is Q1b | values wait; Q1b his |
| 27 | Where SQS sits | In the guard, band 500, entries only; the producer moves from `qmn/host/sqs_baseline_producer.py` to `guard/spread.py`; the rule text of `decision_root.py:493-510` unchanged; eight settings derive from the spread histogram's percentiles; DEC-0230 stands, so **the first live entry waits hours for a live-account baseline** | decided; values wait |
| 34 | `too_thin` | `presets.py:45` `min_trades=100` becomes `verification_trades_needed` at the band's low end with an incubation cap | decided; value waits |
| 35 | Version pull | A sizer-only swap trades the same R and pays the pull; an exit change is a counted try; re-read once R11 lands | decided |
| 36, 37 | Rules on a real run; a check with no orders | Never claimed by a stack list; no orders ends `inconclusive` | decided |
| 1, 2, 10, 12, 14 | The socket, six exits, position facts, `timer()`, bid bars | Section 4.6 | decided |
| 11, 13 | Wicked-bar stop; lost stop | Refused at `enter` and at send; the latest accepted amend row, at step 3 | decided |
| 15-20 | USDJPY, costs, receipt, wrong side, socket tests, real risk | Sections 4.3, 4.4; `residue_r` on the row | decided |
| 21 | Metal margin | Account leverage until `leverageId` is read; clamp labelled | waits for G-DEMO |
| 28-33 | Halts, statistics, the hook, row fields, the Book, grids | Sections 4.2, 4.4, 4.7; the guard holds the bet-key ledger; Book against tags is Q8; grids refused at preflight | decided; Q8 his, later |

The work proceeds on the funnel's defaults for Q1 to Q8; none blocks the build. Q7's pushes need his word before they exist.

## 10. The build plan

On landed repair tips only. Must land first: R04 to R06 (format 4, refusals, the record reaches the run) at J; R10 (money measures); R15 (reason census); R20 and R21 (the broker wins, `_close_scope`); R22 (the real balance, the snapshot path); R17 (`_admit`, `_deployment`). Everything above R06 is unreviewed or unmerged (G12), so slices 1 and 2 start on J and rebase.

| Slice | PRs | Main files | Needs landed | Collides with |
|---|---|---|---|---|
| 1. Exit step 2; trade row v2 and `net_r`; the cut block and its two-arm trial | 3 | `qml/protocol/unit.py`, `blocks/api.py`, `compiler.py`, `unit_handler.py`, `results/journal.py`, `journal_kinds/unit.py` | R04-R06, R10, R15 | R15 journal; rebase after it |
| 2. Guard core and seam; the fact kernel with both ports and the conformance tape; status file and `recover`; RiskState; delete the hook | 4 | `qmf/risk/guard/*`, `guard_port.py` x2, `ctrader_account.py` (timed re-read), `unit_handler.py:358,484`, N `runtime.py:1018,1066`, `api.py:196-218`, `journal_kinds/` | R15, R20, R21, R22 | R22 rewrites `_host` (`:2654`); `first_start.py` for the first status write |
| 3. Profile and group documents, presets, numbers widening, census, format 5, `_deployment` carries both | 4 | `qmx_library/kinds/risk-*.schema.json`, `qml/risk/*`, `qml/unit/model.py`, `compiler.py` (4.9), `promote.py._deployment`, `catalog.py` | R17 | R17 `_admit`, `_leave` |
| 4. Anchors, the applier, first derivations (horizon-floor-odds, cost cells with the pooled default); `money-at-stop@1` and the rip-out with its migration row; feasibility and shed | 3 | `guard/anchor.py`, `guard/applier.py`, `stdlib/*`, `identity/table.py`, `host.py:2090-2125` | 2, 3, R11 | R11 |
| 5. Climb and drift: start level from the card, cohorts, CUSUM, the drift rule | 2 | `guard/level.py`, `guard/drift.py`, judge `presets.py` | 4 | none |
| 6. Tail brakes, clamps, registry rows, rank table and its property test, `Kind.RISK_RULE`, scope keys, retry-then-lockout | 4 | `guard/brakes/*`, `guard/ledger.py`, `registry.py`, N `stand_down.py`, `operations.py:241-258` | 2, 5, R21, R23 | R21 `_close_scope`; R23 stand-downs |
| 7. SQS slice; the news window; the kill table | 3 | `guard/spread.py` (moved producer), `labelers.py` rule, `registry_catalog.py` rows as derivations, `feed_keeper.py`; `guard/news.py`, `news_calendar.py`, `windows.py`; `effect_matrix.py` | R19; before C-20 and deletion-4 | C-20; R21 kill path |
| 8. Harness: the integrated sim lifted in (`fold_sim.py` the first job), the mandatory block, the choke test in CI, the dry chassis | 2 | `qmf-risk/harness/*`, `ReplayPort` | 2, 4, 5, 6 | none |
| 9. Machine check, the bound click in `_admit`, two records, identity rows, world switch, preflight firewall | 3 | `promote.py:321`, `identity/table.py`, `judge.py`, `qmx_control/service.py` | R17, R18, 8 | R17 |
| 10. Shadow rows for the timing brakes and the press; morning card; alert tiers; agent rows | 2 | `stdlib/*`, card renderer, `catalog.py` (QMA flag), alarm register | R16, Q7 | R16's closed push list |
| 11. Target at the venue | 1 | N `runtime.py:1055-1057, 1757`, `commands.py`, `encode.py:748`, `ctrader_account.py` | R24 | R21 |

**31 PRs [judgment]**, inside the funnel's 25 to 35. Order: 1 → 2 → 3 → 4, then 5 and 6 in parallel, then 7, 8, then 9, 10, 11. Not counted: exit step 3, two more PRs after R21's block lifts and R24 reports. The F1 trial runs as soon as slice 1 lands, on bare QMB, and may change slice 4's first preset.

**Collisions with the repair:** N `runtime.py` at the hook call (`:1018`, deleted), the health check (`:2531`, stays), `risk_stop` (`:2602`, first producer), `protective` (`:1757`), `_move_stop` (`:1308`, step 3), `_host` (`:2654`); `host.py:2090-2125`; `first_start.py`; R17's `_admit` and `_deployment`; R21's `_close_scope` and `Blocked`; R22's snapshot path and balance wait; R15's `REASON_CODES`; R16's closed push list; R18 leaves the board unwired, so isolation stays shadow by construction.

**Claimed before C-20 and deletion-4** (extends `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md`): the files it names, plus `qmf-risk/control_rank.py`, `control_action.py` (the rank table's shape and `effect_matrix.py`'s importers), `qmf-risk/sizing` (the kill line `qmn/capital` reads), `qmf-risk/versioning` (the migration map's seed), `qmn/protection/effect_matrix.py`, `qmf-data/calendar_feed.py`.

**Unknown until his demo sign-in (R24):** whether a fill carries the stop; deal fields; a close on a gone position; real slippage and commission; the venue's close kind for a take-profit. **Go-live dependencies the funnel does not list:** the right bars come after G-DEMO (every unit gets 15-minute today, R22 refuses the mismatch), so a 1-minute cut cannot run on the node before then; the SQS baseline on a live account takes hours before the first entry (DEC-0230).

## 11. Cuts and additions

**If told to cut more, in order:** the press's shadow row; the dial and Q6; the chain to three keys; freed swing (flat B only); `risk_card`; the morning card's prose; news's per-leg logic; the Simplex rung in the sizer ladder. None changes a contract. Not cut: the bench, the day stop, the clip, SQS, receipts, the choke test.

**Added beyond the funnel, and why:** the group document, so the one portfolio config has a contract and Q8 stays open; facts live and numbers at anchors, which removes the case for `live`; the fact kernel with a conformance tape; a sizer base as a derivation, which makes a new base a row and fixes USDJPY at its root; `two_live_readers` as a compile refusal (M3 as structure); the choke budget as a CI test; one seam in `unit_handler.py`; the `cost_alarm` trigger; `tzdata`; absolute stops at every seam; the drift lockout (appendix C: the bench's retry-then-lockout applied to the CUSUM, so one restore rule serves the unit's two brakes); the day stop's k from the group's own bad day with the tail rows on; freed swing; `foreign` risk counted at the account; the status file rebuilt from journals; resting targets.

## 12. Assumptions, open questions, deferred

`[ASSUMPTION]` the unit's status file sits beside R22's snapshot under `data/deployments/<id>/` and the group's under `data/risk-groups/<id>/`; R22 is not started, so the paths may move. `[ASSUMPTION]` one account and one group at go-live, so `all` equals the group. `[ASSUMPTION]` QMB runs one unit with N from the group's plan; multi-unit behaviour is proven in the harness. `[ASSUMPTION]` the first units are FX scalpers at 10 or more trades a day. `[ASSUMPTION]` `UnitSliceHandler` can take a `sizing:<market>` surface without touching the per-market surfaces. `[ASSUMPTION]` agent positions on the demo account read as `foreign` from `attribution.py`'s "not ours". `[ASSUMPTION]` cTrader's order form takes a take-profit on a market order the way it takes `relativeStopLoss`; the amend path is the fallback either way. Open for him: Q1 to Q8 as the funnel lists them. Open for the numbers lens: h and the drift window; the day stop's target fire rate; the dollar clamp; the eight SQS rows; `verification_trades_needed`; the reserve share; the floor-touch tolerance; the survival horizon.

**Deferred, with plug points:** learner bounds and the modes `at_period_open` and `live` (`Recommendation.low`, `high`; `authority`); dead band and share cap (fork rows); the `suggestions` part and its card queue; packs beyond one and combiners beyond `smallest_cap`; the seven reserved keys, tags and drop-ins (`tag:` scope key); the cluster level and Q8 (`risk-group.parent`); pooled priors across a cluster; halt slots inside the unit (a move of rows); exit step 3, the six refused exits, breakeven, trails; REDUCING, loss points, "about three", density, chorus, burn tiers, class isolation, the weekend scale, the Kelly ceiling, the memory ceiling, probes and earned restore (shadow rows, `RegistryRow.restore`); cushion lending, shed classes, de-gross, the ratchet and the sweep (group rows; his base floor split from the lock line); whole-contract ladders, inverse volatility, carry; the trust ladder and outside code (loader signature); the canary, challenger, funded gate, rehab; marked equity (`basis:unmarked` until it lands); the commission key and a cost profile from fills (after G-DEMO); multi-position units; the phone push list (Q7); automatic closes (Q1b); the agent jobs, the mini app, the Lab tenancy, the department (**QMA flag**).

**Stack:** Python as the repo; `tzdata` new in `qmf-risk`. No other new dependency.

---

## Appendix A. The fold's integrated check

`fold_sim.py fold 40 120`: 40 paths, 120 days, the worked example, fat tails, gap days, lot rounding with the shed rule. Size as a share of the flat baseline; `paper%` is the share of units the drift rule sent to paper inside the run. The funnel's core as `core_sim.py` ran it (flat B, budget sigma k 2.5, second warning to paper) against the fold (raises at the anchor, freed swing, sized sigma with k derived from the group's own p1 day, third warning to paper). **Model numbers only.**

| Case | N | Funnel core: size / half-cushion runs / stops per 100 d / to paper | Fold: size / half-cushion / stops / to paper | Median $ funnel → fold | Derived k |
|---|---|---|---|---|---|
| Healthy +0.10R | 1 | 0.92 / 0 % / 0.00 / 25 % | **0.87** / 0 % / 0.23 / **5 %** | 1568 → 1687 | 2.17 |
| Weak +0.05R | 1 | 0.89 / 0 % / 0.00 / 32.5 % | 0.82 / 0 % / 0.21 / 5 % | 733 → 716 | 2.18 |
| Bleeding, card +0.10R | 1 | 0.73 / 0 % / 0.00 / 100 % | 0.49 / 0 % / 0.29 / 97.5 % | 442 → 442 | 2.17 |
| Healthy | 5 | 0.89 / 0 % / 0.00 / 37 % | **0.88** / 0 % / 0.46 / **7.5 %** | 3434 → 4127 | 1.64 |
| Weak | 5 | 0.84 / 0 % / 0.00 / 11.5 % | 0.80 / 0 % / 0.29 / 1.5 % | 696 → 658 | 1.95 |
| Bleeding | 5 | 0.73 / 22.5 % / 0.00 / 59 % | 0.62 / 17.5 % / 0.71 / 26.5 % | 415 → 412 | 1.64 |
| Healthy | 10 | 0.90 / 0 % / 0.00 / 25 % | **0.89** / 0 % / 0.98 / **3 %** | 4566 → 5311 | 1.45 |
| Weak | 10 | 0.83 / 0 % / 0.00 / 6 % | 0.81 / 0 % / 0.94 / 0.5 % | 686 → 726 | 1.76 |
| Bleeding | 10 | 0.73 / 17.5 % / 0.00 / 27 % | 0.60 / 25 % / 1.73 / 12.3 % | 412 → 414 | 1.45 |

Reading: the healthy unit stays above the 0.75 budget in every cell and pays two to five points of size for the drift lockout; freed swing returns most of that at N = 5 and 10, where the healthy medians rise 16 to 20 %. The derived k lands between 1.4 and 2.2 and fires 0.2 to 1.7 times per 100 days, about once a month at most, as his bar asks. The drift lockout sends 3 to 8 % of healthy units to paper inside 120 days against 25 to 37 % under the funnel's rule, and holds the bleeding book's half-cushion runs where the funnel left them (17.5 to 25 % at N = 5 and 10); the bleeding unit trades at half size while it bleeds. Floor touches are 0 % in every cell, with the structural caveat (F12) standing. The bleeding book at N = 5 and 10 stays the funnel's open item; the first fold run, before this rule was settled, is kept in `out-fold-notails.txt` and the decomposition in `out-decompose.txt`.

## Appendix B. The scenario walks

**X4-01, five units lose on one shared move.** N = 5. Before the move: `before_order` adds each entry's risk to its bet key; short EURUSD and short gold both load `currency:USD:short`; once `open_risk_cap_per_key_usd` binds, the next entry shrinks or refuses with `bet_key` and the receipt names the clamp. The move: each venue-resident stop fires at rank 200; exits never met the guard; R20 reconciles the closing deals and the kernel writes five `TradeFact` rows in `net_r` about −1. Each unit's bench reads its own window once: −1R against an own p1 near −5.3R, no bench, no streak it did not have. The group day ledger falls about five sized losses, under the taper's start; one reading. The press is shadow and its row would have stayed locked inside `loss_event_window`. Next anchor: cushion down about 2 %, B recomputed on admitted units, N not raised under the caution, baseline down. Bar met. Gap: no same-driver cooling time; once the stops fire the key's open risk is back to zero, so a unit may re-enter the same move; only the taper and the day stop lean against that.

**X4-14, everything is bad everywhere.** N = 10, sizes $0.50. Losses mount across classes; each unit's bench acts at its own loss. The group day ledger passes the taper's start and new entries shrink; it reaches `day_stop_sigma_multiple` times the sized sigma and the guard emits `RaiseStandDown("all", rule="day_stop", clears="next_anchor")`, a `Card` (the one-tap escalation) and, if Q7 says yes, a `Push`. Entries refuse from band 400; exits and venue stops run; no position is closed by the rule (Q1b default); the kill level does not move (Q5 default). Class isolation computes in shadow and shows on the card; he is told it does not bind. Next day anchor: the stand-down clears (a raise, so it waits for the anchor); the baseline re-derives on the smaller cushion and the stop tightens with it. Model (`out-verify-k.txt`): on an X4-14 day of edge −0.40R the book loses about 13 % of the morning's cushion with no stop and about 9 % at k 1.5 to 1.7, for about one point of size; the derived k fires about once per 100 days on a healthy book, against his bar of about once a month and never on a normal day. Passes in the model; the rate on clustered real days is unknown.

**X4-66, the overfit card and the twin.** QMB's deflated holdout: low end below zero refused live; at zero start 0.25; positive start 0.50. The machine check passes, because the machine is fine. His packet says "proof pending, 212 of 610 trades, level 0.50, expires" and approves one hash, one level, these markets. Live: bad cohorts stop the climb; the CUSUM steps one level at once with cause `drift_warning` and locks the top there for `level_lockout_days`, so the unit cannot climb straight back; a second warning inside the window steps and locks once more; the third moves the unit to paper with `demotion_cause`, re-promotion his click. Model (`out-drift-variants.txt`): the bleeding unit reaches paper in 99 % of paths and trades at half size on the way; the overstated card in 61 %; the healthy unit in 8 % against 28 % under the funnel's rule. Ten unproved units are not ten full bets because B splits them. The twin, a lookahead bug with a too-good first week: nothing at go-live can pay it; the press is shadow, the dial needs its e-bar and a once-rule, raises need all clear, the upside alarm is a shadow row that flags it. Honest soft spot: the bleeding book at N = 10 loses half its cushion in about a quarter of runs before any one CUSUM alarms.

**A restart in the middle of an outage (X4-45 with X4-48 and X4-71).** 14:28 the link drops with four positions open and the group day at −$6; 14:40 the process dies; 16:10 it restarts with no link; 17:00 a day anchor is due; 17:20 the link returns. While down, the venue stops are the only protection, and they work: that is why every entry carries one. 16:10: R22 holds the compiled unit and waits with a plain reason; no handler means no entries; `state()` reads UNKNOWN, never a stale green. 17:00: `advance` sees the anchor due but the balance is stale; it keeps the old values in force and leaves `guard_unavailable` up. 17:20: R20's reconcile runs first and the broker wins; positions closed while down land with price and kind; R21 restores or closes any position with no stop; `reconciler.holds` still blocks entries. The guard reads `risk-status.json`: the generation matches, so the bench, its rest, the day baseline, the ledger window, the level and the anchors come back as they were; deals since the cursor replay in broker order, split across the 17:00 boundary by their own time, and a bench or day stop that should have tripped while down trips now with `cause: outage_catchup`; cuts first. The missed anchor opens with `cause: restart_late` on the real balance; the old day's stand-down clears; a bench's rest counts in calendar time. Entries open only with feed, reconcile, recover, values in force, clock and SQS reading all fresh. If the status file is missing or from another generation, `recover` rebuilds it from rows and deals and `no_new_entries` holds at `all` until it finishes. Five restarts in ten minutes raise `REPEATED_FAULT` and wait for his resume. A test kills the process at ten random points of a replayed day and asserts every brake variable equals the no-restart run's: a restart changed nothing a brake can see.

## Appendix C. The grafts that were claims, verified

Reruns beside this file, time-limited, model numbers; the candidates' own scripts were rerun first and `fold_sim.py` reproduces each.

- **The drift finding (candidate 3).** `candidate3_sim.py` rerun: at h 17 with two warnings inside 500 trades, a healthy 10-a-day unit goes to paper in 42.0 % of 200 one-unit paths inside 120 days (median day 67), a weak one in 41.0 %, the overstated card in 95.5 %, the bleeding unit in 100 %. **Holds.** The pick's answer as written (the third warning is paper, nothing else changes) **fails on the bleeding book**: `out-decompose.txt` and `out-drift-variants.txt` show it returns healthy units (paper 4 to 8 %) but lets a bleeding unit climb back between warnings, so a bleeding book of 5 or 10 units loses half its cushion in 52 to 57 % of paths against the funnel's 17 to 25 %. What holds is the bench's own restore applied to drift: every warning steps one level down **and locks the top there for the bench's lockout (20 days, `level_lockout_days`)**, the third inside the window is paper. Healthy paper 3 to 8 %, healthy size 0.86 to 0.89, the bleeding book at 17.5 to 25 %, the bleeding unit at half size. A lock for the whole 500-trade window also holds survival but costs six to ten points of healthy size; a shorter window (300 trades) or a lock from the second warning only do not hold survival. The rows `drift_warning_window_trades`, `drift_warnings_to_paper` and `level_lockout_days` carry the rule as a derivation, so the numbers lens can move h, the window and the lock without code.
- **The day stop's k (candidate 2).** `anchor_sim.py kstop 40` rerun: on the sized sigma k 2.5 fires 0.00 to 0.02 times per 100 days at N = 1, 5 and 10 and leaves the X4-14 day's loss at 10 to 12 % of the morning's cushion; k 1.5 fires 1.0 to 3.5 times and cuts it to 8 to 10 % for about one point of size; the budget sigma never fires. **Holds.** The fold derives k as the group's own bad day at the target fire rate in sized-sigma units (`day_stop_sigma_multiple`, `fold_sim.k_own_p1`), with 1.7 as the preset rung. A first derivation drew the day from the cards without the class's tail rows and got k 1.0 at N = 10, a stop that fired on most weeks (`out-fold-notails.txt`); with fat tails and gap days in the draw k derives to 1.4 to 2.2 and fires 0.2 to 1.7 times per 100 days (appendix A). `out-verify-k.txt` shows the derived k beside the budget sigma and the rungs.
- **Level-weighted B (candidate 2).** By algebra: DP9 read literally gives `B = sqrt(Σ l_i² + ρ Σ l_i l_j)`, which at N = 1 is `l`, so `size = D ÷ (s z √H l) × l` and the level cancels. `anchor_sim.py bmodes 30` rerun: the literal reading lifts a bleeding one-unit book from 0.76 to 0.94 of baseline and a weak N = 10 book's half-cushion runs; freed swing to units at level 1.00 leaves N = 1 unchanged and lifts N = 10 healthy from 0.89 to 0.92. **Holds.** `out-verify-b.txt` reproduces it in the fold's model.
