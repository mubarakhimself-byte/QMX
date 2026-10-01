---
id: ADR-0026
title: QMX UI host and backend-delta — differentiated-shell client, pairing, host-control
type: adr
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON, COMP-QMB]
decisions: [DEC-0469, DEC-0470, DEC-0471, DEC-0472, DEC-0473, DEC-0474, DEC-0475, DEC-0476, DEC-0477, DEC-0478, DEC-0479, DEC-0480, DEC-0481, DEC-0482, DEC-0483, DEC-0484, DEC-0485, DEC-0486, DEC-0487, DEC-0488, DEC-0489, DEC-0490, DEC-0491, DEC-0492, DEC-0493, DEC-0494, DEC-0495, DEC-0496, DEC-0497, DEC-0498, DEC-0499, DEC-0500, DEC-0501, DEC-0502, DEC-0503, DEC-0504, DEC-0505, DEC-0506, DEC-0507, DEC-0508, DEC-0509, DEC-0510]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/PARENT-AMENDMENT-MAP.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/DEPENDENCY-MAP.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/CLOSURE-C1-C2.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/CLOSURE-J1-J5.md, workroom/qmx-ui-final-closure-2026-09-24/REVIEW.md, workroom/qmx-ui-final-closure-2026-09-24/RECHECK-2026-09-25.md, _docwork/riders/ui-and-backend-delta-2026-09-25.md, _docwork/ui-backend-increment-brief.md, _docwork/ledger.yaml, docs/decisions/ADR-0024-workflows-construction-kit.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 1y
---

# ADR-0026: QMX UI host and backend-delta — differentiated-shell client, pairing, host-control

Date: 2026-09-25. Status: accepted (docs authority only).

## Context

The 2026-09-19 Workflows construction kit ([ADR-0024](ADR-0024-workflows-construction-kit.md)) and the 2026-09-23 pack-and-grant kit ([ADR-0025](ADR-0025-pack-and-grant-kit.md)) bound composition, grants, envelopes, JobHandles, and the host SDK. They left chrome and the daemon/QMB doors a browser needs unnamed. GAP-0081 and GAP-0100 were out-of-scope as kit holes because the user interface was not designed (DEC-0468).

Two BMAD architecture sittings closed that hole as a candidate, then Codex reviewed them:

- `architecture-QMX-UI-2026-09-23` — differentiated-shell Svelte client (local UI AD-1..AD-24). Codex R1–R9 closed.
- `architecture-QMX-UI-BACKEND-2026-09-24` — pairing, host-control, mailbox field, cancel field, artifact PUT/transfer, drafts, PackUiRequest (local backend AD-1..AD-17, AM-01..AM-17). Joint-review J1–J5 and focused C1/C2 closed.

Codex 2026-09-24 focused closure plus 2026-09-25 recheck: **PASS — ready for one integrated Documentation Factory pass**. The operator launched this change-mode fold the same day. This ADR records the absorption. It does not authorize implementation, credentials, a live session, order submission, promotion, or go-live — those arrive only through the factory pipeline (DEC-0504). ADR-0024 and ADR-0025 Decision sections stay as written. Named inherited-contract amendments are AM-01..AM-17 (DEC-0506). No sixth COMP. No COMP-UI. No new CT number (DEC-0505).

Planning checkout is this `main` workspace. Implementation was inspected on `integration@34c148be` via `.worktrees/integration-inspect` without switching branches. Parent freeze honesty at `270e992` still applies for ADR-0024 original Decision text (DEC-0450). Fixtures are not e2e (DEC-0286, DEC-0465, DEC-0507). Existing epics 41–42, 46.4, 57, 60–65 are planned requirements, not delivery.

Cite parent 09-18 ADs as `parent AD-n`. Cite kit 09-23 ADs as `kit AD-n`. Cite this sitting as `UI AD-n` or `backend AD-n`.

## Options considered

1. **Mint COMP-UI / a sixth application** — rejected because QMF stays one framework (L7) and parent AD-1 already forbids a sixth application (DEC-0414, DEC-0462, DEC-0505, DEC-0508).
2. **Qt or React/Next host** — rejected by sitting direction and UI AD-2 (DEC-0469).
3. **Origin-only pairing issuance / cookie login** — rejected by R2 and backend AD-3 (DEC-0491, DEC-0508).
4. **Browser-spawned Python daemon** — rejected by UI AD-19 / backend AD-6 (DEC-0485, DEC-0494).
5. **Differentiated-shell Svelte client over pack-and-grant host, with named daemon/QMB adds** — chosen (DEC-0504).

## Decision

The UI host spine UI AD-2..AD-24 and the backend-delta spine backend AD-3..AD-17 are adopted as DEC-0469 through DEC-0503. The umbrella is DEC-0504. Architecture-preflight is DEC-0505. Named inherited-contract amendments are DEC-0506. Wiring honesty at `34c148be` is DEC-0507. Dead-list honors are DEC-0508. GAP catalog restamp is DEC-0509. Cheap-veto A10–A14 ride DEC-0510.

- **Client, not a COMP (DEC-0505).** The product UI is a client of `qma-wire` (CT-40) talking to `qma-daemon`. Identity, grants, envelopes, JobHandles, and op execution stay in existing COMPs. Chrome never becomes a scheduler or a grant store.
- **Rail (DEC-0470, R1).** Destinations above the divider with zero opened apps: Home (work / attention / resume), Copilot (conversation), Library, Authoring. They may share components. They are not the same destination. Headless packs stay first-class (DEC-0471).
- **Stack seed (DEC-0469).** Svelte 5.57.1, SvelteKit 2.70.3 `adapter-static` `ssr=false`, TypeScript 5.9, Vite 8.3.0, Tailwind 4.3.3, shadcn-svelte 1.7.0 Rhea, bits-ui 2.19.3, `@xyflow/svelte` 1.6.6. Node.js `>=22.12.0 <23.0.0` and pnpm. SPA origin is never daemon port 8765. Tauri 2 is a later optional shell (DEC-0478, GAP-0112).
- **Issuers (DEC-0474, DEC-0484, DEC-0489).** Unique invoke issuer `dispatchInvoke`. Unique chat issuer `dispatchChat` → `send_message`. Unique cancel issuer `dispatchCancel` → `cancel_job`. Widgets never own invoke. Tab close does not cancel a JobHandle (DEC-0479).
- **First operator (DEC-0503, J1, C1).** Trust root is the OS user of `QMA_DAEMON_ROOT` plus a daemon-minted `host_control` token. `qmb host recover-control` on a stopped daemon by that OS owner does not present the lost token; `local_operator` and journals are preserved; no second principal; no data-root wipe. `rotate-control` remains the live-token path. Empty root means no `local_operator`. Missing token plus existing principal is not first-start bootstrap.
- **Host verbs (DEC-0494, AM-10).** `qmb host start|status|stop|pair|configure|rotate-control|recover-control`. QMB never writes daemon sqlite. Running-daemon host-control verbs require the current token. Narrow exception: `stop` when the token file is missing or unreadable, allowed only for the OS owner of the root, so recovery can run. Do not broaden that exception.
- **Pairing (DEC-0485, DEC-0491, DEC-0492, DEC-0493, C2, R2).** `pairing_proof` is the bearer. `pairing_record_id` is the journal identity. Origin never issues a new proof. Unauthenticated HTTP is only `/pair/start`, `/pair/confirm`, and CORS `OPTIONS`. HTTP Bearer `pairing:<proof>`. WS subprotocols `qmx.ct40.v1` and `qmx.pair.<proof>`. Cookies, `localStorage`, and IndexedDB are forbidden for the proof. Origin-revoke is a `journal_seq` barrier: renew-then-revoke kills the new proof; revoke-then-renew of the old proof refuses; `--session` is that record only; after the barrier a new `/pair/start` is legal.
- **Reload vs cold start (DEC-0501).** Same-tab reload may restore proof from `sessionStorage`. Closed tab is cold start: empty storage, `list_mailbox` restore, never auto-resend. Cloned tab copies storage: existing proof plus a new `producer_id` if the old one is live. `/pair/renew` is an explicit rotate, not the clone path.
- **Mailbox (DEC-0484, DEC-0495).** Durable delivery stays Epic 46 / Story 46.4 / FEAT-0045. Additive Envelope field `product_session_ref` is excluded from Envelope fp1. `list_mailbox` is an addable Epic 41 query. Home chat needs no instance.
- **Cancel (DEC-0489, DEC-0496).** Optional immutable `originating_product_session_ref` at UI admit; omitted on headless. `queued`→`running` does not kill the same `command_id`. Terminal is a recorded no-op.
- **Artifacts (DEC-0488, DEC-0497).** Authenticated HTTP `PUT /artifacts/stage`. Interrupted v1 upload refused. Remote run needs explicit `transfer_artifact` on recorded reachable TLS plus dest-authored `transfer_complete`.
- **Drafts (DEC-0487, DEC-0499).** Daemon issues `editor_draft_id`. First Run is `publish_editor_draft` into the local authoring pack then parent AD-30 enable. QMA AD-22 stays one RefinementProposal type.
- **Pack UI (DEC-0481, DEC-0486, DEC-0498).** `PackUiRequest` is an ingested request DTO. `PluginManifest.copilot_profile` stays Epic 60 sibling. `GRANT_AMBIGUOUS` if two or more matching grants. Do not duplicate FEAT-0058..FEAT-0063 (DEC-0479 in extractions / DEC-0504).
- **GAP restamp (DEC-0509).** GAP-0081 and GAP-0100 are answered sitting law of this UI sitting, delivered by FEAT-0064..FEAT-0071. They remain out-of-scope as pack-and-grant kit holes.

## Architecture-preflight verdict

**reuse** existing applications. **new COMP: none. new CT: none.** No new `depends_on` edge. No existing component's authority shrinks (DEC-0505).

| Work | Owner | Class |
|---|---|---|
| Svelte host chrome | client of COMP-QMA-WIRE (UI lens; not a COMP) | extend parent AD-17 |
| `qmb host` + `host_control` + `recover-control` | COMP-QMB + COMP-QMA-DAEMON | named AM-10 / AM-15 |
| Pairing HTTP + bearer proof | COMP-QMA-DAEMON + COMP-QMA-WIRE + COMP-QMB | named AM-01 / AM-03 / AM-11 |
| Mailbox `product_session_ref` + `list_mailbox` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-02 / AM-08 / AM-14 |
| `cancel_job` + originating field | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-04 / AM-09 |
| PUT + transfer | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-05 / AM-06 / AM-13 |
| Drafts + `publish_editor_draft` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-03 / AM-07 / AM-09 / AM-17 |
| PackUiRequest / ActionContext | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-16; Epic 60 reuse |
| Live JSON-RPC/HTTP/event serving | COMP-QMA-DAEMON + COMP-QMA-WIRE | adoption of Epic 41–42 |

Candidates refused by id (DEC-0505, DEC-0508): COMP-UI / sixth COMP; new CT-*; third ProductSessionProfile; cookie login; `ui_view` contribution point; AD-22 as graph draft store; json-render/MCP as identity; QMB sqlite writer; reminting `local_operator` on recover; Origin-only issuance.

Dead list honored: DEC-0084 stays dead, DEC-0085 stays dead, DEC-0086 stays dead, DEC-0361 stays dead, DEC-0362 stays dead, DEC-0366 stays dead, DEC-0408..0413 stay dead, DEC-0466 stays dead (DEC-0508).

## Wiring honesty @ 34c148be (DEC-0507)

**CONNECT (types/fixtures exist; not e2e):** InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, `view:*` DTOs, JobHandle types + in-memory store, mailbox Envelope types, `later_commands`.

**AMEND relative to this sitting:** Envelope has no `product_session_ref`; JobHandle has no `originating_product_session_ref`.

**ABSENT as product surface:** live CT-40 server (`DaemonProcess` discards TCP bytes); `/pair/*`; `qmb host`; pairing table; `list_mailbox`; `cancel_job`; PUT `/artifacts/stage`; `transfer_artifact` / `transfer_complete`; draft save/publish/head; `get_pack_ui_request`; `host_control` / `recover-control`; `PluginManifest.copilot_profile`; first-party Svelte/Tauri frontend.

## Consequences

Easier: coding agents can implement chrome and the named daemon/QMB adds from `docs/` without re-reading the architecture sittings. FEAT-0064..FEAT-0071 are pre-ordered against FEAT-0041/0042/0045/0055/0058.

Harder, deliberately: no COMP-UI; no silent override of Story 41.4 / 46.4 / 57.3; no claiming inspect types are live protocol.

Blast radius: `qma-daemon`, `qma-wire`, `qmb`, CT-40, CT-42, CT-46 (`originating_product_session_ref`), CT-48, constitution L7/L31, AGENTS.md, overview/stack, security-model, logging-spec, test-strategy, glossary, gap-report, UI lens docs, SCN-0028..0035. No new `depends_on` edge. Host verbs include `pair revoke --session` and `--origin`.

Foreclosed: Origin-only issuance; cookie login; browser-spawned daemon; sixth COMP; `ui_view` contribution point; AD-22 graph draft store.

Scenarios: [SCN-0028](../scenarios/SCN-0028-first-operator-pair.md), [SCN-0029](../scenarios/SCN-0029-origin-revoke-vs-renew.md), [SCN-0030](../scenarios/SCN-0030-recover-control.md), [SCN-0031](../scenarios/SCN-0031-mailbox-lost-ack.md), [SCN-0032](../scenarios/SCN-0032-artifact-put-transfer.md), [SCN-0033](../scenarios/SCN-0033-publish-then-enable.md), [SCN-0034](../scenarios/SCN-0034-home-vs-copilot-rail.md), [SCN-0035](../scenarios/SCN-0035-cancel-queued-to-running.md).
