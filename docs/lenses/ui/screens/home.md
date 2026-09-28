---
id: LENS-UI-SCREEN-HOME
title: Home screen
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0470, DEC-0484, DEC-0480]
sources: [DEC-0470, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# Home screen

Work / attention / resume surface on the platform rail (DEC-0470). Profile `authoring`. Independent of Copilot.

## Data in

Running JobHandles (CT-46), unknown, failed, resume targets (`psess:` or handle ids), kit listing/health/diagnosis snapshots (DEC-0480). Mailbox rows for Home chat keyed by CT-48 `product_session_ref` (excluded from Envelope fp1, DEC-0484). Specification only; `list_mailbox` and Svelte chrome are absent at `34c148be` (DEC-0507).

## Callbacks out

`onResume(psess_or_handle)`, `onOpenCopilot(psess)`, `onSendChat` via `dispatchChat` (no instance), `onCancel` via `dispatchCancel` when CT-46 `originating_product_session_ref` is present (not CT-42).

## States

| State | Shape |
|---|---|
| Empty | No running work; one action to start Copilot or Authoring |
| Loading | Skeletons inside the same attention list |
| Error | Typed refusal; shell remains usable |
| Populated | Attention rows plus optional Home chat |

## Sample data

`psess:H` authoring, no `app_instance_id`. One JobHandle `queued`. One failed handle with typed refusal text.
