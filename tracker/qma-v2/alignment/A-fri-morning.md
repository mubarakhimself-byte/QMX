# Alignment part A: Friday 16 Oct, morning and midday (transcript lines 0-657)

Written 2026-10-18 by one Opus 5.5 agent, read-only except this file. Nothing committed.

**Sources read.**
- The transcript `5efecf49-2c39-4a71-bfb7-8ce9c1e6d0dd.jsonl`, lines 0-657 (0-based). I read every operator message in full: lines 3, 77, 273, 323, 456, 488 and 542. I also read every assistant reply, every subagent hand-back, and the two correction briefs the lead sent to the Fable agent (438 = corrections 1-13, 464 = corrections A-K).
- Later operator messages (lines 658 onward), grepped only to follow threads forward.
- On disk: `26` rulings 1-104, `AUDIT-2026-10-18.md`, `RECOLLECTION-2026-10-18.md`, `HANDOFF-2026-10-18.md`, `BACKLOG.md` and `UI-HANDOFF.md`; the spines of all three architectures, plus `SOLUTION-DESIGN.md` §12-13 and the Cua section; the relevant wayfinder tickets; `36` S11; `37b` §6.2.
- Merged code on `origin/engine/base` (`132169c7`), read with `git show`, `git grep` and `git ls-tree`.

**Settled facts I treat as true** (from the brief):
- No QMX usage or spend caps of any kind. The `$5 max_budget_usd` and the `0.5` background cap are bugs.
- No opencodex or CLIProxyAPI. The pool and load balancer are built in-house.
- The engine PRs are merged into `engine/base`.
- No Fable for planning agents. Tests run on haiku through the plan login.

**Shape of this slice.** Most of the slice is the lead running research agents. The operator's own words come in six long dictations. Rulings 1-21 in `26` are this slice, paraphrased. Rulings 22 onward are parts B and C. Several things the lead said in this slice became disk facts without his ratification. The worst is the "50% background cap". I list those as items too.

Line numbers are 0-based JSONL indexes. "Code" means `origin/engine/base`. Paths are under `tracker/qma-v2/` unless stated.

---

## 1. LEDGER

STATUS values:
- **shipped**: in merged code (file named).
- **designed**: in an architecture AD or design section.
- **file-only**: in research, a ticket or the backlog, but not in an architecture.
- **chat-only**: nowhere on disk.
- **reversed**: undone by a later ruling or line.
- **superseded**: replaced by a later design.

Where two apply, the row names the main one first.

MATCH says whether the disk version means what he meant: yes, partial or no.

### 1a. Goal, method and process (lines 3, 77, 273, 488)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-1 | 3 | "design the workflow system... together with the methodology and wire it in into QMA" | shipped (engine: `qmx_engine`, EP0-14 merged) + file-only (methodology: tickets `methodology-umbrella`, `methodology-builder` open) | partial | All of QMA v2. The methodology half is still owed (HANDOFF "Open items": B26-B29). | none |
| A-2 | 3 | "the skills to use today will be the Wayfinder skill... potato mod skills" | reversed (ruling 101: no poteto-mode, no skills for the planning lead). The Wayfinder map exists (`wayfinder/`). | n/a | How the planning lead works. | none |
| A-3 | 3 | "graph engineering, loop engineering... leverage this a lot" (ruling 2) | designed (engine spine "Design Paradigm"; loops capped AD-5 and AD-16) + shipped (`core/loops.py`, `core/ladder.py`) | partial | Engine and templates. The clipping's main warning was not adopted as a rule: a graph built before you have watched the work freezes wrong assumptions, so start from traces. See A-95. | none |
| A-4 | 3 | "we were using LangGraph... since you're using the Claude Agent SDK, we don't have access to LangGraph" | shipped (own engine, AD-1). The 16 lost LangGraph features are listed in `03` §9 and covered by AD-7, AD-11 and AD-16. | yes | Engine. | none |
| A-5 | 3 | "try an agent to do probabilistic thinking in terms of the workflow" | shipped (`templates/_shared/calibrate/`, R7). The spines use [retrieved]/[remembered]/[inferred] labels. | yes | Graders, every research template, explainer output (confidence has to show in the UI). | From the clipping: rerun in fresh sessions and read the spread; ask for candidate answers and ranges first. |
| A-6 | 3 | "We also, I think, need to design the lab today" | designed (`architecture/lab-and-pods/`, AD-1 to AD-17) | yes | Lab, engine, Library, QMB. | none |
| A-7 | 77 | "use a bloody browser... click through... like a human" | file-only (memory rule "browser-read sources"; research 01, 02 and 11 were read that way) | yes | Research method only. | none |
| A-8 | 77 | "BMAD... leverage it under QMX... you're not doing agile-driven development" (ruling 4) | file-only (`01`, `02`; ticket `methodology-builder` open). Engine AD-22 adopts only BMad's six build phases plus Pocock's loop-me. | partial | Builder, skills, methodology, system prompts (B28, B29). | none |
| A-9 | 77 | "methodology compiles all the other two. It compiles organogram and workflows" (ruling 1) | file-only (ticket `methodology-umbrella` open, blocked on five other tickets). | partial | Engine AD-35 says the home sets "the methodology's autonomy row", a table no file defines. System prompts (B29), packs and homes all key on it. | none |
| A-10 | 77 | "workflows is mostly autonomous work" (ruling 1) | designed (AD-9, AD-16, AD-17: nothing waits for him; ruling 57) + shipped (`admission.py`, `core/ladder.py`) | yes | Inbox, UI, templates. | none |
| A-11 | 77 | "look at how Claude Code handles dynamic workflows" | file-only (`03`: the Workflow tool cannot be the engine) + designed (AD-5 `claude_workflow` kind, off) + shipped (registry kind present, `available` false) | yes | Engine node kinds. | none |
| A-12 | 77 | "plain copilot... compilation of all across; the lab copilot needs its own methodology... portfolio, we are having a rethink" (ruling 5) | designed in part (engine AD-35 homes; Lab AD-14 pack loaded by the hub) + file-only (B26 copilot methodology owed) | partial | Copilot prompts, packs, autonomy per home. | Lab gets more freedom; Portfolio gets more instruction (B26). |
| A-13 | 77 | "so many user journeys to be generated... from trading to... idea generation" | file-only (archived `06`, `12` §a only) | partial | Methodology, templates, UI journeys, QA (B47). | Trading to ideation journeys. Not carried into any live file. |
| A-14 | 89 | "the daily driver for the copilot... I think the BMAD would be good" | file-only (`02` picks: router, grilling, ketchup, bro) | partial | Copilot methodology (B26), standing orders skill. | none |
| A-15 | 89 | "storyboard... vibe coding, but for trading strategies... we need to ground ourselves with methodologies" | designed (Lab AD-2 `board` kind; engine AD-11 selected-subgraph runs) + shipped draft template `l1-idea-to-first-result` (needs `qmb-door`) | partial | Lab editor, builder, UI board. See A-78. | none |
| A-16 | 89 | "workflow templates perhaps, because I'm seeing some, especially for strategy generation" | shipped (31 templates, `qmx_engine/templates/`, TP1-TP4: 9 published and disabled, 22 drafts) | partial | Every quant layer. Names and scope were later criticised (line 883; ruling 35). See A-47. | none |
| A-17 | 89 | "Structuring 40 Million Documents... we might also use that to design our library" | designed (Library AD-8: parse-first graph, refusal ladder before any model) | yes | Library search and copilot answers. The Library is not built; the engine runs on a fake. | none |
| A-18 | 89 | "Kapathi... it's more about output... I don't want to read... blocks of text. So we need also a methodology of output" | file-only (see A-37) | partial | All outputs. | none |
| A-19 | 92 | "these things shouldn't be... stuck to one model... any LLM... past March 2026" (ruling 3) | designed (engine AD-13 roles, not models) + shipped (`roles.py`) | partial | Code residue: `settings.py` keeps `claude/fable` in the strong ladder and a Kimi test default (AUDIT; rulings 87 and the haiku rule). Skills are not yet in the open format with QMX verbs (the old "skill format" ticket was folded into `methodology-builder`). | Some clippings are vendor-specific; the design must not be. |
| A-20 | 92 | "how does the Copilot create, maintain, and... delete mini apps? How are mini apps handled currently?" | designed (engine AD-19, SOLUTION-DESIGN §12) + shipped draft `ma-mini-app-lifecycle` (needs `sandbox`, `app-op`). `apps_archive` in `qmx_control/service.py:1017` is a stub that returns "unavailable". | partial | Mini apps, Library, harness tool rows (H17), UI Apps page. | Delete becomes archive (A-40). |
| A-21 | 92 | "The UI is actually going to be coded today... some things in the back end that are missing. For example, the lab" | designed (`UI-HANDOFF.md`, running list) | yes | UI session. | none |
| A-22 | 92 | "the lab... Jupyter notebooks with a node-based editor, with... Visual Studio Code... build neural nets... experiment... use the workflows... inside the lab" (ruling 6) | designed (Lab AD-1 to AD-9; notebooks AD-9; ML AD-7; Graph and Code AD-2). No `qmx_lab` package in code. | yes | Lab, engine, QMB, kernels and sandbox. | Run workflows inside the Lab; hypotheses; neural nets. |
| A-23 | 92 | "I have MT5 installed. It can click through and set up a strategy, use MT5 instead of QMX... instead of us rebuilding" | designed **against** him: engine AD-33 and SOLUTION-DESIGN's Cua manifest say "deny (always): broker, MT5, cTrader, prop-firm windows and origins" | **no** | Computer use (B17, B37 video-to-cTrader trial), the money gate on desktop actions, B39 broker connections. | Agent sets up a strategy in MT5 so QMX need not rebuild it. Demo click-arounds were allowed by the 10-13 Q1 ruling (BACKLOG). |
| A-24 | 92 | "memory should be considered, especially for the workflows... autonomous... have a deep study on LangGraph... deep agents" (ruling 8) | designed (engine AD-18 memory port, AD-26 self-improvement; `03`, `28`). Code: `memory/__init__.py` is one docstring line. | yes | Engine, Library `memory-row`, self-improvement. | Workflows run unmanaged, so memory must not need a human. |
| A-25 | 92 | "read the unread sources... recover deleted designs... I don't know what that means" | designed (B53 recovered: `run_scope` became AD-11 selected subgraph; `trigger_fires` became AD-10; `lessons` became AD-18 and AD-26) | yes | Engine. | He did not understand the jargon. Plain words are a standing need. |
| A-26 | 273 | "a Fable 5.1 agent... designed for complexity... use CIS and... Wayfinder" | reversed (ruling 87: no more Fable). Outputs archived (`archive/2026-10-16-methodology-drafts/06, 07, 12, 19`). | n/a | Planning process. | none |
| A-27 | 273 | "five types of quants... researcher, trader, developer, portfolio manager... I've forgotten the fifth" | chat-only: the lead *assumed* "risk quant" (line 292). He never confirmed it. No later operator line mentions it. | partial | Template families (the RK risk set exists), journeys, methodology lenses. | The fifth lens is unconfirmed. |
| A-28 | 273 | "the copilot in the literal name is meant to help me consider different angles" (ruling 5) | file-only (26 only; methodology owed) | partial | Copilot methodology and prompts. | none |
| A-29 | 273 | "clearly see what are the central pieces, what is dependent and what is independent" | superseded (`07` and `19` archived; the three architectures now hold the central contracts) | yes | Planning. | none |
| A-30 | 488 | "I might require you to have this built out to death. Not in this session, but plan it through" | superseded (later rulings 33, 73, 84; built through the EP program) | yes | Planning. | none |
| A-31 | 488 | "maybe have some other agents for advice... you know what, figure it out" | file-only (process, done with reviewers) | yes | Planning. | none |

### 1b. Organogram, sessions, tools and packs (lines 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-32 | 323 | "Sessions have no home. What? No way... How did we miss that?" | designed (engine AD-35: `home {kind, project_id}` in `qmx_control.session_homes`, write-once; UI-HANDOFF §1.2). Not in code: no `session_homes` on engine/base. | yes | Memory scope, packs, badge, UI `absorb()`, methodology autonomy row. The ticket `wayfinder/tickets/session-homes.md` still says "no architecture covers it", which is stale. | none |
| A-33 | 323 | "the Copilot issue is that in the UI... a session in the lab or in the portfolio... can also be brought back in the normal Copilot hub... back and forth" | designed (AD-35: every surface opens and continues any session; "open in its home" is the way back) | yes | UI, control routes. | Back and forth both ways, not one-way. |
| A-34 | 456 | "Think of the Copilot Hub as just a place... resuming it in the Copilot UI... it's still using the context" (ruling 12) | designed (AD-35: opening elsewhere never changes the home; packs travel) | yes | Same. | Lab session resumed in the hub keeps Lab context and tools. |
| A-35 | 456 | "tools for the lab are different from tools from the normal copilot... the general one should be able to have the capabilities for the copilot for the lab" | designed (Lab AD-14: the hub loads the same `qmx-lab` pack; tool rows need H17) | partial | The harness tool table (H17 grant), Portfolio tools (not designed). | none |
| A-36 | 456 | "one thing from the portfolio, one thing from the lab... a workflow... a mini app, all that is in one session... should be able to handle that" (ruling 12) | designed in part (AD-35 "a combined session keeps its one home while loading other packs"; closed ticket `capability-packs`) | partial | The ticket says "packs are fixed at launch, so adding one is a relaunch". A mini app's own tools have no path into a chat at all (A-38). Combining on the fly is not designed. | Mixing four sources in one live session. |
| A-37 | 323 | "Portfolio... a watcher for now... again goes back to the templates... workflows... scripts. Most of them might actually be scripts" | shipped drafts (`p1`, `p2`, `pp`, `dc`, `gw`, `rk2`, `rk5`, `rk8`; all need `trading-node` or `risk-session`) | yes | Trading-node readers, the risk session. | none |
| A-37b | 323 | "Lab and portfolio... we need to run on them" (real backends, not demo) | designed for the Lab only. Portfolio has no architecture of its own: the Lab's pod panel, templates and NodePort reads cover parts. | partial | UI Portfolio screens. UI-HANDOFF §2 says "do not wire yet". | none |

### 1c. Mini apps and plugins (lines 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-38 | 323 | "the plugin thing is just for mini app... building a plugin for each mini app... leverage the plugin system as a contract towards the mini apps" (ruling 10) | designed (engine AD-19: a pack folder that "is a valid Claude plugin") | partial | The harness loads exactly one SHA-locked plugin (`qma/harness/home.py:73 PLUGIN_SHA256`). `HARNESS-REQUESTS.md:31` deliberately does not ask to change the plugin lock. `37b` §6.2 records the gap: "no rule for when a newly enabled app's tools reach a running chat". So the contract's main promise, that copilot and agents reach an app "without custom wiring", has no load path. Ruling 24 (don't touch the harness) and ruling 39 (the only exception is the pool) collide here. | none |
| A-39 | 323 | "the plugin thing is just for mini app" (not general Lab and Portfolio plugins; B31 re-scope) | designed differently: Lab AD-14 calls the Lab pack "one Claude-SDK plugin `qmx-lab`". In practice it ships as tool rows in the one `qmx` tool table. | partial | Words only. "Plugin" means two things across the specs. | none |
| A-40 | 323 | "I wouldn't like mini apps being deleted... we can archive them... mini apps have dev ops... observability, logging" (ruling 9) | designed (Library AD-6, engine AD-19 `archived`; SOLUTION-DESIGN §12 `[health] probe`). Code: `apps_archive` stub. | partial | Archive is designed. App DevOps is thin in the spine: only a health probe. Logs, incidents and the doctor path live in `14`, `37b` and the MA template's "left out" list. | none |
| A-41 | 456 | "creating it requires us to write code... How do you know that a mini app will work?... connected to the UI? Is it rendering properly in the UI?... Shopify... VS Code extensions" | file-only (`14` §2.6 `qmx app check`, 12 steps with a UI render check; `37b` §6.2 adopts it) + shipped draft `ma-mini-app-lifecycle` (render check of four prop states, needs `sandbox` and `app-op`) | partial | No AD names `qmx app check` or the render check. The engine test gate (AD-11) is generic. | Will the app render? Is it set up properly? Is it wired to the UI? |
| A-42 | 456 | "mini apps can produce input and taking output from fellow mini apps or from other things external and internal... APIs... webhooks... use mini apps output for themselves" | designed (AD-19 `feeds/provides/emits/accepts`; webhooks through the gateway). Code: `app_op` unavailable; webhook triggers "come with L5" (`triggers/rows.py`). | partial | Gateway, engine bus. An app feeding its own output back (a self-loop) is not addressed. | Self-feeding app; external webhooks. |
| A-43 | 323 | "some mini apps are most likely going to depend on the lab. In fact, most might" | chat-only as a design rule (AD-19 says apps meet only at declared edges; nothing says how an app calls Lab services or nodes) | partial | Mini-app contract and the Lab service. | Most apps depend on the Lab. |

### 1d. The Lab (lines 92, 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-44 | 323 | "the idea for the lab... is just freedom of creativity" (the assistant reframed this as "Lab = nothing asks except money and publishing out") | designed (Lab AD-13) | yes | Autonomy rows, the builder, triggers. Ruling 80 later made creation human-driven first (publish and enable ask once). | none |
| A-45 | 323 | "different versions of the MIS or specific versions of the MIS... different variants of a given unit... indicators... ML... neural networks" | designed in part (Lab AD-7 slots, including `regime` on an MIS config; AD-16 identity table; AD-17 labelers reach the node as candidates; `bc-build-a-component` draft) | partial | MIS editing is only "candidate labelers" promoted in Portfolio (the MIS UI lives in Portfolio, `10`). MIS variants in the Lab, as he described, are not designed. Ruling 14 parks node depth. | MIS variants per scalper type (`09`). |
| A-46 | 323 / 456 | "the lab is QMX's core feature... Not just one of... it has everything. It should have everything" | designed (Lab spine) | yes | Everything routes through the Lab; mini apps depend on it (A-43). | none |
| A-46b | 323 | "the lab also has to produce stuff that perhaps goes into the portfolio" | designed (Lab AD-12: paper ends the Lab line; promotion card; two clicks in Portfolio) | yes | Portfolio, node. | none |

### 1e. Workflow engine, failure, notification (lines 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-47x | 323 | "I would prefer combining Claude, LangGraph, and... the Hermes agent... cron jobs... scripts" | shipped (engine core, `triggers/` cron, catch-up, quota, preflight; script nodes; AD-10) | yes | Engine. | none |
| A-48 | 323 | "we just need to make sure we have logging, observability... the copilot maybe look at what happened, how it happened" | shipped (`ledger/spans.py`, `service/explain.py`, AD-15 one trace per run) | yes | UI run timeline, copilot tools (`workflow_runs_explain`). | none |
| A-49 | 323 | "is RLM being used in QMA V2?" | designed (AD-5 `rlm` kind). Code: kind present, unavailable. Template `rs8` is a draft that needs `rlm`. | yes | Sandbox, kernel (Lab AD-9 shares it). | none |
| A-50 | 456 | "who writes the workflow engine? Who monitors it?" | shipped (builder agents per PR; merged) + designed (AD-16 watchdog, doctor) + shipped (`nodes/doctor.py`, `core/ladder.py`) | yes | none | none |
| A-51 | 456 | "how am I notified if something fails?" | designed (AD-17 inbox; severities; digest) + shipped (`ledger/inbox_table.py`, `service/inbox.py`). The lead promised a phone push at line 482. Later ruling 34 (phone later) and ruling 77 (notifications are UI-side) changed that. | yes | UI notifications. | none |
| A-52 | 456 | "if something fails at a step... how do we make sure we are not going to be reworking our logic? Or reworking the entire thing... costly" | shipped (memo `ledger/memo.py`, AD-7; failure ladder `core/ladder.py`; doctor) + designed (replay fork AD-7 B-82; fix-set and guard-set AD-26). Code: no `runs.replay`, no champion logic. | yes | Self-improvement. | Costly reruns: a failed step 7 never reruns steps 1-6. |
| A-53 | 456 | "shepherd-agents.ai... academic paper... some sort of harness" | file-only (`13`); ideas absorbed into AD-8 effect classes and AD-7 replay | yes | none | none |
| A-54 | 456 | "Prime Intellect... prime-agent" (for RLM) | file-only (`13`) + designed (AD-5 `rlm`) | yes | none | none |

### 1f. Methodology, builder and folders (line 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-55 | 456 | "I should be able to create a new version... a specific thing for macro analysis or... for specific pair... the same way BMAD allows me to create specific agents, specific workflows... the Claude skill writer skill" (ruling 18) | designed for workflows (AD-22 builder; variants as overlays) + shipped (`definition/overlay.py`). Skills, agents and methodologies have no builder: ticket `methodology-builder` is open. The plugin ships only `qmx-overview`. | partial | Skills format, methodology, Library `skill` and `methodology` kinds. | Macro analysis for one pair (worked as variant examples in `15`, `16`). |
| A-56 | 456 | "folders and agent... inside QMX workflows... organization is paramount... folder as an agent... Vercel" (ruling 19) | shipped for workflows (AD-2 folder; every template is a folder) + designed for apps (AD-19). An agent as a folder (B32) is not designed beyond packs. | partial | Agents, skills, packs. | none |
| A-57 | 323 | "Mubarak mod. Huh, what the hell is that?" | file-only (ticket `mubarak-standing-orders-skill`, open, AFK, never written) | yes | System prompts (B29). | none |

### 1g. Strategy funnel and templates (lines 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-58 | 323 | "videos, we can use the watch skill... start with a watch skill... understanding what the video is all about... some are very short, some just hint, some are very complex... podcasts, some are useless" | shipped (`templates/a-fill-the-library`: intake, captions with `yt-dlp`, triage into useless, hint, component, full or knowledge, keep the holes) | partial | The template's README "Left out": no frames or visual pass (no `watch`), no Whisper, no TradingView, no Instagram saves. | The five content types he named are handled by triage. The visual side of a video is not. |
| A-59 | 323 | "pour as much garbage as we have... the funnel is meant to produce... strategies that go into demo trading or paper trading" | shipped A (published, disabled, manual trigger only) + shipped draft `b-build-and-prove` (needs `qmb-door`); ends at paper (ruling 29, Lab AD-12) | partial | Template A: "Expanding a playlist, a channel or a saved collection: it needs his approval. Each such URL is one row." That clashes with "pour in garbage", with ruling 57 (nothing waits for him) and with ruling 35's example: run over "a whole YouTube playlist, or his Instagram saves". | Bulk intake; paper as the confirmation step. |
| A-60 | 323 | "strategy population is something, and I want it to be automated most of the time" | shipped as manual-only (template A has no cron; L4 overnight loop is a draft) | partial | Triggers, Library. | none |
| A-61 | 456 | "WF2... stress test, try to iterate until you get actual results without overfit... iterate against QMB" (ruling 16) | shipped draft `d3-iterate-against-qmb` + shipped `_shared/overfit-gates/scripts/deflated_sharpe.py` | yes | QMB door. | Overfitting. |
| A-62 | 456 | "the stats folder... meant to replace the old combination of WF1 and WF2... reference" | superseded (ruling 16 reference only; ruling 28 "Strats is out") | yes | none | none |
| A-63 | 456 | "Why do you think I'll be keeping on iterating?" | chat-only (the lead's reading at 482: fixed pipelines break on messy input, so build a funnel of swappable steps the copilot reshapes; never ratified) | partial | Templates. Line 883 (part B) later says "I disagree with most of them... poor wording... what do you mean by build and prove?" | none |
| A-64 | 323 | "workflows for each quantitative layer... AlphaXiv... cookbooks from either Anthropic or... OpenAI... harnesses" | shipped (31 templates by layer; `_shared/research-harness` in Anthropic's shape) + file-only (`11` alphaXiv MCP) | partial | alphaXiv appears in no architecture file. RS1 and RS4 "Left out": no alphaXiv tool, no PDF reading (abstracts only). | none |
| A-65 | 323 | "Research from academic papers... most strategies can come from academic papers" | shipped (`rs1`, `rs2`, `rs4` published; `rs3` draft) | partial | Readers see only titles and abstracts (RS1 README). | none |
| A-66 | 323 | "macro analysis... daily... the templates you can have here are endless" | shipped (`t3-news-calendar-watch`, `db-desk-brief`, `t4-research-desk-overnight`) | yes | none | none |
| A-67 | 488 | "so many templates to come up with... specificity" | shipped (31) + designed (variants AD-22) | partial | Names are not plain (ruling 35, part B). Template ids and titles in code still read "A Fill the Library" and "B Build and prove", the exact names he rejected at line 883. | none |

### 1h. Portfolio, unit and node (lines 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-68 | 323 | "we combine everything under one thing, under one unit... self-configuring strategies" | file-only (`09`; `workroom/risk-lab-2026-10-05/`) + designed as seams only (Lab AD-11 ports, AD-16 identity table) | partial (deliberately deferred) | Portfolio, pods, MIS, QML, node. | none |
| A-69 | 456 | "A unit is in that trading node. That trading node is a server... upload our strategy, give it the connections" (ruling 14) | designed (Lab AD-11 `PodCompilerPort`, `NodePort`; engine AD-25 "that server is never the trading node") | yes | The risk session, DEC-0261. | "Premature": don't go deep. |
| A-70 | 323 | "Portfolio is always human driven... it might require portfolio to actually move, if not be there at all" (ruling 13) | designed (Lab AD-12 two clicks; Library AD-9 MANAGE; AD-17 proposals) | yes | The Portfolio purpose is still pending. | Portfolio may disappear. |
| A-71 | 456 | "we can at a point change things in the portfolio, but based off something that is in the lab or... in a mini app" | designed (AD-17 proposals; `pp-proposal-pack` draft) | yes | none | Combined-session Portfolio edits. |

### 1i. Models, reviewers, servers (line 323)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-72 | 323 | "Reviewers run on different model family... that's ideal" | designed (AD-13: allowed but labelled `same_family`) | yes | Graders, validation reviews. | none |
| A-73 | 456 | "it should be configurable by design in the settings panel. The reviewers and the model stuff" (ruling 15) | designed (AD-13; UI-HANDOFF §9.3) + shipped (`roles.py`) | yes | Settings UI. | none |
| A-74 | 323 | "for starters... ChatGPT and Claude, but Claude has the most usage... we might bring in Chinese models. For workhorses... for the workflows" | superseded (rulings 26, 62-63, 92, 95, 100 and RECOLLECTION gap 6: third-party models become primary) | n/a | Pool, relay. | none |
| A-75 | 323 | "model configuration for the workflows is paramount. Most times, we might use API" | designed (AD-13 roles in Settings; AD-29 key providers; trigger `role_pins`) | yes | none | none |
| A-76 | 323 | "sending a workflow in a server somewhere because most of these can run for a long period" | designed (AD-3 one instance per home; AD-30 placements) + shipped only as the local worker (`workers/local.py`) | yes | Contabo, vault, relay. | Long runs. |

### 1j. Browser and computer use (lines 92, 323, 456, 542)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-77 | 323 | "if I pay for TradingView, I can have my browser in QMX logged in... strategies, discussions... use them in the storyboard" | designed in part (AD-33 `profile: logged_in` only on the PC with an explicit grant) + file-only (`14`, `18`: QMX Browser profile). Template A marks TradingView rows "not captured". | partial | Browser, funnel, board. | Paid login reused inside QMX. |
| A-78 | 456 | "the copilot and I just see the same bloody thing... Hermes agent going to YouTube... use my YouTube... searches as if it's me... which creators talk about... portfolio optimization" (ruling 20) | file-only (`14`, `18`: watch pane, broker, leases B0-B4; closed ticket `browser-for-copilot-and-workflows`; open ticket `browser-plan-and-journeys`) + designed only for engine agent nodes (AD-33) | partial | The **hub copilot chat** (a harness session) has no browser design at all. AD-33 binds only engine `agent` nodes. UI-HANDOFF §7 says the browser plan is "still owed". | YouTube playlists read as him; creator search; he watches live and can take over. |
| A-79 | 456 | "in most harnesses I've used, it's only the main agent that has access to the browser" | file-only (`14` leases, one controller per tab, queue) | partial | Sub-agents and workflows sharing one logged-in browser. | Concurrency on one profile. |
| A-80 | 456 | "since you're using Claude, let's just take what Claude has. For the browser" | file-only (`14`, `18`: Claude in Chrome needs an interactive `/login` and cannot be used from the Agent SDK) | n/a | Told to him at line 536. He answered with A-81. | none |
| A-81 | 542 | "look into browser-based and other related browser harnesses. So browser-base" | file-only (`18`: Browserbase is cloud-only; Stagehand local replay; CDP screencast pane) + designed one line (SOLUTION-DESIGN: "Playwright and Stagehand stay for headless, logged-out research") | partial | none | none |
| A-82 | 92 | "computers and browser use... in a workflow, when will we need a computer... the general copilot... use cases are... enormous" | designed for workflows (AD-33 Cua pack by node scope). The general copilot has no design (see A-78). | partial | Harness (ruling 24). | none |

### 1k. Output methodology (lines 89, 323, 456)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-83 | 323 | "I don't think pictures are ideal... animated documents... Kimi K3... Claude Design... I don't have to literally read the bloody thing... it can just show me" (ruling 7) | file-only (`11`; ticket `output-methodology` open: "no architecture covers it"). Code: `_shared/render-and-grade` checks schema and numbers only; no renderer exists (RS1: "no renderer is wired to the engine yet"). UI-HANDOFF §1.8 has only a Markdown renderer and diagram parts. | partial | Every template's output schema, UI chat renderers, MCP apps (B16), the Library's "Explain it as" on articles. | Kimi K3 research pages; Claude Motion; one claim per screen. |
| A-84 | 456 | "having this inside QMX... I also have to have something like widgets inside chats preview modes" | file-only (ticket `output-methodology`: inline widget mode and drawer preview; ticket `mcp-apps` open) | partial | UI chat, MCP apps. | Widgets inside chat; preview modes. |
| A-85 | 323 | "the agentic UI part really needs some more thought... the output has to be rendered in the UI... tool calling" | designed (UI-HANDOFF §1: block renames, "What it did"; AD-15 tool spans) | partial | UI. | none |

### 1l. Library (lines 89, 323)

| id | line | his words (short) | STATUS | MATCH | BLAST RADIUS | SCENARIOS / EDGE CASES he raised |
|---|---|---|---|---|---|---|
| A-86 | 323 | "library might need some more thought... how the library design is... meant to be designed in the UI... the UI transcript is in the downloads folder" | designed (`architecture/library-and-data/`; schema-driven previews AD-17; ruling 41) | yes | Not built; the engine uses a fake Library (`ports/library_fake.py`). | none |

### 1m. Things the lead asserted in this slice that became disk "facts"

| id | line | what was said | STATUS | MATCH | BLAST RADIUS | notes |
|---|---|---|---|---|---|---|
| A-87 | 71, 224, 292, 317, 377 | "background work is capped at 50% of spare usage. Every workflow has to pause, not fail, when it hits the cap"; "usage page with the 50% cap bar" | reversed (rulings 26, 27, 90; settled: no caps). **Residue on disk and in code** (see Mismatches M-2). | no | Harness, engine admission, UI usage page. | This was the lead's restatement of the 10-13 "one Max, 50%" rule, passed to the Fable agent as a constraint. |
| A-88 | 224 | "This only works if the login has the `user:profile` permission"; the SDK marks the usage report experimental | file-only (`03`) | n/a | Pause at provider limits (AD-9). | Still a live probe for reading provider limits honestly. |
| A-89 | 376, 553 | "Lab = full creative freedom, nothing asks. The only Lab limits are money... and publishing outside the Lab" | designed (Lab AD-13) | yes | none | He did not object. Ruling 80 refined it. |
| A-90 | 397, 635 | "Safe to fix now: locking agents out of the account guard" | file-only (ticket `account-guard-lockout` closed PARTLY-STALE: it touches the harness, against ruling 24). No code. | n/a | Money boundary. | Not his words. Still unowned. |
| A-91 | 482 | run doctor; watchdog; "one message per run, never one per retry" | designed (AD-16, AD-17) + shipped (`nodes/doctor.py`, inbox dedupe by `(run_id, signature)`) | yes | none | none |
| A-92 | 420 | "agents output structured data, and QMX's own fixed templates turn it into the page. A grader checks..." | file-only (`11`) + shipped only as the grade step (`render-and-grade`) | partial | See A-83. | none |
| A-93 | 190 | Clipping lesson: a coordinator that "hires, briefs and checks" with code cut rules ("no source, no claim") | shipped (`t4-research-desk-overnight`; cut rules as rule and grader steps, `16`) | yes | none | none |
| A-94 | 190 | Build Alpha loop: "the validation gate stays fixed and the agent can't loosen it... dead ends are an asset" | designed (Lab AD-13 tighten-only; AD-18 `dead_end` rows) + shipped draft `l4-overnight-lab-loop` | yes | none | none |
| A-95 | 190 | Clipping lesson: "a graph built before you've watched the work happen freezes wrong assumptions. So start with traces, then formalize" | chat-only as a rule | partial | Template authoring and the builder. AD-26 learns from traces, but no rule says "trace first, then freeze the graph". | none |
| A-96 | 190 | "Portfolio... combining strategies so the portfolio works" | shipped draft `p1-portfolio-combination` | yes | none | none |
| A-97 | 302 | Fable first pass: "UI can wire... usage page with the 50% cap bar" | reversed (A-87) | no | UI-HANDOFF §9 row 15 (see M-2). | none |

---

## 2. MISMATCHES (every partial or no)

**M-1. MT5 click-through is denied by design (A-23, MATCH no).**
- *What he said (line 92):* an agent could open his installed MT5 and "click through and set up a strategy", so QMX need not rebuild it. BACKLOG B17 and B37 carry the same intent: agents click around cTrader, MT5 and TradingView on demo, and "demo trading and click-around trials are fine" (10-13 Q1).
- *What the disk says:* engine AD-33 and SOLUTION-DESIGN's Cua manifest have `deny (always): broker, MT5, cTrader, prop-firm windows and origins`. AD-33 also lists "cTrader and MT5 control exposure" as a probe, so the spine contradicts itself.
- *Fix:* `architecture/workflow-engine/ARCHITECTURE-SPINE.md` AD-33 and `SOLUTION-DESIGN.md` (Cua section). Two options: a demo-account allow scope for MT5 and cTrader (account id pinned, money gate still first), or an explicit ruling that this scenario is dropped. He has to decide. Do not decide it for him.

**M-2. 50% background cap and $5 per Background chat survive (A-87, A-97, MATCH no).**
- *Settled:* no caps of any kind.
- *Still on disk or in code:*
  - Code: `qma-harness/src/qma/harness/launch.py:229` (`background_cap: float = 0.5`), `:232` (`max_budget_usd: float = 5.0`), `:519`; `harness.py:378` and `:624` apply them.
  - `UI-HANDOFF.md` §9 row 15 tells the UI to show `max_budget_usd` and `background_cap` in Settings.
  - `SOLUTION-DESIGN.md:488` says "the 50 % cap applies per account", and `:965` raises `max_budget_usd` "far above" rather than removing it.
  - `UI-NOTES.md:61`, `BACKLOG.md` line 23, B35 and S3.
  - `36` S11 records the $5 cap, but HANDOFF step 8 hygiene does not list it (RECOLLECTION gap 10).
- *Fix:* the next plan's hygiene packet (code); UI-HANDOFF §9.15 (drop both, keep only the engine runaway guard); SOLUTION-DESIGN §7 table and §17; the audit's edits to UI-NOTES and BACKLOG.

**M-3. "Plugins are the contract to mini apps" has no load path (A-38, A-39, A-36, MATCH partial).**
- *What he meant:* each mini app is a plugin, so the copilot and agents reach it "without us building on top of everything".
- *What the disk says:*
  - AD-19 makes the app folder a valid Claude plugin.
  - The harness loads one SHA-locked plugin (`home.py:73`), and `HARNESS-REQUESTS.md:31` leaves the lock alone on purpose.
  - The capability-packs ticket says packs are fixed at launch.
  - `37b` §6.2 names the gap: there is no activation rule for app tools in a running chat.
  - Lab AD-14 calls the Lab pack a "plugin", but in practice it is tool rows in the single `qmx` table.
- *Fix:* engine AD-19 plus HARNESS-REQUESTS. Either an approved-plugin registry composed at launch, which needs a harness change and so needs a ruling against 24 and 39, or app tools exposed through the in-process `qmx` MCP server as namespaced rows, with "new chat to pick up a new app" written down. Align the word "plugin" in Lab AD-14.

**M-4. The funnel template does not match "pour in garbage, mostly automated" (A-58, A-59, A-60, A-67, MATCH partial).**
- *What the shipped template does* (`templates/a-fill-the-library/README.md`):
  - It refuses playlist, channel and saved-collection expansion without his approval.
  - It has a manual trigger only.
  - It has no `watch` visual pass, no Whisper, no TradingView and no Instagram saves.
- *Names:* "A Fill the Library" and "B Build and prove" are still the code titles. He rejected those exact names at line 883 ("what do you mean by build and prove?") and ruling 35 requires plain names.
- *Fix:*
  - `qmx_engine/templates/a-fill-the-library` and `b-build-and-prove`: rename, add playlist and saved-collection intake under the "nothing waits" rule (57), add a cron or monitor trigger.
  - `docs/TEMPLATES.md` and `templates/catalog.py`.
  - The logged-in source rows wait for the browser design (M-6).

**M-5. Output methodology has no architecture (A-83, A-84, A-85, A-92, MATCH partial).**
- *What he meant:* animated, interactive explainer documents and widgets with preview modes inside chat. Not pictures, and not text blocks.
- *What the disk has:*
  - Code has a grader for numbers (`render-and-grade`) and no renderer.
  - UI-HANDOFF §1.8 has a Markdown renderer and diagram parts only.
  - The ticket `output-methodology` says outright that "no architecture covers it".
- *Fix:* an AD in the engine spine (the output schema family, the renderer contract and grading before display) or a UI-HANDOFF section with the backend contract; then close the ticket. It touches every template's `schemas/output.json`.

**M-6. Browser for the copilot and shared watching are not designed (A-77, A-78, A-79, A-81, A-82, MATCH partial).**
- *What AD-33 covers:* engine `agent` nodes only.
- *What has no design:* his main scenario. That is the hub copilot browsing his logged-in YouTube or TradingView while he watches the same window and can take over.
- *Where the rest lives:* the QMX Browser profile, the broker, leases B0-B4, the CDP screencast pane and Stagehand replay are only in `14`, `18` and a closed ticket.
- *Fix:* the engine spine (a browser AD beside AD-33, covering copilot sessions too) and UI-HANDOFF §7. Ruling 30 still wants the plan and journeys explained to him first (open ticket `browser-plan-and-journeys`).

**M-7. The Experimentation Board's "fewest iterations" goal is not written into a live design (A-15, A-78 in ruling 17, MATCH partial).**
- *What is designed:* the Lab spine has the `board` kind and "run just this part".
- *What is missing:* the iteration-cutting levers are in the archived `12` §e and a closed ticket only. These are: questions with recommended answers up front, a "what I understood" card, side-by-side options, an iteration counter, and memory of rejected ideas.
- *In code:* `l1-idea-to-first-result` cannot pause for his answer (`human_gate` unavailable).
- *Fix:* `architecture/lab-and-pods/ARCHITECTURE-SPINE.md` (a board AD or an L1 section in the LLD).

**M-8. Methodology, organogram and prompts are still owed (A-1, A-8, A-9, A-12, A-14, A-28, MATCH partial).**
- *The gap:* engine AD-35 refers to "the methodology's autonomy row", but no file defines that table.
- *What is open:* B26-B29 are open tickets (`methodology-umbrella`, `methodology-builder`, `trader-agent-methodology`, `system-prompt-design`).
- *Fix:* a methodology design that the architecture pass should either own or name as a dependency.

**M-9. Five-quant journeys live only in archived files (A-13, A-27, A-34 to A-36, MATCH partial).**
- *What he said:* the situational mix per journey (ruling 11): copilot only, copilot plus sub-agents, or workflow alone.
- *Where it lives:* only `archive/.../12` §a.
- *The fifth quant:* "risk" was the lead's guess and was never confirmed.
- *Fix:* a live journeys file or section that the methodology and QA (B47) can use, plus a one-line confirm of the fifth lens.

**M-10. Mini-app "does it work and render" and app DevOps are outside the spine (A-40, A-41, A-42, A-43, MATCH partial).**
- *Where `qmx app check` lives:* `14`, `37b` and the draft `ma-mini-app-lifecycle` only. That covers the UI render check, contract tests and a shadow run.
- *Other gaps:*
  - App logs, incidents and doctor are thin in AD-19.
  - An app reusing its own output, and apps depending on the Lab, are not addressed.
  - `apps_archive` is a stub.
- *Fix:* engine AD-19 (name the check and the health path; say how an app calls Lab services) and SOLUTION-DESIGN §12.

**M-11. The builder covers workflows only (A-55, A-56, MATCH partial).**
- *What he asked for:* new versions of skills, agents and methodologies, BMad-builder style plus a skill writer.
- *What exists:* AD-22 and overlays exist for workflows. The skill and methodology builder is an open ticket, and the shipped plugin has one skill (`qmx-overview`).
- *Fix:* the `methodology-builder` ticket, then an AD (likely the engine spine, since skills and methodologies are Library lifecycle kinds).

**M-12. Model-agnostic code residue (A-19, MATCH partial).**
- *What remains:* `qmx_engine/settings.py` names `claude/fable` in the strong ladder and Kimi as the test default (AUDIT).
- *Fix:* code hygiene in the next plan. Not a design change.

**M-13. MIS versions in the Lab (A-45, MATCH partial).**
- *What he described:* making MIS versions and variants in the Lab.
- *What the design has:* only candidate labelers through `NodePort`, promoted in Portfolio.
- *Note:* ruling 14 parks node depth, so this may be correct for now.
- *Fix:* record it as an open item for the risk session in `architecture/lab-and-pods/OPEN-DECISIONS.md`, so it is not lost.

**M-14. alphaXiv and full-paper reading (A-64, A-65, MATCH partial).**
- *The gap:* the alphaXiv MCP (`11`) appears in no architecture file. RS1 reads abstracts only.
- *Fix:* the tool table in engine SOLUTION-DESIGN (tools declared by `[credentials.tools]`), or a Library or tools note.

**M-15. Combining packs mid-session (A-36, MATCH partial).**
- *The conflict:* "packs fixed at launch, adding one is a relaunch" against "one session may combine Portfolio + Lab + a workflow + a mini app".
- *Fix:* engine AD-35. Write the rule and its UX: when a pack is added, does the session restart, fork, or wait for the next chat?

**M-16. Portfolio backend (A-37b, MATCH partial).**
- *The gap:* no Portfolio architecture. Parts are spread over Lab AD-12, NodePort and templates.
- *Fix:* name it as a deferred design behind the risk session, in one place.

**M-17. Traces-first principle (A-95, A-3, MATCH partial).**
- *The gap:* not written as a rule.
- *Fix:* one line in engine AD-22 (builder) or AD-26: a new workflow starts loose, its traces are read, and only then is the graph tightened.

**M-18. Stale ticket text (A-32).**
- *The problem:* `wayfinder/tickets/session-homes.md` says no architecture covers homes. AD-35 does.
- *Fix:* the ticket, during the MAP refresh.

---

## 3. CHAT-ONLY items the architecture pass must take in

These are said by him in this slice, and are not in any live design file. Some sit in archived or research files only.

1. **MT5 click-through scenario** (line 92): an agent sets up a strategy in his installed MT5 instead of QMX rebuilding it. It conflicts with AD-33's deny-list (M-1).
2. **Hub copilot browsing as him while he watches the same window** (line 456): YouTube playlists, "which creators talk about portfolio optimization", TradingView strategies and discussions fed into the board (line 323). AD-33 covers engine nodes only (M-6).
3. **Mini apps that consume their own output, and most mini apps depending on the Lab** (lines 323, 456). Neither is written into AD-19.
4. **"How do we know a mini app works, is set up right, is wired to the UI, renders properly"** (line 456). Only research `14` and a draft template hold the answer.
5. **Widgets inside chat with preview modes** for animated documents (line 456). Only a ticket holds it.
6. **The fifth quant type** is unknown. "Risk quant" was the lead's assumption (line 292).
7. **Journeys are situational** (line 456): some need only the copilot, some the copilot plus sub-agents, some only workflows; the copilot is always present. This is ruling 11, but no live design encodes it. The archived `12` is the only place.
8. **"Most strategies, or components of strategies, come from academic papers"** (line 323). It implies full-paper reading and alphaXiv, which are not in any architecture.
9. **The lead's reading of why he kept iterating on WF1 and WF2** (line 482): fixed pipelines break on messy input, so a funnel of swappable steps. Never ratified. His later template criticism (line 883) is the evidence to check it against.
10. **Traces before graph** (clipping lesson, line 190) as a builder rule.
11. **"Don't just accept my ambiguity"** (line 323). Only memory holds it. Process, not architecture, but the methodology should carry it.

---

## 4. Cross-cutting threads (for stitching with parts B and C)

| thread | starts here | continues | where it stands |
|---|---|---|---|
| **T1 Caps and usage** | Lead line 71 item 5 ("50% background cap... pause, not fail"); lines 224, 292, 317 | Rulings 26, 27, 90; 36 S11; settled today: no caps | Pause-at-provider-limit (AD-9) is right. The 50% and $5 residue remains in code and docs (M-2). |
| **T2 Providers and model mix** | Line 323: "ChatGPT and Claude... Chinese models later as workhorses... most times API" | Rulings 26, 62, 63, 92, 95, 99, 100; RECOLLECTION gap 6 | Third-party models are now primary. In-house pool. |
| **T3 Fable** | Line 273: Fable agent for five-quant lenses | Ruling 87 (no Fable); code residue in `settings.py` | Reversed. Code residue (M-12). |
| **T4 Templates and funnel** | Lines 89, 323, 456 (funnel, templates per layer, WF2 core) | Rulings 22, 35, 48, 83; line 883 criticism; TP1-TP4 shipped | Names and bulk intake are off (M-4). |
| **T5 Session homes, hub as a place, packs** | Lines 323, 456 | Ruling 12; engine AD-35; UI-HANDOFF §1.2 | Designed, not in code. Mid-session pack add is open (M-15). |
| **T6 Plugins as the mini-app contract** | Line 323 | Rulings 10, 23, 24, 39, 80; AD-19; `37b` §6.2 | No load path (M-3). |
| **T7 Browser and computer use** | Lines 92, 323, 456, 542 | Rulings 20, 30, 60, 65, 67; AD-33; `37d` Hermes browser and HUD (ruling 102) | MT5 deny (M-1); copilot browser (M-6). |
| **T8 Output methodology** | Lines 89, 323, 456 | Rulings 7, 82; MCP apps (B16); memory "output as animated explainers" | No architecture (M-5). |
| **T9 Methodology, organogram, prompts** | Lines 3, 77, 273 | Rulings 1, 4, 5, 18, 82; HANDOFF open items | Owed (M-8, M-11). |
| **T10 Unit, trading node, risk session** | Lines 323, 456 | Rulings 14, 58; Lab AD-11 and AD-16; `09` | Deliberately deferred (M-13). |
| **T11 Lab freedom and asks** | Lines 323 (Lab freedom) and 376 (lead restatement) | Rulings 27, 57, 80; Lab AD-13 | Aligned. |
| **T12 Engine failure, monitoring, notification** | Line 456 | Rulings 21, 34, 57, 77; AD-16, AD-17 | Mostly shipped. Replay fork and self-improve not in code. |
| **T13 Remote and server runs** | Line 323 | Rulings 25, 43, 55, 69, 74-76; AD-3, AD-30 | Designed. Local worker only in code. |
| **T14 Memory and self-improvement** | Line 92 | Rulings 8, 49, 79; AD-18, AD-26 | Designed. Memory module empty in code. |
| **T15 Experimentation Board** | Lines 89, 456 | Rulings 17, 31; Lab AD-2; L1 template | Goal not written live (M-7). |
| **T16 Library** | Lines 89, 323 | Rulings 28, 41, 56, 57, 91; Library spine | Designed. Not built (the engine uses a fake). |
| **T17 Five-quant journeys** | Lines 273, 323, 456 | Ruling 11; archived `06`, `12` | Not live (M-9). |
| **T18 Probabilistic thinking and calibration** | Lines 3, 190 | `_shared/calibrate`; spine labels | Shipped. |
| **T19 Mini-app lifecycle and DevOps** | Lines 92, 323, 456 | Rulings 9, 23, 80; AD-19; MA template | Partial (M-10). |

---

## 5. Counts

Rows: 99 (A-1 to A-97, plus A-37b, A-46b and A-47x). Each row is counted once, under its main status.

Counted by script from the table's first STATUS word.

| STATUS | rows |
|---|---|
| shipped | 20 |
| designed | 44 |
| file-only | 23 |
| chat-only | 4 |
| reversed | 4 |
| superseded | 4 |

| MATCH | rows |
|---|---|
| yes | 46 |
| partial | 44 |
| no | 3 (A-23 MT5, A-87 and A-97 caps) |
| n/a | 6 |

Many "designed" rows also have part of the work in code, and many "partial" rows are partial only because the code lags the design. The 18 mismatches in section 2 are the ones where the **design itself** differs from what he meant, or no live design exists.
