# His rulings in force, as of 4 November 2026

Auditors read this instead of the sources. One line per ruling, in plain words, with its source. Where a newer ruling replaced an older one, only the newer stands here and the line names what it replaced.

## Authority order (the higher one wins)

1. `R` = `D:/QMX-worktrees/audit-ship/RULINGS-2026-11-04.md`
2. `RC` = `D:/QMX-worktrees/risk-plan/tracker/risk-core/STATE.md` (operator rounds of 1 to 3 November)
3. `TR` = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/TRIAGE-2026-11-03.md`, whose top table is his 4 November word, and `VAL` = `.../build/VALIDATION-2026-11-03.md`
4. `US` = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/STATE.md` (operator corrections, midday rulings 1 to 55, sections marked binding)
5. `PO` = `D:/QMX-worktrees/audit-ship/plan-original.md` (the 73), `PC` = `D:/QMX-worktrees/audit-ship/plan-current.md` (the 91)
6. `T` = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/transcript-2026-10-30-to-31.md`, his verbatim words, used to settle a doubt

A source reads `file:line`. "Lead's" means the planner wrote it from his words and he did not reverse it; it binds, but a word of his beats it.

## Whole system and how work runs

- Keep it simple: design for complexity (hard edge cases), never a complex system. [US:20] [T:1264]
- A small solid core that others build on, like Shopify or Wix. Edge cases shape it. [US:89]
- Foundation first: the smallest complete set of parts, so QMX grows on top with no rework. Never call it "minimal viable". [US:75]
- Priority of care: QML first, the trading node second, the MIS third. [US:79]
- Build order: QML, the MIS and the contracts first, then assembled into the node, which comes late. [US:110]
- Everything he says is a seed; the lead may refuse it with a reason. He directs, the lead decides. [US:92] [US:276]
- Bring him only real ambiguity. Settle simple issues and report them in one line. [US:30] [US:71]
- Nothing is set in stone; shipped work is still not removed casually, and every proposal names what it touches. [US:26] [US:153] [RC:147]
- Legacy code is surgical, not frozen: change what is necessary, with a one-line reason. [US:96] [US:105]
- Local first: everything works on This PC alone. Servers extend or stand in, never replace. [US:234] [US:190]
- It must work out of the box for someone who was not in the planning. [US:189]
- Nothing capped: freedom to build any trading algorithm, up to portfolio optimisation. [US:190]
- Every market type is traded as it comes. Replaces the April rules (no leverage, swap-free, no futures). [US:188]
- Markets first: forex, futures, metals, CFDs; cTrader first, Hyperliquid second. [US:162]
- Windows is first class; he prefers plain Windows to WSL unless the architecture truly needs it. The node is the named exception, see the node section. [US:159] [US:187]
- Contracts between parts get their own design: who connects to whom, where, what crosses. [US:154] [US:81]
- He wants the build finished, not widened. Everything before the demo is two PRs. [TR:5] [TR:16]
- Cluster work: six to nine bugs is one to three PRs, not six to nine. [R:26]
- A finding must be justified as a real bug before anyone plans work for it. Not everything goes in the backlog. [R:27]
- The orchestrator never plans; the planner plans, the orchestrator builds. [R:36]
- "The code is his" never means leave a real defect alone. He wrote no line of it. [R:38]
- He lands the stack himself. Nobody else merges. [PC:6] [RC:36]
- Planning on `plan/unit-system`, building on `build/unit-system`. The merge target is decided later, never `main`. [US:282]

## This audit

- Do not throw the code away. Find whether it is right and write down everything wrong before anyone fixes anything. [R:7]
- No fixes in this run; he does not trust the build orchestrator to fix things. [R:8]
- Audit the code, not the PRs. "I don't want to merge slop." [R:9]
- Chunk the work as the plan is chunked. Money code is not a special first case. [R:10]
- Audit against the 73 and against what was added. The plan itself is not above question, because its session was compacted. [R:11]
- Do not hold code to a ruling a newer one replaced. [R:12]
- Autonomy: make the call. A call too heavy that blocks nothing goes aside for him. [R:13]
- Sub-agents do not wait on long tests; the orchestrator runs long checks. [R:14]
- Skylos after fixes, mutmut not now, the first-start dry run waits, CodeRabbit or Greptile perhaps later. None tonight. [R:16]
- Skills are followed to the letter; not every skill is used. [R:17]
- Every agent tonight runs Opus 5.5; no Fable. Replaces midday ruling 16 for this run. [R:18] [US:85]
- Old loose ends and backlog are sorted tonight, not implemented. [R:19]
- The audit also says which code to delete. [R:21]
- His picture is a chief engineer cleaning up after junior engineers. [R:22]
- A code-quality pass was left out of the 3 November round; this audit replaces that ruling. [R:39]

## QML and the dictionary

- A unit replaces the trading bot: one complete algorithm with no separations (entry, exits, its own self-calibrating risk and sizing, its condition needs, session profile, exam baseline, journals), tested as one. [US:21] [US:190]
- QML is upgraded into the library agents use to build units: build, test, promote, monitor. Deep modules, JSON schemas, simple mental models. [US:22]
- No throwaway prototype. Build the real parts. The proof is a dummy unit on the real template, any strategy the lead picks. Replaces his morning "prove it in code first" route and Fable's two-day prototype. [US:70] [US:156]
- "Does it work" means a unit actually makes sense: it self-optimises and leans on few things, unlike a bot. [T:1145]
- Agents write units through deterministic checks, never their own judgement: a compiler or linter in the spirit of pytest. "Favor determinism over non-determinism." [US:157]
- Agents get feedback while they write, the way Claude Code gets a linter error through a hook, with no false positives. [US:81]
- Anything an agent under QMA can do, the copilot can do. [US:77]
- QML, the unit and the schemas are a standard for agents. They never stop a human or a mini app; plain Python is always possible. [US:208]
- Scalper types and dictionary shapes are defaults, never a cage; a custom ML model must fit. [US:204]
- Design for agents, not humans: agents run this through workflows, skills and hooks. [US:209]
- The gold mine session's intent for QML is a key seed. Do not set it aside. [US:170]
- The dictionary's form is code built by builders. Its first content wave (port the 239, then families beyond forex) is in the same build, no cap. Later growth goes through one authoring door, checked by the same scripts. Lead's, answering ruling 13. [US:137] [US:82]
- The dictionary is rebuilt in form; the 239 entries and their ideas are kept as seeds, never lost. Lead's, from his words. [US:374]
- The dictionary must expand far beyond FX. [US:309]
- Publishing the ported dictionary to main is his click; it waits for the UI session's card. [TR:59]
- The same unit on the same pair on 1m and 5m is one correlated idea, not two bets. Replaces his 20 October seed. [US:307]
- Everything about a unit is saved and traceable to its origin: chat, video, post, article. No vibe trading. [US:212]
- Only he promotes, including market versions agents work on. [US:190] [T:1105]
- A market's own version is earned from a record the general unit built on that market; it never appears from thin air. [US:281]
- "System 1" and "System 2" are explanation names only. Do not raise them. [US:169] [US:295]
- "Regime" and "volatility state" are ruled words; "Fixed", "Follows the market", "Follows its record" have his default yes. [TR:58]

## QMB

- QMB is not live trading. Backtest and stress are one world, live on the node another. [US:23]
- QMB is the first mini app: built as a foundation he can improve, replace with a new version, or run in several variants. [US:93] [US:94] [US:120]
- Agents call QMB as a tool and never hand-roll backtest code; the aim is professional quant level. [US:97] [US:242]
- Build on, enhance or scrap, with the reason. Lead's fix from his "toss or rebuild": the core loop is rebuilt around the unit, working parts kept. [US:113] [US:374]
- All instrument types by default. [US:244]
- No limit on lookback. Post-COVID is a default, never a cap. Find and remove the limit. [US:207]
- Historical data is the Library's job; assume it will be there. Replaces his earlier ask to check data sources from QMB. [US:160] [US:245]
- Holdouts are his choice per study, off by default (rulings 136 and 137). Lead's. [US:374]
- When strategies are nearly free, judging is the product. Look at how professionals judge; do not be too strict. [US:29] [US:248]
- Judge from historical and paper together, which lowers overfitting. [US:249]
- Judging is a skill: hooks and deterministic scripts calling QMB. Agents judge from results and may propose; proposals show in the UI. [US:251]
- The judge may label a unit tested or parked by itself. Every move toward paper or live is his click. Lead's call LC-B-30, kept after the fix-check. [US:46]
- Luck is not an argument: QMB's workflows prove or enhance the edge before a unit reaches demo. Which units to promote is not the risk session's job. [RC:357]
- A study's gap rule beats a chat's `allow_gaps`, because it protects evidence. Decided, one-line fix in backlog. [TR:57]

## Journals and agents

- One trading journal per unit, from creation through stress, paper and live. [US:25]
- Journals are not one simple row shape. A journal spans instruments, brokers, accounts, platforms, nodes, and paper or live; units go back to paper. Design it in depth. [US:166] [T:903]
- The journal is the unit's DevOps layer. Record trades taken, signals not taken, missed trades. Agents may write analysis there. [US:217] [US:218]
- A separate journal holds market facts (spread, fees, slippage, sessions per instrument and broker), so unit journals do not duplicate them. [US:219] [US:220]
- Performance studies over time and portfolio work come from journals. [US:221]
- Everything a node produces comes back to the Library: readings, logs, journals. "Don't ruin its core." [US:131]
- QMA v2 is in scope, surgically. The copilot already reaches nearly everything and discovers new tools. [US:77] [US:96]
- Agents carry the slow lane between sessions: unit review, market review, a pre-session shortlist, tagging units to markets, MIS check, daily review, node watching. They propose and explain, numbers decide, he approves, and agents are measured. [US:121]
- The fast lane (unit, fast readings, kill switches) has no agents. Agents never feed it. [US:121] [US:129]
- Every agent can use cTrader's MCP, on demo accounts only. Replaces the risk session's flag that order tools need an operator-only guard, for demo. [R:37] [RC:285] [TR:65]
- The skipped agent-step file write is one of the engine fixes; script steps writing files is intentional. [US:128]
- Methodology comes later, after this session and the risk session. [US:134]
- His agent department (agents as traders, a Shepherd, copilot ingestion) is not this build's. [RC:183]

## The MIS

- The MIS reads and publishes, units pick, none needs it to trade. [US:190]
- The router only routes and never switches units on or off. The unit alone controls trading, risk and sizing. If the router is down, the unit keeps trading. [US:24] [US:224] [US:225]
- Guards work independently of the router. [US:226]
- The MIS gets defaults now and room for models he trains later. A core with no training; training and research happen later in the Lab. [US:80] [US:135]
- It holds for every instrument in scope, not only forex. [US:80]
- It is shaped by trading style, then timeframe, then the data a market offers. [US:280]
- Lead's answer he did not reverse: indicators first with freshness, models behind the same reading shape, the MIS runs where trading runs and publishes back to the PC, its screen a section of the node mini app. [US:127]
- Agents read markets their own way beside the MIS; disagreements go to him. [US:129]
- Workflow templates read the MIS's logs, not the MIS model. [US:164]
- MIS logs go to the Library. Add it simply where missing. [US:131]
- Any correlation ledger is "internally external" to the unit; where it sits is the risk session's. [RC:345] [US:313]

## The trading node and servers

- The node is "just a server": it sets itself up, sets the MIS up, checks, monitors, and heals itself. It holds units trading autonomously with kill switches. [US:99] [US:110]
- Only the node sends orders, by design, so it is contained and the kill switch works. [US:99]
- It sets itself up on a server of his choice with one click, for a good trader who knows nothing technical. His only jobs are renting and naming the server and entering its keys in its own window. Replaces "a wizard or one click". [R:30] [US:314]
- Nothing may break the local-first stack or the Library and its backups. [R:30]
- It runs on This PC first, then a server. [US:168] [US:314]
- Linux, because most servers are VPSs; WSL on This PC is an acceptable fallback. [US:99] [US:187]
- The node may start afresh; about 97,000 lines is far too much. We may delete a lot. [US:99]
- The old-code cut waits for the full demo proof, C-14's real run and C-15. Nothing is deleted before its replacement passes. [VAL:45]
- The node and QMB are the first two mini apps. [US:120]
- He deploys from his machine; results come back; it is monitored; kill switch from him. [US:168]
- Clocks: nodes in different regions keep different local times and must be monitored together. [US:167]
- DevOps builds on the wrap-up session: OpenObserve, agents read-only, one telemetry switch, the connect dialog. [US:118]
- Compute is largely done by the local-first stack. Build on it. [US:111]
- Several nodes and routers must be thought through; one node to start. [US:230] [US:314]
- CCXT opens up beyond spot reads (perps, trading). Hyperliquid gets designed. [US:100] [US:114]
- Design for futures accounts and every instrument now, so he is spoiled for choice. Placeholders or what works; no decision from him now. [US:101] [US:115]
- Algorithms need order-flow data, not charts. He does not want to pay for a platform now. [US:83] [US:115]
- Sign-ins come later; nothing in the build waits on the cTrader sign-in. [US:112]
- The real-money-key decision is dropped. Brokers sign in on their own pages. Ruling 135's refusal on This PC is a code fact to handle technically. Do not raise it. [US:161]
- His live broker logins are separate accounts held in his browser, never in QMX. The forged live account record item is dropped. [R:29] [TR:11]
- C-21, the path to bind a live account, comes later. He refused a change to the workflow engine for it until someone has thought it through. [R:31] [VAL:43]
- Each host gets its own pass key before any live account (C-28). [VAL:45]
- The shared pairing key stays unless he says otherwise. It reaches only the data read, not orders or money. [R:32] [TR:14]
- PR 1 before the demo is C-35, C-29 and C-38; PR 2 is C-14's rehearsal. Then G-DEMO. Replaces the dispatch order below that table. [TR:16]
- An installed node must find its calendars and cTrader definitions; a host restart must start the node again (C-38). [TR:10] [TR:13]
- Before he lands the stack: A1 price scale, H1 vault owner-only, I1 lock order. Before the first real trade: E1 records, D1 cache keys, B1 order id length, B2 partial fill, B3 filled read as absent, B4 stale quote, C1 status word. [TR:24] [TR:31]
- The kill he presses must act before a real trade. His resume is journalled. [TR:39] [TR:40]
- Hyperliquid waits for G-WALLET. CCXT records are not landed before then. [TR:49]
- Deployment files on a server while This PC is primary go in C-19 at G-SERVER. [TR:12]
- The MIS board relay not started is safe today, because units fall back to every admitted market. [TR:49]

## Workflows and mini apps

- "Most things can become mini apps." Each part is judged core or mini app on that core, with defaults out of the box. [US:94]
- Workflow templates: build them. They can be removed or improved later. [US:164]
- Take the workflows from the Hermes sessions and enhance them, beside existing and analyst templates. [US:312]
- The workflow engine is his "baby": understand it fully first; every improvement rests on the ideas of "QMA V2 Workflow System Design 2"; nothing appended without a core reason from that session. [US:128] [US:133]
- The mini-app core is the other baby: understand its intent before touching it. The work is mostly connecting. [US:133]
- Fix the mini-app core where it truly blocks; defaults such as the three-error breaker stay unless they truly block. [US:125]
- Mini-app limits exist by design, for logging and monitoring; they are not bugs. [US:96]
- Engine changes U1 (a) to (f): not blocking, ask once, batched, after G-DEMO. Builder model stays strong by default. [TR:55] [TR:56]
- UI: notes and design proposals only. No UI code is written or edited. [US:123]
- Build prompts follow the QMA v2 templates; Claude Code by default, a DeepSeek option kept. [US:126]

## Tests and code size

- No "every part must prove itself" machinery, no hundreds of tests. [US:20] [R:15]
- Tests can pass and still prove nothing. He suspects 40,000 lines of test code is too much. [R:15]
- Every change keeps the shipped tests green; the standard is near zero errors. [US:132]
- "Coded is not built until run" is a direction for the lead, not a ruling. [US:190]
- The old mistake must not repeat: building what he did not ask for, or building more on top of something simple. [US:180]
- About 97,000 lines is too much for what the node does. [US:99]
- Light verification is his rule of 15 October. [PC:27]

## Risk and sizing boundaries

- The build's risk and sizing pieces are placeholders, not decisions. Their values (0.5%, 2R, 48 bars, empty halts) carry no weight. Do not report build-level slips unless the plan itself makes them persist. [RC:290]
- Sizing and exits are clearly labelled placeholders, on backtest and demo alike; the risk session gets the list to rip out. [US:185]
- The proof uses a placeholder unit and market. [US:186]
- Exit methodology, stops, targets, profit caps, account-wide halts and probability exits belong to the risk session. This build leaves room: the unit owns its exits and the socket takes whatever comes. [US:306]
- The Book and correlation control belong to the risk session. [US:313]
- The signed stop-move distance belongs to the risk session. Adds no risk beyond the held stop. [R:28] [TR:9]
- The kill line stays a placeholder until the risk session; the new node acts through `PLACEHOLDER_KILL_EFFECTS`. [VAL:15] [VAL:45]
- Kill switch and SQS stay; exits are never blocked. [RC:320]
- The only automatic move in trading is a risk rule stopping a unit, logged and monitored. [US:200] [US:46]
- The Book/BMS is not sacred: anything better may replace it. "Overhaul" was his word for nothing off limits, not a request to overhaul. Replaces "the Book/BMS is the skeleton". [RC:147] [RC:159] [RC:353]
- Risk works at several levels: unit, cluster, methodology, portfolio, with overlaps. [RC:354]
- Each unit type gets its own sizing template with reasoned defaults. Baseline first. [RC:355] [RC:356]
- Every number needs a reason; no key setting left blank; risk per trade stays configurable. [RC:317] [RC:318] [RC:341]
- Every change in size needs a stated reason. [RC:361]
- Brakes first, accelerators second; keep house money. [RC:319] [RC:364]
- More than one brake, each saying what is breaking. Do not confine anything yet. [RC:30] [RC:360]
- Costs per market, instrument, timeframe and time must be known to the unit and feed Kelly. [RC:342]
- Every number shown must include fast invalidation. Stop versus fast invalidation needs its own thought. [RC:321]
- R fixed at entry is not accepted by him: "We shall see about that." Dollars or percent, pips or points, is still open. [RC:322]
- The floor is almost never touched, only by black swan or real failure. The BMS keeps a buffer. [RC:358]
- Live drift never means pulling out on one bad day; size down slowly. [RC:32]
- Performance with intention; survival is a constraint, not the goal. [RC:162]
- The deliverable is a malleable, self-configuring, extensible risk-and-sizing template for the unit, shipped through builders. Technical lens first, numbers later. [RC:29] [RC:169]
- The Lab and MCPs must use that template without rework; agents read risk state and propose, out of the order path. [RC:184] [RC:189]
- QMA changes are flagged, not designed, by the risk session. [RC:159]
- Component ideas turn into dictionary entries in a later slice set. [RC:210]
- Seed $500, split open. Proposals only: $300 and $200, multi-position units, ORB first. Do not grade code against them. [RC:315] [RC:327] [RC:335] [RC:336]
- Still open for him: step down and back without his click; the BMS raising the kill; agent isolation; live at level 1; profile against Book words; how rare the floor is; what happens at the floor; night paging. Do not grade code against them. [RC:277]

## What never happens

- Agents never reach a live account. [R:29]
- His live logins are never in QMX. [R:29] [TR:11]
- Nothing enters live without him: no variant, no unit. Minimum-lot auto-promotion is rejected. [US:200]
- No agent in the fast lane. [US:121] [US:129]
- No news trading for now. [US:165]
- No UI code in this build. [US:123]
- No engine change for the live-host agent refusal until he says yes. It ships as a labelled placeholder and live binding stays closed. [VAL:43]
- The real-money-key question and System 1 and 2 are not raised again. [US:161] [US:169]
- Firecrawl is never used or mentioned. Replaces "Firecrawl last". [RC:214] [US:27]
- Old Hermes logs are not read raw; they hold credentials. [US:350]
