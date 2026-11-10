# Master backlog (rebuilt 2026-10-03 from a full transcript audit)

This section is the working backlog. Order of passes (operator, 2026-10-03): Library, main Copilot, Home, Settings, Mini apps; Lab and Portfolio leftovers alongside. Older notes below it are kept for history; where they conflict, this section wins.

Code checked: C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\src (branch ui-review/repair, HEAD 9aadfc76, clean tree). Paths below are relative to that `src` folder.
Sources read: all operator messages (user_msgs.txt), the seven question answers (2026-10-01 to 2026-10-03), the last message (2026-10-03 10:59: "You've forgotten about the library"), missed-requests.md, recovered.md, UI-BACKLOG.md, UI-LEDGER.md, BACKEND-REQUIREMENTS.md.
Status words: NOT DONE, PARTLY, DONE, SUPERSEDED (a later message replaced it), UNCLEAR (not sure he meant it). Within each section the order is NOT DONE, PARTLY, DONE, SUPERSEDED, UNCLEAR.
Later rulings win. Rulings applied: Grok UI scrapped; Books are now Pods (each with a live side and a paper side); spot crypto only (IC Markets, cTrader, CFDs, prop firms dropped); agent requests removed; Allocate folded into Lab Test as "Run together"; Lab has Strategies | Pods benches; the trading node is folded into Portfolio as Live; Home keeps the current rail; themes and background art stay everywhere (10-03 answer), the real fault was see-through panels.

---

## Revision 2026-10-14: changes since the last design pass (read this first)

The UI paused on 2026-10-05. Three sessions ran after it: risk and sizing (10-05 to 10-08), the backend rebuild on `rebuild/base` (P01 to P24, 10-07 to 10-09) and the QMA v2 agent planning (10-12, 10-13). Their rulings below change the UI. Later rulings win over everything further down this file.

**Operator, 2026-10-14 (resume):**
- Home, the desk, Settings and Apps: "most of it looks okay to me". He wants more personality, "to the animations or something". He was satisfied, which is why designing stopped.
- The agentic system is held back from UI design: the copilot's skills, workflows, and how agents work with mini apps and their databases. Designs may be sketched; nothing is fixed until the agent session settles. Small copilot fixes still go ahead.
- Lab and Portfolio need a backend design session. The engines exist (QMB, QML, QMN, QMF, MIS); the layer the screens show (pods with live and paper sides, pod tests, run together, the kill-switch grid, promotions, many servers) does not.
- Stack stays SvelteKit with shadcn-svelte.

**Triage of everything below:** `handoff/research/backlog-triage-2026-10-14.md` checked every open item against the code (149 after merging duplicates: 34 open UI work, 53 done, 10 superseded, 23 parked for the agentic system, 14 waiting on the Lab and Portfolio backend, 12 other backend, 3 not UI). Work from its OPEN-UI list; the older sections below are history.

**R1. Markets: CFDs are back (10-07).** "we are going back to trading CFD"; IC Markets and cTrader back; "multiple brokers, multiple connections, multiple accounts"; CCXT stays for crypto; a cTrader MCP for the copilot by default. Risk session 10-05: spot crypto and FX are "not really out"; prop firms "take a back seat". Replaces "spot crypto only" (2026-10-03).
- UI: demo data on Portfolio, Lab, Library, Home and the ticker becomes CFD plus crypto. Settings, Exchange accounts becomes brokers and accounts (cTrader / IC Markets, CCXT exchanges, several accounts each). The kill switch's account tab follows.

**R2. No copilot modes (10-09).** "I want a skill to help me plan. I don't want a planning mode." Copilots differ by their skills: "a co-pilot in portfolio rather is different from a co-pilot in ... the lab because these are all different skills".
- UI: remove Ask / Plan / Do from the desk and the side copilots; skills are invoked instead ("/" in the composer). Which skills exist is agent-session work (parked).

**R3. Mini apps will be redesigned (10-07).** "for the mini apps section ... don't take it like it is ... in terms of design, yeah, we are going to change it a bit." Still extension-like, but "many apps were not meant to be just like VS Code style extensions". The backend now has a sandbox runtime, a Docker tier and road to live (P12, P14, P17).
- UI: Apps pass 1 stays as a first cut. The redesign is parked with the agentic system.

**R4. Agent engine under re-plan.** The 10-04 note "agents on LangChain and LangGraph" is out of date: QMA v2 plans one engine (Claude Agent SDK, with a translator for GPT). What the chat screen needs from it is listed in `tracker/qma-v2/UI-NOTES.md` on branch `plan/agent-system` (effort control, compaction, model-switch cost warning, usage page, approvals as events, sub-agents as child sessions, export per session, cursor overlay, session home badges).
- UI: parked. Do not build these until the agent session hands over.

**R5. Risk and sizing redesign (10-05 to 10-08, `workroom/risk-lab-2026-10-05`).** Loss points, fast invalidation, a scalper-first system; "are we still using books?". The unit structure is not agreed.
- UI: the Pods bench in the Lab and the Portfolio pod screens wait for the Lab and Portfolio backend design. Pod vocabulary may change.

**R6. Workflows (10-08, 10-09, 10-12).** Cron jobs belong to workflows. A daily decay-spotting workflow (the old WF3) under the Lab. He now prefers graphs and loops to an n8n-style node editor.
- UI: parked with the agentic system.

**R7. Charting is open (10-07).** "who's going to provide charting for us that is very paramount". Decide in the Lab and Portfolio design session.

**R8. The backend was rebuilt.** `rebuild/base` P01 to P24: `qmx-control` (one REST and MCP door), mini-app runtime, brokers and accounts (P18), Library and run index (P22), remote runs (P21). `handoff/` and `BACKEND-REQUIREMENTS.md` describe the old daemon and are stale; re-derive them after the Lab and Portfolio design. Wiring still waits.

**R9. Browser app first** (10-12): ship the UI in the browser so agents can click through it; the desktop wrapper comes later.

**R10. Firecrawl:** he is willing to pay for it, including Alexandria (10-07). Every call still needs his approval. An MQL5 article scraper runs on a schedule (P19).

---

## Operator rulings 2026-10-04 (after Copilot pass 2)

Added from the resume brief. Later rulings win over older notes below.

- **Our own design, not borrowed.** "have our own spin... not borrow it from other applications... Not borrowing from anyone." He also said there was "literally no intention behind the design". Inspiration is allowed ("where you want inspiration, you can look for it"), copying is not. Other apps may still be studied for mechanics (how plugins work, how the copilot adds UI), not for look or interaction.
- **Bigger fonts, less compact, as a standing rule.** Base text is 17px. Settings, Appearance has a Text size choice: Standard, Large, Larger. No fixed pixel font sizes: use rem so the choice scales everything. Judge spacing at full-screen desktop (1920 to 2560). He dislikes both unused space and cramming.
- **Status of the rebuilds.** Home (7fa36fb5), the Copilot "desk" (6b4d247a) and Settings (56036fcc, fixed up in 8ef175ad) are built and committed. None has been reviewed by him. Home and the desk skipped the options-then-pick step.

Not in the backlog before this; all open:
- [ ] 1. Own spin, no borrowed references, and "no intention behind the design" (the rule above). The old StrategyQuant "borrow" section is a reference list only.
- [ ] 2. The desk redesign itself: awaiting his review. Present it first (`pnpm build`, then `pnpm preview` on port 4173; stop the stale server first).
- [ ] 3. Bigger fonts rule. Fixed-pixel text sizes were replaced by rem in 8ef175ad; check any that remain and check the Text size setting at every width.
- [ ] 4. Mini apps (details in handoff/MINI-APPS-AND-COPILOT-CONTRACT.md): a road to live like paper trading, "QMX's own CI"; approval that depends on the type; a container or sandbox per mini app (Docker or similar) with circuit breakers, logging, monitoring and observability; full access inside the box; a mode where the copilot builds overnight; one session crossing modes (portfolio, Lab, mini app); mini apps feeding other mini apps and providing widgets or panels.
- [ ] 5. Opus 5.5 as the copilot's daily-driver model (2026-10-03). It shows only in Settings demo text.
- [ ] 6. Idea: "maybe make this open source and free for everyone" (2026-10-03). Not UI work; recorded so it is not lost.
- [ ] 7. Desktop start-up in detail: "QMX then... the world is filling slowly by slowly based off the theme." The start-up screen is in the backlog only loosely.
- [ ] 8. Background art "not just lines", and a generator that changes the wallpaper every so often.
- [ ] 9. Learning from papers as diagrams and video ("turning the paper... into a video", Karpathy post). Only "Explain it as" exists.
- [ ] 10. Monitoring as a workflow or cron the copilot sets up. Open question: where does it live, is it a mini app?
- [ ] Real terminal and real browser in the copilot work area. Today the terminal only echoes typed commands with a demo note, and the browser is an iframe that most sites refuse. Do not tick until both are real.
- [ ] The disliked new-session greeting: 8ef175ad removed the greeting from the new-errand screen; confirm with him that `HowDoI` is acceptable as it now stands.

---

## Session review (2026-10-04) — read this first

An independent review re-read every message from 2026-10-01 to 2026-10-03 and checked the code (scratchpad `session-review.md`). Verdict on Copilot pass 1: a good-looking storyboard of one scripted conversation, not a working screen; it skipped the agreed method (study, options, you pick, click-through). Ticks above were corrected.

New facts from the operator (2026-10-04):
- The agentic layer moved to **LangChain and LangGraph**; the own agent SDK is dropped.
- Two SDKs: the **agent SDK** and the **mini-app SDK** (for mini apps and widgets). The mini-app SDK's **UI part is undecided**; research how others do it before designing.
- The main copilot should be like the **Codex, ChatGPT and Claude desktop apps**, including a real terminal. Look at those apps, don't design from memory. SUPERSEDED for look and interaction by the own-design ruling above (2026-10-04, 09:50); studying their mechanics is still fine. Permissions are parked for now.

Missing from this backlog until now:
- [ ] Demo copilot can receive a message and answer (a scripted responder that streams blocks).
- [ ] Diff tab in the copilot work area.
- [ ] One session store shared by the main and side copilots; "Continue in the main copilot" opens that exact session.
- [ ] The copilot builds a panel end to end (json-render or the chosen mini-app UI format): draft in chat, keep, discard or pin to a screen.
- [ ] MCP Apps (sandboxed app windows) renderer, if the mini-app SDK chooses it.
- [ ] Settings per mini app, beside global settings.
- [ ] Settings per copilot: instructions, tools, skills, model, permission defaults.
- [ ] Text-size floor as a rule (most copilot text is under 12px today).
- [ ] A one-page design-style sheet for the new look (glass, ink art, themes, surfaces), for the copilot and Codex.
- [ ] One widget system: move Home off the old MiniAppShell grid onto the tiling board.
- [ ] The desktop app wrapper as its own pass (needed for the in-app browser, pop-outs and the start-up screen).
- [ ] Components contract for Codex in BACKEND-REQUIREMENTS.md (panel format, catalog registry, copilot build tools, drafts, loading without restart, new component code).
- [ ] A terminal ruling written into the architecture (the 2026-09-23 contract says preview only; the operator wants a real terminal like the desktop apps).

Top fixes for Copilot pass 2 (from the review): it answers; it builds a panel; one session model; the sessions column collapses on its own; a real work area (diff, terminal, browser, per-artifact preview); readability (13px floor, fits 1280 wide); skills and per-copilot settings; drill into an agent; pop out any screen kept in sync; attachments shown as cards in messages.

## Operator review of Library pass 1 (2026-10-03, evening) — new requests

Library (pass 2 built the first six):
- [x] Journals are not a shelf: journal and logs sit inside bots, models and pods (inspector tab "Journal & logs").
- [x] See the code of things (blocks, bots, pods, workflows, models, setups): inspector tab "Code", read only, "Edit in the Lab".
- [x] Pick several items and hand them to the copilot together; keep them as a collection.
- [x] Shelf groups stand out (banded, with icons) and fold; the whole shelf column can hide.
- [x] Reading mode for articles and papers (list and shelves step away, bigger text).
- [x] Articles from other sources (Obsidian clippings, arXiv, web pages) beside MQL5; "Explain it as" plain words, diagram, interactive page or explainer video (Karpathy post, 2026-10-02).
- [x] "Ask the copilot" in + New opens the copilot with a drafted message (copilot page takes `?ask=`).
- [ ] Firecrawl (including its Alexandria provider catalogue) as the web source and for scheduled scrapes. Operator may pay for it; nothing calls it until he approves (BACKEND).
- [ ] The Library still lacks personality (an identity, an icon of its own).

Copilot (next pass; operator: "needs a rethink"):
- [x] Rethink "aim this message at" (the target menu). Built as mode, reach and who answers; the operator parked permissions on 2026-10-04, so revisit in Copilot pass 2.
- [ ] Sessions grouped into collections by where they started (Lab, Portfolio, …); reopen any old session from the main copilot. PARTLY: groups exist; side-copilot sessions are a separate list and the hand-off carries nothing.
- [ ] One main-copilot session can act across everything: start a Lab experiment, train a model, change a pod, look at Portfolio, in one conversation. PARTLY: one scripted sample; you cannot send a message.
- [ ] Show how it works: artifacts in chat, skills, sub-agents, tools, commands, the ask-you-a-question card, permissions, delegation, background tasks and running agents (what each is doing right now). References: Codex desktop app, Claude desktop app (SUPERSEDED for visual and interaction design by the own-design ruling of 2026-10-04; mechanics may still be studied). PARTLY: shown in one sample; no skills anywhere; browser empty, terminal plain text, every artifact previews the same numbers, Stop and Save are toasts.
- [ ] Terminal (look at shadcn's terminal component) and browser integration.
- [ ] Rules for what the copilot builds in the UI (see "Copilot pass: rules" above), plus: new things load in place without restarting the app; heavy things load in the background.
- [ ] The copilot designs components from shadcn (registry) or its own design style.

Home (needs a full rethink):
- [ ] Greeting; a customizable ticker (by hand or the copilot); a screener mini app; news; everything we've added since.

Settings:
- [ ] APIs and keys, trading servers, multiple exchange accounts and brokers, sources, MCP servers.
- [ ] Compute page wastes space: the main card should fill or split the width.
- [ ] Background art that is not only lines; more themes (editing already works).

App-wide:
- [ ] Start-up screen like Photoshop or PyCharm: QMX appears, then the world fills in slowly in the theme's colours. Loading states and a few deliberate animations.
- [ ] Screen sizes: headers and panels must fit smaller screens (Portfolio header fixed; check every screen).
- [ ] Fresh out of the box with no demo data: how every screen looks on day one (later, as its own pass).
- [ ] Monitoring that keeps running when the laptop is off: scheduled jobs and watch workflows on a server, with logs and alerts; decide where they live (a "Automations" shelf of headless mini apps).
- [ ] Live market data for charts (exchange streams through the backend); charting as a mini app.
- [ ] New pod journey from scratch ("build my own").

## Library (operator priority 1: "needs a bloody redesign", "needs to connect to all the other parts")

**Library pass 1 (2026-10-03) moved these:**
- DONE: whole redesign (shelves, cards or list, inspector); "how does it connect" shown as a map on every item; every item lists where it is used with links into Lab, Portfolio, Copilot, Home and mini apps; reader uses the width (text plus a side column); files open in the inspector; saved setups shelf (test settings, presets, features, model settings); card colour by family; list view; templates shelf (workflows, pods, Portfolio pods, Lab layouts, a mini app); detail page says pod and server, and "Road to live" replaces the old Promote button; copilot "From Library…" opens a picker instead of leaving the screen; Portfolio's promotion card and Lab pod resources link into the Library; demo items switched to spot crypto.
- PARTLY: videos are listed as a source (fetching is backend); "Make it an app" for a source is a button with a reason (desktop app).
- STILL OPEN: model and app full pages; diagrams from articles; Home and "Save to Library" links; adding a source for real.

NOT DONE
- [NOT DONE] Library must connect to every other part: Lab, Portfolio, main Copilot, Home, mini apps, templates, artifacts, bot cards, journal, evidence. — (2026-10-03, "It needs to be able to connect to all the other parts") — Today the links are one-way and thin: Lab Resources has one icon linking to the Library page (lib/lab/panels/ResourcesPanel.svelte:56), the Copilot "From Library…" attach item only navigates to the Library page instead of opening a picker (lib/workbench/copilot-context.ts:70-76), Portfolio bot cards (road to live) have no link to their Library entry (lib/portfolio/panels/RoadPanel.svelte:55), "Save to Library" is disabled (routes/copilot/+page.svelte:319). Ledger pass 6 lists no connection work at all.
- [NOT DONE] Ask "how does the library connect to all this?" — show it, not just describe it. — (2026-10-03, "maybe how does the library connect to all this?") — No design or screen for it exists.
- [NOT DONE] Whole Library redesign as its own one-screen pass (research, 2-3 layout options, build, click-through). — (2026-10-03, "the library is, I think, needing a bloody redesign") — Ledger pass 6 is "queued"; nothing started. Library layout is the same as round 5.
- [NOT DONE] Reader should use the full width on large screens; text-heavy page wastes the right side. — (2026-10-02, "a lot of space on the left, like on the right") — Reader text is capped at max-w-3xl inside a 54% pane (routes/library/+page.svelte:340). Full-page reader (routes/library/article/[id]/+page.svelte:109) is centred at max-w-7xl with contents and side column, but the in-page reader is what he complained about.
- [NOT DONE] Artifacts tab: items must open; it needs a whole rethink ("they don't even open and they are all awful"). — (2026-10-02, "artifacts, nah, I don't like this that much") — It is still a plain table whose rows are not clickable (routes/library/+page.svelte:457-493).
- [NOT DONE] Saved configurations (test presets, model configs such as two gradient-boosting setups, feature sets, datasets) should live in the Library, probably under a different name than "artifacts". — (2026-10-01, "I think this is where artifacts were meant to come in") — Lab Resources holds "Saved tests", "Presets", "Datasets" (lib/lab/demo.ts ASSET_GROUPS) but the Library has no such kind and the Artifacts tab is still the old file table.
- [NOT DONE] Card art colour by family (for example scalper = blue and gold), or let the operator edit card art as a preset. — (2026-10-02, "if it's a scalper, it can be like gold") — Cover colour is fixed per kind only (lib/qmx/CoverArt.svelte:5-10); `family` exists on entities (lib/qmx/entities.ts:80) but is not used for colour.
- [NOT DONE] List view as well as card view for bots/models/apps. — (2026-10-02, "different views like list view or card view") — Only the card grid exists (routes/library/+page.svelte:507-519).
- [NOT DONE] Templates in the Library (start from a template; most things will begin from templates). — (2026-10-03, "we are introducing templates in the library") — Ledger line "Library templates" is unchecked; nothing in routes/library.
- [NOT DONE] Diagrams generated from articles, without AI or with a cheap model. — (2026-10-01, "maybe we could have some diagrams from them") — No diagram code anywhere; reader shows scraped figures only (routes/library/+page.svelte:325-337).
- [NOT DONE] Videos as a source for hypothesis research ("from maybe videos to academic papers"). — (2026-10-01, "hypothesis research from maybe videos to academic papers") — Not in the Sources list (lib/demo/feeds.ts) or BACKEND-REQUIREMENTS.md.
- [NOT DONE] Model detail page is poor: unused space and no function; app/workflow detail likewise. — (2026-10-02, "the actual detailed view is very poor") — routes/library/[id]/+page.svelte is the same first-cut tabs (Performance, Trading, Setup); no redesign pass yet.
- [NOT DONE] Detail page vocabulary and links are out of date: still says "Book" and "node"; "Promote…" says approve on the trading node, which no longer exists. — (2026-10-03, "let's not call them books I guess let's call them pods") — routes/library/[id]/+page.svelte:128-136 and :292. Should link to Portfolio, Road to live.
- [NOT DONE] Library items should show where they are used (which pods, nodes, paper results, backtest reports) and open their paper-trading and test reports. — (2026-10-01, "it's trading history paper trading results or trading backtesting reports") — Detail shows evidence runs, a journal and a connections list only for demo bots (routes/library/[id]/+page.svelte:234-312); no paper-results or report views.

PARTLY
- [PARTLY] Real article summaries (key points) and testable claims from a cheap model. — (2026-10-01, "I want to see if I can have a summary in there") — "Key points" box exists but just shows the article's opening excerpt (routes/library/+page.svelte:303-312); real summary is a backend item (BACKEND-REQUIREMENTS.md:61).
- [PARTLY] Sources: arXiv, alphaXiv, SSRN, MQL5 as feeds/RSS. — (2026-10-01, "put them as an RSS feed") — Sources tab lists them with sample items only, labelled "Proposed · needs backend" (lib/demo/feeds.ts); you cannot add a source from the Library.
- [PARTLY] In-house browser for sources instead of a pop-up, same styling. — (2026-10-01, "I would prefer if the browser is in-house, not a pop-up") — iframe pane built (routes/library/+page.svelte:441-449), but many sites refuse embedding (he saw this 2026-10-02) and the only fallback is a hint line and an "Outside QMX" button; scraping through Firecrawl is not designed.
- [PARTLY] Omarchy-style: any site becomes an in-app "web app". — (2026-10-01, "he has apps where he can have browsers as apps") — Comment in feeds.ts only; no way to promote a site to an app.
- [PARTLY] Turn an article into a hypothesis. — (2026-10-01 plan; button built) — Button exists but is disabled (routes/library/+page.svelte:277-285).
- [PARTLY] Resources menu in the Lab as the quick menu into the Library, also holding artifacts and recently used indicators. — (2026-10-02, "artifacts also come here") — Resources has Items, Data, Machines, Slots tabs only (lib/lab/panels/ResourcesPanel.svelte:23-28); no artifacts, no recent indicators.
- [PARTLY] Entity detail: denser, overlay instead of busy background, fewer tabs. — (2026-10-01, "I prefer like an overlay because the background is confusing me") — Done in first cut (scrim, 3-4 tabs); his 2026-10-02 verdict was still "poor" for models and apps (see NOT DONE).
- [PARTLY] Apps & workflows: tighter layout, operations for headless apps. — (2026-10-01, "operations for these are what these are apps and workflows") — Cards are good and headless apps get an Operations tab (routes/library/[id]/+page.svelte:335-369), but Run buttons are disabled and the layout is not tightened.
- [PARTLY] ML models look different from bots. — (2026-10-02, "I haven't seen any ML model") — Models are green, bots blue (lib/qmx/CoverArt.svelte:5-10); cards otherwise identical.
- [PARTLY] Cover art for academic papers and articles like the model-release "college" style, possibly via JSON render. — (2026-10-01, "even in academic papers I don't know if that's possible") — Generated cover art exists for bots, models, apps and workflows only.
- [PARTLY] Library layout, spacing and text size across all five tabs. — (2026-10-01, "the layout for the library, you haven't given it time") — Sections list and three-pane done; full pass not done.

DONE
- [DONE] Bot/model cards with named measures and plain definitions, no overall score. — (2026-10-01, "I'm not understanding what RET is") — lib/qmx/EntityCard.svelte:95-116.
- [DONE] FIFA/FC-style player cards for bots, models, apps, workflows; also used in Copilot and Portfolio. — (2026-10-01, "the FIFA or FC card") — lib/qmx/EntityCard.svelte, routes/copilot/+page.svelte:378-392, lib/portfolio/panels/RoadPanel.svelte:55.
- [DONE] Card variables change after an edit in chat (before/after). — (2026-10-01, "the card variables can change") — routes/copilot/+page.svelte:33-47 with `changed` highlight.
- [DONE] Artifacts tab restored (he was shocked it was removed). — (2026-10-01, "that's why I was so shocked that you removed artifacts") — routes/library/+page.svelte:47 (but see NOT DONE: it must open).
- [DONE] Knowledge: list | reader | side three-pane layout. — (2026-10-01, "the three window thing was far better") — routes/library/+page.svelte:169-352.
- [DONE] Read the MQL5 articles in-house, with search and sections. — (2026-10-01, "I would like to just be able to read them") — routes/library/+page.svelte:169-352; full page at routes/library/article/[id]/+page.svelte.
- [DONE] News moved from the Library to Home. — (2026-10-01, "news is not meant to be the library") — News widget in routes/home/+page.svelte:434.
- [DONE] "Add to copilot" does something visible. — (2026-10-01, "when I click add to compiler, like nothing goes on") — routes/library/+page.svelte:274, workbench.addRef.
- [DONE] Clicking a bot card in chat or on Home opens that exact version in the Library. — (2026-10-01, "a link that takes me straight to that version") — routes/copilot/+page.svelte:381; routes/home/+page.svelte:405.
- [DONE] Back arrow on a detail page returns to the tab it came from. — (2026-10-02, "it takes me straight back to the library I don't know why") — routes/library/[id]/+page.svelte:52.
- [DONE] Trading journal, connections and evidence inside a bot's detail. — (2026-10-01, "look at maybe tests ... the trading journal") — routes/library/[id]/+page.svelte:234-312.
- [DONE] Mini apps without a UI are shown as "headless" with operations. — (2026-10-01, "mini apps that don't really have a UI") — lib/qmx/EntityCard.svelte:73; routes/library/[id]/+page.svelte:335.
- [DONE] "Open in Lab" from a bot/model detail. — (implied by "connect to all the other parts") — routes/library/[id]/+page.svelte:123.

UNCLEAR
- [UNCLEAR] "How is QMB going to come in / how is a model running?" in the Library detail. — (2026-10-01, "I want to see a model running") — A terminal was added for models in an earlier round; unclear if he wants more.

---

## Copilot (main copilot chat)

Redesigned as "the desk" in 6b4d247a (errands, one at a time, a "What it did" receipt, the decision where you type, a drawer for helpers, reports, changes, terminal and browser). 8ef175ad added an empty new-errand screen with no greeting (errands waiting on you, then templates); blank errands are hidden and New errand reuses a blank one. Built fast with no options step; awaiting his review. The list below was written against passes 1 and 2 and is not updated for the desk. Terminal and browser stay unticked: they are a demo echo and an iframe only.

NOT DONE
- [NOT DONE] Session column on the left must collapse by itself while keeping Browser/Terminal/Diff open (today only Focus mode hides it, and Focus also hides the work area). — (2026-10-02, "I want it to be able to collapse on its own") — routes/copilot/+page.svelte:178-227.
- [NOT DONE] Sub-agent preview in the main copilot. — (2026-10-02, "You haven't also done the sub-agents preview") — Sub-agents appear only in the Lab Agents panel (lib/lab/panels/AgentsPanel.svelte) and Home Agents widget; nothing in routes/copilot.
- [NOT DONE] Show how a message looks with an attached document, a Library item, or a mini-app item. — (2026-10-02, "I want to see how a message looks like when I attach") — Attachments show only as chips in the composer (lib/workbench/Composer.svelte:82-100); no message shows one.
- [DONE] "New session" and "Search sessions" buttons work (Copilot pass 1). — (implied by sessions list) — Both are disabled (routes/copilot/+page.svelte:184, :195).
- [NOT DONE] Sessions that run for days, using sub-agents (replaces agent requests). — (2026-10-03, "that session can run for days") — No long-running session state, progress or sub-agent tree in the session list. Ledger says "Copilot pass".
- [NOT DONE] Main copilot can take in a conversation from another screen (for example a Lab chat), and its changes show live there, even with the Lab popped out on a second monitor. — (2026-10-03, "I can bring in conversations from other pages") — No bring-in action, no Lab pop-out (only the copilot has pop-out, routes/copilot/+page.svelte:55).
- [NOT DONE] Built-in help or guide ("how do I train something new?"). — (2026-10-03, "some sort of helping thing feature") — Only the three copilot-led walks exist (lib/lab/guides.ts); no general help.
- [NOT DONE] Copilot builds whole mini apps and workflows from the component library through skills, not just widgets. — (2026-10-01, "the copilot in the chat is meant to be able to build all mini apps") — No flow; component spec catalog exists (lib/qmx/catalog.ts, routes/gallery).
- [NOT DONE] Rules for anything the copilot creates: only catalog components, declared size range, checked at smallest size, draft preview you keep or discard, no overflow. — (2026-10-03, "How do we prevent overflows? How do we prevent buggings?") — Eight open items in UI-BACKLOG.md "Copilot pass"; none built.
- [NOT DONE] Stress-test the UI across many failure scenarios because the copilot inherits any inconsistency. — (2026-10-01, "we need to really consider multiple scenarios") — Open in backlog.
- [NOT DONE] Target menu: think through failure cases. — (2026-10-01, "there are lots of issues that can come from it") — Open; menu shows readiness axes (lib/workbench/copilot-context.ts:56-68) but no failure handling.
- [NOT DONE] Update shadcn-svelte components and document which ones the copilot may use. — (2026-10-03, "we have to update components") — Open in backlog.

PARTLY
- [PARTLY] Copilot can create a new widget from JSON render and the flow front-to-back is shown. — (2026-10-02, "I want to see how the co-pilot can create a new widget") — "Build a new panel…" only shows a message (routes/lab/+page.svelte:305-307, routes/portfolio/+page.svelte:199); widget board "Add widget" adds from a fixed list.
- [PARTLY] Copilot understands what each mini app does and does not do. — (2026-10-01, "this mini app does this this mini app doesn't do this") — Target list shows each target's operations and five readiness checks (lib/workbench/copilot-context.ts:56-68); the app declaring its own tools is only wired for Lab and Portfolio.
- [PARTLY] Attach: from the Library, upload a file, per-context sources. — (2026-10-02, "attach also needs a rethink") — Per-context attach sources exist (Composer.svelte:120-150); Library attach just navigates away, upload says "needs daemon".
- [PARTLY] Sub-agents, workflow agents and copilots all visible (QMA's three kinds). — (2026-10-01, "three types of agents") — Lab and Home show quants and sub-agents with states; not in the main copilot.
- [PARTLY] Copilot-led "Start something new" using question cards, then it switches Lab layouts. — (2026-10-03, "we start just as a co-pilot session") — Built (routes/copilot/+page.svelte:232, lib/workbench/GuidedStart.svelte, lib/lab/LabStrips.svelte); the copilot does not yet act on its own, which needs backend skills and hooks.
- [PARTLY] Save a chat result to the Library. — (implied) — Button present but disabled (routes/copilot/+page.svelte:319).

DONE
- [DONE] Copilot input: no focus box, grows with text then scrolls. — (2026-10-01, "I don't know why there is a box that forms") — lib/workbench/Composer.svelte:112-117.
- [DONE] Model picker in the chat box. — (2026-10-01, "I haven't seen a model picker") — lib/workbench/Composer.svelte:45-48.
- [PARTLY] Model choice also lives in Settings, set per copilot (three generic profiles only). — (2026-10-01, "model selection actually is meant to be inside the settings") — routes/settings/+page.svelte (Models tab, default model per copilot).
- [PARTLY] Pop-out copilot to a bigger screen or new window (an unsynced copy, not a second-monitor view). — (2026-10-01, "detached to a bigger screen") — routes/copilot/+page.svelte:55-61, Focus mode.
- [DONE] Tools, Target, Attach and messaging differ per context (main, Lab, Portfolio). — (2026-10-02, "tools in every mini app are not going to be the same") — lib/workbench/copilot-context.ts, lib/lab/copilot.ts, lib/portfolio/copilot.ts.
- [PARTLY] App copilot has multiple sessions with history and its own settings (VS Code style header): every session is empty. — (2026-10-02, "multiple sessions in application co-pilot") — lib/workbench/CopilotColumn.svelte:60-117.
- [DONE] Composer icons with count badges, no Offline label, better new-session empty state. — (2026-10-02, "Things like tools, you can just use an icon") — Composer.svelte:70-73.
- [PARTLY] Copilot settings link to Settings (agents and models): a generic Models tab, no per-copilot instructions, tools, skills or permissions. — (2026-10-02, "Settings for the copilot, it should take us straight to settings") — ledger L12, CopilotColumn.svelte:117.
- [DONE] A chat session demo with tool calls, result table and a preview tab. — (2026-10-01, "I would like to see a chat session") — routes/copilot/+page.svelte:234-395.
- [DONE] "Add to copilot" on widgets shows a chip and a toast. — (2026-10-01, "Can I add it to chat? Bloody hell") — WidgetFrame onmessage; workbench.addRef.

SUPERSEDED
- [SUPERSEDED] Agent requests inside Portfolio. — (2026-10-03 10:01, "agent requests, again, seems like a very irrelevant tab") — Removed; replaced by long-running copilot sessions (see NOT DONE).

---

## Home

Rebuilt in 7fa36fb5: one tile board, tabs Today, Markets and Research plus your own saved tabs, an editable ticker, a bell and a "Needs you" panel (copilot questions, promotions to sign, paper runs ready for live, raised kill switches, failed runs), Pods and News reused from Portfolio, a screener drawn from a panel description. Items marked BUILT below are addressed by that rebuild but he has not seen it; do not tick them. The lines under them still describe the pre-rebuild code. Still open: many parallel jobs in "while you were away", news with room, a Markets view for one broker, templates on Home, a richer approval flow, and checking the rebuild against the own-spin and bigger-text rulings.

NOT DONE
- [BUILT, awaiting operator review] Add your own tabs so Home is your dashboard. — (2026-10-02, "I want to be able to add new tabs") — Views fixed to Today, Markets, Agents (routes/home/+page.svelte:225-243); WidgetBoard has no "add view" (lib/workbench/board.svelte.ts).
- [BUILT, awaiting operator review] Notifications area at the top for things needing attention. — (2026-10-02, "give it some spacing on top") — None; approvals live in a widget only.
- [NOT DONE] Drop the word "Home" in the header, keep the ticker. — (2026-10-02, "we don't need this home word") — Header still prints it (lib/workbench/MiniAppShell.svelte:102; routes/home/+page.svelte:320).
- [PARTLY BUILT, awaiting operator review] Home tabs are previews that link through to the full pages (Markets to Portfolio, Agents, main Copilot). — (2026-10-02, "markets ... can connect the portfolio page agents main co-pilot") — Only the brief cards and pipeline cards link out.
- [NOT DONE] "While you were away" must carry many parallel jobs (for example nine models training on a GPU provider). — (2026-10-02, "this thing will not give me enough information") — Three fixed brief cards and four jobs (routes/home/+page.svelte:61-105).
- [BUILT, awaiting operator review] Minimising a widget must free its space (it docks at the bottom, others fill up). — (2026-10-02, "protection goes all the way to the bottom and the top fills up") — Done in Lab/Portfolio tiling, not on Home, which still uses the older grid where a minimised card only shrinks in place (lib/workbench/MiniAppShell.svelte:160-169).
- [BUILT, awaiting operator review] Tiling quality for the Markets view. — (2026-10-02, "the tiling is very poor") — Same old grid; no tiling engine on Home.
- [BUILT, awaiting operator review] Home on spot crypto with many accounts (Binance, Coinbase, Bybit) and a Markets view for one specific broker. — (2026-10-02, "crypto can have more than one broker") — Home still shows FX demo data, "Paper · 3 books", and promotions to "book FX-P" (routes/home/+page.svelte:21-47, :292); ledger says "Home still FX: next".
- [NOT DONE] Agents view and News widget use their space (news too thin, empty space below). — (2026-10-02, "why would news be this thin") — Same widgets as round 5; no change recorded.
- [NOT DONE] Richer approval flow in the review dialog. — (2026-10-01, "I don't know if I can do better") — Open in backlog.
- [NOT DONE] Templates on Home. — (2026-10-03, "even the home section") — None.

PARTLY
- [PARTLY] Rename Books to Pods everywhere (the Home rebuild reuses Portfolio's pod panels; Library detail and Settings still need a check). — (2026-10-03, "let's call them pods") — Done in Portfolio and Lab; Home, Library detail and Settings still say books.

DONE
- [DONE] Remove the sidebar from Home. — (2026-10-01, "remove that bloody sidebar on the home page") — Home uses no sidebar (routes/home/+page.svelte:320).
- [DONE] Dashboard grid of widgets with minimise, expand, add widget, edit layout. — (2026-10-01, "think of it like a dashboard") — lib/workbench/MiniAppShell.svelte, WidgetFrame.
- [DONE] Live equity next to paper equity. — (2026-10-01, "Live equity, there is nothing") — routes/home/+page.svelte:285-310.
- [DONE] Strategy pipeline columns scroll and expand. — (2026-10-01, "they're not scrollable, they don't expand") — routes/home/+page.svelte:395-440.
- [DONE] News on Home with filters. — (2026-10-01, "news ... meant to be on the home page") — routes/home/+page.svelte:434-473.
- [DONE] Live trade ticker; Sydney/Tokyo/London clocks removed. — (2026-10-01, "maybe we can have also a live trade ticker") — lib/qmx/TickerTape.svelte; no session clocks in code.
- [DONE] Fresh-install "Get started" board instead of empty boxes. — (2026-10-01, "most of these things ... likely not be populated") — routes/home/+page.svelte:215-243.
- [DONE] Waiting-for-you review pop-up. — (2026-10-01, "the pop-up is nice") — routes/home/+page.svelte (Dialog).

UNCLEAR
- [UNCLEAR] "You didn't update the carding, other cards at home" — (2026-10-01, "you actually didn't update the carding") — Unclear which cards; Home pipeline cards do use the new cover art.

---

## Settings

Regrouped in 56036fcc into Exchanges, Servers, Connections (providers, MCP), Copilots, Mini apps and Safety sections. It was committed without a visual check; 8ef175ad then checked it with screenshots at 1600 and 1280 wide (no overflow, no console errors) and put the cards on a solid backing over the art. He has not reviewed it. Items marked BUILT are addressed but not ticked. Still open: Data & sources (CSV or Excel upload, cron, scraping), real API keys (OS credential store only), per-mini-app depth, the storyboard reference, remaining design styles, the art generator.

NOT DONE
- [PARTLY BUILT, awaiting operator review] Every tab needs depth and things to do; fewer words, nothing only readable. — (2026-10-02, "I can't click a thing") — General tab is a static readiness list with disabled Pair/Check buttons (routes/settings/+page.svelte:207-262).
- [PARTLY BUILT, awaiting operator review] Each tab gets its own layout for its job (he liked the pill tabs, not the same card everywhere). — (2026-10-02, "you didn't have to design everything every section like that") — Same card pattern on all tabs.
- [BUILT, awaiting operator review] Trading nodes tab (now a Servers section): a node is a VPS; show server, provider, region, IP, latency, status, who uses it; kill it from here; paper and live may not be separate nodes. — (2026-10-02, "who's the provider the latency is it active") — Still a static two-row table "Paper node / Live node", "Not connected", column "Books" (routes/settings/+page.svelte, nodes tab). The actions exist in Portfolio Live (lib/portfolio/panels/NodesPanel.svelte, ServersStrip.svelte) but not here.
- [NOT DONE] Data & sources: add new sources (Excel/CSV upload, API providers), keys, scraping workflows, cron schedules, use by mini apps. — (2026-10-02, "I can't add data I can't add anything") — Only six disabled switches (routes/settings/+page.svelte, data tab).
- [BUILT, awaiting operator review] Models/providers tab will change (Claude CLI proxy for model providers). 8ef175ad adds provider routes: Claude through your plan (CLI), Anthropic API, OpenAI, Gemini, OpenRouter, local. Routes are demo; nothing calls a provider. — (2026-10-02, "we are going to use something claude CLI proxy") — Static three-row list.
- [NOT DONE] Appearance text contradicts the 2026-10-03 ruling: it still says trading screens never show the background. — (2026-10-03, "I don't think the themes are removed. I think keep them") — routes/settings/+page.svelte Appearance card. Fix the wording.
- [NOT DONE] Background art generator (new wallpaper every so often). — (2026-10-03, "changing the background art generation of its own") — Rotation among saved/built-in variants exists (workbench.artRotate); no generator.
- [NOT DONE] Remaining design styles he asked about (neumorphism, claymorphism, skeuomorphism, minimalism). — (2026-10-03, "what do you think is viable for us here") — Styles offered: Glass, Liquid glass, Solid, Brutalist (lib/workbench/look.ts:9-30).
- [NOT DONE] Settings reference layout from the Excalidraw storyboard (oval/diamond/green box he tried to point to). — (2026-10-01, "that's ideal for settings to be honest") — Never located; ask him to re-show it.

PARTLY
- [PARTLY] Compute providers and storage buckets added and removed by the operator. — (2026-10-03, "I can add providers, compute providers, I can remove") — Compute tab hosts Add compute and Add storage (lib/lab/panels/ComputePanel.svelte:43, :126) but bucket connection "needs the daemon".
- [PARTLY] Themes editable like VS Code. — (2026-10-03, "can't I just edit them like Visual Studio Code") — "Your theme" accent, background, opacity, radius, text size (lib/workbench/LookSettings.svelte); not a full token editor.

DONE
- [DONE] More themes; remove the plain one. — (2026-10-01, "the plain one is ugly you can add more themes") — Seven themes: Ink, Cobalt, Ember, Graphite, Moss, Violet, Paper (routes/settings/+page.svelte:61-100).
- [DONE] Multiple background art variants, saved. — (2026-10-01, "multiple variants of the background art ... and save them") — routes/settings/+page.svelte Background art section; lib/workbench/art.ts.
- [DONE] Default model per copilot. — (2026-10-01) — Models tab.
- [DONE] Appearance has more variations (contours, candles, liquidity, halftone, fractal). — (2026-10-02, "you could add more on your own time") — lib/workbench/art.ts.
- [DONE] Compute lives in Settings with a link from the Lab. — (2026-10-02, "adding compute can be in the settings") — Compute tab; lib/lab/panels/ResourcesPanel.svelte:121.
- [DONE] Settings has a Developer tab with demo mode and component library. — (2026-10-01, "demo mode is on oh that's cool") — routes/settings/+page.svelte.

---

## Mini apps

Pass 1 built 2026-10-04 (Apps screen, see UI-LEDGER.md), awaiting operator review. Items below marked BUILT are addressed, not ticked.

NOT DONE
- [BUILT, awaiting review] Many more mini apps (news and sentiment, and others); three kinds: remix screens, headless apps, extensions. — (2026-10-03, "we can have way more mini-apps") — Backlog line, nothing built.
- [DONE] Retire the Research demo mini app. — (2026-10-03, "this research mini app is very useless now") — Still on the rail in demo mode (lib/workbench/workbench.svelte.ts:32; routes/apps/demo-research/+page.svelte).
- [BUILT, awaiting review: Home and Portfolio widgets only, Lab not yet] Show how mini apps are made and rendered, including building a variant from widgets taken from Portfolio or the Lab. — (2026-10-03, "combine certain functionalities from portfolio and then ... create a mini app") — No flow. He asked the agent to help him think this through.
- [BUILT, awaiting review: Run now, Pause, schedule, log, circuit breaker] Headless mini apps and workflows: how they are presented and run in the UI. — (2026-10-02, "mini apps and workflows that don't use the front end") — Only the Operations tab in the Library; no run surface.
- [NOT DONE] News and sentiment workflow shipped as a template. — (2026-10-03, "one of the workflows we should have as a template is one for news") — Portfolio events panel has an "Add a source or a news workflow" button that only shows a message (lib/portfolio/panels/EventsPanel.svelte:101).

PARTLY
- [PARTLY] A mini app declares its own tools, targets and attach sources, and may need none. — (2026-10-02, "some mini apps I don't think need actual bloody things") — Mechanism exists (lib/workbench/copilot-context.ts null targets/attach); only main, Lab, Portfolio use it.
- [PARTLY] The platform absorbs new mini apps and widgets without showing an error. — (2026-10-01, "it needs to be able to fit in without showing that there is an error") — Typed "unsupported" frame exists in MiniAppShell and TileBoard (lib/workbench/MiniAppShell.svelte:61-68).
- [PARTLY] Customisable component library: can the operator create new components? — (2026-10-01, "I can create new components of my own freaking") — Gallery lists the catalog (routes/gallery); backlog still says "decide".

DONE
- [PARTLY] Same widget controls everywhere (add to copilot, minimise, expand, close, add): Home's old widget grid still behaves differently from the Lab and Portfolio tiles. — (2026-10-01, "where is the minimization maximization") — lib/workbench/WidgetFrame.svelte, MiniAppShell.
- [DONE] Add widgets, edit layout, resize in edit mode. — (2026-10-02, "I can add widgets? Heck no way!") — MiniAppShell.svelte:123-130, :173-190.
- [DONE] Mini apps render well in small views. — (2026-10-01, "mini apps look good though in small views") — no change needed.

SUPERSEDED
- [SUPERSEDED] ML Studio as a mini app or workflow. — (2026-10-02, "Now the ML Studio, I think goes straight to the lab. This is a non-negotiable") — Redirects to the Lab Train layout (routes/apps/demo-ml/+page.svelte).
- [SUPERSEDED] Trading node as a mini app. — (2026-10-02, "backtesting ... not a mini app"; 2026-10-03 folded into Portfolio) — routes/trade redirects to Portfolio Live.
- [SUPERSEDED] Backtest lab as a mini app. — (2026-10-02, "it's now a standard icon, not a mini app") — Folded into the Lab.

---

## Lab

NOT DONE
- [NOT DONE] Genetic algorithms and the wider set of Lean-style experiments (parameter search, many metrics). — (2026-10-01, "to literally genetic algorithms there are so many experiments") — No code mentions it.
- [NOT DONE] Explain the sweep grid with a diagram, not text; show other layouts than the one grid. — (2026-10-03, "Maybe explain that to me a bit in a diagram") — Grid is built (lib/lab/panels/MatrixPanel.svelte) but no explanation view.
- [NOT DONE] Explain model slots. — (2026-10-03, "the one thing I don't understand is slots") — Slots tab exists (lib/lab/panels/SlotsPanel.svelte) with no plain-words help.
- [NOT DONE] Save compare sets as presets and "watch" them; primary and secondary compare layers; better equity and compare views. — (2026-10-02, "can't I just compare then save, then compare, then save") — lib/lab/panels/ComparePanel.svelte has no save; open in ledger.
- [NOT DONE] A proper training-runs tile and starting a training session from the editor. — (2026-10-02, "How do I start a training session?") — Training tile shows one pipeline (lib/lab/panels/TrainingPanel.svelte); guide covers it only by walk-through.
- [NOT DONE] Robustness checks editable and buildable from workflows. — (2026-10-02, "robustness itself can come from workflows") — Open in ledger.
- [NOT DONE] Agents live: their nodes, sub-agents, streamed work; agents on their own machines (EC2, Modal). — (2026-10-02, "I'm yet to see what they're actually doing live") — Static demo list (lib/lab/panels/AgentsPanel.svelte); ledger backlog.
- [NOT DONE] Editor: run state on nodes, saved-steps palette, copilot edits the graph. — (2026-10-01, "Show what happens while a step runs") — Open in ledger L5.
- [NOT DONE] Remove all mock data when wiring to the live backend. — (2026-10-02, "you should remove your mock data") — Future step.
- [NOT DONE] Order-flow views for charts (crypto venues provide it). — (2026-10-02, "Can we get in some order flow things") — Not in code; backlog lists it under the dead "Trading node" heading, should move to Portfolio Live.
- [NOT DONE] Evidence status of off-machine runs (Colab, AWS). — (2026-10-02/10-03 answers) — UI shows "exploration only"; ruling still open.

PARTLY
- [PARTLY] Resources tile also holding artifacts and recently used indicators. — (2026-10-02, "Then I think artifacts also come here") — See Library section.
- [PARTLY] "Build a new panel" and most edits run through copilot skills. — (2026-10-02, "being able to build a new panel might require skill") — Menu item only shows a message (routes/lab/+page.svelte:305-307).
- [PARTLY] Add a slot must work; add parameters and metrics everywhere. — (2026-10-02, "Can I add new metrics to measure?") — Scenario builder lets you add markets, parameters and measures (lib/lab/ScenarioDialog.svelte:179, :340, :351-371); the "Add a slot" button exists (SlotsPanel.svelte:80) but not wired.
- [PARTLY] Templates in the Lab, including the one he could not find again. — (2026-10-02, "I can't find the template") — Start dialog can "keep as a template" (lib/lab/StartDialog.svelte:374), pod templates exist (lib/lab/pods.ts); no template gallery.
- [PARTLY] Any compute provider; each run shows where it ran; agent swarms visible with location. — (2026-10-02, "I can use colab I can use AWS") — Machines, pulse marking (lib/lab/EnvChip.svelte, themes.css:341); real adding needs backend.
- [PARTLY] StrategyQuant patterns (databank, what-ifs, robustness ladder, walk-forward matrix, cluster pass). — (2026-10-01, "what if scenarios the editors and whatnot") — Runs table, scenarios, robustness ladder, matrix built; databank saved views and cluster pass rule not confirmed.
- [PARTLY] Custom workflows as first-class (train in a pattern, test a hypothesis). — (2026-10-02, "a custom workflow ... then what?") — Copilot-led walk exists (lib/lab/guides.ts); workflows are not first-class objects beyond Resources list.
- [PARTLY] Import a model or code built elsewhere (ONNX, notebook, repo). — (2026-10-02, "I can import a Jupyter notebook") — Import modes exist (lib/lab/panels/EditorPanel.svelte:49); runs only against demo data.

DONE
- [DONE] Authoring, Backtest lab and ML Studio merged into one permanent Lab. — (2026-10-02, "Authoring, backtesting, ML, all of them are combined in one lab") — routes/lab/+page.svelte; old routes redirect.
- [DONE] Tiling board with saved layouts, linked panels, minimise dock that reflows others. — (2026-10-02, "you've really done the minimizing thing quite well") — lib/workbench/tiles/*.
- [DONE] Tile border colour for link groups and paper/live. — (2026-10-02, "You can color code the border itself") — lib/lab/..., lib/portfolio/bits.ts:34-35.
- [DONE] Machine switch connects first, then scopes the whole Lab, with a "nothing here" state per layout. — (2026-10-03, "make sure it's connected") — lib/lab/MachinePicker.svelte, MachineEmpty.svelte, LabStrips.svelte; commit 5aee5513.
- [DONE] Start something new: copilot-led survey with question cards, then layouts switch step by step. — (2026-10-03, "the options here are absurdly poor") — routes/copilot/+page.svelte:232; lib/lab/StartDialog.svelte.
- [DONE] Scenario generator (pairs, timeframes, pair trading) with styled drop-downs. — (2026-10-02, "that scenario generator ... is bloody nice") — lib/lab/ScenarioDialog.svelte.
- [DONE] One Resources tile in every layout; compute tile folded in; machine status in the bottom bar. — (2026-10-02, "we can call it Resources") — lib/lab/panels/ResourcesPanel.svelte; lib/workbench/StatusBar.svelte:50.
- [DONE] Curated default layouts (no equity in Build, runs not everywhere). — (2026-10-02, "in build, why do we have equity?") — ledger L12.
- [DONE] Node editor readable over the background; code mode; import; inspector; minimap toggle. — (2026-10-02, "the background makes it difficult to see") — lib/lab/panels/EditorPanel.svelte; solid backing (themes.css:394).
- [DONE] Lab copilot with its own tools, targets, attach, sessions and starters. — (2026-10-02, "copilot for even a node-based editor needs to be specific") — lib/lab/copilot.ts.
- [DONE] Pods bench (Design, Test, Paper) and Strategies bench (Build, Test, Train, Compare). — (2026-10-03, "there are so many tabs up here") — routes/lab/+page.svelte:57-60; ledger round 4.
- [DONE] Pod resources differ from strategy resources. — (2026-10-03, "resources under pods are very different") — lib/lab/panels/PodResourcesPanel.svelte.
- [DONE] Stress board with your own scenarios added through the copilot. — (2026-10-03, "I'll add my own custom things with co-pilot") — lib/lab/panels/StressPanel.svelte:56-115.
- [DONE] Paper trading for new risk and sizing systems happens in the Lab. — (2026-10-03, "they have to go through paper trading themselves") — lib/lab/panels/PaperRunPanel.svelte, PaperFeedPanel.svelte.
- [DONE] Head to head replaces the unclear comparison table. — (2026-10-03, "pod comparison ... I don't get it") — lib/lab/panels/HeadToHeadPanel.svelte.
- [DONE] Lab demo data on spot crypto. — (2026-10-03) — lib/lab/demo.ts.

SUPERSEDED
- [SUPERSEDED] Allocate tab. — (2026-10-03, "allocate is out completely") — Now "Run together" in Lab Test (lib/lab/panels/PodEquityPanel.svelte:95).
- [SUPERSEDED] Separate Pods, Pod test, Pod compare and Allocate tabs. — (2026-10-03, "these tabs are so many") — Replaced by the Pods bench.
- [SUPERSEDED] Colab is "not evidence" vs "any provider allowed" confusion. — (2026-10-03 answer) — Any provider allowed; evidence question still open (see NOT DONE).

---

## Portfolio

NOT DONE
- [NOT DONE] MIS gets logs, indicators and model views later. — (2026-10-03, "I want to be able to add indicators") — Placeholder only (lib/portfolio/panels/MisPanel.svelte).
- [NOT DONE] Portfolio items link back to the Library (bot cards, journals, evidence). — (2026-10-03, "how does the library connect to all this?") — No hrefs on Road-to-live cards.
- [NOT DONE] Main copilot or Lab copilot can wire a Lab-built pod or workflow into Portfolio. — (2026-10-03, "the co-pilot can wire that stuff from the lab to here") — Backend skills; UI has no hand-off beyond the paper tab's "Promote to live".

PARTLY
- [PARTLY] Spot crypto only; IC Markets, cTrader, CFDs and prop firms removed. — (2026-10-03, "IC markets is meant to be totally out") — Portfolio and Lab done; Home, Library demo bots (EURUSD) and Settings text still FX-style.
- [PARTLY] Events and news split by crypto and FX with sentiment, each item naming a backend source. — (2026-10-03, "every little bit of information ... should have a source") — Built (lib/portfolio/panels/EventsPanel.svelte); data is demo.
- [PARTLY] Promotion card: sign and activate. — (2026-10-03, "if I don't promote can I sign an activate?") — Blocked correctly; the operator said the card needs more thought (lib/portfolio/panels/SigningPanel.svelte).

DONE
- [DONE] Portfolio as a permanent page; promotions, risk and sizing live here, not in the trading node. — (2026-10-02, "Risk management, position sizing is going to be portfolio") — routes/portfolio/+page.svelte.
- [DONE] Trading node folded into Portfolio as a Live section; separate node screen gone. — (2026-10-03, "a trading node won't be necessary") — routes/trade redirects to ?layout=live.
- [DONE] Books renamed Pods; pod page redesigned with bigger controls, save and discard. — (2026-10-03, "let's call them pods") — lib/portfolio/panels/PodPanel.svelte:413-420.
- [DONE] Every pod has a live side and a paper side. — (2026-10-03, "every pod should have a live mode and a paper mode") — lib/portfolio/panels/PodsPanel.svelte:65-71.
- [DONE] Live layout: positions on top with exposure and correlation as tabs; bot charts below; sortable positions. — (2026-10-03, "put positions on top, put the charts at the bottom") — lib/portfolio/panels/HoldingsPanel.svelte; portfolio.svelte.ts:36-44.
- [DONE] Trading servers actionable (test latency, restart, drain) and shown in the header. — (2026-10-03, "trading servers ... I can't do anything to it") — lib/portfolio/panels/NodesPanel.svelte; ServersStrip.svelte.
- [DONE] Kill switch always in the header, per server or per pod as a grid. — (2026-10-03, "kill switch per server or per pod") — lib/portfolio/KillMatrix.svelte.
- [DONE] Road to live starts at paper; day progress inside the card; bot journal; player cards. — (2026-10-03, "it should be inside the bot card") — lib/portfolio/panels/RoadPanel.svelte, JournalPanel.svelte.
- [DONE] Paper/live colour on tile borders (orange paper, blue live). — (2026-10-02, "maybe in paper mode it's like orange") — lib/themes.css:316-317; bits.ts.
- [DONE] Pod templates for Portfolio. — (2026-10-03, "the lab and the portfolio should have templates") — lib/portfolio/TemplatesDialog.svelte.
- [DONE] Portfolio copilot with own tools and targets. — (2026-10-03, "the portfolio copilot is also very specific") — lib/portfolio/copilot.ts.
- [DONE] Many accounts across Binance, Bybit, Coinbase, Kraken. — (2026-10-02, "seven accounts ... Binance, Coinbase, bybit") — lib/portfolio/demo.ts:13-15; AccountsPanel.

SUPERSEDED
- [SUPERSEDED] Dedicated portfolio optimisation page. — (2026-10-01, "portfolio optimization seriously deserves its own page") — Moved into Lab as "Run together" (2026-10-03).
- [SUPERSEDED] Order of Live tiles ("charts across the top"). — (2026-10-03 09:17) — Replaced by positions on top, charts at the bottom (2026-10-03 10:01).
- [SUPERSEDED] "Waiting for you"/promotion and Protection widgets on the trading node. — (2026-10-02, "this one is not going to be here") — Removed with the node.
- [SUPERSEDED] Research-paper, node-paper, live shown as separate stages in Portfolio. — (2026-10-03, "everything earlier stays in the lab") — Road to live begins at paper.

---

## Cross-cutting

NOT DONE
- [NOT DONE] A few purposeful animations (panel expand, run finishing, connect). — (2026-10-01, "I haven't seen charting, I haven't seen animations") — Only a pulse for remote work (lib/themes.css:341).
- [NOT DONE] Review the Minara reference site. — (2026-10-01, "I browse them myself") — Never reviewed.
- [NOT DONE] alphaXiv link 2409.06289 as the Sources example. — (2026-10-01, pasted link) — Not used.
- [NOT DONE] Multi-screen: open views on several windows. — (2026-10-01, "Can I have ability to add multiple screens") — Only the copilot pops out.
- [NOT DONE] Space management and layout rules that hold at full-screen desktop (1920, 2560). — (2026-10-01, "when i put it on full screen there is a lot of space") — Foundation says done; his 2026-10-02 verdict was still "unused space" on Home, Library, Settings, Agents.

PARTLY
- [PARTLY] Customisability ("Lego") app-wide: everything has defaults but can be added, removed, edited. — (2026-10-02, "customizability is paramount here") — Strong in Lab and Portfolio; Home, Library and Settings are not.
- [PARTLY] Templates on every page that builds things. — (2026-10-03, "templates ... for everything every page") — Portfolio and Lab only; Library and Home none.
- [PARTLY] Help/guide for "how do I train something new". — (2026-10-03) — See Copilot.
- [PARTLY] Design styles beyond themes. — (2026-10-03) — Four surface styles built; see Settings.
- [PARTLY] Vocabulary renames (Pods, spot crypto, no cTrader). — (2026-10-03) — See Home and Library.

DONE
- [DONE] Scrap the Grok UI; rebuild from the storyboard as a web app first. — (2026-10-01, "scrap the entire bloody thing") — SvelteKit app.
- [PARTLY] Build on shadcn-svelte and community components, with a component library page: 17 primitives and an 11-entry catalog; community extras never added. — (2026-10-01, "SHAD CN has MCPs ... you don't have to work from scratch") — lib/components/ui, routes/gallery.
- [DONE] Seven themes with frosted glass, ink background made trading-themed (fractals), themed scrollbars, larger text. — (2026-10-01, "they're scroll bars. They're ugly as hell") — lib/themes.css:287; lib/workbench/InkBackground.svelte; app.css font-size.
- [DONE] OpenBB-style widget controls (minimise, expand, close, add to copilot). — (2026-10-01, "that widget thing where I can close, minimize, maximize") — lib/workbench/WidgetFrame.svelte.
- [DONE] Unknown widget renders a typed "unsupported" frame, never an error. — (2026-10-01) — MiniAppShell.svelte:61.
- [DONE] See-through panels fixed: charts, graph canvases and nodes sit on solid backing. — (2026-10-03, "that opacity I think is the issue here") — lib/themes.css:394 `.solid-backing`; near-opaque tiles at :328.
- [DONE] Charting and calendar. — (2026-10-01, "I haven't seen charting ... A calendar") — lib/qmx/LineChart.svelte, lib/demo/CandleChart.svelte, Home "Next events".
- [DONE] Rail kept as is. — (2026-10-03, "keep what we have for now") — lib/workbench/destinations.ts.
- [DONE] One screen at a time with options, click-through and ledger. — (2026-10-02, "keep a ledger for your backlog") — UI-LEDGER.md.

SUPERSEDED
- [SUPERSEDED] "No themes for trading" read as no background art on trade screens. — (2026-10-01 → 10-03 answer) — Themes and art stay everywhere.
- [SUPERSEDED] Claude Design rail options A, B, C and "Claude's take". — (2026-10-03, "I'm okay with what we have") — Rail unchanged.
- [SUPERSEDED] Whole-frame paper/live border. — (2026-10-02) — Tile borders instead.

UNCLEAR
- [UNCLEAR] T3 Code as a reference platform. — (2026-10-01, "another platform called T3 Code") — Never followed up.
- [UNCLEAR] Make the "Markets" tab Bloomberg-like only in tiling, or add widgets from other apps. — (2026-10-02, "Bloomberg Terminal ... would do this far better") — Tiling covered; scope of "Bloomberg-like" unclear.

---

## Missing from UI-BACKLOG.md (not in the current backlog at all)

Not in UI-BACKLOG.md and not in UI-LEDGER.md either:
1. How the Library connects to Lab, Portfolio, Copilot, Home and mini apps: a real Library picker for "attach from Library", "Save to Library" from chat, Library links on Portfolio bot cards, Library items showing where they are used. (The operator's last message; only a vague "Library" pass exists.)
2. Library detail pages still say "Book" and "node"; "Promote…" should go to Portfolio, Road to live.
3. "New session" and "Search sessions" buttons in the main Copilot are disabled.
4. Settings Appearance copy still says trading screens never show the background (contradicts the 2026-10-03 ruling).
5. Remaining design styles (neumorphism, claymorphism, skeuomorphism, minimalism) and a background art generator.
6. Explain the sweep grid with a diagram; explain model slots in plain words.
7. Move "order-flow views" out of the dead "Trading node" heading into Portfolio Live.
8. Home still on the old widget grid: minimise does not reclaim space, no tiling engine; Home demo data still FX and "books".
9. A way to build a mini app (or Portfolio variant) from widgets taken out of Portfolio or the Lab.
10. Library "Turn into hypothesis" and "Save to Library" stay disabled; no plan beyond "needs daemon".

In UI-LEDGER.md only (not in UI-BACKLOG.md): Library templates; help or guide feature; sessions that run for days; main copilot taking in conversations from other screens and Lab pop-out; Lab compare presets and "watch"; slots; agents live; Home still FX.

---

# Older backlog notes (history)

# QMX UI backlog (operator feedback, 2026-10-01 round 5)

Branch `ui-review/repair`. Demo data only; backend wiring is Codex's (see BACKEND-REQUIREMENTS.md).
Order of work: **design system first**, then rebuild screens on it. Most problems below come from screens built one by one.

## Recovered from the transcript audit (2026-10-03)

An agent re-read every operator message in this session and checked it against these files. Rounds 1–4 (2026-10-01) were never written down; they are summarised here so a rebuild doesn't undo them.

### Built in rounds 1–4 (keep)

- Themed scrollbars; larger base text; no focus box on the composer; the composer grows with its text.
- Model picker in the composer; copilot pop-out window.
- Seven themes ("Plain" removed); frosted glass, neumorphic wells, ink background made trading-themed (fractals).
- Player cards for bots, models, apps and workflows with named measures and **no overall rating or tier** (QMB bans composite scores).
- Artifacts tab restored in the Library; headless-app operations on detail pages; ticker; Sydney/Tokyo clocks removed.

### Rulings (recorded now)

- Grok UI scrapped; the Excalidraw storyboard is the working spec. Web app first, desktop wrapper later; spacing judged at full-screen desktop (1920–2560).
- Build on shadcn-svelte (Rhea preset) and community components, not from scratch. Read docs/, _bmad-output and _docwork before work.
- Model selection lives in Settings, set per copilot.
- Research pipeline follows the current docs: hypothesis → graduate → QMB evidence → paper → promote → activate (WF1/WF2 only as labels).
- ML has a home in the UI (now the Lab) because models from papers should be usable anywhere: risk, sizing, MIS.
- Crypto is the design focus, with more than one broker or exchange per setup.
- The operator delegated chunking: "keep a ledger… I believe you are smart enough" (2026-10-02).
- Customisability ("Lego") applies to the **whole app**, not only the Lab.

### Needs the operator's confirmation

- [x] Ruled 2026-10-03: themes and background art stay everywhere, trading included. The real problem was see-through panels: charts, graph canvases and nodes now sit on solid backing.
- [x] Ruled 2026-10-03: compute providers (any VPS, AWS, Colab, GPU clouds) are added and removed by the operator; the backend adapts. Two kinds of work need placing: the copilot's own agents and swarms, and workflow agents from the node editor that run locally or on servers (long or always-on jobs). Storage buckets too. Evidence status of off-machine runs still open (UI shows "exploration only" until ruled).
- [x] Ruled 2026-10-03: keep the current rail and shell. "If I did not choose, it means surprise me; I haven't complained, so I'm okay with it."
- [x] Restated 2026-10-03: templates across the app (Lab most, then Portfolio, Library, Home); the operator will mostly start from templates rather than build from scratch.

### Missing items (now on the backlog)

- [x] Lab machine switch connects first and scopes the whole Lab; "nothing here" state per layout (done 2026-10-03, `5aee5513`).
- [x] Start something new: outside work, custom workflows and training start as a main-copilot conversation with question cards, then a guide strip drives the Lab layouts (done 2026-10-03).
- [ ] Genetic algorithms and other Lean-style experiment types in the Lab (dropped in the merge).
- [ ] Animations: a few purposeful ones (panel expand, run finishing, connect).
- [ ] Review the Minara reference site (never reviewed).
- [ ] alphaXiv link 2409.06289: use as the example item for the Sources feed.

### Details that were dropped (now on the backlog)

- [ ] Library: diagrams generated from articles (no AI, or a cheap model), not only key-point summaries.
- [ ] Sources: videos as a research source; any site can become an in-app web app (Omarchy-style).
- [ ] The copilot builds **whole mini apps and workflows** from the component library through skills, not only widgets.
- [ ] Resources tile also holds artifacts.
- [ ] Home tab previews link through to the full pages (Markets → Portfolio, Agents, main Copilot).
- [ ] Settings: each tab gets its own layout for its job, not the same card pattern everywhere.
- [ ] Headless mini apps and workflows: how they are presented and run from the UI.
- [ ] Stress-test the UI across many failure scenarios; the copilot inherits any inconsistency.

## Round 6 feedback (2026-10-02, operator walk-through, ~40 min dictation)

**Verdict:** visual design gets marks; layout, usability and intentionality are poor. Too much unused space, too many words and too little to do, screens rushed. **New way of working: one screen at a time**, done properly (options, then build, then click-through user journeys, then backend mapping), before moving on.

### Working method (operator ruling)
- [ ] One screen per pass. Each pass: study the job, 2–3 layout options, operator picks, build, then drive it like a user (click, drag, minimise, small window, many accounts, empty and overloaded states), then list what the backend must provide.
- [ ] Drive pages in the browser with intent, not only screenshots.
- [ ] Use the local design skills (frontend-design, design-system-compliance, verify-ui-change) on every pass.
- [ ] Settle the design system / layout rules (space management, density, text measure) so screens stop drifting.

### Structure (needs operator ruling)
- [ ] Proposal: one permanent **Lab** that merges Authoring, Backtest lab and ML Studio (all are "experiment, test, prove in paper, then live"). Some work needs a node editor, some code, some neither; bring in models built outside (Claude Code, Codex, ONNX). Add datasets, reports, tests, models and features as first-class items. External compute (Colab, GPU providers, external engines). StrategyQuant-style scenario generation: many pairs, timeframes, pair trading. Needs a deep design pass (subagent research allowed). Backend may need restructuring (Codex/docs ruling).
- [ ] Permanent rail destinations rather than mini apps: Lab, Portfolio (books, risk, position sizing, promotions/approvals live here), Trading node manager.

### Copilot and composer (all surfaces)
- [ ] Tools, Target, Attach and messaging differ per context (mini app, Lab, node). An app declares its own tools, targets and attach sources; some apps need no attachments.
- [ ] App copilot: multiple sessions with history, and its own settings (VS Code style header).
- [ ] Main copilot: session column must collapse on its own (keep Browser/Terminal/Diff open). Sub-agent preview missing.
- [ ] Show how a message looks with an attached document, a Library item, and a mini-app item.
- [ ] Copilot can create a new widget (JSON render, as in the storyboard): show the flow, and how it connects front to back.

### Widget grid (all boards)
- [ ] Minimise must reclaim space: minimised widgets dock to the bottom and the rest fill up (Bloomberg-style space management).
- [ ] Tiling quality (Markets view especially).
- [ ] Operator likes: Edit layout, add widget, the idea of copilot-built custom widgets; good layouts become templates.

### Home
- [ ] Add your own tabs (dashboard you build); current tabs are previews.
- [ ] Notifications area at the top for things needing attention.
- [ ] Drop the "Home" word in the header. Keep the ticker.
- [ ] "While you were away" too thin for many concurrent jobs (e.g. nine models training on a GPU provider).
- [ ] Many accounts across brokers/exchanges (Binance, Coinbase, Bybit, …); crypto can have more than one broker.
- [ ] News widget too thin; unused space below.
- [ ] Agents view leaves space unused.

### Trading node
- [ ] Paper/live colour on the tiles' borders, not the whole page frame.
- [ ] Order-flow views for charting (crypto venues provide it).
- [ ] Drop "Waiting for you"/promotion here; promotion belongs in Portfolio.
- [ ] Protection widget not needed.

### Authoring (until merged into Lab)
- [ ] Whole page needs a rethink: too compact; background makes editor, sidebars and bottom tabs hard to read.
- [ ] Copilot for the node editor should be specific to it.

### Library
- [ ] Reader wastes the right side on wide screens (text-heavy page): use the width.
- [ ] Sources: embedded browser fails inside QMX (sites refuse embedding); works outside. Scraping (e.g. Firecrawl) is a backend item.
- [ ] Artifacts tab: items don't open; needs a full rethink.
- [ ] Cards: operator loves them. Colour by family (e.g. scalper = blue and gold), or let the operator edit the card art as a preset. Add list view vs card view. ML models should look different from bots.
- [ ] Model detail page is poor (unused space, no function); app/workflow detail likewise. Summary cards are good.
- [x] Back arrow on a detail page returned to the Knowledge tab; now returns to the tab the item came from.

### Settings
- [ ] Every tab needs depth and things to do; too many words, nothing clickable.
- [ ] General: thin; use the space.
- [ ] Models/providers: will change (Claude CLI proxy for model providers).
- [ ] Trading nodes: a node is a VPS. Show server, provider, region, IP, latency, status, who uses it; kill it from here; paper and live may not be separate nodes.
- [ ] Data & sources: can't add anything. Sources need API keys, scraping workflows, cron schedules, use by mini apps.
- [ ] Appearance: fine; more variations welcome.

## 0. Foundation (do first)

- [x] One `MiniAppShell` for every mini app: name, views tabs, edit layout, copilot toggle, widget grid, optional app copilot. Research, Trade, Lab, ML Studio all use it.
- [x] Every widget uses `WidgetFrame` with the same controls: add to copilot, minimise, expand/return, close (edit mode), add widget.
- [x] Page layout primitives with spacing rules that hold at 1440, 1920 and 2560 wide (operator uses full-screen desktop). Fill width with denser grids; no big empty areas.
- [x] Fresh-install empty states must also fill the page sensibly (most things will be empty on day one).
- [x] More depth and personality across the app: an overlay/scrim under content so the ink background never fights charts or text.
- [x] Platform must absorb new mini apps / widgets without broken UI: unknown widget type or missing data renders a typed "unsupported" frame, never an error (backend + catalog).
- [ ] Component library: can the operator create new components? (decide: authoring components vs only composing catalog entries).
- [x] Background art: multiple variants, savable. Five styles (fractal, contours, candles, halftone, liquidity), density/strength/glow/variation, built-in and saved variants in Settings > Appearance; per machine.

## Home

- [x] Too much empty space; denser layout.
- [x] Live equity next to paper equity (accounts).
- [x] Strategy pipeline: scrollable and expandable columns; redesign.
- [x] News belongs on Home (not Library); richer news panel.
- [ ] Review dialog fine; consider richer approval flow.

## Copilot

- [x] Clicking a bot card in chat opens that exact version in the Library.
- [x] "Add to copilot" must visibly do something (chip + toast + jump).
- [ ] Target menu: keep, but think through failure cases later.
- [ ] Sub-agents and workflow agents visible (QMA: copilots, sub-agents, workflow agents e.g. quant research / analysis).

## Library (redesign; candidate for a dedicated pass)

- [x] Knowledge: go back to the three-pane layout (list | reader | side), not the card grid + separate page.
- [x] Sources: browser inside QMX (preview pane), not pop-up windows; same styling.
- [x] Entity detail: too much space; overlay instead of background; combine Evidence/Journal/Connections/Artifacts into fewer, denser views; Overview may merge.
- [ ] Apps & workflows: tighter layout.
- [ ] Saved configurations (test presets, model configs like two GBM configs, feature sets) — these are what "artifacts" were meant to be; maybe a different name. Backend addition.

## Authoring

- [ ] Minimap: removable or minimisable.
- [ ] Small window sizes break the editor.
- [ ] Palette = toolbox: saved test/model/feature configurations; add datasets.
- [ ] Show what happens while a step runs.

## Trading node

- [x] ~~Paper vs live: whole-frame border colour~~ Superseded 2026-10-02: the colour goes on the tile borders, not the whole frame (see Round 6, Trading node).
- [ ] Multiple nodes; latency test.
- [ ] Kill-switch authority (research docs).
- [ ] Book: risk management and position sizing — where it lives.
- [ ] Portfolio optimisation: a dedicated page (not a mini app).
- [x] Use the same widget components as Research.

## Backtest lab / experiments

- [x] Read docs on how experiments work across QMX; redesign accordingly.
- [x] StrategyQuant reference: what-if scenarios, editors, robustness.

## ML Studio

- [ ] Probably a workflow, not only a mini app (dataset→features→split… is a pipeline). Decide placement.
- [ ] "Model ideas from your Library" should be generated automatically (backend).
- [ ] Slots: models mostly for stress testing, MIS, risk, position sizing.

## Settings

- [ ] Data sources: add new ones (file upload: Excel/CSV, API providers).
- [ ] Inference providers page good; keep.

## Multi-screen

- [ ] Open views on multiple screens/windows.

## Reference: StrategyQuant X patterns to borrow (research 2026-10-01, public docs only)

- One skeleton for every experiment module: **Run / Settings / Results** tabs; live log + progress on Run.
- Results table ("databank") docked at the bottom with a detail pane for the selected row; saved column views; bounded top-N with dedupe of near-identical strategies.
- **What-if scenarios**: named, composable transforms of an existing trade list (no re-backtest), each with a baseline-relative pass rule ("≥ 80% of baseline"), shown as an overlay on the baseline equity curve.
- **Robustness checks tiered by cost** (fast → slow), sequential with early exit; cost estimate beside expensive tests; "run all anyway" switch for diagnostics.
- Monte Carlo: fan chart **plus** percentile table (80/90/95%); parameter perturbation as "probability changed" + "max % change".
- **Walk-forward matrix**: grid of runs × OOS% coloured pass/fail, click a cell to update the equity chart, cluster-pass rule (e.g. 7 of 9 in a 3×3 block); flat heatmap, not only 3D.
- Filters scoped to IS / OOS / robustness / portfolio slices.
- Portfolio: correlation matrix with selectable basis (daily/weekly/monthly; P&L or counts) and threshold colouring; sector caps.
- Task pipelines: vertical task list, each task with source/target result sets; conditional loop tasks (needs visible iteration counter + cap); shipped example pipelines; save/load a whole pipeline.
- Avoid: deep nested settings; locked features that look broken; research and portfolio split across products.
- Caution: QMB bans composite scores/ratings — a "fitness score" can only be a user-defined sort, never evidence.

## Reference: what the docs already rule (research 2026-10-01)

- **Agents (QMA)**: ontology Desk → Role → Quant → Agent → Subagent. Roles: Researcher, Trader, Developer, Analyst, PM ("Portfolio Manager"). Quants are persistent named actors with mailboxes; Agents are running instances; Subagents are leaves (no mailbox, no delegation, capabilities ≤ parent). Copilot = `psess:` product sessions (profiles authoring / app-use), not an Agent record. Workflow agents = Graph Template `agent` nodes pinned to a `worker_template`. Agents never touch the money path (no orders, sizing, bindings, kill switch). UI shows JobHandle states queued/running/done/failed/cancelled/aborted/**unknown (never shown as failed)**; approvals arrive as `approval_request` for the operator principal; closing UI never stops an agent.
- **Experiments**: CT-47 ExperimentSpec (fp1, code/config/data/env refs, seed, cost assumptions, lineage). Three lanes chosen by the door: ungoverned (`qmb.run()`, no ledger), governed (QMB ledger line + CT-32, "research-paper"), coordinated (QMA places runs under a spec; Experiment Ledger). "Project/workspace" are UX aliases only. One `qmb` run per environment; governor queues, never oversubscribes. Run roles confirmation/trial/replicate/aborted; verdict is a read-time fold. Compare must refuse when recipes, splits or completeness differ, or a run is unknown. Reopen = walk ExperimentSpec successors.
- **Kill switch**: KSA GREEN..BLACK; automatic escalation only; de-escalation is operator `resume` naming scope; scopes global and per (venue, account). Effects suspend_new | drain | flatten via UI-editable `registry:ksa_effect_matrix`. Kill line = per-Book capital floor (breach flattens and stands the Book down). Flatten authority: operator always; Book policy via pre-declared triggers; protection authority per matrix; never the adapter. Exits are never blocked. Node control = closed list of powers (resurrect, resume, resolve_unknown, flatten, escalate, paper flip/reset, promotion sign/activate, config_version_activate, seat_reinstate…), revalidated server-side and journaled. Show "requested" apart from "enforced"; read models carry authority source + source/receive time; no generic LIVE/PAPER toggle.
- **Books**: authority bot → Book → BMS → operator. Book owns admission, sizing, doors, leash, exits; BMS owns accounting, constraints, kill line, reporting. Sizing ladder in USD (book_capital, loss_floor, loss_runway, period_loss_budget, r_unit_price, position_risk_amount = requested_r × r_unit_price). Template sections: charter, footprint_requirements, money_rules, admission_bar, leash_grammar, capacity_and_sweep, exit_policy, control_policy, protection_windows, paper. UI edits mint a new version (branches-from), never mutate. Seat active|benched; Book mode LIVE|PAPER; binding live|paper|stood-down (three vocabularies). **No ratified portfolio-optimisation concept** — operator wants a dedicated page; flag as new scope.
- **Data sources**: all via CT-15 → CT-10; Dukascopy primary (personal use), news calendar, cTrader intended. CSV import = a CT-15 adapter (no Excel in docs). Upload = `PUT /artifacts/stage` (refuses while stage_max_bytes unset). Dataset node shows provider, coverage, schema, units, timezone, calendar, freshness, provenance, entitlement, revision; missing/denied/truncated distinct.
- **Unknown views/widgets**: PackUiRequest ingest drops bad views with typed diagnostics (unknown_pack_ui_schema, view_op_not_contributed, view_schema_drift…); unknown renderer → empty pane with visible reason, `failure_class=view`, pack stays enabled, other views mount, jobs untouched. Closed slots app-nav / canvas-widget / detail / copilot-panel / preview-tab; renderers native / json-render / mcp-app.


## Copilot pass: rules for things the copilot creates (operator, 2026-10-03)

The copilot will make panels, blocks, scenarios, layouts and mini apps. To stop overflows and broken screens:
- [ ] It builds only from the component catalog (shadcn-svelte + QMX components), never raw HTML or its own CSS.
- [ ] Every generated panel declares a size range (min width and height) and is checked at its smallest size and in a narrow tile before it is offered.
- [ ] Text truncates or wraps by rule; numbers use the `num` style; long lists scroll inside the panel, never the page.
- [ ] Unknown or broken panels show the "not supported" frame with a reason, never a crash (already in TileBoard).
- [ ] New things arrive as a draft you can preview, keep or discard; nothing replaces a working layout silently.
- [ ] Component library refresh: update shadcn-svelte components and document which ones the copilot may use.

## Mini apps (operator, 2026-10-03)

- [ ] Many more mini apps: news and sentiment, and others. Three kinds: remix screens, headless apps, extensions. Retire the Research demo.
