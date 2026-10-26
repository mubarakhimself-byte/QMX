# 26 — Operator rulings (2026-10-16 to 2026-10-18) and alignment with the backlog

Written by the lead session from the live conversation. **This file outranks 01-25.** Where an earlier file (including 19 and 21) disagrees, this file wins. These are his words, paraphrased tightly. Quotes are marked.

## A. Rulings and corrections, in order given

### Morning (context and scope)
1. Today's goal: design the workflow-based system and the methodology, and wire them into QMA v2. Methodology is the umbrella over the organogram and the workflows. "Workflows is mostly autonomous work."
2. Use the latest agentic engineering: harness, loop and graph engineering, and probabilistic thinking. LangGraph is gone, so design on the Claude Agent SDK.
3. Everything must be model-agnostic: any capable LLM, never tied to one vendor.
4. Use BMad, Matt Pocock and pstack skills as the basis for QMX's methodology, re-hosted under QMX, not agile delivery.
5. Organogram: one plain (hub) copilot that compiles everything, a Lab copilot with its own methodology and more freedom, and a Portfolio copilot whose purpose is being rethought. The copilot's job is to help him "consider different angles".
6. The Lab: notebooks + a node editor + a VS Code-like space for experiments. Neural nets, strategies, components, variants, MIS versions, indicators, ML, and running workflows inside the Lab. "The sky is the limit." **The Lab is QMX's core feature.** Most mini apps will depend on it.
7. Output methodology: he does not want to read text blocks. He wants animated or interactive explainer documents (Kimi K3 / Claude Motion style), rendered inside QMX, including tool calls, widgets in chat, and preview modes.
8. Memory matters most for autonomous workflows, which must run unmanaged. Study LangGraph Deep Agents for what we lost.
9. Mini apps: how the copilot creates, maintains and edits them. They are **archived, never deleted**. They have DevOps (observability, logging). They take input from and give output to other mini apps, QMX internals, external APIs and webhooks.
10. **Plugins are the contract to mini apps.** Each mini app ships as a Claude-Agent-SDK-style plugin, so the copilot and agents reach it without custom wiring.

### Midday (corrections)
11. Five-quant journeys are situational. Some need only the copilot, some the copilot plus sub-agents, some workflows alone. The copilot is always where he talks.
12. **The hub is "just a place".** A session started in the Lab or Portfolio can be resumed in the hub and keeps its context and tools. One session may combine Portfolio + Lab + a workflow + a mini app. The hub copilot must have the capabilities of the Lab and Portfolio copilots.
13. Portfolio is human-driven. A combined session may change Portfolio based on Lab or mini-app output.
14. **The unit lives INSIDE the trading node.** The node is a server environment: upload a unit (strategy + MIS + risk/sizing) and give it connections. This is premature; don't go deep.
15. Reviewer and model choices are configurable in Settings.
16. Old WF1/WF2 and the Stats-folder design are **reference only**. WF2's useful core is "iterate against QMB until real results come out, without overfitting".
17. The storyboard is **vibe coding for trading**: go from a rough idea to what he meant in as few iterations as possible. BMad-style methods help here.
18. He and the copilot must be able to **create new versions**: a specific workflow with a specific methodology or skills (for example, macro analysis for one pair). BMad builder style, plus a skill writer.
19. Organization is paramount. Agents and workflows are folders (Vercel Eve style).
20. Browser: a shared browser he can watch, using his logged-in profiles (YouTube playlists, TradingView). Hermes-demo style. Look at Browserbase and similar tools.
21. Engine questions he asked: who writes it, who monitors it, how he is notified, and how a failed step avoids reworking everything. He pointed to Shepherd and prime-agent (RLM).

### Evening (answers to the eight decisions and big corrections)
22. **ONE workflow engine.** Templates are configurations of that one engine, never hand-built one by one. QMX itself must be able to create workflows. First build the engine and the way to create workflows; then an agent recreates the templates with it. Look at n8n, LangGraph and Claude Code dynamic workflows.
23. **Workflows are created like mini apps:** human-driven, built in the node editor (or the Lab), run and tested before use. A mini app can be a combination of workflows. Both can be agentic or not.
24. **The QMA v2 harness is built. Don't tamper with it.** The workflow engine and harness is a DIFFERENT thing that runs separately, the way Claude Code dynamic workflows run apart from the chat. Don't confuse the two.
25. Workflows must be able to run on a server or cloud as well as locally. Look at the Hermes architecture: plugins and cron.
26. **Several accounts, with a load balancer** (round-robin or least-loaded, CLIProxyAPI-like: https://github.com/router-for-me/CLIProxyAPI). Opus 5.5 is the copilot's daily driver, Fable when needed. Workflows run on non-loaded accounts. Providers: Claude (more than one account), ChatGPT, GLM, Kimi, OpenCode, Ollama Cloud. OpenRouter is for tests only. **This overrides the 10-13 "exactly one Claude Max" ruling and the "CLIProxy rejected" row.**
27. **No spending caps and no asking about usage.** Limits pause the work gracefully and it resumes later (as happened today). Resumability is required.
28. **Strats is out of scope.** It was his old personal library. The **Library** inside QMX stores **everything**: units, artifacts, bots and bot cards, relationships, logic, workflows, mini apps, previews and detail views. Today the UI and the backend disagree about the Library; they must match. Click through the UI with demo data to learn it.
29. WF1/WF2-style work ends at **paper trading**.
30. Browser: yes to a first step. Explain the plan and the user journeys first.
31. The Experimentation Board: save it, in the session. The board is (or became) the Lab's node editor. The hub chat gets previews and artifacts using the same underlying logic, without forcing him into the node editor. Keep it simple: "the experimentation board is simply code".
32. **QMX is a local installed desktop app** (PyCharm-like startup card). It runs in a browser only during design. There will never be a web version.
33. No build order yet. Explain before planning builds. "You're not vibe coding here." Waves are dropped completely.
34. Phone alerts: later. He hasn't reviewed the mobile UI.
35. Template names must say plainly what they do. Example: "run the WF1/WF2 idea over one video, a whole YouTube playlist, or his Instagram saves." "Helper agents" means sub-agents.
36. The design needs real technical architecture: a Fable agent with an architecture skill (BMad architecture), self-driven.
37. Track every document produced today. A sub-agent rubric walk marks what is now wrong.

## B. Risk he must see (not a ruling)

Earlier research (`tracker/qma-v2/trail/sources/2026-10-12-13-session-operator-messages.md:230`, `tracker/agent-system/research/26-requirements-from-today.md:30`) recorded two points:
- Anthropic's terms let a user sign in to the unmodified Claude Code binary with their own plan, but forbid third-party apps from routing subscription requests. CLIProxyAPI's "cloaking" violates this.
- Theo's video says pooling is common and rarely punished, and that the risk lies in a custom harness.

On 10-13 he reversed CLIProxy-for-Claude for this reason. Using someone else's Claude account adds account-sharing risk. The load balancer can be built either way; **which provider routes it may use is his call, made knowingly.** Providers that sell keys or allow their own SDK carry no such risk.

## C. Alignment with the morning backlog (BACKLOG.md)

| Backlog item | Status after today |
|---|---|
| B26 copilot methodology | Researched. The design must be redone on rulings 11-13 and 22-24. |
| B27 trader-agent methodology | Templates drafted (15-17). Names and descriptions must be rewritten (ruling 35) as configurations of one engine (ruling 22). |
| B28 BMad + Pocock as QMX methodology | Researched (01, 02). **Not designed**: no QMX skill set or builder spec yet. |
| B29 system-prompt design | **Missed today.** Research 31's five-layer prompt design was never used. |
| B30 organogram / session homes | Designed (homes + packs). Must be checked against the UI click-through (rulings 12, 28). |
| B31 Lab/Portfolio plugins | Re-scoped by ruling 10: plugins are the mini-app contract. |
| B32 agent as a folder | Researched (14). Folded into the design. |
| B23 mini-app creation | Researched (14, 17). Must align with ruling 23 (same creation flow as workflows). |
| B16 MCP apps | **Not covered.** |
| B33 workflows/graphs/loops | Researched widely (03, 11, 13, 18). The **one engine** design is still owed (rulings 22-25). |
| B13 research harness + templates | Templates drafted (15). Must become engine configurations. |
| B34 cron | Hermes research (11). The architecture study is running (25). |
| B35 orchestrator that picks models | Now the **load balancer** (ruling 26). |
| B36 two agents editing the same thing | **Not covered.** |
| B40/B41 memory, self-improvement | Light (03, 13). Memory for autonomous workflows is still owed (ruling 8). |
| B42 backend ready for agents | Partly (17's list of 27 Lab tools). The Library mismatch comes first (ruling 28). |
| B17/B38 browser | Hold partly lifted (ruling 30). The journeys are owed. |
| B10, B7, B8, B9 | Out (other sessions). B8 (Strats v2) is now superseded by ruling 28. |

**Drift today:** time went into trading-node and unit detail, Portfolio rules, and spend-cap rules (all reversed or premature), and into building template-by-template waves (reversed by ruling 22). **Missed:** B29, B16, B36, and a real QMX skill/builder design for B28.

## D. Status of today's files

| File | Status |
|---|---|
| 01-04, 11, 13, 14, 18 | Research. Still valid as sources. |
| 05, 10 | Being corrected by 23 and 24. |
| 06, 07, 12 | Superseded. |
| 08 | Valid as reference only (ruling 16); its Strats parts are out (ruling 28). |
| 09 | Valid for the risk session only (ruling 14). |
| 15, 16, 17 | Raw material. To be rewritten as engine configurations with plain names. |
| 19, 20a, 20b, 21, 22 + the explainer page | **Superseded by this file** wherever they conflict: waves, spend caps, harness extensions, Strats, browser wording, decision list. |
| Wayfinder map | Needs a rubric walk against this file. |

## E. Today's rulings vs ratified docs (from 24; his latest words win, but each needs a docs change)

| Ruling | Ratified doc it overrides | Note |
|---|---|---|
| 28: Library stores everything (units, artifacts, workflows, mini apps…) | DEC-0271 (Library = projection over ten trading record kinds); glossary:699-701 (workflows, skills, routines, templates, mini apps are not Library kinds); UI0923 LIBRARY-AND-ATTACHMENTS:16 (no generic Library DB) | The backend at hp17 has TWO Libraries with opposite rules (QMB projection vs control `library.db`). One design must replace both. |
| 9: mini apps archived, never deleted | DEC-0443 (`uninstalled` state) | Uninstall can become archive. |
| 22: one engine | DEC-0420, DEC-0439 (one engine: QMA Graph Template / Task Graph, "no second scheduler") | Matches in spirit, but both engines in hp17 are deleted by D1/D3. The new engine must be written down and the DECs updated. |
| 23: workflows tested before use | Docs flow is draft → validate → publish → enable → invoke, with no test step | Add a test step (n8n-style pinned data). |
| 31: Board saved | DEC-0417 "client-only, writes nothing" (at least 7 places) | The Board became the Authoring graph editor and then Lab Editor Graph mode (DEC-0475, 10-01 rebuild). Selected-subgraph runs are KEPT (DEC-0417), not dropped. |
| 32: installed desktop app | DEC-0478/GAP-0112 (Tauri shell optional, installer deferred); DEC-0262 (one installed app, design owed, GAP-0058) | Consistent; the installer design is still owed. |
| "Strats" | DEC-0380 (STRATS = old seed-corpus key, refused as a Library kind) | Consistent with ruling 28 (Strats is out). Our files 05/10/12/19 and BACKLOG B8 misnamed the Library "Strats". |

## F. Late evening additions (2026-10-16)

38. **Risks are already aligned; don't re-raise them.** History: LangChain/LangGraph came first, then two harnesses (OpenAI SDK + Claude Agent SDK), then one, because the Claude Agent SDK can sign in with ChatGPT (proven), and other providers serve the Anthropic-compatible API that Claude Code and Codex use. CLIProxy was removed because of the ban risk; only its load-balancing LOGIC is borrowed. Section B stands as history only.
39. **QMA v2 exception for the load balancer:** the harness may be extended for the account pool and balancer. It wasn't designed earlier only because workflows had not been discussed; copilots alone barely need it. Everything else in the harness stays untouched.
40. "Installed like PyCharm" was only an illustration. **QMX is a desktop application, full stop.**
41. **The Library gets its own design, done by an agent.** Base it on the UI and on the "Structuring 40 Million Documents into an Agentic Knowledge Graph" clipping. Requirements: previews and detail views; agents can access it; agents editing the same files need git-like logic; backups.
42. **Storage:** the S3 bucket is for his storage. His PC has little space; his own server has a lot. Storage is cheap.
43. **Remote data access (an "intermediator"):** workflows and agents may run off his machine (his server, E2B, Modal, Amp and others). They must reach the same QMX files and Library, retrieve and store everything, and carry a DevOps layer (monitoring, observability, logging). This needs a deliberate design of an intermediary or gateway between remote runs and QMX's data. He wants an agent to work this through.
44. A workflow can be a single agent; it is still a workflow.

## G. Night rulings (2026-10-16, after reading the two architectures)

45. Both architectures are approved in direction ("clean, no overlap").
46. **Lab and Pods:** he trusts the lead to design them. Design the backend for what the UI (with demo data) shows; iterate later in QMX.
47. **Keep a running UI-session handoff list** covering everything the UI session needs, across all work.
48. **Templates stay.** Build them, but all on the one engine.
49. **Workflow memory:** a dedicated, pluggable memory setup for workflows and agents. Look at Hermes's memory providers, Hindsight, and an Alibaba memory project on GitHub (name not recalled). Avoid rebuilding what another workflow already built. Self-improvement belongs here. Check how QMA v2 handles self-improvement, and how memory interacts with the Library.
50. **E1 (engine seat): yes.** Plug it in beside the harness. Keep it clean and upgradable.
51. **E2 (tests): no.** Tests use REAL models through the providers QMA v2 already has; cheap ones are fine (OpenRouter is OK for tests). "We don't want to assume, we want to make sure things work."
52. **Agent steps may need sub-agents.** Study how the Claude Agent SDK handles sub-agents. RLM and prime-agent come in for data and tables. Agents may make their own tools. The engine must still support script-only, mixed and fully agentic workflows (the "Not every workflow needs AI" clipping, Hermes cron).
53. **Runs happen inside an execution environment,** so a mistake isn't catastrophic, while agents keep their folder. Pick one that fits all needs (candidates he named: Matt Pocock's Sandcastle, Convex, others). Borrow Hermes's mental models for bots, agents and sub-agents.
54. **Scheduling follows Hermes.** E4 (one catch-up run after downtime): yes.
55. **Don't rely on his laptop.** He wants to host many workflows or agents at once (around 20) on a server or provider and sync data back. Think of it as "deployment of agents". Prefer **plain servers he controls** (he owns one; E2B, Modal, Railway and Amp are unpaid and optional). His own setup means workflows are not limited by any one provider. Tailscale is fine.
56. **L1 (Library home):** the PC is OK for now, but **design for the Library living off his machine** (server primary later) to cut load on the PC and simplify multi-agent access.
57. **L2: nothing waits for him.** Workflows write to the Library freely, garbage or clean. Design for no human intermediaries. A workflow that runs for a long time untouched is working.
58. **A data and DevOps study is needed:** market data, historical data, APIs and databases across QMB, QMF and QMN. Cover the stacks and how they connect, and include the risk-sizing "unit" angle.
59. **No hard deadline tonight.** Finishing before or after 8 is fine.

## H. Evening additions after Amp and Cua (2026-10-16)

60. **Amp + Cua together:** Amp handles machines, Cua handles computer use on those machines. Load Cua only when a task is scoped to need a desktop or browser. A QMX worker can live elsewhere: "an agent as an employee with its own machine".
61. **Credentials across machines is the open problem.** How does every worker or machine get the same sign-ins and keys? Amp does this out of the box (sign in once, served everywhere); QMX must design its own equivalent, together with the load balancer.
62. **Mixed providers in one workflow**, e.g. the main agent on Kimi K3 and its sub-agents on DeepSeek V4, with three or more providers requested at once through the load balancer. This must be designed for.
63. **Providers:** most connect the way Kimi and GLM connect to Claude Code, with an Anthropic-compatible base URL plus an API key, not a login. The pool must take any such provider, OpenCode included.
64. **Big fan-out jobs must be designed for.** Examples: a whole playlist; scraping articles from a site with Firecrawl (he will pay for it), then sorting and categorising them, then ideation and planning, then macro research.
65. **Multiple VMs must render in the UI.** Cua's demo of VM desktops rendering live is a reference.
66. **His server is on Contabo.** One big server for a year (database, storage, everything) appeals on cost. The worry is resource management for many Claude Agent SDK sessions (RAM). That is why he leans to managed providers such as Amp, or "Cloud Room" (name to confirm).

## I. Late night (2026-10-16, before the usage reset)

67. The **Machines view** can lean on the providers' own dashboards (Cloudroom, Amp, T3 Code's maker, Cloudflare). The copilot can reach them through computer use or an MCP into their dashboard, so he doesn't have to babysit. A native QMX Machines view is optional and only if necessary (UI latency and load).
68. A Claude Code session at about 1 GB is the LIGHT case: scraping, tool calls and backtests add more. **Backtests run on ONE dedicated QMB machine that agents call** (QMB detail is another day).
69. **Contabo is kept for storage and the always-on services.** Agent hosting is still open: there are many providers, cheap and reliable matters, and nothing is paid for yet. Don't lock to Amp. Candidates: Cloudroom (cloudroom.dev), Amp, Cloudflare, T3 Code's maker's offering, others. The core idea: these providers already host Claude Code and Codex out of the box, so they give agents "a place to live" at any level of workflow complexity. Keep the Rivet principle (harness outside the sandbox) in view. Tailscale may help.
70. He wants a **focused architecture pass** next (credentials, provider routing, machines), built with more complexity in mind. Architecture over creativity now.
71. **Ship tonight** with the poteto-mode-based shipping workflow used for QMA v2, in a LIGHTER version: it works, it's tested, the code is right, PRs are stacked overnight for morning review. Reference session: "Claude Agent SDK Baseline and Design".
72. **Before acting, re-walk the whole session** (especially from about 4 pm and across the usage resets) so no seed is skipped. Then report where we are, what's next, and how much of the backlog is covered.

## J. Wrap-up answers (2026-10-16 night)

73. **Architecture approved as solid.** Coding can start.
74. **Hosting:** start with **Contabo**. Every other provider (Amp, Cloudroom, E2B, others) must be addable later. Providers publish skills or instructions for external agents, so the copilot should be able to set a provider up from those instructions (built in, no hand-wiring).
75. **Central routing idea (Theo / T3 Code):** one machine runs the proxy/relay and the other machines route through it over Tailscale. No answer beyond that on provider-hosted harnesses.
76. **Contabo today:** 6 cores, **12 GB RAM**, 200 GB SSD. Possible upgrade in December. This means about 4-6 concurrent Claude sessions at most, so burst providers matter.
77. **Inbox waits:** almost nothing. Workflows run end to end. Human attention is needed only for provider failures and harness-level errors. **Notifications are UI-side**: the UI session designs them (UI-HANDOFF).
78. **Chunking:** fan-out is per CHUNK of items, not one agent per item. 1M-context models take large chunks; compaction near 40%. **Context compaction, caching, tool calls and hooks are critical in the engine.**
79. **Self-improvement:** ship a default; borrow from prime-agent/RLM and the harness. Memory providers (Hindsight for the copilot) also give self-improvement.
80. **Creation is human-driven first** (workflows, mini apps, pods): build, test, paper if needed, then run autonomously. Starting a pod on paper is part of that human-driven creation.
81. **Data is among the first things built.** He will provide data later; tick backup and import are early work.
82. Methodology, system prompts and MCP apps (the Model Context Protocol apps standard used in Claude Desktop; a UI concern) are handled **tomorrow**.
83. **Templates ship as ship-ready working defaults ("fillers").** (He said "ship", not "cheap"; that was a dictation slip.) He edits them with the copilot as he uses QMX. Each must actually run on the engine.
84. **Shipping starts early tomorrow morning** (not tonight). Tonight: one more rubric walk, the Wayfinder map rewrite, a detailed build plan in the QMA v2 style, and the branch prepared. What remains of the backlog after that: methodology and system prompts (tomorrow). MCP apps are a UI topic.
85. **Voice chat inside QMX** is a much-later nice-to-have (BACKLOG B15).
86. **Shipping prep follows `WORKFLOW-SHIP-PREP.md`'s skills and its "mistakes not to repeat", adapted rather than run verbatim:** our design came from the files plus the BMad architecture, not from transcripts.
87. **No more Fable.** Every agent from now on is Opus 5.5.
88. **Gaps go back into the architectures first.** If the rubric walk, the Wayfinder rewrite or the planner finds missing gaps, apply them to the architectures (with Opus), then centralize the architecture once more, then continue the plan. Take time and ground slowly; the morning prompt is the deliverable.

## K. Morning answers (2026-10-17)

89. **Harness grants H0, H15, H16 and H17: YES.** Add the harness PR (HG1) to the stack. The engine uses the real exports, compaction control, per-chat hooks and tool-table rows; the fallbacks stay only as safety.
90. **No fixed cap, configuration is key.** The 50% background cap is a DEFAULT, not a limit. Every account in the pool carries its own configurable share and strategy, CLIProxyAPI style: fill-first, round-robin, least-used, per-account ceilings, cooldowns. With a large plan or several accounts, a fixed 50% would be far too limiting. Defaults are editable in Settings, like agentic IDEs and Claude Code do. Never a hard global cap.
91. **Data is held.** Ship nothing on data for now (DP1 removed). A deeper data study comes first, explained to him, because data is the area where he gave the least context.

## L. After the first engine run (2026-10-18)

92. **Mixed providers must work for the copilot too.** The main agent can be on a subscription (Claude or Codex) while its sub-agents run on APIs: several sub-agents, each possibly on a different API (Kimi, Qwen and so on). Thinking mode, tool calling, sub-agents and the DevOps layer (logging, observability, monitoring) must hold for the copilot AND for workflows.
93. **Borrow heavily from Hermes Agent's developer guide**, especially extensibility: adding tools, adding providers, platform adapters, plugins and built-in plugins (including how mini apps are created and monitored by the copilot), skill system and curator, tool search, LSP, document extraction. Also prompt assembly, agent loop internals, micro-compaction, caching, gateway multiplexing, session storage, state DB recovery, cron (script-only), browser CDP supervisor, egress proxy, gateway monitoring and the guides' best practices. Voice mode stays a later nice-to-have. Honcho is good but he doesn't use it.
   - *Clarified 10-18 (alignment C, M-13):* from his own words that day, programmatic integration is out as a product surface ("I don't think we need it") and streaming TTS is out. Telegram (later, ruling 34), SOUL.md (the `persona` item) and the built-in plugin groups (automation, media, web) are in.
94. **Rerun the workflow once more:** context collection (Hermes) → append to the architecture → triage → review/fix-check → plan → prompt. Opus only; take time. Workflows and the quant parts stay QMX's own.
95. **Clean split by family, by design:** a Claude request goes through Claude (the plan), a GPT request through the GPT lane, and everything else (Kimi, Qwen, GLM, DeepSeek, OpenCode, Ollama Cloud) through the third-party pool. The open question is only how the pool is provided.
96. **Candidate pool: opencodex** (https://github.com/lidge-jun/opencodex), which he has used inside Claude Code and finds safer, or CLIProxyAPI, used **verbatim**, since both have configurable load balancers built in. The risk: losing QMX logic already coded. Weigh a hybrid.
97. **Order of work:** research and alignment first, then architecture, then code. Hermes ideas are compiled later in the rerun; pick up mental models where the architecture already covers a topic.
98. **The split router (option A vs B/D) is decided inside the architecture pass.** The architect looks at every angle (BMad architect persona, "Winston"); he does not pick between options himself.
   - *Clarified 10-18 (alignment C, M-13):* he named BMad **party mode** with the architect persona, not the BMad architecture skill. The intent is the same: the architect weighs every angle and decides. The rerun (39) used the architecture skill in amend mode and decided A + B + D.
99. **No opencodex or CLIProxyAPI, not even as a hybrid.** The load balancer and pool stay entirely in-house; third-party tools bring update and maintenance problems. Learn how Hermes lets sub-agents use different models and build that.
   - *Clarified 10-18 (alignment C, M-13; 39 §2.6):* two premises in his words were not so. No pool was ever built, so no QMX code gets deleted. Hermes pins the sub-agent model globally, and its Anthropic OAuth path bills extra usage, not the Max allowance, so Hermes does not run a plan main with Kimi sub-agents. "Hermes as a provider over RPC" is closed: Hermes serves an agent, not a model, and fits only as a `cli` delegate target.
100. **Coding-plan accounts are NOT restricted to interactive use.** Models are multimodal: video and audio inputs must be supported by default. Leave room to add providers (MiniMax and others).
101. **Planning-lead work uses no poteto-mode and no skills by default.** The lead holds the workflow in this session. One agent does a FULL pass over the whole Hermes docs menu: getting started, using Hermes, features, messaging (light), integrations, guides and tutorials, developer guide (especially), and reference.
   - *Clarified 10-18 (alignment C, M-13):* "no poteto-mode and no skills" covers this lead and its successor. In the same answer he said he would start a fresh session (ruling 104), so "in this session" means whichever session holds the planning lead.
102. **Hermes is borrowed without limits.** Map every useful Hermes idea, with no top-N cap. Many targets don't exist in QMX yet, and some existing code may need a refactor or rebuild. Prefer Hermes solutions that solve several QMX problems at once. Include user journeys, the browser (one of the best), the HUD mode and the desktop app. Permissions, approval modes, user rules, approval timeouts, cron, state, DM pairing, Docker, skills and the skill curator (handled like templates) are all in scope.
   - *Clarified 10-18 (alignment C, M-13):* also in scope from his list that day: symlinked shared helpers (shared tools), git worktrees for agents and workflows, and the desktop app rather than the terminal UI ("we don't need" the TUI). No limit on how much each research agent reads ("1 million context window… Don't limit").
103. **State, 2026-10-18:** the whole engine stack (EP0-EP14, HG1, HG2, TP1-TP4) is MERGED into `engine/base` (origin, `132169c7`). It is not yet merged into `rebuild/base`.
104. **Work moves to a fresh planning-lead session** after this one. It orients from files, and uses this session's transcript only to check details. Disk contents need sorting into useful and stale.

## M. 2026-10-18 (new lead session)

Recorded by the planning lead from the settled facts the operator gave the new lead session, checked against the 10-18 transcript (alignment C, chat-only items 1-3; `AUDIT-2026-10-18.md`). Several close gaps the audit and alignment C found. Where an earlier ruling disagrees, these win.

105. **Tests run on haiku through the plan login.** OpenRouter is used only to prove that other providers work, never as the default test model. This replaces "OpenRouter is for tests only" (26) and "OpenRouter is OK for tests" (51).
106. **No QMX-internal usage or spend caps of any kind.** The $5 per Background chat and fixed shares (the 0.5 background share) are bugs, not settings. The providers' own limits are the only limits. Configuration per account (strategy, priority, which models it serves) lives in the UI. This finishes rulings 27 and 90; 90's "50 % as a default" is superseded.
107. **He will use the Chinese models more than Claude.** Defaults are key-first: third-party key providers come before GPT and the plan, and nothing in QMX limits them.
108. **MT5 and cTrader click-through is allowed on demo accounts only, with the money gate first.** Agents may set up strategies there; live accounts are never touched.
109. **The harness stays; the provider contracts change.** Routing work lands in the router, profiles and pool, not in the harness core.
110. **The Claude SDK limit is to be solved, not assumed.** "If it is a limit, there should be a solution." A design may not stop at "the SDK can't".
111. **Data stays held** (ruling 91 stands). His intent behind it: server storage and agent deployment that work out of the box.
112. **The fifth quant lens is unresolved.** Four lenses are confirmed: researcher, trader, developer and portfolio manager. Nothing is built on the fifth.
113. **Every research idea is validated in full, with no top-N**, including where each one lands in the UI.
114. **Deep context alignment comes before architecture.** The order is alignment, then architecture, then code (ruling 97, made firmer).
115. **Design for complexity; do not design a complex system.** QMX stays simple the way Claude Code and Hermes are, but covers the scenarios. Do not oversimplify either: complexity that works and does not produce bugs stays. Only what is clearly over-engineered, not yet built and safe to remove is removed, and nothing built in merged code (`engine/base`) that works is removed. Text meant for him is in plain words, with no codenames.
116. **Agents have no path to money, so the money-safety machinery is retired.** Live trading happens only after a backtest, a stress test and his manual admission (his liability). Withdrawals happen only through his broker in his own browser, never QMX's or an agent's; cTrader and MT5 cannot withdraw. Agent computer and browser use on brokers always runs on dedicated demo accounts he set up, and agents never sign in to his provider accounts. QMX's daily use is research, development and analysis. Kept: keys are never printed into logs, the inbox or the ledger (simple redaction), keys live in the OS keyring, and the harness's existing behaviour (its money gate included) stays as built.
117. **Local by default; remote workflows stay fully designed.** Scripts and agents run locally on his PC by default, as Claude Code does. Docker, Contabo or a server is never forced as a safety requirement; a remote placement is an option he chooses. Workflows that run off his machine are very important and stay fully designed: remote placements (his server or Contabo, other providers), remote workers reaching the same QMX files and Library, credentials served to remote machines, the central relay, the run passes and access control those runs need, resume across machines, and logs and monitoring for remote runs. None of that is money-safety machinery.
   - *Applied 2026-10-18 (`methodology/39` "Retirement pass"):* retired the money text scan (engine AD-36), forced script isolation (AD-24 tiers, the Windows sealed box, Docker-first, `cli` helpers forced into containers), the five-layer MT5 and cTrader demo proof (AD-33) and the step-pass misuse alarm (AD-28). Open decision E is answered no and F is retired.
118. **The whole QMX app is unlocked (2026-10-18, about 15:00).** Nothing is legacy or protected: the QMA v2 harness, the workflow engine, the Library, the Lab and the data layer, and also QMF, QMN, QML, QMB and the rest. The old "don't touch X" rules, such as ruling 24 ("don't tamper with the harness") and its exceptions 39 and 89, and ruling 109's "the harness stays", were temporary locks for particular sessions and no longer bind. Anything may be refactored, overhauled, or deleted and rebuilt ("remove a lot to grow a new fruit"), as long as the result works. "I don't want to vibe code": every change is reasoned, verifiable and buildable by agents. If something anywhere needs real improvement (the codebase was messy enough to need a full audit days ago), bring it up instead of working around it. The UI stays a separate session. Still binding: rulings 105-117 (no QMX caps; key-first defaults with the Chinese models used most; mixed providers for the copilot and workflows, ruling 92; multimodal by default; money-safety machinery retired, agents cannot touch money; scripts local by default and remote workflows fully covered; tests on haiku through the plan login; no Fable), and "design for complexity, not a complex system" without oversimplifying (keep what works and does not produce bugs).
   - *Applied 2026-10-18 (`methodology/43-whole-app-unlocked.md`):* engine AD-52 to AD-60 added (one host process, the harness turn API, the guard replacing the money gate, packs as plugins, the router as its own package, one run system, capacity per resource class, old runtimes deleted, agents that write locally); `HARNESS-REQUESTS.md` rewritten as a plain change list; open decisions D and G closed (no longer his calls); Library AD-21 (sessions are Library items); Lab AD-14 (the Lab pack is a real plugin). Where ruling 116 kept "the harness's money gate as built", that keep rested on the harness lock this ruling lifts; the gate's protections of sign-ins, keys and QMX stores stay in the guard, and its money-word matching goes.
119. **Hindsight is QMX's memory engine (2026-10-18).** He chose Hindsight. It is the default engine that finds memories, for the copilot and for workflows, behind one seam; the memories themselves stay QMX's own records in the Library, so Hindsight can be rebuilt or swapped without losing anything, and the built-in search stays as the second engine for tests, offline work and fallback. This replaces 39's "the built-in provider ships first and is the default; Hindsight is an optional adapter" (39 §5 C M-18, H-141) and engine AD-18's rule that kept Hindsight passive (no automatic remembering from copilot chats). Recorded by the architect from study 44 §2.6, where the operator's choice is stated.
   - *Applied 2026-10-18 (`methodology/47-studies-folded.md`):* engine AD-18 amended (Hindsight the default adapter behind `RecallEngine`; three banks by who writes, tags by subject; copilot chats remembered from session digests written by QMX; validity windows and regime tags; forget; the extractor model through the router; on the PC until the server exists, then on the server); the Deferred row on an external memory provider closed; probe P-MEM before ship.

### 2026-10-22, the data round (his answers to the funnel, `51-data-round-seeds.md` §8 and §9)

Recorded by the architect of the data round from his words in 51 §8-9, which the planning lead wrote from his dictation. Applied in `55-data-round-architecture.md`. Where an earlier ruling disagrees, these win; rulings 91 and 111 (data held) are lifted by them.

120. **The Library is the one catalog of all data** (funnel Q1: "yes"). Every piece of data has an entry in the Library he can find, open and link. The big price files sit next to it in a format made for fast reading by date, and each set has a card in the Library that says what it is, where it is and how fresh it is. This is what "the Library takes in all data" means.
121. **The server holds the main copy from this week** (Q2: "yes"). His PC keeps a working copy, works offline and catches up; work on the server lands while the PC sleeps.
122. **Free sources first** (Q3: "yes"): forex, metals, indices and CFDs from Dukascopy, crypto from Binance's free files. Paid futures data (Databento) only when a strategy needs futures.
123. **OpenObserve's free tier is fine as the external monitoring** (Q5).
124. **He has no more data seeds.** The lead and the architect handle the technical design and should improve on his seeds: "what you make is the worst it will ever be, it only gets better". Design for complexity, not a complex system.
125. **For now the backend tool that matters for agents is QMB (backtests).** The rest reaches agents through the Lab and mini apps. Do what is sensible; no long tool list.
126. **Two DevOps layers from one source of events.** Internal: QMX's own light health and incident view in the app (already designed). External: OpenTelemetry into OpenObserve on the server, with deep logs and traces and a door for an outside agent such as Claude Code. Not two systems.
127. **Every Library item has a preview and a detail view** (his "FIFA card" idea from the UI transcript): each kind has a small card and a full page. When each appears is a UI and Library contract; the Library must give each kind what both views need.
128. **Market data:** use dukascopy-node as the Dukascopy downloader, and check its data quality and alternatives. Some strategies may need order-flow data; true volume and order books exist for futures and crypto exchanges, not for spot FX.
129. **Brokers are managed and controlled inside QMX, not in an outside browser:** cTrader first, MT5, more later, crypto through CCXT. He controls brokers through QMX; agents still never reach money. The trading-node session owns live trading; the platform owns the accounts, connections and their health.
130. **The old 10 GB of ticks is on his PC** (`C:\Users\Mubarak\Documents\QMX\data\raw\external-deep-history`), not on the server; the server was reset on 2026-10-21 and holds no data.
131. **Feeds:** standing sources QMX watches and pulls automatically (academic research sites, blogs, MQL5 articles as in the "agent team for MT5 article analysis" session, news), scraped on a schedule with Firecrawl or agent browsers, landing in the Library as items workflows and the copilot can use. A feed is a scheduled workflow plus a source definition; the UI design already shows something like it.
132. **"Dead ends" in study 50 means "goes nowhere today"** (no consumer or no path yet), not "cannot be done". Each one gets a proper path.
133. **External connections need their own design:** data providers (free and paid), brokers and platforms with several brokers and several accounts per broker (some of it built earlier, such as `qmx-broker`): how each connection is added, tested, kept healthy and shown in QMX, and how a connection is used from a trading node. The platform owns accounts, connections and health; the trading-node and unit sessions own live trading. Agents never touch money.
134. **Ship the rest of the backend (everything except the unit work) as soon as possible, carefully:** "nothing is fixed or locked".
   - *Not answered in this round:* funnel Q4 (removing the old 10 GB from his C: drive once two checked copies exist). It stays his call, with a cloud bucket for the second copy (55 §12).
   - *Applied 2026-10-22 (`55-data-round-architecture.md`):* Library AD-25 to AD-33, engine AD-67 to AD-70, Lab AD-19 and AD-20 added; Library OPEN-2 closed (the registry room is replaced); the money-word matcher's call sites are removed under rulings 116 and 118 (engine AD-59, three call sites).

### 2026-10-22, after the edge-case review of the data round (`57-data-round-edge-case-review.md`)

Not his words. **The planning lead's decision, derived from his rulings 115-118, 129 and 133, recorded here so he sees it and can overrule it.** Applied in `55-data-round-architecture.md` ("Edge-case review applied (57)").

135. **Keys that can trade live money never sit where agents work.** (Lead's decision, derived from rulings 116-118.)
   - **His PC, his server and any machine an agent can reach hold read-only broker keys only.** A read-only key can see accounts, balances, positions and history, and cannot place an order. Agents on those machines have a shell, so anything stored there is treated as readable by an agent; a read-only key is safe to be read. A key that can trade only demo accounts holds no money and may sit there too.
   - **A key that can trade a live account lives only on a trading server.** He enters it there himself when he sets that server up: he signs in on the broker's page in his own browser, and the one-minute sign-in code it hands back goes to that trading server, which turns it into the key and keeps it. QMX on his PC never stores it. His PC's Connections list still shows that account and its health, read from the trading server's reports.
   - **Only the home machine holds a sign-in.** For cTrader, refreshing a sign-in logs out every other copy of it, and cTrader advises at most one demo and one live connection per registered app. So each sign-in has one home machine, and only that machine holds it, refreshes it and opens its connection; other machines ask that home. The sign-in itself never passes through the key copy that QMX sends between his machines, so no stale copy is left on his PC and deleting a copy on one machine cannot delete it on another. The home belongs to the sign-in he gave, not to a row on the screen: one cTrader sign-in covers demo and live and every account he ticked, so all of them share one home.
   - **Each trading server has its own cTrader app.** The PC and the server share one registered app for reading. Every trading server registers its own app, separate from that one and from each other's, so a routine refresh on one machine can never log out a live bot on another. Spotware approves each app first, with no published timeline, so registering it is one of his steps when he sets up each trading server.
   - **Why this is simpler, not more machinery.** Nothing new guards money: there is no money gate and no sandbox (rulings 116-118 retired them). The rule is only about where a key is typed and kept.
   - **One thing to know.** A broker app he signs into himself with a trading password on his PC (for example an MT5 terminal) can be reached by an agent's shell. Keep such logins on demo accounts, or off the PC, the same way.
   - **The tension with ruling 117, named so his overrule is informed.** Ruling 117 says Docker, Contabo or a server is never forced as a safety requirement. This ruling does require a separate machine for keys that trade live money. The substance holds because live trading was always the trading server's job (rulings 116, 133), so no research or development work is moved off his PC by it; if he prefers to trade live from his PC, this is the ruling to overrule, and only the key rules change.
   - *Applied 2026-10-22 (`55` "Edge-case review applied (57)"):* engine AD-28, AD-67 and AD-70 amended; Library AD-12 amended.
   - *Reworded 2026-10-22 night (`58-data-round-fix-check.md`, applied in `55` "Fix-check applied (58)"); substance unchanged:* the sign-in code goes to the home, which alone keeps the tokens (the built key copy carries only plain keys); the home belongs to the sign-in, not to a row; one cTrader app per trading server; the tension with ruling 117 is named. Engine AD-28 and AD-67 and Library AD-12 amended again.

### 2026-10-25, the wrap-up session (his words, recorded by the wrap-up coordinator)

Where an earlier ruling disagrees, these win.

136. **The PC is home; servers are substitutes, never replacements.** Everything lives on his PC first, the data included, with a local backup always. A server (Contabo, a burst provider, any borrowed compute) exists so that work continues when the PC is off, asleep, offline or without power, and to add capacity, like horizontal scaling. It is never the main copy. The reverse holds too: the PC carries on when a server is down. This replaces ruling 121 ("the server holds the main copy from this week"). The "move the Library to the server" flip (DR2D, G-FLIP) is therefore the wrong shape. The right shape is the PC as primary, with a server that can stand in for it and hand back. The same model applies to every place QMX borrows external compute, including the trading node, which keeps trading when the laptop closes.
137. **No built-in locks that limit what he can do.** A lock that refuses by default (for example the market-data door staying shut until a holdout month is set) is a bug, not a safety feature. A holdout is an optional setting he chooses per study, off by default, editable in the UI. He may test any idea on any period, 1996 included. This extends rulings 106 and 118 and the "configurable means UI-editable" rule. Agents still never touch money, because his brokers are outside QMX; that is the only boundary, and it needs no lock inside QMX.
138. **Units, not bots.** A unit replaces what was called a bot. Text for him, questions to him and new design say "unit". Anything about units belongs to the unit session.
139. **He needs a way back in without agents.** Every server QMX sets up has a recovery script he can run by hand to see what is wrong, restart services, repair or re-pair, and get things moving again without a full reset and without an agent.

### 2026-10-26, the wrap-up session, morning (his words, recorded by the wrap-up coordinator)

140. **Local first in every system, server second.** Ruling 136 is not a server fix; it runs through all of QMX. Anything that uses outside compute or storage (buckets, workflow placements, memory, monitoring and DevOps, data downloads, the Library, the Lab, pods, backtests, file formats) runs and is set up on his PC first, and the same thing can also run on a server as a stand-in or added capacity. The UI offers "on this PC" or "on a server" wherever work or data can live in either place. The trading node is the one place where a server is the natural home, and even it can run on his machine. QMX must work for someone who owns a strong machine and no server at all.
141. **His data is independent of the app.** Like a dictation app, a game or a browser profile, his data lives in its own clearly organized folder in open file formats, separate from the installed program. Uninstalling, reinstalling, or a broken release never touches it, and a reinstall picks up exactly where he left off. Data and the QMX program are loosely coupled.
142. **Setup order: QMX on the PC first, the server second.** The first real boot is a local one with no server involved. Setting up a server never comes first, and nothing in QMX may assume a server exists.
143. **No messy files.** Every folder and file format has a documented home and purpose; agents never scatter files. Organization is a design concern, not an afterthought.
144. **External compute is an optional supplement, designed with the UI in mind.** QMX works fully on the PC out of the box; the UI's Settings and its other "add external compute" places let him add a server, a GPU, a bucket or a database later, and QMX uses it when present. Every local-first design names the screen where that choice appears, so wiring the UI later is straightforward.
145. **The copilot helps him connect external compute** (for the methodology session). It walks him through adding a server or other compute step by step, built around the pattern of the wizard skill (an interactive walk through the steps only he can perform), so he never needs to be technical to add one.
