# UI backlog triage, 2026-10-14

Every open item in `UI-BACKLOG.md` (`- [ ]`, `[NOT DONE]`, `[PARTLY]`, `[UNCLEAR]`, `[BUILT, awaiting review]`) was checked against the code at `ui-review/repair` HEAD 1cc66208 and `UI-LEDGER.md`. Duplicates are merged: each item appears once, with every backlog line number it came from. "L" numbers are lines in `UI-BACKLOG.md`. File paths are relative to `apps/qmx-ui/src`.

Two notes about how items were judged:
- Items marked "BUILT, awaiting review" on Home, the desk, Settings and Apps count as DONE. The operator's 10-14 note (L17) says "most of it looks okay to me".
- The Revision section (L12-46) holds rulings, not ticks. Its UI consequences (R1 data and brokers, R2 no modes, 10-14 personality) are listed as items below.

## 1. Counts

| Status | Items |
|---|---|
| OPEN-UI | 34 |
| DONE | 53 |
| SUPERSEDED | 10 |
| PARKED-AGENTIC | 23 |
| PARKED-LAB-PORTFOLIO-BACKEND | 14 |
| BACKEND-OTHER | 12 |
| NOT-UI | 3 |
| **Total (after merging)** | **149** |

## 2. OPEN-UI (pure UI work, no backend or agent decision needed)

Size: S = under half a day, M = about a day, L = several days.

### App-wide
1. **More personality and a few purposeful animations** (panel expand, a run finishing, connecting). L17, L416, L511. The only motion today is spinners, pulses and the ticker scroll (`themes.css:341`, `TickerTape.svelte:40`). **M**
2. **Demo data becomes CFDs plus crypto** (R1) on Home, the ticker, Library, Apps, Lab and Portfolio. L23, L387, L427, L461. Almost all demo data is crypto only (`portfolio/demo.ts:2,13-16`, `lab/pods.ts`, `apps/apps.svelte.ts`). Do Home, the ticker, Library and Apps first. Lab pods and Portfolio may change after the R5 design. **L**
3. **Fix stale wording**: Books, node, spot only, LangGraph. Section 4 lists each place. L158, L255, L427. **S**
4. **Screen sizes**: headers and panels fit at 1280 wide and smaller on every screen, and the Text size setting works at every width. L132, L61. Only the Portfolio, Lab and Library headers were fixed (ledger, Library pass 2). **M**
5. **Space at full screen (1920, 2560)**: no big empty areas. L420, L534, L591. For example, Settings is a centred `max-w-6xl` column (`routes/settings/+page.svelte:203`). **M**
6. **Pop out any screen, kept in sync** (for example, the Lab on a second monitor). L419, L655, L204 (pop-out part), L224. Only the copilot pops out, and that copy is not synced (`routes/copilot/+page.svelte:41-47`). The Lab and Portfolio have no pop-out. **L**
7. **Background art generator** (new art every so often), and art that is "not just lines". L66, L128, L283, L458, L585. There are five styles and a rotation (`workbench.svelte.ts:229`), but no generator. **M**
8. **More design styles** (neumorphism, claymorphism, skeuomorphism, minimalism). L284, L426, L458. Only Glass, Liquid glass, Solid and Brutalist exist (`workbench/look.ts:10-26`). **M**
9. **Stress-test the UI across failure states** (empty, overloaded, broken data), because the copilot inherits any inconsistency. L208, L524. No such pass has been recorded. **M**
10. **One-page design-style sheet** (glass, ink art, themes, surfaces, spacing rules) for the copilot and builders. L92, L534. Not written. **S**
11. **Refresh shadcn-svelte components**, add community extras, and list which components the copilot may use. L210, L431, L689. There are still 17 primitives and an 11-entry catalog (`lib/components/ui`, `routes/gallery`). **S-M**
12. **"Lego" customisability in the Library and Settings** (add, remove and edit what you see). L423. This is strong in the Lab, Portfolio and Home. The Library and Settings are fixed. **L**

### Home
13. **Markets view for one broker or account** (many accounts across brokers). L249, L557. The Markets panel is one watchlist with no broker or account filter (`home/panels/MarketsPanel.svelte`). This goes with item 2. **M**
14. **"Going on" carries many parallel jobs** (for example, nine models training on a GPU provider, grouped). L246, L556. It shows a flat list of 5 demo jobs with no grouping (`home/panels/GoingPanel.svelte:40-60`, `copilot/demo.ts:629`). **M**
15. **Templates on Home** (start a tab from a template). L252, L424. Home has "Save as a new tab" (`routes/home/+page.svelte:137`) but no templates. **S**

### Copilot desk (UI-only parts)
16. **Remove Ask / Plan / Do** (R2). Skills are offered through "/" instead. L26. The mode chip is still in the main composer (`workbench/Composer.svelte:208`, `copilot/AimMenu.svelte`, `copilot/aim.svelte.ts:8-18`), and Settings still has "By default it may" (`settings/CopilotsSection.svelte:29-65,113-125`). The skill list itself is parked. **S**
17. **"Save to Library" from a chat result**. L218, L143, L463. There is no button. The artifact preview only says "the copilot saves it to the Library" (`copilot/WorkArea.svelte:276-277`). **S**

### Library
18. **Full detail pages for models, apps and workflows** (he called them "very poor"). L157, L168, L576, L143. These are still the first-cut tabs Performance, Trading and Setup (`routes/library/[id]/+page.svelte:29-34`). **M**
19. **Library personality** (an identity and an icon of its own). L111. The header is a plain icon and the word "Library" (`routes/library/+page.svelte:429-431`). **S-M**
20. **ML models look different from bots**, beyond colour. L170, L575. Only the cover colour differs (`qmx/CoverArt.svelte`). The cards are otherwise identical. **S**
21. **Cover art for papers and articles**. L171. Generated covers exist for bots, models, apps and workflows only (`qmx/CoverArt.svelte`). **M**
22. **alphaXiv 2409.06289 as the example Sources item**. L418, L513. alphaXiv is listed (`demo/feeds.ts:27`), but that paper is not used. **S**

### Lab
23. **Explain the sweep grid with a diagram**, and show more than one grid layout. L333, L459. There is no explanation view in `lab/panels/MatrixPanel.svelte`. **S**
24. **Explain model slots in plain words**. L334, L646, L459. There is no help text in `lab/panels/SlotsPanel.svelte`. **S**
25. **Resources tile: artifacts and recently used items**. L167, L345, L520. The tabs are only Items, Data, Machines and Slots (`lab/panels/ResourcesPanel.svelte:22-27`). The Library link goes to the top of the Library (`:56`). **S**
26. **Save compare sets as presets**, with primary and secondary layers. L335. There is no save in `lab/panels/ComparePanel.svelte`. "Watch" needs a backend. **M**
27. **A template gallery in the Lab** (he could not find a template again). L348. Templates can be saved from the Start dialog (`lab/StartDialog.svelte:374`), but there is nowhere to browse them. **M**

### Portfolio
28. **Road-to-live bot cards link to their Library item**. L383, L146. The promotion card links (`portfolio/panels/SigningPanel.svelte:42`). The Road cards have no link (`portfolio/panels/RoadPanel.svelte:55`). **S**

### Apps
- None. The Apps redesign is parked under R3 (see section 3).

### Settings
29. **Brokers and accounts** (R1): cTrader / IC Markets plus CCXT exchanges, several accounts each. L23, L126. The section still says "Spot crypto only" and lists crypto exchanges only (`settings/ExchangesSection.svelte:3,35`, `portfolio/demo.ts:13-16`). **M**
30. **A cTrader MCP listed by default** under MCP servers (R1). L22. There is no cTrader entry (`settings/ConnectionsSection.svelte`). **S**
31. **Data and sources: an add-a-source flow** (CSV or Excel upload, API provider, scrape, schedule), plus dropping "Free sources only" (R10). L280, L584, L650. It shows six disabled switches (`routes/settings/+page.svelte:291-307`). Real fetching is a backend job; the screen and flow are UI work. **M**
32. **Themes editable like VS Code** (a fuller token editor). L289. "Your theme" covers only accent, background, opacity, radius and text size (`workbench/LookSettings.svelte`). **M**

### Start-up and day one
33. **Start-up screen**: QMX appears, then the world fills in slowly in the theme's colours, with loading states. L65, L131. Nothing like this exists in the code. It can be built in the browser now (R9). **M**
34. **Day one with no demo data**: how every screen looks fresh out of the box. L133. Demo mode is always on (`workbench.svelte.ts:287`). There has been no pass over the empty states with demo mode off. **L**

## 3. Other statuses

### DONE (the code does it now)
- Desk reviewed and the new-errand greeting accepted. L60, L70. Operator note 10-14 (L17). `copilot/HowDoI.svelte`.
- Bigger text, rem sizes and the text-size floor. L61, L91. `app.css:17` (17px base), Text size at `LookSettings.svelte:49`, no pixel font sizes left.
- Opus 5.5 is the daily driver. L63. First in `workbench.svelte.ts:39` and the default in `CopilotsSection.svelte:28`.
- The copilot answers (scripted). L84. `copilot/store.svelte.ts:97`, `routes/copilot/+page.svelte:96`.
- Diff tab. L85. `copilot/WorkArea.svelte:41,282`.
- One session store, grouped by origin, side copilots included. L86, L115, L226. `store.svelte.ts:79` (absorb), `CopilotColumn.svelte:138`, `SessionsSidebar.svelte:41`.
- The copilot builds a panel: keep, discard or pin, with no restart. L87, L213, L545. `routes/copilot/+page.svelte:103-117`, `lib/sdk`.
- Settings per copilot and a model per copilot. L90, L223, L228. `CopilotsSection.svelte:20-21,96`. The mode picker there is stale (open item 16).
- One widget system; Home is on the tile board. L93, L318, L547. `routes/home/+page.svelte:258`. `MiniAppShell` is no longer used.
- Rules for copilot-built panels: catalog only, size range, draft, unsupported frame. L119, L207, L684-688. `sdk/spec.ts:23,85`, `tiles/TileBoard.svelte:78`.
- Home greeting, editable ticker, screener and news. L123. `routes/home/+page.svelte:35,232`, `home/catalog.ts`.
- Settings sections for keys (credential store), servers and MCP. L126. `routes/settings/+page.svelte:45-51`. R1 brokers are still open (item 29).
- Compute page. L127. Merged into Servers (`routes/settings/+page.svelte:74`).
- The Library connects to other screens and shows the map. L146, L147, L454. `LibraryPicker` in `Composer.svelte:340`, `library/ConnectionsMap.svelte`, `ItemInspector.svelte:46`, `home/panels/RecentPanel.svelte:25`.
- Library redesign and its layout pass. L148, L172. Commits 417f938d and 6518249f.
- The reader uses the width, with a reading mode. L149, L572. `routes/library/+page.svelte:761-829`.
- Artifacts open. L150, L574. The Files, Reports and Setups shelves open in the inspector (`library/items.ts:154-190`).
- Saved setups shelf. L151, L619. `library/items.ts:178,612`.
- Card colour by family, and a list view. L152, L153, L575. `routes/library/+page.svelte:105,318`.
- Library templates shelf. L154, L465. `library/items.ts:142,482`.
- Items show where they are used, plus test reports and paper runs. L159. `ItemInspector.svelte:162`, `items.ts:154,160`.
- Turn an article into a hypothesis. L166. `routes/library/+page.svelte:795` hands it to the copilot.
- The sessions column folds on its own. L199, L543. `routes/copilot/+page.svelte:39,133`.
- Sub-agent preview as child threads. L200. `routes/copilot/+page.svelte:98-102`.
- Attachments shown in messages. L201, L544. `copilot/Thread.svelte:121`.
- New session and search sessions. L202, L456. `SessionsSidebar.svelte:9,78`.
- Sessions that run for days (UI side). L203. Errands with Going on, ledger Copilot pass 1.
- Bring in a conversation from another screen. L204. `store.svelte.ts:79`. The pop-out part is item 6.
- Built-in help. L205, L425. `HowDoI.svelte`, `/help` at `copilot/demo.ts:720`.
- Attach from the Library. L215. `Composer.svelte:340`. Upload needs a backend.
- Copilot-led "Start something new". L217. `GuidedStart.svelte`, `lab/LabStrips.svelte`.
- Your own Home tabs. L242, L553. `routes/home/+page.svelte:68,137`.
- Notifications. L243, L554. The bell and Needs you (`routes/home/+page.svelte:158-190`).
- The word "Home" dropped from the header. L244, L555. The header shows the greeting (`:101`).
- Home previews link through to full screens. L245, L521. `GoingPanel.svelte:22`, `needs.ts`.
- Minimise frees space, tiling and good layouts kept. L247, L248, L548, L549, L550. TileBoard on Home; save as a tab.
- News and Agents views use their space. L250, L558, L559. These are now resizable tiles; the Agents tab is gone.
- Settings depth and a layout per tab (except General and Data). L277, L278, L522, L580. Commit 56036fcc, accepted 10-14.
- Servers page. L279, L583, L631. `settings/ServersSection.svelte:54,65,125`.
- Model providers. L281, L582, L651. `ConnectionsSection.svelte:21`.
- Appearance wording. L282, L457. `routes/settings/+page.svelte:321-322`.
- More mini apps. L306, L693. 8 apps and 8 templates (`apps/apps.svelte.ts:89-353`).
- Research demo app retired. L307. `workbench.svelte.ts:30` (an empty list).
- Headless apps' run surface. L309, L523. `apps/AppDetail.svelte:205`.
- New panels never show an error. L314, L594. `TileBoard.svelte:78`.
- Events split by crypto and FX, each with a source. L388. `portfolio/panels/EventsPanel.svelte:14`.
- T3 Code studied. L446. `handoff/research/bb-t3code-research.md`.
- One Lab, and permanent rail places. L537, L538. `routes/lab`, `workbench/destinations.ts`.
- The composer differs by context. L541. `workbench/copilot-context.ts`.
- Paper and live colour on tile borders. L562. `themes.css:316-317`.
- Authoring rethink and the editor copilot. L568, L569. `lab/panels/EditorPanel.svelte`, `lab/copilot.ts`.
- Minimap toggle, refit at small sizes, toolbox of saved setups. L623, L624, L625. `EditorPanel.svelte:36`, `lab/FitOnResize.svelte`, `AssetsPanel.svelte`.
- Kill-switch authority researched and drawn. L632. `UI-BACKLOG.md:675`, `portfolio/KillMatrix.svelte`.

### SUPERSEDED
- Target menu failure cases. L209, L610. Replaced by the mode chip, which R2 now removes.
- Spot crypto only. L387. R1: CFDs, IC Markets and cTrader are back.
- Desktop wrapper as its own pass. L94. R9: browser first, the wrapper later.
- Settings layout from the Excalidraw storyboard. L285. Operator 10-14 (L17): Settings "looks okay".
- Review the Minara site. L417, L512. The 10-04 own-design ruling (L54): no borrowed look.
- "You didn't update the carding" on Home. L268. Home was rebuilt (7fa36fb5).
- Bloomberg-like Markets tab. L447. The Home tile board (7fa36fb5).
- Promotion and Protection widgets on the trading node. L564, L565. The node folded into Portfolio (L408).
- A dedicated portfolio optimisation page. L634. "Run together" in the Lab (L406).
- ML Studio placement. L644. Moved into the Lab (L323).

### PARKED-AGENTIC (waits for the agent session, R2/R3/R4/R6)
- Mini-app sandbox, road to live, overnight builds and apps feeding apps. L62. R3.
- Papers as diagrams or video; diagrams from articles. L67, L155, L517. Copilot skills (R4).
- Monitoring and cron as workflows that keep running. L68, L134. R6.
- MCP Apps renderer. L88. R3 (mini-app SDK).
- Settings per mini app. L89. R3.
- Components contract for builders. L95. R3, R8 (re-derive later).
- One session acting across everything. L116. R4 engine.
- Show skills, permissions, delegation and running agents. L117. R2 skills, R4.
- The copilot designs components from a registry. L120. R4.
- The copilot builds whole mini apps and workflows. L206, L519. R3, R6.
- The copilot knows what each app does; apps declare their own tools. L214, L313. R3.
- Three kinds of agents visible in the main copilot. L216, L611. R4.
- An app built from widgets, including Lab panels. L308, L462. R3 (`FromWidgets` has Home and Portfolio only).
- News and sentiment workflow template. L310. R6 (`EventsPanel.svelte:101` only shows a message).
- The operator creates new components. L315, L595. R3.
- Robustness checks built from workflows. L337. R6.
- Agents live, on their own machines. L338. R4.
- Editor run state, saved steps, the copilot editing the graph. L339, L626. R6 (graphs and loops replace the node-editor style).
- The Lab's "Build a new panel" through skills. L346. R2 (`routes/lab/+page.svelte:306-311` only opens the copilot).
- Custom workflows as first-class items. L351. R6.
- The copilot wires a Lab pod into Portfolio. L384. R4.
- "Model ideas from your Library" generated automatically. L645. R4.
- Apps and workflows detail: Run buttons, tighter layout. L169, L618. R3 (`library/[id]/+page.svelte:365` is disabled).

### PARKED-LAB-PORTFOLIO-BACKEND (waits for the Lab and Portfolio design, R5/R7)
- The kill switch's account tab follows the brokers. L23. R1, R5.
- Live market data for charts; charting as a mini app. L135. R7.
- New pod journey from scratch. L136. R5.
- "How is a model running?" in Library detail. L190. Unclear; QMB and QML runs.
- Richer approval flow and the promotion card. L251, L604, L389. R5.
- Books to Pods everywhere. L255, L427. R5: "are we still using books?"; the pod vocabulary may change.
- Genetic algorithms and Lean-style experiments. L332, L510. Lab engine design.
- Training-runs tile; start training from the editor. L336. Lab design (QML).
- Order-flow views. L341, L563, L460. R7 charting.
- Evidence status of off-machine runs. L342. Ruling still open.
- "Add a slot" wired. L347. R5 (slots feed sizing and risk).
- StrategyQuant databank views and the cluster-pass rule. L350. Lab design.
- MIS logs, indicators and model views. L382. R5.
- Where risk and sizing live. L633. R5 reopened it.

### BACKEND-OTHER
- Real terminal and real browser in the copilot; a terminal ruling. L69, L96, L118. Today the terminal is an echo (`WorkArea.svelte:67-79`) and the browser an iframe (`:374`).
- Firecrawl and Alexandria for sources and scheduled scrapes. L110. R10; each call needs his approval.
- Real article summaries and testable claims. L162. Needs a model or backend.
- Sources as live feeds; adding a source for real. L163, L143. The button exists (`routes/library/+page.svelte:976`).
- In-house browser for sources (sites refuse iframes). L164, L573. Firecrawl, or the desktop wrapper later.
- Any site as an in-app web app. L165, L518. "Make it an app" (`:1002`) needs the desktop wrapper.
- Fetching videos as a research source. L156, L518. Listed in the UI (`library/items.ts:673`).
- General tab readiness and pairing. L277 (General part), L581. `Pair` is disabled (`routes/settings/+page.svelte:235-236`).
- Adding compute providers and storage buckets. L288, L349. The buttons exist (`ServersSection.svelte:125-139`).
- Remove mock data when wiring. L340. qmx-control wiring (R8).
- Import a model built elsewhere, for real. L352. Import modes exist (`EditorPanel.svelte`).
- Model choice is shown, but providers are not called. L281 tail. Provider routes are demo only (`ConnectionsSection.svelte`).

### NOT-UI
- The own-spin rule. L59. A standing design rule, not a task.
- Open source and free for everyone. L64. An idea.
- Working-method rules (one screen per pass, drive in the browser, design skills). L531-533. Process.

## 4. Stale demo data and text (contradicts R1, R2, R4, R5)

**Spot crypto only (R1: CFDs and FX are back)**
- `lib/settings/ExchangesSection.svelte:3`: comment says "spot crypto only".
- `lib/settings/ExchangesSection.svelte:35`: screen text says "Spot crypto only."
- `lib/settings/CopilotsSection.svelte:48`: the Lab copilot's instructions say "Use spot crypto data."
- `lib/portfolio/demo.ts:2-3`: says "spot crypto only … no CFDs, no FX broker, no prop firms".
- `lib/portfolio/demo.ts:13-16`: venues are Binance, Bybit, Coinbase and Kraken, all "Spot".
- `lib/portfolio/panels/AccountsPanel.svelte:2` and `lib/portfolio/catalog.ts:47`: say "spot accounts".
- `routes/portfolio/+page.svelte:74`: banner says "Sample spot accounts".
- `lib/settings/ConnectionsSection.svelte`: has no cTrader MCP (R1 wants one by default).
- `lib/home/home.svelte.ts:70-82`: the ticker list is coins, plus only EURUSD, DXY and Gold.
- `lib/apps/apps.svelte.ts`: all 8 demo apps are crypto (coin screener, funding watcher, token unlocks).
- `lib/lab/demo.ts:356` and `lib/demo/assets.ts:293,600`: datasets are "Binance spot" only.
- `lib/library/items.ts:398`: every bot is labelled a "spot strategy".

**Ask / Plan / Do modes (R2)**
- `lib/copilot/aim.svelte.ts:3,8-18`: defines the three modes.
- `lib/copilot/AimMenu.svelte:9-54`: the mode chip and its picker.
- `lib/workbench/Composer.svelte:208`: the main composer shows the chip.
- `lib/settings/CopilotsSection.svelte:29,45,55,65,113-125`: "By default it may" with Ask, Plan and Do.

**"Books" (R5: vocabulary open; the UI said Pods)**
- `lib/portfolio/panels/ControlPanel.svelte:34`: "Route this account's Books to their demo pair".
- `lib/portfolio/panels/CorrelationPanel.svelte:2`: comment says "How the Books move together".
- `lib/lab/demo.ts:520`: "Book decides today".
- `lib/lab/pods.ts:277-337` and `lib/portfolio/demo.ts:191,815`: "Classic Book" and "Book + BMS" as a sizing method. These are deliberate, but they depend on the R5 outcome.
- `routes/portfolio/+page.svelte:3` and `lib/workbench/destinations.ts:50`: comments say "books".

**"Node" / trading node (folded into Portfolio and servers, 10-03)**
- `routes/library/[id]/+page.svelte:305-307`: "Not on any node yet … reaches a node only after you promote it".
- `lib/lab/panels/GraduatePanel.svelte:65,74`: "Needs the trading node."
- `lib/portfolio/panels/PodPanel.svelte:419`, `SigningPanel.svelte:76`, `NodesPanel.svelte:38`, `ServersStrip.svelte:23`, `TemplatesDialog.svelte:73`: "needs the trading node".
- `lib/portfolio/KillMatrix.svelte:77`: "the real switch goes to the trading node".
- `lib/portfolio/panels/ControlPanel.svelte:49,88-89`: "needs the trading node", "the Tokyo node", "source: node".
- `lib/demo/feeds.ts:55,195`: "news windows on the node", "Trading node news windows".

**LangGraph (R4: one engine, Claude Agent SDK)**
- `lib/copilot/store.svelte.ts:10`: comment says "(LangGraph) streams the same block shapes".

**Also out of date (R8, R10)**
- "Needs the daemon" appears 98 times across `src`. R8 replaced the old daemon with `qmx-control`. Reword when wiring starts.
- `routes/settings/+page.svelte:291-292`: "Free sources only." R10 says he will pay for Firecrawl.
- `lib/workbench/MiniAppShell.svelte`: no file uses it any more. It is dead code.
