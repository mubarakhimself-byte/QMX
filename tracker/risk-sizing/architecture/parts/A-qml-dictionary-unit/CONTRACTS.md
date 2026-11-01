# Part A contracts: every shape this part owns or consumes

Part A of the Level 1 run, 31 Oct 2026; amended 1 Nov by fixer X1-0A after review R1 (the roll rule moves onto the unit, R1-C-10; reading tiers, CF-6; the journal kinds and writers, R1-B-06; record ids, R1-B-10; starting state, R1-C-01; deployment files by fingerprint, R1-C-06; one new setting, R1-A-02). Each shape is listed field by field with its owner, its version rule and the connection rows of `architecture/01-connections.md` that carry it. Version codes are that file's (V-S, V-K, V-P, V-CT). Decisions are this part's AD-101 to AD-120 (`ARCHITECTURE-SPINE.md`) and Level 0's L0 AD-n. CHECKED means read at the cited line or run; INFERRED means judgement.

**Common rules.** Every document carries a `schema` marker such as `"qmx.unit/1"`. Fields may be added; meanings never change; a breaking change is a new version plus an upgrader that QML ships (AD-119). Numbers are decimal strings (`"0.30"`), parsed to exact values; instants are UTC nanoseconds as integers or ISO-8601 UTC text; ids are strings; pins are `entry_id@version` plus a fingerprint `fp1:sha256:...`. Optional fields are marked (opt).

## 1. The unit document `qmx.unit/1` (owner: P2, this part)

Carried by: the Library `unit` kind's `fields` (C2), the `unit_*` rows (C1, C5), templates (C3), QMB run requests by reference (C7, C8), deployments (X1). Version: V-K for the kind, V-S for the document.

| Field | Type | Meaning | Checked at layer |
| --- | --- | --- | --- |
| `schema` | `"qmx.unit/1"` | marker and version | A |
| `unit_id` | string | stable id across versions (the Library item id) | A |
| `family_id` | string | the strategy family, e.g. `trend-pullback` | A, B |
| `title` (opt) | string | display name; a label, never identity (OP-11) | A |
| `claim_card` | object | `idea` (text), `claimed_context` (text, opt), `sources` (list of `{source_ref, locator, quote (opt), dated}`), `written_at` | A; E needs at least one source (UT-21) |
| `lineage` (opt) | object | `parents`: list of `{unit_id, version_ref, edit_labels}`; `rewritten_from` (opt) | B, identity |
| `markets` | list | each `{market_id, instrument_ref (venue, symbol; or venue, root for a future), roll (futures, opt): {rule: calendar, volume or open_interest; days_before_expiry (opt)}, settings (opt): {number name: decimal string}, settings_record (opt): earning-record ref}`; the roll rule is the unit's, because a unit picks its roll, and the records only list the contract months (R1-C-10); read by the shipped Markets tab | A; E needs one; D per market, and a future with no `roll` and no exit before expiry is an error (UT-18) |
| `streams` | list | each `{name, market: "*" or market_id, bar: {kind: time, tick, range, volume; size}, input: closed_bars, quotes, ticks; price: bid_ask, mid, last; derived_from (opt): stream name}` | A, D (QML-19, QML-20) |
| `sessions` (opt) | list | each `{name, calendar_ref, zone (IANA), windows: [{from, to}] in the market's zone}` | A, D (UT-13) |
| `direction` | `long`, `short`, `both` | sides traded | A |
| `position_limit` (opt) | object | `per_instrument` (integer, default 1) | A, C (UT-15) |
| `logic` | object | `long` and or `short`: each `{slots: {slot name: Slot}}`, or `short: {mirror_of: "long"}` for blocks that declare mirroring | A; B refuses an implicit mirror (QML-17) |
| `exit_set` | list of Binding | exit blocks; each binding names its scope (`position`, `unit`, `account`) | A; E needs one; socket (§4.3) |
| `sizer` | Binding | one sizer block | A; E |
| `halts` | object | `position`, `unit`, `account`: lists of Binding (may be empty; a warning) | A; E warns when empty |
| `reads` | list | each `{reading: entry_id@version, market: market_id or "*", fallback: compute_here, treat_as_absent, no_new_entries; stale_after_s}` | A, B, D (L0 AD-2, AD-40) |
| `numbers` | object | `{number name: NumberSpec}` (§2) | A, C |
| `context_needs` (opt) | object | `require`, `warn`, `block`: lists of `{word: entry_id, reading: entry_id@version (opt)}` | B |
| `routes` (opt) | object | `data`: per data kind a route ref; `execution`: route ref; a proxy (a futures tape for a CFD) declared, never silent | B, D |
| `pins` | list | the lock: each `{entry_id, version, fingerprint}` for every block bound anywhere, sorted | A; B checks each pin resolves and matches |
| `baseline` (opt) | string | the baseline card ref the judge froze (Part B) | B |
| `plain_python` (opt) | object | manifest form: `{block: entry_id@version}`; slots then name only data needs and numbers | A, F |

**Slot** = `{role: Role, bindings: [Binding], combiner: Combiner}`. **Binding** = `{name, block: entry_id@version, params: {param: {number: name} or {value: decimal string}}, inputs: {port: stream name, "stream.field", or another binding's name}, scope (exit and halt bindings only)}`. **Role** is one of AD-104's vocabulary. **Combiner** = `{kind: all, any, k_of_n, weighted, sequence, veto; k (k_of_n); weights, open, close (weighted); within_bars (sequence); when_inputs_absent: no_signal, treat_as_false}`; every combiner yields `signal` or `no_signal` with a reason (QML-21).

## 2. Numbers

### 2.1 `NumberSpec` (owner: P1)

| Field | Values | Rule |
| --- | --- | --- |
| `kind` | `fixed`, `calibrated`, `derived` | fixes the allowed motion modes (AD-103) |
| `measure` | §2.2 | conversions only through the instrument record |
| `range` | `{min, max, step}` decimal strings | min ≤ default ≤ max; the step divides the range |
| `default` | decimal string, or a category or flag value | |
| `motion` | `{mode, source, cadence, min_count, shrink_k, step_limit, rule, rule_params}` | `fixed`: mode `fixed`. `derived`: `scaled`, `percentile_of_own_history`, `state_table`. `calibrated`: `shrink_from_own_trades`, `learned`. `cadence` = `{every_closed_trades (opt), at: market_day_close or session_close (opt)}`; `rule` = a motion block pin |
| `authority` | `motion_inside_range` | a new range is always a new version and his click |
| `origin` | `source_stated`, `published_convention`, `strats_standardized`, `inferred`, `builder_chosen`, `unresolved`, `placeholder` | `builder_chosen` and `unresolved` warn |
| `applies_to_open_positions` | boolean, default false | the risk session may change the default |

### 2.2 Measures and the QMF `UnitKind` table (owner: P1)

| Measure | QMF `UnitKind` (`packages/qmf-core/src/qmf/core/exact.py:135-144`) | Converts through |
| --- | --- | --- |
| `price_distance` | `price-delta(instrument)` | the record's tick size and digits |
| `ticks` | `count` | the record's tick size |
| `pips` | `price-delta(instrument)` | only when the source states pips and the record defines a pip |
| `atr_multiple` | `dimensionless-ratio` | the bound ATR block's value at the instant |
| `percent` | `dimensionless-ratio` | stored as a fraction |
| `ratio`, `probability` | `dimensionless-ratio` | none |
| `bars`, `count` | `count` | none |
| `seconds` | `duration` | none |
| `money` | `money(currency)` | the record's value per point and the account currency |
| `r` | `r-multiple` | the trade's initial risk |
| `lots` | `quantity(unit)` | the record's lot step and minimum lot |
| `category`, `flag` | categorical, boolean parameter types | none |

### 2.3 Instrument record fields this part reads (owner: P4, Part C; consumed here)

Layer C and D and the sizer slot read, per market at an instant: `market_id`; `venue`; `symbol`; `class` (fx, metal, index_cfd, commodity_cfd, stock_cfd, future, perp, spot_crypto, stock); `digits`; `tick_size`; `pip` (opt, with its source); `contract_size`; `value_per_point` (money per price unit per lot); `lot_step`; `min_lot`; `max_lot` (opt); `currency`; `calendar_ref` and zone; `day_boundary`; `data_levels` (the vocabulary of §5.2); `expiry`, `last_trade`, `root` and `rolls_to` (futures, opt; the roll rule is on the unit's market entry, §1, R1-C-10); `funding_interval` (perps, opt); `leverage` and `margin` (versioned); `record_version`. The class list above is the one class enum every part spells the same way (Part C's records and Part B's capabilities match it; R1-C-10), and the keys are the exact keys of Part C's `instrument` kind, which its key-parity test pins. A missing field that a check needs is an error naming the field and the record, never a guess. Until Part C's records land, the first slices use fixture records for EURUSD and XAUUSD with the same fields (BUILD-SLICES A3).

## 3. Check results

### 3.1 `qmx.check/1` (owner: P1)

Carried by: C1 to C4 (rows, Library refusals, template step, hook `additionalContext`). Version: V-S.

| Field | Meaning |
| --- | --- |
| `schema` | `"qmx.check/1"` |
| `verdict` | `pass` or `fail` (fail when any error) |
| `counts` | `{errors, warnings}` (first, so a spilled answer's head shows them, AG-15) |
| `errors`, `warnings` | lists of Problem, errors first |
| Problem | `{kind, layer (A to F), where: [JSON pointers], message (≤ 300 characters), hint (≤ 300), nearest (opt): up to N ids}`; identical problems are grouped with all their pointers |
| `layers_run` | e.g. `["A", "B", "C", "D", "E", "F"]`; a layer that could not run names why in a warning |
| `document_fingerprint` | fp1 of the document |
| `compiled_fingerprint` (opt) | set by `compile` and by a passing check that compiled |
| `checker_version` | `qml-check/<format>` plus the rules fingerprint |
| `entries_snapshot`, `records_snapshot` | fingerprints of the inputs used |
| `problem_set` | fingerprint of the sorted problem list |
| `no_progress` | true when the caller passed the previous `problem_set` and it is equal (AG-11) |

### 3.2 `qmx.behaviour/1`, layer G's behaviour report (owner: P1; run by Part B)

| Field | Meaning |
| --- | --- |
| `slice` | `{data_card_ref, market_id, from, to, fingerprint}` (at least the derived warm-up plus `checker_slice_margin_bars`) |
| `safety` | `{verdict: pass or fail, failed_check (opt), layer2_verdict_fingerprint}` from the unchanged `evaluate_layer2` |
| `trades`, `entries_long`, `entries_short` | counts on the slice |
| `may_not_trade_on_slice` | the unit's declaration, echoed |
| `exits_fired` | `{binding name: count}`; `exits_unfired`: names |
| `signal_constant` | true when the trigger's output never changed |
| `one_side_only` | true when every entry took one side of a both-sides unit |
| `shuffled_day_control` | `{decisions_equal_to_real: boolean, trades}`; bars shuffled within each day with times kept |
| `warnings` | list of Problem for each item above that fires; never errors |
| `compiled_fingerprint`, `checker_version` | as §3.1 |

### 3.3 The `test-report` record for G (existing kind, extended additively)

New optional fields on `test-report`: `check` (`"qml-g/1"`), `compiled_fingerprint`, `unit_ref` (`unit_id` and version), `safety` and `behaviour` (§3.2), `run_id` (the core run id). Landed through the core landing (C10) and linked `tests` to the unit version. The node's deploy and QMB's run find it by `compiled_fingerprint` (AD-111).

## 4. Runtime shapes

### 4.1 `CompiledUnit` (in process, owner: P1; consumed by QMB, the node, the MIS app through C12)

`factory` (satisfies `BotFactory` structurally); `footprint` (QML `Footprint`); `parameter_space` (QML `ParameterSpec` list, for QMB's optimiser); `trace_schema`; `lock` (the pins); `compiled_fingerprint`; `compiler_format_version`; `warm_up` (from `derive_horizon`, per stream); `state_bound` (derived from the blocks' bounds); `placeholders` (bindings whose block origin is `placeholder`); `options` (the compiler options that change decisions, such as the port quantum, which enter the compiled fingerprint).

`construct_unit` takes the compiled unit, the starting assignment (calibrated values the deployment or run starts from: a QMB run and a paper lane start from the unit's defaults; a live deployment carries the paper lane's last calibrated state with its watermark, Part C's call, R1-C-01), the read surfaces of §4.5, `scope_id` (the QMB run id or the node's deployment id), the state scope and bound, `trace_level` and `motion` (`on` or `off`).

### 4.2 `UnitStep`, returned by `HostedUnit.on_instant` (owner: P1; written by Part B's journal writer)

QMB and the node turn a step into rows through one run-slice handler, `qmb/src/qmb/host/unit_handler.py` (Part B, L0 AD-5). Decision and calibration rows ride the unit journal under Part B's kinds for them; state events ride kind `state`, which means only these runtime events (lifecycle moves are kind `lifecycle`, §8; R1-B-06). Every row that carries a `row_id` is journaled with that id as its record id, so a slice replayed after a crash writes nothing twice (R1-B-10).

| Part | Fields |
| --- | --- |
| `intents` | CT-23 format 3 intents (§4.4) |
| `decisions` | `row_id` is fp1 over the host's scope id (run id or deployment id), the instant and the ordinal; each `{row_id, instant, side, outcome: taken, skipped, no_signal, suppressed_warming, suppressed_limit, dropped_opposite; slot_trail: [{slot, binding, output}], readings_used: [{reading, version, value, source, knowable_at}], numbers_in_force: {name: value}, reason}`; taken and skipped rows and near misses by default, every bar at `trace_level = every_bar` (MIS-10) |
| `calibrations` | each `{row_id, number, old, new, rule (pin), read_trades: {from_trade_id, to_trade_id, count}, statistic, watermark}` |
| `state_events` | `warming`, `ready`, `cold_start {reason}`, `seam_flag {stream, jump}` |

### 4.3 The risk socket's slot contracts (owner: P2; content: the risk session)

| Slot | Inputs (local, plus optional surfaces with fallback) | Output |
| --- | --- | --- |
| sizer | entry reference price, stop price, instrument facts (§2.3), account facts `{equity, balance, open_risk}`, the unit's own record in R, market statistics from bound blocks, his limits `{risk_fraction ceiling, per-unit cap}` | `{quantity (lots, exact), receipt: {inputs used, rounding residue in R}}` or `{skip: reason}` (below minimum lot, rounding to zero) |
| exit block | the position `{quantity, average price, stop, targets, opened_by (compiled fingerprint), opened_at, bars_held, mfe_r, mae_r}`, market evidence | zero or more of `close_full`, `close_partial {quantity}`, `amend_protection {stop, targets}` with a reason |
| halt | unit and account statistics (losses in R this session, streaks), his limits | `none`, `no_new_entries {scope, reason}` or `flatten {scope, reason}` |
| cross-unit hook (called by the host, not the unit) | the proposed intent, the account's open positions across units, the board's dispersion reading (opt) | `pass` or `refuse {reason}` |

### 4.4 CT-23 format 3 (owner: P1; family in `qmf.risk.unit_intent`; consumed by the node and QMB)

Version: V-CT; the unit door accepts only 3; the Book door's known versions stay 1 and 2 (`packages/qmf-risk/src/qmf/risk/door.py:146-151`, CHECKED).

| `UnitEntryIntent` field | Meaning |
| --- | --- |
| `contract_format_version` | 3 |
| `intent_family` | `entry` (read by the kept Layer 2 harness) |
| `unit` | `{unit_id, version_ref, compiled_fingerprint}` |
| `instrument`, `market_id`, `direction`, `reason_code`, `execution_target` | as CT-23 format 2 where they exist there |
| `order` | `{type: market, limit, stop, stop_limit; limit_price (opt); stop_price (opt); time_in_force (opt); expires_after_s (opt)}` |
| `quantity` | lots, exact, from the sizer |
| `sizer_receipt` | §4.3's receipt |
| `protection` | `{stop: price or "none_declared", targets: [{price, fraction}], time_exit_bars (opt)}` |
| `not_before` | the latest `knowable_at` of the inputs the decision read (QML-18) |
| `placeholder_labels` | the bindings whose blocks are placeholders |
| `decision_row_id` | links the journal's decision row |

`UnitExitIntent`: `contract_format_version` 3, `kind` (`close_full`, `close_partial`, `amend_protection`), `quantity` (partial), `stop` and `targets` (amend), `position_ref` (opened by which compiled fingerprint), `reason_code`, `decision_row_id`. Default law: an amendment may tighten a stop, never widen it.

### 4.5 Read surfaces the host injects (owner: P1; fed by Part B in replay and Part C live)

| Surface key | Sample value | `knowable_at` |
| --- | --- | --- |
| `own_position:<market_id>` | the position of §4.3, or flat | the fill time |
| `own_journal` | closed trades `{trade_id, opened_at, closed_at, side, market_id, world, r_after_costs, entry_stamps: {name: value}}`, only those this hosted unit closed in its own run or deployment after its starting watermark; earlier history reaches the calibrator through the state the deployment carries | the close time |
| `weights:<entry_id>@<version>` | bytes plus fingerprint | deployment time |
| `reading:<entry_id>@<version>:<market_id>` | a stamped reading (Part C's shape) | its own |

`seam_check(warmup_tail, live_head, scale)` (pure, in QML) returns `{flag, jump}` for UT-11; the node records the warm-up source on the deployment and journals the flag.

## 5. Dictionary shapes

### 5.1 The entry `qmx.entry/1` in `component` fields (owner: P1)

`component_type` (old values kept; new: trigger, exit, sizer, motion, reading, combiner, calendar, context, structure, statistic, model, entry_order, halt, hook); `entry`:

| Group | Fields |
| --- | --- |
| identity | `schema: "qmx.entry/1"`, `entry_id`, `version`, `family`, `aliases`, `same_word_as` |
| trader face | `definition`, `boundaries`, `recognition`, `eligible_roles` (AD-104 vocabulary), `class_meanings: {class: text}`, `sources: [{source_ref, quote, dated}]` |
| machine face | `inputs: [{port, stream_kind, data_level (§5.2), fallback: [{data_level, expected_loss}]}]`, `output: {type: event, level, series, state, probability, quantity, exit_action, calendar_state; measure}`, `parameters: {name: NumberSpec}`, `warm_up: {rule, bars}`, `confirmation_lag_bars`, `min_sample`, `expected_lag_bars`, `transfer: {class: native, direct, adapted, conceptual_only, not_transferable, not_assessed}`, `mirroring: supported or not_applicable`, `state_bound` |
| implementation face | `code` (the existing `code` blob, Python), `fingerprint`, `golden: {reference, cases blob}`, `tests` (blob), `settle_bars` (recursive check) |
| origin | `qml`, `port-239`, `agent`, `human`, `placeholder`; `owner` for placeholders (`risk-session`) |

The `status` annotation (`named`, `specified`, `implemented`, `tested_on_data`, `used_in_unit`) and its evidence fingerprint are written by the status script, never by an author.

### 5.2 The data-level vocabulary `qmx.data-level/1` (owner: P1; used by Part C's instrument records)

`level`: 0 calendar, 1 bars, 2 quote ticks, 3 depth, 4 trade tape with aggressor side, 5 derivatives fields, 6 outside data. Splits: `volume: exchange, taker_split, tick_count, venue` (level 1); `depth: top, by_price, by_order` (level 3); `derivatives_clock: end_of_day, five_minutes, live; history: complete, sampled, provider_limited` (level 5); `licence` (text ref). A block declares what it needs; a record declares what a market offers; layer D compares them.

### 5.3 The reading card (owner: P1; publishing is Part C's)

A reading is an entry with `component_type: reading` and `reading: {tier: tick, bar, session, day or calendar (the clock it runs on, which decides where it runs: the tick tier inside the node on a trading machine, the others in the `mis` app, L0 AD-40, CF-6); concern: market_state or execution_health (a label for screens, never a placement rule); outputs: {value (measure), state (word list), health (live, stale, degraded, down)}, valid_classes, stale_after_s, minimum_sample, lag_bars, fallback chain}`. The tier words are Part C's (its reading record's `tier`). Stamped readings and reading history are Part C's (`01-connections.md` §5).

## 6. The block loader and the deployment's block folder (owner: P1; the folder carried by Part C's deployment)

```text
blocks/
  lock.json                         # [{entry_id, version, fingerprint, path}] sorted; its fp1 enters the compiled fingerprint
  <entry_id>/<version>/block.py     # the block source, bytes as stored in the Library
  <entry_id>/<version>/entry.json   # the entry's machine face and fingerprint
  weights/<entry_id>@<version>.<ext>   # learned weights (opt), fingerprint in lock.json
```

On a node the folder is assembled in its volume from files the deployment names by fingerprint; files the volume lacks reach the machine ahead of the deploy through the Library hub, and there is no size setting, so a learned block's weights of any size deploy (R1-C-06, Part C). `load(lock, sources, weights)` returns `{blocks: {pin: BLOCK}, lock_fingerprint}` or every problem (`block_missing`, `block_fingerprint_mismatch`, `block_compile_error`, `block_protocol`, `weights_missing`, `weights_fingerprint_mismatch`), each with the pin and a hint. Block fingerprint: fp1 over `{"block.py": LF-normalised UTF-8 text}`. The block protocol (`qml.blocks.api`): a module exports `BLOCK` with `make(params, inputs) -> instance`; an instance has `update(evidence) -> output` (exact, quantised at the port), `export_state() -> mapping` and `import_state(mapping)`, and its state never exceeds the entry's `state_bound`.

## 7. The identity table `units.identity_table` (owner: P2; read by QML, the judge and the Lab)

A core setting, a list of rows `{label, result: calibration_row, new_version, new_unit; counted_try: boolean; click_before_live: boolean}`. Shipped default (from funnel `unit.md` §5 and Lab AD-16, designed only):

| Label | Result | Try | Click |
| --- | --- | --- | --- |
| `motion_inside_range` | calibration row | no | no |
| `learned_retrain_in_bounds` | calibration row | no | no |
| `learned_retrain_out_of_bounds` | new version | yes | yes |
| `range_change`, `motion_rule_change`, `cadence_change`, `fixed_value_change`, `bar_change`, `session_change`, `markets_change`, `market_settings_adopted` | new version | yes | yes |
| `block_fix` (same entry, new version) | new version of every unit that pins it | yes, per unit | yes |
| `block_swap`, `role_added`, `role_removed`, `combiner_change`, `transplant`, `market_logic_change` | new unit in the family, linked to its parent | yes | yes |
| `rewrite` | new unit marked `rewritten_from` | yes | yes |
| `ambiguity_resolved` | corrected successor; the old version stays | yes | yes |
| `title_change` | none (a label) | no | no |

`qml.identity.classify(old, new, table)` returns `{labels, result, counted_try, click_before_live}`; the highest result wins when several labels apply (new unit over new version over calibration row).

## 8. Lifecycle (owner: P2; events carried by Part B's journal)

States per unit per market: `draft`, `tested`, `parked`, `paper`, `live`, `stopped`, `retired`. Event body: `{schema: "qmx.lifecycle/1", event_id, unit_id, version_ref, compiled_fingerprint, market_id, from, to, by: {kind: judge, his_click, risk_rule, system; principal}, reason, evidence_ref, clears (opt): the event id a move out of `stopped` clears, at}`. Carried by Part B's unit-journal kind `lifecycle`. Writers, each on its own partition: This PC's host for his clicks (through `units_promote` for moves toward paper or live, Part C slice C-23), the judge for draft to tested or parked, the node for risk stops (R1-B-06). A `his_click` event is legal only with `principal = "operator"`; any other principal on a move toward paper or live is a rejected event (AG-13). Transitions: draft to tested (judge pass) or parked (judge fail); tested to paper (his click; automatic only if `lifecycle.auto_paper` is on, default off); paper to live (his click); live or paper to stopped (risk rule, automatic, logged); stopped to paper or live (his click); live to parked (his click); any to retired (his click). `fold(events)` orders by `(at, writer, sequence)`, applies a move out of `stopped` only when its `clears` names the latest stop for that unit and market (so clock skew between This PC and a server cannot clear a newer stop), and refuses an illegal transition as a rejected event, which it reports. Admitting a version on a market where another is `paper` or `live` requires the same click to park or retire the other (UT-23).

## 9. Settings this part names (all editable; none is a cap)

| Setting | Starting default | Origin |
| --- | --- | --- |
| `checker_slice_margin_bars` | 200 bars past the derived warm-up | funnel `qml.md` §11, INFERRED |
| `checker_slice_source` | the unit's first market's most recent full month in the Library | funnel `qml.md` §11 |
| `unit_check_hook_timeout_s` | 8 | under the guard's 10 s (G2 §2.1) |
| `nearest_suggestions` | 3 | funnel `qml.md` §11 |
| `problem_text_max_chars` | 300 per message and per hint | keeps answers under the 20,000-character spill (G2 §1.3), INFERRED |
| `no_progress_repeats` | 1 (stop after the same set twice) | AG-11 |
| `port_quantum_significant_digits` | 12 | INFERRED: absorbs float noise between builds |
| `decision_tolerance` | decisions identical; values within 1e-9 relative | funnel `qml.md` §11 |
| `golden_tolerance` | 1e-9 relative, 1e-12 absolute | shipped `bc-build-a-component/scripts/verdict.py` |
| `settle_check_warmups` | 1x, 2x, 4x the declared warm-up | QML-03, INFERRED |
| `min_trades` (slow motion) | 60, for a calibrated number that declares no `motion.min_count`; the dummy's `min_trend_strength` declares 20 (R1-A-01) | funnel `unit.md` §10 |
| `shrink_k` | 100 | funnel `unit.md` §10 |
| `slow_cadence` | every 20 closed trades or at the market's day close | funnel `unit.md` §10 |
| `range_edge_card` | at its range edge 3 times in 10 sessions | funnel `unit.md` §10 |
| `seam_jump_scale` | 3 times the warm-up's median absolute bar change | UT-11, INFERRED |
| `trace_level` | `events` | funnel LC-18 |
| `lifecycle.auto_paper` | off | R0-14 |
| `state_bound` | derived from the blocks' bounds; the shipped 256 for bots stays | G1 §9 |
| `update_time_growth_tolerance` | 1.5: the last tenth's median time per update may be at most 1.5 times the first tenth's (QML-04's test) | R1-A-02, INFERRED |

## 10. Catalog rows (owner: P8 by registration; functions here)

| Row | Approval | In | Out |
| --- | --- | --- | --- |
| `unit_new` | read | `template` (id), `overrides` (opt) | a unit document with defaults and origins |
| `unit_check` | read | `document`, `previous_problem_set` (opt) | `qmx.check/1` |
| `unit_explain` | read | `document` or `unit_ref` | the unit card: slots in trader words, numbers with motion, data needs, placeholders |
| `blocks_find` | read | `words`, `role` (opt), `data_level` (opt), `class` (opt), `limit` | one-line index rows `{entry_id, version, aliases, family, output, data_level, status}` |
| `blocks_get` | read | `entry_id`, `version` (opt) | the entry in full |
| `blocks_check` | read | an entry draft and its source text | `qmx.check/1` for entries |
| `blocks_match` | read | `text` | each sentence with an entry id or `unmatched`, plus append requests |

Saving uses the existing `library_save` row; the Library runs its checks.

## 11. Library kind-file additions (owner: P6 rules; this part's entries)

`checks: [{checker, on: put or publish, applies_when (opt): {pointer, equals}}]`. `unit.schema.json`: `schema_version` 2, the generated shape of §1, `checks: [{checker: "qml.unit/1", on: "publish"}]`. `component.schema.json`: new `component_type` values, an optional `entry` object, `status` in `annotations`, `checks: [{checker: "qml.entry/1", on: "put", applies_when: {pointer: "/entry/schema", equals: "qmx.entry/1"}}]`. The refusal keeps the first problem's message as its text and carries every problem. The host registers `qml.unit/1` and `qml.entry/1` at composition.

## 12. Matching `01-connections.md`, row by row

| Row | Same shape, owner, door, version, down-behaviour? | Note |
| --- | --- | --- |
| C1 copilot or agent to the checker | yes | row name `unit_check` in the new `unit` toolset |
| C2 author to the Library | changed | put checks shape; publish runs A to F (contract change 1) |
| C3 script step to the checker | yes | the step imports `qmx_tools` (which imports QML) |
| C4 hook to the checker | yes | after the probe; the save and compile still check |
| C5 the QML door rows | changed | two toolsets and seven rows (contract change 2) |
| C6 the loader | yes | layout and error shape defined in §6 |
| C7, C8 QMB run requests | yes | the unit by `id@version`; QMB compiles and needs G (§3.3) |
| C10 result landing | consumed | G's `test-report` rides it (contract change 3) |
| C12 compiled unit in process | changed, folded in | hosted through `construct_unit` and Part B's one run-slice handler; the step and surfaces of §4 (contract change 4) |
| C13 journal writer | consumed | decision, calibration, state and lifecycle bodies (contract change 5) |
| C15 queries | consumed | `instrument_get` for records (§2.3) |
| C18 refresh jobs to records | consumed | the data-level vocabulary is this part's (contract change 6) |
| X1 deployment | consumed | carries the block folder of §6 (contract change 7) |

## Contract changes (for the writer of `01-connections.md`)

All eight were folded into `01-connections.md` on 1 Nov by fixer X1-0A (rows C2, C5, C10, C12, C13, C18 and §5).

1. **C2.** "unit document in; governed draft or a refusal with every problem out" becomes: the Library `put` of a `unit` checks the kind's generated shape (layer A) and returns every problem; publish of a `unit` runs the QML checker (A to F) and refuses with every problem; the kind file lists the check and the host registers the checker. Reason: a shipped test saves a schema-minimal unit (`qmx-library/tests/test_view.py:110-128`, run).
2. **C5.** Rows `unit_new`, `unit_check`, `unit_explain`, `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match` in two new core toolsets `unit` and `blocks`; the harness derives its domain groups from the catalog.
3. **C10.** Add: layer G's result lands as a `test-report` record (`check: qml-g/1`, keyed by the compiled fingerprint, linked `tests` to the unit version).
4. **C12.** "the structural `BotFactory` seam" becomes: hosts run units through `construct_unit` and `HostedUnit` (`qml.protocol.unit`), which admits only CT-23 format 3; the step output and the injected surfaces `own_position`, `own_journal` and `weights` are §4's.
5. **C13.** Add the bodies this part owns: decision rows, calibration rows, state events (§4.2) and lifecycle events (§8), each a journal kind of Part B.
6. **C18 and §5 of the master.** Add the data-level vocabulary `qmx.data-level/1` as a shape owned by P1 and used by P4's records.
7. **X1 and §5 of the master.** The deployment's block folder layout is §6 here (owner P1); the deployment record that carries it stays Part C's.
8. **§5 of the master.** Add owner rows: the identity table setting (P2), the lifecycle event body (P2), the `qmx.check/1` and `qmx.behaviour/1` shapes (P1).
