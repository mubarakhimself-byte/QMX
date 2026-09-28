---
id: LENS-UI-SCREEN-AUTHORING
title: Authoring screen
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0475, DEC-0487, DEC-0499]
sources: [DEC-0475, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# Authoring screen

Graph/code/detail family reachable with no app open (DEC-0470, DEC-0475). VS Code image. LSE ML Studio layout refused. QMA AD-22 RefinementProposal is not the graph/draft store (DEC-0487, DEC-0499). Specification only; drafts are absent at `34c148be` (DEC-0507).

## Data in

Graph viewport, node selection, `editor_draft_id` / `editor_revision`, validation results against immutable fp1, local authoring-pack roster after publish.

## Callbacks out

`onSaveDraft` (first save omits id), `onPublish` → `publish_editor_draft`, `onEnable` parent AD-30, `onRun` via `dispatchInvoke` after enable+grant+select. Expand/return restores viewport (DEC-0474).

## States

| State | Shape |
|---|---|
| Empty | Blank graph; save creates daemon-issued id |
| Loading | Save in flight |
| Error | Draft Run refused; stale `expected_revision` |
| Populated | Graph + code + detail for named revision |

## Sample data

Draft `editor_draft_id=D1`, `editor_revision=fp1:abc`. Run control disabled until publish+enable.
