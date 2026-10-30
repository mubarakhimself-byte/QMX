# CIS innovation strategy (brief): what makes QMX different

Written 2026-10-30 by the CIS agent. Method: `bmad-cis-innovation-strategy`, run briefly as the brief asks. QMX is his own platform, not for sale (ST:29, CHECKED), so "market" here means the tools he could use instead, and "customer" means him. Where the skill asks for a recommendation, I list options and what would favour each. Nothing is chosen.

**Labels.** CHECKED = read this session (cited). INFERRED = my reading. **General knowledge** = what I know of a product from before this session, not checked against its current pages; treat as INFERRED.

---

## Step 1. Strategic context

**His question (CHECKED).** "what makes QMX unique compared to things like Copilot and all that? Anyway, it's what I'm trying to justify to myself, okay? Compared to rather MT5" (T2:6). And "multiple experiences that a unit can provide" (T2:6).

**Why now (INFERRED).** The backend is near done and the unit is "the last huge part" (T2:6). Building it costs his weeks and his subscriptions; he wants a reason it beats using MT5 or cTrader with a copilot.

**Breakthrough success, in his words (CHECKED).** "300 can be grown by only one or two units" and the fish put in "a freshwater lake or an ocean instead of putting it in a swamp" (T2:132). "even a bot that is performing poorly, its edge can be amplified by these other things" (T2:132). Origin: "I can't beat these guys in speed, obviously, but I can beat them in compounding" (T1:264).

---

## Step 2. The landscape he could use instead

| Alternative | What it does well | What it lacks for his goal | Source |
| --- | --- | --- | --- |
| **MT5** | Trades almost anything brokers offer; Strategy Tester; MQL5 Wizard modules (signal, trailing, money); a huge article and code base | The money module does not calibrate itself; no placement of one EA across markets by market state; no lineage from source to trade | Wizard modules CHECKED via ST:21 and ST:143 (R04); breadth from his "MT5 is, I think, the one with the biggest breadth" (T1:783); rest general knowledge |
| **cTrader** | Open API on Linux, depth of market, cBots, clean retail execution | No trade tape on FX; one app connection advised; a token refresh logs the other machine out | ST:141, ST:153, SE:113 (CHECKED) |
| **StrategyQuant** | Mass generation, robustness tests, What-If filters, QuantAnalyzer, a "Q" assistant | Never corrects for the number of tries; users say its robustness tests do not predict live; no live placement | ST:142 (R03, CHECKED) |
| **QuantConnect (LEAN)** | Professional backtests, data, an agent door (MCP server), Insights that expire | "Quant Connect is heavy" (T1:828); cloud-first; not built around one person's self-sizing units | ST:143 (R04); his words CHECKED |
| **A plain copilot (Claude, ChatGPT) writing EAs** | Turns any idea into code fast | Confidently wrong analysis; no memory of what failed; no test discipline; no money guard | Knot (b) in `problem-solving.md`; general knowledge |
| **Jesse, freqtrade** | Strategy-owned exits, look-ahead checks | Crypto-focused; no cross-market placement | ST:143 (R04, CHECKED) |

**Five forces, adapted to one user (INFERRED).** Substitutes are strong (MT5 plus a copilot is cheap). Supplier power sits with brokers and data vendors (cTrader rate limits, Dukascopy's bot wall, ST:151). His switching cost is his own build time. The real competitor is not a product; it is "trade one bot on one pair by hand", which most retail algo traders do (his T1:376: "most people who do algorithmic trading are going to trade against one pair specifically").

**Where he is underserved (INFERRED).** Placement across markets by state; sizing that learns from the bot's own record; honest judging when ideas are cheap; remembering why everything exists.

---

## Step 3. QMX's own model, honestly

**Value proposition canvas.**
- *Jobs:* grow a small account by compounding; find where an edge lives; avoid trading luck; understand what the system did; not be needed for every number.
- *Pains:* text; forgetting; over-built machinery; numbers without provenance; agents that sound sure.
- *Gains:* a picture of why a unit traded; one click he understands; units that keep going when parts fail.
- *QMX's pain relievers (proposed, INFERRED):* lineage from source to trade; journals; judging as a skill; units that stand alone.
- *QMX's gain creators (proposed):* MIS placement; self-calibrating sizing; agents as analysts.

**Defensible advantage, if any (INFERRED).** Not code: others have backtesters and brokers. The advantage would be accumulated, private data: his own journals, market journal, almanac, graveyard and source scores, which no product has about his units. "data collection and data stacking, I would say, is very important, because agents are very good with data" (T2:322, CHECKED).

**Model weaknesses (INFERRED).**
- Every advantage above depends on measurements that do not exist yet (RC-C in `problem-solving.md`).
- At $300 the terrain limits breadth before the MIS does (R16 §7.3).
- One person, not technical, must approve all money moves; the system's speed is his attention.
- Build cost in tokens; his complaint that Claude over-builds (T2:132).

---

## Step 4. Disruption vectors and whitespace

**Jobs to be done that no listed tool does (INFERRED).**
1. "Put my one good logic in every market where its water is today, and size it from what it has learned."
2. "Tell me, without me reading, which ideas are luck."
3. "Remember every idea, test and death, and learn where winners come from."
4. "Do the trader's end-of-day review for me, with proof, every session, 24/7."

**Blue ocean ERRC grid (INFERRED, not chosen).**

| Eliminate | Reduce | Raise | Create |
| --- | --- | --- | --- |
| Per-bot hand placement on one pair | Number of live strategies (few units, sized well, T2:132) | Honesty of judging (tries counted, sealed months) | Placement by market state across classes |
| Speed racing (Hummingbird lesson, T1:264) | Text he has to read | Unit independence from every central part | Self-calibrating sizing per unit |
| Proof machinery for its own sake (ST:20) | Agent trust by default | Lineage depth (source to trade) | Agents as analysts with scored calls |

**Technology enablers (INFERRED).** Agents that read data and charts cheaply on a subscription; a workflow engine with event triggers already built (R18 §1.2); a content-addressed Library (R18 §6); cTrader Open API on Linux (SE:113).

---

## Step 5. Innovation opportunities (seeds)

1. **Placement engine:** the MIS and router as the product's heart (System 1).
2. **Judge-first lab:** QMB plus a judging skill as the heart; strategies are cheap, judging is the product (ST:29).
3. **Living journal desk:** agents run the daily trader's review across all units and markets; the almanac and graveyard grow.
4. **Self-sizing socket:** risk and sizing as a pluggable module that learns per unit (T2:132 "male and female connector").
5. **Lineage memory:** "where winners come from" (ST:52) as a source-scoring loop.
6. **Recorded-market pantry:** QMX records its own live data across markets (T2:216), so every week becomes replayable.

---

## Step 6. Three strategic directions (pros and cons; none chosen)

### Direction A: "The placement engine"
QMX's difference is putting units in their best water: System 1 breadth, MIS matching, correlation control.
- **Pros.** Closest to his origin story and his fish-in-a-lake picture. Unique against every listed tool.
- **Cons.** Needs the slowest, least-built parts first (live MIS, correlation, context labels). Breadth is not independence (R16 break 3). $300 limits breadth.
- **Would be favoured if** research shows fast context readings lift results at scalper speed.

### Direction B: "The honest judge"
QMX's difference is knowing which ideas are luck before money moves: QMB with tries, sealed months, context-stamped trades, and judging as a skill.
- **Pros.** Ruled important ("When generating strategies is nearly free, judging them is the product", ST:29). Mostly research-side, so safer.
- **Cons.** StrategyQuant and QuantConnect already cover much of testing; the uniqueness is thinner. Does not by itself grow the account.
- **Would be favoured if** the first reference units fail mostly from overfitting rather than from placement.

### Direction C: "The analyst desk"
QMX's difference is agents that study markets and units every session with proof, building private data no product has.
- **Pros.** Uses the workflow engine and Library that already exist (R18 §1, §6). Grows his defensible data. Matches his 29-30 Oct seeds (A01-A05 in R17).
- **Cons.** Rests on the least trustworthy actor (knot b). Value shows only after weeks of data.
- **Would be favoured if** agents' scored calls prove calibrated in a replay.

Combinations are possible (INFERRED): the three share one precondition, trades stamped with market state in R.

---

## Step 7. Hypotheses that must be checked before any direction

- H1. A unit's context claim can be tested on history with labels stamped at entry (needs QMB change, R16 §6 item 5).
- H2. At $300, more than two or three markets can be traded at safe risk for a given unit (terrain check).
- H3. Agent market readings, scored next session, beat a naive baseline (no comparer needed: the market scores them).
- H4. The old system's forgotten parts (Intent Aggregator, `capability_spec`) cover cross-unit conflict with little new design (R19).

## Steps 8-9. Roadmap, metrics, risks

Skipped as a roadmap: no direction is chosen. Kept as risk notes (INFERRED):
- **What could kill any direction:** building machinery before the measurement plumbing; vocabulary drift; agents trusted without receipts.
- **Leading indicators to watch later:** share of trades with stamped context; share of agent claims with receipts; his say-back accuracy on click cards.
- **Lagging indicator:** account growth per unit, net of costs, in R.
