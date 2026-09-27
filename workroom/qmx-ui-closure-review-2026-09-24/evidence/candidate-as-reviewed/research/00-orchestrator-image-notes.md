# Orchestrator first-hand image notes

Inspected 2026-09-23 by the parent sitting, not by a child agent. Images opened at readable scale via the Read tool. These are observations. Inferences are labeled.

Packet copies live at `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/source-images/`.

## Layout-governing images

### `Pasted Image 20260922150714_899.png` — OpenBB Workspace (mini-app proportions)

Visible layout, left-to-right:

- No persistent QMX-style global rail in this screenshot; a thin OS window chrome and a small left edge handle.
- **App navigation above the canvas:** Overview | Financials | Technical Analysis | Comparison Analysis | Ownership | Company Calendar | Estimates, plus a small edit/close cluster on the right of that bar.
- **Dense widget canvas occupying most width:** Ticker Information (sparkline + price), Key Metrics table, Price Performance candlestick with volume, Management Team table, Revenue Per Business Line stacked bars.
- Each widget has a header with ticker chip, **refresh**, **message/chat**, **overflow**, **expand**, **close**.
- **Substantial right copilot:** titled “Revenue Growth Analysis”, prompt, OpenBB Copilot with step-by-step, a small results table, prose analysis, composer with “Using dashboard widgets”, model picker.

This is the **mini-app interior** source. Do not copy OpenBB branding, AMZN data, or page names. Preserve: app-owned top nav, widget density, optional right copilot, expand/message on widgets.

Dictation ids: `UEafaJLm` “this open bb”; `lDsh2tno` layout pick; `YJYDP26I` reusable top bar; `JHZj5SdT` widgets expand, message icon, menus dynamic.

### `Pasted Image 20260922151452_954.png` — VS Code + right Codex (main copilot proportions)

Visible layout:

- **Narrow activity rail** on the far left (Explorer, Search, SCM, Run, Extensions, account).
- **Editor group** as the large centre: markdown file with tabs across the top.
- **Right copilot panel** with conversation, file-edit cards, composer at the bottom, model picker. Tabs on the panel: Chat / Claude Code / Codex.
- Status bar at the bottom.

This is the **main-copilot family**: sessions/history can live left of conversation; the large centre is a tabbed work/preview area; a conversation can sit beside it. Do not copy VS Code icons or Codex product chrome as QMX identity.

Dictation ids: `lDsh2tno` (layout similarity with OpenBB); `C39LFtm1` (sessions/history left); `rrUMAlEq` (preview/work area, terminal may live here).

## Main-copilot conversation / launcher references

### `Pasted Image 20260922153805_586.png` — Hermes Agent

Left: SESSIONS | BOTS, session list, search, pinned, home projects. Centre: branded splash + composer with git branch chip. Right: BROWSER tab (`about:blank`) as a preview pane. Top tabs: NEW SESSION, TERMINAL, + NEW SESSION.

Role: **main copilot with tabbed preview (browser/terminal/session)** and a left session list. Branding is not QMX. Supports `rrUMAlEq` preview-pane claim.

### `Pasted Image 20260922153840_932.png` — Codex desktop conversation + launcher

Left: chat list, pinned, projects. Centre: conversation. Right: empty panel with a **work-area launcher** (Review, Terminal, Browser, Files, Side chat) and shortcuts. Composer has `+` / Full access.

Role: conversation-navigation + explicit work-area launch. The expanded plus menu is **not** in this screenshot (packet warning). Official Codex control names unverified.

### `Pasted Image 20260922153920_566.png` — Cowork empty home

Left nav: New, Projects, Artifacts, Scheduled, Customize. Centre: “You’re here!” composer with `+`, model picker, project/folder chip, suggested ideas.

Role: **home/empty-authoring** mental model (composer-first), not a QMX layout lock. Cowork product is not a dependency.

## Settings / first-run references

### `Pasted Image 20260922154354_046.png` — Select Workspace (local/remote)

Centered dialog: Local | Remote tabs, search, workspace list, New Workspace, Back/Next. Composer at the bottom of the window.

Role: **first-run / reconnect target picker** idea (local vs remote). Not QMX chrome. Supports UX-01 connection discovery.

### `Pasted Image 20260922154421_046.png` — SETTINGS (Session tab)

Tabs: General, Integrations, Session, API Keys, Billing & Usage. Cards: Local Repositories, Factory Bridge, Remote Workspaces table with status Success/Failed.

Role: **global settings with session/API-key/remote** as separate tabs. Dictation `qhuD191N`: global settings exist; apps may also have their own. Do not copy billing.

## Other composition references (not layout locks)

### `Pasted Image 20260922154128_267.png` — Manus project home

Left app nav (New task, Agents, Search, Library, Projects). Centre: project header, composer, Instructions/Files/Skills cards, task list.

Role: **an app with its own left nav** — evidence that interiors differ. Do not impose this left nav on every mini-app (layout-fidelity-reset). Library as an app destination is a lead, not taxonomy.

### `Pasted Image 20260922154153_959.png` — Voices / studio empty state

Left grouped nav (VOICE TOOLS, LIBRARY, LIVE, STUDIO, PLATFORM). Centre: filters + empty state with three creation actions.

Role: **app-specific nav groups + empty/filter state**. Shows a second composition vs OpenBB’s top-tab + canvas. Empty states are required (03-EXPERIENCE-SCOPE checklist).

## Callout crops on OpenBB

### `Pasted Image 20260922155654_792.png` — Ticker Information widget crop

Shows sparkline, price, day’s change, volume, sector chips, and header actions: **refresh, message, overflow, expand**.

Role: the **message-plus / expand** callouts in dictation (`nLB3FO70`, `w6Wra1LH`). Message is how a widget talks to copilot without merging sessions. Expand is the compact→detail path.

## Text-element coverage (orchestrator)

All 20 text ids in `scene-text.json` were listed. Child agent 01 will produce the full ledger. Parent confirmation of the load-bearing ids:

| id | Role |
|---|---|
| `lDsh2tno` | U: pick OpenBB/VS Code **layout** |
| `UEafaJLm` | E: OpenBB image label |
| `viURg15y` | P: first/upper layout candidate |
| `YJYDP26I` | U: top bar reusable; some apps omit it |
| `rrUMAlEq` | U: main work area is preview (browser, mini-app, widget, workflow, video, diff, terminal) |
| `C39LFtm1` | U: left of main copilot = sessions/history/agent settings |
| `qhuD191N` | U: settings idea; global vs per-app still open |
| `nLB3FO70` | U: widget message icon → copilot |
| `Y3XcLbSh` | U: widget layout editing |
| `wLhO8DpA` | U: bottom add-panel control |
| `C2K3xORn` | U: Book/BMS / local-vs-server cue |
| `Ibr804Se` | U: history control |
| `NJidF6Tg` | U: jump preview → **global Library** (then self-corrects toward platform rail) |
| `w6Wra1LH` | U: expansion tool |
| `JHZj5SdT` | U: full dictation — rail divider, opened apps, dynamic menus, expand-as-tab, json-render, MCP Apps, two copilot permission seats |
| `hoGJ6iaL` | U: expanded view of widget or workflow |
| `4AhOiPPo` | E: LSE video label — **layout rejected later** in 02-CURRENT-DIRECTION |
| `rbuAuIXL`, `tD33M0Ny`, `EIWGwk1g` | minor connectors / alternate-layout pointers |

## Corrections that override image-native product names

- LSE video (`4AhOiPPo`) informs **ML capability coverage**, not layout.
- Study 03’s permanent secondary sidebar is rejected.
- Commercial dashboard kit is reference-only.
- Codex plus-menu behavior was not operated.
