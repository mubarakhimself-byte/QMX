# Questions raised by the QML-depth CIS run

Written 2026-10-30 by the QML-depth CIS agent. Every question raised in `problem-solving.md`, `design-thinking.md`, `seams-options.md` and `glossary-qml-draft.md`, for the wayfinder chart. No answers. Keys and labels as in `problem-solving.md`.

**Tags.**
- `research`: evidence or a measurement would settle it.
- `operator`: his intent, money, vocabulary or irreversible scope (asked only in plain words, one at a time).
- `lead`: a technical call the lead can make at architecture.
- `fog`: cannot be phrased sharply yet.

**Source** names where the question came from: a knot section (`PS §n` = `problem-solving.md`), a contradiction (`C-Qn`, `PS §5.8`), an option (`K1-n`, `S1`-`S7`, `R-A`-`R-E`), a journey or persona (`DT J1`-`J5`, `DT P1`-`P5`), a glossary word (`G:word`). Quotes of his words are CHECKED at the line given.

---

## 0. The trading-lens filter: questions not raised

Each item below came up while working the knots and was dropped because research 35's "any trader knows" list already answers it (R35 §6, CHECKED by R35), or because a ruling does.

| Dropped question | Why not asked | Source of the answer |
| --- | --- | --- |
| Should stops sit where the idea is wrong and define 1R? | Standard practice | R35 §6 item 2 |
| Is the same logic on 1m and 5m two bets? | His ruling: one idea, correlated | `ST:146` |
| Should distances scale with volatility (ATR multiples)? | Standard practice; one setting travels across instruments | R35 §6 item 15 |
| Should a breakout enter with stop orders and a fade with limits? | Standard practice | R35 §6 item 14 |
| Do instruments have session habits (gold at London and NY)? | Standard practice | R35 §6 item 6 |
| Is a strategy context, location, trigger, confirmation, entry type, stop, targets, management, size, halt? | Settled anatomy | R35 §6 item 1 |
| Must same-bar stop and target collisions have a stated rule? | A tester convention | R35 §6 item 18 |
| Does stale data mean no new entries, protection stays? | Usual default; the timeout is a number | R35 §6 item 10 |
| Fewer parameters, out-of-sample judgement and counted tries guard against overfitting? | Settled literature | R35 §6 item 20 |
| Is it safe to take less risk when volatility is high? | Published evidence | R35 §6 item 16 |
| Do FX swap, perp funding and futures roll follow calendars? | Venue facts | R35 §6 item 19 |
| Does one indicator serve many roles? | Role neutrality, settled in August | R35 §6 item 3; `DR:3` |

---

## 1. Knot 1: the if-else question

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q1 | Is "a rule has no inspectable anatomy" the root cause of the if-else question, or is one of RC2-RC4 (three meanings fused, tries uncounted, identity undefined) more basic? | lead | PS §3.1 |
| Q2 | Does every part of a rule fall into one of four kinds (number with a range, structure, block choice, coordinate), or is there a fifth? | research | PS §3.2 |
| Q3 | Can each of R36's eight self-tuning mechanisms be written as a "motion" on a declared number? Which ones cannot? | research | PS §3.5, K1-2 |
| Q4 | Which of the three authority options (moves in the unit and logged; a workflow proposes as a counted try; only as a new variant) does each mechanism belong to? | lead | PS §3.5 |
| Q5 | In plain words for him: after he promotes a unit, may it change any of its own numbers without asking him again, as long as they stay inside ranges he approved? | operator | PS §3.4 (R20 meaning b); his "If it can self-tune, I don't have to tune it myself" (`T2:779`) |
| Q6 | Today's law runs live seats on defaults only and makes a tuned assignment a new version (`GL:150`). Is that law kept for units, changed per motion type, or dropped? | lead | C-Q10 |
| Q7 | Who counts tries when a unit moves a number live, and are moves inside an approved envelope tries at all? | research | RC3; R35 §7 q9 |
| Q8 | Does a "chosen by measured state" switch (17781 pattern) lag the state by more than it gains at 1m, 5m and 15m? | research | K1-5; R35 §7 q7 |
| Q9 | Is "frozen rule, moving market" (only live statistics flow into fixed formulas) enough to meet his idea of self-configuring? | operator | K1-10 |
| Q10 | Should every literal number in unit logic be a declared parameter, enforced by a check? | lead | DT idea 2 |
| Q11 | Should a builder be allowed an `unresolved` number that a QMB sweep may explore but live refuses? | lead | DT idea 3 |
| Q12 | Is a "tuner" its own block, promoted and replayed like any block, or a field on each number? | lead | K1-7 vs K1-2 |
| Q13 | Can an ML model be one block with declared inputs and a confidence output, and is retraining a variant? | lead | K1-12 |
| Q14 | Must an LLM-built unit be tested on a window after the model's training cutoff (R11 via `ST:173`)? | research | K1-12 |
| Q15 | What does "self-configuring" read and change, concretely, for one reference unit? A worked 17239 example would show it. | research | `ST:78`; PS §3.2 |
| Q16 | Does a bandit over sibling exits on paper count as one try per round or one per sibling? | research | K1-11 |

## 2. Knot 2: the three layers and the seams

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q17 | Where does a rule's structure live: in Python (S1), in declared data (S2), or in a fixed port shell (S3)? | lead | `seams-options.md` §7 |
| Q18 | How fast must a declared rule graph evaluate per quote on the PC and on the node for a 1m scalper? | research | S2; PS Step 6 test 2 |
| Q19 | Do cheap models invent fewer numbers and roles when writing a declared graph than when writing Python? | research | S2 vs S1; DT Step 6 |
| Q20 | Does DEC-0175 ("condition semantics live in Python logic in V1") still hold, or was "V1" the end of it? | lead | C-Q6; `QD:82` |
| Q21 | Should the weighted-sum-with-threshold operator (MT5 Wizard) join the graph operators, or is it `K_OF_N` with weights? | lead | R36 §7 q4 |
| Q22 | Which roles beyond four join the closed-and-addable set: veto, target, sizing modifier, regime detector, context, invalidation, stop, exit, management? | lead | C-Q12; R39 C3 |
| Q23 | Do roles come from a list, or from a block's output type (event, level, series, state, probability, intent)? | lead | `seams-options.md` §4 |
| Q24 | Can a unit use another unit's output as an input ("a mini scalper for an indicator", FG 796) and still stand alone? Build-time only, or live with a fallback? | lead | S7; `SO` 10 |
| Q25 | Is composing two units into one input a hidden correlation that the try count and the pod must see? | research | S7; `ST:146` |
| Q26 | Does every unit become an Alternative Trading Composition (own PolicyPair), and can a PolicyPair hold a sizer that moves itself? | lead | S5; `GL:66` |
| Q27 | Could the QMX workflow engine run unit rules, or does standing alone rule it out (engine is agent-side today)? | lead | S6; `SO` 10 |
| Q28 | If unit rules reuse the workflow expression language, its 1,000-character and 10,000-repeat limits come with it (`expr.py:19-20`). Keep, lift, or use another language? | lead | S6; `SO` 9 |
| Q29 | Where do views (pillars, lenses) live: generated from the record each time, or stored? | lead | G:view |
| Q30 | Should timing, session and direction be per leg (DNA bindings) or per unit? | lead | `seams-options.md` §1 |
| Q31 | Is the confluence (shallow for running, deep for identity) kept, merged into the graph, or retired? | lead | `seams-options.md` §0 deletion test |
| Q32 | How does a structural diff between two units look, so the analyst agent can say "same blocks, moved numbers"? | lead | DT J4 |

## 3. Knot 3: the dictionary

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q33 | What earns a slot as an entry, versus a profile of an entry, a tag, an instrument fact, a style or an evaluation word? | lead | RC5 |
| Q34 | Is it one artefact (vocabulary that runs) or two (vocabulary plus block catalogue joined by slug)? | lead | RC6, M-C |
| Q35 | Which of the 12 fields stay prose and which become code or schema? | lead | R34 §6 q1; PS §5.3 |
| Q36 | Do the 239 August entries get reviewed first, as his 26 Aug words asked ("we should start by reviewing if they are valid", R41 §1.5), before any rebuild? | lead | PS §5.5 |
| Q37 | In plain words for him: the August dictionary was written in one morning by four agents. Keep it as the starting point and fix it, or start again and keep the old one only as a reference? | operator | `T2:216` "needs a rebuild" (CHECKED by R34) vs "permanent" (R41 §2.1) |
| Q38 | Do statistical tests and models (ADF, Hurst, HMM, GARCH, regression, clustering, neural nets) enter as primitives with a state or probability output, or live elsewhere? | lead | R36 §7 q1-2 |
| Q39 | Do MT5's built-in indicators get one entry each, or one generic "oscillator with levels" entry plus profiles? | lead | R36 §7 q3 |
| Q40 | How does a user's own custom indicator (iCustom, 214 articles) enter: as a block anyone may register? | lead | R36 §2.2 |
| Q41 | Where do evaluation words (Sharpe, PBO, walk-forward) live: in the judging skill's vocabulary? | lead | R36 §3.1 |
| Q42 | Is broker server time a session primitive, a data dependency, or an instrument fact? | lead | R36 §7 q7; DT J1 step 4 |
| Q43 | Do alternative bars (Renko, range, tick, volume, Heikin-Ashi) live as BarSpec kinds only, or also as primitives? | lead | R36 §7 q9; `GL:98` |
| Q44 | How do futures, index CFDs, perps, stock CFDs, metals and energies enter without forking: per-class profiles, tags, or instrument specs? | lead | PS §5.4, §5.6 |
| Q45 | Which data classes does each entry declare it needs (OHLC, quotes, depth, trade prints, funding, OI, liquidations, calendar, fundamentals, positioning)? | lead | PS §5.3 |
| Q46 | How well does futures order flow stand in for CFD flow on the same index? | research | R35 §7 q8; his "Order flow is good for scalpers" (`T2:132`, CHECKED by R35) |
| Q47 | Are grid, martingale, averaging and hedging (172 articles) a family, excluded by design, or a guard's concern? | operator | R36 §7 q11 (risk appetite is his call) |
| Q48 | Is a variant of a concept (ZigZag vs swing pivots, KAMA vs MA) an alias, a profile, or its own entry? | lead | R36 §7 q12 |
| Q49 | Do the 12 designed relation types (alias-of, contradicts, supersedes, …) ship, or only a few? | lead | R34 §6 q17 |
| Q50 | Do the nine kept slug collisions survive when each entry has one implementation? | lead | R34 §6 q18 |
| Q51 | What proves a block computes what its entry says: golden values, platform parity, QMB-versus-live parity? | lead | PS §5.3 "proof" |
| Q52 | Who may append an entry: any agent, a workflow with checks, or his click? (A curator agent was rejected twice, R39 N8.) | lead | PS §5.3 |
| Q53 | Does the dictionary move into the QMX Library or the QML package, and does AD-19 ("Forbid" git absorb) still hold? | lead | C-Q7 |
| Q54 | Should strategy styles (trend-following, mean reversion, scalping, arbitrage, grid) be a layer above primitives? | fog | R36 §7 q6; ties to the funnel3 "trading style" word |
| Q55 | Does a source's "market context" ("the source tells us which market context the strategy is meant to work in", `T1:1951`, CHECKED) become a declared context need on the unit? | lead | C-Q9 |

## 4. Knot 4: contradictions with the unit plan

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q56 | Is the premise "a bot is a signal source inside a Book" replaced for units (P-1, P-2, P-3, P-5), patched rule by rule (P-4), or postponed (P-6)? | lead | PS §3.7, §5.7 |
| Q57 | Which half of a unit emits the size: the one callback, or a separate sizer module? | lead | C-Q1 |
| Q58 | Can each of R35's 16 exit families run inside a unit and replay in QMB? | research | C-Q2 |
| Q59 | Where does a UI-editable number of one unit live: its declared parameters, Library fields, or registry rows? | lead | C-Q3, C-Q11 |
| Q60 | Is "missing exit means entry hypothesis" kept as a class, with a "builder-added" label when a unit gets exits? | lead | C-Q4; R34 §6 q7-8 |
| Q61 | How many real sources state no exit: 10 of 36 MQL5 extracts did (R36 §4.3); what about YouTube sources? | research | C-Q4 |
| Q62 | Is Stage 0 kept as the idea-record layer in front of units (R10 gap), folded into the unit spec, or replaced? | lead | C-Q5 |
| Q63 | Does a composite unit with two parents have one family, two, or a family that is only its lineage root? | lead | C-Q8 |
| Q64 | Can the MIS and the analyst agent read a unit's context needs without running its code? | lead | C-Q9 |
| Q65 | Does "strategy family" (a Book key in `GL:1025`) keep its name now that "family" also means heritage and try pool? | operator | C-Q13; vocabulary he cares about |
| Q66 | After a QML change, does a rerunnable census (`git grep` for `requested_r`, `never sizes`, `exit_policy`, `admission_bar`, `Book's job`) show the premise is gone from the unit path? | lead | PS Step 6 test 4 |

## 5. Knot 5: room for the risk-and-sizing session

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q67 | Which socket shape does that session want: two ports (R-A), one risk module (R-B), graph roles (R-C), a PolicyPair (R-D), or a library call (R-E)? | lead (for that session) | `seams-options.md` §6.2 |
| Q68 | Which inputs must QML make readable to a sizer (entry, stop, instrument facts, account facts, own journal in R, volatility, his limits)? | lead (for that session) | `seams-options.md` §6.1 item 3 |
| Q69 | Do exits act per position, per basket, or per account, and can one socket carry all three? | lead (for that session) | `seams-options.md` §6.1 item 2 |
| Q70 | Can a unit's own halt stop it with no click and no router, and be logged as the one automatic transition? | lead | `ST:39`; `SO` 10 |
| Q71 | Which journal fields does the risk session need (size chosen, size refused, halt fired, exit fired with reason)? | lead (for that session) | `seams-options.md` §6.1 item 5 |
| Q72 | Do risk numbers get the same motion and authority fields as rule numbers? | lead | `seams-options.md` §6.1 item 4 |

## 6. Words

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q73 | "Range" has seven meanings, four of them trading senses. Which words does QML use for parameter bounds and approved envelopes so a source's "range" is never misread? | lead | G:range |
| Q74 | "Role" means a strategy job and, in QMX's agent system, an agent persona (`GL:882`). Keep one word with two senses, or rename one? | operator | G:role; vocabulary |
| Q75 | "Entry" means a dictionary record and a trade entry. Rename the record (for example "term" or "concept")? | operator | G:entry; vocabulary |
| Q76 | "Block" is the node's refusal state (`GL:300`). Can QML use "block" for parts at all? | lead | G:block |
| Q77 | Is "motion" (how a number may change) worth a word, and which: motion, adaptation, tuning rule? | operator | G:motion; vocabulary |
| Q78 | Does "pillar" keep his four, the lock's four, or practice's ten parts as the unit's human view, and is risk and sizing back in? | operator | G:pillar; R34 §6 q4-5 |
| Q79 | Is "event" (his 28 Oct pillar, `T1:2051`) its own lens or the trigger? | fog | G:pillar |

## 7. Personas and journeys

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q80 | What does his approval click cover: the unit as it is, or the unit plus an envelope of future moves? | operator | DT J2 step 4 |
| Q81 | What must fit on one phone screen for him to approve a unit? | operator | DT J2; DT idea 1 |
| Q82 | Does a plain-Python unit or ML ensembler get the same journal, judge, risk socket and UI as a QML unit, through a thin wrapper? | lead | DT J3 |
| Q83 | Does Stage 0 need a "video" origin kind with timestamp lineage, or does lineage live only in Library links? | lead | DT J1 step 1 |
| Q84 | Should a "what any trader knows" sheet be a skill agents read before raising any question to him? | lead | DT idea 15; his `T2:836` |
| Q85 | Which of the four prototypes (paper card for 17239, two-form build by a cheap model, human-as-runtime, approval storyboard) run first? | lead | DT Step 5 |
| Q86 | "Multiple experiences" means his user experience of trading with units (`T2:849`). What does QML add to that experience beyond what a simple bot gives? | fog | `T2:849`; `ST:137` |

---

## Counts

86 questions: research 13, operator 11, lead 59 (four of them for the risk session), fog 3. Counted by `grep` over the tables. Plus 12 dropped by the trading-lens filter in §0.
