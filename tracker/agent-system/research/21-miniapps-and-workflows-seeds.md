# 21: Mini apps and workflows: the seeds from the 2026-09-17 transcript

Written 2026-10-12. This is a read-only study. Nothing in the repo was changed apart from adding this file.

Source: `Explore-Node-Editor-Architecture.md` (ChatGPT web, 2026-09-17, 1,238 lines, 8 operator turns). It was read in full, in order, along with its two images. "L" numbers below are line numbers in that file. The operator's turns are at L5-8, L196-198, L311-321, L427-429, L591-597, L720-726, L884-892 and L1056-1072.

Cross-checked against:
- `rebuild/DESIGN.md` on `origin/rebuild/base`, cited as **D§x Ly**;
- `rebuild/research/2026-10-12-agent-system/qmx-internal.md`, cited as **QI Ly**;
- `tracker/agent-system/research/20-qma-v2-direction.md`, cited as **R20 Ly**. This is the latest direction, and it wins where it differs from the others.

Status words used below:
- **STILL VALID**: the idea holds and nothing later replaced it.
- **SUPERSEDED**: a later document replaced it. The entry names that document and line.
- **SHIPPED**: built. The entry names the rebuild packet, as listed in QI L557-578.
- **OUT OF SCOPE**: the idea belongs to the Library or QMB, which R20 L15-17 puts outside QMA v2.
- **OPEN**: undecided, or decided but not built.

**What happened right after this transcript.** Grok turned it into the 2026-09-18 sitting, "Workflows construction kit", with AD-1..31 (QI L339, L358-363). That sitting was never accepted by the operator (QI L365). The October rebuild then reshaped it (D§7) and R20 reshaped it again.

**The two images:**
- `image-001.png` is a generated mock-up of a "QMX Quantitative Market Exchange" home dashboard. It shows a side rail (Home, Markets, Strategies, Agents, Portfolio, Orders, Risk, Analytics, Research, Data Hub, CRM, CMS, Settings), headline tiles (including "Active Agents 187/200"), an agent status list, alerts and a system log. The operator calls it the intended look, not the real product (L595). The rebuilt UI rail differs: Home, Copilot, Library, Lab, Portfolio, Apps, Settings (QI L88).
- `image-002.png` is Taskade's workspace: an assistant chat on the left ("add Gmail into automation flow"); Projects, Agents, Flows, Media and Connections; a Workspace / Preview App toggle; New, AI generate and Template buttons; Workflows and All Runs tabs; a flow made of a trigger, then "Score with AI", then an IF branch with yes and no paths; a Publish button.

---

## 1. Plain-words summary

1. A **workflow** is a saved recipe of steps. Each step is a real QMX operation: run a backtest, fetch data, run a notebook, ask an agent, wait for the operator. The steps are joined by typed connections, and a connection says exactly what passes along it. The recipe is stored as JSON, and the work inside each step is Python or an agent.
2. A workflow can be **deterministic, agentic, or mixed**. "Agentic" is a property of a node, not of the whole system (L198, L832).
3. Workflows begin as **messy experiments** on a board, the Experimentation Board, which now lives in the Lab. Only a method that has been tested is saved as a reusable workflow or template (L313, L385-389).
4. A **mini app** is a packaged, usable thing built from capabilities:
   - its own data and settings;
   - workflows;
   - optional agents;
   - optional screens made of widgets;
   - schedules and tools.

   It can be headless: a data collector, the trading node itself, an alternative MIS. It is installed, versioned and run like a container, and it is proven on a road to live before it can act (D§7.1-7.2).
5. A mini app is **not a dev-server preview**. It is the operator's unit of extensibility, the "Lego brick" (L595, L1063). Its complexity is ML-level: models, data recipes, versions, shadow runs and live deployment.
6. **How mini apps relate to workflows.** A workflow is the behaviour; a mini app is the package and the interface around one or more workflows (L1169). A workflow can run without any app (L758).
7. **How they relate to the board.** The board is where things are tried. Promotion goes experiment → tested method → workflow or template → optional mini app (L385-389).
8. **How they relate to the Lab.** The Lab is the authoring bench: Graph, Code and Import views of the same workflow JSON (D§7.4 L291).
9. **How they relate to agents.** Agents do reasoning work inside nodes. The **Copilot builds, runs, edits and explains** workflows and apps through the same API the UI uses (L379-381, D§8 L357).
10. **How they relate to QML, QMB and QMF.**
    - QML (strategy authoring), QMB (backtests) and QMF (data, risk and indicator interfaces) **own the computations**.
    - Workflows and apps call those owners and never absorb their responsibilities (L496-498).
11. **How they relate to data.** Data handling is a capability layer of its own: providers, recipes, point-in-time rules, and live feeds versus history (L447-477). Apps own their own small database and pass data to each other by reference (D§7.3, §7.6b).
12. **How they relate to money.** Live trading is reached only through the road to live and the money-path barrier. A box on a canvas never gains authority that its capability does not have (L86).
13. For QMA v2, the agentic system must **build, run, maintain and edit** both workflows and mini apps (R20 L84). It must also be a participant inside them, not their owner (L253-255).

---

## 2. Every seed, one entry each

### S01. A workflow means "composing QMX capabilities into understandable, reusable work"
- **Idea:** A workflow is a composition of existing capabilities, not a new strategy language, trading runtime or screen replacement. The operator adopted the phrase.
- **Where:** L24, L48, L188, L198 ("that's a very good way to state it")
- **Status:** STILL VALID. D§1 keeps the quant engine and puts agents and workflows on top.
- **Why it matters:** QMA v2 tools must call the owners (QML/QMB/QMF/QMN). Agents must never re-implement domain logic inside nodes.
### S02. Three kinds of diagram must not share one model
- **Idea:** A strategy's logic, a procedure and an execution record can all look like boxes, but they mean different things. Connections must keep their meaning: "supports" is not "must finish before".
- **Where:** L32-44, L216-235
- **Status:** STILL VALID. The split is shipped as stores: workflow definitions and workflow run state are separate (D§7.6b L327-328).
- **Why it matters:** The agent needs distinct tools for "edit the definition" and "inspect a run". It must never patch a run record to fix a definition.
### S03. Durability and control boundaries
- **Idea:** The old task graph was held in memory, and the daemon read socket bytes without dispatching UI commands. "Saved graph" is not the same as "survives a restart".
- **Where:** L14-16, L60-64, L297
- **Status:** SUPERSEDED as a code defect: the daemon and task graph were replaced (D§3 L46, L53). It is OPEN again as a requirement, because R20 L240-243 drops LangGraph for QMA's own runner, which "checkpoints each node in SQLite".
- **Why it matters:** The v2 runner must prove reconnect, crash and resume. R20 L243 already lists retries, timeouts and joins as risks.
### S04. Graph validation must be adversarial
- **Idea:** The old validator caught A→B→A but not A→B→C→A. A good-looking graph demo is not evidence.
- **Where:** L66
- **Status:** SUPERSEDED (that validator was retired with the task graph). The lesson is OPEN for the v2 graph: cycles are allowed only through an explicit `loop` node.
- **Why it matters:** Agent-written graphs will contain mistakes. Validation must be deterministic and complete before a run starts.
### S05. Step-as-contract
- **Idea:** Every exposed capability declares six things: what it accepts; what it produces; who owns it; where it may run; what it may change; what happens if it fails or is invoked again. "Effect and authority" information goes beyond typed I/O.
- **Where:** L90-104
- **Status:** Partly SHIPPED. Typed ports exist (D§7.4 L288), with JSON Schema per output reference (D§7.3 L279) in P10. **Effects, authority, idempotency and placement are not in any descriptor yet.** That part is OPEN.
- **Why it matters:** This is the catalogue the Copilot reads in order to compose safely. Without effect fields, it cannot tell a read from a write or a paid call.
### S06. An interpretation is not a measurement
- **Idea:** A "Summarise findings" agent step produces interpretation, and the system must label it as different from measured results.
- **Where:** L100
- **Status:** STILL VALID. The Experiment Ledger is kept, with "invalid evidence quarantined verbatim" (D§12 L474). Interpretation is not labelled as a separate output type.
- **Why it matters:** Agent output must never pass as evidence in a promotion card.
### S07. Approval binds to an exact revision
- **Idea:** If the operator's review is recorded and the candidate is edited afterwards, the approval must not silently carry over.
- **Where:** L102
- **Status:** SHIPPED for apps. P14 has immutable versions and compare-and-swap, and undo is a new transition (D§12 L479). It is OPEN for workflow `human_gate` nodes.
- **Why it matters:** The agent edits often, so every gate must re-ask after any change.
### S08. Three different things that sound alike
- **Idea:** Closing the browser, restarting a worker, and moving work to a server are three separate problems.
- **Where:** L108
- **Status:** SHIPPED. The UI and the backend are decoupled (P11). Remote runs use Git-style push and fetch (D§11b, P21).
- **Why it matters:** Long agent runs must keep going when the UI goes away. Each one needs a declared placement.
### S09. A retry is not a new experiment
- **Idea:** Recovery must not repeat an external action that already succeeded. A deliberate rerun keeps its own history.
- **Where:** L110
- **Status:** OPEN. The result memo helps for backtests (D§7.6b L319), but there are no idempotency keys on node side effects.
- **Why it matters:** An agent that retries will otherwise send two Telegram alerts, make two paid calls, or write the Library twice.
### S10. Editing a workflow is not editing a running execution
- **Idea:** An edit creates a new draft, and a running execution keeps the definition it started with. Changes to a running job go through explicit commands.
- **Where:** L112
- **Status:** OPEN for workflows. It is implied for apps, where the definition is immutable and hashed (D§7.1 L244).
- **Why it matters:** The Copilot edits live workflows while they run. Runs must pin the definition hash.
### S11. Exploration → procedure
- **Idea:** From an afternoon's exploration, keep the deliberate method as a saved, parameterised procedure. Do not keep every tool call.
- **Where:** L120-128
- **Status:** STILL VALID and OPEN. R20 L242 is close: "a dynamic workflow the copilot writes is saved as a graph" that can be re-run.
- **Why it matters:** This is the core of "the agent builds workflows". It needs a "promote to procedure" operation that turns selected steps into parameters.
### S12. What a change invalidates
- **Idea:** If cost assumptions change, show which results depend on them, reuse upstream outputs, and rerun only what changed, where the semantics allow it. Changing Book rules or sizing is never a "projection" of old trades.
- **Where:** L130-138
- **Status:** OPEN. The memo key (strategy version + data snapshot + params) gives reuse (D§7.6b L319). Projection-versus-rerun is a September guardrail (QI L547). The lineage and dependency views are Library work, so that part is OUT OF SCOPE (R20 L16).
- **Why it matters:** When the agent maintains apps, it must know what goes stale after an edit. Without that it cannot tell the operator which numbers can still be trusted.
### S13. Levels of detail
- **Idea:** The top level reads like "Select → evaluate → investigate → review". Each box can expand into a subflow, a bounded agent task or plain Python. Not every function deserves a node.
- **Where:** L140-150
- **Status:** SHIPPED as a shape: the `subworkflow` node kind (D§7.4 L287). Expanding and collapsing in the UI is OPEN.
- **Why it matters:** Graphs written by agents tend to grow too many nodes. The skill must teach the agent which granularity to choose (L572).
### S14. Experimentation Board, partly non-executable
- **Idea:** Charts, questions and unfinished pieces sit next to runnable parts. "Run" has a scope: the selected operation, a connected section, or a defined procedure. The board never has to become one giant graph.
- **Where:** L152-158, L237-247, L316 (operator renames it). The operator says the board "should be messy" (L1070).
- **Status:** STILL VALID. In the UI it became the Lab tiling workbench (QI L150). There is no board object in the backend, so it is OPEN.
- **Why it matters:** The agent needs to tell drafts from runnable sections. It must never auto-run a whole canvas.
### S15. Connections must be intentional
- **Idea:** The operator rejected ChatGPT's "source → hypothesis" edge. Only purposeful units become nodes, and every edge has a meaning and a cardinality (one-to-one, one-to-many, many-to-many). Things that cannot connect must visibly fail to connect, as in n8n.
- **Where:** L313, L349
- **Status:** Typed ports are SHIPPED (P10). **Cardinality, meaning broadcast versus pairing, is OPEN** (L349).
- **Why it matters:** Typed edges let a weak model wire correctly. The rule is "weak models operate through schemas" (09-23 AD-7, QI L362).
### S16. Drawing a connection does nothing
- **Idea:** Drawing an edge does not submit a job, install anything or change a running system. Execution is explicit.
- **Where:** L351
- **Status:** STILL VALID.
- **Why it matters:** The agent's canvas edits must have no side effects until a run tool is called.
### S17. Node kinds
- **Idea:** The transcript names these kinds: QMB evaluate, compare and record conclusion; notebook or code node (n8n's Code node); agent task; human review; command/CLI node with streaming logs and cancel; subflow; branching and collection operators; data acquire and transform; triggers and webhooks; app call.
- **Where:** L174-176, L313, L375, L991-992, L891 ("Webhooks")
- **Status:** Partly SHIPPED. P10 has 10 kinds: `python`, `agent`, `tool`, `app_call`, `condition`, `parallel`, `join`, `loop`, `human_gate`, `subworkflow` (D§7.4 L287). **There is no trigger or webhook node, and no command node with log streaming.** R20 L241 shortens the list to code, agent loop, mini-app call and human gate. The list is OPEN.
- **Why it matters:** The set of node kinds is the agent's vocabulary for building workflows. A missing trigger kind blocks the event-driven apps the operator described.
### S18. The notebook node, and granularity that can be configured
- **Idea:** A notebook holds a whole genetic search, and only its declared outputs cross the edge. The operator still wants to see the code inside. Encapsulation is available but never forced.
- **Where:** L313, L343-347, L429, L445
- **Status:** SHIPPED in part: the Graph, Code and Import views of one JSON, and `to_python()` (D§7.4 L291, QI L564).
- **Why it matters:** The agent writes the notebook. Its contract (inputs, outputs, what it may do) is what makes the notebook safe to reuse.
### S19. Composition in JSON, operations in Python
- **Idea:** n8n saves workflows as JSON, and its nodes are code with declared descriptions. JSON is the format, and a schema constrains it. Valid JSON can still fail a schema, and a schema-valid run can still fail.
- **Where:** L316 (operator: "why did these guys choose JSON?"), L355-369, L429 (operator accepts)
- **Status:** The JSON graph format is SHIPPED (P10). The engine is SUPERSEDED: LangGraph (D§7.4 L289) gives way to QMA's own graph (R20 L63-66).
- **Why it matters:** One inspectable document is shared by the editor, the agent and the runner. The agent can read and validate a workflow without running Python.
### S20. Defaults first, then custom
- **Idea:** Never ship an empty editor. Ship a curated catalogue covering QML, QMB, QMF, notebooks, QMA tasks and control flow, and let the user and the agent create new nodes. Custom work raises the question "where does it belong, and how is it validated?"
- **Where:** L319, L371-375, L429
- **Status:** STILL VALID. This is the operator's standing Lego rule (QI L174). The domain tool catalogue is SHIPPED in P09 (D§6). The custom-node path is OPEN.
- **Why it matters:** Defaults teach the agent good patterns. Custom nodes need the validation in S33.
### S21. One capability description drives the UI and the agent
- **Idea:** The same declaration drives the manual editor and the assistant's tools, so there are never two implementations.
- **Where:** L377-381, L522
- **Status:** SHIPPED in principle: `qmx-control`, "one implementation, two doors" (D§8 L357, P11). Workflow operations are stubbed, `CTL\service.py:880-894` (QI L564), so that part is OPEN.
- **Why it matters:** Anything the operator can click, the Copilot can do, and the reverse. This is the backbone of an agent that maintains apps.
### S22. Templates and accumulation
- **Idea:** Successful runs become templates, as in n8n. Over time a library of many workflows builds up, and workflows call other workflows.
- **Where:** L316, L385-389, L1067 ("you are seeing why we needed templates")
- **Status:** Workflow-to-workflow calls are SHIPPED as the `subworkflow` node and `CompiledSubAgent` (D§5.2). Template sets come from Claude's six dynamic-workflow patterns (R20 L242, OPEN). Per-app template sets are OPEN.
- **Why it matters:** The agent should start from templates, not a blank graph.
### S23. QMA and workflows are not the same thing
- **Idea:** QMA is for long-running agentic tasks; workflows are a different and broader thing. An assistant that helps build a workflow is not an agent that takes part in it. A deterministic workflow needs no agent, Quant or Mission.
- **Where:** L198 ("Egentic is the word I want to focus on"), L249-261, L828-838
- **Status:** STILL VALID. R20 L66 says "workflows and mini apps can be agentic or not". The old QMA Mission model is SUPERSEDED (D§3 L46).
- **Why it matters:** QMA v2 must expose the workflow runner as a tool and a sub-agent kind. It must not own every run.
### S24. QMA graph templates as default workflows
- **Idea:** Existing QMA Graph Templates could become selectable procedures.
- **Where:** L198, L261, L319
- **Status:** SUPERSEDED. The QMA templates were retired (D§3 L46), and v1 shipped none (QI L499). R20 L242 replaces them with Claude's six patterns as built-in templates.
- **Why it matters:** Do not port the old templates; design the new ones.
### S25. The optimizer example: building what QMX does not have yet
- **Idea:** A user can write a new portfolio optimizer, a new data route, or a hybrid of two bots as an experimental callable. Later it can become a reusable capability or a runtime policy. Today's Book and BMS contracts must not set the limit.
- **Where:** L198, L263-281, L316
- **Status:** STILL VALID. It is the reason the operator built QMF (L1063). The domain contracts are OPEN (see S44).
- **Why it matters:** The agent must be able to create new capabilities, not only wire existing ones.
### S26. Not only trading ideas
- **Idea:** Workflows and apps also serve ML experiments, sentiment, data handling, or a new model such as Jev. A method can be valid even when it disproves the idea it tested.
- **Where:** L391, L429, L510
- **Status:** STILL VALID. App shapes include a dataset builder and a data collector (D§7.1 L264).
- **Why it matters:** The success criteria the agent works to must be general, not "find a winning strategy".
### S27. The local/VPS axis
- **Idea:** Placement is explicit, local or remote, and the UI can show a simple toggle. What matters is where the execution owner lives. Moving a running computation between machines is a separate, harder problem. The VPS takes unattended batches, schedules and long studies.
- **Where:** L198, L283-291, L321, L415
- **Status:** SHIPPED: `ComputeProvider`, "Run on…", and "resume elsewhere" (D§11b L417-465, P21). Amp is SUPERSEDED (R20 L80, no orbs). The Contabo server becomes "QMX's own orb" (R20 L247-251).
- **Why it matters:** The agent must choose and record placement. Long and cron workflows run on the server by design (R20 L78-79).
### S28. SQLite has a single writer, and remote access goes through the owner
- **Idea:** WAL mode allows one writer, and a database file must never be shared across machines. Remote access goes through the application that owns the data.
- **Where:** L303
- **Status:** SHIPPED as "rule zero": one writer per file, others ask through `qmx-control` (D§7.6b L314).
- **Why it matters:** Agents on the VPS cannot write the laptop's databases. They must call the API.
### S29. Board records point to data instead of copying it
- **Idea:** Records reference datasets and results by pointer, and storage keeps journals, state, artifacts and views separate.
- **Where:** L299-301
- **Status:** SHIPPED: artifact references (D§5.2 L113, D§7.3 L279) and the data map (D§7.6b).
- **Why it matters:** Agents pass references, which keeps context small and lineage exact.
### S30. The data layer
- **Idea:**
  - Providers declare their datasets, coverage, history, polling or streaming, resolution, credentials and limits.
  - Reusable **data recipes** record entity mapping, units, revisions, missing data and point-in-time availability.
  - Live feeds need subscription ownership, buffering, stale-data behaviour and catch-up.
  - Storing data is not the same as handling it.
- **Where:** L429, L447-477, L595, L796
- **Status:** OPEN. Source-aware ingestion and the market store exist (D§7.6b L318; L453). R20 L18 says QMF's role is unclear. Recipes and provider discovery are unbuilt.
- **Why it matters:** Workflows built by agents will mix sources. Without point-in-time rules, a historical study quietly uses information from the future.
### S31. Settings needs capability provisioning
- **Idea:** Settings holds each provider's API or CLI access, its mode (polling or streaming) and its resolution. Brokers and providers can change at any time.
- **Where:** L595, L891
- **Status:** SHIPPED in part. Settings has Connections (Exchanges and accounts, Servers, Model providers, MCP servers, Data and sources) (QI L240). Secrets are in Credential Manager (D§7.6b L331).
- **Why it matters:** The agent configures providers through settings tools, never through code edits.
### S32. Custom capabilities outside the core
- **Idea:** Separate who owns an interface from where an implementation is packaged. A custom component can satisfy a QMF interface without living in `qmf-core`. "Classify by responsibility and interface, not by whichever screen created it."
- **Where:** L479-498, L645-655
- **Status:** Partly SHIPPED: each app's `tools/` are Python exposed over MCP (D§7.1 L255). The ownership map is OPEN.
- **Why it matters:** When the agent creates something, it must know where it belongs: QMF extension, QML authoring, or app tool.
### S33. Three validation questions
- **Idea:** Does it conform to its declaration? Does it behave correctly? Is it useful for the purpose? A draft can run in an experimental environment, but reuse needs stronger evidence.
- **Where:** L500-508, L313 ("it has to pass tests")
- **Status:** SHIPPED for apps as the road to live: Build → Tests → Sandbox → Shadow → Live, with evidence at each step (D§7.2 L272, P14).
- **Why it matters:** These are the gates the agent works towards when it builds or edits an app.
### S34. Taskade: "the assistant works on the application"
- **Idea:** The assistant works across apps, projects and workflows. It can create, edit, inspect and troubleshoot them, and it can call actions as one-off tools. There are three entry routes: from scratch, generated by AI, or from a template.
- **Where:** L316, L516-524, L1165-1177, `image-002.png`
- **Status:** SHIPPED in principle (D§1 L13, D§8). The UI has three ways to make an app (QI L217). The build skills are placeholders in P20 (QI L575), so that part is OPEN.
- **Why it matters:** This is the clearest single statement of QMA v2's job. The Copilot needs tools to discover capabilities, inspect the board, validate, execute, read failures and package the result (L524).
### S35. OpenBB
- **Idea:** OpenBB separates provider extensions from analysis extensions that have no provider. Backend operations are separate from widget descriptions. An app groups widgets and links shared parameters (dates, portfolios, regions). One operation can have many presentations.
- **Where:** L319, L401, L429, L526-534, L595 (operator: "now I see it")
- **Status:** Widgets are SHIPPED in the UI as a tile board (QI L228). Parameter linking across an app's widgets is OPEN. OpenBB as a data reference is OUT OF SCOPE for QMA v2 (it is a QMF/data question).
- **Why it matters:** Apps the agent builds need linked parameters, otherwise every widget has to be wired by hand.
### S36. JSON Render and a widget catalogue
- **Idea:** Register rich components (code editor, dataset preview, model-comparison table, parameter form, chart, run inspector), and let an app or the agent assemble screens from them.
- **Where:** L170, L429, L536-556
- **Status:** SHIPPED as tier-1 JSON panels, with `ui.propose_panel`, `propose_layout` and `propose_app` (D§7.1 L254; QI L126). The tier-2 iframe and tier-3 plugin are not built (QI L219-222).
- **Why it matters:** The agent builds screens by describing them, never by writing arbitrary UI code.
### S37. MCP Apps
- **Idea:** A tool can come with an interactive HTML view, with traffic both ways between the view and the host. This is how the operator talks to the Copilot about a chart.
- **Where:** L887, L1004-1016
- **Status:** SHIPPED in design: every app is an MCP server with `ui://` panels (D§7.3). The Svelte AppBridge is OPEN (D§13 L534).
- **Why it matters:** App-use sessions need the Copilot and the app screen to share state.
### S38. Apps talk to each other through exported capabilities, not screens
- **Idea:** One app exports datasets and operations, and another app consumes them. No app ever drives another app's UI.
- **Where:** L552, L661
- **Status:** SHIPPED: typed artifact references, wired by a workflow or the Copilot, with no app-to-app bus (D§7.3 L278-281).
- **Why it matters:** The agent connects apps by passing references, never by scripting another app's UI.
### S39. The taxonomy: capability, extension, workflow, mini app, widget
- **Idea:**
  - A **capability** is an operation QMX can call.
  - An **extension** is a versioned package that adds capabilities.
  - A **workflow** is a composition.
  - A **mini app** is the usable interface around capabilities and workflows.
  - A **widget** is one view inside that interface.

  These are not a rigid hierarchy. The operator asked "what exactly are we adding?"
- **Where:** L595 ("mini apps are ideally extensions"), L665, L726, L744-768
- **Status:** SUPERSEDED in part. D§11 L393 says "mini apps are not just extensions": a mini app is one container shape with optional parts (D§7.1). R20 L47-50 adds **plugins** (MCP/tools + skills + model + hooks) as the unit of the organogram. The word "extension" now has no clear home, so naming is OPEN.
- **Why it matters:** The agent needs one vocabulary, otherwise it will create the wrong kind of artifact.
### S40. Stable public interfaces carry extensibility
- **Idea:** An extension declares its dependencies, supported interface versions, operations, permissions and data migrations. QMX discovers them. "An extension can change without changing QMX's core." Sharing does not need a marketplace.
- **Where:** L726, L772-786, L892 (Omarchy, VS Code)
- **Status:** SHIPPED in part. `app.toml` is content-hashed with `uv.lock` (D§7.1 L244). The app catalogue works like a registry (L247). There is a network allow-list and a list of allowed operations (QI L214). Interface versioning and data migrations are OPEN.
- **Why it matters:** The operator's stated reason for all this: "I don't want to spend a lot of time maintaining" (L726).
### S41. VS Code and Zed
- **Idea:** VS Code's manifest declares contributions, compatibility, activation and local versus remote placement, and has webviews for panels. Zed has typed contribution kinds plus WebAssembly.
- **Where:** L595, L667-669
- **Status:** STILL VALID as a reference. The side panel and Copilot layout follow it (L1060).
- **Why it matters:** These are models for what an app manifest declares.
### S42. Assistant specialisation: skill, tools, hooks
- **Idea:** Give the Copilot a skill package for building compositions, real catalogue and context tools, and runtime enforcement hooks. The operator asked for a dedicated hook system and skill (L429).
- **Where:** L429, L558-572, L595
- **Status:** Hooks are SHIPPED (P20). **The skills are three placeholders** (QI L575). R20 L47-50 puts skills into plugins. OPEN.
- **Why it matters:** Without the build-mini-app and build-workflow skills, the Wednesday minimum fails (R20 L82-87).
### S43. One copilot, many sessions, specialists behind it
- **Idea:** The operator talks to one "QMX Copilot", like Copilot in VS Code or the Codex app, across many separate sessions. Specialists are spawned behind it. Workflows reduce how much the agents have to improvise. Departments become optional groupings, and "a mini app can represent a department".
- **Where:** L726 (operator rejects "one assistant" as ChatGPT framed it), L886-892, L906-928
- **Status:** SHIPPED with one copilot (P15). Screen copilots are OPEN (QI §e item 2). The organogram as plugins is R20 L47-50. Desks and Quants are SUPERSEDED (QI L409).
- **Why it matters:** QMA v2 must keep one front door and still support delegation. Sub-agents follow Claude's pattern (R20 L53-56).
### S44. Book/BMS replaceable, and QMF as a construction kit
- **Idea:**
  - Scalping Book v1 and v2.
  - Two MIS versions running together, in production plus shadow, or for separate consumers.
  - A portfolio without Book or BMS (Kelly, XGBoost, a neural network).
  - "System A" versus "System B".
  - Refactor once, so that each new system needs no platform refactor.
- **Where:** L891, L958-984, L1063-1067, L1123-1143
- **Status:** OPEN. QMN still wires Bot → Book → BMS. The UI renamed Books to **Pods**, "one risk/sizing method" with live and paper sides (QI L186). D§1 keeps the domain core unchanged. QML will change (R20 L18).
- **Why it matters:** A mini app can **be** a trading system. The agent authoring one must know the QMN and QMF interfaces (L1067), not write free-form Python.
### S45. "Identity-bearing" changes and sequential replacement
- **Idea:** Any change to code, parameters or weights creates a new version identity. Replacement is sequential: develop, paper trade, retire the old version, then activate the new one. "Rolling back software does not undo orders already executed."
- **Where:** L970, L978, L1063, L1147-1161
- **Status:** SHIPPED for apps (P14): road to live, money apps propose only, the operator signs.
- **Why it matters:** Agent edits to a live app must open a new version on the road, never a hot patch.
### S46. Readiness dashboard
- **Idea:** Before trusting a new system, show that it works, that latency is acceptable, and where it is deployed.
- **Where:** L1063
- **Status:** SHIPPED in part. Host-provided observability gives heartbeat, metrics, breaker and placement (D§7.7). The app detail pane shows road evidence (QI L209-216).
- **Why it matters:** Promotion cards prepared by the agent need this evidence.
### S47. Headless capabilities, CLI and command nodes
- **Idea:** Not everything needs a UI. An app can contribute only a computation, an adapter or a CLI operation. A command node shows a declared command, streaming logs, cancel and identified outputs, in a terminal-like view.
- **Where:** L891, L986-992, L1070
- **Status:** SHIPPED in part: the headless app shape (D§7.1 L264), `run_job`/`job_logs` (D§5.6b L197), and a terminal per job in the UI drawer (QI L107). Cancel is `not_implemented` (QI L565). A real terminal is OPEN (QI §e item 5).
- **Why it matters:** Long agent jobs need to be visible and stoppable.
### S48. GPU: what is needed, where it runs, how results come back
- **Idea:** These are three separate decisions. Training can happen on a rented GPU and inference elsewhere. Run checks first: is a GPU subscription set up? Does this machine have a GPU?
- **Where:** L892 (Colab, Modal, E2B), L994-1002, L1072
- **Status:** SHIPPED in design: resource declarations, ONNX "train once, run anywhere", models as Library artifacts (D§5.6b L201-207). R20 L74-75 says sandboxes are not needed by default.
- **Why it matters:** The agent asks for resources and never configures drivers itself (D L207).
### S49. Structured app context, not screenshots, and the session owns its context
- **Idea:** The Copilot receives the selected object and version, the highlighted chart interval, the configuration and the run status as data. The operator: "we can have a proper schema". Switching tabs does not change the target of a task that is already running.
- **Where:** L930-936, L1060, L1103
- **Status:** OPEN. The UI has an "Aim" control (QI L112-117), but there is no context schema in the backend.
- **Why it matters:** App-use sessions depend on it.
### S50. Two session profiles: authoring versus app use
- **Idea:** "Firepower" differs by profile. An app-use session can inspect, run and ask the app's agents. An authoring session can change implementations. A change-request artifact carries work from app use into authoring. Each app ships a **copilot integration profile**: its exposed context, operations, documentation and skills, and permitted interactions.
- **Where:** L1060 ("each application should ship with a version of a copilot"), L1063, L1094-1117
- **Status:** OPEN. September's `product_session` with these two profiles was never accepted (QI L142, L363). Permissions were parked on 2026-10-04 (QI L117).
- **Why it matters:** This is the permission model for an agent that both uses and edits apps.
### S51. App lineage, documentation as a skill, and logs
- **Idea:** A mini app records the session that built it. Its documentation becomes an agent skill with hooks. Every workflow keeps logs and traceability.
- **Where:** L1060
- **Status:** The `errand` field on MiniApp exists in the UI only (QI L140), so that part is OPEN. Logs and the journal are SHIPPED (D§7.7, P08).
- **Why it matters:** An agent maintaining an app needs its history and its manual.
### S52. Harness, context, loop and graph engineering
- **Idea:** These are the four parts of agentic engineering. "Loops can become mini apps" (L1060). Loops are like skills, and Caliper evaluates them.
- **Where:** L1060
- **Status:** STILL VALID. R20 §2.4 (L196-218): the graph runs inside the harness, loops are nodes, and every agent node loops on evidence.
- **Why it matters:** This is the layering QMA v2 follows.
### S53. Memory: context, durable memory and work records
- **Idea:** Keep conversation context, durable memory (with provenance and scope) and factual work records apart. Retrieval is scoped with sharing rules. RLM helps with investigation but does not replace memory.
- **Where:** L888, L940-956
- **Status:** SHIPPED in P07/P08 (one provider per profile, plus the journal). R20 L41-42 changes this: use each SDK's default memory under QMX's pluggable layer. OPEN.
- **Why it matters:** Apps have their own `memory.db` (D§7.6b L325), so the agent must not mix scopes.
### S54. Skill creation is separate from skill activation (Caliper)
- **Idea:** Draft a skill, validate it, test its behaviour and activation (with and without the skill), save it as a version, then activate it. The assistant may create skills for other agents. Creating a skill does not grant it authority.
- **Where:** L726, L806-826
- **Status:** OPEN. August's AD-22 self-improvement pipeline was dropped (QI §e item 8). R20 L245: "lessons write back to skills (with approval)".
- **Why it matters:** Apps ship skills. If the agent can edit skills, the edits need gates.
### S55. Portfolio Manager, not Product Manager
- **Idea:** PM means Portfolio Manager. Review the role's responsibilities, not only its label.
- **Where:** L726, L840-846
- **Status:** SHIPPED in the UI, where the Portfolio copilot targets are "Portfolio Manager" and "Trader" (QI L194).
- **Why it matters:** This settles the vocabulary for any Portfolio plugin.
### S56. Multiple brokers and accounts, with explicit targets
- **Idea:** A conversation or system is tied to its app instance, version, environment, broker, account and data sources. Picking another account on Home must not change it. Instruments with the same name at two brokers are not the same instrument. The right to analyse data and the right to trade it are configured separately.
- **Where:** L1032, L1072, L1185-1195
- **Status:** SHIPPED for the broker model: many brokers, connections and accounts (D§11 L405, P18). Binding targets into context is OPEN.
- **Why it matters:** Workflows built by agents must carry their targets explicitly.
### S57. n8n's role
- **Idea:** Borrow n8n's interaction ideas, JSON format, Code node, AI workflow builder, templates and sub-workflow calls. Do not adopt its runtime (queue mode with Redis and workers). Embedding its editor needs an OEM licence. Study its node system.
- **Where:** L7, L160-168, L259, L316, L383, L389, L891
- **Status:** STILL VALID. "The workflow design started from n8n" (R20 L66).
- **Why it matters:** It confirms that QMA v2 owns its runner and editor.
### S58. Build the enabling system, not every idea
- **Idea:** The examples are tests of extensibility, not a backlog: neural portfolio, energy intelligence, macro brief, alternative MIS, dataset builder, LSE tools. Sort ideas into accepted requirements, technical questions and seeds.
- **Where:** L892 (operator: "not every idea should be built"), L1018-1034
- **Status:** STILL VALID. Wednesday minimum (R20 L82-87).
- **Why it matters:** Scope control for v2.
### S59. Other references
- **Idea:** StrategyQuant and QuantConnect (heavy experimental operations), LSE (data, backtester, ML Studio, dataset builder, heat maps; worth its own browser-driven study), Cordis/DeepSeek Harness (reversible registrations), LangGraph, CIS (opportunities mapped to journeys), Jev/TypeSafe, Omarchy.
- **Where:** L313, L395-405, L722-726, L788-804, L848-870
- **Status:** Reference only. LangGraph was adopted (D§7.4) and then SUPERSEDED (R20 L63). The LSE study's result is unknown.
- **Why it matters:** Copy mental models only: "we are borrowing mental models" (L429).
### S60. The first proof slice and its uncomfortable acceptance tests
- **Idea:** The first slice: governed strategy → two Book configurations → compare → record → save the procedure. The tests: reconnect, one branch failing, interrupt and recover, edit while running, trace the inputs.
- **Where:** L172-182
- **Status:** The slice is SUPERSEDED by Macro daily bias as the first app (D§13 L535, P15) and by the Wednesday minimum (R20 L82-87). **The tests are STILL VALID.**
- **Why it matters:** Reuse these tests as the acceptance set for the v2 runner.
### S61. Is a new library needed? QMF is the one framework
- **Idea:** Extend QMF for data. Only create a composition library if the responsibilities do not fit elsewhere.
- **Where:** L595, L633-643
- **Status:** SUPERSEDED. The rebuild added `qmx-agents`, `qmx-apps` and `qmx-control` (D§4, D§9). QMF's role is now unclear to the operator (R20 L18).
- **Why it matters:** QMA v2 should name its package seams up front.
### S62. Workflows and cron are different things
- **Idea:** A schedule triggers work; a workflow is the work.
- **Where:** L595
- **Status:** SHIPPED: the `jobs/` schedules part of an app (D§7.1 L255). Cron workflows on the server (R20 L78).
- **Why it matters:** The agent sets triggers apart from definitions.

---

## 3. The operator's own requirements and positions

Positions are in order. The latest one wins.

1. The change is big but not a rewrite: "I don't think actually we are rewriting much" (L198).
2. Work continues on a server, and there are two modes, on-prem and server (L198, L321). Server placement can be "a simple toggle in the UI" (L321).
3. QMA is for agentic tasks. Workflows are "a very different thing… I don't want you to confuse that" (L198).
4. Both deterministic and non-deterministic work, with reach into nearly all of QMX (L198).
5. Workflows began as a storyboard: dump material, then build from it (L198). The storyboard "should be messy" (L1070).
6. Be "intentional by design". Not everything is a node, and connections must carry meaning (L313).
7. Reusable means tested: "for something to actually be reusable it has to pass tests" (L313).
8. A notebook or Jupyter-like node, encapsulating something like a genetic algorithm with declared outputs (L313). He still wants to see the code inside a node (L429).
9. The name is "Experimentation Board", not "research board", because QMA has research staff (L316).
10. The agent does most of the building while he talks to it, and he can build things himself too (L316).
11. Templates, and "accumulation of many workflows over time" (L316).
12. Defaults are required: "we should have defaults". He must also be able to create his own (L319, L429).
13. Mental models only: "we are borrowing mental models, we are not using OpenBB" (L429).
14. "Don't limit yourself on just trading ideas": ML, sentiment, data (L429).
15. Data from many sources, live and historical. Data handling is a separate concern from storage (L429).
16. Mini apps are extensions in the VS Code sense; a mini app opens in the sidebar (L595). The October design later narrowed this (D§11 L393).
17. Extensibility should cover the whole platform, not only indicators or Python (L595).
18. WF1/WF2-style agent research loops are "the birth of workflows" (L595).
19. Backend first, then UI. The UI can then "just slap on top" (L595, L889).
20. He "never said anything like one main assistant should be the interface" (L726). Then, at L886, he reverses this: one copilot to talk to, many sessions, and "one agent can handle other agents".
21. PM means Portfolio Manager (L726).
22. Goal: others can build on QMX without core edits, and he does not want "to spend a lot of time maintaining" (L726).
23. Every opportunity should link to a user journey for later UI work. Use CIS (L726).
24. The workflow assistant must be able to create skills for agents (L726).
25. The Copilot must be very capable: strong memory, RLM, local files, browser and computer use, "like Codex but for QMX" (L888-889).
26. Many configuration fields: data provider, broker, account. Everything is swappable (L891).
27. Several versions run side by side ("scalping book version one, … version 2"), and two MIS versions at once (L891-892).
28. CLI use, a CLI view inside a node, and webhooks. Study n8n's node system (L891).
29. GPU experiments on Colab, Modal or E2B. Server management, DevOps and trading-node changes without clashes (L892).
30. LSE-style ML Studio, dataset builder and macro or micro daily-bias apps (L892).
31. Codex subscription for the main agent, and possibly paid DeepSeek for other agents (L892).
32. "Not every idea should be built by Grok" (L892).
33. Sessions per job: one session builds a workflow, another a strategy, another an ML experiment (L1060).
34. App context comes from a schema, not screenshots (L1060).
35. Two kinds of Copilot use, with different "firepower": using an app versus authoring one. "Each application should ship with a version of a copilot" (L1060). Clarified at L1063: one global copilot plus a defined schema per app. Only the general copilot edits apps.
36. The four layers are harness, context, loop and graph, and "loops can become mini apps" (L1060).
37. A mini app keeps lineage: the session that built it (L1060).
38. Logs and traceability in every workflow (L1060).
39. QMN means "a trading VPS" that runs unattended. The placement choice must stay explicit: live only on his machine, or with an agent watching (L1063, L1067).
40. Replacement is sequential, with paper trading first: "I can't replace a book system and then have it trade tomorrow" (L1063).
41. QMF was meant to be the construction kit, and "things just got out of hand" (L1063, L1067).
42. Authoring must use the QMN and QMF interfaces, not random Python (L1067).
43. Multiple brokers, multiple accounts, and a default Home dashboard (L1072).

---

## 4. The complexity list (what QMA v2 must design for)

1. **Definition versioning and pinning.** Every workflow, app, skill and plugin has a content hash. Runs pin the hash, and edits create drafts (S10, S45).
2. **Lineage.** Track input → run → output → app version → building session, so you can answer "which inputs produced this?" (L180, S51).
3. **Invalidation.** Know what a change makes stale, and keep the distinction between projection and rerun (S12).
4. **Reproducibility and point-in-time data.** Pin data snapshots and avoid look-ahead from revised data (L473).
5. **Typed I/O with cardinality.** Broadcast versus pairing, collections, and schemas per output reference (S15).
6. **Effect, authority and idempotency descriptors per capability** (S05, S09).
7. **Durable long runs.** Per-node checkpoints, resume after a crash, and survival when the UI disconnects (S03, S08).
8. **Partial failure.** One branch fails while the others keep their results. Joins after a failure, retries, timeouts (L180, R20 L243).
9. **Retry without repeating side effects** (S09).
10. **Human gates bound to exact revisions,** with re-approval after any edit (S07).
11. **Run scope.** Run one node, a section or a whole procedure, with drafts sitting beside them (S14).
12. **Agent nodes that loop on evidence,** with a separate verifier and stop rules (R20 L245).
13. **Placement.** Local, VPS or GPU. Capability checks before a run. Results returned Git-style. No migration of a live run between machines (S27, S48).
14. **Single-writer storage across machines.** Remote work goes through the owning service (S28).
15. **Cost and budgets.** Model calls, tool calls, paid data, GPU hours. A router balances across providers per session (R20 L58-61, D§5.7).
16. **Permissions by session profile.** Using an app versus authoring one, the copilot integration profile, and grant intersection (S50).
17. **Context binding.** A session's target (app, version, broker, account, environment) must not drift when the operator switches tabs (S49, S56).
18. **Memory scoping.** Copilot, per app and per workflow. Sharing rules. Memory kept apart from work records (S53).
19. **Skill lifecycle.** Author, test (including tests with the skill removed), version, activate, with grants unchanged (S54).
20. **Custom capability validation.** Conformance, behaviour and usefulness, plus where the capability belongs (S32-33).
21. **Interface stability.** App manifests declare compatible interface versions and data migrations (S40).
22. **Live-system replacement.** Ownership of open positions and orders, sequential handover, shadow runs, no hot swap, and rollback cannot undo fills (S44-45).
23. **Several versions running at once.** Separate identity, state and consumers. No silent competition for one output (L980).
24. **Data recipes and live feeds.** Subscription ownership, staleness, catch-up and conflicting sources (S30).
25. **Observability.** Logs, heartbeat, breaker, placement, and evidence rather than logs (D§7.7).
26. **The money path.** Order-capable tools are never in any agent's reach, at build time or at invoke time (D§5.7, D§12 L477).
27. **Engine parity.** The same plugin or workflow must run on the Claude Agent SDK and the OpenAI Agents SDK (R20 L234-237).
28. **Graph validation completeness.** Cycles only through loop nodes, every port satisfied, a schema check before a run (S04).
29. **Granularity guidance.** Stop the agent producing hundreds of nodes, while letting the operator open any node up (S13, S18).
30. **Interpretation versus measurement labelling** on agent outputs (S06).

---

## 5. Open questions for the operator

1. **Vocabulary.** What happens to the word "extension"? Proposal: **plugin** = agent capability pack (R20 L47); **mini app** = runnable package (D§7.1); **workflow** = graph; **widget** = view. Is "extension" retired?
2. **Is the Experimentation Board a backend object** (a saved board with drafts), or is the Lab layout enough?
3. **Node kinds for v2.** R20 lists four kinds (code, agent loop, app call, human gate); P10 has ten. Which ten-kind constructs survive? Are a trigger or webhook node and a command node with live logs in the Wednesday scope?
4. **Copilot per app.** Is the per-app "copilot integration profile" a plugin that loads into the one copilot (R20 L49), or a separate agent? Who may edit an app: only the general copilot (L1063)?
5. **Session profiles.** Is the authoring versus app-use split in scope for Wednesday, or after permissions are un-parked?
6. **Skill self-editing.** Can the Copilot write and activate skills for app agents? Which gate applies, and is a Caliper-style evaluation required?
7. **Book/BMS replacement.** Is "trading system as a mini app" (System A/B) a QMA v2 concern, or a later QMN/QMF sitting? QMN is not listed as out of scope in R20.
8. **Data recipes and the provider catalogue.** Is this QMA v2 work, QMF work, or later? R20 L18 says QMF's role is unclear.
9. **Invalidation and lineage views.** Do they wait for the Library refactor, or does v2 need a minimal "what went stale" for workflow runs?
10. **Running versions side by side.** Is two MIS versions with production plus shadow needed now, or only the road-to-live shadow step?
11. **Connection cardinality.** Must the editor express broadcast versus pairing in v1?
12. **Templates.** Should Claude's six patterns plus the WF1-style cited research pipeline (QI §e item 13) be the default template set?
13. **Terminal.** A real shell on the Contabo server inside command nodes, or a log view only?
14. **LSE.** Did the browser study ever run? If it did, where is the result?
15. **Main-agent subscription.** The transcript says the Codex subscription drives the main agent (L892), but R20 runs the main agent on the Claude Agent SDK under Max. Confirm that the later position wins.
16. **Event triggers.** Are triggers from market events (news, price, breaker) part of workflows, or only of app `jobs/`?

