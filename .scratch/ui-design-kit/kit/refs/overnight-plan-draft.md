# Overnight design run: brief and resume point (started 2026-11-09 night)

Read this first after any compaction. It holds his mandate, the rules, the loop, and the current state.

## His mandate (from his dictation, 2026-11-09, around 23:00)

- **Roles.** I am head of product design and act only as the orchestrator: I write no code myself. Builder agents run on Opus. Fable 5.1 is allowed as a **UI judge** only, never wasted. Do not use 5.2.
- **The challenge.** "Surprise me." References are starting points: give each my own spin, improve it, and look at the angles QMX needs (quant plus agentic trading, data heavy, extensible like Bloomberg, used by non-technical people).
- **Scope.** Finish T3 Code fully. Open every page, dropdown and thread, the Provider screen at the bottom, Pull requests, Usage, and the floating machine card at top right ("leverage it"). Then design and build a release-grade UI with demo data. Propose the wiring; do not wire yet, we talk in the morning. He hopes for a release version by morning, but it is not a deadline.
- **Things to design for:**
  - Agent workspace (one place, grouped like projects; T3-style bands and hover cards; sub-agents, tools, file changes, browser use and computer use made visible). In QMX terms, "file changes" are Library changes.
  - The orchestrator upgrade (Shepherd-protocol-style orchestrator plus the Hindsight memory, self-improving). It may or may not be built, so cater for it.
  - Shipped workflows and mini apps (macro and micro analysis, etc.).
  - The methodology session's scenarios (brainstorm, build a mini app, build a workflow).
  - The DevOps layer for the app, mini apps, workflows and agents.
  - Usage v2 with the add-provider journey and inheritance.
  - The Settings overhaul.
  - Themes: a true black like T3 Code, remove the "cloudy" look from Ink, and neumorphism if it can be done well.
  - The Lab restructure (pods, surfaces). Portfolio (too clustered).
  - Adding a machine in one click.
  - Use plans, branches and CIS user journeys from QMA v2 and other branches as sources.
- **Wiring.** Most of the backend is on `engine/base` (118 PRs merged today). No merge until about Wednesday.
- **Inspiration.** Pinterest, Mobbin (free tier only, never pay), Dribbble and others; his Chrome stays signed in. Skills: taste-skill (github.com/Leonxlnx/taste-skill), emilkowalski/skills. Videos via the watch skill: https://youtu.be/of628n5754g and https://benji.org/stageshow (stageshow plus Fable as the judge).
- **Checks.** Confirm what the Claude Agent SDK gives the UI (done: grounding/03).
- **Stack.** Stays shadcn-svelte unless there is a strong reason to change.
- **Budget.** Weekly usage at most 80%, at most 85% in a pinch. At the start it was 65% for all models and 46% for Fable (2026-11-09 night), so about **15 points for the night**. Agents run **sequentially**, one at a time, so each result can shape the next brief.
- **Thinking level.** He set it to high. Compaction is expected, so keep this file current.

## Rules carried in

- Design in the real UI code (`ui-review/repair`, SvelteKit, shadcn-svelte, Rhea preset), never on a canvas. Run the UI and look at it; never read UI code as a contract.
- One screen per pass. Inspiration first, then options, then build, then click through at 1280, 1600 and 1920.
- Few words, real controls, icons with tooltips. Preview first, detail one level down. Theme-aware colours.
- No pushes and no merges. Commits stay local on the design branch (see below).

## The loop (v2, reshaped by the skills; references copied to `plan-2026-11/skills-ref/`)

**His later corrections (same night):** his words are a baseline to iterate on, not a script. The budget is roomy (Ultra plan), so stay under 80% but don't starve the work; agents still run one at a time. Deliver **variants he can toggle**, not single versions. Look at X (signed in) for UI. T3 Code's "Orchestrator V2" is stable as of v0.1.0: subagents and background work are tracked; remote access goes through T3 Connect tunnels.

**What I took from the skills:**
- **Emil `prototype`:** every screen ships as 3 genuinely different variants, each on a named axis (never three tints of one idea), behind Emil's picker (PICKER.md, verbatim) on an isolated route `/prototypes/<slug>`. Nothing touches production routes until he picks. Each variant fully works with realistic content. He flips with the keys in the morning, then says "keep X" or "riff X".
- **Emil `break-ui`:** every prototype gets a data toggle (**Demo / Worst case / Empty / One / 1,000 rows**) at the data boundary. Worst case means plausible QMX data: long unit names, 14-digit balances, 400 runs, a node unreachable for 3 days, 1-character symbols, 0 trades.
- **Emil `emil-design-eng`, `review-animations`, `remove-animations`, the cheatsheet:** the craft bar.
  - ease-out under 300 ms, never ease-in;
  - animate only `transform` and `opacity`, with reduced motion handled;
  - tabular numbers, `-0.02em` tracking on large headings;
  - `scale(0.97)` on press, origin-aware popovers;
  - absolute dates after a week, real plurals;
  - nothing animates on high-frequency actions.
- **Emil `apple-design`:** read by the builder for the shell, theme and motion passes.
- **taste-skill:** built for marketing sites, so not used for screens. Kept: its idea of a **finish gate** (a script that loads every page in a real browser and fails on blank visuals or broken layout). Ours is a Playwright sweep: every `/prototypes/*` × each variant × each data state × 1280, 1600 and 1920 → screenshots in `plan-2026-11/shots/<slug>/`, plus console-error and overflow checks.
- **QMX lenses each variant is scored on:** extensible (can he add, remove or rebuild it?); data- and update-heavy (live numbers, many rows); fast to read; non-technical friendly (one-click journeys); shows where things run; preview first, detail one level down.

**Per screen (one pass):**
1. **Brief** (me): the screen's job, its user journeys (CIS/BMad journeys and plans from the branches), what it reads (`grounding/01` routes), worst-case data. Inspiration notes in `inspiration/NN-*.md` (T3 Code, Refero chat, Pinterest, X, Mobbin free).
2. **Build** (one Opus builder): 3 variants behind the picker with the data toggle, on the design branch, plus a wiring note per variant.
3. **Gate** (script): the screenshot sweep, console and overflow checks.
4. **Judge** (Fable 5.1, read-only): scores the variants against the lenses and the craft bar, lists breaks, and ranks them (a recommendation only; he picks).
5. **Fix** (the same builder resumes): one round on the judge's must-fix items.
6. **Ledger:** commit locally, tick the state list, write a one-line "what to look at".

**Order:**
- Foundation first: **themes as variants** (True Black, Soft/neumorphic, Ink refined), the shell (the floating context card with my spin, a surfaces panel, the rail), and the picker and data-toggle harness that every later screen reuses.
- Then:
  1. the agent workspace (absorbs the Inbox; run tree for the orchestrator, sub-agents, tools and Library changes);
  2. Usage v2 with providers and inheritance;
  3. the Settings sheet (scope lines, machines in one click);
  4. Workflows (day view, create with the copilot);
  5. the Lab as surfaces, plus pods;
  6. a Portfolio declutter;
  7. Home.

**Morning hand-over:** one page listing each prototype URL, its variants and their trade-offs, the judge's ranking, what broke under worst-case data, and the wiring map per variant.

## State (keep current)

- [x] Grounding 01–04 and the T3 Code first pass (`inspiration/01-t3-code.md`)
- [x] Usage A coded at `/usage` (to be redone as v2)
- [ ] T3 Code full pass (every page, desktop vs web noted)
- [ ] Videos and taste skills studied
- [ ] Plans and journeys mined (QMA v2, Shepherd/orchestrator, methodology, DevOps, CIS)
- [ ] DESIGN-DIRECTION.md, then the Fable review
- [ ] Theme v2 (true black, neumorphic option, Ink de-cloud)
- [ ] App shell: rail, floating context card, surfaces panel
- [ ] Agent workspace (it absorbs the Inbox)
- [ ] Usage v2 plus providers
- [ ] Settings sheet (scope lines, machines)
- [ ] Workflows (day view, create with the copilot)
- [ ] Lab: surfaces and pods; Portfolio declutter
- [ ] Morning summary
