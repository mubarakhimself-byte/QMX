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
