# UI handoff: everything the UI session needs (running list)

Started 2026-10-16 by the lead session, at the operator's request (ruling 47). It is kept up to date as each design lands. **Read this before wiring anything.** `UI-NOTES.md` still holds the harness event details. This file adds everything since then.

Binding rulings: `research/methodology/26-operator-rulings-and-alignment.md`. Sources for each item are in brackets.

## 0. Ground rules for the UI session

- QMX is a **desktop application**. The browser is only the design-time host (rulings 32, 40). Never design for a web version.
- Build with **demo mode OFF**, so unwired places say "Not connected" instead of showing sample data [10 §6.17].
- **The UI is a design, not a coded product.** Its code exists only to show the design. Backend requirements come from the screens' intent (screenshots), never from the UI code or its types.
- Demo data shows the intended shape. Don't treat its specifics as the backend contract [ruling J/UI].
- Node 22 is pinned, but the machine has Node 24. `pnpm dev` hangs, so start Vite directly [10, 23].
- Treat `BACKEND-REQUIREMENTS.md` and `handoff/MINI-APPS-AND-COPILOT-CONTRACT.md` in the UI repo as history. The real door is REST + SSE (`/api/chats`, `/api/sessions/{id}/turns`, `/live`, `/api/approvals/{id}`, `/api/usage`, `/export`) [10 §6.15].

## 1. Fix before wiring the harness (QMA v2, exists today)

1. **Block renames:** `tools→tool`, `changes→changed`, `cards→entity`, `ask→question`. Add a `needs_you` renderer. Decide whether `tool` is one call or a batch [10 §6.1].
2. **Session home:** show a home badge. A session keeps its birth home. "Open in hub" must not rewrite the home, and there must be a way back to the Lab. Replace the one-way `absorb()` [10 §6.2-6.3, 23, ruling 12]. The backend home field is still owed (harness writes `origin="qma"`).
3. **Status words:** add `failed`, `cancelled`, `expired` [10 §6.4].
4. **Approvals:** the backend has **four** answers in code (`allow_once | allow_always | reject_once | reject_always`; verify `cancel` against hp17). "For this errand" doesn't exist. Add "expired, re-run from here" [10 §6.5, 20b].
5. **Sub-agents:** show start, end and result only. The backend has no live progress [10 §6.6].
6. **Harness features missing in the UI:** effort control, compaction events and "compact now", stop/interrupt/steer, the model-switch cost warning, a usage page, Export per session [10 §6.12, UI-NOTES].
7. **Terminal:** label it read-only. It is not a shell [10 §6.13].
8. **Output:** add a Markdown renderer and diagram parts in the panel catalog. These are pure UI work [10, 19].

## 2. Do NOT wire yet (no backend today)

- Lab copilot tools (`qmb.*`, `lab.*`, `pod.*`, `graph.edit_draft`, `compute.place`) [10 §6.7]. These arrive with the Lab/Pods design (section 5).
- Editor draft, publish and run. `workflows_*` return 501 until the engine ships [10 §6.8].
- Pods bench, Portfolio pod screens, Portfolio copilot tools [10 §6.16].
- Mini-app build paths ("from widgets", "describe it") [10 §6.10].

## 3. Coming with the workflow engine (`architecture/workflow-engine/`)

- **A Workflows screen** is needed. Today workflows have no screen of their own [23 §3]. It needs a list, versions, enable/disable, triggers, and runs.
- **One draft, two views:** the Lab editor's Graph mode and Code mode are projections of ONE draft. The saved Board is a draft. Free-form note nodes and unconnected nodes are allowed in a draft [engine AD-11].
- **Lifecycle states to show:** draft → validated → tested → published (version) → enabled ⇄ disabled → archived. A draft can only run in test mode. Selected-subgraph runs ("run just this part") are allowed [engine AD-11].
- **Test runs use real models** through existing providers (ruling 51). Show each test report and its cost.
- **Run timeline:** one trace per run and one span per step (status, cost, time, account, model). Steps that waited at a usage limit show `waiting (resume_at)` [engine §observability].
- **Inbox items:** one per problem, with buttons: retry, stronger model, skip step, open trace, stop. Long-pause alert after 6 h (editable) [engine §failure ladder].
- **Account pool settings:** list accounts per provider, the strategy (fill-first / round-robin / least-used), cooldowns. OpenRouter is marked test-only. GPT capacity is 1 [engine pool AD].
- **Defaults are all UI-editable.** The list is in `SOLUTION-DESIGN.md` §17.
- **Copilot builder:** the copilot asks numbered questions with suggested answers, then draws the draft on the canvas.
- **Templates:** a template is a copyable workflow. A variant is an overlay with a "variant of" link (ruling 48).
- Node kinds the palette needs: trigger, script, rule, loop, join (all/any/quorum), wait, human gate, llm, agent, sub-workflow, grader, monitor, app op, library, claude_workflow (off in v1).

- **Nothing waits for him during a run** except an irreversible outside effect, which goes to the inbox while the run parks [engine AD-22]. Publishing or enabling a workflow asks once. Self-improvement shows "challenger vs champion" with automatic rollback [engine AD-26].
- **Where it ran:** each run card shows its placement (PC, server, Amp runner or orb, E2B/Modal) and its sandbox tier [engine AD-24/25].

## 4. Coming with the Library (`architecture/library-and-data/`)

- **One Library holds everything** (ruling 28). There are 29 object kinds, including unit, bot, bot card, workflow, workflow run, mini app, skill, methodology, source, note, backtest result, board, merge conflict [library AD-3].
- **Previews and detail tabs are driven by schema data.** Render them from each kind's schema, not hand-built per shelf [library AD-17].
- **Links are typed,** from a closed list (CT-07's 14 relations plus 17 Library ones). Show "Used in", "Produced by", "Tested by", "Variant of" and so on as real links between items, not links to screens [library AD-4, 23 §1].
- **Versions and branches:** `main` is the trusted version. Agents work on their own branches. A merge conflict is an object with a side-by-side diff view [library AD-7].
- **Archive, never delete.** There is no Remove button; there is Archive with a reason [library AD-6, ruling 9].
- **Search:** text search plus the links map. Answers cite items. A "nothing found" refusal comes before any model runs [library AD-8].
- **No asks on Library writes** from workflows (ruling 57). The UI shows what landed; it doesn't gate it.
- The Library may live on his server later (ruling 56). The UI must tolerate a remote home: loading states, offline cards.

- **A "landed" feed, not a gate:** workflow results and the items workflows produce fast-forward into `main` under a per-workflow standing rule (`publish auto|hold`, default auto). The UI shows what landed and never gates it. A copilot-chat merge of governed kinds (units, bots) still asks once [library AD-18, OPEN-7].
- **Library home can switch** between the PC and the server (`[library] primary`). The UI never knows which store answered [library AD-19].
- **New kinds to render:** `dataset` cards (every result shows what data it consumed), `memory-row`, `agent-tool` (marked unreviewed), `book`/`bms` (compiled from a pod), `model` with versions [library LLD §3].

## 5. Coming with Lab and Pods (`architecture/lab-and-pods/`)

- **The full map is `architecture/lab-and-pods/UI-TO-BACKEND-MAP.md`:** every Lab and Pods UI element, the backend piece it needs, and the screenshot that shows it (`23-ui-shots/` and `lab-and-pods/ui-shots/36-58`). Wire against that map, not against demo data.
- **The Lab owns no runner and no store.** It is document kinds plus a Lab node pack plus templates on the ONE engine and the ONE Library [AD-1]. The UI computes nothing. Every number comes from the service through REST, MCP or in-process calls [AD-15].
- **One draft per subject.** Graph and Code are projections of the same draft with a round-trip check. The authoritative form depends on the kind: a workflow is JSON, bot logic is code, a pod block follows its own kind, a board is cells [AD-2].
- **The palette is the engine's registry, filtered** to the Lab pack (`lab.*`, `qmb.*`, `ml.*`, `pod.*`, `paper.*`, `data.*`). "Run this part" is a selected-subgraph test run. The fresh/stale dots come from the engine's memo [AD-3, AD-4].
- **Backtests:** a `setup` is compiled and run through the qmb node pack. The old `run_backtest(config_ref)` door retires. The holdout is touched once per family [AD-5, AD-6].
- **ML:** model objects with versions. A slot is a port that mints a new version. The machine picker uses the engine's placement preflight [AD-7, AD-8]. Notebooks run on a KernelPort [AD-9].
- **Pods:** a versioned stack of blocks in seven slots. One simulator drives size trail, test, stress, fan, head-to-head, mix and paper [AD-10]. Pods compile to Book+BMS [AD-11]. Paper trading is an engine run on a paper ledger over live prices. Promote mints a card. Signing and activation stay as Portfolio's two clicks [AD-12].
- **The Lab copilot's 17 tools** ship as a plugin with Effects [AD-14].
- **Deferred:** pairs, Colab, broker demo/testnet paper money, live sub-agent lines, the explainer video.
- **Dev-server tips:** bits-ui menus open with a focused trigger plus Enter/ArrowDown. Dialogs open via `element.click()`. Hide the Reticle overlay with a fixed-ancestor `display:none`.

## 6. Mini apps

- **Archive, never delete** (ruling 9). Today the UI has Remove; the backend has neither delete nor disable [10 §6.10].
- **Two mini-app data sets disagree:** Apps has 21 apps, the Library shelf has 2 with other ids [23 §5]. Use one source, the Library.
- **Per-app copilot:** the UI offers one, but the design says any copilot loads an app's pack and no app has its own copilot [10 §6.11]. The UI should drop the per-app copilot setting.
- A mini app is a plugin pack containing workflows, widgets and tools. Workflows inside it appear on the Workflows screen too.

## 7. Pending studies that may add items

- Workflow memory (`research/methodology/28-workflow-memory.md`): lessons and "already built" hints may surface in the UI.
- Environments and deployment (`29-environments-and-deployment.md`): where each run runs (PC or server), shown on the run card.
- Browser plan: the watch pane and lease queue. This is still owed to the operator.
- Phone alerts: later (ruling 34).
