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
| AM-02 | QMA AD-20 Envelope field list; Story 46.4 / FR-Q60 required Envelope members | UI chat cannot survive daemon restart by `psess:` if the field is absent | Additive Envelope / journal field **`product_session_ref`** on the **operator product-chat path**. Quant/machine rows with no product conversation omit it. Principal equality applies **when the field is present**. Seed `send_message` stays legal for `machine` when omitted. Replies inherit. Not a new store. Story 46.4 remains the delivery owner. | AD-7 |
| AM-03 | QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 declaration validator; parent AD-16 complete v1 sqlite additions | Pairing, draft head, transfer ticket, first operator have no named projection | **Named add** of journal projections `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`, **`local_operator`** to that closed list. Still not a new sqlite **class**. Each fold: stream `noun.verb`, ordering `journal_seq`, knowledge-time `as_of` over `recorded_at`, equal-instant ascending `journal_seq`. Live shape: unrevoked pairing rows / draft head pointer / open tickets / single local operator principal plus current `host_control_fp1`. Migrations follow QMA AD-27. | AD-4, AD-9, AD-11, AD-17 |
| AM-04 | QMA AD-17 JobHandle record; parent AD-26 handle vocab; Story 57.3 “vocabulary exactly” (states stay closed) | UI cancel authority has no durable starter session | Optional immutable **`originating_product_session_ref`** at UI admit; omitted on headless. `handle_id` is `job_id`. States unchanged. | AD-8 |
| AM-05 | QMA AD-5 / UI AD-12 three CT-40 families (JSON-RPC WS, HTTP GET, events) | Raw upload bytes cannot travel as a JSON-RPC body; a REST invoke API is forbidden | Authenticated HTTP `PUT /artifacts/stage` is a **byte channel** on the daemon origin, not invoke, not a fourth message family, not a BFF. | AD-9, AD-15 |
| AM-06 | Story 41.4 “daemon never dials in”; QMA loopback default | Remote worker cannot pull laptop loopback | Ticket + dest-audience pull from **recorded reachable TLS** source; `source_unreachable` on loopback-only; dest-authored `transfer_complete` closes the ticket. Daemon never dials in. | AD-9 |
| AM-07 | QMA AD-22 one RefinementProposal type | A builder might store graph drafts in AD-22 staging | **Non-amendment of AD-22.** Drafts use artifact-store bytes + `editor_draft_head` (AM-03). AD-22 stays one type. | AD-11 |
| AM-08 | Epic 41.1 seed query count as closed-and-addable | `list_mailbox` is not in the seed seven | Addable query `list_mailbox` owned by `qma-wire`. Same rule as `facade_search`. | AD-7 |
| AM-09 | Epic 41.1 seed command count as closed-and-addable | cancel, transfer, draft save/publish, transfer complete have no names | Addable commands `cancel_job`, `transfer_artifact`, `transfer_complete`, `save_editor_draft`, `publish_editor_draft`. `stop_run` stays distinct. No JSON-RPC `stage_artifact`. Pair/revoke/TTL are **local host-control**, not these CT-40 names. | AD-8, AD-9, AD-11 |
| AM-10 | QMB CLI `COMMAND_GROUPS` (parent AD-21); QMA AD-24 human-gate list; QMA AD-26 `variable.set` | No process-lifetime door; pairing TTL would otherwise be a wire variable | Add group `host`: `start`, `status`, `stop`, `configure pairing-ttl`, `pair <code>`, `pair revoke --session\|--origin`, `rotate-control`, **`recover-control`**. Human-gate: running-daemon verbs are operator-only via `host_control`. `recover-control` is OS-owner of a **stopped** root and does not present the lost token. **Only** host-control may write `registry:pairing.session_ttl`; CT-40 `variable.set` of that key refuses. | AD-6, AD-17 |
| AM-11 | `authenticate_before_protocol` takes `credential_ref`; secret-surface key list | Browser cannot present a broker ref; raw pairing proof must not be journaled | Browser-paired session: `principal_class=operator` + `pairing_record_id`, **no** `credential_ref`. Proof is a bearer; journal stores `proof_fp1` only. Surface scan is by value class (proofs), not only key spelling. | AD-4, AD-5 |
| AM-12 | Story 41.3 `registry:wire.dedup_window` | Mailbox lost-ack lookup needs journal-lifetime collision | For `send_message` only, same `(producer_id, id)` + different payload hash refuses for **journal lifetime**, not the wire dedup window. Other commands keep Story 41.3. | AD-7 |
| AM-13 | QMA AD-5 three families; AM-05 PUT-only | Machine pull and authenticated renew have no family | Authenticated `POST /pair/renew` is pairing HTTP, not a CT-40 family. Authenticated `GET /artifacts/<fp1>` with transfer ticket is the machine byte pull (AM-06). | AD-5, AD-9, AD-15 |
| AM-14 | QMA conventions `_ref` law (ten named exceptions) | Envelope/handle pointers named `product_session_id` / `originating_psess` fail the parent validator | Use **`product_session_ref`** and **`originating_product_session_ref`**. Do not add those old names to the exception list. ProductSession **own** identity stays `product_session_id`. | AD-7, AD-8 |
| AM-15 | QMA AD-5 single inbound port; QMA AD-15/AD-24; Story 41.4 never unauthenticated bind; human-gate list | First operator cannot use CT-40; a second 8765 bind would break single-port | **Local host-control** under `QMA_DAEMON_ROOT` is a token-gated loopback channel **outside port 8765**. First operator + TTL + pair confirm use that channel. CT-40 still authenticates before protocol. Broker allowlist **not** widened. | AD-17 |
| AM-16 | Epic 41.1 addable queries | PackUiRequest read-back unnamed | Addable query `get_pack_ui_request` keyed by `instance_id` + `availability_revision`. Record the request on the existing plugin-install / instance row (parent AD-16 item 3); not a new sqlite name. | AD-10 |
| AM-17 | Epic 41.1 addable queries | Draft-head reload unnamed | Addable query `get_editor_draft_head` keyed by `editor_draft_id` (authenticated HTTP GET snapshot family). | AD-11 |

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
- Broker allowlist prefixes unchanged (no `cred://operator/`).
- QMA `_ref` exception list unchanged; new pointers use `_ref`.
- Credential-broker allowlist still code, not settings.

## D. What is not an amendment (adoption of planned work)

Live JSON-RPC/HTTP/event serving on `DaemonProcess`, journal sole-writer, mailbox projection fold, `facade_search` HTTP door, GrantRecord hop-compare, and `qmb` headless invoke are **Epic 41–42 / 54 / 55 planned work**. Missing code at `34c148b` is an **adoption gap**, not a new amendment.

## E. Documentation Factory / epics later

This map is the input to the coordinated epics/stories amendment pass. Do not renumber existing epics here. Do not predict a final epic count.
