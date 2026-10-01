---
id: RIDER-UI-BACKEND-2026-09-25
title: Operator rulings — QMX UI host plus backend-delta absorption
type: rider
status: authoritative
date: 2026-09-25
---

# Operator rulings for the 2026-09-25 UI + backend-delta change-mode pass

These rulings are operator-direct. They win over architecture-package leftover `status: draft` / `not operator-accepted` YAML. The operator launched `/documentation-factory` in a fresh session after Codex's 25 September 2026 recheck returned **PASS — ready for one integrated Documentation Factory pass**. That launch is the acceptance stamp for both packets as the plan to fold.

This session folds the increment into the existing `docs/` knowledge base (route **e**, change mode, Stage 9). It does not implement production code, re-run architecture, start epics-and-stories, or start factory coding lanes. It does not rewrite the 2026-09-16 QML fold, the 2026-09-19 Workflows fold, or the 2026-09-23 pack-and-grant fold. ADR-0024 and ADR-0025 Decision sections stay as written; this sitting adds dated follow-ups.

## Packets

1. **UI host** — `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/` (local UI AD-1..AD-24). Citation surface: `ARCHITECTURE-SPINE.md`, `START-HERE.md`, `EXPERIENCE-AND-LAYOUT.md`, `BOOTSTRAP-AND-AUTH.md`, `CHAT-AND-HISTORY.md`, `VIEW-AND-PACK-CONTRACT.md`, `AUTHORING-AND-ML.md`, `LIBRARY-AND-ATTACHMENTS.md`, `COMPONENT-CONTRACTS.md`, `DESIGN.md`, `JOURNEYS.md`, `TRACE-MATRIX.md`, `EXAMPLES.md`, `CLOSURE-MAP.md`, `BACKEND-DEPENDENCIES.md`, `DELIVERY-AND-QA.md`, `CHANGE-IMPACT.md`, `DECISIONS-AND-OPEN.md`, `.memlog.md`.
2. **Backend-delta** — `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/` (local backend AD-1..AD-17). Citation surface: `ARCHITECTURE-SPINE.md`, `START-HERE.md`, `PARENT-AMENDMENT-MAP.md`, `DEPENDENCY-MAP.md`, `PAIRING-AND-ADMISSION.md`, `HOST-LIFECYCLE.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `ARTIFACTS-AND-TRANSFER.md`, `PACK-UI-AND-AUTHORING.md`, `PROVIDER-AND-COMPAT.md`, `TRACE-MATRIX.md`, `CLOSURE-C1-C2.md`, `CLOSURE-J1-J5.md`, `CLOSURE-EVIDENCE.md`, `UI-CANDIDATE-CHANGELOG.md`, `.memlog.md`.
3. **Codex closure** — `workroom/qmx-ui-final-closure-2026-09-24/REVIEW.md` and `RECHECK-2026-09-25.md`.
4. **Session transcripts** (operator words / sitting history, not a second spine): `[backen-ui]` (UI architecture sitting) and `[ui-arch]` (backend-delta sitting) at the QMX desktop root.

Parents bind read-only: architecture-QMX-2026-09-18 AD-1..AD-31, architecture-QMX-2026-09-23 kit AD-1..AD-9, architecture-QMA-2026-08-28, ADR-0024, ADR-0025. Local `UI AD-n` and `backend AD-n` never mean a parent or kit id.

Pins: docs workspace `main` (this checkout). Implementation inspect `integration@34c148be` via `.worktrees/integration-inspect`. Parent freeze `270e992` still applies for ADR-0024 original Decision text. Fixtures are not e2e (DEC-0286, DEC-0465). Existing epics (including 41–42, 46.4, 57, 60–65) are **planned requirements**, not delivery.

## Standing corrections (ratified)

- The product UI is a **Svelte client** of `qma-wire` talking to `qma-daemon`. It is **not** a COMP. No `COMP-UI`. No sixth application. No new CT number.
- One persistent platform rail. Destinations above the divider with zero opened apps: **Home** (work / attention / resume), **Copilot** (conversation), **Library**, **Authoring**. They may share components. They are not the same destination. Headless packs stay first-class.
- v1 is a **browser plus an externally running daemon**. The browser does not spawn Python. Privileged owner is COMP-QMB `qmb host …` over **local host-control**. Tauri 2 is a later optional desktop shell.
- First operator on a clean root is the OS user of `QMA_DAEMON_ROOT` plus a daemon-minted `host_control` token. Browser pairing **maps** to that principal. Provider `cred://` is not login. Broker allowlist is not widened.
- `pairing_proof` is a bearer credential. `pairing_record_id` is the nonsecret journal identity. A remembered Origin **never** issues a new proof. Issuance is QMB confirm of that pending, or authenticated `/pair/renew` with a still-valid proof. Cookies, `localStorage`, and IndexedDB are forbidden for the proof.
- Lost `host_control` recovery is `qmb host recover-control` on a **stopped** daemon by the OS owner of the root, without presenting the lost token. `rotate-control` remains the live-token path. Empty root means no `local_operator`. Missing token plus existing principal is not first-start bootstrap.
- `qmb host stop` on a running daemon requires current `host_control`, **except** when that file is missing or unreadable: then the OS owner of the root may stop so recovery can run. Do not broaden that exception into unauthenticated stop.
- Origin-revoke (`qmb host pair revoke --origin <origin>`) is a `journal_seq` barrier. Renew-then-revoke kills the new proof. Revoke-then-renew of the old proof refuses. `--session` is that record only. After the barrier, a new `/pair/start` is legal (re-pair).
- Durable mailbox delivery stays Epic 46 / Story 46.4. Additive Envelope field is `product_session_ref` (excluded from Envelope fp1). `list_mailbox` is an addable Epic 41 query. Chat issuer is `dispatchChat` → `send_message`. Home chat needs no instance.
- Unique invoke issuer is `dispatchInvoke`. Unique cancel issuer is `dispatchCancel` → addable `cancel_job`. JobHandle optional field is `originating_product_session_ref` (omitted on headless).
- Artifact bytes land by authenticated HTTP `PUT /artifacts/stage`. Interrupted v1 upload is refused. Remote run needs explicit `transfer_artifact` on a recorded reachable TLS source plus dest-authored `transfer_complete`.
- Daemon is the sole durable `editor_draft_id` issuer. First Run is `publish_editor_draft` into the **local authoring pack** then parent AD-30 enable. QMA AD-22 RefinementProposal is not the graph editor store.
- `PluginManifest.copilot_profile` stays Epic 60 / kit sibling field. `PackUiRequest` references it and must not replace it. Do not duplicate FEAT-0058..FEAT-0063 or Epics 60–65.
- Same-tab reload may restore proof from `sessionStorage`. Closed tab is cold start: empty storage, `list_mailbox` restore, never auto-resend. Cloned tab copies storage: existing proof plus a new `producer_id` if the old one is live. `/pair/renew` is an explicit rotate, not the clone path.
- GAP-0081 chrome and GAP-0100 observation surfaces are **answered sitting law** of this UI sitting. They are no longer open design questions. They remain out of the pack-and-grant kit as kit holes. Delivery is the new FEAT-0064+ slices. Inspect absence at `34c148be` is wiring honesty, not a gap.
- Codex non-blocking cleanup is sitting law: AM-10's generic running-daemon token sentence must cite the AD-17 / HOST-LIFECYCLE OS-owner stop exception when the token file is missing or unreadable.

## Named constitution work (this pass must write)

L7 annotation: the Svelte host is still composition over existing applications — not a sixth COMP. L31 annotation: the UI attaches over `qma-wire`; it does not re-implement QMF contracts in TypeScript. Do not reopen Book/ATC/fencing. Do not rewrite L36.

## Evidence honesty

Do not describe proposed connects as implemented. At `34c148be`:

**CONNECT (types/fixtures exist; not e2e):** InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, `view:*` DTOs, JobHandle types + in-memory store, mailbox Envelope types (CT-48), `later_commands`.

**AMEND relative to this sitting:** Envelope has no `product_session_ref`; JobHandle has no `originating_product_session_ref`; ProductSession `app_instance_id` still required `str`; envelope has no `caller_kind`.

**ABSENT as product surface:** live CT-40 server (`DaemonProcess` discards TCP bytes); `/pair/*`; `qmb host`; pairing table; `list_mailbox`; `cancel_job`; `stage_artifact` / PUT; `transfer_artifact` / `transfer_complete`; `save_editor_draft` / `publish_editor_draft` / `get_editor_draft_head`; `get_pack_ui_request`; `host_control` / `recover-control`; `PluginManifest.copilot_profile`; first-party Svelte/Tauri frontend.

## Out of this pass

- Do not fill GAP-0085, GAP-0063, GAP-0061, GAP-0062, GAP-0058, GAP-0093, GAP-0096.
- Do not mint COMP-UI, COMP-WF, or a new CT number. Additive CT-40 / CT-42 / CT-48 family annotations only.
- Do not duplicate Epics 60–65 / FEAT-0058..FEAT-0063 as new features.
- Do not pin json-render or MCP Apps as identity. Seed versions in stack.md are optional painters.
- Do not start videos, n8n, Hermes, or a BMAD UX redesign.
- Do not write QMX production code.
- Do not emit a BMAD epics-and-stories prompt in this session.
- Do not freeze CodeMirror vs Monaco (later fidelity spike). Do not make Tauri v1-required.
- Trading ticket chrome (UX-10) stays a later trading-app sitting.

## Dead list (honor)

DEC-0084 / 0085 / 0086 stay dead. DEC-0361 marketplace, DEC-0362 solver, DEC-0366 HMR stay dead. DEC-0408..0413 mill deaths stay dead. Study 01/02/03 as baseline stay rejected (salvage already listed). LSE ML Studio as layout stays refused. Qt host stays refused. Screen-kit and automation-kit as the center stay dead. Third ProductSessionProfile stays un-minted. Merged live Task Graphs stay refused. Cookie session stays refused. `ui_view` contribution point stays un-minted. JSON Render / MCP Apps as identity, persistence, runtime, or authority stay dead. QMA AD-22 stays one RefinementProposal type.

## Cheap-veto (sitting machinery)

Each item is overturnable in one line without unwinding another call:

| Id | Item | Default if no veto |
|---|---|---|
| A10 | `registry:pairing.session_ttl` exists; this sitting mints no duration | proceed |
| A11 | `registry:artifact.stage_max_bytes` exists; this sitting mints no number | proceed |
| A12 | shadcn-svelte Rhea compact is the working visual seed, not a brand freeze | proceed |
| A13 | Node.js `>=22.12.0 <23.0.0` and pnpm lockfile at an unexecuted scaffold gate | proceed |
| A14 | Product data root Windows `%LOCALAPPDATA%\QMX\qma-daemon` (and the POSIX rows in HOST-LIFECYCLE.md) | proceed |

Not vetoable here: no sixth COMP; no new CT; Origin-never-sufficient issuance; no cookies/`localStorage` proof; no COMP-UI; Epic 60 `copilot_profile` stays a sibling field; recover-control does not remint a principal or wipe journals; QMB never writes daemon sqlite.
