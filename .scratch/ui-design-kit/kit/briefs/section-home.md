# Section brief: Home

For the builder who designs Home after round 4 lands. Read `round-2-shared.md` first (the rules for every builder), then the "Round 3 verdict" and "Day one" entries in `../DESIGN-LOG.md`, then this.

## Where Home stands

The owner has accepted Home's general layout: the Board with Two pills, in demo data, worst case and day one. Day one ("Your desk is not open yet", the market sessions, four steps) he called "one of the best… a very, very nice touch". Do not restyle what he accepted. This section adds what is missing: **the way from day one to a working dashboard, the Markets view, and depth.**

## What he asked for (2026-11-10, his words shortened)

- "I just need to see that transition" from day one to the dashboard.
- "QMX is not for any user. It's for me… The dashboard itself should be there already. Or we should have some sort of transition to it."
- "Some things inside QMX don't need the user to really click. That's the whole point of QMX… some things should already come in-house… mini apps already have stuff."
- Remove "Look around with demo data" for a real install.
- The session bars need depth: "when I click on New York… I can go to instruments."
- The views on top (Today, Markets, Research): "I don't think Research is necessary… Markets is okay, but what happens when I click on Markets? Surprise me."
- "Dashboards need a lot of interconnectivity. We need to look at the technical lens… How can we make it simple? We don't want to write a huge pile of slop."
- "We just need depth."

## Facts to design from (backend at `3ae41ffc`; see `../refs/grounding/08-qmx-today-for-design.md`)

What exists on a fresh install before he connects anything:
- This PC as the one machine.
- The built-in apps: backtester, market intelligence, trading node. All three have no screen of their own.
- About 55 workflow templates, installed but switched off.
- A sample unit as a draft, and the block dictionary waiting for one publish click.
- Market hours are plain clock facts and need nothing.

What each step switches on:
1. **An AI provider** → the copilot, sessions, agent steps in workflows.
2. **Market history downloaded** → prices and charts from stored data, market intelligence readings, backtests.
3. **A unit built and tested** → units, results, the judge's verdicts, proposals.
4. **A broker demo sign-in and a node started on This PC** → paper trading, positions, live prices from the broker.

Not in the backend today: a getting-started state, a news source that works with no setup (he has ruled "free news only"), saved board layouts. Design for them and list them in your report as backend asks; do not pretend they exist.

## What to build

1. **The desk wakes up.** Day one is the dashboard itself, not a page in front of it. The widgets he will have are already in their places. Each one that cannot work yet says in a few words what switches it on and offers that one action; each one that needs nothing (market sessions, the clock, the sample unit, This PC) is alive from the first second. The four steps stay as the short strip he liked; finishing a step visibly wakes the widgets that depended on it, and the strip shrinks until it is gone. Make the steps completable in the demo so he can watch the whole transition from nothing connected to the full dashboard in under a minute. Keep the headline feeling ("Your desk is not open yet") at the start. No "Look around with demo data".
2. **Markets.** His question was what happens when he clicks it. Design the answer. Direction: the market's day on one time axis (sessions, his own events, scheduled news such as CPI), and under it the instruments, grouped by the session they trade in. Clicking a session filters to its instruments. Clicking an instrument opens that instrument's page: price, the market intelligence reading for it, his units on it with live or paper state, what is coming up for it, and links to the macro workflow and news for it. An instrument is one of his things like a unit is; reuse the page pattern from round 4. Drop the Research view.
3. **Depth on Today.** Every widget on Home gets its second level if it lacks one after round 4: the full view when opened in a tab, sorting where a list can be long, and each row leading to the thing it names.
4. **One simple way for widgets to connect.** He asked for interconnection without complexity. Propose and build the smallest mechanism that does it: for example one shared "focus" per board (pick an instrument or a unit in one widget and the others on that board follow it), switched off per widget if he wants. Say in your report what a widget must declare to take part (what it shows, what it follows, what a row opens). Before building it, invoke these skills and follow them: `principle-foundational-thinking`, `principle-model-the-domain`, `principle-subtract-before-you-add`, `principle-experience-first`. If two mechanisms would do, build the smaller one and say what you left out.

## Checks specific to this section

- The transition works in one sitting: step 1 to step 4, each waking its widgets, ending on the dashboard he already accepted.
- Day one still looks right at 1280x720 and at `?text=larger`.
- Worst case on Markets: 60 instruments, a long instrument name, a market on holiday, a session that wraps past midnight.
- Take one visual risk in Markets you can defend; keep Today as he accepted it.

## Report

As the shared brief says, plus: the backend asks this section adds, and what a widget declares to join the shared focus.
