# CIS problem solving: the unit system's contradictions and three knots

Written 2026-10-30 by the CIS agent of planning-run step 2 (expansion). Method: `bmad-cis-problem-solving`, run straight through with no human present. I played the facilitator and the problem owner. Where the skill asks me to recommend or select, I list options and the evidence that would separate them instead. Nothing here is chosen or designed.

**Labels.** CHECKED = I read it at the cited place this session. INFERRED = my reasoning. A citation to research 17-19 means the fact is CHECKED by that agent at the line it gives, and I read their file, not the underlying source.

**Short names.** `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md` (line = the line holding that turn's text). `D27`, `D28`, `N28` = the three other operator files. `ST` = `STATE.md`, `SE` = `seeds.md`. `R16`-`R19` = research 16-19. `C1`-`C23` = the open contradictions listed in `R17` §4.

**Scope split with the party agent.** The party-mode and brainstorming agent maps lenses and questions broadly. This file goes deep: root causes, the premise each contradiction rests on, and options with the scenario that would tell them apart.

---

## Step 1. Define and refine the problem

**Problem title.** The unit is being designed on words that mean different things to different speakers, on an identity rule that the 28 Oct shift broke, and without the measurements that could settle the arguments.

**Category.** A definitional and systemic problem in a design-before-build phase. Not a bug, not a performance issue.

**Initial problem, in his words.**
- "the biggest issue at the moment is that we need to understand what a unit is" (T1:376, CHECKED).
- "the definition of system one is lacking… we haven't defined a full unit. The whole idea was a self-configuring" (T1:1999, CHECKED).
- "There's so many contradictions" (T2:216, CHECKED).
- "I think we are like taking 5% of what we are actually meant to be solving" (T2:322, CHECKED).

**Refined problem statement (INFERRED).** QMX needs a unit that one person who is not technical can understand and approve, that agents can build and judge without big mistakes, and that trades on its own when the router, the MIS or his PC is gone. Twenty-three recorded contradictions and three open knots block that. Most of them are not disagreements about what to build. They are three kinds of gap:
1. the same word used for different things (unit, System 1, correlation ledger, router, context, read, calibration, envelope);
2. no settled answer to "what makes two units the same unit", which every downstream rule (tries, journals, sizing records, promotion clicks, family tree) needs;
3. no measurements that would let the data answer (no context labels on backtest trades, no results in R, no live MIS run, no market-correlation computation, no agent proof).

**Problem context (CHECKED unless marked).**
- The word "unit" was coined by Claude on 8 Oct for his idea of a bot with its own self-recalibrating risk system (R17 §1.1).
- The 28 Oct shift: a unit is defined by the market context it needs, not by an instrument ("we're not trading a Euro USD scalper. No, we are trading a mean reverting scalper", T1:1951).
- QMX code has a real workflow engine, a Library and 46 templates, but none can analyse markets or units, QMB has no runner that trades, and the MIS lives only in the never-deployed node (R18 §1.5, §2, §4).
- The old system had more of the parts he remembers than current files show: the Intent Aggregator, bot-level MIS views, `capability_spec`, `symbol_scope` (R19 "Ideas the old system had").

**Success criteria for this step (INFERRED).** Not a design. Success here is that each contradiction is stated as a premise plus a hidden variable, has at least three options, and names the scenario or evidence that would separate them, so the wayfinder chart can turn each into a research ticket, a grilling ticket or fog.

---

## Step 2. Diagnose and bound the problem (Is / Is Not)

| Dimension | IS | IS NOT | Pattern (INFERRED) |
| --- | --- | --- | --- |
| Where the contradictions sit | Identity of a unit (C2, C3, C10, C17, C21), the MIS and router (C1, C5, C9, C19), safety across units (C4, C7, C20), proof (C11, C15), process (C13, C14, C16), words (C8, C23) | Not in the money path's existing guards (KSA, news windows, kill line, SQS are BUILT, never deployed; R18 §5). Not in the workflow engine (BUILT). | The contested area is the new layer between a strategy and the market. The old protective layer is not contested. |
| When they arose | Mostly after 20 Oct, and a second wave after 28 Oct | Not from the 5-13 Oct risk sessions, whose concepts (house money, loss points, fast invalidation) are agreed as concepts (R17 §2.8) | Each reframe (MIS out of the unit on 20 Oct, unit = bot on 24 Oct, System 1 on 28 Oct) reopened rules that were set under the old frame. |
| Who holds each side | Often the operator against his own earlier words (C3, C6, C8, C12, C17, C18, C20), sometimes the operator against an agent or the lead (C4, C9, C10, C11, C19) | Rarely two agents against each other | Many contradictions are his ideas evolving, recorded as rules too early (R17 §5.4 pattern 6, "hardening proposals"). |
| What kind of thing is unclear | Words, identity rules, the place a function lives, and whether a fact is true in data | Not the goal: compounding through placement and sizing, "grab a fish, put it in a freshwater lake" (T2:132) | The goal is stable since the Hummingbird origin (T1:264). The means keep moving. |
| Evidence available | Old-system recoveries, code truth, research 01-16 | No QMB trade with a context label, no live MIS output, no unit journal, no market-correlation number | Every "does it work" contradiction is argued in words because the measuring parts do not exist yet. |

---

## Step 3. Root cause analysis

Methods used: Five Whys (for linear chains), a fishbone (many factors), systems thinking (loops and delays). Each is run on the whole problem here and again per knot below.

### 3.1 Five Whys on "we haven't defined a full unit"

1. Why is the unit not defined? Because each time a definition is written, a later conversation reframes what a unit is for (R17 §1.8: seven meanings in three weeks).
2. Why does each reframe break the definition? Because the definition was anchored on the instrument ("a bot trades a pair") and every rule below it (sibling per instrument, registry per pair, tries per cell, sizing from its own record on that pair) inherited that anchor. The 28 Oct shift moved the anchor to market context, so those rules lost their footing (INFERRED from R17 U23, U24, U41, Q1 revision pending).
3. Why was the anchor never made explicit? Because "what makes two units the same unit" was never asked as its own question. It was answered piecemeal: by instrument (Q1, 27 Oct), by edit type (R10, R17 U27), by logic (lead 28 Oct, U22), by lineage (U28).
4. Why piecemeal? Because each answer came from a different lens (risk, MIS, lineage, QMB) in a different session, and no single record of the unit's identity rule exists. `STATE.md` holds the corrections, not an identity rule (CHECKED `ST:18-30`).
5. Why does that matter more now? Because the identity rule decides what gets counted (tries), what gets a journal, what his click admits, and what the family tree draws. Nothing downstream can be built until it is stable (INFERRED).

**Root cause RC-A (INFERRED).** The identity axis of a unit (what makes two units the same, and what makes one a child of another) is undefined, and the 28 Oct move from instrument-first to context-first invalidated the implicit answer without replacing it.

### 3.2 Five Whys on "there are so many contradictions"

1. Why so many? Because statements with the same word mean different things (C4 "correlation ledger", C23 "system one", C1 "read the MIS", C15 "deterministic").
2. Why do words drift? Because his dictation is a seed stream, speech-to-text slips are common (R17 lists "boats", "MRS", "Febble"), and the lead or agents turn a seed into a term in a file.
3. Why do those terms stick? Because once a term lands in `STATE.md` or a research file, later agents read it as settled (R17 §5.4 patterns 4 and 6).
4. Why is there no check? Because QMX's own docs have a glossary with strict rules (for example bare "timeframe" is retired for `BarSpec`, CHECKED `docs/glossary.md:98`; "envelope" is never written bare, CHECKED `docs/glossary.md:306`), but the unit work has none, and never consults the docs one.
5. Why has the unit work not used the docs glossary? Because the docs stopped at 27 Sep and are seen as stale (R18 §9 row 12), so their vocabulary rules were dropped with their stale content (INFERRED).

**Root cause RC-B (INFERRED).** The unit work has no shared vocabulary, so each contradiction is partly a name collision. Some collisions are with QMX's own ratified docs vocabulary, which the unit work does not read.

### 3.3 Five Whys on "is it luck / does context work / is it correlated"

1. Why can't these be settled? Because nobody has a number: no backtest trade carries a market-state label (R16 §1.3, CHECKED by R16 at `01-ground-truth.md:236`), QMB results are in money not R (R18 §2), no labeler has run on a live feed (R18 §4).
2. Why are those measurements missing? Because QMB was built for strategy evidence under the Book era, when bots never read the MIS and the MIS reached only the Book door and KSA (CHECKED `docs/glossary.md:558`).
3. Why did that design omit labels on trades? Because in the Book era placement was not QMX's job; the Book sized and the MIS informed the Book (R19 §2 July).
4. Why does the new idea need them? Because System 1 is a claim about where a logic works, and a claim about where can only be tested on trades stamped with where.
5. Why has that not been raised as the first build item? It has been raised (R16 §6 item 5, R07 foundations) but the conversation kept moving to definitions before the plumbing (INFERRED).

**Root cause RC-C (INFERRED).** The parts that would let data settle the arguments (labels on trades, R, live MIS output, correlation numbers, agent proof receipts) do not exist, so every contradiction about effect is argued in words, and his and the agents' seeds cannot be told apart by evidence.

### 3.4 A fourth candidate (kept, not ranked)

**RC-D (INFERRED).** Two worlds are mixed in one conversation: research before live (QMB, many variants, history) and live trading (node, seconds, one account). He named it himself: "you're handling live trading as well as strategy development, research, analysis, and curation. Like, I think let's handle one bit at a go" (T1:1574, CHECKED). C5, C6, C9, C13, C20 sit on this seam.

### 3.5 Fishbone: "the unit cannot be built yet"

| Bone | Contributing factors (CHECKED source or INFERRED) |
| --- | --- |
| Words | Unit has 7 dated meanings (R17 §1.8). "System one" means two things (C23). "Correlation ledger" means a lineage projection in docs and a market control to him (R18 §5). "Router" names the LLM router too (R17 M38). |
| Identity | Sibling per instrument (Q1) vs same unit (lead 28 Oct) vs child (R16) vs edit type (R10). Timeframe undefined (C3). |
| Evidence | No context labels on trades; no R; QMB runner places no trades (R18 §2); MIS never run live (R18 §4). |
| Code | QMB, QML, QMN, QMF unchanged since 7 Oct (R18 intro). 6 indicators run (R18 §3). No account guard code (R18 §5). |
| Process | Defining before broadening (R17 §5.4 pattern 2). Summaries instead of sources (pattern 4). Proposals hardened into rules (pattern 6). |
| People | He is not technical and dictates; he asks the lead to "call BS or make a better call" (T2:132). Agents trust earlier agents (T2:436). |
| Data | Dukascopy behind a bot wall (ST:151); Hyperliquid keeps 3.5 days of 1m (ST:141); cTrader FX has no tape (R17 T11). |
| Money | $300 seed; minimum lots pick the tradeable universe first (R16 §7.3). |

### 3.6 Systems thinking: the loops

Loops are INFERRED from the cited seeds.

- **R1, breadth compounding (reinforcing).** More markets where the unit's context holds → more trades → faster own record → better self-calibrated sizing → more growth → room for more units. Source: the Hummingbird origin (T1:264) and System 1 (D28:7).
- **B1, herding (balancing).** More markets in the same context at once → those markets move together (a quiet dollar) → the effective number of bets falls → a correlated loss → guards cut risk. Source: R16 break 3; his "20 markets ranging at once… a real point" (T2:216).
- **R2, lineage learning (reinforcing).** Every unit traced to its source → "where winners come from" counted → the search narrows to good sources → better units (ST:51-52).
- **B2, tries inflation (balancing).** More variants and more expansions → more tries → a higher bar for each → fewer pass. Source: SE:53-55.
- **R3, agent trust (reinforcing when right).** Agents propose with proof → he approves good proposals → more journal data → better agent analysis.
- **B3, confident error (balancing, can flip R3).** An agent is confidently wrong → a bad proposal approved → a loss or a wasted week → his trust drops → he stops reading proposals. Source: his "we can't really have confidence in what agents are going to be producing" (T2:382).
- **Delays.** Direction context needs hours to show on 1m bars (R16 break 1). A specialist record needs hundreds of trades (R17 U41, disputed). An MIS retrain re-labels the past (R16 §1.3). Each delay sits inside a loop above and makes it oscillate.

**Leverage points (INFERRED, not chosen).** The stamp on each trade (feeds R1, B1, R2, R3 at once). The identity rule (decides what B2 counts). The proof receipt for agent claims (decides whether R3 or B3 wins).

### 3.7 Contributing factors and system dynamics, in one paragraph

The unit sits where three loops meet: placement (MIS), self-sizing (risk), and evidence (QMB and journals). Each loop was designed in a different era: placement in April (bots read the MIS through a context view, R19 §2), sizing in July (the Book sizes, bots never size, `docs/glossary.md:46`), evidence in August (STRATS, pair and session are challenge coordinates, R16 §0). October pulled all three into one object called a unit without re-deriving how they connect. INFERRED.

---

## Step 4. Forces and constraints

### 4.1 Force field

| Driving forces | Restraining forces |
| --- | --- |
| His goal is stable and clear: compounding by placement, few units sized well (T2:132) | Vocabulary drift and name collisions (RC-B) |
| A real workflow engine, Library and event triggers already exist (R18 §1) | No measuring plumbing (RC-C) |
| Agents code fast once the plan is right (T2:216) | His fear, from experience, that Claude over-builds (T2:132) |
| Codex usage available for research (T2:132) | The node has never been deployed (R18 §7) |
| Stats already has the shape: four pillars, context as a role, A to I record (R16 §3.1) | The $300 account limits what can be tested live (R16 §7.3) |
| The old system's forgotten parts are now recovered (R19) | Data limits: no tape on cTrader FX, short Hyperliquid history (ST:141) |

Strongest driver (INFERRED): the stable goal. Strongest restrainer: missing measurements, since without them each new session re-argues the same points.

### 4.2 Constraints: real vs assumed

| Constraint | Real or assumed | Evidence |
| --- | --- | --- |
| Agents never touch money | Real (ruling) | ST:20 |
| Only he promotes; the only automatic transition is a risk rule stopping a unit | Real (ruling) | ST:39 |
| Units trade with the router, MIS, PC link or Library down | Real (ruling) | ST:64; standing order 10 |
| Local first | Real (ruling) | ST:72-73 |
| Nothing capped | Real (ruling) | ST:46 |
| A unit is tied to one instrument | Assumed, and now contested | T1:1951 vs Q1 |
| The MIS must detect direction (trend vs mean reversion) per trade | Assumed | R16 §7.1 says the fast contexts are spread, volatility, liquidity, cost, session, news |
| More variants mean more compounding | Assumed, his own reversal | C6 |
| Proof must be deterministic | Assumed; he asked for something "non-deterministic… that can't be cheated" | T2:382 |
| Agent analysis is expensive | Assumed; he is on a subscription | T2:382 "after which costs?" |
| History for agents must be long | Assumed; he wants "a landmark" | T2:382 |
| The correlation control must be invented | Assumed; several eras had one | R19 §4 |
| Backtesting a week of own recorded data makes no sense | His assumption, open | T2:216 |

### 4.3 Key insights (INFERRED)

1. Many contradictions dissolve into a hidden variable once the word is split. "Read the MIS" splits into read-for-placement, read-as-a-rule-input and read-for-a-veto (C1). "Correlation ledger" splits into a lineage record, a market-correlation measurement and a per-tick conflict resolver (C4).
2. His statements are consistent at the level of purpose and inconsistent at the level of mechanism. Purpose: "the MIS is to give direction" (T1:1574), "a unit is independent" (same line). Mechanism varies by day.
3. The old system already faced several of these knots and left traces: the Intent Aggregator for cross-unit conflict, `mis_context_view` for units reading the MIS, `capability_spec` for a unit declaring its conditions (R19 §2, §3).
4. The three knots share one structure: a quantity people want fast and sure (market state, agent truth, cross-unit risk) where speed and certainty trade against each other.

---

## Step 5. Generate options for the three knots

Each knot gets diagnosis, then options from TRIZ, assumption busting, morphological analysis and reverse brainstorming. Options are a mix of small and wild. None is chosen.

### Knot (a): market context is slow to see at scalper speed

**Statement.** R16 (break 1): on 1m bars a volatility doubling shows in about 12 minutes, a 50% rise in about 44, a strong trend in about 8 hours (CHECKED in R16:38, citing R05). He objects to the conclusion, not the number: "Scalpers use very quick or very small time frames, and they need data quickly… you are not going to put an HMM inside a scalper's MIS… But you can put multiple indicators inside a scalper's MIS" (T2:216, CHECKED). On the lead's four fixes he said "habits known in advance… also goes into the funnel. Quick proxies, I don't know, man" and "this 44 minute thing is huge" (T2:322, CHECKED).

**Five Whys.**
1. Why slow? A direction state is a statistical average and needs many bars before it differs from noise.
2. Why many bars? A 1m time bar of mid prices carries little information about direction.
3. Why so little? It is one price path, one instrument, one bar type, and on cTrader FX no volume or trade tape (R17 T11).
4. Why only one path? Because the frame is "detect this instrument's state from this instrument's bars at the unit's timeframe".
5. Why that frame? It mirrors a human chart reader. It is not forced by the data.

**Root cause (INFERRED).** The slowness comes from the measurement frame (one instrument, one bar type, one timeframe, direction first), not from the idea of context.

**TRIZ contradiction.** Improving parameter: speed of the state reading. Worsening parameter: reliability of the reading. Inventive principles that fit:
- *Segmentation (1).* Split context into fast dimensions and slow ones. The lead already proposed this as "two speeds" (T2:84-87). He called the lead's habit of defining early a pattern to stop (T2:322), not the idea itself. Kept as one option, not the answer.
- *Prior action (10).* Know the state before it happens: an almanac of habits by instrument, hour and weekday (gold at the NY open). R17 T17.
- *Another dimension (17).* Read across instruments at once, not along one. A cross-section of 100 markets carries more information per minute than one market's history.
- *Nested doll (7).* The scalper's context is the higher-timeframe state it sits inside. The Stats dictionary has `higher-timeframe-reference` as a context entry (R19 §6). Slow to see, but already known when the scalper trades.
- *Feedback (23).* Use the unit's own recent fills as the live sensor: when its mean-reversion entries stop reverting, the market has told it.
- *The other way round (13).* Do not detect context and then trade. Trade small and let outcomes reveal the context (the market tells you through fills).
- *Preliminary anti-action (9).* Assume the last state holds until a fast change detector fires. Watch for breaks, not for confirmations.
- *Dynamics (15).* Adaptive windows that shorten when tick rate is high.
- *Changing the physical state (35).* Change the bar type: tick-count, volume or range bars. QMX's ratified noun `BarSpec` already allows them (CHECKED `docs/glossary.md:98`).

**Assumption busting.**

| Assumption | Busted version | Option it opens |
| --- | --- | --- |
| Context must be measured live | Much of it is known in advance (sessions, news calendar, roll dates, funding hours, habits) | Calendar and almanac context, zero lag |
| Context is a property of one instrument | It can be a property of a cluster or of the dollar | Cross-sectional state per cluster |
| The unit needs context per trade | It may need it per session | Session or day eligibility list (R16 §1.2) |
| Direction is the main context for scalpers | For scalpers, spread, volatility, liquidity, cost, session and news may matter more | Fast-six first, direction as a placement label (R16 §7.1) |
| Context comes from the MIS | It can come from the unit's own logic | His point: "if it's using the same things as in those in the MIS, it means it is already specific" (T2:216) |
| Context comes from price | It can come from order flow where it exists (futures, crypto) | Per data class sensors (C18) |
| A label is a yes or no | It can be a probability with a confidence | Units weigh, not switch |
| The MIS must be faster than the unit | The unit can be faster than the MIS and use the MIS only for where | Placement vs entry split |
| Context must be computed by QMX | Agents can read the day's charts and data and say what a market has been doing | His daily review seed (T2:322) |

**Morphological box (pick one per column to form an option; not chosen).**

| Dimension measured | Source | Lag class | Where it runs | Who consumes |
| --- | --- | --- | --- | --- |
| direction / persistence | own bars | per tick | in the unit | the unit's entry rule |
| volatility vs usual | cross-section of markets | per bar | feed keeper on the node | placement (which markets) |
| liquidity, tick rate | order book or tape (where it exists) | per session | MIS on PC | sizing |
| cost vs target | calendar and almanac | per day | agent workflow | the operator's shortlist |
| session, events | higher timeframe | known in advance | QML library code anywhere | the journal only (record, no action) |

Example option drawn from the box: "volatility vs usual, from the cross-section, per bar, as QML code inside the unit, consumed by sizing." Another: "direction, from higher timeframe, per day, agent workflow, consumed by placement."

**Generated options (not ranked).**
1. Two speeds: fast dimensions per bar, direction per session or day (lead and R15/R16).
2. Almanac first: precomputed habits per instrument × hour × weekday, refreshed weekly by a workflow.
3. Cross-sectional state: one reading per cluster of correlated markets, updated every bar.
4. Change detectors instead of state classifiers: flag "the state broke" fast, never "the state is X".
5. Unit outcome as sensor: the unit's own last N trade results act as its live context reading.
6. Tick, volume or range bars for the MIS where tick data exists.
7. Order-flow sensors only on venues that have a tape (futures, crypto); FX uses tick activity (R16 §2).
8. Higher-timeframe nesting: a 1m scalper reads 1h state, known before its session starts.
9. Agent daily review of charts and data (his seed, T2:322) produces a "what each market has been doing" list before each session.
10. Probabilistic labels: the MIS publishes a probability and its sample size; the unit decides how much to trust.
11. Trade small to sense: a unit starts each session at minimum size and grows inside the session as its fills confirm the context. Conflicts with nothing live without him only if size growth is automatic; flagged for the risk session.
12. Wild: borrow state from a correlated faster market (BTC perps' order flow as a read on crypto spot; index futures for index CFDs).
13. Wild: treat the context as the unit's job and drop direction from the MIS entirely; the MIS only gives terrain and fast state.
14. Wild: let the copilot and he label markets by hand for a week ("you trade oil", T2:216) and train a labeler on those labels.

**What would separate them (research or prototype).** Measured lag and false-alarm rate per sensor at 1m and 5m, per asset class (R16 §7.10 names these two questions). A replay study: does the label available at entry time (stamped at entry, with a version) lift results versus the label known only afterwards?

### Knot (b): how agents can be confidently wrong, and what proof cannot be cheated

**Statement.** "We need them to be able to prove what they are producing in terms of analysis… I'm proposing a skill which can use tools… we need something that is non-deterministic, something that can be, that can't be cheated, okay, or can't be manipulated… We also need to know in which ways they can be wrong before we define the tools" (T2:382, CHECKED). He rejected the lead's "measure the agents: compare three shortlists after costs" with "How? … Who's comparing?… after which costs?" (T2:382, CHECKED) and the training-cutoff point as sloppy because agents use live data (same line).

**Failure modes first (his order: know how they can be wrong before the tools).** INFERRED unless cited.

| # | How an analysis agent can be confidently wrong | Example in QMX |
| --- | --- | --- |
| F1 | States a number it never computed | "Gold was mean-reverting 70% of today" with no script run |
| F2 | Computes on the wrong data (instrument, timezone, broker, bar type, stale file) | Reads UTC bars as London time; reads demo quotes as live |
| F3 | Picks the window that tells the story | Shows the 3 days that fit, omits the 4 that don't |
| F4 | Searches many contexts and reports the one that worked (fail branch luck) | R16 §1.4: "search long enough and some context always works" |
| F5 | Peeks at months that should be sealed | Reads holdout data while "analysing" |
| F6 | Narrative over chart images | "A clean double bottom" read from a picture with no rule |
| F7 | Vocabulary drift | Its "mean-reverting" differs from the MIS's (R16 §1.4) |
| F8 | Grades its own work | The same model writes and judges |
| F9 | Agrees with the operator or with the last agent | Sycophancy; trusting earlier agents (his complaint T2:436) |
| F10 | Edits the tool or its output | Changes a QMB setting, re-runs until green; he wants QMB to "run and wait. It doesn't have to tinker with the results" (T2:132) |
| F11 | Follows instructions inside a source | A YouTube transcript or article tells the agent what to conclude |
| F12 | Mixes memory with tool output | Recalls a "typical" spread instead of reading the market journal |
| F13 | Confuses correlation with cause | "The unit traded well because of London" when it was a quiet dollar |
| F14 | Overstates certainty from a small sample | Two good weeks called an edge |
| F15 | Silent tool failure read as a result | An empty Dukascopy hour returned without an error (ST:151) analysed as "no movement" |

**Five Whys on "an agent can cheat its proof".**
1. Why can it cheat? Because the same actor makes the claim, chooses the data and writes the proof.
2. Why the same actor? Because a skill with scripts runs inside the agent's own turn and the agent picks the inputs.
3. Why does picking inputs matter? Because most analysis lies are in the selection (F2, F3, F4, F5), not in the arithmetic.
4. Why can't a deterministic script stop selection? Because a script is deterministic given its inputs; it says nothing about whether the inputs were the honest ones.
5. Why does that bear on his "non-deterministic" word? Because the property he wants is that the agent cannot steer the outcome, which is about who controls the inputs and when the claim is scored, not about randomness (INFERRED reading of C15).

**Root cause (INFERRED).** The claim, the choice of evidence and the proof are made by one actor at one time. Proof that cannot be cheated needs a separation of at least one of: actor, inputs, or time.

**TRIZ contradiction.** He wants open-ended, creative analysis (non-deterministic) and a result nobody can manipulate (fixed). Separation principles:
- *Separation in role:* the agent generates claims; tools the agent cannot edit compute every number; a second model or a script checks.
- *Separation in time:* the claim is written down before the outcome is known and scored later against what the market did (a forecast). This is what the July Cartographer was judged on: "calibration of weekly calls" (R19 §8, CHECKED there).
- *Separation in data:* the agent cannot read the data used to score it (sealed months for research; the future for live forecasts).
- *Separation in condition:* free-form analysis is allowed only when it ends in a typed claim with evidence references; prose without a typed claim is commentary, not evidence.

**Assumption busting.**

| Assumption | Busted version |
| --- | --- |
| Proof is something the agent produces | Proof is something the engine records about what the agent did (the engine's ledger, run zones and Library append-only refs already exist: R18 §1.1, §1.4) |
| Deterministic means trustworthy | Deterministic means repeatable; trust needs control of inputs |
| Agents must be measured against a baseline by someone | The market measures them: a dated forecast is scored by later data, no comparer needed (answers "who's comparing?") |
| Cost of an agent run matters | On a subscription the cost is time and attention, not money (his point T2:382) |
| An agent's analysis is either right or wrong | It can carry a calibrated confidence, and be judged on calibration over many calls |
| One agent analyses | Two agents from different "departments" disagree on purpose; April's WF2 used a primary diagnosis agent and a reviewer from another department, because "the biggest risk in wf2 is the false diagnosis" (R19 §1, CHECKED there) |
| History is dangerous for agents (training memory) | History is fine with a landmark: a fixed, named window (his T2:382 "you need to give a pass, in other words, a landmark") |

**Generated options (not ranked).**
1. **Receipts.** Every number in an agent's analysis comes from a tool call whose inputs (data window, instrument, broker, bar type), script version and output hash the engine records. The analysis cites receipt ids. A number with no receipt renders as "unproven".
2. **Typed claims.** The old opinion-node shape: subject, claim, typed evidence, self-assessed confidence 0-1, author, superseded-by (R19 §8). Prose is allowed around it.
3. **Forecast ledger.** Market-analysis agents publish dated calls ("these 5 markets will range in London today") with a confidence; a deterministic script scores them after the session. Over weeks this gives each agent a calibration record. No comparer needed.
4. **Recompute check.** A deterministic hook re-runs each cited receipt and fails the claim if the number differs.
5. **Disagreement on purpose.** A second agent of a different model family reviews; the docs already have `author_family != reviewer_family` machinery for review routing (CHECKED `docs/glossary.md:570`). Disagreements reach him; agreement is a strong signal.
6. **Landmarks.** Each analysis names its window ("since the Monday London open", "last 20 sessions"); the window is a typed field, not prose.
7. **Sealed inputs.** For research analysis, the market-data door's seal and splits (R18 §8) keep agents off the months used for judging.
8. **Tool-only numbers.** The skill's hook refuses an analysis output whose numbers do not match tool outputs in the same run.
9. **Negative controls.** An agent's method is run on shuffled or synthetic data (QMB already has block-bootstrap synthetic series, R18 §2); a method that "finds" structure in noise is flagged. Watch for the rejected "every part must prove itself" machinery (ST:20); this would be one check, not a battery.
10. **Coroner-style graveyard.** A workflow keeps a record of every wrong call and its cause, judged on recurrence rate (the July Coroner, R19 §8).
11. **Source quarantine.** Text from sources (videos, articles) enters as data with a marker, never as instructions; the harness guard already refuses some tools (R18 §1.6).
12. **Wild: the unit is the judge.** An agent's market shortlist is scored only by what units that followed it earned versus units that did not (needs a split, conflicts with "nothing live without him" if units follow it automatically).
13. **Wild: chart and number twins.** Every chart an agent reads has the numbers it was drawn from attached; a claim made from the chart must be restated from the numbers.
14. **Wild: proof by bet.** An agent's proposal states what result would prove it wrong, before the test runs (pre-registration).

**What would separate them.** A short replay over recorded days: give two agents the same day's data, one with receipts and typed claims required and one without; count F1-F15 failures by a script. Which failure modes appear in practice decides which tools matter first (his order).

### Knot (c): does a market-correlation control exist, and where does it live

**Statement.** He: "No, dude, we have a correlation ledger… it's actually already there" (T1:444); "But the correlation ledger exists, man" (T2:322); "if you look at system one, correlation doesn't happen. It rarely happens" (D28:7, via T1:1903); and "Maybe the correlation ledger can take the output also… I feel like it's again wrong to put it there [in the MIS]" (T2:216). All CHECKED. Agents: no market-correlation control in today's docs or code (R17 C4); the docs name is a record linking each order to its decision (R18 §5); real maths only in the draft `rk2` template and an optional `cohort_correlation` slot (R18 §5); the old Intent Aggregator rediscovered (R19 §2).

**Attack the premise (principle-attack-the-premise).** Every past answer assumed "the correlation ledger" names one thing that either exists or does not. Census by era (from R19 §4 and R18 §5, both CHECKED there):

| Era | What existed | What it did | Status today |
| --- | --- | --- | --- |
| April vault | Funding-stage gate in the slot allocator; sizing `correlation_multiplier`; `corr_diversification` in the slot auction | Limited correlated capital at slot time | Text only, code lost in the crash |
| April vault | Intent Aggregator rule 3 | Per tick, across bots: drop intents that push portfolio correlation over a threshold; losers return to the pool unpenalised | Text only |
| July GitBook | Exposure ledger (one of seven doors); cohort correlation in the exam | Exposure accounting; correlation as exam input, not a gate | Name and shape only |
| August STRATS | Dated pair-correlation ledger with method, horizon, regime | A knowledge record, not a control | In Stats, prose |
| Today (docs) | "correlation ledger" = projection over `enacts` edges | Lineage of intent to enactment | BUILT as a name |
| Today (code) | `cohort_correlation` optional evidence slot; `rk2` hourly drift workflow (draft) | Carries evidence; computes legs, matrices, effective bets, per-currency limits | Partial; needs the trading node |

**Reading the skew (INFERRED).** He remembers real controls from April and July. Agents searched today's docs, where the name was reused for something else. Both are right about different things. The premise "it exists or it doesn't" is false. The live question is which of these jobs QMX needs now, and where each one runs.

**Systems thinking.** Correlation sits on loop B1 (herding). It has three time scales: per tick (two units on one symbol, the aggregator's job), per session (20 markets in the same context, the MIS or pod's job), per month (cohort correlation for judging families, the judge's job). INFERRED.

**Is / Is Not.**
- IS a cross-unit concern. IS NOT inside one unit's logic (a unit alone cannot see the others).
- IS about measured co-movement, which is unstable ("stability over time is poor", the Stats dictionary entry `currency-pair-correlation`, R19 §4). IS NOT a fixed table of pair relationships.
- IS needed most on the day System 1 finds many matching markets (R16 break 3). IS NOT absent under System 1 as his 28 Oct line says; it is less visible.

**Options for where it lives (not chosen).**
1. In the MIS, as one more output (he leaned against: "wrong to put it there", T2:216).
2. Downstream of the MIS, taking its output (his seed, T2:216).
3. In the pod or an "ideal BMS" with the news kill switch (his seed, T2:216; R17 R05).
4. In the router, as its own ledger (his 27 Oct seed, ST:68).
5. Per tick, an intent aggregator between units and the broker (the April shape).
6. As a workflow that recomputes hourly and writes limits the units read locally (the `rk2` shape).
7. As agent analysis over collected data (his T2:322 "there are many ways that correlation ledger can be useful").
8. As a judging input only (July: cohort correlation in the exam, not a gate).
9. Wild: units carry a "which bet am I" tag (cluster id) and the guard counts bets, not units.
10. Wild: no correlation number at all; instead a same-bet rule from the shared context ("units entering on the same MIS label within N minutes count as one bet").

**Independence check (standing order 10).** Options 3, 5 and 6 can run on the node with the router down. Options 1, 2 and 4 need care: if the router or MIS is down, the control must not stop trading, yet must not vanish. This is a lead-level question (see `cis-questions.md`).

**What would separate them.** A replay day with 20 matched markets: how many independent bets were there, measured three ways (pairwise correlation, effective number of bets, shared MIS label). If the three disagree, the control's input is the open question, not its location.

---

## Step 5b. Every contradiction worked

Each row: the premise both sides share or the hidden variable, the method used, options (not chosen), and the scenario that separates them. Question ids point into `cis-questions.md`.

| C | Premise or hidden variable (INFERRED) | Method | Options | Separating scenario | Q |
| --- | --- | --- | --- | --- | --- |
| C1 Do units read the MIS? | "Read" hides three uses: as a rule input, as placement, as a veto. Also, an MIS reading is a dictionary primitive bound to the context role, so a unit that uses the same indicator already "reads" it (his T2:216; R16 §7.7) | Is/Is Not, assumption busting | (a) never; (b) placement only; (c) declared dependency with a fallback, the STRATS `requires: mis.x.vN` shape (R19 §2); (d) freely; (e) MIS as library code the unit runs itself; (f) the unit proposes whether to use it (his T1:1951) | Router down for an hour; an MIS version bump re-labels history; data parity (whatever touches history must touch live, R17 J16) forces QMB to replay what the unit read | Q1-Q4 |
| C2 Same logic, new instrument: new unit? | Identity rule undefined (RC-A). Each side protects a different downstream need: Q1 protects separate records and try counts, the lead's "same unit" protects System 1's breadth | Five Whys | (a) sibling unit; (b) same unit, per-instrument settings inside; (c) child record under a parent; (d) membership tag only (old `symbol_scope`); (e) identity by edit type (R10); (f) identity by evidence: a child exists only once earned (Path A) | A unit trades EURUSD for 3 months, then the MIS matches GBPUSD: where does the GBPUSD journal go, what does his click cover, how many tries are counted? | Q5-Q8 |
| C3 Timeframe change: new unit? | "Timeframe" mixes bar type, holding period and style. QMX's docs retired the bare word for `BarSpec` (CHECKED `docs/glossary.md:98`) | Morphological analysis | (a) coordinate like an instrument; (b) logic change (lookbacks in bars change meaning); (c) calibration inside a declared range; (d) a style change (1m to 15m turns a scalper into an intraday unit, his malleable unit, T2:132); (e) timeframes are parts of the logic (higher-timeframe reference) | A rule with RSI(14) on 1m vs 5m; returns of the 1m and 5m versions correlate at 0.8: one bet or two? | Q9-Q10 |
| C4 Does a market-correlation control exist? | One name, six things across eras (knot c) | Attack the premise, census, systems thinking | Ten options in knot (c) | 20 matched markets on a quiet-dollar day | Q11-Q13 |
| C5 Where does the MIS run? | Mixes three jobs: fast state for units, slow placement lists, training. Each has a different home | Force field and constraints | (a) node; (b) split planner on PC, checks on node; (c) one central place; (d) per machine; (e) as QML library code inside each unit; (f) agents on the PC as the slow MIS | PC asleep overnight while crypto trades 24/7 (T2:322); two nodes; a retrain per instrument class | Q14-Q15 |
| C6 More variants, more compounding? | Compounding scales with placement and sizing, not with the count of strategies; the 20 Oct claim was about research breadth, the 28 Oct reversal about live breadth (RC-D) | Five Whys, assumption busting | (a) variants as a research tool only; (b) live breadth through System 1 placement; (c) a new variant only on a logic change; (d) both, counted as tries | $300 with minimum lots: how many units can trade at all? (R16 §7.3) | Q16 |
| C7 Anything live without his click? | His click's scope is undefined: one unit, one unit on one market, or an envelope | TRIZ, separation in condition | (a) click per unit; (b) per unit × market; (c) per envelope by instrument class (R16 §4); (d) click plus automatic paper; (e) only stops are automatic | The USDCHF example (R16:168): never backtested, matches inside the admitted class | Q17-Q18 |
| C8 QML rebuild or upgrade; dictionary unique or GPT's? | "Rebuild" applies to the dictionary content; "upgrade" to the protocol that already matches the industry (R17 C8) | Is/Is Not | (a) upgrade protocol, rebuild dictionary; (b) rebuild both; (c) upgrade both; (d) new library beside QML | What does an agent need to build one reference unit end to end? | Q19 |
| C9 How fast can the MIS work for a scalper? | Knot (a) | TRIZ, assumption busting, morphological | 14 options in knot (a) | Lag and false-alarm per sensor per class | Q20-Q22 |
| C10 Does a new System 2 start with no history? | "New market" means three things: never backtested, already traded by the System 1 unit (Path A), or only recorded by QMX's own collection | Assumption busting | (a) parent prior, shrunk (R16); (b) its own paper trail (Path A, ruling); (c) paper only until a record builds (Path B, proposal); (d) both blended; (e) a short backtest on QMX's own recorded live data | His own case: a System 2 made on a pair the unit rarely trades, then market structure changes (T2:216) | Q23-Q25 |
| C11 Where do trade-count thresholds come from? | A number with no provenance vs a number nobody can stop on. Code first, numbers later (ruling R17 R20) | Five Whys | (a) a research default as a template; (b) an agent workflow proposes ranges from performance (his T2:322); (c) he sets it; (d) QMB computes it per unit from that unit's own variance (the number is an output); (e) sequential tests with no fixed count | A 70%-win skewed scalper vs a 40%-win trend unit need very different counts | Q26-Q27 |
| C12 News trading | The news kill switch guards non-news units; a news unit wants the opposite | Is/Is Not | (a) no news units for now; (b) news only as a context dimension (events); (c) news units with their own KSA scope; (d) a separate news book or pod | NFP at 13:30 with one news unit and nineteen scalpers live | Q28 |
| C13 Live first or backtest first? | The 13 Oct order was set before the unit owned QMB (24 Oct). The real question is what blocks the first paper unit | Systems thinking (critical path) | (a) QMB trading runner first; (b) node first; (c) one reference unit through both | Which is missing on the day a reference unit is ready: a backtest that trades, or a node that runs? (R18 §2, §7) | Q29 |
| C14 Solutions now or broaden first? | Separation in time: 17:25 he wanted testable answers to named breaks; 17:53 he wanted the field widened before designs | TRIZ, separation in time | (a) options with tests in the run, designs only in architecture; (b) practical answers for the named breaks only; (c) both, kept in separate files | This file's format | Q30 |
| C15 Proof tools: deterministic or not? | He wants the agent unable to steer the result, which is about control of inputs and timing, not randomness (knot b) | Five Whys, TRIZ | 14 options in knot (b) | Replay two agents with and without receipts | Q31-Q33 |
| C16 Wayfinder | Wayfinder charts decisions; it is narrow before the field is wide, useful after | Is/Is Not | (a) after expansion (the current plan, ST:131); (b) before, as a map of fog; (c) in loops | Does the chart lose tickets the expansion found? | Q34 |
| C17 Scalpers first or malleable from the start? | What is malleable: the logic, the risk template, the MIS profile, or all three? | Morphological analysis | (a) style is a coordinate; (b) style is a template (risk + MIS profile) attached to a unit; (c) style is identity, so a scalper turned intraday is a new unit; (d) scalper first in research, malleable in the schema | The same breakout logic on 1m and on 1h | Q35-Q36 |
| C18 Do instruments matter? | They matter through data and terrain, not as identity: "we are going to consider variables that each market has" (T2:216) | Is/Is Not | (a) instrument as coordinate only; (b) instrument class keys the MIS; (c) data-availability class keys the MIS (OHLC-only vs order flow, his own split T2:216); (d) instrument habits matter (almanac) | Gold vs EURUSD on cTrader: same data class, different sessions and habits | Q37-Q38 |
| C19 One MIS or one per scalper type? | MIS = sensors × style × timeframe × data class; "one" or "many" depends on which axis the grouping uses | Morphological analysis | (a) one MIS plus declared needs; (b) a template per style; (c) per class; (d) per style × data class; (e) generated per need, "grow its own limbs" (T2:132) | Research results: which sensors work where (his "an HMM with a specific configuration can work best in BT", T2:216) | Q39 |
| C20 The unit alone sizes, or central parts? | Shared budget is a shared resource; someone allocates it. Separation in level: the unit sizes its trade, the centre allocates the budget | Systems thinking, TRIZ separation in level | (a) units size, a pod or BMS allocates shares; (b) units size within a share they negotiate; (c) the centre sizes, units propose; (d) units own all sizing and the guard only stops | Two active units and $300: each "should be able to use all the 300" (T2:216). What happens when a third arrives? | Q40-Q41 |
| C21 Who owns the unit idea? | Concept vs word | Is/Is Not | (a) record both, no design effect; (b) treat as evidence for the hardening pattern | None needed for design | none |
| C22 Pain floor: open or answered? | "Percentage of what" (equity, seed, peak) was never set (R17 C22) | Five Whys | Belongs to the risk session; listed only | A 20% floor on $300 seed vs on $600 peak | Q42 |
| C23 "System one" means two things | Name collision, plus a third resonance with fast-and-slow thinking (INFERRED general knowledge) | Domain modeling | See `glossary-draft.md` | An agent reads an old file saying "system one models" | Q43 |

---

## Step 6. Evaluate (criteria only, no selection)

The skill asks to score options and pick one. I list the criteria any later step should use, drawn from his rulings. Scoring is left to the funnel and to him.

| Criterion | Source |
| --- | --- |
| Works with the router, MIS, PC link and Library down | standing order 10; ST:64 |
| Nothing live without his click; the only automatic transition is a risk stop | ST:39 |
| The simplest mechanism that holds; no prove-itself machinery | ST:20 |
| Local first | ST:72 |
| An agent cannot make a big mistake with it; a human is never stopped | ST:47 |
| Numbers are editable defaults or templates | ST:116 |
| Settles a contradiction with data rather than words | RC-C |
| Does not remove shipped backend work casually | ST:26 |

Skip: decision matrix and recommendation. Reason: the brief forbids choosing.

## Step 7. Plan implementation

Skip. Reason: no design is chosen in this phase. What exists instead is the separating evidence per option (step 5b) and the questions file.

## Step 8. Monitoring and validation

Skip as a plan. Kept as one observation (INFERRED): every option above becomes testable only once trades carry a stamped market state and results are in R. That plumbing is the shared precondition of RC-C, not a design choice.

## Step 9. Lessons from this run

- **What worked.** Splitting a contested word into its uses dissolved several contradictions into hidden variables (C1, C3, C4, C10, C15).
- **What surprised me.** QMX's own docs already ruled on two contested words (bare "timeframe" retired; "envelope" never bare), and the unit work does not use those rulings.
- **Pattern.** His purpose statements are stable; his mechanism statements are seeds. Treating mechanism statements as purpose caused most hardening.
- **To avoid.** Turning "two speeds" or "one MIS" into answers. Both appear above only as options.
