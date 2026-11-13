# 09 Extensible UI: patterns, not products

Research only, 2026-11-10. This file starts from what QMX's UI must make possible. It then lists the known ways to structure an interface that can grow, and uses products only as evidence. No design is recommended here. "(not verified)" marks claims I could not check in a primary source. Sources are in section 7.

---

## 0. What the UI must make possible (from the QMX files)

**Jobs** (grounding 08 §5, the 15 journeys), grouped by the kind of work:
- **Start and set up**: first start (1), start a node and sign in (6), add a provider (15), download data (14).
- **Ask the copilot to make something, then judge it**: idea to judged unit (2), unit with live checks (3), workflow from one sentence (10), "why didn't it trade" (8).
- **Decide on a gated action**: promote to paper (5), deploy or withdraw (7), resume, back to paper or retire after a risk stop (9), publish and enable a workflow (10).
- **Triage what needs him**: morning proposals (4), fix a failed run from the inbox (11), a risk alarm (9).
- **Watch things run**: nodes and units trading (9), runs (11), the copilot and its helpers (12), usage readings (15).
- **Add capability**: install a mini app and use it (13).

**His tests** (INTENT.md):
- Lego: defaults everywhere, and every screen answers "add this, remove that, edit this?".
- One component set, because the copilot builds with it. New things fit in without errors.
- A summary expands into a detail view. Every item can be sent to the copilot and linked to its Library item.
- Space management: many things open at once. Size sets priority (DESIGN-LOG round 1).
- More to click than to read.
- Fresh out of the box with no demo data.
- Everything shown has a real backend source.
- The copilot "should be able to control anything".

**What changes at runtime and must not be hard-coded** (grounding 08 §6):
- mini apps, their operations and their screens;
- Library kinds and card fields;
- step kinds, trigger kinds and templates;
- providers, models and accounts;
- places;
- connect-dialog kinds and their `needs` cards;
- settings sections;
- tool sets and skills;
- inbox actions;
- the count of anything.

**Backend facts that limit the choice:**
- There is no widget, layout or dashboard object in backend code (checked by search at `3ae41ffc`).
- Two traces show widgets were intended but never built:
  - the backtester's stream strips UI fields named `ui_widget` and `ui_view`;
  - the `ma-mini-app-lifecycle` template plans a "render check" of "each widget" of a mini app "fitting its slot".
- Mini-app screens are sandboxed HTML served as MCP `ui://` resources.
- The three first-party apps (backtester, market intelligence, trading node) are headless: they have operations but no screens.
- Chat has 14 fixed block kinds. Library kinds have schemas. Inbox items carry a closed set of actions. Connect jobs return generic `needs` cards.

So the question splits into three:
- **A.** What is the main organising principle?
- **B.** Which layout patterns carry it?
- **C.** How does UI that QMX did not draw (mini apps, agent-made views) get in and stay consistent?

---

## 1. A. Organising principles

**Task-oriented.** Screens follow the steps of a job: "build a unit", "deploy", "set up a node".
- Source: the task-analysis tradition. NN/g's wizard guidance (section 2, item 6) is its narrow form.
- Good for rare or risky jobs and for novices.
- Bad when there are many jobs. Every new job needs new screens, and things made in one job are hard to find from another.

**Object-oriented** (object first, action second).
- The user picks a thing (a unit, a node, a run), then sees only the actions that apply to it.
- Sources:
  - IBM Common User Access (CUA, from 1987). It is described as "select an object, then an action", which avoids action modes. I read secondary sources only.
  - Object-Oriented UX (OOUX, Sophia Prater): "objects first, actions second". Its ORCA method maps Objects, Relationships, Calls to action and Attributes.
- Good for growth. A new kind needs a schema and its actions, not a new journey. It matches "every item links to its Library item".
- Bad for guided first-time jobs, and for jobs that cut across many objects.

**Conversation-oriented.** The user states intent in words. The system does the steps and shows results as it goes.
- Sources: the MCP Apps overview, and the OpenAI Apps SDK UX principles. The second says to add UI only "when visual interaction materially improves part of the workflow".
- Good for a non-technical user with many possible jobs. Fits "the copilot should control anything".
- Bad for watching, scanning and comparing. Results are hard to find again unless they become objects.

**Monitoring-oriented.** Screens are built around what is happening now.
- Source: Shneiderman's information-seeking mantra (1996): "overview first, zoom and filter, then details on demand".
- Good for the watch jobs; weak for everything else.

These four do not exclude each other. Products pick one as the spine and use the others in bounded places (section 6).

## 2. B. Layout and navigation patterns

The pattern names follow common catalogues, mainly Jenifer Tidwell's *Designing Interfaces* (O'Reilly, 3rd ed. 2020; not re-read this pass). Primary sources are cited per pattern.

1. **Hub and spoke.**
   - A home lists destinations. Each spoke is a self-contained place.
   - It grows by adding spokes, so every new app becomes another destination.
   - Weak when a job crosses spokes.
2. **Sidebar plus list plus detail** (master-detail, split view).
   - Apple's guidance uses sidebar, content and detail columns. It says sidebars suit long, often user-generated lists and are poor for deep nesting.
   - It grows by adding sidebar entries. It suits object-oriented apps: each kind is a list and each item a detail.
3. **Workspace: a fixed frame with panes and slots.**
   - The frame is a rail, sidebars, a main area, a bottom panel and a status bar. Extensions fill named slots (section 3).
   - Users move panes within limits; they do not change the frame.
4. **Canvas or board.**
   - A grid or free surface the user arranges. Overview and space management are its strengths.
   - Grafana's best practices warn against "dashboard sprawl". They say a dashboard "should tell a story or answer a question" and recommend drill-down to detail.
5. **Document of blocks.**
   - A page is a stack of blocks plus live views of records (table, board, calendar, chart), as in Notion.
   - Good for reading in depth.
   - Known weakness: the blank page. Reviews call Notion overwhelming to set up; Notion answers with templates. (Reviews and blogs, not official data.)
6. **Wizard** (staged disclosure).
   - NN/g: use it for novices, rare processes and branching set-ups.
   - Avoid it for jobs that repeat often, steps that can come in any order, or work that needs comparing across steps.
   - Show the steps, allow save and resume, and keep each step self-sufficient.
7. **Feed or inbox.**
   - A time-ordered list of typed cards with fixed actions.
   - Good for triage, poor for seeing state.
8. **Command-driven.**
   - A palette reaches every action by name, and a new command needs no screen.
   - Poor for discovery by novices unless paired with visible structure.

**Cross-cutting: progressive disclosure** (Jakob Nielsen, NN/g, 2006).
- Show the few important options first; put advanced ones on a secondary screen.
- More than two levels usually hurts usability.
- His "a summary expands into the detail" is this rule. It works in any layout, not only on boards.

## 3. C. How outside UI gets in and stays consistent

This is what makes a UI extensible. Five mechanisms exist. They differ in who draws the pixels.

1. **Slots (contribution points).** The host defines named places, and an extension declares what it fills. The host draws the chrome around each slot.
   - VS Code: view containers, views, commands, menus, status bar items, custom editors and webviews, declared in `package.json`.
   - JetBrains: a tool window declared in `plugin.xml` with an id, an icon and an anchor (left, right or bottom).
   - Obsidian: a registered view type opened in a pane or sidebar, plus ribbon icons and commands.
2. **Declarative component set.** The extension returns a description and the host renders it, so the extension cannot look foreign.
   - Raycast: views are only List, Grid, Detail and Form, each with an Action Panel. Raycast calls this "a design system".
   - Slack: Block Kit builds most surfaces.
   - Coda: "Packs don't ship their own UI".
   - Atlassian Forge UI Kit: Atlassian components only, with no DOM access and no arbitrary HTML.
   - Shopify admin UI extensions: web components that "automatically match the Shopify admin's look and feel".
3. **Sandboxed custom UI with shared tokens.** The extension ships HTML in an iframe, and the host passes theme tokens and a bridge.
   - Atlassian Forge Custom UI: an iframe with a content security policy and a bridge. Its look comes from following the Atlassian Design System.
   - Shopify App Home: an iframe page.
   - VS Code webviews: called a last resort, "only when absolutely necessary", not for wizards, and required to use the theme colour tokens.
   - **MCP Apps, which QMX already uses.**
     - The host sends `hostContext` with `theme`, `styles.variables` (CSS custom properties such as `--color-background-primary`) and fonts. It resends them when they change.
     - `displayMode` and `availableDisplayModes` let a view ask to be inline, fullscreen or picture-in-picture.
   - ChatGPT's Apps SDK adds published rules on top:
     - system fonts and colours;
     - no nested scrolling;
     - at most two actions on an inline card.
4. **User-assembled pages from a palette** (a pattern not in the earlier list).
   - Salesforce Lightning App Builder: a no-code admin drags components into the regions of a page template.
   - Page types are app, home and record (object) pages.
   - Components come from Salesforce, from the customer, or from third parties.
   - This is the board idea applied to an object's own page instead of a free canvas.
5. **Actions and blocks attached to objects** (also not in the earlier list).
   - Shopify action extensions: modals launched from a resource page's "More actions".
   - Shopify block extensions: cards on Product, Customer or Order pages, which merchants add and pin.
   - Linear: agents can be @mentioned or delegated an issue, and their activity shows on it.
   - The extension point is the object, not the screen.

**The trade-off, in every case:**
- Declarative sets keep consistency and are safe for agent-made UI. They cannot do what the set did not foresee, such as rich charts or dense live views.
- Sandboxed HTML can do anything. Consistency then rests on tokens, rules and review.
- Mature platforms offer both and steer authors to the declarative path first: Forge UI Kit before Custom UI, VS Code tree views before webviews, Shopify extensions before App Home.

---

## 4. The models, assembled

Combining A, B and C gives six recognisable models. Products are evidence only.

| Model | Spine (A) | Layout (B) | Extension unit (C) | User arranges | Evidence |
|---|---|---|---|---|---|
| **M1 Board of tiles** | monitoring | canvas or board | tile type plus data endpoint; HTML or iframe tiles as an escape hatch | everything on the board | OpenBB Workspace (`widgets.json`, `templates.json`, `apps.json`), Grafana, Home Assistant (auto-generated default board) |
| **M2 Workspace with slots** | task or object | fixed frame with panes | slots: view, command, status item, editor, page | pane placement within limits | VS Code, JetBrains, Obsidian, Grafana app plugins |
| **M3 Object pages** | object | sidebar, list, detail; record pages | actions and blocks attached to an object kind; optionally a page builder | page regions (Salesforce); pinned blocks (Shopify) | Salesforce record pages, Shopify blocks and actions, Linear issues |
| **M4 Documents of blocks** | object records, shown as text | document | block types, view types, data syncs | blocks and views on any page | Notion, Coda |
| **M5 Commands and host-drawn surfaces** | task | command-driven, plus modals and forms | a command that returns a declarative view | little: commands and hotkeys | Raycast, Slack Block Kit, Forge UI Kit |
| **M6 Conversation with opened views** | conversation | chat plus a side, inline or fullscreen view; feed cards in the thread | a tool with a `ui://` view, an artefact, a skill | little: he asks, pins and reopens | MCP Apps hosts, Claude artifacts (side window plus an Artifacts tab), ChatGPT apps |

The feed or inbox is not a model of its own here. In every product examined it is one area inside another model: Slack messages, Linear's inbox, QMX's `/api/inbox`.

What each model is good and bad at, in one line each:
- **M1:** best at watching many live things. Weak for flows and depth; risks a blank board on day one and sprawl. Needs a layout engine.
- **M2:** consistent and scalable, but feels like a developer tool. Watching is limited to side views and a status bar.
- **M3:** grows by adding kinds and actions, not screens. Strong for depth and gated actions. Weak for cross-object jobs and live overview.
- **M4:** strong for reading and for mixing text with data. Has the blank-page problem. Weak for live data and for enforcing step order.
- **M5:** cheapest to keep consistent, and strong for guided steps. Weak for charts, dense views and personal layout.
- **M6:** strongest for "he asks, it happens" and for agent-made UI. Weak for watching many things, and results are hard to find again without an object home.

## 5. Comparison

Scale: strong, ok, weak. Judged from the sources, not measured.

| Model | Watch many live things | Guided multi-step job | Read one thing in depth | Agent that makes things | Outside UI fits in | Non-technical user customises | Cost to build and keep consistent |
|---|---|---|---|---|---|---|---|
| M1 Board | strong | weak | weak | ok (side copilot) | ok (native tile types); weak (HTML tiles) | ok, but blank board and sprawl | high (layout engine, sizing, overflow, saved layouts) |
| M2 Workspace with slots | ok | ok | strong | ok | strong (native slots); weak (webviews) | weak | medium |
| M3 Object pages | weak to ok | ok (actions as modals) | strong | ok (the agent acts on objects) | strong | ok (pin blocks, page builder) | medium (generic pages from schemas) |
| M4 Documents | weak | weak | strong | ok | strong | ok, but blank page | high (block editor) |
| M5 Commands and surfaces | weak | strong | ok | ok | strong | weak | low |
| M6 Conversation with views | weak | strong | ok | strong | ok (tokens plus rules) | strong (he asks) | medium |

## 6. Fit to QMX's journeys and backend

**Journeys.** The main shape of each journey (a journey can have two):

| # | Journey | Shape | Serves well | Serves badly |
|---|---|---|---|---|
| 1 | First start | flow (rare, novice: the wizard case) | M5, M6 | M1, M4 |
| 2 | Idea to judged unit | converse, then read | M6; M3 for the result | M1 |
| 3 | Unit with live checks | converse plus read | M6, M3, M4 | M1 |
| 4 | Morning proposals | triage, then read | a feed area; M3, M6 | M1 |
| 5 | Promote to paper | gated action on an object | M3, M5 | M1 |
| 6 | Node on This PC, cTrader demo | flow | M5, M6 | M1, M4 |
| 7 | Deploy or withdraw | gated action plus configure | M3, M5 | M1 |
| 8 | "Why didn't it trade?" | converse plus read | M6, M3, M4 | M1 |
| 9 | Risk stop, alarm, decide | watch, then gated action | M1 or M2 for the watch; M3 for the decision | M4 |
| 10 | Workflow from one sentence | converse, then flow | M6, M5 | M1 |
| 11 | Runs; fix from the inbox | watch plus triage | a feed area; M1, M2 | M4 |
| 12 | Watch the copilot work | watch, inside a conversation | M6; M2 (a helpers view) | M4 |
| 13 | Install a mini app, use it in chat | configure plus converse | M6 (MCP Apps); M2 (a slot) | M4 |
| 14 | Download data, see coverage | flow, then read | M5 or M6, then M3 | none clearly bad |
| 15 | Usage and providers | configure plus watch readings | M2; M3 (a provider as an object) | M4 |

**Count:**
- Shapes: flow or gated action 9; converse 6; read in depth 6; watch 4; configure 3; triage 2; compare 0. Compare appears in the Lab, outside these 15.
- Models that serve a journey well: M6 9; M3 8; M5 6; M2 4; M4 3; M1 2 (journeys 9 and 11, their watch part only).

**Backend fit.**

| Model | Fits what exists | New backend concept needed |
|---|---|---|
| M1 Board | `ui://` screens and Library cards could become tiles | A widget and board object: type, binding, size, layout, templates. None exists; only the two traces above. Tiles for the three headless apps. |
| M2 Workspace with slots | `app.toml` already declares operations, jobs, skills and agents; `ui://` can fill a slot; settings render from data | A "contributions" section in `app.toml` that names slots. This is the template's "fitting its slot" idea, unbuilt. |
| M3 Object pages | Library schemas, versions and links; unit lifecycle; the operator-only promote route; app operations as actions | A declaration of which actions and blocks attach to which Library kind; a kind filter on the Library list (missing); REST routes for unit reads (model tools only today) |
| M4 Documents | Units are already block documents; collections exist | A page object he can edit, with embedded live views |
| M5 Commands and surfaces | App operations are commands; `needs` cards, inbox actions and approval blocks are host-drawn forms | A declarative view spec (list, detail, form, chart) if apps should not need HTML; a command list at REST (dropped today) |
| M6 Conversation with views | The copilot; 14 block kinds including `artifact`, `panel`, `table`, `needs_you`; `ui://` is MCP Apps, which already passes theme tokens and display modes | A place to reopen views outside the thread; attach-on-click (missing at REST); live data the backend drops (context meter, helper prose) |

**Hybrids seen in the wild, and how they split the work.**
- OpenBB: fixed navigation, boards and a copilot side panel. Set-up flows sit outside the board.
- Grafana: a navigation frame; dashboards for questions; app pages for whole features; alert lists.
- Home Assistant: fixed pages plus user dashboards. Integrations are set up in flows, and a default dashboard is generated.
- Salesforce: app, home and record pages, all made with one page builder.
- Shopify: native object pages extended with blocks and action modals, plus a separate iframe App Home.
- Slack: messages as a feed, modals for flows, an App Home per app, canvases, and a split view for agents.
- Claude and ChatGPT: a conversation, views opened inline or beside it, and a gallery to find them again.

The split is not written down anywhere, but it repeats across these products:
- overview on a board or a status strip;
- one thing in depth on its own page;
- a risky or multi-step job in a modal or guided flow;
- the agent in a chat pane, with results opened beside it;
- "needs me" in a list;
- outside UI declarative by default, with HTML only in a bounded slot that uses the host's tokens.

---

## 7. Not verified, and sources

**Not verified**
- The original IBM CUA text: I read secondary sources only.
- Tidwell's pattern names: from the book, not re-read.
- Bloomberg Launchpad, the Cursor and Codex layouts, and Linear's inbox.
- Composer beyond its nested if/else blocks.
- Apple's split-view guidance: the page body did not load, so it comes from search excerpts of the HIG pages.
- Notion complaints: from reviews, not data.
- "Almost 60% of dashboards unused": from a 2021 Grafana blog post, not checked further.
- OpenBB's widget type list: it differs between doc versions.

**Sources**
- Progressive disclosure, Nielsen 2006: https://www.nngroup.com/articles/progressive-disclosure/
- Wizards, NN/g: https://www.nngroup.com/articles/wizards/
- OOUX, Sophia Prater: https://www.ooux.com/what-is-ooux
- IBM CUA and object-action (secondary): https://en.wikipedia.org/wiki/IBM_Common_User_Access ; https://en.wikipedia.org/wiki/Object-oriented_user_interface
- Shneiderman 1996, "The Eyes Have It": https://drum.lib.umd.edu/items/cd983adb-568a-47d3-b43a-1d8d8b8c72f4/full
- Apple split views and sidebars: https://developer.apple.com/design/human-interface-guidelines/split-views ; https://developer.apple.com/design/human-interface-guidelines/sidebars
- MCP Apps: https://modelcontextprotocol.io/docs/extensions/apps ; spec https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx
- OpenAI Apps SDK: https://developers.openai.com/apps-sdk/concepts/ui-guidelines ; https://developers.openai.com/apps-sdk/concepts/ux-principles
- Claude artifacts: https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them
- Atlassian Forge: https://developer.atlassian.com/platform/forge/ui-kit/ ; https://developer.atlassian.com/platform/forge/custom-ui/
- Shopify admin extensions: https://shopify.dev/docs/apps/build/admin
- Salesforce Lightning App Builder: https://trailhead.salesforce.com/content/learn/modules/lightning_app_builder/lightning_app_builder_intro
- VS Code: https://code.visualstudio.com/api/ux-guidelines/overview ; https://code.visualstudio.com/api/ux-guidelines/webviews
- JetBrains: https://plugins.jetbrains.com/docs/intellij/tool-windows.html
- Obsidian: https://docs.obsidian.md/Plugins/User+interface/Views
- Raycast: https://developers.raycast.com/information/manifest ; https://developers.raycast.com/api-reference/user-interface
- Slack: https://docs.slack.dev/surfaces/
- Linear agents: https://linear.app/developers/agents
- Coda Packs: https://coda.io/packs/build/latest/guides/overview/
- Notion views: https://www.notion.com/help/views-filters-and-sorts ; complaints: https://onboardme.substack.com/p/how-notion-solved-the-blank-page-product-strategy-deepdive
- OpenBB: https://docs.openbb.co/workspace/custom-backend ; https://docs.openbb.co/workspace/widgets-json-reference ; https://docs.openbb.co/terminal/custom-backend/advanced-controls/templates
- Grafana: https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/ ; https://grafana.com/developers/plugin-tools/key-concepts/plugin-types-usage ; https://grafana.com/blog/new-in-grafana-7-4-export-usage-data-to-loki-to-help-manage-dashboard-sprawl-and-troubleshoot-faster/
- Home Assistant: https://www.home-assistant.io/dashboards/ ; https://www.home-assistant.io/dashboards/sections/
- TradingView Pine visuals: https://www.tradingview.com/pine-script-docs/visuals/overview/
- QuantConnect IDE: https://www.quantconnect.com/docs/v2/cloud-platform/projects/ide
