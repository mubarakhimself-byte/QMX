# 39: The gold mine session, read start to finish

Research date: 2026-10-30. Read-only. Nothing here is a design or a ruling. It records what two August Hermes sessions designed, in the order they designed it.

Labels: **CHECKED** means I read it this session (database row, file and line, or command). **INFERRED** means my reasoning from checked material.

Credential rule kept. The Hermes store was opened read-only (`sqlite3.connect('file:...?mode=ro', uri=True)`). I never opened `auth.json`, `.env` or any credential file. One operator turn (FG 832, 24 Aug 16:17) contains a pasted service key in plain text; I skipped that line and reproduce nothing from it. The store still holds it, so any future copy of that message must be redacted. CHECKED.

## Citation keys

| Key | What it is |
| --- | --- |
| `GM n` | `C:/Users/Mubarak/AppData/Local/hermes/state.db`, table `messages`, `id = n`, session `20260825_115530_94412f` ("Continue STRATS Forex context library"). This is the session the August agents called "the gold mine". |
| `FG n` | Same table, session `20260824_121737_86f88c` ("Friendly greeting"), the session the gold mine continued from. Other files call these `M n`; the numbers are the same. |
| `RT Ln` | `C:/Users/Mubarak/Desktop/Stats/.hermes/orchestration/resume-20260826/full-recovered-transcript.md`, line n. |
| `DOS` | `C:/Users/Mubarak/AppData/Local/hermes/cache/delegation/subagent-summary-0-20260825_132506_664562.txt` (recovery dossier the gold mine received, 25 Aug). |
| `BND` | `.../delegation/subagent-summary-1-20260825_132506_670669.txt` (boundary dossier, 25 Aug; read via its summary in GM 3248). |
| `PKG` | `.../delegation/subagent-summary-1-20260824_170919_175475.txt` (strategy-package bot, 24 Aug). |
| `EXP` | `.../delegation/subagent-summary-2-20260824_170919_180173.txt` (experiment-design bot, 24 Aug). |
| `AUD` | `.../delegation/subagent-summary-0-20260826_105437_667387.txt` (dictionary fidelity audit, 26 Aug). |
| `SC` | `C:/Users/Mubarak/Desktop/Stats/.hermes/orchestration/dictionary-wave-1/shared-contract.md` (the dictionary workers' contract, 26 Aug). |
| `CB` | `.../orchestration/user-corrections/2026-08-26-starting-brief.md` (the 26 Aug correction brief, last edited 26 Aug 16:02). |
| `R10 §n`, `R34 §n` | `research/10-hermes-stats-goldmine.md` and `research/34-grounding-qml-and-dictionary.md` in this folder. |

---

## 1. Which copy I read

### 1.1 Three copies exist

| Copy | Size and dates | How complete | CHECKED by |
| --- | --- | --- | --- |
| Recovered transcript (`RT`) | 459,629 bytes, 1,322 lines, 57 messages. Exported from `hermes\sessions\saved\hermes_conversation_20260826_112651.json`. | **Only the tail.** Message 00 (RT L5-521) is the agent's own summary after the second compaction; messages 01-56 are 26 Aug 11:21-11:24 (model probes, four dictionary workers, the freeze). No operator design turn is in it except the 26 Aug nudges. | `wc`, `grep "^## Message"` |
| Hermes store, gold mine session (`GM`) | 610 rows, ids 2671-4193; 25 Aug 11:55 to 26 Aug 11:24 local; model gpt-5.6-sol; session closed 1 Sep. | **Fullest.** Compaction keeps old rows (`active=0`) and re-inserts copies, so most rows are duplicates. After removing exact duplicates: 30 distinct user/assistant texts. Its 57 `active=1` rows are exactly the recovered transcript. | `select ... from messages where session_id=...`; md5 dedupe |
| Snapshot store `state-snapshots/20260909-122706-pre-update/state.db` | Same row counts for both sessions. | Identical to the live store for these sessions. | same query on the snapshot |

I treated the **live store as the original**. The recovered transcript is a strict subset of it.

### 1.2 The gold mine holds less design than its name says

The part "above good morning" is short. It has five operator turns and four real replies, all on 25 Aug 11:55-13:29 (CHECKED):

- GM 2671: the operator pastes a recovery prompt and says it "is not from me".
- GM 2701, GM 2717 (22.6K chars), GM 2725 (34K chars): his long dictations.
- GM 3248: three recovery dossiers return (`DOS`, `BND`, a video-tool report).
- Replies: GM 2700, GM 2716, GM 2724 (19K), GM 3261 (24K).

Then "good morning" (GM 3262, 26 Aug 08:12, 27.5K chars; re-pasted as GM 3449 and GM 3591), the agent's apology (GM 3584), the audit (`AUD`), four workers, the freeze (GM 4193).

**Most of what the operator remembers (role-neutral entries, the strategy record, pillars, families, ports, variants) was designed the day before, in the parent session "Friendly greeting".** The gold mine recovered it. CHECKED.

Earlier files point at `GM 4065`, `GM 4066` and `GM 4067` as the gold mine's "massive design response" and "massive dictation" (the 26 Aug analysis brief, `R10 §2`). Those rows are **tool outputs**: the agent printing old genesis turns from the database after "good morning". GM 4064 = FG 795, GM 4065 = FG 831, GM 4066 = FG 975, GM 4067 = FG 2607. CHECKED (`select id, role, tool_name, substr(content,1,200)`).

So I read both sessions in full:

- **FG** (24 Aug 12:17 to 25 Aug 11:20, 1,201 rows, 78 distinct user/assistant texts): every operator turn and every assistant reply, start to end.
- **GM**: every distinct operator turn and assistant reply, start to end.
- The subagent reports each received: `PKG`, `EXP`, `DOS`, `AUD` in full; `BND`, round-1 reports, the Prime Terminal and OpenKnowledge reports through the summaries the sessions show.
- `SC` and `CB` in full.

Cross-check with the paper-trail agent (research 40), relayed by the lead. It agrees: the gold mine originals are the 25 Aug rows 2700-3261, the lowest id of each duplicate is the original, rows 4065-4067 are replays, and GM 3261 is the last answer before "good morning". Two more stores exist:

- **Row 5678** (session `20260826_180446_36307b`, 26 Aug, 55,992 chars, 20 sections, "STRATS design-decision recovery"). Never saved to a file. I read its section list and four sections. It restates the same design and adds only two small points, now C17 and H20. It also cites the gold mine as "GM M4065-M4070", repeating the replay-row mistake. CHECKED.
- **Session `20260826_153051_f809fd`** ("Review saved sessions for status", 151 rows, ids 4663-5732). Never exported. I did not read it.

Not read in full: tool outputs (about 4.2 MB of file reads and searches), attached web pages, the compaction summaries (FG 1209, 1675, 1808, 2112, 2217, 2397; GM 3431, 3511, 4137), which restate the dialogue. I sampled their decision sections and quote one line from FG 1209 below, labelled. The lineage file `transcripts-lineage/20260824_121737_86f88c-friendly-greeting.md` (575 KB, exported 24 Aug 18:41, 175 messages) is an earlier, shorter export of FG; it stops before FG 2096. CHECKED (`manifest.jsonl`).

---

## 2. The journey, in order

### 2.1 Friendly greeting (24-25 Aug), where the design was made

**FG 769, 14:27. The ask.** He wants "a knowledge base that i can later refer to and use together with other agents". Seven points: videos into documents; "Spliting specific organs frm strategies"; mini knowledge bases (scalping, a pair, a session); "categorising every idea to something athat can be coded by any agent (so like a strategy spec, i have a target of N...)"; chart patterns and discretion; pair and session specificity; sniping. "we aren't coding, we aren't testing". "i am not a trader so i might need you to help with the heavy lifting".

**FG 774. First proposal.** A pipeline "SOURCES → RAW LIBRARY → DISTILLERY → KNOWLEDGE → SPECS → CuriumX → VALIDATION"; raw versus distilled tiers; organs reused across specs; a flat YAML spec with `type: sniping`, invented TP/SL and a `status` ladder; a `trading-kb/` tree.

**FG 779, 14:54. His four pillars and many corrections.** "it is QMX not carrium X". "for us it's as if we are building more of a context layer or library". "every strategy has around four pillars": the level ("a place on a chart that you are watching"), the trigger ("the event that tells you to enter a trade"), confirmation ("filters out the weaker setups"), and "risk management and position sizing", which "QMX handles with a lot of care". "it's not finite okay you just need to find the best combinations or the simplest version that produces results". One pillar can come "from a mere sentence to literally paragraphs". Remove "buy my course" and "this is why traders fail" talk. "every strategy should be able to be tested on a minimum of three pairs". "some strategies might come from futures trading others can come from crypto". Sniping is not a methodology; "most strategies have entry they don't have exit". Use the Gemini web app, MarkItDown, books, MT5 articles, TradingView, indirect source mining ("scratch the earth").

**FG 795. The assistant's restructure.** Levels need construction, geometry, timeframe, validity, role, direction, interaction. Triggers need bar-close or intrabar, relation to level, timeframe, symmetry, once or repeated. Confirmation split by timing: context filters (before), synchronous, post-trigger. Fourth pillar renamed trade management. "A strategy without an exit can still be captured, but it should be classified as an **entry hypothesis**". "The spec should be a logic graph, not four flat lists." Three separate axes: holding horizon, methodology family, execution archetype. Evidence rules per extracted rule. "Test on at least three compatible instruments unless the hypothesis is explicitly instrument-specific." Kelly not the default. Transcript pass plus visual pass plus reconciliation. Proposes a dry run on one real source before any folders.

**FG 796, 16:04. His long reaction (about 37 minutes of dictation).** "I don't want you to take my words literally". "we could also build a huge, huge dictionary". "a trigger is what gives us an entry... this is where I think we can capitalize". "you can't pair a wrong confirmation with another wrong trigger". He had "an idea of using a mini scalper for an indicator". Order book and depth for crypto and futures. Exit ruling: if a bot brings its own stops and exits "we take it as such"; otherwise the book supplies them; "if we give ten scalpers their same exit mechanisms... It's not really that so different from having one centralized exit mechanism". Daily loss limits, exposure and re-entry are already in QMX ("circuit breaker"). "Entry hypothesis... That's perfect." "The spec should be a logic graph... I'm liking this read". "snipers actually are levels" (later self-corrected). Stops at swing; no position trading; prop-firm knowledge base. He gave a personal reason for not trading futures and asked not to be lectured. "methodology or strategy family... we need to dig deep and expand it". Pairs: "categorize the pairs and then we test a specific category". Ingestion: "level number one is unbiased information... we store it then after storing it it can be retrieved at any point x or at any time t". cTrader MCP and AutoChartist as a place where agents could test hypotheses by hand.

**FG 831. The core.** Bots allowed as construction machinery; the library must not depend on them. QMX split read from the docs: "Bots trade; books control bots; BMS accounts for and constrains books". Reusable exit module referenced by many bots. Kelly withdrawn. A five-layer "trading plan" table (setup, bot plan, book plan, system plan, operator plan); the four pillars are "a **strategy hypothesis grammar**". "**The biggest ontology improvement: primitives and roles must be separate**", with bullish engulfing, RSI and order flow each shown in four roles. The three layers: "Primitive dictionary 'What things exist?' / Role bindings 'What job does this primitive perform here?' / Strategy logic graph 'How are the bound components combined?'". "Timeframes and pairs are coordinates, not levels." "Sniping spans several roles." Large family lists. 19 fields per dictionary entry. Trigger and confirmation as "the largest optimization surface" with a step-by-step search order. Pair similarity and the home, analogue, adversarial challenge. A ten-stage video pipeline. Six confidence dimensions. A 15-role research crew feeding "one compiler/curator".

**FG 902, 17:00. His reaction.** "your graph idea struck me very well because if a new variant of a strategy is born... You can change like multiple triggers and the level remains the same". Each strategy "in a fold of its own"; "combining multiple strategies together". Books are not fixed. "I don't know about candlestick patterns for me candlestick patterns fall under triggers... it's not inherently... I get it now". "sniping can be a level liquidity window it can be a trigger... can even be bloody confirmation". Testing criteria must be specified because agents will run the tests. "the sweet spot is according to the book". Pair knowledge "like a banker"; session knowledge for sniping "per session per pair per bot... in like big huge tables". "I've actually not objected to anything so far".

**FG 941. Visual tree and packages.** A STRATS tree with `dictionary/primitives/` by family and `dictionary/bindings/` by role, `knowledge/`, `strategies/<name>/` (manifest, evidence, graph, lineage, variants, experiments, evaluations), `intelligence/` and `adapters/qmx/`. Variants "should generally be compact overlays". A combination has several parents: a lineage DAG. "The experiment artifact is separate from the strategy." The "sweet spot" is conditional on the book; surface "a **Pareto frontier**", not one best variant. An MIS rule. `knowledge/` (slow) versus `intelligence/` (dated). Three bots launched: Prime Terminal, package, experiment.

**FG 965 and FG 974. Bot results.** `PKG`: lockfiles, semantic overlays, named graph ports, lineage edge types. `EXP`: experiment contract, result identity, ΔBookUtility, staged tests, challenge cube, signal funnel.

**FG 975, 17:35. His verdict and the placement correction.** "if we build a strong enough dictionary, it can be reused in the strategy itself... maybe this is a bullish engulfing... It maybe it has ranges... certain things might need specific numbers or defaults. And I think Python is already suitable". "Methodologies and macro. What's the difference". SMC and ICT are "collections of multiple strategies"; "a scalper can use a level from SMC, a trigger from ICT, and a confirmation from elsewhere". "all that is written in QML... it's a library in there". Experiments "like... git work trees". "we might need to keep even the failed experiments". "it's not about avoiding... the magical variant... over time we can create one, but it doesn't mean it's the only one". "the perfect identity... for a mean reversion" built from focused knowledge. MIS "is a constant". Mini-KBs "more like a library than normal day-to-day usage" and must not collide with the agentic memory. The intelligence layer belongs in QMX's UI and database. "I like this lineage". Then: package and experiment ideas "are genuinely good but... both of them I think are placed in the wrong place"; coding and testing go to QMX.

**FG 983 to FG 2095. Orchestration.** He asks the agent to orchestrate bots. Seven bots run; he asks for model diversity (FG 1260, 1270, 1280: "choose the right model for the right tasks", no Grok). Rounds 1-3 produce plans and reviews. FG 1599: "we are literally going to have to fill the library by ourselves... It's not like we are filling in some few examples". The agent pauses with nothing populated (FG 2095).

**FG 2096 to FG 2501, 24 Aug evening.** He brings the video skill; stock-trader videos "consider that too" (FG 2382). The agent writes transfer rules for stock sources and a phased Kanban plan (FG 2388). FG 2490: no wrapper layer needed; bots, not skills; Obsidian; podcast channels "might be the actual gems". FG 2501: a video as a seed for a whole channel; a three-axis source sort.

**FG 2502 to FG 2608, 25 Aug morning.** He wants sources collected, aligned and categorised before any processing, and asks about OpenKnowledge. FG 2599 proposes a two-pass sort, a four-level source hierarchy and a "working, human-reviewable operating system". FG 2607 rejects it: "this entire thing is not code it's just a folder... why should we create a pilot for a folder". He starts a new session.

### 2.2 The gold mine (25-26 Aug), where the design was recovered

**GM 2671 to GM 2716.** The recovery prompt is "not from me". GM 2701: "we create a leader, a bot that is going to lead and monitor other boats". GM 2716 collapses the "six open agenda items" into three questions and a leader-and-workers shape.

**GM 2717, 12:33.** "What open agenda?... we kind of covered everything". STRATS is about "turning that into a structured format that you know we can test and you know, backtest, evolve". Mini-KBs per pair or session. Folder READMEs that "explain what is where". Gemini web app as the visual worker, prompted "like a human"; NotebookLM; n8n as a cheaper deterministic intake. "how does it know?... a complex strategy is not as easy as you think". Videos with 19 chart patterns; strategies spread over a 20-minute explanation. Obsidian, not OpenKnowledge; no Notion. Curator on a small-context model; "I don't want these agents deleting no stuff".

**GM 2724.** "do not classify an entire video into one bucket". An eight-part completeness checklist (market context or location, trigger, filters or confirmations, entry semantics, invalidation or stop, target or exit or management, timing and sequencing, scope). "Every detected rule must point back to transcript timestamps; subtitle cues; chart frames; OCR". A contribution table (strategy candidate, `entry_hypothesis`, fragment, education, creator preference, non-operational, ambiguous). Long-transcript economy. "Raw does not quite mean unbiased". A Gemini prompt pack. Non-destructive worker rules.

**GM 2725, 13:07.** Test manifests, run results, ledgers, executors, adapters "is under QMX". "the experiments folder would work kind of like a Git worktree". "I had a decision to make whether I build this now or build it after building KMX... let me just build it now". "a global index the same way, like you have skills". "It was the dictionary built?... I'm not so much of a trader, but I'm good with dev work... have an X amount of phrases that could be used in the dictionary... under levels, triggers, confluence". "The missing piece was the actual speck of bot for QMX... like spec-driven development". He calls the checklist "very, very good" and the evidence rule "very insane I couldn't have thought of that". Gemini can later be used "for comparison... we are not backtesting we just want to confirm like the descriptions". Run Gemini in several browser tabs in parallel. NotebookLM data tables, mind maps and infographics for chart-pattern videos.

**GM 3261, 13:29.** "**The graph and dictionary were not the post-compaction mistake. They were the correct semantic core.**" The dictionary was "designed extensively, but it was not populated". The record A-I (identity, evidence map, primitive references, role bindings, logic graph, exit completeness, dependencies, unknowns, lineage). Pillars "survive as a convenient human view". Clear STRATS-owns and QMX-owns lists. Catalog "like your skills-index analogy". STRATS lineage versus QMX lineage. Genetic algorithms "not found" in the record. The video tool: "Best accuracy: videos under 10 minutes". Sixteen "settled" points.

**GM 3262, 26 Aug 08:12, "good morning".** "let's just leave QMX out. QMX will adapt to the library". "I want you to be more of an orchestrator". "most strategies actually are not coming from Forex traders, they're coming from futures traders"; "I might trade crypto very soon... spot... BTC against USD... Solana... against USD". "logic graph wasn't my idea. I agreed with it". "the pillars against the completeness model... this is something I really couldn't have come up with on my own". "doesn't all this... have to have relationships to the dictionary". Part-by-part comments on A-I (see ledger F). "a bot that has ambiguity shouldn't be tested". "Most guys are going to give you abstract strategies... This is the use case of the knowledge bases". Exits "are not mandatory... a boat most times will have its own exits under a book". G "is going to undermine QMX". Genetic lineage: "mutate and adopt certain features from specific bots... hybrids, tribids... we test it across families". "like trying to mix law students with biology students". "we really don't need an adapter". "this guy told me he has around 7,000 strategies". "some trading bots might be good. They don't need succession... We just make a new variant." "Let's find a workaround for the limitations of this skill". No Grok, no Kimi K3.

**GM 3467 to GM 4193.** The session compacts. He asks it to "pause... and read through the transcript". GM 3584: "You were right to stop me"; ten points re-established; it names its own regression ("alignment packet → model-probing phase → specialist fleet → staging → curator → YAGNI review → promotion gates → video R&D"). `AUD` runs and corrects two false quotes. Then the agent launches four dictionary workers under `SC` (GM 3728). The internet drops; two workers die (GM 4005). After a second compaction he stops it again (GM 4171: "this is the second time I'm telling you this"). GM 4193: "Everything is now frozen". Two artifacts survive (66 context entries, 57 exit entries) as "unapproved scratch material".

---

## 3. Ledger of design ideas

Status words: **seed** (operator said it), **proposed** (assistant or bot), **agreed** (he approved it in words), **rejected**, **reversed** (agreed then undone), **open** (left undecided). "10/34" says whether research 10 or 34 already carries it.

### A. Purpose and boundary

| Id | Idea, plain words | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| A1 | A knowledge base agents can use; turn every idea into something any agent can code ("a strategy spec... a target of N"). | FG 769 | seed | both |
| A2 | It is a context layer or library; QMX does validation. | FG 779, FG 795 | agreed | 10 |
| A3 | The library must not depend on Hermes bots at runtime; bots are only construction machinery. | FG 795, FG 831 | agreed | 10 |
| A4 | Build it now, while QMX is being built, because it is independent and subscriptions will expire; "the populated library, not merely its foundation, is the product". | FG 1599, FG 1605, GM 2725 | agreed | both |
| A5 | "This entire thing is not code, it's just a folder"; no pilot for a folder. | FG 2607 (re-read as GM 4067) | agreed | both (cited as GM 4067) |
| A6 | Leave QMX out; QMX adapts to the library; no adapter, because an agent can read an Obsidian folder. | GM 3262 | agreed | both |
| A7 | STRATS-owns list (evidence, claims, dictionary, bindings, graphs, specs, entry hypotheses, mini-KBs, catalog, durable lineage) versus QMX-owns list (implementations, tests, backtests, evolution, worktree experiments, ledgers, run results, executors, adapters, locks, certification). | GM 3261 | agreed | 10 |
| A8 | "Law students versus biology students": the library keeps the books in order; QMX experiments on them. | GM 3262 | seed | no (in research 40) |
| A9 | The end product is the spec of a future **trading bot** ("speck of bot... spec-driven development"); name it "trading-bot candidate specification" to avoid confusion with Hermes bots. | GM 2725, GM 3261 | agreed ("I hope the term specification makes sense", GM 3262) | 34 |
| A10 | The 1 Sep tree, `schema/`, DNA lock and SQLite were built by another tool after both sessions; no Hermes session exists that day. | (outside both sessions) | n/a | 10 |

### B. Pillars and views

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| B1 | Four pillars: level, trigger, confirmation (filter), risk and sizing. Each holds any number of parts: "not finite". | FG 779 | seed | both |
| B2 | Rename the fourth pillar "trade management" (invalidation, stop, target, time exit, trailing, break-even, partials, sizing, exposure, daily loss, re-entry). | FG 795 | proposed, later split (B5) | no |
| B3 | Pillars are a "strategy hypothesis grammar", not the whole trading plan. A five-layer trading plan: setup/entry model, bot trading plan, book plan, system plan, operator plan. | FG 831 | proposed; he answered "the missing parts are the first two but the rest I think is already there" (FG 902) | **no** |
| B4 | Pillars survive "as a convenient human view" over primitives, bindings and graph, "not four rigid buckets". | GM 3261 | agreed ("this is something I really couldn't have come up with", GM 3262) | both |
| B5 | Eight-part completeness checklist: market context or location, trigger, filters or confirmations, entry semantics, invalidation or stop, target/exit/management, timing and sequencing, scope. | GM 2724 | agreed ("very, very good", GM 2725) | 34 |
| B6 | Reconciled split: location separate from context; trigger with arming, timeout, reset; confirmation in three timings; confluence as graph composition, not a role; entry is its own action; invalidation split from stop; timing graph-wide; scope on each binding. | GM 3261, DOS §7 | proposed; confluence left open | 34 |
| B7 | Every area must link to the dictionary: "doesn't all this... have to have relationships to the dictionary". | GM 3262 | seed, accepted in CB | 34 (CB) |
| B8 | Views over the same record, never a second ontology; ambiguity shown with tags or colour, "Obsidian-friendly views". | GM 3262, CB, AUD §3 | agreed | 34 |
| B9 | Market context as a pillar: "market context is the one we can add... market context is more in-depth". | GM 2725 | seed | 34 |

### C. Dictionary, role neutrality and hybrids

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| C1 | Primitives and roles are separate. The same primitive can be a level constructor, a trigger, a confirmation or an exit. Bullish engulfing, RSI and DOM each shown in four roles. | FG 831 | agreed ("it's not inherently... I get it now", FG 902) | both |
| C2 | Three layers: dictionary ("what exists"), role binding ("what job here"), graph ("how combined"). | FG 831 | agreed; "logic graph wasn't my idea. I agreed with it" (GM 3262) | both |
| C3 | Wider role list: "context, trigger, confirmation, veto, exit, target, **sizing modifier**, or regime detector". | FG 1209 (assistant's own compaction summary of FG 831-975) | proposed | **no** (sizing modifier and veto as roles) |
| C4 | Sniping spans several roles: level, time window, narrow trigger, execution policy, tight invalidation. He: "sniping can be a level liquidity window it can be a trigger... even... confirmation". | FG 831, FG 902 | agreed | 10 |
| C5 | **A whole bot as an input:** "I had an idea of using a mini scalper for an indicator". | FG 796 | seed, never answered | **no** |
| C6 | The phrase "an exit used as a trigger" does not appear in either session (`grep -i hybrid` finds only the genetic-lineage line). The idea is covered by C1: an opposite engulfing close or an RSI cross back is an exit in one strategy and a trigger in another. "Hybrids, tribids" in his words means combined bots (G9). | FG 831, GM 3262 | INFERRED mapping | partly |
| C7 | The dictionary is what agents cite instead of long prose: "where an agent was going to be writing long sentences, it just... says... use bullish engulfing"; entries may carry "ranges... specific numbers or defaults"; "Python is already suitable". | FG 975 | seed | both |
| C8 | Why a dictionary: "I'm not so much of a trader, but I'm good with dev work... have an X amount of phrases that could be used in the dictionary". | GM 2725 | seed | 34 |
| C9 | Starter families. Levels: 27 kinds (swings, S/R, supply/demand, order blocks, breakers, FVGs, liquidity pools, equal highs, prior day/week/month, session highs/opens/ranges, opening ranges, gaps, round numbers, pivots, Fibonacci, MAs, VWAP and anchored VWAP, channels, Bollinger/Keltner, Donchian, volume profile, nodes, necklines, trend lines, ATR bands, event-anchored, broker-visible liquidity). Triggers: 22. Confirmation/filter: 19. Exit/invalidation: 15. | FG 831 | proposed as seeds ("I really do hope these are examples. You will expand it", FG 975) | 10 (count only) |
| C10 | Nineteen fields per entry: name, aliases and marketing names, definition, inputs/outputs, data requirements, candidate detection algorithms, parameters, eligible roles, timing, timeframe behaviour, market compatibility, redundancies, compatible/incompatible primitives, latency, cost sensitivity, failure modes, evidence, existing code, MIS labeler mapping. | FG 831 | proposed | 34 ("about 25 fields") |
| C11 | Minimum entry (seven parts) versus optional enrichments; Python described as "supportive brainstorming, not approval of a mandatory Python implementation layer". | AUD §4 | proposed | 34 |
| C12 | Twelve-field worker format; every value labelled `source-stated`, `published-convention`, `STRATS-standardized`, `inferred` or `unresolved`. | SC | used by workers | both |
| C13 | Folder layout by family (`patterns/`, `indicators/`, `market-structure/`, `liquidity/`, `order-flow/`, `time-and-sessions/`) **plus** `bindings/` folders by role (level, trigger, confirmation, exit). | FG 941 | proposed; the role folders were later dropped (27 Aug session, per R34 §2.3) | 34 (later tree only) |
| C14 | Trader marketing names become neutral concepts with aliases; separate raw price facts from derived indicators from discretionary reading. | SC | used | 34 |
| C15 | The dictionary was designed but never populated in these sessions; 123 candidate entries survived the 26 Aug run as scratch. | GM 3261, GM 4193 | fact | both |
| C17 | Helper scripts (deterministic parsers, indicator reference semantics, alias and dedupe support, coverage reports) are construction tools that "do not turn STRATS into a codebase". Defaults carry a sixth label: "generated for future experimentation". | row 5678 §4.1, §10.2 | proposed | no |
| C16 | Big gaps flagged: when is the dictionary "complete enough"; whether STRATS defines standard defaults at all. | AUD §8 | open | 34 |

### D. Bindings, coordinates and timing

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| D1 | Every component carries its own instrument scope, timeframe, session, direction, parameters, evidence, confidence and dependencies; "strategy timeframe cannot be only one global field". Example: H4 level, H1 bias, M5 trigger, M1 execution, London filter, pair spread limit. | FG 795 | agreed ("wow... Yeah", FG 796) | 10 (partly) |
| D2 | Timeframes and sessions are coordinates, not levels. "London-session high" is a level; "London session" is context. | FG 831 | agreed (he self-corrected, FG 902) | both |
| D3 | Level needs construction rule, geometry, source timeframe, validity window, role, direction, interaction rule (touch, close through, sweep, retest). | FG 795 | proposed | no (as a list) |
| D4 | Trigger needs bar-close or intrabar, relation to the level, timeframe, long/short symmetry, fire once or repeatedly, entry immediate or later. | FG 795 | proposed | 10 |
| D5 | Confirmation in three timings; post-trigger confirmation moves the honest entry price ("prevents lookahead bias"). | FG 795 | agreed ("I actually couldn't think of this", FG 796) | both |
| D6 | Two confirmations are not automatically better; RSI and MACD may encode the same momentum, so test incremental value. | FG 795 | agreed | 10 (as search order) |
| D7 | Trigger path as a state sequence: prerequisites, arming, trigger, optional confirmation, entry, manage/exit, timeout/invalidation/reset/re-entry. | DOS §3 | proposed | 10 (operators) |
| D8 | A binding carries role, parameter profile, pair, timeframe, session, direction, timing, bar semantics, dependencies, evidence, data provenance, unresolved values; this keeps one RSI entry instead of ten copies. | GM 3261 | agreed | both |
| D9 | His seed: "I think we are specific on triggers and confirmation... level I don't know". | FG 902 | seed | no |

### E. Logic graph and ports

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| E1 | A logic graph, not four lists: AND, OR, K-of-N, ordered "followed by within N bars". | FG 795 | agreed ("Perfect. Wow", FG 796) | both |
| E2 | Typed nodes (bindings, operators, temporal operators, actions, data inputs) and edges (`requires`, `then`, `suppresses`, `emits`, `invalidates`). Explicit bar-close/intrabar, pre/same/post timing, long/short branches, cooldown, expiry, re-entry. | PKG | proposed | 10 |
| E3 | Edge words in the dossier: `at`, `after`, `only_if`, `arms`, `confirms`, `vetoes`, `invalidates`, `manages`, `exits`. | DOS §3 | proposed (AUD: "not individually ratified") | no |
| E4 | **Named ports** for combining strategies: `setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`. A composite imports parents' ports, never their insides; parents namespaced; `conflict_policy: error`. | PKG | proposed; he liked the lineage ("I like it", FG 975) | 10 |
| E5 | Graph example with sequence window: Asia high → sweep → SEQUENCE within 3 bars (displacement, retracement entry) AND London filter → open → OR(target, level break). | PKG | proposed | 10 (STRAT-000001 only) |
| E6 | For AND, OR, K-of-N and sequences, define how "removing a node" works so the rest keeps its meaning. | EXP §4 | proposed | 10 |

### F. The strategy record and its parts

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| F1 | First flat YAML spec (`type: sniping`, invented TP/SL, risk inside, status ladder written back by results). | FG 774 | rejected (FG 779; DOS §6) | 10 (rejected list) |
| F2 | A strategy is a package, "not one giant specification": evidence, graph, lineage, variants, experiment manifest, evaluation report, QMX binding. | FG 941 | he liked a package (FG 975), then moved experiment and evaluation to QMX | 10 |
| F3 | Each strategy in its own folder because of variants, children and combinations. | FG 902 | seed | 10 |
| F4 | Record A-I: A identity and class; B evidence map; C primitive references; D bindings; E graph; F exit completeness; G dependencies; H unknowns; I lineage. | GM 3261 | agreed with comments (GM 3262) | both |
| F5 | His A comment: "most bots might not work out... we have to have some sort of way to see that". The identity must show failure history. | GM 3262 | seed | **no** |
| F6 | His B comment: Gemini can draw charts; channels like Mind Math Money use AI-made illustrations, so "most of the time you will prefer using the transcript". | GM 3262 | seed | no (in research 40) |
| F7 | His C/D comment: some parts are huge, so "folders or files... Just make it organized as long as I can understand it and the agents can understand it". | GM 3262 | seed, accepted in CB | 34 (CB) |
| F8 | His H comment: tags or colour; "a bot that has ambiguity shouldn't be tested"; maybe "a folder of ambiguity"; but abstract is not ambiguous: "unspecified time frame... This is the use case of the knowledge bases". | GM 3262 | seed | both |
| F9 | Seven ambiguity kinds: contradictory, unreadable, source-unspecified, methodology-implied, researcher inference, deliberate downstream choice, genuinely unresolved. | AUD §6 | proposed | no |
| F10 | His G comment: dependencies "is going to undermine QMX"; keep only what is needed to reproduce the source logic. | GM 3262, CB | agreed | 34 |
| F11 | Contribution classes for one source: source strategy candidate, `entry_hypothesis`, primitive/pattern/fragment, education, creator preference, non-operational, ambiguous. | GM 2724 | agreed | 10 (classes) |
| F12 | Five record classes: complete, entry_hypothesis, fragment, descriptive_pattern, composite. | 1 Sep lock (outside) | n/a | both |
| F13 | Spec should name the intended book class, the required labelers and the assumptions for examination. | FG 831 | proposed, later removed (AUD §7) | no |

### G. Variants, family tree and families

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| G1 | Variants are small overlays, not copies: `replace: liquidity-sweep with: liquidity-sweep-plus-displacement`, `add: higher-timeframe-bias`. | FG 941 | agreed ("I like this lineage", FG 975) | 10 |
| G2 | Edit operations: `add_binding`, `remove_binding`, `replace_parameter`, `add/remove_constraint`, `connect`, `disconnect`, `replace_subgraph`, `change_timing`, `change_entry`, `change_exit`. Ordered stack plus result digest; stale target fails; no last-write-wins. | PKG | proposed | 10 |
| G3 | Baseline: smallest source-faithful candidate, one parentless node per strategy family, immutable once published; corrections create a successor. | PKG | proposed | 10 |
| G4 | Link types: `derived_by_overlay`, `composed_from`, `merged_from`, `corrected_from`, `supersedes`. | PKG | proposed | 10 |
| G5 | Lineage kinds in plain words: source baseline, corrected successor, source-defined variant, curated derived variant, composite parents, exact semantic difference. | GM 3261 | agreed "for now... let's go with your version" | 10 (via REC) |
| G6 | "Some trading bots might be good. They don't need succession... We just make a new variant." | GM 3262 | seed | 10 |
| G7 | History "if it is a child or a grandchild of another trading bot". | GM 3262 | seed | no (wording) |
| G8 | "Corrected successor... links with unknowns and ambiguities": a correction is how an ambiguity gets resolved. | GM 3262 | seed | **no** |
| G9 | Genetic lineage: "mutate and adopt certain features from specific bots... combine them to make hybrids, tribids... if... a certain... confirmation mechanism can give us a higher win rate... we test it across families". Placement: QMX. | GM 3262 | seed; "take the idea, maybe adopt it" | both |
| G10 | A combined strategy from several sources must be labelled a curated composite, never one creator's strategy. | GM 3261, FG 941 | agreed | 10 |
| G11 | Two lineages: STRATS knowledge lineage versus QMX run lineage (implementation, variants, runs, evolved candidates, failures, certification). A QMX discovery might be curated back later; raw runs never flow in. | GM 3261 | proposed; feedback rule open | no (the split) |
| G12 | Strategy families as axes: holding horizon (scalp, intraday, swing, position), methodology family (13: trend, mean reversion, breakout, SMC/ICT, S/R price action, pattern, order flow/profile, stat arb, volatility, seasonality, event, indicator, hybrid), execution archetype (breakout, pullback, reversal, retest, sweep, sniping entry). | FG 795 | agreed ("The methodology section... is perfect", FG 796) | 34 (open taxonomy) |
| G13 | SMC and ICT are collections of strategies to be split into parts; a scalper is cross-cutting; methodology versus macro confusion, self-corrected. | FG 975 | seed | both |
| G14 | "The perfect identity... for a mean reversion": focus knowledge on one family until its identity is strong, then build agent skills from it and "all the stuff above kind of updates itself". | FG 975 | seed | 34 §5.3 |
| G15 | Swap triggers while keeping the level: "you can change like multiple triggers and the level remains the same. Confirmation is we've changed like one". | FG 902 | seed | no (as wording) |

### H. Sources, evidence and exact quotes

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| H1 | Raw versus distilled: raw is immutable; agents read raw and write distilled. | FG 774 | agreed | 10 |
| H2 | "Level number one is unbiased information": store it first, retrieve it "at any point x or at any time t". | FG 796 | seed | **no** (as his rule) |
| H3 | "Raw does not quite mean unbiased": call it uninterpreted source evidence; it keeps promotion, mistakes and cherry-picks. | GM 2724 | agreed | 10 (partly) |
| H4 | Per extracted rule keep: exact quote or transcript segment, timestamp or page, chart frame, pillar, normalized rule, explicit/visual/inferred/added-by-us, confidence, ambiguity. Unknowns stay unknown; never turn "wait for a strong candle" into a number. | FG 795 | agreed ("this one I'll trust you", FG 796) | 10 |
| H5 | "Every detected rule must point back to transcript timestamps; subtitle cues; chart frames; OCR; or another exact source location." | GM 2724 | agreed ("very insane", GM 2725) | 10 (partly) |
| H6 | Creator research is creator-profile evidence, never a rule of that strategy. | FG 795 | proposed | **no** |
| H7 | Six confidence dimensions: extraction, rule explicitness, source quality, empirical status, portability, ambiguity. He: "confidence is something that can confuse agents". | FG 831, FG 796 | agreed | 10 |
| H8 | Model output is interpretation: transcripts and frames are evidence; Gemini explanations, NotebookLM answers and Qwen outputs are derived. | FG 831 | agreed | 10 |
| H9 | Do not put one video in one bucket: a podcast yields biography, a market-structure lesson, a session preference, a primitive, an entry hypothesis, chart timestamps, missing exits, promotion. A video of 19 chart patterns yields 19 pattern entries, not 19 strategies. | GM 2724 | agreed ("very crucial", GM 2725) | 10 |
| H10 | Source hierarchy, four levels: container (channel, book, site, notebook), item (episode, article, script), evidence segment (time range, page range, frame, code section), derived knowledge. | FG 2599 | proposed (in the turn he rejected for its OS framing) | **no** |
| H11 | Two-pass sort: cheap triage on metadata, then informed classification after reading; result `confirmed`, `revised` or `ambiguous`. Source taxonomy: content form, original asset class, transferability. | FG 2599, GM 2716 | agreed in plain form ("initial triage → informed classification") | **no** |
| H12 | Seed video → channel dossier (creator, specialty, playlists, guests, instruments, episode count, style, transferability) → episodes → guests → related channels. Podcast channels "might be the actual gems". | FG 2501, FG 2599, FG 2490 | agreed | 10 ("seeds, not corpus") |
| H13 | Remove marketing and lectures ("buy my course", "this is why traders fail") from operational extraction, but keep them labelled. | FG 779, GM 2717 | agreed | 10 |
| H14 | Long transcripts: chapter segmentation → overlapping chunks → cheap per-chunk relevance → keep trading segments → gather related segments across the episode → strong model reads compact evidence packets. | GM 2724 | agreed ("very in-depth", GM 2725) | **no** |
| H15 | Gemini prompt pack: video mapper, strategy extractor, chart analyst, teaching/diagram, critic; each demands timestamps, quotes, spoken/visual/inferred split, unknowns, asset class, transfer assumptions. | GM 2724 | agreed | **no** |
| H16 | Use Gemini afterwards to check a finished spec against the video: "we are not backtesting we just want to confirm like the descriptions". | GM 2725 | seed | **no** |
| H17 | Gemini and NotebookLM as the main way to resolve ambiguity: ask them "like a student". | GM 3262 | seed | 34 (mentioned) |
| H18 | Indirect source mining: MQL5 articles, CodeBase, forum comments, parameter names, author histories; TradingView scripts, inputs, comments, similar scripts under other names. | FG 795 | agreed ("you literally went all out", FG 796) | **no** |
| H20 | Research status stays separate from source truth: clear or codable is not edge; claimed performance is a cited claim; later results live apart. | row 5678 §4.1 item 14 | proposed | 10 (partly) |
| H19 | AutoChartist as a source of pattern definitions and a benchmark, never proof of edge. | FG 795 | proposed | **no** |

### I. How context was meant to be described and measured

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| I1 | Context filters are known before the trigger: higher-timeframe trend, session window, spread below a threshold, price in discount of a range, volatility within a regime. | FG 795 | proposed | 34 (via DNA) |
| I2 | Context can gate, veto, score, rank or just label a setup; it must not be merged with location. | DOS §2 | proposed | 34 (partly) |
| I3 | MIS rule: put a feature in MIS when it is shared by many bots, expensive, market state rather than trading authority, needed the same way in exam and live, and worth versioning; keep it in the bot when cheap, strategy-specific, proprietary or changing fast. The graph declares `requires: mis.liquidity-regime.v3`. | FG 941 | proposed; he: MIS "is a constant... centrally used" and should not keep old versions running (FG 975) | no (the rule) |
| I4 | Pair similarity, not one correlation number: shared currency, session participation, spread and liquidity, volatility, range, news sensitivity, trend versus mean-reversion tendency, gaps, correlation by timeframe, rolling correlation, cost, strategy-family results, broker behaviour. A pair can sit in several clusters. | FG 831 | agreed ("insane... I am really loving it", FG 902) | 10 |
| I5 | Correlation ledger stores method, horizon, regime and dated measurements, never "one permanent relationship". | FG 941 | proposed | 10 |
| I6 | Knowledge (slow, durable) versus intelligence (dated: bias, live correlation, rate expectations, data surprises). He moved intelligence to QMX's UI and database. | FG 941, FG 975 | agreed with placement change | 10 |
| I7 | Prime Terminal's flow as a model of context: Aggregate → Filter → Validate → Confirm → Plan → Execute; domains: macro, central banks, positioning, sentiment, cross-asset, seasonality, volatility. | FG 941, FG 965 | proposed; he: "let's not dig so deep into it" | **no** (Prime Terminal 1 hit, elsewhere) |
| I8 | Regimes for testing: trend versus range; low, normal, high volatility; normal versus stressed liquidity and cost; event versus non-event. "Regime labels must be available at evaluation time or fitted only on training data." | EXP §6 | proposed | **no** (the timing rule) |
| I9 | Pair, session and regime are "challenge coordinates, not tunable strategy factors". | EXP §3 | proposed | both |
| I10 | Session knowledge for sniping per session, pair and bot, "categorize everything in like big huge tables", so QMX can find "the best suitable scenarios for a bot to flourish in". | FG 902 | seed | **no** |
| I11 | Trade "like a banker": deep pair research plus daily macro, curated so he can read it. | FG 902, FG 975 | seed | no |
| I12 | Latency and co-location (London, about 4-30 ms) as metadata on primitives and strategies. | FG 941 | proposed | 10 (mention) |
| I13 | News kept only as durable concepts (schedule, class, window), no live bias. | worker output via GM 3938 | used | 34 |

### J. Exits, management and sizing

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| J1 | No exit: capture it as an **entry hypothesis**, never as a complete strategy; derived exits (fixed R, opposing liquidity, ATR, time, signal reversal, trailing) are labelled "added by our pipeline". | FG 795 | agreed ("That's perfect", FG 796) | both |
| J2 | His exit ruling: a bot's own stops and exits are kept; otherwise the book supplies a fallback; ten scalpers with the same exit equal one central exit. | FG 796 | agreed | 10 |
| J3 | Reusable exit module, one canonical file referenced by many bots (`opposing-liquidity-exit-v1` used by A, B, C). | FG 831 | agreed | 10 |
| J4 | Exits not mandatory; four exit labels: `source_defined`, external/book supplied, `deliberately_open`, `unresolved`. The "missing exit = entry_hypothesis" rule is softened, not universal. | GM 3262, AUD §6 | agreed; boundary left open | both |
| J5 | Split: level invalidation ≠ setup invalidation ≠ stop reference ≠ protective stop order ≠ target reference ≠ exit trigger ≠ exit order; partial exits ≠ partial fills; retry ≠ re-entry; pending-order expiry ≠ time exit. | GM 3987 (exits worker result) | proposed | 10 (exit entries) |
| J6 | Kelly withdrawn as a default; neutral baseline of fixed risk per trade and results in R; Kelly, volatility targeting and drawdown sizing tested later. | FG 795, FG 831 | agreed (he pointed to QMX's own Kelly, FG 902) | 10 |
| J7 | Sizing, daily limits, exposure, breakers belong to the book and BMS; source sizing kept only as a claim. | FG 831, FG 796 | agreed then | both |
| J8 | Open: is source-native sizing a primitive or only a preserved source claim; does execution-state reconciliation belong in the dictionary. | GM 3987, AUD §8 | open | 34 (partly) |

### K. The testing design

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| K1 | Minimum three pairs; refined to three compatible instruments; challenge picks: home pair, close analogue, adversarial compatible pair. | FG 779, FG 795, FG 831 | agreed ("one sentence... has changed the entire perspective", FG 796) | 10 |
| K2 | Costs follow the instrument: spread, commission, slippage, tick size, session liquidity, financing, market hours. | FG 795 | proposed | no (list) |
| K3 | Confirmation judged against an objective, not win rate: expectancy after costs, frequency, win/loss shape, mean loss, tail loss, MAE, spread sensitivity, regime and pair stability, out-of-sample decay, parameter sensitivity, redundancy. "A filter can increase the win rate while making the strategy worse." | FG 831 | agreed | no (list) |
| K4 | Search order: fix location and context, compare trigger families, keep a few, add one confirmation family at a time, measure gain, interactions last, then challenge pairs, costs, regimes. | FG 831 | agreed | 10 |
| K5 | Experiments like git worktrees: a copy of the strategy, many runs. Keep failed experiments with when and how they failed. | FG 975, GM 2725 | seed, placed in QMX | 10 |
| K6 | Result identity: graph × book version × labeler versions × data × cost model × pair/session universe × experiment config; later as hashes. | FG 941, EXP §1 | proposed | 10 |
| K7 | Sweet spot depends on the book; show a **Pareto frontier** (expectancy versus trade count, robustness versus return, drawdown versus speed, portability versus home specialisation). He: not "only the magical variant". | FG 941, FG 975 | agreed with his wording | **no** (Pareto) |
| K8 | ΔBookUtility: judge a candidate by what it adds to the book; win rate descriptive only; "stale, not false" when book policy changes. | EXP §2 | proposed; "I know it's good" (FG 975) | 10 |
| K9 | Staged tests: semantic gates (no lookahead, timing, entry price available, deterministic replay) → screening → ablation → interactions → sensitivity → locked challenge. Tries controls (preregistration, purged walk-forward, block bootstrap, Holm, FDR, Reality Check). | EXP §4-5 | proposed | 10 |
| K10 | Report: challenge cube pair × session × regime, signal funnel with node fire counts through admission, ablation, redundancy, fragility surfaces, book impact, selection audit. | EXP §8 | proposed | 10 |
| K11 | His testing seeds: "trigger at a given level... a trigger with multiple levels"; agents' reports should "visualize"; "scalper book one, then scalper book two". | FG 902, FG 975 | seed | no |
| K12 | Testing criteria belong in the spec or a test artifact because agents will run tests in the new QMX. | FG 902 | seed | no |
| K13 | cTrader MCP and AutoChartist as an exploratory lab where agents look at charts "like a human" and test hypotheses by hand, never replacing certification. | FG 796, FG 831 | seed and proposed | **no** |
| K14 | "A bot that has ambiguity shouldn't be tested." | GM 3262 | seed | both |

### L. Instruments beyond FX

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| L1 | Strategies come from futures and crypto too; "charts are still charts" is a hypothesis to test, not an assumption. | FG 779, FG 795 | agreed | 10 |
| L2 | A futures strategy tied to an exchange open is not blindly moved to three FX pairs; a crypto funding-rate setup cannot transfer unchanged to spot FX. | FG 795 | proposed | no (examples) |
| L3 | DOM and order flow for crypto and futures; IC Markets cTrader DOM is broker-specific, so record provenance. | FG 796, FG 831, FG 941 | agreed | 10 |
| L4 | Stock-trader sources included with original asset class, venue, target market, transfer assumptions, equity dependencies and a status (`unreviewed`, `partially transferable`, `adapted`, `not transferable`). Never translate centralised volume, equity books, opening gaps or shorting rules into FX. | FG 2388 | agreed | 10 (discipline) |
| L5 | Original-market list: spot Forex, FX futures, other futures, equities, crypto, options, multi-asset, market-agnostic; transferability: native, direct, with adaptation, conceptual only, not transferable, not assessed. | FG 2501, FG 2599 | proposed | no (lists) |
| L6 | Crypto spot added: "I might trade crypto very soon... BTC against USD... Solana... against USD". Futures traders are the main strategy source. | GM 3262 | seed | both |
| L7 | Separate centralised-exchange truth (exchange volume, VWAP, depth, footprint, delta) from broker spot-FX tick volume. Per-market execution contexts (OTC FX, crypto spot, centralised futures). | GM 3938, GM 3987 | used by workers | 10 |
| L8 | Gold as a mini-KB example: a gold video may add a gold note and transferable concepts but no strategy. | GM 2724 | proposed | no |

### M. Mini knowledge bases, catalog and scale

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| M1 | Mini-KBs per topic, pair, session, methodology, prop firm, macro; books and papers feed them best. "One of the huge wins you can have quickly." | FG 769, FG 779, FG 902 | seed | 10 |
| M2 | Two uses: research for building strategies, and his day-to-day reading. Later narrowed: "more like a library than normal day-to-day usage", not colliding with the agentic memory. | FG 796, FG 975 | reversed (narrowed) | 10 |
| M3 | Mini-KBs fill abstract strategies: podcast traders say one sentence and assume the audience knows the method. | GM 3262 | seed | 34 |
| M4 | Mini-KBs to improve and optimise books and prop-firm challenges. | FG 902 | seed | no |
| M5 | Global index "like you have skills, you have a short description"; one-line rows (id, type, description). Later maybe a database at 7,000 strategies. | GM 2725, GM 3261, GM 3262 | agreed | 10 |
| M6 | A README per folder saying what belongs, what does not, relations, evidence needed, examples. "It's not just for me, I think for agents". | GM 2724, GM 2725 | agreed | no |
| M7 | Folders describe what the knowledge is, never which bot made it; queue state lives in Kanban. | GM 2724 | agreed | no |
| M8 | QMX's storyboard: mini-KBs as inspiration thrown on a board when building bots and books. | FG 975 | seed | 34 (one hit, other file) |

### N. Pipeline, tools and bots

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| N1 | Ten-stage video pipeline: discovery → immutable inventory → deterministic extraction (metadata, subtitles, transcript, frames, OCR) → visual analysis → temporal alignment (claim ↔ subtitle ↔ frame) → atomic claims → primitive and role mapping → graph → candidate or entry hypothesis → QMX. | FG 831 | agreed ("knock yourself out", FG 902) | 10 |
| N2 | n8n as a deterministic "filter or funnel in a water pipeline" before the bots; outside the library ("I can just host it in a server"). | GM 2717, GM 2725, GM 3262 | agreed as external intake | 10 calls it "rejected" (see §4) |
| N3 | Leader bot that monitors worker bots; right model for each task; DeepSeek as fast text worker, never visual; no Grok, no Kimi K3. | GM 2701, FG 1280, GM 3262 | agreed | 10 (partly) |
| N4 | Gemini web app as the main visual worker, several tabs in parallel, batched packets prepared by a worker and run in a visible session. | GM 2725, GM 2724 | agreed | no |
| N5 | The `watch` video tool is a targeted evidence probe for short windows, not the backbone ("Best accuracy: videos under 10 minutes"); he asked for a workaround, maybe chunking videos into 10-minute clips. | GM 3261, GM 3262 | open | no (in research 40) |
| N6 | Workers write only to their own staging, never delete, never overwrite silently; destructive tools disabled. | GM 2724 | agreed | no |
| N7 | A curator gets compact packets only (proposed additions, related entries, evidence, conflicts) to stop small-context models over-engineering. | GM 2724 | agreed | no |
| N8 | Specialist fleet → staging → curator → promotion gates as the way to build the library. | GM 3584, GM 4193 | rejected twice | 10 |

### O. Lessons about the process itself

| Id | Idea | Where | Status | 10/34 |
| --- | --- | --- | --- | --- |
| O1 | Compaction ruined each session: after it, the agent turned a folder into software. "what ruined everything was the compaction". | GM 2725, FG 2502, FG 2607 | fact | 10 |
| O2 | Keep durable documents so compaction cannot erase decisions; "I prefer if you have documents you keep around to remind you". | GM 3262 | seed | no |
| O3 | Recovery agents invented quotes: "the true reusable unit is primitive + role binding + ..." and "An entry mechanism without a stop or exit is not yet a complete strategy" are not in FG 795. | AUD §1 | fact | 34 (caught it), 10 (repeats it) |
| O4 | Broad praise is not ratification of every field; "I've actually not objected to anything so far" was direction, not a schema vote. | DOS §6, AUD §2 | fact | no |

---

## 4. Ideas no current file mentions

Checked by `grep -rli` over `risk-sizing/research` and `risk-sizing/*.md` on 30 Oct, including research 40 (written the same morning). "No hits" means the idea is absent, not that the word is. Research 40 already carries the AI-illustration warning, the video-chunking workaround and the law-versus-biology framing, so they are not listed here.

1. **A whole bot used as an indicator** ("a mini scalper for an indicator", FG 796). A unit's output as an input to another unit. Nobody answered it. No hits.
2. **Roles beyond the four:** veto, target, **sizing modifier** and regime detector as roles a primitive can play (FG 1209 summary). "Sizing modifier" has no hits. It matters now that the unit owns sizing.
3. **The five-layer trading plan** (setup, bot plan, book plan, system plan, operator plan; FG 831). His reply: the bot layers were the missing part. No hits for "trading plan".
4. **A Pareto frontier instead of one best variant** (FG 941, FG 975). R10 has "no magical best"; no file has the frontier.
5. **"Regime labels must be available at evaluation time or fitted only on training data"** (EXP §6). A look-ahead rule for context. No hits.
6. **Two-pass sort and four-level source hierarchy** (container, item, evidence segment, derived knowledge; FG 2599). No hits.
7. **Channel dossier and creator-profile evidence** (FG 795, FG 2599). No hits.
8. **Long-transcript economy** with overlapping chunks and compact evidence packets (GM 2724). No hits.
9. **Gemini prompt pack and Gemini as a later checker** of a finished spec against the video (GM 2724, GM 2725). No hits.
10. **Failure history on the identity** ("most bots might not work out", GM 3262).
11. **Corrected successor as the way ambiguity gets resolved** (GM 3262).
12. **Session × pair × bot tables** to find where a bot flourishes (FG 902).
13. **cTrader MCP plus AutoChartist as a hands-on lab** for agents (FG 796, FG 831). No hits.
14. **Indirect source mining** of MQL5 forum comments, parameter names and TradingView inputs (FG 795).
15. **The MIS placement rule** (five tests for central versus in-bot features, FG 941) and his view that MIS has one live version (FG 975).
16. **Folder READMEs and "folders describe knowledge, not the bot that made it"** (GM 2724).
17. **Two lineages** (knowledge lineage versus run lineage) with a curated feedback path (GM 3261).

Where earlier files missed or misread:

- **R10 §1.1 and §2** treat `GM 4065-4067` as gold-mine design turns. They are re-prints of FG 831, FG 975 and FG 2607 (24-25 Aug). Citations stand, dates do not. R10 does say "replay of genesis M975" for 4066.
- **R10 §1.1** places "7,000-strategy scale" in GM 2717/2725. It is in GM 3262 ("this guy told me he has around 7,000 strategies"). R34 places it correctly.
- **R10 §2.1** quotes "the true reusable unit is..." as FG 795. AUD showed it is a recovery synthesis. R34 §1.3 caught this.
- **R10 §3** lists "n8n as required intake" as rejected. In the gold mine he proposed n8n himself and the agent agreed (GM 3261 point 13); he only placed it outside the library (GM 3262). It was moved, not rejected.
- **The 26 Aug analysis brief** (`prompt-gpt56sol-gold-mine-analysis.md`) says "Everything ABOVE good morning is valuable design work". Above good morning is mostly recovery; the design is in FG. It also merges FG 975 content (methodologies, scalpers) with GM 3262 content (7,000, Mind Math Money) under one id.
- **STATE.md:149** remembers "hybrids such as an exit used as a trigger". That phrase is in neither session. The idea is the role-neutral rule (C1, C6); "hybrids" in his own words means combined bots (G9).

---

## 5. What the sessions assumed that no longer holds

Today's rulings from `STATE.md` (CHECKED lines shown).

| Assumption then | Where | Why it no longer holds |
| --- | --- | --- |
| "Do not create Python, YAML schemas, CLIs, Pydantic, tests... or runtime machinery"; the library is prose. | SC "Quality rules"; FG 2607 "not code" | QML is now the library agents use to build runnable units (STATE.md:22); "Plain Python is always possible" (STATE.md:47). His own FG 975 seed ("Python is already suitable", ranges and defaults) fits the new direction better than the August rule. |
| Bots trade, books control bots, BMS accounts; sizing, daily limits, exposure and fallback exits belong to the book. | FG 831, FG 796 | "A unit... entry, exits, its own self-calibrating risk and sizing" (STATE.md:21); "The unit alone controls its trading, risk and sizing" (STATE.md:24). |
| Missing exits are fine because "a boat... will have its own exits under a book". | GM 3262 | A unit needs its own exits to trade. Keep the honesty part: label who added an exit (J4). |
| Markets: Forex and crypto spot; no futures as a target; no position trading. | FG 796, GM 3262, CB | Units span instruments including futures and perps (STATE.md:66, 140); the dictionary "must expand far beyond FX" (STATE.md:148). The transfer-caveat rules (L2-L7) matter more now. |
| QMX validates; STRATS never tests; experiments, ledgers and results are "under QMX". | GM 2725, GM 3261, CB | QML lives inside QMX now; testing is a QML verb (STATE.md:22). The experiment design (K5-K10) has a home again. |
| Leave QMX out; QMX adapts to the library; no adapter. | GM 3262 | Moot: QML is QMX's own library. |
| Knowledge lives in an Obsidian folder outside the repo. | GM 2724, FG 2501 | Units fit the QMX Library with JSON schemas (STATE.md:22); idea records may stay Markdown (R10 §4). |
| Intelligence (live bias, macro) belongs in QMX's UI, not the library. | FG 975 | Still holds in spirit; today's home is journals and the router's market facts (R10 §2.11). |
| The dictionary is GPT's idea but central and to be populated by workers. | GM 3261, GM 3728 | "The dictionary was GPT's idea: a good start, not sacred" (STATE.md:22); "types are defaults, never a cage; the same goes for the dictionary" (STATE.md:43). |
| Pair, session and regime are fixed challenge coordinates, never tuned. | EXP §3 | Units carry their own session profile and per-market calibration (STATE.md:21); the line between tuning and new unit is a current open question (R34 §6 q20). |
| A curator and promotion gates guard library entries. | FG 2388, GM 2724 | Rejected then (N8) and still out for knowledge; promotion now means only his click for units to live (STATE.md:39). |
| The book's "sweet spot" and ΔBookUtility judge a bot inside a book. | FG 941, EXP §2 | "Book" became the pod and guard design, still open (STATE.md:205). The marginal-value idea survives; the object it is measured against changed. |
| Recovery quotes and the 239 entries are trustworthy. | DOS, 1 Sep build | Two DOS quotes are invented (O3); the entries were written by workers he froze, half "needs source evidence" (R10 §2.5). |
