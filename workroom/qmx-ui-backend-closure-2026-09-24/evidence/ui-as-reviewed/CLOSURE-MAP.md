---
name: Codex R1–R9 closure map
sitting: architecture-QMX-UI-2026-09-23
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
status: candidate — not operator-accepted
---

# Closure map

Second amendment after `workroom/qmx-ui-closure-review-2026-09-24/REVIEW.md`. R1/R8 preserved. AD ids stable. Tests unexecuted. Inspect SHA unchanged.

## R1–R9

| ID | Decision | Changed files | Evidence | Remaining risk | Status |
| --- | --- | --- | --- | --- | --- |
| R1 | Home / Copilot / Library / Authoring independent | AD-3; EXPERIENCE-AND-LAYOUT | session dictation | Geometry unfrozen | **closed** (preserved) |
| R2 | One proof `pairing_proof`. HTTP Bearer. WS subprotocol `qmx.pair.<proof>`. Unauthenticated `/pair/*` only. Cookies refused. **Issuance:** Origin never sufficient; QMB confirm or authenticated renew. Journal identity `pairing_record_id` | AD-19; BOOTSTRAP-AND-AUTH; backend-delta AD-3/AD-4/AD-17 | RFC 6455 §10.1; RFC 6750; WHATWG WebSocket; CT-40 auth | pairing HTTP not in code | **closed as candidate** (issuance + J1/J2 custody reconciled 2026-09-24) |
| R3 | Mailbox Envelope persists `product_session_ref`. Pre-ack identity `(producer_id, id)`. `list_mailbox` looks up that pair. Principal equality on send and list | AD-18; CHAT-AND-HISTORY; TRACE-MATRIX | CT-48; lost-ack restart trace; QMA `_ref` law | additive mailbox field is a QMA amend | **closed as candidate** |
| R4 | Keep Epic 60 `PluginManifest.copilot_profile`. Nav `view_ids`. `GRANT_AMBIGUOUS` if ≥2 grants | AD-15, AD-20; VIEW-AND-PACK-CONTRACT; EXAMPLES | kit CONTRACTS §1; epics 60.1 | PackUiRequest still unspecified in code | **closed as candidate** — **no parent amendment** |
| R5 | First Run = `publish_editor_draft` into **local authoring pack** then AD-30 enable. Daemon issues `editor_draft_id`. Export later. CAS `expected_revision` | AD-21; AUTHORING-AND-ML | parent compile-at-enable | local pack roster implementation | **closed as candidate** (J3/J4 bound) |
| R6 | Local daemon possession first; HTTP PUT `/artifacts/stage`; v1 refuse partial; explicit `transfer_artifact` only on recorded reachable TLS; dest `transfer_complete` | AD-22; LIBRARY-AND-ATTACHMENTS | J-UI-09; J5 | byte channel not in code | **closed as candidate** |
| R7 | Starter `originating_product_session_ref` on UI admits; omitted on headless. `queued`→`running` does not kill cancel. Terminal = no-op | AD-23; TRACE-MATRIX | parent JobHandle | field is a proposed JobHandle amend | **closed as candidate** |
| R8 | USER / INHERITED / CANDIDATE tags | DECISIONS-AND-OPEN | Codex R8 | CANDIDATE ≠ operator accept | **closed** (preserved) |
| R9 | Node.js **>=22.12.0 <23.0.0**; bits-ui 2.19.3; pnpm | AD-2; stack; DECISIONS | Vite 8.3 engines | lockfile unexecuted | **closed as candidate** |

## Whole-session rubric

| Area | After amendment |
| --- | --- |
| UX-01 Startup | Candidate contract in BOOTSTRAP-AND-AUTH; native install still later |
| UX-02 Home / platform | Corrected (R1) |
| UX-03 Copilot | Chat contract closed; references via AD-22 |
| UX-04 App / widgets | ActionContext + PackUiRequest |
| UX-05 Library | Verb matrix promoted |
| UX-06 App building | AD-21 transitions |
| UX-07 Graph / code | Draft not runnable |
| UX-08 Charts | AD-17 plus TRACE-MATRIX |
| UX-09 ML | AUTHORING-AND-ML journey |
| UX-10 Trading | Paper scoped; ticket chrome deferred to trading-app sitting |
| UX-11 Operations | dispatchCancel; Home attention |
| UX-12 Settings / previews | Pairing, stage_artifact, xterm preview |
| Headless / mixed | Pass at policy |
| Original layouts | Pass with R1 |
| Parent authority | Preserved; named backend adds, no local override of grants |
| Honesty | CANDIDATE tags; inspect SHA unchanged |

## Backend adds (not this sitting)

See `BACKEND-DEPENDENCIES.md` and backend-delta `DEPENDENCY-MAP.md` plus `CLOSURE-J1-J5.md`. Already planned: Epic 60–65 fields. Proposed amendments: pairing HTTP + WS subprotocol **with Origin-never-sufficient issuance**; first-operator host-control; mailbox `product_session_ref` (**Epic 46.4 delivery**, Epic 41 query name); `list_mailbox`; `cancel_job` + optional `originating_product_session_ref`; artifact HTTP PUT + reachable transfer + `transfer_complete`; daemon-issued drafts + `publish_editor_draft`; `get_pack_ui_request`. **Not** amending Epic 60 `copilot_profile`.

J1–J5 evidence, traces, and deferrals: backend-delta `../architecture-QMX-UI-BACKEND-2026-09-24/CLOSURE-J1-J5.md`.

Post-amendment independent review follows this delta. Remaining risk is implementation of named backend adds, not a second unnamed owner.
