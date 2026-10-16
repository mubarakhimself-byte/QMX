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
2. **Session home:** show a home badge. A session keeps its birth home. "Open in hub" must not rewrite the home, and there must be a way back to the Lab. Replace the one-way `absorb()` [10 §6.2-6.3, 23, ruling 12]. **The backend field is now designed (engine AD-35):** `home: {kind: general | lab | portfolio | library | app, project_id}` lives in `qmx_control` (`session_homes`), not in the harness, which keeps writing `origin="qma"`. The UI writes it once, right after `POST /api/chats` and before the first turn, with `PUT /api/sessions/<id>/home` (a second write is refused `home_fixed`); Child chats inherit the parent's home; a session with no home reads as `general`. Every screen can open and continue any session through the same session id and turn routes; "open in its home" is the way back.
3. **Chat status words** (chat turns, not runs): add `failed`, `cancelled`, `expired` [10 §6.4]. Run statuses are a different set (§9 row 8) and have no `cancelled`.
4. **Approvals:** the backend has four **decisions**: `allow_once`, `allow_always` (not offered when a QMX tool asks), `reject` (with a message) and `answers` (the reply to an AskUserQuestion). An answer returns `resolved | already_answered | expired | invalid | unknown`. There is no `reject_once` or `reject_always`, and "for this errand" doesn't exist. Add "expired, re-run from here" [`QH/routes.py:180-205`, `QH/chat.py:230-253` on hp17, 27b F11; 10 §6.5, 20b].
5. **Sub-agents:** show start, end and result only. The backend has no live progress [10 §6.6].
6. **Harness features missing in the UI:** effort control, compaction events, stop/interrupt/steer, the model-switch cost warning, a usage page, Export per session [10 §6.12, UI-NOTES]. "Compact now" has **no backend**: the harness only observes compaction today; it needs harness request H15 (engine HARNESS-REQUESTS), so leave the button out until he grants it [27b F14].
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
- **Lifecycle states to show:** draft → validated → tested → published (version) → enabled ⇄ disabled → archived. A draft can only run in test mode. Selected-subgraph runs ("run just this part") are allowed [engine AD-11]. Drafts never sit on `main`; see §9 for the draft vs published badge.
- **Test runs use real models** through existing providers (ruling 51). Show each test report and its cost. Saving a draft and running a test never ask him; publishing and enabling ask once.
- **Run timeline:** one trace per run and one span per step (status, cost, time, account, model). Steps that waited at a usage limit show `waiting (resume_at)` [engine §observability].
- **Inbox items:** one per problem, with buttons: retry, stronger model, skip step, open trace, stop, resume. Long-pause alert after 6 h (editable) [engine §failure ladder]. Only provider failures and harness-level errors reach the inbox; everything else is a digest line (§9 row 9).
- **Account pool settings:** list accounts per provider, the strategy (fill-first / round-robin / least-used), cooldowns. OpenRouter is marked test-only. GPT capacity is 1 [engine pool AD].
- **Defaults are all UI-editable.** The list is in `SOLUTION-DESIGN.md` §17.
- **Copilot builder:** the copilot asks numbered questions with suggested answers, then draws the draft on the canvas.
- **Templates:** a template is a copyable workflow. A variant is an overlay with a "variant of" link (ruling 48).
- Node kinds the palette needs: trigger, script, rule, loop, join (all/any/quorum), wait, human gate, llm, agent, sub-workflow, grader, monitor, app op, library, claude_workflow (off in v1).

- **Nothing waits for him during a run** except an irreversible outside effect, which goes to the inbox while the run waits (`waiting`) [engine AD-16, AD-17]. Publishing or enabling a workflow asks once. Self-improvement shows "challenger vs champion" with automatic rollback [engine AD-26].
- **Where it ran:** each run card shows its placement by registry name (`pc`, `contabo`, `qmb`, or a provider row such as an Amp runner or orb, E2B, Modal, or a managed agent host like Cloudroom or Amp threads), its `agent_mode` (`runner_outside | cli_inside | host_harness`), its sandbox tier, and the run's `mode` badge (`live | test`) [engine AD-24/25, AD-32].

## 4. Coming with the Library (`architecture/library-and-data/`)

- **One Library holds everything** (ruling 28). There are 33 object kinds, including unit, bot, bot card, workflow, workflow run, mini app, skill, methodology, source, note, backtest result, board, merge conflict [library AD-3].
- **Previews and detail tabs are driven by schema data.** Render them from each kind's schema, not hand-built per shelf [library AD-17].
- **Links are typed,** from a closed list (CT-07's 14 relations plus 24 Library ones; one of the 24, `ran-on`, is retired, because where a run ran is now a field on the run). Show "Used in", "Produced by", "Tested by", "Variant of" and so on as real links between items, not links to screens [library AD-4, 23 §1].
- **Versions and branches:** `main` is the trusted version and holds published versions only. His drafts sit on `refs/drafts/<item>`; agents work on their own branches. A merge conflict is an object with a side-by-side diff view [library AD-7].
- **Archive, never delete.** There is no Remove button; there is Archive with a reason [library AD-6, ruling 9].
- **Search:** text search plus the links map. Answers cite items. A "nothing found" refusal comes before any model runs [library AD-8].
- **No asks on Library writes** from workflows (ruling 57). The UI shows what landed; it doesn't gate it.
- The Library may live on his server later (ruling 56). The UI must tolerate a remote home: loading states, offline cards.

- **A "landed" feed, not a gate:** workflow results and the items workflows produce fast-forward into `main` under a per-workflow standing rule (`publish auto|hold`, default auto); new workflows, apps, pods and skills a run made arrive as drafts instead. The UI shows what landed and never gates it [library AD-18]. A copilot-chat merge of governed kinds (units, bots) or lifecycle kinds (workflows, apps, pods) into `main` asks once [library AD-9].
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
- **The Lab copilot's 17 tools** ship as a plugin with Effects [AD-14]. Their tool-table rows need his grant (engine HARNESS-REQUESTS H17).
- **No spend asks anywhere in the Lab** (ruling 27). Show estimates; never gate on them. There is no `ask_above_usd` setting.
- **Backtests run on the QMB machine** (the `qmb` placement, ruling 68); results from `qmb` or the PC count as evidence, any other placement shows "Exploration only" [Lab AD-5, AD-8].
- **Paper is one run per trading day,** chained; pause = switch the daily schedule off, resume = on, +7 days = more days [Lab AD-12].
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

## 8. Notifications (ruling 77)

- Notifications are designed by the UI session. The engine only emits inbox items: provider failure, harness-level error, and the rare irreversible external step. Phone, toasts and digest are UI-side.
- MCP apps (the Model Context Protocol apps standard, interactive UI in chat as used in Claude Desktop) are a UI topic. The design discussion is tomorrow.

## 9. Machines, keys, providers, context (added 2026-10-16 night, 27c gap fixes)

Fifteen rows the UI session needs that earlier sections missed [27b §5]. Each names its backend source.

1. **Machines list in Settings** = the placement registry with live preflight states (`available → configured → authorized → reachable → healthy`), sessions in use / `max_sessions` (derived from RAM; about 4 on Contabo today), RAM in use, vault sync age, last error, and each row's `relay: local | central`. Run cards, spans and inbox items show `placement`, `agent_mode`, the run `mode` badge, `health`, `cost so far` and `link_out`. A live desktop or VM view loads only for nodes with `watch: true`, and only when he opens it. Provider dashboards are reached by the copilot, not rebuilt [engine AD-30, AD-32; SD §21, §23].
2. **Keys once:** per key `replicable`, `vault_version` and last sync; "key rotated, N relays updated"; re-pair placements; `qmx node login <placement>` for a plan sign-in on an owned machine [engine AD-28; SD §19].
3. **Providers and roles:** a provider row = base URL + key ref + four tiers + quirks (+ `wire: openai_chat`); role candidate lists **per placement** (`pc`, `contabo`, burst rows); OpenRouter marked test-only [engine AD-13, AD-29; SD §9].
4. **Provider onboarding:** "Add a provider" starts the copilot flow that reads the provider's own published instructions and drafts a placement row; he applies it with one click and types any key once; a smoke test result card follows [engine AD-30, ruling 74; SD §21].
5. **Cua scope and manifest editor** on an agent node (apps, origins, profile `isolated | logged_in`, expiry); screenshots in the trace; the always-on broker deny-list shown read-only [engine AD-33; SD §24].
6. **Self-improvement:** per workflow `self_improve auto | propose_only | off`; a champion vs published badge; a "rolled back automatically" line [engine AD-26].
7. **Agent-made tools:** `unreviewed` / `reviewed` with a review action [library AD-3].
8. **Run vocabulary:** one status set for every run, `queued | running | waiting | passed | failed | stopped | interrupted` (with a reason on `waiting`, `failed` and `stopped`), plus a separate `mode` badge `live | test`. "Tested" = a passed run in either mode [engine SD §3.1, library AD-15].
9. **Inbox severities:** `info` (daily digest), `normal`, `urgent`, `black` (repeats until acknowledged). Only provider failures, harness or ledger errors, unknown outcomes on irreversible external steps and stolen passes reach `normal` and above (ruling 77). Actions `retry | stronger model | skip node | open trace | stop | resume` [engine AD-17; SD §10.4].
10. **Chunk progress** on fan-out nodes (chunk n of m, cache hits per chunk), a **tool-call sub-timeline** under each agent span, and `compacted` markers on the span [engine AD-34].
11. **Draft vs published** on every workflow, mini-app and pod card; run-made workflows, apps, pods and skills arrive as drafts waiting for his one yes; triggers show the exact version they pin and whether they follow the champion [engine AD-10, AD-11; library AD-7, AD-18].
12. **QMB machine** as a placement with its own queue depth [engine AD-31].
13. **Lab paper** as a daily schedule: Day n of m, pause = disable the daily trigger [Lab AD-12].
14. **Library home indicator:** off. The UI never shows which store answered, but shows `primary_moving` during a cut-over [library LLD §7].
15. **Harness budgets** in Settings: `max_live_chats`, `max_budget_usd` (shown as a runaway guard, never as a spending cap), `background_cap`, each with its effect on workflows; and the engine's runaway guard per workflow (tokens, agents, tool calls, wall time, `on_runaway: pause | degrade`). No spend ask exists anywhere (ruling 27) [engine SD §7.4, §17].
