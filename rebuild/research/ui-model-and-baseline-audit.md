# QMX: the UI's mental model + Aurelius's baseline audit (read-only analysis, 2026-10-07)

Abbreviations: `S4C` = `C:\Users\Mubarak\Desktop\QMX-session-for-Codex\`; `WT` = `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\`; `SP` = this scratchpad; `SHOTS` = `C:\Users\Mubarak\Desktop\QMX\workroom\ui-review-2026-10-01\`.
I did not unzip the 141 MB transcript; the summaries answered every question.

---

# PART 1 — The UI's mental model (Claude UI session, 2026-10-01 to 10-04)

## 1.1 Where it stands

- Branch `ui-review/repair`, HEAD `1cc66208` (2026-10-04 17:02, "Apps: mini apps on their road to live…"). The tree is clean and nothing has been pushed. Only `apps/qmx-ui` was changed.
  - `S4C\session-summary.md` was written at HEAD `56036fcc`. Five later commits landed after it: 8ef175ad fixes, 6a50bc28 pod cards, 97fc78fa doc reconcile, and 1cc66208 Mini apps pass 1.
  - So two things in that summary are now out of date. "Mini apps not started" is no longer true, and the stale backlog it complains about was reconciled in 97fc78fa.
- **Everything is demo.**
  - `workbench.demoMode` defaults to `true` (`WT\src\lib\workbench\workbench.svelte.ts:287`).
  - No transport is bound. There is no WebSocket, EventSource or recording client in src; the only `fetch` reads the local demo article JSON.
  - Every screen has a "Demo …" banner, and the status bar reads "Not connected to daemon · daemon wiring pending".
- **The operator has reviewed nothing built on 10-04:** Home (7fa36fb5), the Copilot "desk" (6b4d247a), Settings (56036fcc + 8ef175ad) and Apps (1cc66208).
  - Home and the desk skipped his ruled method (study, 2-3 options, he picks, build, click-through). They were built in about 6 and 10 minutes (`WT\UI-LEDGER.md`, "2026-10-04, later").
- **What he signed off:**
  - Lab: "outdone yourself"; Pods bench "loving it".
  - Portfolio: "bloody brilliant".
  - Library: "good to go".
- 191 Svelte files. The handoff docs in `WT\handoff\` are byte-identical to `S4C\handoff\` (diff -q was clean).

## 1.2 Rail and screens (`WT\src\lib\workbench\destinations.ts`)

Rail order: Home(1) · Copilot(2) · Library(3) · Lab(4) · Portfolio(5) · Apps(6) · Settings(,) at the rail foot.
Old routes are 13-line redirects:
- `/authoring` → Lab
- `/trade` → Portfolio Live
- `/apps/demo-ml` → Lab Train
- `/apps/demo-lab`

`/gallery` is the component catalog page, reached from Settings › Developer.

| Screen | What it is for | Built shape (files) | Status |
|---|---|---|---|
| **Home** `/home` | His dashboard: what needs him, what is running, markets, news | One tiling board shared with Lab and Portfolio. Tabs: Today / Markets / Research, plus saved tabs. Greeting, editable ticker, bell, "Needs you" (copilot questions, promotions to sign, paper runs ready, raised kill switches, failed runs). Also Going on, Pods, News & events (crypto / FX+macro, with sentiment and source), Markets watchlist, Coming up, Screener (a tier-1 spec panel), Recent. `routes\home\+page.svelte`, `lib\home\panels\*` | Built; not reviewed. Open: many parallel jobs, a Markets view for one broker, templates, richer approval |
| **Copilot "desk"** `/copilot` | Hand the copilot errands that run for days; the main copilot can reach everything | Left: errands grouped Needs you / Working / Earlier, with sub-agent children. Centre: errand header (goal, 5-step track, chips: helpers, reports, changes, Terminal, Browser), the conversation as large text, and a folded "What it did" receipt. The pending question or approval takes over the composer. Right drawer tabs: Activity (sub-agents + background jobs with where each runs), Preview, Diff, Terminal, Browser. Focus mode, pop-out window. `routes\copilot\+page.svelte`, `lib\copilot\{Thread,WorkArea,ErrandHeader,PendingPanel,SessionsSidebar,store.svelte.ts,demo.ts}` | Built in 10 minutes; not reviewed. Terminal only echoes; Browser is an iframe |
| **Library** `/library` | One catalogue connected to every screen | 16 shelves in five groups: things that trade, things that run, proof, inputs, knowledge. Cards or list, an inspector with a "where it's used" map, Journal & logs and Code tabs, collections, multi-select → copilot, reading mode, article sources (MQL5, arXiv, clippings, web), "Explain it as" ×4 via `/copilot?ask=`. `routes\library\*`, `lib\library\items.ts` | Approved. Open: full model/app pages, Save to Library, Firecrawl (paid) |
| **Lab** `/lab` | Authoring + Backtest + ML Studio merged. Build, test, train, compare strategies; design, test and paper-trade pods | Tiling board with saved layouts, linked panels (border colour per link group) and a minimise dock. Bench switch: **Strategies** (Build, Test, Train, Compare) or **Pods** (Design, Test, Paper). 28 panels in `lib\lab\panels\`: Editor, Inspector, Runs, Matrix (sweep), Equity, Robustness, Compare, Training, Slots, Data, Compute, Agents, Logs, Resources, PodStack, Block, SizeTrail, Fan, Stress, Interventions, HeadToHead, PodEquity ("Run together"), PaperRun, PaperFeed, Graduate, PodResources, Pinned. Also: machine picker (VS Code-remote style), Start-something-new guided flow, scenario builder, Lab copilot | Approved for first stable release |
| **Portfolio** `/portfolio` | Watch money: pods live and paper, risk, road to live, kill switch. The trading node is folded in as "Live" | Layouts: Overview, Pods, Live, Road to live, MIS. 15 panels in `lib\portfolio\panels\` (Accounts, Pods, Pod, Positions, Holdings, Exposure, Correlation, BotCharts, Events, Journal, Road, Signing, Nodes, Mis, Control). Kill-switch chip and grid in the header (`KillMatrix.svelte`), servers strip, templates. Spot crypto: Binance, Bybit, Coinbase, Kraken | Approved. MIS "let it slide" |
| **Apps** `/apps`, `/apps/[id]` | Mini apps, judged by what they can touch and how far they have got on their road to live | Section 1.4. `lib\apps\{apps.svelte.ts,AppDetail.svelte,FromWidgets.svelte}`, `routes\apps\*` | Pass 1; not reviewed |
| **Settings** `/settings` | All configuration | Sections (`routes\settings\+page.svelte:40-65`): General (readiness, workspace, sources), Appearance (7 themes, background art + variants + rotation, surface styles Glass/Liquid/Solid/Brutalist, text size Standard/Large/Larger, "Your theme"). Then Exchanges and accounts, Servers, Model providers, MCP servers, Data and sources, Copilots, Mini apps, Safety, Developer (demo mode, component library). `lib\settings\*Section.svelte` | Regrouped; not reviewed. Data & sources is still a stub; keys go only to the OS credential store |

Screenshots: `SHOTS\v24\*` (desk: errand, receipt, drawer, new errand, 1280), `v23\*` (Home: Today, bell, Markets, 1280), `v22\*` (copilot pass 2: draft panel, pin to Lab, sub-agent thread, diff), `v18\*` (Pods Design/Test/Paper, kill grid), `v19-v20` (Library), `v16-v17` (Portfolio).
There are no screenshots of the Apps screen or the Settings regroup (`v25\` is empty).
What the screens look like: dark glass over ink-art candles and fractals, tile borders orange for paper and blue for live, mono numbers.

### Node editor / authoring
- It lives inside Lab › Build as `EditorPanel.svelte`, using `@xyflow/svelte` SvelteFlow. It has three modes:
  - **Graph**: a Graph Template, i.e. a workflow of steps;
  - **Code**: first-class plain code (DEC-0433);
  - **Import**: Claude Code/Codex output, notebooks, ONNX, a repo folder.
- Map toggle, refit on resize. The Inspector shows step settings, code and **where each step runs**.
- Rule shown: "Drafts never run; only published versions do", which maps to backend Epic 71 `save_editor_draft` / `publish_editor_draft` / `draft_not_runnable`.
- Open (`UI-LEDGER.md` L5): run state on nodes, a saved-steps palette, copilot edits to the graph. The copilot cannot actually change the graph.

## 1.3 Pods and the kill switch

- **Pods replaced Books** (10-03). A pod is one risk/sizing method: a Book + BMS is one kind; models, Lab workflows and hybrids are others. Each pod has a **live side and a paper side running at once**. Designed and paper-tested in the Lab, it is wired into Portfolio by a copilot.
- **Pod stack** (Lab › Pods › Design; `SHOTS\v18\0-pods-design.jpg`): ordered slots run per trade: Inputs, Guards (kill line, daily stop, news-aware kill switch), Allocator, Sizer, Throttles (regime, volatility spike), Caps, Ledger, Venue fit. There are 25 blocks and 10 spot templates. Size trail shows each block's cut to a trade. "Send to paper".
- **Pod Test**: equity + stress board (built-in and "Yours" scenarios from the copilot, real dates or hand-set shocks), Head to head (bars with a noise width, a trophy only when the gap beats the noise, no total score), drawdown fan, "Run together" mixes (replaces Allocate).
- **Pod Paper**: paper equity against the band its test predicted, soak day, verdict, live decisions feed, a "Ready for live?" checklist, then Promote. Signing and activation stay in Portfolio, effective at the next day boundary.
- **Kill switch** (`lib\portfolio\KillMatrix.svelte`, `kill.svelte.ts`): always in the Portfolio header as a grid. Pods run down the side, servers across.
  - Pick a row (pod everywhere), a column (server), a square (one pod on one server) or the corner (everything).
  - Two strengths, "Stop new trades" and "Close and halt", each needing a second click; plus Resume.
  - A second tab holds exchange-account KSA levels. Demo toast: "the real switch goes through the daemon".
- **Backend reality:** the node powers list has no per-pod pause and nothing per server. New powers are needed, each rechecked at click time and journaled.

## 1.4 How the UI represents mini apps (Apps pass 1, `WT\src\lib\apps\apps.svelte.ts`)

- **Design intent (the agent's own):** judge an app the way you judge a pod, by **what it can touch** and **how far it has got on its road to live**, never by how it was built.
- **Risk classes (`RISK`):**
  - *Shows things*: goes live by itself once tests and shadow run pass.
  - *Runs work*: goes live by itself inside a budget it can't exceed.
  - *Touches money*: only proposes; every order needs his signature in Portfolio.
- The same table appears in Settings › Safety (`lib\settings\SafetySection.svelte`).
- **Kinds (`KIND`):** Has screens / Runs in the background (headless) / Both. The backlog's "three kinds" (remix screens, headless apps, extensions = in-app code) are not done: extensions are not built.
- **Road to live (`STEPS`):** Build → Tests → Sandbox (its own container on recorded data) → Shadow run (live data, output logged but used by nothing; the mini-app version of paper trading) → Live (monitoring, budget, per-app circuit breaker). Called "QMX's own CI". Each step must leave **evidence, not logs** (DEC-0456).
- **Apps screen:** bands are Live / Proving itself / Being built. Each card shows:
  - a health dot (ok / warn / tripped / idle);
  - the risk class;
  - a 5-step track;
  - a one-line stage note.

  A tripped app sorts first with a red border.
- **Detail pane (`AppDetail.svelte`):**
  - Risk class and its go-live rule.
  - "It stopped itself", with Restart and "Ask the copilot why".
  - Road to live with the evidence per step.
  - What it gives you (`provides`), what it feeds (`feeds`), schedule.
  - **Its box:** runs on, budget plus `budgetUsed`, network allow-list, circuit-breaker rule, the ops it may call.
  - Last log lines.
  - Actions: Open it / Run now / Pause / Ask the copilot / Remove.
- **Eight demo apps** cover every case:
  - News & sentiment (live; feeds Market mood);
  - Coin screener;
  - Weekend watcher (headless, Telegram);
  - Exchange status (tripped breaker);
  - Market mood (shadow run);
  - Whale alerts (sandbox);
  - Weekly DCA proposer (touches money, failing tests);
  - Correlation map (built overnight by the copilot).
- **Eight templates:** News digest, Price alerts, Funding watcher, Token unlocks, On-chain flows, Weekly report, Liquidation map, DCA proposer.
- **New app, three ways:**
  1. describe it to the copilot;
  2. **make from widgets** (`FromWidgets.svelte`): pick Home and Portfolio panels (not Lab yet), name it, and it opens at once on the tile board at stage Build (`apps.fromWidgets`, kept in localStorage `qmx.apps.v1`);
  3. a template.
- **App screen** `/apps/<id>`: the same tile board (`layoutFor`), with Edit layout and + Widget, and a "Not live yet" banner until Live.
- **Safe mode:** one switch shared by Apps and Settings that turns off everything not shipped with QMX.
- **Settings › Mini apps** reads the same list. The Research demo app is retired.
- **Not done:** Lab panels as widgets; opened apps on the rail; extensions; real runs, logs and evidence.

### Three screen tiers and surfaces (`S4C\handoff\MINI-APPS-AND-COPILOT-CONTRACT.md` §2; a proposal, not ratified)
- **Tier 1, Description** (built): a JSON panel spec drawn only from the QMX catalog, so no author code runs in the window.
  - Code: `WT\src\lib\sdk\spec.ts`, `SpecView.svelte`, `pinned.svelte.ts`, `spec.test.ts`.
  - Catalog: Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button. A Button carries an op id, never code.
  - `validate()`: catalog types only, required props, children exist, no loops, ≤60 elements, ≤6 levels deep.
  - The data binding is an op or stream id, never a URL.
  - json-render was never installed; this home-grown spec replaced it without a recorded decision.
- **Tier 2, Sealed window** (not built): MCP-Apps-style sandboxed iframe, theme tokens passed in.
- **Tier 3, In-app code** (not built): a reviewed plugin bundle, bb-style. Never for unreviewed copilot code.
- **Surfaces (start with five):** a Lab or Portfolio tile, a copilot message card, a Home widget, a copilot right-panel tab, a per-app settings section.
- **Host rules:**
  - theme tokens only;
  - crash containment;
  - generations (mount the new version first, keep the old if the new fails);
  - every registration undoes itself (the Cordis rule);
  - safe mode;
  - text floor 12px, num style, scroll inside the panel, test at the minimum size.
- **Backend already has (on integration):**
  - PackUiRequest v1 with closed slots `app-nav, canvas-widget, detail, copilot-panel, preview-tab` and renderers `native | json-render | mcp-app`;
  - ActionContext (0 grants: paints but cannot act; 1: bound; 2+: `GRANT_AMBIGUOUS`).
  - Source: `S4C\handoff\research\backend-map-miniapps.md` §1.

## 1.5 Sandbox / Docker ideas for apps

- **Operator direction (10-04):** each mini app in **its own container/sandbox** (Docker or similar) with "full access inside the box". Each box has circuit breakers, logging, monitoring, observability, a budget, an egress allow-list and a per-app kill switch. Copilot code may run with full access inside it ("I think yes"). Contract §1, §6.
- **The UI already shows a "box" per app:** runs on, budget, network, breaker, ops. The tripped state shows "It stopped itself", plus a Sandbox road step on recorded data.
- **Backend reality** (`backend-map-miniapps.md` §3, §7):
  - The CT-46 ExecutionEnvironment declares `local | docker | remote_container | remote_host | browser | desktop`, with "docker-per-worker ephemeral default". But **no code starts a container**.
  - Pack Python is `exec_module`'d **inside the daemon process** (`plugins/packs.py`).
  - There is no per-app budget, egress enforcement, circuit breaker, per-app kill switch or per-app metrics.
  - The nearest real sandbox is QMB per-run OS process limits (`qmb/src/qmb/orchestrator/spawn.py`).
- **Conflicting rulings to amend:**
  - ADR-0019 / DEC-0200/0201: containers only for observability, never on the node VPS.
  - GAP-0075 / DEC-0316: Modal, Daytona and E2B rejected.
  - "No fourth observability product".
  - Logs ≠ evidence.
  - Packs can never reach the money path.
- **First ruling recommended** (contract §9.2): where pack code runs (in-process, subprocess or Docker), on workstation/research servers and never the trading node.

## 1.6 The Copilot: how it builds, controls and accesses workflows and mini apps

- **One session store** for the main copilot and the screen copilots (Lab, Portfolio, mini apps). A side chat moves into main by id and keeps its history.
  - "Errands" have an origin, a status (needs you / working / earlier), an age and agents.
  - Sessions run for days. Agent requests were removed (10-03); permissions are parked (10-04).
  - Code: `lib\copilot\store.svelte.ts`, `demo.ts`.
- **A session is an append-only list of typed blocks** (contract §7, `BACKEND-REQUIREMENTS.md` "Main copilot"):
  - user message + attachments, text, plan;
  - agents (name, role, state, where it runs, last line, progress);
  - tool calls;
  - "changed elsewhere" deep links;
  - artifact (save to Library), table, before/after entity card;
  - question (options, recommended, free answer);
  - permission (once / session / not now; real money never);
  - panel draft, handoff.

  The UI shows only what the log holds.
- **Sub-agents are child sessions** that get only their task (T3 Code style). They open as child threads with Back. Activity covers sub-agents and background jobs with where each runs, and Stop.
- **Mode and reach per message** (`AimMenu.svelte`, `aim.svelte.ts`): Ask / Plan / Do; reach = Lab, Portfolio paper, Library, mini apps, servers, settings; who answers. Real money is never in reach. Today it changes no behaviour.
- **Building UI:** the copilot replies with a tier-1 draft panel that you **Keep / Throw away / Pin to the Lab**. Pinning adds a Lab tile with no restart (`SHOTS\v22\5-draft-panel.png`, `6-pinned-in-lab.png`).
  - Proposed backend tools: `ui.propose_panel`, `ui.propose_layout`, `ui.propose_app`. Each draft is validated against catalog, granted ops and size range, and stored versioned.
  - Install is one logged, reversible transaction (DeepSeek Harness `plugin_manager`).
  - Chat markers (`::inline-vis` / LangGraph `push_ui_message`).
  - A tiny authoring skill.
- **Building mini apps and workflows:** a planned build mode where the copilot builds **overnight, unattended**, then the app proves itself on the road to live.
  - Demo: Correlation map "built overnight"; Weekend watcher "set up by the copilot from an errand"; an `errand` field on each app; "Ask the copilot" / "Ask the copilot why" deep links (`/copilot?ask=`).
  - Monitoring/cron as a copilot-set workflow; where it lives is open (maybe a mini app).
- **Starting work:** Lab "Start something new" → copilot question cards → a guide strip that switches Lab layouts step by step (`lib\workbench\GuidedStart.svelte`, `lib\lab\guides.ts`). Pod tools are planned: pod.edit / test / stress_scenario / mix / paper.
- **Per-surface copilots:** own tools, targets, attach sources and starters (`lib\workbench\copilot-context.ts`, `lib\lab\copilot.ts`, `lib\portfolio\copilot.ts`).
  - Settings › Copilots lists Main, Lab, Portfolio and "News & sentiment (mini app)", each with model, mode, reach and instructions (`CopilotsSection.svelte`).
  - Model providers: Claude through your plan (CLI proxy), Anthropic API, OpenAI, Gemini, OpenRouter, local. MCP: Firecrawl, Exchange data, Files, GitHub + "Add an MCP server" (`ConnectionsSection.svelte`). Opus 5.5 is the intended daily driver.
- **Agentic stack (10-04 ruling):** the agentic layer moves to LangChain/LangGraph. QMX's own agent SDK is dropped. Two SDKs: agent (LangGraph) and mini-app/widget (UI part undecided). The copilot should be a desktop-app-class chat with a **real terminal**.
- **What is fake:**
  - Replies are scripted.
  - Terminal echoes; Browser is an iframe most sites refuse.
  - Skills are not shown.
  - Pop-out is an unsynced copy.
  - Fixed-px text was converted to rem in 8ef175ad.
  - `HowDoI.svelte` is still present.
- **Backend reality** (`SP\audit-code.md` §2.2): `authored_graphs.py` (copilot proposal → MissionCompiler) exists but has **no production caller**, so the copilot cannot turn a proposal into a graph today.

## 1.7 Where jobs run (compute providers)

- **Ruling:** any provider (own laptop, VPS, Colab, AWS, GPU clouds), added and removed by the operator in Settings. Each run/job shows where it ran and its cost. Off-machine work pulses and is labelled "exploration only" until B-9 (evidence of remote runs) is ruled.
- **Demo environments** (`lib\lab\demo.ts:23-`): This laptop (local, evidence ✓), Research VPS Hetzner (remote_host), Colab (remote_container, T4), AWS GPU g5.xlarge; plus storage buckets (S3/B2). Kinds map to CT-46.
- **Lab machine switch:** connect first, then every tile is scoped to that machine. The status bar shows "3 of 4 machines · 4 jobs". Activity and Home "Going on" tag each job with vps-fsn / colab / This laptop / Tokyo.
- **Two kinds of agent work to place:**
  1. the copilot's own agents and swarms;
  2. workflow agents inside Graph Templates, local or on a server, including always-on and multi-hour jobs.
- **Trading servers** (Frankfurt, Tokyo, This laptop) appear in the Portfolio servers strip, Settings › Servers and the kill-grid columns.
- Agents on their own VMs (EC2, Modal) is backlog. Modal was rejected by GAP-0075.

## 1.8 Design rulings to respect (summary of `session-summary.md` §4, `UI-BACKLOG.md` top)

- **Own spin**, not borrowed from Codex, Claude desktop, T3, bb or DeepSeek. Mechanics may be studied.
- **Bigger fonts:** 17px base, rem only, Text size setting. Judge at 1920-2560.
- **"Lego":** defaults everywhere, everything addable, removable and editable; templates on every building page.
- One tiling widget system everywhere; Bloomberg-style minimise-dock-reflow.
- Spot crypto only (Binance, Coinbase, Bybit, Kraken). IC Markets, cTrader, CFDs and props are out.
- Every value needs a backend source; demo data is removed at wiring; there will be a "day one with no demo data" pass.
- Web app first, desktop wrapper later. Start-up screen "world filling slowly by theme".
- Order after mini apps: start-up screen → day one empty → screen sizes → desktop wrapper.

## 1.9 Every backend capability the UI needs, by domain
(From `S4C\BACKEND-REQUIREMENTS.md` + contract §2-§9. Superseded: Books → pods; agent requests removed; Allocate → "Run together"; Authoring → Lab; QMA agent SDK → LangGraph.)

**A. Transport, pairing, readiness, identity**
- Live CT-40: WebSocket JSON-RPC + HTTP GET snapshots + `wire.attach` events. `/pair/start|confirm|renew`; WS subprotocol `qmx.pair.<proof>`; five readiness axes + `retry_probe` (Epics 67/68).
- Three browser issuers only: `dispatchChat` (`send_message`), `dispatchInvoke` (InvocationEnvelope), `dispatchCancel` (`cancel_job`). The browser never spawns Python or holds credentials.
- A missing method returns typed `INCOMPATIBLE` / `caller_kind_unsupported`, never empty success (J-UI-13). Accepted ≠ completed: wait for the terminal JobHandle state.
- Push "changed" events so layouts and panels redraw without a restart.

**B. Copilot sessions and agents**
- `psess:` list/create; `list_mailbox` with `product_session_ref`; `send_message` (Epic 69). Session origin, status, age, agent count, pinning; move a session into main keeping its history.
- Session as a stream of typed blocks (the list in 1.6). Sub-agents as child sessions.
- Activity feed across sessions (agents + jobs, progress, where it runs, log tail, stop). Scheduled jobs report back to the session that set them.
- Mode, reach and answerer per message. Slash-command registry. Per-copilot instructions, tools, skills, default model. Per-surface tool lists, targets and attach sources.
- `PluginManifest.copilot_profile`; `app-use` psess (Epic 60.1).
- Copilot build mode (overnight), multi-day sessions off-machine with sub-agents.
- Real terminal through the daemon, which overrides AD-21 "preview only". Today: a read-only job output stream.
- Provider/model registry for the composer and Settings (the UI stores no keys).

**C. Mini apps / packs / panels**
- Instance listing + `health()`; `get_pack_ui_request` by `instance_id` + `availability_revision`; PackUiRequest v1 `nav[]/views[]`; ActionContext per mount (Epics 64/72).
- Serve the tier-1 catalog to the copilot as a tool schema. Validate on the server. Bind `data` to real ops/streams with empty, stale and failed states. Grow the catalog with real QMX panels.
- `ui.propose_panel|layout|app`; versioned drafts; reversible logged install; chat markers.
- Surfaces contract (5 surfaces with size contracts, declared in the manifest).
- Approval by risk class; shadow-run length per class.
- Road-to-live states with **journaled evidence per step**.
- Per-app box: container launcher, budget, egress allow-list, circuit breaker, per-app kill switch, logs, metrics, health.
- App-to-app feeds ("feeds Market mood"). Apps providing widgets and panels. Per-app settings. Safe mode. App templates.

**D. Authoring / Lab (Graph Templates, runs, ML)**
- `save_editor_draft` (daemon-issued id, CAS on `editor_revision`), `get_editor_draft_head`, validate, `publish_editor_draft` → enable → grant → instance → invoke; a draft refuses with `draft_not_runnable` (Epic 71). Add-step palette (operations / Graph Template contributions).
- Runs per subject: procedure, run role, market, measures, state, progress, **where it ran** (CT-46 env ref); CT-32 equity series; run console stream.
- Sweep grid by market × timeframe (B-12; CLI wiring missing DEC-0286). Scenario submit with count and time estimate. Pairs, saved scenarios.
- Robustness ladder per run plus operator pass bars (GAP-0048/0049). Compare N runs with refusal reasons.
- Import model file, repo or notebook. Training jobs with curves. CT-12 split manifest.
- **ML model as a first-class object** with slots (entry, sizing, regime, throttle, custom). New scope: DEC-0172 only allows weights baked into bot logic.
- Datasets: provider, schema, tz, freshness, gaps, revision; upload via `PUT /artifacts/stage` (Epic 70), connect a source, derive.
- Saved tests, reports, datasets and feature sets as reusable items; templates stored by the backend.
- Agents tree: quants, agents and sub-agents with state and environment (live read model).

**E. Compute and storage**
- CT-46 environments: kind, hardware, slots used/total, cost, status, evidence eligibility. Add/remove SSH, Colab or cloud GPU (vendors GAP-0075). Storage buckets: list, connect, usage, cost.
- Evidence status of remote runs (B-9 ruling). Laptop-off continuation (continuation host).

**F. Pods, Portfolio, node** (biggest gap: no doc connects the UI to the node; ADR-0026 says the UI talks only to the daemon)
- Accounts and venues with role, equity, today, settlement currency (USDT gap DEC-0267), node, reconciliation, KSA level; connect an exchange.
- Spot exchange adapters (Binance, Bybit, Coinbase, Kraken), order-size filters, USDT/USDC quotes, 24/7 budget periods, testnet paper accounts.
- Pod read model: version fp1, template, account, mode, binding, seats, equity series (live + paper sides), USD sizing ladder, loss used, distance to kill line, rule states. Risk source = rules / model / hybrid / Lab workflow.
- Pod paper runs: equity vs predicted p5/p95 band, soak day, verdict, graduation checks, live sizing-decision stream. Pod tests and custom stress scenarios as objects. Mixes ("Run together"). Lab pod tools.
- Exposure and correlation as as-of reports (DEC-0143). Events and news mapped to pods. Live prices and charts. Positions and working orders across accounts.
- **Kill switch by scope** (all / server / pod / pod×server; stop-new / close-and-halt / resume). Needs new node powers, rechecked at click and journaled. Existing powers: resume, escalate, flatten, paper flip, reset paper, resolve unknown.
- Trading servers: location, latency, heartbeat (DEC-0262), accounts; add a node.
- Road to live: stages, server-run checks, card, evidence, sign, activation at the day boundary (TN-20, DEC-0205/0261).
- MIS labelers (live/shadow). Pod templates. Per-bot trading journal (R, events, notes).

**G. Library and knowledge**
- Facade search over HTTP returning typed ArtifactHit / KnowledgeHit / ContributionHit. Article full text + figures + "key points" by a cheap model on the daemon.
- Feed subscriptions (arXiv q-fin, alphaXiv, SSRN, MQL5; RSS/APIs, daemon-side). Save to Library via artifact staging. "Turn into hypothesis" (QML Stage 0 with `research_ref`).
- Entity detail: evidence runs (CT-32 + role), journal (CT-13), connections, operations with input schemas, linked artifacts.

**H. News, data sources, settings**
- Crypto news + FX/macro calendar (free; Forex Factory is the only ruled source DEC-0214); sentiment scoring (a workflow template); mapping to coins and pods.
- Data upload (CSV/Excel), cron/scrape sources. Firecrawl/Alexandria are paid and need approval.
- Per-user preferences store (optional: art presets, layouts, templates across machines). API keys only in the OS credential store; Claude CLI proxy; MCP server registry.

## 1.10 Known untruths and gaps in the UI work (from `session-summary.md` §6, `session-review.md`)
- Fast passes skipped options and click-through: desk (10 min), Home (6 min), Settings (no visual check until 8ef175ad). Pass 1 copilot was "a storyboard of one conversation".
- Ledger claims "terminal per job" and "browser with address bar"; both are demo. Skills were ticked done but never existed (later unticked in 557da44b).
- json-render was never installed. The home-grown `lib/sdk/spec.ts` was not recorded as a decision, though the 09-23 architecture specified `@json-render/svelte` + MCP Apps.
- Silent regression: the pods commit 9aadfc76 deleted the Lab Logs panel (restored 10-04 with a test).
- Open decisions (contract §9):
  1. which qma-daemon subsystems survive LangGraph;
  2. where mini-app code runs;
  3. adopt three tiers, and can tier 3 be copilot-written;
  4. risk/approval table + shadow length;
  5. real shell vs AD-21;
  6. per-app observability vs "no fourth observability product".

---

# PART 2 — Aurelius's baseline audit (before any coding)

Sources:
- `C:\Users\Mubarak\Downloads\QMX_Baseline_Audit.pdf` (text: `SP\audit-packets\baseline.txt`)
- `QMX_Audit_Work_Packets.zip` → `SP\audit-packets\` (START_HERE, MANIFEST.json, Work_Packet_00…10, `reproductions\`)

## 2.1 Identity and pins
- Title "QMX Baseline Architecture and Runtime Audit — Renewed for Mubarak on **30 September 2026**". START_HERE says "Prepared 30 September 2026", so the stated date is 09-30, not 10-01. Coding started 10-01 08:21.
- Pins:
  - backend `a0e87697` (origin/integration, PR16-19 = Epics 70-73 merged);
  - docs authority main `c3e8ec5e`;
  - UI `f6ffaddf` on `ui-epic/066-shell`. This is the old Grok-era shell, scrapped 10-01 and replaced by the Claude rebuild in Part 1.
- 25 remote branches were inspected and no combined backend+UI tree exists. Relative to the earlier baseline 49e72693, integration added 29 commits and 76 files (70 in qmx-agents). QMF, QML, QMN and QMB execution are unchanged.

## 2.2 Verdict
- "Real progress, but QMX still does **not** meet the Windows out-of-box mini-app goal. **Keep the domain architecture.** Repair the installed product and its evidence chain before any broad repo reorganization."
- No readiness percentage is supported. Windows, real provider/broker, browser visual and accessibility, and security review are all uncertified.
- "No technical reason to buy Claude": Codex implementer + separate reviewer is enough. But the Codex lane needs explicit ratification under CLAUDE.md, with operator merge control kept.
- Recommended sequence:
  1. pin one candidate;
  2. fix packaged bootstrap + fail-closed gates;
  3. prove one provider-free browser→durable-result mini-app journey, then a second pack on the same host;
  4. domain repairs alongside;
  5. refactor measured seams only after characterization tests;
  6. Windows installed acceptance last.

## 2.3 What it called correct (keep)
- **QMA:** the 17 selected Epic 70-73 controls pass (durable drafts with CAS / lost-ACK reuse / publication replay, pack-UI metadata, failure compensation, cancellation races) on real stores. Caveat: the composed graph is empty, the view fixture is empty metadata, and no worker runs. Real SQLite/journal behaviour.
- **QMF:** exact risk types; exact-money / scale / rounding / overflow / canonicalization (no new defect); registry as-of reads and canonical stamps.
- **QML:** conformance machinery. Plain-Python is fine; no `.qml` DSL is not a defect.
- **QMB/QMN:** shared unforked slice mechanics.
- **MIS:** immutable values and canonical producer checks.
- **KSA:** epoch/severity folding.
- **UI shell:** typed capability refusals, reconnecting/unknown states, separate chat/invoke/cancel issuers, app-close vs job-cancel semantics, source a11y affordances.
- **Static structure:** a 707-module import inventory preserves the intended package direction, so there is no basis for a ground-up folder move.
- **Suites:** root 5,252 passed (7 live deselected); tooling 348 passed / 1 skipped; UI shell 46 unit tests.

## 2.4 Findings by severity (stable IDs)

| ID | Area | Severity | Finding (one line) |
|---|---|---|---|
| MA01 | QMA bootstrap | High (blocker) | `python -m qma.daemon` exits 2 with only an INFO `daemon.composed` line; default compose lacks the mandatory research-corpus `root_path`. There is no first-run route |
| MA02 | QMA install | High (blocker) | Non-editable QMA wheels lack all pack manifests and entrypoints; outside the checkout, mandatory packs are missing |
| MA03 | QMA provider | High | OpenCodexDeployment with no handler returns a **synthetic OK** with no provider call |
| MA04 | QMA execution | High | The serving root has no START_MISSION/LAUNCH_TASK branch (method-not-found); dispatcher, runtime and provider are never composed into an execution chain |
| MA05 | QMA runtime | Gap | `start_rlm_kernel` returns a descriptor and launches no interpreter or container; no launcher/reattach proof |
| UI01 | UI | High (blocker) | Production default is `recordingTransport`, which returns recorded success; no fetch/WS/EventSource exists |
| UI02/03 | UI | High | Authoring is a static blank graph with Save always disabled. Copilot Start, Library Search and Settings are dead or copy only; Resume and opened apps live only in memory |
| UI04/05 | UI | Medium | Bootstrap and pair are fixtures; 15 Playwright tests never ran; contract/perf scripts print "scaffold success" by default |
| QB01 | QMB CLI | High | Installed `qmb backtest run` cannot resolve its port, Book/BMS fragments or slices; Book/BMS options are discarded; QMA transport placement is accepted, then the child exits 1 |
| QB02 | QMB worker | High | The default child uses `SilentSliceHandler`: a backtest-shaped success **without executing the selected bot** |
| QB03 | QMB evidence | High | CT-32 mint omits trades, equity_curve and journal_events; a real fill with $2.50 commission and −$3.50 financing still reports zero fees |
| QB04 | QMB ledger | High | Governed `spawn_governed` success writes **0** terminal ledger rows (control: 1) |
| QL01 | QML conformance | High | Omitting `factory_spec` lets an always-throwing bot pass all 6 Layer-2 checks; scan and executable are different artifacts |
| QM01 | QMF/QMN command | High (latent) | Long and short entries produce the same command identity; the same Command encodes as buy and sell with the same `client_msg_id`; side, symbol and account come from mutable context |
| QM02 | QMN dispatch | High (latent) | Swapping `BookPathContext.account` to a live account yields OK and a live-addressed command despite a demo-admitted target |
| QM03 | MIS freshness | Correctness | A future snapshot (frontier 1000) is accepted at decision 900 by Book and KSA |
| QM04 | MIS mint | Correctness | A demo SQS slot is mintable into a live snapshot (public factory, no env cross-check) |
| QM05 | QMN admission | Correctness | Hosted dispatch cannot carry `has_open_virtual_position`; it defaults to false |
| — | QMN/MIS integration | Gap | No production Book/KSA caller of `consume_signal_snapshot`; `SeatDispatchReceipt.hops` is a constant; replay reconstructs only SQS rows |
| R01 | QMN service | High (node) | `python -m qmn.host.supervise` (systemd target) exits 0 in 1.3 s with no run loop |
| R02 | Packaging | High (mini-app) | Root build = 11 wheels; nested QMA and packs are outside the bill of materials |
| R03 | QMN deploy | Documented limitation | `qmn/deploy/install.py --apply` always refuses (planner only) |
| DF01 | QMF journal | High | After a torn append + OSError, same-writer `retry_blocked` returns OK but the stream is unreadable (`read_checked` refuses) |
| DF02 | QMB registry | High | `RegistryFragment` tuple-copies sequences without deep-freezing; nested mutation changes content under the same fingerprint / AsOfSet |
| DF03 | Registry lineage | Correctness | A supersedes edge + failed witness write cannot be repaired by retry or reopen (fails closed) |
| DF04 | Journal | Open gap | A multi-room `extra_writes` obligation is held only in memory; no recovery owner (no production caller) |
| NF01 | Indicators | High | SMA marks the mean **confirmed** despite a provisional contributor, with two causes (sparse scatter index; warm-up hiding a dependency); passes `require_governed` |
| NF02 | Indicators | Correctness | Rolling knowable time uses the current-row max, not the support max, so the output is "known" before its inputs |
| NF04 | Structure | Correctness | Lifecycle fold accepts invalidation before confirmation |
| NF05 | Structure | Correctness | Cascade accepts mixed parent/child horizons |
| NF06 | Structure | Correctness | GBPUSD close can confirm an EURUSD swing; the reverse-order variant returns a non-earliest match |
| NF03 | Core | Bounded P3 | Empty half-open `[5,5)` "overlaps" `[0,10)` |
| G01 | Gates | High | Coverage evaluator passes malformed empty summaries and an omitted QMB package. Real source-only coverage is **79.30%** (QMB 76.6, QML 76.6, QMN 74.5) vs the reported 83.95%, which includes 205 non-source files |
| G02 | Gates | High | `check-release` aliases `check-integration`; QMA fail-under is 0; no Windows/UI workflow; mutation runs on schedule only; branch protection unverified |
| — | QA | Disposition | Six qa-verify failures: 3 stale assertions (proto filename, QMB host spawn, loopback socket), 2 QML research/host authority, 1 CT-15 intake-key ownership |
| — | Optimization | Assembly gap | The optimize door runs one trial; no generation/barrier driver |
| — | Refactor | Signal | `DaemonProcess` is 2,937 lines with 126 methods; QMB facade duplicates 2,717 export lines |

## 2.5 Correct vs broken per component (condensed)
- **QMF:**
  - Correct: money/time exactness, registry as-of.
  - Broken: indicator taint and knowable time (NF01/02), structure lifecycle/cascade/swing (NF04-06), interval edge (NF03), journal same-writer retry (DF01), lineage retry (DF03), shared command identity semantics (QM01).
- **QML:**
  - Correct: conformance machinery, plain-Python authoring.
  - Broken: Layer-2 verdict not bound to the declared executable (QL01). Research/host placement is ungoverned (ADR-0023 proposed).
- **QMB:**
  - Correct: deterministic computation pieces, adaptive sampler and stepper exist.
  - Broken: CLI request materialization (QB01), silent default handler (QB02), CT-32 economic inputs (QB03), terminal ledger (QB04), shallow fragment freeze (DF02), no optimization driver.
- **QMA:**
  - Correct: drafts, publication, pack-UI metadata, cancel races, SQLite/journal.
  - Broken: bootstrap (MA01), packs absent when installed (MA02), synthetic provider OK (MA03), no mission/task execution (MA04), descriptor-only runtime (MA05), coverage fail-under 0.
- **QMN / MIS:**
  - Correct: KSA folding, MIS immutability, producer guards, much injectable machinery.
  - Broken: command identity/target binding (QM01/02), future snapshots (QM03), mixed-env mint (QM04), position fold (QM05), no sanctioned service root or service loop (R01), deploy is a planner (R03), no integrated risk/replay proof.
- **UI (old shell):** recording transport, dead authoring, fixture bootstrap (UI01-05).

## 2.6 The work packets (`SP\audit-packets\Work_Packet_*.txt`; "10 packets" = 01-10 plus 00)
All packets share the same rules:
- pin commits;
- new branch only, never touching main / integration / ui-integration;
- regression first with a positive control;
- an independent reviewer;
- no merge, deploy, settings, provider, credentials or trading.

| # | Title | Intent | Exit evidence |
|---|---|---|---|
| 00 | Reconcile candidate | Read-only reviewer. Pin the combined backend+UI candidate and bill of materials; settle the open decisions (Windows surface vs Ubuntu QMN, Codex lane, QML research/host, CT-15 intake keys); dispose the 6 QA failures without deleting tests | Decision record, candidate manifest, finding dispositions, retest list |
| 01 | Restore mini-app host | MA01-04 + R02: actionable bootstrap/config, installed resource contract and BOM incl. nested wheels and packs, compose dispatcher → worker, remove synthetic provider success | Non-editable install starts, runs one grant-bound op, rediscovers the result after restart |
| 02 | Restore backtest evidence | QB01-04 + QL01: one QMB CLI request adapter, selected-source child, evidence accumulator → CT-32, one idempotent terminal row; conformance bound to manifest bytes | Installed qmb, fresh process, nonzero trades with exact costs, one ledger row per terminal outcome |
| 03 | Seal node domain contracts | QM01-05 + R01: versioned command envelope with side/instrument/target, target from frozen admission, reject negative snapshot age, env cross-check at mint, position state, a real supervise loop | Recorded frontier → MIS → Book/KSA → sealed command → recorded order adapter; service survives to readiness |
| 04 | Prove mini-app journeys | Three journeys on one combined candidate: (1) data → reusable mini app (draft, CAS, publish, run, reopen after restart); (2) two instances → durable workflow result (nested task, model double, reattach); (3) chat + optional copilot → action + cancel (lost ACK, grant ceiling, tab close ≠ cancel) | Per-journey traces, PASS / FAIL / BLOCKED / NOT SUPPORTED |
| 05 | Verify Windows release | Clean non-dev Windows profile: install, launcher, duplicate launch, occupied port, crash, upgrade with data, backup/restore, uninstall retention | Installed acceptance record; go/no-go belongs to Mubarak |
| 06 | Data integrity | DF01 reconcile the uncertain tail; DF02 recursive freezer (incl. ConfigFragment); DF03 edge+witness commit protocol; DF04 owner decision or deferral | Baseline-failing regressions pass, plus independent retest |
| 07 | Causal numeric contracts | NF01 (both causes), NF02, NF04, NF05, NF06, NF03 | Discriminating regressions + approved contract decisions |
| 08 | Connect real UI | UI01-05: bind a real transport, daemon-issued drafts with CAS/publish/run/reopen, no dead enabled buttons, real connect/pair, scaffold checks ≠ acceptance | One visible action reaches the daemon, executes, is durable and reopens; second pack with no bespoke code; real screenshots and a11y |
| 09 | Repair release gates | G01/G02: malformed/omitted-inventory regressions, git-tracked source inventory, BOM across root/nested/UI/launcher, fail-closed same-candidate aggregator, reconcile qa-verify, mutation with reviewed survivors | A release cannot pass with missing files, packages, lanes or resources |
| 10 | Refactor measured seams | Only after 01/08/04/02: split DaemonProcess (composition / lifecycle / transport / handlers), separate UI transport selection from fixtures, single QMB facade, move test-only kit fixtures | Unchanged public API, wire and identities; rebuilt wheels pass the journeys |

Order (START_HERE): 00 → (01 ∥ 09) → (08 + 04, then second pack) → (02 ∥ 06 ∥ 07) → 03 before any QMN operational claim → 10 → 05 last.

## 2.7 Reproductions (`SP\audit-packets\reproductions\`, synthetic, Linux CPython 3.14.7, pin a0e8769)
- `check_backtest_and_conformance.py`: QL01 (omitted factory passes throwing logic; matching factory refuses) and QB02 (silent default worker).
- `check_governed_ledger.py`: QB04 (0 rows vs 1-row explicit-finish control).
- `check_economic_collector.py`: QB03 (commission/financing objects exist but CT-32 omits them).
- `check_real_qma_qmb_transport.py`: QB01 (placement acknowledged; real QMB child exits 1). Needs `QMB_BIN`.
- `check_miniapp_runtime.py`: MA01/02/03 (exit 2, INFO-only; synthetic provider OK; optional wheel inventory).
- `check_rlm_descriptor.py`: MA05 (descriptor, no interpreter).
- `check_qmn_domain_contracts.py`: QM01-05 (in-memory mint/encode only).
- `check_causal_numeric_contracts.py` + `test_foundation_numeric_regressions.py`: NF; expected 8 failed / 7 passed.
- `check_data_recovery_variants.py` + `test_foundation_data_regressions.py`: DF; expected 3 failed / 3 passed.
- Caveats from the README: exit 0 only means the observation ran; nothing here is acceptance; Windows was not tested.

## 2.8 What happened to the findings afterwards (cross-checked with `SP\audit-code.md` + read-only `git log`/`git show` on fetched refs + `gh pr view 20-24`)

**Structural fact first:**
- The direct responses to the packets were made on **2026-10-01** in the 316-commit range `a0e87697..7b4ece09`, branch `qmx-stop-checkpoint-2026-10-01`.
- That range is the **base** of PR20, so it is an ancestor of PRs 20-24 but **not in any PR diff**. No PR reviews it and CI never ran on it.
- PRs 20-24 (10-04/05) are drafts with 0 checks, layered on top. Their workflows trigger only on main/integration, and the PR22 trigger fix produced 0 runs.
- **Nothing is merged.** origin/integration last moved 09-30.
- Per-finding evidence notes live at `origin/review/backend-recovery-public-20261005:release/evidence/{host-bootstrap,execution,node,data,numeric,gate-review,install-lifecycle}.md`. They are Codex's own claims; audit-code marks the aggregate counts and "independent acceptance" CLAIMED-UNVERIFIED.

**ID collision warning:** Codex later named its own mini-app lanes "MA01-MA05" (MA01 discovery queries, MA02-04 app candidate / validation / publication in `staging/app_*.py`, MA05 unaccepted, private SHAs `2dfa57d7` / `8ef21bf8` on `D:\Codex-Recovery` only). These are **not** the audit's MA01-05. Do not conflate them.

| Finding | Status now | Where (commit on Oct-1 checkpoint unless noted) |
|---|---|---|
| MA01 bootstrap | **Addressed (claimed)** | `f0392c78` "package mandatory packs and diagnose bootstrap refusals": `<QMA_DAEMON_ROOT>/operator-config.json` with `research_corpus_root_path`; `daemon.startup_refused` ERROR line. PR23 adds startup/control/cleanup repairs |
| MA02 packs in wheel | **Addressed (claimed)** | `f0392c78`: packs bundled under `qma/daemon/bundled_packs`; external non-editable smoke loads 5 packs. PR24: wire schemas shipped in the wheel (`2894da8a`) |
| MA03 synthetic provider | **Addressed** | `f0392c78`: default OpenCodex returns `UNAVAILABLE_DEPENDENCY`; `test_handler` only in tests. **No live provider call has ever been proven** (PR23/24, audit-code) |
| MA04 mission/task execution | **Partly** | `724c3910` compose shared mission/task runtime, `cbec39d6` CT-40 invokes via session grants, `480d3bf8` grant-bound mission start test, `8d06dba9` jobs queued until worker acceptance. Host review: "compile admissions remain QUEUED", i.e. no worker lease is claimed. PR21-24 add LangGraph/actor workflows + canonical join; 4 reproducible actor-deadline test failures remain (audit-code §3) |
| MA05 interpreter launcher | **Open** | No launcher/container commit found; still descriptor-only. No container launcher exists anywhere |
| UI01-05 | **Open (target changed)** | Codex did not touch the UI; `1fc1d5de` / `620c2f88` only document the UI transport boundary (`release/UI_INTERFACE.md`). The audited Grok shell was scrapped; the new Claude UI has **no transport at all** (demo mode, labelled, disabled daemon controls). PR24's "Claude handoff": connect the CT-40 transport, unique producer IDs per tab, keep upload disabled (no operator-cap initializer; 1,024-byte cap is test-only) |
| QB01 CLI request | **Addressed on the replay path (claimed)** | `3e598bbe` durable selected-source `ReplayInputRequest`, `4a483215` content-pinned operator replay composition for delegated CLI, `e72b97f0` QMA service transport → real QMB child, `613c6a74`. Generic `qmb backtest run` was not re-verified; audit-code lists "QMB production CLI child runs" as CLAIMED-UNVERIFIED |
| QB02 silent handler | **Addressed (claimed)** | `70fe7249` installed manifest-bound source loader; execution.md: the selected `HostedBot` runs through Book admission and fill/cost adapters; silent fixtures refuse |
| QB03 CT-32 economics | **Addressed (claimed)** | `3fa9282c` persist realized CT-32 measures; fixture gross −104, fees 2, net −106 USD |
| QB04 terminal row | **Addressed (claimed)** | `83970a03` one terminal ledger row for completed/aborted jobs; siblings reaped |
| QL01 conformance binding | **Addressed (claimed)** | `83970a03` (`qml/conformance/layer2.py`, `qmb/host/runner.py`): manifest `factory.py:factory` byte-verified in host and child; mismatch or silent refuses |
| QM01 command identity | **Addressed (claimed)** | `a982cf09` + `3f34884c` (`qmf-venue/commands.py`, `encode.py`, `qmn/order/identity.py`): admitted instrument and side in place-order params |
| QM02 target binding | **Addressed (claimed)** | `a982cf09`: venue / account / role checked before mint |
| QM03 future snapshot | **Addressed (claimed)** | `a982cf09` (`qmn/mis/signal_snapshot.py`) |
| QM04 mixed env mint | **Addressed (claimed)** | `a982cf09` |
| QM05 position state | **Partly / open** | The door no longer defaults to false, but node.md: "production composition still has not wired this adapter to an actual Book/KSA caller, so QM 05 remains open" |
| QMN integration proof | **Open** | No end-to-end recorded frontier → order-path transcript claimed. GAP-0098 adoption stays open |
| R01 supervise loop | **Addressed (claimed)** | `875d77ab` provider-free stand-down supervisor, `d000e0bd`: supervise validates roots and serves `/healthz`. Ubuntu/systemd runs are BLOCKED/pending |
| R02 BOM | **Largely addressed (claimed)** | `eff8dfa3` hash-pinned bundle, `ad24e8eb` preflight, `16afbfde` node assets, `c3821ea0`; PR24: 14 non-editable wheels, 20 schemas, 5 packs installed. Native Windows still pending |
| R03 deploy planner | **Not verified** | No change found |
| DF01 journal retry | **Addressed (claimed)** | `4c706d1a` (`qmf-data/.../engines/jsonl.py`) |
| DF02 deep freeze | **Addressed (claimed)** | `4c706d1a` (`qmb/config/fragments.py`, `registryread/as_of.py`), `3f964d1c` replay request deep freeze |
| DF03 witness retry | **Addressed (claimed)** | `4c706d1a` (`qmf-registry/persistence.py`) |
| DF04 multi-room owner | **Deferred** (as the packet allowed) | data.md "Deferred before adoption" |
| NF01-06 | **Addressed (claimed)** | `a400f334` "fix causal numeric support contracts" (chrono, indicators/batch, structure lifecycle/families) + `24511efb`. NF02 keeps non-monotonic input accepted but derives knowable time from the support |
| G01 coverage evaluator | **Addressed, with a residual** | `f6e2119f` (`tools/coverage_report.py`, `release_gate.py`) uses a git-tracked inventory. gate-review: artifacts that are empty files with matching hashes still PASS (no format inspection). Source coverage is **still below 80%** (79.08-79.42% aggregate, daemon 78.1-78.2%) |
| G02 release gate | **Partly** | Fail-closed aggregator added (`tools/release_gate.py`, `readiness_gate.py`). The full acceptance gate FAILs because mandatory lanes are absent. No Windows/UI runtime lane. **No CI ever ran on PRs 20-24.** **`main` is unprotected** (audit-code §4) |
| QA 6 failures | **Reconciled (claimed)** | setup.md: DEC-0141 / DEC-0494 exceptions applied; QML host persistence moved out (`86ec0e79`) |
| Optimization driver | **Open** | `b85e83bf` reference-only optimize descriptor; `bbea29d5` "checkpoint unfinished retry, optimization transport and SQS receipt work; stop implementation" |
| DaemonProcess refactor (pkt 10) | **Worse** | 2,937 → 4,007-line class (process.py 4,828). Hand-rolled HTTP/WS. 5k LOC of test fixtures in src. 223k md lines (audit-code §5) |
| Journeys (pkt 04) / Windows (pkt 05) | **Not done** | No combined UI+backend candidate; no browser journey; no Windows install |

**Net:**
- Codex fixed most of the audited domain defects (QB, QL, QM01-04, DF01-03, NF, MA01-03, R01/R02) in one unreviewed day, 10-01.
- It then spent 10-02 to 10-05 on the LangGraph agent core, canonical join, capabilities and recovery (PR20-24), plus mini-app staging (private MA01-04 lane).
- **Still open:** UI01-05 (no transport), MA05, QM05, QMN integration proof, DF04, the coverage floor, Windows, the optimization driver, three-journey acceptance, CI reachability and branch protection.
- **Custody risk:** the private MA02-05 commits exist only on `D:\Codex-Recovery\2026-10-04\integration-base.git` (audit-code §1, §7).

## 2.9 Where Part 1 and Part 2 meet (observations, not rulings)
- **Road to live vs backend.** The UI's 5-step road and "evidence not logs" rule line up with the backend's data-only candidate → validation → publication staging (private MA01-04 lane). Sandbox, shadow run, budgets, breakers and per-app kill have **no backend at all**, and pack code still runs in-process.
- **Journey 3 vs the desk.** Packet 04's Journey 3 (chat → instance → action → cancel, tab close ≠ cancel) is the acceptance test the desk's errands, drawer and Stop need. The UI's "accepted ≠ completed" rule matches the audit's.
- **Copilot building panels and graphs.** It is UI-only (tier-1 spec, pinned in localStorage). The backend `authored_graphs.py` exists but is unwired. No `ui.propose_*` tools exist.
- **Compute "anywhere".** The UI's compute-anywhere and remote-job labels assume CT-46 environments plus a container launcher. That launcher does not exist (MA05-adjacent), and GAP-0075 forbids the hosted sandbox vendors.
- **Kill switch.** The per-pod and per-server switch needs new QMN powers. It sits right on QM02/QM05 territory: target binding and the position fold must be sound first.
