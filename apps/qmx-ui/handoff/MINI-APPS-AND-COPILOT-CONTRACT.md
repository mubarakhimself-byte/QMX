# Mini apps, panels and the copilot: what the UI expects from the backend

Written 2026-10-04 by the UI lane (branch `ui-review/repair`) for the fresh backend session. **Status: proposal.** Nothing here is ratified. Items the operator has ruled are marked **(ruled)**; open choices are listed in section 9.

Read with:
- `research/miniapp-sdk-ui-research.md`: how other products let add-ons and AI draw screens.
- `research/bb-t3code-research.md`: bb, T3 Code and DeepSeek Harness (Cordis), read from their source.
- `research/backend-map-miniapps.md`: what the QMX backend already has, committed and uncommitted.
- `research/session-review.md`: an honest review of the UI work so far.

## 1. Facts this rests on (operator, 2026-10-04)

- **(ruled)** The agentic layer moved to **LangChain and LangGraph**. The team's own agent SDK is dropped. Which parts of `qma-daemon` (sessions, task graph, hooks, tools) survive is **not yet recorded**. ADR-0020 (DEC-0360) had rejected hosting LangGraph, so it needs reopening.
- **(ruled)** There are two SDKs, never to be confused:
  - the **agent SDK** (LangGraph);
  - the **mini-app SDK** for mini apps and widgets.
- **(ruled)** The main copilot should behave like the Codex, ChatGPT and Claude desktop apps, including a real terminal.
- **(ruled)** Do not reinvent the wheel: follow DeepSeek Harness and bb patterns.
- **(operator's direction, to design)** A mini app can bundle UI, backend code, a database, external APIs and ML. It can feed other mini apps and provide panels. The copilot should be able to build one unattended (overnight) and prove it before it goes live, the way paper trading proves a strategy. He leans to running mini apps **with full access inside controlled sandboxes (containers)**, with circuit breakers, logging, monitoring and observability per mini app.

## 2. How a screen gets into QMX (three tiers)

| Tier | What the author supplies | Where it runs | Who may use it | Status in the UI |
|---|---|---|---|---|
| 1. Description | A panel described as data, drawn only from QMX's catalog | QMX draws it; no author code in the window | Everyone, including the copilot (default) | **Built:** `src/lib/sdk/spec.ts`, `SpecView.svelte`, tests |
| 2. Sealed window | One HTML file built ahead of time (MCP Apps style) | A sandboxed iframe with no same-origin access; theme tokens passed in | Mini apps that need a custom visual | Not built |
| 3. In-app code | A reviewed plugin bundle (bb style) | Inside the QMX window | Only plugins a person reviewed and approved | Not built; never for unreviewed copilot code |

The mini app's **backend** (Python, data, ML) is separate from all three. It runs where the backend decides, for example a container (section 6). Screens only receive data through the host.

### 2a. The panel description (tier 1), as built

```jsonc
{
  "title": "Weekend risk",
  "description": "How the momentum pods did on weekends",   // read by people and the copilot
  "size": { "minW": 3, "minH": 3 },                        // smallest size that still reads well
  "data": "pod.test.weekend_breakdown",                     // an operation or stream id the host serves, never a URL
  "root": "page",
  "elements": {                                             // flat map, as in json-render
    "page":  { "type": "Stack", "children": ["m1", "chart"] },
    "m1":    { "type": "Metric", "props": { "label": "Worst weekend", "value": "−$560", "tone": "up" } },
    "chart": { "type": "LineChart", "props": { "series": [ { "label": "Weekend rider" } ] } }
  }
}
```

- **Catalog today:** Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button. A Button carries an operation id the host runs, never code.
- **Validation** (`validate()`): only catalog types; required props; children must exist; no loops; at most 60 elements and 6 levels deep. An invalid panel shows what is wrong and never breaks the screen.
- **Backend asks:**
  1. Serve the catalog to the copilot as a tool schema.
  2. Validate on the server too.
  3. Bind `data` to real operations or streams, with empty, stale and failed states.
  4. Grow the catalog with the real QMX panels (runs table, sweep grid, pod stack, kill grid, candles).

### 2b. Where screens may appear (named surfaces)

This follows bb's surface list and DeepSeek Harness's slots. **Start with five:**
1. a tile in a Lab or Portfolio layout;
2. a card in a copilot message;
3. a Home widget;
4. a tab in the copilot's right panel;
5. a settings section for the mini app.

Each surface has fixed props and a size contract. A mini app declares which surfaces it fills in its manifest.

### 2c. Rules the host enforces

- **Theme tokens only, never raw colours.** QMX passes its tokens into sealed windows.
- **Crash containment:** a broken panel shows a small error card, never a blank QMX.
- **Generations:** the new version is mounted first, then the old one is removed. If the new one fails, the old one stays.
- **Every registration undoes itself on unload** (the Cordis rule).
- **Safe mode:** one switch that turns off everything not shipped with QMX.
- **Text and size floors:**
  - nothing under 12px;
  - numbers use the number style;
  - lists scroll inside the panel, never the page;
  - each panel is tested at its minimum size.

## 3. The copilot building UI

**Built in the demo:**
- The copilot answers with a draft panel (a tier-1 description) in the conversation.
- You **keep**, **throw away** or **pin** it. Pinning adds a Lab tile at once, with no restart (`src/lib/sdk/pinned.svelte.ts`, `PinnedPanel.svelte`).

**Backend asks:**
- **Tools:** `ui.propose_panel`, `ui.propose_layout` and `ui.propose_app`. Each returns a draft that is validated against the catalog, the granted data operations and the size range.
- **Drafts are stored with versions,** so "undo that screen" is one action.
- **Install is one logged, reversible transaction** (DeepSeek Harness `plugin_manager`): validate, snapshot, apply, then report `applied`, `failed` or `restart-required`, and restore on failure.
- **A small authoring skill for the copilot** (bb has one of 33,000 words; QMX's can be tiny because the catalog is small): the catalog schema, five examples, and the validator it must pass.
- **Chat markers** (bb `::inline-vis`, LangGraph `push_ui_message`): a short marker in a reply that the UI swaps for a live card, with no install.

## 4. Approval depends on what a mini app can touch (proposal)

The operator does not want to judge technical details; he wants to judge **risk**.

| Class | Example | Goes live when |
|---|---|---|
| Shows things | A news panel, a chart | Its checks and shadow run pass (no signature) |
| Runs work | A scheduled scraper, a retrain | The same, plus budget limits it cannot exceed |
| Touches money | Anything that proposes orders | **Always the operator's signature**, as with pods. Mini apps only propose; QMX's own confirmation places orders |

Approvals say no unless explicitly allowed: `allowed-once`, `rejected`, `cancelled` or `unavailable` (DeepSeek Harness).

## 5. A mini app's road to live (proposal: "QMX's own CI")

1. **Build:** in the copilot's build mode, possibly overnight.
2. **Tests:** its own unit and contract tests, plus the panel validator. The copilot cannot skip them.
3. **Sandbox run:** in its own container on recorded data.
4. **Shadow run:** live data for N days. Its output is shown and logged but used by nothing. This is the mini-app version of paper trading.
5. **Live:** with monitoring, budgets and a per-app circuit breaker.

The backend map notes that **logs are not evidence** (DEC-0456), so each step must leave journaled results, not only logs. The bot pipeline's gates (silent precondition battery, refusal of sandbox-provenance artifacts) are the closest existing pattern.

## 6. Where mini-app code runs (proposal; needs rulings)

- The operator's direction is **containers** per mini app: full freedom inside a controlled box, with logs, metrics, health checks, budgets, an egress allow-list and a per-app kill switch.
- **The backend already declares this but doesn't build it.** The ExecutionEnvironment contract (CT-46) has kinds `local | docker | remote_container | remote_host | browser | desktop`, and ephemeral Docker is the default per worker. No code starts a container yet, and pack Python currently loads **inside the daemon process** (`plugins/packs.py`).
- **Conflicts to resolve:**
  - ADR-0019 and DEC-0200/0201 allow containers only for observability and never on the trading-node VPS.
  - GAP-0075 (DEC-0316) rejected Modal, Daytona and E2B.
  - "No fourth observability product" limits per-app monitoring.
- **Recommended first ruling:** where packs run (in-process, subprocess, or Docker on the workstation and research server, never the trading node). Budgets, egress, circuit breakers and per-app observability all hang off it.

## 7. Sessions, sub-agents and modes (what the UI now shows)

The UI expects all of this, as built in the demo (`src/lib/copilot/`):
- **One session store** for the main copilot and the screen copilots (Lab, Portfolio, mini apps). A side conversation moves into the main copilot by id and keeps its history.
- **A session is an append-only list of blocks:**
  - user message plus attachments;
  - text;
  - plan;
  - agents;
  - tool calls;
  - "changed elsewhere" links;
  - artifact;
  - table;
  - before-and-after card;
  - question;
  - permission;
  - panel draft;
  - handoff.

  The UI shows only what the log holds (the DeepSeek Harness rule), so a second window or a refresh sees the same thing.
- **Sub-agents are child sessions.** They receive only their task, not the parent's history (T3 Code), and have a way back to the parent.
- **Questions and permissions take over the composer** until answered.
- **The Activity feed** covers sub-agents and background jobs with an id, status, progress, where each runs, and Stop. Scheduled jobs report back to the session that set them (DeepSeek Harness `jobs` and `schedule`).
- **Mode and reach on each message:**
  - mode: Ask, Plan or Do;
  - reach: Lab, Portfolio paper, Library, mini apps, servers, settings;
  - who answers.

  Real money is never in reach. **The operator parked permissions on 2026-10-04,** so treat this as a placeholder.
- **One session crossing modes** (Portfolio → Lab → mini app → build a mini app) means the session carries context, not the screen. The copilot's build mode is a backend feature (compare DeepSeek Harness "Creator mode").

## 8. What exists in the backend today (from the map)

- **Pack and grant kit (committed, on `origin/integration`):**
  - manifests, `pack_sdk`, contributions;
  - the daemon loader;
  - `pack_ui_request.v1`, which already has a canvas-widget slot;
  - `action_context`.

  This is the natural home for tier 1 and the manifest.
- **QMB** runs each backtest in its own process with time and memory limits and a cancel token. That's the closest existing sandbox.
- **Other pieces that exist:**
  - a secrets broker;
  - the trading node's egress allow-list;
  - the kill switch, for the node only;
  - JSON-lines logs;
  - an OpenTelemetry port that isn't wired yet;
  - Prometheus, Grafana and Loki, for the node only.
- **No LangChain or LangGraph code exists anywhere yet,** committed or not.
- **The only uncommitted backend work** is stale duplicates of Epics 71 and 72 in two worktrees.

## 9. Decisions needed (in this order)

1. Which `qma-daemon` subsystems survive the move to LangGraph (sessions, tools, hooks, approvals, jobs).
2. Where mini-app code runs: in-process, subprocess or container, and on which machines. This also needs the container rulings in section 6 amended.
3. Adopt the three screen tiers, with tier 1 as the default for the copilot. Can tier 3 ever be copilot-written? The operator leans "yes, like bb", but **inside the container model**. Needs his final word.
4. The approval-by-risk table in section 4, and the shadow-run length per class.
5. The terminal: a real shell on servers through the daemon (the operator wants it). That overrides the 2026-09-23 "preview only" contract (AD-21).
6. Per-app observability inside the existing stack, given "no fourth observability product".
