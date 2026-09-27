# QMX UI architecture candidate — start here

**Status:** research and architecture candidate for Codex review. Gate applied 2026-09-23 (lint clean; reviewer holes closed in the spine). Not operator-accepted. Not implementation. Not Documentation Factory.

**Workspace:** `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`

**Inspected:** 2026-09-23. `main@92279dfe` (dirty docs checkout, not modified except this sitting). `integration@34c148be` at `.worktrees/integration-inspect`. `ui@af66288` is old BMad epics — not the new UI base.

## Read in this order

1. This file
2. `ARCHITECTURE-SPINE.md` — invariants
3. `EXPERIENCE-AND-LAYOUT.md` — rail, three interiors, expand/return, composer
4. `COMPONENT-CONTRACTS.md` — QMX components vs shadcn vs adapters
5. `DESIGN.md` — provisional visual conventions
6. `CHANGE-IMPACT.md` — reuse / adapt / add / unresolved
7. `JOURNEYS.md` — J-UI-01..12 plus the frozen 85
8. `DELIVERY-AND-QA.md` — branches, slices, Reticle, packaging
9. `DECISIONS-AND-OPEN.md` — accepted, proposals, conflicts
10. `reviews/` — independent challenge (after the gate)
11. `research/` — evidence; do not treat as law. Workflow citation reports: `16` Svelte/Tauri SPA, `17` Tauri sidecar, `18` json-render/MCP Apps, `19` specialized libraries.

Handoff packet (input, not this candidate): `workroom/qmx-ui-architecture-handoff-2026-09-23/`.

## What this sitting is

Grok research + BMAD architecture (Fast path) for GAP-0081 chrome and GAP-0100 observation surfaces, over parent Workflows (09-18) and pack-and-grant kit (09-23). BMAD UX was not used. No application code on `main`. No Documentation Factory. No epics. Other Grok worktrees were not interrupted.

## Honesty in one screen

| Claim | Fact |
| --- | --- |
| Frontend exists | **No.** No first-party `package.json`, Svelte, or Tauri in git. |
| Wire types exist | **Yes** at `34c148b` (envelope, GrantRecord, `product_session`, `view:*`) — in-process tests, not e2e. |
| Live daemon protocol | **No.** `DaemonProcess` binds loopback TCP and discards bytes. |
| `caller_kind`, optional home instance, `copilot_profile` | Specified; **absent** in code. |
| Studies 01/02/03 | Rejected as baseline. Salvage listed in `research/12-rejected-studies-salvage.md`. |
| LSE ML Studio UI | Rejected as layout. |
| 85 BDD IDs | Frozen SHA `1c2c865d…`; specification only; not UI journeys. |

## Codex paste

See `CODEX-REVIEW-LAUNCH.txt`.
