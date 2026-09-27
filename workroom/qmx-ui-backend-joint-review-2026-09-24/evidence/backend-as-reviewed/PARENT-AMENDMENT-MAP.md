---
name: Parent-amendment map
sitting: architecture-QMX-UI-BACKEND-2026-09-24
status: candidate — not operator-accepted
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
---

# Parent-amendment map

Every conflict with inherited contracts is named here. Nothing in the backend-delta spine silently overrides a parent, kit, QMA, or planned epic.

Amendments are **proposed**. They bind this sitting’s builders only after operator acceptance and the later Documentation Factory / epics pass.

## A. Named amendments (accept or this sitting is inconsistent)

| ID | Inherited contract | Conflict if ignored | Proposed amendment | Local AD |
| --- | --- | --- | --- | --- |
| AM-01 | QMA AD-5, AD-15, AD-24 transport custody; Epic 41 Story 41.4 “never offers an unauthenticated bind”; credential_ref authenticates before protocol bytes | Browser cannot present `credential_ref` from JS; CORS OPTIONS on PUT/renew would be illegal if the carve-out is POST-only | Unauthenticated HTTP **only** for `POST /pair/start`, `POST /pair/confirm`, and CORS `OPTIONS` on daemon HTTP routes that declare CORS. OPTIONS never issues a session, never upgrades WS, never returns bytes. `POST /pair/renew` is authenticated. Machine clients still use `credential_ref`. | AD-5 |
| AM-02 | QMA AD-20 Envelope field list; Story 46.4 / FR-Q60 required Envelope members | UI chat cannot survive daemon restart by `psess:` if the field is absent | Additive Envelope / journal field `product_session_id`. Replies inherit. Not a new store. Story 46.4 remains the delivery owner. | AD-7 |
| AM-03 | QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 declaration validator; parent AD-16 complete v1 sqlite additions | Pairing, draft head, transfer ticket have no named projection; “not a new class” does not satisfy Story 42.2 | **Named add** of journal projections `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket` to that closed list. Still not a new sqlite **class**. Each declares a fold contract (live unrevoked rows / head pointer / open tickets). Migrations follow QMA AD-27. | AD-4, AD-9, AD-11 |
| AM-04 | QMA AD-17 JobHandle record; parent AD-26 handle vocab; Story 57.3 “vocabulary exactly” (states stay closed) | UI cancel authority has no durable starter session | Additive immutable `originating_psess` written at admit. `handle_id` is `job_id`. States unchanged. Nested Epic 63 children store their own field at child admit. | AD-8 |
| AM-05 | QMA AD-5 / UI AD-12 three CT-40 families (JSON-RPC WS, HTTP GET, events) | Raw upload bytes cannot travel as a JSON-RPC body; a REST invoke API is forbidden | Authenticated HTTP `PUT /artifacts/stage` is a **byte channel** on the daemon origin, not invoke, not a fourth message family, not a BFF. | AD-9, AD-15 |
| AM-06 | Story 41.4 “daemon never dials in” | Remote artifact placement needs a data plane | `transfer_artifact` records a ticket; the destination **pulls** as `machine` principal. Daemon remains the single inbound listener. | AD-9 |
| AM-07 | QMA AD-22 one RefinementProposal type | A builder might store graph drafts in AD-22 staging | **Non-amendment of AD-22.** Drafts use artifact-store bytes + `editor_draft_head` (AM-03). AD-22 stays one type. | AD-11 |
| AM-08 | Epic 41.1 seed query count as closed-and-addable | `list_mailbox` is not in the seed seven | Addable query `list_mailbox` owned by `qma-wire`. Same rule as `facade_search`. | AD-7 |
| AM-09 | Epic 41.1 seed command count as closed-and-addable | `cancel_job`, `transfer_artifact`, QMB pair, draft CAS have no names | Addable commands `cancel_job`, `transfer_artifact`, `confirm_pair`, `revoke_pair`, `save_editor_draft`. `stop_run` stays a different verb. There is **no** JSON-RPC `stage_artifact`. | AD-6, AD-8, AD-9, AD-11 |
| AM-10 | QMB CLI `COMMAND_GROUPS` (parent AD-21); QMA AD-24 human-gate list | No process-lifetime door; pair/revoke would be ungated | Add group `host`: `start`, `status`, `stop`, `pair <code>`, `pair revoke --session|--origin`. Add `confirm_pair` and `revoke_pair` to the QMA AD-24 operator-only human-gate list. Not a sixth COMP. | AD-6 |
| AM-11 | `authenticate_before_protocol` takes `credential_ref`; `FORBIDDEN_SECRET_SURFACE_KEYS` includes `token`/`bearer` as JSON keys | Builder might pass `pairing_session_id` to `parse_credential_ref`, or put the proof under a `bearer` JSON key | Pairing is a pre-step. After table match the daemon mints `AuthenticatedWireSession` with the **copied operator** `credential_ref`. `pairing_session_id` is not a CredentialRef. HTTP `Authorization: Bearer pairing:<id>` is a header, not a scanned JSON key. JSON traces use key `pairing_session_id`. | AD-5 |
| AM-12 | Story 41.3 `registry:wire.dedup_window` | Mailbox lost-ack lookup needs journal-lifetime collision | For `send_message` only, same `(producer_id, id)` + different payload hash refuses for **journal lifetime**, not the wire dedup window. Other commands keep Story 41.3. | AD-7 |
| AM-13 | QMA AD-5 three families; AM-05 PUT-only | Machine pull and authenticated renew have no family | Authenticated `POST /pair/renew` is pairing HTTP, not a CT-40 family. Authenticated `GET /artifacts/<fp1>` with transfer ticket is the machine byte pull (AM-06). | AD-5, AD-9, AD-15 |

## B. Already-named kit/UI amendments this sitting reuses (do not re-author)

| Inherited named amend | Owner | This sitting |
| --- | --- | --- |
| parent AD-8 `app_instance_id` optional on authoring | Epic 60 / DEC-0463 | reuse; adoption gap at inspect |
| parent AD-24 `caller_kind` | Epic 60 / DEC-0464 | reuse; until present, UI still refuses pack invoke |
| selected-ref kind `instance_id` | Epic 60 | reuse |
| `PluginManifest.copilot_profile` | Epic 60 Story 60.1 | **no parent amendment to move it into PackUiRequest** |
| JobHandle `later_commands` no-ops | Epic 57 / parent AD-26 | reuse for terminal cancel |

## C. Explicit non-amendments

- No sixth COMP, no `qma-cli`, no COMP-UI.
- No new CT.
- No `ui_view` contribution point.
- Envelope `instance_id` remains required on invoke.
- Mailbox MessageKind / DeliveryState closed sets unchanged.
- JobHandle states unchanged (`succeeded` / `awaiting_approval` still refused).
- Cookie session still refused.
- `localStorage` still forbidden for pairing proof.
- json-render / MCP Apps still adapters, not authority.
- QMA AD-22 still one RefinementProposal record type.
- Credential-broker allowlist still code, not settings.

## D. What is not an amendment (adoption of planned work)

Live JSON-RPC/HTTP/event serving on `DaemonProcess`, journal sole-writer, mailbox projection fold, `facade_search` HTTP door, GrantRecord hop-compare, and `qmb` headless invoke are **Epic 41–42 / 54 / 55 planned work**. Missing code at `34c148b` is an **adoption gap**, not a new amendment.

## E. Documentation Factory / epics later

This map is the input to the coordinated epics/stories amendment pass. Do not renumber existing epics here. Do not predict a final epic count.
