# October UI trace: the ideas, not the layout

The October UI (branch `ui-review/repair`, head `eea09941`) is a **design proposal, never the product**. This file traces each idea behind it to three sources, so a fresh design session inherits the ideas and is free to drop the layout.

## How to read a row

- **Idea:** the idea in plain words.
- **He asked:** his own dictated words, short, with the UTC time. His local time is about three hours later.
- **Storyboard:** what his Excalidraw storyboard drew, or "not in storyboard".
- **Built:** the October screen and a screenshot file.
- **Verdict:** his words after he saw it.

**Marks**
- **NEVER BUILT:** asked for or drawn, never built.
- **REVERSED:** he later ruled against it, or it was replaced.
- **UNREVIEWED:** built, but he never judged it.

## Sources

- **T:** session 063611de, `C:/Users/Mubarak/Desktop/QMX-session-for-Codex/QMX-UI-session-raw.jsonl`, 2026-10-01 to 10-12. All 32 plain-text operator messages and all 11 question answers were read.
- **T2:** session 2c89d97c, 2026-10-14 (resume, declutter, day one). Quotes come through `ui-review-repair/apps/qmx-ui/plan-2026-11/grounding/04-earlier-design-method.md`.
- **SB:** `C:/Users/Mubarak/Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md`, drawn 2026-09-22 and decoded from its compressed block. It has 142 elements: two wireframes, 11 pasted images, red and blue call-outs and one long dictation.
  - `Drawing 2026-11-10 15.39.23.excalidraw.md` is **empty**: it decodes to `"elements":[]`.
- **SB images:** `C:/Users/Mubarak/Documents/brain/brain/Pasted Image 20260922*.png`.
- **Screenshot folders:** paths are under `C:/Users/Mubarak/Desktop/QMX/workroom/ui-review-2026-10-01/`.
  - **SF:** `2026-10-14-stale-fixes/`, demo data on.
  - **DC:** `2026-10-14-declutter/<area>/after/`, demo on.
  - **D1:** `2026-10-14-day-one/`, demo off; D1v2 is `2026-10-14-day-one/v2/`.
  - **vNN:** the October rounds `v2` to `v24`.
- **Ledger:** `UI-LEDGER.md`. **Backlog:** `UI-BACKLOG.md`. Both are in `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/`.

### What the storyboard holds (every element group)

| SB group | What it shows |
|---|---|
| A. Top wireframe | A thin rail on the left. A tab strip across the top. Four widget boxes. A copilot column on the right with tabs, chat and a message box marked with a diamond. An arrow points to the OpenBB image. Note on the strip: "this top bar is ideal… some apps might not need it… a reusable component." Note on the layout: "more like the first layout… could serve more of an app layout." |
| B. OpenBB + VS Code images | The OpenBB Pro dashboard: widgets with history, add-to-chat, menu, expand and close, plus a copilot pane. A VS Code window with a Codex side panel. Note: "the layout is what I'm picking… OpenBB developers took the exact same thing." |
| C. Copilot wireframe | A rail, then the main chat with a message box. Then a column of stacked session rows: "open sessions, history settings for the agents". Then a big preview panel: "agentic browser… preview for mini apps… widgets… workflows… sub-agents… CLIs… strategy cards… live browsing, video watching… diff view… the terminal can also be in here." |
| D. Session-sidebar examples | Images of the Hermes Agent desktop (sessions, capabilities, scheduled jobs, crew, kanban; a browser pane; ink background), the Codex desktop (sidebar, chat, side panel with Review, Terminal, Browser, Files and Side chat) and Claude Cowork ("You're here!"). |
| E. "Or we can try these ones" (diamond) | Images of Manus (project page with Instructions, Files and Skills cards), the Cartesia voice library (filter column and chips) and the Factory "Select workspace" step. |
| F. Orange box (settings) | An image of the Factory Settings page: big title, pill tabs (General, Integrations, Session, API Keys, Billing & Usage), cards with toggles, a workspaces table with actions. Note: "a very different approach… an idea settings page… this one is global… each app needs its own." **This is the "orange square" settings reference the October agent never found.** |
| G. Annotated OpenBB (red and blue call-outs) | "this is the expansion tool"; "history thing"; "this thing (editing the set up of widgets)"; "message icon" (add to copilot); "thing at the bottom" (add panels); "the thing… for risk mgt and bms stuff" (revenue per business line chart); blue: "this can help us go from preview mode to library"; orange: "this is for the expanded view of a widget or workflow". |
| H. Long dictation | Covers several ideas:<br>- Mini apps are dashboards of expandable widgets.<br>- The message icon on every widget links it to the copilot.<br>- The top menus of a mini app change with the app.<br>- Expanding a widget opens a new tab with the detail view.<br>- A mini-app copilot has different permissions and tools (MCP apps).<br>- json-render for widgets.<br>- The rail: a main menu, a thick line, then the opened mini apps below it.<br>- A main Home dashboard always present.<br>- A design system or SDK for mini apps.<br>- The node editor versus code.<br>- Links: json-render, MCP Apps, xynth, primemarket, quantx, minara, LSE terminal. |
| I. LSE video | An embedded `terminal-preview.mp4` ("lse vide"). |

---

## 1. Shell and rail

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Fixed rail of places, settings at the foot | "the sidebar I minimized… any more ideas?" (10-01 09:20) | A, C: thin left rail | Rail: Home, Copilot, Library, Lab, Portfolio, Apps; Settings at the foot (`lib/workbench/destinations.ts`). See SF `1600-home.png` | Claude Design rail options came out as a blank page for him (10-02 09:09). Answer 10-03: keep the current rail. |
| Opened mini apps sit on the rail below a divider. **NEVER BUILT.** | Storyboard dictation only | H: "a thick one… the remaining new icons below that line represent… applications that have opened" | Divider drawn; no opened apps (Ledger, Apps pass 1 "Not done") | None |
| One tiling board everywhere (minimise docks, the rest fills) | "if I minimize… the top fills up. Space management… Bloomberg Terminal" (10-02 09:46) | A: widget boxes; G: expansion tool | `TileBoard` on Home, Lab, Portfolio and app screens: link groups, drag swap, edit layout, + Panel. DC `lab-home/after/lab-test-1600.png` | "you've really done the minimizing thing quite well" (10-02 11:30); "the panel thing is insane". The mixed patterns were judged later: "at times… cards, at other… tabs" (10-14 08:44, T2). |
| One widget frame: history, add to copilot, menu, expand, close | "That widget thing… close, minimize, maximize" (10-01 09:20) | G: every red call-out; B | `WidgetFrame`: link, minimise, expand, and "Add to copilot" on items | "this is fucking cool" (10-01 17:18, per grounding 04). The frame was his OpenBB pick. |
| Widget history (time travel). **NEVER BUILT.** | Not asked in chat | G: "history thing i mentioned" | No history control on tiles | None |
| Expanding a widget opens a detail tab | Not asked in chat | G orange: "expanded view of a widget or workflow"; H: "it opens a new tab… shows a detailed view" | Expand fills the board, with compact, regular and expanded sizes (`panelSize()`). No new tab. | No verdict on the expand behaviour itself |
| Preview to Library jump from any widget | Not asked in chat | G blue: "go from preview mode to library" | "Used in" links, the Library deep links `?shelf=&item=`, "Open in Lab / Portfolio". SF `1600-library-bots.png` | "this cool thing of where it's used" (10-03 12:12) |
| Edit layout and add or build widgets | "I can add widgets? Heck no way!… That's a nice touch" (10-02 09:46) | G: "editing the set up of widgets", "thing at the bottom" | Edit layout, + Panel, saved layouts, templates | Praised. "Build a new panel" was left to copilot skills (Ledger, Lab round 2) |
| Status bar: compute and machines at the bottom | "compute… something to show… a status, maybe at the bottom" (10-02 11:30) | Not in storyboard | Bottom bar: "Not connected to daemon · 3 of 4 machines · 4 jobs" (every SF shot) | Accepted (10-03, no complaint) |
| Pop out any screen, kept in sync; several screens | "Can I have ability to add multiple screens" (10-01 19:00) | Not in storyboard | "New window" on the desk (SF `1600-desk-after-send.png`). No sync and no multi-monitor layout. | "it actually exports in a new window… never thought of" (10-03 12:12). Sync and multi-monitor: **NEVER BUILT** |
| Notifications with room at the top | "if there is an issue in markets that needs my attention… give it some spacing on top" (10-02 09:46) | Not in storyboard | A bell plus a "Needs you" panel on Home (`v23/2-bell.png`, DC `home-today-1600.png`) | 10-16: "the notification system is different… I think it's UI based". 11-09: both Inbox options were rejected; it "must be agentic". **REVERSED as designed** |
| Paper or live shown on tile borders only | "border… in paper mode… orange… blue" (10-01 19:00); "not the bloody radius of the entire UI" (10-02 09:46) | Not in storyboard | Orange and blue tile borders (SF `1600-portfolio.png` pod cards) | Accepted 10-02 11:30 ("You can color code the border itself") |

## 2. Home

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| A main dashboard that "shows everything running" | Storyboard dictation | H: "that main home dashboard, which shows all everything running… always there" | Home on the tile board, with Today, Markets and Research tabs (DC `lab-home/after/home-today-1600.png`) | First version: "it lacks style" (10-01 18:02); "you've left so much space" (10-01 19:00) |
| Your own tabs (Home as "my dashboard") | "I want to be able to add new tabs. So it's more like my dashboard" (10-02 09:46) | Not in storyboard | Saved tabs on Home (chevron beside Research) | **UNREVIEWED** (rebuilt 10-04 in about 6 minutes, 7fa36fb5). 10-14: "most of it looks okay" |
| Drop the word "Home" | "we don't need this home word" (10-02 09:46) | Not in storyboard | A greeting replaces the title ("Good afternoon") | **UNREVIEWED** |
| Live ticker, editable by hand or by the copilot | "maybe… a live trade ticker" (10-01 18:02); "this ticker above needs to be customizable" (10-03 12:12) | Not in storyboard | Ticker strip with an edit control (DC `home-today-1600.png`) | "I like the Tika idea seriously" (10-02 09:46) |
| News lives on Home with room, crypto then FX, with sentiment and a named source | "News is not meant to be the library, it's meant to be on the home page" (10-01 19:00); "sort them by crypto and then… fx… sentiment" (10-03 09:17) | Not in storyboard (OpenBB shows a news widget) | News and events panel with All / CFDs / Crypto, a score and its source | "every little bit of information… should have a source in our back end" (10-03 09:17). No later verdict. |
| Markets for one broker or many accounts | "what if I want to connect one specific broker?" (10-02 09:46) | Not in storyboard | Markets panel with an "All accounts" filter (10-14) | No verdict |
| "While you were away" holds many parallel jobs | "nine models… training… I don't think this will give me enough" (10-02 09:46) | Not in storyboard | "Going on" folds a batch (nine Colab trials) into one row (10-14) | No verdict |
| Copilot-made widgets (json-render), e.g. a screener | "I want to see how the co-pilot can create a new widget" (10-02 09:46) | H: "for the widgets, I was proposing JSON render" | Screener drawn from a panel description (`lib/sdk/spec.ts`); json-render was never installed | No verdict |
| Home needs a full rethink | "home needs another refurbishment like a long very very long one… an actual rethought" (10-03 12:12) | — | 7fa36fb5 skipped the options step | 10-14: "most of it looks okay… adding some more personality" |
| Day one: Get started steps | "how it will look… fresh out of the box" (10-03 12:12) | Not in storyboard | Four Get started cards with demo off (D1v2 `home-1600x900.png`) | **UNREVIEWED** |

## 3. Copilot

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| A desktop-class agent app: sessions, chat, side preview | Answer 10-04 08:51: "not so different from the Codex desktop app or the ChatGPT desktop app and the Claude desktop app" | C wireframe; D: Hermes, Codex, Claude images | Pass 1 (47a65197, `v21/`), pass 2 (83b87f71, `v22/`), then "the desk" (6b4d247a, `v24/`, SF `1600-desk-after-send.png`) | Pass 1: "you may have not done it quite well" (10-04 08:32). Pass 2: "references we used were a bit poor… no intention behind the design… Not borrowing from anyone" (10-04 09:50). **REVERSED:** copying T3 Code, bb and DeepSeek Harness |
| Sessions column with history; collapses on its own; per-copilot settings | "history and settings for the agent… multiple sessions… on top, like Visual Studio Code" (10-02 09:46) | C: "open sessions, history settings for the agents" | Errands column (Needs you, Working, Earlier); the gear opens Settings, Copilots | Desk: **UNREVIEWED** beyond 10-14's "looks okay" |
| Preview pane: browser, terminal, diff, sub-agents, mini-app preview | "we haven't done the terminals… the browser integration" (10-03 12:12) | C: the big preview panel text | A drawer with helpers, terminal (demo echo) and browser (iframe); a Diff tab in pass 2 | Backlog: "Do not tick until both are real". Real terminal and browser: **NEVER BUILT** |
| One session crosses Lab, pods, Portfolio and mini apps; sessions run for days | "one session… start an experiment in the lab… touch a pod then look at portfolio" (10-03 12:12); "sessions that can run for days" (10-03 10:01) | Not in storyboard | Showcase "Weekend-safe pod, end to end"; "Continue in the main copilot" | No verdict on the mechanism |
| Sub-agents visible (what each is doing) | "how do I know which tasks are running in the background" (10-03 12:12) | C: "open for sub-agents" | Sub-agents as child threads with Back (`v22/3-subagent-thread.png`) | No verdict |
| Attachments shown in messages; attach depends on context | "attach also needs a rethink… for mini apps it's a different case" (10-02 09:46) | Not in storyboard | Attachment cards; the attach source differs per screen | No verdict |
| Tools as an icon with a count, not word chips | "you can just use an icon, maybe with a number" (10-02 11:30) | Not in storyboard | Composer icons with badges (SF desk: key icon with a 3) | Accepted |
| "Aim this message at" (target) rethink | "this attachment of aiming the message at part needs… rethink" (10-03 12:12) | Not in storyboard | Mode and reach: Ask / Plan / Do + areas | **REVERSED** 10-09: "I don't want a planning mode"; modes removed 10-14 (d40b1135); the chip now reads "4 of 6 areas" |
| Agent requests (approve agent work) | Built unasked | Not in storyboard | Was in Portfolio, then moved to the Lab | **REVERSED:** "I don't think I'll send an agent off… and it still needs my permission" (10-03 10:01) |
| New-session greeting / "How do I…" | Built unasked | Not in storyboard | Greeting plus HowDoI | "the way it begins, I don't like this thing you've added" (10-02 11:30). Greeting removed in 8ef175ad; HowDoI was never confirmed |
| Copilot builds UI under rules (catalog only, no overflow, keep or discard, no restart) | "how the co-pilot is going to be able to create new things… Need rules… Overflows" (10-03 10:22) | H: json-render, MCP apps, an SDK or design system | `lib/sdk` spec, renderer and validator; a draft panel pinned into the Lab (`v22/5-draft-panel.png`, `6-pinned-in-lab.png`) | No verdict. He said the mini-app SDK's UI part is undecided (answer 10-04 08:51) |
| Bigger text, airy | "This text is a bit too small for my eyes… everything seems a bit too compact" (10-04 09:50) | — | Base text 17px with Standard, Large and Larger; rem only | Standing rule. 10-14: "the remaining issues are… the text… and the clutter" |
| Help or guide feature | "we shall have some sort of helping thing" (10-03 10:01) | Not in storyboard | HowDoI guided walks | See the greeting row |

## 4. Library

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| One global Library reached from anywhere | Storyboard dictation | H: "QMX Global Library… can open up… anywhere in any mini app"; G blue | `/library`: 16 shelves in 5 groups (things that trade, things that run, proof, inputs, knowledge), with an inspector (SF `1600-library-bots.png`) | "library is mind-blowing how much you've transformed it" (10-03 12:12) |
| Player (FIFA) cards for bots and models, richer than ratings | "the card idea is bloody, bloody brilliant" (10-02 09:46); FIFA card (10-03 09:17) | Not in storyboard (Hermes cards were pasted in chat) | EntityCard with cover art by family, real measures, no rating | Praised; later (10-22): wants "a preview and a detailed view". Edit art by family: partly (presets) |
| Card art coloured by family; list or card view | "if it's a scalper… blue and gold… list view or card view" (10-02 09:46) | Not in storyboard | Gold and blue covers; grid or list toggle | Accepted |
| Detail page: attributes, tests, connections, journal, artifacts | "look at the attributes… tests… trading journal… artifacts" (10-01 18:02) | Not in storyboard | Full page: Performance, Trading, Setup; evidence runs (SF `1600-library-gold-scalper.png`) | Earlier: "the actual detailed view is very poor" (10-02 09:46). The rebuilt full page drew no later complaint |
| Where-used map | Not asked | G blue (preview to Library) | "Used in" graph in the inspector | "this cool thing of where it's used" (10-03 12:12) |
| Journals inside items, not a shelf | "journals should be connected in… models or pods" (10-03 12:12) | Not in storyboard | "Journal & logs" and "Code" tabs | Done as asked |
| Multi-select into the copilot; collections | "multi-select a collection to add to the co-pilot" (10-03 12:12) | Not in storyboard | Select, add to copilot, save as a collection (`v20/3-multi-select.png`) | Done as asked |
| Article reader: three panes, reading mode, collapsible menu | "I preferred… a list, then on the right… the three window thing" (10-01 19:00); "reading mode" (10-03 12:12) | Not in storyboard | Three-pane reader, reading mode (`v20/5-reading-mode.png`) | Articles still "a bit compact" (10-03 12:12) |
| In-house browser and web apps as sources (Omarchy) | "I would prefer if the browser is in-house, not a pop-up" (10-01 19:00) | C: agentic browser | A sources shelf; the browser is an iframe | In-house browser **NEVER BUILT** (real) |
| Paper sources: arXiv, alphaXiv, SSRN, RSS; Firecrawl scrapes | "can we… put them as an RSS feed" (10-01 18:02) | Not in storyboard | Sources shelf; Firecrawl shown as paid and needing approval | RSS and Firecrawl wiring: backend |
| Learn from papers as diagrams or video | "turning the paper… into… a video" (10-03 12:12) | Not in storyboard | "Explain it as" four ways (hands off to the copilot) | Diagrams and video **NEVER BUILT** |
| Templates in the Library | "I'm proposing we introduce templates in the library" (10-03 09:17) | Not in storyboard | Templates shelf (26), Use this template | "start from a template no bloody fucking way" (10-03 12:12) |
| Library identity and personality. **NEVER BUILT.** | "we actually even don't have an icon… lacks… more personality" (10-03 12:12) | — | None | Open |

## 5. Lab

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Merge Authoring, Backtest and ML Studio into one Lab | "Authoring, backtesting, ML, all of them are combined in one lab" (10-02 09:46); answer 09:53 "Merge into one Lab" | Not in storyboard | `/lab`; `/authoring` and `/apps/demo-ml` redirect there | "the lab, you've outdone yourself" (10-02 11:30) |
| Tiling layouts per task (Build, Test, Train, Compare) | Layout pick (answer 10-02 10:07: "surprise me") | A (widget grid) | DC `lab-home/after/lab-*-1600.png` | "for the first stable release… quite enough" (10-02 11:30) |
| Node editor plus code plus import | "the node-based editor… needs a rethink… a bit compact" (10-02 09:46) | H: "node-based editor… or code" | Graph / Code / Import modes, map toggle, inspector | "So I can import… a Jupyter notebook… so cool" (10-03 10:01). 10-12: prefers graphs and loops to n8n style (backlog R6) |
| Scenario generator (pairs × timeframes × pair trading), sweep grid | StrategyQuant "adaptive scenario generator" (10-02 09:46) | Not in storyboard | Sweep grid, New scenario, runs table (DC `lab-test-1600.png`) | "scenario generator… bloody nice touch" (10-02 11:30). Sweep grid: "Maybe explain that to me… in a diagram. I don't like reading texts" (10-03 10:01) |
| Add your own markets, parameters and metrics | "Can I add new metrics to measure?" (10-02 11:30) | Not in storyboard | + column, + Add check, add parameters | Done |
| One Resources tile (toolbox, data, compute, slots, presets) as a "menu to the library" | "combine them in what we can call resources… the menu to the library" (10-02 11:30) | Not in storyboard | Resources tile (DC `lab-test-1600.png`, left) | Accepted. "slots… I don't understand" (10-03 10:01) |
| Machine switching ("run on") like VS Code remote | "like Visual Studio Code… with virtual environments… not like a 404" (10-03 08:10) | Not in storyboard | "All machines" picker; empty states per machine | "I have no other complaint here" (10-03 08:10) |
| Start something new: a guided survey per experiment | "when I click Start Something New… think of it like a survey" (10-02 11:30) | Not in storyboard | GuidedStart: question cards, then a guide strip | Bring-outside-work options "absurdly poor": start it as a copilot session (10-03 08:10). 11-09: "keep the old Lab's project journey" |
| Pods bench (Design, Test, Paper) | "pods under the lab need a better design" (10-03 10:22) | Not in storyboard | Strategies / Pods switch (D1 `lab-pod-*`) | "I'm loving it. I don't think I have anything to complain" (10-03 10:59). **REVERSED** for the four extra tabs (Pods, Pod test, Pod compare, Allocate): "these tabs are so many dudes" |
| Allocate / pod comparison table | Built unasked | Not in storyboard | Folded into Run together and Head to head | "allocate what is this about I don't understand it" (10-03 10:22). **REVERSED** |
| Agents in the Lab are mostly workflows; custom workflows first-class | "90% of the times agents that are in here are workflows" (10-02 11:30) | H: "workflow representation… we haven't looked at" | Workflows on the Resources tile; no workflow screen | **NEVER BUILT** as a screen. 10-18: "workflows are made in the lab" |
| Compare presets and "watch" sets; training-runs tile; genetic algorithms. **NEVER BUILT.** | "compare, then save… multiple presets, and then watch" (10-02 11:30) | Not in storyboard | Backlog only | Open |
| Agents on their own machines (EC2, Modal); live agent streams. **NEVER BUILT.** | "agents might need… their own virtual machines" (10-02 11:30) | Not in storyboard | Backlog | Parked with the agent engine |

## 6. Portfolio and pods

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Portfolio as "a Lab for risk and sizing"; many methods | Answer 10-03 08:48: "not just one book or one BMS… multiple… add your own spin" | G: revenue-per-business-line chart "for risk mgt and bms stuff" | `/portfolio`: Overview, Pods, Live, Road to live, MIS (SF `1600-portfolio.png`) | "you've done a bloody brilliant job" (10-03 10:22) |
| Books become Pods; each pod has a live side and a paper side | "let's not call them books… pods" (10-03 09:17); "every pod has live and paper" (10-03 10:01) | Not in storyboard | Pod cards with live (blue) and paper (orange) figures; a pod sheet with a kill-line meter | "the pods are insane" (10-03 10:01); "one of your best products" (10-03 12:12). The vocabulary is open again: R5, "units not bots" (later) |
| Trading node folds into Portfolio Live; a server shows provider, region, IP, latency and who uses it | "a trading node is a VPS… IP… latency… who's using it" (10-02 09:46) | G: "what is on a server, what is local… that blue icon" | Servers chip; test latency, restart, drain; `/trade` redirects | "test latency restart then drain… very, very good" (10-03 10:01) |
| Kill switch always visible, per server or per pod | "kill switch put it up here… you need to be able to see it" (10-03 10:01); "per server or per pod" (10-03 10:22) | Not in storyboard | Header chip "YELLOW Bybit spot" opens a pods × servers grid | No complaint after it was built |
| Live: positions on top with exposure and correlation as tabs; one chart per bot | "put positions on top, put the charts at the bottom" (10-03 10:01) | Not in storyboard | Live layout | Done as asked |
| Road to live from paper; trading journal; progress inside the bot card | "it only reflects here when it starts paper trading" (10-03 09:17) | Not in storyboard | Road to live lanes, promotion card | "Road to Live is fucking nice" (10-03 10:01) |
| Templates on every page that builds | "the lab and the portfolio should have templates" (10-03 09:17) | Not in storyboard | Templates button in the header | Done |
| MIS with logs, indicators and models. **NEVER BUILT.** | "I'll let it slide for now" (10-03 09:17) | Not in storyboard | MIS tab, thin | Open |
| Order-flow charting | "Can we get in some order flow things in here" (10-02 09:46) | Not in storyboard | None | **NEVER BUILT.** Charting provider open (R7) |

## 7. Apps and mini apps

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| A mini app is a composition of widgets and workflows with its own menus | Storyboard dictation | H: "a mini app is a composition of widgets and workflows… these menus on top change, they're dynamic" | App screen on the tile board with + Widget (`/apps/[id]`; D1v2 `app-my-desk-1600x900.png`) | No direct verdict |
| Mini apps without a UI (headless) need a place | "there are mini apps that don't really have a UI" (10-01 18:02) | Not in storyboard | Background apps show "Next check / next run" on their tile | Accepted in the Apps redesign. A run surface for headless apps and workflows: **NEVER BUILT** |
| Per-app copilot with its own tools and permissions (MCP Apps) | "tools in every mini app are not going to be the same" (10-02 09:46) | H: "has different permissions and tools… MCP apps configuration" | Per-surface composer context; Settings, Copilots per app | No verdict. Agent work is parked |
| Road to live for apps, "QMX's own CI"; a sandbox with breakers and logs | Answer 10-04 09:16: "paper trading as an example… unit tests… CI" | Not in storyboard | Apps pass 1 bands (Live, Proving itself, Being built); risk class; box | First cut: "This is ugly… an observability layer", the Docker analogy taken "literally" (10-14 08:44). **REVERSED** into the product-style grid |
| Apps feel like products: tiles that show their output | 10-14 08:44 (T2) | Not in storyboard | Grid with a live glimpse per tile; Discover (DC `apps/after/main-1600.png`) | **UNREVIEWED.** 10-07 (R3): mini apps will be redesigned; "many apps were not meant to be just like VS Code style extensions" |
| Make an app from Portfolio or Lab widgets (a Portfolio variant) | "get a widget… from portfolio… create a mini app… a new variant of a portfolio" (10-03 10:01) | Not in storyboard | "From widgets" on Discover; Home and Portfolio widgets only | Lab panels as widgets: **NEVER BUILT** |
| Many more mini apps (news, screener, charting, monitoring) | "I think we can have way more mini-apps" (10-03 10:22) | Not in storyboard | 11 demo apps; Research demo retired | No verdict |
| Monitoring or cron: where does it live? | "will it be a mini app? I think it will" (10-03 12:12) | Not in storyboard | Weekend watcher (headless) | Later: cron belongs to workflows (R6) |
| The copilot builds overnight in a build mode | Answer 10-04 09:16 | Not in storyboard | "Built overnight" sample app only | **NEVER BUILT** (backend) |

## 8. Settings

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Settings like his storyboard reference | "I've highlighted it with an orange square… I think that's ideal for settings" (10-01 18:02) | F: the Factory settings page (title, pill tabs, cards with toggles, a table with actions). E: Manus, Cartesia, Factory alternatives | Never found by the October agent. Built as grouped pages (D1 `settings-*-1600x900.png`, DC `settings/after/`) | The F reference was **never used**. Use it now |
| Global settings plus settings per app | Storyboard | F: "this one is global… each app needs its own" | Settings, Mini apps table; per-copilot page | Per-app settings pages: **NEVER BUILT** |
| Real controls, depth, not words | "a settings panel is a settings panel dude… I can't click a thing" (10-02 09:46) | — | Declutter: General, Appearance, Brokers and accounts, Models and tools, Servers and data, Copilots, Mini apps, Safety, Developer | 10-14: "so many words. There is little functionality" drove the declutter; the rebuilt pages are **UNREVIEWED** |
| Providers via the Claude CLI proxy; model selector lives in Settings | "we are going to use something claude CLI proxy" (10-02 09:46); "model selection actually is meant to be inside the settings" (10-01 18:02) | Not in storyboard | Models and tools: providers and MCP in one row style | 10-18: usage visible "the way CLI proxy shows it". 11-09: model routing moves into a Usage page (`/usage`, November, uncommitted) |
| Data sources you can add: upload, API, scrape, cron | "I can't add data… some might need API keys… scraping… cron jobs" (10-02 09:46) | Not in storyboard | Servers and data: Add source dialog | **UNREVIEWED** |
| Servers you can act on (kill, latency, IP) | "I want to be able to kill them from settings" (10-02 09:46) | Not in storyboard | Machines table; remove is daemon-only | Partly |
| Many accounts across brokers and exchanges | "if I have seven accounts… Binance… Coinbase… Bybit" (10-02 09:46) | Not in storyboard | Brokers and accounts (cTrader at IC Markets plus CCXT) | Accepted (R1, CFDs back) |
| Agents' share of the plan; daily caps | Built unasked | — | Safety page | **REVERSED:** later memory says shares and caps are bugs ("no caps") |

## 9. Themes and look

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Glass over an ink-map background of his own (Hermes, Arch wallpapers) | "I wanted to have my own version of it" (10-01, per grounding 04) | D: Hermes image (ink texture) | `InkBackground`, `art.ts`: contours, candles, liquidity; panels on solid backing | "theming is freaking cool" (10-01 17:18). The fault was see-through panels (answer 10-03 08:27) |
| More themes; edit themes like VS Code | "the plain one is ugly, you can add more themes" (10-01 18:02); "can I edit these themes… like Visual Studio Code" (10-03 09:17) | Not in storyboard | Seven themes plus a colour-picker editor | "this is so cool" (10-03 12:12) |
| Background art variants, saved; "not just lines"; an auto-rotating generator | "can it be not just lines" (10-03 12:12); "if it can change like a wallpaper every now and then" (10-03 09:17) | Not in storyboard | Variants and rotation (Ledger round 2) | "Not just lines": **NEVER BUILT** |
| Surface styles (glass, liquid glass, solid, brutalist) | "glass morphism skew morphism… what do you think is viable" (10-03 09:17) | Not in storyboard | Four surface styles | "I don't think I'll ever use that" (10-03 12:12). **REVERSED** in effect |
| Personality and purposeful motion | "the whole platform needs a little bit more personality" (10-01 19:00) | Not in storyboard | Start-up motion only (eea09941) | 10-14: "more personality, to the animations". Still open |
| Fewer words, more doing; one Demo chip; info tips | "I have more words than actual intentionality" (10-02 09:46) | Not in storyboard | `DESIGN-RULES.md` word budget; InfoTip; DemoChip | "Most of the layout is perfect… the text… and the clutter" (10-14 08:44) |
| Own spin, inspiration allowed | "Not borrowing from anyone… Where you want inspiration, you can look for it" (10-04 09:50) | SB itself borrows OpenBB and VS Code layouts on purpose | — | The standing rule. "Bloomberg… still, no" (10-14) |
| Ugly scrollbars, unstyled drop-downs | "They're ugly as hell" (10-01 17:18); "these drop-downs lack styling" (10-02 11:30) | G mentions scroll bars | Fixed (styled selects, thin bars) | Done |

## 10. Start-up and day one

| Idea | He asked | Storyboard | Built | Verdict |
|---|---|---|---|---|
| Start-up like Photoshop, PyCharm or cTrader: "QMX, then the world fills slowly by slowly based off the theme" | 10-03 12:12 | Not in storyboard | `StartUp.svelte` (eea09941): QMX draws in, tiles settle, art fades up | **UNREVIEWED** (no screenshot set) |
| Web app first, desktop later | "first turn this into a web app… render it later into a full desktop app" (10-01 09:03) | Not in storyboard | SvelteKit SPA; no wrapper | R9 (10-12) confirmed. The desktop wrapper is out of this kit |
| Fresh out of the box, no mock data | "I want to see this without mock data… fresh out of the box" (10-03 12:12) | Not in storyboard | Demo switch; day-one lines; empty boards collapse to one welcome (D1, D1v2) | **UNREVIEWED** |
| Choose the start screen | Not asked | — | Settings, General, Start screen; `/` routes to it | — |
| Screen sizes and overflows | "screen sizing is also something" (10-03 12:12) | Not in storyboard | Checked at 1280, 1600 and 1920; server chips fold below 1800 | Judge at full screen 1920 to 2560 (his rule) |
| Component gallery page (`/gallery`) | "I can create new components of my own… cool as hell" (10-01 19:00) | Not in storyboard | `/gallery` | Praised as an idea; copilot-made components are open |

---

## Carry forward: the strongest ideas

1. **One tiling board and one widget frame everywhere.** Minimise docks and the rest fills; edit layout; + Panel; add to copilot from any widget. This is his OpenBB pick plus Bloomberg space management. Praised every time.
2. **Copilot as a desktop-class agent app with a preview pane.** Use storyboard C: sessions, chat, and a preview for browser, terminal, diff, sub-agents and mini apps. One session crosses every screen and can run for days. Build the real terminal and browser.
3. **Pods with live and paper sides, road to live, kill switch always in view.** His "best products", and new ideas he "would not have come up with".
4. **The Library as the global database:** the where-used map, preview to full page, player cards, templates, journals inside items.
5. **Lab:** a scenario generator you can extend (markets, parameters, metrics); one Resources tile; machine switching like VS Code remote; templates.
6. **Customisability ("a box of Legos")** with defaults everywhere, templates on every building page, and copilot-built panels under rules.
7. **Look:** his own ink art with editable themes, on solid panels. Big rem text. Few words, every block data or an action.
8. **Ideas drawn but never built:**
   - opened apps on the rail below a divider;
   - widget history;
   - expand into a detail tab;
   - per-app settings;
   - the Factory-style settings page in the orange box.

## Rejected or reversed

- Copying other apps' look: the copilot passes after T3 Code, bb, DeepSeek Harness and Codex. Ruled "Not borrowing from anyone" (10-04 09:50). Bloomberg is for density, not look.
- The Grok UI (scrapped 10-01) and the Claude Design canvas look, rejected again on 11-09.
- Ask / Plan / Do modes. Agent requests. The new-session greeting.
- Allocate and the pod comparison table. Too many Lab tabs.
- The observability-style Apps page and the literal Docker framing.
- The notification bell and "Needs you" as designed: the inbox must be agentic (11-09).
- Surface styles (brutalist and others) he will "never use". Agents' plan share and daily caps.
- Wasted space, small text, word-heavy panels, and cards mixed with tabs. These are the constant complaints.
