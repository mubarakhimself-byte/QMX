# QMX UI work ledger

How the UI work is chunked and where it stands. The backlog (`UI-BACKLOG.md`) holds the operator's feedback; this ledger holds the order of work. Updated at the end of every chunk.

## Rules (operator, 2026-10-02)

- One screen per pass. Finish it to a usable standard before starting the next.
- Every pass runs the same steps: **research → 2–3 layout options → operator picks → build → click-through journeys → backend mapping**.
- Click-through means using it: click, drag, minimise, small window (1280) and full screen (1920, 2560), empty, overloaded and many-accounts states. Screenshots alone don't count.
- Design skills on every pass: `frontend-design`, `design-system-compliance`, `verify-ui-change`.
- No guessed APIs. Demo data stays labelled. Backend needs go to `BACKEND-REQUIREMENTS.md`; Codex supplies the verified backend path (ruling relayed 2026-10-02).
- "No backend yet" never excuses empty space or settings you can't click.

## Pass order

| # | Pass | Status |
|---|------|--------|
| 1 | **Lab**: Authoring + Backtest lab + ML Studio merged into one permanent section (ruled 2026-10-02) | in progress |
| 2 | Portfolio: books, risk, position sizing, promotions and approvals, allocation, MIS, live trading | first cut done 2026-10-03; awaiting operator review |
| 3 | Trading nodes: folded into Portfolio → Live (ruled 2026-10-03); node manager lives in Settings → Compute and Portfolio | merged into pass 2 |
| 4 | Settings: depth and real controls on every tab; data sources you can add (keys, scraping, schedules) | queued |
| 5 | Home: your own tabs, notifications, many accounts across exchanges, widget reflow on minimise | queued |
| 6 | Library: full-width reader, Artifacts rethink, card art by family, list/card view, detail pages | queued |
| 7 | Copilot (main): collapsible sessions, sub-agent preview, attachments shown in messages, copilot-built widgets | queued |

Cross-cutting items land in the first pass that needs them: per-context composer (tools, target, attach) and app-copilot sessions in pass 1; widget reflow on minimise in the first pass that uses a widget board.

## Pass 1: Lab

| Chunk | What | Status |
|-------|------|--------|
| L1 | Research: what the docs define for experiments, QMB, QML, graphs, compute; reference products (StrategyQuant, QuantConnect, MLflow/W&B, node editors, Bloomberg tiling) | done (docs brief + reference patterns) |
| L2 | 2–3 whole-screen layout options for the operator | shown 2026-10-02 (A workbench, B evidence first, C tiling presets) |
| L3 | Operator picks; record the ruling | done: C tiling engine with A (Build) and B (Test, Compare) as default layouts; name "Lab" |
| L4 | Lab shell and navigation: one rail entry, old Authoring / Backtest / ML entries folded in, links redirected | done: tiling engine (`lib/workbench/tiles`), `/lab`, 4 layouts, 14 panels, rail shows Lab, redirects |
| L5 | Build: node editor rethink (readable over the background, specific copilot), code mode, import a model built elsewhere | first cut: Graph / Code / Import modes, map toggle, refit on resize, inspector shows where a step runs. Open: run state on nodes, saved steps palette, copilot edits to the graph |
| L6 | Test: runs, scenario generator (pairs × timeframes × pair trading), robustness, compare | done (demo): runs table, sweep grid, scenario builder with run count / time / luck warning, robustness ladder, compare with refusal note |
| L7 | Train: ML datasets, features, split/leakage, models, plug into slots | first cut: pipeline, loss curves, CT-12 split, four slots + add a slot (three marked new scope) |
| L8 | Data and compute: datasets, features, presets as reusable items; where it runs (local, Colab, GPU provider) | done (demo): toolbox with add-your-own per group, data with dataset details, compute with slots, cost, evidence status; off-machine work pulses |
| L9 | Lab copilot: its own tools, targets and attach sources; multiple sessions with history | done: per-surface context in the composer; Lab tools, quants as targets, Lab attach sources; sessions, new session, settings |
| L10 | Click-through journeys and fixes | first round done at 1280/1920/2560: minimise reflow, link follow, drag swap, save layout + reload, edit close/add, redirects, scenario counts; fixed edited-mark bug, table wrap, graph refit. Next round after operator review |
| L11 | Backend mapping for Codex; gaps flagged as new scope | — |

## Rulings for the Lab (2026-10-02)

- Layout C (tiling, saved layouts, linked panels, minimise docks and others reflow) with A as the Build layout and B as the Test/Compare layout. Operator: "surprise me" latitude.
- Name it **Lab**. Docs list Authoring on the rail (DEC-0470); the rename and the backend refactor go to Codex/docs.
- Customisability is paramount: every part has defaults but can be added, removed, edited or rebuilt (model slots for entry, sizing, regime, risk throttle included). Docs lag the vision; design for the vision and flag gaps.
- Any compute provider (own machines, remote hosts, Colab, AWS, GPU providers). Each run shows where it ran; off-machine work is visibly marked. Evidence status per run follows the docs (B-9) and is shown, not hidden.
- Agents and sub-agent swarms inside workflows must be visible, including where they run.

## Log

- 2026-10-02: ledger created. Round 6 feedback recorded in `UI-BACKLOG.md`. Library back arrow fixed (`a5babae3`). L1 research started.
- 2026-10-02: Lab built while operator away (commits 9d3f7985..). L4, L6, L8, L9 done as demo; L5, L7 first cut; L10 round 1; L11 written.
- 2026-10-02: L1 done (docs brief: 17 gaps; reference patterns). L2 shown. L3 ruled (see above).

## Lab round 2 (operator review 2026-10-02: "good enough for the first stable release")

Doing now (L12):
- [x] Composer: icons with count badges, no overflow, drop the Offline label, better new-session empty state; copilot settings link to Settings (agents and models).
- [x] Styled selects everywhere (scenario builder used native ones); add your own markets, parameters and metrics in the scenario builder.
- [x] One **Resources** tile (toolbox + data + compute + model slots + presets + recent indicators), the same in every layout, a quick menu into the Library. Machine status moves to the bottom bar; adding a machine goes to Settings.
- [x] Link-group colour on the tile border.
- [x] Curated default layouts (no equity in Build; runs not everywhere). "Run on" filters the Lab to what that machine runs.
- [x] "Start something new": a guided flow (what are you testing → steps → layout), e.g. compare versions (regime study v1 vs v3 + hybrid), train a model, test a hypothesis, custom workflow.

Backlog (needs backend or later passes):
- [ ] Agents live: their nodes, sub-agents and streamed work (after the QMA refactor). Agents get their own machines (EC2, Modal).
- [ ] Compare: save compare sets as presets, "watch" sets; better equity and compare views; primary and secondary layers.
- [ ] Training: start a session from the editor; a proper training-runs tile.
- [ ] Model slots: "Add a slot" must work; parameters and metrics extensible everywhere; robustness checks configurable and buildable from workflows.
- [ ] Agents in the Lab are mostly workflows: custom workflows (train in a pattern, test a hypothesis) as first-class.
- [ ] "Working on" holds configurations; compare versions side by side and build a hybrid with the copilot.
- [ ] "Build a new panel" and most edits run through copilot skills (design skill input from the UI lane).
- [ ] Remove all mock data when wiring to the live backend.

## Lab round 3 (2026-10-03)

- [x] Machine switching like a VS Code remote window: connect (reachable, signed in, healthy), then every tile shows that machine only; per-layout counts; "nothing here" state that points to where its work is; offline machines say why.
- [x] Copilot-led start for outside work, custom workflows and training: question cards in the main copilot, then a guide strip that switches Lab layouts step by step.
- [x] Transcript audit: recovered requests and rulings written to `UI-BACKLOG.md` ("Recovered from the transcript audit").

## Pass 2: Portfolio

| Chunk | What | Status |
|-------|------|--------|
| P1 | Research (done 2026-10-03: docs brief + 20 verified reference products): what the docs define (Books, BMS, sizing ladder, kill line, KSA, promotion, approvals, seats, bindings); reference products (StrategyQuant/QuantAnalyzer, Darwinex, Myfxbook, Bloomberg PORT, IBKR, Portfolio Visualizer, 3Commas, Riskfolio, approval UIs) | in progress |
| P2 | 2–3 whole-screen options | shown: Risk, Books, Promotions, Optimise on one tiling board |
| P3 | Operator picks (or "surprise me") | "surprise me, take it further" (see rulings) |
| P4 | Portfolio shell on the tiling engine; rail entry; layouts | done: /portfolio, Risk, Books, Live, Promotions, MIS, Allocate; shared LayoutStore; /trade redirects |
| P5 | Accounts and venues: many brokers/exchanges, live risk per account and platform-wide | done (demo): 5 venues, 6 accounts, nodes, KSA per account, USDT flagged |
| P6 | Books: charter, sizing ladder, loss budget, kill line, seats; edits mint versions; templates | done (demo): risk source (rules/model/hybrid/Lab workflow), ladder, rules stack, wall, 10 templates |
| P7 | Promotions and approvals: research-paper → node-paper → live, signed cards | done (demo): lanes, card with server checks (blocks on fail), activation; agent requests with diffs |
| P8 | Optimisation (new scope): allocation across Books and bots, correlation, what-if | first cut: aims, limits, frontier, now vs proposed with resample bands, correlation |
| P9 | Portfolio copilot context (tools, targets, attach), templates | done: own tools, PM/Trader/Analyst targets, attach Book/account/Lab/event, sessions, starters |
| P10 | Click-through journeys and fixes | round 1 at 1280/1920: link follow, paper/live borders, blocked signing, activation, templates, redirect; fixed grid width and frontier size |
| P11 | Backend mapping for Codex | done (BACKEND-REQUIREMENTS.md) |

### Portfolio rulings (operator, 2026-10-03)

- Portfolio is a Lab for risk, sizing and allocation: many Books and BMS variations (mini apps make them multiply), risk and sizing by rules, by ML models, by older QMX models brought back, or hybrids. Sky's the limit; surprise and take it further.
- Allocation is conversational: "this Binance account should grow quickly, let it take on the book." Portfolio copilot is specific, with its own skills; the main copilot reaches it too.
- **The trading node folds into Portfolio** as a Live section (paper and live portfolios; trading locally or on one or many servers). A separate trading node screen is no longer needed.
- QMX's edge over other platforms: agents, news and workflows feed the portfolio; things built in the Lab or the main copilot arrive here.
- Main copilot can take in conversations from other screens (e.g. a Lab chat) and its changes show live elsewhere, e.g. the Lab popped out on a second monitor (Copilot pass).


### Portfolio round 2 rulings (operator, 2026-10-03)

- **Spot crypto only.** IC Markets and cTrader are out; no CFDs, no prop firms. (Big backend change: the docs are cTrader-centred.)
- **"Books" become "Pods".** A pod is one way of doing risk management and position sizing; a Book + BMS is one method among many (models, workflows, hybrids, BMS variants). Nothing centralised.
- Portfolio is mostly for watching; risk and sizing systems are built in the Lab and wired here by the Lab or main copilot.
- Pod page needs a real redesign: less text, bigger controls, things you can adjust.
- Live: a chart per trading bot across the top; positions sortable and richer; trading servers must be actionable (or move into the header); exposure and correlation move to Live.
- Road to live starts at paper trading (anything earlier stays in the Lab); each bot gets a trading journal; use the player (FC/FIFA-style) bot cards here.
- Agent requests go back to the Lab. Allocate leaves Portfolio: allocation is experimentation, so it moves to the Lab.
- Events and news split by crypto and FX (FX as influence on crypto), with sentiment; every item must name its backend source. A news/sentiment workflow ships as a template.
- MIS stays as is for now; later it gets logs, indicators and model views, grown from the Lab or the copilot.
- **Proposal accepted:** an in-depth Lab refactor for risk management and position-sizing systems (pods, Books, BMS variants, models, workflows, allocation experiments).
- Templates on every page that builds things (Lab, Portfolio, and introduce them in the Library).
- Appearance: themes editable like VS Code; background art can rotate on its own; consider design styles (glassmorphism, liquid glass, minimalism, neumorphism, claymorphism, neo-brutalism, skeuomorphism).

### Portfolio round 2 progress (2026-10-03)

- [x] Spot crypto only in Portfolio data (Binance, Bybit, Coinbase, Kraken); pods replace Books.
- [x] Pod page redesign (curve, safety meter, sliders, guard rings, bot weights, draft to paper).
- [x] Live: per-bot charts, sortable/groupable positions, exposure, correlation; servers actionable and in the header.
- [x] Road to live from paper, player cards, promotion card, trading journal.
- [x] Events split crypto / FX with sentiment and source.
- [x] Allocate removed; agent requests in the Lab.
- [x] Appearance: surface styles (glass, liquid glass, solid, brutalist), your own theme, rotating art.
- [x] Lab pods: Pods (stack, block, size trail), Pod test (equity, drawdown fan, stress board, interventions), Pod compare (no total score), Allocate (fund plan). 25 blocks, 10 spot templates. Lab demo data switched to spot crypto (Home still FX: next).
- [ ] Library templates.


### Rulings (operator, 2026-10-03, round 3)

- **Every pod has a live side and a paper side**, running together, so changes are watched on paper before going live (or both trade). Done in the UI; backend needs it.
- Live: positions on top with exposure and correlation as tabs; bot charts below. Done.
- Kill switch always visible in the header, not a tile. Done.
- Road to live: paper-day progress inside the bot card; richer trading journal. Done.
- **Agent requests removed.** Agents mostly run off-machine for long stretches; the operator won't start work he's unsure of. Instead: **copilot sessions that run for days**, using sub-agents (Copilot pass).
- Wants a built-in help or guide feature for things like "how do I train something new" (Copilot pass).
- Mini apps need re-thinking now that Lab, Portfolio and Library are first-class; the Research demo app is redundant (Mini apps pass).


### Rulings (operator, 2026-10-03, round 4)

- **Too many Lab tabs.** Pods, Pod test, Pod compare and Allocate were four tabs on top of Build, Test, Train and Compare. Pods need more thought, not more tabs.
- **New risk and sizing systems go through paper themselves** before money, and that happens in the Lab ("Pod test is where paper trading happens"); positions arrive live.
- **Pod resources differ from strategy resources.**
- **Stress board:** the operator adds his own scenarios with the copilot.
- Pod comparison table: not understood. Allocate: not understood.
- **Kill switch per server or per pod**, combined.
- Mini apps: fine; the Lab took over a lot, which is good. Wants many more mini apps (news, anything else).
- Order after this: **main Copilot, then Library, then Home.** Remember component updates. The copilot must be able to create new things in the UI under rules that prevent overflows and bugs (Copilot pass).

### Round 4 done (2026-10-03)

- [x] **Lab benches.** A Strategies | Pods switch in the Lab header; each bench shows only its own tabs. Strategies: Build, Test, Train, Compare. Pods: **Design, Test, Paper**. Old links (`?layout=pods|podtest|podcompare|allocate`) land on the new tabs. Saved layouts remember their bench (`group` on TileLayout, tested).
- [x] **Pod resources** replace Resources on the Pods bench: Pods (with stage: draft, tested, on paper, live), Bots, Blocks by slot, Stress (built-in and yours), Money (testnets and the node paper ledger). Ticks here are what a test runs. New pod from a template or the copilot.
- [x] **Test** = equity + stress board + head to head + drawdown fan (interventions minimised). Compare and Allocate are folded in:
  - **Head to head** replaces the comparison table: one card per pod with bars (profit, deepest dip, worst crash, kill-line risk, luck share, steps in), a trophy only when the gap beats the noise, and a one-line trade-off. No total score.
  - **Run together** replaces Allocate: split $20,000 across the ticked pods with sliders (equal money, equal risk, ask the copilot), see the combined curve against each pod alone, save as a mix (goes to paper like a pod).
  - Stress board: + Scenario (describe to the copilot, replay real dates, set shocks by hand); your scenarios marked "Yours" and show "Not run yet · Run".
- [x] **Paper** (new): Paper run (paper equity against the band its test expected, soak day progress, verdict), Live decisions (each paper trade with the steps that sized it, refusals, arriving live), Ready for live? (checks, Promote to live builds the promotion card; signing and activation stay in Portfolio), today's interventions.
- [x] **Kill switch grid** in the Portfolio header: pods down the side, servers across. Row = pod everywhere, column = server, square = one pod on one server, corner = everything. Two strengths (stop new trades; close and halt), each needs a second click; Resume. The chip shows how many scopes are stopped. Exchange-account levels stay as the second tab.
- [x] Lab copilot gets pod tools and pod starters; surfaces can draft text into it (seed).

### Pass order (operator, 2026-10-03)

Library redesign, then main Copilot, Home, Settings, Mini apps. The backlog was rebuilt from a full transcript audit (UI-BACKLOG.md, top section).

### Library pass 1 done (2026-10-03)

- [x] One catalogue (`lib/library/items.ts`): 16 shelves in five groups (things that trade, things that run, proof, inputs, knowledge), each item with where it is used. Items come from the Lab, Portfolio and Copilot samples, so links are real.
- [x] `/library`: shelves, cards or list (remembered), inspector with a "where it's used" map and links, settings and measures; Everything view grouped by shelf; search across shelves; + New (template, import, copilot). Deep links `?shelf=&item=`; old `?tab=` links still land.
- [x] Articles: section picker, wider reader with a side column (key points, figures, use it). Sources: videos added, "Add a source", "Make it an app".
- [x] Outbound links: copilot attach opens a Library picker; promotion card and Lab pod resources link into the Library; detail page vocabulary fixed (pod, server, Road to live).
- [x] Demo Library data switched to spot crypto (ids now match Portfolio bots).
- [x] Test: catalogue ids unique, links only to real screens, trading things connect to Lab or Portfolio.
- [ ] Next in Library: model and app full pages, diagrams from articles, Home and "Save to Library" links.

### Library pass 2 done (2026-10-03, evening)

- [x] Journals shelf removed; "Journal & logs" and "Code" tabs inside items (bots, models, pods, blocks, workflows, setups).
- [x] Select several → add to copilot, or save as a collection (kept in this browser; "Your collections" in the shelves).
- [x] Banded, foldable shelf groups; hide the shelves; reading mode for articles.
- [x] Article sources (MQL5, clippings, arXiv, web pages) and "Explain it as" four ways via the copilot (`/copilot?ask=`).
- [x] Portfolio and Lab headers fit smaller screens (button words and server latency show only on wide screens).

### Copilot pass 1 done (2026-10-03)

- [x] Sessions sidebar: "Going on now" (running, waiting for you) on top, then Pinned, Main copilot, and sessions from the Lab, Portfolio, Library and mini apps; foldable; search and New session work. Sessions can run for days.
- [x] Sessions started elsewhere open here with a "Continue here" card; the Lab and Portfolio side copilots offer "Continue in the main copilot".
- [x] The conversation is drawn as blocks the daemon can stream: your message with attachments, plan checklist, sub-agents with live status and where they run, tool calls, "Changed elsewhere in QMX" links, artifacts (open, save to Library), tables, before/after cards, question cards (with "Something else"), permission cards (Allow, Allow for this session, Not now; real money never).
- [x] Showcase session "Weekend-safe pod, end to end": one session drafts a pod in the Lab, tests it on a server, saves notes to the Library and asks to put it on paper.
- [x] Work area: Activity (every agent and background job across sessions, progress, where it runs, stop), Artifacts, Browser, Terminal (job output; commands go through the daemon), Preview.
- [x] "Aim this message at" became Mode and reach: Ask, Plan or Do; which areas it may touch; who answers (main, a screen's copilot, a mini app, a running agent). Real money is never in reach.
- [x] "/" commands in the composer; a new session opens with a greeting and "How do I…" (guided walks for train, bring in, workflow; drafted asks for pods, articles, watching while away).
- [ ] Next: terminal as a real shell through the daemon, browser driven by the copilot, skills list, the rules for copilot-built UI, components registry.

### 2026-10-04: review, Copilot pass 2, Home

- [x] Independent session review (handoff/research/session-review.md); backlog corrected; outdated text fixed (557da44b).
- [x] Research: mini-app screens prior art; bb, T3 Code and DeepSeek Harness from source; backend map for mini apps (handoff/research/).
- [x] Copilot pass 2 (83b87f71), following T3 Code, bb and DeepSeek Harness: it answers (scripted, labelled); builds panels as descriptions (lib/sdk: spec, renderer, validator, tests) that you keep, throw away or pin to the Lab with no restart; one session store with the Lab and Portfolio copilots ("Continue in the main copilot" carries the session); questions and approvals take over the message box; sub-agents open as child threads with Back; right panel with Activity, Artifacts (real previews), Diff, Terminal per job, Browser with an address bar; sessions column folds on its own; small text raised. Lab Logs panel restored (lost in the pods change) with a test.
- [x] Hand-off for the backend session (eec91b38): handoff/README.md and MINI-APPS-AND-COPILOT-CONTRACT.md.
- [x] Home rethink: same tile board as the Lab and Portfolio (one widget system); tabs Today, Markets, Research plus your own saved tabs; greeting; editable ticker (by hand or the copilot); a bell and a "Needs you" panel gathering copilot questions, promotions to sign, paper runs ready, raised kill switches and failed runs; Going on; Pods and News reused from Portfolio; Markets watchlist; a screener built as a panel description; Coming up; Recent Library items.
- [ ] Next: see the later 2026-10-04 entries below.

### 2026-10-04, later: Home, the desk, Settings (all awaiting operator review)

Ruling that drove these (09:50): the copilot "references were a bit poor", text "a bit too small", "have our own spin... not borrow it from other applications". Honest status: Home and the desk were built fast, without the study, options and pick step. He has not seen any of them.

- [x] Home rebuild (7fa36fb5). One tile board (Lab and Portfolio's), tabs Today, Markets, Research plus saved tabs, a greeting, an editable ticker, a bell and "Needs you" panel (copilot questions, promotions to sign, paper runs ready for live, raised kill switches, failed runs, each linking to its screen), Pods and News reused from Portfolio, a screener drawn from a panel description. Built in about six minutes, before the own-spin ruling; checked by script at two sizes only. Awaiting review.
- [x] Copilot "the desk" (6b4d247a). Our own design: one errand at a time with its goal and a track of steps; the conversation in large airy letters; everything behind a reply folded into one "What it did" receipt; the one decision it needs sits where you type; helpers, reports, changes, terminal and browser in a drawer; errands grouped by needs you, working, earlier. Base text 15px to 17px with a Standard, Large, Larger choice in Settings, Appearance. Built in about ten minutes, no options step, no click-through journey; screenshots caught two bugs (a doubled question card, art showing through). Terminal and browser in the drawer are still the demo echo and an iframe. Awaiting review.
- [x] Settings regroup (56036fcc). Sections for exchange accounts, servers, connections (providers, MCP), copilots, mini apps and safety. Committed without a visual check.
- [x] Fixes (8ef175ad). Settings checked with screenshots at 1600 and 1280 wide: no overflow, no console errors; its cards now sit on a solid backing over the art. Pixel font sizes (9 to 17px) replaced with rem so the Text size setting scales them. New-errand screen has no greeting: errands waiting on you, then templates. Blank errands no longer pile up under Earlier; New errand reuses a blank one. Model providers: Claude through your plan (CLI), Anthropic API, OpenAI, Gemini, OpenRouter, local (demo, no calls).
- [ ] Next: present the desk to him and take his verdict; check Home and Settings against the rulings; then Mini apps, the start-up screen, day one with no demo data.
- [x] Pod cards (6a50bc28): the sparkline had no size and drew over the equity figure on Home and Portfolio; fixed.

### 2026-10-04, later: Mini apps pass 1 (awaiting operator review)

Design intent (our own): judge an app the way you judge a pod, by what it can touch and how far it has got on its road to live, never by how it was built.

- [x] New rail place **Apps** (/apps). Bands: Live, Proving itself (tests, sandbox on recorded data, shadow run on live data nothing uses), Being built. Each card: health dot, risk class (Shows things / Runs work / Touches money), a five-step track and one line on where it stands. A tripped app sorts first with a red border.
- [x] Detail pane per app: risk class and its go-live rule; "It stopped itself" with Restart and Ask the copilot why when the circuit breaker trips; road to live with what each step proved (evidence, not logs); what it gives you, what it feeds, its schedule; its box (where it runs, budget used today, network allow-list, circuit breaker, operations it may call); last log lines; Open it / Run now / Pause / Ask the copilot / Remove.
- [x] Eight demo apps covering every case: news and sentiment, a screener, a weekend watcher (headless), exchange status (tripped), market mood (shadow run), whale alerts (sandbox), a DCA proposer (touches money, failing tests), a correlation map (built overnight).
- [x] New app: describe it to the copilot, make it from widgets (pick Home and Portfolio widgets, name it, it opens at once on the tile board and starts at Build), or one of eight templates.
- [x] An app's own screen (/apps/<id>) on the same tile board, with Edit layout and + Widget; "Not live yet" banner until it reaches Live.
- [x] Safe mode on the Apps screen and in Settings share one switch; Settings, Mini apps now reads the same list. Research demo app retired.
- [x] Checked by click-through at 1600 and 1280 (select, tripped app, money app, make from widgets, open app, Settings): no overflow, no console errors.
- [ ] Not done: Lab panels as widgets; opened apps on the rail; extensions (in-app code) as a third kind; real runs, logs and evidence (backend, contract sections 4-6).


### 2026-10-14: stale fixes after the pause (R1, R2, R4, R10)

- [x] No copilot modes (d40b1135). Ask / Plan / Do is gone from the desk composer and from Settings, Copilots. The composer chip now says what the copilot may touch and who answers. Skills stay on "/".
- [x] CFDs plus crypto in the demo data (c2cebd0e). One list of markets (EURUSD, GBPUSD, USDJPY, XAUUSD, US500, NAS100, USOIL, BTC, ETH, SOL) feeds the Home ticker, Markets, Portfolio prices and Library bot summaries. Portfolio adds an IC Markets live and demo account with margin, a London server, and two pods: Gold & indices (live) and FX majors (paper). Library has a full Gold scalper page. Lab sweeps and datasets cover CFDs. Apps: Whale alerts became a Spread watcher, plus a new Economic calendar watcher.
- [x] Settings (2ad4f3fd). Exchanges is now Brokers and accounts: cTrader at IC Markets beside the CCXT exchanges, several accounts each, keys still in the credential store. A cTrader MCP is on for every copilot. Data and sources lists Firecrawl as paid and off until he approves; "Free sources only" is gone.
- [x] Wording (7abbe89a, fa57571d). Pods, not Books (sizing names "Classic Book" and "Book + BMS" kept). Trading servers, not the node. "The agent engine", not LangGraph. MiniAppShell deleted (fc6e9f84).
- [x] Portfolio header (0040e7a6). With four servers the header spilled at 1280 and 1600, so the server chips fold into one "Servers" chip below 1800 wide. News opens on All.
- [x] Checked by a scripted click-through at 1600 and 1280: desk send, Settings (brokers, MCP, data, copilots), Portfolio, Home, Apps, the Gold scalper page. No overflow. One console 404 on the Library list: the dev-only MQL5 article route, which the preview server does not have. Screenshots: `workroom/ui-review-2026-10-01/2026-10-14-stale-fixes/`.
- [ ] Not done: Lab pods (`lab/pods.ts`) stay crypto until the risk redesign (R5). The Markets panel has no broker or account filter yet (triage item 13).
