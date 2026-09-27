---
name: Mailbox and delivery
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Mailbox and delivery

UI AD-18 stays: `dispatchChat` → `send_message`; no InvocationEnvelope; no instance. This file binds **owners** the UI candidate labelled too narrowly.

## Owners

| Concern | Owner | Plan anchor |
| --- | --- | --- |
| Command name `send_message` | COMP-QMA-WIRE | Epic 41.1 seed vocab (**reuse**; socket dispatch is an adoption gap) |
| Query name `list_mailbox` | COMP-QMA-WIRE addable | AM-08; **not** in seed seven |
| Durable Envelope + delivery projection | COMP-QMA-DAEMON bus | **Epic 46 / Story 46.4** / QMA AD-20 / CT-48 |
| Journal / fold rebuild | COMP-QMA-DAEMON | Epic 42 |
| `product_session_id` on the Envelope | DAEMON at write | AM-02 additive field |

Do not say “Epic 41 mailbox.” Wire vocabulary is Epic 41. Delivery is 46.4.

## Additive field (AM-02)

Inspect `Envelope` required: `msg_id`, from, to, kind, `correlation_id`, body, priority, `created_at`. Optional mission/task/reply/causation/artifact_refs.

**Add** `product_session_id` at accept. Replies and questions copy it from the parent and refuse a different session. Rebuild folds `message.*` rows by that field. Do not parse bodies.

Also persist originating `(producer_id, wire_id)` and payload hash on the **journal row** (not necessarily on the Envelope fp1 identity; `correlation_id` stays excluded from fp1 as today).

## `list_mailbox`

Authenticated HTTP GET snapshot (authoritative), same pairing proof as other queries.

| Form | Args | Result |
| --- | --- | --- |
| Full | `{product_session_id}` | Transcript snapshot for that session |
| Pre-ack | `{product_session_id, producer_id, wire_id}` | Zero or one row |

Authorization: the connection’s operator principal (from the pairing table) must **equal** `product_session.principal`. A valid pairing for operator A cannot snapshot operator B’s mailbox. `machine` connections do not use this UI query.

Collision: same pair + same hash → prior result. Same pair + different hash → refuse for **journal lifetime** (stricter than `registry:wire.dedup_window`). UI sitting already specified this; this sitting keeps it.

Missing query: typed `query_unavailable`. Chrome must not paint an empty conversation.

## Recovery (AD-14)

| Client state | Backend |
| --- | --- |
| Pending triple in sessionStorage (reload) | Pair lookup; paint landed row; no resend |
| Empty storage (cold start) | If operator selected `psess:`, full snapshot only. No pair lookup. No auto `send_message` |
| Daemon restart, empty delivery fold | Fold journal; pair lookup still works |

WakePolicy, DeliveryState, and MessageKind stay QMA AD-20 / Story 46.4. Chat send uses kinds `handoff` \| `reply` \| `notify` \| `status` \| `question`. `approval_request` is still gate-raised, not minted by `ConversationPane.send`.

## Honesty at inspect

Mailbox types exist. `product_session_id` field **absent**. `list_mailbox` **absent**. Socket dispatch of `send_message` **absent**.
