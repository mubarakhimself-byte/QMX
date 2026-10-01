---
id: SCN-0031
title: Mailbox lost-ack lookup by wire pair
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-WIRE]
decisions: [DEC-0484, DEC-0495]
sources: [DEC-0495, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0031: Mailbox lost-ack lookup by wire pair

A Home chat send that loses the ack is recovered by `(producer_id, id)`, not by inventing a new id (DEC-0484, DEC-0495).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

Paired operator principal equals product session `psess:H` principal. Client minted `producer_id=P`, wire `id=C1`, payload hash H1. Envelope persists `product_session_ref=psess:H` (excluded from Envelope fp1).

## When

`dispatchChat` issues `send_message`. The ack is lost. Client calls `list_mailbox` with `{product_session_ref, producer_id, wire_id}`.

Same pair plus different payload hash is a second case.

## Then

Same pair plus same hash returns the prior result. Same pair plus different hash refuses for journal lifetime (DEC-0495). Cold start never auto-resends (DEC-0501). Home chat used no `instance_id` and no `dispatchInvoke` (DEC-0484).

## Worked numbers

Identity is the pair `(P, C1)`, not `msg_id`, until commit.
