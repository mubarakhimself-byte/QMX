---
name: UI candidate reconciliations
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
---

# UI candidate change log

Round 1: remaining R2 issuance and reload/cold-start wording. Round 2 (this amendment): joint-review J1–J5 plus small reconciliations. Closed UI findings R1, R3–R9 intent preserved. No chrome, Svelte, or storyboard redesign.

Workspace edited: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`.

## Round 1 (R2 issuance)

| File | Change |
| --- | --- |
| `BOOTSTRAP-AND-AUTH.md` | Removed Origin-only auto-approve. Bound QMB confirm or `/pair/renew`. |
| `ARCHITECTURE-SPINE.md` | UI AD-19 Rule: Origin never issues a session. |
| `CHAT-AND-HISTORY.md` / `TRACE-MATRIX.md` | Reload vs cold start. |
| `CLOSURE-MAP.md` / `BACKEND-DEPENDENCIES.md` / `CHANGE-IMPACT.md` / `START-HERE.md` / `DECISIONS-AND-OPEN.md` | Issuance + mailbox owner Epic 46.4. |

## Round 2 (J1–J5)

| File | Change |
| --- | --- |
| `BOOTSTRAP-AND-AUTH.md` | Proof is `pairing_proof`; journal identity `pairing_record_id`. Browser session has no `credential_ref`. First operator is host-control. Confirm once / `already_issued` / rotate / expiry closes WS. Status never prints proofs. |
| `ARCHITECTURE-SPINE.md` | AD-15 `get_pack_ui_request`; AD-18 `product_session_ref` + principal equality; AD-19 host-control + `pairing_proof`; AD-21 daemon-issued draft + `publish_editor_draft`; AD-22 reachable TLS + `transfer_complete`; AD-23 optional `originating_product_session_ref`. |
| `CHAT-AND-HISTORY.md` | Envelope/payload/query field `product_session_ref`. Principal equality on send. Reconnect uses `pairing_proof`. ProductSession own id stays `product_session_id`. |
| `AUTHORING-AND-ML.md` | Daemon sole durable `editor_draft_id` issuer; first save omits id; `publish_editor_draft`. |
| `VIEW-AND-PACK-CONTRACT.md` | Snapshot read-back `get_pack_ui_request` by `instance_id` + `availability_revision`. |
| `LIBRARY-AND-ATTACHMENTS.md` | Reachable TLS prerequisite; `source_unreachable`; dest `transfer_complete`; ticket audience. |
| `TRACE-MATRIX.md` | Pairing proof, mailbox `_ref`, cancel optional field, transfer reachability, shell vs provider. |
| `BACKEND-DEPENDENCIES.md` | J1–J5 named contracts. |
| `CLOSURE-MAP.md` | R2–R7 rows reconciled; pointer to backend `CLOSURE-J1-J5.md`. |
| `CHANGE-IMPACT.md` | Host verbs, transfer complete, draft publish, pack-ui query. |
| `START-HERE.md` | J1–J5 status. |

Not edited: `EXPERIENCE-AND-LAYOUT.md`, `DESIGN.md`, `COMPONENT-CONTRACTS.md`, `JOURNEYS.md`, `EXAMPLES.md`, `DELIVERY-AND-QA.md`. Historical `reviews/` left as prior evidence.
