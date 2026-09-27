---
name: Artifacts and transfer
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
closes: joint-review J5
---

# Artifacts and transfer

UI AD-22 stays: local possession first; interrupted v1 PUT refused; explicit transfer for remote placement.

## PUT `/artifacts/stage`

Authenticated HTTP PUT, raw body, Content-Length, Bearer pairing proof, paired Origin. Missing `registry:artifact.stage_max_bytes` **refuses** the PUT (no number minted here). Completeness = daemon hash + byte count. Interrupt → delete incomplete. No partial PUT. Reuse `before_artifact_register`. Home may stage with no instance. Result is **local-complete** fp1.

There is **no** JSON-RPC `stage_artifact`.

## Transfer topology (J5)

Default source bind is loopback. A remote environment **cannot** dial `127.0.0.1` on the laptop.

**Supported route:** destination pulls from the **source daemon’s recorded reachable HTTPS origin**. Issuance of `transfer_artifact` **refuses** `source_unreachable` unless:

1. Source origin is recorded non-loopback TLS, and
2. That origin is on the destination environment’s inherited network allowlist.

Never silently expose loopback. Never fall back to local invoke. Same-daemon instance: no transfer.

A different-daemon copy uses the same ticket, audience, and completion ack. That copy still requires a **registered authenticated destination control connection** and a reachable allowed source. This sitting does not define inter-daemon discovery or relay.

## Ticket

Operator command `transfer_artifact` with durable `command_id` (product-session namespace when a `psess:` is present). Projection `artifact_transfer_ticket`:

- `ticket_id`
- source origin
- fp1 + byte count
- operator / `product_session_ref` (when present)
- destination environment identity + placement revision
- **exact machine `credential_ref` audience** allowed to redeem
- state: `issued` \| `notified` \| `claimed` \| `complete` \| `failed` \| `expired`

The command returns `ticket_id`. Notify the already-authenticated destination control connection **when that connection is live** (worker dial-out to **its** daemon; that daemon then pulls the recorded source origin). If dest control is down, the ticket stays `issued` until dest reconnect then `notified`. Only that audience may `GET /artifacts/<fp1>` with `X-QMX-Transfer-Ticket: <ticket_id>` and Story 41.4 machine `credential_ref`. Wrong credential → refuse. Loopback source → never offered as a GET target. Source never writes dest bytes. Dest never writes source journal except the `transfer_complete` ack received on the source.

## Completion

After dest hash + byte-count verify and durable placement, dest authors addable `transfer_complete` `{ticket_id, fp1, byte_count}` (machine principal, dest daemon sole writer of dest store; source daemon records the ack). Idempotent on `ticket_id` / original `command_id`. Lost ack: dest retries `transfer_complete`; source returns prior complete. Interrupted pull: dest deletes incomplete; ticket stays `claimed` until complete, failed, or expired. **Invoke on that placement refuses until ticket `complete`.** Failure leaves source local-complete fp1.

## Traces (unexecuted)

| ID | Intent |
| --- | --- |
| T-X-01 | Recorded TLS source + matching dest audience → complete ack → invoke allowed |
| T-X-02 | Loopback-only source → `source_unreachable`; no local fallback invoke |
| T-X-03 | Wrong dest credential → GET refuse |
| T-X-04 | Hash mismatch / interrupt → dest incomplete deleted; invoke refuses |
| T-X-05 | Lost `transfer_complete` → retry same ids → one complete ticket |
