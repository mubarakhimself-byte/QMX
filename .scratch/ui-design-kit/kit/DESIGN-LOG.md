# Design log: what he ruled, round by round

The running record of the redesign sessions that started 2026-11-10. Newest round last. Each line is his ruling or a decision he accepted; quotes are his dictation. Backend needs go to `BACKEND-ASKS.md`. The app is `apps/qmx-desk` on `ui-redesign` (dev server: launch config `qmx-desk`, port 5174).

## Round 1: general layout (2026-11-10)

Shown: three navigation layouts (Rail, Spaces, Command), three looks (Night desk, Soft machine, Atlas), demo / worst-case / day-one data, three text sizes. Score he gave: 8 out of 10.

**Picked**
- **Night desk look + Command navigation.** "Night desk combined with the command navigation is my best pick… I can see myself using this on a daily basis."
- The command field at the top: "a very, very good touch."
- The floating dock of places: liked. Make it **collapsible**. Mini apps get **their own section in it, colour-coded and separated** from the built-in places.
- The "Going on" jobs grid: "very cool."
- Count bubbles on places: liked.
- Text size A++ with demo data: liked.
- Rounded widgets are "easy on the eye"; he is fine with them.

**Dropped**
- Spaces layout: "I don't get what the whole point is."
- Soft machine: "the gray gets odd."
- Atlas: "not that bad", not chosen.

**Asked for**
- A **Bloomberg / trading look** to compare against Night desk (sharper widgets, the terminal feel). He expects it to be harder on the eye; he wants to see it.
- Widgets must be **resizable**, not only minimisable. Size is how he sets priority.
- A minimised widget must show that **something new** arrived, without turning into "so many bubbles".
- **Sorting** inside widgets, more detail, and a click that lands on the exact thing that needs him (a mini app, a session, an agent).
- Day one looks like "some generic SaaS project": make it feel like trading. Do not show Home's widgets there, because **Home's contents are not agreed**.
- Status bar is "not that intentional":
  - where does "9 running" go, and "3 need you"?
  - "2 nodes trading" must be clickable;
  - "This PC + vps-fra" next to nodes confused him: say the difference or merge them;
  - the kill switch **has levels**; design for that;
  - **several time zones** should be visible.
- Keep notes of backend needs as they come up.

**Open**
- What goes in Home. To be derived from user journeys (existing ones, or new ones from party mode / CIS).
- The notification model as a whole (bubbles, "needs you", new-in-widget marks). To be designed with the Agents section.
- New components for mini apps, and what the copilot is given to build with.
- Streaming data and news sorting.

## Round 2: his verdict on the revised shell (2026-11-10, evening)

Score fell "from an 8 to a 5 or 6". He put it down to the lead's context getting bloated.

**What failed**
- **The navigation dock.** It grew tall and had to scroll: "when you have to scroll on a navbar, it kind of kills the entire mood." He wants it floating and short, with fewer places. The built-in menu ends, and the mini apps are "detached entirely" in their own group. The colour coding of mini apps was right.
- **The top left** ("QMX, an icon of home, then Home"): "What's that for? I don't get it."
- **Overflows**: scrollbars between widgets, and sideways overflow.
- **Resizing**: the old UI let him size each widget on its own; this one did not feel like that.
- **Terminal look**: "so cool" at a glance, then "ugly" once used. The coloured title bar over a black body "doesn't make sense", and it is "just compact". Parked.

**New asks**
- Explore **navigation variants** on their own, top bar included. The navigation may differ per place (Agents, Library, Home).
- Clocks: on hover or click, show which markets and instruments are open, and link to news and macro workflows.
- **A bigger question: stop designing QMX as a terminal.** Widgets were chosen only because they were the one extensible pattern he knew (OpenBB). "We just need an extensible UI." Look at whole-app designs that are not built from widgets; Home is "more like a dashboard". He wants to compare options. Modern cards and curves are welcome.
- Reference he liked: a video of a short sidebar that collapses from labels to icons beside one inset sheet of expandable cards (`refs/images/sidebar-video-he-liked-2026-11-10.jpg`). More at collectui.com.

**New way of working (his ruling)**
- The lead grounds, picks the skills, writes the briefs and orchestrates. **Background builders build**; the lead waits and does not build beside them.
- No judge agent: he and the lead judge by clicking.
- Builders may be Fable or Opus 5.5; he does not mind which. Builders use the built-in browser, never his own.
- This sits on top of the earlier method: inspiration first, variants he can flip, one question per round.

**Round 2 plan**: four builders. One explores navigation and fixes the Board shell. Three build whole-app concepts that are not widget boards: Pages, Stage, Stream. Shared brief: `briefs/round-2-shared.md`.

**Corrections the same evening**
- The sidebar video "really didn't matter": it only showed what collectui.com holds. It is not a reference for his taste.
- On the widget question he asked for **grounding before options**. The three concept builders were stopped after a few minutes. A research pass on how extensible products structure their UI (`refs/grounding/09-extensible-ui-models.md`) runs first; concepts are briefed from it afterwards. The navigation builder keeps going.

## Round 3: three skeletons (started 2026-11-10, night)

Grounding done first, as he asked: `refs/grounding/10-shapes-from-journeys.md` (from QMX's journeys) and `refs/grounding/09-extensible-ui-models.md` (principles, then products). Both find that watching, which is what a board is for, is the main shape of about 2 of 15 journeys. The backend has no widget, layout or dashboard object (checked in code).

His words: "You want to organize based off objects? That's an interesting thing. I just want to see how it looks like." And: "you take the lead in terms of what to do, when to do."

Three builders (Opus 5.5), one skeleton each, all showing the same five moments (Morning, Decide, A unit in depth, Converse, Watch): **Objects first**, **Copilot first**, **Day first**. Brief: `briefs/round-3-skeletons.md`. The board stays in each as one kind of page.

Noted from him for later: mini apps are Claude Code plugins, which may simplify wiring; how mini apps style their screens is decided "when the time comes"; journeys are hints that may be expanded.

**To ground before the Apps section** (his note, 2026-11-10 night): mini apps are Claude plugins on the Claude Agent SDK, and their screens use MCP Apps, which "might be the right protocol". Study how Anthropic shows plugin and MCP-app UI inside Claude Desktop and Claude Code (where it appears, how it is themed, what the user controls) before designing how mini apps appear in QMX.

**How he works while builders run**: he watches and clicks, and may not reply. Carry on without waiting; ask only when a decision is his.

**Round 3 built (2026-11-10, late night).** All routes in `apps/qmx-desk`, flipped with the bottom-left pill:
- `/` Board, with three navigation variants (`?nav=1|2|3`: Two pills, Folding rail, Place bar), per-widget resizing, market clocks that open.
- `/concepts/objects` Objects first. Unit of extension: a section or an action on a kind's page, or a card for one of two boards. Its risk: the lifecycle line (draft, tested, paper, live) as every unit's identity.
- `/concepts/copilot` Copilot first. Unit of extension: a view the copilot opens, which he pins. Its risk: a drawn line from a message to the view it opened.
- `/concepts/day` Day first. Unit of extension: a source posting five card kinds into the day. Its risk: a time spine with a NOW line and the markets beside the day.

Each builder's own stated weakness: Objects first is weak for jobs that cut across many things and for triage; Copilot first is weak at finding a thing again and needs stored pinned views; Day first makes him pass through the day to reach a thing and the list grows long.

The lead checked the first two moments of each by clicking; the rest is as reported by the builders. Awaiting his verdict. The lead's lean, not yet agreed: Objects first as the skeleton, Day first's "Waiting for you" day as its front page, Copilot first's "opened beside the chat, with a way back" for sessions.

## Round 3 verdict and round 4 (2026-11-10, late night)

**His ruling:** "General overview: board. That's wrapped up. We move on."
- Skeleton: **the Board.** "The board thing sort of makes the most sense eventually… the cleanest organisation."
- Content: **Objects first's depth and layering inside the Board**, and its better cards (he named "Markets today" and "Running now"). "Can we have a mixture of objects first and board?"
- Navigation: **Two pills**, "or maybe folding rail… we can do both". "Place bar will never work." Objects first's own navbar: "ugly".
- Copilot first and Day first: dropped. "All the other pages look ugly."
- Still failing: **widget sizing.** "Look at how the old UI did it. You don't really have to reinvent the wheel."
- The lead's lean (Objects first as skeleton with Day first's front page) was **not** taken. Do not raise it again.

**Round 4:** two builders lock the base. A ports the old UI's tiling behaviour. B merges Objects first's pages, cards and depth into the Board app, settles the navigation, and deletes the losing options. Brief: `briefs/round-4-lock-the-base.md`.

**After round 4:** write the base rules down; then sections one at a time, each with its own grounding, options and worst-case pass. Usage page not designed yet (he noticed the 62% meter).

**Day one (his note, same night):** the Board's day one "mugs" Objects first's: "one of the best… a very, very nice touch". Keep it. For the first-start section later:
- Remove "Look around with demo data" for a real install; think from a new person installing.
- Cover what is needed straight after installation, such as connecting computers and accounts.
- Give the market sessions depth: click a session (for example New York) to see which instruments trade in it and go on to them.
- On Home with data, the ask is the same as everywhere: "we just need depth" on the dashboard.

**Home is the first section (his direction, same night).** Its layout is accepted in demo, worst case and day one. Still wanted: the transition from day one to the dashboard ("the dashboard itself should be there already"), what the Markets view does, depth, and a simple way for widgets to connect ("we don't want a huge pile of slop"). Research view dropped. Each page is designed one at a time and may be overhauled; only the frame, board behaviour, look and "go deeper" pattern are shared. Brief: `briefs/section-home.md`. It goes to a builder when round 4 has landed.

**Round 4 landed (2026-11-10, late night).** The app is one route again (`/`, plus `/components`).
- Tiling is the old UI's mechanism, ported: a tree of splits; drag an edge; drag a widget by its title to split, swap or dock at a board edge; minimise to the foot; "+ Widget", "Arrange", "Reset layout"; layouts saved per place on this machine. Not carried over: named saved layouts, colour-linked groups.
- Objects first's depth is inside the Board: unit, proposal, session and run pages; every widget row opens a page; a narrow list stays beside an open page; a trail and Esc lead back; "Edit page" on a unit.
- Places: Overview and Trading (boards), then Units, Sessions, Runs, Workflows, Library, then mini apps. Two pills; the pill opens out to show names. Usage and Settings in the top bar.
- The Board's own day one was kept after the merge builder briefly replaced it.
- Lead checked by clicking: Overview, a drag-to-split, the session page, day one. Not yet checked by the lead: unit page, Trading, worst case after the merge. Open flaw seen: "Markets today" in its default tall slot leaves empty space.
- Next: his verdict on sizing; then the Home section (`briefs/section-home.md`).

## Round 4 verdict and round 5 (2026-11-10, near midnight)

**Liked:** the depth ("actually nice"); adding widgets ("a very nice touch"); the Overview ("you've done overview quite well, I'm impressed"); opening a page adds a tab ("a nice touch"); the market clocks at the foot ("bloody brilliant"; "a nice touch"); search works.

**Failed again: sizing and space.** "You still fail to do the sizing thing of the widgets properly… Space management is an issue… there are two levels of space management." Examples he circled: the empty space under a freshly added "Open positions", under "Markets today" (which he also could not resize), and under the four rows of "Units on paper and live" when maximised. "Running now" needed more room. Cause found by the lead: the old UI's `panel-size` (each tile tells its content to be compact, regular or expanded) was never ported. Rules written: `SPACE-RULES.md`.

**Other points**
- Units list: "no borders separating what's live, what's what."
- Running now: "I don't know what's with these small boxes."
- "Paper and live, 30 days": "what the hell is this… nothing." Replace with **pods**: a cluster of units of one style with its own risk and sizing rules; "pods is mostly portfolio". The backend for it is being built in another session.
- Markets today: too much space; add news; sync the sessions with pods ("which pods, which what"); a mini page; useful for the phone companion and notifications later.
- Navigation: remove "Show names"; bring back folding the pill vertically ("I never said remove it"); the small divider line is unexplained; start the pill higher so mini apps have room; several mini apps run at once.
- Sessions page: "beyond ugly. We shall design a better one." Mini-app page: "beyond ugly."
- The Copilot button on top "will maybe move or be removed".
- Day one: fine, but "a lot of text"; fill it from what the backend already has; the sessions block there is "more like a diagram".
- Ideas for tomorrow: sound effects; a logo; a start-up card like cTrader, JetBrains or Adobe; units may stay in the Library with a preview and a detailed view.
- He said about 80 mini apps are coded. The code at `engine/base` `3ae41ffc` has 7 app folders and about 60 workflow templates. Unresolved; ask.
- **Next page: "the AI chats… Copilot and the agentic system. This is going to be a long one." Ground on inspiration first; the chat input is where agents fail.**
- He asked for a hand-over ready for compaction: `RESUME.md`.

**Round 5:** one builder on space, sizing, the named widgets and the navigation pills. Brief: `briefs/round-5-space.md`.

## Added after the double check (2026-11-10)

Checked line by line against `refs/his-words-2026-11-10-design.md` (22 messages). Each line: what, his words, message number there.

- **Correction, text size:** A is his favourite, not A++. Round 1's "A++ liked" was only "not bad" at worst case. "I haven't bothered with the sizing of A plus and A plus plus… I've only been in A because I like it" (#19; #9).
- **The redesign code is the real app.** Builders write code fit to ship, not throwaway demos. "I think we can use these things straight up to wrap up QMX as a desktop app… I don't think that code is going to differ" (#13); "we've already started coding the UI. I don't think we are going to change much, maybe connecting to the backend" (#20).
- **Judge it as a live app in its own window**, not a browser demo. "Just assume, you know, this is a live app… we haven't seen this thing in its normal window" (#21); "when it's its own window, that changes a lot" (#19).
- **Sizing is a technical problem: look for a skill.** "Don't you think a skill can help with the sizing?… the spending [spacing] thing is more of a technical problem than a design one" (#20). He accepted the lead's check-script approach: "if that's what you think it's the right way, building the script and whatnot, cool" (#21).
- **Navigation icons must be the same in every state.** Day one's pill icons differed from Overview's: "the icons I've noticed are different. They are very different" (#18).
- **Unexplained bars on the board:** "what's up with this weird sort of bars?" (#19). Find and explain or remove them.
- **Market clocks must keep real time.** "I don't know if the time syncs properly. The time doesn't so far" (#19); "it would really be cool if it syncs properly" (#19).
- **Units may not stay a place of their own.** "Units are kind of in the library, in the old design. I don't think I would want to move them… the card design might cater for units… a preview, then a detailed view" (#19). This conflicts with Units as its own place in the pill; settle it in the Units section. The Units page itself he praised: "it's actually well done, round of applause for that" (#19), and "it might actually not exist" as a page (#19).
- **Protected (praised, keep through every rebuild):** the command field ("a very very good touch", #9); the "Going on" / Running now jobs and their detail ("so much text in there, which is actually quite good", #19); the market clocks at the foot ("bloody brilliant", #19); adding widgets ("a very nice touch", #19); opening a page adds a tab ("a nice touch", #19); the depth ("actually nice", #19); the pill collapsing ("I think you did it well", #19); the Units page (#19); the Board's day one (#16, #17).
- **The Lab is still to come and matters.** "The lab is most likely going to change. We shall talk about that because it's a very important piece of this entire puzzle" (#2).
- **Agent system idea for the Sessions section:** "Previously, we had, for example, agents everywhere. We might change that to just one singular agent panel with proper grouping or color coding… You will surprise me" (#2).
- **Methodology must have a home in the agent section.** "Methodology is literally just skills and standards that QMX will use… like BMAD" (#6).
- **Journeys cross places; design them step by step.** "A lab could somehow start a new project… where does the UI take you from here to there to that? It's like stepwise" (#6).
- **Each section pulls in its backlog.** "We can literally cluster some bits and pieces of the backlog together" (#6); "Asked for but never built. You can add that to the backlog" (#4). The list is `INTENT.md`, "Drawn or asked for, never built".
- **QMX is built for him first.** "QMX is not for any user. It's for me… some things inside QMX don't need the user to really click… the dashboard itself should be there already" (#17). A new person installing is still a case to design for (#16).
- **Use poteto-mode or another skill to keep widget wiring simple.** "Here maybe potato mode can come in, or any other skill… Please don't forget to use the skills" (#17).
- **Skills means the whole set, installed and set up, and our own component library.** "When you just use the front-end skill and that's it… You didn't even bother installing them and setting them up… we needed our own custom component library" (#8).
- **The old look is retired.** "One of the reasons we are starting from scratch again is because of the aesthetics. They were good back then, but right now, it's ugly" (#7). Night desk answered this; do not drift back to October colours or borders.
- **Grounding results are for the lead, not him.** "When the sub agent finishes, I don't think you need to report anything… most of the grounding is for you" (#4).
- **Check who made an old choice before calling it a mistake.** "The mistakes you had just made of the amber border noises, I am the one who suggested those" (#4).
- **Everything in the Obsidian storyboard is fundamental** unless a better idea is agreed. "Things like literally everything that was in the Obsidian page is fundamental" (#2). The storyboard is listed in `SOURCES.md`.
- **Builder models:** he allowed Fable 5.1 or 5.2, or Opus 5.5, for builders, and asked the lead to wait while they run. "Fable models take a lot… maybe you may shift to Opus… I don't think Opus 5.5 is actually that bad… It just needs… proper instructions" (#10).
- **Search inside mini apps.** "I want to see searching with mini apps specific… we shall talk about searching tomorrow" (#19).
- **Workflows and chat get the most care.** "I think workflows and chat are two things we are going to really cater for a lot" (#19).
- **The ~80 mini apps include QMB.** "Out of the box, QMX is coming with 80 something… mini apps… QMB, stuff like that" (#19).
- **Day one from a template.** "Maybe having a template, then… we sort of parse and all the backend stuff sort of fills itself in" (#19).
- **His circled screenshots** from the round 4 verdict are saved at `refs/images/his-screenshot-2026-11-10-msg19-1.png` to `-3.png` (#19). One shows where the pill should start, higher up.
- **Correction, "Mini-app page: beyond ugly" (round 4 verdict):** he was talking about how mini apps look once added to the pill, not a mini-app page. "When mini-apps are added… color coding them, but we shall look at how many apps are meant to look like, because this is ugly, beyond ugly" (#19).
- **Correction, times of day:** rounds 3 to 5 are marked "late night" and "near midnight". His messages ran from about 16:45 to 21:15 local time (UTC+3, by the transcript clock); the round 3 verdict came near 20:00 (#15).

**Scope correction (same night):** he saw the round-5 builder working on unit cards. "If we are touching spacing, scope for spacing. Do not leave the blast radius open to the entire UI… Spacing in widgets, period." Round 5 was cut to the Overview's widgets only; Trading, Units and other pages are untouched until their own sections.
- His correction to the scope lesson: "It is not that the brief should cover one area. It can cover multiple areas. You should have a scope… a range, a start, and a limit. That is one of the reasons we have the skills… potato mode may come in… even the wayfinder skill. You have a lot of skills. I do not know why you have not used them." Lessons 17 and 18 in `RESUME.md`.

**Round 5 landed (2026-11-10, about 22:30 his time).** Scope: the Overview's widgets only. Awaiting his verdict.
- Three size modes per widget from its measured size (`tiles/panel-size.ts`, ported from the old UI); `Fit.svelte` fills what is left with the next most useful thing in whole rows.
- A widget opened in a tab fills the page. Default Overview layout set from content. A lone widget gets "Put a widget beside this one" on a right-click of its title.
- Pods widget replaces "Paper and live" (demo: Breakouts, Scalpers, Trend, Mean reversion; live and paper sides; room before the day stop). Assumed, not from the backend.
- Running now: legend, squares grouped by machine, a tooltip per job. Markets today: sessions, today's schedule, headlines; a session opens what trades in it, shared with the status-bar clock.
- Pills: each folds on its own; places pill starts under the top bar; mini-app pill shows what fits and the rest behind "More"; "Show names" removed.
- `?review=off`: the app edge to edge.
- Measured check: `src/lib/dev/space-check.js`. To run: open the app, then in the browser console `const m = await import("/src/lib/dev/space-check.js?t=" + Date.now()); m.start();` and read `window.__space` (about 15 minutes for the full matrix). Result on the Overview: 1 failure left ("Running now" in a tab at 1280x720, worst case, largest text, review off) and 4 near the limit; before, 90 failing widgets and 31 failing tab pages.
- Files changed outside the Overview's widgets are listed in the builder's report: `Frame`, `Board`, `tiles/*`, `Sessions`, `data.ts`, `MarketClock`, the nav files, `+page.svelte`. Saved layouts reset once (storage key v2).
- Not done by his scope cut: Trading and its unit cards, the Units list page, pod pages.

## Round 5 verdict and round 6 (2026-11-11, about 15:50)

His words are in `refs/his-words-2026-11-11-design.md`.

- **Sizing: "okay for now."** Space inside widgets is accepted for now. "The issue is with the widgets themselves."
- **The bars between widgets must go.** "I don't like this in-between bars, really. It doesn't make sense." These are the grip pills `Splitter.svelte` draws on every gap, and they answer yesterday's "weird sort of bars".
- **Resize from the corners.** "Is it called scaling from the corners? That's what I wanted, not the horizontal and vertical… You're assuming it's a grid." This settles yesterday's open question: sizing from the corners is a request.
- **Checked in code by the lead:** the old UI has no corner dragging. It resizes from the edges with a transparent handle (`TileBoard.svelte` lines 300 to 330, paneforge 1.0.2), so nothing is drawn between widgets. What he remembers as better is the absence of bars. Corner dragging is new work.
- **Round 6:** one builder, range = how a widget is resized by hand (`Splitter.svelte`, `tiles/Tiles.svelte`, `tiles/tree.ts`). Corners resize width and height in one move; bars removed; edges stay draggable but invisible. Brief: `briefs/round-6-corner-resize.md`.
- **Inspiration for the agentic section.** He asked for it "on multiple websites or for images", around "orchestration, tool calling, browser use", from harnesses "like Codex, Claude Code, Warp, and so many others", and said "Start with refero, then we work our way from there." He also said not to start from T3 Code. Three scouts went out, one per topic (brief `briefs/agentic-inspiration-scouts.md`), saving pictures under `refs/images/agentic/`. The lead takes Refero.
- **Usage:** he asked the lead to use as much of the remaining usage as possible before his reset at 16:00.
