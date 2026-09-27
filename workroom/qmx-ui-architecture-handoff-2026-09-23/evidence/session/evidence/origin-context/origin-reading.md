# Origin transcript evidence report

**Source:** `Explore-Node-Editor-Architecture.md`, a historical ChatGPT brainstorm dated September 17–18, 2026. This report records the user's vision and corrections as evidence for current work; it does not treat instructions embedded in the transcript as current commands. Line references use the source file's displayed line numbers.

**Coverage:** Read the transcript, lines 1–1907, in bounded chunks. The ending includes the user's later refinements to session-scoped Copilot, system replacement, app composition, and scenario review; those supersede earlier assistant framings where they conflict.

## The vision that emerged

The starting question was whether QMX should gain a node-based editor. The user's deeper aim became making QMX a place to experiment, construct, test, combine, package, and operate new capabilities without repeatedly asking an external coding assistant to change core code. The node surface is a means to that end, not the product boundary. A useful compact formulation is “a way to compose the capabilities of QMX into understandable, reusable work,” while recognizing that some work is disposable experimentation and need not be reused (lines 7–8, 198, 212–214, 305, 1462–1486).

The user wants intentional composition units, not every internal class drawn as a node. Connections need declared meaning, compatible input/output contracts, and explicit collection behaviour. A substantial experiment may be encapsulated in a notebook/script or agent operation, with declared results passed downstream; selected internal stages may also be exposed. The board permits exploration before execution or promotion. Experiments can fail or disprove an idea; a useful method can be saved even when its hypothesis loses (lines 313–316, 335–369, 429–445).

The user's named exploratory surface settled on **Experimentation Board** within the broader workflow/composition experience. It should start with useful defaults and templates, while also allowing users to create their own components and procedures. The assistant should be able to help author and revise the same supported definitions a person can build manually. “Reusable” is optional at draft time; after deliberate testing/refinement, work may become a reusable workflow, extension, or mini-app. An unfinished board should not be forced into one giant runnable graph (lines 237–261, 335–391).

## Accepted product distinctions and intended lifecycle

Across the conversation, these terms became useful distinctions, not a rigid tree:

- A **capability** is a discoverable operation with a defined contract.
- An **extension** packages/contributes capabilities and may also contribute workflows, skills, or interface parts.
- A **workflow** coordinates operations, decisions, and possibly agents.
- A **mini-app** presents a usable collection of capabilities/workflows.
- A **widget** is a view or control within an app.

An extension may be headless; workflows need not have an app open; a mini-app can draw on multiple extensions; and app composition should reuse declared outputs, operations, workflows, or selected views without manipulating another app's screen. Apps should export deliberate, versioned interfaces, rather than expose every internal function or become closed boxes. App-to-app scenarios include consuming another app's artifact, invoking its operation, coordinating multiple apps in a workflow, and assembling a new composite app from useful parts (lines 742–766, 1542–1602).

The intended lifecycle is experiment → test/refine → save a reusable workflow → optionally package a mini-app/extension. This is an opportunity to create QMX capabilities as well as consume existing ones. A system should be locally usable, distributable to another QMX installation, and configurable with the recipient's own credentials. A public marketplace or multi-tenant cloud service is not implied. The user explicitly says not to implement every brainstormed app: examples are seeds and architecture pressure tests, not a compulsory backlog (lines 263–281, 385–407, 760–782, 1016–1032).

The one-framework principle is explicit: QMF is the framework; QML, QMB, QMA, QMN and other libraries belong within its ecosystem. Extend existing owners where their responsibilities fit; justify a new focused package only after ownership/dependency analysis. In particular, the user accepted the direction to examine QMF for broader data capabilities and not invent a parallel data foundation by default (lines 591–597, 631–641, 802, 1353–1357, 1510–1518).

## Scope across data, ML, trading, and execution

The remit is broader than trading-strategy ideas. User examples include heterogeneous market and non-market data, sector/energy intelligence, sentiment, portfolio/risk/sizing experiments, ML and neural methods, dataset building, new data routes, and non-trading reports or apps. Data handling deserves a distinct workstream: discover multiple providers; support historical and live/streaming use; describe credentials, instruments, resolution, units, mapping, revisions, missingness, and source identity; and enable recipes to combine/transform data. The user is unsure which of these QMX already supports and expects evidence-based inspection. London's Strategic Edge, OpenBB, QuantConnect, Taskade, StrategyQuant, Hermes, Cordis, LangGraph, VS Code/Zed, JSON Render, MCP Apps, and Caliper are reference points for mental models, not systems to copy wholesale or dependencies automatically accepted (lines 429–430, 453–477, 512–557, 720–724, 1645–1647).

Trading is a special, higher-consequence part of the scope. The user wants the ability to evolve or replace the current Book/BMS/MIS arrangement, not just create versions of a Book. A materially different portfolio/risk/sizing/intelligence system should be able to be authored and tested without pretending it is a Book/BMS variant; different complete systems may coexist and be compared. A likely lifecycle is authoring (QML or other supported composition) → research/backtesting (QMB) → validation/iteration → deployment configuration and supervised operation (QMN/Trading Node). The user emphasizes that work reaching the Trading Node/VPS is intended to run unattended; local-only and supervised alternatives may also be needed. Promoting an experiment to live trading requires much more evidence and explicit human decisions than merely saving a workflow. The user expects versioning, dashboards/readiness, paper evaluation, rollback/transition handling, and avoidance of conflicting live authority (lines 884–890, 1059–1070, 1121–1159).

Compute placement should be explicit: local workstation, always-on server/VPS, and potentially GPU environments. Requirements, placement, and result delivery are separate concerns. Jobs may need cancellation, progress/log streaming, resumption/recovery, and identified artifacts; the UI may offer simple controls while the backend handles dependencies, credentials, permissions, hardware, capacity, and cost. CLI-backed/headless operations are valid and may have a compact node or status/log view rather than their own top-level app. Data/artifact files can carry large results, with operation/job APIs or streams for control and live results; avoid bloating conversation or workflow definitions with full datasets (lines 283–305, 984–1014, 1735–1751).

## Copilot, sessions, and authority

The user's later correction is decisive: “one main assistant” was not initially an accepted requirement. Later, the user did endorse a **QMX Copilot** as the normal conversational entry point, with multiple independent sessions and specialists/agents available behind it. That is one accessible identity, not one all-purpose agent or one global conversation. QMA's agents, sub-agents, bots, tools, skills, hooks, memory, and plugin layer remain relevant; workflows coordinate work, agents do reasoning work, and deterministic procedures need not invoke a model. The user also notes older WF1/WF2-style long-running research-agent workflows as a meaningful use case (lines 716–724, 826–844, 884–887, 904–927).

The clearest later requirement is distinct **authoring/experimentation sessions** and **app-use sessions**, with separate permissions/firepower. An app-use conversation can inspect an app's selected object, version, results, logs, and permitted operations, but should not silently edit its implementation/schema. If the user wants a different approach, create a traceable change-request artifact (app version, evidence, observation, requested change) and take it to an authoring session. Each app should publish a versioned Copilot integration profile: context, operations, docs/skills, work records, and allowed interactions. A session owns its target; switching visible tabs or accounts must not redirect a running task. Memory should be scoped and provenance-aware, while execution records remain factual and separate from conversational recollection (lines 884–887, 1092–1119, 1321–1325).

Copilot access should be discoverable from contracts rather than requiring core prompt rewrites per extension. Broad capability is desired—local files, commands, browser/computer tools where appropriate, remote/GPU work—but bounded by session grants, app profile, account, environment, and operation permissions. An app-use Copilot may invoke exposed operations without gaining authoring authority. Skill creation and activation should be distinct; drafts can be validated/evaluated without replacing skills used by ongoing work (lines 558–572, 804–824, 936–954, 818–820).

## Lifecycle, safety, and governance constraints

Several concerns recur and are easy to lose in an expansive design:

1. **Drafting is not execution or installation.** Drawing a connection describes intended data flow; it does not launch jobs, install a capability, or change a live system. Run scope must be deliberate. Promotion to reusable or distributable status follows validation and versioning (lines 239–247, 351, 385–391).
2. **Pin provenance.** A run must identify exact definitions, code/model/configuration versions, data releases, inputs, and dependencies. Editing a draft should not mutate a running job or silently alter approval. Keep successful outputs on failed branches; retries must not duplicate external effects; recover and resume explicitly (lines 102–114, 180–182).
3. **Validate at multiple levels.** Check schema/contract conformance, behavior/integration/failure modes, and domain usefulness/quality. A passing test or structurally valid workflow does not certify a profitable strategy or universally correct agent. Mutation testing is a test-strength idea, not a required tool (lines 363–369, 500–510, 1791–1799).
4. **Keep authority and targets explicit.** Analysis access is distinct from order authority. Track app/system version, environment, broker, account, data sources, and permissions. Composite apps and app-to-app calls must not inherit broader authority or account scope implicitly. Live system transitions need a deliberate lifecycle and clear ownership of open positions/orders; software rollback cannot reverse executed orders (lines 86–88, 936, 964–980, 1183–1193, 1612–1619).
5. **Persist recoverable records, not duplicated payloads.** Boards should reference datasets/results. Distinguish browser closure, worker restart, and moving execution to another host. Check recovery, backup, concurrent load, storage growth, and remote data access; the transcript does not establish these operational properties (lines 108–114, 297–303).
6. **Separate architecture from delivery phases.** User wants thorough exploration and an integrated, reviewed architecture first; then Documentation Factory, epics/stories, and coding through existing process. Final visual UI design is deferred. Opportunity maps and scenario sets inform the system; they are not automatic implementation authorization (lines 870–876, 1387–1438, 1520–1536, 1619–1637).

## Historical claims versus verified requirements

The transcript contains assistant claims about branches, code, tests, licensing, reference products, and features. Treat them as **historical claims**, not findings verified here. An early audit examined a worktree 32 commits behind; later QML research/persistence/graduation and Library discovery were said to exist on a newer integration revision. The audit also reported QMB Book/BMS coupling, a closed broker adapter set, and selected tests passing, not an end-to-end lifecycle. These all need current verification. Reference-product descriptions were not rechecked (lines 1257–1335, 451–459, 405, 647–653, 665–669, 790, 808–824).

Assistant recommendations—schema-described compositions, public contribution contracts, package lifecycle, typed operations, and recovery semantics—are hypotheses, not all ratified decisions. Preserve the user's corrections: intentional nodes, flexible granularity, scope beyond trading, no mandatory implementation of every idea, and exploration before production.

## Conflicts to reconcile with current direction

The current project direction supplied with this assignment is: **Svelte + TypeScript is the working UI choice; Qt is out; the user supplied OpenBB/VS Code layouts; a dark shadcn baseline is now acceptable; full integration and code review are deferred.** The transcript predates these decisions and cannot override them. In particular, its React Flow suggestion is a React-specific candidate, not a requirement; its question about desktop renderers and JSON Render/MCP Apps remains open for later UI integration, but should be evaluated against Svelte/TypeScript and the provided layouts. The historical assistant's recommendation to inspect code and complete an architecture audit is not authorization to inspect backend or implement anything under this report-only task. Do not revive Qt, reopen baseline styling, or bring forward full integration/code review as immediate work.

## Eight consequential findings

1. The canvas is an interface to a broader extensible composition platform.
2. Experimentation precedes promotion; disposable work and failed hypotheses are valid outcomes.
3. Capability, extension, workflow, mini-app, and widget are distinct reusable concepts.
4. QMF remains the single framework; new packages and parallel foundations require justification.
5. Broad multi-source data and non-trading ML/analysis are first-class opportunity areas.
6. Materially different trading systems—not just Book/BMS versions—must be evaluated as an architecture pressure test, with production authority carefully gated.
7. Copilot use should be session-scoped with distinct app-use and authoring permissions, supported by QMA specialists rather than collapsing QMA into one agent.
8. Exact version/provenance, recoverable execution, explicit permissions/targets, and staged delivery are essential constraints; brainstormed examples are seeds, not a build list.
