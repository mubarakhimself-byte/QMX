# QMX UI backlog (operator feedback, 2026-10-01 round 5)

Branch `ui-review/repair`. Demo data only; backend wiring is Codex's (see BACKEND-REQUIREMENTS.md).
Order of work: **design system first**, then rebuild screens on it. Most problems below come from screens built one by one.

## 0. Foundation (do first)

- [x] One `MiniAppShell` for every mini app: name, views tabs, edit layout, copilot toggle, widget grid, optional app copilot. Research, Trade, Lab, ML Studio all use it.
- [x] Every widget uses `WidgetFrame` with the same controls: add to copilot, minimise, expand/return, close (edit mode), add widget.
- [x] Page layout primitives with spacing rules that hold at 1440, 1920 and 2560 wide (operator uses full-screen desktop). Fill width with denser grids; no big empty areas.
- [x] Fresh-install empty states must also fill the page sensibly (most things will be empty on day one).
- [x] More depth and personality across the app: an overlay/scrim under content so the ink background never fights charts or text.
- [x] Platform must absorb new mini apps / widgets without broken UI: unknown widget type or missing data renders a typed "unsupported" frame, never an error (backend + catalog).
- [ ] Component library: can the operator create new components? (decide: authoring components vs only composing catalog entries).
- [ ] Background art: multiple variants, savable.

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

- [x] Paper vs live: whole-frame border colour (paper orange, live blue), not just a badge.
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
