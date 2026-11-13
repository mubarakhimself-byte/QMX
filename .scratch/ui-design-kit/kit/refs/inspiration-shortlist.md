# Inspiration shortlist

Scouted 2026-11-10. 18 entries, ranked within each question.
Refero links need his Refero sign-in (free tier is enough to open a screen). All other links are public.
Landing and feature pages come first. Docs links appear only where the landing page shows no real UI.

---

## 1. SHELL: rail plus tiled panels, hosted mini apps

### 1.1 Foxglove: Visualization workspace
- URL: https://foxglove.dev/product/visualization (scroll past the hero; the big dark shot is the real app)
- Take: every panel follows one shared timeline scrubber at the bottom, so a chart, a table and a 3D view all show the same moment. Each panel header has only three icons: expand, settings, menu.
- Take: "describe the view you want and the agent builds the layout, then you adjust it". That is the copilot making boards, which fits the Lego idea.
- Don't take: the grey robotics chrome and the rainbow plot lines. Their colour encodes series, not meaning.
- Answers: 1 (also 4)

### 1.2 Foxglove: Extensibility (user-made panels inside the shell)
- URL: https://foxglove.dev/product/extensibility
- Take: user scripts and custom panels sit in the same layout as built-in panels, with the same header and settings. Multi-select panels and use "Group in tab" to fold a cluster of panels into one tabbed tile.
- Don't take: the code editor as the main way to make a panel. He is non-technical, so the copilot writes the code and he only sees the result.
- Answers: 1

### 1.3 Warp: factory grid (many background jobs at a glance)
- URL: https://www.warp.dev/ (first figure under the hero, "fig. 1, the factory")
- Take: hundreds of jobs shown as a dot matrix. One accent colour, four states (queued / working / waiting / shipped) shown as fill style, and one line of totals ("224 tasks, 44 active"). Good for "many jobs on several machines" on a home board.
- Don't take: the light theme and the blueprint-paper look.
- Answers: 1 (also 2)

### 1.4 Raycast: list plus preview plus action bar
- URL: https://www.raycast.com/ (scroll to the Clipboard History demo)
- Take: preview first, detail second. Left list, right preview with three or four key/value rows, and a footer action bar with the main action plus "Actions Ctrl K". Library rows could work this way.
- Don't take: the red streak backgrounds and marketing glow.
- Answers: 1 (also 3)

---

## 2. AGENT WORKSPACE

### 2.1 Warp: agent management panel and sub-agent pill bar
- URL: https://docs.warp.dev/platform/managing-cloud-agents/ (docs, because the landing page does not show this panel)
- Take: few states, each with its own icon: Working / Blocked (waiting on you) / Failed / Success / Canceled. Every row shows source (chat, schedule, Slack, API) and opens the full session in one click.
- Take: sub-agents appear as a pill bar above the session, one pill per child with a live status badge. Click a pill to swap the pane to that child; a breadcrumb leads back.
- Don't take: the parent shows "done" while a child has failed. Roll child failure up to the parent.
- Answers: 2

### 2.2 Linear for Agents: agents as teammates, work grouped by state
- URL: https://linear.app/agents (scroll to "Stay in the loop" and "Orchestrate tasks at scale")
- Take: each agent has a page with Assigned / Created tabs and its items grouped under state headers (In progress, In review, Done). The activity log is short: who, verb, state change, time ago.
- Take: "delegate, not accountability". The human stays owner and the agent is a contributor. That gives a clean model for an inbox that asks the owner to approve.
- Don't take: issue IDs and estimates. Too much text for him.
- Answers: 2 (also 3)

### 2.3 Lemni: inbox, thread, details in three panes, tool calls inline
- URL: https://refero.design/pages/f139a9a3-b343-4ef1-9860-60c5f62c32eb (his Refero sign-in)
- Take: the inbox list on the left opens a thread in the middle. Each agent tool call shows as a small card (inputs plus tool name) followed by a one-line result pill with a jump arrow. The details pane on the right holds status, priority and dates as real controls.
- Don't take: the CRM contact fields and the dense email headers.
- Answers: 2

### 2.4 Conductor: collapsed tool calls and a review side panel
- URL: https://www.conductor.build/ (hero screenshot)
- Take: a run of tool calls collapses to a single "5 tool calls" line in the chat. The right panel has Changes / Checks / Review tabs and one state chip ("Ready to merge") with a single main button.
- Don't take: the coding-only layout. He already knows the T3 Code and Codex shape; take only the collapse and the one-state-one-button idea.
- Answers: 2

### 2.5 Cofounder: run event log with History / Approvals / Logs tabs
- URL: https://refero.design/pages/a09f3c65-c0a6-421d-8bf8-71c57485e4d4 (his Refero sign-in)
- Take: one automation run has separate History, Approvals and Logs tabs. Events are timestamped and filterable, and an auto-approve toggle sits next to the approval control.
- Don't take: the light theme with the decorative shadow-leaf background.
- Answers: 2 (also 5)

---

## 3. LOOK

### 3.1 Raycast: restrained soft depth on near-black
- URL: https://www.raycast.com/ (the dock of key-cap buttons under the Clipboard History demo)
- Take: this is the closest real product to neumorphism done well. Raised key-cap buttons with a soft top highlight and inner shadow, used only for a few primary controls on a near-black ground. Panels stay flat. Depth means "you can press this", nothing else.
- Don't take: soft depth on every card. Raycast keeps it for controls only.
- Answers: 3

### 3.2 Resend: settings on true black
- URL: https://refero.design/pages/b374be61-cc40-4599-a43f-e95475c011ca (his Refero sign-in)
- Take: true black background, hairline separators instead of boxes, and one white primary button per section. Calm even with many rows.
- Don't take: the small grey body text. He wants big readable text.
- Answers: 3 (also 5)

### 3.3 Linear marketing pages: near-black with state colour only
- URL: https://linear.app/agents
- Take: near-black surfaces with very faint raised cards (1px light top edge plus a soft shadow). Colour appears only on state icons: yellow for in progress, green for in review, blue for done. It works as a direct "colour = meaning" rule (for example paper vs live).
- Don't take: the fading gradient masks over content. They hide data.
- Answers: 3

---

## 4. DATA PRODUCTS

### 4.1 Foxglove: compare two runs side by side
- URL: https://foxglove.dev/product/visualization (section "04 Compare multiple runs side by side")
- Take: load run A and run B into one layout ("Merge" source mode), each row tagged with an A or B badge and stepped by one shared playhead. This fits backtest-vs-backtest or paper-vs-live.
- Don't take: the magenta and olive state bars. Use his own state colours.
- Answers: 4

### 4.2 Weights & Biases: runs list drives every chart
- URL: https://wandb.ai/site/experiment-tracking/ (hero video and "Visualize and compare every experiment" shot)
- Take: a runs list on the left, where each run has an eye toggle and a colour swatch, and toggling a run updates every chart panel on the right. On the docs side, the Run Comparer "Diff only" switch hides every setting that is the same across runs: https://docs.coreweave.com/products/wandb/app/features/panels/run-comparer
- Don't take: the yellow accent headings and the many-colour line spaghetti.
- Answers: 4

### 4.3 Steel: compact usage overview on near-black
- URL: https://refero.design/pages/d499ba7e-45e3-4365-be81-a2d756f9f775 (his Refero sign-in)
- Take: one row of five or six KPI numbers with no cards around them, then two activity charts side by side. A good first screen for jobs or spend, because it reads quickly.
- Don't take: the bright yellow and blue bar colours, which carry no meaning.
- Answers: 4 (also 5)

---

## 5. SMALL BUT HARD SCREENS

### 5.1 Trigger.dev: run trace timeline and run table
- URL: https://trigger.dev/product/observability-and-monitoring
- Take: the run page is a trace waterfall (steps as bars on a time axis) with a right inspector that has Overview / Detail / Context tabs and the payload. The run table filters by status, task and environment, and its status pills are the only colour.
- Take: the alert setup is small and real: channel tabs (Email / Slack / Webhook) plus checkboxes per event and per environment.
- Don't take: the neon headline colours on the marketing page.
- Answers: 5 (also 2)

### 5.2 JetBrains AI Assistant: model assignment by role, with fallback
- URL: https://www.jetbrains.com/help/ai-assistant/use-custom-models.html#use-custom-models-in-ai-features (docs; no landing page shows it)
- Take: models are assigned to roles ("Core features", "Instant helpers"), not to each feature, with one short line under each dropdown saying what that role covers. Unassigned roles fall back to the default, and a separate "assigned and fallback models" list shows the result. This is inheritance he can understand.
- Don't take: the cramped IDE settings dialog styling.
- Answers: 5

### 5.3 Raycast AI: model picker with a spec card
- URL: https://refero.design/pages/77c117fd-3d56-450a-986d-fca5502971d2 (his Refero sign-in)
- Take: hovering a model in the picker opens a side card with Speed and Intelligence as five-step bars, context size, "Recommended for" and "Supports" checkmarks. He can pick a model without knowing model names.
- Don't take: the long flat list of near-identical model variants. Group by provider and hide old versions.
- Answers: 5

### 5.4 Anthropic Console: usage with filters and paired charts
- URL: https://refero.design/pages/865a7bf8-9a2a-4a62-8709-2fa28f9f0dbb (his Refero sign-in)
- Take: dark usage page with two big totals and two paired charts underneath, filtered by key, model and date, plus export. A plain base for his usage page; add plan-limit bars on top.
- Don't take: the orange accent (he dislikes orange).
- Answers: 5

---

## Patterns that repeated
- Few states, fixed icons: about five run states (working, waiting on you, failed, done, canceled) recur in Warp, Linear and Trigger.dev. "Waiting on you" is always its own state.
- One click from a list row to the full session or run. The list is for navigating, not a second detail view.
- Tool calls collapse into one line or a small card with a one-line result. The detail is one level down.
- Right-side inspector with tabs (Overview / Detail / Logs or History / Approvals / Logs) instead of more sidebars.
- Comparison means a shared axis or playhead plus an A/B tag, or a "diff only" switch, not two screens.
- Colour used only for state on near-black. Charts get neutral or one-hue lines.
- Panel headers stay tiny: title plus expand, settings, menu. Expand to full screen is a header icon or double-click.
- Soft depth, when used well, is only on pressable controls (Raycast). Data surfaces stay flat.

## Dead ends
- Neumorphism in a real data product: Refero's research chat itself said it found no real neumorphic dashboards, only subtle depth on dark panels. A Dribbble search for "soft ui dark dashboard" returned only concept shots.
- Agent task boards grouped by "needs review / running / done" on Refero: none. Refero offered Zapier, GitHub and n8n run lists instead, which are generic.
- Strategy backtest result pages (equity curve plus drawdown plus two-strategy compare): Refero found none; it offered only portfolio charts (Glassnode, Wealthsimple, Kraken).
- Empty first-day states: Refero results were light-theme onboarding modals (Reown, Linktree "show sample data"). Nothing strong for a dark data tool.
- Composer (retail strategy builder) home page would not load in the tab. Rerun viewer docs URL was dead. Koyfin dashboards are a light-theme repeat of the OpenBB linked-widgets idea, so they were left out.
- Refero's earlier saved research threads (Manus, ChatGPT, Claude, Factory, CRM/CMS shells) were mostly noise: wrong products under right labels.
