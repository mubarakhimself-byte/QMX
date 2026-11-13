# Resume here: QMX UI redesign

Written 2026-11-10 late night by the design lead, for the lead's own next session (after compaction or a fresh start). Read this file first, then the files it names. It replaces the opening prompt the session started from.

## Your role

You are the owner's chief of design. He gave you creative control and expects to be surprised, and he still gives his opinion at every step. You ground, pick the skills, write briefs and orchestrate background builders. **You do not build screens yourself**; when you did, quality fell and he noticed. He and you judge by clicking the running app.

## Where things are

- Branch `ui-redesign`, worktree `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign`. **Nothing is committed** since the kit commit; he has not asked for a commit.
- The app: `apps/qmx-desk` (SvelteKit 2, Svelte 5, Tailwind 4, shadcn-svelte). Run it with the launch config `qmx-desk` (port 5174). The old October UI is the config `qmx-ui-design` (port 5173), kept as a behaviour reference.
- The kit: `.scratch/ui-design-kit/kit/`. The files that matter now:
  - `DESIGN-LOG.md`: every ruling he made, round by round, in his words. **Read all of it.**
  - `SPACE-RULES.md`: the space and sizing rules. Every brief must point at it.
  - `INTENT.md`: why the October UI looked as it did, and the tests he applies.
  - `BACKEND-ASKS.md`: backend needs raised by the design. Add to it as they come up.
  - `refs/grounding/08` (what QMX is today), `09` (extensible UI models), `10` (what the journeys ask of the UI).
  - `briefs/round-2-shared.md`: the standing rules for every builder. `briefs/section-home.md`: the Home brief, written, not yet sent. Other briefs are history.
  - `refs/his-words.md`, `refs/his-words-october.md`, `refs/storyboard-text.md`: his own words; they outrank every summary.

## What is decided

- **Look:** Night desk. True black, rounded flat surfaces, hairlines, Archivo type, IBM Plex Mono for numbers, text size A is his favourite. Colour means state only: blue live, amber paper, violet needs you, green fine, red problem, cyan working.
- **Skeleton:** the Board. Overview and Trading are boards of widgets. The other places hold his things: Units, Sessions, Runs, Workflows, Library, then mini apps as a detached, colour-coded group.
- **Depth:** from Objects first. Every widget row opens that thing's page; a narrow list stays beside the open page; a trail and Esc lead back; "Edit page" lets him add, remove and reorder sections.
- **Navigation:** two floating pills (places; mini apps). Each folds on its own, vertically. No "show names" toggle. The command field in the top bar (Ctrl+K). Usage and Settings in the top bar.
- **Always in view:** what is running, what needs him, machines, market clocks that open, trading state and a stop with three levels.
- **Day one:** "Your desk is not open yet" with the sessions timeline and four numbered steps. He called it one of the best screens. Do not replace it.
- **Tiling:** the old UI's tree of splits, plus "+ Widget", "Arrange", "Reset layout".
- **Protected, because he praised them:** the command field; Running now and its detail; the market clocks at the foot; "+ Widget"; a page opening as a tab; the depth; the pill folding; the Units page; the Board's day one. A brief that touches one of these says so and keeps it.
- **This code is the real app.** He expects the redesign in `apps/qmx-desk` to become QMX's desktop UI, with only the backend wiring left. Builders write code fit to ship.
- **QMX is built for him first.** "It's not for any user. It's for me." Things should already be there without clicking. A new person installing is still a case to design for.
- **Units:** he does not want to move them out of the Library, where the old UI had them (preview card, then detailed view). This conflicts with Units as its own place; settle it in the Units section.
- **Dropped:** Spaces, Rail and Place bar navigation; Soft machine, Atlas and Terminal looks; Copilot first and Day first skeletons; the Research view on Home; Reticle in the new UI.

## What is in flight

**2026-11-11 afternoon:** he said good afternoon and asked to resume. Both dev servers had stopped overnight; `qmx-desk` was started again (port 5174). The old UI (5173) is not running. One read-only scout (Opus 5.5) is out for the Sessions section, brief `briefs/sessions-inspiration-scout.md`; it writes `refs/inspiration-sessions.md` and touches no code. Step 1 for Sessions (reading the kit) is done by the lead: `LEDGER.md` section 4, `INTENT.md` models 6 and 7, grounding 03 and 08, `refs/t3-code.md`, shortlist section 2. Not yet grounded: what "methodology" is in the code and plans today (Library kinds `methodology`, `skill`, `persona`, `agent` exist), and the old October copilot's behaviours (`refs/october-ui-trace.md` section 3). No Sessions builder goes out before his verdict on round 5.

**The scout finished (about 13 minutes).** `refs/inspiration-sessions.md` has 15 entries and a table of the chat input part by part. **Nothing in it was seen as a picture**: the built-in browser draws nothing while the Claude window is in the background, so the scout read pages as text, and about half the entries come from documentation pages, which he asked us not to lean on. The lead tried to open the first page and hit the same wall. Before step 3 (options): with the Claude window in front, open the best few as pictures (the product page for Claude Code desktop, Cursor's agent and voice entries, the VS Code agents list, Wispr Flow, Superwhisper, Amp's demo video with the `watch` skill) and correct the notes from what is seen. Treat the file as leads until then.

**Round 5 landed on 2026-11-10 and waits for his verdict.** It was cut to the Overview's widgets only. What it did: each widget now renders in three sizes (compact, regular, expanded) from its measured size, as the old UI did; a widget opened in a tab fills the page; the Overview's default layout is sized from content; "Paper and live" is replaced by a Pods widget on demo data; Running now has a legend and is grouped by machine; Markets today shows the sessions, today's schedule and headlines, and a session opens what trades in it; the navigation pills fold on their own, the places pill starts under the top bar, and "Show names" is gone. `?review=off` shows the app edge to edge as it will be in its own window.

**The measured check** is `apps/qmx-desk/src/lib/dev/space-check.js` (how to run it is in the round-5 entry of `DESIGN-LOG.md`). On the Overview it went from 90 failing widgets and 31 failing tab pages to 1 failure: "Running now" opened in a tab at 1280x720, worst case, largest text, with the review frame off. Four more cases are near the limit. Run it after any change to widgets.

**Not done, left for their own sections:** the Trading board and its unit cards, the Units list page, pod pages. The new Open positions, Nodes and Regime readings cards also appear on Trading because both boards share them. Saved layouts were reset once by this round.

**The lead checked by clicking:** the Overview with the review frame off, and "Units on paper and live" opened in a tab. Everything else in this section is from the builder's report.

## What is next, in order

1. His verdict on round 5 (space and sizing). This has failed four times; do not move on until he says it is right.
2. **Sessions: the copilot and the agent system.** He said this is next and that it is "a long one". Ground on inspiration first, the chat input above all ("many agents fail at that"). His earlier wants are in `LEDGER.md` section 4 and `INTENT.md` model 6. The current Sessions page he called "beyond ugly". The Copilot button in the top bar may move or go. His own idea to test: instead of agents everywhere, "one singular agent panel with proper grouping or color coding". The methodology (QMX's skills and standards, "like BMad") needs a home here. Workflows and chat are the two things "we are going to really cater for a lot".
3. **Mini apps.** How many open at once look in the pill, what a mini app's page is, and how they declare UI. Ground first on how Anthropic shows plugin and MCP Apps UI in Claude Desktop and Claude Code. He believes about 80 mini apps exist; the code at `engine/base` `3ae41ffc` has 7 app folders and about 60 workflow templates, so ask him which he means or check newer branches (he named QMB among them).
4. **Home, the rest:** `briefs/section-home.md` (the desk waking up from day one, the Markets view, widgets that follow each other). Day one "is a lot of text"; he wants the backend's own facts to fill it in, and the journeys to shape it.
5. Then, as he raised them: Workflows; the **Lab** ("a very important piece of this entire puzzle", likely to change); Units (he wants them kept in the Library with a preview card and a detailed view); the notifications page; search, including search inside mini apps; Usage; a logo and a start-up card like cTrader or JetBrains (he asked about sound effects too); the phone companion later.
6. Small fixes he noted that no brief has yet: the pill icons differ between day one and Overview (make them one set); "weird sort of bars" on the board (explain or remove); the market clocks do not keep real time.
7. When a section is agreed, write its rules into the kit so later builders follow them. Each section also pulls in its items from `INTENT.md` "Drawn or asked for, never built", and designs its cross-place journeys step by step (for example, the Lab starting a new project).

## The loop for every section (the method he agreed to, in order)

1. **Ground.** Read what the kit already holds for the section: his words, the ledger, the journeys in grounding 08, the backend facts. Send one research builder only for what is missing. Verify any fact you will state.
2. **Inspiration.** A builder scouts landing and product pages (not documentation) with the built-in browser and returns a short list; you look at the best few yourself.
3. **State the question** for the round in one line, and the options that differ in kind, each with a name.
4. **Brief.** One file per round in `briefs/`, pointing at `round-2-shared.md`, `SPACE-RULES.md` and the log. Name what is protected. Name who owns which files.
5. **Build.** Background builders, Opus 5.5, one per option or one per job. You wait. If his message changes a builder's job, steer it or stop it.
6. **Check.** Click each result yourself in his browser, then tell him what to click, what you checked and what you did not. Run `apps/qmx-desk/scripts/space-check.mjs` if it exists.
7. **His verdict.** Log it in his words. Lock the winner; delete the losers.
8. **Worst case and space rules**, then write the section's rules into the kit and add backend needs to `BACKEND-ASKS.md`.

## Starting tomorrow

He should not have to dictate anything again. When he says good morning: tell him in a few lines where round 5 ended (check the log and the app), then start step 1 of the loop for **Sessions** unless he says otherwise. `refs/his-words-2026-11-10-design.md` holds all 22 messages he sent on 2026-11-10, verbatim. What this file and the log first missed is in the log's last section, "Added after the double check".

## How he works

- He dictates long, wandering messages late in the day. Read for the decisions; quote him in the log.
- He watches and clicks while builders run and may not reply. Carry on; ask only when a decision is his.
- He reads short replies. Lead with what changed and what to click. Detail goes to the kit.
- He is non-technical. No codenames, no jargon, no file dumps.
- Grounding and research results are for you. Do not report them to him unless he asks: "most of the grounding is for you."
- He judges the app as if it were live, in its own desktop window, not as a browser demo.
- When a problem is technical (sizing was one), look for a skill that fits before reinventing.
- Everything in the Obsidian storyboard (see `SOURCES.md`) is fundamental unless you agree a better idea with him.
- His browser is Brave, driven through the `claude-in-chrome` tools. Builders must use the built-in browser only. When you test in his browser, undo what you changed (for example reset a layout).

## Lessons from today, so he does not have to repeat them

1. **Do not build yourself.** Brief builders; wait; check their work by clicking before telling him it is ready.
2. **Ground before generating.** He stopped a round because builders went out before the grounding was done. Research first, then options, then builders.
3. **Use the skills, do not just read them.** He meant the whole set he collected, installed and set up, not only `frontend-design`; and our own component library (`/components`). For wiring and technical shape, `poteto-mode` or another fitting skill. Every builder invokes `frontend-design`, `emil-design-eng`, `apple-design` and `break-ui`; `variant-picker` when there are options; the `principle-*` skills for technical shape.
4. **"Look at the old UI" means port what it did, all of it.** Four sizing failures came from reinventing, then from porting half. Run the old UI, read its code, list its behaviours, and check each one off.
5. **Empty space is his oldest complaint.** A widget or page with a hole in it fails, whatever else is right. Check against `SPACE-RULES.md`.
6. **Never replace something he praised.** A builder swapped his favourite day-one screen during a merge. Briefs must name what is protected.
7. **One question per round, with options he can flip.** Then lock the answer and delete the losers.
8. **Verify a claim before stating it as fact** ("the backend has no widgets" had to be checked in code when he asked).
9. **References are for patterns.** The sidebar video and the app list were only examples; do not treat an example as his taste.
10. **Do not push your own preference after he has ruled.** He chose the Board over the lead's lean.
11. **Each page is designed on its own.** Only the frame, board behaviour, look and "go deeper" pattern are shared.
12. **Keep the kit current as you go**: rulings in `DESIGN-LOG.md`, backend needs in `BACKEND-ASKS.md`. He asked for this so nothing is lost at compaction.
13. **Builders report gaps honestly; pass them on.** Say what you checked yourself and what you are taking from a report.
14. **Subagents: Opus 5.5 by default.** For builders today he allowed Fable 5.1 or 5.2 as well, but Fable uses a lot while you also run, and Opus 5.5 is fine with precise instructions; you wait while they build. One builder per job; builders never spawn their own; builders that would edit the same files run one after another.
15. **Check who made an old choice before calling it a mistake.** The October amber borders the lead called a mistake were his own idea.
16. **Do not drift back to the October look.** He started over partly because the old aesthetics are "ugly" now.
17. **Give every brief a range: where the work starts and where it stops.** A spacing round wandered into unit cards and Trading, which had not been designed yet; he caught it in the builder's log. His correction: a brief may cover several areas, but it must have a scope "like a mathematical range, a start and a limit". Say what is in, say what is out of bounds, and have the builder report every file it changed outside the range.
18. **Use the planning skills to set that range before briefing.** He said the skills exist to scope the work, and that the lead has many it is not using. Before a section's brief: `wayfinder` to map a big piece of work as decisions resolved one at a time; `poteto-mode` (its playbooks for a feature, a prototype, visual parity and orchestration) for how builders work; `blast-radius` to find what a change could break elsewhere; `architect` to sketch the shape before code. Invoke them; do not just name them in a brief.
