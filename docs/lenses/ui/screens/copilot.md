---
id: LENS-UI-SCREEN-COPILOT
title: Copilot screen
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0470, DEC-0484, DEC-0454]
sources: [DEC-0470, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# Copilot screen

Conversation workspace on the platform rail (DEC-0470). Sessions, messages, preview tabs. Independent of Home. Distinct from the optional in-app copilot panel (DEC-0454).

## Data in

Session list, mailbox snapshot for the selected `product_session_ref` (CT-48; session identity remains `psess:` / `product_session_id`), preview tab view DTOs, GrantRecords for invoke. Specification only; `list_mailbox` and Svelte chrome are absent at `34c148be` (DEC-0507).

## Callbacks out

`onSelectSession(psess)`, `onSendChat` via `dispatchChat` (CT-40 `send_message` / CT-48), `onInvoke` via `dispatchInvoke` after `bindActionContext`, `onOpenPreview(view_id)`.

## States

| State | Shape |
|---|---|
| Empty | No sessions; one action to start |
| Loading | Session list skeleton |
| Error | Typed incompatibility (J-UI-13) if `list_mailbox` missing |
| Populated | Sessions + conversation + tabbed preview |

## Sample data

`psess:C` with two messages. Preview tab showing a `view:*` DTO. No widget-owned invoke.
