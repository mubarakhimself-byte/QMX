# Xynth + Prime Terminal live UI/UX research

Observed in the browser on 2026-09-23 using the assigned public sites and public demo content. This is product-interface evidence, separate from vendor marketing claims and from design recommendations. Three visual evidence captures are saved under [`screenshots/`](C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/live-research/screenshots/): [Prime matrix](C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/live-research/screenshots/prime-bias-matrix.png), [Prime expanded narrative](C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/live-research/screenshots/prime-bias-expanded.png), and [Xynth alert description](C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/live-research/screenshots/xynth-alert-description.png). The Xynth screenshot shows the anonymous sign-up gate's blur over the Description view; its content was accessible in the page's accessibility tree, but the site would not render it sharply without signing in.

## Xynth

### URLs and actions

- [Homepage](https://xynth.com/): opened the AI research prompt, expanded the model / data / skills controls only by inspecting their visible state, and reviewed the ticker actions, public library teasers, live-session list and market workflow explainer.
- [Library](https://xynth.com/library): opened through the homepage Library link; inspected the category filters and cards for Skills, Signals, Automations, User Stories and Tutorials. Clicking a public signal card brought up an account-creation gate; no information was entered and no account was created.
- [Short Interest Alert](https://xynth.com/alerts/alert-316c218a3600): opened from the homepage's public-alert link. Closed the sign-up overlay to read the delayed public run and used the Description tab. The LIVE option explicitly advertises a paid-plan requirement. Subscribe, download, run history and edit flows were not submitted or changed.
- Tried a public session link from the live-session list. The visible link resolved to a shortened identifier and the public session route reported “Chat not found,” so I did not treat that as a successful chat inspection.

### Directly observed interface

- The home composer is the main entry point. It includes file selection, a prompt field, model selection (the public default showed Opus), attachment, data-source selection, skills selection, voice recording, and an Analyze button for each of the listed market tickers. The ticker cards show a quote and change alongside the action.
- The home page presents several related surfaces together: the assistant composer, market ticker, public alerts, library teasers, trader sessions and a staged research explainer. The explainer depicts question → blueprint / plan → data retrieval and code → dashboard findings → alert automation. Treat that staged sequence as a product illustration; only the public alert result described below was exercised.
- The Library uses category filters and card grids rather than a single undifferentiated list. Skill cards expose the model, estimated cost for each model, approximate run time, usage count and a Run action. Signal cards surface deployed amount, current value / percentage change, win rate, trade count and open count. Automation cards are named examples, while alert cards show their schedule and owner.
- The Short Interest Alert result has a compact header with alert title, last-run / delayed state, and Dashboard, Description, Canvas and View past runs controls. It also exposes dashboard download, delayed/live selection and Subscribe. A contextual “Ask Xynth about this alert” composer carries the selected alert context and offers model, file, data-source and skills controls. The header helper copy describes editing cells and thresholds and saving changes with `upload_alert`; that destructive/persistent edit workflow is login-gated and was not attempted.
- The public delayed dashboard is an actual structured result, rather than just a claim: it labels the snapshot time, condition status, ticker, current short interest, change, alert status, action list, plain-language meaning, next steps, chart, and explanatory sections (“what it shows,” “why it matters,” “look for”). A log-style bottom-line explains why the condition did not fire. The sample says TSLA short interest was 75.19M, +1.6%, below a 10% trigger; its chart has 12 reporting periods. This creates a useful path from compact summary into evidence and next action.
- The Description view explains the monitor schedule and threshold, lists its data and comparison steps, describes the dashboard, and states its email delivery condition. This pairs an operational overview with the result view.
- A public alert click immediately presented signup; closing it exposed the delayed snapshot. Account-specific alert controls and live data remain gated. A sample session route also returned “Chat not found.”

### Vendor claims, not independently verified

The marketing page claims 3,000+ data sources, 24/7 automations, email delivery, AI research/coding/backtesting, cited synthesis and reductions in research time. The library includes performance figures for sample signals, and the landing page includes trader earnings stories. Those are claims or displayed examples, not evidence that the platform's performance or sources were independently validated.

### QMX design implications / questions

- The per-card run time and model-specific cost are useful before execution; QMX could expose expected time, resource cost and model/tool choice at the action point for any workflow with variable cost.
- A single output view can combine outcome, evidence, interpretation and next actions while preserving a separate Description view for “how this runs.” Consider a persistent top-level preview with these as sibling result/detail modes, and make long evidence expandable.
- Libraries benefit from distinct content types and metadata: skill (reusable procedure), signal (track-recorded result), automation (schedule), story/tutorial (learning). QMX should decide whether these are different artifact types or filters over one library model.
- The public result shows how an individual alert's design could support widget expansion: a compact condition summary expands into charts, explanatory prose and audit-like logs. Ask whether QMX's expanded widget or workflow should take over the canvas, open a same-app tab, or use a right-hand preview beside the originating workspace.
- Research history and per-run history were visible as affordances but user-owned session/history content could not be read anonymously. Decide which history is global, per app, per workflow and per run; the UI should distinguish saved artifacts from transient results.
- The contextual assistant is repeatedly attached to the artifact being inspected. QMX could scope a copilot to the selected mini-app/widget and pass current selection/data without making the global assistant lose its own conversation state.

## Prime Terminal

### URLs and actions

- [Prime Terminal homepage](https://prime-terminal.com/): inspected the top market ticker, nav, embedded Smart Bias Tracker preview, market tabs, process section, module summaries, pricing, FAQ affordances and links to Knowledge, login and demo. I did not follow checkout, trial messaging, WhatsApp or login.
- [Smart Bias Tracker public demo](https://prime-terminal.com/feature-demos/smart-bias-tracker/index): opened from the iframe route exposed in the homepage accessibility tree so the public sample could be inspected at full size. Captured one screenshot of the matrix and a separate screenshot of the expanded GBP narrative. The expanded screenshot visibly shows the detail view rather than the matrix; the page accessibility tree retained the table while the detail was open. Clicking a table cell exposed a per-currency summary; the demo fixture and selection varied across observations, so the exact selected-cell mapping is uncertain.

### Directly observed interface

- The homepage keeps a narrow, repeating market tape under the primary navigation. The active quote stream remains visible as the page scrolls through feature sections.
- The actual public demo is a compact terminal-like panel: widget title and controls across the top; currency flags as columns; indicators / banks / positioning as rows; green, gray and red status chips; sticky headers and a vertical scrollbar. The dimensions favor seeing many cross-currency comparisons at once.
- The toolbar shows a Scanner selector, date range, gear and close icons. Opening the Scanner selector reveals currency choices USD, EUR, GBP, AUD, CAD, CHF and JPY. The gear was visible but its panel could not be verified through the accessible tree. I did not change any settings.
- Selecting a matrix value opened an expanded detail view. In the verified screenshot the detail fills the available app viewport and the matrix is visually displaced/hidden; the accessibility tree still contained the table. The view keeps currency and date at the top, puts category-level biases in a narrow left rail, and uses the larger right area for a weekly narrative, highlighted drivers, and near-term / longer-term outlook. The interaction is progressive disclosure, while the screenshot confirms that detail takes visual precedence over the matrix.
- The sample overview rows include Fundamental Data (growth, prices, confidence, manufacturing/service activity, housing, permits, retail sales); Bank Overview (multiple named banks); Hedge Fund Positioning; Retail Positioning; Monetary Policy; Trend; Seasonality; and Overall Conclusion. This is a multidomain dashboard module, not a generic chart.
- The content shows a date mismatch: the widget header displayed 22–28/06/2026, while the expanded summary was labelled 01–06 Jan 2026. This appears to be a demo-fixture consistency issue and is a warning for QMX preview fixtures: every drilldown must inherit a consistent as-of date and timezone.
- The homepage's “One platform. Different workflows.” section has three selectable market tabs (FX and macro; Indices and commodities; Rates and fixed income). Selecting each tab actually changed the selected tab and body panel. The panel gives an audience-specific description and a short set of included modules, e.g. cross-asset confirmation for FX or COT / seasonality for indices and commodities.
- The page outlines a six-step information workflow: Aggregate news, data and research → Filter by asset/region/impact/watchlists → Validate directional bias and drivers → Confirm against cross-asset context → Plan in Research Files with levels and invalidation → Execute with charts and risk tools. This is a marketing process description; I did not observe those steps executing end to end in an authenticated workspace.

### Vendor claims, not independently verified

The site claims 80 modular widgets in one section and 90+ widgets in pricing, 1,000+ news sources, live alerts, bank research, 24/5 analysts, and availability across web, desktop and mobile. Reviews, Trustpilot score and competitor cost comparisons are displayed as claims. The pricing copy says the product has the same terminal in each plan; no paid or trial workspace was entered.

### QMX design implications / questions

- Prime's table-first overview makes the relationships between instruments, factors, and evidence legible before zooming into one result. QMX should reserve dense grid layouts for comparisons that need synchronized cross-asset context; each cell should have a keyboard-accessible drilldown and a short textual status for screen readers.
- The expansion preserves the context used to interpret the result: currency, period, aggregate category scores and narrative drivers. If QMX opens detail in an app tab or preview pane, carry those identifiers and a clear back/close action so the user can return without losing place.
- Consider an expanded widget as a distinct view of the same underlying artifact. It can hold detailed charts/data and evidence while keeping the surrounding mini-app's top tabs and copilot context; it need not become a new top-level application.
- The always-visible market tape, workspace-level market tabs and per-widget controls form three different navigation scopes. For QMX, avoid mixing global navigation, mini-app sections and widget-local controls in one undifferentiated top bar.
- QMX layout-edit mode could borrow a visible distinction between “reading data” and “arranging panels.” The Prime sample exposes widget-level settings only as an icon; QMX should label panel controls and make rearrangement / configuration available in an explicit edit mode, with current layout name and saved/local state visible.
- Use typed status chips (bullish / neutral / bearish) with shape or text cues as well as color, and connect each aggregate conclusion to its supporting rows. Keep the aggregate at a glance, and let it drill into component evidence.

## Cross-reference to the fresh QMX storyboard

The storyboard emphasizes a reusable app shell, a workspace / preview pane for agents, mini-apps, workflows and terminals, expandable dashboard widgets, an assistant tied across surfaces, session history and a global library. These sites validate the need to distinguish four navigation levels: workspace shell, mini-app pages/tabs, widget focus/detail, and per-run history/result. Xynth demonstrates a contextual research assistant and artifact-oriented result views; Prime demonstrates dense cross-asset dashboard comparison and a same-widget expansion pattern. These are source inspirations, not instructions to copy their information architecture wholesale.

Open questions for the design session:

1. Is the global library a shelf of reusable components/workflows, a library of complete mini-apps, or both with separate types?
2. Does an expanded widget replace its current canvas area, open a tab within the mini-app, or appear in the preview pane? What is the expected return path?
3. Which items deserve history: assistant session, workflow execution, widget refresh, automation firing, and user layout edit? How do their lifetimes differ?
4. Which layout controls are global, mini-app-specific or widget-specific? Can the shell show those scopes without duplicating controls in every app?
5. How should every displayed result expose its input snapshot, source/timestamp, method, calculation/log, interpretation, and suggested next action?
