---
name: Cancel and handles
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Cancel and handles

UI AD-23 stays: unique issuer `dispatchCancel`; command `cancel_job`; not `stop_run`.

## Record field (AM-04 / AM-14)

Inspect `JobHandle` has no product-session pointer. **Add optional** `originating_product_session_ref` (QMA `_ref` law).

| Admit path | Field |
| --- | --- |
| UI `dispatchInvoke` / `dispatchCancel` world | Immutable `originating_product_session_ref` of the admitting `psess:` |
| Headless QMB / no product session | **Omit** the field |

UI `cancel_job` is **unavailable** when the field is absent. Story 36.5 remains the headless abort door. The new field must not make headless work impossible.

`JobHandle.owner` remains the Quant `ActorId`.

## UI `cancel_job`

Fields: `handle_id` (**is** `job_id`), `logical_run_id`, `attempt_id`, `command_id`, `expected_state`.

**Fences:** `handle_id`/`job_id`, `logical_run_id`, and `attempt_id` must **equal** the durable handle or the command refuses. Stale-attempt retry cannot cancel a different attempt.

`command_id` namespace is the handle’s stored origin session. `expected_state` is a non-authoritative observation; `queued`→`running` does not change the canonical hash.

| Situation | Result |
| --- | --- |
| `queued`→`running` | Same `command_id` valid |
| Already terminal | Recorded no-op on `later_commands` |
| `unknown` | Not cancellable |
| Lost ack | Query; repeat same `command_id` |
| Nested child with a session | Child’s own `originating_product_session_ref` |
| Nested child headless | Field omitted; UI cancel unavailable |

## Honesty at inspect

`cancel_job` absent. `later_commands` exists. Session pointer absent.
