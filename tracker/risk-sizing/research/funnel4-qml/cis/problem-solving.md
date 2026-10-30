# CIS problem solving on QML's knots

Written 2026-10-30 by the QML-depth CIS agent. Method: `bmad-cis-problem-solving` (SKILL.md and `solving-methods.csv` read), run straight through with no human present. Where the skill asks me to recommend or select, I list options and the evidence that would separate them. Nothing here is chosen or designed. Exits, stops, targets and sizing maths are named only as slots; their content belongs to the risk-and-sizing session (ST:145).

**Scope split.** A parallel party-mode and brainstorming agent goes broad on QML (`../party-brainstorm/`). This file goes deep on four knots: the if-else question (knot 1), dictionary expansion (knot 3), QML's contradictions with the unit plan (knot 4), and, briefly, the three layers (knot 2, worked in full in `seams-options.md`). Knot 5 (room for the risk session) is in `seams-options.md` §6.

**Labels.** CHECKED = I read it at the cited place this session. "CHECKED by R39" = that research agent read it at the place it gives; I read their file, not the underlying source. INFERRED = my reasoning.

**Keys (all five files use them).**

| Key | Meaning |
| --- | --- |
| `T1`, `T2` | `operator/transcript-2026-10-20-to-28.md`, `operator/transcript-2026-10-29-to-30.md`; line = the line holding the quoted text |
| `ST`, `SO` | `STATE.md`, `STANDING-ORDERS.md` |
| `R20` … `R41` | `research/20-…` to `research/41-…` |
| `F3G`, `F3P`, `F3Q` | `research/funnel3/cis/glossary-draft.md`, `problem-solving.md`, `cis-questions.md` |
| `EB:` | `git show origin/engine/base:<path>` in `C:/Users/Mubarak/Desktop/QMX` (tip `d82be318`, 26 Oct) |
| `GL`, `QD` | `EB:docs/glossary.md`, `EB:docs/components/qml.md` |
| `S/`, `DNA`, `DR` | `C:/Users/Mubarak/Desktop/Stats/`, `S/schema/strategy-dna.md`, `S/dictionary/README.md` |
| `FG n`, `GM n` | Hermes store rows, as cited by R39 (Friendly Greeting and gold-mine sessions) |

**A correction before the work.** R34 §1.2 says the phrase "how do we make sure that those if-else statements can self-tune" appears in no transcript. It does now. The refreshed `T2` holds it in his 30 Oct 06:11 turn: "what is a trading bot? It's just a set of rules. In programming, it's if-else statements. That's it. Okay. So how do we make sure that those if-else statements can self-tune?" CHECKED (`T2:779`). The same turn holds "there are reasons as to why the dictionary was made like that". CHECKED (`T2:779`).

---

## Step 1. Define and refine the problem

**Problem title.** QML must become the library a unit is made of, but nothing today says what a rule is made of, which of its parts may move, or who may move them.

**Category.** Definitional and structural, in a design-before-build phase. Not a bug.

**Initial problem, in his words (all CHECKED).**
- "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot." (`T2:779`)
- "If it can self-tune, I don't have to tune it myself, right? But it does beg the question, how does it do it and what is it actually tuning?" (`T2:779`)
- "For me, I'm imagining this like JSON. Most of it is JSON. Because in a way, it's actually very similar to a workflow. Because these are just conditionals." (`T2:779`)
- "QML is a library so that we don't just write Python" (`T2:779`); and, earlier, plain Python is never off: "it doesn't mean that normal Python is off entirely... I might make maybe an ML ensembler" (`T1:1574`).
- "the dictionary... you get what multiple traders would use from languages... so that if someone from a source mentions anything, we already know what it is... Or if it's new, we can append it. In other words, the agents working in the workflows that are building the units are not confused." (`T2:779`)
- "QML is literally the wrapper for this entire thing" (`T1:2051`).

**Refined problem statements (INFERRED), one per knot.**
1. **Knot 1.** A rule is `if <condition over inputs> then <action>`. To self-tune, each part of that rule needs three facts written down: what kind of part it is, how it may change, and who may change it. Today none of the three is a field anywhere.
2. **Knot 3.** The dictionary is the shared vocabulary that keeps cheap agents from confusion. It is prose, covers FX and crypto spot, and holds 44 % of the concepts MQL5 authors use. It must grow to every asset class and data class without forking per market, without becoming ambiguous, and in a form a unit can run.
3. **Knot 4.** QML's shipped laws were written for a bot that is a signal source inside a Book. The unit plan reverses that premise. At least eleven QML rules now contradict the plan.
4. **Knot 2 (short).** The gold mine's three layers (primitive, role binding, graph) exist only as non-runnable Stage 0 types. Where the seams between them go is open.

**Problem context (CHECKED unless marked).**
- QML is the "bot-authoring library" (`QD:17`) that "May never: be, or be called... a framework, an engine" (`QD:25`). CHECKED. A governed bot is a declaration plus plain-Python logic (`GL:134`, CHECKED).
- Conditions are forbidden from the declaration: `FORBIDDEN_CONDITION_FIELDS` lists `condition`, `when`, `predicate`, `expression` and others (`EB:qml/src/qml/declaration/confluence.py:51-61`). "Condition semantics live in Python logic in V1" (`EB:…/confluence.py:1-10`; `QD:82`).
- The only data-visible tunable thing is the parameter space: type, bounds, step, mandatory default, hard constraint, unit kind, one UI flag (`EB:qml/src/qml/declaration/parameters.py:1-7`). QMB's optimiser reads that one schema through a sampler port (`EB:qmb/src/qmb/optimize/__init__.py:1-11`).
- Live and paper seats run the canonical defaults only; "Promoting a tuned assignment mints a NEW Bot version" (`GL:150`).
- QMX's workflow engine already has a `rule` node: "a safe expression... over its inputs that routes to the `true` or `false` port" (`EB:qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/rule.py:1-2`; kind declared at `…/definition/registry.py:58`).

**Success criteria for this step (INFERRED).** Each knot ends with a root-cause candidate, a set of options of at least three, and the evidence or scenario that would separate the options. No selection.

---

## Step 2. Diagnose and bound (Is / Is Not)

| Dimension | IS | IS NOT | Pattern (INFERRED) |
| --- | --- | --- | --- |
| Where "what tunes" is unclear | Thresholds inside conditions, the conditions themselves, which block fills a role, exits, sizing, session and instrument coordinates | Not the indicator periods of the six wrappers: those are declared numbers today (`R34 §5.1`) | Only numbers already lifted into the parameter space are clear. Everything still inside Python or prose is unclear. |
| Where the dictionary fails agents | Missing words (statistics, models, MT5 built-ins, account-level exits, server time), no runnable form, no "how this number moves" field | Not the chart vocabulary of price action, sessions, exits and filters: 70-88 % covered by article weight (`R36 §0`) | It covers the discretionary trader's chart and misses the quant's toolbox and the venue's facts. |
| Where QML contradicts the plan | Sizing, exits, thresholds, family constraints, live tuning, context as a role | Not the runtime purity rules (no clock, I/O, network), which a unit can keep: the evaluation instant rides the callback (`EB:qml/src/qml/protocol/contract.py:31-35`) | Every contradiction traces to one premise: the Book owns money and exits. |
| When the problem appeared | After 13 Oct (unit = bot with its own risk), sharpened 24 Oct (QML builds units) and 30 Oct (if-else question) | Not in August, when STRATS was prose by order and the Book owned exits (`R34 §2.7`; `R39 J7`) | Each reframe changed the owner of a part, and the code still encodes the old owner. |
| Who holds each side | Shipped QML code and ratified docs on one side; his October words and `ST` on the other | Rarely two agents | It is a shipped-code-versus-new-intent gap, not a disagreement between people. |

---

## Step 3. Root cause analysis

Methods: Five Whys for the linear chains, a fishbone for the dictionary, systems thinking for the tuning loop. Each knot gets its own pass.

### 3.1 Knot 1. Five Whys on "how do the if-else statements self-tune, and what tunes?"

1. **Why can nobody say what tunes?** Because only one part of a rule is visible as data: declared parameters with ranges (`parameters.py:1-7`). The "if" itself is forbidden from the declaration (`confluence.py:51-61`) and lives in opaque Python. CHECKED.
2. **Why is the "if" not data?** Because DEC-0175 put "when" into Python for V1 (`QD:82`), and the only data form of a rule, the Stage 0 graph, is non-executable by design: compiling it is refused (`R34 §4.1`, `projection.py:8-9` CHECKED by R34). On the STRATS side the graph "is not a QMX executor" (`DNA:87`, CHECKED). So the rule exists either as prose or as code, never as inspectable runnable data.
3. **Why did neither side need a data form?** Because each side assumed the other would own it. STRATS said "leave QMX out. QMX will adapt to the library" (`GM 3262`, CHECKED by R39 A6). QML said thresholds, exits and sizing live in the Book (`QD:252`, CHECKED). Neither layer had to describe a whole rule.
4. **Why does that block self-tuning now?** Because self-tuning is a property of a rule's parts, and three facts per part are missing:
   - **kind**: is it a number with a range, a structure, a choice between blocks, or a coordinate (where it runs)?
   - **motion**: how may it change (fixed; scaled by a live statistic; refit on a window; chosen by measured state; learned; selected by record)? The dictionary's profile field says where a number came from, not how it moves (`R36 §6.3`, CHECKED by R36). QML's `ParameterSpec` has bounds and a UI flag, no motion. CHECKED.
   - **authority**: may the unit move it by itself, may a workflow propose it, or does it need his click? `ST:39` says only he promotes and the only automatic transition is a risk rule stopping a unit. No field anywhere maps a part to one of these. CHECKED (field lists above).
5. **Why is there no place for those facts?** Because today's law says a live bot cannot move any number at all. Live seats run the canonical defaults only, and a tuned assignment is a new Bot version (`GL:150`, CHECKED). The question "what may move live" was answered "nothing", so no field was needed.

**Root-cause candidate RC1 (strongest, INFERRED).** A rule has no inspectable anatomy. Its "if" is opaque code or prose, and none of its parts carries a kind, a motion or an authority. So "what tunes" cannot be read off a unit. It can only be argued.

**Other candidates kept, not ranked.**
- **RC2. Three meanings of self-tuning are spoken as one.** R20 separates (a) recalculating an order from a balance and a fixed rule, (b) updating a rule's inputs from finished trades, (c) changing the policy. R36 finds eight mechanisms in practice. His "self-configuring" covers all of them (`ST:78`, "has never been shown concretely"). CHECKED (R20 §1, R36 §6.3).
- **RC3. Tries are not counted where tuning happens.** Every automatic re-fit is a try; R35 §4.2 and R11 say overfitting grows with refinement depth. If a unit tunes itself live, nobody owns the try count. INFERRED from CHECKED R35 §4.1 rows.
- **RC4. Identity is undefined.** Whether a moved number is "the same unit" is the open identity question (`F3P §3.1`; `ST:199` recommendation 2, not a ruling). Self-tuning is blocked on it. CHECKED.

### 3.2 Knot 1. First principles: the anatomy of one if-else rule

A trading rule written as code is `if C(inputs; θ) then A(θ′)`. Breaking it into the smallest parts any trader would recognise (R35 §1.1 anatomy, CHECKED) gives the table below. "Kind" uses four words: **N** = number with a range, **S** = structure (shape of the logic), **B** = block choice (which named block fills a slot), **K** = coordinate (where or when the rule runs). The examples are from the 17239 MQL5 article, an Asian box breakout (box 23:00-03:00, MA 50 trend, stop orders offset 10 pips, target RR 1.3, exit at 13:00), CHECKED by R36 §5.2.

| Part of a rule | Kind | Example from 17239 | Self-tuning mechanisms that apply (R36 §6.3 numbering) | Notes |
| --- | --- | --- | --- | --- |
| Input stream (instrument, bar type) | K | EURUSD, M15 bars | none inside a unit; choosing streams is placement | BarSpec replaces bare "timeframe" (`GL:98`, CHECKED). His ruling: 1m and 5m of one logic are one correlated idea (`ST:146`). |
| Transform (indicator) and its settings | B + N | MA, period 50 | 1 offline optimiser, 3 scale by live statistic (adaptive MA), 4 refit on window | Adaptive indicators are "safe to adapt automatically" in practice (R35 §4.1). |
| Comparator and threshold | N | close above box high + 10 pips | 1, 3 (ATR multiple), quantile thresholds | Volatility-scaled distances are how one setting travels across instruments (R35 §6 item 15). |
| Combinator | S + N | box break AND trend filter | 5 branch by measured state; weighted vote (MT5 Wizard) | `K_OF_N` exists; no weighted-sum-with-threshold operator (R36 §0 item 6). |
| Temporal operator | S + N | entry window inside London open | 1 on the window length | `within`, `sequence`, `arming`, `cooldown`, `reset`, `re-entry` exist in DNA E (`DNA:69-84`, CHECKED). |
| State | S | box formed, armed, in trade, done for day | none (a state machine is structure) | S27 lifecycle states: dormant, eligible, armed, triggered, confirmed, entered, invalidated, expired, cooldown, reset (R40 §4 row 22). |
| Context requirement | B + N + K | trend filter, session | 5 branch by state, 6 quality-gated switch | Context is a role, not a class (`R34 §3.5`). |
| Action: entry order type | B | buy stop / sell stop | none in practice | "Fades use limit orders and breakouts use stop orders" (R35 §6 item 14). |
| Action: exits and management | B + N (slots only here) | target RR 1.3, exit at 13:00 | 3, 7, 8 | Slot content is the risk session's (`ST:145`). |
| Action: size | N (slot only here) | lot 0.1 | 7 own record drives size | Maths is the risk session's (`ST:93`, `ST:145`). |
| Scope coordinates | K | session hours in broker time | none inside the rule; a placement decision | Broker server time / DST is missing from the dictionary (115 articles, R36 §2.2). |

**What the table shows (INFERRED).**
- Every part is one of four kinds. A rule is a small structure (S) whose slots are filled by blocks (B), whose blocks carry numbers (N), and which runs at coordinates (K).
- The eight mechanisms in R36 act on different kinds. Mechanisms 1, 3 and 4 move **N**. Mechanism 5 and 6 pick between pre-declared **S** or **B** alternatives. Mechanism 7 moves size. Mechanism 8 (a learned policy) replaces S, B and N together with a model.
- Research 35's practice line maps onto the kinds: moving **N** inside declared rules is routine; picking among declared alternatives by state is "partly" safe; changing **S** or **B** automatically is "the riskiest search" (R35 §4.1, CHECKED).

### 3.3 Knot 1. Systems thinking: the tuning loop

```
source idea -> unit spec (S, B, N, K) -> QMB test -> journal -> tuner -> new N (or new S/B)
      ^                                                                     |
      |__________________ his click (promotion to live) ____________________|
```

- **Reinforcing loop (risk).** Tuner moves N, results improve in-sample, more moves follow. Without a try count the loop rewards noise (R35 §4.2; R11 "gains decay after ~15 rounds", via ST:173). CHECKED.
- **Balancing loop (wanted).** A frozen exam baseline (`ST:21`) and the live-versus-baseline decay check (R08 via ST:171) pull the unit back. CHECKED (ST rows).
- **Delay.** Market-state labels at scalper speed take hours to show (R15 via ST:177). A tuner keyed on state lags the state. CHECKED (ST row).
- **Leverage point (INFERRED).** The authority fact per part. It decides which loop a change enters: a logged in-unit move, a counted research try, or a variant for his click.

### 3.4 Knot 1. The three meanings of self-configuring (R20) against the four kinds

| R20 meaning | What moves | Kinds touched | Who moves it today in other platforms (R20 §2, CHECKED by R20) | Fit with `ST:39` (only he promotes) |
| --- | --- | --- | --- | --- |
| (a) Recalculate the order from a balance and a fixed rule | quantity | N (output only) | the strategy, every trade, no approval | Fits: no rule changes. |
| (b) Update the rule's inputs from finished trades | an estimate (win rate, payoff, volatility) | N | the strategy or helper, no per-change approval | Open: is a moved estimate a "promotion"? |
| (c) Change the trading policy | which sessions, which stops, which rules | S, B, K | "nobody changes policy without a human" (R20, via ST:185) | Needs his click under any reading. |

### 3.5 Knot 1. Mechanism-by-authority grid (options, not a choice)

Rows are R36's eight mechanisms plus bandit selection. Columns are three authority options a unit could carry per part. A cell says whether that pairing is consistent with today's rulings. Nothing is picked.

| Mechanism | A. Moves inside the unit, logged, no click | B. A workflow proposes, counted as a try, re-tested, his click | C. Only as a new variant, his click |
| --- | --- | --- | --- |
| 1 fixed numbers, offline optimiser | not possible (offline by definition) | natural fit | possible if each tuned set is a variant (`GL:150` today) |
| 2 re-optimise on a schedule, live | conflicts with `GL:150`; open under `ST:39` | fits if each re-fit is a try | heavy: a variant per re-fit |
| 3 numbers relative to a live statistic (ATR multiple) | fits: the rule is fixed, the market moves the value | not needed | not needed |
| 4 refit a model every bar or window | open: the model is part of the rule, the refit is data-driven | fits if the refit rule is the thing promoted | possible |
| 5 branch by measured state, pre-declared branches | fits if branches and switch rule were promoted together | fits for adding a branch | fits for adding a branch |
| 6 quality-gated switching between pre-declared sources | as 5 | as 5 | as 5 |
| 7 own record drives size | risk session's call (`ST:93`) | risk session's call | risk session's call |
| 8 learned policy (RL) | open: the whole policy moves | fits per retrain | fits per retrain |
| 9 bandit selection among sibling blocks | open: moves B live | fits | fits |

**Reading (INFERRED).** Column A holds only mechanisms whose *rule for moving* is fixed and promoted once (3, and arguably 4, 5, 6). Everything that changes the rule for moving lands in B or C. That is one way to read "the thresholds self-tune, the branches change only through counted variants" (R35 §4.2). It is not chosen here.

### 3.6 Knot 3. Fishbone: "the dictionary cannot carry agents to every market"

| Bone | Causes found (CHECKED unless marked) |
| --- | --- |
| **Purpose** | Built as a prose library for later coding while QMX was unfinished (`R34 §2.2`). The reason no longer holds (`R34 §2.2` INFERRED; `R39 §5` row 1). |
| **Process** | Written in one morning by four workers under a "Do not create Python" contract (`R34 §2.7`); population then frozen (`R34 §2.2`); two workers died mid-run (`R39 §2.2`). |
| **Scope** | FX and crypto spot only; futures as sources with caveats (`R34 §2.8`). |
| **Content** | 239 entries; 0 of 57 exit entries carry a number (`R34 §3.1`); statistics and models 0 of 40 concepts (`R36 §2.1`); MT5 built-ins all missing (`R36 §0`); six of ten family folders empty (CHECKED `ls S/dictionary/*` this session). |
| **Form** | 12 prose fields (`DR`, CHECKED); ~25 fields and 12 relation types designed, not shipped (`R34 §2.7`); no "how it moves" field (`R36 §6.3`). |
| **Rules** | Role-neutral; "Do not fork per market"; append, do not rewrite; slug collisions allowed (`DR`, CHECKED). No rule for when something is an entry, a profile, an alias or a style (R36 §7 q12). |
| **People and agents** | He is "not so much of a trader" (`GM 2725`, CHECKED by R39 C8). Agents were the domain experts. Recovery agents invented quotes (`R39 O3`). |
| **Placement** | Lives in `Desktop/Stats`, outside the repo by rule (QMA AD-19, via R34 §6 q13); QML reads it from bytes a host passes (`R34 §4.1`). He wants no limbo files (`R41 §2.1`). |

**Root-cause candidate RC5 (INFERRED).** There is no admission rule for what a dictionary entry *is*. Without one, growth either forks per market (forbidden), bloats into ambiguity (what a cheap agent cannot handle), or stalls (today). The 12 fields describe an entry's content, not what earns a slot as an entry versus a profile of an entry, a tag, an instrument fact or an evaluation word.

**Kept alongside.** RC6: two jobs are fused in one artefact. One job is a *vocabulary* (what a source's words mean). The other is a *block catalogue* (what a unit can run). Prose suits the first; code suits the second. The August contract chose the first; the October intent needs both (INFERRED from `T2:779` and `R34 §2.2`).

### 3.7 Knot 4. Attack the premise

Several fixes have been proposed for QML's sizing and exit rules (07 funnel foundations, 01's ATC seam, 34's open questions). They share one premise. Per `principle-attack-the-premise`, I write the premise down and take a census before listing options.

**The premise.** "A bot is a signal source inside a Book. The Book owns money, exits, thresholds and family constraints."

**Census: where the premise is encoded (all CHECKED this session).**

| # | Actor | Where | What it encodes |
| --- | --- | --- | --- |
| 1 | Intent door | `EB:qml/src/qml/protocol/intents.py:1-7` | "An inbound `requested_r` is invalid input. The bot may not size." The declared full-loss price is Book-side. |
| 2 | Example bot | `EB:qml/examples/conformant_bot/bot.py:1-9` | "never sizes... and never carries Book exit logic" |
| 3 | Stage 0 | `EB:qml/src/qml/research/stage0.py:101` | `STAGE0_NEVER_SIZES = True` |
| 4 | QML docs, exits | `QD:106` | `ExitLogicRef` "stays... in the Book's `exit_policy`, per family" |
| 5 | QML docs, numbers | `QD:252` | "every threshold and configurable number... lives in the Book's `admission_bar`, `footprint_requirements`, and `exit_policy`... or in a bot's own declared parameter space" |
| 6 | Families | `EB:qml/src/qml/families/__init__.py:1-7` | "Constraining stays the Book's job." |
| 7 | Glossary, strategy family | `GL:1025` | per-family variables live in the Book's `exit_policy`; a bot declares exactly one family |
| 8 | Glossary, canonical assignment | `GL:150` | live and paper run defaults only; a tuned assignment is a new Bot version |
| 9 | Role collapse | `EB:qml/src/qml/research/collapse.py:60-75` | `context`, `stop`, `exit`, `management`, `target`, `invalidation` fall to "Python WHEN", never a role |
| 10 | Confluence | `EB:…/confluence.py:82-89` | four roles only: level, trigger, confirmation, filter |
| 11 | DNA exits | `DNA:89-110` | `external_policy` label: exits "deliberately deferred to a non-source policy (e.g. ... house risk)" |

**The skew (INFERRED).** All eleven actors are QML or its docs. None is in the operator's October words or in `ST`. The premise is held by the code, not by the people. The thing that assigned the role is the August Book design, retired for units by `ST:21` and `ST:24`.

**A counter-actor already in code (CHECKED).** The Alternative Trading Composition: "a complete second trading system... whose Book/BMS/bot keys are absent, not null" and that "MUST carry a complete PolicyPair of AccountingPolicy + RiskPolicy" (`GL:66`). QML authors it (`EB:qml/src/qml/declaration/alternative.py:1-5`); its risk fields are `max_gross`, `halt`, `sizing`, `override_principal` (`alternative.py:36-41`). R01 and R07 named it the nearest seam (CHECKED, `R01:291`, `R07:190`).

### 3.8 Contributing factors and dynamics, one paragraph (INFERRED)

Three shifts happened in three months: prose library (August), Book-owned bot (September docs), self-configuring unit (October). Each was recorded as law before the next arrived. QML's code is the September layer. The dictionary is the August layer. The unit plan is the October layer. The if-else question is the first time the three are asked to answer one question together, and they cannot, because each was built on a different owner for the same parts.

---

## Step 4. Forces and constraints

### 4.1 Force field

| Driving forces | Restraining forces |
| --- | --- |
| His ruling that the unit owns entry, exits, risk and sizing (`ST:21`, `ST:145`) | Shipped QML laws and tests built on the Book premise (§3.7 census) |
| The need for cheap agents to build without big mistakes (`ST:22`, `T2:779`) | No QMB runner that trades yet, so no measurement can settle tuning questions (`ST:228`) |
| Practice already splits strategies the same way (R35 §0 item 1) | 239 prose entries that he called permanent in August (`R41 §2.1`) and "needs a rebuild" in October (`T2:216` via R34) |
| ATC/PolicyPair already runs a non-Book policy (`GL:66`) | Every automatic move is a try, and tries are not counted at the QMB door yet (`ST:170`) |
| QMB optimiser already reads QML's parameter space (`EB:qmb/src/qmb/optimize/__init__.py:1-11`) | Speed: anything interpreted per tick on the node must be fast; a scalper runs per quote (INFERRED) |

### 4.2 Constraints: real versus assumed

| Constraint | Real or assumed | Evidence |
| --- | --- | --- |
| Only he promotes to live; the only automatic transition is a risk rule stopping a unit | Real (ruling) | `ST:39`, `SO` 7 |
| Plain Python is always possible beside QML | Real (ruling) | `ST:47`, `SO` 9 |
| Units stand alone from the router, MIS, PC link and Library | Real (standing order) | `SO` 10 |
| Nothing capped; providers' limits only | Real | `SO` 9. Note: the workflow `rule` expression language caps expression length at 1,000 and repeat at 10,000 (`EB:…/definition/expr.py:19-20`). If unit rules reused it, that would become a limit. |
| Exits and sizing maths belong to the risk session | Real | `ST:145` |
| Conditions must live in Python | Assumed (V1 choice, DEC-0175) | `QD:82` "in V1" |
| The dictionary must be prose | Assumed (August reason gone) | `R34 §2.2`, `R39 §5` |
| The dictionary lives outside the repo | Assumed (AD-19, contestable) | `R34 §6 q13`; his "not under a Hermes folder" (`R41 §2.1`) |
| Live seats run defaults only | Assumed for units (September law) | `GL:150` vs `ST:21` |
| A family is an attribution key with cardinality one | Assumed for units | `GL:1025`; composites have two parents (`R39 G4`) |
| Four leg roles only | Assumed ("closed-and-addable") | `confluence.py:82-89`; roles beyond four in `R39 C3` |

### 4.3 Key insights (INFERRED)

1. The if-else question is not a tuning-algorithm question. It is a data-shape question: until a rule's parts are visible with kind, motion and authority, no tuning rule can be stated or checked.
2. Practice already sorts the kinds by risk. Numbers inside fixed rules: safe with counted tries. Picking between declared branches: partly safe. Changing structure: riskiest (R35 §4.1). That sorting fits `ST:39` without new machinery.
3. The dictionary problem and the if-else problem meet at one point: a dictionary entry that runs is a block, and a block's numbers are where self-tuning happens.
4. QML's contradictions are one premise, not eleven bugs. Options that replace the premise differ from options that patch each rule.

---

## Step 5. Generate options

Methods: TRIZ contradictions, morphological analysis, assumption busting, SCAMPER, reverse brainstorming. Wild ideas kept.

### 5.1 Knot 1. Options for making a rule's parts tunable (15)

| # | Option | What it changes | Separating evidence or scenario |
| --- | --- | --- | --- |
| K1-1 | **Status quo plus.** Keep conditions in Python; lift every number a rule uses into the declared parameter space; tuning = QMB optimiser over ranges; live = defaults. | Nothing structural | Does a cheap agent lift every number, or hide some in code? A reading test on 10 built units. |
| K1-2 | **Motion field per number.** Add to each declared parameter how it may move (fixed / scaled by a live statistic / refit on a window / chosen by state / learned) with its own settings. | `ParameterSpec` | Can the 17239 example be fully described? Can QMB replay each motion? |
| K1-3 | **Authority field per part.** Each number, block slot and branch carries who may move it (unit itself, workflow with a try, his click). | Every part | Does the operator read it at approval time? |
| K1-4 | **Rules as data.** Conditions become a declared expression or graph that QML evaluates; Python remains an option per node. | Reverses DEC-0175 | Speed per quote on the node; can a cheap agent write it with fewer errors than Python? |
| K1-5 | **Declared branches.** A unit may hold several pre-declared rule sets and a declared switch on measured state (the 17781 pattern, R36 §5.3 item 3). Live switching is allowed because the switch was promoted. | Combinator | Does the switch lag cost more than it gains (R35 §7 q7)? |
| K1-6 | **Volatility-relative numbers by default.** Distances in a unit are written relative to a live statistic unless the source states fixed points. | Comparator | R35 §6 item 15 says this is standard; R36 §4.3 says MQL5 authors write points (84 vs 9 articles). |
| K1-7 | **Tuning as a separate block.** A "tuner" is itself a block with declared inputs (journal fields) and outputs (which parameters), promoted like any block. | New block kind | Can a tuner be replayed in QMB like any block? |
| K1-8 | **Two-speed tuning.** Fast moves (mechanism 3) inside the unit; slow moves (1, 2, 4) as scheduled research runs whose results wait for his click. | Process | Do scalpers need anything faster than a nightly re-fit? |
| K1-9 | **Tuning envelope.** He approves a range per number once; the unit may move inside it by a declared motion; leaving it needs a click. | Authority | Is a range approval one click or many? His "never above his ranges" wording (`ST:201`, an open recommendation) is near this. |
| K1-10 | **Frozen-rule, moving-market.** Nothing moves; only live statistics flow into fixed formulas. Self-configuring means "the formula already contains the market". | Narrowest | Does it meet his "If it can self-tune, I don't have to tune it myself" (`T2:779`)? |
| K1-11 | **Bandit over siblings.** Several sibling blocks (three exits, two triggers) run on paper; the unit's own record ranks them; live uses the promoted one only. | B kind | Is ranking on paper a try? Yes by R35 §4.1; how many tries per bandit round? |
| K1-12 | **Learned policy as a block.** An ML model is one block in the graph with declared inputs and a confidence output (the 39 % of MQL5 articles with a model, R36 §2.2). Retraining is a variant. | B kind | Can its look-ahead be checked (R11 "test window after the model's training cutoff", via ST:173)? |
| K1-13 | **Tune by edit operations.** Every change, live or research, is an edit operation from the PKG list (`replace_parameter`, `change_exit`, …, R39 G2). The operation type decides the authority. | Lineage | Does the edit-type table cover the eight mechanisms? |
| K1-14 | **Wild: the unit writes its own if-else.** An agent rewrites rules in research; QMB judges; he promotes. Live never changes structure. | Process | Same as K1-13 in practice; the difference is who authors. |
| K1-15 | **Wild: a "mini scalper for an indicator".** A whole unit's output (signal, record) becomes an input block for another unit (`FG 796`, CHECKED by R39 C5). Tuning one unit retunes the other's input. | Graph | Does a dependency between units break "units stand alone" (`SO` 10)? |

### 5.2 Knot 1. TRIZ contradictions

| Improve | Worsens | TRIZ principles that apply | Options they suggest |
| --- | --- | --- | --- |
| Adaptivity (the unit tunes itself) | Overfitting and trust (each move is a try) | 2 Taking out; 10 Prior action; 23 Feedback | Take the moving rule out and promote it once (K1-7); decide motion in advance (K1-2); feed live versus baseline back as a stop rule only |
| Expressiveness (rules as data) | Speed and simplicity on the node | 1 Segmentation; 15 Dynamics; 26 Copying | Data form for authoring, compiled form for running; a Python copy per node |
| Cheap-agent safety (few choices) | Coverage (every market, every style) | 6 Universality; 7 Nested doll; 17 Another dimension | One block, many roles; profiles nested in entries; tags on a second axis instead of more entries |
| Operator control (only he promotes) | Operator load (many clicks) | 5 Merging; 24 Intermediary | Approve an envelope of motions once (K1-9); a workflow prepares the evidence |

### 5.3 Knot 3. Morphological analysis of a dictionary entry

Each row is a parameter of the entry's design; each cell an option. Any combination is a candidate design. None is chosen.

| Parameter | Options |
| --- | --- |
| Representation | prose only (today) · prose + formula · prose + reference code · code with a prose card · JSON card + code · code only |
| Granularity | one entry per concept · one generic entry + profiles (e.g. "oscillator with levels") · one entry per variant (ZigZag, swing pivot) |
| Market handling | tags on the entry · per-class profiles inside the entry · overlays outside · separate forks (forbidden by `DR`) |
| Data class it needs | OHLC · quote ticks · displayed depth · trade prints · funding · open interest · liquidations · calendar · fundamentals · positioning (COT) · on-chain · model output |
| Output type | boolean event · level or zone · number series · state label · probability · order intent |
| Roles | open list per entry (today) · computed from output type · closed list per family |
| How its numbers move | none (today) · motion field per parameter (K1-2) · motion in the binding, not the entry |
| Who may append | any agent · a workflow with checks · his click · a curator agent (rejected twice, `R39 N8`) |
| Proof it is right | none · golden values on a fixed series · parity with a platform (TA-Lib, MT5) · replay parity QMB versus live |
| Relations | none (today) · the 12 designed types (`R34 §2.7`) · only alias-of and variant-of |
| Where it lives | Stats (today) · QMX Library · QML package · both with one source |

**Combinations that differ most (INFERRED, for comparison only).**
- **M-A "vocabulary card".** prose + formula · generic + profiles · tags · open roles · motion in binding · workflow appends · golden values · alias/variant relations · Library.
- **M-B "runnable block".** code with a prose card · one entry per concept · per-class profiles · computed roles · motion per parameter · his click for new blocks · parity tests · QML package.
- **M-C "two artefacts".** a prose vocabulary (what words mean, any agent appends) plus a separate block catalogue (what runs, each block cites vocabulary slugs), joined by slug.

### 5.4 Knot 3. TRIZ contradictions for expansion

| Improve | Worsens | Principle | Option |
| --- | --- | --- | --- |
| Breadth (every asset class) | No fork per market | 3 Local quality | Per-class profiles inside one entry: one `stop-reference`, a perps profile with mark/index/last trigger basis (R35 §5.3) |
| Breadth | Agent confusion | 7 Nested doll | Concept → profile → implementation; agents cite the concept, the binding picks the profile |
| Role neutrality | Runnable code (code tends to bake in a role) | 1 Segmentation | Code returns a typed output (event, level, series, state); the role is chosen by the binding |
| Venue truth (funding exists only on perps) | One vocabulary | 2 Taking out | Instrument and venue facts go to an instrument spec (R04 §0.10 via R35 §2.2 reading), not to primitives |
| Statistical tests as vocabulary | Strategy-only scope | 17 Another dimension | A second axis: "evaluation words" live in the judging skill's vocabulary, "sensor words" (Hurst, HMM) live as primitives with a state output |

### 5.5 Knot 3. Assumption busting

| Assumption | Busted by | What becomes possible |
| --- | --- | --- |
| The dictionary must be prose | `R34 §2.2`; `R39 §5` row 1; his "Python is already suitable" (`FG 975`, CHECKED by R39 C7) | Entries that run |
| There is one dictionary | Nothing requires it | Vocabulary plus block catalogue (M-C) |
| Entries are strategy primitives only | 52 % of MQL5 articles use evaluation words (R36 §2.2) | Separate homes for evaluation words, sensor words and strategy words |
| The 239 entries stand | He said "permanent" on 26 Aug (`R41 §2.1`) and "the dictionary needs a rebuild" on 29 Oct (`T2:216`, CHECKED by R34) | Review first, as his 26 Aug words asked ("we should start by reviewing if they are valid", `R41 §1.5`) |
| Role-neutral means no role information | The entry already lists "eligible roles" (`DR` field 8) | Roles computed from output type |
| Market differences need new entries | `DR` "Do not fork per market" | Profiles and tags |
| A model is not a primitive | 39 % of strategy articles use one (R36 §2.2) | "Learned model" as a block kind with declared inputs and a confidence output |

### 5.6 Knot 3. The expansion map (what is missing, by axis; counts from R36, CHECKED by R36)

| Axis | Missing or thin today | Article weight where counted |
| --- | --- | --- |
| Asset classes | futures (roll, expiry, continuous contracts), index CFDs (cash open, RTH/ETH), perps (funding, mark price, OI, liquidations), stock CFDs (dividends, earnings), metals and energies, options (greeks, 83 articles) | R35 §2.2; R36 §2.2 |
| Data classes | quote ticks vs trade prints vs displayed depth (R21 §3), funding, OI, liquidations, calendar, fundamentals (188), positioning/COT (105), alternative bars (98) | R36 §2.2 |
| Statistical tests | ADF/KPSS (169), autocorrelation/variance ratio (83), Hurst (35), cointegration (44), entropy (118) | R36 §2.2 |
| Models | regression (201), clustering (175), neural nets (566), trees (139), HMM (49), GARCH (29), Kalman (14), RL (123) | R36 §2.2 |
| MetaTrader built-ins | CCI, SAR, Williams %R, AO/AC, Alligator, DeMarker, MFI, OBV, A/D, RVI, Force, Bulls/Bears, TRIX (273 together) | R36 §0 |
| Account-level concepts | margin/leverage (114), lot step (79), netting vs hedging (92), stops/freeze level (40), server time and DST (115), prop-firm rules (30) | R36 §2.2 |
| Exits | time-varying targets, unrealised-profit caps, give-back, account halts, probability exits (R35 §5.3); basket, equity kill switch, daily loss, grid average-price TP, close-by (R36 §4.2) | names only; content is the risk session's |
| Styles | trend-following (163), mean reversion (152), scalping (115), arbitrage (70), grid (41) | R36 §2.2 |
| Assembly operators | weighted sum with open/close thresholds (MT5 Wizard) | R36 §0 item 6 |

### 5.7 Knot 4. Options for the premise (not per rule)

| # | Option | What happens to the eleven actors | Separating scenario |
| --- | --- | --- | --- |
| P-1 | **Invert.** The unit owns sizing, exits and thresholds; the Book path stays for old bots only | Actors 1-11 change for units; Book code stays (STATE correction 7: "never casually remove shipped backend work") | Does any shipped QMB test break when a unit sizes? |
| P-2 | **Unit = ATC.** Every unit is an Alternative Trading Composition with its own PolicyPair | Actors 1-3 apply to Book bots only; the unit carries `sizing`, `halt` in its RiskPolicy | Can one PolicyPair hold "self-calibrating" sizing, or only a fixed policy? |
| P-3 | **Book inside the unit.** The Book's `exit_policy` and `admission_bar` become modules the unit embeds | Actors 4, 5, 7 keep their shape but move owner | Does a per-family Book variable make sense per unit? |
| P-4 | **Dual path, one door.** The intent door accepts `requested_r` only when the declaration says the unit sizes | Actor 1 gains a flag | Does a flag create two kinds of unit agents must tell apart? |
| P-5 | **Rewrite from first principles.** Start from the unit and derive what QML needs; keep code that fits | All eleven re-examined | Cost; `ST:26` says shipped backend work takes 2-3 weeks to ship |
| P-6 | **Postpone.** Leave QML laws until the risk session defines the socket | none now | Blocks building any reference unit (`R07` foundation 10 via ST:170) |

### 5.8 Knot 4. Each contradiction worked (premise, options, evidence)

| Id | Contradiction | QML side (CHECKED) | Plan side (CHECKED) | Options | What would separate them |
| --- | --- | --- | --- | --- | --- |
| C-Q1 | Bot never sizes vs unit sizes itself | `intents.py:1-7`; `bot.py:6-9`; `stage0.py:101` | `ST:21`; his "the bot never sizes and the unit sizes itself... we shall have to clear that" (`T1:1177`) | P-1 · P-2 · P-4 · the unit names a sizer block, the door stays closed to the signal half | Which half of a unit emits the size: one callback or a sizer module? |
| C-Q2 | Book owns exits vs unit owns exits | `QD:106`; DNA `external_policy` (`DNA:106`) | `ST:145` | exits as unit roles · exits as a slot filled by the risk session · exits as a Book module embedded (P-3) | Can every one of R35's 16 exit families be replayed in QMB from inside a unit? |
| C-Q3 | Thresholds live in the Book vs numbers are the unit's | `QD:252` | `ST:116` (numbers as editable defaults) | unit-owned parameters · Book-shaped variable set per unit · registry rows per unit | Where does a UI-editable number of one unit live? |
| C-Q4 | "Missing exit means entry hypothesis" vs a unit must have exits | `DNA:40`, `DNA:99`; Stage 0 classes (`stage0.py:67-80`) | `ST:21`; R34 §6 q7-8 | keep the class, add "builder-added" exit label · a unit can only be built from `complete` · an entry hypothesis becomes a unit only with the risk session's default exit set | How many MQL5 strategy sources state no exit: 10 of 36 in extracts (R36 §4.3) |
| C-Q5 | Stage 0 merged but provisional | DEC-0395 `provisional` (`R34 §1.1`) | QML builds units (`ST:22`) | keep Stage 0 as the idea-record layer (R10 gap, ST:172) · fold into the unit spec · replace | Does an idea record need a different shape from a unit spec? |
| C-Q6 | Conditions forbidden in declarations vs "most of it is JSON... similar to a workflow" | `confluence.py:51-61`; `QD:82` | `T2:779` (seed) | K1-1 · K1-4 · a hybrid: declared graph for structure, Python for leaf conditions | Error rate of cheap agents writing each form; node speed |
| C-Q7 | Dictionary outside the repo vs "everything must fit the Library" | AD-19 (via `R34 §6 q13`) | `ST:70`; his "not under a Hermes folder" (`R41 §2.1`) | Library object · QML package data · Stats with a sync | Who edits it, and does an agent in QMX need it offline? |
| C-Q8 | Family cardinality one vs composites with two parents | `GL:1025` | `R39 G4` (`composed_from`); his hybrids (`GM 3262`, CHECKED by R39 G9) | primary family plus parents · multi-family · family = lineage root only | Tries counting per family (R07 via ST:170) with two parents |
| C-Q9 | Context, stop, exit, target fall to "Python WHEN" vs context needs are part of the unit | `collapse.py:60-75` | `ST:21` (condition needs); R16 via ST:178 ("two unit-spec fields") | add roles · a context-needs field outside the confluence · keep context in Python and declare only its inputs | Can the MIS or the analyst agent read a unit's context needs without running it? |
| C-Q10 | Tuned assignment = new Bot version vs moved setting = same unit | `GL:150` | `ST:199` (recommendation, not a ruling) | per motion type (§3.5) · always new version · never new version inside an approved envelope | His answer to "is a moved number a new unit?" (identity, F3P root cause 1) |
| C-Q11 | QML mints no configurable rows vs configurable = UI-editable always | `QD:252` | `ST:116`; his standing rule (memory index entry "configurable = UI-editable always", not read as a file this session: INFERRED from the index line) | the unit's declared parameters are the configurable rows · Library fields · registry rows | Where the UI reads an editable unit number |
| C-Q12 | Four leg roles vs roles beyond four | `confluence.py:82-89` | `R39 C3` (veto, target, sizing modifier, regime detector) | add roles (closed-and-addable) · open roles · roles derived from output type | Does a cheap agent mis-assign more with more roles? |
| C-Q13 | "Strategy family" is a Book key vs "family" as heritage and try pool | `GL:1025` | `F3G` family D3-D5 | rename · keep one word with senses · split words | Glossary step |

### 5.9 Reverse brainstorming: how to make QML fail cheap agents (then reverse)

| How to guarantee failure | Reverse (option) |
| --- | --- |
| Give two names to one thing and one name to two things ("entry" = record and trade; "range" = parameter bounds and a ranging market) | A glossary pass on QML words (`glossary-qml-draft.md`) |
| Let an agent invent a number when the source is silent | Keep the provenance labels (`source-stated`, `unresolved`) and add "builder-chosen" |
| Hide the "if" in code so no reviewer sees it | Make conditions inspectable (K1-4) or summarise them in the card |
| Let the unit move anything live | Authority per part (K1-3) |
| Make every market a new dictionary | Profiles and tags (§5.4) |
| Ship a block without a test of its values | Golden values per block (§5.3 "proof") |

---

## Step 6. Evaluate (criteria only, no selection)

Criteria a later step can use, each tied to a ruling or a standing order:

| Criterion | Source |
| --- | --- |
| A cheap agent builds a unit from a loose source without big mistakes | `ST:22`, `T2:779` |
| The operator can read what will move and approve it in plain words | `ST:39`, `SO` 14 |
| Every move is counted as a try or is a fixed rule promoted once | R35 §6 item 20 |
| Plain Python is never blocked | `ST:47` |
| The unit stands alone on the node | `SO` 10 |
| The risk session's design plugs in without a QML rewrite | `ST:145` |
| QMB can replay everything the unit does live | R04 via ST:166 |
| Nothing capped | `SO` 9 |
| Design for complexity, not a complex system | `ST:20`, `SO` 6 |

Separating experiments (to run later, not now):
1. **Reading test.** Give the 17239 article and one YouTube transcript to a cheap model with each candidate form (K1-1, K1-4, M-A, M-B). Count invented numbers, wrong roles and missing parts.
2. **Speed test.** Evaluate a declared rule graph per quote on the PC for 1m and tick data. Compare with plain Python.
3. **Motion coverage.** Try to write each of R36's eight mechanisms with K1-2's motion field. List what does not fit.
4. **Premise census rerun.** After any QML change, rerun the §3.7 census as a `git grep` over `requested_r`, `never sizes`, `exit_policy`, `admission_bar`, `Book's job`.

---

## Step 7 and 8. Plan and monitoring

Skipped by brief: this is an expansion step, not a plan. The separating experiments above are the inputs a plan would need. Their tags are in `qml-questions.md`.

## Step 9. Lessons from this run

- The if-else question was easier to work once a real article (17239) was broken into parts. Abstract talk about "self-tuning" hid that the parts have four kinds.
- The strongest finding was not in any research file: `GL:150` says live seats run defaults only. Every self-tuning idea has to pass that law or change it.
- The trading lens removed several questions before they were raised (see `qml-questions.md` §0).
