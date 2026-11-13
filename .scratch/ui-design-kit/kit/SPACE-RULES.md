# Space rules

The owner has rejected widget sizing four times. His complaint is the same one he made through the whole October session: space that holds nothing. These rules apply to every board, widget and page from now on. A builder checks its work against them before reporting.

His words (2026-11-10): "Space management is an issue… there is so much space at the bottom, which is making the thing look very ugly… the widget that needed more space is Running now… when you maximize, there is so much space… why isn't it taking the entire page?… there are two levels of space management… when do we scroll, when do we not scroll, how do we not have overflows, which widgets need what."

## What the old UI did that the port missed

The old UI's tiling had two halves. The port brought over the first and left the second behind.
1. **A tree of splits** (kept): every edge resizes the widgets beside it.
2. **Every tile tells its content how big it is** (missed). `ui-review-repair/apps/qmx-ui/src/lib/workbench/tiles/panel-size.ts` measures each tile and gives the panel inside one of three modes: **compact** (a summary), **regular** (the working view), **expanded** (everything, with full controls; always used when maximised). Each panel renders differently per mode, so a big tile is never a small view with a hole under it.

## Level 1: the board

1. **The board is always full.** No widget sits in a slot it cannot fill. No slot is empty.
2. **A widget's default size comes from what it holds.** A long list gets height; a table with many columns gets width; three session bars get a small slot. Set the default layout from the content at demo data and check it again at worst case.
3. **Every widget can be made bigger or smaller by him**, on every side that touches another widget. A widget that is alone in a column or row can be resized by dropping another widget beside it, and "+ Widget" offers to do that.
4. **The board never scrolls and never overflows**, at 1280x720 and at the largest text size. When there is not room for every widget at its minimum size, the extra ones go to the dock at the foot, newest last, and say so.
5. **Maximised means the whole page.** A widget opened in a tab uses its expanded mode and fills the page.

## Level 2: inside a widget

6. **Three modes, chosen by the widget's measured size**: compact, regular, expanded. Every widget defines all three before it ships. Compact is the fewest things that still answer its question. Expanded adds columns, rows, a chart, filters and actions, not padding.
7. **Content fills its widget.** When a list is shorter than its widget, the widget does one of these, in this order: shows more per row (the second line, a small chart, the where-it-runs line); shows the next most useful thing for that subject (for market sessions: what is coming up and the news; for open positions: closed today); or, if it truly has nothing more, asks for a smaller slot by default. A bare gap under a short list is a defect.
8. **A widget scrolls only down, only inside itself, and only its list.** Its header and its key numbers stay put. A widget never scrolls sideways; a table drops its least important columns first and never drops the name or the live/paper state.
9. **Numbers are never cut off.** Names truncate with the full name on hover; long secondary text clamps to two lines.
10. **Empty is a state with a design**, not blank space: one line saying what will show here and the one action that fills it.

## Level 3: pages

11. **A page fills the window.** A list page with four rows shows the rows large (more per row) or pairs the list with the open item; it does not stop a third of the way down.
12. **Groups are visible.** In a list of his things, live, paper and the other states are separate groups with a heading and a hairline, in his colours.

## How a builder checks

- At 1600x900, 1280x720 and 1920x1080, in demo, worst case and day one, at standard and largest text: no empty band taller than one row inside any widget or page; no scrollbar on the board; no sideways scroll anywhere.
- Drag a widget to its smallest and largest: all three modes appear and each looks intended.
- Open every widget in a tab: it fills the page.
