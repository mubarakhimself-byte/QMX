# QMX UI backend-delta architecture — start here

**Status:** draft candidate for joint UI/backend review. Not operator-accepted. Not implementation. Not Documentation Factory. Not an epic backlog rewrite.

**Workspace:** `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/`

**Inspected:** 2026-09-24. `main@92279dfe43922d60fabe38e29284ca52956ab75c`. `integration@34c148be404a375cbfd79fd4ce6997452e4f1d20` at `.worktrees/integration-inspect`. Existing epics are **planned requirements**, not delivered product.

## What this sitting is

A BMAD architecture **backend-delta** over the reviewed UI candidate (`architecture-QMX-UI-2026-09-23`). It scopes daemon, wire, QMB, mailbox, cancel, artifact, pack-ingest, draft, credential, and compatibility work the UI needs. It does not redesign chrome, Svelte, or storyboard layouts.

R2 pairing issuance is **resolved here** and reconciled into the UI candidate. The other eight UI findings stay closed.

## Read in this order

1. This file
2. `CLOSURE-EVIDENCE.md` — R2 closed; UI R1/R3–R9 preserved
3. `ARCHITECTURE-SPINE.md` — local AD-1..AD-16
4. `PARENT-AMENDMENT-MAP.md` — every conflict with inherited law, named
5. `DEPENDENCY-MAP.md` — supplement inventory vs Epics 41–42, 46.4, 57, 60–65
6. Companions: `PAIRING-AND-ADMISSION.md`, `HOST-LIFECYCLE.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `ARTIFACTS-AND-TRANSFER.md`, `PACK-UI-AND-AUTHORING.md`, `PROVIDER-AND-COMPAT.md`
7. `TRACE-MATRIX.md`, `UI-CANDIDATE-CHANGELOG.md`
8. `REVIEW-LAUNCH.txt` — paste for the joint review
9. `research/` — evidence, not law

UI candidate (reconciled in place, changelog in this workspace): `../architecture-QMX-UI-2026-09-23/`. Intake: `workroom/qmx-ui-closure-round2-2026-09-24/`.

## Honesty in one screen

| Claim | Fact |
| --- | --- |
| Live CT-40 server | **No.** `DaemonProcess._handle_client` discards TCP bytes. |
| `send_message` name | **Yes** in `qma-wire` vocabulary. Not dispatched on the socket. |
| `list_mailbox`, `cancel_job`, `/pair/*`, `stage_artifact`, `qmb host` | **Absent** at inspect. |
| Mailbox `Envelope` | **Yes** as CT-48 types. **No** `product_session_id` field. |
| JobHandle | **Yes** as types + in-memory store. **No** `originating_psess`. `later_commands` exists. |
| `PluginManifest.copilot_profile` / `caller_kind` | Specified in Epic 60. **Absent** in code. |
| Pairing table | **Absent.** |
| This sitting implemented anything | **No.** |

## After joint review

One integrated Documentation Factory pass → coordinated epics/stories amendments and additions → software-factory execution. This sitting starts none of those.
