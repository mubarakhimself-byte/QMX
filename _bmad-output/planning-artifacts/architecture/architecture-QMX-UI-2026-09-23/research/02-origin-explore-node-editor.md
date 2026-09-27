# Origin transcript — Explore Node Editor Architecture

**Sitting:** architecture-QMX-UI-2026-09-23  
**Role:** durable user-intent extract for the UI architecture sitting. Not architecture. Not implementation.  
**Primary source:** `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/origin-context/Explore-Node-Editor-Architecture.md` (ChatGPT brainstorm 2026-09-17 12:56 → 2026-09-18 11:12; file lines 1–1907). Read in full.  
**Companions read:** `origin-reading.md`, `ml-reference-notes.md`, `images/image-001.png`, `02-CURRENT-DIRECTION.md`, parent spines `architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` and `architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md`.

Line numbers below are the source file’s displayed lines. Unique nearby headings or phrases are given so a claim can be found even if line numbers drift.

## How to read this file

| Tag | Meaning |
|---|---|
| **user-spoken** | Operator dictation or an explicit correction in the origin chat. Binds this UI sitting unless `02-CURRENT-DIRECTION.md` supersedes it. |
| **assistant-proposal** | ChatGPT framing, vocabulary, or design in the origin chat. Useful; not ratified by being written. |
| **later overlay** | 09-18 Workflows spine, 09-23 pack-and-grant spine, `origin-reading.md`, `ml-reference-notes.md`, or `02-CURRENT-DIRECTION.md`. Use for conflict detection. Current-direction **U** rows win over origin assistant text. |

Historical assistant claims about branches, tests, n8n licensing, OpenBB release dates, and “what already exists in code” are **not** findings here. They stay dated reconnaissance.

---

## 1. What still binds: the product, not the canvas

**user-spoken (start).** The conversation opens as a node-editor idea inspired by n8n, already framed as larger than a drawing surface:

> “I want to explore the possibilities of adding a node-based editor… I feel like there is something missing, seriously. I really feel like it's not as simple as I intend it to be… it was built off the idea, I think, from N8N.”  
> — L7, first user turn, 2026-09-17 12:56.

**assistant-proposal, then user-spoken acceptance.** ChatGPT compacted the aim as “a way to compose QMX’s capabilities into understandable, reusable work” with the canvas as one interface, not the owner (L23–24, heading “What I think feels missing”). The operator accepted that wording:

> “Yes, composing the capabilities into understandable and reusable work. Wow, that's actually very good. That's a very good way to state it. Okay, so it's one interface to that, so it means it connects to almost everything…”  
> — L198.

**user-spoken (morning recap, still binds).** After a pause, the operator restated the same centre (L1446, 2026-09-18 09:30). ChatGPT’s recap, which the operator did not refuse, is:

> “Make QMX a place where you can create, test, combine, package, and operate new capabilities—without repeatedly asking an external coding agent to modify QMX’s core.”  
> — L1466–1468, heading “Where we actually got to”.

**user-spoken maintenance motive.** Extensibility exists so the operator (or another installer) can add work without reopening core:

> “The whole point of me proposing this is because I don't want to spend a lot of time maintaining the code base. And if I want to give this platform to someone else, same thing. Okay, I want them to be able to create new things on top of what we have…”  
> — L720.

**user-spoken: examples are seeds, not a backlog.** Energy intelligence, neural portfolios, dataset builders, LSE-like tools, and WF1/WF2-style research loops are pressure tests. They must not become a compulsory UI catalogue.

> “not every idea should be built by Groker… the ideas are so endless… I think we have now the tools.”  
> — L890, near “I want you to understand.”

**later overlay (`02-CURRENT-DIRECTION.md` U).** Restates the same product: discover and construct capabilities, then test, reuse, and operate them. Historical sample apps are examples, not a closed launch backlog. That overlay is current law for this sitting.

UI implication that still binds: the node editor is a construction surface inside a composition platform. Shipping a pretty canvas without capability discovery, packaging, copilot seats, and headless reuse would miss the origin.

---

## 2. Capability / extension / workflow / mini-app / widget

The five-noun split is **assistant-proposal** that the operator repeatedly accepted and used. It is the vocabulary this UI sitting should keep, reconciling it with parent AD law rather than minting a parallel ontology.

**assistant-proposal (canonical table).** Heading “What exactly are we adding?” (L742–754):

| Noun | Assistant wording | Example in that table |
|---|---|---|
| **Capability** | “An operation QMX can discover and invoke.” | Retrieve a dataset, calculate a feature, evaluate a model, run a specialist task |
| **Extension** | “A versioned package that contributes capabilities and, optionally, workflows, skills, or interface components.” | An energy-sector analysis package |
| **Workflow** | “A defined composition of operations, agents, and decisions.” | Acquire data → features → exceptions → report |
| **Mini-app** | “A usable interface around a collection of capabilities and workflows.” | Energy Intelligence workspace |
| **Widget** | “An individual view or control within that interface.” | Liquidity chart, dataset table, model comparison, code editor |

Immediately after: they are **not** a rigid hierarchy. An extension may be headless; a mini-app may draw several extensions; a workflow may run with no mini-app open (L756).

**user-spoken acceptance of the split.** After OpenBB “app groups widgets and links shared parameters”:

> “an app can group widgets and link shared parameters such as dates, portfolios, origins. Now that's a clear difference, it's perfect.”  
> — L593.

And on VS Code as the mini-app mental model:

> “mini apps are ideally extensions, unless I'm wrong, but ideally, they kinda are the same thing. Same way VS Code has extensions, and if you look at it, they are just mini apps on top of it.”  
> — L593.

**user-spoken: all of them, not a pick-one.** The operator asked whether QMX was adding mini-apps *or* extensions *or* widgets (L720). The assistant answered “all… as one coherent extension system” (L742). The operator did not refuse; later speech uses all five nouns together (“we are combining apps, extensions, and is it widgets”, L1065).

**user-spoken: QMA workflows ≠ this composition surface.** Early correction, still load-bearing for UI naming:

> “What QMA has is for long-running agentic… However, the workflows, maybe the name is confusing… I don't want you to confuse that two, please.”  
> — L198.

**user-spoken: one framework.** QMF stays the framework; QML/QMB/QMA live under it. Do not invent a parallel data foundation by default (L593: “only one framework, which is QMF”).

**later overlay (09-18 AD-1 / conventions; 09-23 AD-1).** Same nouns. Pack-and-grant adds: a **pack** declares ops / optional views / requested access / optional copilot profile; the **host grants**; a mini-app is an **installed instance**. Copilot is one platform capability, not a field every pack must ship. UI sitting must show optional-copilot chrome, not a copilot on every app.

**Conflict to watch.** Origin assistant sometimes treats “mini-app ≈ extension”. Parent law keeps them distinct (extension/pack contributes; mini-app is the installed instance; widget is a view). Use parent nouns on screen copy.

---

## 3. Authoring vs app-use (two firepowers)

This is the origin’s strongest UI-session law. 09-18 captured it as `ProductSessionProfile` `{authoring, app-use}`. The UI sitting still has to **place** those seats.

**user-spoken (the story).** Two conversations, different harnesses, VS Code as the picture. Heading context: user turn 2026-09-17 18:30, after attaching the Taskade screenshot (L1052–1058).

- One session can be **building** (workflow + node editor, strategy, portfolio, ML experiment). Another session can be **using a mini-app**.
- In-app copilot lives on the **extreme right**, “more like how GitHub compiler is there” / VS Code Ctrl-Alt-B / Claude Code / Codex right panel — “a secondary panel.”
- In-app copilot may inspect, run exposed operations, ask specialists inside that app, watch the UI change **or** pull answers without changing the UI.
- To change implementation, the user takes an artifact/prompt back to the **main agent UI**.

Firepower:

> “When I'm now talking and I'm just trying to see or interacting with an app… Each deserves different firepower.”  
> — L1058.

> “if the co-pilot can access it, it doesn't have the ability to edit or improve it. However, what has the ability to edit and improve it and create new versions of it is the general co-pilot.”  
> — L1061.

> “each application should ship with a version of a copilot… definitions of the access that the co-pilot should have for that application.”  
> — L1058.

**assistant-proposal that the operator then used.** Heading “The two copilot use cases are now distinct” (L1092–1108): one copilot identity, two session profiles; app-use mints a **change-request** (app version, inputs/results, observation, proposed change); authoring develops v2; v1 and its running work stay. Session owns context; the visible tab does not silently retarget a running task.

**user-spoken: structured context, not screenshots, for in-QMX work.**

> “I don't think I want to give it screenshots since everything is in its own app… browser use, computer use, those come when we need external use cases.”  
> — L1055.

**user-spoken: sessions stay independent.**

> “in one session, I would be in the UI of creating a workflow and I would need the note-based editor view. Then, in another session, I could be creating a strategy… In another session, I could be carrying out an experiment in ML.”  
> — L1055.

**later overlay (`02-CURRENT-DIRECTION.md` U).** Shared copilot capability; independently scoped conversations; switching apps restores the relevant history instead of merging; a copilot is **optional per app**. Matches origin firepower + 09-23 “pack may omit copilot_profile / instance may omit in-app panel.”

**later overlay (09-18 AD-8 / AD-29; 09-23 AD-3).** App-use must not apply a change-request. Tab is not a session. Panel dispose does not cancel durable work.

UI implication: design two copilot *surfaces* (main/authoring workspace vs optional in-app right panel) over one product identity. Do not ship one global chat that edits whatever is on screen.

---

## 4. Unnamed home / general copilot seat

The origin never minted a third `ProductSessionProfile`. It **did** name a seat that is not “inside a mini-app”:

**user-spoken names.** “quant mind co-pilot” (L884); “the general co-pilot” (L1061); “main agent UI” (L1058); talking about Library items and default sections of the application without being inside a mini-app (L884: “let's say I want to talk about a specific strategy… think of it like the Codex app, but expanded”).

**user-spoken home dashboard.** Distinct from opened apps:

> “you have a home dashboard by default. You already saw that. I sent you an image earlier.”  
> — L1070.

**assistant-proposal (do not confuse with user law).** Early “one main assistant should be the interface” (L609–610). **user-spoken rejection** the same afternoon:

> “I never said anything like one main assistant should be the interface. You have to differentiate the difference between a workflow and an agent… QMA already has agents in there, they are specialists.”  
> — L720.

Later the operator **did** endorse one conversational identity with many sessions and specialists behind it (L884, L908–922). That is **one accessible name**, not one all-purpose agent and not one global transcript.

**later overlay conflict.** 09-18 AD-8 required `app_instance_id` on product sessions — no honest “nothing selected” home seat. 09-23 named amendment: `app_instance_id` MAY be absent when `profile=authoring` (main/home); still required for app-use; **no third profile**. 09-23 open question: revisit a third seat only if this UI sitting proves authoring-with-absent-instance is not the main workspace.

**later overlay (`02-CURRENT-DIRECTION.md` U).** Platform destinations **above** the rail divider exist independently of opened apps **below**. Home contents are still to design. That is the chrome this sitting owns; 09-18 deferred it as GAP-0081.

UI implication: the unnamed general seat is the **main/home copilot + home destinations**, not a third legal profile unless this sitting proves two profiles cannot host it. Invoke-from-home still needs an explicit instance (09-23: authoring with absent instance may not invoke).

---

## 5. Loops becoming mini-apps

**user-spoken (almost an aside; still binds).** In the 18:30 dictation, among harness/context/graph engineering:

> “Oh, by the way, loops can become mini apps. I almost forgot, and then graph engineering.”  
> — L1055.

Nearby, the operator treats long-running WF1/WF2 research-agent loops as a workflow that can later become testable strategies (L593), and treats a successful experiment as something that **graduates** after tests (L313, L1069: “by the time something is converted into a mini app, that thing should have passed a lot of tests”).

**assistant-proposal.** Experiment → test/refine → save reusable workflow → optionally package a mini-app (L387). A Loop in later parent law is **node state**, not a Skill and not a graph cycle (09-18 AD-4).

**later overlay (09-23 AD-9).** Daily path: yap at authoring → Graph Template → runs → **pack export** after validate. Packaging a loop exports the operations it calls; it does **not** mint a new loop engine.

UI implication this sitting must still honor: a loop that has been tested should be **packageable into a mini-app / pack** with a real graduation gesture (export, version, optional UI). Do not leave loops as canvas-only scribbles, and do not invent a second loop runtime to make them feel like apps.

---

## 6. Graph vs code vs dashboard

The origin refuses a single-surface product. Different work needs different views; they share one platform.

**user-spoken: node editor is one session view among several.** Quoted in §3 (L1055): workflow session needs the node-based editor; another session creates a strategy; another a portfolio; another an ML experiment. “UI is going to be the biggest issue.”

**user-spoken: not everything is a node; connections need meaning.**

> “not everything is going to be in the node or in the workflow seriously… we need to be very intentional what is in the workflow system… to be able to connect point A to point B, the connection itself has to have a meaning… Whether you are having a one-to-one, a one-to-many, or a many-to-many…”  
> — L313.

**user-spoken: notebook/code as a first-class node, internals not auto-exploded.**

> “you could have a notebook canvas in there, or a notebook node… Think of it like a Jupyter notebook… the results are what are passed to go to the next connection…”  
> — L313.

Then a correction that **some** code visibility is wanted:

> “those internals do not each need a visible node. I mean, I would argue to differ, but it depends… I would still need, like, I don't know a simple node which shows the chord [code] or something.”  
> — L429.

**assistant-proposal, not refused.** Encapsulation available, not compulsory. A notebook can be one node, expose its code, or expose selected stages (L445). Collapsed strategy node shows ports; expanded opens QML authoring (L233) — operator called that “true, true” (L316).

**user-spoken: dashboards and widgets for operating, not only for authoring.**

> “I'm seeing why widgets are very necessary because widgets are going to be making up dashboards.”  
> — L1070.

Readiness / operate:

> “we need a dashboard that shows: okay, this works, the latency works, we deployed it, stuff like that.”  
> — L1061.

**user-spoken: CLI inside a node, not a fake terminal app.**

> “not everything needs to be in the user interface… we can have a CLI use case… even in the workflow… we can just have a CLI render in the node.”  
> — L884.

**assistant-proposal (Taskade construction model).** After `image-001.png`: the workflow is **part of the app’s construction, not the entire app definition** (L1163–1175). Three related assets in one authoring experience: Experimentation Board (behaviour), presentation definition (widgets/views), app package (config, deps, docs, copilot profile). Not necessarily three separate editors.

**later overlay (`02-CURRENT-DIRECTION.md` U).** Layout family:

- Platform shell: rail, shared destinations, divider, opened apps.
- Main copilot: conversation + flexible tabbed preview/work area.
- Mini-app: app-specific navigation where useful, substantial widget canvas, optional right copilot.
- Authoring and ML: “original app/VS Code-like family; central graph can contain code/data/model operations; code/detail expansion; right copilot.” A node may open code, diff, inputs, parameters, outputs or run details **without losing graph context**.
- **P:** select once for a compact inspector; explicitly expand into a detail tab for deeper code/data. Prototype against original expansion arrows. No universal lossless code-to-graph conversion.

UI implication: graph, code, and dashboard are **co-equal presentations of operations**, not three products. Do not freeze n8n-as-the-app or dashboard-kit-as-the-app (09-23 paradigm explicitly rejects both as the centre).

---

## 7. Experimentation Board

**user-spoken name (rejects “research board”).**

> “the research board. No, I don't want to call it that. No. No, no, no, no, no. Let's call it the experimentation board. The reason I don't want to call it that is because QMA has dedicated research staff…”  
> — L316.

**user-spoken: storyboard / draft sheet, not instant execution.**

> “Imagine a storyboard… you dump stuff, then after dumping stuff, you kinda like use that for inspiration. Like, that's where this all started from.”  
> — L198.

> “think of it like this for something to actually be reusable it has to pass tests… why would you create an execution dependency on something that is not even a draft it is an experiment”  
> — L313.

**user-spoken: experiments may fail; that is valid.**

> “an experiment can pass, fail, or you learn and improve.”  
> — L316.

**user-spoken: defaults and templates; humans and the assistant use the same catalogue.**

> “do you really expect me to use blank things out of the box? No, we should have defaults.”  
> — L319.

> “If we are able to get this thing to run and pass… Are you seeing how N8N has templates? We should be able to create templates also.”  
> — L316.

> “Remember, the agent I'm using inside this system is the one doing most of the stuff. So it's creating the nodes, it's running the experiments. I'm just there talking with it… I can also come and like create my own. It doesn't mean the agent only has access to it.”  
> — L316.

**assistant-proposal, accepted in spirit.** The board is not obliged to become one giant runnable graph (L243). “Run” has a scope: selected operation, connected executable section, or a defined procedure. Drawing connections describes intent; it does not submit jobs, install a capability, or change a live system (L351).

**later overlay (09-18 AD-4 / AD-13).** Board layout is **client-only**. It is not a registry kind, not a Mission, not automatic execution. Display names and board layouts are UX; a saved runnable pins code/config/data/model/env.

UI implication: the Experimentation Board is the named authoring canvas inside the workflow/composition experience, not a separate “Research” app. Draft vs run vs package must be visible. Empty-canvas-only is forbidden (parent AD-20: ship defaults).

---

## 8. Headless vs visual

**user-spoken.** Capabilities need not own a top-level page.

> “not everything needs to be in the user interface. Some things can be in the back end… CLI use case… CLI render in the node.”  
> — L884.

> “how are we going to be able to deploy different… portfolio risk management… If I want to have two versions of the MIS working in a go, because now that does not need to render in the UI.”  
> — L884.

> “headless capabilities should be either specific to a mini app or the node-based editor… they should be a node literally… we can reuse them multiple times, they can be used in workflows.”  
> — L1069.

**user-spoken: local vs server is a placement choice, not an agent requirement.**

> “this thing has to have access to our VPS. So, those are two modes working on-prem and then working on, you know, in a claude somewhere.”  
> — L198.

> “it can be a simple toggle in the UI, and then the back end carries the rest.”  
> — L319.

> “by the time something reaches the VPS, it means it can work unattended to.”  
> — L1065.

Also: some work should trade only while the operator is live on the machine, or with an agent watching (L1065). Unattended is a **declared** mode, not the only mode.

**assistant-proposal (placement).** Heading “Headless capabilities, GPUs, and CLI access fit the same model” (L984–998): an extension may contribute only a computation, adapter, CLI-backed operation, schedule, or deployed service. Optional UI = configuration, status, logs, result inspection. Separate **what the job requires, where it runs, how results return**. GPU training vs later inference may be different machines.

**later overlay conflict.** 09-18 AD-15: compute placement is **preflight**, not a toggle sticker. States: available / configured / authorized / reachable / healthy. The origin “simple toggle” is user hope; parent law forbids promising durability because a remote worker exists. `02-CURRENT-DIRECTION.md` U: mini-apps and workflows may be UI-oriented, backend/headless, or mixed; a useful capability need not have its own UI; a headless capability may have an optional configuration/inspection surface without making that surface a runtime requirement.

**later overlay (09-18 AD-17 / AD-21; 09-23 AD-1).** Headless packs appear as reusable AD-3 steps with no navigation. UI mount/dispose must not start/kill durable backend work. Deep behaviour of an operation is identical across that operation’s supported doors.

UI implication: every public operation needs a **headless path**. Visual chrome is optional. Status/log/CLI-in-node is enough for many steps. Do not design a world where closing a tab cancels a VPS job.

---

## 9. ML and non-trading (first-class; LSE layout is not)

**user-spoken: trading is the motive, not the ceiling.**

> “ESQMX is about trading, but doesn't mean that we're only taking trading ideas… We can try some ML stuff. There is a new model called Jev… it could be something about market sentiment or data handling.”  
> — L429.

> “That can end with a dataset, model, report, alerting procedure, or mini-app. **It does not need to produce a trading bot or pass through a backtest.**”  
> — assistant L471; operator had already demanded this scope.

**user-spoken: ML work is an ordinary session type** (L1055: “carrying out an experiment in ML”). Neural nets, XGBoost, custom MIS models, dataset builders, energy-industry intelligence, macro briefings are **seeds**.

**user-spoken: LSE is a capability reference, not an instruction to clone a product.** First mention (L720): attach londonstrategicedge.com; “it deserves its own session.” Later enthusiasm (L890): data, backtesting, **“ML studio of our own”**, charts + copilot, dataset builder, websockets. Explicitly: mental models, not “we are using OpenBB or Taskade” (L429).

**later overlay — SUPERSEDES LSE-as-layout (`02-CURRENT-DIRECTION.md` U, latest correction):**

> LSE's ML Studio UI is rejected as a layout/model for QMX. Its ML capabilities can inform coverage. Do not recreate a fixed Train/Optimise form as the default ML experience. “ML Studio” is a working label for capabilities/composition, not approval of a separate rigid application.

**later overlay (`ml-reference-notes.md`).** Observed LSE surfaces (Markets strip, Workspace IDE/notebook/terminal, prompt-to-code, model catalogue, Train form, Optimise as a separate prerequisite-aware stage, Walk Forward risk fields) are **coverage hints**. Proposed QMX adaptations in that file are **assistant/research proposal**, not operator layout law. No sign-in, training, or optimisation was performed.

**later overlay (`02-CURRENT-DIRECTION.md` U).** Non-trading exploration and ML are first-class. Paper trading is relevant only where a capability executes trades or materially affects trading/risk behaviour. General data tools, headless utilities, and non-trading ML need suitable functional/operational evaluation instead. No universal week-or-two paper gate.

UI implication: ML lives on the **same authoring family** (graph that can contain code/data/model ops, expand to code/diff/params/outputs, right copilot). Do not ship a separate Train/Optimise studio as the default ML app. Keep risk/sizing/compounding visible when the work actually touches trading.

---

## 10. Image-001 (Taskade Flows) — what it is and is not

**Provenance.** User attached `images/image-001.png` at L1052 (2026-09-17 18:30) while asking how mini-apps will be built: “Is it via a node-based editor like Tascad? … Let me show you a screenshot on their website” (L1069).

**Observed in the image (evidence, not QMX UI law).** Taskade workspace “Pipeline that scores every lead”:

- Left: app/project chrome, key-features list, Gmail connection card, Genesis AI prompt at the bottom.
- Mid-left nav: Projects, Agents, **Flows** (selected), Media, Connections.
- Main: Workspace / Preview App tabs; New, **AI generate**, Template; Workflows / All Runs.
- Canvas: trigger → AI score → branch ≥ 80 → notify owner / add to nurture.
- Header: Publish, Analytics, Users.

**assistant-proposal after the screenshot (L1163–1175).** Useful observation: the workflow is part of app construction, not the whole app. QMX analogue: Board + presentation + package in one authoring experience. Headless capability can have a reusable node without a top-level page.

**later overlay (`02-CURRENT-DIRECTION.md` U).** Original Excalidraw images and full dictation remain the foundation. Later Codex, dashboard, and n8n/Taskade references **add context; they do not replace it**. Thoughtful navigation improvements are invited; exact coordinates are not frozen.

UI implication: keep Taskade’s *construction kit* lesson (AI generate + templates + flows + preview + connections + optional assistant). Do not copy this screenshot as QMX chrome. Platform rail + divider + opened apps is current-direction law; Taskade’s left nav is a donor, not a spec.

---

## 11. Copilot power, specialists, and “yap to build”

**user-spoken identity.** “we can call it the quant mind co-pilot” (L884). “I would prefer being given the tools and I just yap at the QMX co-pilot, and we build that stuff on a daily” (L890).

**user-spoken breadth (bounded by grants, not by screenshots).** Local files, browser, computer use, Codex-class desktop feel, memory, RLM when needed, hooks, QMA plugin layer (L884–890). Settings for data providers, brokers, accounts, GPU subscription vs local GPU (L884, L1070).

**user-spoken: workflows do not delete agents.** WF1/WF2 long-running research agents with their own computer, producing tables, looping (L593). Specialists remain; the copilot is how you talk.

**assistant-proposal (L908–936, heading “One copilot to talk to…”).** QMX Copilot is the normal entry point; multiple independent conversations; specialists behind it; inspector for delegated work; they need not occupy main navigation as dozens of chat windows. Switching tabs makes new context *available* but must not retarget a running task. Powerful ≠ every extension inherits machine and trading-account access.

**user-spoken skill authoring.** The workflow-authoring assistant may create skills for other agents (L720, Caliper link). **assistant-proposal lifecycle** (L812): draft → validate → test activation → versioned candidate → activate. Creation and activation are separate so a draft cannot replace a live skill.

**later overlay (09-18 AD-9; 09-23 AD-3 / AD-7).** Copilot discovers **grants**, not prose. Skills describe; they do not grant. Weak models operate through schemas. Installing an app must not rewrite core copilot instructions (origin L1748–1749; parent AD-9).

---

## 12. Data, library, app-to-app, trading-system honesty (UI must not lie)

These are backend-heavy origin requirements. The UI sitting still has to **surface** them honestly.

**user-spoken multi-source data.** Live and historical, many providers, polling/streaming/resolution, OpenBB/QuantConnect as mental models (L429, L593). Settings grow API/CLI provision (L593). **assistant-proposal:** storing data ≠ making it discoverable, combinable, transformable (L477). Recipes, not only file paths.

**user-spoken Artifact Library.** “we have a library, as in it's meant to be should I call it an artifact library. So for now, it's where we are storing most of the strategies. The thing is, we are going to upgrade it” (L1790). Talk about a specific strategy from the general copilot (L884).

**user-spoken app-to-app (morning of 09-18).**

> “isn't there a possibility of having apps combining with other apps?”  
> — L1446.

**assistant-proposal four modes (L1542–1582), operator: “perfect” / not refused:** (A) consume another app’s output; (B) invoke its capability; (C) workflow coordinates several apps (“unnecessary evil” but “I have no problem with it”, L1648); (D) new composite app from parts, while A/B/C stay independently useful. Interop via exported outputs/operations/workflows/views — **not** one app driving another’s screen (L552, L1600).

**user-spoken alternative systems.** Build a new Book, a new BMS, or a system **that is not a Book** (L198, L884, L1061). Scalping Book v1 vs v2. Two MIS versions. Kelly instead of Book. Sequential, not hot-swap; paper then live; “I can't replace a book system and then have it trade tomorrow” (L1061). Trading Node = unattended VPS; QMN is the host symbol, not the only possible composition (L1065).

**user-spoken no marketplace required.** Distributable to another QMX install with the recipient’s own credentials (L760–782, L890).

**later overlay (09-18 AD-10 / AD-11 / AD-12 / AD-14 / AD-23).** Four composition modes, Book/BMS default not ceiling, dummy Book forbidden, recipes wrap qmf-data, sequential handover, software rollback cannot undo fills. 09-23 inherits and does not re-elicit trading-system completeness.

UI implication: Library chrome over typed hits (not one mashed search). Composite apps must show **which instance, version, account, broker, data source** is in play. Home dashboard aggregates; it must not silently retarget execution (assistant L1187–1191). Alternative systems must not be forced into Book-shaped screens.

---

## 13. What the 09-18 sitting captured — and what this UI sitting still must honor

09-18 turned most of the **backend** origin into AD-1..AD-31 and then deferred **chrome**. That deferral is why this sitting exists. Gaps below are “UI still owes the origin,” not “09-18 was wrong.”

| Origin intent | 09-18 / 09-23 status | UI sitting still owes |
|---|---|---|
| Five-noun vocabulary | Captured (conventions; 09-23 pack/instance) | Screen copy and IA that keep the nouns distinct; optional copilot per app |
| Experimentation Board | AD-4: client-only projection, not a registry | The actual board: defaults, templates, draft ≠ run, code-in-node, CLI-in-node |
| Authoring vs app-use | AD-8 profiles, change-request AD-29 | Two visible seats, attachment/handoff, session ≠ tab, history restore on app switch |
| Unnamed home / general copilot | **Missed as chrome.** 09-18 required `app_instance_id`. 09-23 folded home into authoring-with-absent-instance | Home destinations above the divider; main copilot workspace; no invoke without an instance |
| Loops → mini-apps | AD-4 loop = node state; 09-23 AD-9 pack-export of ops | Graduation UX from a tested loop/board to a pack/mini-app |
| Graph vs code vs dashboard | Deferred as GAP-0081 “no final visual layout” | Co-equal surfaces; expand-without-losing-graph; no LSE Train/Optimise default |
| Headless first-class | AD-17 / AD-21 / 09-23 AD-1 | Optional inspection; jobs survive panel dispose; placement honesty (not a fake toggle) |
| ML / non-trading | AD-11 class 3; AD-31 recipes | First-class authoring family; paper gate only where trades/risk are real |
| json-render / MCP Apps | AD-17 adapters, unpinned | Consider as view adapters; native panes first; they cannot grant |
| App-to-app | AD-10 four modes | Composite chrome without merging screens or unioning authority |
| Artifact Library | AD-2 rails | One Library chrome over typed hits; talk-about-a-strategy from home |
| Portfolio Manager label | AD-22 | Display label only; no `desk_slug` rewrite here |
| Final visual UI / BMAD UX | Explicitly out of 09-18 | This sitting designs chrome; `02-CURRENT-DIRECTION.md`: skip BMAD UX, Figma is not the workflow |
| Startup / splash / first-run | Not in origin as PyCharm/DaVinci | **later overlay U** in current-direction — honor it here, do not back-port into origin claims |
| Svelte / shadcn / Svelte Flow | Origin assistant floated React Flow (L168) | **Superseded** by current-direction U. Qt is out |

**09-18 conflicts if the UI sitting ignores them (not optional):**

- Board layout must not become a sqlite/Mission field (AD-4).
- App-use must not edit implementation or apply change-requests (AD-8).
- json-render / MCP Apps are not identity, persistence, runtime, or authority (AD-17; 09-23 AD-8).
- No sixth COMP, no n8n-as-runtime, no screen-kit-as-centre (09-18 AD-1; 09-23 paradigm).
- Dummy Book/BMS screens are forbidden (AD-11).
- Cartesian fan-out and guessed joins are forbidden (AD-5) — connection UI must expose mapping.

---

## 14. Superseded by `02-CURRENT-DIRECTION.md` (do not revive)

These origin or post-origin ideas are **dead as layout/stack law** even when they appear in the transcript:

1. **LSE ML Studio as QMX layout** — rejected. Keep capability coverage only. “ML Studio” is a working label, not a rigid application (current-direction U, latest correction).
2. **React Flow / commercial React dashboard kit as the UI stack** — origin assistant named React Flow (L168). Current-direction U: Svelte + TypeScript, shadcn-svelte, Svelte Flow; commercial React kit is reference only; zero spend on component kits.
3. **Qt** — out.
4. **n8n / Taskade / OpenBB / Codex / LSE screenshots as the frozen shell** — they add context; original Excalidraw + this dictation remain the foundation.
5. **Study 01/02/03 prototypes** — not an implementation baseline (current-direction evidence section). Study 03 failed on layout and unusable text-heavy surfaces, not merely colours.
6. **One global agent session / tab-owned context** — rejected in origin and in both parent spines.
7. **Marketplace / multi-tenant cloud** — origin user-spoken no; parents keep DEC-0361 dead.
8. **Hot-swap of live trading systems / HMR** — origin sequential; parents AD-14 / DEC-0366.
9. **Implement every brainstormed mini-app** — origin and current-direction both forbid a closed launch backlog.
10. **Universal paper-trading gate** — superseded; paper only where trades or material risk behaviour exist.
11. **BMAD UX / Figma as this sitting’s workflow** — skip BMAD UX; architecture + epics remain usable.
12. **“Local/Server” as a sticker that implies durability** — origin hope; parent AD-15 wins.
13. **JSON Render / MCP Apps as the mini-app runtime** — origin enthusiasm (L593, L1070); parent law: adapters until a host contract exists; do not pin `@json-render/*`.
14. **Assistant claim “one main assistant should be the interface” as a specialist-deletion order** — user rejected at L720; later endorsed only as one *identity* over QMA specialists.

---

## 15. Durable UI-sitting checklist (origin still in force)

Use this as a bind list. Each item is user-spoken unless marked.

1. Node editor exists to compose, test, package, and operate capabilities — not as the product boundary.
2. Keep capability / extension (pack) / workflow / mini-app / widget distinct on screen.
3. Experimentation Board is the exploratory surface name; it is a draft sheet; it is not QMA Research; it is not auto-run.
4. Defaults and templates first; humans and copilot edit the same supported definitions.
5. Connections declare meaning and collection behaviour; no garbage-to-garbage wiring.
6. Notebook/code nodes are legal; internals need not explode into boxes; a node may still **show** code.
7. Graph, code, and dashboard are co-equal; expanding a node must not dump the graph (current-direction U).
8. Authoring vs app-use are different firepowers; in-app copilot is a right panel; general/home copilot is the editor.
9. Sessions are independent; tabs do not retarget running work; switching apps restores that app’s history (current-direction U).
10. Copilot is optional per app (current-direction U / 09-23).
11. Loops can graduate into mini-apps/packs after tests; no second loop engine (09-23 overlay on user-spoken).
12. Headless is first-class; CLI-in-node / logs / status are enough; jobs survive closing UI.
13. ML and non-trading data work are first-class; do not wrap them as bots; do not clone LSE ML Studio layout.
14. Mini-apps may be UI, headless, or mixed (current-direction U).
15. App-to-app via exported artifacts/ops/workflows/views; never by driving another app’s screen.
16. Home/platform destinations sit above opened apps (current-direction U); home dashboard must not silently change broker/account targets.
17. Alternative trading systems must be authorable without pretending to be Book/BMS; live replace is sequential and evidenced.
18. Examples in this transcript are seeds. Do not build an LSE clone, a Taskade clone, or a 40-app backlog.
19. json-render and MCP Apps are to be considered as view adapters, not as authority.
20. Desktop shell: VS Code / Bloomberg / origin Excalidraw family — contributed mini-app views inside a stable host, not a website of unrelated pages.

---

## 16. Source trail

| File | Use in this report |
|---|---|
| `Explore-Node-Editor-Architecture.md` L1–1907 | Full origin chat; all user-spoken and assistant-proposal quotes |
| `origin-reading.md` | Later overlay synthesis; used as a cross-check, not as a substitute for the transcript |
| `ml-reference-notes.md` | Later overlay: LSE observed vs marketing vs proposed QMX adaptations |
| `images/image-001.png` | User-attached Taskade Flows screenshot at origin L1052 |
| `02-CURRENT-DIRECTION.md` | Current sitting authority; supersession list in §14 |
| `architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` | Parent law; chrome deferred |
| `architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md` | Pack-and-grant overlay; home folded into authoring-with-absent-instance |
| `architecture-QMX-2026-09-18/COPILOT-AND-APPS.md` | 09-18 copilot/app table |
| `architecture-QMX-2026-09-23/COPILOT-AND-APPS.md` | Explicit Main/general/home vs in-app vs engine-run seats |

End of report.
