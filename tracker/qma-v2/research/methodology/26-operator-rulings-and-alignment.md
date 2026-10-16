# 26 — Operator rulings of 2026-10-16 and alignment with the backlog

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
