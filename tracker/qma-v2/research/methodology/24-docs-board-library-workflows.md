# 24 — What the docs say about the Board, the Library and workflows

Research date: 2026-10-16. Read-only. The only file written is this one.

## How to read the citations

- `main:` is `C:\Users\Mubarak\Desktop\QMX` on branch `main` (head `c3e8ec5e`). `main` holds docs and plans only; it has no product code.
- `ledger:` is `main:_docwork/ledger.yaml`, the documentation factory's decision ledger. Every DEC- id below is quoted from it.
- `hp17:` is code on branch `qma/hp17` (head `584a7f41`), read with `git show`.
- `T:` is the node-editor transcript, `main:workroom/research/2026-09-18_node-editor-architecture/explore-conversation/Explore-Node-Editor-Architecture.md` (ChatGPT, 2026-09-17/18, 1,906 lines, 13 operator turns). A byte-identical copy sits at `main:_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/transcript-refresh-20260919/`.
- `UI0923:` is `main:_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`.
- `plan:` is `D:\QMX-worktrees\agent-system\tracker\qma-v2\`.
- The UI side comes from `10-ui-depth.md`, as the brief asked. I did not re-run the UI.

**One-line verdict.** The operator's reading is right on all four points. The docs split his single "storyboard" into four layers and made the Board a browser-only layout. The Library became a narrow projection over ten trading record kinds that explicitly excludes workflows, skills and apps. The docs do pick one workflow engine, but the code later grew a second one, and the deletion plan removes both. "Strats" in the docs is only the old seed corpus, never the Library's name.

---

## 1. Storyboard → Experimentation Board → node editor

### What he said (2026-09-17, the node-editor transcript)

| Line | His words (short) | What it means |
|---|---|---|
| T:198 | "the workflows, I think the way it started is that they would have acted more like a storyboard" | Workflows started as a storyboard. |
| T:198 | "an assistant to help me create workflows because that's a storyboard idea … you dump stuff, then … use that for inspiration" | The copilot builds while he dumps ideas. |
| T:198 | He cites n8n's built-in assistant: "you didn't really have to suffer manually crea[ting]" | n8n is the model for building. |
| T:313 | "this is more of a storyboard … let's just call it a draft sheet … for something to actually be reusable it has to pass tests" | Messy draft first. Only tested parts become reusable. |
| T:316 | "one visual environment with distinguishable underlying meanings … neither did I say that it requires entirely different separate graphs" | One canvas, not separate graphs. |
| T:316 | "the research board. No … Let's call it the experimentation board … because QMA has dedicated research staff" | The **assistant's** name "research board" was rejected. "Experimentation Board" replaced that name, not "storyboard". |
| T:316 | "Are you seeing how N8N has templates? We should be able to create templates also" | Templates come out of boards. |
| T:319 | "do you really expect me to use blank things out of the box? No, we should have defaults" | Default nodes ship. |
| T:1068 | "that's why the storyboard should be messy … by the time something is converted into a mini app, that thing should have passed a lot of tests" | Board → tested → mini app. |

The assistant's own summary at the time: "build an Experimentation Board with a useful default capability catalogue, explicit connection contracts, notebook-level freedom, conversational control, and a tested path from experiments to reusable workflows and mini-apps" (T:419).

### What the planning sittings did with it

| Date | Where | What happened |
|---|---|---|
| 2026-09-18/19 | Workflows sitting, `main:_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md:25`, `:110` | "The Experimentation Board is a working-surface projection. It is not a registry kind, not a Mission, and not automatic execution." Board layout becomes "client-only". |
| same | Codex challenge, `…/codex-challenge-20260919/INDEPENDENT-SCENARIO-BASELINE.md:151`, `:225` | Codex kept his intent: "A storyboard can be messy/non-executable; the author deliberately selects and validates a runnable subgraph." Scenario P1-WF-001: "Execute selected valid subgraph on a messy storyboard." |
| 2026-09-19 | **DEC-0417** (ledger:4032-4034), ADR-0024 AD-4 (`main:docs/decisions/ADR-0024-workflows-construction-kit.md:44`) | "Four workflow layers stay distinct": (1) "Board layout is client-only. It MUST NOT be a field of product_session, Mission, Task Graph, Graph Template, or any sqlite row … Editing the client layout writes nothing." (2) Graph Template, (3) Task Graph, (4) ungoverned library call. Selected-subgraph runs exist, but only on a **registered** template: "not a live board scribble, not a board id." |
| 2026-09-19 | ADR-0022 follow-up (`main:docs/decisions/ADR-0022-workbench-expansion.md:114`) and glossary (`main:docs/glossary.md:356-358`) | "Experimentation Board" is "an allowed display alias … it still mints no Project/Workspace/Mission/sqlite record." |
| 2026-09-19 | Workflows epics (`main:_bmad-output/planning-artifacts/epics-WORKFLOWS-2026-09-19.md:130`, `:730`) | FR-WF-41 "Board layout is client-only"; saving "layout JSON, positions, widgets" is refused. |
| 2026-09-22 | UI storyboard (Excalidraw, a different thing with the same name) | Preview pane is "not where we design or make workflows from"; "A node editor was explicitly left for further design" (`main:workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/storyboard-reading.md:23`, `:65`). |
| 2026-09-23 | UI sitting research, `UI0923:research/02-origin-explore-node-editor.md:268` | "the Experimentation Board is the named authoring canvas inside the workflow/composition experience." Its own gap table (`:402`) admits the docs' Board is "client-only projection" while his Board needs "defaults, templates, draft ≠ run, code-in-node, CLI-in-node". |
| 2026-09-25 | **DEC-0470** (ledger:4668-4670), **DEC-0475** (ledger:4728-4730), `main:docs/lenses/ui/screens/authoring.md:17` | The rail gets an **Authoring** destination. Authoring is "one graph/code/detail family (VS Code image)". The Board's canvas is now this graph editor. |
| 2026-09-25 | **DEC-0487** (ledger:4872-4874), **DEC-0499** (ledger:5016-5018) | Drafts are saved, but "Run refuses a mutable draft." First run is publish → enable → grant → invoke. |
| 2026-10-01/02 | UI rebuild (`10-ui-depth.md` §1) | Authoring merged into the Lab. The Board survives only as the Lab Editor's **Graph** mode (`@xyflow/svelte`), "Drafts never run; only published versions do". |

**Plain summary.** His one messy canvas, where notes, charts and runnable pieces sit together and the copilot helps, was cut in two. The messy half became a browser-only layout that saves nothing. The runnable half became the Authoring graph editor, which then became the Lab Editor. Nothing in the docs stores a board, its notes or its "run this part" on a draft. That is the misunderstanding he describes.

---

## 2. The Library

### 2a. As the docs define it

| Question | Docs answer | Source |
|---|---|---|
| What is it? | "Library is a projection." No new component and no new store. | DEC-0271 (ledger:3390-3392); ADR-0022:41; `main:docs/components/qmf-registry.md:91` |
| What can it hold? | Exactly ten existing record kinds, by fingerprint (fp1): CT-33 bot, CT-34 confluence, strategy-family, CT-22 Book, CT-27 BMS, CT-28 binding, CT-12 split, CT-10 observation, CT-32 result, CT-47 ExperimentSpec. | DEC-0271 |
| What may it **not** hold? | "QMA staging/RefinementProposals, JobHandles, Graph Templates, Skills, Routines, saved views, analysis publications, derived datasets." Hypotheses only after CT-33 registration (DEC-0381). Mini apps are "not a registry kind" (glossary:699-701). A composite app is "not a Library kind" (DEC-0423). | DEC-0271; ADR-0022:106; ADR-0024:50 |
| How is it shown? | "One chrome over typed hits." Three hit classes: Knowledge, Artifact, Contribution (installed pack operations). "Must not collapse kinds." | DEC-0476 (ledger:4740-4742); DEC-0415; `main:docs/lenses/ui/screens/library.md:17-21` |
| Is a Library database allowed? | No. "Forbidden: a generic Library database, `COMP-LIB`, a copied-row sqlite, a sixth store class." | `UI0923:LIBRARY-AND-ATTACHMENTS.md:16` |
| Where is it stored? | The registry room of `qmf-data`, one per world (live, replay, simulated). Records are append-only per-kind files keyed by fp1; lineage is pinned JSONL. "No graph database and no database server." SQLite and DuckDB only as rebuildable indexes. | CT-09 (`main:docs/contracts/ct-09-registry-persistence.yaml:11-35`); qmf-registry.md:64 |
| Files and uploads? | Uploads become artifacts only after an authenticated `PUT /artifacts/stage` on the local daemon. | DEC-0488; library.md:25 |
| Other machines? | QMB machines read "immutable fingerprinted as-of sets" over "a passive file-sync hub — dumb storage only". | qmf-registry.md:88 |
| S3? | **Not for the Library.** The only bucket in the docs is the off-machine **backup** target: nightly, encrypted, versioned, pushed by the VPS with rclone (Backblaze B2 default; S3, R2, Wasabi, MinIO allowed). | DEC-0118, DEC-0188; `main:docs/components/object-storage.md:17`, `:47-49`; `main:docs/architecture/stack.md:179`; changelog.md:137, :262 |
| Relations | CT-07 typed lineage edges, append-only, a closed set (`supersedes`, `promoted-from`, `branches-from` …). | CT-07; qmf-registry.md:52 |
| Versions | Every record is immutable by fp1. A change is a new record with a lineage edge. A byte-identical rewrite is accepted silently; a collision is refused. | CT-09 invariants; qmf-registry.md:88 |
| Strats | "STRATS is not a QMX language … Stats is seed corpus only. source_id=strats is the adapter key, not product copy." `strats` is "a refused Library kind". | DEC-0380 (ledger:3594-3596); DEC-0271; ADR-0022:106; AGENTS.md:77 |

His own words in the transcript go the other way: "we have a library … should I call it an artifact library. So for now, it's where we are storing most of the strategies. The thing is, we are going to upgrade it, which means database" (T:1791). He also flagged storage early: "I don't think we handled it properly while we were expanding the library" (T:321).

### 2b. As the backend implements it

There are **two Libraries** in the code at `hp17`, and they follow opposite rules.

| | Library A: QMB projection | Library B: control Library |
|---|---|---|
| Code | `hp17:qmb/src/qmb/registryread/library.py:1-9`, `:77-92` | `hp17:qmx-agents/packages/qmx-control/src/qmx_control/library.py:26-45`; routes `server.py:66-71` |
| Origin | Story 34.1, built to DEC-0271 | Packet P22, which says "Lab objects (strategies, pods) are typed, versioned Library artifacts" (`hp17:rebuild/packets/P22-library-runs-caching.md:13-17`) |
| Kinds | The docs' ten, closed. `NOT_LIBRARY_KIND_NAMES` refuses staging, templates, skills, STRATS and others (`:98+`) | Free string: `kind: str = Field(min_length=1)` (`models.py:18-27`) |
| What is written today | Registry records via QMF | `article` (`qmx_agents/research.py:36`, deleted in D1), `backtest` (`qmx_tools/service.py:215`), `remote-result` (`qmx_control/service.py:581`), `app-output` (`:777`), and any tool artifact kind (`qmx_tools/service.py:133`) |
| Storage | qmf-data registry room (SQLite metadata plus JSONL lineage) | `<home>/library.db` (SQLite: `items`, FTS5 `search`, `links`, `memo`) plus blobs at `<home>/artifacts/<sha256>` (`library.py:30-45`) |
| Content | Typed records | JSON only (`encoded()` at `:22-23`); no binary files |
| Versions | fp1 records plus lineage edges | `root_id` + `version` + `previous_id` chain; "Versions must keep their artifact type" (`:95-104`) |
| Relations | 14 typed CT-07 edges | `links(source, target, relation)`, free text, default `"related"` (`:226-235`) |
| Delete | Never (append-only) | No delete method or route |
| Backup | Docs' nightly encrypted bucket | Weekly snapshot to a private **GitHub** repo set in Settings (`service.py:432-446`; P22 step 6) |
| S3 | None | None. The only S3 in the code is an optional Litestream replica for a mini app's own SQLite under the Docker supervisor (`hp17:qmx-agents/packages/qmx-apps/README.md:98-107`; `qmx_apps/docker.py:269-273`) and the QMF backup bucket |

A third store, the QMA daemon artifact cache that implements the docs' `PUT /artifacts/stage` (`hp17:qmx-agents/packages/qma-daemon/src/qma/daemon/artifacts/store.py:1-7`), is deleted with the daemon in D3 (`plan:DELETION-PLAN.md:183-190`).

### 2c. Mismatch table: docs vs backend vs UI

| Topic | Docs | Backend (`hp17`) | UI (from `10` §2) |
|---|---|---|---|
| What the Library holds | Ten trading record kinds; workflows, skills, routines, templates and apps are excluded (DEC-0271) | A: the ten kinds. B: any kind string, but only article, backtest, remote-result and app-output are written | 15 shelves: bots, models, pods, pod blocks, workflows, mini apps, templates, test reports, paper runs, stress scenarios, setups, data, files, articles, sources |
| One store or many | One projection, no Library database (LIBRARY-AND-ATTACHMENTS:16) | Two Libraries with opposite rules, plus the QMB ledger and the app volumes | One screen; links computed in the browser |
| Workflows in the Library | Forbidden (Graph Templates are not Library kinds) | Nothing writes a workflow; `workflows_*` return 501 (`service.py:916-930`) | A "Workflows" shelf and Lab Resources list them |
| Mini apps and bot cards | Mini app is "not a registry kind"; a bot is CT-33 | Apps live in the app runtime, not the Library; a bot card is not a kind in B | Bots and mini apps are shelves with full entity cards |
| Relations | Typed CT-07 lineage, closed set | A: typed. B: free-text `relation` | "Used in" hub map from demo data; no lineage tab |
| Versions | Immutable fp1 plus lineage edges | B: version chain per root | "New version" draft beside current; stage labels |
| Search | Typed hits, kinds kept apart | B has FTS5 over title, tags and text | Client substring match |
| Files | Upload via `PUT /artifacts/stage` | That route dies with the daemon in D3; B takes JSON only | "Files" and "Data" shelves |
| Storage location | Local registry room per world; backups to a bucket | Local `library.db` plus blob folder; weekly GitHub backup | Collections in localStorage |
| S3 | Backup bucket only | Litestream replica for app SQLite only | None |
| Name | "Library"; STRATS is refused as product language (DEC-0380) | "Library" in code; STRATS refused (`registryread/library.py:7`) | "Library" ("Strats in the plan" per `10`) |
| Delete | Never; append and supersede | No delete | "Remove" exists only for apps, in browser state |

**Plain summary.** He wants one Library that stores everything with relations and versions. The docs forbid exactly that. The newer control Library (B) is closer to his idea, because it accepts any kind, keeps versions and has links, but the docs ban it, its relations are free text, and nothing writes his kinds into it. The UI draws his version on demo data.

---

## 3. Workflows in the docs

### The engine

- **One engine, reused from QMA.** "Reuse QMA as the procedure runtime; extend in place. Author in Graph Templates; instantiate via Mission Compiler; schedule via RoutineScheduler" (DEC-0420, ADR-0024:47). "No second scheduler" (DEC-0439, ADR-0024:66). No new application for workflows (DEC-0414, ADR-0024:41).
- **Three shapes.** A Graph Template is the authored, versioned, stateless DAG, contributed by a plugin (glossary:424-426, DEC-0312). A Task Graph is one run's persisted state (glossary:1049-1051). A Routine is a scheduled trigger that expands a template; "Firing is deterministic and never an LLM decision" (glossary:886-888, DEC-0328).
- **Graphs, not loops.** "Graphs, not loops, are the organizing centre" (DEC-0340, ledger:2985-2987). A loop is a node kind inside a graph.
- **The code.** The docs' engine was built at `hp17` in `qma-daemon/src/qma/daemon/taskgraph/` (compiler, dispatcher, join, nested, outbox). The P-packet rebuild then added a **second** engine, `workflow.v1` in `qmx_agents/workflows` on LangGraph (`hp17:…/qmx_agents/workflows/models.py:11-22`). D1 deletes the second; D3 deletes the first (`plan:DELETION-PLAN.md:70-82`, `:183-190`). After both, no engine is left (`05` gap 1).

### Node kinds

| Source | Kinds |
|---|---|
| Docs Task Graph (DEC-0312, glossary:1051) | `task`, `conditional`, `parallel_branch`, `join`, `approval_gate`, `human_gate`, `deterministic_script`, `loop`, `agent`, `artifact_dependency` |
| Docs ports and edges (DEC-0418, ADR-0024:45) | Port kinds `reference`, `data`, `event`, `control`. Edge mapping `one`, `zip`, `broadcast`, `keyed-join`, `cartesian` (Cartesian needs an explicit flag). "Conditional skip is a node kind." |
| Code `workflow.v1` (deleted in D1) | `python`, `agent`, `tool`, `app_call`, `condition`, `parallel`, `join`, `loop`, `human_gate`, `subworkflow` |
| Our proposal (`19` C2) | `script`, `rule`, `model`, `agent`, `human`, `grader`, `subflow`, `fanout` |

### The editor and how a workflow is created

1. **Where.** The Authoring destination: "Graph/code/detail family … VS Code image" (DEC-0475; authoring.md:17). The graph library is `@xyflow/svelte` 1.6.6 (DEC-0469; stack.md:241).
2. **Defaults ship.** "Ship enough defaults … Graph editing is not the only programming route" (DEC-0433, ADR-0024:60). Notebooks and scripts can be wrapped as operations.
3. **Draft.** The daemon issues `editor_draft_id`; saves need `expected_revision` (DEC-0487, DEC-0499).
4. **Validate.** The DAG check refuses cycles (DEC-0419); mapping must be explicit (DEC-0418).
5. **Publish and enable.** `publish_editor_draft` writes into the local authoring pack; enabling the pack sets the template identity `(qualified_id, version)`; then grant, select the instance, and `dispatchInvoke` (DEC-0487; SCN-0033).
6. **Run part of it.** `MissionCompiler(template, version, node_ids)` runs a selected subgraph, but only of a registered version (DEC-0417).
7. **Schedule.** A Routine fires a compile (DEC-0328). "A schedule/webhook trigger is not the workflow definition" (DEC-0417).
8. **Copilot building.** The transcript wants an n8n-style assistant that builds graphs (T:198; assistant at T:259, T:383). The docs say "Copilot discovers granted descriptors; prose is not authorization" (DEC-0422), but name no "copilot edits the graph" operation.

**Testing.** The docs define validation (DAG, schema, mapping) and a refused "Draft Run". There is no test run on fixture data and no "tested" state between draft and published. Test evidence comes only as BDD specs and the 85-scenario Codex catalog, which "is specification, not executed proof" (ADR-0024:25, :135). His "it has to pass tests" (T:313) has no step in the docs' workflow life.

### Mini apps and workflows

- A **pack** "requests operations, optional `view:*` wire DTOs, optional `copilot_profile` …"; "Headless packs … are first-class" (glossary:695-697, DEC-0452).
- A **mini app** is "an installed instance of a pack, keyed by `instance_id`" (glossary:699-701, DEC-0453).
- A **widget** is "a view of an operation — display only" (glossary:703-705, DEC-0455).
- Four ways apps combine: use a saved artifact, invoke an exported operation, coordinate through a Graph Template, or build a composite app as an instance graph (DEC-0423, ADR-0024:50).
- Pack life: `downloaded → installed → validated → enabled ⇄ disabled → uninstalled` (DEC-0443, ADR-0024:70).
- So, in the docs, workflows (Graph Templates) are contributions inside a pack, and a mini app is that pack installed. The UI storyboard says the same in plain words: a mini app is "a composition of widgets and workflows" (storyboard-reading.md:24). His path, board → tested → workflow or template → mini app (T:1068), maps to: draft → publish into the local authoring pack → enable. No graduation step from a board exists, because no board is stored.

---

## 4. Where things run, and the "installed like PyCharm" shell

- **Desktop today (docs).** "Python qma-daemon owns runtime. v1 is browser plus host-supervised daemon. Tauri 2 is an optional later desktop shell" (DEC-0478, ledger:4764-4766). `qmb host start|status|stop|pair…` supervises the daemon (DEC-0494). The browser app is a Svelte SPA, never served from daemon port 8765 (DEC-0469). The installer is deferred: "GAP-0112 Tauri 2 installer / sidecar supervisor … v1 is browser plus host-supervised daemon" (`main:docs/gap-report.md:271`).
- **"Installed like PyCharm".** The word PyCharm does not appear in `docs/`. The nearest ruling is the single-machine variant: the node runs "on the same machine as the agentic system as one installed QMX application, so that a non-technical operator … can set the whole platform up out of the box"; "the backend sets itself up"; "the desktop UI later carries an installation page" (DEC-0262, ledger:3282-3284; gap-report.md:169, GAP-0058, design owed). In the transcript he says "Remember, this is a desktop application" (T:887) and asks "this is a desktop application. How are we going to be doing that mini app thing?" (T:429). The Authoring layout is the "VS Code image" (DEC-0475).
- **Server.** The trading node: "three planes, two machines and one bucket"; the VPS plane runs the trading loop as a systemd service (DEC-0188; trading-node.md:117, :334). No node command line; control is "a user interface on the desktop application" (DEC-0211; trading-node.md:21).
- **Other compute.** Placement is a preflight, not a toggle: "available / configured / authorized / reachable / healthy … No cloud/Colab/provider is assumed; bind only through existing QMA ExecutionEnvironment / ComputeProvider ports" (DEC-0428). Work that must survive the laptop sleeping lives in the daemon plus remote environments (DEC-0278). Moving input bytes to a remote run needs `transfer_artifact` over TLS (DEC-0497). In the transcript he wanted local or server to be "a simple toggle in the UI, and then the back end carries the rest" (T:321).
- **Buckets.** Backups only (section 2a).
- **Gap now.** The docs' runtime (the daemon) is deleted in D3. The harness (`qma.serve`) replaces it. No doc says where `qma.serve` runs or how it installs.

---

## 5. Errors in our files 05, 10, 12 and 19

1. **05 §2, 10 §1, 05 §3a: wrong history of the Board.** `05:137` says the Board "became the Lab tiling workbench plus Start something new", and `10:78` builds on it. The trail in section 1 shows the Board's canvas became the **Authoring graph editor** (UI0923 research `02:268`; DEC-0475), and Authoring became the Lab Editor's Graph mode. This matches his reading.
2. **05 §3a: wrong rename.** `05:133` says "He renamed it the Experimentation Board because QMA has research staff". He renamed the assistant's "research board", not the storyboard (T:316).
3. **05 §2: wrong transcript size.** `05:107` says the transcript is "1,238 lines, 8 operator turns" at the `main:workroom` path. That file has 1,906 lines and 13 operator turns. `05:133` cites L1070 for "should be messy"; the line is 1068. The last turn (T:1791), where he calls the Library an "artifact library" that will become a database, is missing from 05.
4. **05 §3a and gap 7: "run scope was dropped".** `05:138` says run scope "was designed once … and dropped by later revisions". The docs keep it: DEC-0417 runs a selected subgraph via `MissionCompiler(template, version, node_ids)`, and the Codex scenario P1-WF-001 is "Execute selected valid subgraph on a messy storyboard". What the docs drop is running a **draft or board**, not running a section. `12:214` and `19:203` repeat the error by citing only revision 1.
5. **05 §2: wrong ratification status and line.** `05:109` says ADR-0024's AD-23..31 were "repairs required; not ratified", citing `:28`. That text is at `ADR-0024:25` and is Codex's verdict. The ledger folds the package "as ratified (AD-24..AD-31 with cheap-veto A1-A6)" (DEC-0417 rationale, ledger:4036). The ADR status is `ratified`.
6. **05 §4, 10 §2, 12, 19: "the Library is called Strats".** `05:151` (citing `BACKLOG.md:113`; the B8 row is at `:91`), `10:113`, `12:26` ("the docs' ban is lifted"), `12:171` and `19:43`, `:95`, `:383` all treat Strats as the Library's name. The docs say "Stats is seed corpus only. source_id=strats is the adapter key, not product copy" (DEC-0380), and `strats` is a refused Library kind (DEC-0271; ADR-0022:106). The operator now says the Strats folder was an old personal strategy library and is out of scope. The docs were right; our files and backlog B8 were wrong.
7. **05 §4, 10 §2 and mismatch 9: incomplete list of Library kinds.** `10:176` and `10:384` say the control Library has only `article` and `backtest`. The code also writes `remote-result` (`service.py:581`), `app-output` (`:777`) and any tool artifact kind (`qmx_tools/service.py:133`). `kind` is a free string, so the 15 shelves need writers, not a new table.
8. **05 §4: the two Libraries are not named.** 05 lists "five stores" but never says that two of them are both called Library with opposite rules: the QMB projection built to DEC-0271 (`registryread/library.py:1-9`) and the control Library from P22. It also misses that the docs forbid "a generic Library database" (LIBRARY-AND-ATTACHMENTS:16), which is exactly what the control Library is.
9. **05 §2 and 10 §1 table: the wrong engine behind the editor.** `05:118` and `10:103` tie the editor only to `workflow.v1` (deleted in D1). The docs' editor publishes Graph Templates for the QMA daemon's Task Graph (`qma-daemon/.../taskgraph/`, deleted in D3). `hp17` had two engines, against the docs' "No second scheduler" (DEC-0439). 05 §7 mentions the taskgraph only as the old research harness.
10. **05 §6: "WF1/WF2 … 'dead in docs'".** `05:219` cites memory, not the docs. The docs name "the old WF2 machinery (`mutation_allowance`, locked zones)" as **deferred** to the agentic sitting with a seam (`main:docs/components/qml.md:170`, DEC-0176), not dead. WF1 does not appear in the docs.
11. **10 §1: "prefers graphs and loops to an n8n-style editor".** `10:77` copies UI-BACKLOG R6 without a check. In the transcript n8n is his model for building, templates and the AI builder (T:198, T:316, T:319). The docs' shape, graphs with loops as node kinds (DEC-0340), is an n8n-like node graph. His 10-16 statement asks for an n8n-like editor on one engine. R6 should not be read as "no node editor".
12. **12 (c) and 19 C2: a new engine with no reference to the docs' engine.** The node kinds in `12:142` and `19:129` have no conditional, loop, join or artifact-dependency kinds, which both the docs (DEC-0312) and `workflow.v1` have. They also have no edge mapping (DEC-0418). 19 §10 does not list the conflict with DEC-0420 ("reuse QMA as the procedure runtime") or DEC-0439 ("No second scheduler").
13. **19 §1 decision 6: undercounted doc conflict.** `19:22` says the backend Board "changes two docs". The client-only rule is in at least seven places: DEC-0417, ADR-0024:44, ADR-0022:114, glossary:358 and :705, epics-WORKFLOWS:130 and :730, and UI0923 AUTHORING-AND-ML:69.
14. **19 §10: missing Library conflicts.** It lists no conflict for "Library stores everything" against DEC-0271 (workflows, skills, routines, templates and apps are not Library kinds), DEC-0476 ("must not collapse kinds") or the ban on a generic Library database.
15. **12 (g) and 19 C1: "archive, never delete" is not flagged.** The docs' pack life ends in `uninstalled` (DEC-0443, ADR-0024:70). 12 and 19 propose no delete and do not list the conflict.
