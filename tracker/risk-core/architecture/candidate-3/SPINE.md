# Candidate 3: the unit carries its own brakes (F-B b), numbers refresh at anchors (F-A b)

Fable, 6 Nov 2026. Architecture spine for the first increment of the risk-and-sizing template (`funnel/FUNNEL.md` 5.1 to 5.5). Read against the code at the tips G12 names (J `bld-repair-10` for QML, N `bld-repair-21` for the node, R `bld-repair-19` for records); every file and line below was read, not remembered. Proofs: `candidate3_sim.py` and `out-c3.txt` beside this file. **[judgment]** marks opinion. `[ASSUMPTION]` marks an inference nobody confirmed. Memlog: `.memlog.md`.

## 0. Words (one vocabulary, no codenames)

| Word | Means |
|---|---|
| unit | one compiled trading unit, the document `qmx.unit/1` plus its blocks; stands alone on the node |
| risk profile | the unit's risk-and-sizing document: a **spec** (what he and agents chose) and a **status** (what the runtime learnt and did) |
| preset | a profile with derivations instead of numbers, one per unit type (`scalper-mr`, `orb`, `trend-pullback`) |
| portfolio config | the one document above every unit on an account: floor, buffer, kill line, bet-key rule, parent limit, rank table, never-self-tune list, the portfolio brakes. No cluster level at go-live; "Book" and "BMS" stay screen words until Q8 |
| fact | a measured value the runtime computes and nothing learns: equity, open risk, cost cell, spread, kill level, day P&L |
| fact kernel | the one package that computes every fact, with two adapters (QMB, node); the guard, the unit and the harness read it |
| guard | the portfolio's half of the money path: `before_order`, the portfolio brakes, stand-downs, kill effects, RiskState |
| halt | a brake block bound in the unit's `halts` list; the unit's own brake |
| brake / accelerator | any rule that cuts / raises size or entries, with one registry row; class `tail` or `timing`; mode `shadow` or `live` |
| level | the unit's fraction of its derived baseline: 0.25, 0.50, 0.75, 1.00; starts from the holdout, climbs on cohorts, steps down on a CUSUM warning |
| anchor | the moment a learned number is recomputed and applied: `daily_risk` (the day boundary) or `weekly_allocation` |
| receipt | the record on every resolved number and every order: inputs, rung, reason code, binding control |
| stand-down | a hold at a scope key in the node's table (`qmn/app/stand_down.py`), with a cause and a clear rule |
| shadow row / would-have row | a brake running with its action replaced by a journal write (`would_have` kind, R `journal_kinds/unit.py`) |
| cushion, floor, buffer | equity above the floor; the floor he set; the buffer above it where the clip binds |

## 1. The shape in one page

The money path has two halves and one shared kernel.

- **The unit stands alone for its own brakes.** Its sizer, exits, its own brakes (halt blocks), its level and its numbers are blocks compiled into the unit, run by `UnitSliceHandler` in both hosts. On every bar the unit's **halt runner** feeds each halt block the facts it declared, folds the answers (any halt sets the unit's state; smallest cap wins), applies them or journals them as would-have rows (shadow), and only then asks the sizer. The entry intent leaves the unit already sized, with a receipt naming the binding control.
- **The guard holds only the portfolio.** Instantiated by `qmb/host/unit_handler.py` and `qmn/app/runtime.py`, it answers `before_order(intent, open_positions, facts)` with pass, shrink or refuse: the portfolio day stop and the pair's brake half, the cushion clip, the bet-key cap, margin headroom, the order veto, the SQS gate, the news window, the lot-shed at anchors, kill-level effects and stand-downs. It never raises. Exits never pass it.
- **The fact kernel computes, nobody else does.** One package, two adapters. Every statistic a halt, a sizer, a derivation or the guard reads is a named fact with a timestamp and a staleness limit. The host hands the unit its facts through the evidence surfaces it already has (`account`, `own_journal`, `own_position:<market>`, J `unit_handler.py:360-368`) plus one new surface, `facts`. The harness reads the same kernel over a tape, so backtest, live and harness agree by construction.
- **Numbers refresh at anchors; facts move live.** A learned number (risk fraction, the bench threshold, the level) is recomputed by its derivation block at its anchor and applied at the next; `authority` is `off` or `at_anchor`. A fact (a cost cell after the broker changes it, the spread, equity) moves at once because the sizer reads it as an input, not as a number.
- **Who owns what.** He: the portfolio config's user rows and the click. The unit (via its profile): its own brakes, level, numbers. The guard: facts and portfolio brakes. The kernel: shared. Agents: read and propose. The node: the kill switch, by his hand.

```mermaid<br/>flowchart LR<br/>  subgraph HOST[host: QMB handler or node runtime]<br/>    K[fact kernel\none package, two adapters] -->|facts surface| U<br/>    subgraph U[compiled unit, stands alone]<br/>      H[halt runner\nunit + position halts\nshadow or live] --> S[sizer\nfacts in, Size+receipt out]<br/>      L[level + numbers\nderivation blocks at anchors] --> S<br/>      X[exit socket step 2\nper-bar exits fed position facts]<br/>    end<br/>    S -->|entry intent + receipt| G[guard: before_order\npass / shrink / refuse]<br/>    K --> G<br/>    G -->|RiskState every pass| J[(journal)]<br/>    X -->|exit intents, never gated| O[order path]<br/>    G --> O<br/>  end<br/>  P[portfolio config\nhis rows, rank table, brake rows] --> G<br/>  R[risk profile\nspec + status] --> U<br/>  A[agents: read, propose] -.->|tool rows, cut-only facts with TTL| K<br/>```

**How an order flows.** Signal on a bar → halt runner (state, caps) → sizer(facts, numbers) → `Size(lots, receipt)` → intent with `sizer_receipt` → host → `guard.before_order` → pass, shrink or refuse (reason code) → venue. A refusal is a decision row with a closed reason code; a shrink rewrites `quantity` and appends to the receipt.

**How a number gets its value.** Spec names a derivation block and a fallback ladder → at the anchor the block reads facts and the unit's own record → first rung that has enough evidence wins (own record, pooled class, preset default) → receipt written to status (`rung`, `reason_code`, inputs) → the value is in force from the next entry. No rung: compile refuses. His rows: never derived.

## 2. Invariants

Each is a call two builders could make differently. Everything else is under Deferred.

| AD | Binds | Prevents | Rule |
|---|---|---|---|
| AD-1 the unit stands alone | profile, compiler, halt runner | a unit that needs a guard version to brake itself | everything that judges the unit's own trades (bench, level, CUSUM, cohorts, its numbers) is a block compiled into the unit; the guard holds only rules that read more than one unit |
| AD-2 facts down, events up, the guard never raises | kernel, guard, unit | two arbiters that disagree | a higher scope publishes facts and caps; a unit reaches up only by journalled events and its status; `before_order` answers pass, shrink or refuse, never a larger size |
| AD-3 exits never gated | guard, node, QMB | a blocked exit | exit intents skip `before_order`, SQS and news; a venue refusal raises urgency, never a retry gate |
| AD-4 one reading per running loss per scope | registry rows | April's stacked handbrake | the unit's running loss is read by one live row (the own-p1 bench); the book's by one (the pair taper into the day stop); every other reader is a shadow row |
| AD-5 every number has a derivation and a receipt, or refuses to compile | profile, compiler, checker | a blank or a placeholder on the money path | `numbers[*].derivation` names a block and a ladder; `origin: placeholder` fails layer E for a live profile; user rows need a value |
| AD-6 learned numbers move at anchors; facts move live | derivations, kernel | motion between anchors nobody can explain | `authority ∈ {off, at_anchor}`; a sizer reads facts as inputs, so a changed cost cell or spread acts at once with no learned number moving |
| AD-7 shadow is the same code with the action replaced by a journal write | halt runner, guard | a shadow brake that behaves differently when turned on | `mode: shadow` runs the block, writes a `would_have` row and applies nothing; `live` applies; nothing else differs |
| AD-8 status is the runtime's and stamped | profile status, R22 snapshot | a brake state from an old version sizing a trade | only the runtime writes status; every status carries `status_generation` = spec fingerprint; a mismatch reads as cold |
| AD-9 the kill level is a fact; rules raise stand-downs | guard, node | a brake lowering or setting the kill level | brakes and the day stop write stand-down rows (`Kind.RISK_STOP`, N `stand_down.py:94`) with a cause and a clear rule; only his hand moves `KsaLevel` |
| AD-10 the money ledger reads broker deals | kernel | fire rates that read low or high on the record holes | on the node unit trade facts come from R20's deal reconcile, not from trade rows; in QMB from fills; both become one `TradeFact` shape |
| AD-11 two records | identity table, judge | the rip-out costing a unit its record | the logic record in R continues across profile versions; the money record starts per profile version |
| AD-12 closed reason codes | R15 census | a brake text with no code | every halt, guard answer and skip carries a code in `REASON_CODES` (R `journal_kinds/unit.py:43-75`); new codes are added, never redefined |
| AD-13 one rank, two stages | unit arbiter, guard arbiter | a product of multipliers | permission: any refusal wins; exposure: flatten > reduce > hold; size: smallest cap; state: the highest; raise only with every brake clear. The unit applies its rows, the guard its rows; the composition equals one table because both are cut-only (`out-c3.txt` check 1) |
| AD-14 R is gross at the disaster stop; `net_r` beside it | trade row, sizer, judge | two R's in one sentence | `trade_r` = planned loss at the stop; `net_r` = `trade_r` minus costs in R; brakes, the money ledger and the admission gate read `net_r`; the judge reads `trade_r` |
| AD-15 the harness shares the kernel | harness | a harness that disagrees with the guard | the light harness runs the kernel and the unit's halt runner over a tape; a conformance test on one tape pins them |
| AD-16 agents read and propose, direction on every operation | tool rows, kernel | an agent in the order path | an agent cut is a fact (`agent_cut_factor ≤ 1`, TTL) the sizer reads; a loosening is a card; no tool sends an order, lowers a kill level or writes status |

**Deferred (not decided here, named):** the cluster level and tags (Q8); the applier with modes (fork F-A a); packs that stack and combiners beyond `smallest_cap`; the trust ladder and outside code (loader signature); exit step 3; multi-position units (`position_limit` stays 1); REDUCING at own p10, loss points, "about three", chorus, burn tiers, class isolation (all shadow rows); the Kelly ceiling; the ratchet; the Lab tenancy; the agent jobs; the numbers: k for the day stop, k for the gate, h and the paper window, the floor-touch tolerance, survival days.

## 3. The contracts

Typed sketches, each bound to the file it lands in. Field names are the ledger's ids where one exists.

### 3.1 The risk profile document, `qmx.risk-profile/1`

Lands in J `qml/src/qml/unit/model.py` beside `Unit` (new dataclasses), with a Library kind `risk-profile` (schema file beside `unit.schema.json`). The unit document gains one field, `risk_profile: Pin {id, version, fingerprint}`; its `sizer`, `exit_set`, `halts` and risk numbers move into the profile and are embedded at compile (`compiler.py`, format 5). The census test (`qml/tests/test_unit_refuses.py:457`) gets one decision per new field: run.

```
RiskProfile
  schema: "qmx.risk-profile/1"
  profile_id, version, fingerprint, preset: PresetRef        # x1_profile_version_pin, x1_preset_id
  chain: {preset, class, instrument, unit}                   # x1_override_chain_order; the seven reserved keys parse and resolve to their parent
  spec:                                                      # written by him or an agent draft; never by the runtime
    sizer: Binding            # block + params bound to numbers; inputs may name facts  (today J unit.py:785-793 passes four)
    sizer_base: EntryRef      # "horizon-floor-odds@1"; the row in 3.2
    exit_set: [ScopedBinding] # scope position only at go-live; per-bar exits fed position facts (3.6)
    halts: {unit: [HaltRow], position: [HaltRow]}   # account scope refused: "lives in the portfolio config"
    levels: {fractions: [0.25,0.50,0.75,1.00], start_rule: EntryRef, climb: EntryRef, step_down: EntryRef}  # size_level_fraction_table
    numbers: {name: NumberSpec + derivation: Derivation}     # every number
    needs: [FactName]         # computed by the checker from halts, sizer, derivations; x1_needs_list
    fail_mode: {FactName: compute_here | treat_as_absent | no_new_entries}   # x1_fail_mode, the Read fallbacks already in model.py:391
    never_self_tune: [name]   # inherited from the portfolio config; a profile may add, never remove
  status:                                                    # written only by the runtime; R22's snapshot under data/deployments/<id>/
    status_generation: fingerprint of spec
    numbers_now: {name: {value, receipt: Receipt}}
    level_now, cohort: {n, r, clean}, cusum: {s, warnings: [trade_no]}, bench: {until, days: [], lock_top, lock_until}
    halt_states: {row_id: {state, since, would_have_count}}
    last_risk_state: row id
  suggestions: reserved, refused with a message at go-live

Derivation                                                   # x1_derivation_rule
  rule: EntryRef               # a `derivation` component (new component_type in catalogue/entry.py:106-127)
  inputs: {port: FactName | NumberName}
  anchor: daily_risk | weekly_allocation
  fallback: [own_record | pooled:<class> | preset]           # derivation_fallback_order; the unit's own rung order; refuse when exhausted
  authority: off | at_anchor                                 # x1_number_authority_mode; the `authority` label the compiler now ignores (J compiler.py:869-877) is read
  changed_by: measured | self | user                         # x1_changed_by_class; user rows are the never-self-tune list
  cautious_direction: down | up                              # x1_cautious_direction; missing input moves this way or holds

Receipt                                                      # x1_derivation_receipt
  number, value, rung: own_record | borrowed:<group> | preset | user, reason_code: x1_value_reason_code,
  inputs_used: {}, anchor_ts, derivation_pin, status_generation
```

The never-self-tune list at go-live: `portfolio_floor`, `bms_buffer_before_floor`, `kill_line_floor`, `kill_switch_level`, `floor_touch_tolerance`, `survival_horizon_rounds`. A blank user row blocks live (`x1_settable_by_levels`).

### 3.2 The registry row (brake, accelerator, sizer base, scope)

One row per brake, accelerator, sizer base or scope key, in the profile (unit rows) or the portfolio config (portfolio rows). A row is also a ledger row and a dictionary entry (`component_type` `halt`, `sizer`, `scope`).

```
RegistryRow                                                  # x1_brake_registry_row
  row_id, kind: brake | accelerator | sizer_base | scope
  block: EntryRef                                            # halt or sizer block; none for a scope
  scope: unit | position | portfolio | account | <scope key>  # isolation_scope values: all, account:, instrument:, class:, region:, currency:, underlying:, session:
  brake_class: tail | timing                                 # brake only; tail enforces from day one
  mode: shadow | live                                        # x1_brake_shadow_mode
  reads: [FactName]                                          # becomes part of needs
  anchor: day_boundary | weekly_allocation | rolling_trades(w)
  loss_counting_rule, brake_equity_basis: committed | marked | realised, fail_mode
  direction: cut | raise
  action: no_new_entries | flatten | cap(fraction) | step_level(-1) | stand_down(scope, expiry)
  restore: retry_then_lockout {rest, retry_max_in_window: 2/20d, lockout: -1 level/20d, third: paper/20d}   # bench_retry_max_in_window, bench_min_rest
  thresholds: {name: NumberName}                             # each a number with a Derivation (3.1)
  reason_code: str                                           # in REASON_CODES
  expected_fire_band: [lo, hi] per 100 days                  # from the harness; shown on the card
```

Go-live rows, unit scope (live): `own_p1_bench` (tail, `own-p1-money-bench@1`, reads `unit.running_loss_r(w)`, action `no_new_entries` + restore). Unit scope (shadow): `reduce_at_p10`, `loss_points`, `about_three_run`. Portfolio scope (live): `portfolio_day_stop` (tail, reads `book_day_pnl`, `book_sized_day_sigma`; action `stand_down(all, expiry: next anchor)`), `pair_taper` (its brake half, `cap(f(z_day))`), `cushion_clip`, `bet_key_cap`, `margin_headroom`, `order_veto`, `lot_shed`, `sqs_gate`, `news_window`. Portfolio scope (shadow): `pair_press` (house money, raise), `class_isolation:<class>`, `chorus`, `burn_tiers`, `kelly_ceiling`.

### 3.3 The sizer socket

J `qml/src/qml/blocks/api.py:151-157` and `protocol/unit.py:785-793`. Today four inputs, a hard-coded receipt (`unit.py:827-830`), no residue on `Size` (`api.py:105-109`), and `/sizer/inputs/<port>` refuses (`compiler.py:930-936`).

```
SizerInstance.update(evidence) -> Size
  evidence (facts, all exact Decimal; the four today stay):
    equity, entry_price, stop_price, record                  # as built
    cushion_usable                                           # committed_cushion_usd = marked equity - floor - buffer - reserve, basis:unmarked until marked equity lands
    result_spread_r                                          # from own TradeFacts with the cut inside the distribution; card's value until calibration_min_trades
    horizon_trades                                           # trade_rate (floored at the card's) x survival days
    breadth_factor                                           # B over admitted, level-weighted units; from the portfolio anchor
    level                                                    # size_level_now (status)
    cost_cell_r                                              # hourly_cost_profile value, or the pooled stressed class default labelled cost:uncalibrated
    stressed_slippage_r, value_per_point, conversion_rate(ts), min_lot, lot_step, max_lot
    accelerator_factor (default 1.0), agent_cut_factor (default 1.0), taper_factor_hint (default 1.0)   # facts from the guard
    + its own parameters bound to numbers
  answer:
    Size(lots | None, skip_reason, receipt: SizeReceipt)     # SizeReceipt added to api.py: {inputs_used, rounding_residue_r, base_risk_usd, level, caps: [{name, fraction}], binding_control, cost_label}
```

The horizon sizer block `horizon-floor-odds@1`: per-trade risk in money = `cushion_usable / (result_spread_r x z x sqrt(horizon_trades) x breadth_factor)` x level x accelerator x agent cut, over a shared lot converter (`qml.numbers.lots`) that rounds down and skips below `min_lot`; `fixed-fraction-at-stop@1` stays as the Simplex fallback and the second adapter (X1-H25).

### 3.4 The guard's `before_order` and the fact set

Replaces the static `cross_unit_hook(command) -> str | None` (N `runtime.py:1065-1069`) and the `CrossUnitHook` protocol (J `api.py:196-219`). Lives in `packages/qmf-risk/src/qmf/risk/guard/` with the kernel in `qmf/risk/facts/`.

```
Guard.before_order(intent: UnitIntent, open_positions: Sequence[OwnPosition], facts: Facts) -> Pass | Shrink{to_lots, reason_code, control} | Refuse{reason_code, control}
  order of checks (the rank table, 3.5): kill level at scope → stand-downs (incl. day stop, sqs, news, health) → bet-key cap → cushion clip → margin headroom → order veto (sanity band, order rate, stop side) → pair taper
  exits: never called (the node's loop skips ExitIntent as the old SQS gate did, G12 §2)

Facts (one object per pass, per unit x market; every field carries ts and staleness limit; a stale field takes the profile's fail_mode)
  account:   equity_marked | balance_last_read(ts), margin_used, margin_free, open_risk_at_stops, open_risk_by_bet_key{key: usd}, foreign_open_risk (agent positions, DP33 flag)
  portfolio: floor, buffer, cushion_usable, high_water_mark, day_start_equity, book_day_pnl, book_sized_day_sigma, live_unit_count, admitted_unit_count, breadth_factor, day_stop: {state, expiry}, taper_factor, accelerator_factor, stand_downs{scope: row}, kill_level{scope}
  unit:      trades: [TradeFact], running_loss_r(w), session_fills, loss_streak, day_start_equity_unit, status (level, cohort, cusum, bench, halt_states)
  market:    sqs: {score, readiness, hard_block}, news_window: {state, release, until}, cost_cell: {r, label}, spread_now, value_per_point, conversion(ts), min_lot, lot_step, max_lot, feasible_at_level
  verification: zone, trades_toward_proof, holdout_band
TradeFact: trade_id, market, side, opened_at, closed_at, trade_r (gross), net_r, costs_r, mechanism (3.6), mae_r, mfe_r, size_lots, world, source: deal | fill | trade_row
```

The kernel's adapters: QMB (`qmb/host/unit_handler.py`, fills and the handler's `Account`) and the node (`qmn/app/runtime.py` with a timed balance re-read in `ctrader_account.py`, R20's deals, protection rows for open risk at stops). Until marked equity exists the receipt says `basis:unmarked` (DP12).

### 3.5 The rank table

One table, declared on the portfolio config; the unit applies rows 5 to 6 inside the unit, the guard rows 1 to 4 and 7 on the intent.

| rank | control | kind | where applied |
|---|---|---|---|
| 1 | his hand: kill switch, resume, promotion | permission | node (`_enact`, N `runtime.py:2419-2433`) |
| 2 | protection: disaster stop, forced flat, broker close | exposure | node and venue; never gated |
| 3 | stand-downs: SQS, news, health, day stop, risk stop | permission | guard |
| 4 | portfolio caps: bet key, clip, margin, veto, lot-shed | size | guard |
| 5 | unit halts: bench, lockout | permission and state | unit |
| 6 | level, taper | size | unit (level), guard (taper) |
| 7 | accelerators: pair press (shadow at go-live) | raise | the kernel's `accelerator_factor`, > 1 only when ranks 3 to 6 are all clear |

Rule: permission, any refusal wins; exposure, flatten > reduce > hold; size, smallest cap; state, the highest of unit and guard; a raise needs every brake clear. The receipt names the binding control. Check 1 in `out-c3.txt`: 20,000 random control states, two stages equal one table, no raise while braking. Finding from that test: the guard folds `max(state)` even when the unit already refused, or a benched unit under a day stop shows BENCHED instead of HALTED.

### 3.6 The exit socket (what the repair is waiting on)

Step 2, lands in J `api.py:160-166`, `compiler.py:350-364, 472-506`, `protocol/unit.py:751-836`, both hosts' apply paths.

```
ExitInstance.update(evidence) -> Decimal | Signal | ExitAction | None
  stop:    evidence = {bars (series), position: OwnPosition+}  → price level; read every bar; tighten only (the loss side; past entry is step 3)
  target:  evidence = {entry_price, stop_price}                → price level, rests at the venue as protection (hand-off 6: the node way stands)
  per-bar: evidence = {bars, position: OwnPosition+, side}     → Signal(close) | ExitAction
ExitAction = close_full{reason_code} | close_partial{fraction, reason_code} (compiles, refused at send until step 3) | amend_protection{stop, reason_code} (tighten only)
OwnPosition+ (unit.py:128-138 widened): + stop, targets, bars_held, mfe_r, mae_r, entry_r_usd
```

- **Rank among exits** (the sub-choice): inside the compiled unit, fixed, not configurable: on one bar `close_full` > `close_partial` > `amend_protection`; among equals the earlier binding in `exit_set`; the winner's reason is the trade row's `exit_mechanism`. The guard never sees exits.
- **The disaster stop** is every live order's `protection.stop`; `stop_not_built` (J `compiler.py:500-506`) stays a refusal: no unit without a price stop at go-live (hand-off 7: no).
- **The cut**: `fast-invalidation-cut@1`, a per-bar exit reading `mae_r` against `fi_cut_mae_percentile` from the winners' MAE; a counted two-arm trial per unit (F1 open).
- **Trade row v2** (R `journal.py:412`, `journal_kinds/unit.py`): + `exit_mechanism` ∈ {disaster_stop, fast_invalidation, time, target, forced_flat, kill_close, protection_close, broker_close, hand_close, bench_flatten}, `trade_r`, `net_r`, `costs_r`, `mae_r`, `mfe_r`, `size_lots`, `session`, `stage`.
- **Step 3 waits** for the signed stop: the convention is pinned in one place, `qmf-venue/encode.py:115-120` (`_LEVEL_RULES`): `new_distance` signed from entry, positive on the loss side; R21's `Blocked` (N `runtime.py:1278-1287`) stays until that lands. `timer()` long-only (hand-off 12) is fixed inside step 2.

### 3.7 The RiskState row

A new journal kind `risk_state` written by the guard every pass per scope (unit, portfolio, account), read by the UI, the morning card, the agents' read door and the harness.

```
risk_state {ts, scope, status_generation, word: GREEN|REDUCING|BENCHED|STOOD_DOWN|HALTED|UNKNOWN,
  equity: {marked|balance, basis, committed_cushion, floor, buffer, hwm}, open_risk_at_stops, open_risk_by_bet_key, margin_used,
  day: {start_equity, book_pnl, sized_sigma, z}, level_now, cohort, cusum_s, bench, drift_zone, trades_toward_proof,
  brakes: [{row_id, mode, state, distance_to_trip, fires, would_have}], binding_control_last, kill_level{scope}, stand_downs[],
  numbers_pending: [{name, value_now, value_at_next_anchor, rung}], staleness: {fact: age}}
```

`UNKNOWN` is written when a needed fact is stale past its limit; a stale green is impossible.

### 3.8 The agents' read and propose surfaces

Tool rows in `qmx_control/catalog.py` and `qmx_tools/functions.py`, also served as read-only MCP tools (transport is QMA's, flagged). Every operation carries `direction`.

| row | direction | does |
|---|---|---|
| `risk_state(scope)` | read | the last `risk_state` row |
| `risk_profile_explain(unit, number)` | read | the chain, the receipt, the ledger row |
| `risk_ledger_query(id)` | read | one ledger row |
| `risk_resize_replay(unit, profile)` | run (harness) | the unit's TradeFacts under another profile, money measures |
| `risk_scenarios_run(profile, set)` | run (harness) | the mandatory X4 block |
| `risk_profile_new(preset, overrides)`, `risk_profile_check(doc)` | draft | a profile draft, checked |
| `risk_propose(scope, lever, direction, expiry, evidence)` | cut: applies as a fact `agent_cut_factor ≤ 1` at scope with TTL, journalled; raise or loosen: a card for his click | never writes status, never an order |

### 3.9 Compiler refusals to lift, and the format bump

Format 4 → 5 (`compiler.py:100`); the compiled fingerprint and `pack.json` move. Lift, by name: `halts_not_built` for unit and position scope (`compiler.py:902-903`; account scope keeps a refusal with the message "lives in the portfolio config"); `binding_not_read` for halts reading account or trades ports (R05) replaced by the needs-list check; `inputs_not_built` on `/sizer/inputs/<port>` for `facts` ports (`:930-936`); `exit_not_built` for a per-bar exit with inputs and a stop reading the position (`:358-363`); the logic-stamp requirement for a calibrated number bound only to the sizer (`:617-643`) when the number has a Derivation; `cadence_not_built` (`:1009-1014`) with `cadence.at` read as the anchor; `open_positions_not_built` stays refused. The checker (`check/layers.py`) gains: needs ⊆ provides or a fail mode per need; a live profile with `origin: placeholder` on the money path fails; a blank user row fails.

## 4. The fork, argued

**F-B (b), built here: the guard computes facts, the unit runs its own halts.** What it buys: the unit carries its brakes between hosts with no guard version (the same `UnitSliceHandler` code runs them in QMB and on the node, which is a stronger backtest-equals-live than two adapters); "units stand alone" holds for the rule he cares about most (the unit bench); the shipped halt family (five blocks, `HaltInstance`, the contract test) is used as built; the identity table already labels a halt list change (G8 §3.6). What it costs: two arbiters, and a fact round trip for anything cross-unit.

- **Brake rank this way.** One table (3.5), two stages. The unit stage is cut-only and the guard stage is cut-only, so composition is `min` over caps and `max` over states whatever the order; proved by property test over 20,000 random states. The one subtlety the test found: the guard must fold its state even on an intent the unit refused. Rank numbers only decide which reason the receipt names and which exposure action wins; they never change the size.
- **Backtest equals live this way.** Unit brakes: by construction, one code path in both hosts. Portfolio brakes: the guard with two adapters, as in (a). Facts: the kernel with two adapters, the conformance test on one tape (AD-15). The difference from (a) is where the risk of drift sits: in (a) every brake depends on the two guard adapters agreeing; in (b) only the portfolio brakes and the facts do.
- **Shadow rows this way.** `mode` on the registry row; the halt runner inside the unit and the guard apply the same rule (AD-7): run the block, write `would_have`, apply nothing. A unit-scope shadow brake needs nothing from the guard; a portfolio-scope one needs nothing from the unit. Precision is read from the rows before a flip to `live`.
- **The constraint the funnel named** (halts refused as `binding_not_read` because they read account and trades ports, R05): answered by the needs list. A halt's `reads` becomes `needs`; the kernel's `provides` covers them or the profile names a fall-back (`compute_here` for anything computable from the unit's own trades, which covers the bench, the CUSUM and the cohorts).
- **What would make (a) win.** A brake that must read two units' facts on the same tick and act on both (chorus, class isolation) is native in (a) and a fact round trip in (b); at go-live those are shadow rows, so (b) pays nothing yet. If after go-live most live brakes turn out to be cross-unit, or if the node's fact round trip is measured slower than a bar, (a) is the better home and the migration is: move the unit rows into the portfolio config; the row shape is the same.

**F-A (b), refresh at anchors, chosen because it fits (b).** With the unit standing alone, its numbers must move without a guard organ. The built motion engine already moves a number every N closed trades (J `compiler.py:869-878`); an anchor is one more cadence (`cadence.at`, parsed and ignored today, now read). The applier with modes needs a herding cap across units, a cross-unit concern, which under (b) would pull number motion back into the guard. The case for (a), a number that must move between anchors (X4-39, the broker changes its costs), is answered by AD-6: costs are facts the sizer reads live, not learned numbers; the spec-change stand-down (R23, X4-51) covers the rest until the next anchor. Herding is a harness column, not a guard, because all units recompute N and B at the weekly anchor together by design. What would make (a) win: a learned number whose lag of one anchor is shown to cost money in the harness on X4-60 (slow decay), or his wish to see a number move `at_flat` mid-day.

## 5. The extension proof

| change | what changes | rework? |
|---|---|---|
| a new brake | a halt block entry (`entry.json` + `block.py`) with its `reads`; one registry row in the preset or profile, `mode: shadow`; `needs` extends itself; the halt runner runs it; a new version of the profile (identity: `profile_version_change`) | none, unless it reads a fact the kernel does not provide and cannot `compute_here`: then one kernel adapter PR (admitted) |
| a new sizer base | a sizer block with `facts` ports and its numbers' derivations; a `sizer_base` row; a migration-map row from the old block; contract tests enrol it; `smallest_cap` combines if two are bound | none |
| a new instrument class | a class key in the chain with class defaults in the preset's class layer; an instrument risk record (lot step, value per point, stressed cost default, session clock); `class:<x>` is already a scope key; lumpy lots go through the lot-shed and level floor | none; a venue adapter if the venue is new (not the template's) |
| a new style preset | a Library `template` item `risk-profile` preset with derivations, class-keyed layer, revisions; `unit_new(template, overrides)` already starts from one | none |
| he changes how one number derives | edits `numbers[x].derivation.rule` (or its ladder order) in the profile; `profile_version_change` → new version, counted try, his click, adopted at the next flat; the logic record continues | none |
| an agent proposes a tighter limit | `risk_propose(scope, lever: cap, direction: cut, expiry, evidence)` → the guard validates against the ledger (level, measure, bounds, never-self-tune) → `agent_cut_factor` fact at scope with TTL → the sizer multiplies; journalled; the card shows it | none |
| the Lab simulates a variant | `risk_resize_replay(unit, profile)` over the unit's own TradeFacts through the harness (kernel + halt runner on a tape); the Lab is one more caller of the run rows; never the node | none |
| a version rollout that keeps the record | bump the profile pin; identity label `profile_version_change`; the snapshot rule exempts logic block state from the cold start; money record starts anew; the sizing-only replay fills it from history | none; the identity table row is his to edit |
| class isolation from shadow to binding | the portfolio config row `class_isolation:<class>` flips `mode: shadow → live`; a config version; his click; the scope key already blocks in `stand_downs.blocking` (N `runtime.py:2570-2579`) once `class:` keys are added to the table | none |
| house money's press switching on | the pair row's accelerator half `mode: shadow → live` by the once-rule when the proof card passes; the kernel's `accelerator_factor` exceeds 1.0 only with every brake clear; the sizer already multiplies | none |

One finding against the design, admitted: a cross-unit brake that needs a fact the kernel does not compute costs a kernel PR with two adapters. The needs list makes that loud at compile instead of silent at run time.

## 6. The performance proof

`out-c3.txt`, the funnel's worked example, model numbers only.

**Factors that touch size, in order.** Unit stage: baseline (cushion over spread x z x sqrt(H) x B, times reserve and the cost denominator) × level (holdout start, cohorts up, CUSUM down, lockout top) × bench (no entry while benched). Guard stage: × pair taper (reads the book's running loss once) × day stop (no entry) × bet-key, clip, margin, veto caps × lot round-down and skip. The unit's running loss is read once, by the bench, inside the unit. The book's once, by the taper and the stop, inside the guard.

**Traces (check 2).** Healthy: starts at 0.50, climbs to 1.00 by day 4, size 0.93 to 1.00 of base, binding control `level` then `lot_round`. Weak: starts at 0.25, climbs to 1.00 by day 7, 0.91 to 0.95 of base. Bleeding with an overstated card: benched on day 5 at its own p1, CUSUM warning on day 10 (level 0.75), second bench on day 12 locks it at 0.50, second warning on day 14 sends it to paper on day 15 with $124 of the $200 cushion left.

**Choke budget (check 3).** CORE at N = 1 and N = 10, cost 1x: healthy 0.92 and 0.89 of base, weak 0.86 and 0.84, zero floor touches, zero dark; above the 0.75 bar. The bleeding unit runs at 0.69 to 0.73 because the brakes are working.

**A finding for the numbers lens (check 2d).** With h = 17 and "two warnings inside 500 trades", a healthy 10-a-day unit goes to paper in 42 % of 120-day paths (median day 67); a weak one in 41 %. That is the price of DP27's second-warning rule at these values, and a re-promotion needs his click (DP27), so 4 in 10 healthy units would wait on him inside four months. The architecture keeps the rule as a derivation on the drift row (`drift_paper_rule`: window, h, count) so the numbers lens can move it without code; **[judgment]** the second warning should step one more level down and the third send to paper, or the window should be measured in alarm spacings. Not decided here.

## 7. Scenario walks (summary; the full walks are in the appendix)

- **X4-01, five units short one USD move.** Bet keys cap the stack at `before_order` before the move; each stop fires as protection (never gated); each unit's bench reads its own net loss once, one -1R is above p1, no bench; the kernel's `book_day_pnl` falls; the taper cuts the next entries; the day stop fires only if the book passes k sigma; next anchor recomputes cushion and B. Holds.
- **X4-14, everything bad everywhere.** The day stop reads the sized sigma and raises `stand_down(all)` with expiry at the next anchor; `guard` refuses every entry (`stand_downs.blocking("all")`); exits run; the escalation card lands; the kill level stays his (Q5). Holds, with the fire rate the numbers lens's.
- **X4-66, overfit card.** Start level from the holdout, cohorts, the CUSUM: warning in a median 43 days on the overstated case, paper by rule; the upside alarm is a shadow row. Holds; the paper-rate finding above is its cost on healthy units.
- **Mid-outage restart.** Status (level, cohort, CUSUM, bench days, lock) lives in R22's snapshot and is stamped with `status_generation`; the day stop's stand-down is a journalled `risk_stop` row re-held from the last `risk_state`; the kernel rebuilds TradeFacts from R20's deals, so a close while down is counted; a bench's rest keeps running in calendar time (DP20); facts older than their limit read UNKNOWN and the profile's fail mode holds entries until fresh. Holds; the known holes (G12 item 10) stay holes.

## 8. The hand-offs

| hand-off | answer | who |
|---|---|---|
| stop past entry | out of scope for step 2; step 3 after the convention is pinned in `encode.py` `_LEVEL_RULES` (signed from entry, positive = loss side); R21's `Blocked` stays until then | decided |
| stop widening | never; `amend_protection` is tighten-only in the unit and the node | decided |
| target at the broker | rests at the venue as protection; the node way stands; the per-bar target is the backstop | decided |
| a unit with no stop | refused at go-live (`stop_not_built` stays); a stop-less sizer base is a later plug with a declared worst case | decided |
| a moved number and open trades | applies at the next entry; `applies_to_open_positions` stays refused; an open trade's exits read the values stamped at entry | decided |
| two exits on one bar | close_full > close_partial > amend; earlier binding wins ties; the winner is the mechanism | decided |
| partial close and R | R stays the planned loss at the disaster stop; a partial's realised R is fraction x move / R; a rest below min lot is refused by the checker; partials ship with step 3 | decided; step 3 |
| R and costs | gross `trade_r`, `net_r` beside; brakes and the gate read net; our call, his B9 reservation stands | decided |
| kill level meanings | YELLOW no new entries at scope; ORANGE no new entries, amends tighten only; RED close this node's positions at scope, no entries; BLACK close all and pause; resume only by his hand; replaces `PLACEHOLDER_KILL_EFFECTS` (N `effect_matrix.py:137-146`) | decided; values his |
| where SQS sits | inside the guard package as a gate fact (`sqs_gate` row); the baseline producer moves to `qmf/risk/guard/sqs/`; its eight rows get derivations from the spread histogram; exits never checked | decided; numbers wait |
| `too_thin` | `verification_trades_needed` derived from the holdout band's plan, not 100 | numbers lens |
| the version pull | R11's rule stands: a sizer-only swap pays the pull; an exit change is a counted try | decided |
| grid and martingale | refused by the preflight firewall | decided |
| the Book's fate | Q8, his, after go-live | him |
| a check with no orders | `inconclusive`, never a pass | decided |

## 9. The build plan

Slices in order, each a few PRs on landed repair tips (R01 to R06 at J; R20 and R21 at N once reviewed). About **28 PRs** **[judgment]**.

| # | slice | files | PRs | must land first | collides with |
|---|---|---|---|---|---|
| 1 | exit socket step 2, trade row v2, `net_r` | J `qml/blocks/api.py`, `compile/compiler.py`, `protocol/unit.py`; `qmb/host/unit_handler.py`; N `qmn/app/runtime.py` (apply, tighten-only); R `qmf-data/journal_kinds/unit.py`, `qmb/results/journal.py` | 3 | R04 to R06 (J), R10 (money measures), R15 (reason census) | R21 at `runtime.py:1278-1320` (stop amends); agree the signed convention first |
| 2 | fact kernel and RiskState | new `packages/qmf-risk/src/qmf/risk/facts/`; `qmn/venue/ctrader_account.py` (timed balance re-read); `qmn/app/runtime.py` (adapter); `qmb/host/unit_handler.py` (adapter); journal kind `risk_state` | 4 | R20 (deals), R22 (balance at start, snapshot) | R22 and R17 at `runtime.py`, `host.py`, `first_start.py` |
| 3 | profile document, presets, derivations, format 5 | J `qml/unit/model.py`, `check/layers.py`, `compile/compiler.py`, `unit/templates/*.json`, `blocks/stdlib/derivations/*`, `catalogue/entry.py`; `qmx-library/kinds/risk-profile.schema.json`; `identity/table.py` (+ `profile_version_change`) | 4 | slice 2's fact names | R04's census test (one decision per field) |
| 4 | sizer `horizon-floor-odds@1`, lot converter, `SizeReceipt`, migration map | `blocks/stdlib/horizon-floor-odds/1/`, `qml/numbers/lots.py`, `api.py`, `protocol/unit.py:785-836`, `tests/test_socket_contracts.py` (short side, facts) | 2 | slices 2, 3 | none |
| 5 | halt runner, the bench, the level | `protocol/unit.py` (runner, shadow, would_have), `blocks/stdlib/own-p1-money-bench/1/`, `blocks/stdlib/size-level/1/` (cohorts, CUSUM), status in R22's snapshot | 3 | slices 2, 3 | R22 snapshot shape |
| 6 | guard: `before_order`, portfolio config, day stop + taper, clip, bet keys, margin, veto, lot-shed, kill effects | `qmf/risk/guard/`; `qmx-library/kinds/portfolio-config.schema.json`; N `runtime.py:1065-1069` (call), `:2531-2581` (reasons), `effect_matrix.py`, `stand_down.py` (+ `class:`, `region:`, `currency:` keys), `operations.py:241-258`; `qmb/host/unit_handler.py` (call) | 4 | slices 2, 4; R21 reviewed | R21 `_close_scope`; R23 stand-downs |
| 7 | SQS slice and the news window | move `qmn/host/sqs_baseline_producer.py` → `qmf/risk/guard/sqs/`; `labelers.py` rule; `registry_catalog.py` rows → derivations; `qmn/data/news_calendar.py`, `qmn/protection/windows.py` as the window's reader | 3 | the claims file honoured before C-20 and deletion-4 | C-20 |
| 8 | light harness, conformance test, choke budget, X4 mandatory block as data | `tools/risk/harness/` (kernel + halt runner on a tape), `funnel/working/review/core_sim.py` as the first job, scenario yaml | 2 | slices 5, 6 | none |
| 9 | machine check, bound click, two records, world-switch reset, preflight firewall | `qmx-judge/promote.py`, `judge.py` (`verification_trades_needed`), `identity/table.py`, `qmx_control/service.py` defaults | 2 | R11 (pull), R17 (`_admit`) | R17 |
| 10 | shadow rows for timing brakes, morning card, wake contract, agent tool rows | registry rows; `catalog.py`, `functions.py` (3.8); card template; R16's push list (three pushes need his word, Q7) | 2 | slices 5, 6 | R16 |

Claims before the deletion sweep (already in `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md`): `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `qmn/protection/dispatch.py`, `sqs_baseline_producer.py`, `labelers.py`, `qmn/replay/port.py`, `qmf-risk/control_window`, `registry_catalog.py`. This design adds none.

## 10. What I would cut, and what I added

**Cut if more must go:** the chain to two keys (preset, unit) with class and instrument folded into the instrument record; the news window to the calendar tier only; the level ladder to two steps (0.50, 1.00); the shadow rows to the three with evidence (REDUCING, class isolation, the Kelly ceiling); the agent `risk_propose` row (keep reads only) until an agent job exists.

**Added beyond the funnel, and why:** the fact kernel as a named package apart from the guard's rules, so (b) can hand facts to units and the harness without a guard; `accelerator_factor` and `agent_cut_factor` as facts the sizer reads, so a raise and an agent cut go through one input instead of a second arbiter; the two-stage arbitration proof; `compute_here` as the needs fallback for unit-scope brakes; exits skipping `before_order` by contract; the `drift_paper_rule` derivation after check 2d.

---

## Appendix A. The scenario walks in full

### X4-01. Five units short one USD move

1. Before the move: each unit's sizer reads `breadth_factor` from the weekly anchor and `cost_cell_r`; each intent carries its receipt. At `before_order` the kernel's `open_risk_by_bet_key["usd:short"]` already holds four units' risk; the fifth gets `Shrink` to the remaining cap (`bet_key_cap`, reason `cross_unit_hook` until a `bet_key_cap` code is added to `REASON_CODES`). The receipt names `bet_key_cap`.
2. The move: five disaster stops fire at the venue (rank 2, never gated). R20 reconciles the closing deals; the kernel writes five TradeFacts (`mechanism: disaster_stop`, `net_r` about -1).
3. Unit stage next bar: each halt runner reads `running_loss_r(w)` = -1R, above p1 (-5.9R on the card); no bench; the CUSUM adds one step; no warning. State ACTIVE.
4. Guard stage: `book_day_pnl` fell by five sized losses; z against `book_sized_day_sigma` is near -1.3, the taper starts cutting new entries (reason `pair_taper`); if z passes -k the day stop writes `stand_down(all, expiry: next daily anchor)` and `guard()` refuses entries with `risk_stop`.
5. Next anchor: cushion lower, B recomputed on admitted, level-weighted units; r falls. No unit benched for a streak it did not have. The event-window row (shadow) journals that it would have counted five as one.
6. The upside twin (X4-05): `accelerator_factor` stays 1.0 (shadow at go-live; later, the raise gate needs every brake clear and the pair's own window).

### X4-14. Everything bad everywhere

1. Two hours in, several units' own benches fire on their own p1 (unit stage, each once). The kernel folds `book_day_pnl`.
2. The guard's `portfolio_day_stop` row reads `book_day_pnl <= -k x book_sized_day_sigma` and writes the stand-down at `all` (`Kind.RISK_STOP`, clears itself at the next daily anchor). `guard()` returns `risk_stop` for every entry (N `runtime.py:2570-2579` already blocks on `all`). Exits, stops and the kill switch keep working.
3. RiskState: word STOOD_DOWN at `all`, each unit's own word beneath it (BENCHED or ACTIVE), `binding_control_last = portfolio_day_stop`.
4. The one-tap escalation card lands; whether the stop may raise YELLOW itself is Q5 (default: no). If his phone push for "day stop fired" is approved (Q7) it goes through R16's register.
5. Next anchor: the stand-down clears; the cushion is read fresh; r falls with it; no unit is in paper for a bad day. Fire rate on history is the harness column beside k.

### X4-66. The overfit card

1. QMB's deflated holdout gives a band whose low end is barely positive: start level 0.50 (or 0.25 at zero). The plan prices `verification_trades_needed` from the band; the click approves one hash at one level on these markets until a date.
2. Live: cohorts climb only on clean cohorts; the CUSUM on `net_r` against the card's mean minus the allowance accumulates; `out-c3.txt` 2d: the overstated case alarms in a median 43 days, the bleeding one in 23; a second warning inside 500 trades moves the unit to paper with cause `drift_warning`; re-promotion is his click.
3. The lookahead twin: `upside_alarm` is a shadow row at go-live; the daily-Sharpe audit in the judge (G7 §1.4) still holds the verdict. Accelerators are shadow, so nothing pays a bug.
4. Cost on healthy units: 42 % to paper inside 120 days at these values (section 6); a numbers-lens row.

### Mid-outage restart

1. The node goes down with two units open and one benched. R22's snapshot holds the profile status (level, cohort counters, CUSUM, bench days, lock) under `data/deployments/<id>/`, stamped with `status_generation`.
2. On restart the unit starts at the real balance (R22); the kernel re-reads the broker's deals since the last reconcile (R20); a stop that fired while down becomes a TradeFact with `mechanism: broker_close`, so the bench's window is not blind to it.
3. The guard re-holds any `risk_stop` stand-down whose expiry has not passed from the journal's last `risk_state`; `day_start_equity` is the persisted day baseline (X3-H74), not the balance at restart.
4. The bench's rest counts calendar time while down (DP20). Facts older than their staleness limit read UNKNOWN; the profile's fail mode (`no_new_entries` by default for `cushion_usable`) holds entries until the kernel is fresh.
5. A snapshot from another spec fingerprint starts the profile's status cold and says so in the first decision row; the logic blocks keep their state if only the profile changed.

## Appendix B. Assumptions

- `[ASSUMPTION]` R22's snapshot can hold a second object (the profile status) beside the unit's; its PR is not started.
- `[ASSUMPTION]` `stand_down.py`'s `Row` can carry an expiry for `RISK_STOP` rows that clear themselves at an anchor; today `held_for_ns` is the only clock.
- `[ASSUMPTION]` The node's loop can skip `before_order` for `ExitIntent` the way the old SQS gate did; the new `guard()` is entry-only today, so this holds.
- `[ASSUMPTION]` A `facts` evidence surface can be added to `UnitSliceHandler` without touching the per-market surfaces.
- `[ASSUMPTION]` The halt contract test's three-step session fixture extends to facts without changing its shape.
