# Round 4 builders: lock the base app

You are one of two builders. Read `round-2-shared.md` in this folder first; every rule in it applies (the owner, the skills to invoke, the app, the data, how to check, how to report). This file says what the owner decided and what the two of you build. The two tasks are split so that you never edit the same file.

## What the owner decided (2026-11-10, after clicking all four options)

His words, shortened:
- "General overview: **board**. That's wrapped up." The Board route (`/`) is the app. Copilot first and Day first are dropped: "all the other pages look ugly."
- **Objects first** "just looks better… it goes deep and deep… it's layered". He wants a **mixture**: the Board's general layout and navigation, with Objects first's depth, layering and better-looking cards. "The depth that objects first has compared to what the board has is like miles apart. I would like the depth that objects first has to be the one that board has."
- **Navigation: the Board's.** "Two pills is what I'll go with. Or maybe folding rail. I think we can do both." "Place bar will never work." He called Objects first's own navbar "ugly".
- **Widget sizing failed again.** "You sort of just divided it into three panels and that's it… all the agent did was add some things I can drag… Look at how the old UI did it. You don't really have to reinvent the wheel here."
- The cards he named as good in Objects first: "Markets today", "Running now", and "that simple thing of clicking and then that depth".

So the base app is: **the Board, with the old UI's tiling behaviour, and Objects first's depth behind every widget.**

## Builder A: tiling that works like the old UI

**You own**: `src/lib/qmx/Board.svelte`, `src/lib/qmx/Splitter.svelte`, and a new folder `src/lib/qmx/tiles/`. Nothing else.

The October UI's tiling board is the reference for behaviour, by his instruction. Study it two ways before writing anything:
1. Run it: `http://localhost:5173` (already running; do not start or stop servers). On Home or the Lab, drag a tile's edges, drag a tile by its header onto another, minimise one and watch the rest fill, switch on "Edit layout", add a panel. Note exactly what each gesture does.
2. Read its code: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/src/lib/workbench/tiles/` (a tree of splits, saved layouts, drag to swap, minimise docks and the rest reflow). Port the mechanism into `src/lib/qmx/tiles/`; adapt names and styles to this app. That code is Svelte 5 too.

What must be true when you are done:
- **Each widget is sized on its own.** A layout is a tree of splits, not three fixed columns. Dragging any edge resizes just the widgets that share that edge. A widget can span, sit beside one tall widget, or take a full row.
- **Drag a widget by its header** to move it: drop on another widget's left, right, top or bottom half to split there, or on its centre to swap. A clear drop preview shows where it will land. It tracks the pointer exactly.
- **Minimise** docks a widget at the foot and the rest reflow to fill; restoring puts it back where it was. Keep the white "something new" dot on a docked widget.
- **Add and remove** widgets (a "+ Widget" control with the place's available widgets; remove from the widget's menu), and **reset to the default layout**.
- Layouts are kept per place in the state the board already uses (`shell` in `src/lib/shell/state.svelte.ts` is owned by Builder B: do not edit it; keep your own store in `tiles/` and key it by `shell.place`).
- Handles are easy to find: a visible grip on hover, a resize cursor, a hit area of at least 16px, double-click to reset that split. Keyboard: a focused handle moves with the arrow keys.
- Nothing overflows: the board never scrolls; a widget's body scrolls only inside itself, vertically. Check 1280x720, `?text=larger`, `?data=worst`.
- `Board.svelte` keeps rendering each widget through `Frame` with the same props it passes today (`panel`, `onexpand`, `onminimise`, `onsend`), and still shows `FirstOpen` when `shell.fixture === "first"` and the full-size view when `shell.activeDetail` is set. Builder B is changing what `Frame` shows inside; you only decide where frames go and how big they are.

## Builder B: Objects first's depth inside the Board app

**You own**: `src/lib/shell/` (all of it), `src/lib/qmx/` except the three things Builder A owns, `src/lib/concepts/`, `src/routes/` (all routes), and a new folder `src/lib/pages/`. Not `Board.svelte`, `Splitter.svelte` or `tiles/`.

Read the Objects first build first: `src/lib/concepts/objects/` and its route, and click it at `/concepts/objects`. Then bring its depth into the Board app:

1. **Pages behind the widgets.** A unit, a proposal (the Decide page), a session and a run each get a page in the main app, moved over from Objects first with their behaviour intact: the lifecycle line (draft, tested, paper, live) with the dashed step a proposal asks for; the judge, result and costs side by side with Promote and Not yet together; the unit page with state per market, sections and actions; the session page with helpers, folded tool calls and the inline approval; lists that shrink to a narrow column beside an open page so he keeps his place; the trail that leads back; Esc to go back.
2. **Every widget leads somewhere.** Clicking a row in a widget opens that thing's page (a unit row opens the unit, a "needs you" row opens the proposal or the session with the approval, a run row opens the run). Today rows do nothing. The widget's own "Open in a tab" stays for the widget's full view.
3. **Better cards.** Rebuild the Board's widget contents to the standard of Objects first's Overview cards, which he singled out: "Waiting for you" (with the Decide / Approve / Fix word and age), "Units on paper and live", "Running now" (the squares, the counts per place), "Markets today" (the session bars with the now line), "Since you left". Use Objects first's data model where the shell's demo data is too thin; move what you need into shared data and keep `worst` and `first` working.
4. **The Lego rule on pages**, as Objects first has it: "Edit page" on a unit (move, remove, add a section, including one from a mini app marked as a guest) and the guest action in the menu.
5. **Navigation: Two pills is the default; the pill can open out to show names** (that is the "folding rail" idea living inside the same pill: collapsed shows icons, opened shows icon and name). Remove the Place bar variant and its code. The list of places becomes: Overview and Trading (the two boards), then Units, Sessions, Runs, Workflows, Library, then mini apps as the detached coloured group. Usage and Settings stay in the top bar. Navigation never scrolls.
6. **Review chrome.** Remove the navigation picker and the concept picker. Keep one small pill for data (Demo, Worst case, Day one) and text size.
7. **Clean up.** When the merge is done and checked, delete `src/routes/concepts/`, `src/lib/concepts/` (all three options and the picker), and anything in `src/lib/shell/` that nothing uses any more. Icons that Objects first kept in its own `Glyph.svelte` move into the shared `src/lib/qmx/Icon.svelte`.
8. Fix the two flaws seen in review: a narrow table must never drop the live/paper column (drop other columns first); opening a market clock at `?text=larger&data=worst` must not shift the page sideways.

Keep the Night desk look and the colour meanings. Where Objects first used amber for the "Promote to paper" button, keep it only if it reads as "this leads to paper"; the primary action colour otherwise stays white.

## For both

Do not wait on each other. Builder A must not change `Frame`'s props; Builder B must not change how `Board.svelte` calls `Frame`. If you need something from the other's files, say so in your report instead of editing. Run svelte-check before reporting; if it shows errors in the other builder's files, name them and leave them.
