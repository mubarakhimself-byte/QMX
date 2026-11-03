# X1: the template's shape (the chassis)

Expansion round, layer X1, 3 Nov 2026. File id `X1-template-shape`. Ledger additions in `ledger/additions/X1-template-shape.yaml` (prefix `x1.`; the funnel renames and merges).

**What this layer is.** His words: "how do we technically design this or make something that can handle any amount of stress without it? I would call it the chassis" (`seeds/operator-words-2026-11-03.md:10`). This file widens what the chassis could be. It does not pick. It does not set numbers; the numbers lens comes later.

**How to read.** Each idea has what, why a trader wants it, how it works, the ledger ids it touches, its sources, and a maturity tag: **solid** (builds on a seam that exists in code), **plausible** (needs a new seam but fits the rulings), **wild** (keep for the funnel; it may break a ruling). **[judgment]** marks my opinion. Paths: `T/` is `D:\QMX-worktrees\bld-us-c13` at d02af358; `G8`, `G9`, `G11` and the others are `grounding/`; `R1`, `R3` are `research/`; `SEEDS` is `seeds/SEEDS.md`; `TLH n` is item n of "What the technical lens must hold" in SEEDS.

**Skills used.** `bmad-party-mode` in session mode, non-interactive, five personas voiced by me (Appendix A). `codebase-design` for the deep-module words: module, interface, implementation, seam, adapter, depth, leverage, locality (Appendix B).

---

## 0. The ground the chassis stands on (facts, no design)

These are the seams that exist today. Every idea below hangs on one of them or names the seam it needs.

| Seam | What it is today | Where |
|---|---|---|
| The unit document `qmx.unit/1` | has every risk *place*: one `sizer`, an `exit_set` with scopes, `halts` at position, unit and account, `reads`, `numbers` with kind, measure, default, range, motion, authority, origin | G8 §1.1; `T/qml/src/qml/unit/model.py` |
| The compiler, format 1 | refuses any halt and any `reads` entry; compiles two of six motion modes; a number bound only to the sizer cannot move | G8 §1.1, §3.10; `compiler.py:496-499` (checked) |
| The slot contracts | sizer, exit, halt, cross-unit hook, each a protocol with a contract test; no host runs halts or calls the hook | G8 §2; G9 §1.1 |
| The sizer's inputs | equity, entry, stop, instrument record; one instance per market; hard-coded receipt | G8 §1.4 |
| The identity table | edit label to result (none, calibration row, new version, new unit); lives in Settings; `block_swap` and `role_added` are new units | G8 §3.6; `service.py:352-388` (checked) |
| The loader and layer F | one loader, fingerprint pin, deny-by-default imports for agent code | G8 §3.2, §3.3 |
| Library kinds | `unit` and `component` are governed with checkers; `template`, `book`, `bms`, `pod`, `pod-block`, `methodology` are shells (checked) | G8 §3.8 |
| Agent rows | `unit_new(template, overrides)`, `unit_check`, `unit_explain`, `blocks_*`, journal and node reads; no row saves a block, runs the socket contract, publishes or promotes | G8 §4.1 |
| Workflows | `b-build-and-prove`, `dc-decay` tighten-only cards, `p1` and `pp` wait for this session | G8 §4.2 |
| Mini apps | `app.toml` with `risk = shows | runs | money`; only `trading-node` holds trading keys; the MIS proves an app can run QML blocks by entry id; the feed relay exists, unstarted | G8 §6; G9 §4.3 |
| The node | kill switch (his hand, four scopes), health stand-downs, a risk-stop pipe nothing feeds, paper as a zero-slippage simulation, settings as code constants | G9 §1 |
| Journals | unit rows `trade`, `fill`, `guard`, `signal`, `calibration`, `lifecycle`; `risk_event` and `would_have` kinds exist with open bodies (checked) | G9 §7.1; G11 §4.1 |
| The ledger lineage | July's `formulas.yaml` recorded `registry_inputs` per formula ("coefficients are configurable; relationships are law"); the unit build keeps numbers per unit with no levels and no edges | G11 §1 |

What the chassis must hold is the 55-item list in SEEDS "What the technical lens must hold". The ones this layer owns most: TLH 1-10 (shape), 30 (levels), 31-39 (access, schemas, agents), 52 (ledger as deliverable).

---

## 1. Ideas

### A. What the template is

**X1-template-shape-01. A risk profile as its own document, `qmx.risk-profile/1`.**
- What: the risk and sizing part of a unit becomes a document of its own: sizer binding, exit set, halts at every scope, hook policy, numbers with their derivations, and the level each piece acts at. A unit *names* a profile and a version, the way an n8n node names a credential type and a version (R1 §4.1-4.3). At compile time the profile is embedded into the compiled unit, so the unit still stands alone on the node (G2 ruling 11).
- Why: his "scalping based pod or scalping based system, risk management [and position] sizing system of a unit... how do we wire it in? we need schemas" (SEEDS D43). One profile can serve many units of one type (TLH 3), agents can version it without touching the unit's logic, and the identity table can give a profile swap its own row (idea 28).
- How: a new governed Library kind `risk-profile` with a checker (layers A to F plus a new layer H for risk couplings, idea 48). `unit.risk_profile: {entry_id, version, fingerprint}` beside today's `sizer`, `exit_set`, `halts`, `numbers`. Transition: the compiler accepts either the inline fields or a profile pin, never both. The compiled unit carries the profile's fingerprint in its own.
- Ledger: `x1.profile_schema_version`, `x1.profile_version_pin`, `x1.profile_embed_at_compile`.
- Sources: G8 §1.1, §3.8; R1 §4.1-4.3; SEEDS D43, A5.
- Maturity: **solid** (the fields exist; the document split is new).

**X1-template-shape-02. One chassis, many presets.**
- What: one schema, N presets. A preset is a Library `template` item (the kind exists, empty) holding bindings, derivation choices and override values for one unit type: `scalper-mr`, `orb`, `trend-pullback`, and whatever comes next. "Any type" is a new preset, not a new schema.
- Why: "one template by any type... I think things might change" (SEEDS A5). Types will change; the schema should not.
- How: `unit_new(template, overrides)` already starts from a template; today only the dummy exists (G8 §4.1). Presets are files in `qml/unit/templates/` for first-party ones and Library `template` items for his and agents'. A preset carries a `style` tag that also keys the override chain (idea 24).
- Ledger: `x1.preset_id`, `x1.style_tag`.
- Sources: G8 §4.1, §3.8; R1 §8 point 7 (presets ship complete).
- Maturity: **solid**.

**X1-template-shape-03. Facts, responses and his limits as three separate parts.**
- What: the template splits its content three ways, as article 24237 does (R1 §3.2): (1) *facts* about the venue, account and instrument, measured and never typed (equity series, costs, lot step, margin, kill level, SQS state); (2) the unit's *response* rules (sizer, halts, exits, derivations, accelerators); (3) *his limits* (floor, cushion, ceiling, budget share), user-configured, never self-configured. The template is (2) plus derivations that read (1) and (3).
- Why: "some things are self-configured, others user-configured" (SEEDS D32); "the floor/cushion is user-configured" (STATE, third round). Mixing them is how the old numbers got blanked (SEEDS D31).
- How: every ledger row carries `changed_by: measured | self | user`. The checker refuses a profile that self-derives a `user` row or types a `measured` one. The UI groups by the same field.
- Ledger: `x1.changed_by_class`, `x1.his_limits_set` (the names of the user-only rows).
- Sources: R1 §3.2 (24237), §8 point 8; SEEDS D32, C11.
- Maturity: **solid**.

**X1-template-shape-04. The template behind one deep interface.**
- What: the whole risk template is one module behind one interface at the host: `decide(intent, facts) -> SizedIntent | Skip(reason)`, `on_event(event, facts) -> [Halt | Amend | None]`, `state(facts) -> RiskState`. Sizer, halts, exits, derivations and accelerators are implementation with internal seams. Both hosts, QMB and the node, call the same three verbs (`UnitSliceHandler` already serves both, G8 §2.4).
- Why: "design for complexity, don't design a complex system" (SEEDS D34). A caller learns three verbs and gets every brake and accelerator behind them. Fix once, fixed in backtest, paper and live.
- How: the three verbs wrap today's per-slot calls in `protocol/unit.py`. The deletion test (Appendix B): delete the module and the sizing, halting and exit logic reappears in two hosts, so it earns its keep.
- Ledger: `x1.host_verbs` (the three names, so the ledger can say which rows each verb reads).
- Sources: codebase-design; G8 §1.4, §2.4; R1 §0 point 1 (every platform's sizer is one small function).
- Maturity: **solid**.

**X1-template-shape-05. Packs that stack.**
- What: a profile is composed from packs: a sizing pack, a brake pack, an exit pack, an accelerator pack. Each pack is a small versioned bundle of blocks, numbers and derivations. Packs stack in a declared order, the way LEAN chains risk models and the newer target wins (R1 §1.4) and StrategyQuant adds money-management snippets (R1 §2.2).
- Why: "brakes must be addable, removable and combinable" (TLH 23). He wants to try "versions that are literally like the first system, then versions that take parts of both" (SEEDS B6).
- How: `profile.packs: [{pack_ref, version, order}]`. The compiler flattens packs into slots and refuses two packs that claim the same slot without an explicit combiner. A pack is a Library `collection` of `component` items plus a manifest.
- Ledger: `x1.pack_order`, `x1.pack_conflict_rule`.
- Sources: R1 §1.4, §2.2, §8 point 9; SEEDS B6, TLH 23.
- Maturity: **plausible**.

**X1-template-shape-06. A needs list the host must meet.**
- What: a profile declares the statistics it reads (`session_loss_r`, `day_start_equity`, `open_risk`, `book.day_loss_r`, ...). The compiler refuses a profile whose needs the target host does not compute. A halt can no longer be bound to a scope whose statistics nobody produces.
- Why: today "nothing checks that a halt's binding scope agrees with what it reads" (G8 §3.5, `US/BACKLOG.md:259`), and no host computes the halt inputs (G9 §1.3).
- How: the `reads` field already exists with fallbacks `compute_here`, `treat_as_absent`, `no_new_entries` (`model.py:157-160`, checked). Extend it from MIS readings to host statistics. The host publishes a `provides` list (an app manifest already has `provides` and `feeds`, G8 §6.1). Compile = needs ⊆ provides, or a named fallback per need.
- Ledger: `x1.needs_list`, `x1.need_fallback` (reuse the stack's `reads.fallback` values).
- Sources: G8 §1.1, §6.1; G9 §1.3; `model.py:157-160`.
- Maturity: **solid**.

**X1-template-shape-07. A self-test card per profile version.**
- What: every profile version carries a card with: contract-test results per slot, a trade-list replay (idea 45) on the unit's own record, a scenario-battery result (the scenario layer's set), the ledger check, and the list of placeholders left. The card is what an agent and he read to answer "how do they know that the things are correct?" (SEEDS D43).
- Why: a profile without a card is a guess with a version number.
- How: the engine's `b-build-and-prove` already ends on a card (G8 §4.2). A `rp-profile-card` shared block runs the four checks and lands a `proposal-card` with `ask: profile_version`. The judge's `baseline-card` is the model (G9 §7.1).
- Ledger: `x1.self_test_battery`, `x1.card_required_before_live` (flag).
- Sources: G8 §4.2; G9 §7.1; SEEDS D43.
- Maturity: **solid**.

**X1-template-shape-08. Trading states as the spine of every brake.**
- What: the template holds a small state machine per scope: `ACTIVE` (everything), `REDUCING` (new entries only at a smaller size or not at all; amendments may only tighten; exits always run), `HALTED` (no new entries; exits, broker stops and the kill switch still work), `RESTORE` (size climbs back by steps). Every brake and every accelerator is a transition or a step inside a state, never a bespoke action. Nautilus has the first three states; article 15085 has the restore state (R1 §6.1, §3.2).
- Why: "size down, but not quickly" (SEEDS A25) is a `REDUCING` state with steps, not a cliff. "Exits are never blocked" (SEEDS C21) is a law of the `HALTED` state. Each brake "says what tripped it" (SEEDS C7) because each transition carries a reason.
- How: `RiskState.state[scope]` with a transition table in the profile. The halt slot's answers `no_new_entries` and `flatten` map onto `HALTED` with and without a flatten; a new answer `reduce{factor, steps}` maps onto `REDUCING`. The lifecycle machine's `stopped` by `risk_rule` (G9 §1.4) is `HALTED` at unit scope.
- Ledger: `x1.trading_state`, `x1.state_transition_table`, `x1.reduce_step`, `x1.restore_rule`.
- Sources: R1 §6.1, §3.2 (15085, 24249); G9 §1.4; SEEDS A25, C21, C7.
- Maturity: **solid** for the states, **plausible** for `RESTORE`.

**X1-template-shape-09. Three faces on every profile and preset.**
- What: like a dictionary entry, a profile has a trader face (plain words: "risk half a percent of the pot to the stop, stop the unit after three full stops in a session"), a machine face (the schema) and a code face (the blocks). Agents write the trader face first; the checker proves the faces agree by running the code face on the self-test card.
- Why: "terminology matters because this system is very agentic driven" (SEEDS D37); "dumb it down for me" (SEEDS D33).
- How: the `component` kind already has three faces (G8 §3.4). Reuse the shape on `risk-profile`.
- Ledger: `x1.profile_faces`.
- Sources: G8 §3.4; SEEDS D37, D33.
- Maturity: **plausible**.

**X1-template-shape-10. A chassis stress battery.**
- What: a fixed set of adversarial extensions the chassis must absorb without a schema change: add a brake at a new level; add a level; swap the sizing basis (edge-led to day-budget to volatility-unit); add an instrument class with a different lot granularity; add a timeframe axis; add an outside block; add an accelerator. Each is a test in CI against the schema and the compiler.
- Why: "handle any amount of stress... the baseline will change a lot or deviate a lot" (SEEDS A23). This turns his worry into a test.
- How: one test file per extension; each builds a profile, compiles it against both hosts, runs the contract tests and the self-test card.
- Ledger: `x1.chassis_stress_battery`.
- Sources: SEEDS A23, E27; G8 "What blocks it today".
- Maturity: **plausible**.

### B. Where each piece lives

**X1-template-shape-11. The money path stays in QML blocks inside the unit.**
- What: sizer, position-scope exits, position-scope halts and their numbers are blocks compiled into the unit, run by `protocol/unit.py` on the node and in QMB. No call leaves the unit at trade time.
- Why: ruling 11 (G2): nothing a unit needs may depend on the router, the MIS, the PC link or the Library at trade time. Only the node sends orders (ruling 6).
- How: as built (G8 §6.3). The template adds nothing here except the three verbs (idea 04).
- Ledger: none new.
- Sources: G2 rulings 6, 11; G8 §6.3-6.4.
- Maturity: **solid** (fact).

**X1-template-shape-12. A guard module on the host for unit, book and account scope.**
- What: one module, `qmf-risk/guard`, used by both hosts, that computes the statistics the slots read (day-start equity, session loss in R, streaks, fills, open risk, exposure per bet key, budget used), runs unit- and account-scope halts, calls `before_order`, and feeds the risk-stop pipe. The same block code runs in it; the guard only supplies the inputs and the scope.
- Why: today "no host computes `day_start_equity`, `losing_day_streak`, `session_fills` or `session_loss_r`" (G9 §1.3), the hook "passes every order" (G9 §1.1), and "units on one account do not know about each other" (G9 §0.9). Backtests must match live, so the guard must be one module with two hosts as adapters.
- How: the guard is node-local (no Library at trade time). QMB's `unit_handler` and the node's `runtime` both instantiate it. It writes `risk_event` rows (the kind exists with an open body, checked) and emits `RiskState` (idea 57).
- Ledger: `x1.guard_statistics` (the list), `x1.guard_unavailable_action` (idea 54).
- Sources: G9 §0.9, §1.1, §1.3, §6; G8 §2.1; R1 §3.2 (RiskGate, 24477).
- Maturity: **solid**.

**X1-template-shape-13. The Book and the BMS as documents, compiled into guard config.**
- What: a `book` Library item = {members (unit refs or a methodology tag), budget-share rule, brakes at book scope, allocation mode, counting rule}; a `bms` item = {books, floor, cushion, aggregate limit, isolation protocol, slot policy}. The host compiles them into the guard's config at deploy. The kinds exist as empty shells (checked).
- Why: "the Book is the right skeleton... it's just cleaner" (SEEDS B3); "the BMS holds the overall portfolio" (SEEDS B2); the Lab spine already compiles a pod into Book and BMS fragments (AD-11, `QV2/.../ARCHITECTURE-SPINE.md`).
- How: fill the `book.schema.json` and `bms.schema.json` fields; give each a checker that validates against the ledger (level, measure, needs). A deployment carries a frozen copy. Numbers at these levels get ledger rows with `level: book` or `level: bms`, which no generation ever had for Gen 4 (G11 §1.4).
- Ledger: `x1.book_document`, `x1.bms_document`, `x1.budget_share`, `x1.aggregate_limit_factor` (idea 19).
- Sources: G8 §3.8; G6 §3.1; G11 §1.4; Lab spine AD-10, AD-11.
- Maturity: **plausible**.

**X1-template-shape-14. The pod as a shippable bundle: a book plus its packs plus its skills.**
- What: resolve his two senses of "pod" (SEEDS B14, glossary) by making a pod a Library *bundle*: one `book` document, the packs it uses, the presets its units start from, the agents and skills that propose changes, and a self-test card. It ships the way a mini app ships (a signed bundle), and installs by landing its items into the Library. It never sits in the order path.
- Why: "pods are meant to be mini apps... how do we ship pods?" (SEEDS B14); "a solid baseline core, extended the way mini apps extend QMX" (STATE; SEEDS D35).
- How: a pod is a `mini-app` whose `provides` lands `risk-profile`, `template`, `component` and `book` items through a lander (today an app's lander does not land those kinds: G8 §6.4). The node reads only what the host compiled from the landed items.
- Ledger: `x1.pod_bundle_contents`, `x1.pod_install_requires`.
- Sources: G8 §6.1-6.4; SEEDS B14, D35; Lab spine AD-10.
- Maturity: **plausible**.

**X1-template-shape-15. A Risk Lab mini app around the template.**
- What: an app with `risk = runs` that ships the tooling: a trade-list resizer (QuantAnalyzer's money-management simulator, R1 §2.3), the scenario generator, preset editing, the derivation preview (idea 23), the ledger browser, and the agents and skills that draft profile versions. It lands `component`, `template` and `risk-profile` drafts for his yes.
- Why: "combine a mini app together with the risk and sizing system" (SEEDS B14). The MIS already proves an app can run QML blocks by entry id with one copy of the code (G8 §6.2).
- How: `app.toml` with jobs `resize_replay`, `scenario_run`, `profile_check`, `derivation_preview`; a lander for the risk kinds; skills `build-risk-profile`, `explain-size`.
- Ledger: `x1.risk_app_jobs`.
- Sources: G8 §6; R1 §2.3; SEEDS B14.
- Maturity: **plausible**.

**X1-template-shape-16. The node's fast lane stays outside the template and feeds it as facts.**
- What: the kill switch, the SQS, the stand-downs and the protection escalation stay node organs. The template never replaces them. It reads their state (kill level per scope, SQS state, stand-down scopes) as facts, and its derivations may size down on them.
- Why: "the kill switch and SQS stay: they earned their place" (STATE, 1 Nov). He lists SQS and MIS strength among the reasons a size may fall (SEEDS A13).
- How: the guard's facts include `kill_level[scope]`, `sqs_state[market]`, `stand_down[scope]`. A derivation may read them. A brake inside the template may *raise* a stand-down through the risk-stop pipe, never lower the kill switch (operator only, G9 §1.1).
- Ledger: `x1.fact_kill_level`, `x1.fact_sqs_state`, `x1.fact_stand_down`.
- Sources: G9 §1.1; SEEDS A13, C21.
- Maturity: **solid**.

**X1-template-shape-17. `before_order` as the one seam where account rules touch a trade.**
- What: the cross-unit hook becomes the guard's `before_order(intent, open_positions, facts)`. It is the only place a book or BMS rule can refuse or shrink one order. It answers `pass`, `shrink{to, reason}` or `refuse{reason}` with a closed list of reason codes (Nautilus, R1 §6.1).
- Why: the hook exists and nothing calls it (G8 §2.1). One seam with two adapters (QMB and node) is a real seam.
- How: add `shrink` to the hook's answer; call it from `runtime.py:1010-1013` and `unit_handler.py`. Reason codes journalled on the `guard` row.
- Ledger: `x1.hook_answer_kinds`, `x1.refusal_reason_codes`.
- Sources: G8 §2.1; G9 §1.1; R1 §6.1, §3.2.
- Maturity: **solid**.

### C. Levels, and how a rule reaches across them

**X1-template-shape-18. Level as a field on every number, brake and state.**
- What: `level ∈ {trade, position, unit, book, methodology, bms, account, node}` on every ledger row and every binding, with a `scope_key` the host knows how to resolve (position id, unit id, book id, methodology tag, account id, class code). The halt lists already have three scopes; this extends them and names them in the ledger.
- Why: "risk management can be at a portfolio level, at a unit level, at a cluster level, or at a methodology level... subsets... intersections" (SEEDS B1). G11 §1.4: no Gen 4 ledger row has a level.
- How: `ScopedBinding.scope` grows from three values to the set above; the compiler refuses a scope the target host cannot resolve (idea 06).
- Ledger: `x1.level`, `x1.scope_key`.
- Sources: G8 §1.1; G11 §1.4; SEEDS B1.
- Maturity: **solid**.

**X1-template-shape-19. Down the levels as caps and states; up the levels as events.**
- What: a higher level never calls a lower level's code. It emits *constraints* the lower level reads as facts: a budget share, a max open risk, a trading state. A lower level never reaches up except by *events* it journals: trade closed, brake fired, breaker strike, derivation moved. The guard aggregates the events into the higher level's statistics.
- Why: this is how limit hierarchies work in banks (R1 §5.3) and in the three-scope article (R1 §3.2, 24477). It keeps "simple at the core" (G2 ruling 25).
- How: facts flow down through `RiskState`; events flow up through `risk_event` and `trade` rows. The ledger's `affects` edges are typed `down:cap`, `down:state`, `up:event`.
- Ledger: `x1.coupling_direction`.
- Sources: R1 §5.3, §3.2; G2 ruling 25; G11 §1.2.
- Maturity: **solid**.

**X1-template-shape-20. Methodology and cluster as tag scopes, with the strictest answer winning on overlap.**
- What: a rule bound to `methodology: mean-reversion` applies to every unit tagged so, across books. A unit can be in a scalper book and in the mean-reversion methodology at once. Where two scopes answer differently, the strictest wins, as the identity table already does with edit labels ("the highest result of an edit's labels wins", `table.py`, checked).
- Why: he asked for intersections and unions (SEEDS B1).
- How: the guard resolves every active scope for an intent, collects every answer, and applies `min(size)`, `max(state)`. Each answer is journalled, so the trace shows which scope bound.
- Ledger: `x1.scope_overlap_rule`, `x1.methodology_tag`.
- Sources: SEEDS B1; `identity/table.py` (checked); G11 §1.2 (April's `binding_clamp`).
- Maturity: **plausible**.

**X1-template-shape-21. A parent limit below the sum of its children.**
- What: the BMS declares an aggregate limit that is *less* than the sum of its books' limits, scaled by a measured co-loss factor; the guard scales children down only when the sum binds (LEAN insight weighting, R1 §1.3; RiskMetrics 3.1, R1 §5.3).
- Why: this is the professional answer to his "10 units, $20 each or $2 each" question (SEEDS C29): each unit keeps its own size until the total binds. It is a chassis slot; the numbers lens sets the factor.
- How: `bms.aggregate_limit = factor × Σ book.limit`, `factor` derived from measured joint losses (idea 22's bet keys give the data). The guard enforces at `before_order`.
- Ledger: `x1.aggregate_limit_factor`, `x1.co_loss_measure`.
- Sources: R1 §1.3, §5.3; SEEDS C29.
- Maturity: **plausible**; the factor is a numbers-lens value.

**X1-template-shape-22. Same bet counted once through a bet key.**
- What: the guard assigns every open position a bet key from a declared rule (currency legs, class, direction, window) and caps open risk per key. Exposure across units is born from this: `open_risk[bet_key]`, `open_risk[class]`, `open_risk[account]`.
- Why: "no cross-unit exposure measure exists" (brief; G11 §2.2); "preventing losing all at once" (SEEDS B15). The `rk2-correlation-drift` draft already turns positions into currency legs in R (G9 §6).
- How: `bms.bet_key_rule` chooses the key; the guard computes it per order; the hook reads `open_risk[key]`.
- Ledger: `x1.bet_key_rule`, `x1.open_risk_by_key`.
- Sources: G9 §6; G11 §2.2; SEEDS B15, A8.
- Maturity: **plausible**.

### D. Defaults and derivations

**X1-template-shape-23. Derivation as a block, so the way a default is derived can be swapped.**
- What: a new component type `derivation`. Every number may bind one. It computes the number from facts (equity, costs, the record, his limits, the state) and writes a receipt. "Change the way it is derived" (SEEDS D46) means swap the derivation block or its parameters. Today's `motion` rules (`trend-floor-from-record@1`) are one family of derivation; add `derive_at_boot`, `derive_on_schedule`, `derive_from_record`, `derive_from_state`.
- Why: "if you say 10%, where does it come from? What if I want to change the way it is derived?" (SEEDS D46).
- How: `NumberSpec.derivation: {entry_id, version, params}` beside `motion`. The compiler lets a sizer-bound number move through a derivation (today it cannot, G8 §3.10). A derivation is a block with inputs `facts` and `current`, output `value`, and the same layer F limits.
- Ledger: `x1.derivation_rule`, `x1.derivation_params`.
- Sources: G8 §3.9-3.10; SEEDS D46, D29; R1 §4.1 (n8n expressions as computed defaults).
- Maturity: **solid**.

**X1-template-shape-24. Derivation receipts: a reason row for every value.**
- What: every derived value writes a `calibration` row with the derivation id, its inputs and the old and new value. "Every number has a reason" becomes a row he can read.
- Why: SEEDS D29, A13 (the volleyball rule).
- How: the `calibration` row exists for moved numbers (G9 §7.1); extend its body with `derivation`, `inputs`. Boot derivations write one too.
- Ledger: `x1.derivation_receipt`.
- Sources: G9 §7.1; SEEDS D29, A13.
- Maturity: **solid**.

**X1-template-shape-25. A derivation ladder with fallbacks, so no key setting is ever blank.**
- What: for each number: `derive_from_own_record` → `derive_from_class_default` → `derive_from_preset_default` → refuse to compile. Each step is a receipt. A fresh unit with no record still gets a value with a reason.
- Why: "no key setting left blank" (SEEDS D30); demo units at boot (SEEDS A22).
- How: `derivation.fallback_order` on the profile; the checker refuses a number whose ladder can end empty.
- Ledger: `x1.derivation_fallback_order`.
- Sources: SEEDS D30, A22; R3 §4.3 (pysystemtrade's config, private, defaults order).
- Maturity: **solid**.

**X1-template-shape-26. The edge as a range the derivation reads, with the point a dial.**
- What: the size derivation reads the record as a range (low, mid, high from the baseline cone) and the profile declares which point sizing uses: `edge_point ∈ {low, mid, floor_odds}`. Leaning on the edge becomes a setting, not a law.
- Why: "let's give a range for the edge" (SEEDS A24). The lead's edge-led basis and his low-edge tolerance are both expressible on one chassis; the sizing layer argues which default.
- How: the baseline card already holds a cone (G9 §7.1). A derivation `size-from-edge-range@1` takes `edge_point`.
- Ledger: `x1.edge_point`.
- Sources: SEEDS A24; G9 §7.1; R2 §9 (errors in expected returns do most damage).
- Maturity: **plausible**; collides with the sizing layer (Collision 4).

**X1-template-shape-27. Derivation preview before saving.**
- What: the copilot and the UI can dry-run a derivation against today's facts and show the number it would give, as StrategyQuant's `display` template shows a snippet's current settings (R1 §2.2).
- Why: he will not read a formula; he will read "$9 at risk on this trade, because..." (SEEDS D33).
- How: a `derivation_preview(profile, number, facts)` job on the Risk Lab app (idea 15) and a tool row (idea 41).
- Ledger: none new.
- Sources: R1 §2.2; SEEDS D33.
- Maturity: **plausible**.

**X1-template-shape-28. Two derivation languages: blocks, and a small safe expression form.**
- What: beside derivation blocks, allow a tiny expression form in the document (`equity * fraction / stop_distance`), parsed to a block at compile, with no calls, no loops, a fixed name list from the ledger. n8n lets any field be an expression (R1 §4.1).
- Why: a non-coder and the copilot can write and read an expression; a block needs a file and a test.
- How: the expression compiles into a generated `derivation` block, so layer F and the loader see only blocks. The ledger supplies the allowed names.
- Ledger: `x1.expression_names_allowed`.
- Sources: R1 §4.1; G8 §3.3.
- Maturity: **plausible**; Problem P6.

### E. The override chain

**X1-template-shape-29. A fixed chain: preset → style → class → bucket → instrument → venue account → unit → market settings.**
- What: later wins. A residual bucket holds anything unclassified (ISDA SIMM, R3 §4.3). The resolved value carries its provenance path, so "where did this 0.5 % come from" is answered by the chain.
- Why: R3 §5.8 proposes exactly this; "defaults with overrides answer 'every variable has a value without hand-setting all of them'" (R3 §4.3).
- How: `markets[].settings` already exists and is checked, then ignored by the compiler (G8 §1.1). Make the compiler resolve the chain and write the resolved values plus path into the compiled unit.
- Ledger: `x1.override_chain_order`, `x1.residual_bucket`.
- Sources: R3 §4.3, §5.8; G8 §1.1.
- Maturity: **solid**.

**X1-template-shape-30. A class code per instrument that picks its defaults.**
- What: each instrument carries a short code (QMX's nine classes plus a bucket: `fx-major`, `fx-cross`, `metal`, `index-us`, `index-eu`, `index-asia`, `commodity`, `stock`, `crypto-perp-major`, `crypto-perp-alt`, `residual`), like ISO 10962's CFI (R3 §4.3). Defaults attach to codes, not to free text.
- Why: "the terminology is increased, the variables increased, because last time I was only using FX" (SEEDS D51). R3's worked number shows one rule gives a tradable size in one class and nothing in another (R3 §4.2).
- How: `instrument.class` exists with nine values (G9 §2); add `bucket`. Buckets are a Library `collection` so he can add one.
- Ledger: `x1.instrument_bucket`, `x1.bucket_defaults`.
- Sources: R3 §4.1-4.3; G9 §2; SEEDS D51.
- Maturity: **solid**.

**X1-template-shape-31. Overrides stored as diffs, upgrades offered, never silent.**
- What: a unit stores only what differs from its resolved chain (n8n stores non-default values only, R1 §4.2). When a preset or class default improves, untouched units get a *proposal card* to adopt the new value; nothing changes silently.
- Why: "nothing is set in stone" and "every change needs a stated reason" at once (SEEDS E2, A13).
- How: the identity table's `fixed_value_change` is a new version with his click (checked); an upgrade offer is a `proposal-card` with `ask: adopt_default`.
- Ledger: `x1.overrides_as_diffs`, `x1.upgrade_offer_policy`.
- Sources: R1 §4.2-4.3; `service.py:352-388` (checked).
- Maturity: **solid**.

**X1-template-shape-32. Timeframe and session as override axes.**
- What: overrides may be keyed by bar size and by session (or context word), not only by market, because cost ÷ stop distance changes with the timeframe (G9 §5.4) and the record differs by session.
- Why: "multiple time frames, multiple instruments" (SEEDS D51); records today split per market only (G7 §0.8).
- How: `record_split_keys: [market, timeframe, session]` on the profile; the guard keys its statistics the same way; the trade row needs `session` (G9 §7.1 gap).
- Ledger: `x1.record_split_keys`, `x1.timeframe_axis`.
- Sources: G9 §5.4, §7.1; G7 §0.8; SEEDS D51.
- Maturity: **plausible**; Problem P13.

**X1-template-shape-33. `risk_explain`: print the chain for any number.**
- What: one call, one unit, one number, and the answer is the chain with the winning level marked, the derivation receipt and the ledger row. Ten words for him, the full chain for an agent.
- Why: "every trade's size can be traced to a few numbers" (lead's counter in SEEDS D33); agents need it to propose (SEEDS D42).
- How: `unit_explain` exists (G8 §4.1); add a number argument.
- Ledger: none new.
- Sources: G8 §4.1; SEEDS D33, D42.
- Maturity: **solid**.

### F. Versions

**X1-template-shape-34. A profile swap gets its own identity row.**
- What: new edit labels `profile_version_change` and `profile_swap`, with their own rows in the Settings table (he can edit them), instead of falling into `block_swap` = new unit. Default proposal: `profile_version_change` → new version, counted try, his click; `profile_swap` → new unit.
- Why: under today's defaults "replacing the placeholder sizer with a real one, or adding the first halt, makes every existing unit a new unit... The rip-out therefore costs each unit its record" (G8 §3.6). The table "is data he can edit" (G8 "Where it would plug in" 5).
- How: `EditLabel` gains two members; `diff.py` labels a change inside `risk_profile` with them instead of `block_swap`/`role_added`.
- Ledger: `x1.identity_profile_version_change`, `x1.identity_profile_swap`.
- Sources: G8 §3.6; `table.py`, `service.py` (checked).
- Maturity: **solid**; Problem P1; Question Q2.

**X1-template-shape-35. Two records: a logic record in R and a money record per profile version.**
- What: the judge is size-blind (G8 §5.3), so a profile change cannot change a verdict. Keep the unit's logic record (R) across profile versions, and start a new money record (dollars, drawdown, budget used) per profile version. Both show on the card.
- Why: this is what lets a sizer swap keep the evidence QMB and paper earned, which his "most of the work has already been done" expects (SEEDS E19).
- How: `paper-run` and `trade` items carry `profile_version`; the judge reads R regardless; the money measures group by profile version.
- Ledger: `x1.logic_record_scope`, `x1.money_record_scope`.
- Sources: G8 §5.3; SEEDS E19.
- Maturity: **solid**.

**X1-template-shape-36. Pinned profile versions per unit version, old ones keep running.**
- What: a unit version pins its profile version and fingerprint, as n8n pins `typeVersion` (R1 §4.3). A new profile version sits beside the old one; units move by his click, at the next flat.
- Why: "a workflow saved with version 1 stays on version 1, even after you publish version 2" (R1 §4.3). No silent change on the money path.
- How: the `Pin {entry_id, version, fingerprint}` shape exists (`model.py`, checked). The snapshot rule (a different fingerprint starts cold, G8 §3.7) must exempt profile-only changes from cold-starting the logic blocks' state (Collision 11).
- Ledger: `x1.profile_version_pin`, `x1.adopt_at_next_flat`.
- Sources: R1 §4.3; G8 §3.7.
- Maturity: **solid**.

**X1-template-shape-37. Shadow a new profile version before adopting it.**
- What: a proposed profile runs as `would_have` on the live unit's own trades for N trades before it may size live: the old profile sizes, the new one is journalled. The `would_have` kind exists with an open body (checked).
- Why: "size down, but not quickly"; and no product self-tunes under guardrails (R1 §8 point 15), so shadow-first is the guardrail.
- How: the guard runs both profiles' `decide` and journals the second as `would_have`. The card compares them.
- Ledger: `x1.shadow_trades_before_live`.
- Sources: `journal_kinds/unit.py` (checked); R1 §8 point 15; SEEDS A25.
- Maturity: **solid**.

**X1-template-shape-38. Schema, preset, pack, block and derivation each versioned, each with an upgrader.**
- What: five version numbers, five upgrader chains. A new schema cannot ship without an upgrader (A10 already demands this for unit, entry, check and behaviour shapes, G8 §3.7).
- Why: the chassis must change without breaking stored profiles.
- How: `qmx.risk-profile/N` with `upgrade.py`; presets and packs use semver (the `pod` kind already annotates `semver`, checked).
- Ledger: `x1.profile_schema_version`, `x1.preset_version`, `x1.pack_version`.
- Sources: G8 §3.7; `pod.schema.json` (checked).
- Maturity: **solid**.

### G. Outside code and trust

**X1-template-shape-39. A trust ladder per block, and a minimum trust per slot.**
- What: trust = origin (`qml`, `human`, `agent`, `community`) × evidence (`named`, `specified`, `implemented`, `contract_passed`, `tested_on_data`, `used_in_unit`, `shadowed_live`). A profile declares the minimum trust for each slot. Proposal: live sizing needs `contract_passed` and `shadowed_live`; a derivation needs `contract_passed`; a brake needs `tested_on_data`.
- Why: "Can we add external things like external code?... How do they know that the things are correct?" (SEEDS D43). The dictionary already computes status from evidence but `tested_on_data` and `used_in_unit` are computed by nothing (G8 §3.4).
- How: compute the two missing statuses from the self-test card and the journals; add `shadowed_live`; the checker refuses a binding below the slot's minimum.
- Ledger: `x1.block_trust_level`, `x1.min_trust_per_slot`.
- Sources: G8 §3.4, §3.11; SEEDS D43.
- Maturity: **solid**.

**X1-template-shape-40. Community packs with n8n's rules, and his signature before the money path.**
- What: outside packs follow n8n's community rules (R1 §4.4): a naming prefix, a manifest, no runtime dependencies, layer F deny-by-default, contract tests on install, a README, and a verified tier. A pack may land into the Library on install, but a block from it reaches a live profile only with his bound signature on the pin, the way a `money` app needs his signature to activate (G8 §6.1).
- Why: "white label software" (SEEDS A23) means others will add to it after he is gone (SEEDS D43).
- How: `pack.toml` validated like `app.toml`; the install runs `blocks_check` plus the socket contract on every block; the pin's `signature` field is checked by the loader.
- Ledger: `x1.pack_install_requires`, `x1.pin_signature_required_for_live`.
- Sources: R1 §4.4; G8 §3.2, §6.1; SEEDS A23, D43.
- Maturity: **plausible**; Question Q3.

**X1-template-shape-41. The raw-code hatch, quarantined.**
- What: `plain_python` at the profile level (a whole sizer or halt in one file) with the same layer F limits, and a quarantine: it runs in shadow (idea 37) for N trades and may never be the only brake at a scope.
- Why: n8n's Code node is the escape hatch every catalogue needs (R1 §4.4); the field exists and is ignored (G8 §1.1).
- How: the compiler reads `plain_python` for the risk slots only, after layer F; the checker demands a second, catalogued brake at the same scope.
- Ledger: `x1.plain_python_quarantine_trades`.
- Sources: R1 §4.4; G8 §1.1, §3.11.
- Maturity: **plausible**.

**X1-template-shape-42. Two adapters per slot from day one.**
- What: a slot is a real seam only when two adapters pass its contract (codebase-design). Ship two sizers (`fixed-fraction-at-stop@1` and one more), two halts at each scope, two derivations per number family, before calling the socket extensible.
- Why: "One adapter means a hypothetical seam" (Appendix B). The contract tests today test one sizer, long only (G8 §2.2).
- How: enrol Library blocks in the contract tests (G8 §2.2 weakness), add a short side, and keep two adapters per slot in the stdlib.
- Ledger: `x1.adapters_per_slot_min`.
- Sources: codebase-design; G8 §2.2.
- Maturity: **solid**.

### H. Agents and the copilot

**X1-template-shape-43. The tool rows agents need.**
- What: `risk_profile_new(preset, overrides)`, `risk_profile_check(document)`, `risk_profile_explain(document, number)`, `risk_resize_replay(trades, profile)`, `risk_scenarios_run(profile, scenario_set)`, `blocks_save(entry, source)` (a draft for his yes), `blocks_contract(entry)` (the socket contract on a Library block), `risk_placeholders_list(unit)`, `risk_ledger_query(id)`, `risk_state(node, scope)`, `derivation_preview(profile, number)`. All write drafts; none publishes, promotes or sends an order.
- Why: G8 §4.3 lists what is missing; "you need to build them tools" (SEEDS D42).
- How: rows in `qmx_control/catalog.py` with `approval: read | domain_write`; functions in `qmx_tools/functions.py`. The `build-unit` skill gets a sibling `build-risk-profile`.
- Ledger: `x1.agent_tool_rows`.
- Sources: G8 §4.1, §4.3; SEEDS D42, D43.
- Maturity: **solid**.

**X1-template-shape-44. The schemas agents need.**
- What: `qmx.risk-profile/1` (document), `risk-state/1` (runtime), `risk_event` body, `derivation_receipt` body, `proposal-card.ask` extended with `profile_version | adopt_default | restore_step`, the ledger row schema, the `book` and `bms` fields, `pack.toml`.
- Why: "we need schemas, obviously" (SEEDS D43).
- How: JSON schemas in the Library kinds plus a `qmf-data` journal kind body per row; every schema has an upgrader (idea 38).
- Ledger: `x1.schema_set`.
- Sources: SEEDS D43; G8 §3.7, §3.8.
- Maturity: **solid**.

**X1-template-shape-45. Sizing-only replay on a recorded trade list.**
- What: a QMB job that takes a trade list (from a backtest, paper or live) and re-sizes it under another profile without re-running the logic: money curve, drawdown, budget use, brake fires. QuantAnalyzer does this ("DOESN'T RUN A NEW BACKTEST", R1 §2.3); StrategyQuant's own equity-control test used it to find a null result.
- Why: "nothing tests sizing on its own" (G8 "What blocks it" 10). Trying a profile must cost seconds, not a backtest.
- How: a new run kind `resize` beside `whatif`; it reads the trade list's entries, stops and exits, applies the profile's `decide` and `on_event` with the guard's statistics replayed in order. Fast invalidation cuts must come from the recorded exit path, never hindsight (G11 §3.1, `CFS:1133`).
- Ledger: `x1.resize_replay_job`.
- Sources: R1 §2.3; G8 §5.3; G11 §3.1.
- Maturity: **solid**.

**X1-template-shape-46. The propose, shadow, card, click loop.**
- What: an agent drafts a profile version; the engine runs the self-test card (idea 07) and the resize replay (idea 45); the profile shadows live (idea 37); a card lands; he clicks; the node adopts at the next flat. Agents never touch money (G2 ruling 5).
- Why: "agents do most of the heavy lifting... I click and stuff" (SEEDS D41).
- How: workflow template `rp-profile-proposal` built from `_shared` blocks (unit-check, proposal card, lineage, conveyor). `dc-decay`'s tighten-only cards are the first producer; `p1` and `pp` already wait for this session (G8 §4.2).
- Ledger: `x1.proposal_loop_steps`.
- Sources: G8 §4.2; G2 ruling 5; SEEDS D41.
- Maturity: **solid**.

**X1-template-shape-47. "Explain this size" as a copilot skill.**
- What: from a decision row, walk the derivation receipts and the override chain and say it in ten words, with the long form a click away.
- Why: SEEDS D33 ("dumb it down for me"); the unit plan's UI notes already want "why a unit is not trading" in ten words (G11 §4.2).
- How: a skill over `risk_profile_explain` and `journal_query`.
- Ledger: none new.
- Sources: G11 §4.2; SEEDS D33.
- Maturity: **solid**.

**X1-template-shape-48. Layer H: the risk-couplings check.**
- What: a new checker layer that validates a profile against the ledger: every number id exists; its level and measure match the row; every `needs` is provided or has a fallback; every `affects` edge the ledger names is honoured (a number that affects another has a derivation on the other side); no `user` row is self-derived; the minimum trust per slot holds.
- Why: "how do they know that the things are correct?" (SEEDS D43). Layers A to G check shape, references, numbers, data, completeness, safety and behaviour (G8 §3.3); none checks couplings.
- How: `check/layer_h.py` reads the ledger snapshot (idea 50).
- Ledger: `x1.layer_h_rules`.
- Sources: G8 §3.3; G11 §1.2; SEEDS D43.
- Maturity: **solid**.

**X1-template-shape-49. Workflows that keep the template alive.**
- What: `rp-profile-proposal` (nightly: reads decay, drift and brake density; proposes one tighten or one restore step), `rp-upgrade-offer` (when a preset ships a new version), `rp-scenario-battery` (on every profile draft), `rp-brake-precision` (each brake's share of fires that needed action, R3 §5.6).
- Why: "agents must solve the issues... with workflows, not lists" (TLH 54).
- How: engine templates like `dc-decay-and-limit-report` (G8 §4.2), reading journals and landing cards.
- Ledger: `x1.workflow_set`, `x1.brake_precision`.
- Sources: G8 §4.2; R3 §5.6; TLH 54.
- Maturity: **plausible**.

### I. The ledger as data the template reads

**X1-template-shape-50. The ledger is the schema's source of truth, frozen into the compiled unit.**
- What: a profile's numbers must reference ledger ids. The ledger row carries level, measure, default derivation, inputs, affects, changed_by, and the identity effect of a change. The compiler freezes a snapshot of the rows the profile uses into the compiled unit, so the node reads no Library at trade time.
- Why: "a ledger with couplings has never existed as data, except July's formula inputs" (G11 "What this adds" 1). The ledger must be "part of the deliverable" (TLH 52).
- How: `ledger/variables.yaml` (v0, being built) is the planning file; a `ledger` Library kind holds the released snapshot the checker and compiler read. The planning file and the released snapshot are the same rows at two stages (Collision 10).
- Ledger: `x1.ledger_snapshot_in_compiled_unit`, `x1.ledger_kind`.
- Sources: G11 §1; TLH 52; G2 ruling 11.
- Maturity: **plausible**.

**X1-template-shape-51. `affects` edges run, not only read.**
- What: when a number moves (a calibration row), the guard recomputes the numbers its ledger row `affects`, writes their receipts, and refuses a move that would push a dependent out of its range. "When this happens, how is the other one affected" (SEEDS D50) is executed.
- Why: history shows hidden couplings doing damage: the bench count doubled as the sizing divisor (G11 §1.2, the B split).
- How: the guard holds the `affects` graph from the snapshot; a move triggers a topological recompute; cycles are refused at compile.
- Ledger: `x1.affects_graph_runtime`.
- Sources: G11 §1.2; SEEDS D50.
- Maturity: **plausible**, leaning **wild** (it makes the ledger a runtime engine).

**X1-template-shape-52. The ledger generates the Numbers tab and the settings forms.**
- What: the UI builds every risk form from ledger rows (group, level, measure, chain, changed_by, range), the way n8n builds a node's form from `properties` and StrategyQuant from `@Parameter` (R1 §8 point 6). No hand-built risk screens.
- Why: "configurable = UI-editable always" (operator standing rules); the unit plan's UI notes already want a Numbers tab with every number, its range and its last move (G11 §4.2).
- How: a `ledger_rows(unit)` read for the UI; the UI session renders by `measure` and `changed_by`.
- Ledger: `x1.ui_from_ledger`.
- Sources: R1 §8 point 6; G11 §4.2.
- Maturity: **plausible**.

**X1-template-shape-53. Every row names its equity series and base.**
- What: any money rule's ledger row states `equity_series ∈ {realized, marked}` and `equity_base ∈ {unit_start, day_start, period_open, high_water_mark, fixed_floor}`. "5 % drawdown" has meant four different things across generations (G11 §2.2).
- Why: the halt blocks assume marked equity that no host supplies (G11 §2.2); cTrader equity is read once at sign-in (G9 §3.3).
- How: two fields on the row; the guard computes each series and base it is asked for; the checker refuses a rule whose series the host cannot supply (idea 06).
- Ledger: `x1.equity_series`, `x1.equity_base`.
- Sources: G11 §2.1-2.2; G9 §3.3; R1 §8 point 12.
- Maturity: **solid**.

**X1-template-shape-54. A fail mode on every piece.**
- What: each number, brake and derivation declares what happens when its inputs are missing or the guard is down: `fail_closed` (no new entries), `fall_back_to_default`, `fall_back_to_position_rules`. Brakes default to fail-closed; derivations to the default; the board read today fails open (G9 §4.3) and isolation needs the other way round.
- Why: "what to do when the risk layer is down is decided up front, and the answers differ" (R1 §8 point 13).
- How: `fail_mode` on the ledger row and the binding; the guard honours it; the stand-down table gains a `guard_unavailable` row.
- Ledger: `x1.fail_mode`, `x1.guard_unavailable_action`.
- Sources: R1 §8 point 13; G9 §4.3.
- Maturity: **solid**.

**X1-template-shape-55. Counting rules declared per brake.**
- What: every loss-counting brake states its counting rule: `full_stop_only`, `stop_outs`, `by_size_r`, `at_or_worse_than_q`; whether fast-invalidation cuts, breakevens and forced flats count; and whether it counts in number, R or money. History has four rules (G11 §3.5).
- Why: "brakes must count fast invalidation and the exit mechanisms" (SEEDS A28). The chassis provides the field; the brakes layer picks values.
- How: a `counting_rule` parameter on halt blocks, read from the ledger row; the trade row must carry the exit reason (idea 59).
- Ledger: `x1.counting_rule`, `x1.counts_fi_cuts`, `x1.count_unit`.
- Sources: G11 §3.5; SEEDS A28.
- Maturity: **solid**.

### J. What must change in the shipped stack

Each is a concrete change; most directly from G8 "What blocks it today" and G9 "What is missing".

**X1-template-shape-56. Compiler format 2.** Run halts and reads; add `derivation` components; let a sizer-bound number move through a derivation; read `markets[].settings`, `sessions`, `position_limit`, `plain_python` (for risk slots) or remove them (Problem P12). `compiler.py:496-499`. **Solid.** Ledger: `x1.compiler_format`.

**X1-template-shape-57. The guard, built.** Idea 12 as a package consumed by `qmb/host/unit_handler.py` and `qmn/app/runtime.py`; it computes the halt inputs, open risk, exposure per bet key, budget used; calls `before_order`; feeds `Runtime.risk_stop` (today called only by tests, G9 §1.1); emits `RiskState`. **Solid.** Ledger: `x1.guard_statistics`, `x1.risk_state_fields`.

**X1-template-shape-58. The sizer's inputs widened.** Balance, marked equity, open risk, the unit's own record with costs, the cost profile for this hour, currency conversion, his limits, budget share, trading state; a real receipt instead of the hard-coded one (`protocol/unit.py:799-802`); one unit-scope state beside the per-market instance (Problem P11). **Solid.** Ledger: `x1.sizer_inputs`.

**X1-template-shape-59. Trade rows carry the exit reason, session, streak, equity before and costs.** The Library `trade` kind has the fields; the journal row does not (G9 §7.1). A time exit, a signal exit and an FI cut all read `close` today (G11 §3.4). **Solid.** Ledger: `x1.exit_reason_code`.

**X1-template-shape-60. Exits after entry run.** Every per-bar exit gets the position; `amend_protection` and `close_partial` are sent; the six silent A13d exits light up (G8 §1.4, §3.5). **Solid.**

**X1-template-shape-61. The risk-stop reason code fixed.** A risk stop's text maps to `kill_switch` today (G9 §1.4); map it to `risk_stop`, so brake density can be counted. **Solid.**

**X1-template-shape-62. Node numbers as config and UI keys, not constants.** Stand-down thresholds and kill effects are code constants (G9 §1.4). Give each a ledger row with `changed_by: user`. **Solid.** Ledger: `x1.node_constants_to_rows`.

**X1-template-shape-63. Identity labels for the profile** (idea 34). **Solid.**

**X1-template-shape-64. Agent rows** (idea 43) **and the socket contract on Library blocks** (G8 §2.2 weakness). **Solid.**

**X1-template-shape-65. The Library kinds filled.** `risk-profile` (new), `template`, `book`, `bms`, `pod` with fields and checkers; a lander for them from a `runs` app (G8 §6.4). **Plausible.**

**X1-template-shape-66. Facts the template needs, produced.** cTrader equity that refreshes (G9 §3.3); a commission key on the instrument record; a writer of the 168-hour cost profile from bar and order rows (G9 §5.2-5.3); a slippage script over node order rows (G9 §3.4). **Solid**; owned with the sizing layer.

**X1-template-shape-67. Scope keys the isolation layer will need.** A `class:` and `region:` scope beside `instrument:` in the kill switch and the stand-down table (G9 §4.4); the feed relay started; a fail-closed placement option. **Solid**; owned by the isolation and brakes layers, but the chassis must carry the scope (idea 18).

### K. Observability the template owes

**X1-template-shape-68. `RiskState`, emitted every pass.**
- What: per unit, book and account: equity series and base, drawdown, open risk, exposure per bet key, budget used, each brake's state and distance to trip, the trading state per scope, the last derivation receipts, the kill level now. The node emits health today, not risk (G11 §0.10).
- Why: "how do we know that this is wrong, this is right, it's working, it's up, it's on" (SEEDS D49). The watcher's README says these rows are "the risk session's" (G11 §4.1).
- How: a `risk_state` node journal row and a `risk_state(node, scope)` read; the watcher and the phone pushes read it.
- Ledger: `x1.risk_state_fields`, `x1.risk_state_emit_interval_s`.
- Sources: G11 §4.1, §4.3; SEEDS D49.
- Maturity: **solid**.

**X1-template-shape-69. UI needs from this layer, for the UI session** (Appendix C). **Solid.**

### L. Wild

**X1-template-shape-70. A central risk oracle.** One RiskGate-style service answers `approved / size / reason` for every unit (R1 §3.2). It breaks "units stand alone" and is a single point of failure; RiskGate's own author calls it overkill for one strategy per account. Kept because the BMS-level breaker he describes (SEEDS C27) is an oracle in disguise. **Wild.** Ledger: `x1.oracle_mode`.

**X1-template-shape-71. Profiles that learn.** The `learned` motion mode exists and is refused (G8 §3.10). A profile may bind a learned derivation only behind shadow-first (idea 37) and a counted try. **Wild.**

**X1-template-shape-72. A profile marketplace in the Library.** Presets and packs with cards, trust levels and results, browsable like the dictionary. **Wild**; depends on ideas 40 and 14.

**X1-template-shape-73. Profile variants as a genome.** Treat a profile as a vector of choices inside ranges; agents mutate within the ranges (the old WF1/WF2 variant pipeline, G10 §0.6, applied to risk), evaluated by resize replay and the scenario battery, counted as tries, shrunk toward the pooled result (G2 §5). **Wild**; collides with "don't chase performance across units" (R3 §5.5).

**X1-template-shape-74. Overrides by context word.** Once `reads` compile, overrides keyed by an MIS reading word (`regime: mean-reverting`) rather than by session. "Thinking in context, not sessions, makes sense" (SEEDS reply 17). **Plausible**; depends on idea 56 and the relay (G9 §4.3).

**X1-template-shape-75. The dry chassis.** A unit whose logic is random entries with the full template on, run through the resize replay and the scenario battery, to measure what the risk layer alone does to the money curve. R2 §9: sizing cannot create an edge, and this is the test that proves it in QMX's own numbers. **Plausible**.

**X1-template-shape-76. The template on his PC and on the node at once.** The same compiled unit and guard run on the PC (QMB, paper, shadow) and on the node (live); the PC is home and the node substitutes (memory: PC is home, servers substitute). The profile carries a `runs_on` list; the ledger snapshot travels with it. **Plausible**; SEEDS C23.

---

## 2. Problems and proposed solutions

Each open problem in this layer, with at least two options and their trade-offs. **[judgment]** throughout on the trade-offs. No picks.

**P1. Swapping the placeholder sizer or adding the first halt makes every unit a new unit, so the rip-out costs each unit its record (G8 §3.6).**
- (a) Split the identity labels: `profile_version_change` → new version (idea 34). Keeps the record; needs his ruling because it changes what counts as a try and what needs a click (Q2).
- (b) Keep the table; carry the *logic* record in R across the swap and restart only the *money* record (idea 35). No table change; the judge already works in R; the UI must show two records.
- (c) A one-time migration: label the rip-out `ambiguity_resolved` (already a new version, not a new unit) with his click per unit. Cheapest now; it does not solve the next swap.

**P2. A number bound only to the sizer cannot move, so a self-tuning `risk_fraction` refuses to compile (G8 §3.10).**
- (a) The `derivation` component and a compiler rule that a sizer-bound number may move through it (ideas 23, 56). Clean; one compiler change; derivations get the same layer F limits.
- (b) Bind the number to a logic-slot stamp as a workaround. No compiler change; a hack that ties sizing to entry logic and breaks the deletion test.
- (c) The guard overrides the fraction from outside the unit each pass. Keeps the compiler; moves self-configuring out of the unit, against "self-configuring remains at a unit" (SEEDS D32).

**P3. Unit- and account-scope statistics have no producer (G9 §1.3).**
- (a) The guard module with two host adapters (idea 12). One code path for backtest and live; a new package.
- (b) Blocks compute their own statistics from the `trades` stream. No host change; per market only, so no cross-unit or account view (G8 §5.3).
- (c) An app publishes them like the MIS board. Breaks ruling 11 (no Library or feed at trade time) and fails open today.

**P4. Where the Book and BMS level lives.**
- (a) `book` and `bms` documents compiled into guard config (idea 13). Fits "the Book is the skeleton"; the kinds exist; needs schemas and checkers.
- (b) The Lab spine's pod bundle compiled through `PodCompilerPort` (idea 14). Fits "pods are mini apps"; the Lab is unbuilt (G8 §6.2).
- (c) A central oracle (idea 70). Simplest to picture; a single point of failure and against standing alone.

**P5. Outside code in the money path.**
- (a) Trust ladder plus contract tests plus shadow trades (ideas 39, 37). Any origin may reach live by evidence; most machinery.
- (b) Only `qml` and `human` origins may size live; agent and community code limited to derivations and brakes. Less machinery; shuts the door he asked to open (SEEDS D43).
- (c) His signature on every live pin (idea 40). Least code; every change costs his click.

**P6. Derivation expressiveness against safety.**
- (a) Blocks only. Safest and testable; a non-coder cannot write one without an agent.
- (b) A small expression form compiled to a block (idea 28). Readable by him and the copilot; a parser to write and a name list to keep.
- (c) Both. Most freedom; two things to document.

**P7. "The unit stands alone" against account rules that need cross-unit data.**
- (a) The guard is part of the node process, not the Library, so standing alone holds at node level. The unit depends on the node; it already does.
- (b) Each unit receives a frozen account snapshot each pass and applies account rules itself. No guard; every unit repeats the account maths, and two units may disagree.
- (c) Account rules only in the kill switch, by his hand. No code; no automatic brake above the unit, against SEEDS C27.

**P8. What happens when the guard or a fact is unavailable.**
- (a) Fail closed for new entries (RiskGate). Safest; a flaky fact stops trading.
- (b) Fall back to the unit's own position-scope rules (freqtrade's fallback). Keeps trading; loses the account view while it matters most.
- (c) Enter `REDUCING` (idea 08). A middle; needs the state machine.
- The chassis answer is idea 54: declare it per piece and let the brakes layer set defaults.

**P9. Paper sizes from the demo account's $10,000, not the unit's live share (G9 §3.1).**
- (a) A `budget_share` number carried by the deployment, read by the sizer in every lane. One number; paper and live then size alike.
- (b) A virtual account per deployment with its own equity series. Cleaner books; more host code.
- (c) A configured paper notional seed. Cheapest; paper still differs from live when shares change.

**P10. The judge is size-blind, so nothing judges a profile (G8 §5.3).**
- (a) The resize replay with money measures (idea 45). Cheap per try; a new run kind.
- (b) The scenario battery (the scenario layer). Tests tails; needs the battery first.
- (c) Both, landing a `profile-verdict` record. Most complete; two jobs to build.

**P11. One sizer instance per market, so unit-level memory (house money, a unit streak) has no home (G8 §1.4).**
- (a) Unit-scope state kept by the guard and passed to every instance as a fact. Matches the levels idea; the sizer stays stateless per market.
- (b) A `unit_state` stream the sizer reads and writes. Keeps it inside the unit; two instances may race on one unit.
- (c) Accept per-market state. No change; house money per market, which is not what he described.

**P12. Nine fields are parsed and then ignored (G8 §1.1).**
- (a) Remove the ignored fields now and re-add each when a compiler format reads it (subtract before add). Honest; a schema change with an upgrader.
- (b) Make the checker *error* on a set-but-ignored field. Cheap; the fields stay as traps for agents.
- (c) Implement all nine in format 2. Most work; some (routes, baseline) are not this session's.

**P13. Records split per market only; timeframe and session axes have no data (G7 §0.8).**
- (a) Extend record keys to (market, timeframe, session) and the trade row with `session` (idea 32). Needed for per-session brakes; more rows to keep.
- (b) Derive session and timeframe at query time from bar rows. No schema change; slower and lossy.
- (c) Treat timeframe as a unit-version property only. Status quo; one unit per timeframe.

**P14. Agents cannot finish a new risk block (G8 §4.3).**
- (a) `blocks_save` as a draft row plus `blocks_contract` (idea 43). Direct; his yes stays the gate.
- (b) `u3`-style artifacts he saves by hand. No new rows; slow.
- (c) The Lab sandbox first (`bc-build-a-component` waits for it). Right long-term home; unbuilt.

**P15. Two state machines on the node: the template's trading states and the kill switch's four levels.**
- (a) Map kill levels onto trading states (YELLOW → HALTED at scope without flatten, RED → HALTED with flatten, BLACK → HALTED at all). One vocabulary; the kill switch stays his hand.
- (b) Keep both; the guard reads the kill level as a fact. Two vocabularies; less change.

---

## 3. Collisions noticed

Named, not resolved.

1. **A separate profile document against "the unit stands alone".** Idea 01 embeds at compile, but two versions now describe one running thing (unit version and profile version), and the snapshot rule (a different fingerprint starts cold, G8 §3.7) would cold-start logic blocks on a profile-only change (idea 36).
2. **Derivations at the host against "self-configuring remains at a unit" (SEEDS D32).** Ideas 12 and 23 put account facts in the guard and derivations in the unit; P2(c) and P7(b) are the two ways it can fall.
3. **Idea 34 changes the identity table's meaning of a counted try.** His rulings (G2 ruling 1, 4) tie clicks to the table; a profile row with "no click before live" would be a new automatic path.
4. **Edge as a dial (idea 26) against both the lead's edge-led basis and his "don't lean on the edge".** The chassis makes both expressible; the sizing layer must pick a default, and the funnel must not read "expressible" as "agreed".
5. **Book/BMS documents (idea 13) against the Lab spine's pod that compiles to Book and BMS fragments (AD-11).** Two compile targets for one level.
6. **`HALTED` must still run exits (SEEDS C21), but Nautilus's `HALTED` denies even protective stops (R1 §6.1).** Idea 08 must not copy Nautilus here.
7. **Overrides by timeframe and session (idea 32) against records per market only (G7 §0.8).** The axis exists before its data.
8. **Community packs (idea 40) against "agents never touch money" and "only trading-node holds keys".** A pack can land in the Library; nothing may put it on the node without his signature; the install path and the money path must be different doors.
9. **A fail-closed guard (idea 54) against the board read that fails open by design (G9 §4.3).** Two opposite defaults on one node.
10. **The ledger as a planning file against the ledger as a runtime snapshot (idea 50).** Which one the node reads, and who releases a snapshot, is undecided.
11. **Trading states per scope (idea 08) against the kill switch's four levels (G9 §1.1).** P15.
12. **`applies_to_open_positions` defaults false (G8 §1.1) against `REDUCING`, which must touch open positions by amend-only.**
13. **The old Book door (formats 1 and 2, "the bot may not size") still in code (G2 §6)** against a unit that sizes itself through its profile. Keep as the BMS door, reuse, or delete.
14. **Count brakes scaled to trade count (lead's sim, STATE item 10) against "circumstantial, let's first explore" (SEEDS E27).** The chassis only gives the field (idea 55); the brakes layer and he decide.
15. **Paper as a zero-slippage simulation (G9 §3.1) against "the unit trades the same way on both, only the account differs" (SEEDS D13).** The profile is the same; the fills are not.
16. **Idea 51 (affects edges run at runtime) against "design for complexity, not a complex system".** It may be the "too much machine" of this generation.
17. **Idea 73 (profile genome) against R3 §5.5 (do not chase performance across units) and against luck as a non-argument.**
18. **Idea 70 (oracle) against G2 rulings 6 and 11.**

---

## 4. Questions only he can answer

1. **Vocabulary.** On screen and in agent prompts: "risk profile", "chassis", "pack", "preset", "pod" (bundle) and "book" (document). Which words does he want, and which does he refuse? He cares about terminology (SEEDS D37).
2. **Record on a sizer swap.** May a profile version change keep the unit's record and skip the "new unit" path (idea 34), given that it changes what a counted try and a click mean (G2 rulings 1, 4)?
3. **Outside code and money.** May a community or agent block ever size a live trade, with his signature on the pin and shadow trades first, or never (P5)?
4. **Irreversible scope.** Book and BMS as Library documents compiled into the guard (idea 13), or as a pod bundle through the Lab (idea 14)? The two set different build orders.

---

## Appendix A. The roundtable (party mode, session mode, non-interactive)

Five voices. 🏗️ **Ada**, platform architect. 🧮 **Quill**, quant developer. 🛡️ **Marguerite**, pod-shop risk manager. 🧩 **Noor**, no-code product designer. 🎙️ **The operator's voice**, his own words only, quoted from the seeds. Topic: what the chassis is, and where it bends. Three rounds, then a close.

**Round 1: what is the thing?**

🎙️ **The operator's voice:** "the template is at the same time, should I say a prime baseline, but I can improve it, all right? In any way, shape or form."

🏗️ **Ada:** Then it is a schema with presets, not a system with options. One document type, `risk-profile`, pinned by version, embedded at compile. Everything else is a preset or a pack. If the schema changes every time he twists an angle, we have failed.

🧮 **Quill:** A schema is paper. The sizer today gets four inputs and a hard-coded receipt. Until the host passes open risk, costs and the record, your profile is a form that describes a function nobody can call.

🛡️ **Marguerite:** You are both describing the trade level. My book never had a problem at the trade level. Our losses came from ten books that thought they were independent. Where is the parent limit? Where is the co-loss factor? If your document cannot say "the BMS limit is less than the sum of the books", it is a toy.

🧩 **Noor:** And none of you have said how he sees it. He said "if you say 10%, where does it come from?" If the answer is a block id, we lost him. The form has to show the chain: preset, class, instrument, unit, and which one won.

🏗️ **Ada:** The chain is in the document. `markets[].settings` is already parsed. It is ignored by the compiler, which is a one-file fix.

🧮 **Quill:** "One-file fix" is how the April system got nine multipliers.

**Round 2: where does it bend?**

🎙️ **The operator's voice:** "how do we technically design this or make something that can handle any amount of stress without it?"

🏗️ **Ada:** Stress means a new brake, a new level, a new sizing basis. Three seams: a slot contract for blocks, a level field for scope, a derivation for defaults. If all three hold, the schema never changes.

🛡️ **Marguerite:** You forgot the fourth. What happens when your guard is down at 02:00 New York with gold open. RiskGate rejects everything. freqtrade trades on. You have to write that down per brake, or someone decides it at 02:00.

🧮 **Quill:** Agreed, and it goes in the ledger row, not in code. Fail mode is a variable.

🧩 **Noor:** Then every row has: level, measure, who changes it, fail mode, and the chain. That is a form I can generate. I do not want to hand-build a risk screen for every brake he adds.

🏗️ **Ada:** The ledger generates the form. n8n does that from `properties`.

🎙️ **The operator's voice:** "What if I want to change the way it is derived?"

🧮 **Quill:** Then the derivation is a block, and swapping it is a version. But he does not write blocks.

🧩 **Noor:** So give him an expression. `equity × fraction ÷ stop`. He reads that.

🏗️ **Ada:** An expression that compiles to a block, so the loader and layer F see only blocks. Two faces, one artefact.

🛡️ **Marguerite:** And every derived value writes a receipt. If I cannot read why the size was $9 yesterday and $7 today, I cannot run the book.

**Round 3: the fight**

🧮 **Quill:** Here is the one you are all walking around. Swap the placeholder sizer and the identity table makes every unit a *new unit*. The record is gone. Every backtest QMB ran is for a unit that no longer exists.

🏗️ **Ada:** Add two labels: `profile_version_change` is a new version, not a new unit.

🛡️ **Marguerite:** That is you deciding what counts as a try. In my shop that is a committee question, not an engineer's.

🎙️ **The operator's voice:** "Only he promotes; nothing enters live without him."

🧮 **Quill:** There is a way that needs no ruling. The judge is size-blind. It reads R. Keep the logic record in R, start a new money record per profile version. Two records, no table change.

🧩 **Noor:** Two records is two numbers on a card. He will ask which one is real.

🛡️ **Marguerite:** Both are real. R says the idea works. Money says the sizing works. I have fired people for confusing them.

🏗️ **Ada:** Then the card shows both, and the table gets the label anyway so the next swap does not cost a record. Both options go up. He picks.

🧩 **Noor:** And "pod". He says pods are mini apps. He also says a pod is the book. If we ship a thing called a pod that is a bundle of a book plus packs, is that one word doing two jobs?

🛡️ **Marguerite:** In a real pod shop the pod is the people and the book is the positions. He merged them. Do not un-merge them for him. Ask him.

**Close.** The room did not agree. It produced: the profile as a document (idea 01), the chain on screen (ideas 29, 33), fail mode as a variable (idea 54), expressions that compile to blocks (idea 28), receipts (idea 24), two records (idea 35), the parent-limit slot (idea 21), and two questions for him (Q1, Q2).

---

## Appendix B. The chassis in deep-module words

From `codebase-design`: a **module** has an **interface** and an **implementation**; a **seam** is where the interface lives; an **adapter** satisfies the interface at a seam; **depth** is behaviour per unit of interface; one adapter means a hypothetical seam, two means a real one.

| Module | Interface (what a caller must know) | Seam | Adapters today | Adapters needed |
|---|---|---|---|---|
| Risk template (profile) | `decide`, `on_event`, `state`; the needs list; the fail modes; the version pin | the host call in `protocol/unit.py` | QMB host, node host (one code path, G8 §2.4) | none new; the two hosts are the two adapters |
| Sizer slot | `Size` or skip with reason; inputs list | block contract (`api.py:150-156`) | `fixed-fraction-at-stop@1` | one more (two-adapter rule, idea 42) |
| Halt slot | `None`, `Halt{action, scope, reason}` | block contract (`api.py:167-185`) | five blocks, none run | the guard as caller |
| Exit slot | a level or a signal; planned `close_partial`, `amend_protection` | block contract (`api.py:159-164`) | three run, six silent | the runtime change (idea 60) |
| Derivation | `value` from `facts` and `current`, with a receipt | a new component type | motion rules (two modes) | boot, schedule, record, state derivations |
| Guard | statistics per scope; `before_order`; `RiskState` | a new package with two host adapters | none | QMB and node |
| Override resolver | resolved values with provenance path | the compiler | none (settings ignored) | one, in the compiler |
| Ledger snapshot | rows by id with level, measure, affects, fail mode | the checker (layer H) and the compiler | none | planning file → released snapshot |
| Lander for risk kinds | land `risk-profile`, `template`, `component`, `book` | the app road | QMB's `backtest-result` lander | a risk-kinds lander |
| Agent rows | drafts in, checks out; never publish | `qmx_control/catalog.py` | unit and block rows | the rows in idea 43 |

**Deletion test.** Delete the guard: the account view reappears in two hosts and disagrees. Delete the profile document: the risk fields stay inline in every unit and a per-type template is a copy-paste. Delete the derivation type: self-configuring is two motion modes and a refusal. Each earns its keep.

**Internal seams.** The sizer, halts, exits and derivations are internal to the template module. Their contract tests are the template's own tests. The host tests only the three verbs. If a host test needs to reach a slot, the shape is wrong.

---

## Appendix C. UI needs from this layer (for the UI session)

1. A Numbers tab generated from ledger rows: level, measure, value, range, chain with the winning level, last receipt, who may change it (idea 52).
2. "Explain this size" from any decision row, ten words first (idea 47).
3. A profile card: version, preset, packs, self-test results, placeholders left, shadow comparison (idea 07).
4. Trading state per scope with the reason and the distance to the next trip (ideas 08, 68).
5. An upgrade offer inbox: adopt a new default, a new profile version, a restore step (ideas 31, 46).
6. Both units of measure on screen for every money row (TLH 9), and the equity series and base named on every money brake (idea 53).
7. A derivation preview before saving (idea 27).
8. A pack and preset browser with trust levels (ideas 39, 72).

---

## Appendix D. Not covered

- No numbers. Every default and factor named here is a slot for the numbers lens.
- No web reading; every outside claim comes through R1, R2 and R3, with their own grades.
- I ran no code. Claims about the stack are from G8, G9, G11 and five spot checks at d02af358 (the compiler refusals, the identity table and its Settings defaults, `NumberSpec` and `Fallback`, the Library kinds, the journal kinds).
- The brakes, sizing, scenario, edge-verification, observability and agents layers own their content; this file only gives them slots and names the collisions.
