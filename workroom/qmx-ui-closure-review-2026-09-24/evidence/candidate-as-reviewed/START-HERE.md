# QMX UI architecture candidate — start here

**Status:** amended after Codex R1–R9. Candidate defaults, not operator-accepted. Not implementation. Not Documentation Factory.

**Closure map:** `CLOSURE-MAP.md`

**Workspace:** `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`

**Inspected:** 2026-09-23. `main@92279dfe` (dirty docs checkout, not modified except this sitting). `integration@34c148be` at `.worktrees/integration-inspect`. `ui@af66288` is old BMad epics — not the new UI base.

## Read in this order

1. This file
2. `CLOSURE-MAP.md` — R1–R9 dispositions
3. `ARCHITECTURE-SPINE.md` — invariants (local AD-1..AD-24)
4. `EXPERIENCE-AND-LAYOUT.md` — Home, Copilot, Library, Authoring
5. `BOOTSTRAP-AND-AUTH.md`, `CHAT-AND-HISTORY.md`, `VIEW-AND-PACK-CONTRACT.md`, `AUTHORING-AND-ML.md`, `LIBRARY-AND-ATTACHMENTS.md`
6. `TRACE-MATRIX.md`, `EXAMPLES.md`
7. `COMPONENT-CONTRACTS.md`, `DESIGN.md`
8. `CHANGE-IMPACT.md`, `JOURNEYS.md`, `DELIVERY-AND-QA.md`, `DECISIONS-AND-OPEN.md`
9. `reviews/` after the post-amendment gate
10. `research/` — evidence, not law

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
