# 04 Earlier design method (UI sessions, 2026-10-01 to 10-22)

Read-only grounding for the next design pass. It covers how the earlier UI work was done, what the operator ruled about the look, and which references were used.

**Sources**
- **S1:** main UI session 063611de, `Desktop/QMX-session-for-Codex/QMX-UI-session-raw.jsonl`. All 37 of his own messages and 11 question answers were read in full.
- **S2:** UI session 2c89d97c, 2026-10-14. All 14 of his messages were read.
- **S3:** later sessions, 10-12 to 10-22, filtered by keyword.
- **Notes:** `UI-LEDGER.md`, `UI-BACKLOG.md`, `DESIGN-RULES.md`, `handoff/README.md`, `session-summary.md`, `workroom/research/2026-09-14-refero-exploration/README.md` and the memory files.

Times are UTC as recorded; his local time is about three hours later. Quotes are his own dictated words and are kept short.

---

## 0. The short version

1. **Why it had structure.** The earlier agent built on a real component library, not on drawings:
   - shadcn-svelte with the Rhea preset;
   - one tiling board (`TileBoard`) used on every screen;
   - one widget frame;
   - a catalog of panels.

   It worked one screen at a time, after he forced that on 10-02. It showed 2-3 options, he picked, it built in code, then clicked through at 1280, 1600 and 1920 wide. He judged the running app in a browser, never a canvas.
2. **His praise was for structure and function.** He praised the tiling and minimise, the panels, the scenario generator, the runs table, the pods, the road to live, the Library reshuffle, the themes and the player cards.
3. **His complaints were the same five every time:**
   - text too small;
   - wasted space, judged at full-screen desktop;
   - too many words and too little to click;
   - clutter;
   - designs "borrowed" with "no intention".
4. **Own spin.** "Not borrowing from anyone" (10-04 09:50). Inspiration is fine; copying a look or layout is not. Mechanics (how plugins work, how a copilot adds UI) may still be studied.
5. **Canvas work failed twice.** The 10-01 Claude Design canvas came out as a blank page for him on 10-02, and no rail option was ever picked. Today's canvas drafts were called ugly (memory `ui-design-in-code-not-canvas.md`). Design in the real SvelteKit code.

---

## a) His verdicts on look and design

### Praise
| When (UTC) | What | Quote |
|---|---|---|
| 10-01 09:20 | First rebuild from the storyboard | "usable right out of the box" |
| 10-01 17:09 | Claude Design "Claude's take" page | "I'm liking this... it just looks better than the other one" |
| 10-01 17:18 | Glass and ink theming | "theming is freaking cool" |
| 10-01 17:18 | OpenBB-style widget (minimise, expand, add to chat) | "this is fucking cool" |
| 10-01 18:02 | Theming overall | "The thing you've got really really well is the theming" |
| 10-02 09:46 | Overall | "design I'll give you marks... but layout and usability this is very poor" |
| 10-02 09:46 | Player cards for bots | "the card idea is bloody, bloody brilliant" |
| 10-02 09:46 | Edit layout and add widget | "That's a nice touch" |
| 10-02 11:30 | Lab, panel system, scenario generator, runs table, minimise reflow | "the lab, you've outdone yourself"; "the panel thing is insane" |
| 10-03 09:17 | Whole app after nine months of trying | "for once I'm seeing it come to life" |
| 10-03 10:01 | Pods, road to live | "the pods are insane"; "Road to Live is fucking nice" |
| 10-03 10:22 | Portfolio | "you've done a bloody brilliant job" |
| 10-03 12:12 | Library (shelves, preview to full page, where-used, templates) | "library is mind-blowing how much you've transformed it" |
| 10-03 12:12 | Pods | "the pods I think is one of your best products" |
| 10-03 12:12 | Theme editor with colour picker | "this is so cool" |
| 10-14 07:43 | Home, desk, Settings, Apps on resume | "most of it looks okay to me, maybe adding some more personality, to the animations" |
| 10-14 08:44 | Layout in general | "Most of the layout is perfect. The remaining issues are... the text... and the clutter" |

**Screens he liked best, and why:**
- **Lab:** many working tools on one tiled board, editable layouts, real-feeling controls.
- **Pods and road to live:** a new idea he "would not have come up with", and visual progress.
- **Library:** the three-pane layout, preview to full page, where-used links and cards.

The common thread is function you can click and space that is used well.

### Complaints
| When (UTC) | Topic | Quote |
|---|---|---|
| 10-01 09:03 | Spacing, copilot quick chat | "some stuff looks irregular, other stuff looks like there is a lot of space" |
| 10-01 17:18 | Scrollbars | "They're ugly as hell" |
| 10-01 17:18 | Text size | "the text font is so small, it's not even funny" |
| 10-01 18:02 | Plain theme | "the plain one is ugly, you can add more themes" |
| 10-01 18:02 | Home | "it lacks style" |
| 10-01 19:00 | Consistency across mini apps | "the components are not consistent" |
| 10-01 19:00 | Full-screen space | "when i put it on full screen there is a lot of space" |
| 10-01 19:00 | Personality | "the whole platform needs a little bit more personality" |
| 10-02 09:46 | Words vs function | "I have more words than actual intentionality so I can't use a bloody thing" |
| 10-02 09:46 | Settings | "a settings panel is a settings panel dude" |
| 10-02 09:46 | Method | "you are giving less time to almost anything" |
| 10-02 09:46 | Trading node colour | Colour the tile border blue, "not the bloody radius of the entire UI" |
| 10-02 11:30 | Overflows, chips | "there are lots of overflows"; tools should be "an icon, maybe with a number" |
| 10-02 11:30 | Drop-downs | "these drop-downs lack styling" |
| 10-02 11:30 | New-session greeting | "I don't like this thing you've added" |
| 10-03 09:17 | Books page | "more text than anything... buttons are too small the text is too small" |
| 10-03 10:22 | Too many tabs | "these tabs are so many dudes" |
| 10-03 12:12 | Library articles | "a bit compact"; the Library "lacks actually more personality" |
| 10-04 09:50 | Copilot | "text is a bit too small for my eyes"; "everything seems a bit too compact" |
| 10-14 08:44 | Apps page | "This is ugly"; it took the Docker analogy "literally" |
| 10-14 08:44 | Text and clutter | "a little bit more text than actual functionality"; "We need more space... more white space" |
| 10-14 08:44 | Bloomberg | "I get we are getting the idea from Bloomberg terminal, but still, no" |
| 10-14 08:44 | Mixed patterns | "at times you're using cards, at other... times you're using tabs" |
| 10-14 08:44 | Settings | "so many words. There is little functionality" |

### Fonts, density, icons, colours, themes (rulings that stand)
- **Fonts and density**
  - Bigger fonts are a standing rule. Base text is 17px, in rem only. Settings, Appearance has a Text size choice: Standard, Large, Larger (10-04).
  - Fonts are Inter (variable) and JetBrains Mono for numbers. Numbers are tabular and never wrap.
  - Judge spacing at full-screen desktop (1920-2560). He hates both unused space and cramming.
- **Icons**
  - Lucide everywhere. On 10-14 he checked and accepted them: "you are using icons, my bad".
  - What is missing is identity: a QMX logo mark, app and pod icons "with character", a Library identity.
  - Use icons with count badges instead of word chips (10-02).
- **Colours**
  - Paper is orange and live is blue, on tile borders only (10-01, 10-02).
  - Link groups colour tile borders (violet, amber, teal).
  - Bot card art is coloured by family, for example a scalper in blue and gold, or editable as a preset (10-02).
- **Themes and backgrounds**
  - Frosted glass with an ink-map background, taken from the Hermes agent and Arch Linux wallpapers.
  - The background art is trading-themed: fractals, contours, candles, halftone, liquidity. Variants can be saved.
  - Seven themes: ink, cobalt, ember, graphite, moss, violet and paper (light). He can edit them with a colour picker.
  - Surface styles: glass, liquid glass, solid, brutalist. Of those he said "I don't think I'll ever use that" (10-03).
  - Themes stay on trading screens too. The real fault was see-through panels, now on solid backing (10-03 answer).
  - Wanted but not built: background art "not just lines", and a generator that changes the wallpaper now and then.
- **Personality and motion**
  - Wanted: purposeful animations, and a start-up like Photoshop, PyCharm or cTrader, where "QMX then... the world is filling slowly by slowly based off the theme" (10-03).
  - Built last, in eea09941: QMX draws in, tiles settle in turn, art fades up.
  - He has not reviewed it.
- **Words**
  - DESIGN-RULES.md (10-14) holds the word budget: a title, numbers and controls, and at most one subtitle line.
  - Explanations go behind an info tip.
  - Use tables for many rows and cards only for things you own.
  - No tabs inside tabs.
  - Panels have compact, regular and expanded sizes.
  - One Demo chip per page.

### The "own spin, not borrowed" ruling and its nuance
- **10-01 09:03:** "you need to add in more spin"; "I think we need to pick more inspiration". He was pushing for more inspiration, not less.
- **10-01 17:18:** "Think of it like a dashboard. Come up with your own inspiration".
- **10-03 12:12:** "look at the Codex desktop app for design reference in terms of the main copilot".
- **10-04 09:19:** "we are not going to reinvent the wheel" (DeepSeek Harness, bb). He meant mechanics.
- **10-04 09:50, the ruling:** "the references we used were a bit poor"; "have our own spin onto the co-pilot panel, not borrow it from other applications"; "there is literally no intention behind the design"; "Not borrowing from anyone"; "Where you want inspiration, you can look for it."
- **How the agent recorded it** (UI-BACKLOG 10-04): inspiration is allowed, copying is not. Other apps may be studied for mechanics, not for look or interaction.
- **DESIGN-RULES §7:** "Our own design. The Bloomberg terminal is a reference for density, not a look to copy."
- **In practice:** the copilot passes that copied T3 Code, bb and DeepSeek Harness were rejected. The panels he loved came from his own storyboard, with OpenBB-style widget controls and Bloomberg-style space management, rebuilt in QMX's own shapes.
- **Today (2026-11-09):** he is again asking for inspiration first (refero.design, Pinterest). See c).

---

## b) The design method the earlier agent used

### The loop (his ruling, 10-02, after "you are giving less time to almost anything")
UI-LEDGER "Rules", memory `ui-one-screen-at-a-time.md`:
1. One screen per pass. Finish it to a usable standard before the next.
2. **Research.** Docs, plus product references. For the Lab, two helper agents: one read the docs, one studied StrategyQuant, QuantConnect, MLflow, node editors and Bloomberg. Findings were marked "for ideas only, not proof".
3. **Show 2-3 whole-screen layout options.** For the Lab these were A Workbench, B Evidence first, C Tiling cockpit. They were offered as AskUserQuestion choices with one-line descriptions. He picked "C with A and B inside", adding "surprise me".
4. He picks. "Surprise me" is a real answer that grants design latitude.
5. **Build in code.**
6. **Click through like a user.**
   - Actions: click, drag, minimise, edit layout.
   - States: a small window (1280) and full screen (1920, 2560); empty, overloaded and seven-accounts states.
   - "Screenshots alone don't count."
7. List backend needs (BACKEND-REQUIREMENTS.md) and write the ledger entry.

**Design skills on every pass:** `frontend-design`, `design-system-compliance` and `verify-ui-change`.
- He asked on 10-02: "Do you have the front-end design skill?" The agent admitted it hadn't been using them.
- On loading, `frontend-design` flagged generic tells: all-caps panel labels, the same rounded card everywhere, and "A · B" strings.
- On 10-14 the agent also proposed `prototype` / `artifact-design` for clickable options, `taste-skill`, `shadcn` and `audit-my-app`.

**Where it slipped:**
- Home (about 6 minutes), the copilot desk (about 10 minutes) and Settings were built without the options step and without a click-through.
- The independent review (`handoff/research/session-review.md`) called copilot pass 1 "a good-looking storyboard of one scripted conversation, not a working screen".
- Those are the screens he was least sure of.

**10-14 refinements:**
- He dictates a walk-through of the running app.
- The agent first recorded rulings ("Ruling that drove this") in the ledger. Then came a declutter pass with word and control counts measured before and after (for example, Apps main view went from 380 words and 21 controls to 143 words and 34 controls).
- Screenshots and scripts at 1280, 1600 and 1920 went to `workroom/ui-review-2026-10-01/2026-10-14-*/`.
- Builders ran one at a time. He then ruled that small UI fixes are done directly, not by agents ("stop wasting tokens", 10-14 14:35).

**Later rulings (10-16 and 10-18):**
- "don't read the UI code... Read the screenshot... Code is for design."
- "Look at the bloody UI in terms of design... design carried more intent."

### Stack and building blocks
- **Stack:** SvelteKit 2 static SPA, Svelte 5, Tailwind 4, shadcn-svelte 1.7.0.
- **Rhea preset b27GcrRo:** applied on 10-01 in commit ff48dac1 with `pnpm dlx shadcn-svelte@1.7.0 init --preset b27GcrRo --reinstall --base-color neutral`.
  - It came from the architecture seed `architecture-QMX-UI-2026-09-23` ("DESIGN = neutral dark Rhea").
  - He had pointed at shadcn's MCP and community components on 10-01: "you don't have to work from scratch".
- **Other libraries:** bits-ui, paneforge, @xyflow/svelte (node editor), lightweight-charts, CodeMirror 6, Lucide, Playwright.
- **Primitives:** 17 in `src/lib/components/ui` (badge, button, card, dialog, dropdown-menu, input, kbd, popover, resizable, scroll-area, select, separator, skeleton, slider, switch, tabs, tooltip).
- **Component library page:** `/gallery`.
- **Catalogs:** `lib/qmx/catalog.ts` is the registry the copilot is meant to build from. There are per-screen panel catalogs in `lib/lab`, `lib/portfolio` and `lib/home`. The rule is that the copilot builds only from the catalog, never raw HTML.
- **Tiling board** (`lib/workbench/tiles`):
  - one tree of splits used by Home, the Lab, Portfolio and app screens;
  - saved layouts and layout templates;
  - linked tiles;
  - minimise docks the tile and the rest reflow, Bloomberg-style;
  - drag to swap, edit mode, + Panel.
- **Panel frame:** `WidgetFrame` gives every panel the same controls: add to copilot, minimise, expand, close, and an unknown-widget frame instead of an error.
- **Panel sizes:** `PanelBody` and `panelSize()` give compact, regular and expanded.
- **Other shared blocks:** `InfoTip`, `DemoChip`, `BoardWelcome` (day-one empty boards), `InkBackground` and `art.ts`, `StartUp.svelte`.
- **History:** the older `MiniAppShell` and `WidgetBoard` grid (10-01) was replaced by the tiling board and deleted on 10-14 (fc6e9f84).
- **Demo mode:** a real switch (`?demo=off`) under Settings, Developer.

### Screenshots and previews
**Widths:**
- 1280 and 1920 from the start, plus 2560 in the ledger rules.
- 1600 and 1280 in most October checks; 10-14 used 1280, 1600 and 1920.
- Playwright scripts captured them. Some are saved, for example `scripts/day-one-shots.mjs` and `scripts/day-one-boards-shots.mjs`.

**10-01 to 10-04:**
- The preview was `pnpm build`, then `pnpm preview` on 4173. The stale server was killed first.
- `pnpm dev` (5173) was tried only once on 10-01.

**10-14:**
- `vite preview` broke on every rebuild, so the agent copied `build/` to a scratchpad snapshot and served it with a 15-line Node static server, `tools/serve.mjs`, on 4173. It falls back to `200.html`; `/_app/` misses return 404.
- That script lived in the 2c89d97c scratchpad and is gone; the recipe is in that transcript at 09:14Z.

**Node and pnpm:**
- The machine runs Node v24.18.0. `package.json` wants Node >=22.12 <23, so pnpm prints an engine warning.
- The October notes do not record `pnpm dev` hanging; that claim is from today's work.

---

## c) Inspiration sources

| Source | How it was used or ruled |
|---|---|
| **His Obsidian storyboard** (`Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md`) | The primary source. The rebuild came "from the storyboard". It was based on VS Code / OpenBB layouts he circled and dictated over. His settings sketch (orange square, green oval) was never found. |
| **OpenBB** | The widget frame (close, minimise, maximise, add to chat). "The OpenBB is the thing I was looking for" (10-01). |
| **VS Code** | Sidebar and rail ideas, per-copilot session history "like Visual Studio Code", machine switching like VS Code remote environments (10-03), editable themes. |
| **Bloomberg Terminal** | Space management: minimise docks and the rest fill (10-02). News and events (10-03). Ruled: density only, not a look (DESIGN-RULES); "still, no" to Bloomberg-style clutter (10-14). |
| **StrategyQuant X** | Scenario generator, what-if, robustness tiers, walk-forward matrix. These are in the UI-BACKLOG "patterns to borrow" (mechanics). He loved the scenario generator. |
| **LSE terminal, xynth, primemarket (Prime Terminal), quantx, minara** (storyboard links) | 10-01: he chose "I browse them myself". The agent captured xynth and quantx and made "denser terminal-style panels from LSE/QuantX/xynth" (commit 4c7dcdc3) and a xynth-style chip composer. Minara was never reviewed. |
| **json-render, MCP Apps** (storyboard links) | Mechanics for copilot-built panels. json-render was never installed; a home-grown `lib/sdk/spec.ts` stands in. |
| **Hermes agent** | The ink-map background ("I wanted to have my own version of it", 10-01). Its website cards were a model for bot and article cards. Later (10-16) his main model for workflows, cron and memory, which is mechanics. |
| **Arch Linux wallpapers** | Background art idea (10-01). |
| **FIFA / FC player cards** | Bot and model cards: "Come up with your own version of that" (10-01). Built as EntityCard plus CoverArt with real measures and no ratings. 10-22: preview vs detailed view. |
| **Claude model-release collage** | Suggested look for bot and model summaries (10-01 18:02). |
| **Omarchy (DHH), Google web-apps** | Library sources as in-app web apps, RSS (10-01). |
| **Claude Design** | 10-01 canvas `claude.ai/artifact/RLoHwHm1gxLpuQnvWqYJ8e`: rail options A/B/C, "Claude's take" and a glass theme page. He liked "Claude's take" and the glass page, then saw a blank page on 10-02. Ruled 10-03: keep the current rail. Today (11-09) canvas drafts were rejected as ugly. |
| **Codex / ChatGPT / Claude desktop apps** | Named for the copilot on 10-03. SUPERSEDED for look by "own spin" (10-04). Mechanics, such as a real terminal, still count. |
| **T3 Code, bb, DeepSeek Harness** | He asked for them on 10-04 08:57 for mechanics. Copilot pass 2 followed them and was then called "an actual bloody wrong reference" (10-04 09:50). |
| **shadcn terminal component** | Named for the copilot terminal (10-03). Not built. |
| **Photoshop, PyCharm, cTrader** | The start-up screen (10-03). |
| **Karpathy X post** | Learning from papers as diagrams or video (10-03). Only "Explain it as" exists. |
| **refero.design** | Not used in the October UI sessions. A Codex-era study (2026-09-14, `workroom/research/2026-09-14-refero-exploration/`) covered Linear, Kraken terminal, W&B, Matter, fal, Exa and others, ending with "dense and calm are task states" and three arrangements (shared workbench, comparison bench, tool canvas). Its README says earlier generated layouts and his reactions were excluded. He named refero again today: he is signed in and will not pay. |
| **Mobbin, Dribbble, Pinterest** | **No mention in any session before November.** Pinterest appears only in today's memory note. Treat them as new. |
| **Claude Room, AMP** | 10-16: their UIs could host workflow and sandbox control, so less load on QMX's UI. Mechanics. |

---

## d) How to start the design preview today

From the notes, in `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui`. The branch head is eea09941. The untracked folders `src/lib/usage` and `src/routes/usage` come from today's work.

```bash
# Built preview, the documented way (port 4173). Stop any old server on 4173 first.
pnpm build
pnpm preview            # = vite preview --host 127.0.0.1 --port 4173 --strictPort
```

```powershell
# Stop whatever holds 4173 (used on 10-04)
Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue | % { Stop-Process -Id $_.OwningProcess -Force }
```

**Dev server with live reload** (port 5173, the host's default UI origin). This skips the `pnpm` wrapper and its Node-22 engine check:
```bash
node node_modules/vite/bin/vite.js dev --host 127.0.0.1 --port 5173 --strictPort
```

**If `vite preview` misbehaves after rebuilds** (10-14), serve a copy of `build/` with a small static server on 4173 that falls back to `200.html`. This is the old `tools/serve.mjs` recipe.

**Useful URL switches:**
- `?demo=off` or `?demo=on` toggles demo data.
- The Library article reader needs `QMX_DEMO_MQL5_DIR=C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library/md` set before `pnpm preview`.

Check every screen at 1280, 1600 and 1920.

---

## e) Specific areas

### Inbox and notifications
- **10-02 09:46:** "Then notifications, please... if there is an issue in markets that needs my attention, I want to be able to see this and give it some spacing on top."
- **Built:** a bell and a "Needs you" panel on Home. It holds copilot questions, promotions to sign, paper runs ready, raised kill switches and failed runs, each linking to its screen.
- **10-16 17:48:** "the notification system is different. So don't design it so much... I think it's UI based."
- **Today's memory:** both Inbox options were rejected. It "must be agentic": every item shows where it leads (a copilot session, a mini app, an agent in an app) and has quick actions.
- **Related:** refero 09-14 suggested Linear's inbox, which pairs events with objects and actors.

### Usage
- No Usage screen existed in October.
- **10-18 08:49:** he wants provider configurability with usage visible, the way CLI proxy shows it, with high-usage accounts used by default.
- **Earlier notes:** the 10-14 Settings had a "background agents' share of the Claude plan". Per memory `no-caps-in-qmx-providers.md` such shares are bugs.
- R4 lists a "usage page" in `tracker/qma-v2/UI-NOTES.md`.
- **Today's memory:** option A, with less text and more showing; refresh buttons; model routing moves from Settings into Usage.

### Workflows
- **10-02 11:30:** most agents in the Lab "will just be workflows"; he asked "What happens if you want to have a custom workflow?" Robustness can come from workflows.
- **10-03 12:12:** monitoring as a cron or workflow, "where will that go, will it be a mini app?"
- **R6 (10-08 to 10-12):** cron belongs to workflows. He prefers graphs and loops to an n8n-style node editor.
- **10-16 14:45:** "workflows will be created the same way... mini apps are created"; the Lab has a node editor but the copilot does not.
- **10-18 12:13:** "workflows are made in the lab"; "how workflows evolve into mini apps"; "design for complexity".
- **Today's memory:**
  - He loved Workflows option B, the day-at-a-glance dashboard.
  - Still wanted: count badges, colour-coded steps that need him, a create-with-copilot page, workflows inside mini apps, and layering.
  - Open question: what is the Lab for once workflows leave it?

### Lab user journeys (the new-project journey)
- **10-02 11:30:** "when I click Start Something New... think of it like a survey... it should walk me through all these things." Each journey is "specific to an experiment", with pre-configured steps and templates.
- **10-03 08:10:** for bringing outside work in, "I would prefer maybe we start just as a co-pilot session"; it uses ask-user cards and changes tabs (Build, Test, Train, Compare) automatically. Switching machines updates what the board shows: an empty state, not a 404.
- **Built:** `GuidedStart`, `LabStrips`, templates, Import (notebook, repo, file). On day one the boards show a welcome with Start from a template, New pod and Ask the copilot.
- **10-03 12:12:** "creating a new pod this one this one is that journey there needs a little bit of [work]."
- **Today's memory:** the Lab declutter was rejected; "keep the old Lab's project journey".

### Units and bot pages
- **Cards:**
  - **10-01:** player cards; the card should carry attributes, tests, connections, journal, paper and backtest results, and artifacts.
  - **10-02:** "the card idea is bloody, bloody brilliant". Colour by family, list vs card view, ML models should look different. The detail page is "very, very poor" with unused space.
  - **10-03:** the progress strip belongs inside the bot card. Each bot has a trading journal. Journals and logs live inside bots, models and pods, not on a shelf.
- **10-22 12:57:** the Library needs "a preview and a detailed view... when it should come, when it should not come", pointing back to the FIFA card part of this transcript.
- **Units:** the unit structure (risk and sizing) was still open in October (R5). Pod screens wait on it, and the vocabulary may change. Memory `pc-home-servers-substitute.md` says "units not bots".

### Trading node
- **10-02:**
  - A trading node is a VPS. Show server, provider, region, IP, latency, status and who uses it, and kill it from there.
  - Colour paper and live on tile borders.
  - Add order-flow charting.
  - Promotion does not belong on the node screen.
- **10-03:** folded into Portfolio, Live.
  - The kill switch is always visible in the Portfolio header, as a grid of pods by servers.
  - Positions go on top, with exposure and correlation as tabs under positions.
  - Each bot gets its own chart.
  - "Test latency, restart, drain" was praised.
- **10-14:** the wording is "Trading servers", not "the node". Servers fold into one chip below 1800 wide.

### Mobile
- No mobile design ruling was found.
- **10-16 14:45:** "I haven't looked at the phone UI... the mobile UI, I haven't really". He paused there and wanted design principles first.
- He often drives sessions from his phone (10-12, 10-19, 10-20) but did not ask for a phone UI.
- The September refero study warned that its iOS examples "do not establish a mobile QMX scope".
- Phone screenshots in `workroom/ui-review-2026-10-01/` (`home-phone.png`, `authoring-phone.png`) predate the rebuild.

---

## What this means for the next pass (from his record, not new rules)
1. Run the real UI first and click through it. Start from the existing shadcn, Rhea, tiling-board and catalog components. Do not draw on a canvas.
2. Gather inspiration first (refero, Pinterest and similar), then make it our own. Never copy a product's look or layout.
3. One screen at a time. Show 2-3 options he can click, in code, let him pick, then build and click through at 1280, 1600 and 1920.
4. Apply DESIGN-RULES:
   - big rem text;
   - word budget;
   - every block is data or an action;
   - tables for rows, cards for owned things;
   - no tabs inside tabs;
   - compact, regular and expanded panel sizes;
   - space at full screen used, without cramming.
5. Personality comes from identity (logo, icons with character, art) and purposeful motion, not from more words.
