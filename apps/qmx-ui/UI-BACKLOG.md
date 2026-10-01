# QMX UI backlog (operator feedback, 2026-10-01 round 5)

Branch `ui-review/repair`. Demo data only; backend wiring is Codex's (see BACKEND-REQUIREMENTS.md).
Order of work: **design system first**, then rebuild screens on it. Most problems below come from screens built one by one.

## 0. Foundation (do first)

- [ ] One `MiniAppShell` for every mini app: name, views tabs, edit layout, copilot toggle, widget grid, optional app copilot. Research, Trade, Lab, ML Studio all use it.
- [ ] Every widget uses `WidgetFrame` with the same controls: add to copilot, minimise, expand/return, close (edit mode), add widget.
- [ ] Page layout primitives with spacing rules that hold at 1440, 1920 and 2560 wide (operator uses full-screen desktop). Fill width with denser grids; no big empty areas.
- [ ] Fresh-install empty states must also fill the page sensibly (most things will be empty on day one).
- [ ] More depth and personality across the app: an overlay/scrim under content so the ink background never fights charts or text.
- [ ] Platform must absorb new mini apps / widgets without broken UI: unknown widget type or missing data renders a typed "unsupported" frame, never an error (backend + catalog).
- [ ] Component library: can the operator create new components? (decide: authoring components vs only composing catalog entries).
- [ ] Background art: multiple variants, savable.

## Home

- [ ] Too much empty space; denser layout.
- [ ] Live equity next to paper equity (accounts).
- [ ] Strategy pipeline: scrollable and expandable columns; redesign.
- [ ] News belongs on Home (not Library); richer news panel.
- [ ] Review dialog fine; consider richer approval flow.

## Copilot

- [ ] Clicking a bot card in chat opens that exact version in the Library.
- [ ] "Add to copilot" must visibly do something (chip + toast + jump).
- [ ] Target menu: keep, but think through failure cases later.
- [ ] Sub-agents and workflow agents visible (QMA: copilots, sub-agents, workflow agents e.g. quant research / analysis).

## Library (redesign; candidate for a dedicated pass)

- [ ] Knowledge: go back to the three-pane layout (list | reader | side), not the card grid + separate page.
- [ ] Sources: browser inside QMX (preview pane), not pop-up windows; same styling.
- [ ] Entity detail: too much space; overlay instead of background; combine Evidence/Journal/Connections/Artifacts into fewer, denser views; Overview may merge.
- [ ] Apps & workflows: tighter layout.
- [ ] Saved configurations (test presets, model configs like two GBM configs, feature sets) — these are what "artifacts" were meant to be; maybe a different name. Backend addition.

## Authoring

- [ ] Minimap: removable or minimisable.
- [ ] Small window sizes break the editor.
- [ ] Palette = toolbox: saved test/model/feature configurations; add datasets.
- [ ] Show what happens while a step runs.

## Trading node

- [ ] Paper vs live: whole-frame border colour (paper orange, live blue), not just a badge.
- [ ] Multiple nodes; latency test.
- [ ] Kill-switch authority (research docs).
- [ ] Book: risk management and position sizing — where it lives.
- [ ] Portfolio optimisation: a dedicated page (not a mini app).
- [ ] Use the same widget components as Research.

## Backtest lab / experiments

- [ ] Read docs on how experiments work across QMX; redesign accordingly.
- [ ] StrategyQuant reference: what-if scenarios, editors, robustness.

## ML Studio

- [ ] Probably a workflow, not only a mini app (dataset→features→split… is a pipeline). Decide placement.
- [ ] "Model ideas from your Library" should be generated automatically (backend).
- [ ] Slots: models mostly for stress testing, MIS, risk, position sizing.

## Settings

- [ ] Data sources: add new ones (file upload: Excel/CSV, API providers).
- [ ] Inference providers page good; keep.

## Multi-screen

- [ ] Open views on multiple screens/windows.
