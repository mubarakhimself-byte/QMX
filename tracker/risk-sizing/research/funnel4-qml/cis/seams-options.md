# Seams options for QML (knots 2 and 5)

Written 2026-10-30 by the QML-depth CIS agent with the `codebase-design` skill (SKILL.md and DEEPENING.md read). Its vocabulary is used exactly: **module**, **interface**, **implementation**, **seam**, **adapter**, **depth**, **leverage**, **locality**, the **deletion test**, and "one adapter means a hypothetical seam, two adapters means a real one". These are **options for where seams could go, not a design**. Nothing is chosen. Exits and sizing appear only as slots; their maths is the risk session's (`ST:145`). Keys and labels as in `problem-solving.md`.

His framing of the aim (CHECKED, `T1:1211`): "some sort of framework or library... which agents can use to build units easily, monitor them, something that is simple on the eyes... JSON schemas, simple architecture... In the back it can be complex. There is this idea of deep modules... very complex things represented by simplified ways of seeing things."

---

## 0. What exists today (the modules and seams QML already has)

All CHECKED on `EB` (`d82be318`).

| Module | Interface (what a caller must know) | Seam it sits at | Adapters today |
| --- | --- | --- | --- |
| Runtime protocol | A factory built with (declaration, resolved assignment, read surfaces) returns a callback driven per evaluation instant; no clock, I/O, network or undeclared randomness | Between host (QMB, node) and bot logic (`qml/src/qml/protocol/contract.py:31-35`; `qml/examples/conformant_bot/bot.py:1-9`) | QMB replay and the never-deployed node: two hosts, so a real seam |
| Intent door | Callback returns entry and exit intents; `requested_r` refused; venue commands never enter | Between bot and money (`qml/src/qml/protocol/intents.py:1-7`) | One: the Book. Hypothetical for units |
| Declaration (CT-33) | Strategy family, confluences, parameter space, footprint | Between author and registry (`GL:134`) | One registry |
| Parameter space | Type, bounds, step, mandatory default, hard constraint, unit kind, UI flag (`qml/src/qml/declaration/parameters.py:1-7`) | Between declaration and any tuner | QMB optimiser reads it through a sampler port with a TPE-class default adapter (`qmb/src/qmb/optimize/__init__.py:1-11`) |
| Confluence (CT-34) | Legs of role `level | trigger | confirmation | filter`, each a producer binding; conditions forbidden (`qml/src/qml/declaration/confluence.py:51-61, 82-89`) | Between bot and producers (indicators, structures) | Producer fingerprints and producer templates (`GL:683`) |
| Stage 0 research | Hypothesis with dictionary cites, role bindings, a boolean/temporal/lifecycle graph, five classes, five exit slots with four labels; never sizes, never executes (`qml/src/qml/research/stage0.py:61-101`) | Between source and governed bot | One |
| Graduation collapse | Maps `level`, `location` to `level`; `trigger`, `confirmation`, `filter` stay; the rest to "Python WHEN" (`qml/src/qml/research/collapse.py:49-75`) | Stage 0 to CT-34 | One |
| ATC / PolicyPair | A complete second trading system: AccountingPolicy plus RiskPolicy (`max_gross`, `halt`, `sizing`, `override_principal`), Book keys absent (`qml/src/qml/declaration/alternative.py:1-41`; `GL:66`) | Between a strategy and a non-Book money policy | QMB `execution/alternative.py` (via R01:144) |
| Workflow `rule` node | A safe expression over inputs routing to `true` or `false` port (`qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/rule.py:1-2`; expression language `…/definition/expr.py:1-8`) | Inside the agent workflow engine, not the trading path | One |
| Indicators | Six wrappers run: SMA, EMA, WMA, RSI, MOM, ROC (via R34 §4) | QMF producers | n/a |

**Deletion test on today's QML (INFERRED).** Delete the confluence module: the bot logic still runs, because conditions live in Python. Only registration and the footprint completeness law lose information. So the confluence is **shallow** for running and **deep** only for identity and audit. Delete the parameter space: QMB optimisation, UI editing and the canonical assignment all break across many callers. It earns its keep.

---

## 1. The gold mine's three layers against today's code (knot 2)

The three layers, as designed 24 Aug (FG 831, CHECKED by R39 C2): "Primitive dictionary 'What things exist?' / Role bindings 'What job does this primitive perform here?' / Strategy logic graph 'How are the bound components combined?'". Pillars became "a convenient human view" over them (GM 3261, CHECKED by R39 B4).

| Layer | August design (R39) | Today's code (CHECKED) | Gap (INFERRED) |
| --- | --- | --- | --- |
| Primitive (building block) | Role-neutral concept with 19 fields incl. "candidate detection algorithms", "existing code", "MIS labeler mapping" (C10) | Dictionary prose in `S/`, parsed by `qml.research` from host bytes (R34 §4.1); producers in QMF (six indicators, one structure family) | No link from a dictionary slug to a runnable producer. The block catalogue is missing (R18 via R34 §4.1). |
| Role binding | Role, profile, pair, timeframe, session, direction, timing, bar semantics, dependencies, evidence (D8) | Stage 0 `RoleBinding`; CT-34 leg = (role, producer binding, declared parameters) | CT-34 carries role and parameters but not timing, session or direction per leg; those fall to Python |
| Graph | ALL, ANY, NOT, K_OF_N, sequence, within, arming, reset, cooldown, re-entry; long/short branches (`DNA:69-84`) | Stage 0 `Graph` (boolean, temporal, lifecycle), never compiled (`GL:420`) | No executable graph. Confluence is explicitly not a graph (`GL:420` homonym note). |
| Views (pillars, lenses) | Four, seven, eight or nine lenses over the same record (R34 §2.6) | None in code | Views have no home; the UI unit tabs are Logic, Results, Family tree, Markets, Versions (R18 via F3G) |
| Ports | Named ports `setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`; composites import ports, never insides (E4) | None in QML; workflow nodes have ports (`registry.py:44-58`) | Combining units has no seam |

**Roles beyond four (C3, CHECKED by R39).** "context, trigger, confirmation, veto, exit, target, sizing modifier, or regime detector". Today's closed-and-addable set has four (`confluence.py:82-89`). "Sizing modifier" matters now that the unit owns sizing (R39 §4 item 2).

**A whole bot as an input (C5, CHECKED by R39).** "I had an idea of using a mini scalper for an indicator" (FG 796). Never answered. A unit's output as another unit's block.

**The unit owns its exits and size (`ST:21`, `ST:145`).** Today the intent door and the Book own them (C-Q1, C-Q2 in `problem-solving.md`).

---

## 2. Where the seams could go: seven options

Each option names its interface, what is deep behind it, its adapters, the deletion test, and how it meets the five pressures: self-tuning (knot 1), plain Python (`ST:47`), standing alone (`SO` 10), the risk socket (knot 5), and speed on the node.

### S1. The unit is one deep module behind today's callback (code-first)

- **Interface.** `factory(spec, assignment, read_surfaces) -> callback(instant) -> intents`, extended so intents may carry size and exits.
- **Deep inside.** Everything: the rules, the blocks (imported QML functions), exits, sizing calls.
- **Adapters.** Any Python logic is an adapter. QMB and the node are the two hosts. Real seam.
- **Self-tuning.** Only declared parameters are visible (§0). The "if" stays opaque. Motion and authority could be added as parameter fields.
- **Plain Python.** Native. A plain-Python unit and a QML unit look the same at the seam.
- **Standing alone.** Strong: the callback needs only its read surfaces.
- **Risk socket.** A library module the logic calls, or a slot in the spec the host fills.
- **Deletion test.** Deleting QML's block functions pushes complexity into every unit's Python: QML earns its keep as a function library.
- **Cost.** Smallest change from today (the intent door law and `GL:150`).
- **Risk.** Hidden thresholds; the analyst agent reads code, not structure (P4 in `design-thinking.md`).

### S2. The unit is a declared rule graph that QML interprets (data-first)

- **Interface.** A JSON graph: bound blocks as nodes, operators as edges (the DNA E set plus a weighted-sum-with-threshold operator, R36 §0 item 6), coordinates per binding, exits and size as typed slots. One QML runtime evaluates it.
- **Deep inside.** The interpreter, the block catalogue, state machines (armed, cooldown), replay parity.
- **Adapters.** Each block is an adapter behind a small block interface (inputs, settings, typed output). A "python" block lets any node be plain code.
- **Self-tuning.** Every N, S, B and K is visible; motion and authority can sit on each node (`problem-solving.md` K1-2, K1-3).
- **Plain Python.** As a block, or as a whole unit through S1's door kept beside it.
- **Standing alone.** Strong if the interpreter ships with the unit on the node.
- **Risk socket.** Typed slots in the graph (initial stop, targets, management, size, halts) filled by blocks the risk session ships.
- **Deletion test.** Deleting the interpreter breaks every declared unit at once: deep, high leverage, high locality.
- **Cost.** Reverses DEC-0175 (conditions forbidden in declarations, `QD:82`); a new runtime.
- **Risk.** Speed per quote; expressiveness ceiling (some rules are easier in Python); a second language for agents to learn. Matches his seed: "Most of it is JSON... very similar to a workflow. Because these are just conditionals" (`T2:779`).

### S3. A fixed-port shell, MT5 Wizard style (ports-first)

- **Interface.** A unit is a shell with a few named ports: context, signals (each with a strength and weight), entry order, exit set, sizer, halts. Each port takes any adapter that meets that port's small interface.
- **Deep inside.** The shell's fixed order of evaluation (signal vote, open/close thresholds, then exits, then size), journal writing, replay parity.
- **Adapters.** Many per port: QML blocks, plain-Python classes, ML models. Real seams by construction.
- **Self-tuning.** Visible at port level (which adapter, its numbers, signal weights); the inside of each adapter can still be opaque.
- **Plain Python.** Per port. A whole-Python unit is one adapter in the "signal" port with default exits and sizer.
- **Standing alone.** Strong.
- **Risk socket.** The exit-set and sizer ports are the socket. The risk session ships adapters.
- **Deletion test.** Deleting the shell spreads ordering and journaling into every unit. Deep.
- **Cost.** Moderate: matches practice (MT5 Wizard, SQX, Tharp's chapters, R35 §1.2).
- **Risk.** A fixed set of ports can be a cage ("types are defaults, never a cage", `ST:43`). New ports need a version of the shell.

### S4. A deep block catalogue with a thin unit spec

- **Interface.** `catalogue.resolve(slug, profile) -> producer`; the unit spec is thin data citing slugs, profiles, roles and numbers. The runtime can be S1, S2 or S3.
- **Deep inside.** The catalogue: implementations, golden values, per-class profiles, aliases, collisions.
- **Adapters.** Each block implementation; a TA-Lib or MT5-parity adapter could check values.
- **Self-tuning.** The catalogue can declare which settings of a block may move and how; the unit chooses within it.
- **Plain Python.** A custom block registers in the catalogue.
- **Standing alone.** The catalogue ships with the unit; no Library call at trade time.
- **Risk socket.** Exit and sizer blocks live in the catalogue like any block.
- **Deletion test.** Deleting the catalogue forces every unit to carry its own indicator code. Deep.
- **Cost.** Joins knot 3 to knot 1: a dictionary entry that runs is a catalogue block (`problem-solving.md` §4.3 insight 3).
- **Risk.** Two artefacts to keep in sync (vocabulary and catalogue, M-C).

### S5. Every unit is an Alternative Trading Composition

- **Interface.** A unit = logic (S1 or S2) + its own PolicyPair (AccountingPolicy + RiskPolicy). The Book keys are absent, not null (`GL:66`).
- **Deep inside.** The PolicyPair evaluation already in QMB (`execution/alternative.py`, via R01:144).
- **Adapters.** Book bots and ATC units are two compositions at one host seam. Real.
- **Self-tuning.** As S1 or S2 for the logic; the RiskPolicy's `sizing` field holds the sizing slot.
- **Plain Python.** As S1.
- **Standing alone.** Strong.
- **Risk socket.** The RiskPolicy fields (`max_gross`, `halt`, `sizing`, `override_principal`, `alternative.py:36-41`) are the socket's starting shape. Whether "self-calibrating" fits a policy record is open.
- **Deletion test.** Removing ATC sends units back to the Book premise. Earns its keep for C-Q1 and C-Q2.
- **Cost.** Lowest for sizing and exits: the seam exists. R01 and R07 named it (`R01:291`, `R07:190`).
- **Risk.** ATC was shaped for a fixed alternative policy (DEC-0436), not for a policy that moves itself.

### S6. The unit's rules are a QMX workflow graph

- **Interface.** A workflow document (`qmx.workflow/1`) whose `rule` nodes route `true`/`false` and whose script nodes run blocks (`research/18-grounding-today.md:45-46`, CHECKED by R18; `registry.py:58`, CHECKED).
- **Deep inside.** The workflow engine, its ledger, triggers.
- **Adapters.** Script nodes, subworkflows.
- **Self-tuning.** Visible as node parameters.
- **Plain Python.** Script nodes.
- **Standing alone.** Weak: the engine is the agent side, PC or remote worker (R18 via ST:180); the trading node runs none of it today. Conflicts with `SO` 10 unless the engine ships on the node.
- **Risk socket.** Nodes.
- **Deletion test.** n/a (the engine exists for agents).
- **Cost.** Reuse; but the expression language caps expression length at 1,000 characters (`expr.py:19-20`), a limit a unit would inherit (`SO` 9).
- **Risk.** Per-quote speed and the agent-side placement. Kept because it is the literal reading of his "similar to a workflow" seed.

### S7. Units as blocks for other units (composition seam)

- **Interface.** A unit publishes named outputs (the PKG ports `setup_signal`, `entry_signal`, `exit_signal`, `regime_filter`, R39 E4); another unit cites them as a block.
- **Deep inside.** The publishing unit.
- **Adapters.** Live copy, replayed copy in QMB, local fallback copy.
- **Self-tuning.** The consuming unit sees the producer as one block; the producer's tuning changes the consumer's input (a hidden coupling).
- **Plain Python.** Any unit can publish.
- **Standing alone.** At risk: if the producer is down, the consumer must run its own copy or a declared fallback (`SO` 10). Option: composition only at build time, compiled into one unit.
- **Risk socket.** Unchanged.
- **Cost.** Answers "a mini scalper for an indicator" (FG 796).
- **Risk.** Correlation between units hidden inside one input (his 1m/5m ruling: correlation, not two bets, `ST:146`).

---

## 3. Comparison (criteria only, no ranking)

| Criterion | S1 | S2 | S3 | S4 | S5 | S6 | S7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| What a cheap agent writes | Python | JSON graph | Port choices + numbers | Thin spec | Logic + policy | Workflow JSON | A citation |
| Parts visible to P2 and P4 | numbers only | all four kinds | ports, numbers | blocks, numbers | numbers, policy fields | nodes | outputs |
| Plain Python | native | as a block | per port | as a block | native | script node | native |
| Stands alone on the node | yes | if the interpreter ships | yes | if the catalogue ships | yes | no today | only with fallback |
| Risk socket | library call or slot | typed graph slots | exit and sizer ports | catalogue blocks | RiskPolicy fields | nodes | unchanged |
| Laws it reverses | intent door, `GL:150` | DEC-0175, intent door, `GL:150` | intent door, `GL:150` | none beyond its runtime's | few (ATC exists) | none in QML; `SO` 10 issue | none |
| Real seams (two adapters or more) | host, logic | blocks, hosts | every port | blocks | compositions | nodes | producer copies |

**Combinations (INFERRED).** S4 is orthogonal: it can sit under S1, S2 or S3. S5 is orthogonal for money: it can carry S1, S2 or S3 logic. S7 is a composition rule on top of any of them. So the three that compete on the same seam are **S1, S2 and S3**.

---

## 4. Internal seams any option will need (options, not choices)

| Internal seam | Why | Options |
| --- | --- | --- |
| Block interface | Lets any block fill any role (role neutrality) | typed output (event, level, series, state, probability, intent) · free Python returning anything |
| Motion | Lets self-tuning be stated per number | a field on each parameter · a separate tuner block (K1-7) · motion in the binding |
| Authority | Lets the operator see what moves without him | a field per part · implied by kind (N moves, S/B need a click) · implied by edit operation (R39 G2) |
| Provenance | Keeps the August honesty | the five labels (`source-stated`, `published-convention`, `STRATS-standardized`, `inferred`, `unresolved`) plus "builder-chosen" · per part · per unit |
| Journal writer | One trade and change record for backtest, paper and live (`ST:21`) | the host writes · the unit writes · both with one schema |
| Coordinates | Instrument, BarSpec, session (with time zone), direction | per binding (DNA D) · per unit · per placement |
| Context needs | Lets the MIS and analysts read a unit's needs without running it | a declared field · roles in the graph · Python only |

---

## 5. What the three layers could look like at each seam (knot 2, mapping only)

| Layer | S1 code-first | S2 data-first | S3 ports-first |
| --- | --- | --- | --- |
| Building block | QML functions and QMF producers | catalogue nodes | port adapters |
| Role binding | parameter names and docstrings | node role field | the port it is plugged into |
| Graph | Python control flow | the declared graph | the shell's fixed order plus signal weights |
| Pillars and views | generated from the spec, if declared | generated from the graph | the ports are the pillars |
| Roles beyond four | Python | roles on nodes | more ports |
| A whole bot as input | an import | a node citing a unit (S7) | a signal adapter wrapping a unit |
| Exits and size owned by the unit | callback intents | typed slots | exit-set and sizer ports |

---

## 6. Knot 5: room for the risk-and-sizing session

His ruling (CHECKED, `ST:145`): exits, stops, targets, time-varying targets, profit caps, account-wide halts and probability exits go to that session; "the unit owns its exits... and the risk socket must take whatever that session designs. No exit or sizing maths here."

### 6.1 What QML must leave open (INFERRED)

1. **The number and kind of exit slots.** R35's 16 exit families (initial stop, invalidation, profit target, time-varying target, unrealised-profit cap, trailing, give-back, break-even, partials, time exits, signal exit, event exits, account halts, probability exits, execution form, collision priority) must all fit without a QML change. QML may name slots; it must not fix their count.
2. **Per-trade versus per-unit versus per-account scope.** Some exits act on one position, some on a basket or the account (R36 §4.3 "exits by aggregate P/L sit with risk"). The socket must allow all three scopes.
3. **What a sizer may read.** Inputs it might need, listed as data available, not as maths: entry and stop prices, instrument facts (tick value, lot step, margin), account facts (balance, equity, open risk), the unit's own journal (outcomes in R), market statistics (volatility), and limits he sets. QML must make these readable, not decide which are used.
4. **How risk numbers move.** The same motion and authority question as knot 1. The socket must accept a sizer whose own numbers move by a declared rule, or not, as the session decides.
5. **Where risk events are journaled.** Size chosen, size refused, halt fired, exit fired with reason. The journal schema must have room; the content is the session's.
6. **The one automatic transition.** A risk rule stopping a unit, logged (`ST:39`). QML must let a unit's own halt stop it without any click and without the router (`SO` 10).
7. **Replayability.** Every exit and sizer must run identically in QMB and live (R04 via `ST:166`).
8. **Execution form.** Stop-market vs stop-limit, server-side vs client-side, trigger price basis (last, mark, index): a property of every exit (R35 §5.1 row 15). The socket must carry it.

### 6.2 Socket shape options

| Option | Shape | Fits | Leaves open |
| --- | --- | --- | --- |
| R-A | Two ports: an exit-set port and a sizer port (S3) | Practice: MT5 trailing and money modules, Tharp's chapters | Whether halts are a third port |
| R-B | One deep risk module per unit owning both exits and size | His "own self-calibrating risk and sizing" (`ST:21`) as one thing | How exits that depend on the entry signal reach it |
| R-C | Roles in the graph (stop, target, management, sizing modifier, halt) filled by blocks the session ships (S2) | The August roles beyond four (R39 C3) | Ordering when several exits fire in one bar (R35 §5.1 row 16) |
| R-D | PolicyPair RiskPolicy per unit (S5) | Code that exists (`alternative.py:36-41`) | Whether a policy record can hold a sizer that calibrates itself |
| R-E | A library the logic calls (S1) | Plain Python units | Nothing visible to P2 and P4 unless declared |

### 6.3 What QML must not do (from the rulings)

- Fix any number, threshold or formula for exits or sizing (`ST:145`, `SO` 5).
- Keep the intent door's "the bot may not size" law for units without the session's say (C-Q1).
- Make the socket depend on the router, MIS, PC link or Library at trade time (`SO` 10).

### 6.4 Contradictions the session will meet in QML (pointers)

C-Q1 (bot never sizes), C-Q2 (Book owns exits), C-Q3 (thresholds in the Book), C-Q4 (missing exit means entry hypothesis), C-Q10 (tuned assignment is a new version) in `problem-solving.md` §5.8.

---

## 7. The three options that differ most

**S1 code-first**, **S2 data-first** and **S3 ports-first** compete for the same seam: where a rule's structure lives.
- In S1 the rule is Python and only numbers are visible.
- In S2 the rule is data and every part is visible, at the cost of a new interpreter and the reversal of DEC-0175.
- In S3 the structure is a fixed shell with ports, practice's own shape, at the risk of a cage.

S4 (block catalogue), S5 (ATC money policy) and S7 (composition) combine with any of the three, so they are not rivals to them. S6 (workflow graph) is the literal form of his seed but fails standing alone today.

**What would separate S1, S2 and S3 (experiments, not run).** The builder invention count and the speed test in `problem-solving.md` Step 6. The card-reading test with him in `design-thinking.md` Step 6.
