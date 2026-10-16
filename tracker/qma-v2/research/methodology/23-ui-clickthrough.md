# 23 — UI click-through with demo data on (ground truth)

Research date: 2026-10-16. Read-only. The only files written are this file and the screenshots in `23-ui-shots/`.

## How this was done

- **App.** Worktree `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair`, head `eea09941`. I started `apps/qmx-ui` by running Vite directly with Node 24 (`node node_modules/vite/bin/vite.js dev`) from the built-in browser's dev-server launcher. The launcher needs `.claude/launch.json` in the session's project root (`Desktop\QMX`), not in the worktree. I added that file for this run and deleted it afterwards. The server is stopped. The worktree has no changes.
- **Demo mode** was ON (yellow "Demo" chip on every screen). Window 1440x900.
- **Startup.** A full page load shows the splash card ("QMX" with a price line) for about 6 s (`23-ui-shots/00-splash.jpg`). The first visit to the Lab and to Apps also made Vite re-optimise dependencies and reload the page once. That is dev-only behaviour.
- **Clicks.** Library shelves, inspector tabs and full pages; Lab Build (Graph/Code/Import), Test, Train, Pods Design, the Lab copilot, the workflow guided walk; Apps, an app screen, its About sheet, Discover; the copilot errand, receipt, drawer Reports, a new errand, the "Build a workflow" start, and a draft panel in chat.
- **Not opened by clicking.** bits-ui dropdown menus (Library "New", Lab "Add a panel", subject picker) did not open under the automation clicks. I read their items from code instead, and every claim about them cites code.
- **Code citations** look like `ui:lib/library/items.ts:219`, relative to `apps/qmx-ui/src`.
- The Reticle dev overlay was hidden with page CSS for the screenshots. It is not part of QMX.

**One-line verdict.** The Library holds 15 shelves of *display projections* built from other screens' demo arrays. It has no "unit", "artifact", "relationship" or "logic" kind. The Lab editor is one fixed sample graph that the UI calls a workflow. It has no node palette, no save, no trigger and no run of its own. Workflows have no screen of their own. Mini apps live in a separate data set that does not match the Library's mini-app shelf. In the copilot, a draft panel can be pinned to the Lab, but nothing the copilot makes reaches the Library.

---

## 1. Library

Screens: `23-ui-shots/02-library-everything-bot-selected.jpg`, `03`–`14`.

### Layout

- Left: shelf groups, which can be collapsed. Middle: the shelf as cards or a list. Right: the inspector for the selected item. A **Full page** opens `/library/<id>` for items that carry an `entity` (`ui:routes/library/+page.svelte:1-11`).
- Header: one search box ("Find anything"), **Select** (multi-select), cards/list toggle, and **New**.
- **New** has three items. "Start from a template" opens the Templates shelf. "Import a file" only shows the toast "Importing goes through the daemon…". "Ask the copilot" goes to `/copilot?ask=Make me something new for the Library:` (`ui:routes/library/+page.svelte:491-511`).
- **Select** lets you tick items, then "Add to copilot" or "Save as collection". Collections are kept in browser storage only (`ui:routes/library/+page.svelte:111-115`).
- **Search** is a substring match on name, summary and family, run in the browser (`+page.svelte:126-133`).
- **Demo off** leaves only Templates and Sources (`+page.svelte:123-128`).

### The 15 shelves (as seen; counts with demo on)

`ui:lib/library/items.ts:90-215`. "Everything" shows 127 items; it excludes Sources.

| Group | Shelf (count) | Built from (demo array) |
|---|---|---|
| Things that trade | Bots (13), Models (2), Pods (9), Pod blocks (25) | `DEMO_ENTITIES` bots + Portfolio `PODS` bots; `LAB_PODS` + Portfolio `PODS`; `BLOCKS` |
| Things that run | Workflows (2), Mini apps (2), Templates (26) | `DEMO_ENTITIES` kind workflow / app; hand-written templates |
| Proof | Test reports (16), Paper runs (5), Stress scenarios (7) | Lab `RUNS` (done), `PAPER_RUNS` + road candidates, `STRESS` |
| Inputs | Saved setups (18), Data (4), Files (6) | Lab `ASSETS` (test/preset/feature) + 2 model configs; `ASSETS` datasets; `DEMO_ARTIFACTS` |
| Knowledge | Articles (401), Sources (7) | `/demo/mql5-articles.json` + `OTHER_ARTICLES`; `SOURCES` feeds |

What the operator expects versus what is there:
- **Units (formerly strategies):** no such word or shelf. Strategies are "Bots" ("Strategies that place trades", `items.ts:103`).
- **Artifacts:** no "Artifacts" shelf. The closest is **Files**, described as "Everything QMX produced" (`items.ts:190-194`), with six demo files (`ui:lib/demo/assets.ts:610-680`). The copilot's own artifacts (`ui:lib/copilot/demo.ts:682-708`) are a different list and do not appear in the Library (section 5).
- **Bots and bot cards:** yes. A bot card shows cover art coloured by family, stage badge, Sharpe, max drawdown, win rate and net return (`02`). The full page has a pipeline strip and tabs Performance / Trading / Setup (`08`).
- **Relationships:** shown only as "Used in" links to *places*, never item-to-item links (see below).
- **Logic:** no shelf. A bot's "logic" is the read-only **Code** tab text (`items.ts:793-804`). Pod blocks have a signature stub (`items.ts:749-767`).
- **Workflows:** a shelf with 2 items (section 3).
- **Mini apps:** a shelf with 2 items, which are not the 21 apps on the Apps screen (section 4).
- **Previews and detail views:** yes. Every item has an inspector; bots, models, apps and workflows also have a full page.

### The item (`LibraryItem`, `ui:lib/library/items.ts:219-241`)

| Field | Meaning |
|---|---|
| `id`, `shelf`, `name`, `summary` | identity and shelf |
| `family?` | strategy family or sub-kind; colours the card (`items.ts:244-264`) |
| `version?`, `stage?`, `updated` | display strings ("v4", "Live", "This week") |
| `uses: Use[]` | where it is used: `{place: Lab|Portfolio|Copilot|Home|Mini apps, what, path, query}` (`items.ts:54-64`) |
| `entity?: Entity` | full record for bot, model, app, workflow only (`items.ts:230`) |
| `starts?: Use` | templates only: what "Use this template" opens |
| `details?` | key/value rows (Settings tab) |
| `journal?`, `logs?` | journal lines `{time,text,tone}` and machine log lines |
| `code?` | `{lang: python|yaml, text}`, read-only, "edit it in the Lab" |

### Inspector (preview) — `ui:lib/library/ItemInspector.svelte`

- Header: shelf · family, name + version, summary.
- Buttons (`ItemInspector.svelte:84-127`):
  - **Use this template** (templates only);
  - **Full page** (items with an entity);
  - **Open in <first use's place>**;
  - **Add to copilot**;
  - **Open file** (Files only; the toast says it needs the daemon);
  - **New version** (the toast says "starts as a draft; the current one stays as it is"; nothing is created).
- Tabs, each shown only when it has data (`ItemInspector.svelte:44-56`):
  - **Used in**: a hub map with spokes to Lab, Portfolio, Copilot, Home and Mini apps, plus a link list (`02`, `03`, `13`, `14`);
  - **Journal & logs**;
  - **Code**: read-only, with "Edit in the Lab" (`04`);
  - **Settings**: details, or the entity's parameters, or the workflow steps listed as "Step 1..n", plus the measure tiles (`05`).

### Full pages — `ui:routes/library/[id]/+page.svelte`

- These exist only for the 8 entities (4 bots, 2 models, 2 apps, 2 workflows). Every other item has the inspector only.
- A banner says "Demo item. Sample numbers; nothing here is evidence."
- Header: kind · family, name, summary, version, fingerprint `fp1:…`. Buttons: "Add to copilot", "Open in Lab" (not for apps), and "Road to live" (bots in Evidence or Paper).
- Tabs by kind (`[id]/+page.svelte:25-36`):
  - **Bot** (`08`): Performance (measures, equity, evidence runs with role confirmation/trial/replicate), Trading (trade journal, and connections `{server, pod, mode, seat}`; "Sizing comes from the pod, never from the bot"), Setup.
  - **Model** (`09`): Performance (AUC, fold stability, leakage checks, inference), Slots (a disabled "Plug in…" button), Setup.
  - **Mini app** (`07`): Operations. Each op card shows id, effect (read/compute/trade-adjacent), typed inputs and "Run (needs daemon)", which is disabled (`:335-368`). Then Setup.
  - **Workflow** (`06`): Steps, a linear chain of op names (`data.refresh → qmb walk-forward → qmb monte-carlo → report.write → library.save`), with "30 runs this month. A draft runs only after it is published." (`:371-383`). Then Setup.
- **Setup** has three boxes: Parameters, Reads (`streams`), and Artifacts (`entity.artifacts` ids matched to `DEMO_ARTIFACTS`).

### Relationships the UI shows

1. **Item → place.** The `uses[]` links are computed in the browser from other screens' arrays. Examples: a bot's links come from pods trading it, test runs whose symbol starts with the bot's first word, and the road and journal (`items.ts:280-319`); a pod block's links come from pods whose stack holds it (`items.ts:480-482`).
2. **Pod → blocks per slot.** Shown in pod details (`items.ts:442-450`) and pod YAML (`items.ts:814-823`).
3. **File → producer.** "Made by" is a free string such as "BTC breakout · run 441" or "Nightly evidence workflow" (`assets.ts:619-679`).
4. **Entity → artifacts.** `entity.artifacts: string[]` (`ui:lib/qmx/entities.ts:99`).
5. **Model → slots.** `entity.slots` (`entities.ts:98`).
6. **Template → what it starts.** `starts: Use`.

There is **no item-to-item graph**. "Used in" points at screens, not at other items. No view shows parent, version lineage, "proved by" or "made in session".

### How workflows, mini apps, units and artifacts appear

- **Workflows.** Shelf cards show runs this month, finished cleanly, typical duration and steps (`03`). The Code tab is generated YAML `workflow: <name> / steps: [...]` (`items.ts:859-874`). The logs are fake "02:00 started (schedule)" lines. **Open in Lab** goes to `/lab?layout=build`, which always shows the same BTC sample graph, not this workflow (section 2).
- **Workflow templates.** Templates includes three: "News & sentiment workflow", "Nightly evidence", "Article to hypothesis". "Use this template" goes to `/lab?layout=build` ("Opens as a new workflow in the Lab. You get a draft; nothing runs until you save and start it.") (`10`; `items.ts:509-529`).
- **Mini apps.** Two entities: "Research · Crypto" (3 views, 3 ops listed but "5" in measures, its own copilot) and "News & sentiment" (headless, schedule shown as last/next run) (`14`, `07`). "Open in Mini apps" points back to `/library?item=…`, not to `/apps` (`items.ts:341-348`).
- **Units.** Not present (see above).
- **Artifacts.** The Files shelf (`12`): backtest report, paper results, trade journal, model file, dataset and chart pack, each with producer, fingerprint and size. "Open file" needs the daemon.
- **Articles** (`11`). A reader with Add to copilot, **Turn into hypothesis**, Reading mode, Full page and Original, plus "Key points" and **Explain it as** (Plain words / Diagram / Interactive page / Explainer video).
  - "Turn into hypothesis" only opens the copilot with a drafted message naming the Article-to-hypothesis workflow (`+page.svelte:800-807`).
  - The four "Explain it as" buttons also only draft a copilot message (`ui:lib/library/articles.ts:49-70`).

---

## 2. Lab node editor

Screens: `15-lab-build-layout.jpg`, `16-lab-editor-graph-max.jpg`, `17-lab-editor-code.jpg`, `18-lab-editor-import.jpg`, `32`, `33`.

### Where it lives

- In the Lab, Strategies bench, **Build** layout, the "Editor" tile. Beside it: Resources (left), Inspector (right), Log (bottom).
- The Editor tile is linked to the Inspector by a colour group. Clicking a node selects it in the Inspector (`ui:lib/lab/panels/EditorPanel.svelte:116`).
- The source comment calls it "a node graph (a Graph Template: a workflow of steps)" (`EditorPanel.svelte:3-6`).
- `/authoring` redirects to `/lab?layout=build` ("Merged into the Lab", `ui:routes/authoring/+page.svelte:2`). This is where the old authoring and "storyboard / Experimentation Board" idea went. No text in `src` says "storyboard" or "experiment board"; the closest thing is the Lab tile board plus this editor.

### Node types and ports

- A single custom node type, `step` (`ui:lib/demo/StepNode.svelte`). Its data is `StepData = {kind, label, detail, preview?, status?}` (`ui:lib/demo/workflow.ts:7-15`).
- `kind` is one of `Data | Feature | Model | Test | Output`, and it sets the accent colour (`StepNode.svelte:8-14`).
- **Ports.** Each node has one untyped input handle on the left (every kind except Data) and one untyped output on the right (every kind except Output) (`StepNode.svelte:92-97`). Ports have no names, no data types and no multiple inputs or outputs.
- **Node body.** Kind label, a **status dot** (ok / warn / stale: "Last run fine", "Last run has a warning", "Not run since edit"), title, detail, and a **mini preview** of the last output (a sparkline, or bars for Feature nodes) (`StepNode.svelte:41-91`).
- **The sample graph** (`workflow.ts:25-110`, `177-204`):
  - nodes: Exchange bars (Data) → Indicators and Labels (Feature) → Gradient boosting (Model) → Backtest (Test) → Report (Output);
  - edges are fixed, and the edge out of the Model node is animated;
  - each step also carries `settings[]` and a Python `code` string.

### How a graph is built

- **There is no node palette in the UI.** `PALETTE` (Data / Feature / Model / Test / Output groups, "Operations the palette offers") is defined in `workflow.ts:132-175` but nothing imports it.
- Nothing adds a node: no right-click menu, no drag from Resources, no "+ step" button.
- Nodes can be dragged and the canvas panned and zoomed. There are zoom controls and a "Map" (minimap) toggle (`EditorPanel.svelte:90-134`).
- **Edges.** I tried to drag an edge and the canvas panned instead. Code has no `onconnect` handler, and edits are never saved.
- **Inspector** (`ui:lib/lab/panels/InspectorPanel.svelte`). For the selected step it shows read-only Settings and Code tabs and a machine chip. The machine is derived from the step kind: Model → Colab, Test → vps-fsn, otherwise this laptop. It cannot be chosen.
- **The guided walk** "A custom workflow" (`ui:lib/lab/guides.ts:54-70`) tells the operator to "Start from an empty graph or one of your templates. Add steps from Resources, or describe them to me." The UI has no empty graph, and Resources items cannot be added as steps; they only have "Add to copilot" (`ui:lib/lab/panels/AssetsPanel.svelte:97-102`).

### Subject

- The header picker lists bots, workflows and models from Lab `ASSETS` (`ui:routes/lab/+page.svelte:70-73`).
- Changing the subject changes only the header label and the Run toast. The editor always shows "Breakout research · draft v7 · published v6" and the same six nodes (`EditorPanel.svelte:87-88`).
- Resources says "Breakout research" has "8 steps · v7 draft" (`ui:lib/lab/demo.ts:300-305`), but the graph has 6.

### Run and save

- **Run** is in the Lab header, not in the editor. It only shows a toast: "Running needs the daemon. It would run the published version of <subject> on <machine>." (`routes/lab/+page.svelte:103-115`).
- There is no Save, Publish or Draft control in the editor. "Draft v7 · published v6" is a fixed label.
- The only "Save" in the Lab saves the **tile layout** to browser storage (`+page.svelte:97-102`).

### Graph versus Code

- **Code** (`17`) is CodeMirror Python, editable, built once from the steps' `code` strings joined with `# <label>: <detail>` headers (`EditorPanel.svelte:46-48`, `137`).
- The two views are **not synced**. Editing code does not change the graph, and moving nodes does not change the code. Both start from the same `DEMO_STEPS`.

### Import

`18`. Four dashed cards, each of which shows a toast "<x>: choose a file. Upload needs the daemon." (`EditorPanel.svelte:49-70`, `142-155`):
- Model file (ONNX, pickle or joblib, "shipped inside the bot");
- Code from a repo ("Claude Code or Codex wrote… becomes the bot's logic");
- Notebook ("cells into steps");
- Python file.

### Is it the workflow editor?

**Yes. In the UI it is the only workflow editor, and the same canvas is the bot editor.** The evidence:
- The code calls it a workflow.
- The minimap is labelled "Workflow overview" (`EditorPanel.svelte:132`).
- Library workflows and workflow templates open here.
- The copilot's "Build a workflow" start ends here (section 3).
- Pod blocks of kind `graph` ("News-aware kill switch: Your graph: halt around big events") show "Open in the editor (Build layout)" (`ui:lib/lab/pods.ts:179-186`; `ui:lib/lab/panels/BlockPanel.svelte:82-90`).

So one graph type is meant to express bot logic, research pipelines, scheduled jobs and pod-block logic. That one graph has neither triggers nor typed ports.

A second, separate pipeline exists in the **Train** layout (`20`): a row of chips (Dataset → Features → Split → Leakage check → Train → Evaluate → Plug into slots, "+ Step"). It is not a graph and is not linked to the editor.

---

## 3. Workflows

### Where they live

| Place | What is shown | Source |
|---|---|---|
| Library › Workflows | 2 entity cards: Nightly evidence (Installed v4) and Hypothesis miner (Draft) | `03`; `ui:lib/demo/assets.ts:520-608` |
| Library › Templates | 3 workflow templates | `10`; `items.ts:509-529` |
| Lab › Resources › "Workflows" | 3 items: Breakout research, Nightly evidence, Regime study. Their asset kind is `"template"` | `15`; `ui:lib/lab/demo.ts:287,300-318` |
| Copilot drawer "Activity" and Home "Going on" | "Nightly evidence (schedule)", state `scheduled`, "next run 02:00 UTC" | `01`; `ui:lib/copilot/demo.ts:672-680` |
| Pod block kind `graph` | a guard built as a graph | `pods.ts:179-186` |

The three lists do not agree. "Hypothesis miner" is only in the Library, and "Breakout research" and "Regime study" are only in the Lab. **There is no Workflows screen**: no rail entry, no list with run state, no schedule view.

### How one is created

1. **Copilot › New errand › "Build a workflow — Steps that run on a timer"** (`30`). A guided start asks three questions, one at a time (`ui:lib/workbench/GuidedStart.svelte:87-117`):
   - Job: retrain on a schedule / test a hypothesis weekly / watch and report;
   - Trigger: a schedule / new data / a news event;
   - Machine: this laptop / research VPS.
2. It then shows a plan (`31`) with "Open the Lab and walk me through it" or "Just set it up for me".
3. "Open the Lab…" goes to `/lab?guide=workflow`. A guide strip walks three steps (`32`, `33`):
   - Build: "Start from an empty graph…";
   - Build: "Choose what starts it: a schedule, new data, a news event, or by hand. Choose where it runs.";
   - Test: "Dry-run it on recent data… Then publish it."
4. Step 2 asks for a trigger, but **the Build layout has no trigger or schedule control**. The editor still shows the BTC sample graph.

Other entry points:
- Library template → "Use this template" → `/lab?layout=build` (same sample graph).
- Lab Resources "+" on Workflows ("New workflow") → toast "the Lab copilot can scaffold it, or build it in the editor" (`AssetsPanel.svelte:74-79`).
- Slash command `/schedule` "Run something on a server on a timer" (`ui:lib/copilot/demo.ts:711-720`).

### Triggered

- Only as words: guided-start answers, guide text, the "(schedule)" job label, and the headless app "Next run 15:00".
- The UI has no trigger object, field or editor.
- The `Entity` type has no trigger or schedule field (`ui:lib/qmx/entities.ts:94-96`, only `steps` and `runs`).

### Monitored

- Library card measures (runs this month, finished cleanly, typical duration).
- Inspector fake logs.
- One `scheduled` job row in Activity / Going on.
- Node status dots and previews in the editor, which are fixed demo values.
- No run history list per workflow and no per-step run timeline.

### Edited

- In the Lab editor only, and nothing there is saved.
- The Library Code tab is read-only YAML with "Edit in the Lab".

**Compared with n8n:**
- Missing: node palette, typed ports, a trigger node, per-node input/output inspection of a real run, an executions list, and activate/deactivate.
- Present: a node canvas with status dots and output previews, and a draft/published label.

---

## 4. Mini apps

Screens: `23-apps-your-apps.jpg`, `24-app-screen-news.jpg`, `25-app-about-sheet.jpg`, `26-apps-discover-new-app.jpg`.

### Apps screen (`/apps`)

- The header says "7 ready · 1 stopped · 5 in progress" and has **Your apps / Discover**, a **Safe mode** switch and **New app**.
- Tiles are grouped by purpose (Pinned, Markets, Watching, Research, Trading helpers). Each tile shows a **preview** of its output. A preview has one of four kinds: `figure | headline | rows | alert` (`ui:lib/apps/apps.svelte.ts:84-88`).
- A stopped app shows **Restart** on its tile (Broker status).

### Create (`26`)

- "Describe an app and the copilot builds it…" → copilot with a drafted ask.
- **From widgets**: pick Home and Portfolio widgets and name the app. It is saved to browser storage as `kind: "screens"`, `stage: 0` (`apps.svelte.ts:800-833`). Lab panels are not offered (`WIDGETS` is built from `PORTFOLIO_PANELS` and `HOME_PANELS` only, `apps.svelte.ts:711-723`).
- **Templates**, filterable by group. "Use" drafts a copilot ask: "Build me a "<name>" app from the template".

### Run and screen (`24`)

- `/apps/<id>` is a tile board of the app's widgets (`panels[]` → `layoutFor`). It has **Edit layout** and **+ Widget**.
- Widgets are the same Home and Portfolio panels, for example "News and events" and "Coming up".

### About sheet (`25`)

- On/off switch.
- **Road to live**: Build, Tests, Sandbox, Shadow run, Live (`apps.svelte.ts:20-26`).
- **Its box**: runs on, budget today, network allow-list, breaker, approval rule. The approval rule comes from `risk`: Shows things / Runs work / Touches money (`apps.svelte.ts:29-42`).
- Log.
- Buttons: Run now, Pinned, Ask the copilot ("Change <app>:"), and Remove (only for apps you made).

### Edit

- There is no code or spec editor. You edit through the copilot ("Ask the copilot → Change…") or by rearranging the widget board.
- Settings › Mini apps adds per-app on/off, budget, schedule, network and approval controls (`ui:lib/settings/MiniAppsSection.svelte`).

### Widgets

- Two kinds:
  - **Built-in panels** (Home, Portfolio, Lab catalogs);
  - **Spec panels**: JSON `{title, description, size, data, root, elements}` drawn from a 10-type catalog (Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button) (`ui:lib/sdk/spec.ts:11-29`, `31-60`).
- Spec panels come from the copilot (section 5). An app screen is built from built-in panels only.

### Relation to workflows

- No field links an app to a workflow.
- The link exists only as text:
  - evidence line "Built from the news workflow template" (`apps.svelte.ts:166`, `478`);
  - `schedule: "Every 5 minutes"`;
  - `ops: ["news.refresh", ...]`;
  - `feeds`.
- The Library's headless app full page says "Run its operations here, from a workflow, or through the copilot" (`[id]/+page.svelte:336-338`). So in the UI's model, workflows call app **operations** as steps. No step in the editor sample is an app operation.

### Two disjoint mini-app models

| | Apps screen `MiniApp` | Library `Entity` kind `app` |
|---|---|---|
| Source | `apps.svelte.ts:109-146`, 21 demo apps | `assets.ts:405-519`, 2 apps |
| Ids | `news`, `screener`, `watcher`, … | `research-crypto`, `news-sentiment` |
| Key fields | group, preview, kind (screens/headless/both), risk, stage 0-4, evidence[], health, box fields, provides[], ops: string[], feeds, schedule, log[], panels[] | stage, version, fp, measures, views[], ops: Operation[] (typed inputs, effect), copilotProfile |

"News & sentiment" exists in both, under different ids and shapes. None of the 21 Apps-screen apps is on the Library's Mini apps shelf.

**Per-app copilot.** "Research · Crypto" appears as an answerer in the composer aim menu (`ui:lib/copilot/aim.svelte.ts:17-26`), and every app is listed in Settings › Copilots (`ui:lib/settings/settings.svelte.ts:453`). App screens have **no side copilot column**. Only the Lab and Portfolio use `CopilotColumn`.

---

## 5. Copilot

Screens: `27-copilot-errand.jpg`, `28-copilot-receipt-open.jpg`, `29-copilot-drawer-reports-artifact-preview.jpg`, `30`, `31`, `34-copilot-draft-panel-widget-in-chat.jpg`, `21-lab-copilot-column.jpg`.

### What renders in chat (`ui:lib/copilot/demo.ts:30-90`; `ui:lib/copilot/Thread.svelte`)

- **Text** in large reading type. **User** bubbles with attachment chips (e.g. "Trend rider v2", "SOL momentum").
- **Receipt.** One line, "What it did: 3 helpers · 4 tools · changed 3 things · 1 report". It opens to Helpers, Tools, Changes and Reports (`28`).
- **Ask** cards (amber, answered in the composer, with options and "Write an answer") and **permission** cards ("Needs your yes").
- **Widget in chat** (`34`). Any message matching `panel|widget|dashboard|show me` gets a scripted reply and a **draft panel** drawn from a spec: "Weekend risk" with three metrics and a line chart (`ui:lib/copilot/store.svelte.ts:127-129`, `164-186`). Its buttons are **Pin to the Lab**, **Keep it here** and **Throw away** (`Thread.svelte:236-258`).
  - Pin adds a "Pinned by the copilot" tile to the **Lab's active layout**, with the spec in browser storage (`ui:routes/copilot/+page.svelte:103-118`; `ui:lib/sdk/pinned.svelte.ts`).
  - Pinning never saves to the Library, Home or a mini app.
- **Table** and **cards** (before/after entity cards) blocks exist in the demo.
- No markdown, Mermaid or diagram renderer.

### Artifacts

- The errand header chip "1 report" opens the right **drawer** at Reports (`29`). The drawer lists the copilot's artifacts across sessions (`ARTIFACTS`, `demo.ts:682-708`):
  - "Weekend rider against Trend rider" (Interactive report, has a spec, so a live preview);
  - "Weekend liquidity: notes from 3 papers" (Notes);
  - "HMC in plain words" (Explainer).
- An artifact without a spec shows "<type>. Its full content opens here once the daemon stores it; the copilot saves it to the Library." (`ui:lib/copilot/WorkArea.svelte:269-280`).
- None of these three is in the Library. The weekend errand's "Changes" list says "Library: Notes on weekend liquidity (3 papers)", but the Library has no such item.
- Other drawer tabs: Activity (jobs with machine and progress), Changes (a diff), Terminal (echo only), Browser (iframe).

### Combined sessions

- **One store** serves all copilots. A session has `origin ∈ Main | Lab | Portfolio | Library | Mini apps` (`demo.ts:11-27`).
- The sidebar groups sessions by need: Needs you, Working, Earlier. A small icon shows the origin (`27`).
- **Cross-area errands.** The demo "Weekend-safe pod, end to end" is the combined-session example:
  - plan steps tagged `where: Lab | Lab | Lab | Portfolio | Server`;
  - helpers Builder, Tester and Researcher on different machines;
  - tools `pod.edit`, `pod.test`, `pod.stress_scenario`;
  - changes in Lab, Lab and Library;
  - a permission to put the pod on paper in Portfolio (`demo.ts:325-470`).
- **Handoff blocks** start sessions from other places, for example "Started in News & sentiment" (Mini apps) and "Started from an article in the Library" (`demo.ts:593-625`).
- **Side copilots.** The Lab (`21`) and Portfolio have a right column with their own starters, history and settings. "Continue in the main copilot" calls `absorb()`, which **rewrites the origin to Main** (`store.svelte.ts:94-105`; `ui:lib/workbench/CopilotColumn.svelte:99`, `138`).
- **Aim menu.** Reach: Lab, Portfolio (paper), Library, Mini apps, Servers, Settings. Answerers: Main, Lab copilot, Portfolio copilot, "Research · Crypto" (a mini app's copilot), and "Tester (running agent)" (`aim.svelte.ts:8-27`).
- **Guided starts** in a new errand (`30`): Train something new, Bring in outside work, Build a workflow, Build a pod. These hand the session to a Lab walk (section 3).

---

## 6. Data model implied by the UI

| Entity | Fields (as typed in the UI) | Relations | Source |
|---|---|---|---|
| LibraryItem | id, shelf (15 ids), name, summary, family?, version?, stage?, updated, uses[], entity?, starts?, details?, journal?, logs?, code? | uses → Place (5 screens); entity → Entity; starts → Use | `items.ts:219-241` |
| Use | place, what, path, query? | points at a screen + layout, not an item | `items.ts:63-64` |
| Entity (bot/model/app/workflow) | id, kind, name, summary, stage (Hypothesis…Live, Installed, Draft), version, fp, family?, measures[], spark?, evidence[]?, journal[]?, connections[]?, parameters?, streams?, ops[]?, views?, copilotProfile?, steps?, runs?, slots?, artifacts? | connections → server + pod; artifacts → DemoArtifact ids; slots → model slots | `entities.ts:73-100` |
| EvidenceRun | run, kind (Backtest/Walk-forward/Monte Carlo/Optimise/Significance/Sweep), role (confirmation/trial/replicate), period, sharpe, maxDrawdown, trades, when | belongs to an Entity | `entities.ts:29-44` |
| Operation (app op) | id, summary, effect (read/compute/trade-adjacent), inputs[{name,type,required}] | belongs to an app Entity; meant to be a workflow step | `entities.ts:66-71` |
| DemoArtifact (Library "Files") | id, type (Backtest report/Dataset/Model file/Trade journal/Paper results/Chart pack), name, producedBy (string), size, date, fp | producer is free text | `assets.ts:610-680` |
| Workflow graph step | id, kind (Data/Feature/Model/Test/Output), label, detail, x, y, settings[], code, preview?, status? (ok/warn/stale) | edges {source,target}, one untyped port each side | `workflow.ts:7-23`, `191-204` |
| Lab Asset (Resources) | id, kind (template=workflow, bot, model, dataset, feature, test, preset, report), name, meta, env? | env → machine | `lab/demo.ts:270-298` |
| Pod (Lab) | id, name, template, version, stage, stack{slot → block ids} | stack → Block | `items.ts:424-451`; `pods.ts` |
| Block | id, name, slot (inputs/guards/allocator/sizer/throttles/caps/ledger), kind (form/graph/code/model), setting, what, docs, required? | kind graph/code → Lab editor | `pods.ts:21-31` |
| MiniApp (Apps screen) | id, name, summary, icon, group, preview?, next?, kind (screens/headless/both), risk (show/work/money), stage 0-4, stageNote, evidence[], health, builtBy, runsOn, budget, budgetUsed, network, breaker, provides[], ops[] (strings), feeds?, schedule?, log[], panels?, stopped?, errand?, on | panels → widget ids; errand → copilot session; no Library link | `apps.svelte.ts:109-146` |
| PanelSpec (widget) | title, description?, size{minW,minH}?, data? (op or stream name), root, elements{id → {type, props, children}} | pinned → Lab tile id (browser storage) | `sdk/spec.ts:11-29` |
| Session | id, title, origin, status (running/waiting/done), age, agents?, pinned?, parent?, goal? | parent → Session; blocks[] | `copilot/demo.ts:14-27` |
| Block (chat) | user, text, panel, plan, agents, tools, changes, artifact, table, cards, ask, permission, handoff | changes → place + path; artifact → Artifact id | `copilot/demo.ts:30-90` |
| Copilot Artifact | id, title, type (Interactive report/Notes/Explainer), session, spec? | session → Session; **not** in Library | `copilot/demo.ts:682-688` |
| Task (job) | id, name, session (or null), where, state (running/waiting/scheduled), progress, log[] | session → Session; where → machine | `copilot/demo.ts:629-680` |
| Collection | id, name, items[] (Library ids) | browser storage only | `routes/library/+page.svelte:109-115` |

Kinds the operator expects that have **no type** in the UI: Unit, Relationship (item ↔ item), Logic (as an object), Workflow trigger/schedule, Workflow run, Artifact as a Library kind.

---

## 7. Corrections to file 10

1. **Library kinds versus his list.** File 10 lists 15 shelves but does not say that units, artifacts, relationships and logic have no shelf or type. "Files" stands in for artifacts. The copilot's artifacts never reach the Library (sections 1 and 5).
2. **"Workflows … open in the Editor" is wrong.** Lab Resources items have only "Add to copilot" (`AssetsPanel.svelte:97-102`). Library "Open in Lab" and "Use this template" open `/lab?layout=build`, which always shows the same BTC sample graph (`EditorPanel.svelte:42-43,87-88`).
3. **"There is no run state on graph nodes" is wrong.** Every node has a status dot (ok / warn / stale) and a preview of its last output (`StepNode.svelte:41-91`). They are fixed demo values, and nothing marks a node as running.
4. **The editor is not a working builder.** File 10 does not say that it lacks a node palette (`PALETTE` exists at `workflow.ts:132` but is unused), lacks any way to add nodes, uses one untyped port per side, has no save or publish, and keeps Graph and Code out of sync.
5. **Subject picker.** File 10 says the editor shows "the same subject" in three modes. In fact changing the subject does not change the graph or the code; the editor is hard-wired to "Breakout research" (`EditorPanel.svelte:87-88`).
6. **Workflow creation path exists.** File 10 says "No workflow screen, run view or scheduler UI exists". That is true, but it misses the copilot "Build a workflow" guided start (Job / Trigger / Machine) and the three-step Lab walk (`GuidedStart.svelte:87-117`; `guides.ts:54-70`). The walk asks for a trigger that no control can set.
7. **The editor is also the pod-block editor.** Blocks of kind `graph` or `code` open "in the editor (Build layout)" (`BlockPanel.svelte:82-90`). File 10 treats the editor as strategy-only.
8. **Two mini-app models.** File 10 describes the Apps screen and the Library shelf as one thing. They are separate data sets with different ids and fields (21 versus 2 apps). Library "Open in Mini apps" links back to the Library itself (`items.ts:341-348`).
9. **No side copilot on mini-app screens.** File 10 §5 implies an app's own copilot. It exists only as an aim-menu answerer and a Settings entry; only the Lab and Portfolio mount `CopilotColumn`.
10. **"Turn into hypothesis runs an 'Article to hypothesis' workflow" overstates it.** It drafts a copilot message that names the workflow (`routes/library/+page.svelte:800-807`).
11. **Pinning a panel targets the Lab's active layout only.** It does not go to Home, the Library or a mini app (`routes/copilot/+page.svelte:103-118`). File 10 lists "Keep / Throw away / Pin to Lab" correctly but says widgets tile on Home, the Lab and app screens. Copilot-made specs reach only the Lab.
12. **Inconsistent demo lists.**
    - The Library has workflows Nightly evidence and Hypothesis miner; Lab Resources has Breakout research, Nightly evidence and Regime study.
    - "Breakout research" says 8 steps but the graph has 6.
    - Research · Crypto says 5 operations but lists 3.
    - The weekend errand claims a Library change that does not exist.
    
    Treat counts on these screens as decoration.
13. **Inspector machine is derived, not chosen.** File 10 says the Inspector shows "where it runs (Colab…)". The value is computed from the step kind (`InspectorPanel.svelte:18-24`); the UI has no way to place a step on a machine.
14. **Lab panel count.** 28 panels is correct. The Train layout's chip pipeline (Dataset → … → Plug into slots, "+ Step") is a second, separate pipeline UI. File 10 lists it as a panel but does not flag that it duplicates the graph editor.
15. **Dev setup.** Vite also runs when started by an absolute path from another directory, but SvelteKit then looks for `src/app.html` relative to the current directory. You must `cd` into `apps/qmx-ui` first. The built-in browser's launcher reads `.claude/launch.json` from the session's project root, not from the worktree. The first visit to the Lab and to Apps triggers a dependency re-optimisation and one page reload.
