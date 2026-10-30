# 19: Grounding C, the old system

Written 2026-10-30 by grounding agent C. Read and record only. No design, no recommendation.

## How to read this

**Labels.**
- **CHECKED**: I read it at the cited path and line on 2026-10-30.
- **INFERRED**: my reading or join of checked facts.

**Scope.** This file builds on four earlier recoveries and records only what they missed or got wrong:
- `G01` = `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\grounding\01-old-system.md`
- `G09` = same folder, `09-original-design-recovery.md`
- `R08` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\research\08-old-qmx-testing-and-decay.md`
- `R10` = same folder, `10-hermes-stats-goldmine.md`

Where those files already cover a point correctly, this file says "covered" and gives the pointer. It does not repeat them.

**Short paths.**

| Alias | Path |
|---|---|
| `V` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` (old vault; read only, nothing run) |
| `GPTR` | `V\07-Source-Material\gpt-trading-algorithm-research.md` (the April GPT conversation; operator turns follow `# you asked`) |
| `BRAIN` | `V\.brain\` (the July 2026 second brain: braindumps, decision ledger, persona roster) |
| `QMLD` | `V\02-Components\00-QML-shared-library\` |
| `PA` | `V\bmad-docs\planning-artifacts\` |
| `BS` | `V\bmad-docs\brainstorming\brainstorming-session-2026-04-28-125147.md` |
| `ST` | `C:\Users\Mubarak\Desktop\Stats\` |
| `GEN` | `ST\.hermes\orchestration\transcripts-lineage\20260824_121737_86f88c-friendly-greeting.md` |

**Three eras of the old system.** The sources describe three different QMX designs. Mixing them causes most misreadings. CHECKED for each era's source; the split is INFERRED.
1. **April to May 2026, the vault era.** Slots, multiplier stack, MIS sensor stack, WF1 to WF3, departments, QML BotSpec (`V\02-Components`, `PA`, `GPTR`). The pre-crash code (`src/router/…`) is known only through `GPTR`.
2. **July 2026, the Book/BMS era.** The GitBook core: books, BMS desks, seven doors, treasury cycles, examination engine. Also the July agentic redesign (`BRAIN`).
3. **August 2026, the STRATS era.** The Hermes-built strategy knowledge library (`ST`).

---

## 1. Workflows

### What existed

**Covered elsewhere.** WF1, WF2 and WF3 stage lists, cadences and the WF3 D0 to D6 pipeline are in `G09` A.10 and `R08` §2.1. Not repeated.

**Older numbering, with a real WF4.** `V\05-Deployment\02-backend-node.md:67-72` shows a different workflow set: "WF1 — AlphaForge (variant generation)", "WF2 — Paper-trading gate", "WF3 — Bot improvement loop", "WF4 — Ecological + feature mutation". CHECKED.
- The old code named two flows, `AlphaForgeFlow` and `ImprovementLoopFlow` (`GPTR:7144`, `GPTR:7799`). CHECKED.
- The July braindump records the operator saying WF4 "only existed in the crashed-laptop version" (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:41`). CHECKED.
- The vault then ruled WF4 a "phantom" on 2026-05-01 and folded its mutation work into WF2 and WF3's mini-WF2 (`V\02-Components\07-bot-registry-and-lifecycle.md:160`). CHECKED.
- In April the operator dictated "in wf3 and wfo we brought about something … ecological" (`GPTR:19153`). CHECKED. INFERRED: "wfo" is a dictation of "WF4".

**Workflow entry points and the deprecated pair.** `V\02-Components\14-agentic-system\02-floor-manager.md:137-147`. CHECKED.
- WF1 starts from an "Opportunity identified by Trading or Portfolio" and ends when backtest reports are archived and a `WF1_COMPLETE` mail goes out.
- WF2 starts from three triggers: WF1's evidence handoff, a WF3 rehab token, or an operator diagnosis request (A4).
- WF3 starts from a "Dead-zone batch trigger".
- Two more workflows existed and were retired: `WF_RISK_SCAN` (folded into Portfolio's standing duties) and `WF_PORTFOLIO_AUDIT` (kept as a scheduled department operation).

**Deterministic flows beside the agent workflows.** `V\04-Integration-Flows\03-integration-flows.md`. CHECKED.
- Flow 1, tick to order (line 9). Flow 2, trade close to demotion (58). Flow 7, journal sync to cold storage (224). Flow 8, a daily economic-calendar pull (251). Flow 9, dead-zone sync (288).
- These ran without agents. WF3 read what Flow 7 and Flow 9 delivered.

**Throughput the operator expected.** CHECKED, all operator words in `GPTR`.
- "wf1 producing around 80 strategies" (`GPTR:19153`).
- "in a day … let's say 20 bots and that puts them into paper trading" (`GPTR:19556`).
- Hosting "the ability to handle 200 bots" (`GPTR:115`).
- In August: "40 strategies total in the entire QMX" as a large number (`GEN:1431`).

**The WF1 pipeline in the operator's words.** "most of such a scan come from youtube or articles … we write a trd for the bot archetype then uh the code is written … vanilla is basically the code as it comes from the source … when we strip by things that the system already handles … spiced is like the logic plus the ctrader article logic" (`GPTR:1400`). CHECKED.

**WF2 complexity control.** CHECKED.
- GPT's April design: "fitness = robustness + generalization + interpretability + execution realism − complexity penalty" (`GPTR:19016`).
- WF2 was to track feature count, dependency count, active conditions, regime and session gates, mutation depth, rule-chain length and interpretability cost, against "mutation sprawl" (`GPTR:19338-19353`).
- The QML plan kept only a stored `complexity_score` (0 to 100) and `complexity_profile_version`, computed outside QML (`PA\qml-architecture.md:235`). A runtime tag `complex` marked bots above a threshold (`PA\qml-types-catalogue.md:3955`).

**WF2's biggest named risk.** The operator: "the biggest risk in wf2 is the false diagnosis so how do we counter the false diagnosis" (`GPTR:19153`). He first wanted a verifier, then settled on "one primary diagnosis agent and one reviewer agent" from another department, talking by mail (`GPTR:19815`, `GPTR:19934`). CHECKED.

**The scenario engine.** The operator named a library for synthetic data: "i wanted to use outlines which is a Python library … for synthetic data generation" (`GPTR:19153`). CHECKED. GPT answered that scenarios "should not create new bots" but "create stress evidence" (`GPTR:19024-19025`). CHECKED.

**July ruling on workflows.** "Workflows: full redesign from scratch, designed AFTER scaffolding", with the WF2-like loop flagged for earlier attention; n8n named for "boring deterministic plumbing" (`BRAIN\decisions\decision-ledger.md:46-52`). CHECKED.

### What earlier recoveries missed or misread

- `G09` A.10 and `R08` §2.1 call WF4 a phantom. The vault did. But the operator remembered a real WF4 in the lost code, and the deployment doc names it "Ecological + feature mutation". CHECKED as above. INFERRED: "phantom" was a documentation verdict, not a fact about the crashed code.
- Neither file records that WF3 once meant "Bot improvement loop" and WF2 once meant "Paper-trading gate". Any old text that says "WF3" may mean either. CHECKED (`02-backend-node.md:69-70`).
- Neither file lists the deprecated `WF_RISK_SCAN` and `WF_PORTFOLIO_AUDIT`, or WF2's three entry triggers. CHECKED.
- `R08` §1.1 notes the GPT talk wanted synthetic data. It does not record that the operator named `outlines` for it. CHECKED.

---

## 2. MIS, sentinel, router, auction and routing matrix

### What existed

**Covered elsewhere.** The vault sensor stack, ensemble weights, RMF, premium sessions, session windows, warm-up and the slot auction score are in `G01` §5.2 and §6. The router package, the RMF and the young/mature specialists are in `G09` A.1 and A.3. Physics is in `G09` A.12 and Job D. Not repeated.

**The operator's own definition of the MIS (April).** "the market intelligence basically deals with news trading stoppage uh session monitoring and routing" (`GPTR:115`). His first message: "a sentinel okay which delegates bots to market or something like that" (`GPTR:5`, already in `G09`). CHECKED.

**Bots read the MIS in the vault era.** CHECKED.
- The vault MIS diagram sends the snapshot to "Signal Evaluators / Bots" as well as to risk, SL/TP, the kill switch and the journal (`V\02-Components\04-market-intelligence-service.md:36`).
- A `BotInputAssemblerFactory` gave each bot three information views: `raw_broker_view`, `qml_feature_view` and `mis_context_view`, "so bots are not forced to rely on a single possibly-biased derived stream" (same file, 557-570).
- The single-computation rule: no bot computes regime state or microstructure quality locally; all read the one snapshot (same file, 13-15).
- The operator in April: "market sentinels so that bots themselves have market sentinels that are complementary" (`GPTR:949`).
- STRATS in August: a strategy graph "can declare `requires: mis.liquidity-regime.v3`, `mis.session-state.v2`". "MIS provides the information; the bot decides how to use it." (`GEN:939-968`). The MIS belongs to things that are shared, expensive, market-state, needed in exam and live, and worth central versioning. Cheap, family-specific, proprietary or fast-changing logic stays in the bot.
- The operator's August reply: "MIS is like centrally used and you kind of have no control over it. I just wanted you to know that it exists. Yeah, just exists, it's a constant." He did not want MIS versions left running side by side (`GEN:1431`).

**What the live sentinel actually ran (pre-crash code).** CHECKED from code scans pasted into `GPTR`.
- `src/router/sentinel.py:52` built the "authoritative RegimeReport from Chaos + Ising Regime + News, with optional HMM shadow/hybrid overlays" (`GPTR:14244-14246`).
- The `EnsembleVoter` (`src/risk/physics/ensemble/voter.py`) existed but was "NOT wired into the live Sentinel tick path — live path uses HMMRegimeSensor directly" (`GPTR:6560`, `GPTR:6602`). INFERRED: the two scans describe different points in time; either way the vault's weighted ensemble never ran live.
- Per-timeframe sentinels were "external and mature" in `multi_timeframe_sentinel.py:132`, read directly by `engine.py:654` and `commander.py:1272` (`GPTR:14247-14249`).
- `NewsSensor` emitted a fourth state vocabulary: `SAFE / PRE_NEWS / KILL_ZONE / POST_NEWS` (`GPTR:14250-14251`).
- The `src/router/` package held far more than routing: `engine.py`, `commander.py`, `sentinel.py`, `bot_manifest.py`, `governor.py`, `enhanced_governor.py` ("Kelly + house money"), `dpr_scoring_engine.py`, `bot_tag_registry.py`, `variant_registry.py`, `session_detector.py`, `trade_logger.py`, `trd_converter.py`, `routing_matrix.py` (`GPTR:7064-7078`, file-name counts across `GPTR`). INFERRED: the old "router" was the bot-management core (rating, governor, registry, auction, sessions), not a thin dispatcher.
- Two DPR engines existed (router and risk); only the router one published to Redis, and the router was ruled canonical (`GPTR:5540-5559`).

**How a bot actually got a slot, in the operator's words.** "with a base equity of $200, we're going to have three slots, which the … other bots in the pool fight for … the bot that actually gets the setup first is the one that goes into our slot" (`GPTR:19556`). CHECKED. The vault later wrote a scored auction at each window boundary (`G01` §5.2). INFERRED: the operator's model was first-setup-wins inside a pool; the scored auction was the vault's formalisation.

**Session specialists in the operator's words.** "these bots are in a pool so the bots with that session id when the session id comes into play … they don't go into the slots originally but they still compete … this bot now knows okay that my session is live so it starts better scanning" (`GPTR:19815`). CHECKED. INFERRED: in his model the bot itself knew its live session.

**A third correlation and conflict point: the Intent Aggregator.** CHECKED (`QMLD\02-QML-bridges.md:74-100`; `QMLD\01-QML-domain-types.md:385-404`; `BS:167`, decision D9).
- It sat between the bots' safety hooks and the risk bridge. It gathered every trade intent on one symbol inside a window of at most 50 ms.
- Rule 1: opposite directions on one symbol; the higher `confluence_score` survives.
- Rule 2: total `proposed_sl_pips × volume` above a per-symbol cap; the lowest-priority intents drop.
- Rule 3: intents on highly correlated symbols that push portfolio correlation over a threshold; the marginal ones drop.
- Losers go back to the bot pool for the next tick. They are not demoted, because "conflicts are routine and not a performance signal".
- It fails open, since risk clamps still apply.
- Origin: the operator's April point that "two different bots can be handling the same pair" (`GPTR:115`).

**The ensembler.** Weights and rules are covered in `G01` §6. Not repeated.

**July.** The GitBook core made the MIS "information-only (L6)" and split it into MIS-Live and MIS-Archive, with snapshots "computed once per labeler×version×params×pair×resolution" (`BRAIN\entities\qmx-new-core.md:22-23, 57-59`). RMF with declared weights went on the dead list: "declared weights are opinions wearing math" (DEC-0018, `BRAIN\concepts\dead-list-and-scope.md:17-19`). Session windows as trading authority also died (DEC-0025, same file, 34-35). CHECKED.

**Weekly market selection on evidence (July).** "If we say we are not trading this pair this week, it has to be backed by a lot of evidence" (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:74-75`). The point of the Prime Market Terminal study was that "book values and metrics get set/adjusted on evidence, not hardcoded whim" (same file, 67-77). CHECKED.

### What earlier recoveries missed or misread

- `G09` A.1 and Job B item 4 record that bots may not read the MIS today (DEC-0204) and that on 20 Oct "bots never read the MIS in their rules". Neither records that in the vault era the snapshot went to bots, that bots had an MIS context view, that the operator wanted bot-level complementary sentinels, or that STRATS let a strategy declare MIS dependencies. CHECKED as above.
- `G09` A.12 says "the live path was regime from OHLCV + Ising features". The fuller scan says Chaos + Ising + News, with HMM only as shadow or hybrid, and the ensemble unwired. CHECKED.
- `G01` G20 lists three kill-switch vocabularies. The old code had a fourth (`SAFE / PRE_NEWS / KILL_ZONE / POST_NEWS`). CHECKED.
- No earlier file records the Intent Aggregator. It is the old system's only per-tick, cross-bot correlation control. CHECKED.
- `G01` §5.2 describes the auction score but not the operator's first-setup-wins slot model. CHECKED.

---

## 3. Tagging and registry

### What existed

**Covered elsewhere.** Lifecycle tags (`post_wf1` to `retired`), `SessionPerformanceProfile`, young and mature specialists and the July wiki's "pair/session overlap" panel are in `G09` A.3 and `R08` §2.1.

**A bot could carry many instruments.** CHECKED.
- `BotSpec.symbol` was the primary instrument. `BotSpec.symbol_scope` was "All instruments the bot can trade (for multi-symbol variants)" (`V\02-Components\07-bot-registry-and-lifecycle.md:31-32`; `QMLD\01-QML-domain-types.md:77-78`).
- `BotSpec.sessions` listed eligible session windows; empty meant all (`QMLD\01-QML-domain-types.md:80`).
- `ECOLOGICAL` mutation could assign "New symbol or timeframe" (`V\02-Components\07-bot-registry-and-lifecycle.md:158`, already in `G09` A.4).

**A bot declared the market conditions it was built for.** `capability_spec` = "Machine-readable declaration of what market conditions this variant is designed for; consumed by the agentic system to rank candidates for given regime/session combinations" (`V\02-Components\07-bot-registry-and-lifecycle.md:44`). CHECKED.
- In the QML types this became composition rules: `required_quality_floor`, `disallowed_feature_families`, `dependencies`, and `compatibility_rules` with a predicate over "archetype, timeframe, session, etc." and an effect of `BLOCK | WARN | REQUIRE` (`QMLD\01-QML-domain-types.md:169-200`). CHECKED.
- `EvaluationProfile` carried a minimum trade count, a session-window sample requirement and a "regime-coverage requirement" (`V\02-Components\07-bot-registry-and-lifecycle.md:51`). CHECKED.
- The old code's `bot_tag_registry.py` was reviewed for "compatibility rule patterns" (`GPTR:7067`, `GPTR:7630`). CHECKED.

**Two tag layers.** CHECKED (`PA\qml-types-catalogue.md:3941-3960`; `PA\qml-protocols-catalogue.md:2980-2982`).
- Compile-time tags on the BotSpec: `vanilla`, `spiced`, `session_specialist`, `regime_specialist`.
- Runtime tags on the registry record: `probation`, `cb_active`, `under_review`, `complex`.
- Feature modules had their own affinity tags: `orderflow`, `regime-sensitive`, `auction`, `scalper`, `orb`, `session-aware`, `confirmation`, `filter`, `exit` (`PA\qml-types-catalogue.md:3916-3932`).
- Mutation types beyond feature and ecological: `SESSION_SPECIALIZATION`, `SESSION_FILTER_REFINEMENT`, `REGIME_SPECIALIZATION` (`PA\qml-protocols-catalogue.md:2988-2995`).

**No pair tags.** No tag vocabulary names an instrument. Instruments lived only in `symbol` and `symbol_scope`. CHECKED (tag tables above). The registry query model filtered by "archetype, session, tier, account_mode" for slot candidates, not by symbol (`V\02-Components\07-bot-registry-and-lifecycle.md:205`). CHECKED.

**Routing to demo was a registry field.** `account_mode` (`LIVE | DEMO`) was the "Source of truth for routing decision in the broker adapter" (`V\02-Components\07-bot-registry-and-lifecycle.md:65`). CHECKED.

**STRATS (August).** "Do not fork per market. Forex, crypto spot, and prop-firm constraints are tags on strategies" (`ST\dictionary\README.md:19-21`). The `strategies` table has one `market` column; pair, timeframe and session sit on each role binding (`ST\schema\strats.sql:37-58`). CHECKED.

**Preferred vs hypothetical markets.** No vault, GPTR, BRAIN or Stats text describes a per-bot list of untested look-alike markets. CHECKED by grep for "hypothetic", "preferred", "look-alike". This confirms `G09` A.3.

### What earlier recoveries missed or misread

- `G09` A.3 says "The old BotSpec carried one symbol and one timeframe" (citing `grounding/05`). The symbol part is wrong: `symbol_scope` existed for multi-symbol variants. One timeframe is right. CHECKED.
- No earlier file records `capability_spec` as a declaration of the market conditions a bot was designed for, or the regime-coverage requirement. That is the nearest old field to "where a bot belongs". CHECKED.
- No earlier file records the compile-time and runtime tag split, or `regime_specialist`. CHECKED.

---

## 4. The correlation ledger

### What existed

**Covered elsewhere.** The vault funding-stage gate, the July wiki `correlation_ledger` stream, the cohort correlation certificate, the chorus flag, and today's reuse of the name for command lineage are in `G09` A.7.

**Correlation controls by era.** CHECKED for each row.

| Era | Control | Where |
|---|---|---|
| April vault | Funding-stage gate (slot allocator) and sizing-stage `correlation_multiplier` | `G01` §2.1 and §5.2 |
| April vault | Intent Aggregator rule 3, per tick, across bots | `QMLD\02-QML-bridges.md:93` |
| April vault | `corr_diversification` term in the auction score (V2) | `G01` §5.2 |
| July GitBook | One of the seven doors is the **exposure ledger**; the exam measures **cohort correlation** as an input, not a gate | `BRAIN\entities\qmx-new-core.md:35-45` |
| July GitBook | DEC-0021 killed "region-shift budget rotation" | `BRAIN\concepts\dead-list-and-scope.md:25-26` |
| August STRATS | A pair correlation ledger "does not pretend EUR/USD and GBP/USD have one permanent relationship. It stores the method, horizon, regime and dated measurements." Placed in dated `intelligence/`, not durable `knowledge/` | `GEN:981-996` |
| August STRATS | Dictionary entry `currency-pair-correlation`: returns-based, window-dependent, "stability over time is poor"; roles filter, confirmation, context | `ST\dictionary\context-regime-and-intermarket\context-filters-confirmations.md:815-828` |

**The operator moved "intelligence" out of STRATS.** "current bias live correlations rate expectations all that … is already in the UI and the agents updating it daily so it can be stored in a simple database under QMX" (`GEN:1431`). CHECKED.

**A false friend.** July GAP-0007 "rho" is not a correlation. It is "the refund-reserve coefficient … how much cash Treasury holds back because some books will need refunds" (`V\outputs\gaps-commentary.md:17`). CHECKED.

### What earlier recoveries missed or misread

- `G09` A.7 lists three meanings. It misses the August STRATS meaning (a dated, method-and-horizon-stamped record of pair relationships) and the Intent Aggregator's per-tick correlation rule. CHECKED.
- `G09` A.7 says the operator recalled the BMS "already had a correlation ledger". The July core as summarised in `BRAIN` names an "exposure ledger" door, not a correlation ledger. CHECKED (`qmx-new-core.md:35-37`). INFERRED: the July name for the control may have been "exposure ledger", with `correlation_ledger` as a Records stream in the wiki.

---

## 5. SQS, news kill switch, KSA, house money, the "radioactive" system, Book/BMS

### What existed

**Covered elsewhere.** SQS formula and thresholds, KSA levels, news windows, soft kill, house money ×1.5, reverse house money, compounding principle and multi-session capital are in `G01` §1, §2 and §6, and `G09` A.6, A.8, A.9. Not repeated.

**"Radioactive" is not an old-system word.** It appears in no file under `V` or `ST`. CHECKED by grep. It first appears in the October unit-plan operator files (`D:\QMX-worktrees\unit-plan\tracker\risk-sizing\research\13-funnel-round2.md:440`, CHECKED). INFERRED: it is the operator's October label for the April risk system (enhanced Kelly, house money, reverse house money, cross-session compounding).

**The operator's April description of that system.** CHECKED.
- "it uses a more enhanced Kelly plus other things yeah it is standardized to my own liking" (`GPTR:50`).
- "an enhanced Kelly with house of money effect fee monitoring and all that because I using sculpting I have to be very aware" (`GPTR:1400`).
- "there is that formula i can't give it to you it's a bit uh contemporary" (`GPTR:19556`).
- SL/TP: "a trailing take profit and sort of like a reverse trailing stop loss which moves like the stop loss to break even if the direction is correct" (`GPTR:19556`).
- In the old code the house-money logic lived in `src/router/enhanced_governor.py`, "Kelly + house money" (`GPTR:7077`).

**House money scope changed inside the vault era.** CHECKED.
- The 28 Apr brainstorm decision D3: "House money is bot-scoped, resets on swap, session-aware activation" (`BS:107`, `BS:161`).
- The vault spec: house money "is indexed to the **slot**, not the bot", and the incoming bot inherits it (`V\02-Components\01-risk-and-sizing\05-session-architecture.md:90-112`).

**Kelly inputs changed too.** D1: "Kelly sizing uses paper-trading realized stats (not planned R:R)" (`BS:159`). `G01` §2 records the opposite, that realised R:R was "proposed but deferred" (R0:169). CHECKED both.

**Circuit breakers in the old code.** CHECKED (`GPTR:10443-10446`, `GPTR:10151`, `GPTR:11262`).
- `SSLCircuitBreaker` (`src/risk/ssl/circuit_breaker.py`): a persisted state machine LIVE → PAPER → RECOVERY → RETIRED that "tracks consecutive losses per bot, rotates to paper on 2/3 loss thresholds".
- `DPRCircuitBreakerMonitor`: a separate quality breaker with four circuits: tier `CIRCUIT_BROKEN`, score below 0.3, `AT_RISK` for more than 3 checks, and rank worse than 10 while `AT_RISK`.
- The two were not wired both ways, so "A bot could be LIVE in SSLCircuitBreaker while being CIRCUIT_BROKEN in DPR" (`GPTR:10552`).
- The code's `BotTier` had six values: `ELITE`, `PERFORMANCE_TEST`, `STANDARD`, `EVALUATION_CANDIDATE`, `AT_RISK`, `CIRCUIT_BROKEN`. The vault reduced this to T1, T2, T3.
- The brainstorm logged "C7: Bot circuit breaker degrades, doesn't remove" (`BS:124`).

**Sharia-aware constraints (April).** CHECKED.
- "broker level → IC Markets Islamic accounts (swap-free); BotSpec level → NO LEVERAGE … zero-leverage strategies, swap-free account, and no-overnight-holding posture" (`PA\prd.md:380`).
- FR48: broker account selection "restricted to swap-free (Islamic) account variants" (`PA\epics.md:160`).
- The operator: "I'm only trading FX no more FX I'm not trading futures, please Islamic compliance" (`GPTR:5871`).

**Lost scheduling idea.** The Gemini source list names "Slot exchange-opening stagger" (`V\07-Source-Material\README.md:24`). No vault spec defines it; the only "stagger" in the specs is the soft-kill exit schedule (`V\02-Components\09-kill-switch-authority.md:333`). CHECKED. The PDF itself was not read.

**Book/BMS (July) and its stance on compounding.** CHECKED (`BRAIN\entities\qmx-new-core.md`).
- "Bots trade; books control bots; BMS accounts for and constrains books; nothing above a bot touches the market" (lines 20-21).
- The first book, the Scalper Book, is a "treasury-customered cash-flow machine judged by swept cash per month per dollar of seed"; it "may never compound between cycles" (31-34).
- Treasury: "cycle = seed→cap; sweep at rollover only; equity resets to seed; money ratchets between cycles" with seed $500, kill line $200, cap 2.5×S (46-49).
- Sizing: "the book offers; trust-bounded cost-aware Kelly disposes"; "Declared-weight multiplier stacks are on the dead list (DEC-0018)" (63-67).
- Other dead items bearing on the April system: DEC-0019 "TIGHTEN half-size kill level", DEC-0020 "Mid-cycle top-up", DEC-0021 "Region-shift budget rotation" (`BRAIN\concepts\dead-list-and-scope.md:21-26`).

### What earlier recoveries missed or misread

- No earlier file records that house money was bot-scoped in the 28 Apr decision before the vault made it slot-scoped. CHECKED.
- `G01` §2 says realised R:R for Kelly was deferred. The 28 Apr decision D1 had already ruled Kelly on paper-trading realised stats. CHECKED.
- No earlier file records the code's SSL breaker state machine, the DPR four-circuit monitor, or the six-value `BotTier`. `G01` G03 says no tier exists below T3; the code had `AT_RISK` and `CIRCUIT_BROKEN`. CHECKED.
- `G09` A.6 records the vault's "compounding is the edge". It does not record that the July Book core forbade compounding between cycles for the Scalper Book and reset equity to seed. INFERRED: the July core and the April "radioactive" system pull in opposite directions on compounding.
- `grounding/06` records spot-only "because of Islamic principles" (October). No earlier file records the April "NO LEVERAGE" BotSpec rule or "not trading futures, please Islamic compliance". CHECKED.

---

## 6. The dictionary

### What existed

**Covered elsewhere.** Four pillars to three layers, DNA A to I, graph operators, 239 entries and 12 fields, 9 slug collisions, the 57 exit entries, the sizer menu, the three execution contexts and the relationship types are in `R10` §2.

**How the dictionary describes market context.** CHECKED (`ST\dictionary\context-regime-and-intermarket\context-filters-confirmations.md`).
- 66 entries in ten families: trend and regime (8), momentum (6), volatility (7), indicator operations (6), session and time (6), spread, liquidity, cost and data health (7), volume and order flow (12), intermarket and correlation (5), news event state (3), pattern quality and distance (6) (lines 16-31).
- `filter`, `confirmation` and `confluence` are never intrinsic classes; they are bindings (lines 3-7).
- `market-regime` is "a categorical classification … intended to select which strategy families are appropriate", heuristic, timeframe-dependent, with no standard state count (lines 80-93).
- Session and time entries: `trading-session`, `session-overlap`, `session-open-price`, `time-of-day-window`, `day-of-week-window`, `higher-timeframe-reference` (lines 440-525).
- Open questions it leaves: no standard regime vocabulary; no cross-market news-event taxonomy ("FX macro event classes and crypto event classes likely need separate vocabularies"); whether timing should be a field on every binding (lines 1037-1045).

**Runnable vs prose.** None of the four family files contains a code block (0 code fences in each). CHECKED by count. The backend holds only an importer, an exporter, a validator and a derived SQLite file (`ST\backend\`). CHECKED. INFERRED: every dictionary entry is prose; the "about 7 runnable" in `01-ground-truth.md:116` (cited by `R10` §2.5) cannot come from the dictionary files themselves.

**Scope.** "Target markets: Forex and crypto spot … Excluded: futures execution, position trading" (`ST\STRATS-GROUND-STATE.md:18-23`). CHECKED.

**What is missing for other instrument classes.** CHECKED by grep across the four files.

| Need | In the dictionary? |
|---|---|
| Perpetual futures, funding rate | No entry. "funding" appears only inside `trading-cost` and `rollover-swap-cost`, which say "FX swap ≠ crypto funding" (lines 594, 620-631) |
| Open interest | 0 mentions |
| Futures contract roll, front month, expiry, continuous contract | No entry. Only an "Uncertainty" note on `centralized-futures-execution-context` mentions continuous contracts and front months (`exits-execution-management.md:761`) |
| Liquidation as a venue event | No entry. "liquidation" appears only as an alias of close orders (lines 106, 121, 316 of the exits file) |
| Margin, leverage | 8 and 1 mentions, all in passing; no entry |
| Index CFDs, stock indices | 1 mention; no index-specific session, cash-open or dividend entry |
| Gold, commodities | Only inside `safe-haven-demand` (line 879) |
| Futures order book and volume | Present as data scope only, flagged "Centralized-exchange only" and "not … silently transformed into Forex or crypto-spot facts" (`exits-execution-management.md:748-761`; context file 645, 660, 705) |

### What earlier recoveries missed or misread

- `R10` covers structure but not the content of the context family, its ten sub-families, or its three open taxonomy questions. CHECKED.
- `R10` §2.5 repeats "about 7 have runnable code". The dictionary files hold no code. CHECKED.
- `R10` §3 notes futures were out of scope. It does not list which instrument-class concepts are absent. CHECKED (table above).

---

## 7. Sourcing

### What existed

**Covered elsewhere.** STRATS provenance (one source, one home; nine evidence layers; six confidence dimensions; 359 NotebookLM sources; cheap-first video pipeline) is in `R10` §2.8. WF1 vanilla and spiced is in `G09` A.10.

**April: the video ingest tool.** CHECKED (`V\02-Components\14-agentic-system\08-video-ingest-tool.md`).
- Five stages: intake and validation, transcription, distillation, categorisation and tagging, review queue (lines 59-133).
- Distillation output: summary, typed `key_claims`, `indicator_refs`, `strategy_patterns`, `market_regimes`, and `citations` as timestamped transcript references (lines 90-106).
- Tags: `content_type`, `archetype_relevance`, `regime_relevance`, `indicator_relevance`, `time_horizon`, `quality_signal` (lines 110-121).
- Items the agent marked `high_confidence` were auto-approved unless the threshold was lowered (line 132).
- Triggers: operator via Copilot, the Research department, or a scheduled cron over subscribed channels (lines 188-196). Provider names, live streams and subscriptions stayed `NEEDS-CLARIFICATION` (lines 200-211).
- Output was a TRD (`spec.md`, "entry/exit narrative, hypothesis"), "**NOT** used as bot coding truth — execution SL/TP is system-owned" (`V\02-Components\13-quantmindwiki.md:358`).
- The wiki kept a human approval gate on curated content (`13-quantmindwiki.md:171-187`).

**July: explorers and scouts.** CHECKED.
- Explorer agents per source: "Instagram explorer, YouTube explorer, book explorer", weekly sandboxed runs, reporting at committee; Apify for scraping; the open-source `claude-video` skill; "Everything logged at every step — e.g. discovered channel URLs into a sheet/table" (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:50-62`).
- Research lenses: "academic papers, industrial, macro, forex, crypto, Truth Social, Discord, his Telegram groups (e.g. opening-range research notes)" (same file, 64-65). The operator "scrapes some Telegram channels and wants to hand those over" (`BRAIN\sources\agentic-braindump-2026-07-17.md:82-84`).
- The operator: "YouTube before Instagram. Can we do that same thing, like simple boring logic? … We could even use N8n" (`V\outputs\session-transcript-qmx-agentic.md:180`).
- The ruled shape (the Scout): deterministic plumbing finds, fetches and logs; the agent only answers "is there an actual strategy here? what exactly is it? is it testable?" and files a hypothesis card with source refs; "One Scout per source-class" (`BRAIN\concepts\persona-charters.md:59-65`).
- A source map of donor repositories: `claude-video`, `last30days-skill`, `claude-trading-skills`, `ai-quant-researcher`, `moon-dev-ai-agents`, `FinceptTerminal`, `backtesting.py`, `QuantDinger`, `blankly`, `AutoTrader` (`BRAIN\sources\agentic-braindump-4-2026-07-21.md:41-62`). None is a market-physics repo. CHECKED.

### What earlier recoveries missed or misread

- None of the four earlier recoveries records the April distillation schema or the auto-approve rule. Another current file already does: `D:\QMX-worktrees\unit-plan\tracker\qma-v2\research\methodology\08-strategy-funnel-lineage.md:80-81`. CHECKED.
- No current file records the July explorer and Scout design or the video tag dimensions. CHECKED by grep.
- `G09` A.12 looked for the physics GitHub repos and found none. The July donor-repo list also names none. CHECKED.

---

## 8. Agents in the old system

### What existed

**April: what agents analysed.** CHECKED (`V\02-Components\14-agentic-system\00-agentic-overview.md`, "Six Agent Roles" and "Integration with the Trading System"; `01-five-departments.md:284`).
- Research: external sources (videos, papers, broker research).
- Trading: market intelligence snapshots and journals; proposes signal logic.
- Portfolio (risk review folded in on 2026-05-01): the whole registry, tier distribution, risk state, BotSpec drafts; asks whether the population is balanced across archetypes (`01-five-departments.md:146`).
- Development: the only code editor.
- All agents read the rating service, the journal, the registry, risk state, kill-switch state and the wiki. They wrote only typed proposals.

**April: how agents proved their work.** CHECKED (`V\02-Components\14-agentic-system\05-memory-and-opinion-nodes.md`).
- Every judgment was an **opinion node**: a cited subject, a claim, typed evidence, a self-assessed confidence from 0 to 1, an author identity, and `superseded_by` (lines 75-101).
- Evidence types: `trade_journal_record`, `performance_score`, `registry_state`, `knowledge_vault_ref`, `mail_thread_ref`, `prior_opinion_node` (lines 117-126).
- Lifecycle: active, cited, superseded, archived (lines 142-150).

**April: how agents were checked.** CHECKED.
- "Agents propose; deterministic services dispose" (`00-agentic-overview.md`, Propose-vs-Dispose section).
- A disagreement resolver in the Floor Manager compared two departments' opinion nodes; a breach of the canonical formula "is not a matter of opinion — it is a deterministic rule"; only genuine ambiguity reached the operator (`02-floor-manager.md:87-120`).
- WF2 stage C was a reviewer mail loop between Development and Portfolio risk review (`11-wf2-variant-improvement.md:57`).
- Backtest reports were written by the engine, never by an LLM (covered in `R08` §1.1).

**April: how much of this actually ran.** The brainstorm logged "C2: Department functionality scope (only 2 of 5 active)" and "Five departments confirmed … only Research and Development functional today" (`BS:108`, `BS:119`). "C3: Floor Manager NEVER touches bots"; "C4: … DPR/MIS/wiki are deterministic" (`BS:120-121`). CHECKED.

**July: the razor and two agent classes.** CHECKED (`BRAIN\decisions\decision-ledger.md:18-41`).
- "anything a deterministic script/hook/plugin can do is NOT an agent." The operator: "What do you think we have hooks and plugins for?"
- Workflow agents (curated, inside workflows) vs autonomous personas (own scoped access, no operator in the loop).
- "The autonomous personas MUST interact with and leverage BMS data."
- Accepted personas: the **Cartographer** maintains "the living Week-Map: regime narrative, event-risk calendar, per-pair weather", judged on "calibration of weekly calls"; the **Coroner** necropsies "kill-lined books, benched bots, exam rejects" and keeps a Graveyard Index, judged on "recurrence rate of known death-causes"; the **Crowd Watcher** interprets crowding, with deterministic collection (`BRAIN\concepts\persona-charters.md:43-55`).
- Rejected: Gunsmith, Sparring Partner ("deterministic checks dressed as an agent"), Librarian of Edges, Registrar and the governance category (same file, 76-82).
- The operator's words on the Cartographer: "this is the reason we had a second brain"; on the Coroner: "That's a good one" (`V\outputs\session-transcript-qmx-agentic.md:214-230`).
- Agents should "interpret QMX's operational data to find inefficiencies, failures and improvement opportunities" (`BRAIN\sources\agentic-braindump-4-2026-07-21.md:26-27`).
- "Multi-model diversity is useful as deliberately different review lenses, not as majority-vote trading authority" (same file, 80-81).
- Monitoring vs observability, his distinction: "Monitoring = tells you the building is on fire. Observability = lets the technician determine it was the short-circuited wire" (`BRAIN\sources\agentic-braindump-2026-07-17.md:94-97`).
- July DEC-0022 killed the "Human chorus review loop": "intraday protection is deterministic; human authority = A1 resurrection + Sunday review only" (`BRAIN\concepts\dead-list-and-scope.md:27-29`).

### What earlier recoveries missed or misread

- No earlier file records the opinion-node evidence model, the disagreement resolver, or that only two of five departments ran. CHECKED.
- No earlier file records the July razor, the accepted personas or their proof metrics (calibration, recurrence rate). CHECKED.
- `R08` §2.1 notes the July "sense, do not dispose" rule for decay. The same rule governed every April agent (propose vs dispose). CHECKED.

---

## Ideas the old system had that no current file mentions

"Current file" means every `.md` file under `D:\QMX-worktrees\unit-plan\tracker\` plus the grounding folder of `G01` and `G09`. I grepped them for each term on 2026-10-30. A term counts as absent when the grep found nothing for it. CHECKED for the grep; each idea's source is CHECKED above.

1. **The Intent Aggregator.** A 50 ms per-symbol window that resolves opposite intents by confluence, caps aggregate risk per symbol, drops intents that push portfolio correlation too high, and returns losers to the pool without penalty (§2).
2. **Bot-level MIS views.** `BotInputAssemblerFactory` with `raw_broker_view`, `qml_feature_view` and `mis_context_view`; the operator's "bots themselves have market sentinels that are complementary"; STRATS `requires: mis.*.vN` declarations (§2).
3. **First-setup-wins slots.** The operator's model: pool bots fight, and the first bot with a setup takes the slot (§2).
4. **`capability_spec` as a market-conditions declaration** with a regime-coverage requirement in the evaluation profile (§3).
5. **`symbol_scope`** for multi-symbol bots (§3).
6. **The `regime_specialist` tag** beside the session-specialist tag (§3). The `REGIME_SPECIALIZATION` mutation type is already in `G09` A.4.
7. **The SSL breaker state machine** LIVE → PAPER → RECOVERY → RETIRED, and the DPR four-circuit monitor with `AT_RISK` and `CIRCUIT_BROKEN` tiers (§5).
8. **Bot-scoped house money that resets on swap** (28 Apr D3), before the slot-scoped version (§5).
9. **No leverage at BotSpec level, swap-free, no overnight holds** as Sharia-aware rules (§5).
10. **Slot exchange-opening stagger.** Named in the Gemini source list, never specified (§5).
11. **A complexity penalty in WF2 fitness** with seven tracked counts against "mutation sprawl" (§1).
12. **`outlines` for synthetic scenarios** and "scenarios create stress evidence, not bots" (§1).
13. **A dated correlation ledger** that stores method, horizon, regime and measurement date per pair relationship (§4).
14. **Weekly pair selection on evidence**: "not trading this pair this week … has to be backed by a lot of evidence" (§2).
15. **The opinion-node evidence types** (`trade_journal_record`, `performance_score`, `registry_state`, …) with supersession, plus a deterministic disagreement resolver (§8). Opinion nodes are named in `qma-v2` files; their schema and the resolver are not.
16. **The Cartographer's Week-Map** (per-pair weather, event calendar) and **the Coroner's Graveyard Index** of death causes (§8).
17. **One Scout per source-class** with deterministic fetch-and-log and an agent that only judges "is there a testable strategy here" (§7).
18. **The video tag dimensions** (`archetype_relevance`, `regime_relevance`, `indicator_relevance`, `time_horizon`, `quality_signal`) (§7). The distillation stages themselves are already in `qma-v2\research\methodology\08-strategy-funnel-lineage.md:80`.
19. **The old workflow numbering** with WF4 "Ecological + feature mutation" and WF3 "Bot improvement loop" (§1).
20. **A fourth news vocabulary** `SAFE / PRE_NEWS / KILL_ZONE / POST_NEWS` in the old `NewsSensor` (§2).

## Not read

- `V\07-Source-Material\gemini-scalping-orderflow-algos.pdf` (38 pages). Only its README summary was read.
- `PA\qml-protocols-catalogue.md` and `PA\qml-types-catalogue.md` beyond the cited sections.
- `PA\ux-design-specification.md`, `PA\architecture.md`, `PA\agentic-system-architecture.md`.
- `V\.brain\references\` (86 scraped third-party docs).
- `ST\.hermes\orchestration\round-1..3`, `reviews\`, `dictionary-wave-1\`, `model-routing\`, `prompts\`.
- The old code itself. It was lost in the laptop crash and is known only through the scans pasted into `GPTR`.
