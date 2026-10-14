# QMX UI design rules

Apply these to every screen and panel. Each rule names the building block that enforces it. If a rule and a screen disagree, the screen is the bug.

## 1. Word budget

- A panel shows a title, numbers and controls. Nothing else is required.
- At most one short subtitle line per panel or page (about eight words). Example: `3 bots · 2022–2025`.
- Explanations go behind an `InfoTip` ("i") next to the thing they explain. Never put a paragraph or a caption sentence on the screen.
- Empty states are one line plus the action that fills them. Example: `No pods ticked` and a `Tick pods` button.
- A screen with prose and nothing to click is a bug.

## 2. Every block is data or an action

- If a setting is described, it is editable right there (switch, slider, select, input).
- A notice that only says "this needs the backend" belongs in the `DemoChip` note or the action's toast, not in the layout.

## 3. Spacing

One scale, named in `src/app.css` (`@theme`). Use the names, not raw numbers, for these four jobs:

| Use                               | Class                   | Size     |
| --------------------------------- | ----------------------- | -------- |
| Table and list rows               | `py-row`, `gap-row`     | 0.375rem |
| Between tiles on a board          | `gap-tile`, `p-tile`    | 0.375rem |
| Inside a panel (padding)          | `p-panel`, `px-panel`   | 1rem     |
| Between groups in a panel or page | `gap-group`, `mt-group` | 1.5rem   |
| Page margins (non-board pages)    | `px-page`, `py-page`    | 2rem     |

Space separates groups; borders do not. Give groups room (`gap-group`). Keep data tables tight (`py-row`). All sizes are rem, so the Text size setting scales them.

## 4. Data density

- Many rows: a table or list with aligned columns. Numbers use `.num` (monospaced, tabular, never wraps) and are right-aligned.
- Cards only for things you own and act on: a pod, an app, an account. Never cards for rows of figures.
- Tabs only to switch views of the same thing. Never tabs inside tabs. Different things get different panels.
- A segmented toggle (two or three options) is fine inside a panel header for a mode of the same data.

## 5. Panel size modes

Every tile tells its panel its size. Read it with `panelSize()`:

| Mode       | When                                       | Show                                                                                                                     |
| ---------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `compact`  | tile under 24rem wide or 13rem tall        | One headline number, a sparkline, a status. No controls beyond a toggle.                                                 |
| `regular`  | normal tile                                | The working view: the chart or table, the key figures, the main toggle. Secondary controls behind one button or popover. |
| `expanded` | tile maximised, or at least 56rem by 30rem | Full controls laid out in the open.                                                                                      |

Never squeeze the full detail into compact. Hide it.

## 6. Demo labelling

- One `DemoChip` beside the page title. It says "Demo" and opens one line on what is sample data.
- No full-width demo banners. No "(demo)" suffix on every label.
- A real limit (for example "needs the daemon") is said once, where the user acts, in the toast.

## 7. Standing rules

- Base text is 17px. Sizes are rem only, never px, so the Text size setting works.
- Our own design. The Bloomberg terminal is a reference for density, not a look to copy.
- Everything is editable: defaults exist, the user can add, remove and change them.

## Building blocks

| Block               | Path                                         | Use                                                                                                             |
| ------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| InfoTip             | `src/lib/workbench/InfoTip.svelte`           | `<InfoTip label="Explain the colours" text="Colour is how much of the room to the kill line a crisis used." />` |
| DemoChip            | `src/lib/workbench/DemoChip.svelte`          | `<DemoChip note="Sample runs and machines. Nothing here ran." />` after the page `h1`                           |
| Panel size (script) | `src/lib/workbench/tiles/panel-size.ts`      | `const size = panelSize();` then `{#if size.mode === "compact"}`                                                |
| Panel size (CSS)    | set by `PanelBody.svelte` on every tile body | `class="group-data-[size=compact]/panel:hidden"`                                                                |
| Popover             | `src/lib/components/ui/popover`              | Secondary controls in regular mode: `<Popover.Root>`, `<Popover.Trigger>`, `<Popover.Content>`                  |
| Sparkline           | `src/lib/demo/Sparkline.svelte`              | Compact summaries: `<Sparkline values={curve} class="h-8 w-full" />`                                            |

Worked example: `src/lib/lab/panels/PodEquityPanel.svelte` (Lab, Pods, Test).
