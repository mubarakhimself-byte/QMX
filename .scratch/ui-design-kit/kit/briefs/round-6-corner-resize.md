# Round 6 builder: resize widgets from their corners, no bars between them

Written 2026-11-11 by the design lead. You are the only builder editing code. Read `round-2-shared.md` in this folder first (rules for every builder, the skills to invoke, how to check and report), then `../SPACE-RULES.md`, then this.

## Why

The owner accepted last night's sizing "for now" and then said (2026-11-11): "I don't like this in-between bars, really. It doesn't make sense… Look at how the old UI has its sizing… is it called scaling from the corners? That's what I wanted, not the horizontal and vertical. That makes no sense. You're assuming it's a grid."

What the lead checked in code:
- **The old UI** (`C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/src/lib/workbench/tiles/TileBoard.svelte`, lines 300 to 330) puts a **transparent** handle between panes (`Resizable.Handle class="bg-transparent mx-[3px]"`, paneforge 1.0.2). Nothing is drawn between widgets. You grab a widget's edge.
- **The new app** (`apps/qmx-desk/src/lib/qmx/Splitter.svelte`) draws a grip pill on every gap whenever the pointer is over the board, and a line on hover. Those are his "in-between bars". They make the board read as a grid with rails.
- Neither UI has corner dragging. He wants it: grab a widget by its corner and change its width and height in one move, like a window.

## The range

**Starts at:** how a widget on a board is resized by hand.
**In:** `apps/qmx-desk/src/lib/qmx/Splitter.svelte`, `apps/qmx-desk/src/lib/qmx/tiles/Tiles.svelte`, `tiles/tree.ts`, and `tiles/store.svelte.ts` only if a helper is needed. Both boards (Overview and Trading) share this mechanism, so both get the new behaviour.
**Stops at:** the widget's frame. Nothing inside a widget changes.
**Out of bounds:** every widget body (`CardBody`, `cards/*`, `Fit`), `tiles/panel-size.ts`, `tiles/defaults.ts` and the default layouts, the shell, the navigation pills, the status bar, pages, demo data, the saved-layout storage key (do **not** reset saved layouts). If `Splitter` is used anywhere outside the boards, keep that use working and list it in your report. Report every file you changed, and say plainly if any is outside the range.

**Protected, keep working exactly as now:** drag a widget by its title to split, swap or dock; minimise to the foot; "+ Widget"; "Arrange"; "Reset layout"; a page opening as a tab; the three size modes (compact, regular, expanded) that follow the widget's measured size; double-click to reset a split.

## What to build

1. **Corners.** Each widget can be resized from any of its four corners. Dragging a corner moves the nearest boundary on that side in each direction at once: the split that sets the widget's width on that side and the split that sets its height on that side. In the tree of splits that means walking up from the widget to the nearest row split and the nearest column split that own those two edges, and resizing both pairs in the same pointer move. A corner that sits on the outer edge of the board in one direction moves only the other direction. A corner on the outer edge in both directions is not a handle.
2. **The mark.** A small, quiet corner mark appears in a widget's corners only while the pointer is over that widget (and on keyboard focus). No mark at rest. The diagonal resize cursor shows on the corner's grab area. The grab area is generous (about 18px square), sits above the widget's content, and never blocks a button or a scrollbar inside the widget.
3. **No bars.** Remove the grip pills and the "every grip shows when the pointer is over the board" rule. Edges between widgets stay draggable, as in the old UI, but invisibly: the cursor changes, and a thin line shows **only while dragging**. In "Arrange" mode show the corner marks on every widget instead of bars.
4. **Feel.** Track the pointer 1:1 from where the corner was grabbed, with pointer capture, no animation while dragging, and the same minimum sizes the edge handle enforces today. The widget's content changes mode live as it crosses a size threshold. Double-click a corner resets both splits it controls.
5. **Keyboard and screen readers.** The edge separators keep their arrow-key behaviour. A corner needs no separate keyboard path.
6. **Words.** Update the tooltips so nothing mentions bars. One short line: "Drag a corner to resize".

## How to check (in the built-in browser, your own tab on `http://localhost:5174/?review=off`)

Other agents are using the same browser for web research in their own tabs. Open your own tab with `tabs_create`, pass your `tabId` on every call, and touch no other tab. Do not start, stop or restart any server; the app is already running with hot reload.

- On the Overview at 1600x900 and 1280x720, demo data and worst case: drag each kind of corner (inner junction, one on the board's edge, one in a nested stack). Width and height both follow. Nothing overflows, the board does not scroll, neighbours never go below their minimum.
- Drag a widget from small to large by one corner: compact, regular and expanded all appear.
- No bar or grip is visible between widgets at rest or on hover. A line shows only during an edge drag.
- Title-drag to split, swap and dock still works. Minimise, "+ Widget", "Arrange" and "Reset layout" still work.
- Trading: the same corners work and nothing else there changed.
- Reset the layout when you finish so the owner finds the default board.

Take a screenshot of a widget mid-hover showing the corner mark, and one mid-drag.

## Done means

Every check above passes and your report says so check by check, lists the files changed, names anything you could not do, and says what the owner should try first in one line. Do not spawn subagents.
