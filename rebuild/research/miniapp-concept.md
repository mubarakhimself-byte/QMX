# Mini app concept — recovered from the original ideation transcripts

Built 2026-10-07. Read-only archaeology. Nothing here is a ruling. Where a point is my inference, it is marked **(inf)**.

Sources and citation keys:
- **N:Lnnn** = `scratchpad/node-editor/Explore-Node-Editor-Architecture.md` (ChatGPT, 2026-09-17/18, 1906 lines, read in full). Operator turns are single very long lines: L7, L198, L313-321, L429, L593-595, L720-724, L884-890, L1058-1070, L1245, L1373, L1446, L1646, L1791. Every other line is ChatGPT.
- **IMG** = `node-editor/images/image-001.png` (operator-attached at N:L1056).
- **A:Lnnn** = `Downloads/Design-Extensible-Agents (1).md` (ChatGPT, 2026-08-22/28, 5083 lines, read in full). Operator turns: L7, L999, L1896, L3011, L3963-3976, L4954, L5071.
- **LC / LV** = `ledger-chat.md` (Aurelius chat, M###) / `ledger-voice.md` (calls, R-###).
- **Repo** = `C:\Users\Mubarak\Desktop\QMX\docs\...`. **MA** = Aurelius ladder in `scratchpad/src2dfa/release/` (MA01-MA04 contracts, `CAPABILITY-STATUS.md`).
- `architecture-mimi0apps/` exists in the repo but is **empty**.

Weight rule: operator words beat ChatGPT words. ChatGPT lines count only where the operator explicitly endorsed them (noted).

---

## A. What a mini app is

### A1. Positive definition, in the operator's terms

> A mini app is a **packaged, usable application built inside QMX on top of QMX's capabilities**. You usually build it on a node canvas. It has its own data: data comes in, gets worked on, and goes out. It can show itself as widgets and dashboards in the QMX shell. It is roughly what an *extension* is to VS Code. It *may* contain workflows, and a workflow *may* contain agents, but neither is required. Most mini apps contain no agents.

Each part, with its evidence:
- **"Composing capabilities into usable work", grown into a packaged app.** The operator endorsed the framing at N:L198 ("Wow, that's actually very good"). Mini apps appear when that composition is packaged: "which means they can become mini-apps. Now, this is where the taskade thing comes in" (N:L319).
- **≈ extension.** "mini apps are ideally extensions, unless I'm wrong" ... "Same way VS Code has extensions" (N:L593). Later: "mini apps I think have become sort of extensions" (N:L724).
- **Groups widgets plus shared parameters.** Operator, on OpenBB: "an app can group widgets and link... Now I see it" (N:L593, reacting to N:L530).
- **Built in a node editor.** "how are we going to be building the mini app? Is it via a node-based editor like Tascad?" (N:L1068). He confirmed this later on a call (LV R-114, R-131).
- **Own data / databases.** "imagine we build a custom database and then we attach it to specific apps" (N:L890). On a call: "Creating of databases for mini apps" (LV R-025, R-132).
- **Data in and out.** "most apps either produce data, so... think of it like files... unless something needs to be streamed, then APIs" (N:L1646).
- **Not a bundle of workflows; usually no agents.** "A mini app is not a combination of workflows. It can be... Most times... there won't be agents" (LC MA-01, M432, 10-06, final word).
- **Earned by passing tests.** "by the time something is converted into a mini app, that thing should have passed a lot of tests" (N:L1068). See also N:L313: "for something to actually be reusable it has to pass tests".

### A2. Depth / complexity level

This is high, not toy-level. The operator sets the bar:
- "the complexity of the mini app system should give you beyond insane amounts of features" (LC MA-13).
- The voice ledger says the mini-apps transcript "will give you the level of complexity" (LV R-135).

The examples below run from small widget dashboards up to whole trading or intelligence systems. The *floor* is a few widgets bound to a data recipe. The *ceiling* is a full replaceable subsystem, such as an alternative portfolio/risk system or a second MIS (N:L890, N:L1061, N:L1065).

He also noted that not everything is a mini app: "Some are not mini apps. Some are just things that QMX should be able to do by default" (LC MA-12).

### A3. Concrete examples from the conversation

| Example | Where | What it shows |
|---|---|---|
| New portfolio optimizer / new BMS / Book variant | N:L198, N:L263-273 | experimental compositions that may graduate |
| New data route; multi-source live+historical data | N:L198, N:L429 | data-first mini app |
| Energy-industry market intelligence ("know when liquidity happens") | N:L429; ChatGPT echo N:L469, N:L659 | data + features + dashboard, no bot |
| Macro/microeconomics app: daily bias at start of day | N:L890 ("as a mini app, which I love to design") | morning briefing from widgets + workflows |
| Scalper-oriented app; portfolio "for scalping only", with or without Book | N:L890, N:L1065 | a trading-system variant as an app |
| Scalping Book v1 / v2 | N:L890 | versioning inside apps |
| Two MIS versions at once | N:L890 | parallel variants; headless |
| ML section/app; models classified per app, instrument or sector | N:L1061 | ML models "belong to this app" |
| Dataset builder, data banks, COT, yields, insider trading, screeners (LSE-inspired) | N:L890 | data-tool apps |
| What's inside the trading node becoming "a mini up" | N:L1061 | trading node as an app (big claim) |
| Loops as mini apps | N:L1058 ("loops can become mini apps") | small, repeatable app |
| "Morning Desk" composite of Sector Intelligence + ML + Portfolio Lab | ChatGPT N:L1572; operator "perfect" N:L1646 | app-of-apps |
| Department grouping: one department ↔ many apps | N:L890 ("three mini apps can represent the same department") | apps replace the old agent "desks" |
| First mini app paired with "my own copilot" | LV R-001, R-133 | first acceptance target |

### A4. What it is made of

| Ingredient | Required? | Evidence |
|---|---|---|
| **Nodes / a composition graph** | Normal build path | N:L1068; LV R-114/R-131. The ChatGPT build triad (board + presentation + package, N:L1171-1175) was not contradicted |
| **Data sources / providers** (API, CLI, polling, streaming, files) | Common | N:L429, N:L593 ("API or CLI provision"), N:L1646 |
| **Its own storage / database** | Yes (operator's words) | N:L890; LV R-025/R-132. See conflict D1 |
| **Widgets / dashboards** | Usual, but headless allowed | N:L1070 ("widgets are going to be making up dashboards"); headless capabilities "should be... a node" (N:L1068) |
| **Code** (Python, notebook node, CLI-backed node) | Optional | N:L313 notebook node; N:L429 "a simple node which shows the chord [code]"; N:L889 CLI rendered in node |
| **Workflows** | Optional (M432) | LC MA-01 |
| **Agents** (Deep Agent nodes) | Optional, rare | LC MA-01; agent nodes default to Deep Agents (LV R-113; LC AG-28) |
| **Copilot integration profile** (access + definitions of what the copilot may do in this app) | Yes, per app | "each application should ship with a version of a copilot" (N:L1058). Refined: "one global and then a defined schema" (N:L1061) |
| **Lineage + docs** (the session that led to it, how it works; docs as a skill with hooks) | Yes | "a mini app I think can have a lineage, the session that led to it" (N:L1058) |
| **Version** | Yes | v1/v2 (N:L890); app-use → authoring change request (ChatGPT N:L1107, not contested) |
| **Exports** (outputs, operations, views) | Optional | N:L1586-1596. Operator: "files... unless... streamed, then APIs" (N:L1646) |
| **Templates** | Yes, as a starting point | "We should be able to create templates also" (N:L316). See also LC MA-06 |

### A5. Lifecycle

1. **Seed / experiment.** Work on the messy board ("the storyboard should be messy", N:L1068) in an authoring copilot session (N:L316: "the agent... is the one doing most of the stuff... I'm just there talking with it"). Drawing does not run anything. An experiment can "pass, fail, or you learn" (N:L316).
2. **Build.** Wire nodes with typed, meaningful connections (N:L313). Start from defaults and templates (N:L319). Add your own custom nodes (N:L429: "I should also be able to create my own").
3. **Test.** It must pass tests before it becomes a mini app (N:L1068). For trading systems: paper trade first plus a readiness dashboard ("this works, the latency works", N:L1061).
4. **Package / publish.** Versioned, with lineage, copilot profile and docs. Choose where it runs: local or server (VPS), GPU if needed ("a simple toggle in the UI", N:L321; GPU checks N:L1070).
5. **Run / use.** It opens as a tab, panel or sidebar item in the shell (ChatGPT N:L548, operator agreed "it can open in the sidebar", N:L593). An **app-use copilot** session can read and operate it but cannot edit it (N:L1061: "it doesn't have the ability to edit or improve it"). It can query the app's own agents and logs (N:L1058).
6. **Maintain.** From app-use, produce an artifact or prompt, then take it to an authoring session that creates the next version (N:L1058). The copilot owns creation, maintenance and DevOps for mini apps (LC MA-10: "not just docker").
7. **Share.** Others build on what you have without touching core code. "I want them to be able to create new things on top of what we have" (N:L724). No marketplace needed (N:L890). The recipient supplies their own credentials (ChatGPT N:L764, not contested).

### A6. Relations

| Relates to | Relationship |
|---|---|
| **Workflow** | A procedure (composition of operations, agents, decisions). A mini app *may* contain workflows. It is not defined as a bundle of them (M432). Workflows "came before mini apps" historically (LC WF-01) and can run with no app open (ChatGPT N:L756). The operator called a workflow coordinating several apps an "unnecessary evil" but acceptable (N:L1646) |
| **Agent** | Optional node type inside workflows. Defaults to a Deep Agent (LV R-113). Most mini apps have none |
| **Copilot** | One global copilot with many sessions. **Authoring** sessions build and edit apps. **App-use** sessions operate them (N:L1058-1061; repo ProductSessionProfile `{authoring, app-use}` matches). Each app ships a schema of what the copilot may access there. The copilot must "update itself" as apps combine (N:L1646) |
| **Node editor** | The build surface. The same canvas family as the Experimentation Board (operator: the board "is part of the thing, but not so separate", N:L316) **(inf)** |
| **Library** | The artifact library (strategies, bots) is to be upgraded with a database (N:L1791). Apps consume and produce artifacts **(inf)**: an app references Library items by identity and does not copy them (ChatGPT N:L301) |
| **Extension** | ≈ the same thing in the operator's mind (N:L593, N:L724). ChatGPT's split (extension = adds capability; mini app = UI over capabilities; widget = one view, N:L663/N:L750-754) was praised (N:L884 "Well done") but never sharply ruled |
| **Widget** | A view or control inside an app. Dashboards are made of widgets (N:L1070) |
| **Trading node (QMN)** | Operator: what runs on the node can itself be a mini app. QMN is "just the symbol that this is a server" (N:L1065) |
| **Other mini apps** | Consume another app's output, invoke its capability, coordinate via a workflow, or compose a new app from parts of others (N:L1542-1580; operator "perfect", N:L1646) |

### A7. What a mini app is NOT (operator's negatives)

- Not a bundle of workflows by definition. Not an agent container by default (M432).
- Not every QMX capability. Some things are "just things that QMX should be able to do by default" (LC MA-12).
- Not a raw experiment. A draft or experiment on the board is not reusable until it passes tests (N:L313, N:L1068).
- Not limited to trading ideas: "don't limit yourself on just trading ideas", e.g. ML, sentiment, data handling (N:L429).
- Not a copy of an external product. "we are borrowing mental models, we are not using OpenBB or Tasket" (N:L429).
- Not the same as a cron job or schedule: "workflows and current jobs are two different things" (N:L593).
- Not a screen-scrape target for the copilot. Context comes from a proper schema, not screenshots (N:L1058).
- Not something that edits itself in app-use mode. Only authoring creates new versions (N:L1061).

### A8. Taskade image (IMG): what it fixes as the reference shape

- Left: AI chat ("Genesis AI") building the app conversationally ("add Gmail into automation flow..."). It proposes connections ("Connect to Gmail" / Skip).
- Middle rail: **Projects, Agents, Flows, Media, Connections**. These are the app's own parts: data, agents, automations, assets, integrations.
- Top: **Workspace ⇄ Preview App** toggle, **Publish**, hosted app URL, **Analytics**, **Users**.
- Flow canvas: trigger ("WHEN THIS HAPPENS", "New lead in #sales") → AI step → IF branch → yes/no actions. Some nodes are tagged "AI"; most are not.
- Flow tabs: **Workflows / All Runs** (run history). Creation: **New / AI generate / Template**.
- Lesson the operator drew (via ChatGPT N:L1165-1167, not contested): "the workflow is part of the app's construction, not necessarily the entire app definition". This agrees with M432.

---

## B. Node editor concept

### B1. Purpose
- The canvas is "one interface" to composing capabilities, not the owner of work (N:L24, endorsed N:L198).
- It works in two modes. **Storyboard / Experimentation Board**: draft, scribble, nothing executes, and drawing creates no execution dependency (N:L313). **Runnable composition**: workflow or mini app.
- Name: **"Experimentation Board"**, not "research board", because that would clash with QMA research staff (N:L316).
- The board can run only a selected part: "Run" means a selection, a connected section, or a defined procedure (ChatGPT N:L245).

### B2. Node types (operator-sourced unless noted)

| Node type | Source |
|---|---|
| Core capability nodes: "everything under QMB" (trading bot, backtesting system, hypothesis/TIF generator) | N:L313 ("everything under QMD" = QMB) |
| Notebook node (Jupyter-like; the agent writes scripts; it declares what it may and may not produce) | N:L313 |
| Code node (n8n-style). Can show its code; granularity is configurable | N:L429 |
| CLI-backed node (shows backend output CLI-style, like n8n's run view) | N:L889 |
| Headless capability nodes (data adapter, computation, scheduled op) | N:L1068 |
| Agent node (= Deep Agent by default) | LV R-113; LC AG-28 |
| Graph Templates as default workflows / nodes | N:L198 ("they can come in as default workflows, perhaps") |
| Strategy node (collapsed inputs/config; expand into QML authoring) | ChatGPT N:L233. Operator: "true, true" but warned not to explode bots into micro-nodes (N:L313-316) |
| Webhooks, cron triggers, branching, subflows | N:L889 webhooks; LV R-116 cron. Branching/subflow are ChatGPT N:L375 **(inf)** |
| Data provider / recipe nodes (multi-source live + historical) | N:L429 |
| Exported app-as-node (another mini app's operation shown as one node) | ChatGPT N:L1598, operator "perfect" N:L1646 |

Anti-pattern (operator): "not everything is going to be in the node or in the workflow" (N:L313). Do not break a bot into components when a genetic algorithm inside a notebook node does it better.

### B3. Data flow
- Every connection has meaning and a reference: one-to-one, one-to-many, many-to-many, many-to-one (N:L313). Incompatible ports cannot connect, as in n8n (N:L313).
- What crosses an edge is the node's **declared output**, not its internals (operator's notebook example, N:L313; ChatGPT N:L345).
- Collection mapping is explicit. One dataset × 20 candidates ≠ 20 × 20 (ChatGPT N:L349). The repo already ratifies `one|zip|broadcast|keyed-join|cartesian` (ADR-0024 AD-5).
- The composition is a **schema'd declarative description** (n8n JSON). "a schema gives specific rules... if something is not correct... it won't run" (N:L316). ChatGPT refinement, accepted by the operator (N:L429): JSON describes, Python and QMX capabilities execute.
- Between apps, outputs are **files/datasets by default, APIs when streamed** (N:L1646). References are passed instead of copying contents (ChatGPT N:L1747).

### B4. Execution model
- **Deterministic by default. Agents optional.** "it can both have agents in the workflows or it can be purely deterministic" (N:L198).
- **Assistant builds, it is not a node.** n8n's AI Workflow Builder is the model (N:L198). ChatGPT distinction, accepted: an assistant that helps build ≠ an agent that participates (N:L259).
- **Placement**: local or server (VPS), with GPU where needed. The UI toggle is simple and the backend resolves it (N:L321, N:L889, N:L1070).
- **Logs + traceability** are mandatory: "workflows... should have logs" (N:L1058).
- **Accumulation**: "one giant, but with like accumulation of many graphs over time" (N:L316). Subworkflows, as in n8n (ChatGPT N:L389).
- **Recovery rules** (ChatGPT N:L108-112, uncontested): a retry is not a new experiment. Editing a workflow does not edit a running execution, because a run pins its definition.
- **Cron ≠ workflow** (operator, N:L593).

### B5. References the operator cited (mental models, not dependencies: "we are borrowing mental models", N:L429)

| Reference | What to take | Cited at |
|---|---|---|
| **n8n** | Node catalogue (~300 nodes), JSON workflow schema, code node, AI workflow builder, templates, subworkflows, node run views. "study... N8N's node system" | N:L7, N:L198, N:L313, N:L429, N:L889 |
| **Taskade (Genesis)** | **Closest model of a mini app.** IMG shows a workspace with Projects / Agents / Flows / Media / Connections, a "Preview App" toggle, Publish, a hosted app URL, Analytics, Users, an AI side-chat building the flow, and flow starts "New / AI generate / Template" | N:L313, N:L316, N:L319, N:L429, N:L1068, IMG |
| **OpenBB** (Workspace apps, ODP extensions) | Apps group widgets + linked params; provider vs processing extensions; data | N:L319, N:L429, N:L593 |
| **StrategyQuant / QuantConnect** | Experimentation mental model; data capability split | N:L313, N:L429, N:L593 |
| **MT5 / MQL** | Experimentation example | N:L316 |
| **JSON Render** | Widget/component catalogue the copilot composes | N:L429, N:L593, N:L1070 |
| **MCP Apps** | Interactive app↔host↔copilot views | N:L885, N:L1058, N:L1070 |
| **VS Code / Zed / Omarchy** | Extension model, side-panel copilot (Ctrl-Alt-B) | N:L593, N:L890, N:L1058 |
| **Hermes desktop plugin SDK** | Built-ins and user plugins share one contribution path | N:L1645 |
| **DeepSeek harness / Cordis** | Extension points, reversible registration (cited at "the DeepSeek harness... is for the mini apps", LV R-134) | N:L313, N:L320 |
| **London Strategic Edge** | Data banks, dataset builder, ML studio, tools: candidate app catalogue | N:L721, N:L890 |
| **LangGraph** | Execution/persistence model for graphs | N:L321 |
| **Caliper** | Eval of copilot-authored skills | N:L724 |
| **Bloomberg** | Panel-based terminal | N:L593 |
| n/a | The operator never named **ComfyUI or Node-RED**. Do not attribute them to him | n/a |

---

## C. Agent ideas: still standing vs superseded

Context: the A-doc predates mini apps and the Oct 4 pivot. Current rulings: LangChain + LangGraph (LC R-04), Deep Agents in workflows (R-05), Hermes-style pluggable memory (R-06), copilot works like Codex/Claude Code (R-07), and no custom SDK ("Please don't try to invent anything", LC AG-21).

### C1. Still standing (plausibly)

| Idea | Evidence | Note |
|---|---|---|
| **Role vs worker**: a persistent responsibility holder spawns ephemeral bounded workers on demand. Don't keep permanent specialist swarms | A:L1465-1531, A:L1996-2047. Operator: dev agents "overcooked" (A:L1896) | Maps onto Deep Agents sub-agents. The old "five quants" become optional departments or app groupings (N:L890) |
| **Role / Bot / Agent split**: Role = declarative prompt/policy; Bot = durable identity; Agent = a running instance | A:L4087-4166; operator: "role is kind of like the system prompt" (A:L3963) | The vocabulary survives as concepts. Whether persistent Bots still exist after "one copilot + workflows" is open |
| **Memory ≠ Knowledge ≠ Ledger ≠ Context ≠ Artifacts** | A:L2092-2125; operator asked for exactly this split (A:L1896) | Matches the copilot's three-way split at N:L944-948 (conversation / durable memory / work records) |
| **Memory = selective, evidence-backed, scoped (role/project/user), supersedable** | A:L2186-2294, A:L1673-1704 | Now implemented via Hermes-pattern pluggable providers (Hindsight / Mem0 candidates). Operator refused to build his own memory (A:L3976) |
| **Knowledge base = versioned evidence corpus with provenance (Delphi-like)** | A:L2298-2332 | Still needed. RLM operates over it and does not replace it (A:L2344) |
| **Ledger is agent-authored, per desk, separate from logs/traces/observability** | Operator, A:L3968; ChatGPT accepted A:L4243-4340 | Operator added: the ledger can be driven by hooks (A:L4954) |
| **Two session runtimes: dialogue vs RLM**; attached/detached; autonomy level | A:L3011, A:L3266-3367 | Detached agents still talk via daemon mailboxes (A:L4043) |
| **Hooks as deterministic gates**, Claude Agent SDK as the reference | A:L3963, A:L4344-4400; LC AG-23 | "agents write deterministic scripts... instead of... review their own work" (A:L3976) |
| **Skill ≠ loop ≠ graph**. V1 loops are authored, not self-invented | A:L4404-4497, A:L3481-3523 | The operator later added "loops can become mini apps" (N:L1058) |
| **Mission = executable contract** (intent, scope, success, budget, escalation, termination) compiled by meta-prompting | A:L3090-3159, A:L4204-4239 | Fits a Deep Agent's task brief |
| **Daemon ≠ UI**; closing the UI never stops agents | A:L3963, A:L4002-4045 | Also in repo (CT-40) |
| **Harness = composition** (model + tools + skills + memory/context policy + permissions + hooks + optional UI contributions) | A:L82-125, A:L3373-3426 | The per-app copilot profile is a harness-lite (N:L1113) **(inf)** |
| **Extensibility / UI contribution points**: activity bar, sidebar, panels, editors, widgets, settings; host owns shell/lifecycle/permissions; three-sided plugin (daemon/worker/ui) | A:L269-404, A:L4966-5035 | This is the mini-app host model. Settings panel to add MCPs/tools per desk "without me doing much" (A:L4954) |
| **Capability contracts** (provides / requires / optional) and **trust levels** | A:L807-888 | "a chart widget should not automatically get shell access" |
| **Tool registry; MCP is one tool source** | A:L4556-4578; operator A:L4954 | Plus plugin MCPs |
| **Capability ladder**: API/CLI → Docker → browser → desktop | A:L3779-3799, A:L4582-4625. Operator: "most things are going to be on a back-end level, no visual" (A:L3976) | Docker per worker, not shared machines |
| **Distributed compute fabric + immutable experiment specs** (OpenResearch) | A:L1896 (operator), A:L2470-2617 | 60-hour laptop-off jobs (LV R-101) |
| **Model proxy (OpenCodex-style)**: deterministic, multi-account, quota/failover, not an LLM router | A:L3011, A:L3976, A:L4631-4675 | = CLI proxy for Codex/Claude subscriptions (LC CP-01) |
| **Cross-model review via policy/hooks** | A:L3963, A:L4679-4721 | |
| **Agent-to-agent mailbox** (identity + durable queue + wake-up) and the machine-off-for-two-days case | A:L4501-4552, A:L4954 | |
| **Folder-as-agent** packaging | A:L3963, A:L4170-4200; LC AG-22 | Open |
| **Live inspection of remote agents in the UI** | A:L5071-5082 | |

### C2. Superseded or likely dead

| Idea | Why |
|---|---|
| **In-house custom SDK** ("we are not using any SDK", A:L3011; qmx.* surface A:L3373-3420) | Reversed: adopt LangChain/LangGraph + Deep Agents (LC R-04/R-05; LV R-087). "building it from scratch is going to take time" (LV R-091) |
| Pi kernel / Prime / bb / Cordis as the runtime stack (A:L31-991, A:L1057-1081) | Mental models only now. Cordis and UI ideas are out of backend scope (LC R-16) |
| TypeScript daemon (A:L4049-4073); fully native Rust UI (A:L3976, A:L5037) | Daemon is Python asyncio (repo COMP-QMA-DAEMON). UI is a separate Claude lane. Rust-native is not current **(inf)** |
| Five persistent quant roles as the main UI, "digital quant organization" (A:L1005-1033, A:L1884) | Operator's newer view: one copilot, many sessions. Workflows and mini apps replace "departments" (N:L884, N:L890). He also asked to restore the departments (LC AG-02), so treat them as optional groupings |
| QMX Console as a non-owning router (A:L2901-2950) | Replaced by the copilot as a Codex/Claude-Code-style harness that *does* author (LC R-07) |
| Custom loop registry, graph engine and memory SDK as QMX-owned code (A:L3527-3541) | Use LangGraph graphs and Hermes-pattern providers. Loops/graphs survive as concepts |
| One global "QMX Event Ledger" (A:L3163-3232) | Rejected by the operator himself (A:L3968). Ledgers are per desk |
| Sandbox vendor picks (Modal, Cloudflare, Daytona/E2B) (A:L3803-3829) | Operator: famous ones too expensive. Choose after the environment contract (A:L3976) |
| Harness self-refinement (Prime continual harness) as a near-term feature (A:L1281-1354) | Deferred. Gated promotion only (A:L4826-4848) |

---

## D. Conflicts: repo docs and Aurelius MA ladder vs the operator's concept

Repo definition (glossary `mini-app`): "An installed instance of a pack, keyed by `instance_id`". A pack "requests operations, optional `view:*` wire DTOs, optional `copilot_profile`". "Headless packs... are first-class" (glossary `pack`). Widget = "display only" (glossary `widget`). The **pack-and-grant** framing roughly fits "mini app ≈ extension" (N:L593). The conflicts are in storage, build path, runtime and ladder order.

| # | Repo / ladder says | Operator says | Gap |
|---|---|---|---|
| D1 | **Storage**: "mini-app instance rows in the existing plugin-install projection... No other new sqlite store class" (ADR-0020 follow-up, DEC-0429/0440). "Bytes of a pack live in the plugin tree plus daemon install/instance rows" (ADR-0025 AD-2). MA02: "No new independent store, definition-store slot, database engine". Aurelius on the call: shared daemon storage, not per-app DBs (LV Note, O-02) | "Creating of databases for mini apps" (LV R-025); "build a custom database and then we attach it to specific apps" (N:L890); ML models "belong to this app" (N:L1061) | **Direct conflict.** The repo gives a mini app no data store of its own. Only its descriptor/rows live in the daemon sqlite. The operator expects per-app data storage that ingests and emits. MA08 "mutable data" is deferred and still unowned |
| D2 | **MA02 descriptor** `kind: "data-only"`. Content = metadata + `composition_ref` + inert `source_refs`/`asset_refs` (fp1 bytes) | A mini app has nodes, data recipes, code, optional workflows/agents, a copilot profile, lineage | "data-only" means *inert descriptor bytes*, not "a data app". The ladder's first app cannot hold logic, providers or a graph. Naming invites confusion with the operator's data-centric apps |
| D3 | **MA03 composition** = `qma.miniapp.composition.v1`: panels + bindings over a **closed 10-component catalogue** (Stack, Grid, Heading, Text, Badge, Metric, Table, LineChart, Callout, Button) | Built in a **node editor** (N:L1068; LV R-114). Widgets include a code editor, dataset preview, model comparison, parameter form, chart, execution inspector, workflow view. The catalogue is "not limited to generic cards and buttons" (ChatGPT N:L542, operator: "exactly how I envision these things", N:L593) | MA03 is a static dashboard layout validator. It has **no nodes, no edges, no ports, no data flow**. The node editor is absent from the whole ladder |
| D4 | **MA04 publication**: `authorizes_invoke: false`, `health: not-observed`. Only a "trusted dev-factory host". One data-only app. "No autonomous Copilot policy... that is MA06" | Publish = a tested, versioned app that runs its flows and can be placed local/server (N:L321, N:L1068); the copilot creates and maintains apps (LC CP-07, MA-10) | The published artifact cannot *do* anything. Copilot-driven creation, the operator's primary build path (N:L316, LC MA-09), is deferred to MA06 |
| D5 | **Ladder order**: MA05 activity → MA06 maintenance → MA07 restricted runner → MA08 mutable data → MA09 API → MA10 executable deployment → MA11 remote → MA12 laptop-off → MA13 custom UI (all "Not shipped", `CAPABILITY-STATUS.md`) | The operator's concept starts from composition + data + execution, then presentation | **Inverted.** The defining traits (runs, own data, API in/out, server/laptop-off, rich widgets) are rungs 7-13. Rungs 1-4 build persistence/validation/publication for a panel with no behaviour. Months of contract hardening sit on the least distinctive part |
| D6 | **Experimentation Board** "is client-only and writes nothing" (ADR-0024 AD-4) | The board is where experiments and apps are built. Experiments *run* there (N:L316, N:L1068). The assistant creates nodes and "is running the experiments" (N:L316) | Partly compatible: drafting ≠ executing. But "writes nothing" also means board work is not persisted, has no lineage, and cannot hand over to a session, which the operator wants (N:L1058 lineage) |
| D7 | **Graph Template is a DAG; loops are node state, not cycles** (ADR-0024 AD-6) | "loops can become mini apps" (N:L1058); research→backtest→iterate loops (A:L3976); bounded app↔app loops (ChatGPT N:L1616) | A tension to resolve, not necessarily a contradiction. The repo must show how a looping mini app is expressed |
| D8 | **"No sixth application... permanent process besides qma-daemon, qmn"** (ADR-0024 AD-1) | Apps that run continuously: morning desk, two MIS variants, trading system as a mini app, laptop-off (N:L890, N:L1061, N:L1065) | Long-running mini apps need a runtime home. Today that is MA10-MA12 (unshipped) or QMN only. Placing a live trading system *as* a mini app also collides with QMN's fixed Book/BMS wiring (N:L1135; audit N:L1287) |
| D9 | **Widget "display only... do not own invoke"** (glossary). MA03 `Button` has an `action binding` | Widgets are views **and controls** (N:L1478 "Displays or controls") | Minor wording. Make sure controls can trigger app operations through the host |
| D10 | Aurelius M417 "we combine workflows to form mini apps"; voice R-130 "a mini app agent is basically a workflow" | M432: "not a combination of workflows... Most times... there won't be agents" | Settled in favour of M432 (LC R-01). R-130 is compatible only if read as "an agent node inside an app lives in a workflow" **(inf)** |
| D11 | Copilot: repo `{authoring, app-use}`, one identity, in-app panel optional (DEC-0454/0463) | The same two seats (N:L1058-1061), **plus** each app ships copilot access definitions; the app-use copilot can query the app's own agents and logs | **Aligned** in principle. `copilot_profile` is optional in a pack. Operator wording ("each application should ship with...") suggests default-on. Low risk |
| D12 | Interop: ADR-0024 AD-10 four composition modes (consume artifact / invoke op / coordinate via template / composite instance graph) | N:L1542-1580, operator "perfect" | **Aligned.** Keep |
| D13 | Graduation: ADR-0025 AD-9 "yap at authoring → Graph Template → runs with JobHandles → pack export after validate" | Experiment → tests → mini app (N:L1068) | **Aligned** in shape. But MA02-04 do not follow this path: they start from a hand-saved panel candidate, not from a tested Graph Template |

Bottom line for D: the repo's *nouns* (pack, instance, grant, widget, two copilot seats, four interop modes) mostly fit. The *ladder* implements the wrong first slice: inert panel publication with shared storage. The operator's mini app starts from a node-built, data-owning, runnable composition.

---

### D-extra. What a concept-faithful first slice would look like **(inf, not a ruling)**

1. A node-built composition: a provider node → transform/notebook node → output dataset, saved as a versioned Graph Template with ports and mappings.
2. Per-app data area: the app's own store receives ingested data and holds outputs. It is referenced by identity and not copied into the daemon journal.
3. Runs: invoke with a JobHandle, logs and lineage. Local placement first.
4. Presentation: widgets bound to the app's outputs. This is where MA03's catalogue becomes useful, extended with QMX widgets.
5. Publish + app-use copilot reading the app's runs and data. Change request → authoring session → v2.

MA02-MA04 artefacts (CAS candidates, validation proofs, publish/undo receipts) can be reused under steps 4-5. They are not wasted. They are simply not the first slice.

## E. Open questions for the operator (genuinely ambiguous only)

1. **"Own database": how literal?** Do you need a separate physical database per mini app, for example its own SQLite/DuckDB file that moves with the app when shared? Or is an isolated per-app area inside QMX's shared store enough, as long as the app owns its tables and ingests and emits data? Also: does an app's data get deleted on uninstall, and is it included when you share the app?
2. **Is the node editor the only way to build a mini app?** Or can an app also be pure code/notebook + widgets with no canvas graph? And is the Experimentation Board the same canvas as the mini-app builder (Taskade-style: flows + "Preview App"), or a separate scratch surface?
3. **Mini app vs extension.** Same thing, or is an "extension" the headless package (adds nodes, providers, capabilities) and a "mini app" the usable thing built from those? The repo currently says mini app = installed instance of a pack, headless allowed.
4. **Does a published mini app run by itself?** Can it run continuously or on a schedule, on a server or laptop-off, without anyone opening it? Can a mini app hold live trading authority (your "trading node as a mini app", N:L1061)? Or does live trading stay a separate node that apps only configure and observe?
5. **First acceptance mini app.** Which single app should prove the concept end to end? Candidates: (a) macro daily-bias dashboard (data in → features → widgets, no agents); (b) a data-recipe/dataset-builder app; (c) a Book-variant experiment app. This choice decides whether storage + ingestion (D1/D5) come before the panel work.

---

## Appendix: quick line index (operator turns, node-editor transcript)

| Line | Topic |
|---|---|
| N:L7 | Opening: node editor, n8n origin, "blast radius" |
| N:L198 | Workflows ≠ QMA agentic tasks; storyboard; deterministic or agentic; n8n assistant; Graph Templates as defaults; extension system |
| N:L313 | Intentional nodes; typed connections; notebook node; experiments must pass tests; Taskade link |
| N:L316 | JSON schema; "Experimentation Board"; templates; accumulation of workflows; agent builds and runs |
| N:L319-321 | Defaults; OpenBB; "they can become mini-apps"; Taskade; Cordis link; local/VPS toggle; LangGraph |
| N:L429 | JSON Render link; code view in node; multi-source data; build your own nodes + validation; mini-app rendering and interop; not only trading ideas; desktop mini apps; storage vs data handling |
| N:L593 | Settings capabilities; WF1/WF2 birth of workflows; trading-floor desks; "mini apps are ideally extensions"; OpenBB apps group widgets; sidebar |
| N:L720-724 | LSE, Caliper; "mini apps... sort of extensions"; what are we adding; maintenance goal; PM = Portfolio Manager |
| N:L884-890 | QuantMind copilot; MCP Apps; Book/BMS/MIS variants; CLI in nodes; GPU; versioning; macro app; dataset builder + per-app DB; department ↔ apps |
| N:L1056-1070 | IMG; two copilot sessions; lineage; per-app copilot; loops as apps; trading node as app; tests before app; build via node editor like Taskade; widgets make dashboards |
| N:L1446 | Apps combining with other apps |
| N:L1646 | Hermes plugins; scenario split; apps output files / stream via APIs; copilot must update itself |
| N:L1791 | Artifact Library upgrade + DB; orchestration between apps/agents unclear |
