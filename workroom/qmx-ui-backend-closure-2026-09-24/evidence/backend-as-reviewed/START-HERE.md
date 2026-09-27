# QMX UI backend-delta architecture — start here

**Status:** draft candidate after joint-review J1–J5 amendment. Ready for Codex closure review. Not operator-accepted. Not implementation. Not Documentation Factory. Not an epic backlog rewrite.

**Workspace:** `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/`

**Inspected:** 2026-09-24. `main@92279dfe43922d60fabe38e29284ca52956ab75c`. `integration@34c148be404a375cbfd79fd4ce6997452e4f1d20` at `.worktrees/integration-inspect`. Existing epics are **planned requirements**, not delivered product.

## What this sitting is

A BMAD architecture **backend-delta** over the reviewed UI candidate (`architecture-QMX-UI-2026-09-23`). It scopes daemon, wire, QMB, mailbox, cancel, artifact, pack-ingest, draft, credential, and compatibility work the UI needs. It does not redesign chrome, Svelte, or storyboard layouts.

R2 pairing issuance stays **closed**. Joint-review J1–J5 and the report’s small reconciliations are bound here and reconciled into the UI candidate. UI findings R1, R3–R9 stay closed.

## Read in this order

1. This file
2. `CLOSURE-J1-J5.md` — J1–J5 evidence, traces, deferrals
3. `CLOSURE-EVIDENCE.md` — R2 preserved; J1–J5 added
4. `ARCHITECTURE-SPINE.md` — local AD-1..AD-17
5. `PARENT-AMENDMENT-MAP.md` — every conflict with inherited law, named (AM-01..AM-16)
6. `DEPENDENCY-MAP.md` — supplement inventory vs Epics 41–42, 46.4, 57, 60–65
7. Companions: `PAIRING-AND-ADMISSION.md`, `HOST-LIFECYCLE.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `ARTIFACTS-AND-TRANSFER.md`, `PACK-UI-AND-AUTHORING.md`, `PROVIDER-AND-COMPAT.md`
8. `TRACE-MATRIX.md`, `UI-CANDIDATE-CHANGELOG.md`
9. `REVIEW-LAUNCH.txt` — paste for Codex closure review
10. `research/` — evidence, not law

UI candidate (reconciled in place, changelog in this workspace): `../architecture-QMX-UI-2026-09-23/`. Intake: `workroom/qmx-ui-closure-round2-2026-09-24/`.

## Honesty in one screen

| Claim | Fact |
| --- | --- |
| Live CT-40 server | **No.** `DaemonProcess._handle_client` discards TCP bytes. |
| `send_message` name | **Yes** in `qma-wire` vocabulary. Not dispatched on the socket. |
| `list_mailbox`, `cancel_job`, `/pair/*`, `stage_artifact`, `qmb host` | **Absent** at inspect. |
| Mailbox `Envelope` | **Yes** as CT-48 types. **No** `product_session_ref` field. |
| JobHandle | **Yes** as types + in-memory store. **No** `originating_product_session_ref`. `later_commands` exists. |
| `PluginManifest.copilot_profile` / `caller_kind` | Specified in Epic 60. **Absent** in code. |
| Pairing table | **Absent.** |
| This sitting implemented anything | **No.** |

## After Codex closure review

One integrated Documentation Factory pass → coordinated epics/stories amendments and additions → software-factory execution. This sitting starts none of those.
