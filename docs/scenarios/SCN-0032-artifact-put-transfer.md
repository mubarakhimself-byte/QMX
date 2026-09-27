---
id: SCN-0032
title: Local PUT then reachable transfer
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-WIRE]
decisions: [DEC-0488, DEC-0497, DEC-0502]
sources: [DEC-0497, SRC-28]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0032: Local PUT then reachable transfer

Bytes land on the authenticated local daemon first. Remote run waits for dest-authored completion (DEC-0488, DEC-0497).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

Paired operator. `registry:artifact.stage_max_bytes` is set (`GAP-0110` if null — PUT refuses). Destination environment has a recorded reachable TLS source. Loopback-only source is the negative case.

## When

Positive: HTTP `PUT /artifacts/stage` with `Content-Length` completes. Daemon recomputes fp1 plus byte count. Operator issues `transfer_artifact`. Dest pulls `GET /artifacts/<fp1>` with ticket header, verifies, authors `transfer_complete`. Invoke on that placement follows.

Interrupted PUT is a second case. Loopback-only remote transfer is a third case.

## Then

Positive: ticket reaches `complete` before invoke (DEC-0497). Interrupted v1 PUT is refused and incomplete bytes deleted; no partial fp1 (DEC-0488). Loopback-only remote route is `source_unreachable`. Silent local fallback is refused.

## Worked numbers

Completeness is fp1 plus byte count. No max-bytes number is minted here (`GAP-0110`).
