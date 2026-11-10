# 02 — Workflows, plugins and what the UI must show

Grounding for the UI planning session. Read-only pass, 2026-11-09.

Sources:
- Plan: `D:/QMX-worktrees/unit-plan/tracker/qma-v2/` (branch `plan/unit-system`, tip ee25171b, 2026-11-05). Below, `SPINE` means `architecture/workflow-engine/ARCHITECTURE-SPINE.md` (status final, last amended 2026-10-26), and `LAB` means `architecture/lab-and-pods/ARCHITECTURE-SPINE.md`.
- Code: `D:/QMX-worktrees/engine-base-read` (detached at 3ae41ffc, 2026-11-08). Paths below are relative to `qmx-agents/packages/` unless they say otherwise.
- `engine-base-read/tracker` and `engine-base-read/docs` hold no `qma-v2` tree, so nothing there is newer. Other worktrees (`risk-plan`, `agent-system`, `qma-ship`, `repair-ship`) hold no ruling that is newer on this topic.
- The latest binding rulings are 136-145 (2026-10-25 and 2026-10-26, `research/methodology/26-operator-rulings-and-alignment.md:261-290`). None of them changes the workflow and plugin model.

---

## 0. A correction to the starting premise (read first)

The operator's summary is half right, and the wrong half changes the UI.

- **Right:** a **mini app is a Claude plugin**, and so is every "pack": the Lab, Portfolio, the built-in groups and an `agent` item (SPINE AD-55, line 418; AD-19, line 196). The copilot's workflow builder is a **skill inside the core QMX plugin** (`qmx-agents/plugin/skills/build-workflow/SKILL.md`; SPINE AD-22, line 214). Choosing plugins was about reusing what the Claude CLI already loads (skills, sub-agents, slash commands) rather than rebuilding it (AD-19, "Prevents" line).
- **Not right:** a **workflow is not a Claude plugin**. A workflow is a QMX engine document: a folder holding `definition.json` in the `qmx.workflow/1` schema (n8n-shaped nodes and connections) plus its `scripts/`, `prompts/`, `schemas/` and `fixtures/` (SPINE AD-2, line 94; schema at `qmx-engine/src/qmx_engine/definition/schema/qmx.workflow.1.json`). QMX's own durable engine runs it, not the Claude SDK.
- **Claude Code's own Workflow tool is explicitly retired.** The `claude_workflow` node kind was dropped by the unlock pass, the harness keeps `CLAUDE_CODE_DISABLE_WORKFLOWS=1`, and the plan names "one engine" (ruling 22) as the reason (SPINE AD-5, line 112). In code the kind is still listed but never marked available (`qmx-engine/src/qmx_engine/definition/registry.py:95`).
- **A plugin, as built, does not even carry workflows.** When a mini app is published, its plugin bundle holds `.claude-plugin/plugin.json` (name, version, operations) and `skills/` only (`qmx-apps/src/qmx_apps/road/__init__.py:56-77`). When a chat loads that pack, it keeps `plugin.json`, `skills/`, `agents/` and `commands/`, and drops `hooks/` and `.mcp.json` (`qma-harness/src/qma/harness/packs.py:1-17, 156-168`). An app's workflows are named in `app.toml [entrypoints] workflows` (`qmx-apps/src/qmx_apps/manifest.py:102-107`), and the engine runs them as ordinary engine workflows.

So the accurate statement is: **packs and mini apps are Claude plugins; workflows are engine documents that a pack can contain; the copilot builds workflows through a plugin skill.** The plugin decision changes how mini apps reach the copilot (skills, agents, slash commands, tools). It does **not** turn workflows into something the UI manages like a plugin. If the operator meant something newer than these documents, that is open question Q1.

---

## 1. The model in plain words

**A workflow is a job you set up once.** It is a small diagram of steps with arrows between them, saved as one JSON file plus helper files in one folder. Each published version is frozen and has a content hash (SPINE AD-2, line 94; AD-11, line 148).

**Agentic and non-agentic are not two product kinds. They are shapes of the same thing.**
- *Script only:* deterministic steps (fetch, parse, compute, write). There is no model step, so a run spends no tokens.
- *Mixed:* scripts plus one or more `llm` steps (one model call each, with a JSON schema).
- *Fully agentic:* one `agent` step does the work. A single-agent workflow is "one trigger node plus one `agent` node and is still a workflow" (SPINE AD-2; ruling 52; ruling 44).
- The builder skill states the three shapes and prefers script-only "whenever the job is arithmetic or retrieval" (`qmx-agents/plugin/skills/build-workflow/SKILL.md:64-74`).
- The operator's own words: "a mini app can be a combination of workflows. It can be agentic or non-agentic" (`alignment/B-fri-afternoon-evening.md:34`).
- The shipped templates are mostly deterministic. Across the 55 template definitions in code there are 271 `script` nodes, 72 `llm` nodes, 43 `grader` nodes, 41 `rule` nodes and only 17 `agent` nodes. 14 templates have no model step at all (tallied from `qmx-engine/src/qmx_engine/templates/*/definition.json`).

**Step kinds (closed list).**
- Built and available: `trigger`, `script`, `rule`, `loop`, `join`, `wait`, `llm`, `agent`, `subworkflow`, `grader` (deterministic mode only), `monitor`, `app_op`, `library` (`definition/registry.py:56-95`).
- Designed, not available: `human_gate`, `rlm`, the grader's `llm` mode (`registry.py:62, 81`).
- `note` is draft-only.
- Packs add types named `<pack>.<name>` on top of a base kind (SPINE AD-5).
- An `agent` step is a Background chat of the harness. It gets a scoped tool surface and helper sub-agents, writes into its own private folder, and has no turn or time ceiling (`qmx-engine/src/qmx_engine/nodes/agent.py:1-25`; SPINE AD-4, AD-60).
- A model can never decide which arrow is taken. A model only produces data, and a `rule` step reads that data (SPINE AD-1).

**Lifecycle.**
- `draft → published (version) → enabled ⇄ disabled → archived`.
- `validated`, `tested` and `stale` are marks on a version, not states (SPINE AD-11).
- Code allows exactly this (`qmx-engine/src/qmx_engine/service/context.py:26-39`): edit, validate and test on a draft; publish only once tested; run, enable and archive only on a published version; nothing is deleted.
- Drafts never sit on `main`. His draft lives at `refs/drafts/<item>`, and a copilot draft lives at `refs/agents/<session>/<item>`.
- Publish and enable are his clicks only. The service refuses them from agent and workflow callers (SPINE AD-11, AD-22).

**Triggers.**
- A trigger is a row stored outside the definition, pinned to one exact published version (SPINE AD-10, line 142).
- Kinds: `cron` (with an IANA zone), `interval`, `manual`, `after` (another workflow finished), `webhook`, `event` (something landed in the Library) and `session` (`qmx-engine/src/qmx_engine/triggers/rows.py:9-12`).
- Each trigger has a home place (`pc` by default, ruling 142), a priority, an optional `ready_by`, model pins and a delivery target (`inbox | digest | silent`).
- A trigger records its last status (`ok | silent | blocked_config | failed | delivery_failed | unknown`) and its fire statuses (`rows.py:47-64`).
- A version counts as "enabled" exactly while an enabled trigger pins it (derived, never stored).
- `explain_trigger` answers "why didn't it fire" (SPINE AD-10; `/api/triggers/{id}/explain`).

**Runs.**
- Every run has a `mode` (`live | test`) and a `status` from one shared table: `queued, running, waiting, passed, failed, stopped, interrupted` (`qmx-engine/src/qmx_engine/ports/library.py:56-59`).
- Each step has a phase: `scheduled, started, finished, failed, waiting, skipped` (`core/state.py:24`).
- Finished steps are saved and never paid for twice. A rerun reruns only the steps that changed. "Rerun from here" is a fork (SPINE AD-7).
- Every unit of work is a workflow run. The separate remote-run and job lists are retired (SPINE AD-57, line 430).

**Inbox.**
- The inbox is the one notification channel. Severities are `info` (daily digest), `normal`, `urgent` and `black` (SPINE AD-17, line 184).
- Only provider failures, harness or ledger errors and unknown outcomes of irreversible outside effects reach the inbox. Logic failures go to the digest.
- The actions are a closed set: `retry, stronger_model, skip_node, open_trace, stop, resume` (`qmx-engine/src/qmx_engine/ports/inbox.py:33-45`).
- "Human points" (approve a promotion, accept a lesson) are **proposals** on the run card, not inbox items.

**Templates.**
- A template is a published workflow tagged `template`, with a `slots` schema. "Use this template" asks for the slots, then makes a draft (SPINE AD-46, line 364; AD-22).
- **Code has 55 catalog rows, not 32.** The docstring still says 31 (`qmx-engine/src/qmx_engine/templates/catalog.py:1-3, 71`).
- Rows whose `needs` are not met (trading node, QMB, real Library, sandbox) install as validated drafts. The rest are tested and published **disabled**, with their schedules added disabled (`catalog.py:1-12`; `templates/install.py`).

**Plugin shape (packs and mini apps).**
- A pack folder holds `app.toml` plus the plugin layout: skills, agents and commands.
- It holds workflows (engine documents), widgets (display only) and operations (tools served on the chat's one in-process `qmx` server) (SPINE AD-19, AD-55).
- When published, a pack becomes a `mini-app` Library item. Each host turns it into a plugin view under `<home>/plugins/<id>/` (`qmx-host/src/qmx_host/sessions.py:266-281`).
- An app's schedule is an engine trigger on an `app_op` workflow inside its pack (`[suggested_trigger]`, created when he enables the app; `qmx-apps/src/qmx_apps/manifest.py:167`; SPINE AD-57).
- "Workflow grows into a mini app" works by pinning: the copilot drafts a pack that pins one or more published workflow versions and generates one widget per output (`research/methodology/45-lab-library-miniapps-domain.md:210-221`).
- The `build-mini-app` skill is still a **placeholder** (`qmx-agents/plugin/skills/build-mini-app/SKILL.md`).

**How a workflow gets made.**
- **By the copilot** (the main road):
  1. He says one line.
  2. The `build-workflow` skill runs a short interview (Trigger, Checkpoints, Brief; at most three questions, each with a recommended answer).
  3. It classifies the shape, writes the draft, lints and validates it, and test-runs it on cheap real models.
  4. It shows a result card. Saving and testing never ask him; publishing and enabling are his click on the card (`SKILL.md`; SPINE AD-22).
  5. "Traces first": the workflow starts loose, he reads the first test traces with the copilot, and then the copilot proposes tightening steps into scripts and rules (AD-22).
- **By template:** use the template, fill the slots, get a draft.
- **By hand:** the REST door exists (draft get and put, validate, test, versions, archive, run, triggers, runs, inbox), served by `qmx-control/src/qmx_control/service.py:2145-2390`. **No hand editor is built**: there is no Graph/Code projection, no `drafts.patch` and no board view in code (grep finds no `to_graph`, `to_code` or `meta.view`).

---

## 2. What the UI must show

All of this is backed by built routes unless it is marked *(designed, not built)*. The Workflows screen is listed as wireable now (`UI-HANDOFF.md:34, 40`).

**Workflow list**
- One row per workflow item: plain name, shape badge (script only / mixed / agentic, derived from step kinds), state (draft / published / enabled / disabled / archived), tested mark, next fire, last run status and its home place.
- Workflows from a mini app appear here too, with the app named (`UI-HANDOFF.md:91-92`).
- There is **no list-all-workflows route** in the control ops. The list has to come from a Library search on the `workflow` kind, or needs a small new read. Flag this for the backend.
- Template shelf: name, what it does, "needs X" when it cannot run yet, and "Use this template".

**Workflow detail**
- A read-only step diagram (or step list) with plain step names, so he can see what it does.
- The inputs it takes.
- Where it runs.
- The standing grants its toolsets hold (the "ask first" actions it may do unattended) (UI-HANDOFF §15.7).

**Versions**
- A list of published versions with semver, tested mark, the run that tested it, and which triggers pin each one.
- Draft vs published on every card.
- Archive a version (`/api/workflows/{id}/versions`, `/archive`).
- Champion badge *(designed, not built: no `self_improve` in code)*.

**Triggers**
- Kind and schedule in his words.
- Zone, home place, enabled toggle, the version it pins, last status, next fire.
- "Run now", edit inputs, open incident, and "why didn't it fire" (`/api/triggers*`, `/explain`).
- A trigger is created disabled.

**Runs**
- One list for every unit of work, newest first, filterable by workflow: status, mode (test or live), start, duration, cost, place, delivery status (`/api/workflow-runs`).
- Actions: cancel, resume, explain.
- "Rerun from here" *(service fork designed; check that it is wired)*.

**Run timeline**
- One lane per step: phase, attempts, waits with their reason (usage limit, time, backoff), model, tokens, cost and duration from spans (`/api/ops/spans/{run_id}`).
- Files changed per agent step.
- Output links into the Library.
- Proposals at the end.
- `/api/engine/events` is the live stream.

**Inbox items**
- Cause, what was tried, cost so far, a trace link and the closed action buttons. Button labels come from the action, never from model text (SPINE AD-17; `/api/inbox`, `/api/inbox/{id}/resolve`).
- Logic failures show in the daily digest, not as alarms.

**Making and editing**
- *Copilot-made* (primary):
  - In chat: the interview questions with recommended answers, then a draft card (step summary, test result, test cost) with Publish and Enable buttons that call REST as him.
  - After the first traces: a "tighten" proposal.
  - This is where most creation happens. The UI is mostly cards and a read view.
- *By hand*: rename, edit inputs and schedule, switch triggers, pick models per role, archive. These are form edits on rows and settings, not graph editing.
  - Editing steps by hand needs the Graph/Code editor, which is unbuilt. Whether he wants it at all is Q2.
  - A "view the JSON or open the folder" escape hatch is cheap and matches "boards are simply code" (ruling 31).

**Mini apps and plugins**
- An app card shows its operations, feeds from and feeds to, freshness, health and logs.
- Its schedules appear on the Workflows screen, not on the app card (UI-HANDOFF §6).
- An app's skills, agents and slash commands appear in the copilot like any plugin's: tools join at once, skills from his next message.
- No per-app copilot.

---

## 3. What is stale in the old design

| Old design element | Status | Why |
|---|---|---|
| Lab "Graph mode / Code mode" editor as the way workflows are made (SPINE AD-21; LAB AD-2) | **Designed, never built**, and pushed aside by the builder-first road | AD-22 and the build-workflow skill make the copilot the maker ("He never sees a form"). There is no graph/code projection in code. |
| A palette of every node kind for him to drag | Overbuilt for a non-technical operator | Kinds are a closed list the copilot picks. Showing them read-only is enough. |
| `claude_workflow` node / Claude Code Workflow tool | **Retired** (SPINE AD-5) | One engine. |
| Separate Remote runs / Jobs screens | **Retired** (SPINE AD-57) | One run list. |
| Lab node pack palette (`lab.*`, `qmb.*`, `ml.*`, `pod.*`, `paper.*`) (LAB AD-3) | **Unbuilt** | The registry registers no pack types (`with_pack` has no caller outside its definition). The Lab backend is only a workspace over the Library and templates (`qmx-control/src/qmx_control/lab.py:45-60`; LAB AD-19). |
| Pods bench (Design, Test, Paper) | Parked | LAB AD-19: pods are not in the first Lab slice. Units replace bots (ruling 138), owned by the unit session. |
| Per-app copilot, app Remove / delete | Stale | No per-app copilot. Archive, never delete (UI-HANDOFF §6). |
| Templates "32" | Stale count | 55 catalog rows in code. |
| A "Board" as its own kind | Not a kind | A board is a workflow draft with `meta.view: board` (LAB AD-2). Not built. |
| Placement wording ("Contabo default", QMB machine for backtests) | Superseded | Local first, `pc` by default (rulings 140-144; SPINE AD-3/AD-10 *Local first* notes). |
| Spend asks, budgets and caps in Lab or workflow settings | Removed | Rulings 27, 106; AD-40. |
| `build-mini-app` as a ready road | Placeholder | The skill body is "Pending authoring". |

---

## 4. Lab declutter implications

What the Lab is today:
- The plan's Lab is a "Strategies bench: Build, Test, Train, Compare; Pods bench: Design, Test, Paper" with an editor whose Graph and Code views project one draft (LAB line 7; AD-2).
- The built backend is much thinner:
  - projects are Library collections;
  - "New…" installs a template at one of four levels: quick idea, experiment, study, campaign (`lab.py:45-60`);
  - every Lab procedure (backtest, sweep, walk-forward, training, stress) is a `qmx.workflow/1` template run by the engine (LAB AD-4, AD-19).

What follows from that:
1. **The Lab does not need its own workflow editor.** Workflows are made by the copilot and seen on the Workflows screen. A Lab "Build" tab with a graph canvas duplicates the Workflows screen and the copilot, and it has no backend. Drop the canvas from v1, or reduce it to a read-only step view. Q2 asks him whether he wants hand-editing at all.
2. **The benches collapse into runs of templates.**
   - "Test", "Train" and "Compare" are the same act: run a published procedure template on a subject, then read the results.
   - Today's backend expresses this as *project → items → runs → results*, not as four benches.
   - A decluttered Lab: a project explorer, a subject view (the strategy or unit and its versions), a "Run…" picker over procedure templates, and a results and compare view over `workflow-run` and `backtest-result` objects.
3. **Pods bench out.** It is unbuilt, parked behind the unit session (ruling 138; LAB AD-19). Do not design it in this pass.
4. **Lab copilot = the main copilot with the `qmx-lab` pack loaded** (LAB AD-14, SPINE AD-55). It is not a separate side copilot with its own tool set. That removes the side-copilot settings and the "continue in main copilot" absorb pattern (`research/methodology/23-ui-clickthrough.md:349`).
5. **Machine picker** becomes the one "This PC or a place" choice per job (SPINE AD-72), shown on the run start, not a Lab-only widget.
6. **Keep notebooks and "run just this part" as later items.** `KernelPort` and selected-subgraph runs on boards are designed and unbuilt.

The net effect: the Lab becomes a **research workspace** (projects, subjects, run a procedure, compare results). It stops being a second IDE for workflows.

---

## 5. Open questions only the operator can answer

1. **"Workflows are Claude plugins": did you mean something newer than the plan?** The plan and the code say packs and mini apps are plugins, and workflows are QMX engine documents run by QMX's own engine. Claude Code's own Workflow tool is retired. If you want workflows to *be* plugins (each one shipped as a plugin, or the Claude Workflow tool brought back), that reverses AD-2, AD-5 and ruling 22. Recommended: keep the plan.
2. **Do you want to edit workflow steps by hand at all?** Recommended: no for v1. The copilot builds and changes steps; you edit only the schedule, inputs, models and on/off switches; a "show the file" view covers curiosity. The graph editor stays a later item.
3. **Lab benches.** Is it fine to replace Build / Test / Train / Compare with project → subject → run a procedure → compare results, and to leave Pods out until the unit session? Recommended: yes.
4. **Templates on first start.** The code installs 55 templates, published but switched off. Do you want all 55 on the shelf, or a short curated starter set with the rest under "more"? Recommended: a curated set grouped by the Lab's four levels.
