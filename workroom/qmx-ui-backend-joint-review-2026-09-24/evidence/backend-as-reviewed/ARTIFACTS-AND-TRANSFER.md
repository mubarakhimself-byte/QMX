---
name: Artifacts and transfer
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Artifacts and transfer

UI AD-22 stays: local possession first; interrupted v1 PUT refused; explicit transfer for remote placement.

## PUT `/artifacts/stage` (AM-05)

| Field | Contract |
| --- | --- |
| Owner | COMP-QMA-DAEMON |
| Transport | Authenticated HTTP PUT, raw body, `Content-Length` required |
| Auth | Same pairing proof as GET snapshots |
| Max | `registry:artifact.stage_max_bytes` (no number minted here) |
| Register | Existing `before_artifact_register` / fp1 |
| Completeness | Daemon hash **plus** byte count after complete bytes |
| Interrupt | Connection close before `Content-Length` bytes → refuse, **delete** incomplete object, no fp1. Retry = new full PUT. Same complete hash may reuse. |
| Partial PUT | **Not used.** RFC 9110 §14.5 remains unused in v1 |
| Return | fp1 + byte count + completeness `complete` |
| Forbidden | JSON-RPC body; query-string id; browser hash as possession; MCP/json-render PUT |

PUT is a byte channel on the daemon origin (AD-15). It is not invoke.

Home may stage with no `instance_id`. Result is **local-complete** fp1, not remote placement.

## Transfer (AM-06)

When the selected instance’s execution placement is **not** this daemon:

1. Operator (via host) issues addable command `transfer_artifact` `{fp1, destination_placement}`.
2. Daemon records a **transfer ticket** (journal-projected; not a new store class) bound to that fp1 and destination.
3. Destination worker/env **dials out** as `machine` and **pulls** `GET /artifacts/<fp1>` with Story 41.4 `credential_ref` and header `X-QMX-Transfer-Ticket: <ticket_id>` (Story 41.4: daemon never dials in). No query-string token. No pairing Bearer on this GET.
4. Destination recomputes hash + byte count. Mismatch or incomplete → delete dest object; local fp1 remains local-complete; typed refusal; **no** silent local run.

Same-daemon instance: no transfer.

Interrupted transfer: destination has no complete object. Invoke on that placement refuses.

## Honesty at inspect

PUT path **absent**. `transfer_artifact` **absent**. Cite-copy through `before_artifact_register` **present** (pattern to reuse). Artifact store is an Epic 42 independent store — reuse, do not mint a Library database.
