> STATUS 2026-10-16 (rubric walk): PARTLY-STALE. See 27-rubric-walk.md. Rulings in 26 win.

# 10 — How deep the UI goes (ground truth for the UI coding session)

Research date: 2026-10-16. Read-only. The only file written is this one.

## How this was done

- **Ran the UI.** Worktree `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair`, branch `ui-review/repair`, head `eea09941`. `apps/qmx-ui` started with `vite dev` on port 5173 (Node 24; `pnpm dev` hangs, but `node node_modules/vite/bin/vite.js dev` starts in about 13 s). Demo mode was already on. I clicked through the screens in the built-in browser at 1440x900 and stopped the server afterwards.
- **Read the code.** Citations look like `ui:src/lib/lab/catalog.ts:72`, relative to `apps/qmx-ui`.
- **Backend** comes from branch `qma/hp17` (the top of the stacked QMA v2 PRs). Citations look like `hp17:...`.
- **Transcripts read:**
  - The UI session where this UI was built (2026-10-01 to 10-05). It is the Claude export `C:\Users\Mubarak\Downloads\QMX-session-exports-2026-10-12\2-QMX-UI-audit-and-planning.zip` (122 MB jsonl), so this is the "UI transcript in Downloads". I pulled his 84 messages out to scratch and grepped them.
  - `Desktop\claude-ui-qmx.md`: the 10-01 opening prompt.
  - `Desktop\trancript_ui.md` (Sept, QuantumindUX design system) and `Desktop\QMX-UI-session-transcript-2026-07-23...md` (July, Open Design). Both are older and were superseded by the 10-01 rebuild. I only grepped them; they add nothing about the Lab, Library or rendering.
- **Screenshots** were taken with the built-in browser. Folder: `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\5efecf49-2c39-4a71-bfb7-8ce9c1e6d0dd\tool-results\`

| Screen | File |
|---|---|
| Lab Build: Graph | `mcp-Claude_Browser-blob-1792139129485-yjdnso.jpg` |
| Lab Build: Code | `...-1792139138627-29h12e.jpg` |
| Lab Build: Import | `...-1792139147755-d30l4o.jpg` |
| Lab Train | `...-1792139147755-m9uxum.jpg` |
| Lab with the Lab copilot open | `...-1792139400551-991bai.jpg` |
| Lab Pods: Design, with the copilot | `...-1792139407610-nyqksr.jpg` |
| Copilot errand "Weekend-safe pod" | `...-1792139202976-scb8fn.jpg` |
| Same errand, receipt opened | `...-1792139211198-jfn041.jpg` |
| Library, bot selected | `...-1792139252634-ocp0mq.jpg` |
| Apps | `...-1792139289964-hqwvxm.jpg` |

  A Reticle dev overlay sits in the bottom-right corner of every shot. It is not part of QMX.

**One-line verdict.** The UI is a full demo of a product much bigger than the backend. Every screen runs on sample data. The Lab and the Library show the depth he expects. Agent output is designed as one stream of typed blocks. Most of what the screens imply has no backend twin today; section 6 lists the gaps.

---

## 1. Lab

### Shape

- One page. It merged Authoring, Backtest and ML Studio (operator, 2026-10-02: "authoring, backtesting, ML, all of them are combined in one lab"). Header comment at `ui:src/routes/lab/+page.svelte:1-10`.
- **Two benches**, each with built-in layouts (`ui:src/lib/lab/lab.svelte.ts:23-160`):
  - **Strategies:** Build, Test, Train, Compare.
  - **Pods:** Design, Test, Paper.
- **Tiles.** Every layout is a resizable grid. Tiles can be added (+), docked, minimised, maximised and colour-linked; tiles in the same colour share a selection. Layout edits are saved per machine in browser storage only (`lab.svelte.ts:1-6`).
- **Header controls:**
  - subject picker (for example "BTC breakout");
  - **machine picker**: "All machines", this laptop, a VPS or Colab, chosen VS Code-remote style. Switching machines filters every tile, and an empty machine says so instead of showing an error (`MachinePicker.svelte`, `MachineEmpty.svelte`; operator 10-03);
  - Run / Run test;
  - edit layout;
  - **Start something new**: a three-step flow that ends in a saved layout, which can be kept as a template (`StartDialog.svelte:1-7`);
  - the Lab copilot toggle.
- **Guided walks.** The copilot hands over a walk; each step opens a layout and says what to do there. Example: "Bringing in outside work" (`guides.ts:1-30`). The note says that once wired, the copilot does the steps itself.

### The 28 panels (`ui:src/lib/lab/catalog.ts:72-234`)

| Group | Panels and what the operator can do there |
|---|---|
| Find things | **Resources / Toolbox**: workflows, bots, models, datasets, features (indicators such as "ATR(14) ratio"), tests, presets, templates. Each item has "Add to copilot". |
| Build | **Editor** in three modes of the same subject. **Graph**: an `@xyflow/svelte` canvas of steps (Data → Features/Labels → Model → Backtest → Report) with a mini map. **Code**: CodeMirror Python of the same pipeline. **Import**: model file (ONNX, pickle or joblib, "shipped inside the bot"), code from a repo, notebook, Python file. "Drafts never run; only published versions do" (`panels/EditorPanel.svelte:1-7,37,53-62`). **Inspector**: settings of the selected step and where it runs (for example "Gradient boosting · Colab · walk-forward 12 folds · purge 24 bars"). |
| Test | **Runs**: a sortable table; tick runs to compare. **Sweep grid**: markets × timeframes. **Scenario builder** dialog: bot version × markets × pairs × timeframes × parameter ranges, run count and time estimate, and a luck warning (`ScenarioDialog.svelte:1-8`). **Equity**. **Robustness**: QMB validation ladder, cheapest check first; the pass bar is his and editable (`RobustnessPanel.svelte:1-6`). **Compare**. **Log**: run console. |
| Train (ML / neural nets) | **Training**: pipeline chips (Dataset, Features, Split, Leakage check, Train, Evaluate, Plug into slots); loss curves with a "Likely overfitting" flag; split bar (train / validation / sealed test); runs on Colab. **Model slots**: entry signal, sizing, regime, risk throttle, plus your own; only "entry" exists in the docs (`SlotsPanel.svelte:1-7`). **Data**: datasets, coverage, gaps. **Compute**: machines, notebooks, GPU clouds, cost. |
| Agents | **Agents**: Quant → Agent → Sub-agent tree with state and where each runs (`AgentsPanel.svelte:1-6`). Demo only. He asked to "see their nodes ... streamed live" (10-02); that is not built. |
| Pods bench | **Pod**: the stack of blocks per slot: Inputs, Guards, Allocator, Sizer, Throttles, Caps, Ledger. **Block**: settings of one block. **Size trail**: why a trade got its size. **Drawdown fan**: chance of hitting the kill line. **Stress board**: crises × pods. **Interventions**. **Pod equity**. **Head to head**. **Run together**: split money across pods. **Paper run**. **Live decisions**. **Ready for live?** checks. **Pod resources**: pods, bots, crises. |
| Copilot-made | **Pinned by the copilot**: a tier-1 panel (section 4) the copilot drafted and he pinned (`panels/PinnedPanel.svelte`). |

### What he asked for that is thin or missing

- **Notebooks.** They exist only as an Import card. There is no notebook runner or panel.
- **MIS versions.** MIS lives in Portfolio (`ui:src/lib/portfolio/panels/MisPanel.svelte`): labelers, live and shadow. Its text says "build new labelers in the Lab", but the Lab has no MIS panel. He said MIS "I'll be enhancing ... from the lab or with the co-pilot" and "I want to be able to add indicators" (10-03). The triage parks this ("MIS logs, indicators and model views", `handoff/research/backlog-triage-2026-10-14.md:148+`).
- **Indicators and components.** Indicators appear only as "features" in the Toolbox. There is no indicator editor. "Create new components of my own" is parked (R3).
- **Variants.**
  - The Library has "New version" (a draft beside the current one), and the Lab subject shows "draft v7 · published v6".
  - Pods carry versions (Trend rider v2).
  - Nothing compares two variants made by two agents side by side (backlog B36).
- **Running workflows.**
  - The Resources tile lists workflows (Breakout research, Nightly evidence, Regime study), and they open in the Editor.
  - There is no run state on graph nodes and no schedule view. Editor run state, the copilot editing the graph, and robustness built from workflows are all parked (R6).
  - He now prefers "graphs and loops" to an n8n-style editor (`UI-BACKLOG.md` R6).
- **Experiments.** Runs, the sweep, robustness and compare cover them. There is no experiment notebook and no "Experimentation Board" of mixed notes, charts and runnable parts (see `05-qmx-today.md` §3a).

### What the Lab copilot is shown doing

- **Tools.** Its own tool list in `ui:src/lib/lab/copilot.ts:12-110`:
  - Test: `qmb.backtest`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness`, `qmb.optimize`;
  - Train: `lab.train`, `lab.import_model`;
  - Build: `graph.edit_draft`, `code.edit`, `lab.add_panel`;
  - Compute and data: `compute.place`, `data.inspect`;
  - Pods: `pod.edit`, `pod.test`, `pod.stress_scenario`, `pod.mix`, `pod.paper`.
- **Targets:** Researcher, Analyst, Developer ("not configured").
- **Attach:** toolbox item, ticked runs, a tile on screen, code folder, dataset upload.
- **Context and starters.** It knows the open subject: "Knows BTC breakout, the open layout and every run". Starters include "Why did Trend rider refuse the AVAX entry", "Build a stress scenario from the March 2020 crash" and "Split $20,000 across the ticked pods" (`routes/lab/+page.svelte:368-400`).
- **In the demo errands** (`ui:src/lib/copilot/demo.ts`) it is shown:
  - running pod tests and stress scenarios on a VPS;
  - running walk-forward on Colab;
  - saving a pod draft that appears in the Lab;
  - running sub-agents named Builder, Tester and Researcher, each with "where it runs".

### Backend each part needs

| Part | Backend today (`05` §2) | Needed |
|---|---|---|
| Runs, equity, log | `runs_list/get/logs`; QMB ledger | A per-subject run list with the machine; live log stream |
| Sweep, walk-forward, robustness, optimize | QMB has them; agents reach only `run_backtest(config_ref)` with pre-registered configs | Agent tools that take a scenario, not a stored config |
| Editor Graph / Code | `workflow.v1` deleted in D1; `workflows_*` return 501 | Workflow engine contract (`07` §2); drafts and publish |
| Import | None | Model/code import into a bot version |
| Training, slots, model objects | None | Model object, training runs, slot contract (QML) |
| Data, compute | `qmx-remote` providers (partly stubbed); CT-46 environments in the docs | Environment list with cost and status; datasets as items |
| Agents tile | Child chats via `delegate`, depth 1 | Agent tree with live state and machine |
| Pods bench | None (risk redesign open) | Pod object, pod test, paper per pod |
| Layouts | Browser only | Optional sync |

---

## 2. Library ("Strats" in the plan)

### How the UI designs it (`ui:src/routes/library/+page.svelte:1-11`; `ui:src/lib/library/items.ts`)

He ruled 10-03 that it "needs a bloody redesign ... needs to connect to all the other parts".

**Views.**
- Shelves on the left, in 5 groups and 15 shelves:
  - **Things that trade:** Bots, Models, Pods, Pod blocks;
  - **Things that run:** Workflows, Mini apps, Templates;
  - **Proof:** Test reports, Paper runs, Stress scenarios;
  - **Inputs:** Saved setups, Data, Files;
  - **Knowledge:** Articles, Sources.
- The shelf in the middle shows cards or a list. Cards are coloured by strategy family and carry key numbers such as Sharpe, max drawdown, win rate and stage.
- The item inspector sits on the right.
- Multi-select can hand items to the copilot or save them as a **collection**. Collections are kept in localStorage only (`+page.svelte:110-115`).

**The item object** (`LibraryItem`, `items.ts:233-255`):
- `id`, `shelf`, `name`, `summary`, `family`, `version`, `stage`, `updated`;
- `uses[]`: every place the item is used, each `{place, what, path, query}` and each a real deep link;
- `entity`: a full card for bots, models, apps and workflows;
- `starts`: for templates, what using the template starts;
- `details`, `journal[]` (what happened and why), `logs[]`;
- `code` (read-only here; edited in the Lab).

**Relations.**
- The **Used in** tab draws a hub map: the item in the middle, spokes to Lab, Portfolio, Copilot, Home and Mini apps, with counts (`ConnectionsMap.svelte`), plus a filterable link list.
- The links are computed in the browser from other screens' demo data (`botUses()` at `items.ts:280-330`).
- Other inspector tabs: **Journal & logs**, **Code**, **Settings**.

**Actions.**
- Full page, Open in Portfolio/Lab, Add to copilot.
- **New version**: "starts as a draft; the current one stays as it is" (`ItemInspector.svelte:122`).

**Search.** One box ("Find anything"). It is a plain substring match on name, summary and family, done in the browser (`+page.svelte:130-134`).

**Knowledge.**
- Articles open in a reader with a reading mode and key points.
- **Turn into hypothesis** runs an "Article to hypothesis" workflow.
- **Explain it as** offers four choices (`ui:src/lib/library/articles.ts:49-70`). The copilot makes the result and saves it beside the article:
  - plain words;
  - diagram;
  - interactive page;
  - explainer video ("3Blue1Brown-style ... Manim and a local voice").
- Sources open in an in-app browser.

**Provenance in the UI** is only:
- version, stage and updated date;
- the journal;
- "used in" links.

There is **no lineage view**: no parent, no "promoted-from", no "which run proved this".

### What it implies for a knowledge graph

1. The UI already treats the Library as **nodes (items of 15 kinds) with typed edges to places**. A graph index should serve `uses` from real edges instead of client code.
2. The backend has the edges, but they are scattered (`05` §4):
   - the CT-07 lineage relations (14 of them, for example `supersedes`, `promoted-from`, `branches-from`);
   - bot → family, confluences and producers;
   - run → bot version;
   - artifact producer → consumer;
   - Library `links` with a free-text relation.
3. The UI has three things with no data behind them: a **lineage tab** (version graph, promoted-from, evidence runs), a **"proved by" link** from a bot to its reports, and **real search**. Backend full-text search exists (`hp17:.../qmx_control/library.py:41`) but is not used.
4. Eight shelves have **no backend kind**: models, workflows, pods, blocks, scenarios, setups, reports, paper. The kinds that exist are only `article` and `backtest` in the control Library, plus the QMF registry kinds. The graph needs a kind table that matches the 15 shelves, or the UI must drop shelves.
5. Collections and "Explain it as" outputs are new node kinds: a user collection, and a derived explainer linked to its source article.

---

## 3. Copilot and sessions

### One store for all copilots

`ui:src/lib/copilot/store.svelte.ts:1-11`:
- The main copilot and the Lab and Portfolio side copilots read and write the **same sessions**.
- A session is an append-only list of blocks. The rule: the UI shows only what the log holds.

### Sessions

`Session` type, `ui:src/lib/copilot/demo.ts:11-30`:
- `origin`: one of `Main | Lab | Portfolio | Library | Mini apps`;
- `status`: one of `running | waiting | done`;
- `age`, `agents` (count), `pinned`;
- `parent` (sub-agent sessions point at their parent);
- `goal` (one sentence).

### Session list

`SessionsSidebar.svelte:1-7`:
- Grouped by what it needs: **Needs you**, **Working**, **Earlier**.
- The **origin is a small icon** (flask for Lab, briefcase for Portfolio, books for Library, window for Mini apps), with the tooltip "Started in Lab".
- Helpers (child sessions) are indented under the open errand.
- A dot marks a session waiting for you.
- Search box; "New errand".

### Side copilots in the Lab and Portfolio

`ui:src/lib/workbench/CopilotColumn.svelte`:
- The right-hand column, opened by a toggle.
- The **session dropdown** offers "New session", the **History** of this origin only, and **"Continue in the main copilot"**.
- A settings icon opens Settings › Copilots for this copilot: model, standing instructions, MCP servers, reach, ask-first rules. Copilots listed: Main, Lab, Portfolio, Library, and each mini app (`settings.svelte.ts:317-322`).

### Moving between the side and the hub

- **Side → hub:** "Continue in the main copilot" calls `copilot.absorb(id)`. That **rewrites the session's origin to Main** and appends "Now in the main copilot: everything it can reach is open to this conversation" (`store.svelte.ts:99-112`). Then it navigates to `/copilot?session=<id>`.
- **Handoff block.** A Lab-born session that shows up in the main copilot starts with a handoff block ("Started in the Lab copilot.") and a **Continue here** button (`Thread.svelte:149-158`).
- **Hub → side:** there is **no path back**. Nothing moves a session back to the Lab, and the "move" is one-way and destructive to the origin.
- **Helpers:** the child's header says "Helper of '<parent>'. It sees only its task." with a back link (`ErrandHeader.svelte:76-83`).

### Message aim

The chip in the composer (`aim.svelte.ts:1-40`):
- **Reach:** which of Lab, Portfolio (paper), Library, mini apps, servers and settings the copilot may touch;
- **Who answers:** Main, Lab copilot, Portfolio copilot, a mini app's copilot ("Research · Crypto"), or a running agent ("Tester").
- There are no modes (R2); skills come through "/".
- Real money is never in reach.

### Errand header

- Title and goal;
- a segmented progress bar ("Step 3 of 5: Put it head to head with Trend rider");
- chips: helpers, reports, changes, terminal, browser;
- a status pill such as "Waiting for you".

---

## 4. Agentic rendering

### Block kinds the UI renders

`ui:src/lib/copilot/demo.ts:34-94`; renderer `ui:src/lib/copilot/Thread.svelte`.

| UI `kind` | What it shows | How it renders |
|---|---|---|
| `user` | text plus attached chips | Right-aligned bubble with attachment chips under it |
| `text` | prose | Large reading type (1.12rem, line-height 1.7), "read like letters" |
| `plan` | steps with state and `where` | Folded into the receipt or header progress |
| `agents` | sub-agents: name, role, state, where, last line, progress | Receipt "Helpers" list; click opens the child session |
| `tools` | calls: name, args, ms, ok | Receipt "Tools" list in monospace with duration |
| `changes` | place, what, deep link | Receipt "Changed elsewhere in QMX" with arrows to Lab or Library |
| `artifact` | id, title, type, note | Receipt "reports" entry; opens in the drawer's Reports tab |
| `table` | title, head, rows | Inline table card with copy |
| `cards` | before and after entity, changed fields | Two FIFA-style entity cards with changed attributes highlighted |
| `panel` | tier-1 panel spec and state | Live panel drawn from the catalog, with Keep / Throw away / Pin to Lab |
| `ask` | question, options, recommended | Inline amber card; answered at the composer (`PendingPanel`) |
| `permission` | action, detail, guard | Answers: **Allow**, **Allow for the rest of this errand**, **Not now** |
| `handoff` | from, note | Card with "Continue here" |

**The receipt rule** (`Thread.svelte:1-9`):
- The reply prose stays on screen.
- Everything done to get there folds into one line, "What it did: 3 helpers · 4 tools · changed 3 things · 1 report", which opens on click.
- Questions, approvals and panels stay visible because they need him.
- This is the "What it did card first, raw log one click down" idea in `UI-NOTES.md` §8. Screenshot `...211198-jfn041.jpg`.

### Drawer (the right panel)

`WorkArea.svelte:1-9`. Five tabs:
- **Helpers and jobs**: sub-agents and background jobs with machine and progress;
- **Reports**: artifact previews, including SpecView panels;
- **Changes**: the diff;
- **Terminal**: one per job. Typed commands only echo "(demo) runs on the server through the daemon";
- **Browser**: an iframe with an address bar.

### Diagrams and documents today

- **Panels (tier 1)** are the only structured visual output.
  - The catalog is 10 types: Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button (`ui:src/lib/sdk/spec.ts`).
  - Panels are validated: at most 60 elements and 6 levels.
  - The shape follows json-render's `{root, elements}`.
- Artifacts preview as panels or plain documents.
- **No Mermaid, SVG or diagram renderer and no markdown renderer** exist in `src`. Text blocks are plain `<p>`.
- **No animation** in chat output. The only motion is the start-up draw-in and panel fades (commit `eea09941`).

### Gaps for "animated documents" / explainer-style output

1. **A document or explainer block kind is missing.** Today a long answer is a `text` paragraph. Without a new block type (UI-NOTES §2 freezes the kind list), an explainer can ride as an `artifact` with `content.kind = "explainer"`, or as a `panel` whose catalog grows. Either needs a renderer.
2. **The catalog has no diagram parts.** It lacks Flow/Diagram (nodes and edges; xyflow is already a dependency), Mermaid, Steps/Timeline, Candles (`CandleChart.svelte` exists outside the catalog), EquityFan, EntityCard and Image/Video. Adding these to `SPEC_CATALOG` is the cheapest path. Agents then emit data, never code.
3. **Motion has no format.** An "animated document" needs ordered reveal steps: a `steps[]` sequence over a spec, where each step highlights or adds elements, with play and scrub controls. Nothing in `spec.ts` expresses order or time.
4. **Interactive and video outputs have nowhere to render.** "Explain it as → interactive page / explainer video" saves into the Library, but no viewer exists. An interactive page needs the tier-2 sealed iframe, which is not built. A video needs a player artifact.
5. **No markdown.** Headings, lists, code and maths in answers render as one paragraph. A safe markdown renderer is a prerequisite for any document output.
6. **Explanations in the screens are text.** He asked for the sweep grid and model slots to be explained "in a diagram. I don't like reading texts" (10-03; `UI-BACKLOG.md:335-336`). Panel explanations (`InfoTip`, `MisPanel` "Explain MIS") are all text.

---

## 5. Mini apps in the UI

### Apps screen

`ui:src/routes/apps/+page.svelte:1-7` and `ui:src/lib/apps/apps.svelte.ts:1-8`:
- **Your apps / Discover**, a **Safe mode** switch, **New app**.
- Tiles are grouped by purpose (Pinned, Markets, Watching, Research, Trading helpers), never by stage. Each tile leads with a glimpse of its own output.
- A slim **In progress** row lists apps still on their road.

### Create

- "Describe an app and the copilot builds it…" box: goes to `/copilot?ask=` (`+page.svelte:74,201`).
- **From widgets**: pick Home and Portfolio widgets, name it, and it starts at Build (`FromWidgets.svelte:1-7`). Lab panels are not offered yet.
- **Templates.**

### Edit

- No editor. "Ask the copilot → Change <app>:" (`AboutSheet.svelte:199-205`).
- The app screen (`/apps/[id]`) is a tile board the operator can rearrange and add widgets to.

### Archive and delete

- **Remove** appears only for apps he built (`AboutSheet.svelte:208-213`). It only edits browser state.
- There is **no archive, no disable** apart from the on/off switch in Settings, and no version list.

### Observability and logging

The About sheet (`AboutSheet.svelte`) shows:
- **Road to live**: Build, Tests, Sandbox, Shadow run, Live, each with the evidence it left;
- **Its box**: runs on, budget today, network allow-list, breaker, approval rule;
- latest log lines;
- Restart and "Ask why" for a stopped app;
- Run now, Pin.

**Settings › Mini apps** (`MiniAppsSection.svelte:1-7`) gives per-app controls: on/off, daily budget, schedule, network allow-list and approval rule.

### Widgets

- Apps declare widgets that tile on Home, the Lab (pinned panels) and app screens.
- `/gallery` shows the component library: every catalog entry rendered live with its spec and states (ready, loading, empty...).
- Tier-1 panels from the copilot can be kept or pinned.

### Workflows

- Workflows are a Library shelf and appear in Lab Resources.
- An app may "bundle widgets and workflows" (storyboard).
- No workflow screen, run view or scheduler UI exists. Parked under R6.

### Per-app copilot

- The UI shows a mini app's own copilot: "Research · Crypto" as an answerer, and each mini app in the Settings › Copilots list.

R3 says the whole Apps design will be redone ("many apps were not meant to be just like VS Code style extensions").

---

## 6. Mismatches the UI session must know

1. **Block names and shape differ.**
   - UI blocks are `{kind, ...fields}`.
   - Backend `SessionBlock` is `{type, content}` with `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you` (`hp17:qmx-agents/packages/qmx-control/src/qmx_control/service.py:66-85`).
   - Renames needed: `tools→tool`, `changes→changed`, `cards→entity`, `ask→question`.
   - The UI has no `needs_you` renderer.
   - The UI's `tools` block batches several calls; decide whether the backend `tool` block is one call or a batch.
2. **Session origin and home.**
   - The UI needs `origin ∈ {Main, Lab, Portfolio, Library, Mini apps}`.
   - The backend `origin` is a free string, and the harness always writes `"qma"` (`05` §6).
   - Reserve `home: {kind, project_id}` now (`07` §5). Map Main→`general`, Mini apps→`app`.
3. **"Continue in main" moves the session.**
   - `absorb()` rewrites origin to Main.
   - UI-NOTES §10 and `07` §7 say a session never changes home; opening it in the hub must not move it.
   - The UI must switch to "view in hub, home stays". It also needs a way back to the Lab, which does not exist.
4. **Status words.**
   - UI: `running | waiting | done`.
   - Backend: chat kinds `Interactive / Background / Child`; approvals can be `expired` after a restart; `needs_you` exists.
   - The UI needs `failed`, `cancelled` and `expired` states.
5. **Approval answers.**
   - UI: Allow / Allow for the rest of this errand / Not now.
   - Backend: `allow_once | allow_always | reject_once | reject_always | cancel` (`POST /api/approvals/{ask_id}`).
   - "For this errand" (session scope) does not exist in the backend; `allow_always` is a global sticky rule.
   - The UI lacks reject-always, cancel and "expired, re-run from here".
6. **Sub-agents.**
   - The UI shows agents with role, progress, machine and a live last line.
   - The backend's `delegate` is synchronous, depth 1 and on the same machine, with no progress events.
   - Claude-native sub-agents give a start and an end only.
7. **Lab copilot tools are fiction.** None of `qmb.*`, `lab.*`, `pod.*`, `graph.edit_draft` or `compute.place` exists. The only backtest door is `run_backtest(config_ref)` with pre-registered configs. Do not wire these buttons (`07` §5).
8. **The Editor has no engine.** `workflow.v1` is deleted in D1, and `workflows_get/put/validate/run` return 501. Draft, publish and run in the Graph/Code editor cannot be wired.
9. **Library kinds.**
   - The UI has 15 shelves; the backend has `article` and `backtest` in the control Library, plus QMF kinds.
   - "Used in" links are computed in the browser.
   - Search is a client substring match while the backend has full-text search.
   - Link relations are free text; CT-07 has 14 typed relations.
   - Collections live in localStorage.
10. **Mini-app lifecycle.**
    - The UI has Remove; the backend has no `apps_delete` or disable.
    - Trust is chosen by the caller.
    - "From widgets" and "describe it" build paths have no backend (the `build-mini-app` skill is empty).
11. **A mini app's own copilot.** The UI offers one (answerer "Research · Crypto"; Settings › Copilots per app). Backlog B23 says "no app gets its own copilot"; apps become plugins any copilot loads. One of the two must change.
12. **Missing harness features in the UI** (UI-NOTES §3 and §6–8; backed by HP10–HP15):
    - effort control;
    - compaction events and "compact now";
    - stop, interrupt and steer;
    - the model-switch cost warning (the composer has a model chip with no warning);
    - the usage page (only a "Background agents' Claude share" slider exists in Safety);
    - the Export button per session;
    - the cursor overlay for computer use.
13. **Terminal and browser.** The drawer terminal echoes typed commands as if a shell existed. The backend has no `terminal.*` live kinds yet, and UI-NOTES plans read-only SSE first with WebSocket later. Label the terminal read-only.
14. **Panels.**
    - The `panel` block exists in the backend.
    - `ui.propose_panel`, a server-side catalog validator and data binding (`data: "pod.test.weekend_breakdown"`) do not.
    - Tier-2 sealed iframes are not built.
15. **Stale backend docs in the UI repo.** `BACKEND-REQUIREMENTS.md` and `handoff/MINI-APPS-AND-COPILOT-CONTRACT.md` still describe the CT-40 WebSocket, `psess:`/`send_message`, LangGraph and Ask/Plan/Do modes. The real door is REST plus SSE (`hp17:.../qma/harness/routes.py`: `/api/chats`, `/api/sessions/{id}/turns`, `/live`, `/api/approvals/{id}`, `/api/usage`, `/export`). Treat those files as history.
16. **Pods and the Portfolio copilot.**
    - The Pods bench, Portfolio pod screens and Portfolio copilot tools (`pod.bring_from_lab`, `risk.explain`, …) wait for the risk and sizing redesign ("are we still using books?").
    - The only Portfolio backend is broker reads and unsigned `propose_order`.
17. **The demo switch hides the gaps.** Demo mode is on by default in this worktree. With it off, every screen falls back to "day one" empty states. The UI session should develop with demo off, so unwired places show "Not connected" instead of sample data. This follows the UI lane's own rule in `BACKEND-REQUIREMENTS.md` ("Nothing is faked").
18. **Dev setup.** `package.json` pins Node `>=22.12 <23`, but the machine has Node 24.18. `pnpm dev` produced no output; running Vite directly works.

## What the UI session can wire today (unchanged from `07` §5, with the renames above)

- Chat and sessions on the 14 kinds (after mismatch 1).
- Approval cards with the five answers plus expired (after mismatch 5).
- One `agents` card per child session.
- Model, provider and effort switch with the cost warning.
- The usage page and the 50% cap bar.
- Money-hook refusals.
- Export per session.
- The `home` badge field (after mismatches 2 and 3).
- The receipt card.

Leave the Lab tools, the Editor run state, Pods, Portfolio tools, mini-app install and the explainer renderer for later. The one exception: growing the tier-1 catalog with diagram parts (section 4, gap 2) is pure UI work and safe to start.
