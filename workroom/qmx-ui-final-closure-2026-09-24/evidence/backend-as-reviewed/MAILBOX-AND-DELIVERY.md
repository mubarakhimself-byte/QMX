---
name: Mailbox and delivery
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Mailbox and delivery

UI AD-18 stays: `dispatchChat` → `send_message`; no InvocationEnvelope; no instance.

## Owners

| Concern | Owner | Plan anchor |
| --- | --- | --- |
| Command name `send_message` | COMP-QMA-WIRE | Epic 41.1 seed vocab |
| Query name `list_mailbox` | COMP-QMA-WIRE addable | AM-08 |
| Durable Envelope + delivery | COMP-QMA-DAEMON bus | **Epic 46 / Story 46.4** |
| Journal / fold | COMP-QMA-DAEMON | Epic 42 |
| Session pointer on Envelope | DAEMON at write | AM-02: **`product_session_ref`** |

## Additive field (AM-02 / AM-14)

Inspect Envelope required fields unchanged. **Add** `product_session_ref` (QMA `_ref` law: pointer at the product-session projection). Own identity of a ProductSession remains `product_session_id` on **that** row.

`product_session_ref` is excluded from Envelope fp1 (with `correlation_id` / `causation_id`).

Replies and questions inherit `product_session_ref` from an authorized parent and refuse retarget. Daemon-originated replies may not accept an arbitrary session.

## Admission (send and query)

When the payload **names** `product_session_ref`: resolve that product session; the connection’s operator principal **must equal** that session’s durable principal **before** append or snapshot. Ordinary product chat needs no GrantRecord.

When the field is **absent**: Quant/machine bus rows with no product conversation. Seed `send_message` remains legal for `machine`. `list_mailbox` without the field is not the product-chat snapshot.

## `list_mailbox`

Authenticated HTTP GET snapshot.

| Form | Args | Result |
| --- | --- | --- |
| Full | `{product_session_ref}` | Transcript snapshot |
| Pre-ack | `{product_session_ref, producer_id, wire_id}` | Zero or one row, including wire pair + `msg_id` |

Collision: same pair + same hash → prior result. Same pair + different hash → refuse for journal lifetime (AM-12). Missing query: `query_unavailable`.

UI stream demultiplexing (thread bound to `psess:`, no reroute on app switch) remains UI CHAT law and is carried into wire stories.

## Honesty at inspect

Mailbox types exist. `product_session_ref` **absent**. `list_mailbox` **absent**. Socket dispatch of `send_message` **absent**.
