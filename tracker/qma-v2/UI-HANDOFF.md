# UI handoff: everything the UI session needs (running list)

> **The UI is a design, not code (operator, 2026-10-16 and 2026-10-18).** The UI has been designed and drafted, not engineered; its code will change a lot. The intent lives in the design: what each screen shows, the click-throughs with demo data, the storyboard. Read the UI as a design (run it, look at it, click through it), never take requirements from its component code or types alone.
>
> **The demo design is not final either.** Many backend capabilities were added after it was drawn. The UI session should propose redesigns where a better representation exists, and should leave some capabilities without a screen of their own when a status update, badge or line in an existing view is enough. Not everything in this list needs its own surface.

Started 2026-10-16 by the lead session, at the operator's request (ruling 47). It is kept up to date as each design lands; last brought current on 2026-10-22 against rulings 1-134 (the data round, §17 below; earlier: 2026-10-18 against rulings 1-118), the rerun (39 with its review and fix-check applied) the unlock pass (`research/methodology/43-whole-app-unlocked.md`, §14 below) and the studies-folded pass (`research/methodology/47-studies-folded.md`, §15 below). **Read this before wiring anything.** `UI-NOTES.md` still holds the harness event details. This file adds everything since then.

Binding rulings: `research/methodology/26-operator-rulings-and-alignment.md`. Sources for each item are in brackets. A bracketed `10 §…` source is `archive/2026-10-18-methodology-studies/10-ui-depth.md`; `27b` sources are in the same folder.

## 0. Ground rules for the UI session

- QMX is a **desktop application**. The browser is only the design-time host (rulings 32, 40). Never design for a web version.
- Build with **demo mode OFF**, so unwired places say "Not connected" instead of showing sample data [10 §6.17].
- **The UI is a design, not a coded product.** Its code exists only to show the design. Backend requirements come from the screens' intent (screenshots), never from the UI code or its types.
- Demo data shows the intended shape. Don't treat its specifics as the backend contract [ruling J/UI].
- Node 22 is pinned, but the machine has Node 24. `pnpm dev` hangs, so start Vite directly [10, 23].
- Treat `BACKEND-REQUIREMENTS.md` and `handoff/MINI-APPS-AND-COPILOT-CONTRACT.md` in the UI repo as history. The real door is REST + SSE (`/api/chats`, `/api/sessions/{id}/turns`, `/live`, `/api/approvals/{id}`, `/api/usage`, `/export`) [10 §6.15].

## 1. Fix before wiring the harness (QMA v2, exists today)

1. **Block renames:** `tools→tool`, `changes→changed`, `cards→entity`, `ask→question`. Add a `needs_you` renderer. Decide whether `tool` is one call or a batch [10 §6.1].
2. **Session home:** show a home badge. A session keeps its birth home. "Open in hub" must not rewrite the home, and there must be a way back to the Lab. Replace the one-way `absorb()` [10 §6.2-6.3, 23, ruling 12]. **The backend field is now designed (engine AD-35, moved by the unlock pass):** `home: {kind: general | lab | portfolio | library | app, project_id}` is sent **in the body of `POST /api/chats`** and stored on the chat at birth; there is no separate `PUT .../home` call (that design was dropped before it was built). `GET /api/chats` returns it. Child chats inherit the parent's home; a chat created with no home reads as `general`. Every screen can open and continue any session through the same session id and turn routes; "open in its home" is the way back.
3. **Chat status words** (chat turns, not runs): add `failed`, `cancelled`, `expired` [10 §6.4]. Run statuses are a different set (§9 row 8) and have no `cancelled`.
4. **Approvals:** the backend has four **decisions**: `allow_once`, `allow_always` (not offered when a QMX tool asks), `reject` (with a message) and `answers` (the reply to an AskUserQuestion). An answer returns `resolved | already_answered | expired | invalid | unknown`. There is no `reject_once` or `reject_always`, and "for this errand" doesn't exist. Add "expired, re-run from here" [`QH/routes.py:180-205`, `QH/chat.py:230-253` on hp17, 27b F11; 10 §6.5, 20b].
5. **Sub-agents:** show start, end and result only today. Live progress arrives with the harness turn events, `delegate` v2 and the router's per-agent journal rows (engine AD-53; HARNESS-REQUESTS H1, H26, H36; §12 row 1) [10 §6.6].
6. **Harness features missing in the UI:** effort control, compaction events, stop/interrupt/steer, the model-switch cost warning, a usage page, Export per session [10 §6.12, UI-NOTES]. "Compact now": H15 was granted and built in HG1 (ruling 89, PR #92), so per-chat compaction exists for Background and Child chats; wire the button only to what that backend exposes for the chat kind on screen (fixed after 41 L1) [27b F14].
7. **Terminal:** label it read-only. It is not a shell [10 §6.13].
8. **Output:** add a Markdown renderer and diagram parts in the panel catalog. These are pure UI work [10, 19].

## 2. Do NOT wire yet (no backend today)

- Lab copilot tools (`qmb.*`, `lab.*`, `pod.*`, `graph.edit_draft`, `compute.place`) [10 §6.7]. These arrive with the Lab/Pods design (section 5).
- Editor draft, publish and run against the chat host. The engine is merged but today runs in its own host (`qmx_engine.host`), which cannot share a QMX home with the chat host (`qma.serve`); wire the Workflows screens only once the one-host packet lands (engine AD-52), when chats and workflows answer on one port [10 §6.8].
- Pods bench, Portfolio pod screens, Portfolio copilot tools [10 §6.16].
- Mini-app build paths ("from widgets", "describe it") [10 §6.10].

## 3. Coming with the workflow engine (`architecture/workflow-engine/`)

- **A Workflows screen** is needed. Today workflows have no screen of their own [23 §3]. It needs a list, versions, enable/disable, triggers, and runs.
- **One draft, two views:** the Lab editor's Graph mode and Code mode are projections of ONE draft. The saved Board is a draft. Free-form note nodes and unconnected nodes are allowed in a draft [engine AD-11].
- **Lifecycle states to show:** draft → validated → tested → published (version) → enabled ⇄ disabled → archived. A draft can only run in test mode. Selected-subgraph runs ("run just this part") are allowed [engine AD-11]. Drafts never sit on `main`; see §9 for the draft vs published badge.
- **Test runs use real models**: haiku through his plan login by default; OpenRouter only to prove another provider works (ruling 105). Show each test report and its cost. Saving a draft and running a test never ask him; publishing and enabling ask once.
- **Run timeline:** one trace per run and one span per step (status, cost, time, account, model). Steps that waited at a provider's own usage limit show `waiting (resume_at)` [engine §observability].
- **Inbox items:** one per problem, with buttons: retry, stronger model, skip step, open trace, stop, resume. Long-pause alert after 6 h (editable) [engine §failure ladder]. Only provider failures and harness-level errors reach the inbox; everything else is a digest line (§9 row 9).
- **Account pool settings:** see §12 row 5 (the Accounts page). Any number of Claude, GPT and key accounts, configured per account in the UI; QMX imposes no share, ceiling or budget of its own (ruling 106). He may set an optional per-account share or ceiling himself on the Accounts page (ruling 90); it is off by default and never set by QMX. The default strategy for workflows is least-used, never fill-first. OpenRouter is marked "provider proof only" [engine AD-12, rerun].
- **Defaults are all UI-editable.** The list is in `SOLUTION-DESIGN.md` §17.
- **Copilot builder:** the copilot asks numbered questions with suggested answers, then draws the draft on the canvas.
- **Templates:** a template is a copyable workflow. A variant is an overlay with a "variant of" link (ruling 48).
- Node kinds the palette needs: trigger, script, rule, loop, join (all/any/quorum), wait, human gate, llm, agent, sub-workflow, grader, monitor, app op, library. (`claude_workflow` is retired, engine AD-5.)

- **Nothing waits for him during a run** except an irreversible outside effect, which goes to the inbox while the run waits (`waiting`) [engine AD-16, AD-17]. Publishing or enabling a workflow asks once. Self-improvement shows "challenger vs champion" with automatic rollback [engine AD-26].
- **Where it ran:** each run card shows its placement by registry name (`pc`, `contabo`, `qmb`, or a provider row such as an Amp runner or orb, E2B, Modal, or a managed agent host like Cloudroom or Amp threads), its `agent_mode` (`runner_outside | cli_inside | host_harness`), its isolation only when he chose one (`container` or a remote placement; `local` is the default and needs no badge), and the run's `mode` badge (`live | test`) [engine AD-24/25, AD-32].

## 4. Coming with the Library (`architecture/library-and-data/`)

- **One Library holds everything** (ruling 28). The kinds are data: each is a schema file with a class (record, definition or governed), so shelves are generated from the schemas and the UI never hard-codes a count. A bot's card is its preview, its logic is its code tab, a board is a workflow draft in board view, a template is a tag, and hypotheses ("Ideas") are a kind [library AD-3, §15].
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
- **One draft per subject.** Graph and Code are projections of the same draft with a round-trip check. The authoritative form depends on the kind: a workflow is JSON, bot logic is code, a pod block follows its own kind, a board is a workflow draft drawn as notes and cells [AD-2].
- **The palette is the engine's registry, filtered** to the Lab pack (`lab.*`, `qmb.*`, `ml.*`, `pod.*`, `paper.*`, `data.*`). "Run this part" is a selected-subgraph test run. The fresh/stale dots come from the engine's memo [AD-3, AD-4].
- **Backtests:** a `setup` is compiled and run through the qmb node pack. The old `run_backtest(config_ref)` door retires. The holdout is touched once per family [AD-5, AD-6].
- **ML:** model objects with versions. A slot is a port that mints a new version. The machine picker uses the engine's placement preflight [AD-7, AD-8]. Notebooks run on a KernelPort [AD-9].
- **Pods:** a versioned stack of blocks in seven slots. One simulator drives size trail, test, stress, fan, head-to-head, mix and paper [AD-10]. Pods compile to Book+BMS [AD-11]. Paper trading is an engine run on a paper ledger over live prices. Promote mints a card. Signing and activation stay as Portfolio's two clicks [AD-12].
- **The Lab copilot's 17 tools** ship as a real Claude plugin with Effects [AD-14; engine AD-55]. No grant step remains (ruling 118); adding the Lab to a running chat switches its tools on without a restart.
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
- **A mini app is a real Claude plugin** (engine AD-55): its skills, helper agents and slash commands appear in the copilot like any plugin's; adding an app to a running chat switches its tools on at once; an app installed or updated after a chat started joins that chat at its next turn ("loads on your next message"). An app's own schedules show as workflow triggers on the Workflows screen, not on the app card (engine AD-57).

## 7. Pending studies that may add items

- Workflow memory (`research/methodology/28-workflow-memory.md`): lessons and "already built" hints may surface in the UI.
- Environments and deployment (`29-environments-and-deployment.md`): where each run runs (PC or server), shown on the run card.
- Browser plan: now designed (engine AD-44; §12 rows 10-12): watch pane, lease queue, take-over, HUD. The plain-words journeys still go to him first (ruling 30).
- Phone alerts: later (ruling 34).

## 8. Notifications (ruling 77)

- Notifications are designed by the UI session. The engine only emits inbox items: provider failure, harness-level error, and the rare irreversible external step. Phone, toasts and digest are UI-side.
- MCP apps (the Model Context Protocol apps standard, interactive UI in chat as used in Claude Desktop) are a UI topic. The design discussion is tomorrow.

## 9. Machines, keys, providers, context (added 2026-10-16 night, 27c gap fixes)

Fifteen rows the UI session needs that earlier sections missed [27b §5]. Each names its backend source.

1. **Machines list in Settings** = the placement registry with live preflight states (`available → configured → authorized → reachable → healthy`), sessions in use / `max_sessions` (derived from RAM; about 4 on Contabo today), RAM in use, vault sync age, last error, and each row's `relay: local | central`. Run cards, spans and inbox items show `placement`, `agent_mode`, the run `mode` badge, `health`, `cost so far` and `link_out`. A live desktop or VM view loads only for nodes with `watch: true`, and only when he opens it. Provider dashboards are reached by the copilot, not rebuilt [engine AD-30, AD-32; SD §21, §23].
2. **Keys once:** per key `replicable`, `vault_version` and last sync; "key rotated, N relays updated"; re-pair placements; `qmx node login <placement>` for a plan sign-in on an owned machine [engine AD-28; SD §19].
3. **Providers, models and roles:** a provider row is a profile (base URL per region, auth style, key refs, usage hook, an optional terms note he writes); each **model** row carries its own wire (`anthropic | openai_chat | responses`) and capabilities (tools, vision, PDF, audio, video, thinking, cache style, window); a "Test" button sends one token; role candidate lists **per placement** (`pc`, `contabo`, burst rows), generated from his providers until he edits them, third-party models first; OpenRouter marked "provider proof only" [engine AD-13, AD-39; SD §26.2].
4. **Provider onboarding:** "Add a provider" starts the copilot flow that reads the provider's own published instructions and drafts a placement row; he applies it with one click and types any key once; a smoke test result card follows [engine AD-30, ruling 74; SD §21].
5. **Cua scope and manifest editor** on an agent node (apps, origins, profile `isolated | logged_in`, expiry); screenshots in the trace; his demo-account list (locked, only he edits it) and the always-deny origins (banks, payment, exchanges, mail) shown read-only [engine AD-33, AD-44; SD §24].
6. **Self-improvement:** per workflow `self_improve auto | propose_only | off`; a champion vs published badge; a "rolled back automatically" line [engine AD-26].
7. **Agent-made tools:** `unreviewed` / `reviewed` with a review action [library AD-3].
8. **Run vocabulary:** one status set for every run, `queued | running | waiting | passed | failed | stopped | interrupted` (with a reason on `waiting`, `failed` and `stopped`), plus a separate `mode` badge `live | test`. "Tested" = a passed run in either mode [engine SD §3.1, library AD-15].
9. **Inbox severities:** `info` (daily digest), `normal`, `urgent`, `black` (repeats until acknowledged). Only provider failures, harness or ledger errors and unknown outcomes on irreversible external steps reach `normal` and above (ruling 77; the stolen-pass alarm is retired, rulings 115-117). Actions `retry | stronger model | skip node | open trace | stop | resume` [engine AD-17; SD §10.4].
10. **Chunk progress** on fan-out nodes (chunk n of m, cache hits per chunk), a **tool-call sub-timeline** under each agent span, and `compacted` markers on the span [engine AD-34].
11. **Draft vs published** on every workflow, mini-app and pod card; run-made workflows, apps, pods and skills arrive as drafts waiting for his one yes; triggers show the exact version they pin and whether they follow the champion [engine AD-10, AD-11; library AD-7, AD-18].
12. **QMB machine** as a placement with its own queue depth [engine AD-31].
13. **Lab paper** as a daily schedule: Day n of m, pause = disable the daily trigger [Lab AD-12].
14. **Library home indicator:** off. The UI never shows which store answered, but shows `primary_moving` during a cut-over [library LLD §7].
15. **No QMX limits (rewritten 2026-10-18, ruling 106):** Settings has no QMX-imposed budget, cap, share, turn, token, tool-call or wall-time setting, and no runaway guard. The only exceptions are ones he chooses himself, off by default: an optional per-account share or ceiling (row 5), and a per-workflow `limits` block he writes (engine AD-40). The $5 per Background chat and the 0.5 background share are bugs being removed, not settings to show. `max_live_chats` shows as machine capacity (derived from RAM), not a limit: extra work queues or spills, it is never refused. The only limits shown are the providers' own, as readings. Stuck and loop stops show as `stalled` with the reason. No spend ask and no QMX limit bar exist anywhere [engine AD-9, AD-16, AD-40; SD §26.3].

## 10. Operations patterns from Hermes (added 2026-10-18, study 37c)

Patterns from Hermes Agent's TUI, desktop app and dashboard that make many runs and agents readable. Sources in `research/methodology/37c-hermes-operations.md`.

1. **Live work dock** above the copilot composer: running sub-agents and workflow runs started from this chat, with name, elapsed time and latest activity; expand to a roster. Steer and Stop where the backend allows. Steer says "queued for the next checkpoint", not "read". Sub-agents still show start, end and result only until the harness emits progress (§1 item 5) [37c §12].
2. **Queued messages panel:** a message typed while the agent works shows as `queued` and can be cancelled before it starts [37c §12; harness queue].
3. **Context meter with breakdown:** % full, and a popover by category (system text, tools, skills, memory snapshot, MCP, conversation). Optional cache hit rate and tokens per second, off by default [37c §12; harness usage].
4. **Failure card names the layer:** provider, key, relay, stream, harness, engine, disk. Actions match the layer: Retry (hidden when it would fail the same way), **Retry when the limit resets at HH:mm** with a countdown and Cancel (nothing retries after he closes the window), Switch model [37c §12; error class set, 37c §7] *(new backend: closed error classes)*.
5. **"Why didn't it fire?" panel** on each trigger: ticker heartbeat age, version enabled, next fire, last 10 fires with status and reason (`silent`, `merged`, `blocked config`, `held until HH:mm`, `skipped`), open incident. The copilot answers the same question from the same read [37c §4] *(new backend: `service.explain_trigger`)*.
6. **Trigger list columns:** name, schedule in words plus the cron text, state badge, delivery, last fire (status + delivery outcome), next fire, Run now. "Passed" and "delivered" are separate badges [37c §1] *(new backend: delivery field)*.
7. **Incidents, not repeats:** one row per trigger and error signature with a count and first/last seen; Acknowledge keeps it quiet until the error changes; a passing run marks it resolved [37c §1] *(new backend: trigger incidents)*.
8. **Engine health badge** in the status bar and on the Machines list: Running, Degraded (with reason), Heartbeat stale ("looks running but nothing is scheduled"), Old code ("restart to load the update"), Safe mode (after a restart loop) [37c §1, §7] *(new backend: heartbeat row, code stamp)*.
9. **Resource banner:** only the most severe active warning (disk critical > memory critical > unexpected restart > disk low > memory low); dismissal lasts until the next engine boot [37c §7].
10. **"Last run" diff scope:** for a workflow or copilot that changed files or Library items, a view of exactly what its latest run or turn changed [37c §12; Library run branch].
11. **Pop-out a run or chat** into its own window without the sidebar, for a second monitor; live output streams into every window showing it [37c §12].
12. **Simple mode:** a chat-first layout switch that hides the status bar, rails and terminal; it changes what is shown, not what QMX can do [37c §12].
13. **Approvals:** keep the four decisions (§1 item 4). Add a visible badge whenever any auto-approve mode is on for a session, in the status bar and on session start [37c §12].
14. **Machines list:** each machine has a device name; the same agent or workflow on two machines shows as `name@machine` [37c §12].
15. **Settings, persona:** one short text box for the copilots' tone and defaults, with the "which file does what" help card beside it [37c §13] *(new backend: persona item)*.
16. **Logs page:** filter by component (engine, scheduler, relay, harness, apps) and level, live tail; analytics by day and by model (tokens, cache hit, cost estimate) [37c §12].
17. **Phone (later, ruling 34):** inbox actions as buttons with a timeout and a numbered-text fallback; one status message edited in place per run [37c §10].

## 11. Desktop patterns from Hermes, second pass (added 2026-10-18, study 37d)

Sources in `research/methodology/37d-hermes-full-pass.md`. Rows marked *(new backend)* need a proposal from 37d.

1. **Widgets inside chat messages.** The model writes a directive paragraph such as `::chart{id="run-123"}`; a registered component renders it inline; an unknown directive shows as plain text; a crash shows an error chip, never a dead message [37d H-83] *(new backend: a directive registry the copilot is told about through a skill)*.
2. **Live previews that talk back.** `::preview{file="…"}` renders an HTML explainer in a sandboxed frame with QMX theme tokens. A button inside can send a short hidden prompt back to the copilot (short text, at most one per second, typed result; an injection guard, not a usage limit). This is the home for animated explainers (ruling 7) [37d H-84].
3. **HUD mode.** A floating, always-on-top chat bar over any app; where it sits is context ("what is this?" means the window below). Read only over broker windows [37d §4.12] *(new backend: `read_window_below` tool)*.
4. **Loop, goal and heartbeat cards** above the composer: "Loop active · 2 runs · next 00:04:12", goal "3 checks so far" (no turn budget exists, engine AD-47; fixed after 41 L2), heartbeat interval; a goal paused as `blocked` or `stalled (no convergence)` shows why; pause, resume, stop [37d H-67 to H-69] *(new backend)*.
5. **Processes block in the live dock** under sub-agents: command, elapsed, last output line; flips to exit status, leaves after about 60 s [37d H-07].
6. **Sub-agent steering:** Steer says "queued for the next checkpoint"; a result that missed the steer shows "steer did not land" [37d H-03] *(new backend: delegate v2)*.
7. **Queued messages and "Turn lost during restart"** with a single Discard; the queue lives on the backend so every window sees it [`D:user-guide/desktop` "Composer history and queue editing"].
8. **Model picker in the composer** with an effort pill that shows what is sent (`Ultra→Max`), favorites, and a confirm dialog when a switch is risky (large cached context, expensive model). Mid-chat switches warn that the cache resets [37d H-40].
9. **Auxiliary-model warning** when side roles (titler, compactor, describer) sit on another provider than the main model [37d H-17].
10. **Bots roster** (organogram): each named agent with avatar, title, persistent chat, routines, model pin, skills and tools; group rooms with @mentions; "Create on" a chosen machine; `name@machine` handles [37d H-106].
11. **Agent screen with Take over / Hand back** for an agent's own desktop or browser at a login or 2FA step; the agent's tool results are void while he holds control [37d H-96].
12. **Comment mode on a preview:** click elements on a live page, leave numbered pins, send them as one grouped message with cropped screenshots [`D:user-guide/desktop` "Comment mode"].
13. **Artifacts gallery:** every image, file and link sessions produced, searchable, with a jump back to the producing chat [`D:user-guide/desktop` "Artifacts"].
14. **Interface modes:** Simple (chat-first) and Advanced, each remembering its own layout [37c row 12, extended].
15. **"Applies to" chips** on Settings pages when several agent homes exist, so an edit lands on the chosen one [`D:user-guide/desktop` "Per-profile settings"].
16. **Quick Entry:** a global hotkey composer from anywhere [`D:user-guide/desktop` "Quick Entry"].
17. **Conversation timeline rail** and reading-position memory per chat [`D:user-guide/desktop` "Chat"].
18. **Restored unsent message** strip when a draft's chat disappeared [`D:user-guide/desktop` "Chat"].
19. **Suggestions list:** proposed automations from templates, usage and newly connected accounts; Accept opens the enable card; Dismiss latches [37d H-71].
20. **Template fill-in:** pick a template, answer its slots one at a time (or as a form), confirm before anything is scheduled [37d H-70].
21. **Rules page:** "always allow" and "never allow" lists with their source (you, imported, suggested); the guard's floor shown read-only (sign-ins and keys, QMX's own databases, destructive commands; engine AD-54) [37d §4.2].
22. **Passwords & Logins page** for site logins the browser agent may fill; never cards [37d H-55].
23. **Multimodal attach:** drop images, PDFs, audio and video into the composer; audio and video show "transcribing" or "analysing" chips before the turn sends [37d §4.9] *(new backend)*.
24. **Keep computer awake while working** setting [37d H-74].
25. **Memory Graph:** skills and memories over time, filter All / Used / Learned, edit or archive a node [37d H-80].

**User journeys for the UI session (from study 37d §5):** (1) ask about what I see through the HUD over TradingView; (2) hand a job to helpers on Kimi and DeepSeek from an Opus copilot and steer one; (3) keep an eye on the overnight Lab loop with a heartbeat; (4) turn a good chat into a template and accept a suggested schedule; (5) an agent hits a 2FA page, he takes over and hands back; (6) meet the team in the Bots roster and @mention the Researcher; (7) drop a podcast clip and a PDF into the composer and send when both are ready.

## 12. The rerun pass (added 2026-10-18 evening, `research/methodology/39-architecture-rerun.md`)

Backend decisions from the rerun that change or add screens. Engine AD numbers in brackets. Nothing here is built yet; build with demo mode off, so these places say "Not connected" until their packets ship.

1. **Helpers on other models, visible.** The copilot (Opus on his plan) can run full helper chats on Kimi, Qwen, DeepSeek, GLM or MiniMax through `delegate` v2, and, only if the build-gate probes pass (P0, P1, P4, P2; review 41), native sub-agents on those models in the same chat. Design for both; under his Opus copilot the native kind may never ship, while a Kimi- or GPT-main copilot gets native helpers on other providers whatever that probe shows (42 N7). The live dock shows each helper with its provider and model, elapsed time, last activity, Steer ("queued for the next checkpoint") and Stop; results land between turns as a summary card with a link to the helper's transcript [AD-38, AD-41].
2. **Per-account switch "native helpers on other providers"** on each Claude account in Settings (the plan lane): shown only if the plan lane ships (it does not if probe P1 fails); on once its checks pass; off means helpers on other providers run only as full helper chats; it can flip off by itself when the router stops answering or overage use appears, with one line saying why. One plain line explains it; it is not an approval [AD-38].
3. **Model picker** lists models from the registry with capability chips (tools, vision, audio, video, thinking, window, cache) and the effort sent; a model that lacks something the chat needs is shown greyed with the reason [AD-39, AD-13].
4. **Add a provider:** a profile row (or the copilot's onboarding flow) plus "Test"; MiniMax, Qwen, OpenCode, Ollama Cloud and the rest are rows, not features [AD-39, AD-30].
5. **Accounts page (per-account provider configuration, CLIProxyAPI-like in capability, built in-house, ruling 99):** any number of Claude, GPT and key accounts across providers; per account: enabled or not, priority, "my copilot account" (workflows use it last), routing strategy (least-used by default, round-robin, fill-first, reset-window, random), which models and roles it serves, plan lane switch (row 2), an optional share or ceiling he sets himself (off by default; ruling 90), the provider's own usage reading, cooldown with its reset time, and "sign in again" when benched (a benched plan account never moves his copilot by itself; the chat waits for his sign-in); with one Claude account, the share of its window that test runs and builder tests used, as a reading; each GPT account shows its owner machine; a key used on two machines shows both [AD-12; 41 H2, H7, M6].
6. **No QMX limits anywhere.** No limit bar, no runaway guard, no spend ask. Run cards show estimates and the providers' own readings. A stop by the stuck detector reads `stalled` (no progress) or `stalled (loop)` with the agent's last summary [AD-16, AD-40].
7. **Failure cards name the error class** (rate limit, plan quota, billing, sign-in, model not allowed, context too long, provider down) with actions that fit: wait for reset (time shown), switch account, next model [AD-40].
8. **Attach anything:** images, PDFs, audio, video, files and `@file`, `@folder`, `@url`; chips show "transcribing", "analysing video", "reading" before the turn sends; the attachments land in the Library [AD-42].
9. **Rules page:** always-allow and never-allow lists with each row's source (you, imported from Claude Code, suggested); the guard's floor shown read-only (it replaced the money gate, AD-54); locked money and risk keys show a lock and need his unlock [AD-43].
10. **Browser and take-over:** the copilot can browse with a QMX Browser profile (`isolated`, or `logged_in` from a snapshot of his real profile that carries only the sites he ticked; banks, payment, crypto exchanges and mail can never be ticked; "close your browser to refresh" when Windows needs it) [41 H8]. Any agent browser or desktop can be watched live; Take over / Hand back; while he holds control the agent waits. A Passwords & Logins page for site logins only (never cards, never broker logins) [AD-44].
11. **HUD:** a floating always-on-top chat bar over any app; "what is this?" reads the window underneath; read-only, broker windows included [AD-44].
12. **MT5 and cTrader on demo:** a Settings list of his demo accounts (login, server, broker) that only he edits (locked); an agent node's desktop manifest names one listed account; cTrader shows "needs a Windows desktop machine" when none exists; live accounts are never offered [AD-33, AD-44]. The five-layer proof indicators ("account proven: demo", the 60-second check, "algo trading off, EA detached") are retired (rulings 115-117); do not build them.
13. **Widgets and explainers in chat:** transcript directives render inline components; `::preview` renders an interactive explainer in a sandboxed frame whose buttons can talk back; unknown directives show as text; a broken widget shows an error chip; file paths in replies become artifact chips [AD-45].
14. **Templates read plainly and fill in:** template titles say what they do (proposed renames in SOLUTION-DESIGN §26.9); "use this template" asks its slots one at a time or as a form; a Suggestions list offers schedules (never auto-created); skills and templates show stale or archived states from the curator [AD-46].
15. **Loops on a chat:** heartbeat, loop and goal cards above the composer (interval or self-paced, ticks so far, goal checks), with pause, resume and stop [AD-47].
16. **Desktop app chrome:** startup card with stages, safe-mode banner after a crash loop, "Docker is starting" line, keep-awake and start-at-login settings, pop-out windows, HUD window, Quick Entry hotkey. Never a web site [AD-48].
17. **Combined sessions:** adding a pack (Lab, Portfolio, a workflow, a mini app) to a running chat shows "tools added" without restarting; if the next turn is needed, it says so [AD-35].
18. **Worktrees:** a helper that edits a folder shows its branch and "changes ready to merge"; a collision shows a reconcile card or a merge-conflict view [AD-49].
19. **Library check for the UI session:** he said the demo Library shows units, artifacts, bots, bot cards, relationships and logic; the study found no such shelves on `ui-review/repair` at `eea09941`. The backend roster has all of them (Library AD-3, AD-4). Please check which build he looks at and align the shelves to the roster [alignment B-79].
20. **One Logs and Analytics view** for the copilot and workflows together: filter by component (router, harness, engine, scheduler, apps), level, day and model; tokens, cache hits, cost estimate per day and model; every copilot sub-agent appears as its own row [AD-15].
21. **Stuck stops say which kind** (review 41): `stalled` (no progress), `stalled (loop)` and `stalled (no convergence)` with the agent's last summary; a slow model shows "waiting on model, first token" and is never called stuck [AD-16].
22. **Helpers that run outside CLIs** (`delegate` target `cli`: at first only CLIs that take an Anthropic base URL, such as OpenCode; Codex CLI waits for a later router front door, 42 N17) run on his PC as an ordinary program by default (a container or his server only when he chose one for that helper role, then shown as such); the first use of each CLI version asks him [AD-41; retirement pass].
23. **Router and pool usage view** (one page, with the Logs and Analytics view of row 20): per account and per provider the provider's own readings (plan 5-hour and 7-day windows as percent with reset times, key providers in USD or tokens as the provider reports them), which lane each request took (plan, GPT, key, chat), live leases per account and machine, cooldowns with reset times and the error class that caused them, and which helper or workflow used what. Readings only: no QMX bar, share or ceiling is drawn on them. OpenRouter rows say "provider proof only" [AD-12, AD-15, AD-38; H36 journal fields].
24. **Defaults read key-first** (ruling 107): model pickers, role lists and "Add a provider" put Kimi, Qwen, GLM, DeepSeek, MiniMax and the other key providers first, then GPT, then the Claude plan; nothing in the UI suggests Claude as the default [AD-13].

## 13. Rerun UI landings: where each one lives (re-centralized 2026-10-18 evening)

A checklist so the UI session finds every UI landing of the rerun (39, with 41 and 42 applied) in one place. Sources: 37c's UI block is §10, 37d's UI block is §11 with its seven journeys, the rerun is §12.

| Landing | Row |
|---|---|
| Widgets inside chat messages | §11 row 1; §12 row 13 |
| Live previews whose buttons send prompts back to the copilot | §11 row 2; §12 row 13 |
| HUD mode (floating chat bar, read-only over any window) | §11 row 3; §12 row 11 |
| Agent desktops and browsers with Take over / Hand back | §11 row 11; §12 row 10 |
| Shared browser he can watch live (ruling 20), logged-in profile by snapshot | §12 row 10; §7 |
| Per-account provider configuration, CLIProxyAPI-like in capability | §12 rows 2, 4, 5; §9 row 3 |
| Router and pool usage view | §12 row 23 |
| One monitoring view for copilot and workflows | §12 row 20; §10 row 16 |
| MT5 and cTrader on demo (his locked demo-account list; cTrader "needs a Windows desktop machine"; the five-layer proof indicators are retired) | §12 row 12 |
| The unlock pass (one host, agents that write, the guard, packs as plugins, one run list, capacity, sessions in the Library) | §14 |
| Helpers on other models in the live dock, steer and stop | §10 row 1; §11 rows 5-6; §12 row 1 |
| Desktop app chrome (startup card, safe mode, pop-outs, Quick Entry, keep awake) | §11 rows 14, 16, 24; §12 row 16 |
| Multimodal attach (images, PDFs, audio, video) | §11 row 23; §12 row 8 |
| No caps anywhere | §9 row 15; §12 row 6 |

## 14. The unlock pass (added 2026-10-18, ruling 118, `research/methodology/43-whole-app-unlocked.md`)

Backend decisions that change what the UI can wire or must show. Engine AD numbers in brackets. Nothing here is built yet; demo mode off.

1. **One backend process.** Chats, workflows, the Library and apps answer on one port from one process (`qmx_host`). The UI never starts or chooses between hosts; the desktop shell starts that one process and shows its startup card [AD-52, AD-48].
2. **Agent steps that write.** An agent step in a workflow can now create and edit files inside its own private folder. The run card shows "files changed" per step and which of them the step kept (only declared outputs are kept); a denied file write shows as a one-line "not allowed: outside its folder" in the step's tool timeline, not as a failure; a shell command the step was allowed to run can still write elsewhere on the PC, as in Claude Code, and only declared outputs are kept (review 48) [AD-60, AD-51].
3. **Rules page shows the guard, not a money gate.** The read-only floor lists: sign-ins and keys, QMX's own databases and settings, his personal Claude folder, destructive commands (recursive delete, disk and registry tools), network paths to unknown machines, a key inside a command. His always-allow and never-allow lists sit below it; the floor cannot be lifted by his always-allow list [AD-54].
4. **Settings and Doctor drop money items.** No "money posture", no "exposure probe" button, no broker scope proofs. Order proposals (if the Portfolio offers them) still always ask [AD-54].
5. **Apps are plugins.** An app's skills, helper agents and slash commands show in the copilot like any Claude plugin's; adding an app to a chat turns its tools on at once, and its skills, helper agents and slash commands join on the next message ("tools now, skills on your next message"); an app installed or updated mid-chat joins the same way (review 48). An app card shows its health, logs and incidents; its schedules live on the Workflows screen [AD-55, AD-57, AD-19].
6. **One run list.** "Remote runs", "Jobs" and "Workflow runs" are one list: every unit of work is a workflow run (a placed GPU job is a one-step workflow). Remove any separate Remote runs or Jobs screen; the run card's placement badge says where it ran [AD-57].
7. **Capacity, not limits.** The Machines list may show capacity per machine as three readings: CPU slots, chat slots (with "kept free for you" = the reserve), container slots, each with "in use". Work past capacity shows `queued`, never failed. These are machine readings, not QMX limits [AD-58].
8. **Turn states for queued work.** A Background or helper turn that waits for a free chat slot shows `queued`, then `running`; "waiting on model, first token" stays as it is [AD-53, AD-16].
9. **Sessions in the Library.** Every chat appears in the Library as a `session` item (title, home badge, models used, last turn, linked items it produced); opening it opens the chat. Search finds past sessions by their text [Library AD-21].
10. **Hooks per workflow.** A workflow's settings page may hold his Claude Code hooks for that workflow's agent steps (the same editor as the global `[claude] hooks` in Settings, scoped to one workflow) [AD-53].
11. **Faster one-shot AI steps.** One-shot AI steps on Kimi, DeepSeek, GPT and the other key providers no longer start a Claude Code program; their span shows "direct call" instead of a chat link. Steps on the Claude plan still show their chat [AD-56, AD-13].

## 15. The studies-folded pass (added 2026-10-18, `research/methodology/47-studies-folded.md`)

Backend decisions from studies 44, 45 and 46 that change what the UI shows or wires. Engine AD numbers unless marked Library or Lab. Nothing here is built yet; demo mode off.

1. **Tools come in sets.** A chat shows which tool sets it has ("Library", "Lab", "this app", "browser"), and adding an app or the Lab to a chat turns its set on at once; the app's skills and helpers join on the next message (review 48). The Settings page for a home lists its default sets (editable, the Lego rule). Never show "82 tools" [AD-61, AD-35].
2. **"What did it see".** A session and every agent step offer a "what it saw" view: tool sets, skills, instruction slots and the fingerprint (surface digest). Two runs with different fingerprints say so [AD-62, AD-15].
3. **@ references in the composer.** Typing `@` offers pods, units, bots, runs and their outputs, an app's latest result, Library search, a file, a folder, a website, a YouTube video or playlist, a past session, a memory question. Each attached item is a chip with: pinned version or "follows latest", and a state (`ready`, `pending` while a video or playlist is processed, `archived`, `not cached` while offline). A pinned item whose newer version exists says so. The chips stay when the session is opened from another screen [AD-63].
4. **Memory view.** Memories show what they are about (pod, workflow, app), where they came from (a chat or a run), the period and market regime they hold for, and a "Forget" action that hides one from every recall and keeps it restorable. Settings show which memory engine runs (Hindsight) and where (PC or server) as readings [AD-18, ruling 119].
5. **Marks on items.** An item built on a bad input shows one badge in plain words ("built on quarantined data", "newer input exists", "input corrected") and one click shows the path. "Mark as bad data" (quarantine) is his action on an item, with a reason; clearing it clears every badge. Schedules that use a quarantined item show "paused: input quarantined" [Library AD-22].
6. **An "Ideas" shelf.** Hypotheses are Library items; each shows supported, refuted, open or mixed (by market regime), the tests behind it, the family's trial count, and the source with a link to the exact minute, page or line [Library AD-23, AD-4].
7. **Publish card additions.** The publish or enable card of a workflow or app lists the "ask first" actions its tool sets contain that will run without asking once he publishes (standing grants), and, for a persona, a methodology, a skill or a change of the copilot's default model, the eval battery's result (pass rate over three tries per task, what changed) [AD-4, AD-66, AD-22].
8. **Trigger card.** Priority (normal or high); an optional "ready by" time with "start by" computed from the last ten runs; "skipped: market closed" for the market-open check; webhook and event triggers show where they live (server by default) [AD-10].
9. **Pause everything.** One global button pauses all autonomous work on every machine; running steps finish their current step; chats keep working; "Resume" runs one catch-up per schedule. Show the paused state everywhere runs are listed [AD-10, AD-65].
10. **Steer a run.** A run card offers "rerun from here" on a step, with only the overrides allowed for a published workflow (models per role, declared inputs); any other change opens the draft. "Compare with…" shows a step-by-step diff of two runs [AD-7, AD-15].
11. **Mini-app cards.** An app card lists its actions (operations), "feeds from" and "feeds to" (from links), each output's freshness ("stale since…"), its setups (profiles: one per currency pair, say), where its saved state lives (PC or server) with "move", and its incidents by class (grant, workflow, view, dependency, host). The app's schedule shows on the Workflows screen [AD-64, AD-65, AD-19].
12. **Machines and ops.** The Machines list adds per host: QMX version ("needs update" when behind), live claims (work in progress that others will wait for), CPU, memory and machine minutes, and GPU slots where there are GPUs. "Bring this run home" on a remote run replays it on the PC [AD-65, AD-58].
13. **Library search answers** name why each item was included ("used in", "produced by", "same family") and may say "not enough evidence" instead of answering; an "as of" date picker shows the Library as it was [Library AD-8, AD-9].
14. **Lab results on drafts are real.** Running a published procedure (backtest, sweep and the rest) on a draft bot gives real, citable results tied to that exact version; only an edited procedure runs as a test. Cell outputs and model-written numbers are labelled "exploration"; a filtered view of an existing result is labelled "view, not a new run" [Lab AD-4, AD-8].
15. **Boards are workflow drafts.** The board view is a workflow draft drawn as notes and cells; publishing it (after deleting the notes) makes it a workflow. There is no separate Board kind [Lab AD-2].
16. **Fork a chat.** "Try both" forks a session into two with the same home, apps and attached items; a compare view follows [AD-35].
17. **Purge a secret** (operator only): on an item holding a pasted key, "Remove secret permanently" replaces it everywhere, with a confirmation; it is the only delete in QMX [Library AD-6].
18. **Answers with confidence.** Explainers show a confidence chip per claim (checked, recalled, inferred; high, medium, low); numbers are drawn from stored results and an unmatched number shows "unverified"; open questions show the spread of several models instead of one answer [AD-45].

## 16. Review 48 (added 2026-10-18, `research/methodology/48-review-unlocked-and-folded.md`)

Backend decisions from the review fix round that change what the UI shows or wires. Engine AD numbers unless marked Library. Nothing here is built yet; demo mode off.

1. **Server work shows on the PC.** Runs, inbox items and incidents of work homed on the server appear in the PC's run lists, inbox and copilot with a "server" badge; answering an item on the PC acts on the server; when the server cannot be reached its rows read "server unreachable since …" with the last values seen [AD-65, AD-21].
2. **"Continue on this machine".** A run card whose home machine is gone offers it; it is refused, with the reason, while that machine still answers [AD-7].
3. **"Pause state unknown".** The doctor page shows it on a machine that has not heard from the server for three heartbeats [AD-10].
4. **Steer with an edit.** After he publishes an edited workflow, a running run's card offers "rerun from here with the new version" [AD-7].
5. **Deletes in a chat's own folder ask.** In an Interactive chat a recursive delete inside its folder becomes an ask card instead of a refusal [AD-54].
6. **Attached folders copy nothing.** A folder chip says "N files, read when needed" [AD-63].
7. **Library main copy.** Settings show the Library's main copy on the server from the Contabo setup on, and the PC's copy and its sync lag as readings [Library AD-19].
8. **Eval battery card** names the model it ran on and the baseline it was compared with [AD-66].
9. **"What it saw"** shows one fingerprint per launch of a chat (start or reopen), so a reopened chat whose instructions changed shows two [AD-62].

## 17. The data round (added 2026-10-22, `research/methodology/55-data-round-architecture.md`)

Backend decisions that change what the UI shows or wires. These are landings, not screen designs: the UI session decides the screens, and may fold an item into an existing view where a badge or a line is enough. Library AD numbers are marked; the rest are engine ADs. Nothing here is built yet; demo mode off.

1. **A card and a full page for every Library item** (his "FIFA card"). Every kind gives a small card (at most five facts, a thumbnail, a badge) and a full page (tabs), from one read that also carries the computed header: marks with their path, freshness, where the bytes are and their size, who made it, how it landed. The card appears wherever an item is one among many (lists, shelves, search answers, chat chips, hover, "used in", the landed feed, the Lab explorer); the page appears when he opens one. The per-kind table (what each card and page shows) is 55 §3. An archived item's card is greyed with the reason; a fact that cannot be computed says so instead of showing a stale number [Library AD-33, AD-17].
2. **Data shelf: one card per price series.** Each card shows source, instrument, kind (ticks, one-minute bars, trades, order book, calendar, fills), the months covered with "complete up to", and a quality grade; its page shows a month-by-month coverage strip, partitions with where each lives (server, bucket, this PC), quality (gaps, spikes, drift against his broker's prices), a sample through the door, and what used it. Sealed months show as sealed; a sample never shows them. The current month shows as "open, updated daily"; a past month with missing hours shows as "incomplete" with its gaps listed and a button to accept them (his click), and it stays incomplete until filled or accepted. Bid and ask are two cards, not one [Library AD-25, AD-28; edge-case review 57].
3. **Hand QMX a file.** Drop any file or folder on a chat, the Library or the Lab: a progress line that resumes after a cut, the item appears at once, then "reading…" while its text is pulled out; books and PDFs open at page anchors, recordings at minute anchors; the same file twice says "already in your Library" and opens it. Screen captures from agent sessions appear as sources linked to the run or chat that made them [Library AD-27].
4. **Feeds.** A Feeds list: each feed's source, how often it runs, last run, new items since he last looked, and any incident. "Add a feed" takes a web address or a sentence ("watch this blog weekly"); the copilot drafts it and he publishes it with one yes. A feed's items land in its own collection in the Library. The economic calendar and news are feeds too [AD-68].
5. **Data health view (the internal layer).** One view: each card's freshness and quality, each downloader's and feed's last run and incident, each connection's state, free disk on the PC and the server, the age of the bucket copy. The morning brief can carry its one-line summary. A failed download or a stale card is an incident like any other [AD-69, AD-65].
6. **The Library's own health.** Settings and the doctor show the Library's main copy on the server, this PC's sync lag, and "N saves waiting for the server" while the server cannot be reached; a save made offline says "saved on this PC, it reaches the server when it is back" and shows in lists and search with "waiting for the server"; a replay of his own save never shows as a conflict, and only a real clash with someone else's change does; when the PC and server run different QMX versions, the message is "the server needs updating" and saves wait; a PC restored from an old backup shows "this PC is behind the server" rather than taking over [Library AD-26, AD-19, AD-14; edge-case review 57].
7. **Deep monitoring (the external layer).** Settings, Monitoring: the server collector's state and what it dropped, a link out to OpenObserve on the server, and the outside-agent tokens he creates, sees and revokes (each with an expiry and "read only"); the runbook skill can be exported for an outside Claude Code. When an outside agent leaves a diagnosis, the inbox shows "an outside agent left a diagnosis" with a link to its note [AD-69].
8. **Connections and broker accounts.** Settings, Connections: one list of brokers, trading platforms and data providers. Each row shows a state chip in the same five words as Machines (available, configured, authorized, reachable, healthy) for setup, and a running reading (ok, slowed, maintenance, needs you, down) where "needs you" is an inbox task, not an error, and only "down" is an incident, its accounts with balance and equity read when opened, token expiry, the last test with each check's verdict, what it can provide, which feeds and workflows use it, and where it runs (MT5 only on this PC). "Add a connection": pick the provider, enter the key in the operating system's secure prompt or sign in on cTrader's own page that QMX opens, choose read-only or trading, see the test run, then label and enable the accounts it found. Keys are never shown. Portfolio reads the same accounts. Each connection names the one machine it lives on ("lives on: server"). A key that can trade a live account is never stored on this PC: if he adds one, the row says "this key can trade live money; it belongs on a trading server" and offers a read-only sign-in instead. Later, an account traded by a trading server shows "on trading server X", its key entered on that server [AD-67; ruling 135].
9. **History and who changed what.** Every item's page has a History tab (each version, who made it, when, from which chat or run) and, for text, a Blame view (who last changed each line). Conflicts have a list and a Resolve view showing both sides with the base; a merge preview says in plain words what each side changed ("agent B changed the stop rule") [Library AD-30].
10. **The Lab workspace.** "New…" offers four levels (quick idea, experiment, study, campaign) and makes a project; the Lab reopens where he left it; a run's inputs can pick any earlier run, result or Library search ("Tuesday's sweep"); a Data panel shows a card, a sample and its quality; a training run on this PC says before it starts how much disk it needs and how much is free. The pod screens stay on demo data: pods are not in this backend [Lab AD-19, AD-20].
11. **Trade journals.** One journal per account (backtest, paper, demo, live), a card per trade (instrument, side, R, holding time), and his tags and notes on a trade, which never make a new version [Library AD-31].
12. **Sealed months, in plain words.** When a copilot answer, a Lab run or a sample asks for sealed months, the UI shows "these months are sealed for the final test" instead of an empty chart; the one final look shows as a recorded event on the family; the sealed boundary moves only when he clicks to move it, and the dialog lists any months that already had a final look [Library AD-28; edge-case review 57].
13. **Where the bytes are.** A storage view per machine and the bucket: what takes space, the PC cache size (set from real free space), and, once two checked copies exist, the action that frees the old 10 GB on his C: drive (his click). Until the cloud bucket exists it says "one copy off this PC". When a disk runs low it says what gave way first (the price cache, then other re-fetchable data), and a save that cannot fit is refused with a plain message, never half-written [Library AD-10, AD-25; edge-case review 57].
14. **Names he reads.** "Library server" (never "hub"), "worker" for machines that run workflow steps, "trading server" for where admitted bots trade; "node" only for a step in a workflow graph [file 54 default 8].
