# Round 5 builder: space, sizing and the Overview's gaps

You are the only builder this round, so you may edit any file in `apps/qmx-desk/src/`. Read `round-2-shared.md` in this folder first (the rules for every builder, the skills to invoke, how to check and report), then `../SPACE-RULES.md`, then the last two entries of `../DESIGN-LOG.md`. Then this.

## Why this round exists

The owner clicked the merged app and said: the depth is "actually nice", adding widgets is "a very nice touch", the market clocks are "bloody brilliant", and the Overview is "quite well" done. But widget sizing failed for the fourth time, and the reason is now known. The tiling tree was ported from the old UI; the second half of the old mechanism was not: every tile measuring itself and telling its content to render as compact, regular or expanded. Without it, widgets hold a small view with a hole under it. `SPACE-RULES.md` states the rules. Your job is to make the app obey them and to fix the specific things he pointed at.

Read the old code before writing: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/src/lib/workbench/tiles/panel-size.ts` and two panels that use it, `…/src/lib/home/panels/GoingPanel.svelte` and `MarketsPanel.svelte`. Run the old UI at `http://localhost:5173` and resize a Home tile from small to large to see the content change.

## 1. Content that knows its size

- Port `panel-size` into `src/lib/qmx/tiles/`: each tile measures itself and provides its mode to the widget inside. A widget opened in a tab is always expanded.
- Give **every** Overview and Trading widget its three modes (`src/lib/qmx/CardBody.svelte` and the bodies it uses), following rules 6 to 10. No widget may show a bare gap under its content at any size.
- A widget opened in a tab fills the page (rule 5), and list pages fill the window (rule 11). His example: "Units on paper and live" opened in full shows four rows and then two thirds of the page empty.
- Set the default layouts from what each widget holds (rule 2). His examples: "Running now" needs more room than it has; "Markets today" has far more than it needs; a freshly added "Open positions" is mostly empty.
- Make resizing reachable for a widget that is alone in a column or row (rule 3); he could not size "Markets today" at all.

## 2. The widgets he named

- **Markets today**: three bars with empty space under them. Give it depth: the sessions, then what is coming up today (scheduled news such as CPI), then headlines, filling the widget. Clicking a session shows what trades in it: his instruments, his units on them with live or paper, and his pods (see below). This is the same content as the market-clock popover in the status bar, which he likes; make the two one piece of work. Compact mode is the three bars and the next event only.
- **Paper and live, 30 days**: "What the hell is this? …there is nothing." Replace it with **Pods**. A pod is a cluster of units of one trading style (for example scalpers) with its own risk and sizing rules; pods are QMX's portfolio view. The backend for them is being built now and is not merged, so use demo data: three or four pods, each with its units, a live side and a paper side, today's result, and how much room it has before its stop. Rows open a pod page built with the existing page pattern. Mark nothing as final; say in your report what you assumed.
- **Running now**: he asked what the small squares are. Keep the idea (he liked it in round 1) but make it readable without explanation: a legend in three words, a tooltip per square naming the job, and squares grouped by where they run.
- **Units list** (the "All" page): "there are no borders separating what's live, what's what… the list is poorly done." Group by state with headings and hairlines (rule 12) and fill the page.

## 3. Navigation fixes

- Remove the "Show names / Icons only" toggle; he called it irrelevant.
- Bring back folding each pill on its own, vertically: the places pill folds to a small handle and so does the mini-app pill. He asked for this in round 1 and it was lost in the merge.
- The small divider line between the first two icons and the rest confused him. Either remove it or make the two groups read as two groups at a glance.
- Start the places pill higher: just under the top bar instead of centred, so the space below it is free for mini apps. Several mini apps can be open at once (plan for six); the mini-app pill shows what fits and puts the rest behind one "More" control. Navigation never scrolls.

## 4. Not in this round

Do not redesign: the Sessions page (he called it "beyond ugly"; it is tomorrow's section), mini-app pages, day one, search, the Usage page. Leave them working.

## Done means

Every check at the foot of `SPACE-RULES.md` passes and you say so check by check in your report. Then list: each widget and its three modes in one line each; what you assumed about pods; anything in section 2 or 3 you did not finish.
