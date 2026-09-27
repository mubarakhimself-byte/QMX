---
review: adversarial-spine
target: architecture-QMX-UI-BACKEND-2026-09-24
attack_surface:
  - ARCHITECTURE-SPINE.md (local AD-1..AD-16)
  - PAIRING-AND-ADMISSION.md
  - MAILBOX-AND-DELIVERY.md
  - CANCEL-AND-HANDLES.md
  - ARTIFACTS-AND-TRANSFER.md
  - PARENT-AMENDMENT-MAP.md
  - PACK-UI-AND-AUTHORING.md
  - HOST-LIFECYCLE.md
  - PROVIDER-AND-COMPAT.md
date: 2026-09-24
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
lens: 'Two factory units, every local AD, still incompatible on shared-data shapes, entity ownership, and state-mutation paths. Credit closed Origin-only issuance. Flag remaining holes only. No spine rewrite. No implementation.'
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Adversarial review — QMX UI backend-delta spine

## Method

Build **two factory units** one level down from this sitting (stories / builders). Both obey every local AD (AD-1..AD-16) as written, plus the companions the ADs name, plus inherited parent / kit / QMA / UI law the spine already binds. They still cannot assemble.

A pair is a hole only when **both readings are literal**. Companion sentences that contradict a local AD are residue, not a second legal unit. Closed UI R2 (Origin-never-sufficient issuance) is not reopened. Inspect types at `34c148be` are evidence, not delivery.

This file does not edit the spine.

## Verdict

**Return remaining holes. Do not treat named amendments as factory-unambiguous.**

AD-3 issuance, AD-5 carve-out, cookie refusal, mailbox-not-invoke, starter-only cancel slogan, PUT-then-transfer, and “drafts are not RefinementProposal” all hold at the slogan layer. What remains is that each closed noun still has an **unbound joint**:

- what object `AuthenticatedWireSession.credential_ref` *is* after pairing / renew / revoke
- which of two live `pairing_session_id`s a WebSocket is bound to, and what revoke does to that socket
- whether `product_session_id` / `(producer_id, wire_id)` / payload hash live on Envelope fp1, on the journal row, or on the `list_mailbox` DTO — and how that query is encoded
- whether cancel authority is `JobHandle.owner`, `originating_psess` principal, or pairing `CredentialRef`, and whether `handle_id` is `job_id`
- where the destination **pulls** bytes, with which proof, against which ticket
- whether `editor_revision` is artifact `fp1`, who writes the artifact store versus `editor_draft_head`, and which command/PUT mutates them

`CLOSURE-EVIDENCE.md` “R2 closed as candidate” is true for Origin-only issuance. It is false as “two stories can share a daemon.” Tests remain unexecuted. Inspect SHA is unchanged.

| Axis | Closed by this sitting? | Remaining hole |
| --- | --- | --- |
| Pairing issuance | **Yes** — AD-3; Origin never sufficient | Table row vs `AuthenticatedWireSession` vs `credential_ref`; QMB confirm IPC |
| Two ids after renew | **Partial** — old WS/HTTP stay; SPA stores latest | Which id the session object carries; revoke of one id vs shared mapped ref |
| Mailbox delivery owner | **Yes** — Epic 46.4 / AM-02 / AM-08 | Envelope field vs journal extras vs HTTP query shape |
| Cancel starter-only | **Yes** — AD-8; not `stop_run`; not observer | `originating_psess` vs `JobHandle.owner`; `handle_id` vs `job_id`; two cancel doors |
| Artifact ingest | **Yes** — PUT then explicit transfer | Ticket vs store vs pull URL/auth; pull path absent from AD-15 family list |
| Draft ≠ AD-22 | **Yes** — AM-07 | `editor_draft_head` vs artifact store vs AD-9 PUT; `editor_revision` vs `fp1` |

---

## Closures that hold (do not reopen)

- Remembered Origin never issues a `pairing_session_id`. Path 1 is QMB confirm of **that** pending; path 2 is authenticated `/pair/renew`. Typed URL second tab is path 1.
- Cookies / `Set-Cookie` / `localStorage` as pairing proof are refused. Browser proof is `pairing_session_id` (HTTP Bearer + WS subprotocol). Machine/worker proof stays Story 41.4 `credential_ref`.
- Unauthenticated HTTP is only `POST /pair/start`, `POST /pair/confirm`, and `OPTIONS` of those two. Those paths never upgrade to WebSocket and never accept family messages.
- `send_message` is mailbox, not `InvocationEnvelope`, not instance. Delivery owner is Epic 46 / Story 46.4. Epic 41 owns the query name. Epic 42 owns journal/fold.
- `cancel_job` is not `stop_run` and not a second invoke. Observation is not UI cancel authority. JobHandle **states** stay closed. Nested children do not splice graphs and do not union grants.
- PUT `/artifacts/stage` is a byte channel, not REST invoke, not JSON-RPC body. Interrupted v1 PUT deletes incomplete; no RFC 9110 partial PUT. Remote placement is explicit `transfer_artifact`; destination pulls; daemon never dials in; no silent local fallback.
- PackUiRequest is not a grant and does not nest `copilot_profile`. Drafts are not QMA AD-22 `RefinementProposal`. First Run is local authoring pack enable (parent AD-30), not a second enable machine.
- No sixth COMP. No new CT. No UI BFF. No Documentation Factory from this sitting.

Inspect honesty in the companions is accurate: `/pair/*`, `list_mailbox`, `cancel_job`, PUT path, `transfer_artifact`, `originating_psess`, `product_session_id`, `qmb host` are **absent** at `34c148be`. `authenticate_before_protocol` is a shape gate on `credential_ref`. `parse_credential_ref` accepts any non-empty opaque string that does not look like `secret=` / `password=` / `token=` / `bearer ` — including `pairing:<id>`. That last fact is why AM-11 exists, and why AM-11 is still not enough.

---

## Two units (both AD-legal)

Shared, both units:

- Svelte static origin ≠ `:8765`. Probe loopback or recorded HTTPS. Never retarget remote → local.
- `qmb host start|status|stop|pair|…` is the privileged door. Browser JS does not spawn Python.
- AD-3 issuance exactly. CORS exact paired Origin on authenticated HTTP. `credentials: 'omit'`. Cookies refused.
- After table match, daemon constructs `AuthenticatedWireSession(credential_ref=<internal mapped ref>, principal_class=operator)` and then accepts protocol bytes. Browser never presents `cred://` as login. `pairing_session_id` is not passed to `parse_credential_ref`.
- Renew mints a **new** id; v1 does **not** require revoking the old; two live ids until TTL or revoke. SPA stores the latest id. Already-open WS that offered the previous `qmx.pair.<id>` stays until detach. In-flight HTTP with the previous Bearer still authenticates.
- `initialize` must not bind a `producer_id` already live on another connection.
- `send_message` persists `product_session_id` on the Envelope at accept. Replies inherit. Collision: same `(producer_id, wire_id)` + same hash → prior result; different hash → refuse for journal lifetime. `list_mailbox` is an addable HTTP GET query with the two argument forms named in AD-7.
- `cancel_job` fields `{handle_id, logical_run_id, attempt_id, command_id, expected_state}`. `originating_psess` immutable at admit. `JobHandle.owner` remains Quant `ActorId`. Headless QMB cancel stays Story 36.5.
- PUT `/artifacts/stage` then `transfer_artifact`. Destination pulls as `machine`. Completeness is daemon hash + byte count.
- Draft bytes in the existing artifact store; head in `editor_draft_head`; CAS `expected_revision`; not AD-22 staging.

They still ship different daemons.

### Unit A — row-scoped bind, Envelope-as-snapshot, job_id cancel, GET-by-fp1 pull, fp1-as-revision

**Pairing table vs session vs ref.** QMB `host pair <code>` appends a `pairing.pending.confirmed` journal event by dropping a privileged file under `QMA_DAEMON_ROOT` (QMB never imports the daemon package). `/pair/confirm` folds that event, mints `pairing_session_id`, and writes a **new** internal `CredentialRef` per row (`cred://telemetry/operator-bind/<pending_id>`, allowlist-legal). Renew copies operator+Origin and **mints another** `CredentialRef`. `AuthenticatedWireSession.credential_ref` is that row’s ref. Two live ids ⇒ two wire identities. Traces emit `credential_ref` only (AD-4: “Values never appear in traces”). Revoke `--session <old>` sets `revoked_at` on that row; the next family message on the old WS re-reads the table and refuses (T-P-04 / T-BE-04 over PAIRING “stays until detach,” which Unit A reads as the *renew* case only).

**WS after renew.** SPA stores the new id and opens a **second** WebSocket with `qmx.pair.<new>`. The old socket remains until detach, carrying the old mapped ref and the old `producer_id`. New socket cannot reuse that live `producer_id` (AD-14). HTTP GET/PUT with either Bearer succeeds until the corresponding row is revoked. Occupancy and mailbox pre-ack are per `producer_id`, so the tab now owns two producers until it detaches the old socket.

**Mailbox.** `product_session_id` is a **required** Envelope field, present in `to_payload()`, **included in Envelope fp1** (not added to `ENVELOPE_FP1_EXCLUDED_FIELDS`). `(producer_id, wire_id)` and payload hash live only on the journal `message.*` row. Payload hash is Envelope identity fp1. `list_mailbox` is `GET /queries?type=list_mailbox&product_session_id=psess:H` (and optional `producer_id` / `wire_id` query params). Response is `Envelope.to_payload()` list. Full snapshot does **not** echo the wire pair. Pre-ack form uses journal extras internally, returns the Envelope or empty. Old journal rows without the field fail `parse_envelope` after AM-02 (required).

**Cancel.** `handle_id` **is** `job_id`. `originating_psess` is copied from the invoke envelope’s `product_session_id` at JobHandle admit. Authority: the connection’s `AuthenticatedWireSession.credential_ref` must equal the internal ref recorded on that `psess:` row. `expected_state` is inside the hashed parent-AD-29 payload; a queued→running change of last-queried state cannot reuse `command_id` unless the bytes match. Nested child copies the parent’s `originating_psess`. `JobHandle.cancel` in-process is the implementation of `cancel_job` after that check.

**Transfer.** `transfer_artifact` writes `artifact_transfer_ticket` `{fp1, destination_placement}`. Destination worker `GET /artifacts/{fp1}` with Story 41.4 `credential_ref` + `principal_class=machine`. No pull token. Ticket is an authorization row checked on that GET. Unit A treats this GET as AD-15 “authenticated HTTP GET snapshots” with a byte body. Same complete hash reuses the artifact-store object. Ticket remains valid until dest reports complete; retry is the same GET.

**Drafts.** Save = PUT `/artifacts/stage` of the draft bytes, then a CAS mutate of `editor_draft_head` with `expected_revision` = last fp1. `editor_revision` **is** that fp1. Client mints `editor_draft_id` (AUTHORING create-draft); daemon persists it on first successful CAS. Failed CAS leaves an orphan complete artifact. Draft blobs are ordinary `complete` artifacts (Library may list them as ArtifactHits; AD-11 does not forbid it). Publish copies those bytes into the local authoring pack.

### Unit B — operator-scoped bind, journal-join snapshot, opaque handle_id, ticket pull, daemon-minted drafts

**Pairing table vs session vs ref.** QMB `host pair` is a privileged loopback HTTP POST to an authenticated control path using the OS-user’s existing operator `credential_ref` (not `/pair/*`; machine/operator Story 41.4). Confirm copies **that same** `CredentialRef` onto the pairing row. Renew copies it again. Every live `pairing_session_id` for that Origin+operator maps to **one** `AuthenticatedWireSession.credential_ref`. Traces emit **both** `credential_ref` and `pairing_session_id` (PAIRING §7 “may also name `pairing_session_id` as that key”; spine logging: session ids are not secrets). Revoke `--session <old>` marks the old row; the mapped ref is still valid via the new row. An already-open WS that offered `qmx.pair.<old>` **stays until detach** even after that revoke, because PAIRING’s stay-until-detach sentence is not scoped to renew-only and the session object has no pairing-id field to re-check. Occupancy stays one `producer_id` per tab: the tab reuses the same initialize on the old socket; HTTP after renew uses the new Bearer against the same mapped ref.

**WS after renew.** SPA stores the latest id for **new** HTTP/WS. It does not open a second socket. The live WS continues with the old subprotocol proof (already accepted at upgrade). `producer_id` unchanged. Clone tab with the copied **old** id is existing proof (AD-14) and reconnects on that old id; initialize assigns a new `producer_id` if the original is live.

**Mailbox.** `product_session_id` is additive / optional on `parse_envelope`, **excluded from Envelope fp1** (same set as `correlation_id`). Originating `(producer_id, wire_id)` and payload hash are journal extras **and** echoed on every `list_mailbox` row. Payload hash is the WireEnvelope payload bytes (not Envelope fp1). `list_mailbox` is `GET /mailbox/{product_session_id}` with `Content-Type: application/json` query document in a `X-QMA-Query` header for the pre-ack triple (GET with a JSON object; no query-string id, matching the artifact “no query-string id” spirit). Response row: `{envelope, producer_id, wire_id, payload_hash, delivery_state, msg_id}`. Old journal rows without `product_session_id` are omitted from session snapshots (fold-by-field), not parse failures.

**Cancel.** `handle_id` is a **new opaque id** on the durable `task_graph_state` row; snapshots expose `handle_id` and `job_id` as different fields. `originating_psess` is the `psess:` selected on the admitting connection (not necessarily an envelope field). Authority: pairing-row **operator principal string** equals `product_session.principal` (not `credential_ref`). `expected_state` is advisory; omitted from the command_id hash so queued→running reuses `command_id` (AD-8 literal). Nested child stores the starter of **that child**: if the nested invoke mints/uses another `psess:`, the child handle’s field differs from the parent. `cancel_job` records a journal command and `later_commands`; in-process `JobHandle.cancel` remains the QMB Story 36.5 door and does **not** consult `originating_psess`.

**Transfer.** `transfer_artifact` returns `{fp1, ticket_id, pull_token}`. Ticket projection holds dest placement + token hash. Destination pulls `GET /artifacts/pull?ticket=<pull_token>` as `machine` (token is not a pairing id; query-string is the ticket, not an artifact id). Machine `credential_ref` must match the ExecutionEnvironment’s declared worker ref **and** the token must match. AD-15 did not name this path; Unit B still calls it authenticated HTTP GET. JSON-RPC byte bodies remain unused. Interrupted pull deletes dest bytes; ticket stays redeemable until dest-complete or operator revoke. PUT reuse of same hash does not mint a new ticket.

**Drafts.** Daemon mints `editor_draft_id` on first save; client-local id is a hint and is rewritten. Save = PUT `/artifacts/stage` (possession) **then** command `editor.draft.save {editor_draft_id, fp1, expected_revision}` where `editor_revision` is a **second** hash stored on the head (not `fp1`, not a Workbench kind). Library facade **excludes** these blobs (not a Workbench AD-3 kind; not AD-22). CAS failure after PUT is typed conflict; head unchanged; blob may remain as an unreferenced complete object. Publish cites `fp1` into the local pack contribution manifest rather than copying bytes. Two restored clients: second save refuses until reload of **head hash**, which is `editor_revision`, not the PUT fp1.

### Where they cannot assemble

| Joint | Unit A | Unit B | Shared-data / owner clash |
| --- | --- | --- | --- |
| Internal `CredentialRef` | New ref per pairing row | One operator OS ref copied onto every row | `AuthenticatedWireSession` identity after renew; traces; who is “the operator” |
| Two live ids → WS | Second WS, second `producer_id`, old socket re-checked on revoke | Same WS, same `producer_id`, stay-until-detach even after `--session` revoke of the offered id | Occupancy; pre-ack pair; revoke of one id |
| Trace keys | `credential_ref` only; pairing ids omitted (AD-4) | `credential_ref` **and** `pairing_session_id` (PAIRING §7 / logging table) | AM-11 vs AD-4 |
| QMB confirm mutation | Journal file-drop under `QMA_DAEMON_ROOT` | Privileged loopback HTTP with OS `credential_ref` | Two writers of `pairing_pending.confirmed_at` |
| Envelope fp1 | `product_session_id` **in** identity | `product_session_id` **excluded** | Same bytes, two fingerprints; collision domain |
| Journal extras vs DTO | Wire pair not on full snapshot | Wire pair + hash on every row | UI lost-ack cannot query Unit A’s full snapshot |
| Payload hash | Envelope fp1 | WireEnvelope payload bytes | Same pair, “same hash” vs “different hash” |
| `list_mailbox` HTTP | `/queries?type=…` query-string | `/mailbox/{id}` + JSON header | Query door; GET encoding |
| Old mailbox rows | Parse fail (required field) | Skip (fold-by-field) | Rebuild after AM-02 |
| `handle_id` | `= job_id` | Opaque sibling of `job_id` | `cancel_job` argument |
| Cancel authority | Mapped `credential_ref` == session bind | Principal **string** == `product_session.principal` | After renew, Unit A’s new ref cannot cancel jobs admitted under the old ref |
| `expected_state` | Hashed (AD-29 collision) | Advisory (AD-8 queued→running) | Repeat `command_id` bytes |
| Nested `originating_psess` | Inherit parent | Child starter’s own `psess:` | Epic 63 child cancel |
| Second cancel door | `JobHandle.cancel` **is** `cancel_job` | `JobHandle.cancel` is QMB-only, skips `originating_psess` | Two mutation paths on one handle |
| Pull URL | `GET /artifacts/{fp1}` + machine ref | `GET /artifacts/pull?ticket=` + token + machine ref | Ticket is authz row vs bearer |
| Pull vs AD-15 | Byte GET is a “snapshot” | Named extra GET; still not a fourth family by slogan | Family list vs data plane |
| `editor_revision` | **Is** artifact fp1 | Second hash on the head | CAS `expected_revision` |
| `editor_draft_id` | Client-minted | Daemon-minted; client id rewritten | Two owners of the draft entity |
| Draft visibility | ArtifactHits legal | Facade-excluded | Library row for a working copy |
| Publish | Copy bytes into pack | Cite fp1 in manifest | Enable-time bytes vs dangling fp1 |
| Save failure order | PUT then CAS (orphan blob) | CAS then bind (or typed conflict, unreferenced blob) | Artifact store vs head pointer |

Neither unit auto-approves Origin, sets a cookie, routes chat through invoke, maps cancel to `stop_run`, uses RefinementProposal as the editor store, or dials out from the daemon. That is the point: the closed pairs stay closed, and the slice still forks.

---

## Remaining holes (only)

### H-PAIR — Pairing table, `AuthenticatedWireSession`, and `credential_ref` are three objects with no join key

AD-4 row: `pairing_session_id`, Origin, operator principal, internal `CredentialRef`, times, `pending_id` / `renewed_from`.

AD-5 / AM-01 / AM-11: after table match, mint `AuthenticatedWireSession(credential_ref=<internal mapped ref>, principal_class=operator)`. `pairing_session_id` is **not** a `CredentialRef` and must not be passed to `authenticate_before_protocol` / `parse_credential_ref`.

Inspect `AuthenticatedWireSession` (`qma-wire` `auth.py`) has exactly `credential_ref`, `principal_class`, `authenticated_before_protocol`. It has **no** `pairing_session_id`, **no** Origin, **no** row id. Inspect `parse_credential_ref` will **accept** `pairing:<id>` as an opaque ref (it only rejects secret-shaped prefixes). AM-11 closes the “pass the Bearer to `parse_credential_ref`” trap only if the builder reads AM-11. The type system will not.

Unbound, both AD-legal:

1. **What is the mapped ref?** PAIRING table says “internal `CredentialRef` (never sent to the browser).” HOST-LIFECYCLE says QMB pair confirms “operator principal + internal CredentialRef.” Allowlist is `cred://models|inference|compute|sandbox|corpus|knowledge|telemetry/`. There is no operator-login scheme. Unit A mints a telemetry-namespaced synthetic per row. Unit B reuses one OS-store operator ref. After renew, Unit A has two operator identities; Unit B has one.
2. **Does renew copy the ref or mint?** PAIRING: new id “bound to the same Origin + operator”; renewal rows cite `renewed_from`. “Same operator” is not “same `CredentialRef`.”
3. **Who writes `confirmed_at`?** Spine mermaid: QMB never imports the daemon. HOST: QMB pair “does not issue the browser token.” No IPC, no control socket, no journal verb is named. Two owners of `pairing_pending`.
4. **Trace keys contradict.** AD-4: “Values never appear in traces.” Spine logging: “Pairing codes and session ids are not secrets.” PAIRING §7: traces “keep using `credential_ref` as today. They **may also** name `pairing_session_id` as that key.” AM-11: “JSON traces use key `pairing_session_id`.” Unit A omits pairing ids (AD-4). Unit B emits them (AM-11 / §7 / logging). Both are literal.
5. **`/pair/renew` OPTIONS.** AD-5 carve-out is OPTIONS of start/confirm only. Browser CORS preflight for authenticated `/pair/renew`, GET snapshots, and PUT `/artifacts/stage` is an OPTIONS with `Access-Control-Request-Headers: Authorization`. Unit A treats those OPTIONS as unauthenticated CORS (otherwise the SPA cannot call them). Unit B refuses OPTIONS without Bearer (AD-5 letter: every other HTTP path authenticates). The SPA dies on preflight or the carve-out silently grows.

**Required bind.** One sentence each: (a) mapped `CredentialRef` grammar and whether renew copies it; (b) `AuthenticatedWireSession` carries pairing-row id **or** every post-upgrade check re-reads the table by the offered id; (c) QMB confirm’s one mutation path; (d) traces contain pairing ids or they do not; (e) OPTIONS on authenticated routes are the CORS preflight carve-out or they are not.

### H-WS-RENEW — Two live `pairing_session_id`s; the session object cannot say which one the WS used

PAIRING §3 / §7 (post-amendment): v1 does not revoke on renew; SPA stores latest; already-open WS stays; in-flight HTTP with the previous Bearer still authenticates. WHATWG echoes **one** protocol (`qmx.ct40.v1`); daemon inspects the offered list at **upgrade**.

Unbound:

1. **Live WS after `--session` revoke of the offered id.** T-P-04 / T-BE-04: revoked proof → refuse CT-40. PAIRING stay-until-detach is written in the two-live-ids paragraph (renew). Unit A re-checks the table per message and kills the old socket. Unit B leaves it up because the session object has no pairing id and the mapped ref still exists on the new row. A clone tab holding the revoked id in `sessionStorage` then reconnects: Unit A refuses; Unit B may still map via operator-scoped ref if it mistakenly treats the mapped ref as login (AM-11 forbids that for *browser* proof, but the already-authenticated socket is not presenting proof again).
2. **Producer occupancy after renew.** AD-14: initialize must not bind a live `producer_id`. Unit A’s “open a second WS with the new id” creates a second producer for one chrome tab (UI AD-24 is one live `producer_id` **per tab**). Unit B’s “keep the old WS” obeys cardinality and ignores the stored latest id until the next full reconnect. Both claim AD-14.
3. **Which Bearer does PUT use after renew while the old WS is up?** SPA stores latest ⇒ new id. Completeness / mailbox commands on the old WS still run as the old mapped ref (Unit A) or the same ref (Unit B). Artifact register + chat admit can disagree on “who” wrote them.

**Required bind.** Renew either (1) keeps one live id per tab (revoke-or-detach the old on successful renew) **or** (2) keeps two ids but states: WS occupancy, per-message table re-check, and revoke-of-offered-id tears down that socket. The session object must retain the pairing id it admitted.

### H-MAIL — Envelope field, journal extras, and `list_mailbox` are three shapes

AD-7 / MAILBOX: add `product_session_id` at accept; replies inherit; originating `(producer_id, wire_id)` and payload hash on the **journal row** (“not necessarily on the Envelope fp1 identity”); `list_mailbox` full `{product_session_id}` and pre-ack `{product_session_id, producer_id, wire_id}`; collision same pair + same hash / different hash journal-lifetime.

Inspect Envelope required fields do not include `product_session_id`. `ENVELOPE_FP1_EXCLUDED_FIELDS` is `{correlation_id, causation_id}` only. UI `CHAT-AND-HISTORY.md` already requires snapshot rows to carry **both** the wire pair **and** `msg_id`. This sitting does not copy that DTO.

Unbound:

1. **Is `product_session_id` in Envelope fp1?** Additive field on the record ≠ identity inclusion. Unit A includes it (two sessions cannot share an Envelope identity). Unit B excludes it (same as correlation). Collision “same hash” then means two different things.
2. **Is the wire pair on the query result?** AD-7 puts it on the journal row so pre-ack lookup works. Full snapshot contents are unnamed. Unit A returns `Envelope.to_payload()` (no pair). Unit B joins extras. The UI lost-ack path cannot be written against Unit A’s full snapshot; it can only use the pre-ack form. Neither form names `delivery_state`, `msg_id` echo, or cursor/generation (UI CHAT’s “usual snapshot cursor”).
3. **HTTP encoding.** MAILBOX: “Authenticated HTTP GET snapshot.” CT-40 queries are HTTP GET. No path, no query-string law, no body law. Artifact companion forbids query-string **artifact** ids. Pairing companion forbids `pairing_session_id` in the query string. `product_session_id` / `wire_id` in the query string is unmentioned. Unit A uses query params. Unit B uses a path + JSON header. A third legal unit POSTs a query document (not a CT-40 command family) and breaks “queries are GET.”
4. **Collision owner.** The collision sentence sits under `list_mailbox` but is an admit rule for `send_message`. Unit A enforces it in the mailbox fold. Unit B enforces it in wire idempotency (`registry:wire.dedup_window` is explicitly *not* the retention). Two writers of “this pair already landed.”
5. **Rebuild of pre-AM-02 rows.** Required vs optional parse. Fold-by-field vs parse-fail vs unscoped bucket.

**Required bind.** One row DTO for both `list_mailbox` forms (fields, fp1 rule for `product_session_id`, whether wire pair is present on the full snapshot). One GET path + argument encoding. One owner of the journal-lifetime collision (command admit, not the query). One migration for rows that lack the field.

### H-CANCEL — `originating_psess` is not `owner`, and `handle_id` is not a JobHandle field

CANCEL (post-amendment): `originating_psess` is **not** `JobHandle.owner`; `owner` remains Quant `ActorId`; UI cancel authority is the **operator principal of `originating_psess`**; headless QMB cancel stays Story 36.5.

Inspect `JobHandle` has `job_id`, `owner: ActorId`, no `originating_psess`, no `handle_id`. `cancel_job` arguments start with `handle_id`.

Unbound:

1. **`handle_id` vs `job_id`.** The sitting never equates them. Unit A aliases. Unit B mints a sibling. Snapshots, `later_commands`, and the UI `dispatchCancel` field cannot be shared.
2. **Which operator principal?** Pairing row has “operator principal” + internal `CredentialRef`. Product session has `principal`. `AuthenticatedWireSession` has `credential_ref` + `principal_class` (not the product-session principal). Unit A compares mapped refs (renew forks authority). Unit B compares principal strings (two pairing ids of the same operator both cancel). After H-PAIR, these are different people.
3. **Two mutation paths on one handle.** AD-8: `cancel_job` → recorded no-op on `later_commands` if already terminal. QMA AD-17 coordinated cancel is `JobHandle.cancel`. Story 36.5 remains a production door and “is not this command.” Unit A implements one door. Unit B leaves QMB able to cancel without `originating_psess`. A machine worker calling in-process `JobHandle.cancel` is not the UI path and not clearly forbidden.
4. **`expected_state` vs parent AD-29.** AD-8: queued→running does not invalidate the same `command_id`. Parent AD-29: collision of `command_id` with a different payload hash refuses. If `expected_state` is in the payload, the bytes changed. Unit A hashes it and **cannot** reuse `command_id` after queued→running unless it strips the field. Unit B omits it from the hash. Both quote AD-8.
5. **Nested “starter of that child.”** Inherit parent `psess:` vs the nested invoke’s session. Epic 63 occupancy already forbids grant union; it does not pick the field.
6. **Admit of what?** “At admit” — invoke envelope admit, `JobHandle.submit`, or Task Graph admit. Three writers can claim the first durable write of `originating_psess`.

**Required bind.** `handle_id` ≡ `job_id` or a named new field on the handle record. Compare key for “operator of `originating_psess`” (principal string vs mapped ref, and what renew does). Whether Story 36.5 / `JobHandle.cancel` bypasses the field. `expected_state` in or out of the hashed payload. Child field copy rule. One admit writer.

### H-XFER — Transfer ticket, artifact store, and pull auth are three planes; AD-15 lists none of the pull

AD-9 / ARTIFACTS: PUT stages local-complete fp1; `transfer_artifact {fp1, destination_placement}` records a journal-projected **ticket**; dest **pulls** as `machine`; dest verifies hash+count; failure leaves local-complete; daemon never dials in.

AD-15 family list on port 8765: unauthenticated pairing HTTP; authenticated HTTP GET **snapshots**; authenticated HTTP PUT `/artifacts/stage`; authenticated JSON-RPC WebSocket. **No pull path.**

AM-03 (post-amendment) names projection `artifact_transfer_ticket`. AD-4’s row list does not. ARTIFACTS does not name ticket fields beyond “bound to that fp1 and destination.”

Unbound:

1. **Pull URL and proof.** Unit A: `GET /artifacts/{fp1}` with machine `credential_ref`; ticket is a background authz row. Unit B: `GET /artifacts/pull?ticket=<token>`; token is possession. A third legal unit uses a WS command to avoid adding an HTTP path AD-15 forgot — and then has to move bytes without a JSON-RPC body (AD-9 forbade that for ingest; pull is silent).
2. **Ticket vs store vs register hook.** PUT completeness uses `before_artifact_register` / fp1 into the Epic 42 artifact store. Ticket is a different projection. Who is source of truth for “this fp1 may leave this daemon”? Store completeness `complete` vs ticket state `pending|pulled|failed` is unnamed. Same complete hash may reuse the object: does that reuse inherit old tickets?
3. **Machine principal vs placement.** Story 41.4 `credential_ref` authenticates the worker. Nothing binds that ref to `destination_placement`. Unit A trusts any machine client that can GET. Unit B adds a token. Neither is written.
4. **PUT before `initialize`.** AD-9 auth is Bearer + Origin. AD-13 advertises `stage_artifact` on `initialize` (a WS handshake). Unit A refuses PUT until initialize advertised the cap. Unit B allows PUT with pairing only (no WS). Home attach with no instance can occur before Copilot ever opens a socket.
5. **Capability name vs path.** `initialize` cap `stage_artifact` vs HTTP PUT `/artifacts/stage`. Unit A also ships a JSON-RPC `stage_artifact` (forbidden by AD-9 as a byte body, so it becomes a “start upload” command). Unit B’s cap means “the PUT exists.” Clients cannot share a feature-detect.

**Required bind.** One pull URL, one proof (machine ref, ticket token, or both), ticket schema, ticket lifecycle on retry/interrupt/hash reuse, whether PUT requires initialize, and a one-line AD-15 amendment naming the machine byte GET (or an explicit statement that pull is that GET snapshot).

### H-DRAFT — `editor_draft_head`, AD-22 staging, and the artifact store are three homes for one working copy

AD-11 / AM-07 / PACK: saved drafts are artifact-store bytes plus journal-projected `editor_draft_head` (`editor_draft_id`, head `editor_revision` / “head hash”, owner principal / optional `psess:`). CAS `expected_revision`. Not AD-22 `RefinementProposal`. Unsaved buffer is client-local.

UI AUTHORING companion still says “COMP-QMA-DAEMON **staging**” on save. That is residue against local AD-11, not a second legal backend unit. The backend sitting still does not name the mutate verb, the id mint, or the hash.

Unbound:

1. **`editor_revision` vs `fp1`.** PACK: “content-addressed `editor_revision`” in the artifact store and “head hash.” AD-11: head `editor_revision`. Artifact ingest already has fp1. Unit A aliases. Unit B stores two hashes. CAS operands differ.
2. **Two writers.** PUT `/artifacts/stage` (AD-9, COMP-QMA-DAEMON artifact store) and `editor_draft_head` CAS (AM-03 projection) are different mutations. Order, failure, and orphan blobs are unnamed. First save must create **both** the bytes and the head. Who mints `editor_draft_id` — client (AUTHORING create-draft) or daemon (PACK honesty: absent)?
3. **Same store as composer uploads.** AD-9 Home stages with no `instance_id`. Draft save if it uses the same PUT is an indistinguishable `complete` blob. Library facade concatenate (parent AD-2 ArtifactHit) will list it unless a filter is named. AD-11 does not name a filter. Workbench AD-3 already excludes QMA staging/RefinementProposals from Library — drafts were moved *out* of staging *into* the artifact store, i.e. into the Library projection.
4. **Authority on the head.** Owner principal / optional `psess:`. CAS is “last known head hash.” Two tabs of the same operator, different `psess:`, same `editor_draft_id`: one owner or two? Optional `psess:` does not say it is the CAS key.
5. **Publish mutation.** First Run: publish template **into** the local authoring pack, then enable. Copy bytes vs cite fp1. Enable-at-compile needs contribution bytes in the pack (parent AD-4). A cited fp1 that the pack loader does not copy is a dangling enable.

**Required bind.** One save command (name, fields). `editor_revision` ≡ fp1 or not. Who mints `editor_draft_id`. Write order for store vs head. Library visibility. Publish copy-vs-cite. CAS key (`editor_draft_id` + hash, plus whether `psess:` participates).

---

## Additional pairs (same test, shorter)

| Pair | Unit A reading | Unit B reading | Why both are literal |
| --- | --- | --- | --- |
| QMB verb | AD-6 / seed: `qmb host pair-revoke` | HOST table: `qmb host pair revoke --session` | AM-10 lists `pair-revoke`; HOST spells a nested argv |
| TTL | Missing `registry:pairing.session_ttl` ⇒ refuse issue (row needs `expires_at`) | Missing ⇒ no expiry until revoke | Sitting mints **no number** |
| `list_mailbox` AuthZ | DEPENDENCY-MAP: operator of that `psess:` (same principal) | Any paired operator on that daemon may snapshot a selected `psess:` | AD-7 does not name AuthZ; companion owners table does not either |
| Chat kinds | MAILBOX: `handoff\|reply\|notify\|status\|question` | Inspect MessageKind also has `review_request` / `approval_request` (gate-raised) | “Stay QMA AD-20” vs the chat subset |
| `stop` vs handles | HOST: local handles may become `unknown` | AD-8: `unknown` is not cancellable; first durable terminal wins | Stop is not cancel, but it mutates the same row |
| PackUiRequest durable | PACK: pack metadata projection beside plugin-install | AD-10: ingested request DTO, not stored as a grant — may be ephemeral at enable | One owner of the document after enable |
| `initialize` caps vs HTTP | Caps gate GET/PUT | Caps are WS-only; HTTP uses pairing table | AD-13 vs AD-5/AD-9 |

---

## What would close this review

Not more slogans. One join key per entity:

1. **Pairing.** Mapped `CredentialRef` grammar; renew copy-vs-mint; session object stores the admitted `pairing_session_id`; per-message re-check; OPTIONS preflight carve-out; QMB confirm IPC; traces yes/no.
2. **Mailbox.** Envelope fp1 rule; `list_mailbox` row DTO (both forms); GET path; collision owner; old-row migration.
3. **Cancel.** `handle_id` identity; principal compare key; `expected_state` hash; one admit writer; QMB door vs `originating_psess`; child copy rule.
4. **Transfer.** Pull URL + proof; ticket schema/lifecycle; AD-15 family line; PUT vs initialize.
5. **Drafts.** Save verb; `editor_revision` vs fp1; id mint; write order; Library filter; publish copy-vs-cite.

Until those binds exist, two stories can each tick every AD and still fail to share a daemon sqlite, a WS occupancy table, or a `list_mailbox` client.

Inspect remains `34c148be`. Tests remain unexecuted. Candidate ≠ operator acceptance. This review does not implement, does not run Documentation Factory, and does not rewrite epics.
