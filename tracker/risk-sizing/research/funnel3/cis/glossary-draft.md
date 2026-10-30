# Draft glossary of contested words (not CONTEXT.md)

Written 2026-10-30 by the CIS agent with the `domain-modeling` skill. **Draft only.** The skill says to be opinionated and pick one term; this brief forbids picking. So each word lists every competing definition found, with its source, and the scenarios that would force a choice. Nothing here is resolved, and no `CONTEXT.md` was written.

**Labels.** CHECKED = read at the cited place this session. INFERRED = my reading. A citation to research 16-19 is CHECKED by that agent. Short names as in `problem-solving.md`: `T1`, `T2`, `D27`, `D28`, `N28`, `ST`, `SE`, `R16`-`R19`. `DOCS` = `C:\Users\Mubarak\Desktop\QMX\docs\glossary.md` (last changed 27 Sep). `DNA` = `C:\Users\Mubarak\Desktop\Stats\schema\strategy-dna.md`.

**A finding before the list.** QMX's ratified docs already rule on some of these words, and the unit work does not use those rulings. `DOCS:98`: bare "timeframe" is retired vocabulary, replaced by `BarSpec`. `DOCS:306`: "the word `envelope` is never written bare". `DOCS:1027`: "archetype" is the retired alias of strategy family. `DOCS:1236`: "Context Engine" is a retired name. All CHECKED. Whether those rulings still bind the unit work is itself a question (`cis-questions.md` Q44).

**How to read each entry.** D1, D2… are competing definitions in no order. "Separating scenarios" are cases where the definitions give different answers. "Collides with" names other QMX meanings of the same word.

---

## Identity words

### unit

- **D1. A bot plus its own self-recalibrating risk and sizing system, tested as one.** 8 Oct: "what if each boat is to get its own assigned risk management and position sizing system whereby we can have it configure or reconfigure or recalibrate itself?" (R17 §1.1, citing G06:51).
- **D2. A strategy with no separations.** 13 Oct: "A unit is a strategy"; "they shouldn't have separations" (R17 §1.2).
- **D3. Strategy + risk profile + conditions + journal.** Claude's 13 Oct four-part formula, never agreed (R17 U08).
- **D4. Strategy (with its own "when") + sizer + record.** The 20 Oct lean (R17 U10).
- **D5. One complete trading algorithm that replaces the bot.** "a unit literally is now just a trading bot, to be honest. It's just that we combined" (T1:1211, CHECKED). Binding correction 2: entry, exits, self-calibrating risk and sizing, condition needs, session profile, exam baseline, journals (ST:21, CHECKED).
- **D6. A unit defined by the market context it needs (System 1), not by an instrument.** "we're not trading a Euro USD scalper. No, we are trading a mean reverting scalper" (T1:1951, CHECKED).
- **D7. A malleable unit that can become a scalper, intraday or swing unit.** (T2:132, CHECKED).
- **D8. R16's synthesis:** one runnable algorithm with context needs, terrain needs, session profile, exam baseline and journal (R16 §2).
- **D9. A Library kind** with tabs Logic, Results, Family tree, Markets, Versions and no properties yet (R18 §6, citing `kinds/unit.schema.json:22-48`).
- **D10. The old docs' "unit-kind"** is a units-of-measure vocabulary (money, r-multiple, count…), unrelated (CHECKED `DOCS:1093-1095`).

**Separating scenarios.**
- The same logic runs on EURUSD and GBPUSD: one unit (D6) or two (D5 under Q1's sibling rule)?
- A unit's sizing module is swapped for a better one: same unit (D1 says the sizer is part of it) or a new version?
- A scalper unit is turned into an intraday unit (D7): same unit, new version, or new unit?
- A plain-Python ML ensembler trades: is it a unit (it has no declared context needs)?

**Collides with.** D10 (units of measure in the money law). "Unit" as in "R unit" (`r_unit_price` in the sizing ladder, R18 §5).

### logic

- **D1. The frozen part of a unit:** primitives bound to roles, the logic graph, exits, entry semantics and the ranges its numbers may move in; no instrument, broker or timeframe (R16 §2, citing DNA and R10).
- **D2. The answer to "what exactly do you trade on gold?"**, about 60% of the unit, the part tested across instruments (T1:2051, CHECKED).
- **D3. The plain-Python half of a governed bot**, versioned by a source-manifest fingerprint; the other half is the declaration (CHECKED `DOCS:134`).
- **D4. A Library kind `logic`** (R18 §6 kinds list).
- **D5. The STRATS logic graph:** how bound nodes combine (Boolean, temporal, stateful), part E of the A-I record (CHECKED `DNA` core and table).
- **D6. "Logic change" = a change to a pillar or block** (lead, 28 Oct, R17 U31).
- **D7. Everything:** "No, I think the logic is the entire bloody thing" (T1:2051, CHECKED), then partly retracted in the same turn.

**Separating scenarios.** Adding a session filter: logic change (D1 counts timing as logic) or calibration? Changing the exit: D2 may not include exits ("what do you trade" is entry-shaped), D1 does. Rewriting the same rules in plain Python: same logic (D1, D2) or new logic (D3, new fingerprint)?

### calibration

- **D1. The unit tuning its own risk and sizing from its own record** ("self-calibrating", ST:21, CHECKED).
- **D2. A number moving inside its declared range: a journal event, same unit** (R16 §2, citing R10's edit table).
- **D3. Per-instrument calibrated settings inside one unit** (the lead's 28 Oct proposal, ST:110, CHECKED).
- **D4. Cost calibration per broker:** QMB's cost models refuse without it (GAP-0048; R18 §2 `cost.py`).
- **D5. Forecast calibration of an agent:** the July Cartographer was judged on "calibration of weekly calls" (R19 §8).
- **D6. A shared template block named `calibrate`** under `TPL/_shared/` (R18 §1.5, listing only; contents not read, INFERRED to be a setup or probe step).
- **D7. Probability calibration of a model** (does 70% mean 70%), general statistics (INFERRED, general knowledge).

**Separating scenarios.** A unit's ATR multiple drifts from 1.5 to 1.7 within 1.2-2.0: D2 says journal event. Its risk per trade rises after a good month: D1 (self-calibration) or a sizing change his click must see? EURUSD and GBPUSD get different stop distances: D3 (same unit) or a child (glossary "child")?

### idea

- **D1. A level of the strategy funnel: source → idea → build in QML → test in QMB** (SE:57-59, CHECKED).
- **D2. A record layer in front of units for full lineage; "an idea is not a unit"** (ST:149, R10 gap).
- **D3. A Library `hypothesis` item:** statement, source, subject (R18 §6).
- **D4. A STRATS candidate class:** `complete`, `entry_hypothesis`, `fragment`, `descriptive_pattern`, `composite` (CHECKED `DNA` §A).
- **D5. Stage 0 Hypothesis, the mill package before registration** (proposed in docs, CHECKED `DOCS:142`).
- **D6. A seed of his,** in the sense "everything he says is a seed" (ST:115).

**Separating scenarios.** A YouTube video gives an entry with no exit: an idea (D1), an `entry_hypothesis` (D4), or not yet anything? A failed unit is kept for the fail branch: does it return to idea status?

### source

- **D1. Anywhere an idea comes from:** article, video, book, his explanation, a chat transcript (SE:58, CHECKED).
- **D2. A Library `source` kind** (R18 §6).
- **D3. STRATS "one home per source with exact quotes and timestamps"** (ST:149).
- **D4. Something that carries a context claim, an instrument claim, both or neither** (lead, N28:47, CHECKED).
- **D5. A source class for scouts:** one Scout per source class (R19 §7, July).
- **D6. A data source:** Dukascopy, Binance, CCXT (R18 §8).
- **D7. Academic research on market behaviour as a source of strategies** ("this is now just a source for the workflows", T1:2051, CHECKED).

**Separating scenarios.** His copilot chat about oil: source (D1) or not, since it holds no strategy? A market-inefficiency study (D7): it names a context, no logic. Does it seed a unit?

---

## Lineage words

### family

- **D1. Strategy family in the docs: an opaque operator-minted keying token with no authority; every bot declares exactly one** (CHECKED `DOCS:1025-1027`).
- **D2. STRATS strategy-families: a named group of candidate ids** (CHECKED `Stats/lineage/strategy-families/README.md`).
- **D3. The family tree in the UI:** parent, pairs, history; preview and detailed view (ST:53; T1:513 "it's like a family tree", CHECKED).
- **D4. "The family and its heritage" = what System 1 is:** "a scalper, but it's a mean reverting" (T2:132, CHECKED).
- **D5. The unit of try counting:** "count tries per family" (ST:147 for R07).
- **D6. Feature families** in the old QML types (`disallowed_feature_families`, R19 §3) and structure families with their own `BarSpec` (`DOCS:218`), unrelated.

**Separating scenarios.** A composite made from two parents: in which family (D1 allows exactly one)? A mean-reverting scalper and a mean-reverting intraday unit: one family (D4) or two? Do tries reset when a new family id is minted (D5)?

### variant

- **D1. Each cell of instrument × timeframe × window becomes a variant with its own proof** (SE:44, CHECKED).
- **D2. A child with a semantic delta on its change history** (STRATS `lineage/variants/README.md`, CHECKED).
- **D3. A Library link `variant-of`** (R18 §6 link list).
- **D4. "System two is just a variant of system one"** (T1:1999, CHECKED).
- **D5. A new System 1 variant from a logic change, possibly combined from several System 2s** (T1:2051, CHECKED).
- **D6. Old WF1 vanilla and spiced:** "vanilla is basically the code as it comes from the source… spiced is like the logic plus the ctrader article logic" (R19 §1).
- **D7. A Book/BMS variant as a complete candidate in QMB** (R18 §2 `analysis/variants.py`).
- **D8. A new bot version from a tuned parameter assignment** (CHECKED `DOCS:134`, "promoting a tuned assignment mints a NEW Bot version").

**Separating scenarios.** Same logic, new instrument: variant under D1, not under D5. Parameter retune: variant under D8, calibration under the calibration D2.

### sibling

- **D1. Same logic on a new instrument, timeframe or broker, in one family tree** (Q1, his yes on 27 Oct: ST:37, CHECKED; T1:1574).
- **D2. A paper-sibling proposal card when the router offers a market outside the envelope** (R13 via ST:152; R16 §4 step 4).
- **D3. A missing Library edge `sibling-of`** (R16 §3.2, citing R14).
- **D4. Old domain expansion "ecological mutation": new symbol or timeframe** (R19 §3).

**Separating scenario.** Under System 1, the same unit trades many markets. Is a sibling still a separate unit, or only a record? D1 predates 28 Oct and is marked "revision pending" (R17 U23).

### child

- **D1. The parent + one instrument (and broker, account type), with its own terrain check, calibrated numbers, journal and proof, starting from the parent's record** (R16 §2).
- **D2. A STRATS child/variant pointer** (Stats `lineage/variants`).
- **D3. A System 2 child born at minimum size inside an admitted envelope** (R16 §4).
- **D4. Calendar gates (gold fix times) stay a System 2 child** (R15 via ST:154).

**Separating scenario.** His Path A ruling: a System 2 is earned from a record the System 1 unit built on that market (ST:120). D3's child is born before any record. Both cannot hold for the same market.

### parent

- **D1. The System 1 record that every System 2 has by default, even when it does not win broadly** (T1:2051, CHECKED).
- **D2. The pooled average of its children; a parent that fails broadly stays a record with a status** (R15 via ST:154).
- **D3. Logic + context claim + tested universe + pooled, shrunk record** (R16 §2).
- **D4. STRATS baseline or source parent; composites have several** (CHECKED `DNA` §I).
- **D5. At-birth parent references in a record header** (CHECKED `DOCS:524-526`).

**Separating scenario.** A gold-only strategy from a source: is its parent an empty record (D1), a record pooled from one child (D2), or nothing until a broad test runs (D3)?

---

## Market words

### context

- **D1. Pillar 2 of every strategy: regime, session, higher timeframe, vetoes** (Stats, R16 §3.1, citing `strategy-dna.md:128-133`).
- **D2. A role, not a class:** filter, confirmation and confluence are bindings (R19 §6; R16 §3.1).
- **D3. What the MIS senses:** "doesn't this mean that market context is simply what the MIS is doing?" (T1:1951, CHECKED); "context is what the MIS is meant to be sensing" (T2:132, CHECKED).
- **D4. The market's state at one moment in a small shared vocabulary with a versioned sensor, changing minute to minute; not terrain, not logic** (R16 §2).
- **D5. The condition a source says a strategy works in** ("the source tells us which market context the strategy is meant to work in", T1:1951, CHECKED).
- **D6. Shared dimensions (direction, volatility, liquidity, time, events) with sensors per asset class** (lead proposal, not agreed, N28:29-41, CHECKED).
- **D7. "Context collection"** as the first level of a research funnel, meaning gathering material (T1:5 pasted prompt, CHECKED).
- **D8. The LLM context window** ("Context Compiler", CHECKED `DOCS:1236`; "your context window", T2:436).

**Separating scenarios.** "Gold at the NY open": context (D1 session) or terrain (fixed trading hours) or a habit (almanac)? A news window: context (D6 events) or a guard's domain (KSA)? "After a loss": R16 says it is not a market context because it depends on the unit's own trades.

### market state

- **D1. The MIS's job "by definition, market state"** (T2:216, CHECKED).
- **D2. Regime:** "a categorical classification… intended to select which strategy families are appropriate", heuristic, no standard state count (R19 §6, Stats dictionary).
- **D3. Tiers T0 facts, T1 seasonal ratios, T2 change flag, T3 regime** (R16 §3.1, citing R05).
- **D4. The signal snapshot:** the per-instant fold of all labeler outputs dispatched to the Book door and KSA (CHECKED `DOCS:558`).
- **D5. Per-pair weather on the July Week-Map** (R19 §8).
- **D6. Old live sentinel states:** Chaos + Ising regime + news, with the news vocabulary `SAFE / PRE_NEWS / KILL_ZONE / POST_NEWS` (R19 §2).

**Separating scenario.** A labeler version bump: does the state of last Tuesday change (D2, D3 if recomputed) or stay as stamped (D4 is per instant)?

### terrain

- **D1. The slow facts of one instrument at one broker and account type:** tick and lot size, minimum lot, hours, spread and commission by hour, swap or funding, expiry and roll, venue type, data available (R16 §2).
- **D2. Instrument = terrain: costs, contract size, hours, liquidity** (N28:24-27, CHECKED).
- **D3. Knowledge (slow, durable) as opposed to intelligence (dated, changing)** (Stats distinction via R16 §3.1).
- **D4. His use: the case where "a market can be perfect for a unit, but its spread is so high"; "does SQS simply fire?"** (T2:216, CHECKED). Here terrain includes live spread, which D1 puts in measured costs.

**Separating scenario.** Spread at 03:00 London on gold: terrain (D1, by hour), context (volatility and liquidity), or an SQS block (D4)?

### instrument class

- **D1. The docs' `instrument_class` record:** a kind under CT-06's addable-kinds law (CHECKED `DOCS:1027`, by reference).
- **D2. Asset class:** FX, futures, crypto perps, gold, indices (N28:36-40; T1:1999 "categorizing by instrument type", CHECKED).
- **D3. Data-availability class:** "the MIS for a market that has all the data is different, but the one for that has open, high, low, close only is also different" (T2:216, CHECKED).
- **D4. Venue type:** OTC quotes vs an exchange tape (R16 §2 terrain list).
- **D5. The unit of admission:** "admit an envelope by instrument class" (R16 §4).

**Separating scenarios.** Gold CFD on cTrader vs gold futures: same asset class (D2), different data class (D3) and venue (D4). Index CFDs have no order flow on cTrader (T2:178 via R17 T11): an "index" class or an "OHLC-only" class?

### timeframe

- **D1. Retired vocabulary in QMX docs, replaced by `BarSpec`** (time interval, tick count, volume, notional, price brick, range, session) (CHECKED `DOCS:98`).
- **D2. A coordinate of a unit like instrument and broker** (R16 §2; lead lean DEC:79 via R17 C3).
- **D3. A trading-style marker:** scalpers trade 1m, 5m, seconds; intraday 15m, 30m vs 1h, 4h (T2:216, CHECKED).
- **D4. A variant axis: same logic on 1m and 5m = two registry entries** (SE:40, CHECKED).
- **D5. A change that "becomes a brand new strategy"** (13 Oct, R17 C3).
- **D6. Part of the logic** when a strategy reads a higher timeframe (Stats `higher-timeframe-reference`, R19 §6).
- **D7. The MIS reading frame:** "see which markets are mean reverting in a given time frame" (D28:7 via T1:1903, CHECKED).

**Separating scenario.** A 1m scalper moved to 3-second bars or to 100-tick bars: D1 handles it; D2-D5 assume time bars.

### trading style

- **D1. Scalper, intraday, swing** (T1:376; T2:132, CHECKED).
- **D2. The first axis of the MIS:** "we need a trading style, firstly", then timeframe, then the data a market offers (T2:216, CHECKED; ST:119).
- **D3. Scalper types (finite, about 7)** (T2:132, CHECKED); research 02 keeps 5, splits order flow, adds two (ST:141).
- **D4. A human trader's routine:** "A human trader who's a scalper will not wake up at the same time to look at charts as a person who day trades" (T2:132, CHECKED).
- **D5. Archetype**, the retired alias of strategy family (CHECKED `DOCS:1027`).
- **D6. Old compile-time tags:** `vanilla`, `spiced`, `session_specialist`, `regime_specialist` (R19 §3).
- **D7. A defaults template, never a cage:** "if we do come up with our own ML model that isn't a scalper type… Like, don't drop anything" (T1:1574, CHECKED).

**Separating scenario.** An ORB unit that holds 20 minutes: scalper or intraday? Which risk template and which MIS profile does it get?

---

## System words

### System 1

- **D1. A unit defined by market context, not tethered to an instrument** (D28:7; T1:1951, CHECKED).
- **D2. The live mode he prefers: the MIS scans a universe, the unit picks the best of the matches by its own record** (ST:107, CHECKED).
- **D3. Pooled evidence across markets** (R16 §7.4: "System 1 vs System 2 is… pooled vs per-cell").
- **D4. Qualitative tracking:** "system one is logging and tracking quality… qualitative analysis" (T1:1903, CHECKED).
- **D5. Old September meaning: small trainable "system one" models for the MIS** (R17 C23, citing G09:214).
- **D6. Resonance (INFERRED, general knowledge):** in Kahneman's usage System 1 is fast and intuitive. That reading suggests the fast lane, which is the opposite of the slow MIS placement role.

**Separating scenario.** A gold-only source: does it "fit into system one"? He asked this himself (T1:1999, CHECKED).

### System 2

- **D1. Context plus a specific instrument: "a Euro USD scalper"** (T1:1951, CHECKED).
- **D2. Round 1's sibling unit per instrument; right before live, for building and varying logic per market** (ST:108, CHECKED).
- **D3. Quantitative tracking** (T1:1903, CHECKED).
- **D4. A specified version of System 1** (T1:1999, CHECKED).
- **D5. "The end goal of QMX"; the fish in the lake** (T2:132, CHECKED).
- **D6. Earned from a record the System 1 unit built on that market (Path A ruling)** (ST:120, CHECKED).
- **D7. Per-cell evidence, joined to the parent by shrinkage** (R16 §7.4).
- **D8. The lead's proposal "System 2 in research, System 1 live"** (ST:110, CHECKED), superseded by "System 1 grows into System 2" (R17 U21).
- **D9. Resonance (INFERRED):** Kahneman's System 2 is slow and deliberate.

**Separating scenario.** D2 puts System 2 before live; D5 and D6 put it after a live record. Same word, opposite ends of the lifecycle.

### router

- **D1. The MIS as a router or load balancer: bots = servers, markets = traffic** (SE:13-17, CHECKED; T1:376).
- **D2. Only routes, never switches; gives "direction and depth of information"** (ST:62-63, CHECKED; T1:1574).
- **D3. A split router: a PC planner writing a signed plan with an expiry, a cheap node check** (R09 via ST:159).
- **D4. Offers that expire, pulled by units** (R14 via ST:153), called too complex on 28 Oct (ST:105).
- **D5. A ranking function over a table of matches** (R16 §7.12).
- **D6. `qmx-router`, the LLM provider router** (ST:182; R18 §1.6, CHECKED there).
- **D7. The old `src/router/` package:** the whole bot-management core (engine, commander, sentinel, governor with Kelly and house money, registry, auction) (R19 §2).
- **D8. A thing that switches units on and off** (R07, reversed on 27 Oct: "This wording is very sloppy", T1:1574, CHECKED).

**Separating scenarios.** Is the router the MIS (D1) or a separate part that reads the MIS (D3, D5)? With D7's meaning, an old file saying "the router sizes" is not wrong for its era.

### MIS

- **D1. Market Intelligence System:** "it's in the name, market intelligence system" (T1:264, CHECKED).
- **D2. April: "the market intelligence basically deals with news trading stoppage uh session monitoring and routing"** (R19 §2, citing GPTR:115).
- **D3. A sentinel that "delegates bots to market"** (R19 §2).
- **D4. Today's docs: the node's labeler layer folded into a snapshot for the Book door and KSA, never bots** (CHECKED `DOCS:558`).
- **D5. A router or load balancer** (see router D1).
- **D6. A scanner and matchmaker** (N28:7, CHECKED).
- **D7. "The output is in a pool. The pool is the output"; units read from "an MIS cluster"** (T2:132, CHECKED).
- **D8. Templates per market type: "grow its own limbs"** (T2:132, CHECKED).
- **D9. A centrally used constant with no versions side by side** (August, R19 §2, citing GEN:1431).
- **D10. A centralised part with the news kill switch, in an "ideal BMS"** (T2:216, CHECKED).

**Separating scenario.** Does the news kill switch belong to the MIS (D2, D10) or sit beside it as a guard (ST:65, guards independent of the router)?

### envelope

- **D1. The admission envelope: his click admits a unit together with markets, sessions and brokers** (R13 via ST:152).
- **D2. An envelope admitted by instrument class** (R16 §4).
- **D3. Agent-driven, built on the workflow system, a default now** (ST:104, CHECKED).
- **D4. The docs' mailbox record on the Agent Bus; "the word envelope is never written bare"** (CHECKED `DOCS:304-306`).
- **D5. The docs' wire envelope (the AD-5 frame)** (same entry).

**Separating scenario.** An agent reads "envelope" in a QMX file. Under D4 it is a message; under D1 it is what his click allows. The docs rule exists to stop exactly this.

### journal

- **D1. A trading journal per unit, creation through stress, paper and live** (ST:25, CHECKED).
- **D2. The unit's DevOps layer: monitoring, logging, observability; agents can write** (ST:55-56, CHECKED; "it's just DevOps", T1:1574).
- **D3. A router journal for market facts** (ST:58, CHECKED), also named a market journal per broker × account type × instrument × minute (R12 via ST:151).
- **D4. The docs' Journal: append-only evidence streams with seven event types; not an application log** (CHECKED `DOCS:478`).
- **D5. A human trader's end-of-day journal, reviewed by agents** (T2:322, CHECKED).
- **D6. Today's code: `trade` items from broker fills, `workflow-run` items, chat sessions, the engine ledger; no `journal` kind** (R18 §6).

**Separating scenarios.** Signals seen but not taken (ST:57): a D1 row, a D4 decision event, or log noise? Spread at entry: D1 copies it, D3 holds it once and the unit links to it.

---

## Which words disagree most (INFERRED count)

| Word | Competing definitions found | Kinds of disagreement |
| --- | --- | --- |
| unit | 10 | identity, structure, scope, a units-of-measure collision |
| MIS | 10 | role (router, scanner, guard, labeler), where it runs, who reads it |
| variant | 8 | what change makes one, when it exists |
| context | 8 | strategy pillar, market state, source claim, research step, LLM window |
| router | 8 | MIS itself, separate ranker, LLM router, old bot-management core |
| System 2 | 9 | before live or after live; research or end goal |
| calibration | 7 | risk, parameters, costs, agents, models |

The widest by kind (not by count) are **context**, **System 1/System 2** (one pair of words whose two halves sit at opposite ends of the lifecycle) and **unit**. **Router** and **MIS** overlap with each other, which is a disagreement of its own.

## Candidate terms seen in sources, not proposed

Listed only so the glossary step does not lose them: `BarSpec` (DOCS:98), `capability_spec` and `symbol_scope` (R19 §3), `context_needs` and `terrain_needs` (R16 §6), `challenge coordinate` (R16 §0), `knowledge vs intelligence` (R16 §3.1), `opinion node` (R19 §8), `Intent Aggregator` (R19 §2), `exposure ledger` (R19 §4).
