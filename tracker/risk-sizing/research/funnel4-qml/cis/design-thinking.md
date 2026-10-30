# CIS design thinking: the people and agents who use QML

Written 2026-10-30 by the QML-depth CIS agent. Method: `bmad-cis-design-thinking` (SKILL.md and `design-methods.csv` read), run straight through with no human present. Where the skill asks me to select concepts or plan, I cluster and list. Nothing is chosen. Keys and labels as in `problem-solving.md`.

**How this differs from funnel3's design thinking (`research/funnel3/cis/design-thinking.md`).** That file's personas were the operator, a market-analysis agent, a unit-analysis agent, the copilot and the unit. This file looks only at QML: who writes units with it, who reads what it produces, who works beside it. Exits and sizing appear only as slots the risk session fills (`ST:145`).

---

## Step 1. The design challenge

**Challenge.** QML is "literally the wrapper for this entire thing" (`T1:2051`, CHECKED). It must let a cheap agent turn a loose source into a whole unit without big mistakes, let the operator read and approve that unit in plain words, never block a human writing plain Python or an ML ensembler, and leave a record an analyst agent can read and prove claims from.

**Challenge statement.** How might QML give each of its five users exactly the vocabulary and the shape they need, so the same unit is easy to build, easy to approve, open to plain code, and easy to judge?

**Constraints (CHECKED rulings).** Only he promotes (`ST:39`). Plain Python always possible (`ST:47`). Units stand alone (`SO` 10). Nothing capped (`SO` 9). Numbers ship as editable defaults (`ST:116`). Design for complexity, not a complex system (`ST:20`).

---

## Step 2. Empathize

Methods chosen from the CSV: empathy mapping, journey mapping, jobs to be done, shadowing (done by reading the transcripts and the MQL5 sample as "observed behaviour"), analogous inspiration (in Step 4).

### 2.1 Persona P1: the cheap building agent

A fast, low-cost model in a QMX workflow. Small context window. Strong at following a template, weak at domain judgement. He named cheap workhorses as the builders: "most of the work I've been talking about is done by cheap workhorses. Okay, like DeepSeek or something" (`T1:513`, CHECKED).

| Says | Thinks | Does | Feels |
| --- | --- | --- | --- |
| "The source says 'wait for a strong candle'." | Is "strong" a number? Do I make one up? | Writes "body > 70 % of range" because it looks plausible | Unsure, but the template wants a value |
| "He says London." | London open in which time zone? Broker server time? | Picks UTC 08:00 | Nothing tells it broker time exists (missing word, 115 articles, R36 §2.2) |
| "BOS, CHoCH, MSS..." | Are these three things or one? | Creates three entries or picks one at random | The dictionary keeps disagreements "as profiles" (R40 §4 row 18) but it cannot see them as code |
| "No exit given." | A unit must trade. Do I invent one? | Either refuses (DNA "Do not invent exits", `DNA:99`) or invents a 1:2 target | Caught between two rules (C-Q4 in `problem-solving.md`) |
| "Should this be Python or JSON?" | Python is easier to write, JSON is easier to check | Writes Python, hides thresholds inside it | Nobody will notice the hidden numbers |

**Jobs to be done.** Functional: turn a transcript into a runnable unit spec plus logic, with every part cited to the source. Emotional (for an agent, read "failure modes it avoids"): avoid inventing, avoid choosing the wrong role, avoid the template's empty field.

**Observed behaviour, as shadowing (R36 §5.2 sample of 36 MQL5 strategy articles, CHECKED by R36).** Authors write fixed numbers and let the optimiser pick (stops in points in 84 articles, in ATR in 9). 10 of 36 show no exit. Multi-timeframe appears as two inputs. A builder agent fed these sources will meet the same gaps.

### 2.2 Persona P2: the operator

A developer, not a trader by his own words ("I'm not so much of a trader, but I'm good with dev work", `GM 2725`, CHECKED by R39 C8). Dictates. Often reads on a phone. Wants the system to do the tuning: "If it can self-tune, I don't have to tune it myself" (`T2:779`, CHECKED). Wants the user experience of trading with units to beat "a person just using a simple bot" (`T2:849`, CHECKED). Hates being asked what any trader knows ("even me as a newbie trader, I already know what they mean", `T2:836`, CHECKED).

| Says | Thinks | Does | Feels |
| --- | --- | --- | --- |
| "Keep it stupid simple... design for complexity" (`T1:1177`) | The inside can be complex; the face must be simple | Reads summaries, then asks for depth | Frustrated by long lists of trivial questions |
| "No vibe trading" (`ST:51`) | Every unit must trace to a source | Asks where a unit came from | Distrust when lineage is missing |
| "Only he promotes" (`ST:39`) | Nothing goes live without me | Clicks promote | Needs to know what the click approves |
| "a bot that has ambiguity shouldn't be tested" (`GM 3262`, CHECKED by R39 K14) | Gaps must be visible | Wants tags or colour coding | Annoyed when agents fill gaps silently |

**Jobs to be done.** Functional: approve a unit and know exactly what may change after approval. Emotional: trust that the system is not trading on a guess. Social: none (QMX is his own platform, `ST:29`).

### 2.3 Persona P3: the plain-Python or ML author

Him in the lab or a mini app, or a stronger model asked to write an ML ensembler. "When I want to rewrite a unit using nothing that QMX has, or maybe pure Python... We shouldn't be limited in any way, shape, or form" (`T1:1574`, CHECKED). "I may not make a unit, but I might make maybe an ML ensembler" (`T1:1574`, CHECKED).

| Says | Thinks | Does | Feels |
| --- | --- | --- | --- |
| "I just want to test this model" | Why must I learn roles and bindings? | Writes a Python class with `predict()` | Blocked if QML insists on its vocabulary |
| "Show me how it did" | QMB and the journal should work anyway | Wants QMB results and a journal | Second-class if the UI shows nothing for it |
| "Use the same risk as the others" | Sizing and exits should plug in | Calls the risk socket | Lost if the socket only speaks QML |

**Today's code already has his door (CHECKED).** "Three legal entries, none a toll booth": ungoverned Python into QMB with zero QML, registration without Stage 0, or Stage 0 then graduation (`QD:210`).

### 2.4 Persona P4: the analyst agent reading a unit's record

A QMX workflow agent that judges units (a seed: "QMX agents as analysts", `ST:118`). It reads journals, QMB results and lineage. It must prove what it claims (the funnel3 finding: uncheatable proof separates who claims, who controls inputs, or when it is scored, `ST:182`).

| Says | Thinks | Does | Feels |
| --- | --- | --- | --- |
| "Win rate fell from 58 % to 49 %" | Did a number move, did the market move, or did the unit change? | Searches the journal for changes | Blind if moves are not logged with their kind |
| "This trigger is weak" | Which block is the trigger in this unit? | Reads the logic | Blind if the logic is opaque Python |
| "This unit is a copy of that one" | Same blocks, different numbers? | Compares two units | Needs a structural diff, not a text diff |
| "Signals were detected but not taken" | Why were they skipped? | Reads the skip reasons | Needs the journal to log not-taken signals (`ST:57`) |

### 2.5 Persona P5 (added): the risk-and-sizing session

A later session that will design exits, stops, targets and sizing maths (`ST:145`). It is a user of QML's seams, not of its vocabulary. It needs: which inputs a sizer can read, which exit slots exist, which numbers may move by themselves, and where its results are journaled. Worked in `seams-options.md` §6.

### 2.6 Key observations across personas (INFERRED)

1. P1 and P4 need the opposite of what P3 needs. P1 and P4 need every part of a rule named and typed; P3 needs to skip all of it.
2. P2 needs one thing from all of them: a plain statement of what may change after his click.
3. The places where P1 invents things (strong candle, London, no exit, hidden thresholds) are exactly the places the if-else question asks about: numbers, coordinates, block choices and structure (`problem-solving.md` §3.2).
4. P4 cannot judge a self-tuning unit unless every move is logged with its kind and authority.

---

## Step 3. Define

### 3.1 Point-of-view statements

- **P1** needs a place for every part of a source's rule, including the parts the source left out, because otherwise it fills gaps with plausible numbers nobody can see.
- **P2** needs to approve a unit by reading what will move and what will not, because self-configuring without that is a black box he cannot trust.
- **P3** needs an exit from QML that still reaches QMB, the journal and the risk socket, because a vocabulary that blocks a model is a cage (`ST:43`).
- **P4** needs a record that separates market change, number change and rule change, because otherwise every judgement is a guess.
- **P5** needs stable slots for exits and sizing, because its maths must plug into every unit without a QML rewrite.

### 3.2 How might we

1. HMW let a cheap agent say "the source did not say" without blocking the unit from trading?
2. HMW make a hidden threshold impossible, or at least visible?
3. HMW show the operator, in one screen, what a unit may change by itself?
4. HMW let a unit be self-configuring while every move stays a counted, logged event?
5. HMW turn "London open" into one correct time across brokers and daylight saving?
6. HMW make BOS, CHoCH and MSS one concept with profiles instead of three guesses?
7. HMW let a plain-Python unit appear in the same UI, journal and judging as a QML unit?
8. HMW let an ML model be one block among others instead of a separate world?
9. HMW let a "mini scalper" feed another unit as an indicator without breaking "units stand alone"?
10. HMW let the dictionary grow to futures and perps without forking per market?
11. HMW make a dictionary entry runnable and still role-neutral?
12. HMW give the analyst agent a structural diff between two units?
13. HMW keep the source's honesty labels after a builder adds an exit?
14. HMW stop agents asking questions any trader already knows (`T2:836`)?
15. HMW let the risk session ship its exits and sizer as blocks every unit can use?
16. HMW let an approved unit move a number inside a range without minting a new version each time (today's law, `GL:150`)?
17. HMW make "what a unit is made of" readable on a phone?
18. HMW keep the 239 August entries useful while the dictionary is rebuilt?

### 3.3 Problem insights (INFERRED)

- The builder's main danger is not missing knowledge but silent invention. Most fixes are about making absence visible.
- The operator's approval is the bottleneck of trust. Anything that lets one click cover a bounded set of future moves reduces his load.
- The analyst can only be as good as the kinds the record keeps.

---

## Journeys

### J1. A cheap agent turns a loose YouTube source into a unit

Source example (INFERRED composite of common practice, built to stress QML; each trader fact is from R35 §6 or R36): a podcast trader says "I trade the London breakout of the Asian range on gold. I wait for a strong candle to close outside, enter on the retest, stop on the other side of the range, and I'm usually out before New York lunch."

| Step | What the agent does | What it meets in QML today (CHECKED where marked) | Pain | Options (not chosen) |
| --- | --- | --- | --- | --- |
| 1 Intake | Gets the transcript and frames | Stage 0 origins `idea`, `chart`, `journal`, `seed_package` (`EB:qml/src/qml/research/stage0.py:76-83`) | No "video" origin; lineage to the timestamp must live elsewhere | Add origin kinds · keep lineage in the Library link set |
| 2 Find claims | Splits the talk into rule claims with timestamps | Nothing in QML; the H4 rule "every detected rule must point back to timestamps" lives in the August design (`R39 H4-H5`) | Claims and rules are not the same thing | A claim record before the unit · claims inside the unit card |
| 3 Map words | "Asian range", "London", "strong candle", "retest", "range" | `session-range`, `opening-range` exist (R35 §1.3); "strong candle" partly as `wick-rejection-bar` (R36 §2.2) | "Range" means both a session box and a ranging market | Glossary pass (`glossary-qml-draft.md` "range") |
| 4 Time | "London", "New York lunch" | Broker server time / DST missing (R36 §2.2) | Picks a wrong hour; gold has strong London and NY sessions (R35 §2.2) | A session primitive with a time-zone profile · a data dependency |
| 5 Bind roles | Asian range = location; breakout close = trigger; retest = entry; strong candle = confirmation | Four leg roles (`confluence.py:82-89`) | "Retest entry" is entry semantics, not a leg role; it collapses to Python WHEN (`collapse.py:60-75`) | More roles · entry semantics as its own field |
| 6 Numbers | "strong" candle; range start and end; retest tolerance | Parameter space with bounds and default (`parameters.py:1-7`) | Every number must have a default, so the agent invents one | An `unresolved` default that blocks live but allows a sweep · a "builder-chosen" label |
| 7 Exits | Stop across the range; "out before NY lunch" | DNA labels `source_defined`, `unresolved` (`DNA:89-110`) | A time exit is stated, a target is not | Partial exit sets are allowed with labels; the risk session's defaults fill the rest (slot only) |
| 8 What tunes | Range hours, candle strength, retest tolerance, time exit | No motion or authority field (`problem-solving.md` §3.1) | Agent cannot say which numbers move live | Motion and authority fields (K1-2, K1-3) |
| 9 Write the logic | Python callback or a data graph | Conditions must be Python (`confluence.py:51-61`) | Thresholds end up hidden in code | Rules as data · a lint that every literal number in the logic is declared |
| 10 Check | Layer 1 linter, Layer 2 verdict | `layer1.py`, `layer2.py` (via R34 §4) | Technical checks only, "never performance" | Add a "source honesty" check |
| 11 Test | Requests a QMB run | The runner that trades does not exist yet (`ST:228`) | Cannot test | Blocked on QMB, outside QML |

**Trading-lens notes on J1 (R35 §6, CHECKED by R35).** The stop goes where the idea is wrong and sets 1R (item 2). Breakouts use stop orders, retests use limits (item 14). Gold's London and NY habits are real (item 6). None of these should become questions to the operator.

### J2. The operator reads and approves a unit

| Step | What he sees today | Pain | Options |
| --- | --- | --- | --- |
| 1 A card arrives | Library `unit` kind with empty fields and tabs Logic, Results, Family tree, Markets, Versions (R18 via F3G "unit" D9) | No content yet | A one-screen card: source, parts, what moves, what is unresolved |
| 2 Is it honest? | Nothing marks invented parts | He cannot tell source from builder | Colour per provenance label (his August ask, R39 F8) |
| 3 What will change? | Nothing | Self-configuring is invisible | A "moves by itself" list with ranges · a "needs my click" list |
| 4 Promote | A click | Does the click cover future moves? | Click approves the unit plus its motion envelope · click approves only the current numbers |
| 5 Later | Journal entries | Moves mixed with trades | A separate "changes" lane in the journal |

### J3. A human writes plain Python or an ML ensembler beside QML

| Step | Need | Today (CHECKED) | Options |
| --- | --- | --- | --- |
| 1 Write | Any Python | Entry (1): ungoverned Python into QMB with zero QML (`QD:210`) | Keep |
| 2 Test | QMB run | Same door | Keep |
| 3 Journal | Same journal as units | Journal schema not built (`ST:170` foundation 3) | Journal accepts any producer with a minimal header |
| 4 Risk | Same sizer and exits | The intent door refuses `requested_r` (`intents.py:1-7`) | A risk socket callable from plain Python · a wrapper that turns any Python class into a unit with default slots |
| 5 Judging | Same judge | Judging skill not built (`ST:90`) | The judge reads results, never the logic |
| 6 Promote | His click | Same click | Same click |

### J4. The analyst agent reads a unit's record

| Step | Question | What it needs from QML | Today |
| --- | --- | --- | --- |
| 1 | "What is this unit made of?" | A structural listing of blocks, roles, numbers, coordinates | Opaque Python plus a declaration |
| 2 | "What changed since the exam baseline?" | A change lane with kind (N, S, B, K) and authority | Nothing |
| 3 | "Did context matter?" | Context labels stamped at entry (R16 via ST:178) | QMB stamps none |
| 4 | "Is this a copy of another unit?" | Block-level diff and lineage links | Library has `variant-of` and 38 other link types (R18 via F3G variant D3) |
| 5 | "Can I prove it?" | Inputs it did not choose, scored later (`ST:182`) | Not built |

### J5. The risk session plugs in (short; full in `seams-options.md` §6)

It needs a list of slots (initial stop, targets, management, time exits, account halts, size), the inputs each slot may read, how its numbers may move, and where its outputs land in the journal. Nothing in QML today offers these as unit-owned slots (C-Q1, C-Q2).

---

## Step 4. Ideate

Methods: brainstorming, SCAMPER design, analogous inspiration, provotype sketching. Judgement deferred.

### 4.1 Analogous inspiration

| Field | How it solves a similar problem | Idea for QML |
| --- | --- | --- |
| MT5 Wizard | Signal + trailing + money modules; signals weighted 0..100 against open/close thresholds (R35 §1.2; R36 §5.3) | Fixed ports with weighted signals |
| Pine strategies | Entry, exit bracket, account halts (`strategy.risk.*`) as separate commands (R35 §1.2) | Three layers in one script with a fixed order |
| freqtrade | An explicit table of which exit callback to use when; fixed check order (R35 §1.2) | A documented exit-slot order |
| Music production (DAW automation lanes) | A track's knobs can carry an automation lane: fixed, drawn, or driven by another signal | A "motion lane" per number: fixed, scaled by a live statistic, refit |
| Medical coding (ICD with modifiers) | One code per condition plus modifiers, never a code per hospital | One dictionary entry plus profiles and tags, never a fork per market |
| Lego | Studs make any brick fit any brick; special bricks still use studs | A small typed output per block (event, level, series, state, probability) so any block fits any role slot |
| Aviation checklists | Each line is a fixed item, read aloud, ticked or flagged | The unit card as a checklist with "source said / builder chose / unresolved" |
| Package managers | Versions, ranges, lock files | Approved ranges per number as a lock; a move outside the lock is a new version |
| Spreadsheets | Formulas visible, values computed | Rules visible as formulas, numbers as cells with ranges |

### 4.2 Generated ideas (30, unranked)

1. A unit card on one phone screen: source, four-kind parts list, "moves by itself", "needs your click", "unresolved".
2. A lint that fails when a literal number in unit logic is not a declared parameter.
3. An `unresolved` default value that QMB may sweep but live refuses.
4. A "builder-chosen" provenance label beside `source-stated` and `unresolved`.
5. Motion lanes per number (fixed / scaled / refit / by state / learned).
6. Authority per part (unit / workflow with a try / his click).
7. A change lane in every journal with the part's kind.
8. Session primitives with a time-zone profile (exchange, broker server, UTC, New York) and DST rules.
9. One concept per structure-break word (BOS, CHoCH, MSS) with profiles for close-vs-wick and lookback.
10. A typed output for every block so roles are chosen by output type.
11. A Python adapter that wraps any class with `on_bar` into a unit with default slots.
12. ML model as a block with declared features and a confidence output.
13. A unit's signal stream published as a block other units may read, with a declared fallback when it is missing.
14. Structural diff between two units: blocks added, removed, swapped, numbers moved.
15. A "what any trader knows" sheet agents read before asking him anything (from R35 §6).
16. A "source honesty" check in conformance: every part carries a label.
17. A dictionary entry with a card (prose) and a reference implementation (code), joined by slug.
18. Golden values per block on a fixed series, so a wrong implementation fails.
19. A per-class profile for stops: trigger basis last, mark or index for perps (R35 §5.3).
20. Weighted-sum-with-threshold as a graph operator (Wizard style).
21. A "tuner" block, promoted like any block, that moves declared numbers from journal fields.
22. Sibling exits run on paper with the unit's record ranking them; live uses the promoted one.
23. A two-sentence plain-words summary written by the builder and checked against the structure.
24. Approve an envelope once: ranges plus motions; moves inside it are journal events.
25. An idea record before the unit (claims with timestamps), kept as the lineage root.
26. Evaluation words (Sharpe, PBO) kept out of the strategy dictionary and in the judging skill.
27. Instrument facts (tick value, swap times, funding hours) kept in an instrument spec, not in primitives.
28. "Mini scalper for an indicator" only at research time; live units read their own copy (stand-alone safe).
29. Provotype: a unit with no numbers at all, every number a live statistic. Shows what self-configuring could mean at its extreme.
30. Provotype: a unit that is only Python with a one-page card. Shows the minimum QML can ask of P3.

### 4.3 Concepts worth prototyping (clustered, unranked)

| Cluster | Ideas | Serves |
| --- | --- | --- |
| **Visible absence** | 3, 4, 16, 25 | P1, P2 |
| **Visible motion** | 5, 6, 7, 21, 24 | P2, P4, P5 |
| **No hidden numbers** | 2, 23 | P1, P4 |
| **Words that travel** | 8, 9, 17, 19, 26, 27 | P1 |
| **Blocks that fit anywhere** | 10, 12, 13, 20, 28 | P1, P3 |
| **Open door for plain code** | 11, 30 | P3 |
| **Judging aids** | 14, 18, 22 | P4 |
| **Fewer trivial questions** | 15 | P2 |

---

## Step 5. Prototype (low fidelity, to learn, not to build)

| Prototype | Method | What it would teach |
| --- | --- | --- |
| A paper unit card for 17239 (Asian box breakout) | Paper prototyping | Whether four kinds, motion and authority fit on one screen he can read |
| A cheap model builds the J1 podcast source twice: once into Python, once into a declared graph | Role playing (the model plays P1) | Where each form makes it invent things |
| A human plays the QML runtime and evaluates the graph by hand on ten bars | Wizard of Oz | Whether a data rule is expressive enough before any engine exists |
| A storyboard of his click: card, envelope, three weeks of journal moves, a change outside the envelope | Storyboarding | Whether one click per envelope matches "only he promotes" in his mind |

## Step 6. Test (plan, not run)

| Test | With whom | Measure |
| --- | --- | --- |
| Card reading | Him, on a phone | Can he say in one sentence what will change by itself? |
| Builder invention count | Two cheap models, five sources (two YouTube, two MQL5 articles, one book chapter) | Invented numbers, wrong roles, missing parts per form |
| Analyst question set | An analyst agent with a synthetic journal containing moves of each kind | Correct attribution of a result change to market, number or rule |
| Plain-Python path | A stronger model writing an ensembler | Steps needed to reach QMB, journal and the risk socket |

## Step 7. Next iteration

Feeds the wayfinder chart through `qml-questions.md`. The prototypes above are candidates for the map's prototype tickets. No refinement is chosen here.
