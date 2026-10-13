---
title: QMA v2 (Quant agents v2)
status: draft
created: 2026-10-12
updated: 2026-10-12
---

# PRD: QMA v2, the rebuilt agent system of QMX

## 0. Document purpose

This is the one requirements document the QMA v2 architecture is designed against tonight (Monday 2026-10-12). Code ships from Tuesday morning. It merges the requirement extractions into one deduplicated list. It is a merge, not a new design: every requirement traces back to something the operator said or ratified.

- **Structure:** BMAD `bmad-prd` template (`.claude/skills/bmad-prd/assets/prd-template.md`): global stable IDs, FRs grouped by feature area, cross-cutting NFRs in their own section, glossary terms used exactly.
- **Inputs, in authority order when they conflict:** `26-requirements-from-today.md` (highest) > `20-qma-v2-direction.md` §4 > `21-miniapps-and-workflows-seeds.md` > `27-requirements-from-audit-session.md` > `00-session-ledger-2026-10-12.md`. Code facts come from `24-how-why-integration-surface.md`. Capability facts come from `19-two-sdk-study.md`, `22-cookbooks-and-templates.md` and `rebuild/research/2026-10-12-agent-system/notes/models/subscription-terms.md`; none of those three creates a requirement by itself. All paths are under `tracker/agent-system/research/` unless stated.
- **Trace keys:** `FR-T##` / `NFR-T##` = file 26. `FR-A##` / `NFR-A##` = file 27. `S##` = seed in 26 §2. `27-S##` = seed in 27 §2. `21-S##` = seed in 21 §2. `[n]` = message in today's full export (26's numbering). `L[n]` = message in the ledger (00's numbering). `R20§x` = direction note section.
- **Priorities:** **WED** = needed for the Wednesday 2026-10-14 minimum. **NEXT** = straight after Wednesday. **LATER** = parked but wanted.
- `[ASSUMPTION]` marks a number or reading Claude inferred; each is listed in §11.

---

## 1. Vision, user and success

### 1.1 Vision (plain words)

QMX is the operator's Windows desktop workbench for quant-trading research. QMA v2 ("Quant agents") is its agent system, rebuilt cleanly.
He talks to one copilot that feels like Claude Code or Codex. Behind it sits an organogram of specialised copilots (Lab, Portfolio, mini apps), each one a plugin.
The copilot builds, runs, maintains and edits his mini apps and workflows. Some are agentic, some are plain code, many are both.
Agents run on two engines behind one QMX contract. The Claude Agent SDK runs on his Max 5x plan. The OpenAI Agents SDK runs GPT through his ChatGPT plan and any other provider by API key.
A router spreads work across his accounts per session, so QMX never depends on one vendor, and he never pays API prices for Claude or Codex.
Long work runs for days, survives crashes, and can move off his PC to rented compute. He always sees where it runs and what it cost.
Agents can propose trades but can never place them. Everything has a sensible default and is editable in the UI, like Lego.

### 1.2 The user

- **Mubarak, the operator.** One person and the only user. Non-technical, he dictates long brain dumps (expect transcription noise) and reads plain words and diagrams, not walls of text.
- **What he has:** a Windows PC; a Claude Max 5x plan; a ChatGPT plan; API keys for other providers (GLM, MiniMax, Kimi, DeepSeek and others); demo and live broker accounts (cTrader; MT5 not installed).
- **Jobs to be done:**
  - research, test and run strategy ideas without writing code himself;
  - have many errands running in parallel (about 40 agents at peak) without watching them;
  - trust what came back: where it ran, what it did, why, and what it cost;
  - change anything (models, plugins, workflows, apps) himself, in the UI.
- **Non-users (v1):** other people. Sharing is by bundle, never a marketplace (FR-A84).

### 1.3 Success criteria

**Wednesday (2026-10-14), the minimum [150][157]**

| ID | Criterion | Measured by |
|---|---|---|
| SC-1 | The copilot works: a message in, a streamed reply out, on the Claude engine on his plan, with tools | FR-013, FR-020-022 acceptance checks pass live |
| SC-2 | He can create, run, maintain and edit a mini app and a workflow, agentic and not, by asking the copilot | FR-056 and FR-072 headless scenarios pass live |
| SC-3 | The organogram works: general, Lab and Portfolio copilots load their own plugins on either engine | FR-002, FR-030, FR-031 checks pass |
| SC-4 | Sub-agents work, each with its own model and provider | FR-084, FR-085 checks pass |
| SC-5 | A workflow runs off his machine on rented compute and its results come back | FR-110, FR-113 checks pass |
| SC-6 | Nothing on the money path was reachable by any agent during the above | FR-102 test passes on both engines |

**Later (NEXT, then LATER)**
- **SC-7:** about 40 concurrent agents on his PC without starving it (NFR-007).
- **SC-8:** a days-long workflow survives a crash and resumes (NFR-010).
- **SC-9:** the usage page shows cache savings, and the cache-read ratio meets NFR-004.
- **SC-10:** he edits seats, plugins, models and templates in the UI without asking for code changes (NFR-018).

**Counter-metrics (do not optimise)**
- **SC-C1:** cheapest model per call. He wants capable, not cheap ([q74a]). Counterbalances the router (FR-041).
- **SC-C2:** number of agents or sub-agents spawned. More helpers burned half his usage ([q74a]). Counterbalances FR-084.
- **SC-C3:** questions asked to the operator. Fewer and better, each with a recommendation (NFR-024).

---

## 2. Scope

### 2.1 In scope

- The copilot and the organogram (general, Lab, Portfolio and per-mini-app copilots as plugins).
- The turn host, sessions, errands and background tasks.
- The two engines behind one `Engine` contract, and the plugin loader for both.
- The router, accounts, usage ledger and limits.
- QMX's own graph and loop runner for workflows, plus templates and triggers.
- Building, running, maintaining and editing mini apps (the mini-app runtime itself stays as shipped: "solid enough for now", R20§1).
- Sub-agents, memory, context, prompts, caching and compaction.
- Approvals, hooks, the money-path barrier and the journal.
- Placement on rented compute, run records, observability and the event stream the UI reads.
- Ports of the LangChain-era features (§7).

### 2.2 Out of scope (named seams only)

| Item | Seam QMA v2 keeps | Source |
|---|---|---|
| **The Library** (v2 refactor, git-like or database; concurrent-edit locking) | A named tool seam; agents call it, QMA v2 does not change it | R20§1; 26 §8; [94][118][141][150] |
| **QMB** (tamper-proof backtest CLI) | A tool seam; the old `qma.daemon` anchor in `qmb/doors/cli/host.py` stays until the QMB review | R20§1; 24 §6.2; [118][150] |
| **QML changes** (risk-and-sizing proposal) | A tool/SDK seam only | R20§1; [50][150] |
| **WF1/WF2 (and WF3)** | The graph runner must be able to express them later (FR-069) | 26 §8; [17][50][89][162] |
| Risk and sizing changes; trading-node (QMN) live deployment | Money path stays in code | 26 §8; 27 FR-A85 |
| UI wiring | Separate UI session, browser-first; the backend must work headless | L[101]-[103] |
| P16c retirement of the old runtime | Its own session; its summary feeds the plan | [111][113] |

### 2.3 Non-goals

- QMX is not a general agent platform for other users, and it has no marketplace.
- QMX does not proxy, cloak or rotate subscription tokens, and never reads a Claude or ChatGPT login token.
- QMX does not run the Claude Code CLI, Codex as a harness, LangGraph, Deep Agents, LangSmith, CLIProxy, Amp orbs or Grok.
- QMX does not own or manage a server.
- No copilot modes. No agent places, sizes or cancels a live order.

---

## 3. Constraints

### 3.1 Ratified constraints

| ID | Constraint | Source |
|---|---|---|
| C-01 | Two engines behind one QMA `Engine` interface: the Claude Agent SDK and the OpenAI Agents SDK | R20§1 "Engines"; FR-T10; [125][128][135][150] |
| C-02 | The Claude Agent SDK is used for Claude Code's capabilities (tools, sessions, hooks, sub-agents, permissions, plugins), never the CLI, and only on his Max 5x subscription, signed in by him | R20§1, R20§4; FR-T11, FR-T12; [150][159] |
| C-03 | The OpenAI Agents SDK reaches any OpenAI-compatible provider by API key, with no limit on how many | FR-T14, FR-T26, NFR-T02; [123][125][128] |
| C-04 | Never pay API prices for Claude or Codex. GPT is used only through his ChatGPT subscription ("Sign in with ChatGPT"). The Max API-credit idea is dropped | R20§4; NFR-T01; S94; [159] |
| C-05 | Plugins (tools/MCP + skills + model + hooks) are the unit of the organogram; a session loads one by default | R20§1 "Plugins"; S64; [123][150] |
| C-06 | QMA has its own graph and loop engine; LangGraph is out | R20§1 "Workflows"; FR-T36; S85; [150] |
| C-07 | The router balances usage across accounts and sessions, never single requests, and replaces CLIProxy | R20§1 "Router"; S76; [141][150] |
| C-08 | No owned server. Off-machine work runs on rented, on-demand compute from several providers | R20§4; S95; [159] |
| C-09 | No sandboxes by default | R20§1 "Sandboxes"; S88; [150] |
| C-10 | No modes: skills plus always-on hooks | FR-T07; 27 §8.1; [7][118]; 27 [149] |
| C-11 | Money-path barrier: agents never place live orders, size positions or touch the kill switch; they only propose | FR-T72; 27 §8.1; NFR-A09; memory rule |
| C-12 | Branching: integration → staging → main. Only the operator promotes to main | R20§1 "Branching"; FR-T109; [150][157] |
| C-13 | Out of scope, named seams only: the Library, QMB, QML changes, WF1/WF2 | R20§1; 26 §8 |
| C-14 | Wednesday minimum: copilot works; create/run/maintain/edit mini apps and workflows, agentic and not; organogram works; sub-agents work; workflows run off his machine | R20§1 + R20§4; S90; [150][157] |

### 3.2 Carried standing rules

| ID | Rule | Source |
|---|---|---|
| C-15 | Credentials live only in Windows Credential Manager under `qmx/*`; never in chat, repo, `.env`, logs or backups | NFR-T19, NFR-A07; memory |
| C-16 | Configurable means editable in the UI, with defaults (the Lego rule) | NFR-T21, NFR-A02; memory |
| C-17 | Risk and sizing authority is GitBook plus the node docs; money is USD | map.md carried rules; memory |
| C-18 | Backend first; it must work and be testable without the UI | NFR-T32; S51; [118] |

### 3.3 Conflicts resolved in this merge

| # | Conflict | Resolution |
|---|---|---|
| K-01 | Server: R20§1 and R20§3.6, 21-S27 and 27 FR-A94 plan his Contabo box as "QMX's own orb"; L[124q] ratified "design now, ship later" | R20§4 and 26 [159] win: no owned server, rented on-demand compute. FR-A94 is kept, retargeted to setting up rented machines (FR-111) |
| K-02 | Claude by API key: R20§2.1/§3.1 (Max credits), 19 §1 (Claude through LiteLLM), ticket 02 L67 | R20§4 wins: Claude runs only on the Claude engine on his plan. No Anthropic API key is ever used for Claude |
| K-03 | Naming: `glossary.md` and L[99]/L[116] say "Claude Code", never "Agent SDK" | 26 NFR-T27 and C-02 win: "Claude Agent SDK" names the engine library, "Claude Code CLI" is never used. §6 replaces the old glossary |
| K-04 | Workflow engine: 19 §13 recommends keeping LangGraph; 27 FR-A64 shipped a LangGraph compiler | C-06 wins. 19 is a capability fact source only. The `workflow.v1` format survives, the compiler is replaced (24 §6.1) |
| K-05 | Main-agent model: 21 Q15 (Codex subscription drives the main agent), 27 [58] (GPT/Codex as workhorse) | 26 and R20§4 win: the copilot runs on the Claude engine on Max; GPT runs only through SIWC |
| K-06 | Isolation: 27 FR-A76 (Docker and remote-sandbox tiers) and FR-A35 ("run new tool code isolated first") | C-09 wins for defaults. A mini app's own subprocess, venv and limits (tier 1) is process separation, not a sandbox, and stays. Docker and remote sandboxes are opt-in only (FR-075, FR-081) |
| K-07 | 27 FR-A15: a full agent loop is the default for every node | 26 FR-T38 wins: non-AI nodes are the default; agent nodes use the engine loop (FR-054, FR-063) |
| K-08 | R20§3.5 "separate verifier" per agent node vs 22 §5 "too strong" | FR-T41 kept: every agent node has a separate checker. It is deterministic (code, schema, execution) by default; an agent verifier is added where stakes or bias call for it (FR-063) |
| K-09 | Orchestrator lifetime: 26 FR-T44/S77 (one persistent session, never fresh per decision) vs 22 §5 (a chain of sessions) | 26 wins: resumed session plus a state file. Whether to roll the session at phase ends is left to the architecture (§9.2 A-12) |
| K-10 | Memory: 27 FR-A53 (built-in plus at most one external provider) vs 26 FR-T62 (per-agent binding) | 26 wins: per-agent binding (FR-092) |
| K-11 | Model switching: 27 NFR-A12/FR-A110 and 22 ("never switch inside a session") vs 26 FR-T70/S62 (switch with a cost pop-up) | Both kept: the router never switches a running session; the operator may, with a warning and compaction first (FR-039, FR-099) |
| K-12 | Approval list: 27 FR-A45 proposes one; 26 FR-T76 says he decides | He decides (Q1); FR-A45's list is the recommended default (FR-105) |
| K-13 | 27 FR-A63: a per-task stance (do it / pair / coach) | Dropped: it sat inside the withdrawn modes section; a skill can offer it |
| K-14 | L[124q] "two lanes": subscription lane through Claude Code plus an API lane on a LangGraph QMX engine | Replaced by C-01: two SDK engines. "Lane" survives only as a glossary word (§6) |
| K-15 | L[116] keep `native_codex.py`; 27 [58] Codex as workhorse | 26 S97/FR-T18 win: no Codex harness. `native_claude.py` is kept as reference only (24 risk 9) |
| K-16 | 21 §3 #16 "mini apps are extensions"; R20§2.3 Amp portals as the mini-app process manager | R20§4 wins: a mini app is QMX's packaged, versioned unit, not a portal. "Extension" is retired as a word (Claude has vocabulary liberty, [159]) |
| K-17 | Node kinds: R20§3.4 lists four, P10 ships ten (21-S17) | Requirements keep the ten as capabilities and add triggers; the final list is architecture's (§9.2 A-08) |
| K-18 | 27 FR-A85: a trading node as a headless app with live permissions | Out of QMA v2 scope (QMN/node docs; money path) |
| K-19 | L[116] "no Claude in workflows" vs L[121] "Claude often orchestrates" | 26 wins: Claude may orchestrate, but never one Claude session per workflow step (FR-021, FR-065) |
| K-20 | `workflow.md` "BMAD not needed" vs project `CLAUDE.md` (PRD plus Architecture via BMAD) | The project `CLAUDE.md` wins; this PRD is that step |

---

## 4. Functional requirements

Format: one row per FR. "Accept" is a check that runs without the UI unless stated.

### 4.1 Copilot and organogram

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-001 | QMX runs a general copilot that handles daily work as broadly as Claude Code or Codex | WED | FR-T01, FR-A06; S04; [15][89] | Headless turn: a plain request is answered with at least one tool call and a streamed reply |
| FR-002 | QMX runs specialised copilots (Lab, Portfolio, one per mini app), each a plugin loaded into a session | WED | FR-T02, FR-A07; S04, S64; 27-S34 | Sessions started with `plugin=lab` and `plugin=portfolio` each list only their plugin's tools and skills |
| FR-003 | Any copilot can host any conversation; a session records its surface and target (app, version, account, environment), and the target never drifts when the UI focus changes | WED | FR-T03; 21-S49, 21-S56; [15][118] | API test: change the UI focus field; a running session's target is unchanged |
| FR-004 | The general copilot lists, opens and continues sessions started on any surface | WED | FR-A08; 27-S35 | List-sessions API returns sessions from every surface, each with a surface field |
| FR-005 | A copilot reaches Portfolio things from the Lab, and both from the main chat | WED | FR-T04; S58; [118] | A Lab session calls a Portfolio read tool successfully; Portfolio write tools still ask |
| FR-006 | Copilots have no modes; skills and always-on hooks replace them, and the leftover plan/do code is removed | WED | FR-T07, FR-A06; S98, 27-S33 | Code search finds no mode enum or plan/do path in QMA v2 packages |
| FR-007 | The operator adds, edits and removes organogram seats in the UI | NEXT | FR-T08; [17][150] | Seat create/update/delete via API persists; the next session loads the change |
| FR-008 | An app-use copilot can operate a mini app but not edit it; edits go to authoring as a change-request artifact | NEXT | FR-A09; 21-S50 | An edit tool called in an app-use session is refused and a change request is created |
| FR-009 | His day-to-day copilot stories are acceptance scenarios: build a workflow, build or change an app, overnight run with morning brief, assess an idea, fix a broken app, connect a broker or data source, schedule a routine, map a big effort, capture a procedure | NEXT | FR-A13 | Each story has a scripted headless scenario that passes on the fake engine |
| FR-010 | Every copilot result is a typed artifact (card, preview, Library item), never only chat text | NEXT | FR-A114 | The block log holds an artifact block for each build action |
| FR-011 | Copilot chat accepts attachments and routes them to tools | NEXT | FR-A38 | An attached CSV reaches a data tool as a file reference |
| FR-012 | Every copilot prompt carries his one standing rule once he names it (Q2) | NEXT | FR-T09; [7] | The rule text is present in each copilot plugin's static prompt |

### 4.2 Turn host, sessions and errands

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-013 | A turn host takes a message, runs the agent and streams the reply, with no UI attached | WED | FR-T19; 24 summary 2-3; [117][118] | POST a message; typed blocks arrive over SSE (fake engine in CI, live engine by operator script) |
| FR-014 | Errands are first-class: several run in parallel, each resumes, and each links to what it built | WED | FR-T06, FR-A59; S21; [17][74] | Start 3 errands, kill the host, restart: all 3 resume and list their linked artifacts |
| FR-015 | The copilot starts, checks, cancels and lists background tasks while the chat stays live | WED | FR-A04; NFR-A17 | `start_task` returns an id at once; a chat turn completes while it runs; cancel stops it |
| FR-016 | Long sessions stay alive by saved-session resume plus a progress/state file, never a fresh session per decision | NEXT | FR-T69; S77; [141][156] | A resumed session reads its state file and continues the plan after a host restart |
| FR-017 | Each task keeps an append-only log; runs resume by run ID and are never merged | NEXT | FR-A60 | Two runs of one workflow keep separate logs; resume by ID continues the right one |
| FR-018 | An unattended run gets its authority at launch, asks no questions, and ends with an "assumptions to confirm" card | NEXT | FR-A29, FR-A61; NFR-A20 | A scheduled run completes with zero approval prompts and emits the assumptions card |
| FR-019 | Each errand has a "What it did" receipt and feeds the drawer: activity, diff, terminal, browser | NEXT | FR-A62; S07 | The errand API returns a receipt and the four drawer feeds |

### 4.3 Engines

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-020 | Agents run on two engines behind one QMX `Engine` contract (start, resume, send, stream, approve, interrupt, delegate, usage, checkpoint, close) | WED | FR-T10; C-01; 19 §11 | One contract test suite passes on both engines with fakes |
| FR-021 | The Claude engine uses Agent SDK capabilities and never the Claude Code CLI; no Claude session and no Codex process is started per workflow step | WED | FR-T11, FR-T18; S26, S97; [125][145][150] | During a 20-node workflow run, live Claude sessions stay at or under the cap, and no `codex` process exists |
| FR-022 | Claude runs only on his Max 5x plan, signed in by him; QMX never reads, stores or relays the login token | WED | FR-T12; FR-A19 (superseded); [51][73][159] | Secret scan of config, logs and journal finds no Anthropic token; the Claude engine refuses an Anthropic API key |
| FR-023 | GPT runs only through his ChatGPT plan via Sign in with ChatGPT; feasibility is confirmed first, and if it fails GPT is shown "unavailable", never routed to paid API | WED | FR-T13; FR-A19 (superseded); [50][86][159] | With SIWC off, a GPT-model session is refused with an "unavailable" card and no OpenAI API key is accepted for GPT |
| FR-024 | Every other provider runs on the OpenAI engine by base URL plus key, in the Anthropic or OpenAI wire format | WED | FR-T14; S67; [125][128] | Add a DeepSeek row; a session completes one tool call on it |
| FR-025 | A capability one SDK lacks (approvals, policy hooks, plugins, compaction) is built once as a QMX contract and mapped onto both | WED | FR-T15; S79; [141][150] | One money-path denial test and one approval test pass on both engines |
| FR-026 | Engine and model are chosen per agent, sub-agent and errand through a chain (global → app → workflow → node → sub-agent); the model actually used is recorded | WED | FR-T16, FR-A17; S54; [118] | Run index shows the resolved model per call; a workflow-level override changes only that workflow |
| FR-027 | A new model or provider is added as data, with no engine code change | NEXT | FR-T17; S32; [86] | Add a model row; a session runs on it with no code diff |
| FR-028 | Every agent is defined by one engine-neutral spec (model, prompt, tools, MCP, skills, memory scope, sub-agents, approvals, file permissions, budget) compiled per engine | WED | FR-A14; 27 §4 "AgentSpec" | The same spec builds and runs on both engines in the contract tests |
| FR-029 | Provider errors are retried or failed over only at session or task boundaries | NEXT | FR-A18 | Injected 429 on a running session: no mid-session switch; the next task goes to the fallback |

### 4.4 Plugins and skills

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-030 | One plugin format (tools/MCP + skills + model + hooks) loads on both engines; QMX supplies the loader for the OpenAI engine | WED | FR-T05, FR-T20; C-05; R20§3.3 | The Lab plugin loads on both engines with identical tool and skill lists |
| FR-031 | QMX ships default general, Lab and Portfolio plugins | WED | FR-T21; [123][150] | Three plugins present; each passes the plugin lint |
| FR-032 | QMX's plugins, skills, settings and memory live in a QMX-only home, isolated from his personal Claude Code | WED | FR-T22; S63; [123] | A Claude session runs with QMX's own config dir; his `~/.claude` is byte-identical after the run |
| FR-033 | The copilot creates, edits and installs plugins and agent specs | NEXT | FR-T23, FR-A05; [118] | Headless: copilot writes a plugin, installs it, a new session loads it |
| FR-034 | A cross-engine delegate plugin lets a Claude agent call an OpenAI-engine agent, and the reverse | NEXT | FR-T24; S80; [150] | A Claude session's `delegate` call returns compact JSON plus usage from a DeepSeek job |
| FR-035 | Default plugins ship the build-workflow, build-mini-app and maintain-app skills, written with intent and naming only real tools | WED | FR-A119; 21-S42; 27-S19 | Skill lint: every tool a skill names exists in its plugin |
| FR-036 | Skills have a lifecycle: rough description → authored → evaluated against "no skill" → versioned → activated; the list stays small, duplicates are flagged, knobs show in Settings | LATER | FR-T25, FR-A120, FR-A122; 21-S54 | A skill that does not beat no-skill on its test prompts cannot be activated |
| FR-037 | The copilot captures a repeated procedure as a skill draft with trigger tests, activated only on his approval; money-path skills never change without it | NEXT | FR-A121 | Draft skill stays inactive until an approval record exists |

### 4.5 Router, accounts and usage

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-038 | Accounts are rows: subscriptions (Claude, ChatGPT), API keys (GLM, MiniMax, Kimi, DeepSeek, MiMo…) and pools (OpenRouter, Ollama Cloud, OpenCode), with no limit | WED | FR-T26; S28, S66; L[124q] | Add and remove rows via API; no code change |
| FR-039 | The router balances usage per session, never per request, and replaces CLIProxy; it never switches a running session itself | WED | FR-T27, FR-A110, FR-A111; S76; C-07 | Simulate 40 sessions over 3 accounts: each stays on one endpoint; spread follows remaining usage |
| FR-040 | The router knows each account's availability, limits, usage and reset times | WED | FR-T28; [125][141] | Router status API returns all four fields per account |
| FR-041 | The router ranks by capability first, then remaining usage | WED | FR-T29; S09; [q74a] | With equal usage, a "hard" role gets the higher-capability model |
| FR-042 | Defaults set a provider per workflow, sub-agent or role; the copilot may change them | WED | FR-T30; S20; [17][150] | Setting "this workflow uses DeepSeek" routes only that workflow there |
| FR-043 | Router data (available models, usage left, strengths) is exposed as tools an orchestrator can call | NEXT | FR-T31; S78; [141] | `models_status` tool returns the catalogue inside a Claude session |
| FR-044 | Several accounts of one vendor are supported; a session stays on one account | NEXT | FR-T32; S29; [74][86] | Two Claude accounts: new sessions alternate, no session changes account |
| FR-045 | Thinking/effort is set per wire format and stays coherent when the model changes | NEXT | FR-T33; [8][123][125] | Switching Opus → GLM maps effort to the GLM equivalent without a 400 error |
| FR-046 | API keys come from Credential Manager and are handed to a session at start; per-run credentials are removed at teardown | WED | FR-T34, FR-A46, FR-A97; C-15 | Secret scan of settings, logs, journal and chat finds no key |
| FR-047 | The UI shows a per-role default model and a model picker | NEXT | FR-T35; S20; [17] | (UI) Picker lists models from account rows |
| FR-048 | QMX keeps its own usage count per run, fills gaps from local session files, and enforces limits by refusing a new session with an error card | WED | FR-T96, FR-A109; S65; [123][124] | At a configured limit, a new session start returns a refusal event, not a crash |
| FR-049 | Usage is read only from documented sources, never private OAuth endpoints | WED | FR-T97; 05 §3 | Code search: no call to undocumented usage endpoints |
| FR-050 | A usage page in T3 Code style shows limits, tokens, accounts in use, a graph and cache savings | NEXT | FR-T95, FR-A20; S40; [89][90] | Usage API returns per-account series and cache-savings totals |
| FR-051 | Model calls, tool calls and USD are capped per turn and per job, editable in Settings; a USD cap pauses rather than fails | WED | FR-A43 | A job hitting its USD cap is paused and resumable |

### 4.6 Workflows (graphs and loops)

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-052 | Workflows run on QMX's own graph runner over the `workflow.v1` JSON graph with typed state, not LangGraph; definitions have their own store | WED | FR-T36, FR-A64; C-06; 24 risk 11 | The P10 test list passes on the new runner; no `langgraph` import in QMA v2 |
| FR-053 | A workflow can be deterministic, agentic or mixed | WED | FR-T37, FR-A65; S52; [118][159] | One test workflow of each kind runs to completion |
| FR-054 | Nodes are non-AI by default; AI is used only where needed | WED | FR-T38; S91; [157] | A deterministic workflow records zero model calls in the usage ledger |
| FR-055 | Workflows, mini apps and widgets pass typed inputs and outputs to each other | WED | FR-T39; S52; [118] | A workflow output feeds a mini-app input; a type mismatch is rejected before the run |
| FR-056 | The copilot creates, runs, maintains and edits workflows through the same API the UI uses | WED | FR-T40, FR-A01; S59; [118][150] | Headless: copilot writes a 3-node workflow, validates, runs, edits a node, reruns |
| FR-057 | Validation runs before every run: cycles only through loop nodes, port types match, every loop has a maximum, every input is satisfied | WED | FR-A66; 21-S04, 21-S15 | Each of the four faults is rejected with a fix-it message |
| FR-058 | Human gates pause and resume; an approval binds to the exact revision and is asked again after any edit | WED | FR-A67; 21-S07 | Edit after approval: the gate asks again |
| FR-059 | Each node is checkpointed; runs lasting days resume after a crash without re-running finished nodes | WED | FR-T43; S77; [118] | Kill the runner mid-run, restart: completed nodes are skipped, the run finishes |
| FR-060 | A run pins its definition hash; edits create a draft and never change a running execution | WED | 21-S10; 21 §4 item 1 | Edit during a run: the run finishes on the old hash; the next run uses the new one |
| FR-061 | Side effects are safe: money or external-write nodes get a human gate, an idempotency key and no auto-retry; nodes have retries and timeouts; code-driven fan-outs are capped; joins name a merge rule; one failed branch keeps the others' results | WED | FR-A70, FR-A27; 21-S09; 21 §4 items 8-9; NFR-T13 | Re-running a recovered node does not repeat its external write; a failed branch leaves sibling outputs intact |
| FR-062 | A saved workflow is callable as a sub-agent or "workflow skill" through one `run_workflow` tool, and runs standalone or inside an app | WED | FR-A71, FR-A03, FR-A73 | The copilot calls `run_workflow` and gets an artifact reference back |
| FR-063 | An agent node is a loop with an evidence stop rule (pass, max attempts, delta flat, needs human, budget) and a separate checker, deterministic by default; a text-only end of turn is not "done" | NEXT | FR-T41, FR-A23, FR-A24, FR-A15 (superseded); R20§2.4 | An agent node that claims done without passing its checker loops again or stops with a named blocker |
| FR-064 | A dynamic workflow the copilot writes is saved as a graph the UI can render and re-run (exploration promoted to procedure) | NEXT | FR-T42; S68; 21-S11 | A copilot-run ad hoc plan is saved as `workflow.v1` and re-runs identically |
| FR-065 | One persistent Claude orchestrator can drive a long workflow and delegate steps to other models | NEXT | FR-T44; S78; [123][141] | A 2-day test workflow is driven by one resumed orchestrator session with delegated OpenAI-engine steps |
| FR-066 | Ready-made templates ship: Claude's six dynamic-workflow patterns, OpenAI's pattern set, and a research template with hard caps (5 researchers, 6 rounds, 10 tool calls each) that keeps idea generation apart from narrowing | NEXT | FR-T45, FR-A89, FR-A90; S12; R20§2.1 | Each template validates and runs on the fake engine |
| FR-067 | Each workflow exposes settings for compaction, sub-agents and models | NEXT | FR-T46; [147][150] | Per-workflow settings override global ones in a run |
| FR-068 | One workflow is shown as Graph, Code and Import views of the same JSON; a run can target one node, a section or the whole; drawing an edge has no side effect | NEXT | FR-A69; 21-S14, 21-S16, 21-S18 | Round-trip JSON → code → JSON is lossless for the template set |
| FR-069 | The graph runner can express WF1/WF2-style strategy pipelines later | LATER | FR-T47; S22; [50][162] | A WF1 skeleton graph validates |

### 4.7 Triggers and scheduler

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-070 | A QMX scheduler offers Hermes-style cron, timed loops and goal loops | NEXT | FR-T84; S41; [89][157] | A cron entry starts a workflow at the set time (fake clock) |
| FR-071 | Workflows start on schedule, event or manual trigger with an overlap policy, refuse when limits are hit, and follow scheduled-job rules (bookmarks, a failed read is never a quiet day, confirm before recording, re-check before acting, state the timezone) | NEXT | FR-T85, FR-A68, FR-A72; 21-S62 | An overlapping trigger is skipped or queued per policy; a failed source read is reported as failure |

### 4.8 Mini apps

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-072 | The copilot creates, runs, maintains and edits mini apps, agentic and not | WED | FR-T48, FR-A01; S59; [118][150] | Headless: copilot builds an app from a paragraph, runs it, edits it into a new version |
| FR-073 | A mini app is QMX's packaged, versioned unit: immutable hashed definition, a running instance, and its own data (database, memory file, Parquet, blobs); agents, workflows, screens, schedules and tools are optional parts; it is not an Amp portal | WED | FR-T49, FR-T54, FR-A74, FR-A75; 21 §1 | Changing any file changes the definition hash; the old instance keeps running on its hash |
| FR-074 | Apps exchange data only as typed artifact references; every app is an MCP server the copilot, workflows and external hosts can call | WED | FR-T50, FR-A77, FR-A12; 21-S38 | App B consumes App A's output by reference; no direct app-to-app call exists |
| FR-075 | Each app runs as a laptop subprocess with its own venv, limits and scrubbed environment; Docker and remote sandboxes are opt-in, off by default | WED | FR-A76; C-09; K-06 | A new app runs with no Docker present |
| FR-076 | Apps move Build → Tests → Sandbox → Shadow → Live by risk class with evidence and rollback; editing a live app opens a new version | WED | FR-A78; 21-S45 | An edit to a live app creates a new version at Build, not a hot patch |
| FR-077 | A publish gate refuses an invalid manifest, red tests, money tools or undeclared capabilities; breaker trips notify him; new versions are tested automatically | WED | FR-A44, FR-A82 | Each refusal case returns a named reason |
| FR-078 | The host provides logs, heartbeat, metrics, breaker state, placement and a per-app budget; no app builds its own | WED | FR-A79, FR-A80; 21-S46 | A tripped breaker records why |
| FR-079 | The agent-bearing example apps are rebuilt on QMA v2 as new versions; Macro daily bias is rebuilt live on the Claude engine as the first acceptance run | WED | FR-A86; 24 risk 2; 27 §4 "Copilot app build" | Live operator script: copilot rebuilds Macro daily bias from its paragraph and it passes its road tests |
| FR-080 | Each app records which errand built it and which watch it | NEXT | FR-T51; 21-S51 | App detail API returns builder and watcher errand IDs |
| FR-081 | Agents may write new tools and MCP servers; the code runs as a separate process first and is enabled only after his review | NEXT | FR-A35; K-06 | A new tool stays disabled until an approval record exists |
| FR-082 | Widgets and MCP-app panels are surfaces for apps; screen state is re-read from the app's database | LATER | FR-T53, FR-A81; 21-S36, 21-S37 | (UI) An app panel re-renders from its database after reload |
| FR-083 | A notebook, script or someone else's strategy can be imported and rebuilt as a workflow or app; anything built is shareable as a hashed bundle, no marketplace | LATER | FR-A83, FR-A84 | Bundle export/import round-trips with the same hash |

### 4.9 Sub-agents

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-084 | Sub-agents have their own model, scope and tools, which the parent never overrides, and return artifact references rather than long text | WED | FR-T55, FR-A16, FR-A02; S25; 24 risk 14 | Parent on Opus, sub-agent spec on DeepSeek: the ledger shows DeepSeek for the sub-agent's calls |
| FR-085 | A lead on one provider can run sub-agents on another (for example a GPT research lead with Claude workers) | WED | FR-T56; L[99] | Mixed-provider test run completes with per-agent usage |
| FR-086 | Claude's sub-agent pattern is the reference; OpenAI-engine workers are acceptable | WED | FR-T57; R20§1 "Sub-agents" | Contract tests use one sub-agent spec on both engines |
| FR-087 | Sub-agent defaults are configurable in Settings and per workflow | NEXT | FR-T58; [150] | Per-workflow default overrides the Settings default |
| FR-088 | Sub-agent nesting depth is capped; by default sub-agents do not spawn sub-agents | WED | FR-T59; NFR-T04; [117][q74a] | A sub-agent's spawn attempt is refused at depth 1 |
| FR-089 | Running sub-agents and child errands appear in the event stream and the UI | WED | FR-T60; S35; [89] | Sub-agent start/progress/end events appear on SSE |
| FR-090 | A data-analyst sub-agent (RLM style) works over data with a Python tool on a chosen target; off by default and workflow-only | LATER | FR-A21, FR-T108; 27-S15 | Analyst returns compact results plus an artifact path |

### 4.10 Memory

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-091 | Each engine's default SDK memory is used | WED | FR-T61; S86; [150] | A fact saved in turn 1 is recalled in a resumed session |
| FR-092 | A pluggable memory layer binds per agent, with scopes (task, workflow, session, global); only the primary agent writes automatically; global writes need approval; prompt-bound memory is capped | NEXT | FR-T62, FR-A53, FR-A54, FR-A55; S16; K-10 | Two agents bound to different providers write to different stores |
| FR-093 | Records (backtests, orders, limits, runs) never live in memory; memory only points at them | WED | FR-T64; 21-S53 | Memory store holds references only; record tables are untouched by memory writes |
| FR-094 | He can see and edit what memory holds; policy (prompts, skills, tools) changes only through an approved proposal with rollback | NEXT | FR-T65, FR-A56 | Memory list/edit API works; a policy change without approval is rejected |
| FR-095 | Memory providers are compared side by side before one is chosen; adapters arrive one at a time (never LangMem); retrieval is narrow and keyword-first; archived history is recallable by summary ID | LATER | FR-T63, FR-A57, FR-A58, FR-A26 | Bake-off report exists before any second provider is enabled |

### 4.11 Context, prompts and compaction

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-096 | QMX uses its own short system prompts (about 1.5-3k tokens, XML meta prompts allowed), not Claude Code's coding prompt; how-to lives in skills and tool descriptions | WED | FR-T66, FR-A22; S84; [150][156] | Claude sessions start with the custom prompt and no CLAUDE.md or user settings loaded |
| FR-097 | The static prompt part stays stable, and tools or system prompt never change mid-session, so caching holds | WED | FR-T67; NFR-A12 | Turn 2+ of a Claude session reports cache reads > 0 |
| FR-098 | Compaction is automatic: Anthropic's own on the Claude engine; a summariser with a chosen model on the OpenAI engine; large tool results go to files | WED | FR-T68, FR-A25; S42; [89][150] | An OpenAI-engine session over its window compacts and continues |
| FR-099 | He can switch model mid-conversation: a cost pop-up warns him, compaction runs first if the new window is smaller, and compaction events are visible | NEXT | FR-T70, FR-T71; S62; [123][124] | Switch request returns a cost estimate event before switching |
| FR-100 | About 10-15 tools are visible per agent; the long tail sits behind a tool search | NEXT | FR-A33; NFR-A13 | Agent tool list ≤ 15 entries plus a search tool |
| FR-101 | Long turns show progress updates | NEXT | FR-A115 | A 5-minute turn emits progress events |

### 4.12 Approvals, hooks and the money path

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-102 | No agent can place, size or cancel an order or touch the kill switch; agents may only `propose_order`; the block lives in QMX tool wrappers and holds on both engines over every permission, setting or skill | WED | FR-T72, FR-A40; C-11; 24 risk 5 | On both engines, an order-capable call is refused even with "allow all" set |
| FR-103 | Hooks decide where things are written (for example strategies) and verify the write landed; agents can read and parse data | WED | FR-T73, FR-T113; S39; [89][118] | A strategy write lands in its configured folder; a fault-injected write is reported as failed |
| FR-104 | One approval contract covers both engines (ask, allow once, allow for session, remember); live and parked requests share one queue and survive a restart | WED | FR-T74, FR-A42; 24 risk 4 | A pending approval survives a host restart and is answerable after it |
| FR-105 | He decides the always-ask list; the default is FR-A45's list (Q1) | WED | FR-T76, FR-A45; [8][94] | The list is a Settings row; each listed action produces an approval request |
| FR-106 | Every run, model call, tool call (argument hash, result reference), interrupt and approval is journaled, append-only | WED | FR-A41 | Journal rows exist for each event type in a test run |
| FR-107 | Agents may use demo accounts (and live accounts read-only) for testing under approval, never trading live money | NEXT | FR-T75, FR-A107; L[121] | A demo-account action asks first; a live-account write is refused |
| FR-108 | A short hardline deny-list no setting can relax; unattended runs deny by default; hook decisions resolve deny > defer > ask > allow; gates fail closed, observers fail open | NEXT | FR-A47, FR-A48 | A deny-listed call is refused in an unattended run with "allow all" set |
| FR-109 | Trust guards: a "done/fixed" claim without a verification artifact is labelled unverified; quoted numbers are checked against tool output; review-fix loops stop at 5 rounds; write and money tools run one at a time; a call repeated 3 times is stopped; tool calls from a truncated reply are blocked | NEXT | FR-A49, FR-A50, FR-A51, FR-A52; NFR-A24 | Each guard has a unit test that trips it |

### 4.13 Placement and off-machine runs

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-110 | Workflows run off his machine on rented, on-demand compute from several providers, never one owned box | WED | FR-T77, FR-A91; C-08; [150][159] | A workflow runs on a rented provider with the laptop runner stopped; results are fetched afterwards |
| FR-111 | Every compute provider sits behind one interface (provision, start, status, logs, stop, teardown); a fresh rented machine is prepared by one idempotent setup with a pass/fail verify | WED | FR-A93, FR-A94 (retargeted), FR-T82; K-01 | Setup run twice on one machine: second run is a no-op and verify passes |
| FR-112 | Every job shows where it runs, its status, cost so far and a live log tail | WED | FR-T80, FR-A96; S93 | Job API returns placement, status, cost and log tail |
| FR-113 | Remote results are Git-like: manifest, hashed artifacts, incremental upload of journal/logs/traces/checkpoints, fetch, resume elsewhere, code changes on a `runs/<id>` branch | WED | FR-A92; 27-S26 | Fetch verifies hashes; a tampered artifact is rejected |
| FR-114 | A session or workflow moves from local to remote, uploading what it needs | NEXT | FR-T78; [125][128] | A paused local run resumes on a rented machine |
| FR-115 | Long-running and cron workflows run remotely by design, configurable in the UI | NEXT | FR-T79; [141] | A cron workflow's default placement is remote |
| FR-116 | Buckets hold storage and remote runs; the bucket provider is swappable; app databases are snapshotted with checksums, restore-tested, and kept in three copies | NEXT | FR-T81, FR-A99, FR-A100, FR-A101; NFR-A14 | Restore test passes on every backup |
| FR-117 | Windows-only work (cTrader and MT5 control) stays on his PC | NEXT | FR-T83; [124] | Placement refuses a remote target for a Windows-only tool |
| FR-118 | An agent can ask for a GPU through a job on a rented provider; agents never touch drivers | LATER | FR-A36; 21-S48 | A GPU job request resolves to a provider that offers GPUs |

### 4.14 Observability and DevOps

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-119 | Every run's transcript and logs (what happened, how, why) are exported automatically by the host, locally and remotely | WED | FR-T86, FR-A95; S24; [50][128] | A remote run's transcript and logs exist locally after fetch |
| FR-120 | Both SDKs' traces go into one local store and are never sent to OpenAI | WED | FR-T87; S87; [128][150] | Network capture during an OpenAI-engine run shows no trace upload; local trace file exists |
| FR-121 | A run index records kind, target, resolved model, status, cost, artifacts and the four axes (caching, where, who, how) | WED | FR-A104; S93; NFR-T07 | Every run row has all fields filled |
| FR-122 | A DevOps lens covers agents, workflows and mini apps (health, logs, status) | NEXT | FR-T88, FR-T52; [118][157] | DevOps API returns health per agent, workflow and app |
| FR-123 | A watchdog finds stuck sessions and restarts them | NEXT | FR-T89; [124] | A hung fake session is restarted within the NFR-012 window |
| FR-124 | A post-P16 smoke check proves what still works across QMA, mini apps, QML, QMF and QMN | NEXT | FR-T90; S50; [118] | Smoke suite runs and reports pass/fail per package |
| FR-125 | Each agent spec has a small golden eval set; traces and evals feed an improvement loop, including weekly tool-description improvements | LATER | FR-A28, FR-T107, FR-A39 | Eval set runs in CI on the fake engine |

### 4.15 UI contract and events

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-126 | Both engines emit one event stream: text, tool calls, sub-agents, approvals, usage, computer-use cursor | WED | FR-T91, FR-A10; S35; [89][122] | Same scripted turn on both engines yields the same event types |
| FR-127 | Sessions are shown like this Claude Code session: previous and running sessions, what is running, raw logs hidden by default | WED | FR-T92; [89] | Sessions API returns running and past sessions with status |
| FR-128 | One service has two doors (REST + SSE for the UI, MCP for the copilot) with identical results; the copilot has no back doors | WED | FR-A112, FR-A01; 21-S21 | The same operation via REST and MCP returns identical results |
| FR-129 | Unbuilt features return an honest `not_implemented`, never a fake success | WED | FR-A113 | Calling an unbuilt route returns `not_implemented` |
| FR-130 | UI updates are pushed over SSE, never polled; token deltas go on an unstored channel, whole blocks go to the log | WED | FR-A117; 24 risk 6 | A 1,000-token reply writes one block row, not 1,000 |
| FR-131 | Agents editing the same files work on git branches; both versions are kept and rendered side by side as variants | NEXT | FR-T93, FR-T102; S72; L[124q] | Two agents on one file produce two branches and a variant pair |

### 4.16 Tools and reach

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-132 | Agents know QML, QMB, QMF and the Library exist through a capability registry of task-shaped tools; the Library and QMB seams are named in code and docs | WED | FR-T112, FR-T118, FR-A30, FR-A103; S58 | Registry lists each seam; a Library call goes through the named seam module only |
| FR-133 | Every agent gets the Claude Code baseline: shell, Python, files, web, CLI tools, video watching | WED | FR-T114; S38; [89] | Baseline tool set present on both engines (QMX-wrapped on the OpenAI side) |
| FR-134 | Tools follow one design (plain description, typed args, concise/detailed output, pagination, fix-it errors, large output as artifact); tool kinds sit on a per-agent allow-list; he adds MCP servers in Settings | WED | FR-A31, FR-A32, FR-A34; S36 | Tool lint passes on all registered tools |
| FR-135 | Research tools: Firecrawl with Alexandria (opt-in, paid); the MQL5 article scraper app keeps running | NEXT | FR-T115, FR-A87, FR-A88; S45 | Firecrawl tool runs when enabled; the scraper's daily job runs |
| FR-136 | Agents get QMX-owned browser use, including logged-in sessions (for example TradingView) | NEXT | FR-T98, FR-A37; S34 | Browser tool reads a page in a persistent profile |
| FR-137 | Agents get QMX-owned computer use (OpenCUA/cua-driver class) that does not take his mouse | NEXT | FR-T99, FR-A37; S34 | A background click test completes while the cursor stays put |
| FR-138 | Broker tools (many brokers, connections, accounts; cTrader for CFDs, CCXT for crypto) offer read plus `propose_order` only, in the Portfolio plugin | NEXT | FR-A11, FR-A106; 27-S20, 27-S21 | Portfolio plugin lists broker read tools and no order tool |
| FR-139 | Agents operate cTrader and MT5 inside QMX (demo first), including "watch a video, then try it in cTrader" | LATER | FR-T100, FR-T101; S19, S44 | Ticket 12 spike passes on a demo account |
| FR-140 | Agents get news and crypto data tools (cTrader news, CCXT) | LATER | FR-T116; S06 | News tool returns items for a symbol |

### 4.17 Concurrency and self-improvement

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-141 | Concurrent Claude sessions (about 1 GB each) are capped by RAM; over the cap, a new one is refused with an error card | WED | FR-T103; S65; [123][156] | Starting cap+1 Claude sessions returns a refusal for the last one |
| FR-142 | "Ways of doing things" and mistakes are saved so agents don't repeat them; lessons reach skills only with his approval and undo | NEXT | FR-T105, FR-T106; S43 | A lesson stays a proposal until approved; undo restores the prior skill version |
| FR-143 | Two agents never edit the same Library item at once (seam only) | LATER | FR-T104; [118] | Seam contract documents the lock call |

### 4.18 Shipping, documents and platform

| ID | Requirement | Pri | Traces | Acceptance check |
|---|---|---|---|---|
| FR-144 | QMA v2 ships through integration → staging → main; main moves only by his click; no code lands on main directly | WED | FR-T109, NFR-A25; C-12 | Branch protection: no agent push to `main` or `staging` |
| FR-145 | Junk branches and worktrees are cleaned with his go per deletion; superseded documents are archived with a stamp, never deleted | NEXT | FR-T110, FR-T111; S82, S83 | Archive folder holds stamped files; deletion log lists his go per branch |
| FR-146 | The database is refactored to be usable by agents | NEXT | FR-T117; S71; [125] | Architecture names the agent-facing data API |
| FR-147 | Voice/conversational mode and GPT audio and image | LATER | FR-T119; S74 | — |
| FR-148 | A week-long paper soak runs with a separate monitoring agent on a pinned version | LATER | FR-A108; 27-S43 | Soak report exists |

**Count:** 148 FRs. WED 81 · NEXT 54 · LATER 13.

---

## 5. Non-functional requirements

| ID | Area | Requirement and target | Traces |
|---|---|---|---|
| NFR-001 | Cost | Zero API spend for Claude or Codex: $0 billed on Anthropic or OpenAI API keys for Claude/GPT models, checked monthly | NFR-T01, NFR-T03, NFR-A01; C-04 |
| NFR-002 | Cost | Every other provider runs on its own key; no cap on the number of providers | NFR-T02; C-03 |
| NFR-003 | Cost | Sub-agents are few and background-only; none pauses mid-run longer than the ~10 min cache life; default depth 1 | NFR-T04; [1][q74a][78] |
| NFR-004 | Caching | Caching is the top priority: stable prefix, one account per session. Target: cache reads ≥ 70% of input tokens from turn 3 of a Claude copilot session [ASSUMPTION] | NFR-T05, NFR-A12; [50][157] |
| NFR-005 | Caching | Cache reads and writes are recorded per call and savings shown; 100% of calls carry cache fields when the provider reports them | NFR-T06 |
| NFR-006 | Caching | The four axes (caching, where, who, how) are recorded for 100% of runs | NFR-T07; S93 |
| NFR-007 | Performance | About 40 concurrent agents on his PC (95th percentile load). OpenAI-engine agents run in-process. Claude sessions are capped by RAM: cap = (free RAM − 4 GB reserve) ÷ 1 GB, default 6 [ASSUMPTION] | NFR-T08, NFR-T09; S56 |
| NFR-008 | Performance | No Docker or heavy sandbox needed by default | NFR-T10; C-09 |
| NFR-009 | Storage | Data stays in files (SQLite, DuckDB over Parquet, JSONL, blobs), one writer per file, no database server; SQLite write limits are measured at 40-agent load before it is reached | NFR-T11, NFR-A15; FR-A98 |
| NFR-010 | Reliability | Crash-resumable: after a hard kill, no completed node is lost; runs resume within 60 s of restart [ASSUMPTION], including days later or on another machine | NFR-T12, NFR-A10 |
| NFR-011 | Reliability | Retries, timeouts and parallel joins are designed in from the start | NFR-T13; R20§3.4 |
| NFR-012 | Reliability | The watchdog detects a stuck headless session within 5 minutes [ASSUMPTION] | NFR-T14 |
| NFR-013 | Observability | Every run is explainable afterwards from local transcript, logs and traces; recording is done by the host, never by agent goodwill | NFR-T16, NFR-A11 |
| NFR-014 | Observability | The DevOps lens gets equal weight with features | NFR-T17 |
| NFR-015 | Security | Money-path rules live in code, never in a skill or prompt; no setting, skill or hook can relax them | NFR-T18, NFR-A09 |
| NFR-016 | Security | Zero secrets in logs, journal, chat, repo, `.env` or backups, checked by a secret scan in CI | NFR-T19, NFR-A07; C-15 |
| NFR-017 | Security | Downloaded content (videos, news, pages) is untrusted input; readers of it get no write privileges | NFR-T20 |
| NFR-018 | Configurability | Every knob is editable in the UI with a sensible default (Lego); target 100% of Settings keys reachable from the UI | NFR-T21, NFR-A02; FR-A116; C-16 |
| NFR-019 | Extensibility | Providers, models, plugins, seats and templates are added or removed as data; a new model is a config row | NFR-T22, NFR-T23 |
| NFR-020 | Extensibility | One QMX contract with two engine implementations (OOP-style); engine hooks only report, policy lives in QMX tool wrappers | NFR-T24; 19 §11 |
| NFR-021 | Pluggability | Memory, compute providers, buckets, tools and plugins are swappable without code changes | NFR-T25, NFR-A18 |
| NFR-022 | Portability | Runs on Windows (his PC) and Linux (rented compute); differences are documented; Linux-only tools are remote-only | NFR-T26, NFR-A19; S70 |
| NFR-023 | Legibility | Everything he reads is plain and short; one word per thing (§6) | NFR-T27, NFR-A21 |
| NFR-024 | Legibility | Agents never ask before he has read; they answer research-shaped questions themselves; they ask only real decisions, with a recommendation; they give opinions, not agreement | NFR-T28, NFR-T29 |
| NFR-025 | Process | Structured method: small work packets with "done when" tests, one PR each, independent verification per PR, no ceremony, no vibe coding | NFR-T30, NFR-A05; FR-A123 |
| NFR-026 | Process | Design for complexity: the 30-item complexity list (21 §4) is addressed by the architecture, item by item | NFR-T31; S46 |
| NFR-027 | Testability | The backend is tested without the UI; automated tests use fake engines for both SDKs (ready before the first engine PR); live calls are operator-run scripts; thresholds are never lowered | NFR-T32, NFR-A08; 24 risk 15 |
| NFR-028 | Process | Docs first: library APIs come from official docs, never guessed; research reads primary sources | NFR-T33, NFR-A06 |
| NFR-029 | Maintainability | Adopt before build; YAGNI; one job per module; no abstraction without two callers; files about 400 lines or less | NFR-A03, NFR-A04 |
| NFR-030 | Durability | Never the only backup on the machine it protects; every backup restore-tested; research and decisions live in the repo | NFR-A14, NFR-T15 |
| NFR-031 | Reproducibility | Definitions, run manifests and result-memo keys are content-hashed | NFR-A16 |
| NFR-032 | Responsiveness | Long work never blocks the chat; first streamed event within 2 s of a message on a warm session [ASSUMPTION] | NFR-A17 |
| NFR-033 | Autonomy | Unattended means no questions: pick the option most consistent with the design and record the assumption | NFR-A20 |
| NFR-034 | Machine limits | Heavy local runs are serialised; bulk data and temp files stay off the nearly full C: drive | NFR-A22 |
| NFR-035 | Safety of change | Code is removed only after a caller audit within a stated blast radius; the quant core (QMF, QML, QMB, QMN, MIS) is untouched | NFR-A23 |
| NFR-036 | Trust | 0 unverified "done" claims shown as verified; quoted numbers trace to tool output | NFR-A24 |
| NFR-037 | Caching | Caching lives in five places only: upstream data, backtest memo, provider prompt caching, TTL on expensive read tools, UI aggregates over SSE; no Redis | FR-A102 |
| NFR-038 | Lean context | System prompt ~1.5-3k tokens; ~10-15 visible tools; a small visible skill list | NFR-A13 |
| NFR-039 | UI | Every requirement considers the UI; the UI ships first as a browser app | FR-T94; S48 |

---

## 6. Mental models and glossary

His words, defined his way. This replaces `tracker/agent-system/glossary.md` (K-03). Use these words exactly.

| Word | Means | Don't say |
|---|---|---|
| **QMA v2** | "Quant agents", version 2: QMX's rebuilt agent system [147][150] | "QMA runtime" (the retired one) |
| **Copilot** | An agent he chats with. One **general copilot** (like Claude Code or Codex) plus specialised ones | "assistant", "desk" |
| **Organogram** | The org chart of copilots: general, Lab, Portfolio, one per mini app; any one can host any conversation [15][141] | |
| **Seat** | One position in the organogram, filled by loading a plugin | |
| **Plugin** | Tools/MCP + skills + a model + hooks. A session loads one by default. The organogram's unit [123][150] | "extension", "desk pack" |
| **Skill** | A folder of how-to an agent loads on demand. Skills replace modes | "mode" |
| **Hook** | An always-on rule that fires around tool calls and events (where files go, what is refused) | |
| **Engine** | What runs an agent's loop. Two: the **Claude engine** and the **OpenAI engine**, behind one `Engine` contract | "harness" in his texts |
| **Claude Agent SDK** | The library the Claude engine uses for Claude Code's capabilities on his plan | "Claude Code CLI" (never used), "Agent SDK" alone |
| **OpenAI Agents SDK** | The library the OpenAI engine uses, in-process, for GPT (via SIWC) and every key-based provider | "Codex" |
| **SIWC** | "Sign in with ChatGPT": how GPT runs on his ChatGPT plan | |
| **Lane** | Plain word for how a model is paid: the **subscription lane** (Claude, GPT) or the **key lane** (everything else) | "QMX engine" (retired LangGraph meaning) |
| **Wire format / API compatibility** | Every provider copies Anthropic's or OpenAI's format, so a provider is a base URL plus a key [125][128] | |
| **Provider / account / pool** | Provider = a vendor endpoint. Account = one login or key, a row. Pool = a reseller of many models (OpenRouter, Ollama Cloud, OpenCode) | |
| **Router** | The usage balancer: picks the account and model per session (never per request) by capability, then usage left. Replaces CLIProxy [74][141] | "load balancer per request" |
| **Orchestrator** | A strong Claude model in a long, resumed session that picks models from router data and delegates [141] | |
| **Sub-agent** | A helper an agent starts for a bounded job, with its own model, scope and tools | |
| **Delegate** | The cross-engine call: a Claude agent hands work to an OpenAI-engine agent, or the reverse | |
| **Session** | One conversation with an engine, resumable by ID | |
| **Errand** | His long-running piece of work and its conversation; it connects everything it builds [17] | "project", "mission" |
| **Turn host** | The backend part that takes a message, runs the agent and streams the reply | |
| **Harness / loop / graph** | Harness = the environment. Loop = a feedback cycle with a stop rule. Graph = the flow. A loop is one node in a graph [145][157] | |
| **Workflow** | A saved graph of steps (code, agent, app call, human gate); deterministic, agentic or mixed | "pipeline" |
| **Dynamic workflow** | A workflow the copilot writes on the fly, then saves as a graph | |
| **Template** | A ready-made workflow to start from (for example "fan-out and synthesize") | |
| **Mini app** | QMX's packaged, versioned unit: definition + instance + own data, with optional agents, workflows, screens, schedules and tools. ML-level complexity. Not an Amp portal | "extension" (retired), "portal" |
| **Widget** | One view inside a mini app or the Lab | |
| **Capability** | An operation QMX can call; the copilot reads them from a registry | |
| **Lab / Portfolio / Home** | Surfaces. The Lab is about 80% of the platform [17]. Portfolio covers risk, sizing, optimisation; PM means Portfolio Manager | |
| **Approval** | His yes/no on an action; one queue whatever the engine | |
| **Money path** | Anything that places, sizes or cancels orders or touches the kill switch. Agents only propose | |
| **Placement** | Where a job runs: his PC or rented compute | "the server" |
| **Rented compute** | On-demand machines paid by the minute from several providers; never an owned box [159] | "Contabo", "orb" |
| **Bucket** | Remote storage for runs and backups | |
| **Run record** | The automatic record of a run: transcript, logs, traces, cost, four axes | |
| **Four axes** | For every run: caching; where it runs; who runs it (provider); how (graph or loop) [157] | |
| **Records / memory / policy** | Records = facts (backtests, orders, runs). Memory = what agents remember, pointing at records. Policy = prompts, skills, tools, changed only with approval | |
| **Variant** | Two versions of the same file from two agents, kept side by side | |
| **Lego** | Everything has a default and can be added, removed or edited in the UI | |
| **Engine in an engine** | His warning: running a full harness (Claude Code) inside QMX untouched couples two engines; QMX must own the configuration [86][118] | |
| **Baseline** | What Claude Code can do out of the box is the floor for every QMX agent [89] | |
| **Design for complexity** | Build for load before it arrives, and surface what he would not think of | |
| **Wednesday minimum** | The five things that must work by 2026-10-14 (C-14) | |
| **Library, QMB, QML, QMF** | Out-of-scope neighbours reached through named seams. QMF's role is unclear to him (Q8) | |

---

## 7. The port list: LangChain-era features to carry onto the two SDKs

From 27 §4. "Neutral" means QMX logic that only needs re-binding.

| Feature (27 §4) | What it does | Under QMA v2 | PRD FRs |
|---|---|---|---|
| Copilot | Main agent; builds and runs apps and workflows over `qmx-control`; streams typed blocks | Claude-engine session on his plan, custom prompt, plugin per surface; block stream and MCP door stay | FR-001, FR-002, FR-013, FR-126, FR-128 |
| AgentSpec | YAML for model, tools, MCP, skills, memory, sub-agents, approvals, budget | Kept as the engine-neutral spec, one builder per engine | FR-028 |
| Sub-agents (sync) | Quick isolated jobs returning artifact refs | Claude native sub-agents; OpenAI `as_tool`/handoffs | FR-084-FR-088 |
| Background tasks | `start_task`/`check_task`/`cancel_task`/`list_tasks` | Kept as QMX tools in both engines; the run inside is an engine session | FR-015 |
| Workflow as sub-agent | Agent delegates to a compiled workflow | `run_workflow` tool over the QMX runner | FR-062 |
| Code-driven fan-out | Bulk coverage by code | Graph `parallel` nodes and fan-out templates, capped | FR-061, FR-066 |
| Data analyst (RLM) | Python sub-agent over app data | Python tool on a chosen target; off by default | FR-090 |
| Model router (P06) | Tiers, chain, fallback, CLIProxy client | Chain survives; router balances per session; CLIProxy gone | FR-026, FR-029, FR-038-FR-045 |
| Memory (P07) | Built-in + one provider; 4 scopes; write rules | SDK default memory under QMX's pluggable layer | FR-091-FR-095 |
| Context/compaction | Summariser, offload, pre-compaction memory save | Claude native; OpenAI summariser; offload kept | FR-098, FR-099, FR-077 |
| Guards (P08) | Journal, admission, money path, call caps | Rules move into QMX tool wrappers on both engines | FR-102, FR-104, FR-106, FR-051 |
| Hooks (P20) | Publish gate, breaker, auto-test, pre-compaction | Claude hooks / OpenAI guardrails + wrappers; app events from the supervisor | FR-077, FR-078, FR-103, FR-108 |
| Approvals | `interrupt_on`, human gates, admission | One QMX approval queue over live (Claude) and parked (OpenAI) requests | FR-058, FR-104, FR-105 |
| Prompt caching | Automatic for Claude; proxy affinity | Claude SDK automatic; OpenAI `prompt_cache_options`; no mid-session swaps | FR-097, NFR-004 |
| Workflows (P10) | JSON graph → LangGraph with SQLite checkpoints | `workflow.v1` kept; QMX runner replaces the compiler | FR-052-FR-061 |
| Research (P19) | MQL5 scraper app, Firecrawl MCP | Unchanged; MCP list moves into the researcher's plugin | FR-135 |
| Remote runs (P21) | ComputeProvider, Git-style results | Kept, retargeted to rented providers; resume = engine resume + graph checkpoint | FR-110-FR-114 |
| Copilot app build (P15) | Builds Macro daily bias from a paragraph | First live QMA v2 acceptance run | FR-079, FR-072 |
| Skills | Placeholder skill folders | Shipped inside plugins; OpenAI loader | FR-030, FR-035-FR-037 |
| Artifacts | Results as references; artifact index | Unchanged; Library stays a seam | FR-010, FR-074, FR-132 |
| Session/thread store | LangGraph checkpoints + block log | Claude session resume by ID; OpenAI `Session` with QMX backend; QMX keeps its block log | FR-014, FR-016, FR-127 |
| Tracing | LangSmith or local OTel | SDK tracing, stored locally, never sent to OpenAI | FR-120 |
| MCP client/servers | `MCPAdapter`, FastMCP servers | Both SDKs speak MCP; FastMCP servers stay | FR-128, FR-134 |
| Plugins | Seed only ("skills + hooks + tools") | The organogram unit | FR-030, FR-031 |

---

## 8. Priority by repetition

The ideas he repeated most (26 §6 counts plus 27 §7 counts, merged), and the FRs that serve them.

| Idea | Times | Serving FRs |
|---|---|---|
| Organogram: copilots per surface, enhance it | 10 + 3 | FR-002-FR-005, FR-007, FR-030, FR-031 |
| Off-machine runs, laptop off | 8 + 5 | FR-110-FR-115 |
| Router, load balancing, several accounts | 8 + 4 | FR-038-FR-045 |
| The copilot builds, controls and edits workflows and mini apps | 4 + 6 | FR-056, FR-064, FR-072, FR-035 |
| Graph and loop engineering | 7 | FR-052, FR-063, FR-066 |
| Don't reinvent; copy known patterns | 6+ | FR-066, NFR-028, NFR-029 |
| Stop vibe coding; structure | 6 | NFR-025 |
| Design for complexity | 6 | NFR-026, FR-061, FR-060 |
| Logs, transcripts, DevOps lens, automatic recording | 6 + 3 | FR-119-FR-124, NFR-013 |
| Library is a database / out of scope | 6 | FR-132, FR-143 |
| Never pay API for Claude/Codex; subscriptions | 5 + 4 | FR-022, FR-023, NFR-001 |
| Caching is critical | 5 + 3 | FR-097, NFR-004, NFR-005, NFR-037 |
| Pluggable memory (Hermes) | 3 + 5 | FR-091-FR-095 |
| Sub-agents with own model and scope | 5 + 4 | FR-084-FR-088 |
| Sub-agent cost rules (few, no nesting) | 5 | FR-088, NFR-003 |
| Compaction, automatic | 5 | FR-098, FR-099 |
| No Claude Code CLI / engine in an engine; one word per thing | 5 + 5 | FR-021, FR-032, NFR-023 |
| Consider the UI in everything | 5 | NFR-039, FR-126-FR-131 |
| Working QMX by Wednesday | 5 | §1.3 SC-1-SC-6 |
| Storage buckets, not everything on the laptop | 5 | FR-116, FR-113 |
| Workflows agentic / non-agentic / mixed | 4 | FR-053, FR-054 |
| Self-improvement (Hermes) | 4 | FR-142, FR-037 |
| Computer use, cTrader, MT5 | 4 | FR-137, FR-139 |
| System prompts, context engineering | 4 | FR-096, FR-097 |
| Skills and hooks instead of hard-coded behaviour | 4 | FR-006, FR-035, FR-103 |
| Models configurable, not set in stone | 3 | FR-026, FR-027, FR-047 |
| Tools for agents are a big gap | 3 | FR-133, FR-134 |

---

## 9. Questions

### 9.1 Owed to the operator (his to answer; at most 8)

Each has a recommended answer, so a one-word reply settles it.

| # | Question | Recommended answer | Sources | Blocks |
|---|---|---|---|---|
| Q1 | Which actions must always ask you first? | Publish, install or grant, schedule, spend over budget, any demo/paper-account action, delete. Everything else runs, and unattended runs get their authority at launch | 26 §7 #9; 27 §9 #2; FR-T76 | FR-105 (WED) |
| Q2 | What is the one rule every copilot must never forget about how you work? | "Answer research questions yourself; ask me only real decisions, with a recommendation, after I've read" | 26 §7 #10; 27 §9 #4 | FR-012 |
| Q3 | Effort/thinking: a dial next to the chat box, or automatic? | Automatic per role default, with an optional per-chat override in the box | 26 §7 #9, #11; 27 §9 #3 | FR-045 |
| Q4 | Is the general copilot one window over every surface's sessions, with Lab and Portfolio as plugins it can load (rather than separate agents)? | Yes: one front door; it lists all sessions; Lab and Portfolio are plugins; only the general copilot edits apps | 26 §7 #29; 27 §9 #6, #7; 21 Q4 | FR-002-FR-004, FR-008 |
| Q5 | If Sign in with ChatGPT cannot drive QMX's OpenAI engine (or not on rented machines), what happens to GPT? | GPT is marked "unavailable" and its roles go to Claude or a key provider; no paid OpenAI API | 26 §7 #27; FR-T13 | FR-023 (WED) |
| Q6 | Which broker accounts may agents touch for testing? | Demo accounts, under approval; live accounts read-only; never an order | FR-T75; L[121] | FR-107 |
| Q7 | Branches: fold `rebuild/base` into `integration`, create `staging` from it, then delete the junk branches you approve one by one? | **ANSWERED 2026-10-12 21:00:** not now. `integration` isn't set up to take code. QMA v2 ships into `rebuild/base`; setting up integration and staging is later work | 26 §7 #28; R20§3 open points | FR-144, FR-145 (WED) |
| Q8 | Two names only you know: the Library's real name ("starts with A"?), and QMF's role | Keep "Library" until its refactor; treat QMF as a tool seam until its own sitting | 26 §7 #22, #23 | FR-132 |

### 9.2 For the architecture to answer (Claude's to decide)

| # | Question | Sources |
|---|---|---|
| A-01 | Is SIWC usable from the OpenAI Agents SDK (Responses only, `store:false`, `stream:true`), and on rented machines ("self-hosted VMs")? | 26 §7 #27; subscription-terms notes |
| A-02 | Is the Claude plan sign-in allowed on a headless rented Linux box? If not, which work stays on his PC? | 24 risk 10 |
| A-03 | Parity table: what one SDK has and the other gets rebuilt (approvals, hooks, plugins, compaction) | 26 §7 #18; 19 §10 |
| A-04 | Compaction on each engine, thinking modes on a model switch, and how Pi and Hermes combine both formats | 26 §7 #6, #11, #19 |
| A-05 | System-prompt architecture (XML meta prompts, static/dynamic split, versioning) | 26 §7 #21; 27 §9 #11; 22 §4 |
| A-06 | Vocabulary: do "graph" and "loop" replace "workflow" and "sub-agent" in the UI? | 26 §7 #24; [159] |
| A-07 | How the router lives inside graphs and loops (per node, per sub-agent spawn) | 26 §7 #25 |
| A-08 | Final node-kind list (P10's ten, triggers, a command node with live logs) | 21 Q3, Q16; K-17 |
| A-09 | Where workflow definitions are stored while the Library is out of scope | 24 risk 11 |
| A-10 | RLM: needed, when, copilot or workflow only | 26 §7 #5; 27 §9 #9 |
| A-11 | QMX-owned browser and computer use: OpenCUA vs cua-driver, MCP or native | 26 §7 #3; 27 §9 #12 |
| A-12 | Orchestrator lifetime: one resumed session vs rolling at phase ends (K-09); how a Claude driver runs cheaply | 26 FR-T44; 22 §5 |
| A-13 | MCP apps and how plugins and MCP servers are accepted | 26 §7 #12, #13; 27 §9 #20 |
| A-14 | Windows vs Linux code differences for agents | 26 §7 #14 |
| A-15 | Database refactor for agents; SQLite at 40 agents; two control planes (laptop and remote) shown as one | 26 §7 #15; 24 risk 16; NFR-009 |
| A-16 | Agent as a folder vs plugin layout; which model goes where by default (on subscriptions and keys) | 26 §7 #1, #2 |
| A-17 | Long agent calls inside apps vs the 20-second app tool timeout | 24 risk 12 |
| A-18 | Import cycle (qmx-control ↔ qmx-apps ↔ qmx-agents) broken before the engine package lands | 24 risk 1 |
| A-19 | Token deltas vs the closed block list and the 50 ms SSE poll | 24 risks 6-7 |
| A-20 | Terms check: several accounts of one vendor rotated per session | FR-T32; models-routing |
| A-21 | Attachments; the node editor against what P10 built; the Experimentation Board as a backend object | 27 §9 #8, #10; 21 Q2 |
| A-22 | How large companies handle tools and database connections (answer for him in plain words) | 26 §7 #8 |
| A-23 | Did the Lab's complexity belong in mini apps? (answer as a design note) | 26 §7 #16 |
| A-24 | CI fakes for both SDKs, and GitHub Actions that never ran any check | 24 risk 15; 27 §9 #5 |

---

## 10. Traceability appendix

Every FR-T (file 26) and FR-A (file 27) ID, mapped to its PRD FR, or marked dropped with a reason. NFR mappings follow.

### 10.1 FR-T → PRD

| FR-T → PRD | FR-T → PRD | FR-T → PRD | FR-T → PRD | FR-T → PRD | FR-T → PRD |
|---|---|---|---|---|---|
| T01 → 001 | T02 → 002 | T03 → 003 | T04 → 005 | T05 → 030 | T06 → 014 |
| T07 → 006 | T08 → 007 | T09 → 012 | T10 → 020 | T11 → 021 | T12 → 022 |
| T13 → 023 | T14 → 024 | T15 → 025 | T16 → 026 | T17 → 027 | T18 → 021 |
| T19 → 013 | T20 → 030 | T21 → 031 | T22 → 032 | T23 → 033 | T24 → 034 |
| T25 → 036 | T26 → 038 | T27 → 039 | T28 → 040 | T29 → 041 | T30 → 042 |
| T31 → 043 | T32 → 044 | T33 → 045 | T34 → 046 | T35 → 047 | T36 → 052 |
| T37 → 053 | T38 → 054 | T39 → 055 | T40 → 056 | T41 → 063 | T42 → 064 |
| T43 → 059 | T44 → 065 | T45 → 066 | T46 → 067 | T47 → 069 | T48 → 072 |
| T49 → 073 | T50 → 074 | T51 → 080 | T52 → 122 | T53 → 082 | T54 → 073 |
| T55 → 084 | T56 → 085 | T57 → 086 | T58 → 087 | T59 → 088 | T60 → 089 |
| T61 → 091 | T62 → 092 | T63 → 095 | T64 → 093 | T65 → 094 | T66 → 096 |
| T67 → 097 | T68 → 098 | T69 → 016 | T70 → 099 | T71 → 099 | T72 → 102 |
| T73 → 103 | T74 → 104 | T75 → 107 | T76 → 105 | T77 → 110 | T78 → 114 |
| T79 → 115 | T80 → 112 | T81 → 116 | T82 → 111 | T83 → 117 | T84 → 070 |
| T85 → 071 | T86 → 119 | T87 → 120 | T88 → 122 | T89 → 123 | T90 → 124 |
| T91 → 126 | T92 → 127 | T93 → 131 | T94 → NFR-039 | T95 → 050 | T96 → 048 |
| T97 → 049 | T98 → 136 | T99 → 137 | T100 → 139 | T101 → 139 | T102 → 131 |
| T103 → 141 | T104 → 143 | T105 → 142 | T106 → 142 | T107 → 125 | T108 → 090 |
| T109 → 144 | T110 → 145 | T111 → 145 | T112 → 132 | T113 → 103 | T114 → 133 |
| T115 → 135 | T116 → 140 | T117 → 146 | T118 → 132 | T119 → 147 | |

All 119 FR-T IDs mapped; none dropped. (T54, "keep the seeds file as input", is satisfied by FR-073 and NFR-026.)

### 10.2 FR-A → PRD

| FR-A → PRD | FR-A → PRD | FR-A → PRD | FR-A → PRD | FR-A → PRD | FR-A → PRD |
|---|---|---|---|---|---|
| A01 → 056, 072, 128 | A02 → 084 | A03 → 062 | A04 → 015 | A05 → 033 | A06 → 001, 006 |
| A07 → 002 | A08 → 004 | A09 → 008 | A10 → 126 | A11 → 138 | A12 → 074 |
| A13 → 009 | A14 → 028 | A15 → 063 (superseded part, K-07) | A16 → 084 | A17 → 026 | A18 → 029 |
| A19 → 022, 023 (proxy superseded) | A20 → 050 | A21 → 090 | A22 → 096 | A23 → 063 | A24 → 063 |
| A25 → 098 | A26 → 095 | A27 → 061 | A28 → 125 | A29 → 018 | A30 → 132 |
| A31 → 134 | A32 → 134 | A33 → 100 | A34 → 134 | A35 → 081 | A36 → 118 |
| A37 → 136, 137 | A38 → 011 | A39 → 125 | A40 → 102 | A41 → 106 | A42 → 104 |
| A43 → 051 | A44 → 077 | A45 → 105 | A46 → 046 | A47 → 108 | A48 → 108 |
| A49 → 109 | A50 → 109 | A51 → 109 | A52 → 109 | A53 → 092 | A54 → 092 |
| A55 → 092 | A56 → 094 | A57 → 095 | A58 → 095 | A59 → 014 | A60 → 017 |
| A61 → 018 | A62 → 019 | A63 → dropped | A64 → 052 | A65 → 053 | A66 → 057 |
| A67 → 058 | A68 → 071 | A69 → 068 | A70 → 061 | A71 → 062 | A72 → 071 |
| A73 → 062 | A74 → 073 | A75 → 073 | A76 → 075 | A77 → 074 | A78 → 076 |
| A79 → 078 | A80 → 078 | A81 → 082 | A82 → 077 | A83 → 083 | A84 → 083 |
| A85 → dropped | A86 → 079 | A87 → 135 | A88 → 135 | A89 → 066 | A90 → 066 |
| A91 → 110 | A92 → 113 | A93 → 111 | A94 → 111 (retargeted, K-01) | A95 → 119 | A96 → 112 |
| A97 → 046 | A98 → NFR-009 | A99 → 116 | A100 → 116 | A101 → 116 | A102 → NFR-037 |
| A103 → 132 (seam) | A104 → 121 | A105 → dropped | A106 → 138 | A107 → 107 | A108 → 148 |
| A109 → 048 | A110 → 039 | A111 → 039 | A112 → 128 | A113 → 129 | A114 → 010 |
| A115 → 101 | A116 → NFR-018 | A117 → 130 | A118 → dropped | A119 → 035 | A120 → 036 |
| A121 → 037 | A122 → 036 | A123 → NFR-025 | | | |

**Dropped FR-A IDs and why**
- **FR-A63** (stance per task: do it / pair / coach): it sat inside the withdrawn modes section (K-13); a skill can offer it later.
- **FR-A85** (trading node as a headless app with live permissions): QMN/node-docs territory and the money path, outside QMA v2 (K-18).
- **FR-A105** (trained models stored as Library items): the Library is out of scope; it returns with the Library refactor.
- **FR-A118** (bars and indicators for TradingView Lightweight Charts): a UI and market-data lane item, not part of the agent system.

### 10.3 NFR-T and NFR-A → PRD

- **NFR-T:** T01→NFR-001 · T02→002 · T03→001 · T04→003 · T05→004 · T06→005 · T07→006 · T08→007 · T09→007 · T10→008 · T11→009 · T12→010 · T13→011 · T14→012 · T15→030 · T16→013 · T17→014 · T18→015 · T19→016 · T20→017 · T21→018 · T22→019 · T23→019 · T24→020 · T25→021 · T26→022 · T27→023 · T28→024 · T29→024 · T30→025 · T31→026 · T32→027 · T33→028.
- **NFR-A:** A01→NFR-001 · A02→018 · A03→029 · A04→029 · A05→025 · A06→028 · A07→016 · A08→027 · A09→015 · A10→010 · A11→013 · A12→004 (and FR-097) · A13→038 · A14→030 · A15→009 · A16→031 · A17→032 · A18→021 · A19→022 · A20→033 · A21→023 · A22→034 · A23→035 · A24→036 · A25→FR-144.

---

## 11. Assumptions index

- §5 NFR-004: the 70% cache-read target from turn 3 is Claude's number; he set "caching is the top priority" but no figure.
- §5 NFR-007: the Claude-session cap formula (4 GB reserve, 1 GB per session, default 6) is inferred from the ~1 GB per session guidance (19 §11); measure on his PC before ratifying.
- §5 NFR-010: the 60-second resume target is Claude's number.
- §5 NFR-012: the 5-minute stuck-session window is Claude's number.
- §5 NFR-032: the 2-second first-event target is Claude's number.
- §4.4 FR-035: the third default skill (maintain-app) is inferred from "maintain" in the Wednesday minimum.
- §9.1: every "recommended answer" is Claude's recommendation, not his decision.
