# QMX UI ledger: every idea, ruling, complaint and open question

Built 2026-11-10 for the fresh design sessions. It holds everything the operator has said about the UI so far, so nothing is lost. A design session reads this file before it designs a screen, and marks an item **covered** in its own notes once its design answers it.

**How to read a line:** the item in plain words — source — status.
- **decided:** he ruled it, or he accepted a proposal. Design to it.
- **open:** raised but not settled. Bring a proposal or ask him.
- **later:** valid, but not for this release.
- **reversed:** a later message replaced an earlier one. Only the later one is listed, with the earlier one noted.

**Sources (short codes)**
- **S 11-09 hh:mm / S 11-10 hh:mm:** his own messages in this kit's session (`0a7a5e72…jsonl`). Times are UTC; his local time is about three hours later. Quotes are his dictation, transcription noise included.
- **OCT §n:** `kit/refs/october-ui-trace.md`, section n. It holds the October ideas row by row with quotes and verdicts; this ledger does not repeat those rows, it points at them.
- **BL:** `ui-review-repair/apps/qmx-ui/UI-BACKLOG.md` (the 10-03 master backlog with its 10-14 revision).
- **HO §n:** `D:/QMX-worktrees/unit-plan/tracker/qma-v2/UI-HANDOFF.md`. **UN §n:** `…/qma-v2/UI-NOTES.md`. **UU §n:** `…/risk-sizing/build/UI-NOTES-UNITS.md`.
- **G01 to G07:** `ui-review-repair/apps/qmx-ui/plan-2026-11/grounding/0n-*.md`. **WP:** `plan-2026-11/WIRING-PLAN.md`. **HF:** `plan-2026-11/HANDOFF-2026-11-10.md`. **T3 §n:** `plan-2026-11/inspiration/01-t3-code.md`.
- **mem:** a memory note in `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/`.

Vocabulary from his dictation: "shad CN" or "shared CN" = shadcn; "Retico" = Reticle; "neuromorphism" = neumorphism; "test skill / taste code" = taste-skill and its desktop app; "Shepard protocol" = Shepherd; "civilian" = subagent; "teacher record / T3 code" = T3 Code; "Mobin" = Mobbin; "Refer" = refero.design.

---

## Open decisions for him

These need his word. Each has a proposal ready; none blocks the design sessions from starting.

1. **Desktop app, web door, or both.** Rulings 32 and 40 say desktop only, never a web site. On 11-09 he praised T3 Code's token-and-link web access ("I don't need that desktop application… you can have a dual setup", S 11-09 19:32), and the 11-09 roadmap lists "a web version first" after release (mem: release-roadmap-2026-11-09; G06 gap G14).
2. **The Lab: keep, reshape or remove.** He asked "do we need the lab?" (S 11-09 19:12). Proposals: surfaces beside the chat for heavy results (T3 §6), or a research workspace of projects, runs and compares (G02 §4). He rejected the decluttered Lab draft and wants the old project journey kept (S 11-09 18:40).
3. **Workflows: what he meant by "workflows are Claude plugins".** Code and plan say packs and mini apps are plugins and workflows are QMX engine documents (G02 §0, Q1). Also: hand-edit steps or copilot plus forms only (G02 Q2); what "layering workflows" means (S 11-09 18:40); all 55 templates or a starter set (G02 Q4).
4. **Inbox folds into the agent workspace,** as T3's Working/Settled sidebar does (T3 §4; HF). He liked the T3 idea ("I think it might solve it", S 11-09 19:12) but did not rule.
5. **Pods: their own place or under Portfolio** (S 11-09 20:21: "you can literally just decide to add pods as a new… section"). Pods also wait on the unit and risk work.
6. **Phone companion scope:** Today, Inbox, Chats, Nodes; and whether live promotions are allowed from the phone (WP decision 7). He wants it "genuinely different… doesn't have to have everything" (S 11-09 17:51).
7. **Rail places:** Inbox, Workflows and Usage as places, Usage at the foot of the rail (WP decision 6).
8. **Neumorphism:** a whole look, or one soft theme with crisp data (proposal: one theme, S 11-09 assistant reply 20:23). Which current themes to drop.
9. **MCP servers:** stay in Settings or move to Usage with providers ("can also transfer. I don't see an issue with them remaining here", S 11-09 19:12).
10. **One design session or one per area** (map, "Not yet specified").
11. **Retire the old taste-skill and redesign-skill** installs: a deletion, so it needs his go (G07 §6).
12. **Vocabulary he may veto:** "units" for bots and strategies, "pods", "Trading node" vs "Connect a server", "regime" and "volatility state", "Tester" vs "QMB version" (UU §0).

---

## 1. Process and method

- **Redesign first, then code.** The design sessions design; a later session builds, wires and runs QA — S 11-10 12:28 ("let's first start with redesigning… Not just jump into coding") — decided.
- **Sessions, plural:** this session builds the kit; design sessions do the long back-and-forth; a build-and-wire session follows and also runs QA across every user journey ("those like 2 to 3 sessions") — S 11-10 12:28, 12:34 — decided.
- **The October UI is a design proposal, never the product,** and is not a base to keep — S 11-10 12:28 ("it was never one"); mem: ui-is-design-not-code — decided.
- **Design sessions may look at the old UI but it is "not paramount".** Trace its ideas to the transcript and storyboard instead (done: OCT) — S 11-10 12:41 — decided.
- **Judge the UI by running and clicking it, never by reading its code** — S 11-09 18:40 ("don't look at the code. Look at the design"); mem: ui-is-design-not-code — decided.
- **Design in real UI code with shadcn-svelte,** demo data on, one screen at a time — S 11-09 18:40; mem: ui-design-in-code-not-canvas — decided.
- **Claude Design canvas rejected:** "beyond poor… ugly", "feverish" Claude orange, no structure, uneven fonts, poor icons, wasted space, big buttons, no components. This overrides his earlier praise of the canvas concepts' looks — S 11-09 18:40 — decided (the concepts he liked still stand).
- **Inspiration first,** then layouts; no vibing — S 11-09 19:18 ("anchor one thing at a go… we find inspiration… then we figure out the layouts") — decided.
- **Inspiration sources:** refero.design (signed in, he will not pay; its chat agent can search for you, S 11-09 18:47 nudge), Pinterest, X (his account is signed in), Mobbin (good, but he will not pay), Dribbble ("not a good one"), GitHub UI skills — S 11-09 18:40, 20:21, 20:28 — decided (ticket 07 lists them).
- **Surprise me, own spin:** take a reference, enhance it, never copy; creative control to the design session, while he still gives opinions — S 11-09 19:12, 20:21, 20:33; S 11-10 12:34 — decided. Earlier "not borrowing from anyone" (OCT §9) still holds: references give mechanics and ideas, not look.
- **Variants he can toggle,** like themes, not single versions — S 11-09 20:28 ("Same UI… versions and variants") — decided (Emil `prototype`, installed as `variant-picker`).
- **Intentional layout:** layout and user journeys are "intention"; design for QMX's fundamentals: extensible day to day, data-intensive, update-intensive, quick to respond, easy on the eye — S 11-09 17:51, 19:18 — decided.
- **Preview first, detail one level down** ("they lack depth") on every screen — S 11-09 19:12; UU intro ("we have a preview and a detailed view. So, design for both") — decided.
- **Few words, icons, real controls, a tooltip on every icon button** — S 11-09 18:40, 19:12 ("this download thing is for what? It has no tooltip") — decided.
- **Design for complexity and for non-technical users** ("this UI is meant to be used by people who are not technical") — S 11-09 20:21 — decided.
- **Use skills, don't just read them:** a skill carries hooks, scripts and schemas — S 11-09 20:33 — decided.
- **Vet skills before installing; never install everything** ("you are going to install garbage") — S 11-09 20:36 — decided.
- **Skills chosen:** Emil's index approved; six installed (`variant-picker`, `emil-design-eng`, `break-ui`, `review-animations`, `remove-animations`, `apple-design`); Reticle not needed; taste-skill not used; poteto-mode mapped to the coding session — S 11-10 12:34, 12:41; map — decided.
- **Fable 5.1 (not 5.2) as UI judge and second opinion,** used sparingly — S 11-09 20:21, 20:33. Then: "I might actually use Fable, but you don't need to add that in the system prompt" — S 11-10 12:34 — decided: the design brief does not mandate Fable; he adds it himself.
- **Stageshow's screenshot-judge loop** (a fresh reviewer judges screenshots only) is the useful part of the videos; the videos add little, one is about taste-skill — S 11-10 12:42; `kit/refs/videos.md` — decided.
- **CIS user journeys** may be run through a subagent; journeys exist in the plans and the release inventory, and "we actually intend to produce way more" — S 11-09 17:51, 20:21; S 11-10 12:34 — open (ticket 06).
- **Plans on other branches and their CIS scenarios are hints for the UI** (QMA v2, unit system, methodology) — S 11-09 20:21 — decided (feeds the screens list).
- **Agents one at a time, on Opus,** so each result shapes the next brief; no budget panic on his ultra plan — S 11-09 20:21, 20:28 — decided.
- **Talk it through, don't run off one dictated prompt;** no overnight unattended design run — S 11-09 20:36, 20:39 — decided.
- **A dedicated UI branch** (`ui-redesign`) — S 11-10 12:41 — decided.
- **A fresh agent double-checks the kit against this whole transcript at the end** — S 11-10 12:41 — decided (final ticket).
- **Track compaction; keep the plan on disk** — S 11-09 20:21 — decided.
- **Install comes after the UI;** "fresh start and install handover… don't come yet" — S 11-09 17:51; S 11-10 12:28 — decided.
- **Goal: a working, released QMX soon** ("a working version tomorrow"), stated as a wish, not an order to cut work — S 11-09 20:21; S 11-10 12:28 — decided.
- **Judge layouts at full screen (1920 to 2560); bigger rem text; no cramming and no empty space** — OCT §3, §10; BL 10-04 rulings — decided.
- **DESIGN-RULES from October** (word budget, every block is data or an action, tables for rows and cards for owned things, no tabs inside tabs, panel sizes) — G04 "What this means" — decided.

## 2. Look and themes

- **True black theme, like T3 Code** ("cool actual black… we don't have any sort of black… Graphite is just grayish") — S 11-09 20:21 — decided.
- **Take the "cloudish" look out of Ink,** the default theme — S 11-09 20:21 — decided.
- **Neumorphism** wanted ("I think neuromorphism is the one I wanted… is it hard to pull it off?"); he pasted a Pinterest image — S 11-09 19:12, 20:21 — open (whole look or one theme; see Open decisions 8).
- **Enhance the themes; remove some** — S 11-09 20:21, 20:28 — open (which ones).
- **Chart and bar colours must follow the theme** — S 11-09 19:12 — decided.
- **Liquid glass and solid surface styles exist;** brutalist and others he will "never use" — S 11-09 20:21; OCT §9 — decided (drop unused styles).
- **His own ink art, editable themes, solid panels under data** — OCT §9 — decided (carry forward).
- **Background art "not just lines"; a wallpaper generator that rotates** — OCT §9; BL — later.
- **Personality and purposeful motion** (start-up "world fills slowly"; few animations) — OCT §9, §10; BL — open.
- **Icons with character; a Library identity** — OCT §4; BL — open.
- **Ugly when cluttered, ugly when too spacious** ("Some doesn't make sense, some is too spacious") — S 11-09 19:12 — decided (constant complaint).
- **Fonts: the canvas's uneven type was rejected;** bigger rem text stands — S 11-09 18:40; OCT §3 — decided.
- **Paper and live shown on tile borders only** — OCT §1 — decided.
- **Colour codes and border colours carry meaning, explained by tooltips** — S 11-09 19:12 — decided.

## 3. Shell and navigation

- **Bloomberg-like layout exists for extensibility;** any other software with that kind of extensibility may be borrowed from — S 11-09 20:21 — decided.
- **"Deep modules, but for UI":** minimal on the surface with depth underneath, like T3 Code — S 11-09 19:12 — decided.
- **One tiling board and one widget frame everywhere** — OCT §1 carry-forward 1 — decided (strongest October idea).
- **Floating context card at top right** (machine, open in editor, add project, branch) "something we can really, really leverage", with our own spin — S 11-09 20:21; T3 §1 — open (design it).
- **Opened mini apps on the rail below a divider** — OCT §1 — open (never built).
- **Widget history (time travel); expand a widget into a detail tab** — OCT §1 — open (never built).
- **Status bar with machines and jobs** — OCT §1 — decided.
- **Pop out any screen, kept in sync, several monitors** — OCT §1; HO §10 row 11 — open.
- **Snapshots** (capture a window into a chat draft) are "an interesting addition to QMX" — S 11-09 19:12, 19:32; T3 §11 — open.
- **Source control, projects, worktrees, environments, pull requests: what do they map to in QMX?** — S 11-09 19:32 ("what do we have in QMX that mimics source control?") — open.
- **Scope lines for inheritance** ("Applying settings for [All areas] on [this machine]") wherever a setting inherits — T3 §7; HF — open (proposal).
- **Simple mode and Advanced mode; Quick Entry hotkey; HUD over any window** — HO §10 rows 12, §11 rows 3, 14, 16 — later.
- **Start screen choice; fit at 1280, 1600, 1920** — OCT §10 — decided.

## 4. Agent workspace, copilot and Inbox

- **One dedicated agent section, grouped like projects** (as Claude Code and T3 Code group sessions), replacing the per-area copilots (Lab, Portfolio and the rest); agents live in their own place ("I don't have to see the file explorer in here") — S 11-09 19:12 — decided as direction; shape open.
- **The copilot gets a full overhaul;** today's copilot demo is "ugly as hell"; aim for "far better" than a Claude Code copy — S 11-09 17:51, 19:12 — decided.
- **Agents are getting an upgrade; design for it** — S 11-09 18:40 ("agents are also going to get an overhaul") — decided.
- **See sub-agents running:** tools, files, browser use, computer use, file changes; file changes land in the Library — S 11-09 20:21; UN §5; OCT §3 — decided.
- **Watch how T3 Code's agent spawns and shows sub-agents** before designing — S 11-09 20:33 — open (ticket 03).
- **Hover a session to see its area, place, model and what it produced** — S 11-09 19:12; T3 §4 — decided.
- **Inbox must be agentic:** both canvas Inbox options rejected ("I don't like either"); every item shows where it leads (a mini app, a copilot session, an agent in a mini app) and has quick actions. Inbox B was "something I can work with"; a mix of A and B was floated. The October bell and "Needs you" panel are reversed by this — S 11-09 18:40 — decided (agentic); layout open.
- **The pinned tabs ("needs you", "urgent", "waiting on reset") were "a good touch"** — S 11-09 18:40 — decided (keep the idea).
- **Inbox likely folds into the agent workspace** (T3's needs-you / Working / Settled bands) — S 11-09 19:12; T3 §4 — open (Open decisions 4).
- **Notification design belongs to the UI;** the engine emits only provider failures, harness errors and rare irreversible steps — HO §8, §9 row 9 — decided.
- **Approvals inline under the command; permission modes as one row** (read-only, ask, auto, full) — T3 §3; HO §1 item 4 — open (proposal).
- **Model picker in the chat** ("obviously") — S 11-09 18:40 — decided.
- **Chat that feels like Claude Code:** effort control, compaction and "compact now", stop and steer, model switch with a cost warning, export per session — UN §3, §8; HO §1 item 6 — decided.
- **Session home badge** (where a chat was born) — HO §1 item 2; UN §10 — decided.
- **Preview pane / surfaces: browser, terminal, diff, files, side chat** — OCT §3; T3 §6 — decided (real terminal and browser still never built).
- **Agent browser and scheduled tasks** ("we haven't done it yet") — S 11-09 19:18 — open.
- **One session crosses Lab, Portfolio and apps, and can run for days** — OCT §3 — decided.
- **No Ask / Plan / Do modes; skills instead** — OCT §3; BL R2 — decided.
- **No new-session greeting; no agent-requests tab** — OCT §3 — decided.
- **Hermes and rerun patterns for the chat** (live work dock, queued messages, context meter, failure cards naming the layer, widgets inside messages, explainer previews, loop and goal cards, "what it saw", @ references, attach anything) — HO §10, §11, §12, §15 — open (design sessions pick what earns a place).
- **Claude Agent SDK gives data and controls, no screens;** QMX drops some (thinking after reload, cost per turn, context meter, sub-agent tokens, approval wording, fork) — S 11-09 17:51, 20:21 asked; G03 — decided (answered); dropped fields go to backend asks.
- **Orchestrator (Shepherd) with Hindsight memory, self-improving;** it handles workflow and mini-app tasks; cater for it in the UI even if not yet built — S 11-09 20:21 — decided (cater); design open.
- **T3 Code's "Orchestrator V2" is a reference** (Theo shipped it) — S 11-09 20:28 — open (ticket 03).
- **Memory view** (what each memory is about, Forget) — HO §15 row 4 — open.
- **Copilot builds panels, widgets, mini apps and workflows under rules** (catalog only, size range, draft to keep or discard) — OCT §3; BL "Copilot pass rules" — decided.

## 5. Usage and providers

- **Usage option A chosen,** with less text and more showing — S 11-09 18:40 — decided. A first cut was coded on `ui-review/repair` (uncommitted, 11-09); his verdict "not bad", then Usage v2 below.
- **Minimal like T3 Code's usage page:** one big number, a chart, Cost / Tokens / Limits switch — S 11-09 19:12 — decided.
- **Refresh buttons for API keys and usage** — S 11-09 18:40 — decided.
- **Model routing moves from Settings into Usage:** who uses which provider (workflows on DeepSeek, copilot on Claude by default, changeable) — S 11-09 18:40 — decided.
- **"Models and tools" leaves Settings for Usage;** brokers and accounts stay in Settings — S 11-09 19:12 — decided.
- **Add a provider / connect an account journey, and proof that the copilot picks it up** — S 11-09 19:12 ("how do I make sure… it updates, you know, the copilot") — decided; T3 §8's three steps are a reference.
- **Inheritance in routing** (defaults per group, overrides shown) — S 11-09 19:12 — decided.
- **An organisation structure for "who uses what"** instead of one crowded table — S 11-09 19:12 ("I'm requesting you propose an organization structure") — open.
- **Analytics: preview first, detail one level down,** not all cluttered together — S 11-09 19:12 — decided.
- **Usage needs backend connection** — S 11-09 19:12 — decided (see §15).
- **No QMX caps, shares or spend asks;** providers' own readings only; "estimates, not your bill" — HO §9 row 15, §12 rows 5, 6, 23; UN §6 — decided.
- **Any number of accounts; Accounts page with routing strategy per account** — HO §12 row 5 — decided.
- **Defaults read key-first** (Kimi, Qwen, DeepSeek and others before Claude) — HO §12 row 24 — decided (ruling 107).

## 6. Settings and machines

- **Declutter Settings;** it "has a lot to change" — S 11-09 18:40, 20:21 — decided.
- **Settings as a sheet with search and grouped sections** (T3 style) — T3 §7; HF — open (proposal).
- **The storyboard's Factory-style settings page (the "orange box")** was never used in October; use it now — OCT §8 — open.
- **Global settings plus per-app settings** — OCT §8 — open (never built).
- **Add a machine with one simple click,** like T3 Code; control several machines and servers — S 11-09 19:32, 20:21 — decided.
- **One-click deploy and server sign-in;** no scripts or terminals — mem: ui-notes-held-for-ui-session — decided.
- **Sharing and access: token plus link, use QMX from anywhere** — S 11-09 19:32; T3 §10 — open (tied to Open decisions 1).
- **Components and Developer sections are still needed** — S 11-09 20:21 — decided.
- **Machines list with capacity, health, version, place names** (This PC plus names he gives) — HO §9 row 1, §14 row 7, §15 row 12, §20 — decided (backend facts).
- **Connections and broker accounts,** demo or live on every money figure — HO §17 row 8, §23 — decided.
- **Rules page** (always allow, never allow, the guard's floor read-only) — HO §12 row 9, §14 row 3 — decided.
- **Unit-system settings** (clocks, keys, alarms and the wake list, units, QMB, records) — UU §16 — decided (as intent).
- **Backups wait for the "sync to my account" design** — HO §24 — later.
- **Deep logs setting** (off, this PC, a server) — HO §25 — open (no screen yet).
- **Persona box for the copilots' tone** — HO §10 row 15 — open.

## 7. Workflows

- **Workflows option B, the day-at-a-glance dashboard, "loved"; A is just OK; C "too generic"** — S 11-09 18:40 — decided.
- **Count badges per workflow** (a red dot with 12) — S 11-09 18:40 — decided.
- **Colour-coded steps that need him** — S 11-09 18:40 — decided.
- **A page for creating a workflow with the copilot** — S 11-09 18:40 — decided.
- **"Layering" workflows,** and with it the Lab's own layering — S 11-09 18:40 — open (meaning unclear; ask).
- **How a workflow inside a mini app shows** — S 11-09 18:40 — open.
- **Two kinds of workflows (agentic and not) and their permutations make things complex;** that is why the Lab existed — S 11-09 18:40, 17:51. Code fact: one format, three shapes (script, mixed, agent step) — G02 — open (Open decisions 3).
- **"Workflows are technically now Claude plugins"** — S 11-09 17:51. Code says packs and mini apps are plugins; workflows are engine documents — G02 §0 — open (Open decisions 3).
- **Graphs and loops over an n8n-style editor** — OCT §5; UN §10 — open (whether to hand-edit at all).
- **Shipped macro and micro analysis workflows and mini apps:** cater for them — S 11-09 20:21 — decided.
- **Triggers like T3's scheduled tasks** (runs on, schedule switch, enabled) — T3 §9 — open (proposal).
- **Run timeline, "why didn't it fire?", incidents, placement badge, draft vs published, self-improvement badge** — HO §3, §9, §10 — decided (backend facts).
- **Cron and monitoring belong to workflows** — OCT §7; BL R6 — decided.
- **Unit workflows:** inputs from stored readings and journals, session and trade-count triggers, slow-lane templates — UU §14 — decided (intent; some triggers later).

## 8. Lab, pods and Portfolio

- **Do we need the Lab?** Asked seriously; its likely new role is "a representation of complex artifacts" (backtest reports, experiments); removing it means decoupling templates, workflows and apps in the backend — S 11-09 19:12 — open (Open decisions 2).
- **The decluttered Lab draft is "absurdly poorly" done;** keep the old Lab's project journey (the "start something new" walk, the BTC breakout drop-down) — S 11-09 18:40, 19:12 — decided.
- **Declutter the Lab; it "has a lot"** — S 11-09 17:51 — decided (how is open).
- **Strategies are now units** — S 11-09 19:12 — decided.
- **Pods: what are pods and labs? Pods may become their own place;** they sit under Portfolio today — S 11-09 20:21 — open (Open decisions 5).
- **Portfolio is too clustered; risk and sizing are being coded, so it changes a lot.** Then he softened it: "it doesn't look so weird… the Fable agent actually pulled it off… only looks weird because there is so much information" — S 11-09 19:12, then 20:21 — reversed to: rework later, keep what works.
- **October Lab and Portfolio keepers:** scenario generator, Resources tile, machine switching, pods with live and paper sides, road to live, kill switch always in view — OCT §5, §6 — decided (carry forward where the backend supports them).
- **Lab backend facts:** projects as Library collections, four "New…" levels, procedures as workflow templates, no Lab HTTP routes yet — G02 §4; G01 §3 — decided (facts).
- **Charting provider; order-flow charts** — OCT §6; BL R7 — later.
- **MIS gets its own views** (readings, defaults, shadow models) — OCT §6; UU §13 — open.

## 9. Library

- **The Library is good and stays,** "like a File Explorer"; maybe a new touch — S 11-09 19:12 — decided.
- **October Library keepers:** player cards, where-used map, preview to full page, templates, journals inside items, reading mode — OCT §4 — decided.
- **A card and a full page for every kind,** schema-driven — HO §4, §17 row 1 — decided.
- **Library identity and personality** — OCT §4 — open.
- **Archive, never delete; History and Blame; sessions as Library items** — HO §4, §14 row 9, §17 row 9 — decided.
- **File changes from agents show in the Library** — S 11-09 20:21 — decided.
- **Attach from the Library on click; @ references** — HO §18 — decided (backend route missing).
- **Feeds, data shelf, data health** — HO §17 rows 2, 4, 5 — open (screens not designed).

## 10. Apps and mini apps

- **The Apps section will change;** "I don't know what was meant to be in the apps section" — S 11-09 19:12 — open.
- **Mini apps are Claude plugins** (skills, helpers, slash commands join the copilot) — HO §6, §14 row 5; G02 — decided.
- **No per-app copilot; one copilot loads an app's pack** — HO §6; G02 §4 — decided.
- **Archive, never delete** — HO §6 — decided.
- **App cards: actions, feeds from and to, freshness, setups, incidents** — HO §15 row 11 — decided (backend facts).
- **First-party apps (QMB, trading node, MIS) need their own screens** — UU §9, §10; WP step 5 row 8 — decided (intent).
- **DevOps layer for mini apps** — S 11-09 20:21 — decided (cater).
- **Build a mini app from widgets; headless apps' run surface** — OCT §7 — open.

## 11. Units, QMB, trading node, MIS

- **Unit page: wasted space, too many words "that mean nothing", no icons; "beyond poor"** — S 11-09 18:40 — decided (complaint to fix).
- **Trading node page: "I feel like vomiting"; buttons too big, poor fonts, two buttons in total, too much text** — S 11-09 18:40 — decided (complaint to fix).
- **The full unit-screen intent** (words on screens, unit card and page tabs, publish and promotion cards, deploy dialog, journal, judge and proposal cards, dictionary pages, QMB runs, node list and node page tabs, world clock, stop and alarm cards, MIS tab) — UU §0 to §17 — decided (as intent; the design session decides the look).
- **The journal "is very important"** and is the unit's DevOps layer — UU §6 — decided.
- **No separate risk screens yet;** risk and sizing get their own session — UU §18 — decided.
- **Trading node October ideas** (server facts, test latency, restart, drain) — OCT §6 — decided (carry forward).

## 12. Home

- **Home: "we shall see"** — S 11-09 19:12 — open.
- **October Home ideas:** your own tabs, editable ticker, news with room, "while you were away" with many jobs, templates on Home — OCT §2; BL — open (most unreviewed).
- **Unit additions:** getting-started panel, morning card, nodes strip — UU §1, §2 — decided (intent).

## 13. Onboarding and first start

- **First start belongs in the UI,** not a terminal script; it remembers answers, skips done steps, masks secrets with asterisks, shows the broker's own account numbers to pick from, and starts the host itself — mem: installer-lessons-first-start-2026-11-09, ui-notes-held-for-ui-session — decided; designed after the main screens.
- **The first-start card, handover and exit codes are built in the backend** — HO §19; G06 §2 — decided (facts).
- **Getting-started list from facts** — UU §1; G06 G12 — open (no backend).
- **Start-up like Photoshop or PyCharm** — OCT §10 — open.
- **The UI does a lot for installation; we will talk it through** — S 11-09 17:51 — later.

## 14. Mobile

- **A phone version should be genuinely different and not have everything** — S 11-09 17:51 — decided.
- **Companion proposal: Today, Inbox, Chats, Nodes** — WP decision 7 — open (Open decisions 6).
- **Phone approvals, voice mode** — UN §10; HO §10 row 17 — later.
- **The roadmap puts the phone after a web version** — mem: release-roadmap-2026-11-09 — later.

## 15. Backend and wiring asks

- **Wire the backend to the UI;** the backend on `engine/base` has moved a lot (about 118 PRs) and most code is ready for the UI — S 11-09 17:51, 20:21 — decided (build-and-wire session).
- **"Maybe you don't wire. First build or propose"** — S 11-09 20:21 — decided: design first, wiring in a later session.
- **A desktop shell must hand the UI the keyring bearer;** streams over `fetch` — G01 §3 gap 1; WP step 1 — open (shell choice is Open decisions 1).
- **Ranked backend asks:** push topics, mount the Lab routes, broker reads over REST, domain reads (backtests, journal, unit checks, readings, heartbeats, provider Test), chat `home` and attach routes, run-list placement, Library filters and archive, app UI folders, getting-started state, SDK pass-through — WP step 5; G01 §3 — open (backend program).
- **Gaps checked at `3ae41ffc`:** several October gaps now exist (cTrader key route, read-only health flag, backup incidents in inbox); others remain — G01 §3 table — decided (facts).
- **Demo mode stays as a switch; unwired places say "Not connected"** — WP step 2; HO §0 — decided.
- **UI must follow the backend;** the UI never guesses missing APIs — mem: ui-notes-held-for-ui-session, qmx-ui-rebuild — decided.
- **DevOps layer of the whole app, mini apps, workflows and agents** — S 11-09 20:21 — decided (cater).
- **QA of the real app across user journeys at the end** — S 11-09 20:21; S 11-10 12:28 — decided (build-and-wire session).
- **The `apps/qmx-ui` folder on engine/base is a stale September stub** — WP; G01 §4 — decided (fact).

## 16. Out of scope or later

- **Installer and desktop shell work** — S 11-10 12:28; map — later.
- **Methodology session** gives the copilot and him structure (brainstorming, building a mini app, building a workflow); the UI must have room for its scenarios — S 11-09 20:21 — later (cater for it).
- **Code-quality, docs and watch-week sessions** — mem: release-roadmap-2026-11-09 — later.
- **Taste Code desktop app:** he tried it, "I don't think I'm going to use it… really has nothing much"; stay on Claude Code — S 11-09 20:28 — decided (not used).
- **Open-sourcing QMX** — BL 10-04 item 6 — later (not UI).
- **Learn from papers as diagrams or video** — OCT §4 — later.
- **Agents on their own machines; live agent streams in the Lab** — OCT §5 — later.
- **Computer use on cTrader, MT5, TradingView demo** — UN §9 — later.

## Added after the double check (2026-11-10)

- He may move the frame from aesthetics to design standards: "we might change from aesthetics to design standards" (11-10). Status: open.
- A reusable component library, needed because QMX is extensible: "you also have a component library because of the fact that QMX is extensible" (11-09). Status: open.
- The feed format for Workflows: "When you put it in feed format, this is interesting" (11-09). Status: open.
- His "ugly" ruling covers every 11-09 canvas draft, including the ones he praised. Usage A and Workflows B are liked **concepts**; their visuals are rejected. Status: decided.
- T3 Code: liked for being easy on the eye, but "we might actually not use it. There are issues." (11-10). Status: open.
- The unfinished T3 Code tour (every page, the sub-agent test) is left to the design sessions if they want it. Status: later.
- Dribbble counts as an inspiration source (11-09). Status: decided.
