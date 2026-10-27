# 13: Funnel round 2: ideas mapped across each other

Written 2026-10-27. Ideas and options only. Nothing here is a decision, nothing is folded into architecture, and no final design is picked.

## How to read this

- **Inputs read in full:** `operator/2026-10-27-review-dictation.md`, `STATE.md`, `research/10`, `11`, `12`. Skimmed: `07-funnel.md` (§0, §3, §6-9), `09-router-architecture.md` (§0, §1.4, §2.4-3.3), `08` (§0, §2.1), `seeds.md`, `HANDOFF-RISK-SIZING.md`, `07a` §3.3, and the old BMS rows in `workroom\risk-lab-2026-10-05\grounding\02-book-and-prior-sims.md` and `05-findings-2026-10-13.md`.
- **Labels.** **CHECKED (file)** = I read it there. **INFERRED** = my reasoning. Every idea in §5 is a proposal, so INFERRED unless a fact inside it is tagged. Party-mode speech is opinion unless tagged.
- **Method (the BMad stack, as he asked).** `bmad-party-mode` in session mode (one mind, every voice inline) over 12 topics, then `bmad-brainstorming` in its headless "ideate for me" form with seven techniques: Morphological Analysis, SCAMPER, Reverse Brainstorming / Anti-Solution, Analogical Thinking (load balancers, observability stacks, genetics, libraries and archives), TRIZ Contradiction, Chaos Engineering and Assumption Reversal.
- **Deviations from the skills, on purpose.** The brief allows one output file. So there is no separate memlog, no HTML keepsake, no subagents. This file is the log. Party mode ran non-interactive (no user in the room), so the operator's chair speaks only in his own dictated words.
- **Out of scope:** risk and sizing maths (own session, `HANDOFF-RISK-SIZING.md`). The account guard and pod shape, and the router's independence, are in scope.

## 0. The short version

1. **The dictation holds 93 distinct points** (§1): 49 rulings, 22 wishes, 10 questions, 4 unfinished thoughts and 8 holds or process directions, counted by first mark. Two more points (D15, D29) are partly unfinished. The funnel produced 179 ideas (§5).
2. **The strongest combination is the "admission envelope" (I180).** His click admits a unit together with a set of markets, sessions and brokers. Inside that envelope the router only directs, and the unit trades with or without it. Anything outside the envelope becomes a paper sibling proposal. This one idea reconciles "router directs, never switches" (D53), "only he promotes" (D74) and "new market = sibling unit" (D71). INFERRED.
3. **Independence comes from three ideas together:** the feed pool (units, guards and the router all read one local bus, I78), the router as an advisory publisher with expiring offers (I55-I57), and guards that read the pool, not the router (I83). With these, the router going down is a yellow light, not a stop. INFERRED.
4. **One trace id from source to trade** (I3), plus the market journal (I40) and the router decision journal (I41), lets any trade be explained end to end. It also answers "where do winners come from" (D7) with a plain group-by. INFERRED.
5. **His unfinished thought (D27, D35) has three candidate articulations:** a market almanac of instrument conditions over time (I45), a cell map of where alpha lives and how it moves (I47), and cost-aware placement by broker and hour (I46). Open question Q6.
6. **Conflicts the next study must settle** (§4.3): units reading MIS output (D66) against the 20 Oct seed; genetic transplant against "no ablation of every part"; copilot remaking pods against an unremovable guard floor; "local first" against 12 GB of free disk.
7. **Dictation points no idea serves:** D2 and D21 (nothing to build), D50, D51 and D75 (risk and sizing, out of scope here), D69 and D70 (he asked to hold), D91 (more agents; this brief forbids subagents). D35 and D79 are served only by guesses at what he meant, so they go to Q6.

---

## 1. Point ledger (dictation, 2026-10-27)

Type key: **R** ruling, **W** wish, **Q** question, **U** unfinished thought, **H** hold or process direction. Every quote is CHECKED (`operator/2026-10-27-review-dictation.md`, line 9 for the main dictation, line 15 for the follow-up). Speech-to-text slips are kept.

### 1.1 Sources, library and unit life

| # | Point | His words | Type |
|---|---|---|---|
| D1 | We looked at the wrong folder for the dictionary. Map the Hermes sessions, find the gold mine, compare the old way of building QML with today's. | "we've been looking at the wrong one" | R |
| D2 | The unit library page is fine. | "as long as it works" | R |
| D3 | A unit's life needs improving and must be very precisely defined. | "we need to be very, very defined" | W |
| D4 | Family tree in the UI: design both a preview (small summary) and a detailed view. | "we have a preview and a detailed view. So design for both" | W |
| D5 | The detailed view holds journals, lineage, pairs, history and backtest results. Everything is saved: the data layer. | "everything about it needs to be saved" | W |
| D6 | Every unit is traceable to its origin: chat session, YouTube video, blog post, copilot chat. | "We're not trying to vibe trade or vibe code here. It needs to be known." | R |
| D7 | Analyst lens: knowing where high performers come from lets the search narrow over time. | "we are starting with a very big blast radius... shall like reduce it" | W |

### 1.2 QMB, data and freedom

| # | Point | His words | Type |
|---|---|---|---|
| D8 | The old system's backtesting proposed a lot. Why were those ideas refused? QMB already used LEAN CLI logic. | "I don't know why we refused them" | Q |
| D9 | Many instruments now, so cater for all of them by default. | "we need to cater for them by default" | R |
| D10 | Data came from Dukascopy via dukascopy-node, which is not the only source. Quality and cleanliness need checking. | "in terms of data quality, data cleanliness, we might need to know" | Q |
| D11 | No lookback limit. A test of 1990 must be allowed. Post-COVID is sensible, never a cap. | "I don't want to limit QMX in any way, shape, or form" | R |
| D12 | This holds for the whole system, above all for the part being designed here. | "We need to not limit a thing" | R |
| D13 | A unit can be rewritten with nothing QMX has: pure Python, in the Lab, in a mini app or a workflow. | "We shouldn't be limited in any way, shape, or form" | R |
| D14 | QML, the unit and the schemas exist as a standard because agents do most of the work. | "We are actually just calibrating the system for agents" | R |
| D15 | Normal Python is never off: an ML ensembler instead of a unit, mini apps. This may mean redesigning several systems. | "it doesn't mean that normal Python is off entirely" | R + U |

### 1.3 Portfolio, account guard and pod

| # | Point | His words | Type |
|---|---|---|---|
| D16 | Two pairs of things are being mixed: the overall portfolio vs its configuration, and live trading vs research and curation. Take one at a time. | "let's handle one bit at a go" | R |
| D17 | The 5% budget made sense in the old system. Is the pod, or risk and sizing, centralised or not? Nothing was set in stone. | "It's everything that is a suggestion" | U |
| D18 | Not the whole Book, only the BMS. The Book is overkill. | "Not the book system entirely. The BMS alone" | W |
| D19 | Self-configuring has never been shown concretely. He needs it most. | "I haven't seen a singular thing in which or how it should be done" | Q |
| D20 | The account guard sits outside the unit. The pod is effectively the BMS, and the BMS already did the guard's jobs. Standardise them, maybe combine them. He asks Claude. | "maybe let's combine it with the pod. What do you think?" | Q |
| D21 | Keep the word "unit". | "keep the word unit" | R |

### 1.4 Journals

| # | Point | His words | Type |
|---|---|---|---|
| D22 | A journal is anything that records data, for the unit and for agents analysing over time. | "it's anything that can record data" | R |
| D23 | Standards keep weaker models from big mistakes, so hooks matter. | "this is why hooks are very important in this system" | R |
| D24 | Record trades detected but not taken, and missed trades. Lots of data. Learn from human journals and from bot observability. | "threads that weren't taken but were detected or that were missed" | W |
| D25 | The journal is the unit's DevOps layer: observability and logging. | "this is literally the DevOps layer for that unit" | R |
| D26 | Spread and fees are centralised. The router gives the journal for them: a separate router journal. | "we need to separate the journal for the router" | W |
| D27 | Unfinished: see which instruments perform, or had suitable conditions, over time, and use that with agents. | "There is something I'm trying to put my finger on" | U |
| D28 | Look through both the dev lens and the trading lens. | "both the dev layer and the dev lens, as well as the trading lens" | W |
| D29 | A copilot chat: gold fits my scalpers, but spread and fees are high. Is it the broker? The time of day? | "is it the broker? Is it the time?" | Q + U |
| D30 | Some things belong somewhere else. Watch data volume. Duplication is huge. | "geoplication is huge" | R |
| D31 | Slippage, spread, fees and sessions at unit level would only duplicate what the router already does. | "It's going to just be duplicating" | R |
| D32 | Journals improve strategies over time. The old WF3 circles this use case. | "WF3 from our old system... does circle around this use case" | W |
| D33 | Performance over time of a strategy or a family tree reveals specific alpha. | "we can realize specific, should I say alpha" | W |
| D34 | Links to last week's idea of one idea branching into many. Here we comb and filter: which family, which pairs. Portfolio optimisation can come from journals. | "we can redesign better methods based off just journals" | W |
| D35 | Unfinished. | "There is something I want to articulate, but I can't find the proper words" | U |

### 1.5 QMB and judging

| # | Point | His words | Type |
|---|---|---|---|
| D36 | QMB is left to Claude. Base: LEAN CLI. Also consider Jesse ("JSE" in the transcript; INFERRED to mean Jesse). | "Quant Connect, Lean CLI... also consider JSE" | R |
| D37 | Agents don't backtest with code; they fiddle over and over. Build what agents use, at a professional quant level. | "building something that agents can use, but at the same time at a professional quantitative trader level" | R |
| D38 | Borrow and drop from old and new as Claude sees fit. He agrees with the defaults. | "things to borrow, things not to borrow, the old and the new, bro, figure it out" | R |
| D39 | "Judging is the product" is right. The five rules need more thought. | "this is something we shall have to think through a little bit more" | R + W |
| D40 | The sky is the limit. Workflows and a copilot may remake most of what is designed, pods included. | "a copilot might remake most of what you've done. Not might, can" | R |
| D41 | Judging can become a skill for a given part of a workflow. | "we can turn it into a skill" | W |
| D42 | Look at how professional quants judge. Don't be too strict. | "we don't want to be too strict" | W |
| D43 | Judging must account for the old "radioactive" sizing. | "while judging, we should put that in mind" | R |
| D44 | Judge and improve from history AND paper; both lower overfitting. When to paper-trade, and in what order? | "there is a sequence there" | R + Q |
| D45 | Stop designing for humans. Design for agents. | "Stop designing for humans, start looking at agents" | R |
| D46 | More papers are coming. QMA v2 already has a lot. Go deep on the quantitative lens. | "in the quantitative lens, I think we need to look into this deeply" | W |
| D47 | The judging skill holds hooks and deterministic scripts that call QMB. Agents judge from results, not by eye. | "a skill literally has hooks and deterministic scripts" | R |
| D48 | Agents may propose, and proposals render in the UI. | "the proposal should be rendered in the UI" | R |
| D49 | Agents can write in the journal too, not only trading results. | "leave room for also agents to be able to write" | R |

### 1.6 Risk and sizing (handed to its own session)

| # | Point | His words | Type |
|---|---|---|---|
| D50 | Risk and sizing combines the best of the two systems. It needs its own session and a mathematical explanation. | "I'll need a prompt or some sort of handoff" | R / H |
| D51 | Fast stops and slow checks track the quality of risk management. Explain loss points, CUSUM and decay. | "Decay is an interesting one" | Q / H |

### 1.7 Router

| # | Point | His words | Type |
|---|---|---|---|
| D52 | The router is what he wanted, but "switches units on and off" is wrong. | "This wording is very sloppy" | R |
| D53 | Routing means directing. It never switches anything on or off. It gives direction toward the best performance. | "Neither does it switch on, nor does it switch off" | R |
| D54 | A unit is independent. With the router off, it still trades if the pair, the broker and the rest are available. | "what happens when the router is off? Then what?" | R |
| D55 | Load balancer: market = traffic. About seven algorithms (round robin, least connections and more) plus hybrids. It pushes traffic by its algorithm and never tells a unit to trade or not. | "its whole point is to just push the traffic to best of that algorithm" | R |
| D56 | The router and the units will likely sit on different servers. Tracking 500 units with on/off is fragile. | "there is a very high chance that these two are on different servers" | R |
| D57 | The router needs a correlation ledger. He asks for Claude's view. | "we need a correlation ledger here" | W + Q |
| D58 | The router gives depth of information ("this fits your conditions", "this market is like this") to improve performance. It is what makes QMX unique. | "it should provide depth of information" | R |
| D59 | Remove dependencies on the router and other big parts: points of breaking. A slow or reset network must not switch off the SQS, the news kill switch or session analysis. | "make sure that they are not dependent on the router" | R |
| D60 | The guards that prevent small black swans (SQS, news kill switch) work independently. Feeding news and spread is independent. | "those are all very, very independent if you think about it" | R |
| D61 | Spread for many instruments: how is it handled? | "How are you catering for that? That's a very good question" | Q |
| D62 | News is easy: scrape it, it arrives in order. | "news is not so hard to get" | W (insight) |
| D63 | Feeds per platform: cTrader Open API (confirm), futures with better data, crypto and Hyperliquid perps, spot. Settle brokers and platforms. | "we need to figure out also the brokers" | Q |
| D64 | The router's technique is fine, the overall architecture poor. "Speed from slow work early" was in the old system already. | "the overall architecture is poor" | R |
| D65 | A unit has its own access to the market feed, so a pool of market feed for 200+ units. How do they all connect, given the Open API limits? | "we need to have a pool of market feed" | R + Q |
| D66 | If a unit reads both live data and MIS output, that design lives inside the unit and the MIS changes. | "the design should be catered for inside the unit" | W (lean) |
| D67 | A 5-trading-day plan is viable for the MIS lens, shaky for the unit (scalper) lens. Re-architect. | "for the unit lens, it's shaky" | R |
| D68 | His earlier answers need rethinking across the whole lens. | "my earlier responses are going to be need to be like rethought through" | H |

### 1.8 Holds, answers to the 8 questions, local first

| # | Point | His words | Type |
|---|---|---|---|
| D69 | The markets-and-gaps page: he will write his own reply. | "I'll rewrite my own pace" | H |
| D70 | Unit library and build order: seen, hold. | "Now hold on to that" | H |
| D71 | Q1: a sibling unit, yes, rethought for agents and all of the above. | "grab your recommendation, but with a bit of thought" | R |
| D72 | Q2: hold. The answer may come from Hermes, journals and QMB. | "I think the answer might arrive on its own" | H |
| D73 | Look at `Stats`, not `strats`. | "The folder you're meant to be looking at is stats" | R |
| D74 | Q3: only he promotes. The only automatic transition is the risk rules stopping a unit, logged and monitored. | "nothing actually ever enters live without me" | R |
| D75 | Q4 and Q5 (grow-back, house money): need more thought. | "I need to think through this a lot" | H |
| D76 | Local first: everything works on his machine before any server. Servers extend, never replace. Backtester and router included. | "It was never to replace" | R |
| D77 | Router split: yes. A fast piece on the trading node; PC; a second and a third machine (storage). | "splitting it, I think, is the best fit" | R |
| D78 | Like the R2 buckets: splittable, yet also viable on one machine. | "it can be split in, but also be on one machine" | R |
| D79 | Unfinished: he already gave the answer but can't articulate it. | "I already gave you the answer. I just can't articulate it" | U |
| D80 | Everything must fit the Library. | "the library is very important" | R |
| D81 | Router logs and journals. DevOps = monitoring, logging, observability. | "DevOps literally has observability" | R |
| D82 | The Library can hold caches: same compute, different positions. | "we can use the same compute, just different positions" | W |
| D83 | Don't overload the node. Many instruments may mean several nodes or several routers. How would a central one work? | "multiple trading nodes or multiple routers, unless I'm wrong" | Q |
| D84 | The router uses models, so training per instrument. What came out of the MTFA research? | "we also need to train for specific instruments" | Q |
| D85 | Scalper types are not set in stone. A custom ML model that isn't a scalper type must fit. | "add defaults, but keep it free" | R |
| D86 | The same goes for the dictionary. | "Keep it free" | R |
| D87 | The Hermes conversations should give nudges and hints. | "giving you bits of nudges and hints" | W |
| D88 | Papers may become workflows or templates (QMA v2 has many) or improve systems. | "you might build your own workflows in here or templates" | W |
| D89 | Pick ideas and tooling (LightGBM, transformers) that widen how strategies are found. | "they can enhance the range in which we can find strategies" | W |
| D90 | Finding and filtering are two puzzle pieces. Filtering is where workflows come in, mostly run by agents. | "I think actually those are two puzzle pieces" | W (insight) |
| D91 | Use agents a lot: the response is huge. | "you're going to need agents for this, like a lot" | H |
| D92 | Follow-up: use the BMad stack (brainstorming, party mode) to map ideas so no permutation is missed. Handle the dictation verbatim. | "we might miss a few permutations" | H |
| D93 | Follow-up: also architecture skills (improve-codebase-architecture, poteto mode). Most problems are architecture-based (MIS, the pool). | "Most of the issues you're having are architecture based" | H |

Counts by first mark: R 49, W 22, Q 10, U 4, H 8. Points with two marks are counted once.

**Note on D84 "MTFA".** No file in `research/` uses "MTFA". INFERRED: it means multi-timeframe analysis in the MQL5 articles (02 lists "multi-timeframe bias (H1/H4 context, M1/M5 entry)", CHECKED `02-instruments-and-traders.md:98`). This is a research gap, not an operator question.

---

## 2. Party mode

**The room.** A long table with a whiteboard someone has already written "ROUTER ≠ SWITCH" on in red. Thirteen seats.

| Seat | Who | One line |
|---|---|---|
| Kofi | FX and gold scalper | Trades London gold on 1m. Hates spread more than losses. |
| Dana | Futures trader | ES and NQ, real tape, real rolls. Thinks CFD data is a rumour. |
| Yuki | Perps trader | Hyperliquid and Binance, funding every hour, never sleeps. |
| Margaret | Prop-firm risk manager | "Who stops it at 3 am?" |
| Ilya | Quant obsessed with overfitting | Counts tries in his sleep. |
| Priya | Market-microstructure and data engineer | Owns the feed, owns the Parquet. |
| Sam | DevOps and observability engineer | "If it isn't logged, it didn't happen." |
| Lars | Load-balancer and networking engineer | Speaks fluent Envoy. |
| Mei | ML engineer | Wants features stamped with time and version. |
| Ada | AI-agent designer | Skills, hooks, workflows. Designs for the cheapest model in the room. |
| Jo | Non-technical creator | "Can I just write Python?" |
| Vic | Skeptic | Has a running grudge with Ada. |
| Operator | His own dictated words, quoted | Never paraphrased. |

### Round 1. Lineage, provenance and the idea layer

**Operator:** "We're not trying to vibe trade or vibe code here. It needs to be known. The history needs to be tracked back."

**Ada:** Then nothing becomes a unit without a parent record. An idea record sits in front of every unit: a source, the exact quote or timestamp, a class. A hook refuses `qml.new` without an `idea_id`.

**Jo:** My best idea came to me in the shower. Do I need a YouTube link?

**Ada:** Your source kind is "operator dictation" or "own idea". It's still a record. Free text is fine.

**Vic:** August already tried this. Nine DNA sections for every YouTube clip, and he froze the run because "the regression was the ceremony" (CHECKED 10 §3). Seven thousand ideas times nine sections is clerical hell.

**Ada:** Three fields required: class, source, claims. The rest is optional and an agent fills it lazily.

**Ilya:** Lineage is the try ledger in disguise. If I can't see that a unit is the 40th child of one idea, I can't deflate its Sharpe. No lineage, no judging.

**Sam:** Make it trace context. One root id from the source goes onto the idea, the unit and every trade row. Then "where do winners come from" is a group-by, not a project.

**Operator:** "if you know where most of the high performing strategies come from, you can easily focus on that."

**Kofi:** I'd pay to know which YouTubers' ideas survive real gold spreads. My guess is almost none.

**Ilya:** Careful. A source that fed us 500 ideas will have more survivors by luck. Yield needs tries in the denominator, or the board just rewards whoever is loudest.

**Mei:** Models need lineage too. An ensembler's parents are its training window, its features and the model it was built with.

**Margaret:** And a compliance note: know whether a unit was copied from a paid signal service. Some prop firms ban copy trading.

**Priya:** Data provenance belongs here as well. Every test should name the dataset fingerprint it used, or lineage stops at the data's edge.

**Vic:** Who reads the preview anyway? Him or the agents?

**Ada:** Both, from one object. The preview is what an agent reads first, the way a skill's one-line description works. The UI renders the same thing.

**Disagreements recorded**
- R1-a: idea record required for every unit (Ada) vs optional for human and plain-Python units (Jo).
- R1-b: how much of DNA A–I is required (Vic: almost nothing) vs (Ada: three fields).
- R1-c: whether a "source yield" board is honest without tries per source (Ilya) or useful as is (Kofi).

### Round 2. The unit journal as a DevOps layer, plus the market (router) journal

**Operator:** "it's anything that can record data... both for the unit and also for the agents."

**Sam:** Then use the three pillars. Events are logs, rollups are metrics, and a trade is a trace: a signal span, a conditions span, an order span, a fill span, manage spans, an exit span. Any trade can be opened like a request trace.

**Kofi:** And the trades I didn't take. Spread too wide, wrong session, max positions: each one with its reason. And the ones I missed because the feed went stale.

**Priya:** Spread, swap, commission, funding and session state are market facts, not unit facts. Put them in one market journal per broker, account type, instrument and minute. About 1-2 GB a year (CHECKED 12 §5.2).

**Operator:** "When you look at slippage, spread, and fees... It's going to just be duplicating, okay? Because the router is kind of doing this already."

**Lars:** Slippage is a fill, though. A fill belongs to whoever sent the order.

**Priya:** Right. Fills stay in the unit journal. Slippage aggregates fold into the market journal nightly. The unit row carries a key into the market journal instead of a copy.

**Mei:** I want the market state at decision time copied onto the trade. If someone rewrites a partition, my training set changes under me.

**Priya:** Frozen partitions never change, and a fingerprint names them (CHECKED 12 §5.3). A key into an immutable partition is as reproducible as a copy, without the copy.

**Mei:** Fine, if "frozen" really means frozen.

**Ilya:** One writer per section, always. Agents get a notes section. They never touch backtest or live results.

**Ada:** And they write through a journal tool behind a hook. A proposal is a typed object with evidence links and an expiry, not a paragraph.

**Vic:** 200 units logging every bar is about 105 million rows a year (CHECKED 12 §5.2). Who reads that?

**Sam:** Nobody, so don't keep it by default. Events by default, every bar on request, tick-level debug time-boxed. That is ordinary log sampling.

**Yuki:** Perps funding is both a market fact (the rate) and a unit cost (what I paid). Both journals, different meanings.

**Dana:** Futures rolls: which contract each trade was in. Otherwise your journal lies at every roll.

**Margaret:** And log the guard too. Every block, every stop, with its level and its reason.

**Sam:** Give units SLOs from their own exam: trade rate, cut rate, slippage band. Burn-rate alerts are your decay watch, only renamed.

**Operator:** "when you look at WF3 from our old system... I think it does circle around this use case."

**Disagreements recorded**
- R2-a: copy market state onto each trade (Mei) vs a join key into immutable partitions (Priya).
- R2-b: the router's decision log inside the market journal (Priya) vs its own journal (Lars, Sam).
- R2-c: events-only default (Sam) vs every bar for ML training (Mei).

### Round 3. The router as a load balancer that directs, its algorithms, the correlation ledger, independence

**Operator:** "Routing is directing or concentric. Neither does it switch on, nor does it switch off."

**Lars:** In load-balancer terms, the market is traffic and the units are backends. The usual algorithms: round robin, weighted round robin, least connections, least response time, hashing (sticky), random with two choices, resource-based. Then hybrids.

**Vic:** A load balancer decides who serves each request. That's a switch with better manners.

**Lars:** Not here, because the traffic isn't exclusive. A unit's home market is its own traffic. The router only hands out the *extra* traffic: new markets, new sessions, look-alikes. It never ejects anyone.

**Kofi:** My gold scalper trades London gold whatever the router thinks. If the router says "USDJPY in Tokyo looks like your conditions", I can take it or ignore it.

**Ilya:** Every accepted offer is a new cell, so a new try. And an offer should say whether it is proven or a hypothesis.

**Margaret:** If the router is down, fine, it's a non-event. But who stops a scalper when gold's spread blows out at 3 am?

**Lars:** The guard, locally, from the feed. Not the router. In 09 the router's gate blocked new entries. Under his correction those checks belong to the unit's own conditions and to the guard.

**Operator:** "what happens when the router is off? Then what? Does it mean we won't be able to trade even if the pair and the broker and everything else is available? No."

**Lars:** So the map: weighted round robin gives proven units a bigger share of offers. Least connections sends the offer to the market with the fewest correlated units already on it. Least response time becomes least cost: the market where spread over target is cheapest now. Hashing gives session affinity, so a unit keeps its known homes. Power-of-two choices picks two eligible units and offers to the less correlated one, which is cheap and stops herding. Resource-based uses liquidity capacity.

**Ilya:** I want power-of-two as the default. Herding is how a book of 50 units becomes one bet.

**Kofi:** I want least cost. Spread is my whole life.

**Lars:** That's what hybrids are for. Affinity first, then power-of-two among the rest, weighted by proof.

**Priya:** The correlation ledger: rolling correlation of unit P&L and signals, instrument correlation, and per instrument how many units lean long vs short and how split they are. That last one is MASS's consensus minus disagreement (CHECKED 11 §2.6), computed from our own units with no LLM.

**Margaret:** The ledger must belong to the pod. The router can't enforce same-bet limits if it never says no. In the old system the BMS held it (CHECKED `grounding/06-qrmx-transcript-recovery.md:110`).

**Priya:** One computation, two readers. The router reads it for direction, the pod reads it for limits.

**Operator:** "it should tell the, or give the bot, or the unit rather, that, okay, this fits your conditions, or this market is like this."

**Mei:** That depth of information is an MIS feed: condition labels per instrument. If units read it, the 20 Oct seed ("units never read the MIS inside their rules") falls.

**Vic:** And then a router outage changes how a unit trades: exactly what he forbade.

**Mei:** Only if the unit has no fallback. Make every unit declare its behaviour when the MIS feed is missing, and have QMB test it both ways.

**Ada:** Give every unit a `router_mode`: ignore, advise or follow-offers. Default advise.

**Lars:** At 500 units, the router publishes on a bus and units pull. No handshakes, no per-unit calls. Fan-out costs one publish.

**Disagreements recorded**
- R3-a: is directing extra traffic still switching? (Vic yes; Lars no, because home traffic stays the unit's.)
- R3-b: correlation ledger owner: router (D57) vs pod/BMS (Margaret, old record) vs shared object (Priya).
- R3-c: units reading MIS labels (Mei, D66) vs never in rules (Vic, seed 20 Oct, 07 F-7).
- R3-d: default algorithm: power-of-two (Ilya) vs least cost (Kofi) vs weighted round robin (Lars's first pick).

### Round 4. The market-feed pool for 200+ units, local first

**Operator:** "Remember, the unit has also access to market feed... So it means we need to have a pool of market feed."

**Priya:** One feed keeper per broker connection. It subscribes once per symbol and fans out to every unit on that machine over a local bus. 200 units on 60 symbols means 60 subscriptions, not 200 (INFERRED design, 12 §4.2).

**Lars:** cTrader allows about two connections per app, one demo and one live (CHECKED 12 §4.1). The PC and the node can't both hold the live one. One holds a lease, the other reads its pool.

**Sam:** Or register two cTrader apps, one per machine, and skip the lease.

**Priya:** Maybe. A token refresh invalidates the old token everywhere (CHECKED `seeds.md`, trading-node correction), so check how grants behave across two apps first.

**Yuki:** Hyperliquid limits per IP: 1,000 subscriptions (CHECKED 12 §4.1). Each machine can subscribe on its own, no lease.

**Dana:** Futures data is paid per exchange subscription, not per unit. Price it per feed, never per bot.

**Kofi:** For scalpers: ticks, and a last-value cache so a restarted unit is warm at once.

**Priya:** And the keeper records everything into the same Parquet QMB reads. Today's live feed becomes tomorrow's backtest data. That is also the Dukascopy escape route.

**Vic:** Local first, with 12 GB free on C: and 8.3 GB on D: (CHECKED 12 §5.2)?

**Sam:** Local first means the same code runs on the PC. The archive lives on the storage machine; the PC caches the months it needs.

**Mei:** Compute the MIS labelers at the keeper: spread ratio, volatility state, session state, published as derived streams. A feature store, basically. Units and guards subscribe.

**Margaret:** Guards read the same pool. No router hop between a spread spike and the guard.

**Jo:** Can my mini app read it too?

**Priya:** Same door, same bus.

**Disagreements recorded**
- R4-a: connection lease (Lars) vs one cTrader app per machine (Sam).
- R4-b: where derived features are computed: keeper (Mei) vs router (09's plan) vs each unit.
- R4-c: in-process bus first (12's recommendation) vs a message server from day one (Lars, who expects separate machines soon).

### Round 5. The account guard plus the pod, or the BMS

**Operator:** "the pod is literally the BMS in a way. I feel like it's literally the same bloody thing, but then the BMS already catered for everything in the account guard, so we need to standardize these two."

**Margaret:** He's right on the record. The BMS "accounts and constrains; never trades or sizes; one BMS per account, many Books" (CHECKED `grounding/02-book-and-prior-sims.md:147`). That *is* the account guard. The Book did the sizing, which now lives in units. So pod = BMS = guard, plus a shared budget, plus the correlation ledger.

**Vic:** Except the Lab already uses "pod" for something else: "pods (risk/sizing systems; Book+BMS is one kind)" (CHECKED `grounding/05-findings-2026-10-13.md:73`). In the Lab a pod is a thing you build and test. The names collide.

**Ada:** So split authority from shape. The guard is a fixed floor: local, per account, unremovable. The pod is a template above it that a copilot may remake. One code shape, two authorities.

**Operator:** "I think we are handling two things at a go. We are trying to handle a portfolio overall, as well as the portfolio configuration."

**Ada:** That's the same split. Pod *design* lives in the Lab and is tested in QMB. A pod *instance* lives on the node with live state. Same code, two places.

**Margaret:** Prop-firm practice: daily loss, max loss, consistency and news windows are guard rules. And the old kill-switch ladder fits his Q3 answer exactly: GREEN to BLACK, escalation automatic, de-escalation by a human only (CHECKED `grounding/02-book-and-prior-sims.md` §1.7).

**Kofi:** One pod per account, or several? Netting accounts want one Book per account (CHECKED same table).

**Ilya:** Whatever the shape, test the pod as a portfolio in QMB and judge each unit by what it adds to the pod, not alone.

**Jo:** If the copilot can remake pods, fine, as long as nobody can remake the floor.

**Vic:** And "self-configuring" still hasn't been shown. That's the risk session's job. What this room can offer is the receipt: when a unit recalibrates, which number moved, from which data, under which rule, inside which range.

**Disagreements recorded**
- R5-a: combine guard and pod into one BMS-like object (Margaret) vs one shape, split authority (Ada).
- R5-b: one pod per account (Kofi) vs several pods per account.
- R5-c: does the pod enforce correlation limits (Margaret) or only read the ledger and propose (Ilya)?

### Round 6. QMB at a professional level: LEAN CLI, Jesse, old QMX

**Operator:** "when you tell an agent to backtest, I don't think an agent is going to use code. It's going to try and manipulate everything over and over again."

**Ada:** So one door: a LEAN-shaped CLI plus an MCP door. The agent sends a run spec and gets back a result id. A hook stops shell-made backtests from writing anywhere a journal reads.

**Ilya:** Bring back the old pass numbers: 200 trades, +0.15R after costs, PBO below 0.25 to pass and above 0.50 dead (CHECKED 08 §0).

**Jo:** He said "don't be too strict".

**Ilya:** Then they warn. They don't refuse. But they show.

**Kofi:** Bring back parity replay of the live rules, and MAE/MFE. The old system had both and the new one dropped them (CHECKED 08 §0, point 3).

**Priya:** The lookback cap is the replay reader: each step copies all prior prices, so runs stop at 1,000 steps, about 17 hours of 1m (CHECKED 12 §1). Window it, and 1990 becomes a question of data, not code.

**Dana:** Continuous futures versus the real contract, and roll dates. The instrument spec has to carry them.

**Yuki:** Today QMB replays quotes only, so no crypto or perps (CHECKED 01). Funding replay is a must.

**Jo:** Can QMB run my plain Python class? LEAN does that: you write an algorithm class and it runs.

**Sam:** Give every result an identity: hashes of the logic, the pod policy, the data, the cost model and the evaluator. Change any of them and the old verdict becomes stale, not false (CHECKED 10 §2.10).

**Mei:** ML units need walk-forward retraining inside the backtest, with each model artifact versioned.

**Vic:** And his question, why the old ideas were refused. From 08 and 10, nobody refused them in a ruling. They were placement calls for an older QMX, or dropped during refactors (INFERRED from 10 §3 and 08 §1.4).

**Disagreements recorded**
- R6-a: pass numbers that refuse (none) vs warn (Ilya) vs grades only (Jo).
- R6-b: plain-Python units in QMB: counted as tries like any unit (Ilya) vs a lighter "exploration" lane (Jo).

### Round 7. Judging as a skill: history plus paper, and the paper sequence

**Operator:** "judging and improvement should come from historical and paper trading... if you do both, you reduce the probability of overfit... we need to figure out, when we do both, when do we paper trade."

**Ilya:** The order: screen, full backtest, stress, sealed months, paper. Paper is the only data the search has never touched.

**Margaret:** Prop firms already run this shape: a challenge with a target and loss limits, then verification, then funded with scaling. Borrow it for paper.

**Kofi:** Broker demo fills flatter you. Paper should run as shadow live on the node's real feed with real spreads, and record the demo fill beside it.

**Yuki:** Same for perps. Testnet books are fake. Shadow mainnet.

**Ada:** The skill: one SKILL.md, deterministic scripts that call QMB, hooks that refuse a verdict without a QMB run id. Output: a judge report in parts, and a proposal card.

**Vic:** "A skill that summarizes everything" becomes a god object.

**Ada:** It orchestrates. The maths lives in QMB `robustness/`. The skill only calls and formats.

**Operator:** "remember, at the same time, we have a very, should I say, special part of risk management and position sizing... it was a bit radioactive... while judging, we should put that in mind."

**Ilya:** So judge twice: once at flat 1R, once along the unit's real sizing path (session capital, house money), with a block-bootstrap ruin probability. A unit that only works at flat R is a different unit.

**Jo:** Grades, please. "Stressed", "sealed", "paper". Not pass or fail.

**Mei:** ML units drift. Paper matters even more for them.

**Disagreements recorded**
- R7-a: paper always (Ilya) vs a shorter lane for siblings of live units (Kofi).
- R7-b: paper length by trade count (Ilya) vs calendar time (Margaret).
- R7-c: judging at flat R, at the real sizing path, or both shown (consensus: both, INFERRED).

### Round 8. Finding vs filtering workflows from the papers

**Operator:** "filtering is where I think we might need workflows... I think actually those are two puzzle pieces."

**Mei:** Finding: LLM hypothesis loops (AlphaAgent), tree search (MCTS), evolution of whole trajectories (QuantaAlpha), plus LightGBM or transformer models as units in their own right.

**Ilya:** Finding is cheap and wide. Filtering is where every candidate gets counted. Overfitting grows with refinement depth, and gains decay after about 15 rounds (CHECKED 11 §0).

**Ada:** Six templates already drafted: T1 hypothesis-to-unit, T2 tree refinement, T3 zoo hygiene, T4 LLM-memory probe, T5 news labeler, T6 consensus study (CHECKED 11 §3).

**Vic:** None of the eight papers tests FX, CFDs or crypto intraday, and none trades live (CHECKED 11 §0). Take the process, not the numbers.

**Kofi:** Here's a finder nobody named: mine the operator's own manual trades, if he keeps any, into idea records.

**Disagreements recorded**
- R8-a: LLM scores as advisory notes (Ada) vs no LLM scores at all (Ilya).
- R8-b: ML-model units that nobody can read (Mei) vs only hypothesis-led units (Vic).

### Round 9. Unbounded by default: plain Python, no lookback cap, no cages

**Operator:** "Like, don't drop anything. Yeah, add defaults, but keep it free, yeah? Same thing, I think, goes the dictionary."

**Jo:** So: a raw Python unit, an ML ensembler, a mini app that rewrites a unit. All allowed.

**Ada:** All allowed. Agents get the standard through hooks. Humans and mini apps get the same doors without the refusals.

**Ilya:** Freedom doesn't buy a softer judge. Same tries, same seal, same cost stress.

**Vic:** A plain-Python unit can't be checked for look-ahead the way a QML graph can. Then what?

**Ada:** It runs, and its report says "look-ahead not verified". It isn't blocked.

**Priya:** No lookback maximum anywhere. Default start 2020-03-01. A request older than the data gets a plain answer, such as "no 1m EURUSD before 2003-05-04 from Dukascopy; daily exists from 1973" (CHECKED 12 §1-2).

**Kofi:** Scalper types are tags. My unit is "custom" if I say so.

**Mei:** A dictionary entry can be a model, not only an indicator.

**Disagreements recorded**
- R9-a: agents may use the escape hatch (operator: a copilot "can remake") vs refuse by default for agents (Ada).

### Round 10. Designing for agents, not humans; the preview and the detailed view

**Operator:** "Stop designing for humans, start looking at agents."

**Ada:** Progressive disclosure, like skills. An index line of one sentence, a preview card with a few numbers, and the detailed view loaded on demand. One JSON object, rendered by the UI.

**Sam:** Handles, not dumps. Tools already page results 50 at a time and return a handle past 5,000 rows (CHECKED 12 §1, row 7).

**Jo:** But he's the one who clicks "promote". The preview has to answer "should I click?".

**Vic:** Design everything for agents and his one click goes blind.

**Ada:** Then the promotion page is the single human-first page. Everything else is agent-first.

**Disagreements recorded**
- R10-a: everything agent-first (Ada) vs one human-first page for promotion (Jo, Vic). Partly settled by I26.

### Round 11. Genetic moves: one part across families

**Operator** (26 Aug, quoted in 10 §2.9): "we can mutate and adopt certain features from specific bots, and then we combine them to make hybrids, tribids... we test it across families."

**Ada:** Named ports make it mechanical: setup, entry, invalidation, exit, regime. A transplant is a `replace_subgraph` from family X into family Y (CHECKED 10 §2.3 and §2.6).

**Ilya:** Each transplant is a try in the receiving family. And to know which part carries the value you need ablations, which round 1 killed as "ablation of every part" (CHECKED 07 §8.2).

**Vic:** 07 also killed "genetic crossover" outright (CHECKED 07 §8.2). He has now revived it. Record that as an overrule.

**Jo:** My Python unit has no ports. Can't it donate?

**Mei:** An agent can rewrite the piece into ports. The original stays as is.

**Kofi:** Confirmation patterns travel badly across instruments. Test transfer on siblings before you transplant across families.

**Disagreements recorded**
- R11-a: measure part value by ablation (Ilya) vs correction 1 "no every-part-proves machinery" (Vic).
- R11-b: transplants run automatically by workflows (Mei) vs proposals only (Ada).

### Round 12. The Dukascopy data risk

**Priya:** The old `bi5` feed broke in July 2026. The new one sits behind an AWS bot wall, and a challenged hour comes back empty without an error (CHECKED 12 §2.1). The site terms forbid bots and "constructing a database" (CHECKED 12 §2.1).

**Margaret:** Personal, non-commercial use, never redistributed, keep the licence tag. Know it; don't panic.

**Sam:** Back up the 10 GB of old ticks today. They are irreplaceable at that cost.

**Dana:** Futures: Databento Standard is $199 a month (CHECKED 12 §2.2). Pay when a futures unit is real, not before.

**Yuki:** Crypto: Binance bulk files are free. Tardis has Hyperliquid since Oct 2024 (CHECKED 12 §2.2).

**Vic:** Record our own feed from day one, and the problem shrinks every month.

**Kofi:** Dukascopy's spreads aren't my broker's. Cost truth comes from my broker's own feed.

**Disagreements recorded**
- R12-a: keep scraping Dukascopy with headed Chromium (Priya) vs freeze it and rely on own recording plus HistData (Vic).
- R12-b: pay for data now (Dana) vs only when a unit needs it (Margaret).

### Round 13 (walk-on). The envelope

**Lars:** Something's been bugging me since round 3. If the router offers a live unit a new market, Q1 says that's a sibling, a new unit. And only he promotes. So offers to live units for new markets can't go live.

**Ilya:** Right. An offer outside what he admitted is a proposal for a paper sibling.

**Margaret:** Then define what his click admits. Not one market: an envelope he ticks. Markets, sessions, brokers.

**Kofi:** Inside the envelope the router directs live. Outside, it proposes paper.

**Vic:** And with the router off?

**Lars:** The unit trades its envelope on its own conditions, or only its home market. That's his call, not ours.

**Disagreement recorded**
- R13-a: router-off behaviour: home market only (Margaret) vs the whole admitted envelope (Kofi). Goes to Q3.

---

## 3. Brainstorming (headless; seven techniques)

Each technique's output is listed by idea number from the master list (§5). New ideas born in a technique are added to §5 and marked there.

### 3.1 Morphological analysis

Axes (all independent):

| Axis | Options |
|---|---|
| Unit kind | QML graph · QML hooks · plain Python · ML model · ensembler · mini-app-built |
| Instrument class | FX · metals · index CFD · stock CFD · commodity CFD · futures · perps · crypto spot |
| Timeframe | tick · 1s · 1m · 5m · 1h · daily |
| Session | Asia · London · NY · overlap · 24/7 · HIP-3 weekend |
| Broker / platform | cTrader · MT5 · Hyperliquid · Binance · IB/Rithmic |
| Source | YouTube · blog · paper · MQL5 article · copilot chat · operator dictation · agent-generated · operator manual trades |
| Stage | idea · built · backtested · stressed · sealed · paper · live · stopped · retired |
| Host | PC · node · storage machine |
| Router mode | ignore · advise · follow-offers |
| History source | Dukascopy · broker · HistData · Binance bulk · Databento/Tardis · own recording |

Cells worth a look (each an untried or risky configuration; INFERRED):

| Cell | What it exposes | Ideas |
|---|---|---|
| agent-generated × ML model × perps × 1m × 24/7 × Hyperliquid | LLM-memory look-ahead, funding replay, only ~5,000 venue candles so own recording is the only history | I10, I112, I154, I123 (J5) |
| plain Python × any × transplant donor | No ports, so no mechanical transplant | I149, I148 |
| operator manual trades × gold × London | A new source kind; idea records from his own trades | I135, I2 |
| scalper × daily data × 1990 | Lookback allowed but intraday data doesn't exist; honest answer | I106, I137 |
| stock CFD × MT5 × node on Linux | MT5 needs Windows or Wine (CHECKED `seeds.md`) | I86, I159 |
| router mode follow × router down | Must fall back; tested in QMB both ways | I59, I58 |
| sibling on a new broker × live parent | Needs his click (Q3); router can't take it live | I180 |
| perps × funding hour × scalper exit | Exit block "don't hold across funding" exists (07 F-10) | I53, I111 |
| futures × roll week × index CFD sibling | CFD and futures diverge at roll | I111, I112 |
| copilot chat source × composite of two parents | `composed-from` edge missing in today's enum (CHECKED 10 §4) | I7, I5 |
| host PC × tick archive | 12 GB free; cache, not archive | I160, I162 |
| ensembler × pod | A model that reallocates units is a pod, not a unit | I16, I95 |
| guard × router × feed all on PC, node absent | PC-only mode is the test bed | I162, I100 |
| storage machine × router plan | The Library holds plans as objects | I67, I82 |

### 3.2 SCAMPER (on the router, the journal and the judge)

- **Substitute:** substitute the gate (09) with unit-owned conditions plus local guards (I76, I83). Substitute a correlation number with a similarity vector (I71).
- **Combine:** combine the market journal and SQS baselines in one keeper job (I82, I84). Combine lineage and the try ledger (I3, I8).
- **Adapt:** adapt prop-firm phases to paper (I124). Adapt Envoy xDS plan slices to many nodes (I68). Adapt OpenTelemetry traces to trades (I30).
- **Modify:** modify the plan expiry so it only stops offers (I65). Modify pass numbers to warn-only (I103).
- **Put to other use:** the router decision journal measures the router's own value (I50). The recorder doubles as the Dukascopy fix (I80, I154). Unit consensus becomes depth info (I73).
- **Eliminate:** remove the router from the data path (I54). Remove per-unit copies of spread and fees (I39, I40).
- **Reverse:** units pull from the router instead of the router pushing on/off (I74). Agents write proposals while humans only accept (I28).

### 3.3 Reverse brainstorming and anti-solution ("how do we make QMX lose money with these parts?")

| Sabotage | Inverse idea |
|---|---|
| Make every unit call the router before each trade | I54, I74: never in the trade path; pub/sub |
| Let the router's 5-day plan decide scalper conditions | I64: two caches by lens |
| Store spread in 200 unit journals, all slightly different | I40, I39: one market journal, join keys |
| Let agents paste backtest numbers into journals | I34, I114: single writer, hooks |
| Pick the best of 3,000 searched units and call it proof | I123 (J1, J2), I8: tries include screens and depth |
| Trust Dukascopy's empty hours | I155, I156: retry on empty, quality checklist |
| Let a copilot remake the pod and delete the kill line | I92, I93: an unremovable guard floor |
| Let a weak model write a unit with no source | I1, I179: idea record and trajectory hooks |
| Promote a sibling because the router liked a market | I180: envelope; outside = paper proposal |
| Let PC and node both open the live cTrader connection | I81: lease or separate apps |
| Train one MIS model on all instruments and apply it everywhere | I69: pooled plus per-instrument fit |
| Delete failed experiments to save space | I11, I172: keep everything, mark only |
| Judge at flat 1R, then trade with house money | I122: judge along the real sizing path |
| Run units on the node until it chokes | I161: node budget, shard by instrument |

### 3.4 Analogical thinking

**Load balancers** (party round 3 plus): algorithm menu I60, default hybrid I61, affinity I60, pub/sub I74, outlier detection turned into information I76, plan slices I68, consistent hashing for instruments I68.

**Observability stacks:** traces I30, SLOs and burn rate I36, exemplars I37, sampling levels I38 and tail sampling I177, black-box flight recorder I165, chaos drills I166, heartbeats that are non-critical I75.

**Genetics:**
- vertical inheritance = versions (I5);
- recombination = crossover (I147);
- horizontal gene transfer = transplant across unrelated families, counted apart in yield stats (I145, I173);
- genotype vs phenotype: the spec vs journal behaviour; same phenotype = same bet (I176);
- linkage disequilibrium: blocks that always travel together can't be scored apart (I175);
- fitness landscape: plateaus vs spikes (I174).

**Libraries and archives:**
- accession register (I170);
- "respect des fonds": keep a source's outputs together for yield (I171);
- finding aids = the three-tier disclosure (I23);
- deaccession = mark, never delete (I172);
- content-addressed identifiers like ISBN (I14, I169);
- citation graph = the lineage DAG (I7).

**CDN and object storage** (his R2 image, D78): plan as an object (I67), edge cache on the node (I64), origin on the PC or storage machine (I66, I160).

### 3.5 TRIZ contradictions

| Improve this | without worsening this | Resolution ideas |
|---|---|---|
| Freedom (plain Python, no cages) | Standards for weak agents | I141 (refuse for agents, warn for humans), I142 |
| Unit independence | Router depth of information | I55-I59 (advisory, expiring, declared fallback) |
| No duplication | ML reproducibility | I39 (keys into immutable partitions) |
| Local first | Small PC disk | I160, I162 (cache vs archive) |
| Agents-first design | His promotion click | I26 (one human-first page) |
| Genetic moves | No "every part proves itself" machinery | I146 (value from comparisons already run), I175 |
| Copilot remakes pods | Safety floor | I92, I93 |
| Router directs new markets | Only he promotes | I180 (envelope) |

### 3.6 Chaos engineering

Break each piece and look at what survives (INFERRED):
- **Router killed:** units keep their envelope (I54, I65); offers expire; drill it weekly (I166).
- **Feed keeper killed:** symbols go stale; guards stop new entries; broker-side stops hold (CHECKED 12 §4.3); flight recorder dumps (I165).
- **PC offline:** node runs on its cached plan (CHECKED 09 §2.6); the planner resumes on reconnect.
- **Library unreachable from the node:** the plan is cached locally (I67).
- **Dukascopy blocks us:** own recording plus HistData (I153, I154).
- **A copilot rewrites the pod badly:** the guard floor holds (I93); the pod is tested in QMB first (I98).
- **A weak model floods 1,000 units:** tries count, the budget grows only on progress (I133), the failure library stops repeats (I11).

### 3.7 Assumption reversal

| Assumption | Reversed | What falls out |
|---|---|---|
| The router decides where units trade | Units decide; the router advises | I55, I58 |
| Spread belongs to each unit | Spread belongs to the market | I40 |
| A unit must be QML | Any Python is a unit | I138, I107 |
| Lineage starts at the unit | Lineage starts at the source sentence | I1, I13 |
| Paper is a gate | Paper is a measurement that runs beside everything | I49, I119 |
| The node is where the MIS lives | The feed pool is where the MIS's fast half lives | I82 |
| The PC is a client of servers | Servers are clients of the PC | I159, I162 (rulings 136-139) |
| Judging needs a score | Judging needs parts | I116, I117 |

---

## 4. Permutation map

### 4.1 Clusters

| Key | Cluster | Ideas |
|---|---|---|
| A | Lineage and provenance, idea layer | I1-I22, I169-I173 |
| B | Views, agents-first | I23-I29 |
| C | Journals | I30-I53, I165, I177, I178 |
| D | Router | I54-I77, I180 |
| E | Feed pool | I78-I90 |
| F | Account guard and pod | I91-I100 |
| G | QMB | I101-I115 |
| H | Judging | I116-I128 |
| I | Finding vs filtering | I129-I136, I179 |
| J | Unbounded | I137-I144 |
| K | Genetic moves | I145-I151, I174-I176 |
| L | Data and Dukascopy | I152-I158 |
| M | Local first, machines | I159-I162, I166 |
| N | Unit life | I163, I164, I168 |

### 4.2 Cross-map

Key: **+** reinforce · **x** conflict (resolution idea in brackets) · **→** the row depends on the column · **.** neutral. Read the row against the column. INFERRED throughout.

| | A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A** | | + | → | . | . | . | + | + | + | x (I17) | + | + | . | + |
| **B** | → | | → | . | . | . | . | → | . | x (I26) | . | . | . | + |
| **C** | + | + | | + | → | + | + | + | + | x (I38) | . | + | x (I160) | + |
| **D** | . | . | → | | → | x (I63) | + | . | . | + | . | . | + | x (I180) |
| **E** | . | . | + | + | | + | + | . | . | + | . | + | x (I81) | . |
| **F** | . | . | + | → | → | | + | + | . | x (I93) | . | . | . | + |
| **G** | + | . | + | + | + | + | | + | + | + / x (I103) | . | → | + | + |
| **H** | → | + | → | . | . | + | → | | + | x (I117) | + | . | . | + |
| **I** | → | . | + | . | . | . | → | → | | + | + | . | . | . |
| **J** | + | x | x | + | + | x | + | x | + | | x (I149) | + | . | . |
| **K** | → | . | + | . | . | . | → | → | + | x | | . | . | . |
| **L** | + | . | + | . | → | . | + | . | . | + | . | | x (I160) | . |
| **M** | . | . | + | + | + | + | + | . | . | . | . | + | | . |
| **N** | + | + | → | x (I180) | . | + | + | + | . | . | . | . | . | |

### 4.3 Strongest pairs and triples

| # | Combination | Why it is strong | Serves |
|---|---|---|---|
| P1 | I180 envelope + I55 offers + I163 unit life | Router directs live only inside what he admitted; outside = paper sibling. "Directs, never switches" fits "only he promotes" | D53, D55, D71, D74 |
| P2 | I78 feed pool + I56 depth feed + I83 guards on the pool | Units, guards and the router read one bus; the router going down changes nothing critical | D54, D59, D60, D65 |
| P3 | I3 trace id + I40 market journal + I41 router decision journal | Any trade explained from source sentence to fill, with no copies | D6, D25, D26, D30, D81 |
| P4 | I8 source yield + I123 (J1) tries + I129 finding/filtering | Narrowing the blast radius honestly, with tries per source | D7, D34, D90 |
| P5 | I145 transplant + I7 edges + I146 block value board | Genetic moves become mechanical, counted and visible | D34, D33 |
| P6 | I154 own recording + I40 market journal + I109 result identity | Closes GAP-0048 (measured costs) and shrinks the Dukascopy risk monthly | D10, D26, D29 |
| P7 | I23 three tiers + I116 judge report + I26 promotion page | Agents-first everywhere, with one human page where his click lives | D4, D45, D48, D74 |
| P8 | I138 unit kinds + I107 Python adapter + I17 outside-standard flag | Full freedom with the same judging and lineage | D13, D15, D12 |
| P9 | I66 split + I67 plan in Library + I159 placement manifest | One codebase on one PC or spread over node, PC and storage | D76-D78, D80, D82 |
| P10 | I45 almanac + I47 cell map + I71 look-alikes | Candidate answer to his unfinished D27, D35 | D27, D33, D35 |
| P11 | I46 cost decomposition + I178 broker SLA + I60 least-cost algorithm | His gold example: broker or hour, answered from data | D29, D63 |
| P12 | I62 correlation ledger + I63 shared object + I94 pod interface | One ledger, router reads for direction, pod reads for limits | D57, D20 |
| P13 | I122 sizing-path judging + I98 pod-in-QMB + I126 ΔBookUtility | Judging respects the radioactive sizing and the pod | D43, D44 |
| P14 | I31 signal funnel + I32 seen-not-taken + I33 missed | His "detected but not taken, or missed" in one mechanism | D24 |
| P15 | I36 SLOs + I44 WF3 reborn + I49 shadow evaluation | Decay watch as DevOps, data keeps flowing while stopped | D25, D32 |

### 4.4 Conflicts that need settling (next study or the operator)

| # | Conflict | Options | Where |
|---|---|---|---|
| X1 | D66 (unit reads MIS output) vs seed 20 Oct and 07 F-7 (unit rules never read the MIS) | never / optional with declared fallback / freely | Q4 |
| X2 | Router offers new markets (D55) vs only he promotes (D74) and new market = sibling (D71) | I180 envelope | Q2 |
| X3 | No duplication (D30) vs reproducible ML features | I39 join keys into frozen partitions | technical, settled by I39 |
| X4 | Genetic transplant vs "no ablation of every part" (correction 1) | I146: score blocks from comparisons already run | next study |
| X5 | Plain-Python freedom vs transplant needs ports | I149: agent rewrite into ports, original kept | next study |
| X6 | Copilot remakes pods (D40) vs a safety floor | I92 or I93 | Q1 |
| X7 | Correlation ledger owner: router (D57) vs BMS/pod (old record) | I63 one object, two readers | technical |
| X8 | Agents-first (D45) vs his click needs a readable page | I26 | technical |
| X9 | Local first (D76) vs 12 GB free disk (CHECKED 12) | I160 cache plus storage machine; a bigger disk is his call | his call, not asked |
| X10 | cTrader about two connections per app vs PC and node both live | I81 lease or two apps; a one-minute demo test settles it (12 §7) | technical |
| X11 | Pass numbers (I103) vs "don't be too strict" (D42) | warn-only | technical |
| X12 | Judging skill "summarizes everything" (D47) vs a god object | the skill orchestrates; maths stays in QMB | technical |
| X13 | 09's gate "blocks new entries" vs D53 | checks move to the unit's conditions and the guard (I76) | technical |
| X14 | Round-1 load-balancer ideas (drain, eject, canary seat; 07a §3.3) vs D53 | re-label as information or guard rules (I76) | technical |
| X15 | Dukascopy terms vs heavy downloads | slow, personal, own recording (I156, I157) | his awareness |
| X16 | 07 killed "genetic crossover" (CHECKED 07 §8.2) vs his 26 Aug idea | record the overrule (I151) | record |

### 4.5 Dependencies (what must exist first)

- Everything in G, H, I and K waits on the QMB door that trades (CHECKED `STATE.md`, "QMB backtest door") and the windowed reader (I105).
- D depends on E (the router reads the pool) and on C (the ledger reads journals).
- F's live instance depends on E (guards read the pool).
- K depends on A (edges) and on named ports (I148).
- B depends on A, C and H (it renders them).
- The analyst lens (I8, I21, I47) needs months of journals: plan it now, expect value later.

### 4.6 Dictation coverage (every Dn against the ideas that serve it)

| Dn | Ideas | Dn | Ideas |
|---|---|---|---|
| D1 | I18, §3 of 10 | D48 | I28, I116, I127 |
| D2 | **none needed** | D49 | I11, I34, I35 |
| D3 | I163, I164 | D50 | **out of scope here** (risk session); I99 only |
| D4 | I20, I23, I24, I127 | D51 | **out of scope here**; I36, I44 touch it |
| D5 | I1, I5, I7, I12, I25, I169, I172 | D52 | I76 |
| D6 | I1, I2, I3, I10, I13, I14, I17, I179 | D53 | I55, I57 |
| D7 | I8, I9, I21, I171 | D54 | I54, I58, I59, I110, I168 |
| D8 | I103, I104 | D55 | I55, I60, I61 |
| D9 | I53, I86, I111, I112 | D56 | I74 |
| D10 | I80, I88, I152-I158 | D57 | I62, I63, I73 |
| D11 | I105, I106, I137, I144 | D58 | I56, I57, I71, I72, I73 |
| D12 | I58, I133, I142 | D59 | I54, I75, I77, I100, I166 |
| D13 | I17, I87, I90, I107, I115, I138 | D60 | I42, I82, I83, I85, I100 |
| D14 | I141 | D61 | I82, I84 |
| D15 | I16, I107, I108, I131, I138 | D62 | I85 |
| D16 | I52, I95, I98 | D63 | I81, I86, I89, I153, I178 |
| D17 | I92, I93, I95 (partial; Q1) | D64 | I64, I66 |
| D18 | I91 | D65 | I78-I81, I89 |
| D19 | I99 (partial; maths in the risk session) | D66 | I56, I59, I82 (conflict X1) |
| D20 | I91-I94, I63 | D67 | I64, I65 |
| D21 | **none needed** | D68 | I76, I151 |
| D22 | I30, I34 | D69 | **hold** |
| D23 | I34, I114, I136, I141, I179 | D70 | **hold** |
| D24 | I31, I32, I33, I48, I49 | D71 | I22, I120, I180 |
| D25 | I30, I36, I37, I165 | D72 | I5, I6, I109 (options only; Q2 held) |
| D26 | I40, I41, I53, I158 | D73 | I18 (10 already did it) |
| D27 | I45, I47, I71 (guesses; Q6) | D74 | I26, I42, I96, I128, I163 |
| D28 | I30, I45, I46 | D75 | **out of scope here** |
| D29 | I46, I178, I60 | D76 | I66, I159, I162 |
| D30 | I14, I38, I39, I51, I109, I177 | D77 | I66 |
| D31 | I39, I40 | D78 | I66, I67 |
| D32 | I36, I44, I49 | D79 | I64, I66, I67 (guesses) |
| D33 | I3, I4, I43, I47, I174 | D80 | I51, I67, I169 |
| D34 | I5, I22, I43, I52, I134, I145-I147 | D81 | I30, I41 |
| D35 | I45, I47 (guesses; Q6) | D82 | I67, I159, I160 |
| D36 | I101, I102 | D83 | I68, I161 |
| D37 | I87, I101, I113, I114 | D84 | I69, I70, I108 (MTFA = research gap) |
| D38 | I103, I104 | D85 | I139 |
| D39 | I116, I123 | D86 | I140 |
| D40 | I93, I143 | D87 | I18 |
| D41 | I116 | D88 | I130 |
| D42 | I103, I117, I124 | D89 | I131, I132 |
| D43 | I122 | D90 | I129 |
| D44 | I118-I121, I125 | D91 | **not served** (brief forbids subagents here) |
| D45 | I23, I27, I29 | D92 | this file |
| D46 | I123 | D93 | **next step** (architecture-skill studies) |
| D47 | I116 | | |

**Unserved points:** D2 and D21 (nothing to build), D50, D51 and D75 (out of scope by brief), D69 and D70 (holds), D91 (process). **Weakly served:** D17, D19, D27, D35 and D79. These rest on partial ideas or on guesses at what he meant.

---

## 5. Idea list (numbered, unranked)

Format: **I#. Name.** What it is. · lens · surface · touches · serves. Lens key: AG agents/code, TR trader, CR creator, AN analyst, OPS DevOps. "Parked" = doesn't fit yet.

### A. Lineage, provenance and the idea layer

- **I1. Idea record tier.** An idea record sits in front of every unit (light DNA: class, source, claims; the rest optional). The unit spec gains `idea_id`. · AN/AG · Library, QML · new `idea` kind, unit spec · D5 D6 D7
- **I2. More source kinds.** chat-session, copilot-chat, operator-dictation, workflow-run, agent-generated, operator-manual-trades, paper, mql5-article, youtube, blog. The locator is a message id, timestamp or page. · AN · Library · source manifest · D6
- **I3. Trace id from source to trade.** One root id on idea, unit and every trade row. · OPS/AN · Library, journals · journal schema · D6 D7 D33
- **I4. Trajectory events.** The ordered steps that made a unit (card, build, check, test, reflect, "mutated step k", "crossed A+B") go into its journal events (from QuantaAlpha). · AG · QML, workflows · journal events · D5 D33
- **I5. Variants as edit operations.** A variant is an ordered list of operations on a pinned parent. Applying it to a stale parent fails. · AG · QML · lineage store · D5 D34
- **I6. The edit's kind decides "new or same".** Uses the table in 10 §5.1, enforced by `qml.check`. An option only: Q2 is held. · AG · QML · check · D72
- **I7. Wider lineage edges.** derived-from, sibling-of, composed-from, corrected-from, rewritten-from, transplanted-from, re-run-of. · AG/AN · Library · edge kinds · D5 D34
- **I8. Source yield board, tries in the denominator.** Survivors per source kind, creator, model and workflow, corrected for how many ideas each source fed. Revives 07's parked scoreboard because he asked. · AN · Lab, mini app · journals, lineage · D7
- **I9. Narrowing the blast radius as a proposal.** A workflow suggests next month's intake mix from source yield. He approves. · AN/AG · workflows · intake queue · D7
- **I10. Author stamp on agent-built units.** Model, its training cutoff, workflow version, prompt hash. Feeds the LLM-memory check. · AG · QML · unit spec · D6 D44
- **I11. Failure library per family.** Typed reasons, never deleted, read by agents before they generate. · AG · Library · family notes · D24 D34 D49
- **I12. Experiments as worktrees.** Each experiment is a Library ref branched from a pinned unit version. Merged or abandoned, both are kept. · AG/OPS · Library · refs · D5
- **I13. Claim-to-rule map.** Which quoted sentence or timestamp became which block or parameter. · AN · Library · idea record · D6
- **I14. One source, one home, by content hash.** Re-ingesting the same video hits the same record. · OPS · Library · source store · D6 D30
- **I15. Ambiguity blocks becoming a unit, never recording an idea.** · AG · QML check · D6
- **I16. Lineage for things that aren't units.** ML models, ensemblers, pods, workflows and mini apps get the same record. · AG/CR · Library · kinds · D13 D15
- **I17. Plain-Python units get lineage** by file hash plus an "outside standard" flag. Nothing is blocked. · CR · QML, Library · D6 D13
- **I18. Redacted import of the Hermes originals** (PKG, EXP, REC) into the repo, with credentials stripped (10 §6.2 warns they are there, CHECKED). · AN · repo · D1 D87
- **I19. The 359 NotebookLM sources** as the first intake once judging works (CHECKED 10 §2.8). · AN · workflows · D7 · *parked until the QMB door trades*
- **I20. Lineage graph view.** Typed edges, colour by stage, size by trades; click through to the detailed view. · CR/AN · Lab · D4 D5
- **I21. Analyst-lens skill.** Fixed queries over lineage and journals ("where do survivors come from?"). · AG/AN · skills · D7 D45
- **I22. One-idea fan-out grid.** Instrument × timeframe cells of one idea's children, with each cell's status. · AN · Lab · D34 D71

### B. Views, agents-first

- **I23. Three-tier disclosure.** An index line (one sentence, like a skill description), a preview card, a detailed view. One JSON object for agent and UI. · AG · Library, Lab · D4 D45
- **I24. Preview card fields.** Stage, origin, family, home markets, tries, grade, last-30-trades R sparkline, health, open proposals. · CR · Lab · D4
- **I25. Detailed-view tabs.** Journal sections, lineage, market map, test runs, calibration receipts, proposals, notes. · CR · Lab · D5
- **I26. The promotion page is the one human-first page.** · TR · Lab, Pods · D45 D74
- **I27. Handles, not dumps.** Agents get ids and pages and fetch detail on demand (paging exists, CHECKED 12 §1 row 7). · AG · tools · D45
- **I28. Proposal cards as typed objects.** Kind, evidence links, expiry, author model. He accepts or rejects; the reason is journaled. · AG · Copilot, Lab · D48 D49
- **I29. "Explain this unit".** A plain summary written by an agent, pinned to a version, regenerated on change. · AG/CR · Lab · D45

### C. Journals

- **I30. Journal in the OpenTelemetry shape.** Events, rollups, and a trade as a trace (signal → checks → order → fill → manage → exit). · OPS · node, QMB · journal schema · D25 D81
- **I31. Signal funnel.** Fire counts per block per window (10 §6.6). · AG/TR · QMB, node · D24
- **I32. "Seen but not taken" rows** with a typed reason (spread, session, max positions, guard, low strength, no offer). · TR · node · D24
- **I33. "Missed" rows.** It would have fired, but the unit was offline or the feed stale. Computed by replay afterwards. · OPS/TR · QMB · D24
- **I34. Single writer per section.** Agents get notes and proposals only, through a journal tool behind hooks. · AG · hooks · D23 D49
- **I35. Agent notes carry evidence links and an expiry.** · AG · journal · D49
- **I36. Unit SLOs from the exam baseline.** Trade rate, cut rate, slippage band, R band. Burn-rate alerts become OK / Watch / Alarm. · OPS · node, workflows · D25 D32
- **I37. Exemplars.** Every metric links to example trades. · OPS/AN · Lab · D25
- **I38. Journal sampling levels.** Events (default), every bar (on request), tick debug (time-boxed). · OPS · node · D30
- **I39. Point-in-time key per trade.** A join key into the market journal plus the MIS label version, never a copy. · OPS/ML · journal schema · D30 D31
- **I40. Market journal** per broker × account type × instrument × minute (12 §5). · OPS/TR · feed keeper, Library · D26 D31
- **I41. Router decision journal**, separate from the market journal. Every direction, its inputs and plan version; replayable. · OPS · router · D26 D81
- **I42. Guard journal.** Every block and stop, with level and reason, so automatic stops are monitored (Q3). · TR/OPS · node · D60 D74
- **I43. Family and portfolio rollups** as computed views, not stored copies. · AN · Lab · D33 D34
- **I44. WF3 reborn.** Nightly decay spotting, fortnightly action *proposals* (CHECKED 08 §2.1 for the old cadence). · AG · workflows · D32
- **I45. Market almanac.** Per instrument, a history of conditions (spread regime, volatility regime, session behaviour by month). · AN/TR · mini app · D27 D35
- **I46. Cost decomposition query.** "Gold fits my scalper but costs are high: broker or hour?" Spread by broker × hour × account type, plus the cheapest hour and broker for this unit. · TR/AN · Copilot skill · D29
- **I47. Cell map: where alpha lives.** Family × instrument × condition cells with deflated journal R, shown over time. · AN · Lab · D33 D34 D35
- **I48. Human-journal fields for bots.** Setup tag, deviation from the exam behaviour, an agent's post-trade review note. · TR · journal · D24
- **I49. Shadow evaluation.** Stopped units keep evaluating on paper so data keeps flowing (old rule, CHECKED 08 §2.1). · OPS/TR · node · D24 D32
- **I50. Counterfactual router value.** What the router suggested vs what the unit did, to measure the router itself. · AN · router, QMB · D58
- **I51. Journals as monthly Parquet partitions** with a Library card per unit: hot on the PC, full on server and bucket. · OPS · Library · D30 D80
- **I52. Pod designs re-weighted from journals**, in research only. · AN · Lab, Pods · D16 D34
- **I53. Funding, roll and swap events** as both a market fact and a unit cost line. · TR · journals · D9 D26
- **I165. Black-box flight recorder.** On any guard stop, dump the last minutes of feed and decisions. · OPS · node · D25 D42
- **I177. Tail sampling.** Keep every losing trade's full trace and sample the winners. · OPS · journal · D30 · *option*
- **I178. Broker SLA.** Measured spread and slippage vs advertised, per hour, as evidence for choosing brokers. · TR · market journal · D29 D63

### D. Router

- **I54. Router never in the trade path.** · TR/OPS · node · D54 D59
- **I55. The router directs extra traffic only.** New markets, sessions and look-alikes arrive as offers with a time limit. A unit's home market is never the router's to give or take. · TR · router · D53 D55
- **I56. Depth-of-information feed.** Per-instrument condition labels ("this market is like this") published on the bus. Units may read them. · TR/ML · MIS · D58 D66
- **I57. Offer object.** (unit, market, session, why, evidence grade, expires). The unit accepts or ignores, and that is journaled. · AG · router · D55 D58
- **I58. `router_mode` per unit:** ignore / advise / follow-offers; default advise. · CR · unit spec · D12 D54
- **I59. Declared "MIS missing" behaviour**, tested in QMB with and without the router feed. · TR/AG · QMB · D54 D66
- **I60. Load-balancer algorithm menu for offers.** Weighted round robin by proof; least connections = fewest correlated units engaged; least cost (the least-response-time analogue); consistent hashing = affinity; power-of-two choices = offer to the less correlated of two; resource-based = liquidity; plain round robin = evidence rotation; hybrids. All UI-editable. · TR/OPS · router · D55
- **I61. A default hybrid.** Affinity first, then power-of-two by correlation, weighted by proof. An option, not a choice. · TR · router · D55 D57
- **I62. Correlation ledger in the router.** Unit P&L and signal correlation, instrument correlation, consensus/disagreement per instrument. Published as information. · AN · router · D57
- **I63. The ledger as one shared Library object**, read by the router (direction) and the pod (limits). · OPS · Library · D20 D57
- **I64. Two caches by lens.** Unit lens = seconds-scale live facts from the local feed. MIS lens = a slow plan with fresh/hard expiry, used only for offers. · TR/OPS · router · D67 D79
- **I65. Plan expiry stops new offers only**, never trading inside the envelope (re-reads 09 §2.6). · TR · router · D54 D67
- **I66. Router split.** The planner sits wherever the Library is, the fast half on each node beside the feed, the archive on the storage machine. Same code on one machine. · OPS · node, PC · D76-D78
- **I67. The router plan as a Library object** (`router-plan`, versioned, fingerprinted) that nodes pull: his R2 pattern. · OPS · Library · D78 D80 D82
- **I68. Several nodes.** One planner, per-node plan slices (like xDS); instruments sharded to nodes by consistent hashing. · OPS · router · D83
- **I69. Per-instrument MIS models with pooled training.** A class-level model shares strength; each instrument gets its own fit. · ML · MIS · D84
- **I70. MIS model registry** with lineage and training windows, as a Library kind. · ML · Library · D84
- **I71. Look-alike markets from a pair-similarity vector** (CHECKED 10 §2.11). · TR/AN · router · D27 D58
- **I72. Router as a recommender:** "units like you did well on X". · AN · router · D58 · *parked until journals exist*
- **I73. Unit consensus as depth info.** Run the T6 study first (CHECKED 11 §3). · ML · router · D57 D58 · *study*
- **I74. Pub/sub broadcast, never a call per unit.** · OPS · bus · D56
- **I75. A visible, non-critical router heartbeat.** Its absence is a yellow light. · OPS · node · D59
- **I76. Re-label round-1 router ideas.** Health checks, draining, ejection and canary seats (07a §3.3) become information or guard rules, never router switches. Same for 09's gate. · AG · docs · D52
- **I77. Every MIS label stamped labeler@version** so QMB replays it exactly. · ML · MIS · D59 D66
- **I180. Admission envelope.** His click admits a unit with a set of markets, sessions and brokers. The router directs live only inside it. Outside it, offers become paper-sibling proposals. *Born in party round 13.* · TR/AG · Pods, router, QML · D53 D55 D71 D74

### E. Feed pool

- **I78. One feed keeper per broker connection.** One subscription per symbol, fanned out over a local bus to units, guards, the router and the recorder. · OPS · node, PC · D65
- **I79. Last-value cache plus warm start from the recorder.** · OPS · node · D65
- **I80. The recorder writes the Parquet QMB reads.** · OPS/TR · Library · D10 D65
- **I81. Connection lease vs one cTrader app per machine.** Two options. · OPS · node · D63 D65
- **I82. Derived feeds at the keeper.** Spread ratio (SQS), volatility state, session state as streams: a feature store. · ML/OPS · feed pool · D60 D61 D66
- **I83. Guards read the pool directly.** · TR · node · D60
- **I84. A per-symbol spread baseline** by hour of week, so the SQS for every instrument comes free. · TR · feed pool · D61
- **I85. News keeper.** Free sources, scraped in order, deduped, timestamped. The kill switch reads a local calendar cache. · TR · node · D60 D62
- **I86. Platform capability registry.** What each platform's feed carries, its limits and connection rules. Units declare needs, and `check` names any mismatch plainly. · AG · QML, node · D9 D63
- **I87. QMB replays through the same bus interface**, so unit code is identical in backtest, paper and live. · AG/TR · QMB · D13 D37
- **I88. Streaming data-quality flags** (spike, crossed spread, stale) on the bus. · OPS · feed pool · D10
- **I89. Venue capacity planner.** Connections needed for N units (Hyperliquid 1,000 subscriptions per IP, Binance 1,024 streams per connection, cTrader no symbol cap; CHECKED 12 §4.1). · OPS · node · D63 D65
- **I90. Mini apps and plain Python read the same pool.** · CR · mini apps · D13

### F. Account guard and pod

- **I91. Option A: pod = BMS = account guard + shared budget + correlation limits**, one per account. · TR · Pods · D18 D20
- **I92. Option B: a fixed guard per account** (local, an unremovable floor), with pods as pluggable templates above it. · TR/AG · Pods · D20 D40
- **I93. Option C: the guard as a locked block inside every pod template.** A copilot may remake the rest. · AG · Pods · D20 D40
- **I94. Pod interface:** `allow_new_risk(unit, R, context) → yes/no + reason`. It never resizes; every call is journaled. · AG · Pods · D20
- **I95. Pod design vs pod instance.** Design in the Lab, tested in QMB; instance on the node with live state; same code. · TR · Lab, node · D16
- **I96. The kill-switch ladder as guard states.** GREEN to BLACK, escalation automatic, de-escalation human only (CHECKED `grounding/02` §1.7). · TR · node · D74
- **I97. Prop-firm rule pack as guard presets.** · TR · Pods · D20 · *parked unless he trades prop*
- **I98. Pod in QMB.** A portfolio backtest under a pod design, with ΔBookUtility per unit. · AN · QMB · D16 D44
- **I99. Calibration receipt.** Every self-configuration writes which number moved, from which journal window, by which rule, inside which range. The maths stays in the risk session. · TR/AG · journal · D19
- **I100. Guard independence drill.** Unplug the router, the MIS and the PC during a node self-test; the guard still stops. · OPS · node · D59 D60

### G. QMB

- **I101. LEAN-shaped CLI plus an MCP door:** init, backtest, optimize, report, data, research. · AG · QMB · D36 D37
- **I102. Jesse features:** multi-symbol × multi-timeframe routes, simple syntax, Monte Carlo, an optimise mode. · AG/CR · QMB · D36
- **I103. Old pass numbers as warn-only defaults** (CHECKED 08 §0). · AN · QMB · D8 D42
- **I104. Recover what was dropped:** parity replay, MAE/MFE, slices by session and regime, scenario stress, a per-unit paper window (CHECKED 08 §0). · TR · QMB · D8
- **I105. Windowed reader** (the lookback fix, CHECKED 12 §1). · OPS · QMB · D11
- **I106. Any start date**, with an honest dataset answer and the source seam on the card. · AN · QMB · D11
- **I107. Plain-Python adapter.** Any class with `on_bar` or `on_tick` runs, LEAN style, and is counted as tries. · CR · QMB · D13 D15
- **I108. ML in QMB.** Walk-forward retraining inside the backtest, versioned model artifacts. · ML · QMB · D15 D84
- **I109. Result identity and "stale, not false" re-runs** (CHECKED 10 §2.10). · AG · QMB · D30 D72
- **I110. Router and pod replayable in QMB**, as pure functions over logged inputs. · AG · QMB · D54 D59
- **I111. Instrument spec for every class by default:** funding, roll, swap, sessions, contract size. · TR · QMB, QML · D9
- **I112. Crypto and perps replay** (trades plus funding); futures continuous and per-contract. · TR · QMB · D9
- **I113. Agent-readable report.** JSON first, short text second, handles to trades. · AG · QMB · D37 D45
- **I114. Hook: shell-made backtests can't reach journals.** Only the QMB door writes results. · AG · hooks · D23 D37
- **I115. Research notebooks over QMB results** for creators. · CR · Lab · D13

### H. Judging

- **I116. The judging skill.** SKILL.md plus deterministic scripts plus hooks. It calls QMB and outputs a report in parts (no single score) and a proposal card. · AG · skills · D41 D47
- **I117. Grades, not pass/fail:** uncalibrated → screened → backtested → stressed → sealed → paper → live. Numbers warn. · AN · judge · D42
- **I118. Paper sequence, strict:** backtest → stress → sealed → paper (minimum trades and weeks) → his click. · TR · node · D44
- **I119. Paper sequence, parallel:** paper starts when stress passes and runs beside the sealed check. · TR · node · D44
- **I120. Paper sequence, sibling fast lane:** siblings of live units paper for less, judged against the parent's baseline. · TR · node · D44 D71
- **I121. Paper as shadow live** on the node's real feed, with the demo fill recorded beside it. · TR · node · D44
- **I122. Judge along the unit's real sizing path** (session capital, house money) and at flat R, with a block-bootstrap ruin probability. · TR/AN · judge · D43
- **I123. Checks J1-J10 from the papers** (CHECKED 11 §4). · AN · judge · D39 D46
- **I124. Prop-firm phases as the shape of paper:** challenge → verification → funded with scaling. · TR · judge · D42 D44
- **I125. Live-vs-exam-baseline compare** (missing in QMB, CHECKED 03 row in STATE). · AN · QMB · D44
- **I126. Marginal value to the pod** (ΔBookUtility) in every report (CHECKED 10 §2.10). · AN · judge · D34 D43
- **I127. Judge report in both views.** Grade plus three numbers in the preview, every part in the detailed view. · CR · Lab · D4 D48
- **I128. The judge never promotes.** Proposals stop at his click; the only automatic step is a guard stop, logged. · TR · judge · D74

### I. Finding vs filtering

- **I129. Two workflow families.** Finding is cheap and wide; filtering counts the tries. · AG · workflows · D90
- **I130. Templates T1-T6** (CHECKED 11 §3). · AG · workflows · D88
- **I131. ML finders.** LightGBM or transformer models as unit kinds, not only LLM-written rules. · ML · Lab · D15 D89
- **I132. Category-balanced seeding plus a frequent-pattern "avoid" list.** · AG · workflows · D89
- **I133. The budget grows only on progress**; no cap. · AG · workflows · D12
- **I134. The fail branch as a finding workflow** with sealed proof (CHECKED `seeds.md`, funnel). · AG · workflows · D34
- **I135. Manual-trades miner.** His own discretionary trades, if any, become idea records. · CR/TR · workflows · D6 · *parked*
- **I136. Cheap model for loops, strong model for cards and reviews** (CHECKED 11 §2.3). · AG · workflows · D23
- **I179. Hooks write trajectory events automatically** (a PostToolUse hook logs "built", "tested"). · AG · hooks · D6 D23

### J. Unbounded

- **I137. No `lookback_max` anywhere**; default start 2020-03-01 per run kind. · AN · QMB · D11
- **I138. Unit kinds are first-class:** QML graph, QML hooks, plain Python, ML model, ensembler. Same journal, same judge. · CR · QML · D13 D15
- **I139. Scalper types are tags and templates.** "custom" is always valid. · CR · QML · D85
- **I140. An open dictionary.** Anyone adds entries; collisions become aliases; never a gate on code. · CR · QML · D86
- **I141. Same check, two modes.** Refuse in agent mode, warn in human mode. · AG/CR · QML, hooks · D14 D23
- **I142. An "outside standard" lineage flag instead of a block.** · CR · Library · D12
- **I143. Pods, routers and journal views as templates with contract tests**, so a copilot can remake them. The guard floor is the exception. · AG · Copilot · D40
- **I144. Reword "refuse complete corpus download"** (FM-5, DEC-0051) in the doc pass (CHECKED 12 §1 row 4). · OPS · docs · D11

### K. Genetic moves

- **I145. Transplant operation.** One component (confirmation, exit, filter) moves from family X to Y through named ports, with a `transplanted-from` edge, counted as a try in Y. · AG · QML · D34
- **I146. Block value board.** Which blocks add value in which families, from comparisons already run, without ablating every part. · AN · Lab · D34
- **I147. Three operators:** crossover (two parents), mutation (one step), transplant. Each is a lineage edge. · AG · workflows · D34
- **I148. Named ports** (setup, entry, invalidation, exit, regime) so transplants are mechanical (CHECKED 10 §2.3). · AG · QML · D34
- **I149. Python donors.** An agent rewrites a plain-Python part into ports; the original stays. · CR/AG · workflows · D13 D34
- **I150. Hybrid and tribrid names** in the family tree. · CR · Lab · D34
- **I151. Record the overrule.** 07 killed genetic crossover; his 26 Aug idea revives it as transplant. · AG · STATE · D68
- **I173. Horizontal vs vertical inheritance** counted apart in yield stats. · AN · Lab · D34
- **I174. Fitness landscape view.** A family's cells shown so plateaus (robust) stand apart from spikes (overfit). · AN · Lab · D33 D42
- **I175. Linkage warning.** Blocks that always appear together can't be scored apart. · AN · Lab · D34
- **I176. Phenotype = same bet.** Two units with different code but the same journal behaviour count as one bet. · AN · Pods · D57

### L. Data and Dukascopy

- **I152. Back up the 10 GB of `bi5` ticks now** (CHECKED 12 §2.1: irreplaceable at that cost). · OPS · storage · D10
- **I153. Several sources per class.** Dukascopy for depth, the broker for costs, HistData to cross-check, Binance and Bybit bulk for crypto, Databento or FirstRate when paid data is needed. · TR · data · D10 D63
- **I154. Record our own history from day one** through the pool's recorder (also fixes Hyperliquid's ~5,000-candle limit). · OPS · node · D10
- **I155. The 17-check data-quality list** (CHECKED 12 §3) at partition write, shown on the dataset card. · OPS · QMB · D10
- **I156. Dukascopy fetcher settings:** headed Chromium, slow, retries on, retry on empty, flats on. · OPS · data · D10
- **I157. Keep the `internal-only` licence tag; never redistribute.** · OPS · data · D10
- **I158. Cross-source drift monitor.** Dukascopy vs broker bars; the gap becomes a cost correction. · TR · market journal · D10 D26

### M. Local first and machines

- **I159. Placement manifest.** Each component declares its roles (planner, fast router, keeper, recorder, QMB, Library). Machine profiles assign them, and one PC can hold them all. · OPS · node, PC · D76 D82
- **I160. Same compute, different positions.** The storage machine holds archives, the PC caches, the node holds live. · OPS · Library · D82
- **I161. Node budget.** Units per node; extra units spill to a second node by instrument shard. · OPS · node · D83
- **I162. PC-only mode is the test bed.** Paper and research run fully on the PC before any server. · OPS · all · D76
- **I166. Weekly chaos drills on demo:** kill the router, drop the feed, take the PC offline; journal the outcome. · OPS · node · D59

### N. Unit life

- **I163. Unit life as a state machine with journaled transitions:** idea → built → checked → backtested → stressed → sealed → paper → (his click) → live → watched → stopped (automatic, guard) / retired (his click) / rehab child. · TR/AG · QML · D3 D74
- **I164. Retirement keeps everything** (a fossil). · AN · Library · D3 D11
- **I168. Units never talk to each other.** All coordination goes through the pod and the guard, which keeps units independent. · TR · node · D54

### O. Library and archive (from the analogy round)

- **I169. Content-addressed everything** (units, plans, datasets, journals), so any result can be rebuilt. The Library already uses fingerprints (CHECKED 12 §5.3). · OPS · Library · D5 D80
- **I170. An accession register.** Every intake gets a number, a date and a provenance chain. · AN · Library · D6
- **I171. "Respect des fonds".** Keep one source's outputs together for yield analysis. · AN · Library · D7
- **I172. Deaccession = mark, never delete.** · AN · Library · D5

(I167, a daily "market weather report" mini app, merged into I45.)

---

## 6. Open questions only he can answer (7)

Each has options. None is pre-decided. Ask them in plain words, one at a time, after the design-idea studies.

**Q1. Account guard and pod (D17, D18, D20).** His lean is that the pod is the BMS.
- (a) **One object:** pod = BMS = account guard + shared budget + same-bet limits, one per account (I91).
- (b) **Two layers:** a fixed guard per account that no one can remove, with pods as templates above it that a copilot may remake (I92).
- (c) **One shape, locked block:** every pod template carries the guard as a part that can't be edited (I93).

**Q2. What his click admits (D53, D71, D74).**
- (a) One unit on one market.
- (b) An **envelope** he ticks (markets, sessions, brokers). The router directs live only inside it; outside becomes a paper-sibling proposal (I180).
- (c) Anything the unit's own conditions allow.

**Q3. With the router off (D54).**
- (a) Units trade their home market only.
- (b) Units trade the whole admitted envelope on their own conditions.
- (c) Units keep following the last offers until those expire.

**Q4. Units reading MIS output (D66, against the 20 Oct seed).**
- (a) Never inside a unit's rules (the seed).
- (b) As optional context, with a declared fallback when it is missing, tested in QMB both ways (I56, I59).
- (c) Freely, like any other feed.

**Q5. The paper sequence (D44).**
- (a) **Strict:** paper only after the sealed check, for every unit (I118).
- (b) **Parallel:** paper starts when stress passes (I119).
- (c) **Sibling fast lane:** siblings of live units paper for less, judged against the parent (I120).

**Q6. His unfinished thought (D27, D35).** Which is closest?
- (a) A market almanac: each instrument's conditions over time (I45).
- (b) A cell map: where alpha lives (family × instrument × condition) and how it moves (I47).
- (c) Cost-aware placement: the best broker and hour for each unit (I46).
- (d) Something else, which he writes himself.

**Q7. Paying for data (D10, D63).** Money, so his call.
- (a) Free only: Dukascopy, HistData, Binance bulk, broker history, plus our own recording.
- (b) Add Databento Standard ($199 a month, CHECKED 12 §2.2) when a futures unit is real.
- (c) Add Tardis for perps depth when a perps unit is real.

Also for his awareness, not a question: Dukascopy's terms forbid bots and databases (CHECKED 12 §2.1); QMX's stance is personal use. A bigger local disk is the only full fix for "local first" with tick archives (CHECKED 12 §5.2).

---

## 7. Path

1. **Next (already planned in STATE):** design-idea studies with `improve-codebase-architecture`, `codebase-design`, `domain-modeling` and poteto-mode on five subjects:
   - the router as an advisory publisher plus the envelope (I55-I65, I180);
   - the feed pool (I78-I90);
   - unit independence (P2, X1, X13);
   - the journals (I30-I53);
   - the guard with the pod (I91-I100).

   Ideas and options only, as he ordered.
2. **Then** the seven questions above, explained first, one at a time.
3. **In parallel and unblocked:** the risk-and-sizing session (`HANDOFF-RISK-SIZING.md`) owns D19, D50, D51 and D75. Its calibration receipt (I99) should match the journal shape.
4. **Research gaps to close, not to ask him:**
   - what "MTFA" means and what came of it (D84);
   - whether two live cTrader connections under one app actually fail (X10);
   - why the old QMB features were dropped, traced to a commit or ruling (D8).
5. **Safe now, needs no design:** back up the 10 GB of `bi5` ticks (I152). Moving or copying his files needs his go.
