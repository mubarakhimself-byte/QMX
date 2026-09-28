---
id: LENS-UI-SCREEN-WIDGET-FRAME
title: WidgetFrame mini-app interior
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0474, DEC-0473, DEC-0486]
sources: [DEC-0474, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# WidgetFrame mini-app interior

Dense working canvas for a mounted pack view. Expand/return is an explicit layout change, never a fifth rail destination (DEC-0474). Widgets bind and display. Widgets never own invoke.

## Data in

Host-minted immutable `ActionContext` (DEC-0486). Pack `view:*` DTO. Matching GrantRecords (zero, one, or `GRANT_AMBIGUOUS`). Graph viewport state to restore on return.

## Callbacks out

`onBind` / `onDisplay` only from the widget. `onInvoke` goes through `dispatchInvoke` with the host ActionContext. `onExpand` / `onReturn` restore the graph viewport (DEC-0474). Composer tools come from parent AD-9 intersection (DEC-0473).

## States

| State | Shape |
|---|---|
| Empty | Mounted view with no rows; paint allowed |
| Loading | Skeleton inside the same frame |
| Error | Typed refusal including `GRANT_AMBIGUOUS`; shell remains usable |
| Populated | Working widgets; expand fills the canvas |

## Sample data

`view_id` `board`. One GrantRecord. Graph viewport `{x: 40, y: 12, zoom: 0.85}` restored on return.
