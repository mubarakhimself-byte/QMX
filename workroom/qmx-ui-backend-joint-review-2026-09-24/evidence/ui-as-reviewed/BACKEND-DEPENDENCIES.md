---
name: Backend dependencies for a later architecture sitting
sitting: architecture-QMX-UI-2026-09-23
status: candidate list — not an epic backlog
---

# Backend dependencies

UI architecture only. Do not start the backend-delta sitting from here. Treat existing epics as **planned requirements**, not implemented product.

## Already planned — reuse, do not duplicate

| Need | Plan anchor | UI use |
| --- | --- | --- |
| Optional `PluginManifest.copilot_profile` | Epic 60 / FEAT-0058 | Host reads the sibling field. PackUiRequest does **not** replace it |
| Authoring `app_instance_id` optional; `selected_refs.instance_id`; `caller_kind` | Epic 60 | Home chat vs invoke |
| Daemon JSON-lines / `failure_class` | Epic 61 / FEAT-0059 | Ops chrome |
| Host retry `none`/`read` | Epic 62 / FEAT-0060 | UI Retry |
| Nested Mission JobHandle | Epic 63 / FEAT-0061 | Nested cancel = child handle |
| Instance `health()` / listing | Epic 64 / FEAT-0062 | Home attention |
| Thin kit proofs | Epic 65 / FEAT-0063 | Not UI e2e |
| Live CT-40 server, auth, idempotency | QMA Epics 41–42 (adoption gap at `34c148b`) | Pairing sits **after** that live server |

## Proposed parent / QMA amendments (new names)

These are **not** in the inspected epic files by exact name. A later BMAD architecture sitting must classify reuse vs amendment. **Do not rewrite the epic backlog in this sitting.**

| Contract | Owner direction | Affected planned work if accepted |
| --- | --- | --- |
| Pairing HTTP `/pair/*` + `pairing_session_id` + WS subprotocol `qmx.pair.<id>` | COMP-QMA-DAEMON + COMP-QMB `qmb host pair` | New vs Epic 41 auth adoption. **Issuance:** Origin never sufficient; QMB confirm or authenticated `/pair/renew`. Named carve-out to unauthenticated bind (backend-delta AM-01). Do not weaken CT-40 pre-protocol law outside `/pair/start|confirm` |
| Mailbox Envelope persists `product_session_id`; `list_mailbox` lookup by `(producer_id, wire id)` | COMP-QMA-WIRE vocab + COMP-QMA-DAEMON delivery | Additive on CT-48. **Delivery owner is Epic 46 / Story 46.4.** Epic 41 owns the addable query name. Epic 42 owns journal/fold. Not a new store |
| `cancel_job` + JobHandle `originating_psess` at admit | COMP-QMA-WIRE + DAEMON JobHandle | Touches Epic 57 handle identity; Epic 63 nested child handles |
| HTTP PUT `/artifacts/stage` + `transfer_artifact`; v1 refuse partial | COMP-QMA-DAEMON | New byte channel; reuse artifact register |
| Local authoring pack enable as first Run bridge | existing AD-30 enable | No new enable machine; export remains later AD-18 |

## Explicit non-amendments

- **No** parent amendment to move `copilot_profile` inside `pack_ui_request`. Epic 60.1 keeps the manifest field.
- **No** sixth COMP, new CT, or UI grant store.
- Envelope `instance_id` stays required on invoke.

## Suggested later BMAD sitting

Fresh architecture session: backend-delta packet from this file + `CLOSURE-MAP.md` + parent spines + `epics-PACK-AND-GRANT-2026-09-23.md` + QMA epics 41–42, 57. Classify each row reuse / planned / adoption gap / amendment. Hold only stories whose **contract** conflicts; let independent epics continue.
