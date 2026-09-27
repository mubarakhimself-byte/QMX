---
name: Chat and history
sitting: architecture-QMX-UI-2026-09-23
status: candidate (Codex R3) — not operator-accepted
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
---

# Chat and history — split send from invoke

**Provenance:** sitting **CANDIDATE** closing [REVIEW.md R3](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/REVIEW.md) and the 2026-09-24 closure remaining correction (durable `psess:` on the mailbox record; lost-ack identity known before ack). Not user-accepted. Not a new COMP, CT, sqlite class, or UI message store.

This companion is the controlling contract for `ConversationPane.send` versus `dispatchInvoke`. It **closes** the research/10 fork that offered mailbox `send_message` **or** a granted-op invoke for the same Send. Team B (chat as `InvocationEnvelope`) is refused. Home chat must not mint a synthetic `instance_id`.

Spine local AD-8’s unique-issuer rule remains for **granted operations only**. The invoke-only sequence that lumped “press widget **or send message**” through `dispatchInvoke` is **wrong for chat**. `send_message` never builds an `InvocationEnvelope` and never enters `dispatchInvoke`. Unique chat issuer is **`dispatchChat`**.

---

## 0. Ruling in one screen

| Intent | Host | Wire | Envelope | `instance_id` |
| --- | --- | --- | --- | --- |
| Chat send (Home, Copilot, in-app panel) | `ConversationPane.send` → **`dispatchChat`** | CT-40 command `send_message` (`WireCommand.SEND_MESSAGE`) | **none** | **not required** |
| Answer a copilot `question` | `ConversationPane.answer_question` → **`dispatchChat`** | `send_message` (kind `reply`) | **none** | **not required** |
| Answer mailbox `approval_request` | same pane, different command | seed command `approve_hook_action` | **none** | **not required** |
| Cancel visible stream | `ConversationPane.cancel_display` | none (chrome) | **none** | n/a |
| Composer tool/op submit | `Composer.submit` → `dispatchInvoke` | public call + parent-AD-24 `InvocationEnvelope` | **required** | **exactly one** `selected_refs` kind `instance_id` |
| Widget Run, json-render action, MCP `tools/call`, graph Run, command-palette op | those components → `dispatchInvoke` only | same as Composer.submit | **required** | **exactly one** `selected_refs` kind `instance_id` |

Home chat on an **authoring** `psess:` with **absent** `app_instance_id` is legal. A later authorized tool call is a **different** host contract and refuses unless that one instance ref is present.

---

## 1. Two host contracts (do not collapse)

### 1.1 `ConversationPane.send` — mailbox command

1. Operator (or in-app panel) commits composer **text**, not a pack `op_id`.
2. Host calls **`apps/qmx-ui/src/lib/host/dispatchChat` only**. That function issues CT-40 **command** `send_message` over JSON-RPC 2.0 WebSocket. Components never import the wire client.
3. **Before send**, `dispatchChat` mints the wire pair `(producer_id, id)` (`id` is the WireEnvelope command id; snapshot/query name it `wire_id`). It stores pending `{producer_id, id, product_session_id}` in **`sessionStorage`** until a `list_mailbox` snapshot shows that row.
4. Wire frame is the ordinary `WireEnvelope` (`v`, `type=send_message`, `id`, `producer_id`, `correlation_id`, `scope_path`, payload). Payload names `product_session_id`. It does **not** carry `InvocationEnvelope`. It does **not** carry a client-minted `msg_id`. It does **not** use product-session `command_id` (that namespace is parent AD-29 mutate / cancel / invoke — not mailbox append).
5. Ack is transport. Durable membership is the mailbox snapshot (query), not the ack and not `message.delta`.
6. No GrantRecord, no `grant_id`, no `caller_kind`, no `idempotency_key` of the invoke family, no envelope `instance_id`.
7. `app_instance_id` may be absent on the authoring Home/`psess:`. Do not mint a dummy instance to make Send work.

`send_message` already exists in seed vocabulary:

```61:61:.worktrees/integration-inspect/qmx-agents/packages/qma-wire/src/qma/wire/vocabulary.py
    SEND_MESSAGE = "send_message"
```

(`WireCommand` member; `command.v1.schema.json` enum includes `"send_message"`. COMP-QMA-WIRE owns the name. Daemon does **not** dispatch it over the socket at `34c148b`.)

Command args this sitting binds (payload `args`; not a new CT):

```json
{
  "product_session_id": "psess:…",
  "body": { "text": "…" },
  "kind": "handoff"
}
```

`kind` uses CT-48 `MessageKind` when the send is a mailbox act (`handoff` \| `reply` \| `notify` \| `status` \| `question`). `approval_request` is **not** minted by ConversationPane.send; gates raise it. Optional `reply_to_ref` / `causation_id` follow CT-48. Chips on the message are `selected_refs` identities already legal on the `psess:` **or** message-only chrome not yet staged (see `LIBRARY-AND-ATTACHMENTS.md`).

Forbidden on this command: `InvocationEnvelope` keys (`logical_invocation_id`, `grant_id`, `op_id`, `instance_id` as envelope field, `idempotency_key`, `caller_kind`, `input_hash`). A client that sends those has left the chat contract.

At **write time** the daemon copies `product_session_id` from this payload onto the CT-48 mailbox `Envelope` / journal `message.*` row (section 3). Originating `(producer_id, wire_id)` and payload hash are recorded on that same journal row so recovery can look the row up **without** `msg_id`.

### 1.2 `dispatchInvoke` — granted operation

`Composer.submit`, `WidgetFrame` Run / `request_invoke`, json-render `executeAction`, MCP Apps `tools/call` intercept, graph Run, and command-palette **ops** call **`apps/qmx-ui/src/lib/host/dispatchInvoke` only**. They never import the wire client. That function builds parent-AD-24 `InvocationEnvelope` and hop-compares GrantRecord + descriptor.

Invoke **requires** exactly one `selected_refs` entry of kind `instance_id`. Zero or many → typed `INVALID_INPUT`. Envelope `instance_id` copies that ref. Parent AD-24 stays: public operation envelopes carry `instance_id`. Copilot **tool** calls use `caller_kind=agent` when that field exists; operator-pressed Run uses `caller_kind=user`; template node uses `caller_kind=workflow`. Until the daemon accepts `caller_kind`, pack invoke is `caller_kind_unsupported` — **Home `send_message` still proceeds**, because it is not pack invoke.

A copilot that decides to call a tool after a chat turn is **not** a second `send_message`. It is `dispatchInvoke` under the same `psess:` grants. Chat without an instance remains allowed; the tool call waits until the operator selects one instance or is refused.

### 1.3 What each component may emit

| Component event | Contract |
| --- | --- |
| `ConversationPane.send` | `dispatchChat` → `send_message` only |
| `ConversationPane.answer_question` | `dispatchChat` → `send_message` reply **or** `approve_hook_action` when the mailbox row is `approval_request` |
| `ConversationPane.cancel_display` | chrome; local AD-13 Stop of local presentation; **not** `JobHandle.cancel`, **not** seed `stop_run` |
| `Composer.submit` | `dispatchInvoke` only |
| `WidgetFrame.message` | stages message-only chrome into the relevant pane; not a send and not an invoke (LIBRARY companion) |
| `WidgetFrame.request_invoke` / Run | `dispatchInvoke` |
| `SessionList.select_session` | chrome select of `psess:`; then history query |

`steer_agent` is not Send. `stop_run` is not widget Cancel. `retry_task` is not UI Retry. `launch_task` / `start_mission` are not graph Run.

```mermaid
sequenceDiagram
  participant U as Operator
  participant P as ConversationPane
  participant C as dispatchChat
  participant I as dispatchInvoke
  participant W as qma-wire
  participant D as qma-daemon
  participant M as mailbox.delivery
  U->>P: Send (Home, no instance)
  P->>C: dispatchChat
  Note over C: mint (producer_id, id) before send
  Note over C: sessionStorage pending triple
  C->>W: command send_message (producer_id, id, psess)
  Note over P,I: dispatchInvoke is not on this path
  W->>D: JSON-RPC
  D->>M: append message.* with Envelope.product_session_id
  D-->>C: command ack
  C->>W: query list_mailbox
  W-->>C: snapshot (wire pair + msg_id)
  D-->>P: event message.delta (progress only)
```

```mermaid
sequenceDiagram
  participant U as Operator
  participant Comp as Composer or WidgetFrame
  participant I as dispatchInvoke
  participant W as qma-wire
  participant D as qma-daemon
  participant G as GrantRecord
  U->>Comp: submit / Run (one instance_id selected)
  Comp->>I: dispatchInvoke
  I->>I: build InvocationEnvelope
  I->>W: public call plus envelope
  W->>D: JSON-RPC
  D->>G: hop-compare
  D-->>Comp: ack then JobHandle / value
  Note over Comp,I: send_message is not on this path
```

---

## 2. Identities (closed set)

| Id | What it is | What it is not |
| --- | --- | --- |
| `product_session_id` (`psess:`) | Authority overlay. Key for grants, `selected_refs`, and **mailbox history**. Cardinality **1 `psess:` → many** QMA `sess:`. **Persisted on the mailbox Envelope at write.** | Not the engine Session. Not a tab. Not a thread string stored on the session row |
| QMA `Session` (`sess:`) | Execution container (execution_model + autonomy) | Not a third chat. Not the transcript |
| `conversation_thread_id` | **Hash-stable** id **derived from** `psess:` at query time | Not a durable Envelope field. Not a `product_session` column. Not `private_notes` |
| Wire pair `(producer_id, wire_id)` | **Pre-ack identity.** `wire_id` is WireEnvelope `id`, minted **before** send. Client stores pending `{producer_id, id, product_session_id}` until snapshot shows the row. Persisted on journal `message.*` at admit. | Not `msg_id`. Not invoke `idempotency_key`. Not product-session `command_id` |
| `message_id` / `msg_id` | Server-assigned CT-48 `Envelope.msg_id` at write. Snapshot includes it **after** commit. Display may use it. | Not available to the client before snapshot. Lost-ack recovery **must not** require it |
| `job_handle` / `job_id` | Durable work | Not a chat row. May be **linked** from a message |
| Tab / pane / window | Chrome | Writes nothing on close |

**Thread derivation (v1, one primary thread per `psess:`):**

```
conversation_thread_id = "thread:" + hex(sha256(utf8(canonical product_session_id)))
```

Canonical form is the `psess:` string already stored on the row (no salt, no `producer_id`, no tab id). Every client of the same session derives the same thread. Home/Copilot of that session share that one primary thread. An **app-use** optional panel has its **own** app-use `psess:` (instance-bound) and therefore its **own** mailbox and `conversation_thread_id`. Switching apps does not merge threads (local AD-4; J-UI-01; J-UI-04).

v1 does not mint secondary threads under one `psess:`. A second thread is a named amendment.

**Questions bind** `(conversation_thread_id, message_id, optional job_handle)` **after** the question row is in the snapshot (so `message_id` exists). A question without a thread is refused. A job result without a message may still exist as a JobHandle on Home attention; it is not silently spliced into another `psess:` transcript.

---

## 3. Durable history owner

**Owner:** existing QMA mailbox. Store `mailboxes_and_delivery_state`, fold `mailbox_delivery_state`, bounded stream **`mailbox.delivery`**, sourced from journal `message.*` (CT-48 / DEC-0319). COMP-QMA-DAEMON is the sole writer.

**Proposed QMA amendment (not a new CT, not a sixth store, not `private_notes`):** persist `product_session_id` **on the mailbox Envelope at write time**. Copy it from the admitted `send_message` payload onto the existing CT-48 `Envelope` / journal `message.*` row. Also record the admitting wire pair `(producer_id, wire_id)` and payload hash on that journal row. Quant `from` / `to` ActorIds stay the bus addressing. Product-session history **reuses that stream**, filtered by the persisted field.

**Key for product chat:** `Envelope.product_session_id`. Rebuild of `list_mailbox` is: fold journal `message.*` rows whose `product_session_id` equals the requested `psess:`. Do not parse body text. Do not derive the index from `private_notes`.

Parent AD-8 durable fields on `product_session` remain:

`product_session_id`, `profile`, `principal`, `context_revision`, `app_instance_id`, `granted_ops`, `selected_refs`, optional `private_notes`, plus CONTRACTS §3 `account_scope`, `resume_cursor`, `cursor_generation`.

**Not durable** on that row (parent AD-8 / `NOT_DURABLE_FIELDS` @ `34c148b`): `qma_session_id`, tab/window/view/pane ids, attachment, layout.

Therefore:

- Transcript **is not** the engine `Session`.
- Transcript **is not** `private_notes` JSON used as a message store. `private_notes` stay session notes (retention/export/deletion with the row), not MemoryProvider, not Knowledge, not chat.
- Grants restore from the **product_session query**. Messages restore from **mailbox snapshot**. Mixing those snapshots is a bug.

CT-48 `Envelope` remains the message record (`msg_id`, `from`, `to`, `kind`, `correlation_id`, `body`, `artifact_refs`, optional mission/task/`reply_to_ref`/`causation_id`) **plus additive** `product_session_id`. Delivery states stay `delivered | queued | woke | deferred | dead_letter`. A message may request work; it is never the work.

**Inheritance.** Replies and questions **inherit** `product_session_id` from the parent message named by `reply_to_ref` / `causation_id`. They do not invent a session. If a `send_message` reply payload also names `product_session_id`, it must equal the parent’s field or the write is refused (no retarget onto another `psess:`). Daemon-originated mailbox rows that are not in a product conversation omit the field; Quant delivery is unchanged.

**Retention.** Journal `message.*` is **not** trimmed (parent AD-8 / AD-23). `mailbox.delivery` is a **bounded non-evidence** stream (GAP-0089). UI history is the **snapshot**. If the delivery projection compacted past the client cursor, the query returns snapshot/resync with a bumped generation — **never** a silent empty success. Pair lookup reads the journal/snapshot, not the bounded delivery tape.

Quant-owned CT-48 mailboxes (ActorId `from`/`to`) stay the bus. Do not stand up a parallel “conversation” table.

### 3.1 Rebuild example (four journal rows)

Fold `list_mailbox({ "product_session_id": "psess:H" })` keeps every `message.*` row whose Envelope field equals `psess:H`. Example after one operator send, one copilot reply, one copilot question, and a later operator answer:

| journal seq | kind | `msg_id` (server) | `producer_id` | `wire_id` | `product_session_id` | `reply_to_ref` | `causation_id` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | `handoff` | `msg:s1` | `prod:tabA` | `C1` | `psess:H` | — | — |
| 102 | `reply` | `msg:r1` | `prod:daemon` | `D1` | `psess:H` | `msg:s1` | `msg:s1` |
| 103 | `question` | `msg:q1` | `prod:daemon` | `D2` | `psess:H` | `msg:s1` | `msg:r1` |
| 104 | `reply` | `msg:a1` | `prod:tabA` | `C2` | `psess:H` | `msg:q1` | `msg:q1` |

How the field got there:

1. **Send.** `dispatchChat` `send_message` payload `product_session_id=psess:H`. Daemon copies that value onto Envelope at write. Wire pair `(prod:tabA, C1)` recorded on the journal row. Server assigns `msg:s1`.
2. **Reply.** Copilot answer is a mailbox `reply` with `reply_to_ref=msg:s1`. Daemon **inherits** `psess:H` from parent `msg:s1`. No UI `send_message` for this row.
3. **Question.** Copilot `question` caused by `msg:r1`. Inherits `psess:H` from that parent (same field as the thread root).
4. **Later answer.** Operator `answer_question` → `dispatchChat` `send_message` kind `reply`, `reply_to_ref=msg:q1`. Inherits `psess:H` from the question (payload, if present, must match).

Rebuild after daemon restart: scan journal `message.*`; keep rows 101–104; drop any row with a different or omitted `product_session_id`. `conversation_thread_id` is derived from `psess:H` at query time. Body text is not consulted.

---

## 4. Authoritative history query

**Query:** closed-and-addable CT-40 `WireQuery` member **`list_mailbox`**.

| Fact | Value |
| --- | --- |
| Family | query (HTTP GET snapshot) |
| Owner of the **name** | **COMP-QMA-WIRE** (same addable pattern as `list_mission_hooks`, `facade_search`) |
| Owner of the **handler / fold** | COMP-QMA-DAEMON mailbox |
| At `34c148b` | **ABSENT** from `WireQuery` and `query.v1.schema.json` (enum ends at `facade_get`) |
| New CT? | **No.** Additive member of existing CT-40 |

Two lookup forms. **Do not require `msg_id` for lost-ack recovery.**

| Args | Returns |
| --- | --- |
| `{ "product_session_id": "psess:…" }` plus the usual snapshot cursor/generation | Conversation snapshot for that `psess:` (envelopes, delivery state, question bindings, artifact/job refs). Each committed row includes **both** the wire pair `(producer_id, wire_id)` **and** server `msg_id`. |
| `{ "product_session_id": "psess:…", "producer_id": "…", "wire_id": "…" }` | Zero or one row: the admitted message with that pair under that `psess:`. Used for lost-ack / restart recovery **before** the client has `msg_id`. |

Display may use `msg_id` once the snapshot has it. Recovery uses the wire pair until then.

**Snapshots are truth. Events are progress.** `message.delta` is **not** authoritative (research/10; DEC-0304). The pane paints deltas for streaming, then reconciles from `list_mailbox`. Accumulating an event tape as history is forbidden.

**Missing query is typed unavailable, not empty-success.** Until COMP-QMA-WIRE adds `list_mailbox` and the daemon serves it, the host must surface a typed `query_unavailable` (query name `list_mailbox`). It must **not** render “no messages” as a successful empty mailbox. A **present** query returning zero rows on a new `psess:` **is** a real empty mailbox and may paint empty.

`SessionList` lists `psess:` rows (product_session query). It is not the transcript.

---

## 5. Ack, idempotency, drafts

| Layer | Identity | Lost ack | Forbidden |
| --- | --- | --- | --- |
| Chat send | Wire pair **`(producer_id, wire_id)`** minted **before** send. Pending `{producer_id, id, product_session_id}` in `sessionStorage` until snapshot shows the row | **Query `list_mailbox` `{product_session_id, producer_id, wire_id}`**. If the row is present, the send landed; paint it (snapshot now has `msg_id` too) and drop pending. If absent, stay `unknown`. **Do not wait for `msg_id` the client does not have.** | **Do not resend with a new `id`**. Do not look up by `msg_id`. Do not invent invoke `idempotency_key` or product-session `command_id` for chat |
| Invoke | Caller `idempotency_key` + envelope uniqueness (parent AD-24) | Query JobHandle / `query-state` **before** any resubmit | Blind retry of `external-egress`; second `dispatchInvoke` for the same submit |

`producer_id` is assigned at `initialize` and **stable across reconnects** of that tab. Wire `id` / `wire_id` is minted by the producer per command **before** the bytes leave. Duplicate `(producer_id, id)` with the **same** payload hash returns the prior ack. Same pair with a **different** payload hash **refuses** (typed collision). Changing either member is a different command — that is why a lost-ack path must reuse the **same** pair or only query.

Uniqueness for admitted chat is **journal-lifetime** on `(producer_id, wire_id)`, not only `registry:wire.dedup_window`. The wire window still coalesces transport acks; the journal row is the durable collision record because `message.*` is not trimmed.

**Drafts vs pending send.**

- Composer text **not yet issued**: client-local draft. Reconnect does not upload it. It is not in the mailbox. No wire pair yet. No `msg_id`.
- Send **issued**: pending triple in `sessionStorage`. Not yet a display `msg_id`. Membership is unknown until snapshot.
- Snapshot shows the pair: drop pending and the local draft; display may switch to `msg_id`.
- Transport ack without snapshot is **not** membership. Snapshot without transport ack **is** membership (lost-ack case).

Duplicate Send in the UI (double-activate) coalesces on the same `(producer_id, id)` (J-UI-07). It must not mint a second command id.

---

## 6. Concurrent streams and app switch

Streams are scoped by `conversation_thread_id` (hence by `psess:`).

- Two conversations (Home authoring `psess:A` and app-use `psess:B`) may stream at once. Demux by `thread_id`. Do not merge histories (XR-07 proposal accepted here as sitting law; research/10).
- Switching the **visible app** restores that app’s `psess:` and its mailbox. It does **not** redirect in-flight `message.delta` of another `psess:`. Tokens, questions, and completion stay bound to the originating thread (J-UI-01).
- Closing a tab is `wire.detach`. It does not cancel the mailbox stream’s durable work and does not cancel JobHandles (local AD-13).
- Two chrome tabs of the **same** `psess:` share one thread and one mailbox. Each tab has its own `producer_id` (local AD-24). Wire uniqueness stays `(producer_id, id)`. Pending triples are per tab (`sessionStorage`).

Result links inside a message are artifact/job **refs**. The JobHandle is observed on Home / `RunInspector`. Painting a job as a chat row does not own the handle.

---

## 7. Questions, stale and revised answers

Mailbox kinds `question` and `approval_request` are the pending-question surface (research/10). Binding is `(thread_id, message_id, optional job_handle)` once the question is in the snapshot.

- A later **`message_id` supersedes** the earlier one for **display** of the same question/answer slot.
- The UI shows **revised**. It **never silently deletes** the earlier id. Both ids remain in the `list_mailbox` snapshot.
- Operator edits of an **unsent** draft are local: no wire pair, no `message_id`. After Send is issued, the client has the wire pair and still has no `msg_id` until snapshot.
- Stale question: the originating `psess:` still owns it after app switch (inherited field on the question row). Answering it from a different visible app must not retarget the reply onto the visible app’s thread.
- `approval_request` is operator-principal `approve_hook_action` only (`OperatorPrincipalRequired` for `machine`). That is still **not** `dispatchInvoke`.

`cancel_display` stops local streaming presentation. It does not mark the mailbox row cancelled and does not `JobHandle.cancel`.

---

## 8. References in chat

Durable chips on a session are parent-AD-8 / kit `selected_refs` (closed kinds + kit `instance_id` when committed). Composer content that is **committed** to the `psess:` follows CAS mutate on that row (parent AD-29) — grants/refs restore with the product_session query, independent of mailbox.

**Widget message-only context is chrome until staged.** `WidgetFrame.message` does not write `selected_refs` and does not `send_message` by itself. Staging, upload/hash-is-not-possession, Knowledge cite, and unavailable recovery are the LIBRARY companion: [`LIBRARY-AND-ATTACHMENTS.md`](LIBRARY-AND-ATTACHMENTS.md). Cross-app reference does not merge transcripts or union grants (J-UI-04).

---

## 9. Reconnect and crash

Order after transport loss (research/10 §9–10; parent AD-29):

1. Re-auth with the same `pairing_session_id` (HTTP Bearer + WS `qmx.pair.<id>`). Daemon maps it internally to `credential_ref`. `initialize` with the **same** `producer_id` (re-hint from the pending triple when `sessionStorage` still holds it).
2. **Product-session query** restores durable AD-8 fields (`granted_ops`, `selected_refs`, `profile`, `app_instance_id` absent-or-present, cursors). Does **not** replay unacked intent. Does **not** imply approval.
3. **`list_mailbox`** restores transcript for that `psess:` (`{product_session_id}` snapshot). Missing query → typed unavailable (section 4). Compacted delivery → snapshot/resync, not empty-success.
4. If a pending triple exists, **also** `list_mailbox {product_session_id, producer_id, wire_id}`. Landed → paint, drop pending. Absent → `unknown`. **Do not resend.** Lookup by stored pair still works if `initialize` assigned a different live `producer_id`; do not substitute the new id into the query.
5. `wire.attach(scope, since_seq)` for **progress** (`message.delta` and others). Events must not overwrite a snapshot terminal.
6. `JobHandle.reattach` for in-flight **jobs** (separate from chat).
7. Unsent drafts remain local. In-flight deltas of `psess:A` are not attached to newly visible `psess:B`. Empty `sessionStorage` (no pending triple) → snapshot the selected `psess:` only; do not mint a send for leftover composer text.

Lost invoke ack: JobHandle query, not mailbox, not a new envelope id.

---

## 10. Honesty at inspect `34c148b`

| Claim | Fact |
| --- | --- |
| `send_message` name | **Present** — `WireCommand.SEND_MESSAGE` in `vocabulary.py`; schema enum |
| Live dispatch of `send_message` | **Absent** — `DaemonProcess._handle_client` drains TCP bytes |
| `list_mailbox` | **ABSENT** — backend add, COMP-QMA-WIRE vocabulary + daemon handler (both lookup forms) |
| `Envelope.product_session_id` | **ABSENT** at inspect (`ENVELOPE_REQUIRED_FIELDS` / optional refs have no `psess:`). **Proposed QMA amendment:** additive field on existing CT-48 Envelope / journal `message.*` |
| Admitting `(producer_id, wire_id)` on `message.*` | **ABSENT** — same proposed amendment, so pair lookup survives rebuild |
| `product_session` messages | **Absent** — durable fields are context/grants/refs, not transcript (`product_session.py` `DURABLE_FIELDS`) |
| `private_notes` as chat | **Forbidden** even if the optional JSON column is later wired |
| Mailbox store | **Present** as Quant mailbox fold (`MAILBOX_STORE_NAME`, stream `mailbox.delivery`); **psess: filter is the named amend** |
| `InvocationEnvelope.instance_id` | **Required on invoke** at inspect; authoring-optional `app_instance_id` is kit law, not wired |
| `caller_kind` | **Absent** — blocks pack invoke, not `send_message` |
| `message.delta` | Seed event; **not** truth |
| This file | Architecture candidate. Unexecuted |

CHANGE-IMPACT class: **reuse** `send_message` + mailbox store; **add** `list_mailbox` (wire vocabulary + query door + both lookup forms); **adapt** CT-48 Envelope with additive `product_session_id` (proposed QMA amend, not a new sqlite class); **adapt** UI host to two functions (`dispatchChat` vs `dispatchInvoke`).

---

## 11. Required traces (R3 closure)

Architecture traces. Unexecuted. Each row: intent → component → identity → wire → owner → ack/result → recovery.

### T-CH-01 — Home send, no instance

Operator on Home, authoring `psess:H`, `app_instance_id` absent, `selected_refs` has **no** `instance_id`. Types a message. `ConversationPane.send` → **`dispatchChat`** → command `send_message` with `product_session_id=psess:H`. Wire pair minted **before** send; pending triple stored. No `InvocationEnvelope`. No client `msg_id`. Daemon copies `psess:H` onto Envelope at write. Ack then `list_mailbox`. Snapshot contains the wire pair **and** `msg_id`. Display may use `msg_id`. `conversation_thread_id` derived from `psess:H`. **Forbidden:** `dispatchInvoke`; synthetic `inst:`; GrantRecord compare; `INVALID_INPUT` for missing instance **on this path**.

### T-CH-02 — Later authorized tool call (invoke)

Same `psess:H`. Operator selects exactly one `instance_id` (kit `selected_refs`). Copilot or Composer submits a granted op. `dispatchInvoke` builds envelope (`instance_id` copied, `caller_session_ref=psess:H`, `caller_kind=user` or `agent`). Host hop-compares GrantRecord. Result may link a JobHandle **into** a later mailbox `reply` as `artifact_refs` / job ref; the invoke itself is not `send_message`. Zero instance refs → `INVALID_INPUT` on **invoke only**. Chat history of T-CH-01 remains. **Forbidden:** routing the tool call as `send_message`; skipping the envelope.

### T-CH-03 — Two concurrent conversations

`psess:H` (authoring/Home) streaming answer A. `psess:B` (app-use panel for instance B) streaming answer B. Thread ids `thread:sha256(H)` and `thread:sha256(B)`. Deltas carry their `thread_id`. Pane H must not paint B’s tokens. Mailboxes are distinct (`Envelope.product_session_id` differs). **Forbidden:** one merged transcript; one mailbox key.

### T-CH-04 — App switch

While A is in-flight on `psess:H`, operator selects opened app B. Chrome restores `psess:B` + `list_mailbox({product_session_id:B})`. In-flight deltas of `psess:H` continue bound to H (J-UI-01). Closing B unmounts chrome, does not cancel H’s mailbox work or B’s JobHandles. **Forbidden:** redirecting H’s answer into B; unioning `granted_ops`; writing B’s id onto H’s in-flight reply.

### T-CH-05 — Stale question, revised answer

Question `message_id=M1` on thread H, optional `job_handle=J`, Envelope `product_session_id=psess:H` inherited from the parent send. Operator switches away and back. Question still bound `(thread_H, M1, J)`. Copilot (or operator reply) writes `message_id=M2` superseding M1 for display; M2 inherits `psess:H` from M1. UI shows **revised** and keeps M1 in the snapshot. **Forbidden:** deleting M1; answering onto the currently visible app’s thread if that thread is not H.

### T-CH-06 — Lost ack, then same-tab reload / restored page session (no resend)

1. `dispatchChat` mints `(producer_id=P, id=C1)` **before** send for `psess:H`. Stores pending `{producer_id:P, id:C1, product_session_id:psess:H}` in `sessionStorage`. Issues `send_message`. Daemon writes Envelope `product_session_id=psess:H` and journal pair `(P, C1)`, assigns `msg:s1`. Transport ack is **lost**. Client never received `msg_id`.
2. **Same-tab reload** (or a restored page session that still has this `sessionStorage`). The pending triple is still present. Re-auth; `initialize` re-hints `P` from that triple when present. **Cold start / closed tab:** `sessionStorage` is empty — skip to step 6 empty-storage branch; do not claim the pending triple survived.
3. Product-session query restores grants/refs. **Do not** look for `msg_id` (the client still does not have it).
4. `list_mailbox {product_session_id:psess:H, producer_id:P, wire_id:C1}` returns the landed row, now including `msg:s1`. Paint that conversation (`psess:H`, not some other session). Drop pending. **Do not resend.** Do not mint `id=C2`.
5. Then `list_mailbox {product_session_id:psess:H}` for the full snapshot (section 3.1 four-row shape if replies already exist). Then `wire.attach(..., since_seq)`.
6. If the pair lookup returns **absent**: chrome `unknown`; keep the pending triple; **still do not resend**. Query again later. If `sessionStorage` is empty (cold start / closed tab), snapshot the selected `psess:` via `list_mailbox(product_session_id)` only; leftover composer text stays a local draft; deterministic pre-ack correlation is unavailable on that client.

**Forbidden:** recovery that waits for `msg_id` before the client has `msg_id`; guessing content; replay unacked intent as a new command; empty history because events were not replayed; attaching the restored send to a different `psess:`.

### T-CH-07 — History restoration vs missing query

Fresh client, `psess:H` known. `list_mailbox` implemented: snapshot is the transcript; events after `since_seq` are progress. `list_mailbox` **absent** (today’s inspect): typed `query_unavailable`, history surface **unavailable**, **not** an empty conversation, **not** “restore from `private_notes`”, **not** “restore from `sess:`”. Grants may still restore from product_session query. **Forbidden:** treating missing query as zero messages.

### T-CH-08 — Projection rebuild from journal

Daemon restart with empty delivery fold. Fold reads journal `message.*` and keeps rows whose `Envelope.product_session_id == psess:H` — the four rows in section 3.1 (`handoff` send, inherited `reply`, inherited `question`, later inherited answer). `list_mailbox({product_session_id:psess:H})` returns those four. Pair lookup `(prod:tabA, C1)` still finds `msg:s1`. **Forbidden:** rebuilding by parsing bodies; a parallel conversation table; dropping inherited replies because they did not repeat the payload field.

---

## 12. Forbidden (explicit)

- `send_message` through `dispatchInvoke`.
- `InvocationEnvelope` on chat send.
- Requiring `instance_id` / GrantRecord for Home chat.
- Synthetic app instance minted only so Send can invoke.
- Chat as a granted pack `op_id`.
- Transcript in `private_notes`, MemoryProvider, Knowledge, telemetry, or a new sqlite class / conversation store.
- `sess:` as the conversation id.
- Authoritative UI history from `message.delta` alone.
- Empty-success when `list_mailbox` is missing.
- Lost-ack recovery that looks for `msg_id` before the client has `msg_id`.
- Requiring `msg_id` on `list_mailbox` recovery lookup.
- Resend with a new wire `id` after lost ack, same-tab reload, or cold start.
- Redirecting in-flight deltas across `psess:`.
- Silently deleting a superseded `message_id`.
- Widget message-only chrome treated as durable `selected_refs` before staging.
- Parsing free-form bodies to rebuild the `psess:` index.
- Using product-session `command_id` as the chat send identity.

---

## 13. Citations

| Source | What it contributes |
| --- | --- |
| `vocabulary.py` `WireCommand.SEND_MESSAGE` | Seed CT-40 command exists; chat reuses it |
| Parent AD-8 durable fields (`architecture-QMX-2026-09-18` spine AD-8; CONTRACTS §3; `product_session.py` `DURABLE_FIELDS`) | Session row is grants/refs/profile — **not** messages |
| CT-48 Envelope at inspect (`ports/mailbox.py` `ENVELOPE_REQUIRED_FIELDS`) | No `product_session_id` today; additive field is the named QMA amend |
| `research/10-transport-reconnect-ops.md` §3.3, §9 send-copilot row | Families; snapshot vs events; reconnect; **fork closed** in favor of mailbox send |
| `workroom/qmx-ui-review-2026-09-23/REVIEW.md` **R3** | Required split, traces, no synthetic instance |
| `workroom/qmx-ui-closure-review-2026-09-24/REVIEW.md` **R3 remaining** | Persist session routing on the mailbox record; identity known before ack |
| CT-48 / `mailbox.py` `mailbox.delivery` | Durable owner; bounded delivery projection; journal `message.*` not trimmed |
| Local AD-4 | Chat without invoke legal; invoke needs one `instance_id` |
| Local AD-8 unique issuer | **Invoke** only — not Send |
| Local AD-18 | Unique chat issuer `dispatchChat`; persist `product_session_id` at write; pre-ack wire pair |
| `LIBRARY-AND-ATTACHMENTS.md` | Message-only widget context until staged |
| J-UI-01, J-UI-04, J-UI-06, J-UI-07 | Switch, separate histories, reconnect, duplicate submit |
