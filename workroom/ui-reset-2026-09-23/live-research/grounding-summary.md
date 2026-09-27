# QMX: corrected design grounding

2026-09-23, afternoon. This supersedes the earlier recommendation to start by designing one widget journey. It is a discovery record, not a finalized specification.

## What the board actually contains

The current saved board has 20 text elements, including the full 16,804-character bottom dictation; 11 image placements from 10 unique image files; 23 arrows; seven web links; and one local video. The decoded scene and Markdown transcription agree after whitespace normalization. The original file was not edited. See the complete [dictation audit](dictation-audit.md) and [current scene text](board-current/scene-text.json).

The expanded-widget/workflow label and orange connector are present. The connector starts at an empty small rectangle; its intended image target is ambiguous. The separate cluster of eight screenshot arrows is also present. We can read the text without the user copying it into a separate note.

## Preserve the whole design picture

| Design area from the user's dictation | What must remain visible in subsequent design work |
|---|---|
| Home and active work | A persistent home overview of everything running; fixed menu, divider, then opened-app icons. Opened, running, and stopped are not automatically the same state. |
| Main agent workspace | Broader access, session/history controls, and flexible previews for apps, widgets, workflows, browser/video, code/diff, terminal, strategies and models. |
| Mini-app workspace | A composition of widgets and workflows with purposeful, dynamic app sections; Overview is a summary, not necessarily a standalone widget. |
| Widget/workflow detail | Compact and detailed representations, with top-tab expansion proposed by the user. Standalone widget and workflow representations are still unspecified. |
| Scoped copilot | App/object context, attach-to-chat affordances, visible tools and permissions different from the main agent. |
| Global library | Accessible from any mini-app; preserve the user's correction toward the sidebar. Define locating, saving, reusing and opening separately. |
| Authoring and use | Code and node-based creation remain distinct from previews and normal app use. Placement/category information is supplied during building. |
| Shared conventions | Reusable toolbars where needed, scoped settings, history, widget editing/add controls, status/local-versus-server indications, and eventual developer conventions/SDK. |

## What real reference research added

All seven linked sites plus OpenBB were inspected through the browser. Three lower-end agents handled text coverage, OpenBB, and Xynth/Prime; the primary agent researched QuantX, LSE, Minara and the two technical links.

| Reference | Evidence reached | Useful comparison for QMX |
|---|---|---|
| [OpenBB](https://openbb.co/products/workspace/) | Official docs, public recorded demo, login boundary | App templates become editable dashboards; page tabs, reusable widgets, linked parameters, and explicit Copilot context. Widget fullscreen/new-tab expansion was not established. |
| [Xynth](https://xynth.com/) | Public composer/library and an alert page, with account/delayed-content restrictions | Research output can have a dashboard, description, canvas, previous runs, and a contextual follow-up conversation. |
| [Prime](https://prime-terminal.com/) | Interactive public Smart Bias Tracker demo | A dense summary matrix can switch to a detail view with a category rail and narrative. Visual inspection corrected an earlier mistaken side-by-side interpretation; the matrix is not visible in the detail capture. Demo data/date inconsistencies mean it is layout evidence, not market evidence. |
| [QuantX](https://quantx.es/signup#das) | Official dashboard/builder/results/document screenshots; app login gate | Node authoring, analytical result views and document-scoped chat deserve attention alongside dashboard layout. |
| [LSE](https://www.londonstrategicedge.com/machine-learning-studio/) | Actual public dataset search, selection, Train/Optimise and method switching | App-specific navigation and guidance change together; prerequisite and empty states make the workflow understandable. |
| [Minara](https://minara.ai/app/strategy-studio) | Actual public Chat/Workflow/Strategy workspaces; creation login gate | A persistent global rail can coexist with local history, app navigation and multiple ways to begin authoring. |

Reports preserve actions, sources and limits: [OpenBB](openbb.md), [Xynth/Prime](xynth-prime.md), [QuantX/LSE/Minara and technical references](quantx-lse-minara.md). Saved screenshots are in [screenshots](screenshots/). We infer why patterns may help QMX; we do not know the companies' internal design rationale or claim to have tested their authenticated products end to end.

## Backend implications and worktree choice

The source inventory already found real workflow/taskgraph, discovery, grant and durable product-session foundations. Mini-app use is not an empty backend. The explicit UI contract is still a stub, and the change-request flow inspected is a fixture, not a ready production editing API. Closing a visual tab must not silently terminate a durable session. See [backend grounding](../backend-grounding.md) for exact paths/commit and verification limits.

The UI questions now needing contracts include compact/detail renderers, app pages and category metadata, shared parameter scope, library-object identity, visible context/authority, and layout restoration. These are candidate integration questions, not a claim that every capability needs new backend implementation. Recheck code before deciding a gap.

For implementation, an isolated worktree is sensible because backend work is concurrent. Choose its base deliberately: root `main` and the old `ui` checkout are not interchangeable with the inspected integration commit. No worktree was created in response to the user's question, and no application code was changed. Grok's observability/logging work remains outside this task's changes.

## Resume here

Present the whole workspace as a small set of connected areas and walk through them with the user. Keep their tentative ideas tentative. Only then choose which uncertain behavior needs a comparison or prototype. Do not turn a reference product's menu into QMX requirements, revive legacy BMAD designs, or choose a frontend stack merely because a reference uses it.
