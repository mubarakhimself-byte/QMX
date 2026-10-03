# QMX UI backlog (operator feedback, 2026-10-01 round 5)

Branch `ui-review/repair`. Demo data only; backend wiring is Codex's (see BACKEND-REQUIREMENTS.md).
Order of work: **design system first**, then rebuild screens on it. Most problems below come from screens built one by one.

## Recovered from the transcript audit (2026-10-03)

An agent re-read every operator message in this session and checked it against these files. Rounds 1–4 (2026-10-01) were never written down; they are summarised here so a rebuild doesn't undo them.

### Built in rounds 1–4 (keep)

- Themed scrollbars; larger base text; no focus box on the composer; the composer grows with its text.
- Model picker in the composer; copilot pop-out window.
- Seven themes ("Plain" removed); frosted glass, neumorphic wells, ink background made trading-themed (fractals).
- Player cards for bots, models, apps and workflows with named measures and **no overall rating or tier** (QMB bans composite scores).
- Artifacts tab restored in the Library; headless-app operations on detail pages; ticker; Sydney/Tokyo clocks removed.

### Rulings (recorded now)

- Grok UI scrapped; the Excalidraw storyboard is the working spec. Web app first, desktop wrapper later; spacing judged at full-screen desktop (1920–2560).
- Build on shadcn-svelte (Rhea preset) and community components, not from scratch. Read docs/, _bmad-output and _docwork before work.
- Model selection lives in Settings, set per copilot.
- Research pipeline follows the current docs: hypothesis → graduate → QMB evidence → paper → promote → activate (WF1/WF2 only as labels).
- ML has a home in the UI (now the Lab) because models from papers should be usable anywhere: risk, sizing, MIS.
- Crypto is the design focus, with more than one broker or exchange per setup.
- The operator delegated chunking: "keep a ledger… I believe you are smart enough" (2026-10-02).
- Customisability ("Lego") applies to the **whole app**, not only the Lab.

### Needs the operator's confirmation

- [x] Ruled 2026-10-03: themes and background art stay everywhere, trading included. The real problem was see-through panels: charts, graph canvases and nodes now sit on solid backing.
- [x] Ruled 2026-10-03: compute providers (any VPS, AWS, Colab, GPU clouds) are added and removed by the operator; the backend adapts. Two kinds of work need placing: the copilot's own agents and swarms, and workflow agents from the node editor that run locally or on servers (long or always-on jobs). Storage buckets too. Evidence status of off-machine runs still open (UI shows "exploration only" until ruled).
- [x] Ruled 2026-10-03: keep the current rail and shell. "If I did not choose, it means surprise me; I haven't complained, so I'm okay with it."
- [x] Restated 2026-10-03: templates across the app (Lab most, then Portfolio, Library, Home); the operator will mostly start from templates rather than build from scratch.

### Missing items (now on the backlog)

- [x] Lab machine switch connects first and scopes the whole Lab; "nothing here" state per layout (done 2026-10-03, `5aee5513`).
- [x] Start something new: outside work, custom workflows and training start as a main-copilot conversation with question cards, then a guide strip drives the Lab layouts (done 2026-10-03).
- [ ] Genetic algorithms and other Lean-style experiment types in the Lab (dropped in the merge).
- [ ] Animations: a few purposeful ones (panel expand, run finishing, connect).
- [ ] Review the Minara reference site (never reviewed).
- [ ] alphaXiv link 2409.06289: use as the example item for the Sources feed.

### Details that were dropped (now on the backlog)

- [ ] Library: diagrams generated from articles (no AI, or a cheap model), not only key-point summaries.
- [ ] Sources: videos as a research source; any site can become an in-app web app (Omarchy-style).
- [ ] The copilot builds **whole mini apps and workflows** from the component library through skills, not only widgets.
- [ ] Resources tile also holds artifacts.
- [ ] Home tab previews link through to the full pages (Markets → Portfolio, Agents, main Copilot).
- [ ] Settings: each tab gets its own layout for its job, not the same card pattern everywhere.
- [ ] Headless mini apps and workflows: how they are presented and run from the UI.
- [ ] Stress-test the UI across many failure scenarios; the copilot inherits any inconsistency.

## Round 6 feedback (2026-10-02, operator walk-through, ~40 min dictation)

**Verdict:** visual design gets marks; layout, usability and intentionality are poor. Too much unused space, too many words and too little to do, screens rushed. **New way of working: one screen at a time**, done properly (options, then build, then click-through user journeys, then backend mapping), before moving on.

### Working method (operator ruling)
- [ ] One screen per pass. Each pass: study the job, 2–3 layout options, operator picks, build, then drive it like a user (click, drag, minimise, small window, many accounts, empty and overloaded states), then list what the backend must provide.
- [ ] Drive pages in the browser with intent, not only screenshots.
- [ ] Use the local design skills (frontend-design, design-system-compliance, verify-ui-change) on every pass.
- [ ] Settle the design system / layout rules (space management, density, text measure) so screens stop drifting.

### Structure (needs operator ruling)
- [ ] Proposal: one permanent **Lab** that merges Authoring, Backtest lab and ML Studio (all are "experiment, test, prove in paper, then live"). Some work needs a node editor, some code, some neither; bring in models built outside (Claude Code, Codex, ONNX). Add datasets, reports, tests, models and features as first-class items. External compute (Colab, GPU providers, external engines). StrategyQuant-style scenario generation: many pairs, timeframes, pair trading. Needs a deep design pass (subagent research allowed). Backend may need restructuring (Codex/docs ruling).
- [ ] Permanent rail destinations rather than mini apps: Lab, Portfolio (books, risk, position sizing, promotions/approvals live here), Trading node manager.

### Copilot and composer (all surfaces)
- [ ] Tools, Target, Attach and messaging differ per context (mini app, Lab, node). An app declares its own tools, targets and attach sources; some apps need no attachments.
- [ ] App copilot: multiple sessions with history, and its own settings (VS Code style header).
- [ ] Main copilot: session column must collapse on its own (keep Browser/Terminal/Diff open). Sub-agent preview missing.
- [ ] Show how a message looks with an attached document, a Library item, and a mini-app item.
- [ ] Copilot can create a new widget (JSON render, as in the storyboard): show the flow, and how it connects front to back.

### Widget grid (all boards)
- [ ] Minimise must reclaim space: minimised widgets dock to the bottom and the rest fill up (Bloomberg-style space management).
- [ ] Tiling quality (Markets view especially).
- [ ] Operator likes: Edit layout, add widget, the idea of copilot-built custom widgets; good layouts become templates.

### Home
- [ ] Add your own tabs (dashboard you build); current tabs are previews.
- [ ] Notifications area at the top for things needing attention.
- [ ] Drop the "Home" word in the header. Keep the ticker.
- [ ] "While you were away" too thin for many concurrent jobs (e.g. nine models training on a GPU provider).
- [ ] Many accounts across brokers/exchanges (Binance, Coinbase, Bybit, …); crypto can have more than one broker.
- [ ] News widget too thin; unused space below.
- [ ] Agents view leaves space unused.

### Trading node
- [ ] Paper/live colour on the tiles' borders, not the whole page frame.
- [ ] Order-flow views for charting (crypto venues provide it).
- [ ] Drop "Waiting for you"/promotion here; promotion belongs in Portfolio.
- [ ] Protection widget not needed.

### Authoring (until merged into Lab)
- [ ] Whole page needs a rethink: too compact; background makes editor, sidebars and bottom tabs hard to read.
- [ ] Copilot for the node editor should be specific to it.

### Library
- [ ] Reader wastes the right side on wide screens (text-heavy page): use the width.
- [ ] Sources: embedded browser fails inside QMX (sites refuse embedding); works outside. Scraping (e.g. Firecrawl) is a backend item.
- [ ] Artifacts tab: items don't open; needs a full rethink.
- [ ] Cards: operator loves them. Colour by family (e.g. scalper = blue and gold), or let the operator edit the card art as a preset. Add list view vs card view. ML models should look different from bots.
- [ ] Model detail page is poor (unused space, no function); app/workflow detail likewise. Summary cards are good.
- [x] Back arrow on a detail page returned to the Knowledge tab; now returns to the tab the item came from.

### Settings
- [ ] Every tab needs depth and things to do; too many words, nothing clickable.
- [ ] General: thin; use the space.
- [ ] Models/providers: will change (Claude CLI proxy for model providers).
- [ ] Trading nodes: a node is a VPS. Show server, provider, region, IP, latency, status, who uses it; kill it from here; paper and live may not be separate nodes.
- [ ] Data & sources: can't add anything. Sources need API keys, scraping workflows, cron schedules, use by mini apps.
- [ ] Appearance: fine; more variations welcome.

## 0. Foundation (do first)

- [x] One `MiniAppShell` for every mini app: name, views tabs, edit layout, copilot toggle, widget grid, optional app copilot. Research, Trade, Lab, ML Studio all use it.
- [x] Every widget uses `WidgetFrame` with the same controls: add to copilot, minimise, expand/return, close (edit mode), add widget.
- [x] Page layout primitives with spacing rules that hold at 1440, 1920 and 2560 wide (operator uses full-screen desktop). Fill width with denser grids; no big empty areas.
- [x] Fresh-install empty states must also fill the page sensibly (most things will be empty on day one).
- [x] More depth and personality across the app: an overlay/scrim under content so the ink background never fights charts or text.
- [x] Platform must absorb new mini apps / widgets without broken UI: unknown widget type or missing data renders a typed "unsupported" frame, never an error (backend + catalog).
- [ ] Component library: can the operator create new components? (decide: authoring components vs only composing catalog entries).
- [x] Background art: multiple variants, savable. Five styles (fractal, contours, candles, halftone, liquidity), density/strength/glow/variation, built-in and saved variants in Settings > Appearance; per machine.

## Home

- [x] Too much empty space; denser layout.
- [x] Live equity next to paper equity (accounts).
- [x] Strategy pipeline: scrollable and expandable columns; redesign.
- [x] News belongs on Home (not Library); richer news panel.
- [ ] Review dialog fine; consider richer approval flow.

## Copilot

- [x] Clicking a bot card in chat opens that exact version in the Library.
- [x] "Add to copilot" must visibly do something (chip + toast + jump).
- [ ] Target menu: keep, but think through failure cases later.
- [ ] Sub-agents and workflow agents visible (QMA: copilots, sub-agents, workflow agents e.g. quant research / analysis).

## Library (redesign; candidate for a dedicated pass)

- [x] Knowledge: go back to the three-pane layout (list | reader | side), not the card grid + separate page.
- [x] Sources: browser inside QMX (preview pane), not pop-up windows; same styling.
- [x] Entity detail: too much space; overlay instead of background; combine Evidence/Journal/Connections/Artifacts into fewer, denser views; Overview may merge.
- [ ] Apps & workflows: tighter layout.
- [ ] Saved configurations (test presets, model configs like two GBM configs, feature sets) — these are what "artifacts" were meant to be; maybe a different name. Backend addition.

## Authoring

- [ ] Minimap: removable or minimisable.
- [ ] Small window sizes break the editor.
- [ ] Palette = toolbox: saved test/model/feature configurations; add datasets.
- [ ] Show what happens while a step runs.

## Trading node

- [x] ~~Paper vs live: whole-frame border colour~~ Superseded 2026-10-02: the colour goes on the tile borders, not the whole frame (see Round 6, Trading node).
- [ ] Multiple nodes; latency test.
- [ ] Kill-switch authority (research docs).
- [ ] Book: risk management and position sizing — where it lives.
- [ ] Portfolio optimisation: a dedicated page (not a mini app).
- [x] Use the same widget components as Research.

## Backtest lab / experiments

- [x] Read docs on how experiments work across QMX; redesign accordingly.
- [x] StrategyQuant reference: what-if scenarios, editors, robustness.

## ML Studio

- [ ] Probably a workflow, not only a mini app (dataset→features→split… is a pipeline). Decide placement.
- [ ] "Model ideas from your Library" should be generated automatically (backend).
- [ ] Slots: models mostly for stress testing, MIS, risk, position sizing.

## Settings

- [ ] Data sources: add new ones (file upload: Excel/CSV, API providers).
- [ ] Inference providers page good; keep.

## Multi-screen

- [ ] Open views on multiple screens/windows.

## Reference: StrategyQuant X patterns to borrow (research 2026-10-01, public docs only)

- One skeleton for every experiment module: **Run / Settings / Results** tabs; live log + progress on Run.
- Results table ("databank") docked at the bottom with a detail pane for the selected row; saved column views; bounded top-N with dedupe of near-identical strategies.
- **What-if scenarios**: named, composable transforms of an existing trade list (no re-backtest), each with a baseline-relative pass rule ("≥ 80% of baseline"), shown as an overlay on the baseline equity curve.
- **Robustness checks tiered by cost** (fast → slow), sequential with early exit; cost estimate beside expensive tests; "run all anyway" switch for diagnostics.
- Monte Carlo: fan chart **plus** percentile table (80/90/95%); parameter perturbation as "probability changed" + "max % change".
- **Walk-forward matrix**: grid of runs × OOS% coloured pass/fail, click a cell to update the equity chart, cluster-pass rule (e.g. 7 of 9 in a 3×3 block); flat heatmap, not only 3D.
- Filters scoped to IS / OOS / robustness / portfolio slices.
- Portfolio: correlation matrix with selectable basis (daily/weekly/monthly; P&L or counts) and threshold colouring; sector caps.
- Task pipelines: vertical task list, each task with source/target result sets; conditional loop tasks (needs visible iteration counter + cap); shipped example pipelines; save/load a whole pipeline.
- Avoid: deep nested settings; locked features that look broken; research and portfolio split across products.
- Caution: QMB bans composite scores/ratings — a "fitness score" can only be a user-defined sort, never evidence.

## Reference: what the docs already rule (research 2026-10-01)

- **Agents (QMA)**: ontology Desk → Role → Quant → Agent → Subagent. Roles: Researcher, Trader, Developer, Analyst, PM ("Portfolio Manager"). Quants are persistent named actors with mailboxes; Agents are running instances; Subagents are leaves (no mailbox, no delegation, capabilities ≤ parent). Copilot = `psess:` product sessions (profiles authoring / app-use), not an Agent record. Workflow agents = Graph Template `agent` nodes pinned to a `worker_template`. Agents never touch the money path (no orders, sizing, bindings, kill switch). UI shows JobHandle states queued/running/done/failed/cancelled/aborted/**unknown (never shown as failed)**; approvals arrive as `approval_request` for the operator principal; closing UI never stops an agent.
- **Experiments**: CT-47 ExperimentSpec (fp1, code/config/data/env refs, seed, cost assumptions, lineage). Three lanes chosen by the door: ungoverned (`qmb.run()`, no ledger), governed (QMB ledger line + CT-32, "research-paper"), coordinated (QMA places runs under a spec; Experiment Ledger). "Project/workspace" are UX aliases only. One `qmb` run per environment; governor queues, never oversubscribes. Run roles confirmation/trial/replicate/aborted; verdict is a read-time fold. Compare must refuse when recipes, splits or completeness differ, or a run is unknown. Reopen = walk ExperimentSpec successors.
- **Kill switch**: KSA GREEN..BLACK; automatic escalation only; de-escalation is operator `resume` naming scope; scopes global and per (venue, account). Effects suspend_new | drain | flatten via UI-editable `registry:ksa_effect_matrix`. Kill line = per-Book capital floor (breach flattens and stands the Book down). Flatten authority: operator always; Book policy via pre-declared triggers; protection authority per matrix; never the adapter. Exits are never blocked. Node control = closed list of powers (resurrect, resume, resolve_unknown, flatten, escalate, paper flip/reset, promotion sign/activate, config_version_activate, seat_reinstate…), revalidated server-side and journaled. Show "requested" apart from "enforced"; read models carry authority source + source/receive time; no generic LIVE/PAPER toggle.
- **Books**: authority bot → Book → BMS → operator. Book owns admission, sizing, doors, leash, exits; BMS owns accounting, constraints, kill line, reporting. Sizing ladder in USD (book_capital, loss_floor, loss_runway, period_loss_budget, r_unit_price, position_risk_amount = requested_r × r_unit_price). Template sections: charter, footprint_requirements, money_rules, admission_bar, leash_grammar, capacity_and_sweep, exit_policy, control_policy, protection_windows, paper. UI edits mint a new version (branches-from), never mutate. Seat active|benched; Book mode LIVE|PAPER; binding live|paper|stood-down (three vocabularies). **No ratified portfolio-optimisation concept** — operator wants a dedicated page; flag as new scope.
- **Data sources**: all via CT-15 → CT-10; Dukascopy primary (personal use), news calendar, cTrader intended. CSV import = a CT-15 adapter (no Excel in docs). Upload = `PUT /artifacts/stage` (refuses while stage_max_bytes unset). Dataset node shows provider, coverage, schema, units, timezone, calendar, freshness, provenance, entitlement, revision; missing/denied/truncated distinct.
- **Unknown views/widgets**: PackUiRequest ingest drops bad views with typed diagnostics (unknown_pack_ui_schema, view_op_not_contributed, view_schema_drift…); unknown renderer → empty pane with visible reason, `failure_class=view`, pack stays enabled, other views mount, jobs untouched. Closed slots app-nav / canvas-widget / detail / copilot-panel / preview-tab; renderers native / json-render / mcp-app.
