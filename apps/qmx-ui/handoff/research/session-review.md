# QMX UI session review (2026-10-01 to 2026-10-03), written 2026-10-04

Reviewer: independent read of every operator message (user_msgs.txt, answers_full.txt, late_msgs.txt, the storyboard text), the main agent's replies, UI-BACKLOG.md, UI-LEDGER.md, BACKEND-REQUIREMENTS.md, the earlier audits, and the code at HEAD 47a65197.
Code paths are relative to `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\`. I also opened the built preview (localhost:4173/copilot) at 1920x1080 and 1280x800.

Status words: DONE, PARTLY, NOT DONE, CONTRADICTED (built differently from what he asked). "Demo" means it only shows sample content and does nothing when used.

---

## 1. Copilot verdict

### 1a. Everything he asked about the copilot

| # | Request (operator words, date) | Status | Evidence |
|---|---|---|---|
| 1 | Quick chat layout: "the quick chat thing, it doesn't make bloody sense" (10-01) | DONE | Rebuilt as a full page, routes/copilot/+page.svelte |
| 2 | "I would like to see a chat session though" (10-01) | DONE (demo) | One scripted transcript, src/lib/copilot/demo.ts:148-455 |
| 3 | Text and spacing: "the text font is so small, it's not even funny" (10-01) | NOT DONE | Measured at 1920: 75 of 134 visible text pieces are under 12px; Thread/WorkArea use text-xs and text-[11px] throughout |
| 4 | Model picker: "I also want to be able to change the model" (10-01) | DONE | src/lib/workbench/Composer.svelte:281-307 |
| 5 | "The tools attachment, I can't do anything with that" (10-01) | PARTLY | Tools toggle; Library picker works; Upload disabled; other attach sources only toast (Composer.svelte:160-168) |
| 6 | Add a widget to chat: "Can I add it to chat?" (10-01) | DONE | workbench.addRef chip + toast (src/lib/workbench/workbench.svelte.ts:305) |
| 7 | Pop-out: "detached to a bigger screen" (10-01) | PARTLY | window.open of a fresh /copilot copy; no shared state with the first window (routes/copilot/+page.svelte:36-42) |
| 8 | Copilot builds mini apps: "meant to be able to build all mini apps" (10-01) | NOT DONE | No renderer from a spec; "Build a new panel…" only toasts (routes/lab/+page.svelte:306-311, routes/portfolio/+page.svelte:200-205) |
| 9 | Input box: "I don't know why there is a box that forms" (10-01) | DONE | Composer.svelte:140-146 (no focus ring, grows then scrolls) |
| 10 | Card edits in chat: "if maybe we've done an edit the card variables can change" (10-01) | DONE (demo) | Before/after EntityCards with changed fields, src/lib/copilot/Thread.svelte:295-318 |
| 11 | JSON render: "maybe jSon render comes in what do you think" (10-01) | NOT DONE | json-render not in package.json; src/lib/qmx/catalog.ts is a description list only, nothing renders from it |
| 12 | Copilot knows each app: "how is the co-pilot also going to know that" (10-01) | PARTLY | Readiness checks per target exist; "Who answers" list is hard-coded (src/lib/copilot/aim.svelte.ts:32-42) |
| 13 | "model selection actually is meant to be inside the settings" (10-01) | PARTLY | Settings has 3 generic profiles (Copilot, App copilot, Background agent), not per surface; no instructions, tools or skills (routes/settings/+page.svelte:120-135, 297-340) |
| 14 | Chat card opens the Library item: "a link that takes me straight to that version" (10-01) | DONE | Thread.svelte:301-316 |
| 15 | Target menu: "there are lots of issues that can come from it" (10-01) | PARTLY | Rebuilt as Ask/Plan/Do + reach + who answers (src/lib/copilot/AimMenu.svelte); choosing anything changes nothing, no failure states |
| 16 | Agents visible: "I haven't seen sub-agents running" (10-01) | PARTLY | Sub-agent cards in the thread and Activity tab (Thread.svelte:142-180, src/lib/copilot/WorkArea.svelte:117-173); workflow agents vs copilot sub-agents not told apart |
| 17 | Consistency first: "i don't think the co-pilot will be okay" (10-01) | NOT DONE | Two board systems (MiniAppShell on Home vs TileBoard in Lab/Portfolio); 12 raw `<select>`, 14 hand-made radio groups, 61 arbitrary pixel text sizes across src |
| 18 | Surface copilots specific: "needs to be a bit more specific" (10-02) | DONE | src/lib/lab/copilot.ts, src/lib/portfolio/copilot.ts |
| 19 | Per-context tools/target: "not just tools, also the target and message art" (10-02) | DONE (mechanism) | src/lib/workbench/copilot-context.ts; only main, Lab, Portfolio use it |
| 20 | "attach also needs a rethink" (10-02) | PARTLY | Same as #5; per-surface attach lists exist but mostly do nothing |
| 21 | "I want to have multiple sessions in application co-pilot" (10-02) | PARTLY | Session list in the side copilot header; picking one shows "messages load from the daemon" (src/lib/workbench/CopilotColumn.svelte:139-142) |
| 22 | Sessions column: "I want it to be able to collapse on its own" (10-02) | NOT DONE | No collapse control; only Focus hides it, and Focus also hides the work area (routes/copilot/+page.svelte:165-175, 241) |
| 23 | Work area: "browser terminal and diff to be there" (10-02) | NOT DONE for Diff | Tabs are Activity, Artifacts, Browser, Terminal, Preview; no Diff (WorkArea.svelte:32-38) |
| 24 | "You haven't also done the sub-agents preview" (10-02) | PARTLY | Agent cards with progress; you cannot open an agent to see its own work, nodes or log |
| 25 | "I want to see how a message looks like when I attach" (10-02) | PARTLY | Attachments show as name chips under the message only (Thread.svelte:88-98); no Library item card, no widget snapshot, no file preview |
| 26 | "I want to see how the co-pilot can create a new widget" (10-02) | NOT DONE | Same as #8 |
| 27 | "Settings for the copilot, it should take us straight to settings" (10-02) | PARTLY | Gear goes to the generic Models tab (CopilotColumn.svelte:121-127) |
| 28 | New session start: "A new session, the way it begins, I don't like this" (10-02) | CONTRADICTED risk | A new greeting + six "How do I…" cards was added without his review (src/lib/copilot/HowDoI.svelte) |
| 29 | "Things like tools, you can just use an icon" (10-02) | DONE | Icon chips with count badges (Composer.svelte:150-156, 244-251) |
| 30 | "being able to build a new panel might require skill" (10-02) | NOT DONE | Toast only (see #8) |
| 31 | "the copilot should be able to edit all this" (10-02) | PARTLY | Surfaces can draft text into a copilot (seed); nothing is edited |
| 32 | Start something new: "take it straight to a co-pilot chat" (10-03) | DONE (demo) | src/lib/lab/StartDialog.svelte:149, src/lib/workbench/GuidedStart.svelte |
| 33 | Copilot drives the Lab: "it can change from build to test to train" (10-03) | PARTLY | Guide strip in the Lab; the copilot itself changes nothing |
| 34 | Help: "some sort of helping thing feature" (10-03) | PARTLY | Six "How do I…" cards on a new session only; no help anywhere else |
| 35 | Long sessions: "that session can run for days" (10-03) | PARTLY (demo) | Status, age and agent count in the list (src/lib/copilot/SessionsSidebar.svelte:77-101); no timeline, no schedule, no "what happened while away" |
| 36 | "the portfolio copilot is also very specific" (10-03) | DONE | src/lib/portfolio/copilot.ts |
| 37 | "I can bring in conversations from other pages" (10-03) | CONTRADICTED | "Continue here" only relabels the session's origin (routes/copilot/+page.svelte:98-106); side copilot "Continue in the main copilot" opens /copilot with no session id (CopilotColumn.svelte:105); side-copilot sessions (src/lib/lab/copilot.ts:173-178) are not the ones in the main list (src/lib/copilot/demo.ts:85-146) |
| 38 | Second monitor: "I can have the lab ... a pop-out" (10-03) | NOT DONE | Only /copilot opens a window; no cross-window sync anywhere (no BroadcastChannel/postMessage in src) |
| 39 | "the co-pilot can wire that stuff from the lab to here" (10-03) | PARTLY (demo) | "Changed elsewhere in QMX" links (Thread.svelte:206-227) |
| 40 | Rules: "How do we prevent overflows? How do we prevent buggings?" (10-03) | NOT DONE | Six rules sit unticked in UI-BACKLOG.md:585-593; nothing enforces them in code |
| 41 | "how do we make sure that it doesn't restart the app" (10-03) | PARTLY | Answered once in chat (reply 10-03 12:22); not written into any doc Codex reads |
| 42 | "aiming the message at part needs a little bit more enhancement" (10-03) | DONE (static) | AimMenu.svelte; mode/reach/answerer change no behaviour |
| 43 | Session collections: "we can have like collections maybe per page" (10-03) | DONE | SessionsSidebar.svelte:60-74 |
| 44 | One session across Lab, pods, Portfolio (10-03) | DONE (demo) | "Weekend-safe pod" script, demo.ts:148-309 |
| 45 | "it actually exports in a new window" (10-03) | DONE | See #7 |
| 46 | Artifacts: "maybe the artifacts used in here" (10-03) | PARTLY | Every artifact opens the same hard-coded four numbers (WorkArea.svelte:272); Save to Library is a toast (Thread.svelte:246-255) |
| 47 | Skills: "skills sub-agents I haven't looked at those" (10-03) | NOT DONE | No skills anywhere in src (only two comments); UI-BACKLOG.md:29 ticks it as done |
| 48 | "how to render tools how to render commands" (10-03) | PARTLY | Tools: collapsible list (Thread.svelte:181-205). Commands: "/" list only pastes text (Composer.svelte:112-129) |
| 49 | "the ask user tool rather" (10-03) | DONE (demo) | Question card with options and "Something else" (Thread.svelte:319-364) |
| 50 | "perhaps this is where permissions can come in" (10-03) | DONE (demo) | Allow / Allow for this session / Not now (Thread.svelte:365-396) |
| 51 | "how does it delegate" (10-03) | PARTLY | Agent cards only; no hand-off tree or who-asked-whom view |
| 52 | "which tasks are running in the background" (10-03) | DONE (demo) | Activity tab; Stop only toasts (WorkArea.svelte:154-163) |
| 53 | "we haven't done the terminals" (10-03) | NOT DONE | A `<pre>` with a disabled input, hard-coded black and green colours (WorkArea.svelte:243-264) |
| 54 | "we haven't done the browser integration" (10-03) | NOT DONE | Browser tab is always an empty state (WorkArea.svelte:288-296) |
| 55 | "I think we should give it ability to shard CN" (10-03) | NOT DONE | No registry, no design-style doc, no copilot path to components |
| 56 | "it should be able to control anything" (10-03) | PARTLY | Reach checkboxes only |
| 57 | Karpathy: "I would like to learn from these papers" (10-03) | PARTLY | Library "Explain it as" drafts a copilot message; the copilot cannot show a diagram, page or video |
| 58 | Monitoring: "I would like to set up a crony perhaps" (10-03) | PARTLY | "/schedule" text and a "Watch something" starter; no schedule view |
| 59 | Storyboard: "open sessions, history settings for the agents" (10-01) | PARTLY | Sessions and history yes; agent settings no |
| 60 | Storyboard: "This can be a browser, an agentic browser" (10-01) | NOT DONE | See #54 |
| 61 | Storyboard: "This is where MCP apps configuration comes into play" (10-01) | NOT DONE | No MCP Apps renderer, no per-copilot permissions page |
| 62 | 10-04: "I believe you may have not done it quite well" | Agreed | See 1b |

Count: 62 items. DONE 19 (8 of them demo-only), PARTLY 25, NOT DONE 15, CONTRADICTED 2, plus 1 agreed verdict.

### 1b. Overall judgement

He is right. The copilot pass is a good-looking storyboard of one conversation, not a working screen.

- **You cannot talk to it.** In demo mode Send is disabled and Enter does nothing (Composer.svelte:90, 138, 313). I typed a message at 1920 and it stayed in the box. "New session" opens a greeting and then a dead composer. Every other part of this UI has some click-through; the copilot, which he uses most, has none.
- **It was rushed.** The commit landed 15 minutes after Library pass 2 (15:22 to 15:37, 1,900 lines). The working method he ruled on 10-02 (study, 2-3 options, he picks, build, click-through) was skipped. The Lab got research agents and four rounds; the copilot got one sitting.
- **Most of the right side is fake.** Browser is an empty state. Terminal is a styled `<pre>`. Preview shows the same four numbers for every artifact. Stop and Save to Library are toasts. There is no Diff tab, though he asked for it twice.
- **"Sessions across QMX" is not joined up.** The main list and the side copilots hold different sample sessions. "Continue in the main copilot" just opens the copilot page. "Continue here" changes a label. That is the opposite of "bring in conversations from other pages".
- **The rethought "aim" menu does nothing.** Ask/Plan/Do, reach and "who answers" are well worded but change nothing on screen, and the answerers are hard-coded.
- **Skills are ticked done but don't exist.**
- **Layout:** three columns at 1280 wide truncate session titles and agent lines. The work-area tab bar runs out of room. "This session" wraps onto two lines. More than half the text is under 12px, the thing he complained about on day one. The background art shows through the thread.
- **What is good:** the block types are the right vocabulary (plan, agents, tools, changes, artifact, question, permission, before/after cards). The session grouping, "Going on now" and the Activity feed are the right ideas. BACKEND-REQUIREMENTS.md gets a usable list of block shapes.

**What a stronger design would do:**
- A demo engine behind Send: typed prompts and slash commands stream blocks into a real thread, so every session can be clicked through like the Lab.
- One session store shared by every copilot. A hand-off shows what context was carried over and opens the exact session.
- A work area driven by what is in focus: artifact, diff, terminal, browser, a panel draft or a popped-out screen.
- A mission-control view for multi-day sessions: a timeline of steps, an agents tree with where each runs, schedules, and "while you were away".
- Generated panels shown inline as drafts, which can be pinned to Home, Lab or Portfolio. That is the JSON-render story he has asked for since the storyboard.

### 1c. Top 10 copilot fixes, ranked

1. Make Send work in demo mode with a scripted responder that streams blocks; give new sessions a real thread (Composer.svelte:90, 313; routes/copilot/+page.svelte:85-97).
2. Show the copilot building a panel end to end: install json-render, render a spec from the catalog as a draft in chat, then keep, discard or pin it to a screen. This replaces the three "Build a new panel" toasts.
3. One session model for the main and side copilots. "Continue in the main copilot" opens that exact session, and side copilots show their threads (CopilotColumn.svelte:105, 139-142; src/lib/lab/copilot.ts:173).
4. Sessions column collapses on its own while the work area stays open; stop re-mounting the panes with `{#key}` (routes/copilot/+page.svelte:163).
5. Make the work area real: add a Diff tab; use a real terminal component (shadcn-svelte-extras Terminal or xterm, read-only until ruled); a browser pane; a Preview that renders each artifact's own content (WorkArea.svelte:243-296).
6. Readability pass: text floor of 13px, fewer 10-11px labels, fit the 1280 layout (work-area tab bar, truncation), a solid backing under the thread.
7. Skills and copilot settings: show skills used per session, a skills list per copilot, and Settings per copilot (instructions, tools, skills, model, permission defaults).
8. Agent drill-in: click an agent to see its transcript, nodes, where it runs and its log; a delegation tree; Stop with real states.
9. Pop out any screen (Lab, Portfolio) into a window kept in sync with the copilot (BroadcastChannel now, daemon events later), with "changed here" highlights.
10. Attachments and commands that do something: an attached Library item or widget shows as a card in the message; slash commands start their walk; Save to Library works against a local store in demo.

---

## 2. Components and backend

### 2a. What he asked
- "I think the component library is what I really" want (10-01): shadcn MCPs and resources, not from scratch.
- "Did we do a component library?" (10-01); "we were meant to start with a component library" (10-01).
- "fit in without showing that there is an error" (10-01): new mini apps must not break the UI.
- "I can create new components of my own" (10-01): asked whether he can.
- Storyboard: "an SDK or a design system" for mini apps; JSON render for widgets; MCP Apps.
- "maybe it's a design system or something" (10-02).
- "we have to update components" (10-03); "How do they come in? Need rules" (10-03).
- "it just fresh it just continuously loads" (10-03): no restarts; heavy things too.
- "this is where we create our own design style" (10-03): the copilot designs with shadcn or its own style.
- "I hope you clarified that components" (10-04): for the backend.

### 2b. What exists
- `src/lib/qmx/catalog.ts`: 11 described components (WidgetFrame, StatTile, DataTable, charts, EntityCard, TickerTape, RunConsole…), essentially unchanged since 10-01. There are 42 Lab and Portfolio panels and 172 Svelte files, so the catalog covers a small fraction.
- `/gallery` page: hand-written previews of those 11 (routes/gallery/+page.svelte), reached from Settings > Developer.
- Layouts are already data: tiling layouts are JSON and are checked on load; unknown panels show a reason instead of crashing (src/lib/workbench/tiles/tiles.ts:200-230). This is the right foundation.
- Panels per surface are a fixed import list (src/lib/lab/catalog.ts), not a registry the copilot or daemon can extend.
- Only 17 shadcn-svelte primitives are installed (src/lib/components/ui). shadcn-svelte-extras Chat, Terminal and Code were promised on 10-01 ("when there's real content") and never added.
- The no-restart answer exists only in a chat reply (10-03 12:22). The six copilot-UI rules are unticked in UI-BACKLOG.md:585-593.
- The 09-23 architecture already specifies the plumbing: json-render (`@json-render/svelte`) with a host-owned catalog, MCP Apps in a sandboxed iframe, the `PackUiRequest` view contract with renderer `native | json-render | mcp-app`, and host-minted ActionContext (`_bmad-output/.../architecture-QMX-UI-2026-09-23/COMPONENT-CONTRACTS.md` §4 and `VIEW-AND-PACK-CONTRACT.md`). That doc itself says these are "specified here and absent in code". The rebuild never picked them up.

### 2c. What is missing (plainly)
1. BACKEND-REQUIREMENTS.md has nothing on components: no panel spec, no catalog registry, no copilot build tool, no draft storage, no hot loading, no add-on components.
2. No renderer: nothing turns a JSON description into a screen, so "the copilot builds UI" cannot be shown or tested.
3. No design-style document for the new look. The 09-23 DESIGN.md is the old neutral seed and predates glass, ink art, themes and liquid glass. Without it, neither the copilot nor Codex can build "in QMX style".
4. The rules (catalog only, size range, smallest-size check, draft then keep or discard, no overflow) are not enforced by any code or written as a contract.
5. No answer on his question "can I create new components of my own": composing from the catalog versus adding new component code.
6. The catalog does not describe the real panels (runs table, sweep grid, pod stack, kill matrix…), so the copilot could only build from 11 simple parts.
7. Terminal conflict: the architecture says terminal is "Preview, not a privileged shell" (AD-21); the ledger plans "a real shell through the daemon"; he wants terminals. This needs his ruling.

### 2d. What to write for Codex (one short contract, about two pages)
1. **Panel spec:** one JSON shape with catalog type, props, data binding (an operation id or stream name, never a URL), size range (minimum width and height), slot (Home, Lab, Portfolio, mini app, chat) and version. Align it with json-render and the `PackUiRequest` views.
2. **Catalog registry:** the UI publishes its catalog (types, prop schema, size class, example, which data shapes each accepts) as versioned JSON. The daemon serves it to the copilot, and the copilot's tools validate against it on the server.
3. **Copilot tools:** `propose_panel`, `propose_layout`, `propose_app`, each returning a draft. The daemon checks the schema, catalog membership, granted data operations and size range. Drafts are stored per user with keep, discard and versions.
4. **Data:** the daemon exposes an operation catalog with output schemas, so a panel knows what it can show and when it is empty, stale or failed.
5. **Live delivery without restart:** layouts, panels and mini apps are data. The daemon pushes "changed" events on the existing socket and the UI redraws in place. Heavy panels load lazily behind a loading state.
6. **New component code:** never evaluated in the main window. Either a sandboxed MCP App (iframe) loaded at run time, or a signed add-on that ships with the next app build. He needs to pick one; I recommend MCP Apps for third-party and copilot-made code.
7. **Storage:** templates, layouts, panels and mini apps are stored by the daemon, so they follow him to the desktop app and other machines.
8. **Design rules the validator checks:** text floor, numbers style, scroll inside panels, truncation rules, minimum size test.
9. **shadcn registry:** at build time, publish a QMX registry (components.json supports a custom registry) so Codex or a developer copilot can add components "in QMX style". This is not a runtime feature.

---

## 3. Backlog gaps

### 3a. Missing from UI-BACKLOG.md entirely (13)
1. Demo copilot cannot receive a message — "I want to see how a message looks" (10-02) — Composer.svelte:313.
2. Diff tab in the copilot work area — "browser terminal and diff to be there" (10-02) — WorkArea.svelte:32-38.
3. One shared session store for side and main copilots — "bring in conversations from other pages" (10-03) — lib/lab/copilot.ts:173 vs lib/copilot/demo.ts:85.
4. json-render actually installed and wired — "for the widgets, I was proposing JSON render" (storyboard 10-01) — not in package.json.
5. MCP Apps renderer — "MCP apps configuration comes into play a lot" (storyboard 10-01) — absent.
6. Per-app settings beside global settings — "each app needs its own" settings (storyboard 10-01) — absent.
7. Per-copilot settings: instructions, tools, skills, permissions — "I should be able to configure, like, the copilot" (10-02) — settings:120-135.
8. Text-size floor as a rule — "the text font is so small" (10-01) — 75 of 134 text pieces under 12px on /copilot.
9. A design-style document for the new look — "this is where we create our own design style" (10-03) — none in apps/qmx-ui.
10. Unify the two widget-board systems (MiniAppShell and TileBoard) — "the components are not consistent" (10-01) — Home vs Lab/Portfolio.
11. Desktop app wrapper as its own pass (needed for the in-app browser, pop-outs, the start-up screen) — "we render it later into a full desktop app" (10-01) — no item.
12. Components contract for Codex (section 2d) — "I hope you clarified that components" (10-04) — not in BACKEND-REQUIREMENTS.md.
13. Terminal ruling (preview stream vs shell) — "we haven't done the terminals" (10-03) — AD-21 conflicts with ledger line 202.

### 3b. Marked done but not really done (11)
1. Skills shown — UI-BACKLOG.md:29 ticked — no skills in code.
2. "One session can act across everything" — UI-BACKLOG.md:28 ticked — scripted only; you can't send.
3. "Reopen any old session from the main copilot" — UI-BACKLOG.md:27 ticked — side sessions are not in the main list; hand-off carries nothing.
4. Ledger "Work area: Browser, Terminal, Preview, stop" — UI-LEDGER.md:199 — browser empty, terminal a `<pre>`, preview hard-coded, stop a toast.
5. "Model choice in Settings, set per copilot" — UI-BACKLOG.md:133 — three generic profiles.
6. "Copilot settings link to Settings (agents and models)" — UI-BACKLOG.md:138 — generic Models tab.
7. "App copilot has multiple sessions with history" — UI-BACKLOG.md:136 — every session is empty.
8. "Pop-out copilot" — UI-BACKLOG.md:134 — an unsynced copy, not a second-monitor view.
9. "Build on shadcn-svelte with a component library page" — UI-BACKLOG.md:335 — 17 primitives; 11-entry catalog; extras never added.
10. "Same widget controls everywhere" — UI-BACKLOG.md:222 — Home's minimise behaves differently from the Lab and Portfolio.
11. The backlog contradicts itself: its lower Copilot section still says New session and Search are disabled and the sub-agent preview is missing (UI-BACKLOG.md:110-112), while the top section ticks the same area done. Nobody reconciled it after the pass.

### 3c. Contradicted by a later ruling, still in code or docs (9)
1. Appearance text "Trading screens never show the background" — ruling "I think keep them" (10-03) — routes/settings/+page.svelte:436-437. Already listed in the backlog and still unfixed after four commits.
2. Settings Trading nodes tab shows "Paper node / Live node" and a "Books" column — "let's call them pods" (10-03) and the node folded into Portfolio — routes/settings/+page.svelte:136-145, 363.
3. Home promotes "EURUSD H1 GBM to paper book FX-P" — "IC markets is meant to be totally out" (10-03) — routes/home/+page.svelte:39-61.
4. Research demo still on the rail — "this research mini app is very useless now" (10-03) — src/lib/workbench/workbench.svelte.ts:33.
5. Lab copilot sample "Sweep the majors on H1 and H4" (FX wording) — spot crypto ruling (10-03) — src/lib/lab/copilot.ts:174.
6. BACKEND-REQUIREMENTS.md still lists Books, Agent requests and Allocate as Portfolio needs, and Authoring as a screen — "agent requests ... irrelevant" and "allocate is out completely" (10-03). Codex reads this file.
7. New-session greeting and cards added — "A new session, the way it begins, I don't like this" (10-02) — HowDoI.svelte; not shown to him for a decision.
8. "Continue here" relabels instead of absorbing — "I can bring in conversations from other pages" (10-03) — routes/copilot/+page.svelte:98-106.
9. Terminal planned as "a real shell" (UI-LEDGER.md:202) vs the architecture's "not a privileged shell" (COMPONENT-CONTRACTS §4) — needs his ruling, not a silent choice.

### 3d. By his priority order (what is still open after Library)
- **Copilot:** see section 1; 15 NOT DONE, 25 PARTLY.
- **Home:** untouched since 10-01 except copy. Still FX and "books", old grid, no own tabs, no notifications, the word "Home" in the header, thin news (UI-BACKLOG.md:150-160). The full rethink he asked for on 10-03 has not started.
- **Settings:** General, Trading nodes and Data & sources are still read-only. No API keys, MCP servers, Claude CLI proxy, exchange accounts or upload. Compute wastes space. The wrong Appearance text is still there.
- **Mini apps:** no new mini apps, no "build a mini app from Portfolio/Lab widgets", no headless run surface, and the Research demo is not retired.
- **Lab:** genetic algorithms, compare presets with "watch", training-run tile, live agents, order flow (filed under Lab but belongs in Portfolio Live).
- **Portfolio:** links back to the Library, MIS later, copilot wiring Lab to Portfolio.
- **Cross-cutting:** start-up screen, animations and loading, screen sizes, day-one with no demo data, monitoring when the laptop is off, live data and a charting mini app, a new-pod journey, multi-screen.

---

## 4. Lost early ideas (2026-10-01 and the storyboard) (12)
1. **JSON render**: named in the storyboard, on 10-01 and on 10-02 ("I told you JSON render ... try leveraging it"). Never installed.
2. **MCP Apps**: storyboard link plus "MCP apps configuration comes into play". Never mentioned again.
3. **Preview pane as an agentic browser** that also previews mini apps, workflows, strategy cards, video and diff (storyboard). Only an empty Browser tab exists.
4. **"Go from preview mode to library"** (the storyboard's blue icon). Save to Library is still a toast.
5. **Expand a widget into a browser-style tab** (storyboard). Left as an "open decision" in BACKEND-REQUIREMENTS.md and never asked.
6. **A mini-app SDK or design system** (storyboard: "an SDK or a design system"). Not written.
7. **Desktop app** ("we render it later into a full desktop app", 10-01). No plan. The in-app browser fails without it (sites refuse iframes), and the start-up screen and pop-outs depend on it too.
8. **T3 Code** ("another platform called T3 Code", 10-01). Never followed up.
9. **Hermes cards as the look for bots and articles** ("those can also be representation of bots", 10-01). Only bot and app covers exist; articles have no cover art.
10. **Omarchy-style web apps** ("he has apps where he can have browsers as apps", 10-01). A comment in src/lib/demo/feeds.ts and a disabled button only.
11. **Reference sites** (xynth, primemarket-terminal, quantx, minara, LSE terminal and its video): Minara was never reviewed and the LSE video was never used. The alphaXiv link 2409.06289 is unused.
12. **shadcn MCP and community components** ("SHAD CN has MCPs", 10-01). The agent replied that no official MCP existed and installed nothing; this was not re-checked when he raised it again on 10-03.

Kept and done from day 1: OpenBB widget controls, FIFA-style cards, the ink and fractal background, themes, the scrollbars, the Artifacts shelf (redesigned in the Library), headless apps shown as "operations", and the Claude Design rail options (superseded by his "keep what we have").

---

## 5. Recommended next order
1. **Clean-up, about an hour, no design:** fix the Appearance text, the Settings nodes tab wording, Home's FX/book copy, the Lab session wording; take the Research demo off the rail; reconcile UI-BACKLOG.md (untick the false items in 3b, merge the two Copilot sections); refresh BACKEND-REQUIREMENTS.md (pods, no agent requests, no Allocate, Lab not Authoring).
2. **Write the components contract for Codex (section 2d) and a one-page QMX design-style sheet** (tokens, type scale with a 13px floor, spacing, panel size classes). Ask him one question: are new components composed from the catalog only, or can new component code arrive as MCP Apps? Codex is nearly done with its refactor, so this is the cheapest moment.
3. **Copilot pass 2, done the way he ruled on 10-02:** research (Codex desktop and Claude desktop), 2-3 layout options, he picks, build, click-through. Scope: the top 10 in 1c, with #1 (it answers) and #2 (it builds a panel through json-render) first. #2 also proves the contract from step 2.
4. **Home full rethink:** move it onto the tiling board (one board system), spot crypto data, own tabs, notifications, a customisable ticker, news with room, previews that link to Portfolio, Lab and Copilot.
5. **Settings** (keys, exchanges, MCP servers, providers including the Claude CLI proxy, real Trading servers, data upload, per-app and per-copilot settings), then **Mini apps** (build from widgets, headless run surface, news and sentiment app, charting app).
6. **Cross-cutting, then the desktop wrapper:** start-up screen, day-one with no demo data, screen sizes, multi-monitor pop-outs, monitoring when the laptop is off.
