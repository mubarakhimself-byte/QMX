> **Overridden (operator, 2026-11-10):** this report's "keep it" verdict does not stand. The October UI was a design proposal, never the product. Read this as a description of what exists, not as advice.

# 05 UI codebase grounding (ui-review/repair, read 2026-11-10)

Read-only grounding for planning the real, wired QMX desktop UI. Nothing was built, run or installed.
Code: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui` (branch `ui-review/repair`,
last commit `eea09941` 2026-10-14). Paths below are relative to that folder unless absolute.

Uncommitted on top of `eea09941`: `src/routes/usage/+page.svelte` (290 lines), `src/lib/usage/demo.ts` (143),
`src/lib/workbench/PlatformRail.svelte` and `src/lib/workbench/destinations.ts` (Usage button at the rail foot,
+19 lines), and `plan-2026-11/`.

---

## 1. Stack and tooling

| Item | Value | Where |
|---|---|---|
| Framework | SvelteKit 2.70.3, Svelte 5.57.1 (runes everywhere, `.svelte.ts` stores) | `package.json` |
| Adapter | `@sveltejs/adapter-static` 3.0.10, `fallback: "200.html"`, `strict: true`. `ssr = false`, `prerender = true` in the root layout: a static SPA. | `svelte.config.js`, `src/routes/+layout.ts` |
| Build quirk | `kit.version.name` runs `git rev-parse HEAD` at config time: the build needs git on PATH and a git checkout. | `svelte.config.js` |
| Assets dir | `kit.files.assets = "public"`; `static/200.html` is a leftover "story 66.1" marker file, not served. | `svelte.config.js`, `static/200.html` |
| Bundler | Vite 8.3.0, `@tailwindcss/vite` 4.3.3, Reticle vite plugin (dev inspection), and a dev-only `/__demo/mql5/<id>` middleware that serves MQL5 articles from `QMX_DEMO_MQL5_DIR`. | `vite.config.ts` |
| Ports | dev 5173, preview 4173, both `127.0.0.1` strict; config asserts it never binds 8765 (old daemon port). The host now defaults to 8766 and expects UI origin 5173 (grounding 01). | `vite.config.ts`, `src/app.html` |
| Tailwind | v4.3.3, CSS-first: no `tailwind.config.*`. `@theme inline` blocks in `src/app.css` and `src/lib/tokens.css`; `@custom-variant dark (&:is(.dark *))`; `tw-animate-css` 1.4.0. Named spacing tokens `row/tile/panel/group/page`. | `src/app.css`, `src/lib/tokens.css` |
| shadcn-svelte | CLI 1.7.0, `style: "rhea"`, base colour neutral, icon library lucide. The preset code `b27GcrRo` is not stored in `components.json`; it was applied by `init --preset b27GcrRo --reinstall` in commit `ff48dac1` (see `plan-2026-11/grounding/04-earlier-design-method.md:176`). Rhea shows in the parts (e.g. `rounded-2xl` buttons). | `components.json`, `src/lib/components/ui/button/button.svelte` |
| Class merge | `cn` 0.4.0 (shadcn's compiled clsx + tailwind-merge drop-in) instead of the usual `clsx` + `twMerge`; `tailwind-merge` and `tailwind-variants` 3.3.1 also present. | `src/lib/utils.ts` |
| Headless | bits-ui 2.19.3, paneforge 1.0.2 (shadcn Resizable) | `package.json` |
| Icons | `@lucide/svelte` 1.49.0, per-icon imports | everywhere |
| Charts | `lightweight-charts` 5.2.1 (one component, `src/lib/demo/CandleChart.svelte`); all other charts are hand-drawn SVG via `src/lib/qmx/charts.ts` (`extent`, `linePath`, `equityWalk`). | |
| Editor | CodeMirror 6 (`codemirror` 6.0.2, `@codemirror/lang-python`) in `src/lib/qmx/CodeEditor.svelte`, used by the Lab editor and inspector panels. | |
| Graph | `@xyflow/svelte` 1.6.6 for the Lab workflow canvas (`src/lib/lab/panels/EditorPanel.svelte`, `src/lib/demo/StepNode.svelte`, `src/lib/demo/workflow.ts`). | |
| Markdown | `marked` 18 + `dompurify` 3 for Library articles. | `src/lib/qmx/article.ts`, `src/routes/library/article/[id]/+page.svelte` |
| Fonts | Inter Variable and JetBrains Mono Variable via fontsource (bundled, offline-safe). | `src/app.css` |
| Unit tests | Vitest 5.0.2, `src/**/*.test.ts`, node environment (no DOM/component tests). 14 files, 57 cases. | `vite.config.ts` |
| E2E | Playwright 1.63.0, one spec `tests/day-one.spec.ts` (11 tests, demo-off journeys). Its webServer runs `pnpm run build && pnpm run preview`. `test-results/.last-run.json` says passed (Oct 14). | `playwright.config.ts` |
| Lint/format | ESLint 9 flat config with `eslint-plugin-svelte` + typescript-eslint parser (no TS rule set enabled, only svelte recommended); Prettier 3 + svelte plugin. `svelte-check` 4.7.6 via `pnpm check`. | `eslint.config.js`, `prettier.config.js` |
| Scripts | `dev`, `build`, `preview`, `check`, `lint`, `format`, `test`, `test:e2e`, `test:reticle`, `test:reticle:runner`; plus screenshot scripts `scripts/day-one-shots.mjs`, `scripts/day-one-boards-shots.mjs`. | `package.json`, `scripts/` |
| Package manager | pnpm 10.18.3 (`packageManager`), lockfile present, `node_modules` installed (Oct 1). | |
| Node pin | `engines.node ">=22.12.0 <23.0.0"`, but `.npmrc` has `engine-strict=false`, so on the machine's Node 24.18.0 pnpm only warns. Vite 8 and Kit 2.70 support Node 24. The pin should be widened (or a `.nvmrc` added) rather than obeyed. | `package.json`, `.npmrc` |

**Does it build?** From config and artefacts: yes as of 2026-10-14. `build/` holds a full prerendered output dated
Oct 14 17:46 (`200.html`, `index.html`, one `.html` per route, `_app/`), and the last Playwright run, which builds
first, passed. The uncommitted Usage route postdates that build and is unverified. Nothing in the config blocks a
build on Node 24 apart from the engines warning.

---

## 2. Structure

Totals: about 34,900 lines of own code and CSS in 200 files (139 `.svelte`, 57 `.ts`, 14 tests, 3 CSS), plus 88
shadcn files (2,027 lines).

### Routes (`src/routes/`)

| Route | Lines | What it is |
|---|---|---|
| `+layout.svelte` | 150 | Shell: platform rail, status bar, ink background art, start-up animation, toast notice, view-transition cross-fades; applies theme/surface/custom-theme classes and CSS vars on `<html>`; `?demo=on/off` switch. |
| `/` (`+page.svelte`) | 23 | Redirects to the start screen chosen in Settings (Home by default). |
| `/home` | 325 | Tiled board (layouts Today, Markets, Research): Needs you, Going, Markets, Screener, Calendar, Recent, Pinned, plus Portfolio panels. Get-started steps when demo is off. |
| `/copilot` | 253 | Main copilot: sessions sidebar, thread of typed blocks, work area, composer, panels drawn from specs (`SpecView`). Scripted replies. |
| `/library` | 1,071 | Library shelves (bots, models, pods, blocks, workflows, apps, templates, reports, paper, scenarios, setups, datasets, files, articles), collections, feed, MQL5 article index. Largest single file. |
| `/library/[id]` | 431 | One Library item page (inspector, connections map). |
| `/library/article/[id]` | 224 | Article reader (marked + DOMPurify), duplicates the parsing in `lib/qmx/article.ts`. |
| `/lab` | 452 | Tiled bench. Strategies bench: Build, Test, Train, Compare layouts; Pods bench: Design, Test, Paper. Machine picker, Lab side copilot. |
| `/portfolio` | 310 | Tiled board: Overview, Pods, Live, Road to live, MIS layouts; servers strip, kill switch, Portfolio side copilot. |
| `/apps` | 299 | Mini-app gallery: status, risk, templates, "make an app from widgets". |
| `/apps/[id]` | 148 | One mini app shown as a tile board of widgets. |
| `/settings` | 496 | Tabs: General, Appearance, Brokers and accounts, Models and tools, Servers and data, Copilots, Mini apps, Safety, Developer (demo toggle, link to Gallery). |
| `/usage` (uncommitted) | 290 | Plan meters, key spend, model routing (moved out of Settings on 11-09). |
| `/gallery` | 233 | Developer page: the component catalog (`lib/qmx/catalog.ts`) with live examples. Reached from Settings, Developer. |
| `/trade`, `/authoring`, `/apps/demo-lab`, `/apps/demo-ml` | 13 each | Redirect stubs for old links (to Portfolio Live and Lab layouts). |

Rail destinations (`src/lib/workbench/destinations.ts`): Home, Copilot, Library, Lab, Portfolio, Apps above the
divider; Usage and Settings at the foot.

### `src/lib/` folders

| Folder | Files | Lines | Purpose |
|---|---|---|---|
| `components/ui/` | 88 | 2,027 | shadcn parts (section 3). |
| `workbench/` | 30 | 3,364 | Shell and shared building blocks: rail, status bar, stores, themes/art/look, composer, copilot column, InfoTip, DemoChip, Segmented, day-one rules. |
| `workbench/tiles/` | 7 | 906 | Tiling engine: tree model, TileBoard, PanelBody, panel size modes, layout store. |
| `qmx/` | 12 | 1,183 | Generic data parts: DataTable, EntityCard, LineChart, TickerTape, RunConsole, CoverArt, CodeEditor; `catalog.ts` (component catalog); `charts.ts`; `article.ts`; `entities.ts`. |
| `sdk/` | 4 | 398 | Mini-app/copilot panel specs: `spec.ts` (json-render-style `{root, elements}` + `validate`), `SpecView.svelte` (draws a spec), `pinned.svelte.ts`. |
| `demo/` | 10 | 1,771 | Shared sample data (markets, assets, feeds, candles, workflow graph) plus three parts that live here by accident: `CandleChart`, `Sparkline`, `StepNode`; and `sizing-math.ts` (browser "what if" maths). |
| `home/` (+`panels/`) | 10 | 1,066 | Home store, panel catalog, needs, get-started, 6 panels. |
| `lab/` (+`panels/`) | 47 | 8,128 | Lab store and layouts, pod model (browser maths), dialogs, 29 panels, `demo.ts` (543), `pods.ts` (824). |
| `portfolio/` (+`panels/`) | 26 | 4,634 | Portfolio store, kill switch, pod simulation, 15 panels, `demo.ts` (1,076, largest file). |
| `copilot/` | 10 | 2,392 | Copilot session store (scripted responder), thread, work area, sidebar, `demo.ts` (755). |
| `library/` | 8 | 1,541 | Library items (`items.ts`, 885), cards, inspector, picker, connections map. |
| `apps/` | 8 | 1,434 | Mini-app store `apps.svelte.ts` (864, of which ~440 lines are demo apps), tiles, about sheet. |
| `settings/` | 12 | 2,239 | Settings store `settings.svelte.ts` (522) and one component per section. |
| `usage/` | 1 | 143 | Usage demo data (uncommitted). |
| `hooks/` | 0 | 0 | Empty (shadcn alias only). |
| `tokens.css`, `themes.css`, `utils.ts` | 3 | 577 | Tokens, themes, `cn`. |

Repo docs beside the code: `DESIGN-RULES.md`, `UI-LEDGER.md` (53 KB), `UI-BACKLOG.md` (86 KB),
`BACKEND-REQUIREMENTS.md` (22 KB, Oct 4), `handoff/MINI-APPS-AND-COPILOT-CONTRACT.md`.

---

## 3. Component library

### shadcn parts present (18)

badge, button, card, dialog, dropdown-menu, input, kbd, popover, resizable, scroll-area, select, separator,
skeleton, slider, switch, tabs, textarea, tooltip.

Import counts across own code: button 60, dropdown-menu 23, input 19, switch 14, dialog 11, popover 8, slider 7,
resizable 5, tooltip 4, badge 3, skeleton 3, select/tabs/textarea 1 each. **Unused: card, kbd, scroll-area,
separator.** Missing parts a real app will want: sheet, sidebar, table, command (palette), checkbox, radio-group,
toggle-group, label/form, alert, sonner (toasts), avatar, chart.

Screens often bypass the parts: 118 raw `<button>`, 16 raw `<input>`, 12 native `<select>` (styled globally in
`themes.css`), 17 hand-written `<table>`s, against 211 `<Button>`.

### QMX's own building blocks

Generic and reusable (keep):

| Part | File | Use count | Notes |
|---|---|---|---|
| Tiling engine | `src/lib/workbench/tiles/tiles.ts` (256) | core of 4 screens | Pure tree functions: `visibleTree`, `removePane`, `swapPanels`, `addPane`, `setSizes`, `parseLayouts`. Tested (`tiles.test.ts`). The most valuable code in the app. |
| TileBoard | `src/lib/workbench/tiles/TileBoard.svelte` (374) | Home, Lab, Portfolio, Apps/[id] | Resizable splits (paneforge), dock/minimise, maximise, drag-to-swap, link groups (violet/amber/teal), edit mode, unknown-panel fallback, day-one collapse to a welcome. |
| PanelBody + panelSize | `tiles/PanelBody.svelte`, `tiles/panel-size.ts` | every tiled panel (via context) | Measures the tile, gives `compact/regular/expanded` (rem thresholds) via `panelSize()` and `data-size` for CSS. |
| LayoutStore | `tiles/store.svelte.ts` | Home, Portfolio, Apps | Built-in + user layouts in localStorage, edit/reset/save-as. The Lab keeps its own copy in `lab/lab.svelte.ts` (duplicate). |
| InfoTip | `workbench/InfoTip.svelte` | 35 files | The one place explanations live. |
| PanelSummary | `workbench/PanelSummary.svelte` | 24 | Compact-mode summary line. |
| EnvChip | `lab/EnvChip.svelte` | 15 | Where a job runs. |
| DemoChip | `workbench/DemoChip.svelte` | 9 | The single "Demo" label per screen. |
| Segmented | `workbench/Segmented.svelte` | 9 | Radio-group mode switch. |
| Sparkline, LineChart | `demo/Sparkline.svelte`, `qmx/LineChart.svelte` | 8, 5 | Pure SVG; theme via CSS vars. |
| EmptyState, FirstStep, BoardWelcome | `workbench/` | 4, 3, 4 | Day-one states. |
| Composer, CopilotColumn | `workbench/Composer.svelte`, `CopilotColumn.svelte` | 3, 2 | Composer with model/tool/target picks; side copilot column for Lab and Portfolio. |
| SpecView + spec.ts | `sdk/` | 4 | Draws a validated panel description from a closed catalog (Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button). This is the seed of copilot-composed mini-app panels. Tested. |
| CodeEditor, CandleChart, EntityCard, TickerTape, RunConsole, CoverArt | `qmx/`, `demo/` | 2-4 each | Reusable, small. |
| Settings primitives | `settings/Group.svelte`, `Row.svelte`, `Choice.svelte` | 7, 4, 6 | Settings-page layout parts. |
| Look and art | `workbench/look.ts`, `workbench/art.ts` (434), `InkBackground.svelte`, `LookSettings.svelte` | shell | Surfaces, custom theme, generated SVG background art with presets and rotation. Tested. |

Two catalogs exist and do not meet:

- `src/lib/qmx/catalog.ts` (`CATALOG`, 14 entries: WidgetFrame, StatTile, DataTable, CandleChart, Sparkline,
  EntityCard, LineChart, TickerTape, RunConsole, EmptyState, Composer, ...): descriptions written for a model's
  `build_app` tool. Only `/gallery` reads it.
- `src/lib/sdk/spec.ts` (`SPEC_CATALOG`, 10 types): what `SpecView` actually draws for the copilot.

Gallery-only parts (built for the catalog, not used by screens): `WidgetFrame.svelte` (167, readable states
ready/loading/empty/unavailable/failed/reconnecting/stale/unknown — worth reviving as the real panel state frame),
`StatTile.svelte`, `DataTable.svelte`. Dead: `src/lib/workbench/board.svelte.ts` (`WidgetBoard`, 84 lines, no
importers; superseded by TileBoard).

Screen-specific (rewrite freely when wiring): the 29 Lab panels, 15 Portfolio panels, 6 Home panels, Settings
sections, Library/Apps components, copilot Thread/WorkArea. Panel registries are three parallel catalogs with
the same shape (`HOME_PANELS`, `lab/catalog.ts`, `PORTFOLIO_PANELS`), each entry `{title, icon, note, view:
Component<any>}`; panels take no data props.

---

## 4. State and data

**Stores** (Svelte 5 classes with `$state`, module singletons): `workbench` (`workbench/workbench.svelte.ts`:
theme, surface, art, text size, model/tool picks, demo mode, connection state, notices, copilot refs), `settings`
(`settings/settings.svelte.ts`), `lab`, `home`, `portfolio`, `apps`, `copilot` (`copilot/store.svelte.ts`),
`pinned`, plus `pod-model.svelte.ts`, `pod-sim.svelte.ts`, `kill.svelte.ts`, `aim.svelte.ts`. Everything that
persists goes to `localStorage` under about 25 `qmx.*` keys (settings, layouts, theme, art, demo flag, pinned
panels, library view), each read defensively.

**Demo data** lives in about 6,200 lines: `lib/demo/*` (shared), `lib/{lab,portfolio,copilot,usage}/demo.ts`,
`lib/lab/pods.ts`, `lib/library/items.ts`, and the `DEMO` array inside `lib/apps/apps.svelte.ts`. Plus
`public/demo/mql5-articles.json` (200 KB). Some screens also compute numbers in the browser
(`demo/sizing-math.ts`, `lab/pod-model.svelte.ts`, `portfolio/pod-sim.svelte.ts`, Math.random walks in
`demo/data.ts`, `qmx/charts.ts`).

**Demo mode**: `workbench.demoMode`, default on, remembered in `localStorage["qmx.demo"]`, switched by
`?demo=on|off` on any URL or the Developer tab in Settings. It is checked in 22 files (55 sites). With it off,
`TileBoard` hides every panel listed in `DAY_ONE` (`workbench/day-one.ts`) and shows the board's welcome; stores
filter demo rows out (copilot sessions, apps); settings sections show empty lists. Note the rule is binary:
`isEmptyPanel = !demo && panel in DAY_ONE`, so with demo off every panel is "empty" regardless of data. Wiring
must replace that with "this panel's query returned nothing".

**Backend client: none.** No fetch wrapper, no SSE, no WebSocket, no auth/bearer handling, no types for host
routes. The only `fetch` calls read demo files (`/demo/mql5-articles.json`, dev-only `/__demo/mql5/<id>`).
`workbench.connection` is a `ConnectionState` union fixed at `"not-bound"` and shown in the status bar.
Comments name intended routes (`usage/demo.ts` mentions `GET /api/usage`, `/api/settings/roles`) but nothing
calls them. The copilot `Block` union (`copilot/demo.ts`: user, text, panel, plan, agents, tools, changes,
artifact, table, cards, ask, permission, handoff) is the closest thing to a wire contract and is a good
starting point for typing the agent SSE stream.

**How hard is a real data layer?** Medium, and mostly mechanical. About 60 components import demo constants
directly at module level (e.g. `home/panels/MarketsPanel.svelte` imports `MARKETS` and `ACCOUNTS`), so data
reaches panels by import, not by props or a query. The work is:

1. Add one client module (`lib/api/`): base URL + bearer from the desktop shell, typed REST calls, one SSE
   reader with reconnect, connection state feeding `workbench.connection`.
2. Per domain, put a small resource store between panels and data (`{status, data, error}` mapping to the
   WidgetFrame states), with the demo module as one source and the host as the other. Then change each panel's
   import to the store. The panels' markup can mostly stay.
3. Move settings and layouts that the host owns out of localStorage.
4. Delete the browser maths that the backend now computes (pod simulation, sizing) or keep it only for
   "what if" previews.

Grounding 01 says the host is REST + SSE with one bearer and no WebSocket, which fits this shape.

---

## 5. Themes

- Mechanism: CSS custom properties. Base shadcn tokens in `src/app.css` and again in `src/lib/tokens.css`
  (`:root` light + `.dark`), Tailwind colours mapped through `@theme inline`. Seven named themes in
  `src/lib/themes.css` as `.dark.theme-<name>` (or `:root.theme-paper`) overriding the tokens, plus QMX extras
  `--panel`, `--glow`, `--ink`, `--info`, `--success`, `--warning`. The root layout puts `theme-<name>`,
  `surface-<id>`, `glass` and `dark` classes on `<html>`, so portals inherit them.
- Themes (`THEMES` in `workbench/workbench.svelte.ts`): **ink** (default, gold), **cobalt**, **ember**,
  **graphite**, **moss**, **violet** (all dark), **paper** (the one light theme).
- Surfaces (`workbench/look.ts`): glass (default, backdrop blur), liquid glass, solid, brutalist.
- Custom theme: accent, background, panel opacity, radius, text size, written as inline CSS vars on `<html>`.
  Text size 15/17/19 px scales everything (rem-based spacing tokens).
- Background art: `workbench/art.ts` generates SVG scenes (fractal, contour, candles, halftone, liquidity) from a
  seed in the theme's `--ink` colour; 5 built-in presets, user presets, rotation per visit/hour/day. Trading
  surfaces opt out; `.solid-backing` and `.tile` keep data opaque over the art.
- Chart colours per theme (`--chart-1..5`):

| Theme | chart-1 | chart-2 | chart-3 | chart-4 | chart-5 |
|---|---|---|---|---|---|
| ink | #e0b062 | #9fd8d0 | #b7c48a | #d99a7a | #a99ad6 |
| cobalt | #7ee2ff | #7ef0c0 | #b4b9ff | #ffd27a | #ff8a9a |
| ember | #ff9a62 | #8fd6a0 | #ffd28a | #e88aa8 | #b0a0e0 |
| graphite | #9cc4ff | #6fd3a0 | #c7b3ff | #f0c46a | #f07f7f |
| moss | #b8e05c | #7fd8c8 | #e8d26a | #8fe0a0 | #f08a6a |
| violet | #c9a6ff | #8fd0ff | #ff8aa8 | #7fe0b8 | #ffd28a |
| paper | #2b55c7 | #1f8a52 | #b7791f | #c2412d | #7a4fc9 |

  Up/down colours come from `--success` / `--destructive` per theme. Link-group colours in `TileBoard.svelte`
  are hard-coded oklch, not tokens. `CandleChart.svelte` reads tokens once on mount (painting a pixel to convert
  oklch), so candles keep the old colours after a theme switch until the panel remounts.

---

## 6. Quality

**Good:** strict TypeScript, Svelte 5 idioms throughout, defensive parsing of everything from storage, pure
tested layout/look/art/spec logic, consistent design rules (`DESIGN-RULES.md`) visibly applied (InfoTip word
budget, DemoChip, day-one lines, `.num` tabular figures), reduced-motion respected, only 1 `@ts-expect-error`,
4 `any`, 0 TODO/FIXME. 48 `eslint-disable` lines, nearly all the `no-navigation-without-resolve` rule on
resolved paths with query strings.

**Debt and duplication:**

- Two token sets: `src/app.css` and `src/lib/tokens.css` both define `:root`/`.dark` and `@theme inline` with
  different values (radius 0.3rem vs 0.5rem, grey vs coloured chart ramps). Load order decides. Pick one.
- Theme list duplicated: names in `workbench.svelte.ts`, values in `themes.css`, swatch hex again in
  `routes/settings/+page.svelte` (~lines 105-140).
- Layout store duplicated: `lab/lab.svelte.ts` re-implements `tiles/store.svelte.ts`.
- Three parallel panel catalogs (Home, Lab, Portfolio) and two component catalogs (`qmx/catalog.ts` vs
  `sdk/spec.ts`).
- Markdown article parsing in both `lib/qmx/article.ts` and `routes/library/article/[id]/+page.svelte`.
- Reusable parts filed under `lib/demo/` (`CandleChart`, `Sparkline`, `StepNode`).
- Single-file tables: 17 hand-written `<table>`s while `DataTable` sits unused.

**Dead code:** `workbench/board.svelte.ts` (WidgetBoard); shadcn card/kbd/scroll-area/separator; empty
`lib/hooks/`; four redirect routes; `static/200.html` marker; `.reticle/flows/*.json` (4 flows targeting the
old stub's `factory-test-issuers` and bootstrap screens, which no longer exist) and the `test:reticle` scripts
that replay them; `public/health.json` stamps an old inspect SHA; `workbench.ts` exports `DEMO_APPS = []`,
`TARGETS` and `MODELS` that are fixed demo lists.

**Very large files:** `routes/library/+page.svelte` 1,071 (should be split into shelf components),
`portfolio/demo.ts` 1,076, `library/items.ts` 885, `apps/apps.svelte.ts` 864 (data mixed into the store),
`lab/pods.ts` 824, `copilot/demo.ts` 755, `demo/assets.ts` 680, `portfolio/panels/PodPanel.svelte` 497,
`routes/settings/+page.svelte` 496.

**Tests:** 57 unit cases cover pure logic only (tiles, panel size, look, art, day-one, destinations, spec
validation, catalog, settings parsing, sizing maths, pod model, apps, library items). No component tests, no
DOM environment. E2E is one spec (11 tests) on demo-off journeys; no tests for demo-on screens, themes, layout
editing beyond show/hide, or anything wired. Screenshot scripts exist for visual review, not assertions.

---

## 7. Verdict: keep and evolve (partial rebuild of the data seam only)

Keep the codebase. It is a modern, coherent stack (SvelteKit 2 static SPA, Svelte 5 runes, Tailwind 4,
shadcn-svelte Rhea, bits-ui) that builds and passed its own e2e on Oct 14, and the hard, reusable parts are
already good and tested. What is missing is not structure but a data layer, and the panels are thin enough
that wiring is a per-panel import swap plus states, not a rewrite.

Why not rebuild: a rebuild would redo the tiling engine, theme system, design rules and about 50 panels that the
operator has already reviewed screen by screen, to arrive at the same stack. The stale stub at
`D:/QMX-worktrees/engine-base-read/apps/qmx-ui` (engine/base) is not an alternative: it is the 2026-09-28
"story 66.1" scaffold (56 files, ~4,800 lines) with a factory-era `lib/host/wireClient.ts` that only records
calls (`recordingTransport`) against the old qma-wire/CT-40 names (`send_message`, `cancel_job`,
`list_mailbox`). The repair branch forked from the same base (merge-base `7b65732f`, 2026-09-27) and scrapped
that layer on 2026-10-01 (commit `0daa00ab`); nothing in it matches today's host routes, so neither branch has a
usable client and engine/base's copy should be replaced by this one.

Partly rebuild:

1. The data seam: a new `lib/api/` client (REST + SSE + bearer + connection state) and per-domain resource
   stores; demo data becomes one source behind the same stores instead of direct imports.
2. Day-one logic: from "demo off means empty" to "query returned nothing", using WidgetFrame's readable states.
3. Theme tokens: merge `app.css` and `tokens.css`, derive the settings swatches from one theme table, feed chart
   colours to lightweight-charts reactively.
4. One panel registry for all boards (and for mini-app panels), merging the two component catalogs.
5. Split `routes/library/+page.svelte`; move reusable parts out of `lib/demo/`; delete the dead code listed
   above; widen the Node engines pin.

Most valuable to keep, in order: the tiling engine (`lib/workbench/tiles/`), the theme/surface/art system
(`themes.css`, `look.ts`, `art.ts`, root layout), the spec renderer (`lib/sdk/`), the shell (rail, status bar,
composer, copilot column, InfoTip/DemoChip/Segmented/PanelSummary/EnvChip), the copilot block model
(`lib/copilot/demo.ts` types), and the day-one/first-run map (`workbench/day-one.ts`). Screen-specific panels are
worth keeping as design references and rewiring one by one; their demo data files can go once each panel has a
real source.
