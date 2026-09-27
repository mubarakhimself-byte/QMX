---
name: Cancel and handles
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Cancel and handles

UI AD-23 stays: unique issuer `dispatchCancel`; command `cancel_job`; not `stop_run`; not a second invoke.

## Additive handle field (AM-04)

Inspect `JobHandle` has `job_id`, owner Quant, state, `task_id`, `wake_mailbox`, `logical_run_id`, `attempt_id`, artifacts, `later_commands`. **No** `originating_psess`.

At **admit**, store immutable `originating_psess` (the `psess:` that started the work). Snapshots expose it. It is not rewritten on `queued`→`running`.

`originating_psess` is **not** `JobHandle.owner`. `owner` remains the Quant `ActorId` (QMA AD-17). Cancel authority for the UI path is the **operator principal of `originating_psess`**. Headless QMB cancel stays the existing production door (Story 36.5) and is not this command.

Authority: **operator** principal of that session. Observation (Home attention, another `psess:`, `machine`) is not cancel authority.

## Nested children (Epic 63)

A nested Mission gets **its own** JobHandle (already planned). At child admit, store the `originating_psess` of the **starter of that child**. Cancel the child through the same `cancel_job`. Do not splice graphs. Do not union grants (Story 63.1 / 60.4).

## Command

Addable CT-40 `cancel_job`: `handle_id`, `logical_run_id`, `attempt_id`, `command_id` (product-session namespace, parent AD-29), `expected_state` (handle state + `attempt_id`).

| Situation | Result |
| --- | --- |
| `queued`→`running` before cancel lands | Same `command_id` still valid |
| Already terminal | Recorded no-op on existing `later_commands` |
| `unknown` | Not cancellable; `unknown.resolve` only |
| Lost ack | Query snapshot; repeat **same** `command_id` |
| Race with complete | First durable terminal wins |

`stop_run` remains the seed agent/mission stop. Widgets never import the wire client.

## Persistence

In-memory `JobHandleStore` at inspect is an **adoption gap** versus Epic 42 / 57 sqlite `task_graph_state`. `originating_psess` lands on that durable row, not a second store.

## Honesty at inspect

`cancel_job` absent from vocabulary. `JobHandle.cancel` exists as an in-process operation. `later_commands` exists. `originating_psess` absent.
