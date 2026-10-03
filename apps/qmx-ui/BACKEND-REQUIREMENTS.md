# QMX UI: what the screens need from the backend

Owner of this file: the UI lane (`apps/qmx-ui`). Audience: Codex / backend lane.
Status: 2026-10-01. The UI is rebuilt on branch `ui-review/repair`. No transport is bound.
Every daemon-backed control is visibly disabled with a reason. Nothing is faked.

Governing specs:

- `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/` (BACKEND-DEPENDENCIES.md, COMPONENT-CONTRACTS.md, VIEW-AND-PACK-CONTRACT.md)
- `epics-UI-2026-09-27.md`, backend Epics 67–73
- Audit Packet 08 (UI01–UI05)

## Rules the UI keeps

- The browser never spawns Python and never holds credentials.
- Widgets never call the wire. Only three host issuers do: `dispatchChat` (`send_message`), `dispatchInvoke` (InvocationEnvelope), and `dispatchCancel` (`cancel_job`).
- Recording or fixture transports are allowed only behind an explicit test switch. Production code binds the real transport or shows "Not connected".
- An accepted placement or acknowledgement is not a completed job. The UI waits for the terminal JobHandle state.

## Needed per screen

| Screen / control                                         | Daemon capability needed                                                                                                                                                                                                           | Spec ref                         |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Status bar connection, Settings › Readiness, Pair button | Live CT-40 server (WebSocket JSON-RPC + HTTP GET snapshots + `wire.attach` events); `/pair/start`, `/pair/confirm`, `/pair/renew`; WS subprotocol `qmx.pair.<proof>`; five readiness axes with `retry_probe`                       | Epics 67, 68; UI-AD-11, UI-AD-19 |
| Copilot › sessions list, New session, history            | `psess:` listing and create; `list_mailbox` with `product_session_ref`                                                                                                                                                             | Epic 69                          |
| Composer Send (Home, Copilot, app copilot, Authoring)    | `send_message` dispatched over the socket                                                                                                                                                                                          | Epic 69; UI-AD-18                |
| Home › Needs attention, Resume; rail badges              | JobHandle listing with `originating_product_session_ref`; terminal states incl. `unknown`                                                                                                                                          | Epics 63, 73                     |
| Cancel (RunInspector, later)                             | `cancel_job`                                                                                                                                                                                                                       | Epic 73                          |
| Library › search and tabs                                | facade search over HTTP returning typed ArtifactHit / KnowledgeHit / ContributionHit                                                                                                                                               | UI LIBRARY §5                    |
| Composer + (attach)                                      | `PUT /artifacts/stage`, `registry:artifact.stage_max_bytes`, `transfer_artifact`                                                                                                                                                   | Epic 70                          |
| Authoring › Save, Validate, Publish, Run                 | `save_editor_draft` (daemon-issued `editor_draft_id`, CAS on `editor_revision`), `get_editor_draft_head`, validate, `publish_editor_draft` → enable → grant → instance → invoke. Draft run must refuse with `draft_not_runnable`.  | Epic 71; UI-AD-9, UI-AD-21       |
| Authoring › add step palette                             | listing of available operations / Graph Template contributions                                                                                                                                                                     | Packet 08 UI02                   |
| Rail › opened apps; mini-app nav and widget canvas       | instance listing + `health()`; `get_pack_ui_request` by `instance_id` + `availability_revision`; `PackUiRequest` v1 `nav[]` / `views[]`; `ActionContext` per mount (0 grants paints and refuses, 1 binds, 2+ is `GRANT_AMBIGUOUS`) | Epics 64, 72                     |
| App copilot panel                                        | `PluginManifest.copilot_profile`; `app-use` psess                                                                                                                                                                                  | Epic 60.1                        |
| Copilot work area › Terminal                             | read-only stream of a job's output (not a shell)                                                                                                                                                                                   | COMPONENT-CONTRACTS §4           |
| Any missing method                                       | typed `INCOMPATIBLE` / `caller_kind_unsupported`, never an empty success                                                                                                                                                           | J-UI-13                          |

## First vertical slice the UI will wire once available

1. Pair, then the status bar shows Connected.
2. Home quick chat goes through `send_message` → `list_mailbox`, and the reply survives a browser and daemon restart.
3. Authoring Save produces a daemon-issued draft id. Reopen shows the same draft and revision.

## Open UI decisions (no backend impact)

- Widget expand: in-canvas layout change with "Back" (current) vs a browser-style tab (storyboard). Docs leave this open.
- Saved widget layouts: client-local only for now. No backend contract exists.

## Demo mode (UI-only, must not ship as product data)

`workbench.demoMode` (Settings › Developer) shows labelled sample surfaces: the Research app on the rail, a sample workflow in Authoring, the Copilot sample session, and a Library list built from `public/demo/mql5-articles.json` (titles, dates, sections and a short excerpt from the local `mql5-library` catalog; no full text). Each one carries a Demo banner. When a transport is bound, these are replaced by:

- Library: facade search + article detail (full text, generated summary, key points) from the daemon's Library.
- Copilot: `psess:` mailbox history; tool-call records and result tables from the JobHandle; "Save to Library" via artifact staging.
- Authoring: the graph from `get_editor_draft_head`; node settings/code from the draft; last results from the JobHandle of a published version.

## New scope from the 2026-10-01 design pass (needs a ruling)

Operator asked for these; the docs do not cover them yet. Flag for a BMad/doc decision before backend work.

- **Library article text**: serve full text plus figures for Knowledge items (today the demo reads the local MQL5 catalog via a dev-only Vite route behind `QMX_DEMO_MQL5_DIR`). Add a "key points" summary written by a small, cheap model on the daemon, never in the browser.
- **Sources**: daemon-side feed subscriptions (RSS/APIs) for arXiv q-fin, alphaXiv, SSRN, MQL5; store kept items as Knowledge hits. The browser never fetches feeds. Forex Factory calendar remains the only _ruled_ source (DEC-0214, free only).
- **News**: headline feed (free sources) with time, source, symbols, impact and tone; consumers are the News widget, node news windows (ruled), workflow triggers on topic/symbol, and copilot citations.
- **Turn into hypothesis**: write a QML Stage 0 hypothesis citing a Knowledge item (`research_ref`).
- **ML models**: there is no ML-model entity in the docs. The UI shows models with "slots" (entry signal, position sizing, MIS regime, risk throttle). Needs a decision on how a model artifact is registered and plugged into a slot.
- **Entity detail**: per bot/model/app/workflow — evidence runs (CT-32 with run role), journal (CT-13), node/book connections and seat state, operations with input schemas (headless apps run from here), linked artifacts.
- **Model and tool lists** for the composer and Settings come from the daemon's provider registry; the UI stores no keys.
- **Background art presets (optional)**: saved variants live in browser storage per machine (`qmx.art`, `qmx.art.presets`, a few numbers each). If the operator wants them to follow them across machines, the daemon needs a small per-user preferences store; no other backend need.

## Lab (operator rulings 2026-10-02; needs docs and backend work)

- **Rename Authoring to Lab** on the rail (docs record Authoring, DEC-0470 / ADR-0026). The Lab merges Authoring, Backtest and ML work; backend/docs refactor to match.
- **Model as a first-class object** (none exists; DEC-0172 only allows weights baked into bot logic), including imported models (ONNX or code from outside) and reuse across mini apps and servers.
- **Model slots** with defaults for entry signal, sizing, regime and risk throttle, all operator-extensible. Today sizing is Book-only (QL-7) and regime/throttle are node MIS/KSA (never read by bots).
- **External compute**: any provider (Colab, AWS, GPU clouds) as execution environments; each run records where it ran and its cost. B-9 says only the controlled machine sees governed/sealed data, so the evidence status of off-machine runs needs a ruling. Vendor choice is GAP-0075.
- **Pair trading, portfolio-level runs, strategy/scenario generator** (GAP-0063, GAP-0085; DEC-0273 defers portfolios).
- **Saved tests, reports, datasets and feature sets as reusable items** (none are Library kinds today, DEC-0271).
- **Pass thresholds and overfit budgets** for sweeps and robustness (GAP-0017/0048/0049).
- **Agents and sub-agent swarms in workflows**: the UI needs where each runs and its live state (QMA refactor pending).

### Lab: what each panel needs from the backend (L11, 2026-10-02)

| Panel | Needs | In docs? |
|---|---|---|
| Runs, Equity, Log | List runs for a subject with procedure, run role, market, measures, state, progress, where it ran; CT-32 series for equity; run console stream | Runs, roles, CT-32: yes (qmb.md B-3/B-4/B-10). "Where it ran" per run: via CT-46 environment ref |
| Sweep grid | Permutation sweep results keyed by market × timeframe (B-12) | Yes; CLI wiring missing (DEC-0286) |
| Scenario builder | Submit a sweep: bot version, markets, pairs, timeframes, parameter ranges from CT-33, costs preset, environment; estimate count and time | Sweep yes; pairs, saved scenarios and estimates: new scope |
| Robustness | Ladder results per run (costs, shuffle, noise, significance, walk-forward), cost tier, state; operator-set pass bars | Procedures yes (B-14); thresholds open (GAP-0048/0049) |
| Compare | Measures for N runs plus what differs; refusal reasons when not comparable | Planning only (T-R5-04) |
| Editor, Inspector | Graph Template draft read/write (editor_draft_head, publish), step settings and code, where each step runs; import a model file, repo folder, notebook | Drafts yes (SCN-0033); import paths: new scope |
| Training, Model slots | Training job progress and curves, split manifest (CT-12), model object, slots (entry, sizing, regime, throttle, custom) | Split yes; model object and slots: new scope |
| Data | Datasets with provider, schema, timezone, freshness, gaps, revision; add data (upload via PUT /artifacts/stage, connect a source, derive) | Dataset fields yes (CT-10/15); derive and connect flows: partly |
| Compute | Environments (CT-46) with kind, hardware, slots used/total, cost, status, evidence eligibility; add an environment (SSH, Colab, cloud GPU) | Environments yes; vendors GAP-0075; Colab and evidence rule for remote runs need a ruling |
| Agents | Quants, agents and sub-agents on the subject with state and environment | Ontology yes (QMA); live tree read model: needed |
| Lab copilot | Per-surface tool list, targets (quants) and attach sources; sessions with history; per-copilot instructions and default model | Product sessions yes (psess); per-surface tool lists: new scope |
| Layouts | None: saved per machine in the browser; optional sync if the operator wants it across machines | — |

### Compute, storage and where agents run (operator, 2026-10-03)

- Operator-managed compute providers: add or remove any VPS, AWS, Colab or GPU cloud; the backend adapts (CT-46 environments, vendors GAP-0075).
- Two kinds of agent work to place: the copilot's own agents, sub-agents and swarms; and workflow agents inside Graph Templates (node editor) that run locally or on a server, including always-on and many-hour jobs. The UI shows where each runs and its live state.
- Storage buckets (e.g. S3, Backblaze B2) for data and artifacts that don't live on the laptop: list, connect, usage, cost.
- Evidence status of runs on remote machines is still open; the UI labels them "exploration only" until ruled (B-9).
- Templates across the app (Lab layouts and workflows, Portfolio, Library, Home): saved, shared and started from; the backend stores them.

