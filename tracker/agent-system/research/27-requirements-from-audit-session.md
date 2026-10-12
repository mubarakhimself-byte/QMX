# 27: Requirements from the "QMX product audit and status" session (2026-10-07 to 10-12)

Written 2026-10-12. Read-only extraction. Nothing in the repo was changed apart from adding this file.

**Why this exists.** The operator wants QMA v2 (Claude Agent SDK + OpenAI Agents SDK, with QMX's own graph and loop engine) to "adopt what we wanted to ship with LangChain and LangGraph to the SDKs and customize". This file is the full list of what that session intended, planned and shipped, so nothing is lost in the port.

**Source.** `scratchpad/old-audit-conversation.md` (320 KB, 174 numbered messages, 2026-10-07 05:59 to 2026-10-12 08:06). It was read in full, in order, then consolidated, then checked against what is on `origin/rebuild/base`.

**Citation keys**
- **[n]**: message number in the transcript. Subagent reports are quoted as Claude-side evidence, not as operator words.
- **D§x Ln**: `rebuild/DESIGN.md` on `origin/rebuild/base`, section and line.
- **C§x Ln**: `rebuild/COPILOT.md`. **RM Ln**: `rebuild/README.md`.
- **Pnn Ln**: `rebuild/packets/Pnn-*.md`. **DP Ln**: `rebuild/reports/p16-deletion-plan.md`.
- **R19, R20, R21, R24, L00**: files `19-two-sdk-study.md`, `20-qma-v2-direction.md`, `21-miniapps-and-workflows-seeds.md`, `24-how-why-integration-surface.md` and `00-session-ledger-2026-10-12.md` in this folder. R20 is the latest direction and wins where it differs.
- Research files named like `harness-practices.md` live in `rebuild/research/` on `origin/rebuild/base`.

**Status words**
- **SHIPPED (Pnn, #PR)**: merged into `rebuild/base`. Almost every shipped piece was proven only with fake models and recorded fixtures. No live model call, CLIProxy run, real server run or real broker call was made in this session ([83], [100], [113], [135], [137]).
- **PLANNED**: written into DESIGN, COPILOT, a packet or a research recommendation, but not built.
- **REJECTED**: the operator or a ruling turned it down.
- **OPEN**: raised and never settled.

**PR map** (from the transcript and `git log origin/rebuild/base`): P01 #28, P02 #29, P03 #27, P04 #30, P05 #26, P06 #31, P07 #33, P08 #35, P09 #34, P10 #36, P11 #32, P12 #37, P13 #38, P14 #42, P15 #47, P16a #48, P16b #49-#57, P17 #40, P18 #39, P19 #41, P20 #44, P21 #46, P22 #43, P23 #45. P24 was never started (on hold). P16c (#58-#67) came after this session.

**Format.** The FR/NFR format follows the BMAD `bmad-prd` template (`.claude/skills/bmad-prd/assets/prd-template.md` L61-79): stable, globally numbered IDs grouped by feature area, capabilities rather than implementation. To fit one file, each FR is one line: the requirement, its source messages, and where it shipped or was planned.

---

## 1. Journey of that session

### Phase A: the audit (2026-10-07, 06:00-06:40, [1]-[20])

- The operator asked for a status check of Aurelius (a ChatGPT agent): what was asked, built, broken and left. He wanted to finish QMX and start using the UI [1]. He capped subagents [1], [8].
- Four Opus readers worked through the chat, the voice calls, the mini-app transcripts and the code [3], [6], [9], [14], [19].
- Findings [20]:
  - Real LangChain/LangGraph code existed, but none of it was merged.
  - Deep Agents was opt-in only, with sub-agents off.
  - There were two memory systems, and the LangMem part was dead.
  - The copilot could not build workflows: `authored_graphs.py` had no production caller.
  - Mini apps were an inert description that could not run.
  - No real model call had ever been made.
  - `DaemonProcess` had grown to 4,007 lines.
- The operator asked for sandboxes for mini apps, YAGNI and modularity [17]. Claude added a keep/simplify/delete table [18].

### Phase B: the CTO view and the first design (08:19-08:40, [21]-[35])

- **The brain dump [21].** Learn from Anthropic and LangChain ("not designing something very new... patterns and patterns"). He wanted:
  - a model router;
  - CLIProxy on his subscriptions;
  - Hermes-style memory;
  - RLM for data-heavy work;
  - a copilot that builds, controls and accesses workflows and mini apps;
  - per-app databases with S3 backups;
  - caching.

  He also wanted Codex as the workhorse and Claude on knowledge work, and he asked "what are you seeing that I'm not?"
- **Claude's answer [22].**
  - There is one mini-app shape, like Docker: definition = image, instance = container, data = volume.
  - Deep Agents is the harness. QMX owns only a tool/MCP catalogue, a memory plug point and a model router.
  - An agent is a settings file.
  - RLM is one tool, not an architecture.
  - The copilot uses the same API as the UI.
  - There is one workflow engine (LangGraph).
  - The process, not the code, was the bigger problem.
- **His reaction [23].** He was enthusiastic about "same API" and "Deep Agents is the harness". He added MCP Apps as the way the copilot handles mini apps, sub-agents at copilot level, delegation to workflows, apps feeding apps, and LangMem.
- Three research reports landed [25], [28], [31]. Draft PR 25 opened [24]. DESIGN.md and P01-P17 were pushed [35].

### Phase C: additions and corrections (11:13-11:17, [36]-[40])

- **Additions [36].** He had held these back until the usage limit reset:
  - copilot skills and hooks;
  - IC Markets via cTrader back for CFDs, a cTrader MCP on by default, multi-broker, CCXT and Hummingbot;
  - charting;
  - Firecrawl (paid, with Alexandria);
  - a cron MQL5 article scraper.

  They became DESIGN §11 and P18-P20 [38].
- **Corrections [39].** "Don't save any memories" (not his account). Mini apps are "not meant to be just like VS Code style extensions". Claude reverted to the one-shape definition [40].

### Phase D: execution scheduling (11:25-12:45, [41]-[57])

- He chose parallel Codex sessions over a sequential run [43]. The backend comes first and the UI comes later, done by Claude [41].
- The P05 review produced DESIGN §12 [50]:
  - no bridge for the old wire;
  - keep the evidence rules and the Experiment Ledger;
  - drop the Task/Quant ledgers;
  - port the money path as is;
  - approval = `interrupt_on` + one backend check.
- Branch cleanup ran [52]-[55]. Test models were picked on OpenRouter [56], [57].

### Phase E: subscriptions, remote runs, data map (12:51-13:23, [58]-[76])

- **[58]** The test models are not daily drivers. Use CLIProxy on his subscriptions:
  - Opus for the copilot, GPT-6.1 Sol for sub-agents and workflow agents;
  - the token cost of cron workflows and of "12 agents all running";
  - agents on a server with the laptop off (Amp, Modal, E2B), launched from the UI;
  - results recoverable "like Git";
  - logging, monitoring, tracing and observability kept.

  This became DESIGN §5.3 and §11b, plus P21 [64].
- **[65]** Models are "not set in stone" (Kimi K3 as an example). He wanted per-sub-agent and per-workflow configuration, and a setup script for his own server with automatic recording. "Don't invent": use documentation. The answer was the model override chain, `qmx node bootstrap` and README rule 8 [66].
- **[67]**:
  - VPS first, bucket on the same box;
  - GPU access;
  - "tooling for agents is a huge gap";
  - a weekly private GitHub repo as the backup of the backup;
  - a database map across agentic, mini-app, workflow, Portfolio, Lab, results, artifacts and Library;
  - where caching belongs.

  The answers were the data map §7.6b, the tool catalogue §5.6b and P22 [69].
- **[70]** When are GPUs needed? He raised ONNX. Answer: train on rented GPUs, run on CPU with ONNX, and models become Library items [71].
- The CLIProxy video study [72], [73] and REFERENCES.md led to DESIGN §12b [74]-[76]:
  - QMX's own `start_task`/`check_task`/`cancel_task`/`list_tasks` replace `AsyncSubAgent`;
  - a Python sandbox replaces the JavaScript interpreter;
  - `MCPAdapter`;
  - FastMCP 4.

### Phase F: the build (2026-10-07 15:26 to 10-09 15:28, [77]-[141])

- P01-P23 merged, plus P15 (copilot and first app) [77]-[137]. The new core is about 6,000 lines replacing about 130,000 [101].
- README rule 9: backend only, no Reticle [101]. He made P16 surgical with a pre-audit [131], which led to P16a and P16b [132]. GPT-6 Astra wrote the plan [139]. DESIGN §12c held the rulings [141].
- Docker vs sandbox, clarified [104], [105]: the Docker mental model everywhere, real Docker only on servers.
- Hooks and skills [115], [116]: LangChain middleware and the Deep Agents skills feature. QMX writes only the rules and the skill text.

### Phase G: copilot design with modes (2026-10-09, 19:01-19:12, [142]-[148])

- **The seed [142].** Skills, artifacts, "modes", rendering through the UI and creating mini apps. Study BMAD v6, CIS and BMad Builder, and combine with Wayfinder. Map the day-to-day copilot stories.
- Two studies [144], [147] produced COPILOT.md and P24 [148]: 5 modes, 13 skills, 16 hooks and 12 stories.

### Phase H: modes rejected, harness research (19:23-20:41, [149]-[172])

- **[149] He rejected modes** ("a mode can be replaced 90% over time by a skill"). The copilot should feel like Claude Code or Codex. New questions:
  - the system prompt;
  - cron jobs in workflows;
  - how solid the node editor is;
  - per-surface copilots for the Lab, Portfolio/Pod, mini apps and the general copilot;
  - the general copilot as a window over all sessions;
  - attachments, tools and RLM;
  - loop and prompt engineering;
  - caching for agents;
  - CLIProxy underneath all of it.

  He repeated "These things are not new... we don't have to reinvent".
- Claude withdrew modes and put P24 on hold [150], [151]. The safety rules stay as always-on hooks.
- **"Let's talk first" [152].** No plan was to be written before discussion [153].
- Studies run in sequence:
  - harness practices [154], [155];
  - six harness/memory papers [157], [161];
  - ten skill/tool papers [159], [164];
  - LangChain posts, cookbooks, loop and graph engineering [163], [169];
  - Hermes plus a harness comparison [167], [171].

  The operator's message that triggered the cookbooks study (the one [163] answers) is missing from the export.
- **His picks [167]:**
  - Claude Code for hooks and permissions;
  - Codex for tooling and computer use;
  - LangChain for compaction;
  - Hermes for memory.

  The comparison corrected two of them: computer use and compaction [171].
- The discussion never happened. Four questions in [155] went unanswered.

### Phase I: export (2026-10-12, [173]-[174])

He switched to his own account. The session ended with "paste the P16b summary, then the plain-words discussion, then the per-screen study" [174].

---

## 2. Seeds and brain dumps

| # | Seed (his idea, plain words) | Messages | Status |
|---|---|---|---|
| S1 | Every workflow agent node is a Deep Agent by default | [3], [6], [9], [21] ("needs more thought") | SHIPPED as a default (D§5.1 L96), with the general sub-agent off in nodes. QMA v2: an agent node is an SDK agent loop (R20 L63-66) |
| S2 | The copilot builds, controls and accesses workflows and mini apps, like Codex or Claude Code | [9], [21], [23], [36], [142], [149] | SHIPPED one copilot over `qmx-control` (P15 #47). Per-surface copilots OPEN |
| S3 | The copilot uses MCP Apps to build, open and control mini apps | [23], [24] | PLANNED (D§7.3 L274-282). UI rendering OPEN (D§13 L534) |
| S4 | Sub-agents are very important, especially at copilot level; delegate to workflows | [6], [23], [58], [65] | SHIPPED: sync sub-agents, background tasks, workflow as sub-agent (D§5.2, P15) |
| S5 | Mini apps feed each other (output becomes input) | [23] | SHIPPED by artifact reference (D§7.3 L278-281, P12 L39) |
| S6 | A mini app has its own database | [6], [14], [21] | SHIPPED (`app.db` per app, P12/P13) |
| S7 | Sandboxes for mini apps, Docker as the mental model | [17], [21], [104] | SHIPPED T1/T2 (P12, P17). QMA v2: sandboxes not needed by default (R20 L74-75) |
| S8 | YAGNI, decouple, modular by design ("spaghetti") | [17], [21] | SHIPPED as principles (D§2 L25-27) |
| S9 | Mini-app categories: with agents, without agents, headless, trading node | [21], [39] | SHIPPED as optional parts of one shape (D§7.1 L250-264) |
| S10 | Don't reinvent: copy Anthropic, LangChain and OpenAI patterns, cookbooks, docs | [21], [23], [65], [149], [159], [167] | STANDING RULE (D§2 L25, RM L19) |
| S11 | A model router | [21], [31] | SHIPPED (P06). QMA v2: router balances across providers and replaces CLIProxy (R20 L58-61) |
| S12 | CLIProxy on his own subscriptions (T3 Code style), several accounts and providers | [21], [58], [65] | SHIPPED as code (P06), never run live. SUPERSEDED: Claude only via the Agent SDK on the plan (R20 §4, L00 "REVERSED") |
| S13 | Automatic context compaction, as Anthropic and LangChain do it | [21], [149], [167] | SHIPPED Deep Agents summariser (D§5.5). Research says it breaks on Opus 5.5 [169], [171]. QMA v2: configurable summariser (R20 L68-69) |
| S14 | Hermes pluggable memory; he picks the provider | [6], [9], [21], [167] | SHIPPED (P07). QMA v2: SDK default memory plus the pluggable layer (R20 L41-42) |
| S15 | RLM for data-intensive work | [21], [149] | SHIPPED as the data-analyst sub-agent (P15 L16). RLM off by default [155] |
| S16 | Caching (Convex, TanStack), cheaper agents through better caching | [21], [67], [149] | SHIPPED five caching places (D§7.6b L334-341, P22). Convex REJECTED [25] |
| S17 | Per-app DB backed up to S3 or a bucket; "I can't keep everything on my machine" | [21], [58], [65], [67] | SHIPPED (P13, P21, P22) |
| S18 | Trading nodes in Singapore and New York; networking and observability for every app | [21] | PLANNED (D§7.1 L264, D§7.7). Docker node SHIPPED (P17) |
| S19 | Skills and hooks for the copilot, written with intent | [36], [115], [142], [149] | Hooks SHIPPED (P20 #44). Skills are placeholders only (P15) |
| S20 | IC Markets/cTrader back for CFDs; multi-broker, connection and account; CCXT; Hummingbot ideas | [9], [36] | SHIPPED (P18 #39), recorded fixtures only |
| S21 | A cTrader MCP for the copilot by default | [36] | SHIPPED (P18 L22-26), read plus `propose_order` |
| S22 | Charting provider | [36] | PLANNED: Lightweight Charts (D§11 L411), UI lane |
| S23 | Firecrawl, paid, for Alexandria | [36] | SHIPPED as an opt-in MCP entry (P19 #41) |
| S24 | Cron scraping of MQL5 articles | [36] | SHIPPED (P19 #41, 3,057 articles imported [113]) |
| S25 | Agents on a server with the laptop off; launch from the UI; Amp, Modal, E2B | [6], [9], [58], [62], [65] | SHIPPED (P21 #46) with fakes. QMA v2: no owned server, rented compute; no Amp orbs (R20 §4, L77) |
| S26 | Remote results "like Git" | [58] | SHIPPED (D§11b L429-434, P21) |
| S27 | Models are never set in stone; configure per sub-agent and workflow | [56], [58], [65] | SHIPPED model chain (D§5.3 L146-150) |
| S28 | A server setup script; recording happens automatically, not agentically | [65] | SHIPPED (P17 #40) but never run on a real server |
| S29 | VPS bucket on the same box; weekly private GitHub as the backup of the backup | [67] | SHIPPED (D§11b L453-463, P22) with live runs skipped |
| S30 | GPUs for agents; ONNX; models inside QMX | [67], [70] | PLANNED/SHIPPED placement (D§5.6b L201-207, P21 L12) |
| S31 | "Tooling for agents is a huge gap" | [67], [149] | SHIPPED tool catalogue (D§5.6b, P09). Open per surface |
| S32 | Study BMAD v6, CIS, BMad Builder and Wayfinder to build our own skills (and modes) | [142] | Research done ([144], [147]). Modes REJECTED [149] |
| S33 | No modes; skills; the copilot feels like Claude Code or Codex | [149] | BINDING. COPILOT §2 withdrawn (C L3), P24 on hold |
| S34 | Different copilots per surface (Lab, Portfolio/Pod, mini apps, general) | [149] | OPEN (per-screen study never run [153]) |
| S35 | The general copilot is a window over sessions from every surface | [149] | OPEN. Claude leaned yes [151] |
| S36 | Attachments, tools, RLM: when, and who uses them | [149] | OPEN |
| S37 | System prompt, meta-prompting research | [149] | PLANNED (harness-practices.md, [155]) |
| S38 | Cron jobs belong in workflows | [149] | PLANNED: cron/event/manual triggers [151] |
| S39 | Loop engineering, prompt engineering, graph engineering | [149], [163] | Research done ([169]). R20 §2.4 carries it on |
| S40 | Papers: remembering versus improving the harness | [157], [159] | Research done ([161], [164]) |
| S41 | Harness picks: Claude Code (hooks, permissions), Codex (tools, computer use), LangChain (compaction), Hermes (memory) | [167] | Researched; two picks corrected [171] |
| S42 | Computer use and browser use will be there | [167] | OPEN (only researched [171]) |
| S43 | Paper-trading soak of a week, with a monitoring agent | [6] | PLANNED (not in packets) |
| S44 | Agent permission model: most agents don't ask; a 60-hour job gets its authority at launch | [6] | PLANNED (`interrupt_on`, headless mode C§6 L107) |

---

## 3. Functional requirements

Format: **ID**: QMX shall ... · *Src* [messages] · *Where* doc/packet and line · status.

### 3.1 Copilot and organogram

- **FR-A01**: QMX shall give the operator a copilot that can create, edit, test, publish, run and inspect mini apps and workflows, using only the API the UI uses (no back doors). · *Src* [9], [21], [22], [23], [36] · *Where* D§1 L13, D§8 L354-366, P15 L4, L31 · SHIPPED (P15 #47, fake models)
- **FR-A02**: QMX shall let the copilot hand quick isolated jobs to sub-agents that return artifact references, not long text. · *Src* [6], [23], [31] · *Where* D§5.2 L107, L113, P15 L16 · SHIPPED (P15: `researcher`, `data-analyst`, `app-builder`)
- **FR-A03**: QMX shall let the copilot delegate to a saved workflow as if it were a sub-agent. · *Src* [23], [31] · *Where* D§5.2 L109, P10 L27 · SHIPPED (P10 #36, `as_subagent`)
- **FR-A04**: QMX shall let the copilot start, check, cancel and list long background tasks, then hand control back so the chat stays live. · *Src* [31], [58], [76] · *Where* D§5.2 L108, D§12b L489-491, DP L36 · SHIPPED (`BackgroundTasks.tools`)
- **FR-A05**: QMX shall let the copilot create new agents and sub-agents (an agent is a settings file). · *Src* [6], [22] · *Where* D§5.1 L75-101, P12 L22 · PLANNED (AgentSpec SHIPPED P06; copilot authoring of specs not built)
- **FR-A06**: QMX shall feel like Claude Code or Codex: the operator invokes a skill and work starts; there are no modes. · *Src* [149], [150] · *Where* C L3 (§2 withdrawn), P24 L1 · Modes REJECTED; skills-first PLANNED
- **FR-A07**: QMX shall provide surface copilots (Lab, Portfolio/Pod, mini apps, general), each with its own skills, hooks and tools. · *Src* [149], [151] · *Where* none · OPEN (per-screen study held [153])
- **FR-A08**: QMX shall present the general copilot as one window over sessions started on any surface. · *Src* [149], [151] · *Where* none · OPEN
- **FR-A09**: QMX shall give a mini app an "app-use" copilot that can operate the app but not edit it; edits go back to authoring as a change request. · *Src* [14] · *Where* C§3 L47 (story) · PLANNED
- **FR-A10**: QMX shall stream each copilot run to the UI as typed blocks: text, plan, agents, tool calls, artifact, question, permission, panel draft. · *Src* [28] · *Where* P15 L20 · SHIPPED (P15)
- **FR-A11**: QMX shall give the copilot the cTrader/broker MCP by default (read tools plus `propose_order` only). · *Src* [36], [38] · *Where* D§11 L407, P18 L22-26 · SHIPPED (P18 #39)
- **FR-A12**: QMX shall let the copilot and workflows call any running mini app as an MCP client, and let external hosts (Claude Desktop, VS Code) open the same apps. · *Src* [23], [24] · *Where* D§7.3 L276-277 · SHIPPED (P12 #37)
- **FR-A13**: QMX shall map the operator's day-to-day copilot stories: build a workflow, build or change an app, run overnight and brief in the morning, assess a strategy idea, fix a broken app, connect a broker or data source, schedule a routine, map a huge effort, capture a repeated procedure. · *Src* [142], [148] · *Where* C§3 L41-56 · PLANNED (the mode column is void)

### 3.2 Agent core

- **FR-A14**: QMX shall define every agent in a settings file: model, prompt, tools, MCP servers, skills, memory scope, sub-agents, background tasks, approvals, file permissions, budget. · *Src* [22] · *Where* D§5.1 L77-94, P06 L12-17 · SHIPPED (P06 #31)
- **FR-A15**: QMX shall make a full agent loop (planning, sub-agents, files, skills, approvals) the default for every agent, including workflow nodes. · *Src* [3], [6], [9], [21] · *Where* D§5.1 L96 · SHIPPED (general sub-agent off in workflow nodes)
- **FR-A16**: QMX shall give each agent its own tools, MCP servers and data routes; a sub-agent gets only its own tools. · *Src* [21], [22] · *Where* D§5.1 L97-100, P06 L58-59 · SHIPPED
- **FR-A17**: QMX shall never hard-code a model. A chain (global → node → app → workflow → agent node → sub-agent) sets a tier or exact model at any level, and the model actually used is recorded per run. · *Src* [56], [58], [65], [66] · *Where* D§5.3 L146-150, P06 L39 · SHIPPED (`resolve_model`)
- **FR-A18**: QMX shall route work to model tiers (fast, workhorse, coding, reasoning_high) with fallback and retry on provider errors. · *Src* [21], [31] · *Where* D§5.3 L117-120, P06 L18-22 · SHIPPED
- **FR-A19**: QMX shall run on the operator's subscriptions as the daily path (Opus for the copilot, Sol for sub-agents and workflow/app agents, Luna for quick steps), with a separate test profile. · *Src* [58], [64] · *Where* D§5.3 L121-151, P06 L30-37 · SHIPPED as config; live smoke never run [83]
- **FR-A20**: QMX shall show the provider proxy's accounts, quota bars (5-hour and 7-day) and login buttons in a native Settings panel. · *Src* [65], [73] · *Where* D§5.3 L134, P06 L49 · PLANNED (management client only)
- **FR-A21**: QMX shall run data-heavy work in a Python sandbox sub-agent (RLM style: load as variables, filter in code, call sub-models only on slices, return compact results plus an artifact path). Recursive RLM is off by default and reserved for dense work in workflows. · *Src* [21], [22], [149], [155] · *Where* D§5.6 L177-185, D§12b L492-494 · SHIPPED as a sub-agent spec; real sandbox unproven [137]
- **FR-A22**: QMX shall use a short system prompt (about 1.5-3k tokens, each rule said once) and keep how-to in skills, tool descriptions and an AGENTS.md-style file. · *Src* [149], [155] · *Where* `harness-practices.md` · PLANNED
- **FR-A23**: QMX shall stop an agent only when a tool result proves the work, or with a named blocker, and after two failed attempts at the same approach. · *Src* [155], [169] · *Where* C§5 L91, `cookbooks-loops-graphs.md` · PLANNED
- **FR-A24**: QMX shall treat a text-only end of turn from Opus 5.5 as progress, not "done", and drive long goals with a goal contract checked against files on disk (2-3 automatic continuations at most). · *Src* [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A25**: QMX shall manage context with one summariser, offload large tool results to files, and keep Opus history append-only (summarise only at task boundaries or server-side). · *Src* [21], [155], [169], [171] · *Where* D§5.5 L168-175 · SHIPPED Deep Agents defaults; the Opus-safe change is OPEN
- **FR-A26**: QMX shall let an agent recall archived history by summary ID. · *Src* [161] · *Where* `papers-harness-memory.md` · PLANNED
- **FR-A27**: QMX shall fan out bulk coverage (every symbol or fold) from code, not model choice, with the interpreter tool gated. · *Src* [31], [169] · *Where* D§5.2 L110 · PLANNED
- **FR-A28**: QMX shall trace every run locally and keep a small golden eval set per agent spec. · *Src* [6], [9] · *Where* D§5.8 L218-221 · PLANNED (no packet)
- **FR-A29**: QMX shall give a long unattended job its authority at launch and pause it only on a defined exception, not on routine approvals. · *Src* [6] · *Where* D§5.1 L91 (`interrupt_on`), C§6 L107 · PLANNED

### 3.3 Tools

- **FR-A30**: QMX shall expose its quant engine (data, backtest, research, node) as a few task-shaped typed tools, also served as MCP servers. · *Src* [21], [22] · *Where* D§6 L223-229, P09 L11-19 · SHIPPED (P09 #34: 13 tools, 4 servers)
- **FR-A31**: QMX shall design every tool with a plain description, typed args, concise/detailed output, pagination, fix-it errors, and large output saved as an artifact reference. · *Src* [31] · *Where* D§6 L231-236, P09 L21-27 · SHIPPED
- **FR-A32**: QMX shall offer agents only these tool kinds: domain, platform API, files and artifacts, code execution on a chosen target, jobs on a target, web, and operator-added MCP, each on a per-agent allow-list. · *Src* [67], [69] · *Where* D§5.6b L187-199 · SHIPPED in part (P09, P21 `run_job`)
- **FR-A33**: QMX shall keep about 10-15 tools visible per agent, with the long tail behind a tool search that is visible by name. · *Src* [155], [171] · *Where* `harness-practices.md` · PLANNED
- **FR-A34**: QMX shall let the operator add MCP servers in Settings (Firecrawl paid and off by default). · *Src* [36], [38] · *Where* D§11 L409, P19 L19, P11 L16 · SHIPPED (P19 #41)
- **FR-A35**: QMX shall let agents write new tools and MCP servers, run that code isolated first, and move it to the laptop only after operator review. · *Src* [21] · *Where* D§7.1 L255, D§7.5 L301 · PLANNED
- **FR-A36**: QMX shall let an agent ask for a GPU through a job and place it on a GPU node or rented provider; agents never touch drivers. · *Src* [67], [70], [71] · *Where* D§5.6b L201-207, P21 L12 · SHIPPED (placement, fakes)
- **FR-A37**: QMX shall give agents computer use and browser use. · *Src* [167] · *Where* `hermes-and-harness-comparison.md` (cua-driver over MCP, browser-use, Codex-style in-app browser) · OPEN
- **FR-A38**: QMX shall accept attachments in copilot chat and route them to tools. · *Src* [149] · *Where* none · OPEN
- **FR-A39**: QMX shall improve tool descriptions offline from past calls (weekly), shipped as versioned descriptions. · *Src* [164] · *Where* `papers-skills-tools.md` · PLANNED

### 3.4 Hooks and guards

- **FR-A40**: QMX shall never give any agent an order-capable tool. Agents may only `propose_order`, and the operator signs in Portfolio. · *Src* [36], [38], [50] · *Where* D§5.7 L215, D§12 L477, P08 L21-23 · SHIPPED (P08 #35, `MoneyPathMiddleware`)
- **FR-A41**: QMX shall journal every run, model call, tool call (with argument hash and result reference), interrupt and approval, append-only. · *Src* [38], [50] · *Where* D§5.7 L213, P08 L10-17 · SHIPPED (`RunJournal`)
- **FR-A42**: QMX shall stage proposals, run deterministic checks, ask the operator, and keep before/after records (admission). · *Src* [50] · *Where* D§12 L478, P08 L18-20, DP L35 · SHIPPED (`AdmissionGate`)
- **FR-A43**: QMX shall cap model calls, tool calls and money per turn and per job, editable in Settings. A USD cap pauses rather than fails. · *Src* [38], [155], [169] · *Where* D§5.7 L216, P08 L24-25 · SHIPPED call caps; USD pause PLANNED
- **FR-A44**: QMX shall refuse to publish an app whose manifest is invalid or tests are red, tell the copilot and operator when an app breaker trips, test every new version automatically, and save memory before compaction. · *Src* [36], [38] · *Where* D§11 L396-401, P20 L27-35 · SHIPPED (P20 #44, `AppHooksMiddleware`)
- **FR-A45**: QMX shall always ask the operator before: publish, install, grant, schedule, spend over budget, any paper-account action, delete. · *Src* [150], [155] · *Where* C§5 L88 · PLANNED (list unconfirmed by operator)
- **FR-A46**: QMX shall keep keys, tokens and account numbers out of chat, tool results and the journal, and collect credentials through a secure form into Credential Manager. · *Src* [57], [144] · *Where* C§4 L73, C§5 L87 · PLANNED
- **FR-A47**: QMX shall keep a short hardline deny-list no setting can relax, and deny by default in unattended, cron and workflow runs. · *Src* [164], [171] · *Where* `hermes-and-harness-comparison.md` · PLANNED
- **FR-A48**: QMX shall order hook decisions Claude-Code style (deny > defer > ask > allow); gates fail closed, observers fail open. · *Src* [167], [171] · *Where* `hermes-and-harness-comparison.md` · PLANNED
- **FR-A49**: QMX shall send back a "done / fixed / passing" claim without a verification artifact, then label it unverified. · *Src* [144], [148] · *Where* C§5 L91 · PLANNED (P24 on hold)
- **FR-A50**: QMX shall stop review/fix loops after 5 rounds and return to the operator. · *Src* [147], [148] · *Where* C§5 L93 · PLANNED
- **FR-A51**: QMX shall run write and money tools one at a time, detect the same call repeated three times, and block tool calls from a reply cut off at the length limit. · *Src* [164] · *Where* `papers-skills-tools.md` · PLANNED
- **FR-A52**: QMX shall check every quoted number against a tool output and every cited ID for existence before a final answer. · *Src* [161] · *Where* `papers-harness-memory.md` · PLANNED

### 3.5 Memory

- **FR-A53**: QMX shall have one pluggable memory interface: built-in memory plus at most one external provider, chosen by the operator in Settings. · *Src* [6], [9], [21], [25] · *Where* D§5.4 L156-158, P07 L4 · SHIPPED (P07 #33)
- **FR-A54**: QMX shall scope memory as task (inside workflow), workflow, copilot session and global. · *Src* [6], [25] · *Where* D§5.4 L159, P07 L15-19 · SHIPPED
- **FR-A55**: QMX shall let only the primary agent write memory automatically, require approval for global writes, and cap prompt-bound memory. · *Src* [25] · *Where* D§5.4 L163-166, P07 L26-29 · SHIPPED
- **FR-A56**: QMX shall separate records (automatic), memory (automatic, visible and editable in the UI) and policy (prompts, skills, tools, which change only through an operator-approved proposal, one edit at a time, with rollback). · *Src* [157], [161], [163] · *Where* `papers-harness-memory.md` · PLANNED
- **FR-A57**: QMX shall retrieve narrowly (1-3 records on action turns) with keyword search first; semantic search comes after a `sqlite-vec` Windows spike. · *Src* [161] · *Where* D§13 L533 · PLANNED
- **FR-A58**: QMX shall add Mem0, Honcho or Hindsight adapters later, one at a time, and never LangMem. · *Src* [21], [23], [31] · *Where* D§5.4 L161-162, P07 L34 · PLANNED; LangMem REJECTED

### 3.6 Sessions and errands

- **FR-A59**: QMX shall keep every copilot session and agent thread resumable from checkpoints, and expose create/list/append/stream. · *Src* [28] · *Where* D§7.6b L324, P11 L17 · SHIPPED
- **FR-A60**: QMX shall keep an append-only log per task ("nothing exists until it is a file"), offer resume by run ID, and never merge two runs. · *Src* [147], [148] · *Where* C§6 L105-106 · PLANNED (P24 on hold)
- **FR-A61**: QMX shall run overnight and scheduled work headless (no questions) and end with an "assumptions to confirm" card. · *Src* [83], [87], [147], [148] · *Where* C§6 L107, P24 L30 · PLANNED
- **FR-A62**: QMX shall give each errand a "What it did" receipt and a drawer with activity, diff, terminal and browser. · *Src* [28] · *Where* UI only (`ui-model-and-baseline-audit.md`) · PLANNED backend
- **FR-A63**: QMX shall let the operator pick a stance per task: do it for me, pair with me, coach me. · *Src* [147], [148] · *Where* C§2 L34-39 · PLANNED (sat inside the withdrawn §2)

### 3.7 Workflows

- **FR-A64**: QMX shall store a workflow as a typed JSON graph (python, agent, tool, app_call, condition, parallel, join, loop, human_gate, subworkflow) and compile it to a runnable, checkpointed graph. · *Src* [21], [22] · *Where* D§7.4 L286-289, P10 L12-26 · SHIPPED (P10 #36)
- **FR-A65**: QMX shall allow deterministic, agentic and mixed workflows. · *Src* [9], [14] · *Where* D§7.4 L289 · SHIPPED
- **FR-A66**: QMX shall reject a cycle without a loop node, an edge whose port types don't match, and a loop without a maximum. · *Src* [14] · *Where* P10 L20, L32-33 · SHIPPED
- **FR-A67**: QMX shall pause at human gates and resume. · *Src* [31] · *Where* P10 L21, L28 · SHIPPED
- **FR-A68**: QMX shall start workflows by cron, event or manual trigger, with overlap policies. · *Src* [6], [149], [151], [169] · *Where* none (apps have schedules, P12 L24) · PLANNED
- **FR-A69**: QMX shall show one workflow as Graph, Code and Import views of the same JSON. · *Src* [28] · *Where* D§7.4 L291, P10 L29 · SHIPPED (`to_python`, best effort)
- **FR-A70**: QMX shall put a human gate, an idempotency key and no auto-retry before any node that touches money or writes externally. Cycles need a round cap and a no-improvement exit, fan-outs are capped, and joins name a merge rule. · *Src* [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A71**: QMX shall expose saved workflows to the copilot as "workflow skills" through one `run_workflow` tool. · *Src* [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A72**: QMX shall follow scheduled-job rules: read from per-source bookmarks, never report a failed read as a quiet day, confirm a write before updating the ledger, re-check before acting, state the timezone. · *Src* [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A73**: QMX shall run a workflow inside an app or standalone as a job. · *Src* [22] · *Where* D§7.4 L290 · SHIPPED

### 3.8 Mini apps and apps

- **FR-A74**: QMX shall treat every mini app as one shape: an immutable, hashed definition, a running instance, and its own data. Agents, workflows, screens, schedules and tools are optional parts. · *Src* [17], [21], [22], [39], [40] · *Where* D§7.1 L240-256, P12 L18-27 · SHIPPED (P12 #37)
- **FR-A75**: QMX shall give each app its own database, memory file (if it has agents), Parquet data and blobs. · *Src* [6], [14], [21] · *Where* D§7.1 L246, P12 L28 · SHIPPED
- **FR-A76**: QMX shall run apps in isolation tiers: laptop subprocess with its own venv, limits and scrubbed environment; Docker on servers; remote sandbox for untrusted work. · *Src* [17], [21], [104], [105] · *Where* D§7.5 L293-301, P12 L29-37, P17 · SHIPPED T1 (#37), T2 (#40)
- **FR-A77**: QMX shall make every app an MCP server, and pass app-to-app data as typed artifact references with no direct bus. · *Src* [23], [24] · *Where* D§7.3 L274-282, P12 L38-39 · SHIPPED
- **FR-A78**: QMX shall classify apps by what they can touch (shows / runs work / money) and move each version Build → Tests → Sandbox → Shadow → Live, with evidence per step and rollback. · *Src* [28], [29] · *Where* D§7.2 L266-272, P14 · SHIPPED (P14 #42)
- **FR-A79**: QMX shall provide logs, heartbeat, metrics, breaker state and placement for every app from the host; no app builds its own. · *Src* [21], [22], [58] · *Where* D§7.7 L343-352 · SHIPPED (P12)
- **FR-A80**: QMX shall enforce a budget and circuit breaker per app and record why it tripped. · *Src* [28] · *Where* P12 L36 · SHIPPED
- **FR-A81**: QMX shall render app screens as MCP Apps panels or tier-1 JSON panels, with screen state re-read from the app's database. · *Src* [23], [24] · *Where* D§7.3 L282, D§13 L534 · PLANNED (UI)
- **FR-A82**: QMX shall run a lint gate before any app, workflow or skill draft is saved: no money tools, declared capabilities match used tools, tests present, manifest valid. · *Src* [147], [148] · *Where* C§7 L117-121, P24 L35-41 · PLANNED
- **FR-A83**: QMX shall import a notebook, script or someone else's strategy and rebuild it as a workflow or app. · *Src* [147], [148] · *Where* C§7 L126 · PLANNED
- **FR-A84**: QMX shall make everything a user builds versioned, hash-addressed and shareable as a bundle (no marketplace). · *Src* [14], [147] · *Where* C§7 L127 · PLANNED
- **FR-A85**: QMX shall run a trading node as a headless app on a server with live permissions (Singapore, New York). · *Src* [21], [22] · *Where* D§7.1 L264, P17 L4 · PLANNED (Docker tier SHIPPED)
- **FR-A86**: QMX shall ship "Macro daily bias" as the first end-to-end app (agent app, screens, schedule, own data). · *Src* [20], [21], [22] · *Where* P15 L21-27, D§13 L535 · SHIPPED (P15 #47, fake models)

### 3.9 Research harness

- **FR-A87**: QMX shall scrape MQL5 articles daily as a headless app, politely and without refetching, and feed the Library. · *Src* [36], [38] · *Where* P19 L13-18 · SHIPPED (P19 #41)
- **FR-A88**: QMX shall offer Firecrawl (with Alexandria) as an opt-in paid MCP for the researcher sub-agent. · *Src* [36] · *Where* P19 L19 · SHIPPED (off by default)
- **FR-A89**: QMX shall provide a deep-research skill with hard caps (5 parallel researchers, 6 supervisor rounds, 10 tool calls each). · *Src* [58], [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A90**: QMX shall keep idea generation separate from narrowing down in strategy research, using technique catalogues stored as data. · *Src* [147], [148] · *Where* C§4 L70 · PLANNED

### 3.10 Remote runs and placement

- **FR-A91**: QMX shall send a workflow, app or agent run to a remote target from the UI and keep it working with the laptop off. · *Src* [6], [9], [58], [65] · *Where* D§11b L415, P21 L4 · SHIPPED (P21 #46, fakes)
- **FR-A92**: QMX shall make remote results Git-like: a manifest, hashed artifacts, incremental upload of journal, logs, traces and checkpoints, `fetch`, resume elsewhere, and code changes on a `runs/<id>` branch. · *Src* [58], [64] · *Where* D§11b L429-434, P21 L19-26 · SHIPPED
- **FR-A93**: QMX shall put every compute provider behind one interface (provision, start, status, logs, stop, teardown). · *Src* [58], [62] · *Where* D§11b L417-422, P21 L13-18 · SHIPPED (ssh, amp, modal, e2b, stubbed)
- **FR-A94**: QMX shall set up a fresh server with one idempotent command plus a pass/fail verify, with secrets typed into a guided prompt. · *Src* [65], [66] · *Where* D§11b L438-448, P17 L16-24 · SHIPPED (#40), never run on a real server
- **FR-A95**: QMX shall record everything a server does automatically, so no agent has to remember to log. · *Src* [58], [65] · *Where* D§11b L449 · SHIPPED (supervisor journaling)
- **FR-A96**: QMX shall show for each job where it runs, its cost so far, a live log tail and status, and offer "resume elsewhere". · *Src* [28], [58] · *Where* D§11b L465 · PLANNED (UI)
- **FR-A97**: QMX shall inject per-run credentials and remove them at teardown. · *Src* [58] · *Where* D§11b L436, P21 L27 · SHIPPED (references only)

### 3.11 Storage, buckets and backups

- **FR-A98**: QMX shall keep all data as files (SQLite, DuckDB over Parquet, JSONL, blobs), each with one writer, and no database server. · *Src* [25], [67], [69] · *Where* D§7.6b L314, D§10 L389 · SHIPPED (as rule, P13/P22)
- **FR-A99**: QMX shall snapshot each app database without stopping it, upload it with checksums, restore-test every run, and back up nightly plus "now". · *Src* [21], [25] · *Where* D§7.6 L305-307, P13 L14-20 · SHIPPED (P13 #38)
- **FR-A100**: QMX shall keep three copies: the remote bucket, the laptop, and a weekly private GitHub repo for small, precious data (no files over 95 MB, no Parquet). · *Src* [67], [69] · *Where* D§11b L453-463, P22 L22 · SHIPPED (#43), live run skipped
- **FR-A101**: QMX shall let the operator swap the bucket provider in Settings. · *Src* [65] · *Where* D§11b L461, P21 L23 · SHIPPED
- **FR-A102**: QMX shall cache in only five places: upstream data, backtest result memo, provider prompt caching, expensive read tools (TTL), and UI aggregates pushed over SSE. No Redis. · *Src* [21], [67], [69], [149] · *Where* D§7.6b L334-341, P22 L19-21 · SHIPPED (memo, TTL); prompt caching under the proxy unproven

### 3.12 Library (seam only for QMA v2, R20 L15-16)

- **FR-A103**: QMX shall save every result as a typed, versioned, content-addressed Library artifact with full-text search; Lab strategies and pods are Library items. · *Src* [69], [71] · *Where* D§7.6b L321-322, P22 L12-17 · SHIPPED (#43); QMA v2 calls only the seam
- **FR-A104**: QMX shall index every run with kind, target, resolved model, status, cost and artifacts. · *Src* [64], [73] · *Where* P22 L18 · SHIPPED
- **FR-A105**: QMX shall store trained models as Library items (ONNX file, training run, data snapshot, metrics, version). · *Src* [70], [71] · *Where* D§5.6b L205-206 · PLANNED

### 3.13 Brokers and money path

- **FR-A106**: QMX shall model many brokers, connections (demo or live) and accounts: IC Markets via cTrader for CFDs, CCXT for crypto. · *Src* [9], [36], [38] · *Where* D§11 L402-406, P18 L12-21 · SHIPPED (P18 #39, recorded fixtures)
- **FR-A107**: QMX shall allow paper-account actions only behind approval and give agents no live trading. · *Src* [6], [148], [155] · *Where* C§9 L140 · PLANNED
- **FR-A108**: QMX shall run a week-long paper soak with a separate monitoring agent, in the background on a pinned version. · *Src* [6] · *Where* none · PLANNED

### 3.14 Usage and costs

- **FR-A109**: QMX shall record tokens and cost per run itself, because the proxy keeps no history. · *Src* [72], [73] · *Where* D§5.3 L135, P22 L18 · SHIPPED in part (journal plus run-index cost field)
- **FR-A110**: QMX shall spread subscription use across accounts (soonest reset first) and keep a thread on one account so its cache survives. · *Src* [58], [65], [72], [73], [155] · *Where* D§5.3 L130-133 · PLANNED (proxy never installed)
- **FR-A111**: QMX shall keep recurring and parallel agent work affordable (cron macro analysis, "12 agents all running"). · *Src* [58] · *Where* D§5.3 L138-144 · PLANNED (QMA v2 router, R20 L58-61)

### 3.15 UI contract

- **FR-A112**: QMX shall serve one service layer through two doors: REST plus SSE for the UI (generated OpenAPI) and MCP for the copilot, with identical results. · *Src* [22], [23] · *Where* D§8 L356-357, P11 L11-21 · SHIPPED (P11 #32)
- **FR-A113**: QMX shall return an honest `not_implemented` error, never a fake success. · *Src* [28] · *Where* P11 L24 · SHIPPED
- **FR-A114**: QMX shall make every copilot output a typed artifact (card, preview or Library item) streamed to the UI, never only chat text. · *Src* [142], [148] · *Where* C§1 L18, C§5 L92 · PLANNED
- **FR-A115**: QMX shall show Opus progress updates during long turns. · *Src* [169] · *Where* `cookbooks-loops-graphs.md` · PLANNED
- **FR-A116**: QMX shall make everything configurable editable in Settings: providers, model chain, MCP servers, budgets, memory provider, bucket, per-skill knobs. · *Src* [65], [66], [148] · *Where* D§2 L33, P11 L16, C§4 L60 · SHIPPED backend; per-skill knobs PLANNED
- **FR-A117**: QMX shall push UI updates over SSE, never by polling. · *Src* [69] · *Where* D§7.6b L339 · SHIPPED
- **FR-A118**: QMX shall serve bars and indicators for TradingView Lightweight Charts. · *Src* [36], [38] · *Where* D§11 L411 · PLANNED (UI lane)

### 3.16 Anything else: skills and process

- **FR-A119**: QMX shall hold procedure in skills, written by Claude with the operator, with intent, one at a time, naming real tools. Five started in P20; 13 are in COPILOT §4. · *Src* [36], [38], [142], [148] · *Where* D§11 L394-395, P20 L19-25, C§4 L62-76 · PLANNED (P15 shipped placeholders)
- **FR-A120**: QMX shall ship a skill only if it beats a no-skill run on the same test prompts, keep the skill list small with no near-duplicates, and flag duplicates. · *Src* [164], [166] · *Where* `papers-skills-tools.md` · PLANNED
- **FR-A121**: QMX shall let the copilot capture a repeated procedure as a new skill draft with trigger tests and operator approval. A money-path skill is never created or changed without approval. · *Src* [147], [161], [164] · *Where* C§4 L76, C§5 L99 · PLANNED
- **FR-A122**: QMX shall give each skill a settings file whose knobs show in Settings. · *Src* [147], [148] · *Where* C§4 L60 · PLANNED
- **FR-A123**: QMX shall use a coding agent through small work packets, each with "Done when" tests and one PR, and no ceremony. · *Src* [21], [22] · *Where* RM L6-22 · SHIPPED (process)

---

## 4. The LangChain/LangGraph-era feature set to port to the two SDKs

"Engine-neutral" means the logic is QMX's own and only the binding changes. "LangChain-bound" means the feature exists because a LangChain or Deep Agents primitive provides it. The QMA v2 column is the proposed home. Where it is inferred rather than ratified, it says so. The SDK capabilities cited are in R19 §10 (the mapping table) and R20.

| Feature | What it does | Where it lives now | Bound? | Under QMA v2 |
|---|---|---|---|---|
| **Copilot** | Main agent; builds and runs apps and workflows through `qmx-control` MCP; streams typed blocks | `agents/copilot.yaml`, `qmx_agents.copilot.build_copilot`, `stream_turn` (DP L33); P15 #47 | Bound (`create_deep_agent`) | A Claude Agent SDK session on the plan, with a custom QMA system prompt and the plugin for its surface (R20 L47-50, §3 items 2-3). The typed block stream and `qmx-control` MCP door stay as they are |
| **AgentSpec** | YAML that sets model, tools, MCP, skills, memory, sub-agents, approvals, budget | `qmx_agents.spec.load_spec`, `build_agent` (D§9 L372); P06 #31 | Neutral schema, bound builder | Keep the spec. Write one builder per engine: Claude → `AgentDefinition` / options; OpenAI → `Agent(...)`. The spec becomes the engine-neutral seam (R19 §11) |
| **Sub-agents (sync)** | Quick isolated jobs; return artifact references | Deep Agents `task` tool; P15 L16 | Bound | Claude: native sub-agents (Agent tool). OpenAI: `as_tool` or handoffs, with any provider per agent (R19 §10 "Sub-agents"). Preferred pattern: Claude's (R20 L53-56) |
| **start_task background tasks** | `start_task`, `check_task`, `cancel_task`, `list_tasks`; chat stays live; Activity panel | `BackgroundTasks.tools` + `qmx-control` runs (D§12b L489-491, DP L36) | Neutral (QMX-owned, chosen because `AsyncSubAgent` needed an Agent Server) | Keep as QMX tools over `qmx-control` runs, bound into both engines (in-process MCP). The run inside becomes an engine session, resumed by ID (R20 §3 item 2) |
| **Workflow as sub-agent** | An agent delegates to a compiled workflow | `as_subagent` → `CompiledSubAgent` (P10 L27) | Bound | A `run_workflow` tool over QMX's own graph runner (R20 L63-66; FR-A71) |
| **Code-driven fan-out** | Bulk coverage by code, interpreter gated | `CodeInterpreterMiddleware` (QuickJS) (D§5.2 L110, D§12b L494) | Bound | QMX graph `parallel` nodes, or Claude dynamic-workflow `parallel()` patterns as built-in templates (R20 §2.1, §3 item 4) |
| **Data analyst (RLM)** | Python sandbox sub-agent over app data | `data-analyst` spec; sandbox backend adapter (D§12b L492-493) | Bound (backend protocol) | A sub-agent with a QMX Python-exec tool on a chosen target. Sandboxes are off by default (R20 L74-75), so laptop T1 or a rented box |
| **Model router (P06)** | Tiers, chain resolution, fallback/retry, provider list, CLIProxy client | `qmx_agents.router.ModelRouter.resolve`, `resolve_model`, `router_middleware` (DP L34) | Mixed: the chain is neutral, the middleware is bound | The chain survives. The router now balances usage across providers and sessions, never single requests, and replaces CLIProxy (R20 L58-61). Claude is reachable only via the Agent SDK on the plan (R20 §4) |
| **Memory (P07)** | Built-in + one provider; 4 scopes; primary-only writes; global approval | `StoreMemoryProvider`, `MemoryManager.middleware` (DP L35); SqliteStore | Mixed: the protocol is neutral, the hooks are middleware, the default store is LangGraph | SDK default memory (Claude memory/CLAUDE.md, OpenAI Sessions) under QMX's pluggable interface (R20 L41-42). Keep the scopes and rules. Hooks move to SDK hooks (Claude) or session wrappers (OpenAI) |
| **Context/compaction** | 85% summariser, offload over 20k tokens, pre-compress memory hook | Deep Agents defaults (D§5.5) | Bound | A configurable Hermes-style summariser with a chosen model (R20 L68-69). Claude auto-compaction is summary-only and safe (R19 §10); OpenAI needs a custom summarising Session. Keep the archive-recall idea (FR-A26) |
| **Guards (P08)** | Journal, admission, money-path refusal at build and invoke time, call caps | `RunJournal`, `MoneyPathMiddleware`, `AdmissionGate`/`AdmissionBackend` (DP L36) | Rules neutral, binding bound | The rules move into QMX's own tool wrappers so both engines enforce them. Claude hooks can deny or rewrite; OpenAI hooks only observe, so blocking goes in tool guardrails and approvals (R19 §10 "Hooks") |
| **Hooks (P20)** | Publish gate, breaker → needs-you, auto-test new version, pre-compaction memory | `AppHooksMiddleware` (DP L36); P20 #44 | Rules neutral | Claude: `PreToolUse`/`PostToolUse`/`PreCompact`-type events. OpenAI: tool guardrails plus QMX wrapper. App events (breaker, new version) come from the supervisor, not the engine |
| **Approvals** | `interrupt_on` per tool; human gates in workflows; admission | AgentSpec `interrupt_on` (D§5.1 L91); P10 `human_gate` | Bound | Claude: `can_use_tool` callback or `defer` (one parked call). OpenAI: interruptions plus serialisable `RunState` (many pending) (R19 §10 "Approvals"). The approval card UI stays the same |
| **Prompt caching** | Automatic for Claude through `ChatAnthropic`; session affinity on the proxy | D§5.5 L173, D§7.6b L338 | Bound | Claude SDK caches automatically (R19 §10 "Caching"). OpenAI uses `prompt_cache_options`. Rule: no mid-thread tool, model or system-prompt swaps (NFR-A12) |
| **Workflows (P10)** | JSON graph → LangGraph `StateGraph` with SQLite checkpointer; run API | `qmx_agents.workflows.compiler.compile`, `WorkflowRuns` (DP L33) | Schema neutral, compiler bound | QMX's own graph runner: graph JSON, a node checkpoint in SQLite, resume (R20 L63-66). Keep the node kinds, port checks and run API. Add triggers and graph safety rules |
| **Research (P19)** | MQL5 scraper app, Firecrawl MCP | `examples/apps/mql5-articles`; settings entry | Neutral | Unchanged; the researcher sub-agent's MCP list moves to its plugin |
| **Remote runs (P21)** | ComputeProvider (ssh, amp, modal, e2b), Git-style results, fetch/resume | `qmx_remote` (P21) | Neutral | Keep. Re-target to rented on-demand providers (no owned server, no Amp orbs: R20 §4, L77). Resume means engine session resume plus graph checkpoint |
| **Copilot app build (P15)** | Copilot builds Macro daily bias from a paragraph | `scripts/live/copilot_build_app.py`; `examples/apps/macro-daily-bias` | Bound (copilot) | The first QMA v2 acceptance scenario: rerun it on the Claude engine, live, on the plan (Wednesday minimum, R20 L82-87) |
| **Skills** | Agent Skills folders; 5 in P20 and 13 in COPILOT §4; placeholders only | `qmx-agents/skills/` (P20 L9) | Format neutral (agentskills.io) | Claude loads skills natively; OpenAI needs a loader. Skills ship inside plugins (R20 L47-50, §3 item 3) |
| **Artifacts** | Results as references; Library save; artifact index for app-to-app | P09 L27, P12 L39, P22 | Neutral | Unchanged. The Library stays a seam (R20 L15-16). `ArtifactEmitter` (C§5 L92) is still to build |
| **Session/thread store** | LangGraph checkpoints `copilot/threads.db`; typed block log | D§7.6b L324, P11 L17 | Bound (checkpointer) | Claude: session JSONL resume/fork by ID. OpenAI: `Session` protocol with a QMX backend (R19 §10 "Sessions"). QMX keeps its own block log for the UI |
| **Tracing** | LangSmith or local OTel | D§5.8 L220 | Bound | SDK tracing stored locally, never sent to OpenAI (R20 L71-72). Claude exports OTel natively; OpenAI needs a custom processor (R19 §10) |
| **MCP client/servers** | `MCPAdapter`, FastMCP 4 servers for tools, control and apps | D§12b L487-488 | Client bound, servers neutral | Both SDKs speak MCP. Claude can also use in-process `@tool` MCP. The FastMCP servers stay |
| **Plugins** | (seed) "a plugin is skills + hooks + tools" [149] | not built | n/a | The organogram unit: MCP/tools + skills + model + hooks; a session loads one by default (R20 L47-50) |

---

## 5. Non-functional requirements

- **NFR-A01 Cost: subscription first.** Daily agent work must not need pay-per-token API spend for Claude or Codex. Recurring and parallel work must be costed before it ships. *Src* [58], [65]. *Where* D§5.3 L121, L151. QMA v2 makes this absolute: "No API spending for Claude or Codex, ever" (R20 §4).
- **NFR-A02 Configurable means UI-editable.** Every knob (models, budgets, providers, schedules, bucket, approvals) is editable in Settings. *Src* [65], [66]. *Where* D§2 L33.
- **NFR-A03 Adopt before build.** If a library or SDK does it, use it; QMX writes rules and glue. *Src* [21], [23], [115], [149]. *Where* D§2 L25, RM L16.
- **NFR-A04 YAGNI and modular.** Build the 95% case; one job per module with a small interface; no abstraction without two callers; files about 400 lines or less. *Src* [17], [21]. *Where* D§2 L26-27, RM L16, P14 L25.
- **NFR-A05 No ceremony.** No decision IDs in code, no evidence folders, the PR is the report. *Src* [22], [23]. *Where* D§2 L34, RM L11-15.
- **NFR-A06 Docs first.** Never guess a library API: fetch the official docs and follow them, and give coding agents the links. *Src* [65]. *Where* RM L19, `REFERENCES.md`.
- **NFR-A07 Secrets.** Credentials live only in Windows Credential Manager `qmx/*` (a node vault on servers), and never in the repo, chat, `.env` or backups. *Src* [57], [80]. *Where* RM L18, D§7.6b L331.
- **NFR-A08 Honest tests.** Automated tests use fake models. Live calls are operator-run scripts only. Thresholds are never lowered, and nothing fakes a success. *Src* [3], [20], [64], [78]. *Where* RM L10, L18, P11 L24.
- **NFR-A09 Money path is absolute.** No setting, mode, skill or hook may give an agent order capability. *Src* [36], [50]. *Where* D§12 L477.
- **NFR-A10 Crash-resumable.** Every long run checkpoints and keeps an append-only log, so a crash loses nothing and can resume on another machine. *Src* [58], [148]. *Where* D§11b L431-432, C§6 L105.
- **NFR-A11 Automatic recording.** Logs, metrics, traces and artifacts are recorded by the host, never by agent goodwill. *Src* [58], [65]. *Where* D§11b L449, D§7.7.
- **NFR-A12 Cache-preserving.** No mid-thread swaps of tools, model or system prompt, no in-place history rewrites, and a thread stays on one account. *Src* [155], [161], [169], [171]. *Where* `harness-practices.md`, `hermes-and-harness-comparison.md`.
- **NFR-A13 Lean context.** System prompt about 1.5-3k tokens; about 10-15 visible tools; a small visible skill list (about 30 for Opus, 10 per Sol worker, a heuristic). *Src* [155], [164].
- **NFR-A14 Backups.** Never keep the only backup on the machine it protects; restore-test every backup. *Src* [66], [67]. *Where* D§11b L463, D§7.6 L307.
- **NFR-A15 Files, single writer.** No database server; one writer per file. *Src* [25]. *Where* D§7.6b L314, D§10 L389.
- **NFR-A16 Reproducibility.** Definitions, run manifests and result-memo keys are content-hashed. *Src* [58], [147]. *Where* D§7.1 L244, P22 L19.
- **NFR-A17 Live chat.** Long work never blocks the chat; the UI gets pushes over SSE. *Src* [31], [76]. *Where* D§5.2 L108, D§7.6b L339.
- **NFR-A18 Portability.** Any model provider, any compute provider, any bucket, swappable without code changes. *Src* [58], [65], [67]. *Where* D§5.3 L152, D§11b L461.
- **NFR-A19 Windows laptop, Linux servers.** The laptop path must work on Windows (Job Objects, Python 3.14). Linux-only tools (Litestream, Firecracker) are server-only. *Src* [25], [104]. *Where* D§7.5 L297, D§7.6 L308, RM L17.
- **NFR-A20 Unattended means no questions.** Overnight runs pick the option most consistent with the design, record the assumption, and skip anything needing keys. *Src* [83], [87], [89], [94].
- **NFR-A21 Plain words.** Everything the operator reads is plain and short; he is non-technical and often too tired to scroll [47], [89]. Long prompts that need mid-session edits are unusable [89].
- **NFR-A22 Machine limits.** Heavy runs are serialized (a CI lock, at most 2 pytest workers), and bulk data and temp files stay off the nearly full C: drive. *Src* [49], [50], [96], [108], [113].
- **NFR-A23 Surgical deletion.** Remove code only after a caller audit and within an explicit blast radius; never touch the quant core (QMF, QML, QMB, QMN, MIS). *Src* [131]. *Where* P16 L9-11, D§12c.
- **NFR-A24 Trustworthy answers.** Quoted numbers must trace to tool output; claims of "done" need a verification artifact. *Src* [161], [164]. *Where* C§5 L91.
- **NFR-A25 Main holds no code.** Work lands on branches through PRs; the operator alone moves `main`. *Src* [21]. *Where* D§2 L35, RM L8. (R20 L28-31 refines this to integration/staging/main.)

---

## 6. His mental models from that session

- **The Docker model for mini apps.** It was Claude's framing [22], and he took it up at once [23] ("Thank you... You are seeing it"). Later he checked it was a mental model, not literal Docker [104]: real Docker only on servers [105]. Image = definition, container = instance, volume = the app's own data.
- **Extensions, but not only.** Mini apps are "ideally extensions" like VS Code [14]. Then "not meant to be just like VS Code style extensions... there are so many ways we can think of them" [39]. The analogy is kept, but it is not the definition (D§11 L393).
- **The Lego vision (everything optional, addable, removable).** The word "Lego" is not used by him in this transcript. The idea is present as "modular by design" [17], [21], "has agents / no agents / headless" as combinations [21], and "a plug-in... is a combination of the three" (skills, hooks, tools) [149]. The comparison study named the Cordis harness as "the closest match to the Lego vision" [171].
- **The organogram.** The word is not used in this transcript. The idea is in [149]:
  - one agentic system each for the Lab, Portfolio/Pod, the general copilot and mini apps;
  - "a co-pilot in portfolio is different from a co-pilot in the lab, because these are all different skills";
  - the general copilot may be "just a window or a UI for other sessions".

  QMA v2 turned this into plugins (R20 L47-50).
- **Errand and desk.** These are UI terms, reported from the UI branch [28]: the copilot "desk" is "errands" with a "What it did" receipt and a drawer for activity, diff, terminal and browser. He did not use either word himself here. "Desk packs" in old code are a different, retired thing (R24 L250, L350).
- **Modes rejected.** "A mode can be replaced 90% over time by a skill... Why would we have an Ask mode?... I want a skill to help me plan. I don't want a planning mode" [149]. He allows modes maybe inside a workflow ("it's meant for a specific purpose"), never for the copilot.
- **Copilot = Claude Code / Codex.** He wants the feeling of invoking a skill and "we get working instead of... being stuck in a mud" [149]. He uses T3 Code and wants the same subscription integration [58].
- **"Same API as the UI."** Anything the UI can click, the copilot can do [22]. His response: "Bloody hell. Yo, the way you are thinking through this is nice" [23].
- **"Think of it like Git."** Remote agents "push" results; QMX "fetches" them when back [58].
- **Patterns, not inventions.** "We are not trying to design something very new... Most of it is just patterns" [21]. "These things are not new... we don't have to reinvent our wheel. I'm tired of this stuff" [149].
- **Design for the 95th percentile** of complexity [21].
- **Lab, Pod, Portfolio** as the heart of the product's agent use [21], [70], [149]. "The Lab is a bloody mess, but... most of the lab has already been catered for" [70].
- **Division of labour.** Claude does knowledge, design and review; GPT/Codex does the heavy lifting through work packets, "so that even when I lose access to you... I can still have a lot of work going" [21], [23].
- **Seeds, not specs.** "I'm mostly brain dumping... that doesn't mean you should handle everything on your own" [21]. "This is a seed... you can literally enhance it" [142]. "I'm just seeding for now. You can take it from here" [149]. But: "let's talk about it... I want to know what's in there" before plans [152].
- **Remembering vs improving** (from his paper source): storing past sessions is not the same as getting better [157], [161].
- **Distrust of over-eager agents.** "GPT models have a tendency of insinuating... take it in their own hands instead of waiting" [87].
- **His harness picks** [167]: Claude Code wins hooks and permissions; Codex wins tooling (because of the models) and computer use; LangChain for compaction; Hermes for memory, "no doubt".

---

## 7. Repetition map (ideas he stated three or more times)

| Idea | Times | Messages |
|---|---|---|
| Don't reinvent: copy existing patterns, docs, cookbooks and harnesses | 6+ | [21], [23], [65], [115]/[117], [149] (twice), [159], [167] |
| The copilot builds, controls and accesses workflows and mini apps | 6 | [9] (M414, M422), [21], [23], [36], [142], [149] |
| Agents and work run on a server with the laptop off | 5 | [6], [9], [58], [65], [67] |
| Storage bucket / S3 backups / not everything on the laptop | 5 | [9], [21], [58], [65], [67] |
| Pluggable memory, Hermes as the model | 5 | [6], [9], [21], [23] (LangMem), [167] |
| Sub-agents are important (copilot level, workflows, configurable) | 4 | [6], [23], [58], [65] |
| Subscriptions, not API, via a proxy (CLIProxy, T3 Code style) | 4 | [6], [21], [58], [65] |
| Skills and hooks instead of hard-coded behaviour | 4 | [36], [115]/[117], [142], [149] |
| Backend first; UI later, done by Claude | 4 | [6], [41], [70], [100] |
| Deep Agents by default in workflows (and it "needs more thought") | 4 | [3], [6], [9], [21] |
| Per-app own database | 3 | [6], [14], [21] (plus the database layer [67]) |
| Sandbox / Docker mental model for mini apps | 3 | [17], [21], [104] |
| Mini-app categories: with agents, without agents, headless | 3 | [9] (M432), [21], [39] |
| Caching (where, and for agents) | 3 | [21], [67], [149] |
| Tools for agents are a big gap / very important | 3 | [21], [67], [149] |
| Lab, Portfolio and Pod must shape the agent design | 3 | [21], [70], [149] |
| Models are configurable, not set in stone | 3 | [56], [58], [65] |
| Logging, monitoring, tracing and observability kept automatically | 3 | [21], [58], [65] |
| YAGNI, decouple, modular | 3 | [17] (twice), [21] |

---

## 8. Decisions that still bind, and decisions superseded by QMA v2

### 8.1 Still binding

| Decision | Source | Note |
|---|---|---|
| Agents never hold order tools; only `propose_order`; the operator signs | [36], [38], [50]; D§5.7 L215, D§12 L477 | Unchanged in QMA v2 (R20 L218 "execution stays behind the money-path barrier") |
| No modes for the copilot; skills plus always-on hooks | [149], [150]; C L3, P24 L1 | Applies across both engines |
| The copilot reaches everything through the same API as the UI (one service, REST and MCP doors) | [22], [23]; D§8 | Engine-neutral; `qmx-control` stays |
| One mini-app shape (definition, instance, own data) with optional parts; every app an MCP server; app-to-app by artifact reference | [22], [39], [40]; D§7.1, §7.3 | R20 L26: the runtime is "solid enough for now" |
| Per-app own database; files only; one writer; no database server | [21], [25]; D§7.6, D§10 L389 | |
| Road to live with risk classes | [28]; D§7.2, P14 | |
| Models never hard-coded; override chain; the model used is recorded | [65], [66]; D§5.3 L146-150 | The router changes, the chain stays |
| Pluggable memory with scopes, primary-only writes, global approval | [21], [25]; D§5.4 | The default provider changes (§8.2) |
| Configurable = UI-editable | [65]; D§2 L33 | Standing operator rule |
| Docs first, no guessing; no ceremony; small packets with tests | [21], [65]; RM L11-19 | |
| Recording is automatic; remote results Git-style; resume elsewhere | [58], [65]; D§11b | Target hosts change (§8.2) |
| Three backup copies, never the only copy on the protected machine | [66], [67]; D§11b L453-463 | The primary bucket location is open now that there is no owned server |
| Secrets only in Credential Manager `qmx/*` | [57]; RM L18 | |
| Backend proven without the UI; the UI is wired by Claude | [6], [41], [100]; RM L20 | |
| Surgical deletion within the blast radius; the quant core untouched | [131]; P16 L9-11, D§12c | |
| Skills written with intent, with the operator, not in bulk | [36], [38]; D§11 L394 | |
| Approval = operator ask plus one backend check (no multi-stage pipeline) | [50]; D§12 L478 | |
| Experiment Ledger kept; invalid evidence goes to quarantine verbatim | [50], [141]; D§12 L474, D§12c L508-511 | |

### 8.2 Superseded by QMA v2 (R20 wins)

| Old decision (this session) | Source | Replaced by |
|---|---|---|
| Agent layer on LangChain + LangGraph + Deep Agents | [6], [9], [22]; D§1 L11 | Claude Agent SDK + OpenAI Agents SDK behind one QMX `Engine` (R20 L37-38, §3 item 1) |
| LangGraph is the one workflow engine | [22]; D§1 L20, D§7.4 | QMX's own graph and loop runner (R20 L63-66) |
| CLIProxy is the primary daily provider (Claude via `ChatAnthropic` to the proxy) | [58], [64]; D§5.3 L121-137 | A router that balances across providers and replaces CLIProxy (R20 L58-61). Claude only through the Agent SDK on the plan (R20 §4; L00 "REVERSED") |
| OpenRouter API test profile; Max-plan API credits idea | [57], [64]; D§5.3 L151 | No API spending for Claude or Codex ever; other providers by API key (R20 §4) |
| Own VPS (Contabo) is the default remote target; `qmx node bootstrap` | [65]-[69]; D§11b L438-451 | No owned server; rented, on-demand compute from several providers (R20 §4) |
| Amp orbs and runners for delegated agents | [58], [64]; D§11b L422-427 | No Amp orbs (not paid for) (R20 L80) |
| T3 remote sandboxes; agent code starts in T2/T3 | [25]; D§7.5 L299-301 | Sandboxes not needed by default (R20 L74-75) |
| Default memory = LangGraph `SqliteStore` | [25]; D§5.4 L158 | SDK default memory, QMX pluggable layer on top (R20 L41-42) |
| Deep Agents summariser for compaction | D§5.5 | Configurable summariser with a chosen model (R20 L68-69) |
| LangSmith or OTel-file tracing | D§5.8 L220 | SDK tracing stored locally, never sent to OpenAI (R20 L71-72) |
| Library as a P22 deliverable inside the rebuild | [69]; P22 | Library out of QMA v2 scope; name the seam only (R20 L15-16) |
| "Build beside the old, then delete" (strangler) | D§3 L57 | The branching mechanism replaces it (R20 L31) |
| The 5-mode copilot (COPILOT §2) | [148] | Already rejected in-session [149]; QMA v2 adds plugins per surface (R20 L47-50) |
| "Deep Agents is the harness, QMX owns three thin pieces" | [22] | QMX owns more: graph runner, router, plugin loader for OpenAI, cross-engine delegate (R20 §3) |

---

## 9. Questions left open in that session

**Asked by Claude and never answered**
1. CLIProxy "cloak": keep it on (looks like Claude Code, but our prompt gets moved) or off (prompt intact)? [155] This is moot if Claude no longer goes through CLIProxy (R20 §4).
2. Which actions always need approval? Proposed: publish, install, schedule, spend over budget, paper-account actions, deleting [155].
3. An effort dial next to the chat box (quick / normal / deep), or does the copilot decide? [155]
4. The one rule that must always be in the copilot's prompt [155].
5. Close PRs 20-24: answered, done [53]-[55]. GitHub Actions never ran any check: never resolved [24], [77], [135].

**Raised by the operator and not settled**
6. Per-surface agent systems (Lab, Portfolio/Pod, mini apps, general copilot): which skills, hooks, tools, attachments and outputs each has [149]. The per-screen study was held until after the discussion [153] and never ran.
7. Is the general copilot one window over every surface's sessions, or a separate agent? [149], [151]
8. Attachments: how they are handled [149].
9. RLM: is it needed, when, and is it copilot or workflow only? [149] Research says off by default, workflows only [155]; never confirmed.
10. How solid the node editor is against what P10 built [149], [151].
11. System prompts and meta-prompting: approach and owner [149].
12. Computer use and browser use: none designed [167]; research proposes cua-driver and browser-use [171].
13. Compaction on Opus 5.5: the shipped design summarises in place, which the research says breaks on Opus 5.5 [169], [171].
14. Whether the proxy passes thinking blocks, cache keys and beta headers through [169], [171]. Moot for Claude under R20, but it still applies to GPT if a proxy is used.
15. The copilot skills (5 or 13): never written. P15 shipped placeholders [137], P24 is on hold [151].
16. The plain-words discussion of the five studies that he asked for [152], [167]: never held. The session ended at [174].

**Carried from earlier sources and still open in this session**
17. Mini-app open questions from [14]: whether the node editor is the only way to build an app; mini app vs extension; whether a published app may run on its own with live-trading authority.
18. Tracing tool: Langfuse or LangSmith [6]. Superseded by R20 L71-72.
19. How a hand-written experiment registers (ExperimentSpec) [9].
20. MCP Apps rendering in the Svelte UI (official AppBridge) [24]; D§13 L534.
21. Whether `sqlite-vec` loads on Windows, before semantic memory search [25]; D§13 L533.
22. When GPUs are truly needed, and where models come from (Hugging Face, own training) [70]. Answered in outline [71]; no provider chosen.
23. Live verification never done:
    - an OpenRouter or CLIProxy smoke [83];
    - a real sandbox [137];
    - live Firecrawl and the GitHub backup [113];
    - a Docker acceptance run [123];
    - a real server bootstrap [113];
    - broker demo reads [113].
24. The P16b outcome is not reported in this transcript [174]. It ran later (PRs #49-#57), followed by P16c (#58-#67) after this session.

**Gaps in the export**
- The operator's message that [163] answers (asking for cookbooks over vendor advice pages, with nine LangChain posts) is not in the export.
- [92] is an image that is not reproduced.
