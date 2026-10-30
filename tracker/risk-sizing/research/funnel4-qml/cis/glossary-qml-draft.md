# Draft glossary of QML's words (extends funnel3's draft; not CONTEXT.md)

Written 2026-10-30 by the QML-depth CIS agent with the `domain-modeling` skill (SKILL.md and CONTEXT-FORMAT.md read). **Draft only.** The skill says "be opinionated" and pick one term per concept; this brief forbids picking. So each word lists every competing definition found, with its source, plus the scenarios that would force a choice and the other meanings it collides with. Nothing is resolved. No `CONTEXT.md` was written.

It extends `research/funnel3/cis/glossary-draft.md` (`F3G`), which already holds unit, logic, calibration, idea, source, family, variant, sibling, child, parent, context, market state, terrain, instrument class, timeframe, trading style, System 1, System 2, router, MIS, envelope, journal. For **family**, **calibration**, **variant** and **logic** this file adds only the QML senses and points to `F3G` for the rest.

Keys and labels as in `problem-solving.md`. D1, D2 … are competing definitions in no order.

---

## Building words

### primitive

- **D1. A role-neutral concept, "not permanently a trigger, confirmation, or stop".** "A primitive is a concept (session high, liquidity sweep, engulfing completion)" (`DR:3`, CHECKED).
- **D2. The first of three layers: "Primitive dictionary 'What things exist?'"** (FG 831, CHECKED by R39 C2).
- **D3. A vocabulary phrase.** "have an X amount of phrases that could be used in the dictionary" (GM 2725, CHECKED by R39 C8).
- **D4. A runnable producer.** QMF's configured producers (indicators, structures) that a footprint binds by fingerprint or template (`GL:396`, `GL:683`, CHECKED). Six indicators and one structure family run today (R34 §4).
- **D5. A census concept.** One of the 252 MQL5 concepts R36 counted, matched by regex (R36 §1.2, CHECKED by R36).
- **D6. A raw price fact as opposed to a derived indicator or a discretionary reading.** The worker contract separates the three (R39 C14, CHECKED by R39).

**Separating scenarios.** "Liquidity sweep" exists as prose but no producer computes it: is it a primitive (D1) or not yet (D4)? A Hurst exponent: a primitive (D4 if computed), a census concept (D5), or a "sensor" outside the strategy dictionary? An LSTM forecast: a primitive with a probability output, or another kind of node (R36 §7 q2)?

**Collides with.** "Primitive" in programming (int, float). The QMX docs never use it for producers.

### block

- **D1. A building block in a strategy builder.** SQX "Building blocks": Signals, Indicators, entry price blocks, order types, exit types with a probability weight (R35 §1.2, CHECKED by R35).
- **D2. A Wizard module.** MT5's signal, trailing and money modules (R35 §1.2; R36 §5.3).
- **D3. A runnable dictionary entry.** INFERRED from "the block catalogue is missing" (R34 §4.1, INFERRED there; R18 cited by R34).
- **D4. A missing piece of the plan.** His "the missing building block is one trade record shared by backtest paper" (`T1:1177`, CHECKED).
- **D5. The trading node's refusal state.** "entry-side-only block": every block the node can raise refuses new risk and nothing else (`GL:300`, CHECKED).
- **D6. A Library kind.** `pod-block` (R01:485, CHECKED by R01).
- **D7. "Data block".** Read aloud by him from a list (`T1:1177` "2 data block", CHECKED); meaning unclear.

**Separating scenarios.** An agent reads "the unit's exit block". Is that a catalogue entry (D3), a Wizard-style module (D2) or the node's refusal (D5)? A "block" that blocks: D5 is a verb-like state, all others are parts.

**Collides with.** D5 is a live-trading safety term. Using "block" for parts risks agents confusing a part with a halt.

### role

- **D1. The job a leg plays in a confluence, closed and addable: `level | trigger | confirmation | filter`** (`EB:qml/src/qml/declaration/confluence.py:82-89`, CHECKED; `GL:224`).
- **D2. Stage 0's open roles**, including `location`, `context`, `invalidation`, `stop`, `exit`, `management`, which collapse to "Python WHEN" at graduation (`EB:qml/src/qml/research/collapse.py:49-75`, CHECKED).
- **D3. The wider August list:** "context, trigger, confirmation, veto, exit, target, sizing modifier, or regime detector" (FG 1209, CHECKED by R39 C3).
- **D4. A field of each dictionary entry: "Eligible roles"** (`DR` field 8, CHECKED). RSI's: "filter, confirmation, divergence source, trigger" (`S/dictionary/context-regime-and-intermarket/context-filters-confirmations.md:194`, CHECKED).
- **D5. An agent role.** "A declarative behavioral contract, close to a system prompt": Researcher, Trader, Developer, Analyst, Product Manager (`GL:882`, CHECKED).
- **D6. An instrument role in a footprint:** trading versus data-only stream (`GL:396`, CHECKED).
- **D7. A port.** The PKG ports (`setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`) act as roles at the composition level (R39 E4).

**Separating scenarios.** "Sizing modifier": a role (D3) or a risk-session slot? A volatility filter that also scales size: one role or two? An agent told "assign the Trader role" in a unit-building workflow: D5 or D1?

**Collides with.** D5 is a ratified QMX word for agents. D1 and D5 will meet inside one workflow.

### binding

- **D1. A role binding on a strategy:** role, profile, pair, timeframe, session, direction, timing, bar-close vs intrabar, dependencies, evidence, unknowns (`DNA:65-67`, CHECKED).
- **D2. A producer binding in a footprint:** a pinned producer fingerprint or a producer template (`GL:396`, `GL:683`, CHECKED).
- **D3. A venue account-binding record** with identity (VenueId, AccountId, role, world) (`GL:104`, CHECKED).
- **D4. A risk-domain Book binding** (`GL:104` continues, CHECKED; `GL:120` "binding epoch" heading).
- **D5. One primitive with two bindings.** "It is one primitive with two bindings" (R35 §6 item 3, CHECKED by R35).
- **D6. An optional MIS binding** of an ATC composition (`GL:66`, CHECKED).
- **D7. Re-binding a bot to a seat**, which "never mints a Bot version" (`EB:qml/src/qml/declaration/versioning.py:1-7`, CHECKED).

**Separating scenarios.** "Bind RSI to EURUSD M5 as a filter": D1. "Bind the RSI producer to the footprint": D2. "Bind the unit to the cTrader demo": D3. An agent asked to "change the binding" could change any of the three.

**Collides with.** D3 and D4 are money-path identities.

### graph

- **D1. The STRATS operational logic graph:** nodes are bound primitives, states, conditions or actions; operators ALL, ANY, NOT, K_OF_N, sequence, within, arming, reset, cooldown, re-entry; "not a QMX executor" (`DNA:69-87`, CHECKED).
- **D2. The Stage 0 graph [PROPOSED, DEC-0398]:** "Boolean/temporal/lifecycle composition field... never an executor" (`GL:420`, CHECKED).
- **D3. A Graph Template:** an authored workflow artefact with no runtime state (`GL:424`, CHECKED).
- **D4. A Task Graph:** the daemon's runtime work state (`GL:1049` heading, CHECKED).
- **D5. A lineage DAG:** the family tree, "a family tree, not overwrites" (`DNA` part I, R34 §2.5).
- **D6. The PKG typed graph:** nodes (bindings, operators, temporal operators, actions, data inputs) and edges `requires`, `then`, `suppresses`, `emits`, `invalidates` (R39 E2).
- **Not a graph.** A Confluence is explicitly "NEVER" the Stage 0 graph (`GL:420`, CHECKED).

**Separating scenarios.** "The unit's graph" in an agent prompt: rules (D1), lineage (D5) or a workflow (D3)? If the rule graph becomes executable (S2 in `seams-options.md`), D1 and D2's "never an executor" breaks.

**Collides with.** D3 and D4 are agent-system words.

### view

- **D1. A human lens over the same record:** pillars "survive as a convenient human view" (GM 3261, CHECKED by R39 B4); "Human view (do not replace A–I)" (`DNA:124-140`, CHECKED).
- **D2. Obsidian-friendly views** with tags or colour for ambiguity (R39 B8).
- **D3. A saved view:** the durable body of an `analysis.project` projection (`GL:902`, CHECKED).
- **D4. A desk ledger view:** "a read-time view over the three ledger stores... never itself a store" (`GL:280`, CHECKED).
- **D5. A UI preview and detailed view** of the family tree (`ST:53`, CHECKED).
- **D6. The old MIS "context view" bots read** (R19 via `ST:181`, CHECKED there).

**Separating scenarios.** "Show the pillar view of this unit": generated from the record (D1) or a stored projection (D3)? Does a view ever hold data of its own? D3 is durable, D1 and D4 are not.

### pillar

- **D1. His four (24 Aug):** level, trigger, confirmation, risk management and position sizing; "it's not finite" (M779, CHECKED by R34 §2.6).
- **D2. The 1 Sep lock's four:** location/level, market context/filter, trigger, confirmation/confluence (`DNA:126-133`, CHECKED).
- **D3. Seven lenses (26 Aug ground state):** location, context, trigger, confirmation, entry semantics, exit and management, timing/scope/lineage (`GS L143-155`, CHECKED by R34).
- **D4. The eight-part completeness checklist** (GM 2724, CHECKED by R39 B5).
- **D5. Nine areas** in the 26 Aug starting brief (R34 §2.6).
- **D6. His 28 Oct memory:** "market context was there, but it was an event, a trigger, then... risk management, position sizing was the last. Then there is a fourth pillar" (`T1:2051`, CHECKED).
- **D7. Practice's ten-part anatomy:** context, location, trigger, confirmation, entry type, initial stop, targets, management, size, account halt (R35 §6 item 1, CHECKED by R35).

**Separating scenarios.** Is risk and sizing a pillar? Yes under D1, D6, D7; no under D2, D3. Is "event" its own pillar (D6) or the trigger (D2)? A unit owns sizing (`ST:21`): does its pillar view show it?

**Collides with.** None outside this vocabulary. Every version says pillars are views, "not folders" (R34 §2.6).

---

## Rule words

### entry

- **D1. A dictionary entry:** "a role-neutral file record" [PROPOSED, DEC-0396] (`GL:284`, CHECKED).
- **D2. A trade entry:** opening a position (general trading use).
- **D3. Entry semantics:** "trigger ≠ order. A completed trigger is not automatically a market order, limit, stop, or fill" (`DNA:137`, CHECKED).
- **D4. An entry hypothesis:** a candidate class whose exits are missing (`DNA:52`, CHECKED).
- **D5. An entry intent:** what the callback returns at the door (`EB:qml/src/qml/protocol/intents.py:1-7`, CHECKED).
- **D6. Entry rules,** as he uses it: "entry rules, it contains a lot. Exit rules, it contains a lot" (`T2:779`, CHECKED).
- **D7. A legal entry into QML:** "Three legal entries, none a toll booth" (`QD:210`, CHECKED).

**Separating scenarios.** "Add an entry for the retest": a new dictionary record (D1) or a new trade entry rule (D6)? "The entry is unresolved": order type (D3) or the whole record (D1)?

**Collides with.** D1 and D2 in the same sentence is the most likely confusion for a cheap agent.

### rule

- **D1. One if-else of a trading bot:** "It's just a set of rules. In programming, it's if-else statements" (`T2:779`, CHECKED); "If this happens, buy. If this happens, sell" (`T1:264`, CHECKED).
- **D2. A workflow `rule` node:** "a safe expression... over its inputs that routes to the `true` or `false` port" (`EB:qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/rule.py:1-2`, CHECKED).
- **D3. A risk rule:** "the risk rules stopping a unit (kill switch and similar)" (`ST:39`, CHECKED).
- **D4. An extracted source rule:** "Every detected rule must point back to transcript timestamps" (GM 2724, CHECKED by R39 H5).
- **D5. A rule set per market state:** the 17781 pattern, one set of numbers per regime (R36 §5.3 item 3, CHECKED by R36).
- **D6. A conformance rule:** the Layer 1 linter's checks (via R34 §4).
- **D7. A house rule:** what the account mode leaves to QMX, for example netting versus hedging behaviour (R35 §6 item 8, CHECKED by R35).

**Separating scenarios.** "The rule self-tunes": its threshold (part of D1) or its structure? "A rule stopped the unit": D3, never D1. Should D1 be written with D2's expression language (`seams-options.md` S6)?

**Collides with.** D3 is the only automatic transition allowed; using "rule" for both D1 and D3 blurs what may act without his click.

### parameter

- **D1. A declared variable in QML's parameter space:** type (exact integer, exact rational, categorical, boolean), bounds, step, mandatory default, optional hard constraint, unit kind, one UI flag (`EB:qml/src/qml/declaration/parameters.py:1-7`, CHECKED).
- **D2. A dictionary "Parameters/profiles" line with provenance labels:** period 14 marked `source-stated` (Wilder), overbought 70 and oversold 30 marked `published-convention` (`context-filters-confirmations.md:193`, CHECKED).
- **D3. An MQL5 `input`:** 4,845 parsed in 664 articles; period, time, lot, stop, multiplier, risk % lead (R36 §6.1, CHECKED by R36).
- **D4. A producer template's space-bound value:** a producer configuration "minus ONLY the space-bound parameter values" (`GL:683`, CHECKED).
- **D5. A study dimension in QMB:** `StudyParameterSpace`, read from the one CT-33 schema (`EB:qmb/src/qmb/optimize/__init__.py:1-11`, CHECKED).
- **D6. "Numbers"** in his words: "The part that tunes itself actually is part two... It's numbers" (`T2:779`, CHECKED).
- **D7. A Book-level UI-editable variable,** e.g. `amend_min_improvement` inside `exit_policy` (`GL:70`, CHECKED).

**Separating scenarios.** A trigger threshold hidden in Python: a parameter (D6, it is a number) or not (D1, undeclared)? A choice between two exits: a categorical parameter (D1) or a structure change? An approved range he set: D1's bounds or something else?

**Collides with.** "Parameter" of a workflow node (`parameters.expr`, `rule.py`, CHECKED).

### range

- **D1. Bounds and step of a declared parameter** (`parameters.py:1-7`, CHECKED).
- **D2. A dictionary range or default:** "It maybe it has ranges... certain things might need specific numbers or defaults" (FG 975, CHECKED by R39 C7).
- **D3. A search range** a sampler explores (QMB optimiser, CHECKED above).
- **D4. A safe range for moving without him:** "never above his ranges" (`ST:201`, an open recommendation).
- **D5. A ranging market:** "trending", "ranging", "chop" (R35 §3.1, CHECKED by R35); dictionary "range/consolidation", 369 articles (R36 §2.2).
- **D6. A session or opening range:** Asian range, opening range (R35 §1.3; dictionary `session-range`, `opening-range`).
- **D7. A range bar:** a BarSpec kind "price-brick, range" (`GL:98`, CHECKED).

**Separating scenarios.** "The unit works in a range": D5. "The stop's range is 1.2 to 2.0 ATR": D1 or D4. "Range breakout on the Asian range": D6. A cheap agent reading "range" in a source has four trading senses and three QML senses.

**Collides with.** All seven. The most overloaded word in this list.

### calibration (QML senses only; see `F3G` D1-D7)

- **D8. A tuned canonical assignment.** "Promoting a tuned assignment mints a NEW Bot version" (`GL:150`, CHECKED).
- **D9. Live seats execute defaults only.** "Governed live and paper seats execute the canonical assignment ONLY" (`GL:150`, CHECKED). Under this law calibration never happens live.
- **D10. A provenance label for a number:** `published-convention`, `STRATS-standardized`, "generated for future experimentation" (R39 C12, C17).

**Separating scenarios.** A unit's ATR multiple moves inside its range overnight: D8 (new version), D9 (forbidden), or `F3G` D2 (journal event)?

### motion (proposed in this run as a word to test, not a term)

Listed because the knots need it and no source has it. "How a number may change": fixed, scaled by a live statistic, refit on a window, chosen by state, learned, ranked by record (R36 §6.3 mechanisms, CHECKED by R36). No QMX or STRATS source defines it (R36 §6.3: "the dictionary has no field for how a number changes over time"). **Competing words in sources:** "self-tuning" (`T2:779`), "self-calibrating" (`ST:21`), "self-configuring" (`ST:78`), "adaptive" (R35 §4.1), "self-optimising EA" (R36 §6.2).

---

## Lineage words (QML senses)

### family (QML senses only; see `F3G` D1-D6)

- **D7. Dictionary concept family:** folders by "what a concept is about, never by job" (`DR` "Family folders, not role folders", CHECKED); ten folders, four with files (CHECKED `ls S/dictionary/*`).
- **D8. Methodology family:** 13 kinds (trend, mean reversion, breakout, SMC/ICT, …) as one axis beside holding horizon and execution archetype (FG 795, CHECKED by R39 G12).
- **D9. Structure family in QMF:** "A type of chart object... never a strategy, bot, or Book category" (`GL:1029`, CHECKED).
- **D10. A census family:** R36's 11 families (indicators, stats and models, …) (R36 §2.1).
- **D11. Strategy family with per-family Book variables:** `exit_policy` declares an `ExitLogicRef` per family; a bot declares exactly one (`GL:1025`, CHECKED; `QD:106`).

**Separating scenarios.** "Add RSI to the momentum family": D7. "This unit is in the mean-reversion family": D8 or `F3G` D4. "Exit logic per family": D11, which the unit plan moves into the unit (`ST:145`).

### variant (QML senses only; see `F3G` D1-D8)

- **D9. An edit operation stack on a parent:** `add_binding`, `remove_binding`, `replace_parameter`, `change_timing`, `change_entry`, `change_exit` … with a result digest (PKG, CHECKED by R39 G2).
- **D10. Exits and entries as variant axes:** "exits become variant, entry become variant" (`T1:1177`, CHECKED).
- **D11. A placement variant:** one of the node's two placements, "never two products" (`GL:647`, CHECKED).

### port

- **D1. A named composition port** of a strategy package: `setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`; "A composite imports parents' ports, never their insides" (PKG, CHECKED by R39 E4).
- **D2. A workflow node port:** `in`, `main`, `true`/`false`, `body`/`done`, `next` (`EB:qmx-agents/packages/qmx-engine/src/qmx_engine/definition/registry.py:44-58`, CHECKED).
- **D3. A port at a seam (ports and adapters):** "Define a port at the seam" (`codebase-design` DEEPENING.md, CHECKED).
- **D4. A venue or replay port:** `VenueClientPort`, "replay import port" (`GL:1129`, `GL:846` headings, CHECKED).
- **D5. A sampler port** in QMB optimise (`EB:qmb/src/qmb/optimize/__init__.py:1`, CHECKED).
- **D6. A Wizard module slot** (signal, trailing, money), not called a port there (R35 §1.2).

**Separating scenarios.** "Connect the unit's exit port": D1 (a published signal), D3 (a socket the risk session fills), or D6 (a module slot)?

**Collides with.** "Port" as a network port.

### coordinate

- **D1. "Timeframes and pairs are coordinates, not levels"** (FG 831, CHECKED by R39 D2).
- **D2. "Challenge coordinates, not tunable strategy factors":** pair, session, regime (EXP §3, CHECKED by R39 I9).
- **D3. Per-binding scope:** pair, timeframe, session, direction on each binding (`DNA:65-67`, CHECKED).
- **D4. A cell:** instrument × timeframe × window, each a variant with its own proof (`SE:44` via `F3G` variant D1).
- **D5. A BarSpec:** the noun that replaces bare "timeframe" (`GL:98`, CHECKED).
- **D6. His correction:** the same unit on 1m and 5m "is one idea, and the two are correlated: correlation, not two bets" (`ST:146`, CHECKED).

**Separating scenarios.** A unit tuned per pair: are pair-specific numbers allowed (D3 binds them) or forbidden (D2)? 1m and 5m: two coordinates of one unit (D6) or two cells (D4)?

---

## Logic (QML senses only; see `F3G` D1-D7)

- **D8. The logic artefact:** "a versioned plain-Python distribution whose identity is distribution identity + version + a normalized, reproducible source-manifest fingerprint" (`EB:qml/src/qml/logic/__init__.py:1-9`, CHECKED).
- **D9. "Python WHEN":** where conditions live; "Condition semantics live in Python logic in V1" (`QD:82`, CHECKED).
- **D10. "QML is literally the wrapper for this entire thing"** (`T1:2051`, CHECKED): logic as everything QML wraps.
- **D11. "The logic behind a unit... needs to also be revised"** (`T2:779`, CHECKED): logic as the unit's design, not its code.

**Separating scenarios.** The same rules rewritten from Python into a declared graph: same logic (`F3G` D1, D2), new logic (D8, new fingerprint)?

---

## Which words disagree most (INFERRED count)

| Word | Definitions found | Kind of disagreement |
| --- | --- | --- |
| range | 7 | three QML senses, four trading senses |
| role | 7 | strategy job, agent persona, stream type, port |
| entry | 7 | record versus trade versus intent versus QML door |
| rule | 7 | if-else versus workflow node versus risk stop |
| parameter | 7 | declared, hidden, Book-level, workflow |
| binding | 7 | strategy, footprint, account, Book, seat |
| pillar | 7 | four versus seven versus ten; risk in or out |
| graph | 6 | rules, workflow, task state, lineage |
| port | 6 | composition, workflow, seam, venue, sampler |

**The widest by kind (INFERRED).** `range`, `entry` and `rule`, because each mixes a trading sense with a QML sense, so a cheap agent reading a source cannot tell which is meant. `role` is the most dangerous inside QMX, because the agent-system meaning (D5) is ratified and will appear in the same workflows that build units.

## Candidate terms seen in sources, not proposed

Listed so the glossary step does not lose them: `producer template` (`GL:683`), `footprint` (`GL:396`), `canonical assignment` (`GL:150`), `confluence leg` (`GL:224`), `ExitLogicRef` (`QD:106`), `PolicyPair` and `ATC` (`GL:66`), `entry_hypothesis` (`DNA:52`), `F labels` (`stage0.py:91-98`), `Python WHEN` (`collapse.py:60`), `edit operation` (R39 G2), `named port` (R39 E4), `motion` (this file).
