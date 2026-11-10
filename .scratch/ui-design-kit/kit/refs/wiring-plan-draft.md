# QMX UI: from design to a wired release (plan, 2026-11-09)

Status: proposal. Nothing here is ratified. Design drafts live on the canvas
<https://claude.ai/artifact/HQ24PViRYAxaFTz5azc9fM>. The evidence is in `grounding/`:
01 (backend routes at engine/base `3ae41ffc`), 02 (workflows and the Lab), and 03 (the Claude Agent SDK and the UI).

## The goal

QMX ships as one complete desktop application. New features come after the release. The UI is the drawn
design on `ui-review/repair`, which was last touched on 2026-10-14. The `apps/qmx-ui` folder on engine/base is a stale
stub from 2026-09-28 and is not the design.

## Steps

### 0. Design first, one screen at a time

The canvas holds 2 or 3 options per screen. He picks one, and the picked design is built against demo data. Wiring
follows. Order of screens that need little from him: Usage, Inbox, Workflows, unit screens (unit page, journal,
trading node app, QMB runs), then the Lab declutter. The Copilot is redesigned with him, because he wants better
than a Claude Code copy. First start and install come later, with him.

### 1. The desktop shell (blocks everything)

- Every host route needs the bearer token kept in the Windows keyring as `qmx/control-token`, and the host never
  serves it (01 §1). A desktop shell must start `python -m qmx_host serve`, read the token, and hand it to the page.
- Streams must use `fetch`. The browser's `EventSource` cannot send the header.
- The shell's page origin goes to `--ui-origin`. CORS allows only GET, POST and PUT.
- Proposal: Tauri 2. It is small, has a keyring plugin and a sidecar process for the host, and runs on Windows first
  and Linux too. The alternative is Electron, which is heavier but has a familiar ecosystem.

### 2. One client layer in the UI

- A typed host client: one module per backend area (chats, library, workflows, apps, settings, usage, inbox,
  connect, keys, backups, first-start).
- One event hub that multiplexes the SSE topics (`runs, sessions, apps, library, settings, aggregates`), the chat
  `live` stream and `engine/events`. Polling covers anything without a stream.
- Demo mode stays as a switch. With demo off, unwired places say "Not connected" (UI-HANDOFF §0).

### 3. Wire the screens whose backend exists now (01 §2 = E)

Copilot chat (turns, live tokens, approvals, questions, model/effort switch with the cost quote, rewind, export),
Workflows (definitions, drafts, versions, runs, triggers, explain, spans), Inbox (list and resolve), Usage (plan
windows and readings), Settings sections, Apps, Library browse/item/versions/publish, Places and the connect
dialog, key entry, cTrader sign-in, backups and restore, the promote/deploy dialog, and the first-start card.

### 4. Wire through the generic app door

The trading node (19 ops) and the MIS (4 ops) go through `POST /api/apps/{app}/tools/{op}`. This works now but has
no push stream.

### 5. Backend asks (for the backend program, ranked)

1. Push: write the `jobs` topic, push `runs` on change, add an `inbox` topic, and add an all-runs engine stream.
2. Mount the Lab routes. `qmx_control.lab.Lab` is built but not served.
3. REST for broker reads (balances, positions, quotes, bars).
4. REST for domain reads that are model-only today: backtest start/status/results, `journal_query`,
   `unit_check`/`unit_explain`, `blocks_*`, `readings_query`, heartbeats, and the provider Test.
5. Chats: accept and return `home`, attach from the Library on click, the @file family, rename, archive, compact now
   and steer.
6. A list-all-workflows read, and `placement` on the run list rows.
7. Library list filters (kind, shelf, draft, status) and archive from the screen. App archive (now 501).
8. First-party app screens: give QMB, the trading node and the MIS a `ui` folder (each manifest is `headless` today).
9. A getting-started state computed from facts. Session and trade-count triggers. Usage rollups over time.
10. Agent SDK pass-through that the host drops today (03): thinking after reload, cost and time per turn, the
    context-window meter, sub-agent tokens, approval prompt wording, the "compacting" status, and session fork.
    Check that the todo tools are switched on for Opus 5.5, or the plan panel stays empty.

### 6. Release

Install and first start are designed with him. Verification uses user journeys that drive the real app
(`create-verification-skill`, which he wants to run through CIS), plus a fresh-install test.

## Facts that changed the old design (from 02)

- Workflows are QMX engine documents (`qmx.workflow/1`) run by QMX's own engine. Mini apps and packs are Claude
  plugins. The copilot builds workflows through a plugin skill.
- "Agentic" and "non-agentic" are not two kinds. They are three shapes of one format: script only, mixed, or one
  agent step. The 55 templates hold 271 script steps and 17 agent steps.
- The graph and code workflow editor, the node palette and the Lab benches were never built. The proposal is that
  the copilot makes workflows, the Workflows screen shows them, and hand edits are forms.
- The Lab becomes a research workspace (projects, versions, run a procedure, compare). Pods wait for the unit
  session.

## Decisions only he can make

1. Do workflows stay as QMX engine documents that the copilot builds (as the plan and code say), or did he mean
   something newer by "workflows are plugins"?
2. Does he want to edit workflow steps by hand, or are copilot plus forms enough for the release?
3. The Lab declutter: is it fine to replace the benches with projects, versions, run and compare?
4. Templates: all 55 on the shelf, or a starter set with the rest under "All"?
5. One option per screen on the canvas (Usage, Inbox, Workflows).
6. Rail places: Inbox and Workflows as their own places, and Usage at the bottom of the rail (as drawn)?
7. Phone: a companion (Today, Inbox, Chats, Nodes), with live promotions kept on the desktop?
8. Desktop shell: Tauri or Electron?
9. Is the release UI built by evolving the `ui-review/repair` code, or rebuilt clean from the picked designs?
