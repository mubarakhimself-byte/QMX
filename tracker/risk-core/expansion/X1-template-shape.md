# X1: the template's shape (the chassis), Stage B

Stage B linking round, layer X1, 3 Nov 2026 (evening). File id `X1-template-shape`. Ledger additions in `ledger/additions/X1-template-shape.yaml` (ids prefixed `x1_`; each carries the Stage A name as an alias so the funnel can merge). This file revises and extends the stopped draft `expansion/drafts-stopped/X1-template-shape.md` (76 ideas, written before R4 to R9 and the component catalogue existed). The draft's ideas are kept; each is now a hybrid that names the components it links, and the appendix maps old idea numbers to new hybrid ids.

**What this layer is.** His words: "how do we technically design this or make something that can handle any amount of stress without it? I would call it the chassis" (`seeds/operator-words-2026-11-03.md:10`). This file widens what the chassis can be. It does not pick and it sets no numbers.

**How to read.**
- `A4-001` is short for `A4-template-agents-telemetry-001` in `linking/components/A4-template-agents-telemetry.yaml`; `A1-`, `A2-`, `A3-`, `A5-` likewise for `A1-sizing-allocation`, `A2-brakes-drift-exits`, `A3-structure-regimes-scenarios`, `A5-topup`.
- `TLH n` is item n of "What the technical lens must hold" in `seeds/SEEDS.md`. `G8 Bn` is blocker n in G8 "What blocks it today"; `G9 Mn` is item n in G9 "What is missing". `R7 §n` is a section of `research/R7-software-patterns-self-configuring.md`; `R9 §0` its definitions.
- Maturity: **solid** (every link rests on a seam that exists in code or on checked production software), **plausible** (needs a new seam, fits the rulings), **wild** (kept for the funnel; may break a ruling).
- **[judgment]** marks my opinion. Evidence grades follow `linking/RANKING.md`: live, fair control, author backtest, idea.
- Every `x1_` id named under "Ledger" is a row in the additions file, except these, which are catalogue, job or list names rather than variables and are left out of the ledger on purpose: `x1_risk_app_jobs`, `x1_pod_bundle_contents`, `x1_agent_tool_rows`, `x1_sizer_inputs`, `x1_node_constants_to_rows`, `x1_dictionary_family`, `x1_dry_chassis_run`, `x1_weight_gap_log`. Some names resolve through an alias (`x1_lock_lower_overrides`, `x1_template_lineage`, `x1_methodology_drop_in`, `x1_rollout_time_to_rollback`, `x1_rollout_share_steps`).
- **Class and style key**, so each hybrid can say its behaviour per class in one line. `K-fx`: FX and metals on cTrader (CFD, 24/5, broker tick values, swaps). `K-idx`: index and energy CFDs (cash session plus thin overnight, gaps at the open). `K-cry`: crypto perpetuals on Hyperliquid (24/7, funding every eight hours, no day boundary unless declared). `K-fut`: exchange futures (per-contract records, rolls, central book). `K-stk`: single stocks (session only, splits and halts). `S-sc`: scalper (tens of trades a day; windows measured in trades). `S-id`: intraday (a few trades a day; windows in sessions). `S-sw`: swing (trades a week; windows in weeks; rarely flat).

**Method.** `bmad-brainstorming` headless (memlog and intent in `linking/stage-b/X1-template-shape/`): Morphological Analysis over the component catalogue, Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure, Solution Matrix. `bmad-cis-problem-solving` on every open problem (section 2). `bmad-party-mode` roundtable, session mode, five voices (Appendix A).

---

## 0. The ground the chassis stands on

The seams that exist at the stack tip (d02af358), from G8 and G9, unchanged since the draft: the unit document with every risk place (`sizer`, `exit_set`, `halts` at three scopes, `reads`, `numbers` with kind, measure, default, range, motion, authority, origin); a compiler that refuses halts and reads and compiles two of six motion modes; four slot protocols with contract tests; a sizer fed equity, entry, stop and the instrument record; the identity table in Settings; one loader with a fingerprint pin and layer F; Library kinds (`unit` and `component` governed, `template`, `book`, `bms`, `pod` empty); agent rows that write drafts; the node's kill switch, stand-downs, SQS and a risk-stop pipe nothing feeds; journals with `risk_event`, `would_have` and `guard` open; a ledger v0 with 267 variables and 473 couplings.

What changed since the draft: R7 found the model (Kubernetes controllers plus the VPA: typed document with defaults, a learner with bounds, an applier with owner modes, guarded guesses; Argo Rollouts plus Kayenta for versions). R9 defined brake, accelerator, restore and clamp with nine attributes. Stage A cut 887 components. STATE item 31 adds that the Lab, MCP-driven agents and the agent department must plug in with no rework and never sit in the order path. The one-line summary of the loop the chassis must hold, in R7's words: QMX has the learner and no applier.

---

## 1. Hybrids

### A. The self-configuring loop (the Kubernetes and VPA model)

**X1-H01. Spec and status on the unit document, with separate write rights.**
- Links: A4-019, A4-020, A4-081, A4-065, A4-040.
- Need: TLH 8 (a clear split of self-configured and user-configured), N3 of R7, G8 B6 (fields parsed and ignored).
- What: the unit document is the **spec**: his and agents' choices (blocks, ranges, derivation bindings, authority modes, the never-self-tune list). A **status** object holds what the runtime learnt and did: tuned values with bounds, brake states, calibration receipts, the trading state per scope, and the last RiskState. People and agent drafts write spec; only the runtime writes status; nothing writes both. Every status carries `status_generation`, the spec fingerprint it was computed against, so a brake state from an old version is known stale. The A10 snapshot already stamps by fingerprint; this names the two halves and gives them owners.
- Levels: unit; the same split on cluster and portfolio documents (H40).
- Class and style: identical for all; `K-cry` status has no day boundary unless the spec declares one (H41).
- Ledger: `x1_field_owner`, `x1_status_generation`, `state_carry_rule`, `applies_to_open_positions`.
- Performance: none direct; it is what lets the learner (H02) and the applier (H03) run without racing his edits. Survival: a stale status can no longer size a trade.
- Evidence: Kubernetes API conventions and MT5 inputs read-only (CHECKED, R7 §3.1, §9.1); the QMX snapshot (built). Weakest link: no trading system was found that splits these two halves by name.
- Maturity: **solid**.

**X1-H02. The learner with bounds: the motion engine becomes a VPA recommender.**
- Links: A4-001, A4-080, A1-062, A4-196, A1-032, A4-015.
- Need: TLH 6, 7 (every number derives; values in ranges with a reason); G8 B5 (sizer numbers cannot move).
- What: a motion block no longer writes a value. It publishes into status a **target with a low and a high bound**, from the unit's own decayed record, shrunk toward its pooled group (empirical Bayes, with the edge shrunk toward zero), clamped by the owner's `range`. Decay is counted in trades, not hours. For `risk_fraction` the learner reads the edge as a band (A1-032) and the profile's `edge_point` picks which point sizing uses. The learner never applies anything; H03 does.
- Levels: unit; the pooling group lives at cluster (H44) or class.
- Class and style: `S-sc` decays over hundreds of trades; `S-sw` over tens; `K-fut` keeps one record per contract and pools across the roll; `K-cry` pools across venues only through the underlying (A1-165).
- Ledger: `x1_recommendation_bounds`, `x1_recommendation_decay_half_life`, `number_motion_mode`, `calibration_shrink_k`, `calibration_min_trades`, `edge_range`, `kelly_shrink_factor`.
- Performance: the fraction can rise toward what the record supports instead of sitting on a placeholder (the self-configuring he asked for). Survival: the bounds show how unsure the learn is, and a wide band keeps the applier (H03) off.
- Evidence: VPA recommender (CHECKED); the shipped motion engine (built); shrinkage is a standard method with no multi-instrument trading comparison in the sources (A4-196). Weakest link: no study shows a learned fraction beating a fixed one when trades are independent (R9 short answer 4).
- Maturity: **solid** for the mechanism, **plausible** for the gain.

**X1-H03. The applier: authority modes per number, with a dead band, a share cap and no infinite retries.**
- Links: A4-002, A4-003, A4-037, A4-102, A1-060, A4-022.
- Need: TLH 6, 8; G8 B6 (`authority` and `applies_to_open_positions` parsed and never read); R7 "QMX has the learner and no applier".
- What: one new organ in both hosts reads each number's status recommendation and applies it only in the mode its spec sets: `off` (shadow: computed, shown, journalled as `would_have`), `at_flat`, `at_new_position` (open positions keep their value unless `applies_to_open_positions`), `at_period_open` (Gen 3's "next period open"), `live`. It skips changes inside a dead band, caps how many units of one cluster may retune in one window (herding guard), remembers infeasible applications and does not retry them until a new recommendation exists.
- Levels: unit numbers; cluster and portfolio numbers through the same organ with their own modes.
- Class and style: `S-sc` is flat often, so `at_flat` is cheap; `S-sw` and `K-idx` overnight units rarely flatten, so `at_period_open` or `at_new_position` are their natural modes; `K-cry` has no period unless declared.
- Ledger: `x1_number_authority_mode`, `x1_retune_dead_band`, `x1_retune_share_cap`, `x1_edit_effective_at`, `applies_to_open_positions`.
- Performance: a better value earns its place without a new unit version; the share cap stops forty units moving together. Survival: `off` and `at_flat` keep a bad learn away from open trades; `live` is the rare mode.
- Evidence: VPA update modes and flags (CHECKED); Gen 3 effect-at-period-open (docs); nothing in trading applies learned values this way. Weakest link: the meaning of "flat" for a multi-position unit is undefined (Gap 6).
- Maturity: **solid** (the fields exist; the organ is new code).

**X1-H04. The guarded guess: a guard per tuned number, a trip counter that freezes, and a Simplex fallback for the whole sizer.**
- Links: A4-006, A4-007, A4-009, A4-031, A4-134.
- Need: STATE principle "tuned numbers are guesses with guards that fall back and freeze"; TLH 28 (size down in steps; tell a bad day from a broken edge).
- What: two guards at two depths. (1) Per number: a `tuned_value_guard` states what must hold while the tuned value is in force (for example realised loss per trade within the bound the learn assumed). A trip reverts the number to its default, writes a reason code, and counts; after `guard_freeze_limit` trips the number freezes at its default and a card flags him. (2) Per unit: a `safe_region_bound` on projected open risk and drawdown; outside it the fixed sizer (`fixed-fraction-at-stop@1` or the preset's baseline) takes over for a `fallback_dwell`, then the tuned sizer may return. Like PID_Compact, a failed tune returns to the previous mode and values.
- Levels: number guards at unit; the region guard at unit and cluster.
- Class and style: the region is in R for all classes; `K-idx` and `K-fut` gaps can leave the region in one step (known failure), so their region bound includes the gap scenario from X4.
- Ledger: `x1_tuned_value_guard`, `x1_guard_trip_count`, `x1_guard_freeze_limit`, `x1_safe_region_bound`, `x1_fallback_dwell`, `x1_value_reason_code`.
- Performance: the tuned sizer runs most of the time; the fallback is a floor on behaviour, not a cap on growth. Survival: every guess has a named way back; a number that keeps failing cannot keep guessing.
- Evidence: HotSpot deoptimisation and recompile limits (CHECKED source); Simplex (secondary paper); PID_Compact (docs, part snippet). Weakest link: the guard conditions themselves are numbers nobody has set (numbers lens).
- Maturity: **plausible**.

**X1-H05. Asymmetric motion: cut by severity, grow only on evidence gathered at the current size, a stabilisation window per direction, missing data pushes the cautious way.**
- Links: A4-004, A4-005, A4-011, A4-012, A4-197, A4-013, R9 §3.2 (asymmetric speeds).
- Need: TLH 28 ("size down, but not quickly" is his; the chassis must express both speeds); his A25.
- What: each moving number carries a `behavior` block per direction, as the HPA does. Down: a short window, a cut graded by the signal (a stop-out is not a slow bleed), a rate cap per update. Up: a long window over which the cautious (lowest) recommendation is taken, growth only when at least the last window's trades were taken at the current size (AIMD "in use"), a smaller rate cap, and a warm-up ramp after a version change or a long idle spell. A tolerance band inside which nothing moves. Missing inputs push the number in its declared `cautious_direction`, never the risky way.
- Levels: unit; the same block shape on cluster caps.
- Class and style: windows in trades for `S-sc`, in sessions for `S-id`, in weeks for `S-sw`; `K-cry` idle is rare, `K-stk` idle is nightly, so the idle rule is per class.
- Ledger: `x1_motion_window_down`, `x1_motion_window_up`, `x1_motion_rate_cap`, `x1_motion_tolerance`, `x1_cautious_direction`, `drift_size_down_step`, `grow_back_rule`, `size_levels`.
- Performance: R9's AIMD-style path brake ran at 79 % of base risk with the same growth per unit of risk; growth is not given up, only churn. Survival: the 25 % drawdown chance fell from 1.3 % to 0.5 % in that script.
- Evidence: HPA, TCP, Netflix AIMD (CHECKED); R9 script arithmetic (synthetic). Weakest link: no live trading test of a direction-split motion rule.
- Maturity: **plausible**.

**X1-H06. His limits as a never-self-tune list, with the account as the policy level.**
- Links: A4-017, A4-052, A4-043, A4-101.
- Need: TLH 8 (user-set floor and cushion); his C11; STATE "a deny-list and borrowed priors".
- What: every ledger row carries `changed_by_class: measured | self | user`. The `user` rows form a never-self-tune list per template that no learner, applier, agent or expression may move: the floor, the buffer before it, the kill line, the kill level. The account is the policy level: a value set there beats every scope (VS Code policy). A blank `user` row blocks live (Gen 3 `blank_effect`), so no key setting is ever left empty by accident.
- Levels: portfolio and account rows; the list is declared on the template.
- Class and style: one list for all; `K-cry` adds a funding-rate ceiling as a user row **[judgment]**.
- Ledger: `x1_never_self_tune_list`, `x1_changed_by_class`, `portfolio_floor`, `bms_buffer_before_floor`, `kill_line_floor`, `kill_switch_level`.
- Performance: none; it bounds the learner. Survival: the floor cannot be learnt away; the old blanked thresholds (D31) cannot recur.
- Evidence: OtterTune deny-list and MT5 `sinput` (CHECKED); Gen 3 `value_status_required` (docs). Weakest link: a list kept by habit can freeze numbers that should move (A4-017 known failure).
- Maturity: **solid**.

**X1-H07. A reason code on every resolved value, in a real sizer receipt.**
- Links: A4-031, A4-086, A4-014, A1-122, A4-153.
- Need: his A13 (every change in size has a stated reason); TLH 7; G8 B3 (hard-coded receipt).
- What: every number the sizer uses resolves with a reason: `default`, `calibrated`, `inherited:<level>`, `capped_by:<rule>`, `stale_so_default`, `frozen_after_trips`, `user`. Evaluation never throws; a missing source returns the default with `stale_so_default`. The receipt names every modifier's proposed cap and the one that bound (April's `binding_clamp`, now a field). Ten words for him come from the reason codes; the full chain is a click away (H52).
- Levels: trade (the receipt), unit (the codes).
- Class and style: identical; `K-fx` conversion reads add a `conversion:<rate>` reason when a cross is sized (A1-160).
- Ledger: `x1_value_reason_code`, `rounding_residue_r`, `control_rank_table`.
- Performance: a cap that always binds is visible and can be fixed (April's dead-weight caps). Survival: a silent fallback is impossible; the fallback is named on the order.
- Evidence: OpenFeature spec (CHECKED); dash.js priorities (CHECKED source); April's audit (old QMX). Weakest link: none technical; it is bookkeeping.
- Maturity: **solid**.

**X1-H08. Derivation as a block, a receipt per value, and a fallback ladder with pooled priors.**
- Links: A4-054, A4-055, A4-015, A4-196, A4-101, A1-063, A5-048, A5-099.
- Need: TLH 6 ("What if I want to change the way it is derived?"); TLH 8 (no key setting blank); D29, D30, D46.
- What: a component type `derivation` computes a number from facts and writes a receipt (derivation id, inputs, old and new value). Swapping the derivation is a version. The ladder: own record (if `calibration_min_trades` met) → pooled group posterior (shrink toward the class or family, costs kept local, market mechanics never pooled, A5-048) → class or bucket default → preset default → refuse to compile. Each rung is a receipt, so a unit with no record still gets a value with a reason. Pooling weight follows years of history (A5-099).
- Levels: unit numbers; group priors at cluster or class.
- Class and style: `K-fut` and `K-cry` pool statistics but never roll, expiry or funding rules; `K-stk` pools within size and sector buckets; `S-sc` reaches its own rung fastest.
- Ledger: `x1_derivation_rule`, `x1_derivation_receipt`, `x1_derivation_fallback_order`, `calibration_min_trades`, `calibration_shrink_k`, `paper_to_live_carry_rule`.
- Performance: a new unit starts from the best evidence it can borrow instead of a placeholder. Survival: a borrowed prior from a mismatched group misleads (A4-015 known failure); the shrinkage of the edge toward zero is the hedge.
- Evidence: OtterTune workload mapping (CHECKED); shrinkage (standard method); Carver's pooling distance test (author backtest). Weakest link: the gain from pooling is lower estimation variance, not shown as higher held-out return.
- Maturity: **solid** for the block and ladder, **plausible** for the pooled rung.

**X1-H09. Two derivation languages: blocks, and a small expression form compiled to a block.**
- Links: A4-056, A4-082, A4-070.
- Need: TLH 6, 33 (he and the copilot can read a derivation); D33.
- What: beside derivation blocks, a field may hold `equity * fraction / stop_distance`, parsed at compile into a generated derivation block with no calls, no loops and a name list from the ledger. n8n lets any field be an expression and marks some fields `noDataExpression`; the never-self-tune rows are those fields here.
- Levels: any number.
- Class and style: identical.
- Ledger: `x1_expression_names_allowed`.
- Performance: the copilot can propose a derivation he can read. Survival: the loader and layer F see only blocks.
- Evidence: n8n expressions (CHECKED); the QMX form is an idea. Weakest link: a parser to write and keep.
- Maturity: **plausible**.

**X1-H10. Trading states as the spine of every brake, mapped onto the kill levels, with hysteresis.**
- Links: A4-063, A2-046, A2-112, A4-134, A4-193, A4-010, A4-171.
- Need: his C21 (exits never blocked), C7 (each brake says what tripped), A25 (size down, not quickly); R9 N8 graded brakes.
- What: per scope a machine with `ACTIVE`, `REDUCING` (new entries smaller or none; amendments only tighten; exits run), `HALTED` (no new entries; exits, broker stops and the kill switch work; unlike Nautilus, protective stops are never denied), `RESTORE` (H11). Every brake and accelerator is a transition or a step inside a state, each with a reason, a declared cost in growth given up (Stitch tactics) and separate trip and clear levels (SwingGuard hysteresis). The kill switch's four levels map onto the same words (YELLOW → HALTED at scope without flatten, RED → HALTED with flatten, BLACK → HALTED at all); the kill switch stays his hand and only he lowers it. Every transition is journalled, including his own.
- Levels: position, unit, cluster, portfolio, account.
- Class and style: `K-cry` REDUCING must allow funding-driven reduce-only closes; `K-stk` HALTED across a venue halt is read from the feed state, not from the brake.
- Ledger: `x1_trading_state`, `x1_state_transition_table`, `brake_state`, `kill_switch_level`, `grow_back_rule`.
- Performance: REDUCING keeps a unit trading small through a bad day instead of stopping it, which is his A25. Survival: HALTED is a law, not a block's choice; closes can never be blocked.
- Evidence: Nautilus states in production (CHECKED); MQL5 15085 RESTORE (author backtest, small gain); SwingGuard four states (author backtest). Weakest link: two state machines on one node until the mapping is built (P15).
- Maturity: **solid** for the states, **plausible** for RESTORE and the mapping.

**X1-H11. Half-open restore: probe small before full size, then regrow fast up to a memory ceiling and slowly past it.**
- Links: A4-191, A2-112, R9 §0.3 "memory ceiling", R9 short answer 9, A4-013.
- Need: TLH 28; R9's rule "do not let an accelerator re-raise into a trip".
- What: leaving HALTED or REDUCING passes through a half-open phase: `restore_probe_trades` at `restore_probe_size_share` of baseline, judged as a group; a failed probe returns to the braked state with a longer wait (Envoy's growing ejection time); a passed probe regrows fast to just below the size where the trip happened (the memory ceiling, TCP `ssthresh`) and slowly beyond it. Any active brake outranks the regrowth (H13).
- Levels: unit and cluster.
- Class and style: probes counted in trades for `S-sc`; in sessions for `S-id`; `S-sw` probes are one trade each, so the group is small and the wait is long.
- Ledger: `x1_restore_probe_trades`, `x1_restore_probe_size_share`, `x1_memory_ceiling`, `circuit_breaker_reset`, `grow_back_rule`.
- Performance: a healthy unit is back at size after a few probes instead of waiting out a timer. Survival: a sick unit never jumps from zero to full.
- Evidence: resilience4j half-open and Envoy ejection time (CHECKED); MQL5 23315 probe before restore (author mechanism); TCP (RFC). Weakest link: no trading study of probe restores against a timer restore.
- Maturity: **plausible**.

**X1-H12. Every brake has a mode: shadow, ramped, live.**
- Links: A4-191, A4-190, A4-030, A4-012.
- Need: TLH 23 (brakes addable, removable, combinable); his "let's first explore" (B13).
- What: a new brake enters in `shadow` (resilience4j METRICS_ONLY): it computes, writes `would_have` rows, trips nothing. Then `ramped`: an `enforcement_percent` chance that a trip is enforced, raised from 0 (Envoy). Then `live`. Brake precision (the share of fires that needed action, A4-156) is read from the shadow rows before anyone turns it on, which answers his "which brakes are useful, which to combine".
- Levels: all.
- Class and style: identical; isolation brakes (class or region scope) default to shadow for longer because their fires are rarer **[judgment]**.
- Ledger: `x1_brake_shadow_mode`, `x1_enforcement_percent`, `brake_precision`.
- Performance: no noisy brake throttles a good unit before its precision is known. Survival: a brake that is needed urgently can be set live at once; shadow is the default, not a lock.
- Evidence: resilience4j and Envoy (CHECKED); `would_have` kind (built, open body). Weakest link: shadow brakes cannot see the market impact of the size they would have cut.
- Maturity: **solid**.

**X1-H13. One arbiter per scope: a rank table for the same tick, and "any brake blocks every raise".**
- Links: A4-103, A5-138, A4-014, A4-018, A4-066.
- Need: his C7 (many brakes at once; know what is breaking); A2-131 (too many brakes fire together without a rank table).
- What: each scope declares one rank table saying which control wins when several act on one tick (operator, protection, forced flat, halt, modifier, accelerator), with defaults the template ships (Gen 3 shipped none and blocked live). Sizing opinions combine as in dash.js: each proposes a cap with a priority; smallest wins within a priority; a strong priority (a halt) beats the rest. Raises follow the inverted AWS rule: cut if any brake says cut; raise only if every accelerator agrees and no brake is active.
- Levels: all; one table per scope.
- Class and style: identical.
- Ledger: `control_rank_table`, `x1_slot_combiner_rule`, `x1_value_reason_code`.
- Performance: a brake's cost is bounded by its rank, not by chance ordering. Survival: no raise can slip through while anything is braking.
- Evidence: Gen 3 rank table (docs, off path); dash.js (CHECKED); AWS any/all (snippet, inverted by R9). Weakest link: smallest-wins across many weak opinions can shrink size to nothing (A4-014 known failure); brake precision (H12) is the fix.
- Maturity: **plausible**.

**X1-H14. One registry row per brake or accelerator: the nine attributes plus counting rule, fail mode and equity base.**
- Links: A5-106, A5-100, A2-113, A2-114, A2-115, A4-059, A4-061.
- Need: TLH 10 (terminology agents can use), 46 (count fast invalidation), 47 (equity measures); D37.
- What: every brake and accelerator is one ledger row and one dictionary entry with: reads, scope, anchor, changes, direction, shape, speed, hysteresis, memory and clear (R9 §0.2); plus `loss_counting_rule` (full stops only, by size in R, at or worse than q; whether FI cuts, breakevens and forced flats count), `fail_mode`, `brake_equity_basis` (realised or marked; day start, period open, high-water mark, fixed floor), and the declared baseline it moves from. The day baseline is computed, optionally confirmed, persisted and restored on restart (MQL5 24396).
- Levels: all.
- Class and style: `K-cry` anchors on a rolling 24 h or a declared UTC boundary; `K-fut` anchors survive the roll; `K-stk` anchors are session-based.
- Ledger: `x1_brake_registry_row`, `loss_counting_rule`, `brake_equity_basis`, `x1_fail_mode`, `x1_day_baseline_confirmation`, `exit_reason_code`.
- Performance: a brake that counts an FI cut by its size fires less on a healthy scalper (R9 short answer 10). Survival: "5 % drawdown" can no longer mean four things.
- Evidence: R9 definitions (first principles plus the audio compressor analogy); MQL5 risk managers (author mechanism); G11's four counting rules (history). Weakest link: the attributes are a schema; no value is set.
- Maturity: **solid**.

### B. The document and its plug-ins

**X1-H15. The risk profile as its own document, `qmx.risk-profile/1`, with unknown fields refused.**
- Links: A4-088, A4-070, A4-047, A4-019, A4-081.
- Need: TLH 31 (schemas; versions of the risk part); D43 ("we need schemas").
- What: the sizer binding, the exit set, halts at every scope, the hook policy, the numbers with derivations, levels and authority modes, the needs list, the fail modes and the pack list become one document a unit names by id, version and fingerprint, embedded at compile so the unit still stands alone on the node. The schema refuses unknown fields (Nautilus `deny_unknown_fields`), and every field it accepts is read by compiler format 2 or refused with a message (no more parsed-and-ignored).
- Levels: unit; cluster and portfolio documents share the shape (H40).
- Class and style: one schema; class and style enter through the override chain (H38) and presets (H16).
- Ledger: `x1_profile_schema_version`, `x1_profile_version_pin`.
- Performance: one profile serves many units of a type; agents version it without touching logic. Survival: a mistyped setting fails loudly instead of doing nothing.
- Evidence: n8n credential types and node descriptions (CHECKED); Nautilus config (CHECKED); the Pin shape in `model.py` (built). Weakest link: two versions describe one running thing (Collision 1).
- Maturity: **solid**.

**X1-H16. One schema, many presets; a preset is a chart: defaults file, schema, parent layer, revisions.**
- Links: A4-053, A4-046, A4-194, A4-060, A4-048.
- Need: TLH 3 (one template per unit type; the set may change); A5.
- What: a preset is a Library `template` item holding bindings, derivation choices and override diffs for one unit type (`scalper-mr`, `orb`, `trend-pullback`, and the next). Its values are derivations, not numbers (D29). It validates against the schema on save, publish and compile (Helm `values.schema.json`); a parent layer (a methodology drop-in, H44) can set shared values; `null` removes a default on purpose; revisions are numbered and a unit can switch back. The nested-settings trap (replace one element, not the parent) is a checker rule.
- Levels: unit; parent at cluster.
- Class and style: a preset carries a `style` tag and class-keyed defaults; "any type" is a new preset, not a new schema.
- Ledger: `x1_preset_id`, `x1_upgrade_offer_policy`.
- Performance: a type ships complete and runs out of the box (R1 §8 point 7). Survival: preset numbers without derivations cannot ship (checker).
- Evidence: Helm, systemd, pysystemtrade (CHECKED or READ); MQL5 18918 modes (author backtest). Weakest link: his own doubt that one shape holds across all variants (third round).
- Maturity: **solid**.

**X1-H17. Packs that stack, with a combiner per slot and a menu of annotated plug-ins.**
- Links: A4-089, A4-066, A4-014, A1-007, A4-068, A4-067.
- Need: TLH 23 (brakes addable, removable, combinable), B6 (versions that take parts of both systems).
- What: a profile is composed of packs (sizing, brake, exit, accelerator, derivation), each a small versioned bundle of blocks, numbers and derivations, with a manifest in the StrategyQuant snippet style (annotated parameters, a display template). Packs stack in a declared order. Where two packs claim one slot the profile names a combiner: `smallest_cap` (sizers and modifiers), `newest_wins` (LEAN risk chain), `all_must_pass` (gates), or refuse. An "old-style" pack and a "Book-style" pack can sit in one profile, which is his B6 hybrid.
- Levels: unit; cluster packs for shared brakes.
- Class and style: a pack declares which classes it supports; a cost pack for `K-cry` carries funding, for `K-fx` swaps.
- Ledger: `x1_pack_order`, `x1_slot_combiner_rule`.
- Performance: trying a hybrid of two sizing structures costs a pack swap, not a rebuild. Survival: the order is shown on the card (A4-089 known failure).
- Evidence: LEAN chaining and StrategyQuant snippets (CHECKED). Weakest link: the combiner semantics for exits are untested.
- Maturity: **plausible**.

**X1-H18. Three parts: facts measured, responses chosen, his limits user-set, with the instrument risk record as the facts object.**
- Links: A4-052, A4-017, A1-162, A1-160, A4-179, A3-084, A1-147, A3-022.
- Need: TLH 8, 9, 17 (units of measure; costs per market, instrument, timeframe and hour).
- What: the template is responses (blocks, derivations, states) that read facts and his limits. The facts object is one **instrument risk record** per (unit, instrument, broker): money per point from the broker's tick value (never pips), lot step and bounds, class and bucket code, the hourly cost profile (spread by hour and session, commission per lot, swap or funding), conversion read live for crosses, the session clock contract (market zone and DST), roll and split rules, calibrated detector thresholds. A missing cost calibration refuses, never zero.
- Levels: trade and unit for the record; account for conversion.
- Class and style: `K-fx` swaps and triple-swap day; `K-cry` funding every eight hours; `K-fut` contract multiplier and roll; `K-idx` cash-session hours; `K-stk` splits and halts. Each is a field, not a special case in code.
- Ledger: `x1_changed_by_class`, `value_per_point`, `price_increment`, `numeraire`, `spread_cost`, `commission_cost`, `swap_financing_cost`, `funding_cost`, `session_windows`, `day_boundary`.
- Performance: costs reach the sizer, so the edge-to-cost gate (A1-138) can run and premium hours can be sized up. Survival: gold sized in pips, or a cross sized on a cached rate, cannot happen.
- Evidence: MQL5 24237 (author backtest), 22187 and 23388 (mechanism); QMB cost ports (built, rates deferred). Weakest link: no article assembles all fields in one record (A1-162).
- Maturity: **solid** for the split, **plausible** for the full record.

**X1-H19. A needs list the host must meet; adding a piece pulls in its statistics with defaults.**
- Links: A4-078, A4-091, A3-183, A4-058.
- Need: G8 B2 (no host computes halt inputs), G8 §3.5 (nothing checks a halt's scope against what it reads).
- What: a profile declares the statistics it reads (`session_loss_r`, `day_start_equity`, `open_risk[bet_key]`, `budget_used`, a context word). The host publishes a `provides` list. Compile is needs ⊆ provides, or a named fallback per need (`compute_here`, `treat_as_absent`, `no_new_entries`, the three the `reads` field already has). Like Bevy's required components, binding a halt inserts the statistics it needs into the guard's job list with defaults, so no halt is ever bound to a scope nobody measures.
- Levels: unit, cluster, portfolio.
- Class and style: a `K-cry` profile needs a funding statistic the guard must provide; a `K-stk` profile needs a halt-state feed.
- Ledger: `x1_needs_list`, `x1_fail_mode`, `session_loss_limit_r`, `day_start_equity`, `losing_day_streak`, `session_fills`.
- Performance: none; it makes brakes real. Survival: a halt cannot be silent by accident.
- Evidence: Bevy (CHECKED); the `reads` fallbacks (built); the `provides` and `feeds` manifest fields (built). Weakest link: none technical.
- Maturity: **solid**.

**X1-H20. The template behind three verbs: `decide`, `on_event`, `state`.**
- Links: A4-090, A4-073, A4-079, A2-017.
- Need: his D34 (design for complexity, not a complex system); TLH 4.
- What: both hosts call `decide(intent, facts) -> SizedIntent | Skip(reason)`, `on_event(event, facts) -> [Halt | Amend | None]` and `state(facts) -> RiskState`. Sizer, halts, exits, derivations, applier and accelerators are implementation behind those verbs with internal slot contracts. The three verbs are also the type boundary agents cannot cross (H55). Deletion test: delete the module and the logic reappears in two hosts and disagrees.
- Levels: unit; the guard exposes the same three verbs at cluster and portfolio scope.
- Class and style: identical.
- Ledger: none new.
- Performance: fix once, fixed in backtest, paper and live. Survival: a host test that needs to reach a slot means the shape is wrong.
- Evidence: every platform's sizer is one small function (R1 pattern 1, CHECKED); `UnitSliceHandler` serves both hosts (built). Weakest link: none.
- Maturity: **solid**.

**X1-H21. A self-test card per profile version, a chassis stress battery, and a PASS or FAIL gate before live.**
- Links: A4-097, A4-186, A4-025, A2-228, A4-083, A5-035.
- Need: D43 ("how do they know that the things are correct?"); TLH 4 (handle any stress); E27.
- What: every profile version carries a card: contract-test results per slot, a sizing-only replay on the unit's own record with money measures (H46), the scenario battery (X4), the ledger check (layer H), the placeholders left, and the shadow comparison (H47). The chassis stress battery is a fixed set of adversarial extensions the schema must absorb in CI without a change: add a brake at a new level, add a level, swap the sizing basis, add a class with a different lot granularity, add a timeframe axis, add an outside block, add an accelerator, add a cluster tag. Statistical passes and portfolio vetoes are separate, each logged with its reason (A5-035).
- Levels: profile; the battery at schema level.
- Class and style: the battery includes one unit per class key and one per style.
- Ledger: `x1_card_required_before_live`, `replay_match_floor`.
- Performance: trying a profile costs seconds of replay, not a backtest. Survival: a profile without a card is a guess with a version number.
- Evidence: `b-build-and-prove` ends on a card (built); MQL5 17956 regression gates (author mechanism); Kayenta's sample rules (CHECKED). Weakest link: the judge is size-blind until money measures are added (G8 B10).
- Maturity: **solid**.

**X1-H22. A trust ladder per block and a minimum trust per slot; his signature before the money path.**
- Links: A4-084, A4-071, A4-082, A4-030, A4-095.
- Need: TLH 32 (external code), D43; G8 B8 (`tested_on_data` and `used_in_unit` computed by nothing).
- What: trust = origin (`qml`, `human`, `agent`, `community`) × evidence (`named`, `specified`, `implemented`, `contract_passed`, `tested_on_data`, `used_in_unit`, `shadowed_live`). The self-test card computes the two missing statuses; shadow rows compute the last. A profile declares the minimum trust per slot; the checker refuses a binding below it. Outside packs follow n8n's community rules (prefix, manifest, no runtime dependencies, contract tests on install, a verified tier); a community or agent block reaches a live profile only with his bound signature on the pin, checked by the loader, as a `money` app needs his signature.
- Levels: block and slot.
- Class and style: a block declares the classes its contract tests cover; a block never tested on `K-cry` cannot fill a crypto slot live.
- Ledger: `x1_min_trust_per_slot`, `x1_pin_signature_required_for_live`.
- Performance: the door he asked for stays open; the ladder, not a ban, decides. Survival: nothing untested sizes money.
- Evidence: n8n community process (CHECKED); the dictionary status ladder (built). Weakest link: the signature check must live in the loader, or an agent draft can bind a landed pack (A4-071 known failure).
- Maturity: **solid**.

**X1-H23. Three faces on every profile, preset and pack; the dictionary as the catalogue.**
- Links: A4-084, A4-069, A4-070.
- Need: D37 (terminology), D33 (dumb it down).
- What: a trader face in plain words ("risk half a percent of the pot to the stop; stop the unit after three full stops in a session"), a machine face (the schema) and a code face (the blocks). Agents write the trader face first; the self-test card proves the faces agree. The `component` kind already has three faces; the profile reuses the shape.
- Levels: all.
- Ledger: none new.
- Performance and survival: none direct; it is how he and agents read the same thing.
- Evidence: the dictionary entry shape (built). Weakest link: proving the faces agree is a test nobody has written.
- Maturity: **plausible**.

**X1-H24. The raw-code hatch, quarantined and never alone at a scope.**
- Links: A4-072, A4-082, A4-030, A4-131.
- Need: TLH 32; the `plain_python` field exists and is ignored (G8 B6).
- What: `plain_python` is read for the risk slots only, after layer F; it runs in shadow for `plain_python_quarantine_trades`, and the checker demands a second, catalogued brake at the same scope so it is never the only brake. Like Steward's core, the hatch can propose but cannot reach the guard's arithmetic.
- Levels: unit.
- Ledger: `x1_plain_python_quarantine_trades`.
- Performance: the escape hatch every catalogue needs. Survival: quarantine plus a catalogued twin.
- Evidence: n8n Code node (CHECKED). Weakest link: shadow cannot see what a raw sizer would have done to fills.
- Maturity: **plausible**.

**X1-H25. Two adapters per slot before a slot counts as extensible.**
- Links: A4-079, A1-007, A1-005.
- Need: TLH 4; G8 §2.2 (contract tests test one sizer, long only).
- What: ship two sizers (fixed fraction at the stop and one more, both behind one shared lot converter so risk policy stays apart from lot rounding), two halts per scope, two derivations per number family, two appliers' modes exercised, before calling the socket extensible. Library blocks enrol in the contract tests; the short side is added.
- Levels: slot.
- Class and style: the contract tests run on one instrument record per class key (lot step 0.01 lots, 1 contract, 0.001 BTC, 1 share).
- Ledger: `x1_adapters_per_slot_min`.
- Evidence: codebase-design rule (one adapter is a hypothetical seam). Weakest link: none.
- Maturity: **solid**.

### C. Where each piece lives

**X1-H26. The money path stays in blocks inside the unit; the guard is node-local with two host adapters.**
- Links: A4-091, A4-074, A4-076, A4-062, A4-036, A4-184.
- Need: G2 rulings 6 and 11 (only the node sends orders; nothing a unit needs may depend on the router, the MIS or the Library at trade time); G9 M2, M12.
- What: sizer, position-scope exits and halts and their numbers are blocks compiled into the unit. One guard package, `qmf-risk/guard`, is instantiated by QMB's `unit_handler` and the node's `runtime`: it computes the statistics the slots read (day-start equity, session loss in R, streaks, fills, open risk per bet key, exposure per class, budget used), runs unit, cluster and portfolio halts, hosts the applier (H03), calls `before_order` (H27), feeds the risk-stop pipe and emits RiskState. It is RiskGate's rule pipeline without the network hop, so it is not a single point of failure. It re-checks every open position on a timer against its rules (MQL5 Engineering Trading Discipline).
- Levels: unit inside the unit; cluster and portfolio inside the guard.
- Class and style: one guard per node serves every class; its statistics are keyed by class and bucket for isolation (H35).
- Ledger: `open_risk_at_stop`, `portfolio_exposure`, `budget_remaining`, `day_start_equity`, `session_loss_limit_r`, `x1_guard_unavailable_action`.
- Performance: backtest equals live for every brake above the position. Survival: units on one account finally know about each other.
- Evidence: the hook and halt slots (built, unused); RiskGate (author build). Weakest link: a new package with two adapters is the biggest build item in this layer.
- Maturity: **solid**.

**X1-H27. `before_order` answers pass, shrink or refuse with a closed list of reason codes.**
- Links: A4-091, A4-064, A2-066, A5-035, A4-155.
- Need: G8 B2 (the hook passes every order); his C7.
- What: the cross-unit hook becomes the guard's `before_order(intent, open_positions, facts)`, the only seam where cluster and portfolio rules touch one order. It answers `pass`, `shrink{to, reason}` or `refuse{reason}` with reasons in `CATEGORY_CONDITION` form (Nautilus). Every refusal is counted by reason with the right denominator so refusals do not read as decay; vetoes (budget, exposure, isolation, correlation) are logged on their own.
- Levels: cluster, portfolio, account.
- Class and style: identical; the reason list includes class-scoped codes (`ISOLATION_CLASS_OFF`).
- Ledger: `x1_hook_answer_kinds`, `exit_reason_code`.
- Performance: a shrink keeps the trade instead of refusing it. Survival: one seam, two adapters, every answer journalled.
- Evidence: Nautilus denial codes (CHECKED). Weakest link: `runtime.py:1010-1013` and `unit_handler.py` must call it (code change).
- Maturity: **solid**.

**X1-H28. The node's fast lane feeds the template as facts; a brake may raise a stand-down, never lower the kill switch.**
- Links: A4-193, A4-176, A3-106.
- Need: his C21 (kill switch and SQS stay); STATE "the kill switch only goes down by his hand".
- What: kill level per scope, SQS state per market, stand-down scopes, feed state and clock drift are facts in `RiskState`. Derivations may size down on them; a brake may raise a stand-down through the risk-stop pipe. Order of authority: his approved configuration, then deterministic risk and the kill switch, then execution, then agents' advice. The scope key set grows with `class:`, `region:`, `currency:` and an underlying group beside `instrument:` so isolation and the kill switch share one vocabulary.
- Levels: node and account.
- Class and style: `K-cry` has its own SQS baseline (funding and 24/7); `K-stk` reads venue halts as a stand-down.
- Ledger: `x1_scope_key_set`, `kill_switch_level`, `kill_switch_scope`, `sqs_score`.
- Evidence: kill switch and stand-downs (built); the flatten that does nothing (G9 §1.1, a fix). Weakest link: no automatic trigger of any kill level exists (G9 M3), and this hybrid keeps it that way for the kill switch.
- Maturity: **solid**.

**X1-H29. A Risk Lab mini app around the template: resizer, scenarios, preset editing, derivation preview, ledger browser.**
- Links: A4-094, A4-095, A4-186, A4-181, A4-049.
- Need: B14 ("combine a mini app together with the risk and sizing system"); TLH 5, 44.
- What: an app with `risk = runs` ships the tooling: `resize_replay` (QuantAnalyzer's money-management simulation on a trade list), `scenario_run`, `profile_check`, `derivation_preview` (StrategyQuant's `display`), a ledger browser, and the skills `build-risk-profile` and `explain-size`. Its lander lands `risk-profile`, `template`, `component` and cluster drafts for his yes. It never sits in the order path; the node reads only what the host compiled.
- Levels: all, off the money path.
- Ledger: `x1_risk_app_jobs`.
- Performance: trying a profile is a job, not a build. Survival: `runs`, never `money`.
- Evidence: the MIS proves an app runs QML blocks by entry id (built); QuantAnalyzer (CHECKED). Weakest link: an app cannot land risk kinds today (G8 §6.4).
- Maturity: **plausible**.

**X1-H30. The pod as a shippable bundle: a cluster document, its packs, presets, agents, skills and a card, installed by landing Library items.**
- Links: A4-094, A4-095, A4-071, A4-096.
- Need: B14 ("how do we ship pods?"); D35.
- What: a pod is a signed bundle (a mini app whose `provides` lands Library items): one cluster document (H40), the packs its units use, the presets its units start from, the agents and skills that propose changes, and a self-test card. It installs into the Library; nothing in it reaches the node except what the host compiles from landed, checked items with his yes.
- Levels: cluster.
- Ledger: `x1_pod_bundle_contents`.
- Evidence: the app road and manifest (built). Weakest link: "pod" has two meanings for him (Q1).
- Maturity: **plausible**.

**X1-H31. The same compiled unit and guard run on his PC and on the node; the PC is home, the node substitutes.**
- Links: A4-184, A4-036, A4-098, A4-035.
- Need: his C23; memory ruling "PC is home, servers substitute".
- What: the profile carries `runs_on`; the ledger snapshot and the status travel with it. The learner (H02) may run on the PC over the home journal; the applier (H03) runs where the unit trades, so `at_flat` is decided next to the order path. A paper twin on the PC runs the same signals and code with a per-trade gap row.
- Levels: unit, node.
- Ledger: `x1_runs_on`, `x1_ledger_snapshot_in_compiled_unit`.
- Evidence: one code path for demo and live (built). Weakest link: none specific.
- Maturity: **plausible**.

**X1-H32. The budget share travels with the deployment, as a compartment of open risk.**
- Links: A1-130, A4-036, A4-188, A4-029.
- Need: G8 B11 (no limits or budget share exist; every unit sizes from the whole account); G9 §3.1 (paper sizes from $10,000).
- What: each deployment carries `unit_capital_share` and a compartment (bulkhead) of open risk; the sizer reads them in every lane, so paper sizes from the unit's live share, not the demo balance. A newly promoted unit starts at a starter share and is raised in stages on live net evidence (H47). Shares are refreshed by the portfolio document, never by the unit.
- Levels: unit and portfolio.
- Class and style: compartments in R for all; `K-cry` margin per compartment checked against liquidation distance.
- Ledger: `unit_capital_share`, `x1_starter_budget_share`, `paper_starting_balance`, `sizing_equity_basis`.
- Performance: a unit's growth compounds on its own share. Survival: one unit cannot use the whole account's room.
- Evidence: bulkhead and Netflix shares (CHECKED). Weakest link: stale shares if not refreshed (A1-130).
- Maturity: **solid**.

**X1-H33. One compile target for the Book level: the Lab's seven-slot pod compiles to the same cluster and portfolio documents.**
- Links: A4-096, A4-092, A4-088, A4-091.
- Need: STATE item 31 (the Lab must use the template without rework); Collision 5 of the draft.
- What: the Lab's pod (inputs, guards, allocator, sizer, throttles, caps, ledger) stays a design for composing; its `PodCompilerPort` emits the documents of H15 and H40, which the guard compiles. One target, two producers (a person or agent writing documents; the Lab composing them). The Lab's allocator writes `unit_capital_share` proposals through the proposal door (H53), never into the guard.
- Levels: cluster, portfolio.
- Ledger: none new.
- Evidence: the Lab spine (designed, unbuilt). Weakest link: unbuilt on both sides.
- Maturity: **plausible**.

### D. Levels and how they compose

**X1-H34. A level and a scope key on every number, brake and state; tag scopes overlap and the strictest answer wins.**
- Links: A4-093, A3-106, A4-048, A4-044.
- Need: his B1 (unit, cluster, methodology, portfolio with intersections); G11 §1.4 (no Gen 4 row has a level).
- What: `level ∈ {trade, position, unit, cluster, methodology, portfolio, account, node}` and a `scope_key` the host resolves. A rule bound to a tag (`methodology: mean-reversion`, `class: crypto`, `driver: usd`) applies to every unit carrying it, across clusters. The guard resolves every active scope for an intent, collects every answer, applies `min(size)` and `max(state)`, and journals which scope bound.
- Levels: all.
- Class and style: class and region are tags like any other, so "everything off for crypto" (C27) is one rule at one tag.
- Ledger: `x1_scope_overlap_rule`, `x1_scope_key_set`, `isolation_scope`.
- Evidence: the identity table's "highest label wins" (built); CSS (CHECKED). Weakest link: strictest-wins stacks caution (A4-093 known failure).
- Maturity: **solid**.

**X1-H35. Down the levels as caps and states; up the levels as events.**
- Links: A4-077, A1-086, A4-058, A4-018.
- Need: G2 ruling 25 (simple at the core); R1 §5.3 limit hierarchies.
- What: a higher level never calls a lower level's code. It publishes constraints the lower level reads as facts: a budget share, a max open risk, a trading state, a halt flag. A lower level reaches up only by events it journals (trade closed, brake fired, guard refused, number moved). The guard aggregates events into the higher level's statistics. Every ledger `affects` edge is typed `down:cap`, `down:state` or `up:event`. A stale broadcast is handled by the lower level's declared fail mode, never by a timer that authorises on old state (MQL5 23629's failure).
- Levels: all.
- Ledger: `x1_coupling_direction`, `budget_remaining`, `decision_freshness_bound`.
- Evidence: RiskMetrics hierarchies (live, banks); 23629 (no test). Weakest link: 23629's degraded mode is the anti-pattern; the fail mode is the fix.
- Maturity: **solid**.

**X1-H36. The cascade: most specific wins for normal values; outer limits marked important win from outside in; the account is the policy top; children may only tighten caps.**
- Links: A4-044, A4-043, A4-045, A1-164, A4-049.
- Need: his C10 and C11 (the floor is his; the BMS keeps a buffer); TLH 8.
- What: normal values resolve preset → cluster → unit (most specific wins). A cap marked `important` at an outer level (portfolio, account) cannot be loosened by anything inside it; a child may tighten it. Numbered priorities (Nix) make "who wins" checkable. A `lock_lower_overrides` switch on a value forbids lower levels from touching it. An inspector prints which level set every value (ESLint `--inspect-config`, H52).
- Levels: all.
- Ledger: `x1_limit_importance`, `x1_settable_by_levels`, `x1_override_priority`, `x1_lock_lower_overrides`.
- Evidence: CSS, VS Code, Nix, ESLint (CHECKED); conv-01's tighten-only children (idea). Weakest link: many `important` flags make the cascade hard to read.
- Maturity: **solid**.

**X1-H37. The override chain with buckets, timeframe and session axes, expiring event overrides, evidence records and diffs.**
- Links: A4-050, A4-051, A1-163, A4-195, A4-185, A3-031, A4-057, A4-039.
- Need: D51 (variables grew with every class, style and timeframe); TLH 53; R3 §5.8.
- What: `preset → style → class → bucket → instrument → venue account → unit → market → timeframe → session → event`, later wins, with a residual bucket for anything unclassified (ISDA SIMM) and a class code per instrument (ISO 10962 style). Event overrides expire and may only tighten. An instrument or session earns its own override only on forward evidence (effective trades across sessions and volatility conditions), and every override stores its evidence window, sample, last update and expiry. A unit stores only diffs from its resolved chain; when a default improves, untouched units get an offer card, never a silent change; lineage records which preset and version a unit forked from.
- Levels: unit, with class and bucket rows at system level.
- Class and style: the chain is the one place class and style differ; `K-cry` buckets by venue and funding regime, `K-fut` by contract, `K-stk` by size and sector.
- Ledger: `x1_override_chain_order`, `x1_instrument_bucket`, `x1_event_override_expiry`, `x1_override_evidence_record`, `x1_upgrade_offer_policy`, `x1_template_lineage`, `instrument_class`, `session_windows`.
- Performance: one rule gives a tradable size in every class; an instrument that earns an override keeps it. Survival: no override without evidence; no silent template change (Home Assistant's failure).
- Evidence: SIMM and CFI (READ, production); n8n diff storage (CHECKED); chat-17 governance (assistant's proposal). Weakest link: the override thresholds are governance numbers, not statistics.
- Maturity: **solid** for the chain, **plausible** for the evidence rule.

**X1-H38. Same bet counted once, compartments per unit, and a parent limit below the sum of its children, with breadth spreading a fixed total.**
- Links: A1-115, A1-086, A4-188, A5-003, A1-165, A3-030.
- Need: B15 (preventing losing all at once); C29 (frequency; each unit keeps its size until the total binds); G11 §2.2 (no cross-unit exposure measure).
- What: the guard assigns every open position a bet key (underlying, currency legs, class, direction, driver, window) and caps open risk per key, per class and per account. The portfolio declares an aggregate limit = factor × Σ cluster limits, the factor measured from joint losses (stressed correlation when available). Breadth spreads a fixed total set by survival limits; it never raises it; it is recomputed on two clocks (daily risk, weekly allocation). Two positions in a session overlap are not a contradiction; they are related only through the same-bet check.
- Levels: portfolio, cluster.
- Class and style: `K-fx` keys on currency legs; `K-idx` and `K-stk` on equity beta and region; `K-cry` on BTC beta; `K-fut` on the underlying across contracts.
- Ledger: `x1_bet_key_rule`, `x1_aggregate_limit_factor`, `cluster_exposure_cap`, `open_risk_ceiling`, `effective_independent_bets`, `unit_result_correlation`.
- Performance: ten units keep their size until the total binds; this is the professional answer to his C29. Survival: the co-loss factor rises in stress, exactly when it matters (A1-086 known failure), so the factor reads stressed correlation.
- Evidence: RiskMetrics (live, banks); bet keys and breadth (ideas). Weakest link: keys miss shared exposure nobody declared.
- Maturity: **plausible**.

**X1-H39. Drawdown by level: one hard floor on the portfolio, caps on driver clusters, only a soft overlay per unit; two anchors.**
- Links: A5-009, A5-010, A4-061, A4-059.
- Need: his C10 (the floor almost never touched; the BMS keeps a buffer); C12 (how the next day starts).
- What: the non-negotiable floor sits once, on combined marked portfolio equity, with a high-water mark that survives unit additions, removals and reallocations; caps sit on clusters sharing a driver; a unit has a working drawdown anchor that may restart after a near-breach, while the portfolio floor and high-water mark never reset by a restart, a payout or a re-seed (Hsieh's 20.18 % against a 20 % cap). The day baseline is computed, confirmed when he wants, persisted and restored across restarts.
- Levels: portfolio, cluster, unit.
- Class and style: `K-cry` marked equity includes unrealised funding; `K-fut` marked equity uses settlement.
- Ledger: `x1_unit_working_anchor`, `x1_day_baseline_confirmation`, `high_water_mark_equity`, `portfolio_floor`, `bms_buffer_before_floor`, `kill_line_floor`.
- Performance: units keep trading through their own small drawdowns; the floor is a portfolio fact. Survival: a restart cannot void the cap.
- Evidence: Hsieh drawdown modulation (READ); chat-04 design (assistant's). Weakest link: margin call before the rule acts.
- Maturity: **plausible**.

**X1-H40. Restructure: replace the Book and BMS containers with three documents: profile, cluster tags, portfolio guard config.**
- Links: A4-092, A4-096, A5-009, A4-048, A4-093, A4-103, A4-077, A1-086.
- Need: nothing is off limits (M31); his B1 (levels with intersections); B3 (the Book is the skeleton, but "it's just cleaner"); C26 (self-optimising at the BMS).
- What: the Book as a container of units goes. In its place: (1) the **unit profile** (H15); (2) **clusters as tags**, not folders: a cluster document is a drop-in applied to every unit carrying its tag (style, methodology, class, region, driver), holding shared caps, counting rules, a pooling group, a shed priority and brakes at cluster scope; a unit may be in many clusters at once, which the Book could not express; (3) the **portfolio guard config**: the one hard floor, the buffer, the high-water mark, the aggregate limit and co-loss factor, the bet-key rule, the isolation protocol with its scope keys, the slot policy, the rank table and the never-self-tune list. The guard compiles the three into its runtime config. The word "Book" can stay on screen for the style cluster if he wants it (Q1).
- Why it performs better: clusters by driver catch co-loss that a Book-by-style never saw (A5-009); the floor is computed once, so two Books cannot each keep a buffer that adds up to idle money (his C11); self-optimising at the portfolio becomes a document edit through the proposal door instead of his hand (C26).
- Levels: unit, cluster, portfolio.
- Class and style: a class is a cluster tag, so class isolation and class defaults are the same mechanism.
- Ledger: `x1_cluster_tag_set`, `x1_shed_priority_class`, `x1_aggregate_limit_factor`, `x1_bet_key_rule`, `control_rank_table`, `unit_capital_share`.
- Performance: see above. Survival: one floor, one high-water mark, no container boundary to hide exposure behind.
- Evidence: systemd type drop-ins, SIMM buckets (CHECKED, READ); chat-04 (assistant). Weakest link: no QMX generation ran a tag-based cluster; it is a design.
- Maturity: **plausible**; a restructure proposal (section 4).

**X1-H41. Shed by declared priority when a budget tightens; burn-rate tiers per level; freeze versions when a budget is spent.**
- Links: A4-189, A4-032, A4-033, A4-200, A4-029.
- Need: his C26 (the BMS reduces scalpers or opens slots); TLH 29.
- What: every unit carries a shed class (probation, paper-graduate, proven, core; four is enough, as in Google's load shedding). When a cluster or portfolio budget tightens, the guard sheds from the bottom class first instead of cutting everyone pro rata. Each level's loss budget has burn-rate tiers over two windows (fast burn → REDUCING or HALTED at that level; slow burn → size down; slower → a review card). A unit whose budget is spent cannot receive a new risk version until it recovers (error-budget policy), and one incident over a declared share of the budget requires a postmortem card.
- Levels: cluster, portfolio.
- Class and style: `S-sc` budgets in trades-per-day windows; `S-sw` in weeks.
- Ledger: `x1_shed_priority_class`, `x1_budget_burn_rate`, `x1_version_freeze_on_spent_budget`, `period_loss_budget`, `loss_runway`.
- Performance: proven units keep their size while probation units carry the cut. Survival: a fast burn is caught in the short window.
- Evidence: SRE workbook (CHECKED, production practice). Weakest link: budgets in calendar windows are unfair to low-frequency units (A4-029).
- Maturity: **plausible**.

**X1-H42. Methodology and cluster drop-ins, applied in order, beneath the unit's own.**
- Links: A4-048, A4-093, A4-044, A4-060.
- Need: his B1 (methodology level); TLH 30.
- What: a cluster document is a drop-in: it applies to every unit tagged, in lexicographic order, beneath the unit's own settings, except values marked important, which it imposes. An explicit reset of a list (halts) must be a declared action, never an empty parent (the nested-settings trap).
- Levels: cluster, methodology.
- Ledger: `x1_methodology_drop_in`.
- Evidence: systemd (CHECKED). Weakest link: an explicit reset can silently remove a brake list a methodology meant to impose.
- Maturity: **plausible**.

### E. Versions and rollout

**X1-H43. Pinned profile versions, a migration map between block versions, and identity labels for profile changes.**
- Links: A4-037, A4-038, A4-041, A4-040, A4-102.
- Need: G8 B9 (the rip-out costs each unit its record); n8n `typeVersion` pinning.
- What: a unit version pins its profile version and fingerprint; a new profile version sits beside the old one; units move by his click, at the next flat. A forwarding map (old block id and version → new, with a parameter transform) lets `fixed-fraction-at-stop@1` → a real sizer be a declared migration. The identity table gains `profile_version_change` (new version, counted try, his click) and `profile_swap` (new unit), both his rows to edit. The snapshot rule exempts profile-only changes from cold-starting logic block state; the profile's own state starts cold.
- Levels: unit.
- Ledger: `x1_profile_version_pin`, `x1_adopt_at_next_flat`, `x1_block_migration_map`, `x1_identity_profile_version_change`, `state_carry_rule`, `effective_tries`.
- Performance: a sizer swap keeps the evidence QMB and paper earned. Survival: no silent change on the money path.
- Evidence: n8n versioning and Simulink forwarding tables (CHECKED); the identity table (built). Weakest link: broken links cannot be upgraded through the table (snippet), and the label change needs his ruling (Q2).
- Maturity: **solid**.

**X1-H44. Two records: a logic record in R across versions, a money record per profile version.**
- Links: A4-042, A4-186, A4-025.
- Need: same as H43, without a ruling.
- What: the judge is size-blind, so a profile change cannot change a verdict. The logic record (R) continues across profile versions; a new money record (dollars, drawdown, budget used, brake fires) starts per profile version. Both show on the card; the sizing-only replay fills the money record from history so a new version is not blank.
- Levels: unit.
- Ledger: `x1_money_record_scope`, `original_risk_r`, `expectancy_r`.
- Evidence: the judge (built). Weakest link: two numbers on one card invite "which is real" (both are, for different questions).
- Maturity: **solid**.

**X1-H45. Shadow, then canary, then full: a rollout with three outcomes, judged against a fresh baseline running at the same time, with motion frozen while judging.**
- Links: A4-023, A4-024, A4-025, A4-026, A4-030, A4-035, A4-121, A4-003.
- Need: STATE "versions roll out (canary, shadow, side by side) without wiping a unit's record"; TLH 28.
- What: a new profile version runs: (1) **shadow** for `shadow_trades_before_live`: the old profile sizes, the new one is journalled as `would_have`; (2) **canary**: a declared share of the unit's markets or size runs the new profile live while the old profile runs the rest as the control, started at the same time; (3) an **analysis template** (metrics, cadence, critical metrics, no-data rule) ends `pass` (next step), `fail` (roll back to the pinned version), or `inconclusive` (pause for his card); Promote's anytime-valid test can be the template's statistic. Time to promote and time to roll back are declared numbers. The motion engine is frozen on both arms while judging, so two effects are not mixed. Fail is never retried on the same version.
- Levels: unit; cluster versions roll out the same way across their units with a share cap.
- Class and style: a canary across markets suits `K-fx` and `K-cry` (many markets per unit); a single-market `K-stk` unit canaries by size share instead.
- Ledger: `x1_shadow_trades_before_live`, `x1_canary_share`, `x1_rollout_share_steps`, `x1_analysis_outcome`, `x1_rollout_time_to_promote`, `x1_rollout_time_to_rollback`, `size_ramp_to_full`.
- Performance: a better version earns full share on fresh evidence instead of waiting for a new backtest. Survival: the canary's loss is bounded by its share; inconclusive pauses rather than guesses.
- Evidence: Argo Rollouts, Flagger, Kayenta (CHECKED, production); Promote (paper, controlled test). Weakest link: a second deployment of one unit version on another market is refused today (G9 §3.2), so the market canary needs a host change.
- Maturity: **plausible**.

**X1-H46. A plan before any change, refused if stale; approval bound to the effect it approves.**
- Links: A4-021, A5-055, A4-120, A4-041.
- Need: his D41 ("I click and stuff"); STATE "only he promotes".
- What: an agent's edit to a profile produces a plan: the identity-table result, whether the record survives, which numbers move and by how much, the rollout steps. The card is rendered from a canonical effect descriptor (artifact hash, base version, instruments, account scope, risk envelope, expiry); his click signs that descriptor; apply executes the stored effect and refuses if the unit's fingerprint moved since the plan or the descriptor expired. Flooding is capped per night.
- Levels: all.
- Ledger: `x1_plan_staleness_check`, `x1_approval_effect_digest`, `x1_card_flood_cap`.
- Evidence: Terraform (CHECKED); "Approve What, Exactly?" and AllPath (papers, controlled test). Weakest link: a person who approves without reading (A5-055).
- Maturity: **solid**.

**X1-H47. Upgrade offers, never silent; declared retry rules.**
- Links: A4-057, A4-039, A4-022.
- Need: E2 ("nothing is set in stone") with A13 (every change has a reason).
- What: when a preset or class default improves, untouched units get an offer card (`adopt_default`), optionally auto-adopted in shadow; never a silent change. A failed deploy of a version is not retried until a new version exists; automation and manual rollback cannot both drive one unit.
- Levels: unit.
- Ledger: `x1_upgrade_offer_policy`, `x1_deploy_retry_rule`.
- Evidence: n8n diff storage, Home Assistant warning, Argo CD (CHECKED). Weakest link: none.
- Maturity: **solid**.

**X1-H48. A few pre-approved profile versions as arms of a conservative bandit, with the default as the baseline arm.**
- Links: A4-199, A4-198, A5-162, A4-041, A4-007.
- Need: TLH 1 (improvable in any way); chat-17's "conservative parameter tuning" workflow.
- What: offline tuning (plateau-seeking, cost-stressed, locked before forward test) proposes two or three stable profile versions; he approves the set once; live, a conservative bandit switches among them only when a lower confidence bound keeps cumulative result above a baseline-relative floor, with stale rewards discounted. A switch is a calibration row, not a version, if the set was approved as one (identity question, Q5).
- Levels: unit.
- Ledger: `x1_approved_config_set`, `number_motion_mode`, `grow_back_rule`.
- Performance: the unit picks the better of a few approved configurations as the regime moves. Survival: the baseline arm is always available; the floor is relative to it.
- Evidence: Conservative Bandits, Rotting Bandits (papers); no trading test in the sources. Weakest link: nonstationary markets break the guarantees.
- Maturity: **wild** (kept).

### F. Agents and MCPs: a read door and a proposal door, never the order path

**X1-H49. The read door: `RiskState` every pass, `risk_explain` for any number, ledger rows by id, over tool rows and MCP.**
- Links: A4-152, A4-049, A4-146, A4-135, A4-020, A4-069.
- Need: STATE item 30 (the template exposes read access to risk state); D49 (how do we know it is working); TLH 51.
- What: a `risk_state` journal row per unit, cluster and portfolio every pass: equity series and base, drawdown, open risk, exposure per bet key, budget used, each brake's state and distance to trip, the trading state per scope, the last derivation receipts, the kill level now, the applier's pending recommendations, and `status_generation`. Tool rows `risk_state(node, scope)`, `risk_profile_explain(unit, number)` (the chain with the winning level, the receipt and the ledger row), `risk_ledger_query(id)`, `risk_placeholders_list(unit)`. The same rows are exposed as MCP tools (read only) so an outside agent, the copilot or the future department reads one door. The UI's Numbers tab and the watcher read the same rows.
- Levels: all.
- Class and style: identical.
- Ledger: `x1_risk_state_emit_interval`, `x1_status_generation`.
- Performance: agents propose from live facts, so proposals are feasible from the start (SwingGuard). Survival: read only; nothing here can act.
- Evidence: node health telemetry (built, health not risk); SwingGuard (author backtest). Weakest link: MCP transport and auth are the build session's (QMA flag, not designed here).
- Maturity: **solid**.

**X1-H50. The proposal door: typed, expiring, evidence-carrying proposals into the guard; tightening may apply within bounds, loosening needs his click.**
- Links: A4-104, A5-070, A4-131, A4-176, A4-197, A4-133.
- Need: TLH 34 (agents propose; he clicks); G2 ruling 5 (agents never touch money); his C27 (isolation "with evidence").
- What: an agent, a workflow, the Lab's allocator or an MCP client submits a **proposal**: scope (unit, cluster, class, region), the lever (size cap, state, isolation, a number's value), direction, an expiry, the evidence record (source, availability time, confidence, permitted use) and a reason. The guard validates it against the ledger (level, measure, bounds), then: a proposal that only tightens, inside the scope's bounds and the never-self-tune list, may apply at once in the scope's authority mode and expires on its own; a proposal that loosens, widens scope, or touches a user row becomes a card for his click. No proposal can lower the kill switch. Every proposal and its fate is journalled. This is the "market isolation protocol kicks in with evidence" of C27 without an agent ever sending an order.
- Levels: all.
- Class and style: class and region proposals use the scope keys of H28; a news proposal for `K-fx` names both currency legs.
- Ledger: `x1_proposal_direction_allowed`, `x1_proposal_expiry`, `x1_proposal_evidence_record`, `isolation_scope`, `market_isolation_trigger`.
- Performance: agent evidence reaches the risk layer in minutes instead of a nightly card. Survival: tighten-only automation; the code core sizes; expiry stops stale narratives (A5-070 known failure).
- Evidence: Steward and SwingGuard (author backtests on paper accounts); MarketSenseAI records (author backtest). Weakest link: a tightening-only path can ratchet a good unit down with no automatic way back except the expiry and the restore state (A4-197; Collision 19).
- Maturity: **plausible**.

**X1-H51. The propose, shadow, card, click loop and the nightly `rp-` workflows, with a flood cap.**
- Links: A4-147, A4-030, A4-021, A4-145, A4-156.
- Need: D41, D42; TLH 54 (agents solve issues with workflows).
- What: an agent drafts a profile version; the engine runs the self-test card and the resize replay; the version shadows live; a card lands with the plan (H46); he clicks; the node adopts at the next flat. Workflows: `rp-profile-proposal` (nightly: reads decay, drift and brake density; proposes one tighten or one restore step), `rp-upgrade-offer`, `rp-scenario-battery` (on every draft), `rp-brake-precision` (each brake's share of fires that needed action; a noisy brake is a defect). Cards are capped per night and grouped by root cause.
- Levels: unit, cluster.
- Ledger: `x1_card_flood_cap`, `brake_precision`.
- Evidence: `dc-decay`'s tighten-only cards (built); `p1` and `pp` templates wait for this session. Weakest link: one card per night per unit across forty units floods him (A4-147).
- Maturity: **solid**.

**X1-H52. The Steward boundary: the guard and the three verbs are a code core no agent edit can reach at the type level.**
- Links: A2-017, A4-131, A4-111, A4-082, A4-109.
- Need: G2 ruling 5; handoff "the boundary that must hold".
- What: agents compose only registry-validated typed tools (proposal, draft, read); the guard, the applier and the slot arithmetic are a package no tool imports or edits; layer F denies clock, file and network to agent blocks; a feasibility projection (OpenPM style) maps any proposal onto the bounds before it is applied, so no vote and no prompt can produce an infeasible size.
- Levels: all.
- Ledger: none new.
- Evidence: Steward (paper account forward run); OpenPM (paper). Weakest link: safety is not correctness; a wrong but safe proposal still needs the shadow step.
- Maturity: **solid**.

**X1-H53. Tool rows agents need, as drafts only.**
- Links: A4-146, A4-186, A4-097, A4-049.
- Need: G8 B8 (agents cannot finish a new risk block); D42 ("you need to build them tools").
- What: `risk_profile_new(preset, overrides)`, `risk_profile_check(document)`, `risk_profile_explain(document, number)`, `risk_resize_replay(trades, profile)`, `risk_scenarios_run(profile, scenario_set)`, `risk_propose(scope, lever, direction, expiry, evidence)` (H50), `blocks_save(entry, source)` (a draft for his yes), `blocks_contract(entry)` (the slot contract on a Library block), `derivation_preview(profile, number)`, plus the reads of H49. All write drafts or proposals; none publishes, promotes, lowers a kill level or sends an order. The `build-unit` skill gets a sibling `build-risk-profile`.
- Levels: all.
- Ledger: `x1_agent_tool_rows`.
- Evidence: the catalog and functions (built). Weakest link: none.
- Maturity: **solid**.

**X1-H54. A read-only explainer: "explain this size" in ten words, incidents narrated, never a verdict.**
- Links: A4-135, A4-049, A4-164.
- Need: D33 ("dumb it down for me"); G11 §4.2 (why a unit is not trading in ten words).
- What: a copilot skill over `risk_profile_explain` and `journal_query` walks the receipts and the chain and says it short, with the long form a click away; a narrator drafts incident timelines and postmortems; neither trips or clears anything.
- Levels: all.
- Ledger: none new.
- Evidence: chat-19 risk narrator (assistant's design). Weakest link: none.
- Maturity: **solid**.

**X1-H55. The agent department plugs into the same two doors; a shepherd is one more client.**
- Links: A4-128, A4-124, A4-127, handoff file.
- Need: STATE item 30 and 31 (the department plugs in later without touching the money path).
- What: shepherds, workers and the knowledge base (QMA, not designed here) use H49 to read and H50 and H53 to propose and draft; an agent profile's contract lists the context it must not receive; tools, skills and memories have their own promotion gates. Nothing in the department holds broker credentials. **QMA flag**: the shepherd and memory are the agent system's; this layer only promises the two doors stay stable.
- Levels: all.
- Evidence: Shepherd paper (idea). Weakest link: none of it exists.
- Maturity: **plausible**.

### G. What must change in the shipped stack

Each is a concrete change at d02af358. Most come from G8 "What blocks it today" and G9 "What is missing"; the links say which hybrids need it.

**X1-H56. Compiler format 2.** Run halts and reads; add the `derivation`, `applier` and `combiner` component types; let a sizer-bound number move through a derivation; resolve the override chain and write resolved values with their path into the compiled unit; refuse unknown fields; read `markets[].settings`, `sessions`, `position_limit`, `plain_python` (risk slots), `authority`, `applies_to_open_positions` and `cadence.at`, or remove them (P12). `compiler.py:496-499`. Links: A4-081, A4-047, A4-080, A4-054. Needs: H02, H03, H08, H15, H19, H37. **Solid.** Ledger: `x1_compiler_format`.

**X1-H57. The guard, built as one package with two host adapters.** Computes the halt inputs, open risk per bet key, exposure per class, budget used; runs cluster and portfolio halts; hosts the applier; calls `before_order`; feeds `Runtime.risk_stop` (called only by tests today); emits `RiskState`. Consumed by `qmb/host/unit_handler.py` and `qmn/app/runtime.py`. Links: A4-091. Needs: H03, H26, H27, H34-H41, H49. **Solid.**

**X1-H58. The sizer's inputs widened and its receipt made real.** Balance, marked equity, open risk, the unit's own record with full costs in R, the cost profile for this hour, conversion, his limits, the budget share, the trading state, the applier's current values with reason codes; one unit-scope state beside the per-market instance. `protocol/unit.py:799-802`. Links: A4-073, A4-086, A1-130, A1-162. Needs: H07, H18, H32. **Solid.** Ledger: `x1_sizer_inputs`.

**X1-H59. Trade rows carry the exit reason and mechanism, session, streak, equity before, costs in R, excursions and stage.** The Library `trade` kind has the fields; the journal row does not. Links: A2-260, A4-150. Needs: H14 (counting rules), H37 (session axis). **Solid.**

**X1-H60. Exits after entry run; stops tighten, never widen; partial closes and amendments are sent.** Links: A2-259, A4-086. Needs: H10 (REDUCING amend-only). **Solid.**

**X1-H61. Closed reason codes on the node, the risk stop no longer filed as a kill switch, node constants as ledger rows with `changed_by: user`, and `class:`, `region:`, `currency:` scope keys in the kill switch and the stand-down table.** Links: A4-154, A3-106, A4-193, A4-064. Needs: H12 (brake density), H28, H34. **Solid.** Ledger: `x1_node_constants_to_rows`, `x1_scope_key_set`.

**X1-H62. The Library kinds filled: `risk-profile` (new), `template`, `cluster` (replacing `book`), `portfolio` (replacing `bms`), each with a schema, a checker and an upgrader; a lander for them from a `runs` app.** Links: A4-087, A4-095, A4-088. Needs: H15, H16, H29, H30, H40. **Plausible.**

**X1-H63. Facts produced.** cTrader equity that refreshes; a commission key on the instrument record; a writer of the hourly cost profile from bar and order rows; a slippage script over node order rows; the paper lane models slippage. Links: A3-084, A1-147, A4-167, A4-168. Needs: H18. **Solid**; owned with X2 and X6.

**X1-H64. Agent rows and the socket contract on Library blocks; the identity labels for profile changes; the `would_have`, `risk_event` and `guard` bodies filled.** Links: A4-146, A4-079, A4-041, A4-030. Needs: H12, H22, H43, H53. **Solid.**

**X1-H65. Layer H: the risk-couplings check.** Every number id exists in the ledger snapshot; its level and measure match; every need is provided or has a fallback; every `affects` edge is honoured; no `user` row is self-derived; the minimum trust per slot holds; the rank table has no blank cell; the never-self-tune list covers every `user` row. `check/layer_h.py`. Links: A4-083, A4-099. Needs: H06, H14, H19, H22. **Solid.** Ledger: `x1_layer_h_rules`.

### H. How the pieces become QML dictionary entries and blocks

**X1-H66. The component catalogue maps onto dictionary entries in the A11 and A12 format; the brake registry row is the machine face.**
- Links: A4-084, A5-106, A4-069, R9 §0.3 taxonomy, A1-007.
- Need: M38 (QML dictionary expansion is a downstream deliverable); D37.
- What: after the funnel, each chosen sizer, brake, accelerator, restore, derivation, applier mode, combiner, cost model and reading becomes a dictionary entry with three faces; the nine attributes plus counting rule, fail mode and equity base are the machine face; the status ladder is computed from the self-test card and shadow rows; the taxonomy's kinds (taper, step ladder, trip, throttle, isolation, gate, demotion, flatten, streak attenuator; cushion leverage, profit-funded boost, evidence step-up, conviction add, environment boost, persistence press, evidence-relaxed shrinkage, capital injection; probe, memory ceiling, budget-burn permit, coupled pair) become entry families, so a new brake is filed under a kind before it is coded. The settings schema beside each block generates its form (n8n `properties`), and the ledger generates the Numbers tab.
- Levels: all.
- Ledger: `x1_dictionary_family`.
- Evidence: the dictionary (built); R9 taxonomy (first principles). Weakest link: `tested_on_data` and `used_in_unit` are computed by nothing until H21 lands.
- Maturity: **solid**.

**X1-H67. New block roles with slot contracts: `derivation`, `applier_mode`, `guard_statistic`, `combiner`, `restore`, `proposal_validator`.**
- Links: A4-054, A4-002, A4-078, A4-014, A4-191, A4-104, A4-079.
- Need: TLH 35 (QML's role; the lead may add to QML).
- What: each new role gets a protocol in `api.py`, a contract test, two stdlib adapters (H25) and a dictionary family. A `guard_statistic` block computes one statistic the needs list can name; a `combiner` resolves several opinions on one slot; a `restore` block implements the half-open phase; a `proposal_validator` checks a proposal against the ledger snapshot.
- Levels: block.
- Ledger: none new.
- Evidence: the four slot protocols (built). Weakest link: none.
- Maturity: **plausible**.

**X1-H68. Entries carry the class keys their contract tests cover, and a `known_failure` from the catalogue.**
- Links: A4-084, Stage A `known_failures`, A1-008 (martingale flagged).
- Need: TLH 53 (clustering of variables across classes); the multi-instrument lens.
- What: a dictionary entry lists the class keys (K-fx, K-idx, K-cry, K-fut, K-stk) its golden cases cover; a slot bound on an uncovered class compiles only in shadow. Each entry carries the catalogue's known failure in its trader face, so `martingale-sizing` reads its warning before anyone binds it.
- Levels: block.
- Ledger: `x1_entry_class_coverage`.
- Evidence: the entry shape (built). Weakest link: none.
- Maturity: **solid**.

### I. Wild, kept for the funnel

**X1-H69. A central risk oracle.** One service answers approved, size, reason for every unit; rejects all when unreachable. Links: A4-074, A1-112, A2-050. Breaks standing alone and is a single point of failure; kept because his BMS-level breaker (C27) is an oracle in disguise, and H26 is the same pipeline without the hop. **Wild.** Ledger: `x1_oracle_mode`.

**X1-H70. Profiles that learn, and profile variants bred as a genome inside ranges.** Links: A4-182, A4-114, A4-126, A4-110. A `learned` derivation only behind shadow-first and a counted try; a genome mutated by agents inside ranges, screened by fixed robustness rules across windows and a cost grid, every trial in a search ledger, shrunk toward the pooled result. Collides with R3 §5.5 (do not chase performance across units). **Wild.**

**X1-H71. The ledger's `affects` edges executed at run time.** Links: A4-098, A4-065. When a number moves, the guard recomputes its dependents, writes receipts, and refuses a move that pushes a dependent out of range; cycles refused at compile. May be this generation's "too much machine". **Wild.** Ledger: `x1_affects_graph_runtime`.

**X1-H72. Overrides keyed by a context word instead of a session.** Links: A4-183, A3-030, A3-183. Once `reads` compile, an override keyed by `regime: mean-reverting` from the MIS; "thinking in context, not sessions, makes sense" (his reply 17). Depends on H56 and the relay. **Plausible.**

**X1-H73. The dry chassis and a live random-entry twin.** Links: A4-181, A4-186, A2 random-control brake test (MQL5 23482). Random entries with the full template on, through the replay and the scenario battery, to measure what the risk layer alone does; a live twin separates kind exits from real edge. **Plausible.** Ledger: `x1_dry_chassis_run`.

**X1-H74. Virtual positions netted into real orders by the guard.** Links: A4-076, A1-118. Units trade virtual positions; the guard nets them per instrument on a netting account; cost is charged at the netted level; two units that always cancel are flagged. **Wild** (fills and attribution are the problem).

**X1-H75. A per-unit feedback controller grants permission to trade from its predicted next state, kept only if it beats a random gate.** Links: A4-178, A4-006. The self-optimising EA series; the random-control test is the guard against its known failure. **Wild.**

**X1-H76. Three vectors side by side on every decision: intended, risk-approved, executed.** Links: A5-075, A4-153. The gap between them is logged and read as a brake-precision and an execution-quality signal. **Plausible.** Ledger: `x1_weight_gap_log`.

**X1-H77. The portfolio self-optimises slots between styles through agent proposals for his click.** Links: A4-174, H50, H41. His C26 made agentic: the allocator proposes slot changes through the proposal door; the shed classes carry them out. **Wild** (QMA flag on the allocator agent).

**X1-H78. A profile marketplace in the Library.** Presets, packs and clusters with cards, trust levels and results, browsable like the dictionary; installs through H30. **Wild**; depends on H22 and H30.

---

## 2. Problems and solutions (`bmad-cis-problem-solving`, run on each)

Each problem was framed (is and is not), traced to a root cause, and given at least two options with trade-offs. **[judgment]** on the trade-offs. No picks.

**P1. A sizer swap or the first halt makes every unit a new unit, so the rip-out costs each unit its record (G8 B9).** Root cause: the identity table has no label between "block swap" and "calibration row". (a) `profile_version_change` as a new version with a forwarding map (H43): keeps the record; changes what a counted try means (Q2). (b) Two records, logic in R and money per profile version (H44): no ruling; two numbers on a card. (c) A one-time `ambiguity_resolved` migration with his click per unit: cheapest now; does not solve the next swap.

**P2. A number bound only to the sizer cannot move (G8 B5).** Root cause: motion needs a logic-slot stamp. (a) The `derivation` type and a compiler rule (H08, H56): clean. (b) A stamp workaround: a hack that ties sizing to entry logic. (c) The guard overrides the fraction from outside: moves self-configuring out of the unit (D32).

**P3. Unit and account statistics have no producer (G9 M2).** (a) The guard with two adapters (H26, H57). (b) Blocks compute from the `trades` stream: per market only. (c) An app publishes them like the board: breaks ruling 11 and fails open.

**P4. Where the Book and BMS level lives.** (a) Cluster tags plus a portfolio config compiled into the guard (H40). (b) Book and BMS documents as in the draft (A4-092): fewer new words; cannot express intersections. (c) The Lab pod as the only producer (H33): the Lab is unbuilt. (d) A central oracle (H69).

**P5. Outside code in the money path.** (a) Trust ladder plus contract tests plus shadow (H22, H12): any origin may reach live by evidence. (b) Only `qml` and `human` size live; agent and community code limited to derivations and brakes: shuts his door. (c) His signature on every live pin (H22's rule alone): least code, most clicks.

**P6. Derivation expressiveness against safety.** (a) Blocks only. (b) Expressions compiled to blocks (H09). (c) Both.

**P7. "The unit stands alone" against account rules that need cross-unit data.** (a) The guard is part of the node process (H26). (b) A frozen account snapshot per pass in every unit: units disagree. (c) Account rules only in the kill switch by his hand: no automatic brake above the unit (against C27).

**P8. What happens when the guard or a fact is unavailable.** (a) Fail closed for new entries (RiskGate). (b) Fall back to position rules (freqtrade). (c) Enter REDUCING (H10). The chassis answer: declare it per piece (H14, `x1_fail_mode`) and let X3 set defaults; the cautious direction per number (H05) covers the silent case.

**P9. Paper sizes from the demo account's $10,000.** (a) Budget share with the deployment (H32). (b) A virtual account per deployment. (c) A configured paper notional.

**P10. The judge is size-blind, so nothing judges a profile (G8 B10).** (a) The resize replay with money measures (H21, H44). (b) The scenario battery. (c) Both, landing a `profile-verdict`; plus the canary analysis template (H45) for live evidence.

**P11. One sizer instance per market, so unit-level memory has no home.** (a) Unit-scope state in the guard, passed as a fact (H58). (b) A `unit_state` stream the sizer reads and writes: instances race. (c) Accept per-market state.

**P12. Nine fields parsed then ignored (G8 B6).** (a) Remove now, re-add each when a format reads it (subtract before add). (b) The checker errors on a set-but-ignored field; the schema refuses unknown fields (H15). (c) Implement all nine in format 2 (H56).

**P13. Records split per market only.** (a) Split keys (market, timeframe, session) with pooling for thin cells (H37, H08). (b) Derive at query time. (c) Timeframe as a unit-version property only.

**P14. Agents cannot finish a new risk block (G8 B8).** (a) `blocks_save` draft row plus `blocks_contract` (H53). (b) Artifacts he saves by hand. (c) The Lab sandbox first.

**P15. Two state machines on the node (trading states and kill levels).** (a) Map kill levels onto trading states (H10). (b) Keep both; read the kill level as a fact (H28). (c) Rename the kill levels to the trading-state words in the UI only, leaving code as is.

**P16. Herding: forty units retune together on the same evidence (MAPE-K's emergent-behaviour warning, A4-008).** Root cause: the learner runs per unit on shared market facts. (a) A retune share cap per cluster per window (H03). (b) Stagger appliers by a declared cadence per cluster (H41's review cadence). (c) Pool the learn at cluster level and apply one move to all (H08): fewer moves, coarser.

**P17. Sample minimums are days or weeks for low-frequency units (resilience4j's 100 calls, A4-191; Kayenta's 50 points).** (a) Minimums in effective trades scaled by trade rate and win rate (R9 short answer 10; X3's job). (b) Borrow the pooled group's sample through shrinkage (H08). (c) Time-based minimums with a declared floor on trades: simplest, least fair.

**P18. Two compile targets for the cluster level (documents versus the Lab pod).** (a) One target, two producers (H33). (b) The Lab pod is the only producer: blocks the template on an unbuilt Lab. (c) Documents only and the Lab compiles to documents later: the same as (a) in a different order.

**P19. Approval flooding across many units.** (a) A nightly flood cap with grouping by root cause (H51). (b) Tighten-only proposals apply in shadow without a card; only loosening lands cards (H50). (c) Batch cards per cluster: one click per cluster.

**P20. Judging a version while its own motion engine moves its numbers (Flagger's rule, A4-024).** (a) Freeze motion on both arms during the analysis window (H45). (b) Judge in R only, ignoring size: the judge today; cannot judge a profile. (c) Treat motion as part of the version under test and lengthen the window.

**P21. Where the applier runs when the PC is home and the node substitutes.** (a) The learner on the PC, the applier beside the order path, recommendations shipped as status (H31). (b) Both on the node: the PC cannot propose while the node is up. (c) Both on the PC with the node polling: an outside call at trade time, against ruling 11.

**P22. Loss budgets in calendar windows are unfair to low-frequency units (A4-029).** (a) Windows in trades for `S-sc`, in sessions for `S-id`, in weeks for `S-sw`, declared on the preset (H41). (b) One calendar window with a per-style burn-rate scale. (c) Two clocks (trades and calendar) and the stricter wins.

**P23. The canary across markets needs a second deployment of one unit version, refused today (G9 §3.2).** (a) Allow two deployments of one version with different profile pins on disjoint markets (H45). (b) Canary by size share on one deployment only. (c) Canary on the paper twin first, then by size share live.

---

## 3. Collisions

Named, not resolved. 1 to 18 carry over from the draft, shortened; 19 onward are new.

1. A separate profile document against "the unit stands alone": two versions describe one running thing; the snapshot rule would cold-start logic state on a profile-only change (H15, H43).
2. Derivations in the unit against pooled priors and the guard above it: "self-configuring remains at a unit" (D32) against H08's pooled rung and H03's share cap, which live above the unit.
3. H43 changes what a counted try and a click mean (G2 rulings 1, 4).
4. The edge as a dial (H02 `edge_point`) against both the edge-led basis and "don't lean on the edge": expressible is not agreed.
5. Cluster and portfolio documents (H40) against the Lab spine's pod compiling to Book and BMS fragments (H33 is one resolution; it is not ruled).
6. HALTED must run exits (C21) but Nautilus's HALTED denies protective stops; H10 must not copy Nautilus.
7. Timeframe and session overrides (H37) before their data exists (P13).
8. Community packs (H22) against "agents never touch money" and "only trading-node holds keys": the install door and the money door must differ.
9. A fail-closed guard against the board read that fails open by design (G9 §4.3).
10. The ledger as a planning file against the ledger as a runtime snapshot (H65, `x1_ledger_snapshot_in_compiled_unit`): who releases a snapshot is undecided.
11. Trading states per scope against the kill switch's four levels (P15).
12. `applies_to_open_positions` defaults false against REDUCING, which must touch open positions by amend-only.
13. The old Book door in code (G2 §6) against a unit that sizes itself through its profile.
14. Count brakes scaled to trade count (STATE item 10) against "circumstantial, let's first explore" (E27): the chassis only gives the field (H14).
15. Paper as a zero-slippage simulation against "the unit trades the same way on both, only the account differs".
16. H71 (affects edges at run time) against "design for complexity, not a complex system".
17. H70 (genome) against R3 §5.5 and against luck as a non-argument.
18. H69 (oracle) against G2 rulings 6 and 11.
19. **Tighten-only automation (H50, A4-197) against "performance with intention, not just safety" (M33, the sitting duck):** an automatic path that can only cut, with growth waiting on his click, ratchets down. The restore state (H11) and the expiry are the partial answers; a loosening path with its own bounds would be a new ruling.
20. **The Steward boundary (H52) against the raw-code hatch (H24):** a `plain_python` sizer is agent-reachable code in a slot the core is meant to own; quarantine makes it a brake twin, not a core replacement, but the line is thin.
21. **Clusters as tags (H40) against "the Book is the skeleton" (B3) and the name he chose (B7):** the structure changes and the word may go; he cares about terminology (D37).
22. **A bandit switching among approved versions (H48) against the identity table:** is a switch a calibration row or a version, and is it a counted try?
23. **The proposal door (H50) is also X7's and the brake states (H10) are also X3's:** three layers describe one seam; the funnel must merge, not pick one.
24. **"The MIS never switches a unit" (A3-184) against isolation published on the board and placement failing closed (A3-115):** the portfolio guard must own the switch; the board only carries it.
25. **His "self-configuring remains at a unit" (D32) against pooling across instruments (H08, A4-195, A4-196):** a pooled posterior is a value the unit did not derive alone.
26. **The retune share cap (H03) against each unit's own evidence:** a unit that has earned a move may be told to wait because its neighbours moved first.
27. **Shed classes (H41) against "each unit keeps its full size" (C29 as read by the lead):** a probation unit is cut first when the total binds, which is not pro rata.
28. **Rollout time to promote (H45) against low-frequency units:** a swing unit's canary needs weeks; the profile it tests may be stale by then.
29. **A never-self-tune list (H06) against "nothing is set in stone" (E2):** the list is his to edit, which keeps both, but an agent cannot propose a floor change at all.
30. **Expressions (H09) against the trust ladder (H22):** a generated derivation block has origin `human` or `agent` but never earns `tested_on_data` unless the card runs it; expressions could become an untested side door.

---

## 4. Restructure proposals

1. **Replace the Book and BMS containers with profile, cluster tags and a portfolio guard config (H40).** What replaces: the Book becomes a tag any unit may carry (several at once); the BMS becomes one document the guard compiles. Why it performs better: driver clusters catch co-loss the style Book never saw; one floor and one high-water mark instead of per-Book buffers that add up to idle money; portfolio self-optimisation becomes a document edit through the proposal door. Cost: new words, two new Library kinds, and his ruling on the names (Q1, Q4).
2. **Add the applier as an organ of both hosts (H03, H57).** What replaces: nothing; it fills the half of the VPA loop QMX lacks. Why better: `authority` and `applies_to_open_positions` stop being decoration; numbers move in modes he owns.
3. **Compiler format 2 with unknown fields refused and ignored fields removed or read (H56, P12).** What replaces: format 1's silent acceptance. Why better: a template cannot silently do nothing.
4. **The identity table gains profile labels and a migration map (H43).** What replaces: `block_swap` = new unit for every risk change. Why better: the record survives the rip-out and every later swap.
5. **One compile target for the cluster level; the Lab is a producer, not a second target (H33).** Why better: the Lab plugs in without rework (STATE item 31).
6. **The node's constants become ledger rows and its scope keys grow (H61).** Why better: isolation by class or region and the UI keys he asked for (C11) need them; no code change per number later.

---

## 5. Gaps: what no component covers

From the Solution Matrix (problems against components; see the intent doc). Empty cells:

1. **The switching cost of applying a tuned value mid-session**, in money (a changed stop distance or fraction on the next trade changes the record's meaning); no component prices it. The dead band (H03) is a stand-in.
2. **What "flat" means for a multi-position unit** (A8): `at_flat` has no definition when a unit holds three positions across markets.
3. **A day boundary for `K-cry`**: every anchor component assumes a day; 24/7 markets need a declared boundary or a rolling window, and nothing says which brake uses which.
4. **The futures roll as a version event**: a roll changes the instrument record; no component says whether a roll is a calibration row, a new version or nothing.
5. **A record for a cluster tag**: units have journals; clusters do not; cluster-scope brakes read statistics that have no persisted history across restarts.
6. **Herding tests**: no component tests many units retuning on shared facts (MAPE-K's warning); P16 has options and no evidence.
7. **MCP transport and auth for the read door**: QMA's; flagged, not designed.
8. **A fair control for the applier itself**: every brake has a random-control test (MQL5 23482); no component proposes the equivalent for a learner-applier pair (apply random values inside the bounds and compare).
9. **A parameter transform language for migration maps** (H43): Simulink has one; QMX has upgraders for stored shapes only.
10. **A ledger row for the rank table's defaults**: Gen 3 shipped none and blocked live; the template must ship them and nobody has written them.
11. **Who releases a ledger snapshot** (Collision 10).
12. **The applier's own telemetry**: how many recommendations were pending, applied, skipped by the dead band, blocked by the share cap, reverted by a guard; X6 owns observability but no component names these counters.

---

## 6. Questions only he can answer

1. **Vocabulary.** "Risk profile", "chassis", "pack", "preset", "cluster" (replacing "Book"), "portfolio" (replacing "BMS"), "pod" (a bundle). Which words stay, which go? (D37, B7, B14)
2. **Record on a sizer swap.** May a profile version change keep the unit's record and skip the "new unit" path, given it changes what a counted try and a click mean (H43, G2 rulings 1, 4)?
3. **Outside code and money.** May a community or agent block ever size a live trade, with his signature on the pin and shadow trades first, or never (P5)?
4. **Irreversible scope.** Clusters as tags plus a portfolio config (H40), or Book and BMS documents as named (A4-092)? The two set different build orders and different words.
5. **Automatic loosening.** May a tightening that an agent proposal applied automatically be released automatically by expiry and the restore state (H11, H50), or does every release need his click (Collision 19)?

---

## Appendix A. The roundtable (`bmad-party-mode`, session mode, non-interactive)

Five voices. 🛡️ **Marguerite**, pod-shop risk manager. ⚡ **Dex**, retail scalper, forty trades a day on gold and NAS. 🏗️ **Ada**, platform engineer. 🧮 **Quill**, quant developer. 🎙️ **The operator's voice**, his own words only. Topic: stress the strongest hybrids. Three rounds and a close.

**Round 1: the loop (H02, H03, H04)**

🎙️ **The operator's voice:** "how does it self configure? ... if you say 10%, where does it come from? What if I want to change the way it is derived?"

🏗️ **Ada:** Then it comes from a learner that writes a target and two bounds into status, and an applier that only moves it in the mode he set. The fields exist. The applier does not. That is the whole gap in one sentence.

⚡ **Dex:** I don't care about your bounds. I care that at 09:31 New York my size is what I set at 09:30. If your applier changes my fraction while I'm in a trade, I'm out.

🏗️ **Ada:** `at_flat`. It waits until you are flat.

⚡ **Dex:** I'm never flat. I've got gold and NAS on at once from 09:30 to 11:00.

🧮 **Quill:** So "flat" has no definition for him. That is a gap, not a mode. Write it down.

🛡️ **Marguerite:** And the learner on forty units reads the same gold move. They all cut together. You have built a herd. In my shop that was the 2020 problem: every desk de-risked on the same Tuesday.

🏗️ **Ada:** The VPA has an eviction tolerance: at most half the replicas at once. A share cap per cluster.

🛡️ **Marguerite:** Then the unit that earned its move waits because its neighbour went first. Say that out loud on the card, or he will think the system is broken.

🧮 **Quill:** And none of this beats a fixed size unless results persist. R9 ran it. With independent trades the learner is a 12 % size increase in disguise. The loop earns its place only when the stream has regimes.

🎙️ **The operator's voice:** "I don't want just safety. I want something that can like perform."

🧮 **Quill:** Then measure persistence in blocks, not trade to trade, and let the applier stay `off` where there is none. The loop is not the performance. The loop is the permission to have performance where it exists.

**Round 2: the levels (H40, H38, H41)**

🎙️ **The operator's voice:** "the book is the right skeleton. I say that, but again, I don't know. It's just cleaner."

🛡️ **Marguerite:** The Book is a folder. My losses never came from a folder. They came from six strategies in three folders that were all short volatility. Tag them by driver and cap the tag. The folder can stay for his screen.

🏗️ **Ada:** Tags are drop-ins. systemd has done it for fifteen years. A unit in three tags gets three drop-ins, strictest wins.

⚡ **Dex:** Strictest wins means every nervous tag shrinks me. Three weak caps and I'm trading one lot.

🧮 **Quill:** That is the dash.js failure. Smallest-cap stacks caution. You need brake precision before you turn a tag on. Shadow first.

🛡️ **Marguerite:** And one floor. One. On the whole account, marked, with a high-water mark that never resets. Every generation of this system kept a buffer per Book and called the idle money safety.

🎙️ **The operator's voice:** "I'd rather give units part of the seed and let them grow than leave $300 idle."

🏗️ **Ada:** So the floor is a portfolio fact and the units get compartments. That is the bulkhead. The guard enforces it at `before_order`.

⚡ **Dex:** And when the total binds, who gets cut?

🛡️ **Marguerite:** Not pro rata. The probation units first. Four classes. The proven desk keeps its size.

⚡ **Dex:** So the new guy always eats it.

🛡️ **Marguerite:** The new guy has no record. Yes.

**Round 3: the fight (H45, H50, H43)**

🧮 **Quill:** Here is the one you are walking around. He swaps the placeholder sizer and the identity table makes every unit a new unit. The record is gone.

🏗️ **Ada:** A forwarding map. Old block, new block, a parameter transform. Simulink. The table labels it a version.

🛡️ **Marguerite:** That is an engineer deciding what counts as a try. Committee question.

🧮 **Quill:** Then two records. Logic in R across versions, money per profile version. The judge is size-blind anyway. No ruling needed.

⚡ **Dex:** Two numbers on my screen. Which one is my P&L?

🛡️ **Marguerite:** The money one. The R one says whether your idea works. I have fired people for confusing them.

🏗️ **Ada:** And the new version does not replace the old one. It shadows, then it canaries on a share of your markets while the old one runs the rest, same time, same size. Pass, fail, or inconclusive.

⚡ **Dex:** Inconclusive on gold takes a month.

🏗️ **Ada:** Then it pauses for his card. That is the rule. Only he promotes.

🎙️ **The operator's voice:** "agents do most of the heavy lifting... I click and stuff."

🛡️ **Marguerite:** Then give the agents a door that can only tighten. A news agent says "cut crypto for two hours" and it happens, with an expiry. A news agent says "double gold" and it is a card.

⚡ **Dex:** So the machine can only ever make me smaller.

🧮 **Quill:** Unless the restore state releases it when the evidence expires. That is the collision. Tighten-only automation against his sitting duck. Nobody in this room can rule it.

🎙️ **The operator's voice:** "being too safe again... that the $300 remaining... I was like a sitting duck."

🏗️ **Ada:** Then it goes up as a question. Not ours.

**Close.** The room agreed on the loop's shape (learner, applier, guard) and on nothing about its gain. It produced: "flat" as a gap (Gap 2), the share cap as a visible reason on the card (Collision 26), brake precision before any tag goes live (H12), one floor with compartments (H39, H32), shed classes (H41), two records plus the forwarding map (H43, H44), the canary with an inconclusive pause (H45), the tighten-only door and its collision (H50, Collision 19), and Question 5.

---

## Appendix B. Draft idea to hybrid map

Draft ideas 01-76 → hybrids: 01→H15; 02→H16; 03→H18; 04→H20; 05→H17; 06→H19; 07→H21; 08→H10; 09→H23; 10→H21; 11→H26; 12→H26; 13→H40 (reshaped); 14→H30; 15→H29; 16→H28; 17→H27; 18→H34; 19→H35; 20→H34; 21→H38; 22→H38; 23→H08; 24→H08; 25→H08; 26→H02; 27→H29; 28→H09; 29→H37; 30→H37; 31→H47; 32→H37; 33→H49; 34→H43; 35→H44; 36→H43; 37→H45; 38→H15, H16; 39→H22; 40→H22; 41→H24; 42→H25; 43→H53; 44→H15, H49; 45→H21, H44; 46→H51; 47→H54; 48→H65; 49→H51; 50→H65; 51→H71; 52→H66; 53→H14; 54→H14, H19; 55→H14; 56→H56; 57→H57; 58→H58; 59→H59; 60→H60; 61→H61; 62→H61; 63→H43; 64→H64; 65→H62; 66→H63; 67→H61; 68→H49; 69→Appendix C; 70→H69; 71→H70; 72→H78; 73→H70; 74→H72; 75→H73; 76→H31. New in Stage B: H01, H03, H04, H05, H06, H07, H11, H12, H13, H32, H33, H36, H39, H41, H42, H46, H48, H50, H52, H55, H67, H68, H74, H75, H76, H77.

## Appendix C. UI needs from this layer (for the UI session)

1. A Numbers tab generated from ledger rows: level, measure, value, range, chain with the winning level, last receipt, reason code, who may change it, authority mode, pending recommendation with bounds (H07, H49, H66).
2. "Explain this size" from any decision row, ten words first (H54).
3. A profile card: version, preset, packs and order, self-test results, placeholders left, shadow and canary comparison, analysis outcome (H21, H45).
4. Trading state per scope with the reason, the distance to the next trip, and the restore probe progress (H10, H11).
5. An inbox: adopt a default, a profile version, a restore step, a loosening proposal; grouped by root cause; a nightly cap (H46, H51).
6. Both units of measure on every money row; the equity series and base named on every money brake (H14).
7. A derivation preview before saving; an expression editor with the allowed names (H09, H29).
8. Cluster tags on a unit, with which tag bound the last size (H34, H40).
9. The never-self-tune list as his settings page, with the policy level marked (H06).
10. Brake mode (shadow, ramped, live) and precision per brake (H12).

## Appendix D. Not covered

- No numbers. Every default, window, cap and factor here is a slot for the numbers lens; where the ledger file sets a categorical default (a mode, an order) it says why.
- No web reading in this run; every outside claim comes through R1 to R9 and the components, with their grades. The Exa tools were available and not needed.
- I ran no code against the stack. Claims about d02af358 are from G8, G9, G11 and the draft's five spot checks.
- X2 (sizing), X3 (brakes), X4 (scenarios), X5 (verification), X6 (observability) and X7 (agents) own their content; this file gives them slots, doors and the collisions.
