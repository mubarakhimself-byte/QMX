# 26: Requirements from today (2026-10-12)

What the operator actually asked QMA v2 to do, pulled from the whole day's dictation. This is not a design. Planning only.

**Sources**
- The full export of today's session: 163 numbered messages, with a compaction at [107]. USER is the operator.
- Checked against `00-session-ledger-2026-10-12.md` (first ~131 messages, **different numbering**) and `20-qma-v2-direction.md` (its §4 corrections override §1-3).

**How to read the references**
- `[n]` is a message in the full export, not the ledger. As a rough guide, ledger `[n]` is about full `[n+2]` after message 13. For example, ledger [87] = full [89], ledger [116] = full [118], ledger [124q] = full [128], ledger [131] = full [135].
- `[q74a]` is a message he queued at 09:27 between [74] and [75]. It is missing from the export; its content comes from the ledger and the compaction summary [107]. It said the router should be "capable, not cheap" and complained about eleven nested sub-agents eating half his usage.
- `[n-research]` is a fact from a researcher report delivered in message n, not something he said. `[20§x]` is a section of the direction note. `[memory]` is one of his standing rules from the memory files.
- "Latest wins": where he changed his mind, the chain is shown with arrows.

**Format**
- The FR/NFR shape is borrowed from the BMAD `bmad-prd` template (`.claude/skills/bmad-prd/assets/prd-template.md`): global IDs, plain "QMX shall" statements and an out-of-scope list.
- Priorities:
  - **WED:** needed for the Wednesday minimum [150][157]. The copilot works. He can create, run, maintain and edit mini apps and workflows, agentic and not. The organogram works. Sub-agents work. Workflows can run off his machine.
  - **NEXT:** right after Wednesday.
  - **LATER:** parked.

---

## 1. Journey: the phases of the day

| # | Time (UTC) | Msgs | What happened | What changed, and why |
|---|---|---|---|---|
| 1 | 08:13-08:31 | [1]-[12] | Resumed the old product-audit session. P16b was found merged but small (~6.7k real lines removed). Claude recommended Pocock plus pstack's principles. Claude fired four questions before he had read the answer; he dismissed them [9]. | He set the cost rules for sub-agents [1] and the "stop vibe coding" demand [4]. The first lesson: never ask before he has read. |
| 2 | 08:37-08:56 | [13]-[18] | Two 14-minute dictations: two agent types, the copilot organogram, trading anything (cTrader, MT5, CCXT), models, memory, agent-as-a-folder, graph/loop engineering, the research harness. P16c prompt written. Six fresh researchers started. | The organogram, pluggable memory, model choice and "the Lab is 80%" enter as seeds. He wanted fresh research, not old summaries [17]. |
| 3 | 09:00-09:36 | [19]-[85] | Research reports came in. Rules set: acknowledge only [50], research lives in the repo [50], caching is the top priority [50]. Claude subscription terms read. He asked about the Agent SDK [70][74] and proposed a router over several subscriptions [74]. Theo's video re-read. Nested sub-agents stopped [78]. | **CLIProxy for Claude reversed**, because of the terms [51][73][80]. The router idea was born [74]. "Capable, not cheap" [q74a]. |
| 4 | 09:42-10:10 | [86]-[93] | Sandcastle. "Engine starting another engine" [86]. A free, model-agnostic harness [86]. Tools mostly local, not MCP; the Library is a database; hooks decide where things are written; a T3-style usage page; Hermes cron; Firecrawl Alexandria [89]. Wayfinder map with 14 tickets. | Claude Code became "a node", not the copilot. Agents get the Claude Code baseline [89]. |
| 5 | 10:15-10:45 | [94]-[106] | Planning only [94]. pstack installed and the skill order fixed [99][101]. Same session, compacted [103]. Decisions through the question tool; shipping in an external session while planning continues [105]. | "Design for complexity" and "look at what I wouldn't consider" became standing rules [105]. |
| 6 | 10:46-14:10 | [107]-[110] | Compaction and a break. P16c ran in a separate Claude session. | The compaction summary carries [q74a]. |
| 7 | 14:10-14:47 | [111]-[122] | `/how` on the runtime: no turn host, workflows return 501, sub-agent model forced, QMB spawns the old daemon. B vs C. He argued for C (switching models when Claude runs low), then settled on B [118]. No Docker; 40 agents; QMB intent; how the copilot builds mini apps; cross-surface reach [118]. He demanded the morning research be used [121]. | **Docker reversed** [118]. Naming: "choose one" [118]. Tickets 17 and 18 were born. |
| 8 | 15:01-15:28 | [123]-[136] | Kimi-in-Claude-Code docs; a Contabo server; mid-conversation model switching with a cost pop-up [123]. **Design for two vendor SDK formats** [125]. Question round: two lanes, API-key compatibility, server designed now and shipped later, logs, buckets, git variants [128]. Architect launched, then killed [135]. He demanded a transcript ledger, an honest opinion, the `/how` redo and structure. | **Claude Code with per-provider profiles reversed** ("a thought", RAM) [125]. A Claude Code session per workflow step was rejected [125]. |
| 9 | 15:38-16:27 | [137]-[156] | Ledger written. Router = a load balancer by API compatibility; a long-lived Claude orchestrator that picks models [141]. The two-SDK study. **QMA v2 rebuild proposal** [147]. The big correction message [150]: plugins as the organogram unit, own graph instead of LangGraph, SDK memory by default, branching, no sandboxes, no Claude Code CLI, XML meta prompts, the Wednesday minimum. Direction note 20 written. | **LangGraph reversed** to QMX's own graph [150]. Short sessions per decision rejected [141]. |
| 10 | 16:40-17:20 | [157]-[163] | The mini-apps transcript zip and clippings ("not every workflow needs AI", harness vs loop vs graph). Final brief: design for complexity, use skills, Fable allowed [157]. Answers [159]: **never pay API for Claude or Codex**, **no owned compute**, vocabulary left to Claude, frustration at repetition. [162]: build the FR/NFR list from the transcripts first. | **Max API credits reversed** [159]. **Contabo reversed** to rented, on-demand compute [159]. Architect stopped until this file exists [163]. |

---

## 2. Seeds: every brain-dump idea

Status words:
- **CURRENT:** stands.
- **REVERSED → x:** replaced by x.
- **PARKED:** wanted later.
- **OUT OF SCOPE:** named seam only.

| # | Idea, in plain words | Msgs | Status | What it implies for the design |
|---|---|---|---|---|
| S01 | Stop vibe coding: a structured, traceable way to plan and ship | [4][15][94][101][135][143] | CURRENT | A fixed skill order; every PR is checked independently against its plan |
| S02 | Re-check old designs (mini apps, backend) for over- and under-engineering | [4][162] | CURRENT | QMA v2 restates requirements before architecture |
| S03 | Two agent types: interactive copilots and background workflow agents | [15] | CURRENT, extended | Copilots, graph/workflow agents, sub-agents and a long-lived orchestrator are all distinct roles |
| S04 | A copilot organogram: a general copilot (Codex/Claude-Code-like) plus Lab (research, coding, workflows) and Portfolio (risk, sizing, optimisation); any copilot can host any conversation | [15][17][105][135][141][162] | CURRENT, "up for discussion / enhance" | Per-surface scoping of tools, skills, hooks, memory and model |
| S05 | Tools, hooks, permissions and memory are split along the organogram | [15] | CURRENT, realised via plugins (S64) | A plugin per surface carries the split |
| S06 | Trade anything: CFDs via his local MT5 and cTrader, crypto via CCXT; cTrader also has news | [15][17] | CURRENT (context) | Agent tools reach these platforms; orders stay behind the money path |
| S07 | A right-hand panel with a terminal, like Claude and Codex desktop | [15] | CURRENT | The event stream must feed the drawer: terminal, browser, diff, activity |
| S08 | Use the Claude subscription through CLIProxy | [15][50] | REVERSED → Claude only through the Claude Agent SDK signed in with his plan; the router replaces CLIProxy | No subscription tokens handled by QMX code [51][73][150][159] |
| S09 | Cheap models for background and server work | [15] | REVERSED → "capable, not cheap" [q74a]; per-workflow provider defaults [150] | The router ranks by capability and remaining usage, not price alone |
| S10 | Opus 5.5 is the daily driver | [15] | CURRENT | The default copilot model is configurable |
| S11 | Sessions can message each other (UI session to planning session) | [15] | PARKED (process) | Not an agent-system requirement |
| S12 | A default research harness/workflow in the Lab; the August one may have been overkill | [15][17][89][162] | CURRENT as a template; depth PARKED | Ship research as a template graph, not a bespoke runtime |
| S13 | Skills are fine; how they are shaped is the problem | [15] | CURRENT | Skills are gated by evals and kept few |
| S14 | Graph engineering and loop engineering | [15][145][147][157][159] | CURRENT, core | The workflow engine is a graph of loops (see §5) |
| S15 | An agent is a folder (Eve, LLM wiki, OKF) | [15][17][50] | CURRENT, partly absorbed by plugins | Agents and plugins are file-defined and editable in the UI |
| S16 | Pluggable memory like Hermes; test several; different agents may use different memory | [15][50][150] | CURRENT; SDK default memory underneath [150] | A memory interface with per-agent binding |
| S17 | LangChain, LangGraph and Deep Agents as the stack | [15][50][74][89] | REVERSED → Claude Agent SDK + OpenAI Agents SDK [125][135][150]; own graph [150]; "port what we meant to ship on LangChain onto the SDKs" [162] | Treat the LangChain-era features as the requirement list |
| S18 | LangSmith Gateway and Engine | [17][74] | OUT OF SCOPE ("not going to use it" [89]) | Local tracing only |
| S19 | Watch a video (or have a sub-agent watch it), then try the idea in cTrader via computer use | [17][89] | CURRENT | Video, computer use and a demo account in one flow |
| S20 | Which model goes where: defaults, a picker, everything sensible in the UI | [17] | CURRENT | Per-role defaults, editable |
| S21 | The Lab is ~80% of the platform: parallel long-running "sessions" (errands) | [17] | CURRENT | Errands are first-class and long-lived |
| S22 | WF1 and WF2 brought back with better integrity | [17][50][89][162] | OUT OF SCOPE (backlog); note as seeds in the architecture [162] | The graph engine must be able to express them later |
| S23 | Read docs and cookbooks "like a human" in a browser | [17][150][157] | CURRENT (process) | Research method, not product |
| S24 | Server agents export their transcript and logs automatically (what, how, why) | [50] | CURRENT | Run records always exported |
| S25 | Deep Agents for workflows; each sub-agent's model and scope must be specific | [50] | Engine REVERSED (S17); specific model and scope CURRENT | Sub-agent spec has model, scope and tools |
| S26 | Wire Claude Code into QMX, or run Claude Code via Docker | [50] | REVERSED → SDK capabilities, no CLI [150]; no Docker [118] | — |
| S27 | Build our own proxy/router instead of CLIProxy | [70][74] | CURRENT as a router; not as a Claude proxy | See FR-T router |
| S28 | Workflows on an OpenCode Go/Zen subscription | [70] | CURRENT as a "pool" provider [128] | Pools are their own provider shape |
| S29 | Several subscriptions in one QMX (2 Claude, 1 GPT, Kimi) | [74][86][125] | CURRENT, with a terms caveat | Accounts are rows; rotation per session |
| S30 | Research sub-agents on Kimi | [74] | REVERSED → don't hard-code roles [86] | Defaults, not fixed roles |
| S31 | Subscriptions and API keys split cleanly; Claude routes its own way via the SDK | [86][101] | CURRENT | Two lanes |
| S32 | A free, model-agnostic harness ("if Fable comes out tomorrow…") | [86] | CURRENT | Adding a model is data, not code |
| S33 | Claude Code's harness as a node inside LangGraph (Sandcastle) | [86][89] | REVERSED → two SDK engines plus QMX's own graph [150] | — |
| S34 | QMX's own browser and computer use (OpenCUA), not Claude Code's | [15][86][89] | CURRENT | QMX-owned tools usable by both engines |
| S35 | The chat should feel like this Claude Code session: sessions, running sub-agents, tool calls, the computer-use cursor | [89] | CURRENT | One rich event stream |
| S36 | Tools mostly local QMX code, not MCP; MCP is fine for browser and computer use | [89] | CURRENT, softened by "the SDKs ship most tools" [145] | Native tools first; MCP where it fits |
| S37 | The Library is just a database; storage buckets | [89][118][141][150] | OUT OF SCOPE (seam); buckets CURRENT [128] | Name the seam in code and docs |
| S38 | Every agent's baseline equals Claude Code's out-of-the-box abilities (videos, CLI, Python, web) | [89] | CURRENT | A baseline tool set for all agents |
| S39 | Hooks tell the agent where to put things (e.g. strategies) and confirm writes landed | [89][118] | CURRENT | A placement and verification hook contract |
| S40 | A usage page like T3 Code's (limits, tokens, who is used, graph) | [89][90] | CURRENT | Usage ledger plus limit snapshots |
| S41 | Cron jobs like Hermes | [89][141][157] | CURRENT | A QMX scheduler |
| S42 | Automatic compaction, Anthropic-style | [89][105] | CURRENT; on the OpenAI side a configurable summariser model [150] | Per-engine compaction policy |
| S43 | Self-improvement (Hermes is the lead reference): don't repeat Wednesday's mistake; save "ways of doing things" | [89][118][141][150] | CURRENT, method left to Claude | Lessons are written back with approval |
| S44 | Use cTrader and MT5 inside QMX, all-in-one; agents click through by default | [89] | CURRENT | Desktop-app control inside QMX |
| S45 | Firecrawl and Alexandria for web and documentation work | [89] | CURRENT (NEXT) | A web/doc tool provider |
| S46 | Design for complexity: build for load before it arrives; show me what I'd miss | [89][105][118][157][159][162] | CURRENT | Requirements beyond the minimum |
| S47 | pstack for depth; automate-me to build QMX skills and workflows | [99][101] | CURRENT (process; automate-me LATER) | — |
| S48 | Ship the UI as a browser app first, so agents can click it | [103] | CURRENT (separate UI session) | The backend serves both browser and desktop |
| S49 | An external session ships while planning continues | [105] | CURRENT (process) | — |
| S50 | Find out what still works after the P16 deletions (QMA, mini apps, QML, QMF, QMN) | [118] | CURRENT (backlog) | Smoke checks plus logs |
| S51 | The backend, database and API must work without the UI | [118] | CURRENT | API-first, headless-testable |
| S52 | Workflows: deterministic, agentic or mixed; typed inputs and outputs; feed each other and mini apps | [118][159] | CURRENT | A typed graph runtime |
| S53 | Simplest: no Claude in workflows | [118] | REVERSED → Claude often orchestrates long workflows [123][141] | — |
| S54 | Option C: per-agent model choice so he can leave Claude when usage runs low | [118] | CURRENT, absorbed into two lanes | Engine and model are chosen per agent and per errand |
| S55 | No Docker; a light own sandbox | [118] | → no sandboxes needed at all [150] | Isolation by folders, hooks and limits |
| S56 | 40 agents at once on his PC (95th percentile) | [118] | CURRENT | Performance budget |
| S57 | QMB as a tamper-proof backtest CLI agents call like a tool (Lean CLI + Jesse) | [118][150] | OUT OF SCOPE (refactor later) | A tool seam to QMB |
| S58 | Agents must know QML, QMB and the Library exist; reach Portfolio from the Lab and both from the main chat | [118] | CURRENT | A capability registry and cross-surface access |
| S59 | The copilot builds, maintains, opens and edits mini apps, workflows, widgets and plugins | [118][150] | CURRENT, core | Build tools for each artefact type |
| S60 | Run all sessions on his Contabo server ("our own Sandcastle") | [123][128] | REVERSED → rented, on-demand compute from several providers; no owned box [159] | A provider-neutral remote runner |
| S61 | Claude Code with one profile per provider (Kimi or GLM inside Claude Code) | [123] | REVERSED → "a thought"; 1 GB per session is "stupid" [125] | — |
| S62 | Switch model mid-conversation, with a cost pop-up; the cache belongs to the old provider | [123] | CURRENT | Switching path; Claude withdrew its "never" [124] |
| S63 | QMX's Claude settings, skills, plugins and memory kept apart from his personal Claude Code | [123] | CURRENT | An isolated QMX config home |
| S64 | Plugins per surface (Lab, Portfolio); a plugin = tools/MCP + skills + model + hooks; a session loads a plugin by default | [123][125][150] | CURRENT, core | The plugin is the organogram's unit |
| S65 | QMX enforces limits itself: refuse a new session and show an error card | [123] | CURRENT | Hard caps |
| S66 | Many providers (Kimi, MiMo, MiniMax, GLM, DeepSeek, Ollama Cloud, OpenCode, OpenRouter) | [123][128] | CURRENT | Providers are rows |
| S67 | Design for two SDK formats only, Anthropic and OpenAI; everything else is "API compatibility" | [125][128][141] | CURRENT | Base URL plus key |
| S68 | Dynamic workflows, but specified and saved | [125][150] | CURRENT | A copilot-written workflow becomes a saved graph |
| S69 | Amp orbs, Railway, Modal and E2B as off-machine options | [125][141][150] | CURRENT as references or providers; Amp orbs not paid for [150] | — |
| S70 | Agents run smoother on Linux; Windows has the aesthetics | [125] | OPEN | Portability NFR |
| S71 | Refactor the database to be usable by agents; the server may be mostly a database | [125] | CURRENT (NEXT) | — |
| S72 | Agents editing the same files: git branches and variants, with both versions kept for comparison | [128] | CURRENT | Variant model, rendered in the UI |
| S73 | Buckets for storage and remote runs | [128] | CURRENT | Storage seam |
| S74 | Voice/conversational mode; System-1 models; GPT audio and image | [128][150] | PARKED | — |
| S75 | No Grok; Gemini maybe for a Library agent | [128] | CURRENT / PARKED | — |
| S76 | The router balances sessions and usage, never single requests, across compatible endpoints; it replaces CLIProxy | [141][150] | CURRENT | Session-level routing |
| S77 | Long sessions persist; never a fresh session per decision; context engineering is paramount | [141] | CURRENT | Resumable sessions plus a state file |
| S78 | A Claude (e.g. Opus 5.5) orchestrator that knows which models are available and what usage is left, and delegates | [141] | CURRENT | Router data exposed as orchestrator tools |
| S79 | Rebuild what one SDK has on the other (approvals, hooks); think of it like OOP | [141][150] | CURRENT | One QMX contract, two implementations |
| S80 | A cross-engine plugin: an OpenAI-engine agent can use a Claude agent, and the reverse | [150] | CURRENT (proposal) | Delegate tool across lanes |
| S81 | **QMA v2:** rebuild the agentic system cleanly; QMA = "Quant agents" | [147][150] | CURRENT | Fresh core; old QMA retired |
| S82 | Archive old documents (they over-complicate things for agents), don't delete them | [147][150] | CURRENT | Superseded stamps |
| S83 | Branching: integration → staging → main; the other branches and worktrees are junk | [150][157] | CURRENT | Shipping targets |
| S84 | System prompts as meta prompts, possibly XML; prompt and context engineering are big topics | [150][157] | CURRENT, undesigned | Prompt architecture |
| S85 | Build QMX's own graph instead of LangGraph; workflows started from n8n | [150] | CURRENT | Own runner |
| S86 | Use each SDK's default memory, keep the pluggable layer | [150] | CURRENT | — |
| S87 | Use the SDKs' tracing, stored locally, never sent to OpenAI | [150] | CURRENT | Local exporters |
| S88 | No sandboxes by default (Sandcastle exists if needed) | [150] | CURRENT | — |
| S89 | Amp's supervised services as a "process manager" | [150] | Partly REVERSED → mini apps are not Amp portals [157][159] | At most a viewing/supervision aid |
| S90 | The Wednesday minimum | [150] | CURRENT | Defines WED priority |
| S91 | "Not every agent workflow needs AI": stop wasting tokens on deterministic steps | [157] | CURRENT | Deterministic nodes by default |
| S92 | Graph engineering might replace "workflows" and "sub-agents" in QMX's vocabulary | [157][159] | OPEN; Claude has liberty [159] | — |
| S93 | Four axes for every run: caching; where it runs; who runs it (provider); how (graph or loop) | [157] | CURRENT | Every run records the four |
| S94 | Never pay API for Claude or Codex; only subscriptions | [159] | CURRENT, firm | Two lanes |
| S95 | Don't own compute; pay-as-you-go minutes, several providers | [159] | CURRENT | — |
| S96 | Port what we meant to ship on LangChain onto the SDKs; QMX "is not so heavy" | [162] | CURRENT | — |
| S97 | Codex as a harness is "slow and heavy", "too compact"; make it lighter; likes its UI | [125][145] | CURRENT | No Codex process per session |
| S98 | No copilot modes | [7][118] | CURRENT | Skills plus always-on hooks; remove plan/do code |
| S99 | QA scenarios generated per page; create-verification-skill with complex user journeys | [89][101] | LATER | — |

---

## 3. Functional requirements

Each row gives the source messages and the priority (WED / NEXT / LATER).

### 3.1 Copilot and organogram

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T01 | run a general copilot that handles daily tasks as broadly as Claude Code or Codex | [15][89] | WED |
| FR-T02 | run specialised copilots: Lab (research, analysis, coding, building workflows) and Portfolio (risk, sizing, optimisation), plus per-mini-app copilots | [15][17][64-research] | WED |
| FR-T03 | let any copilot host any conversation, and let the copilot know which surface it is acting on | [15][118] | WED |
| FR-T04 | let a copilot reach Portfolio things from the Lab, and both from the main chat | [118] | WED |
| FR-T05 | define each organogram seat as a plugin (tools/MCP + skills + model + hooks) that a session loads by default | [123][150] | WED |
| FR-T06 | keep errands (long-running pieces of work) first-class: several run in parallel, resume and connect to everything | [17][21-research][74] | WED |
| FR-T07 | give every copilot no modes: skills and always-on hooks instead; remove the leftover plan/do code | [7][118] | WED |
| FR-T08 | let the operator edit, add and remove organogram seats in the UI (Lego) | [17][150] | NEXT |
| FR-T09 | answer the one rule the copilot must never forget about how he works (asked at [7], never answered) | [7] | NEXT |

### 3.2 Engines

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T10 | run agents on two engines behind one QMX engine contract: the Claude Agent SDK (subscription lane) and the OpenAI Agents SDK (API lane) | [125][128][135][150] | WED |
| FR-T11 | use the Claude Agent SDK for its capabilities (tools, sessions, hooks, sub-agents, permissions, plugins), never the Claude Code CLI | [150] | WED |
| FR-T12 | run Claude only on his Max subscription, signed in by him through the Agent SDK; QMX never reads or relays the login token | [51][73][150][159] | WED |
| FR-T13 | run GPT through his ChatGPT subscription ("Sign in with ChatGPT"); its feasibility must be confirmed | [50][86][159] | WED |
| FR-T14 | run every other provider through the API lane by base URL plus key, in the Anthropic or OpenAI format | [125][128] | WED |
| FR-T15 | implement any capability one SDK lacks (approvals, hooks, plugins, compaction) once, as a QMX contract mapped onto both | [141][150] | WED |
| FR-T16 | keep the engine choice per agent and per errand, so work moves off Claude when Claude usage runs low | [118] | WED |
| FR-T17 | add a new model (e.g. Fable) as data, with no engine code change | [86] | NEXT |
| FR-T18 | never start a Codex process or a Claude Code session per workflow step | [125][145] | WED |
| FR-T19 | provide a turn host that takes a message, runs the agent and streams the reply, with no UI attached | [117][118] | WED |

### 3.3 Plugins

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T20 | load one plugin format on both engines (a QMX loader on the OpenAI side, since that SDK has no plugin system) | [150][20§3] | WED |
| FR-T21 | ship default Lab and Portfolio plugins | [123][150] | WED |
| FR-T22 | keep QMX's plugins, skills, settings and memory in a QMX-only home, isolated from his personal Claude Code | [123] | WED |
| FR-T23 | let the copilot create, edit and install plugins | [118] | NEXT |
| FR-T24 | provide a cross-engine delegate plugin (an OpenAI-engine agent can call a Claude agent, and the reverse) | [150] | NEXT |
| FR-T25 | let him describe a skill roughly and have it authored and evaluated against "no skill" before it is switched on | [7][99] | LATER |

### 3.4 Router and accounts

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T26 | hold accounts as rows: subscriptions (Claude, ChatGPT), API keys (GLM, MiniMax, Kimi, DeepSeek, MiMo…) and pools (OpenRouter, Ollama Cloud, OpenCode); no fixed limit on providers | [74][123][128] | WED |
| FR-T27 | balance usage and resources across accounts and providers per session, never per request | [74][141][150] | WED |
| FR-T28 | know each account's availability, limits, usage and reset times | [125][141] | WED |
| FR-T29 | rank by capability first ("capable, not cheap"), then remaining usage | [q74a][141] | WED |
| FR-T30 | let defaults set a provider per workflow, sub-agent or role; the copilot may configure them | [17][150] | WED |
| FR-T31 | expose "available models, usage left, what each is good at" as tools an orchestrator can call | [141] | NEXT |
| FR-T32 | support several accounts of one vendor (e.g. two Claude plans), keeping a session on one account | [74][86][80-video] | NEXT |
| FR-T33 | set thinking/effort per format and keep it coherent when the model changes | [8][123][125] | NEXT |
| FR-T34 | keep API keys in Windows Credential Manager and hand them to sessions at start, never in settings files | [124][memory] | WED |
| FR-T35 | show a per-role default model and a picker in the UI | [17] | NEXT |

### 3.5 Workflows (graphs and loops)

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T36 | run workflows as QMX's own graphs (nodes, edges, typed state), not LangGraph | [150] | WED |
| FR-T37 | let a workflow be deterministic, agentic or mixed | [118][159] | WED |
| FR-T38 | default to non-AI nodes where AI isn't needed | [157] | WED |
| FR-T39 | pass typed inputs and outputs between workflows, mini apps and widgets | [118] | WED |
| FR-T40 | let the copilot create, run, maintain and edit workflows | [118][150] | WED |
| FR-T41 | treat an agent node as a loop with an evidence-based stop rule and a separate checker | [150][157][20§2.4] | NEXT |
| FR-T42 | let a copilot write a dynamic workflow and save it as a graph the UI can render and re-run | [125][150] | NEXT |
| FR-T43 | checkpoint each node and resume runs that last up to days | [118] | WED |
| FR-T44 | let one persistent Claude orchestrator drive a long workflow and delegate to other models; never a fresh session per decision | [123][141] | NEXT |
| FR-T45 | ship ready-made templates (the six Claude workflow patterns, OpenAI's cookbook patterns, a research template) | [17][150][157][162] | NEXT |
| FR-T46 | expose per-workflow settings for compaction, sub-agents and models | [147][150] | NEXT |
| FR-T47 | be able to express WF1/WF2-style strategy pipelines later (out of scope now) | [50][162] | LATER |

### 3.6 Mini apps

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T48 | let the copilot create, run, maintain and edit mini apps, agentic and not | [118][150] | WED |
| FR-T49 | treat a mini app as QMX's packaged, versioned unit with ML-level complexity, not an Amp portal | [157][159] | WED |
| FR-T50 | let mini apps take inputs from, and give outputs to, workflows and other mini apps | [118] | WED |
| FR-T51 | record which errand built or watches a mini app | [64-research] | NEXT |
| FR-T52 | give mini apps a DevOps lens: health, logs and status | [118] | NEXT |
| FR-T53 | support widgets and MCP apps as surfaces (MCP apps never discussed) | [118][123] | LATER |
| FR-T54 | keep the mini-apps transcript seeds (`21-…`) as design input | [157][162] | NEXT |

### 3.7 Sub-agents

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T55 | run sub-agents with their own model, scope and tools, which the parent does not override | [50][117] | WED |
| FR-T56 | allow a lead on one provider with sub-agents on another (e.g. a GPT research lead, Claude heavy workers) | [101] | WED |
| FR-T57 | follow Claude's sub-agent pattern as the reference design | [150] | WED |
| FR-T58 | make sub-agent defaults configurable in Settings and per workflow | [150] | NEXT |
| FR-T59 | cap sub-agent nesting depth | [117][q74a] | WED |
| FR-T60 | show running sub-agents and child errands in the UI | [89] | WED |

### 3.8 Memory

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T61 | use each SDK's default memory | [150] | WED |
| FR-T62 | keep a pluggable memory layer (Hermes-style) with per-agent binding | [15][150] | NEXT |
| FR-T63 | run a side-by-side test of memory providers (Hindsight, Mem0, a file baseline) before choosing | [15] | LATER |
| FR-T64 | keep records (backtests, orders, limits) out of memory; memory only points at them | [61-research][7] | WED |
| FR-T65 | let the operator see and edit what memory holds | [7] | NEXT |

### 3.9 Context and prompts

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T66 | use QMX's own system prompts (XML-structured meta prompts allowed), not Claude Code's coding prompt | [150][156] | WED |
| FR-T67 | keep the static prompt part stable so caching holds | [50][84-research] | WED |
| FR-T68 | compact automatically: Anthropic's own compaction on Claude, and a summariser with a chosen model on the OpenAI side | [89][150] | WED |
| FR-T69 | keep long sessions alive by saved and resumed sessions plus a progress/state file | [141][156] | NEXT |
| FR-T70 | switch model mid-conversation: warn with a cost pop-up, and compact first if the new window is smaller | [123][124] | NEXT |
| FR-T71 | keep track of compaction events, visible to him | [89] | NEXT |

### 3.10 Approvals, hooks and the money path

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T72 | block orders, sizing and the kill switch from every agent in code, on both engines, overriding all permissions | [7][memory][117] | WED |
| FR-T73 | have hooks decide where things are written (e.g. strategies) and confirm the write landed | [89][118] | WED |
| FR-T74 | define one approval contract across both engines (ask, allow once, allow for session, remember) | [72-research][141] | WED |
| FR-T75 | let agents touch live accounts for testing (the cTrader/MT5 scenario) under approval, never trading live money | [123] | NEXT |
| FR-T76 | let the operator decide the approval list (dismissed question [9]: publish, schedule, paper accounts, delete) | [8][94] | WED |

### 3.11 Placement and off-machine runs

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T77 | run workflows off his machine on rented, on-demand compute from several providers, never one owned box | [150][159] | WED |
| FR-T78 | move a session or workflow from local to remote, uploading what it needs | [125][128] | NEXT |
| FR-T79 | run long-running and cron workflows remotely by design, configurable in the UI | [141] | NEXT |
| FR-T80 | show where every job runs | [memory-lego][157] | WED |
| FR-T81 | use buckets for storage and remote runs | [128] | NEXT |
| FR-T82 | build on P17/P21 (remote runs, providers) and reference Amp, Railway, Modal and E2B | [125][141] | NEXT |
| FR-T83 | keep Windows-only work (cTrader and MT5 control) on his PC | [124] | NEXT |

### 3.12 Cron and triggers

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T84 | provide a QMX scheduler with Hermes-style cron, timed loops and goal loops | [89][157] | NEXT |
| FR-T85 | start workflows on schedules and events, and refuse when limits are hit | [123][141] | NEXT |

### 3.13 Observability and DevOps

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T86 | export every run's transcript and logs (what happened, how, why), local and remote | [50][128] | WED |
| FR-T87 | collect both SDKs' traces into one local log store, never uploaded to OpenAI | [128][150] | WED |
| FR-T88 | give a DevOps lens for agents, workflows and mini apps | [118][128][157] | NEXT |
| FR-T89 | watch for stuck sessions and restart them | [124] | NEXT |
| FR-T90 | run a post-P16 smoke check of QMA, mini apps, QML, QMF and QMN | [118] | NEXT |

### 3.14 UI events

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T91 | emit one event stream from both engines: messages, tool calls, sub-agents, approvals, computer-use cursor | [89][122] | WED |
| FR-T92 | show sessions, previous sessions and what is running, the way this Claude Code session does; hide raw logs by default | [89] | WED |
| FR-T93 | render variants (two versions of the same file) for comparison | [128] | NEXT |
| FR-T94 | consider the UI in every requirement; the UI ships first as a browser app | [17][103] | WED |

### 3.15 Usage page

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T95 | show a T3-Code-style usage page: limits, tokens, accounts in use, a graph, cache savings | [89][90] | NEXT |
| FR-T96 | keep its own usage count, filling gaps from local session files, and enforce limits with an error card | [96-research][123][124] | WED |
| FR-T97 | read only documented sources, never private OAuth endpoints | [96-research] | WED |

### 3.16 Computer and browser use

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T98 | give agents QMX-owned browser use, including logged-in sessions (e.g. TradingView) | [86][89] | NEXT |
| FR-T99 | give agents QMX-owned computer use (OpenCUA/cua-driver class) that works without stealing his mouse | [15][72-research] | NEXT |
| FR-T100 | let agents operate cTrader and MT5 inside QMX (all-in-one), demo first | [17][89] | LATER |
| FR-T101 | support "watch a video, then try it in cTrader" as one flow | [17][89] | LATER |

### 3.17 Concurrency and variants

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T102 | let agents editing the same files work on git branches, keeping both versions for comparison | [128] | NEXT |
| FR-T103 | cap concurrent heavy sessions (each Claude Agent SDK session starts a process of ~1 GB) | [123][156] | WED |
| FR-T104 | prevent two agents editing the same Library item at once (seam only) | [118] | LATER |

### 3.18 Self-improvement

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T105 | save "ways of doing things" and mistakes, so an agent doesn't repeat them | [89] | NEXT |
| FR-T106 | write lessons back to skills only with his approval and undo | [7][150] | NEXT |
| FR-T107 | use traces and evals for an improvement loop (OpenAI cookbook pattern) | [150] | LATER |
| FR-T108 | handle RLM-style recursion (asked twice, never answered) | [89][118] | LATER |

### 3.19 Branching

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T109 | ship QMA v2 through integration → staging → main; main moves only by his click | [150][memory] | WED |
| FR-T110 | clean junk branches and worktrees, with his go per deletion | [150][157] | NEXT |
| FR-T111 | archive superseded docs with a stamp, not delete them | [147][150] | NEXT |

### 3.20 Everything else

| ID | QMX shall… | Msgs | Pri |
|---|---|---|---|
| FR-T112 | let agents know QML, QMB, QMF and the Library exist, as tools or SDKs | [118] | WED |
| FR-T113 | let agents read and parse data, and confirm stored writes | [118] | WED |
| FR-T114 | give agents the Claude Code baseline: shell, Python, files, web, CLI tools, video watching | [89] | WED |
| FR-T115 | integrate Firecrawl, including Alexandria, for web and documentation work | [89] | NEXT |
| FR-T116 | give agents news and crypto data tools (cTrader news, CCXT) | [17] | LATER |
| FR-T117 | have the database refactored to be usable by agents | [125] | NEXT |
| FR-T118 | name the Library and QMB seams in code and docs | [141][150] | WED |
| FR-T119 | support voice/conversational mode and GPT audio/image | [128][150] | LATER |

---

## 4. Non-functional requirements

| ID | Area | QMX shall… | Msgs |
|---|---|---|---|
| NFR-T01 | Cost | never pay API prices for Claude or Codex; Claude and GPT run only on his subscriptions | [50][78][159] |
| NFR-T02 | Cost | let every other provider run on its own API key, with no provider count limit | [123][128] |
| NFR-T03 | Cost | respect vendor terms: Claude only through the Agent SDK signed in by him; no proxy cloaking | [51][73][80] |
| NFR-T04 | Cost | keep sub-agents few, background-only, never pausing mid-run (the cache lasts ~10 min); no nested sub-agents | [1][q74a][78] |
| NFR-T05 | Caching | treat caching as the top priority: a stable prompt prefix and one account per session | [50][89][157] |
| NFR-T06 | Caching | record cache reads and writes per call, and show savings | [89][96-research] |
| NFR-T07 | Caching | record the four axes for every run: caching, where it runs, who runs it, how | [157] |
| NFR-T08 | Performance | handle ~40 agents at once on his PC | [118] |
| NFR-T09 | Performance | keep the light lane in-process; only sessions that need Claude Code capabilities pay ~1 GB each | [123][156] |
| NFR-T10 | Performance | need no Docker or heavy sandbox by default | [118][150] |
| NFR-T11 | Performance | measure the database's write limits before 40 agents run | [120] |
| NFR-T12 | Reliability | survive restarts: workflows and errands resume from checkpoints, even days later | [118][141] |
| NFR-T13 | Reliability | design retries, timeouts and parallel joins in from the start | [20§3] |
| NFR-T14 | Reliability | recover stuck headless sessions with a watchdog | [124] |
| NFR-T15 | Durability | keep research and decisions in the repo, not scratch drives | [50] |
| NFR-T16 | Observability | make every run explainable afterwards (transcript, logs, traces, local only) | [50][128][150] |
| NFR-T17 | Observability | give the DevOps lens equal weight with features | [118][157] |
| NFR-T18 | Security | keep money-path rules in code, never in a skill or prompt | [7] |
| NFR-T19 | Security | keep credentials out of chat, repo and .env (Credential Manager only) | [memory][124] |
| NFR-T20 | Security | treat downloaded content (videos, news, pages) as untrusted input for computer use | [72-research] |
| NFR-T21 | Configurability | make everything editable in the UI with sensible defaults (Lego) | [17][147][150] |
| NFR-T22 | Configurability | let providers, models, plugins, seats and templates be added or removed as data | [86][124] |
| NFR-T23 | Extensibility | be model-agnostic: a new model or provider is a config row | [86] |
| NFR-T24 | Extensibility | build one QMX contract with two engine implementations (OOP-style) | [141] |
| NFR-T25 | Pluggability | make memory, compute providers, tools and plugins swappable | [15][150][159] |
| NFR-T26 | Portability | run on Windows (his PC) and Linux (remote), with Windows/Linux differences documented | [125] |
| NFR-T27 | Legibility | explain in plain words; one word per thing ("Claude Agent SDK" never mixed with "Claude Code CLI") | [101][118][150] |
| NFR-T28 | Legibility | never ask before he has read; answer research-shaped questions yourself; ask only real decisions, with a recommendation | [9][50][125][128][159] |
| NFR-T29 | Legibility | give opinions, not agreement; go back to a skipped step instead of footnoting it | [135] |
| NFR-T30 | Process | follow the structured method (map, skill order, independent check per PR); no vibe coding | [4][94][101][135] |
| NFR-T31 | Process | design for complexity: build for load before it arrives, and surface what he wouldn't consider | [89][105][157] |
| NFR-T32 | Process | test the backend without the UI | [118] |
| NFR-T33 | Process | read primary sources in a browser, not summaries | [17][150][157] |

---

## 5. His mental models, in his terms

- **Organogram** [15][17][141]: an org chart of copilots. One general copilot (like Claude Code or Codex) and specialised ones per surface (Lab, Portfolio, mini apps), each with its own tools, skills, hooks and memory, and any one able to host any conversation. Later he says plugins express it [150].
- **Engine in an engine** [86][118]: Claude Code is already a harness. Putting it inside QMX means two engines coupled together. "If you accelerate this one, the other must accelerate", and they may not be the same capacity. So QMX must own the configuration, or not run Claude Code as-is.
- **Lego** [17][147][150] (from memory, 2026-10-02): everything has defaults, but every part can be added, removed or edited in the UI.
- **Harness / loop / graph** [145][150][157]:
  - the harness is the environment;
  - a loop is a feedback cycle with a stop rule;
  - a graph is the flow;
  - a loop is one node in a graph.
  
  He thinks graphs may replace "workflows" and "sub-agents" as QMX words, and that the clipping comparing the three is a building block.
- **Router as a usage balancer** [74][141][150]: not per-request load balancing. It balances sessions and usage across accounts and providers, so QMX never depends on one vendor. It replaces CLIProxy.
- **API compatibility** [125][128]: every provider copies Anthropic's or OpenAI's format. Design for those two and everything plugs in by base URL plus key.
- **Plugins** [123][150]: a plugin is tools/MCP + skills + a model + hooks. A session loads one by default. That is how the organogram becomes concrete.
- **Errands** [17][64-research]: his long-running "project-like sessions" in the Lab. The UI calls them errands; they connect everything.
- **Design for complexity** [89][105][157]: build for higher load than today and handle cases he hasn't named. The ideas are "endless".
- **OOP** [141]: one interface, two implementations (Anthropic, OpenAI). What one SDK has, rebuild on the other.
- **Orchestrator** [141]: a strong Claude model running a long, persistent session, choosing which model does each job from router data (usage left, strengths), like a manager scoping work for GPT or GLM.
- **Baseline = this session** [89]: whatever Claude Code can do out of the box is the floor for every QMX agent. QMX adds rules (hooks, placement).
- **Branch flow** [150]: integration (works) → staging (ready to integrate) → main (his click).
- **Mini apps from n8n** [150][157]: workflows and mini apps grew from n8n-style node editing into ML-level packaged units.
- **Not every workflow needs AI** [157]: deterministic steps don't spend tokens.
- **Four axes** [157]: caching; where it runs; who runs it (provider); how (graph or loop).
- **Rent, don't own** [159]: compute by the minute (Amp-style), never a box that limits him.

---

## 6. Repetition map (ideas stated 3+ times)

| Idea | Count | Msgs |
|---|---|---|
| Organogram (copilots per surface; enhance it) | 10 | [15][17][86][89][105][118][125][135][141][162] |
| Off-machine / server runs | 8 | [15][50][123][125][128][141][150][159] |
| Router / load balancing / multiple accounts | 8 | [74][86][101][118][125][141][150][q74a] |
| Graph and loop engineering | 7 | [15][86][145][147][150][157][159] |
| Stop vibe coding / need structure | 6 | [4][15][94][101][135][143] |
| Design for complexity | 6 | [89][105][118][157][159][162] |
| Logs, transcripts, DevOps lens | 6 | [50][74][118][128][145][157] |
| Library is a database / Library out of scope | 6 | [89][94][118][141][150][157] |
| Never pay API for Claude/Codex; use subscriptions | 5 | [50][78][86][157][159] |
| Caching is critical | 5 | [50][74][89][145][157] |
| Claude Code vs Agent SDK naming confusion | 5 | [89][101][118][121][150] |
| Don't want the Claude Code CLI / engine-in-engine | 5 | [74][86][118][125][150] |
| Compaction (automatic, Anthropic-style, what is used) | 5 | [50][89][105][123][150] |
| Sub-agents with their own model and scope | 5 | [50][74][101][118][150] |
| Consider the UI in everything | 5 | [17][89][128][141][150] |
| Working QMX by tomorrow / Wednesday | 5 | [103][141][150][157][162] |
| Sub-agent cost rules (few, no nesting) | 5 | [1][17][78][q74a][157] |
| WF1/WF2 deserve their own discussion | 4 | [17][50][89][162] |
| Mini apps: create, run, maintain, edit | 4 | [17][118][150][157] |
| Workflows agentic / non-agentic / mixed | 4 | [118][150][159][162] |
| Hermes as a reference (memory, cron, switching, self-improvement) | 4 | [15][89][123][150] |
| Self-improvement | 4 | [89][118][141][150] |
| Computer use / cTrader / MT5 | 4 | [15][17][89][123] |
| System prompts / context engineering | 4 | [94][141][150][157] |
| Use the morning research / everything already given | 4 | [121][157][159][162] |
| Don't assume I've read / don't ask before processing | 4 | [9][50][128][159] |
| Pluggable memory | 3 | [15][50][150] |
| Plugins per surface | 3 | [123][125][150] |
| Model-agnostic harness / many providers | 3 | [86][123][128] |
| Read docs like a human in the browser | 3 | [17][150][157] |
| "What do you need from me / I'm repeating myself" | 3 | [123][159][162] |

---

## 7. Questions he asked that never got a real answer

From the ledger (morning and early afternoon), still open:
1. "Which model goes where; do we have defaults?" [17]. Defaults exist in `models-routing.md` but on API keys, now invalid for Claude/GPT.
2. "Agent as a folder: your actual take?" [17]. Only an early yes [18]; never confirmed after Eve.
3. "How will QMX's own browser and computer use be built?" [89]. Never designed. OpenCUA vs cua-driver never compared for him.
4. "Do you know what it means to port all these sessions via the UI?" [70][74]. One paragraph.
5. "How does the Agent SDK handle RLM?" [89][118]. "Not built yet".
6. "What are you using for compaction?" [105]. Answered only indirectly.
7. "Find my backlog, not only the UI backlog" [103][105]. Promised, never done.
8. "How did huge companies handle tools and database connections?" [105]. Never answered.
9. Claude's dismissed round [8]-[9]: small first version vs full machinery; which actions always ask; effort automatic vs a dial; proxy disguise. Never re-asked.
10. "The one rule the copilot must never forget" [7]. Never asked again.
11. "Thinking modes when switching model mid-conversation?" [123]. Never answered.
12. "MCP apps: we were meant to talk about it more" [123]. Never answered.
13. "How are we accepting MCPs and plugins?" [123]. Half answered (own home, plugins).
14. "Does Windows vs Linux code differ for agents?" [125]. Never answered.
15. "Refactor the database for agents?" [125]. Never answered.
16. "Should the Lab's complexity have been handled by mini apps?" [118]. Never answered.
17. "How is the agent meant to know QML/QMB exist; how does Lab reach Portfolio?" [118]. Only a ticket (18) was opened.

After the ledger:

18. "Can't we rebuild what Anthropic has in the OpenAI SDK and vice versa?" [141]. Only the plugin-loader idea [156]; no parity table.
19. "How do Pi and Hermes combine both formats?" [141]. One line about Hermes [126]; Pi never looked at.
20. "What is QMA exactly; does it go deeper?" [125]. One line [126]; he then redefined it as "Quant agents" [150].
21. "How are you handling system prompts; meta prompts with XML?" [150]. A one-line yes [156]; he said "you need to really think through that" [157].
22. "What is QMF?" [150]. He doesn't recall its role; not answered.
23. The Library's real name ("Strats…, starts with A"?) [150]. Unclear dictation; not resolved.
24. "What is a graph; does graph engineering replace workflows and sub-agents?" [157]. Turned into a vocabulary question [158]; he gave Claude liberty [159]. No design answer.
25. "The router has to be in the graphs and loops: how?" [157]. Not designed.
26. "How do both SDKs handle logs?" [128]. Partly in study 19 (tracing); no DevOps design.
27. "How do I sign in with ChatGPT in QMX?" [50][159]. "To confirm" [161].
28. "Will P16c interfere with building on rebuild/base?" [159]. Answered "no collision" [161]; the branch fold question (integration vs rebuild/base) is still open.
29. "Best of what? Did you even consider the organogram?" [162]. This file is the start of that answer.
30. "Where do how and why come in? Redesign the workflow" [135]. A table in chat [136]; `workflow.md` never rewritten.

---

## 8. Explicit out-of-scope items and named seams

| Item | Status | Seam / note | Msgs |
|---|---|---|---|
| **Library** (v2, git-like or database, concurrent edits) | OUT OF SCOPE for QMA v2 | Name the seam in code and docs; agents reach it as a tool | [94][118][141][150] |
| **QMB** (tamper-proof backtest CLI from Lean CLI + Jesse) | OUT OF SCOPE; refactor later from its own docs | Tool seam; the old daemon spawn in `qmb host` stays until then | [118][150] |
| **QML changes** (from the risk-and-sizing session) | OUT OF SCOPE here | Tool/SDK seam only | [50][150] |
| **WF1 / WF2** (and WF3) | OUT OF SCOPE (his backlog) | Note as seeds; the graph engine must be able to express them later | [17][50][89][162] |
| Risk and sizing changes | OUT OF SCOPE (other session) | Money path stays in code | [17][50] |
| UI wiring | Separate UI session; browser-first | Backend must work headless | [103][105] |
| P16c | Separate session | Its final summary feeds the plan | [111][113] |
| QMF role | Unknown to him | Ask later | [150] |
| LangSmith, Gateway, Engine | Not used | — | [89] |
| Amp orbs | Not paid for; reference only | — | [150][159] |
| Owned server (Contabo) | Withdrawn | Rented compute instead | [159] |
| Grok | Not wanted | — | [128] |
| Voice, System-1 models, GPT audio/image | PARKED | — | [128][150] |
| Sandboxes / Docker by default | Not wanted | Optional later | [118][150] |
| Codex as a harness | Not wanted ("slow and heavy") | GPT through its SDK lane | [125][145] |
| Claude Code CLI | Not wanted | Agent SDK capabilities only | [150] |
| Max-plan API credits | Rejected | Subscription only | [159] |

**Messages after the ledger that override it**
- Engine is now two SDKs (Claude Agent SDK, OpenAI Agents SDK), not Claude Code + LangGraph.
- No LangGraph: QMX's own graph.
- No owned server.
- No API for Claude/Codex, even with credits.
- No sandboxes.
- Plugins are the organogram unit.
- Branching is integration → staging → main.
- Wednesday minimum defined [150].
