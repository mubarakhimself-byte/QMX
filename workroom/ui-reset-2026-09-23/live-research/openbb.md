# OpenBB Workspace: live reference research

Research date: 2026-09-23

## Scope and confidence

I inspected OpenBB's current public Workspace product page, the public Workspace documentation, and the public sign-in screen using the assigned browser tab. I did not sign in or test a live authenticated workspace. The UI screenshots embedded in docs are documentation illustrations, not a running product interaction. Browser screenshots of the embedded product demo were saved under screenshots/ and are linked below. They are recorded-demo evidence, not live authenticated app captures.

The product site displayed an August 25, 2026 founder letter overlay titled “OpenBB belongs to everyone.” It says OpenBB is committing to release the suite, including Workspace, ODP, Copilot, and the Excel Add-in, under a permissive open source license. It also says release order and timing will be shared later and existing hosted users will hear directly about timelines. I dismissed the letter to inspect the product page. This is a material product-status caveat: the material below documents the public product/docs presentation, not a guarantee that the hosted app remains generally available.

## Factual observations

### Product page and entry point

- Product page: [OpenBB Workspace](https://openbb.co/products/workspace/).
- The page leads with a short product proposition, then four supporting claims: connect any data source, self-host, avoid frontend work, and retain IP ownership. These are vendor claims, not independently tested.
- The page frames the product as one shared workspace for interactive dashboards, firm data, and AI agents. It presents use cases including portfolio analytics, crypto/digital assets, macro research and scenario planning, compliance/operations intelligence, and alternative data integration.
- The page links to public widget, dashboard and Copilot documentation. The product image is a marketing illustration and does not establish live functionality.
- Public sign-in at [pro.openbb.co/login](https://pro.openbb.co/login) rendered a conventional centered sign-in card (email, password, remember-me, forgotten-password link, login and Google sign-in). I stopped there; no account was used.

### Dashboard composition and organization

- [Dashboard docs](https://docs.openbb.co/workspace/analysts/dashboards) describe a dashboard as a canvas for arranging multiple widgets. They explicitly describe drag-to-arrange, resize, automatic data refresh, sharing, and making a copy of a shared dashboard.
- The documented creation flow is: create from the sidebar plus button, name it, add widgets, arrange and resize them, optionally add a navigation-bar widget for categories, then save.
- The docs place folders in the left sidebar. They support nested folders, drag-and-drop organization, and per-dashboard actions from an ellipsis: rename, move, duplicate, open in a new window, share, delete, and refresh data.
- Right-clicking the dashboard canvas is documented as a shortcut menu for adding widgets or data, refreshing data/backends, exporting `apps.json`, and toggling grouping.
- This is enough evidence for a sidebar-managed collection of workspaces and freely composed dashboard canvases, but no live dashboard controls were exercised.

### Widgets, detail controls, and library

- [Widget overview](https://docs.openbb.co/workspace/analysts/widgets/overview) treats a widget as a self-contained analytical data container. It lists a source, discovery metadata (title, description, category, subcategory, source attribution), a visual presentation, input parameters, and widget-specific controls.
- Documented visual forms include sortable/filterable tables, charts, PDFs, and custom views. Input parameters may select tickers, date ranges, or filters. Parameters with the same name can be linked so changes in one widget update other widgets in the same group.
- Universal controls are described as refresh frequency, export to CSV/JSON/Excel, and toggles between chart/view and raw data. Table controls include sorting, filtering and grouping. TradingView charts can expose indicator overlays and timeframe controls; Plotly widgets can render Plotly-supported figures.
- The docs describe the widget library as searchable and categorized. Entry points include the top-left search field or Ctrl/Cmd+K, a plus button at the dashboard's lower right, or an Add Widget button. Search categories are intended to group widgets by analytical workflows (e.g. equity price/fundamentals/options/estimates, or portfolio positions/performance/risk).
- A widget's metadata is also described as AI-readable. Docs state that AI can query source data using metadata and parameters, and that a config flag can exclude a widget from AI. This is a useful example of a UI object carrying a machine-readable contract alongside its visualization.
- The docs include a library UI screenshot, but the widget-resize/full-screen behavior requested for comparison was not demonstrated in the text or in a live workspace during this inspection. Treat expansion affordances seen in screenshots as illustrative unless separately verified.
- The public [Interacting with Data docs](https://docs.openbb.co/workspace/analysts/widgets/interacting-with-data) add resize/reorder for table columns, hover cards, selection-based charting, a chart-view toggle, and a raw-data toggle. They describe chart customization through a three-dot menu. These are in-widget view changes, not a documented full-screen or new-tab expansion.
- The public [Core Widgets docs](https://docs.openbb.co/workspace/analysts/widgets/core-widgets) describe a Navigation Bar widget that creates dashboard tabs, a Note widget for research notes/prompts, and a Website/Iframe widget for embedding external sites side by side. The Website widget is contingent on the site permitting embedding.

### Apps as structured starting points

- [Apps docs](https://docs.openbb.co/workspace/analysts/apps) define an App as a pre-configured dashboard template combining a widget set, preselected AI agent, and custom prompts.
- App widgets can have synchronized parameters and a preset layout. Apps can include prompt libraries written for that App's analytical task. Selecting an App is said to render it as an editable dashboard.
- The docs distinguish Apps (preconfigured purpose, linked widgets, curated prompts, domain-designed) from blank dashboards. They show a multiple-applications view and a portfolio-risk dashboard as static examples.
- The public [App Showcase](https://openbb.co/solutions/app-showcase/) route redirected into the same founder-letter overlay during my inspection, so I did not get a separate interactive showcase state.

### Copilot, context and history

- [Copilot Basics](https://docs.openbb.co/workspace/analysts/ai-features/copilot-basics) describes a three-part panel: a header for the current conversation and actions (new, clear, full-screen, hide); a body showing messages and output; and a footer for context, custom agents, and the prompt library.
- The docs say the panel can be resized by dragging its border, used as a side panel, expanded to full-screen, or hidden while retaining the dashboard.
- The prompt library stores prompts and can tag widgets to make context more specific.
- [Context Management](https://docs.openbb.co/workspace/analysts/ai-features/copilot-context) describes a visible context hierarchy: explicit widgets/skills/tools; AI Library skills; connected MCP tools; attached files; all dashboard widgets (across tabs); conversation; optionally global widget data; optionally web search.
- Users can explicitly tag skills and tools with slash syntax, or attach a widget via “Add to context” or `@` mention. The docs say explicit widget context remains active until a prompt is sent, then is removed. Dashboard context includes all active-dashboard widgets, metadata, and currently selected parameters. File attachments may include PDFs, Excel, CSV, and other document types; the docs warn that selectable PDF text is required because OCR is not supported.
- These are documentation-described behaviors; the chat was not exercised live. I did not find documented chat-session history management beyond current-conversation history and the header's new/clear controls.

### Public product demo footage

- The Workspace overview docs contain a playable, embedded [OpenBB Workspace product demo](https://www.youtube.com/watch?v=uYyhswnZkSw) (23 minutes, per the player). I played the first minute in the browser and inspected the video frames. This is a recorded demo, not a live instance.
- Early in the recording, an Apps gallery appears as a tile grid with a persistent left navigation rail, followed by a selected multi-widget dashboard. The dashboard has a row of named view tabs across the top and a two-column widget layout; the video narrator explicitly describes an app opening into an editable/configurable dashboard.
- A later frame shows the dashboard beside a Copilot panel. The panel includes a context status row (“Using dashboard widgets”), a question input, and an agent selector. Another frame shows Copilot settings with separate Web Search and Global Data switches and short explanations. This gives a concrete public visual for per-chat context/settings even though the user-facing settings page was not found.
- Saved frames from the recording are in [`screenshots/`](screenshots/): [app gallery](screenshots/openbb-app-gallery.png), [multi-widget dashboard](screenshots/openbb-dashboard.png), and [Copilot/context settings](screenshots/openbb-copilot-panel.png). They were captured from the embedded demo around 0:01, 0:41, and 1:01 respectively.
- The video uses sample financial/company data. I did not treat the content as current market data or validate the data outputs. The screencast is historical and may show an older interface than the current docs.

### Customization, sharing and settings

- Customization documented here is mainly per-dashboard: widget layout, sizing, grouping, folders, navigation-bar widgets, and sharing/copying. The docs also describe app-level preset layouts, agents and prompts.
- I found no documentation that a widget expands into a dedicated full-screen view or new tab. Dashboard docs do document resizing a widget; Copilot docs separately document resizing its side panel and expanding chat to full screen. The storyboard's “expand widget/workflow” and “preview to library” controls remain QMX proposals; OpenBB's public docs describe the library as a way to find/add widgets and do not describe that preview-to-library transition.
- Publishing/distribution is described as interactive dashboard sharing, rather than sending screenshots; the docs say recipients may view and make their own copies. Exact access controls and publishing dialogs were not inspected.
- I did not find a public end-user settings page or a live global settings surface within the pages inspected. The product demo does visibly show Copilot-level Web Search and Global Data settings, which should be understood as contextual AI controls rather than evidence of a global preferences screen. The docs mention deployment/admin concerns on the product page (entitlements, access controls, audit trails) as product claims, but those are not evidence of a particular settings UI.

## Design inferences for QMX (not OpenBB product facts)

- A useful transferable pattern is to separate reusable content types: **widget** (one question/data view), **dashboard** (a canvas with tabs/groups of widgets), and **app/template** (a task-specific starting point with curated widgets and prompts). QMX could name these separately so users can tell editing a view from composing a whole mini-app.
- The parameter-linking behavior suggests a QMX pattern for shared symbols, dates, portfolios, or scenario IDs: make synchronization visible, scope it, and show which widgets will respond before a user changes the shared value.
- Carrying source/category/description and an AI-access flag on the widget gives search, attribution, permission and assistant context a shared source of truth. QMX should show provenance and explain what the assistant can see where the user adds an item to context.
- App presets plus editable dashboards suit a “start from a purposeful template, then customize” flow. QMX can preserve a path back to the app library from a preview while keeping saved user variations distinct from the published template.
- The docs' separate dashboard menu and canvas right-click menu show two levels of action scope. QMX can use that distinction to prevent ambiguity: dashboard-wide actions in the tab/header/sidebar menu; widget-specific actions inside each widget; canvas-level “add” actions in empty space.
- Copilot's resize/full-screen/hide states keep chat available at different levels of attention. For QMX's preview pane idea, a similar reversible expansion could preserve the underlying workspace selection and return the user to the prior place.
- OpenBB's documented context priority offers a concrete QMX design question: make scope and precedence visible (selected object, current tab/dashboard, library-wide sources, conversation, external search), instead of leaving the agent's input set implicit.

## Source and action log

- Opened the assigned Workspace product tab and dismissed the founder-letter overlay using its Close letter control.
- Read the public Widgets Overview, Dashboards, Apps, Copilot Basics, and Context Management docs in the browser.
- Also checked Core Widgets and Interacting With Data docs for widget expansion and navigation details.
- Played the embedded product demo for approximately one minute and inspected the visible UI footage: app tile gallery, editable dashboard with top tabs and multiple widgets, and Copilot context/settings.
- Captured browser screenshots and saved three product-demo frames under screenshots/, as linked above.
- Opened the public login page and observed the sign-in UI only. No credentials, account creation, or settings changes were made.
- Tried the public App Showcase route; it surfaced the same founder-letter overlay.
