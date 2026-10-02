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
| 2 | Portfolio: books, risk, position sizing, promotions and approvals (new permanent section; portfolio optimisation is new scope) | queued |
| 3 | Trading nodes: node manager (servers, provider, region, IP, latency, kill) and the node screen (tile borders for paper/live, order flow) | queued |
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
| L4 | Lab shell and navigation: one rail entry, old Authoring / Backtest / ML entries folded in, links redirected | — |
| L5 | Build: node editor rethink (readable over the background, specific copilot), code mode, import a model built elsewhere | — |
| L6 | Test: runs, scenario generator (pairs × timeframes × pair trading), robustness, compare | — |
| L7 | Train: ML datasets, features, split/leakage, models, plug into slots | — |
| L8 | Data and compute: datasets, features, presets as reusable items; where it runs (local, Colab, GPU provider) | — |
| L9 | Lab copilot: its own tools, targets and attach sources; multiple sessions with history | — |
| L10 | Click-through journeys and fixes | — |
| L11 | Backend mapping for Codex; gaps flagged as new scope | — |

## Rulings for the Lab (2026-10-02)

- Layout C (tiling, saved layouts, linked panels, minimise docks and others reflow) with A as the Build layout and B as the Test/Compare layout. Operator: "surprise me" latitude.
- Name it **Lab**. Docs list Authoring on the rail (DEC-0470); the rename and the backend refactor go to Codex/docs.
- Customisability is paramount: every part has defaults but can be added, removed, edited or rebuilt (model slots for entry, sizing, regime, risk throttle included). Docs lag the vision; design for the vision and flag gaps.
- Any compute provider (own machines, remote hosts, Colab, AWS, GPU providers). Each run shows where it ran; off-machine work is visibly marked. Evidence status per run follows the docs (B-9) and is shown, not hidden.
- Agents and sub-agent swarms inside workflows must be visible, including where they run.

## Log

- 2026-10-02: ledger created. Round 6 feedback recorded in `UI-BACKLOG.md`. Library back arrow fixed (`a5babae3`). L1 research started.
- 2026-10-02: L1 done (docs brief: 17 gaps; reference patterns). L2 shown. L3 ruled (see above).
