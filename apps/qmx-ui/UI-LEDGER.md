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
