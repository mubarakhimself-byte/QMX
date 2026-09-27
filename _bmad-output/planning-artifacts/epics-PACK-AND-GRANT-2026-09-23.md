---
stepsCompleted: [1, 2, 3, 4]
validated: true
inputDocuments:
  - _docwork/pack-and-grant-epics-handoff.md
  - _docwork/riders/pack-and-grant-kit-2026-09-23.md
  - _docwork/riders/pack-and-grant-gap-correction-2026-09-23.md
  - _docwork/pack-and-grant-increment-brief.md
  - docs/decisions/ADR-0025-pack-and-grant-kit.md
  - docs/decisions/ADR-0024-workflows-construction-kit.md (dated follow-up only; original Decision not rewritten)
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/CONTRACTS.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/REQUIREMENTS-ADDENDUM.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/COPILOT-AND-APPS.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/IMPLEMENTATION-SEQUENCE.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/reviews/gate-summary.md
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/research/SDK-HYBRID-AND-CORE.md
  - docs/scenarios/SCN-0023-home-instance-pick.md
  - docs/scenarios/SCN-0024-optional-copilot-headless.md
  - docs/scenarios/SCN-0025-nested-mission.md
  - docs/scenarios/SCN-0026-host-retry.md
  - docs/scenarios/SCN-0027-diagnosis-json-lines.md
  - _docwork/feature_inventory.yaml (FEAT-0058..FEAT-0063; blockers FEAT-0052, FEAT-0053, FEAT-0042, FEAT-0055, FEAT-0051, FEAT-0056)
  - _docwork/ledger.yaml (DEC-0452..DEC-0468 ratified)
  - _docwork/gaps.yaml (GAP-0101..GAP-0108 answered; GAP-0081/GAP-0100 out-of-scope as kit holes)
  - docs/constitution.md (L7 pack-and-grant annotation DEC-0452/0453/0461/0462)
  - docs/components/qma-wire.md
  - docs/components/qma-daemon.md
  - docs/components/qma-core.md
  - _bmad-output/planning-artifacts/epics-WORKFLOWS-2026-09-19.md (Epics 53–59 — extend, do not duplicate)
  - _bmad-output/planning-artifacts/epics-QML-RESEARCH-2026-09-16.md (Epic 52 — extend, do not duplicate)
  - _bmad-output/planning-artifacts/epics-QMA-2026-08-29.md (Epics 40–48 — extend, do not duplicate)
  - integration@34c148be404a375cbfd79fd4ce6997452e4f1d20 (inspect: envelope/grant/product_session types exist as fixtures; caller_kind / optional authoring instance / daemon JSON-lines / kit failure_class / host retry loop / nested Mission verb absent)
excludedDocuments:
  - _bmad-output/planning-artifacts/epics.md (must not be rewritten)
  - _bmad-output/planning-artifacts/epics-QMA-2026-08-29.md (must not be rewritten)
  - _bmad-output/planning-artifacts/epics-CONNECT-2026-09-11.md (must not be rewritten)
  - _bmad-output/planning-artifacts/epics-WORKBENCH-2026-09-14.md (must not be rewritten)
  - _bmad-output/planning-artifacts/epics-QML-RESEARCH-2026-09-16.md (must not be rewritten)
  - _bmad-output/planning-artifacts/epics-WORKFLOWS-2026-09-19.md (must not be rewritten)
  - _bmad-output/planning-artifacts/prds/prd-QMX-2026-08-21/prd.md (must not be rewritten; GAP-0061)
  - _bmad-output/planning-artifacts/ux-designs/ux-QMX-2026-09-01/DESIGN.md (empty scaffold)
  - _bmad-output/planning-artifacts/ux-designs/ux-QMX-2026-09-01/EXPERIENCE.md (empty scaffold)
  - _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/ (UI sitting; GAP-0081 / GAP-0100 out of this kit)
  - _docwork/qml-research-epics-handoff.md (FEAT-0047 mill — wrong increment)
  - _docwork/workflows-epics-handoff.md (FEAT-0051..0057 — already specified)
delegation: "operator 2026-09-23 — autonomous epics run; menus auto-continued; pack-and-grant increment only; docs authority; no factory launch; no Documentation Factory; no architecture reopen; no production code"
epicNumbering: "Epic 60–65 — reserved so PACK-AND-GRANT never collides with Phase-1 (1–23), trading-node (24–30), CONNECT (31), WORKBENCH (32–38), QMA (40–48), QML-RESEARCH (49–52), or WORKFLOWS (53–59). Epic 39 left unused as a buffer."
baseInventory: "integration@34c148be404a375cbfd79fd4ce6997452e4f1d20 (inspect only). Parent freeze 270e992 remains for ADR-0024 original Decision (DEC-0450). Do not use 270e992 for current absence of envelope/grant/product_session types."
feature: FEAT-0058..FEAT-0063
adr: ADR-0025
architectureStatus: "docs folded (ADR-0025, DEC-0452..DEC-0468 ratified as docs authority). GAP-0101..GAP-0108 are answered sitting law; delivery is these features (DEC-0468). Implementation authorization remains factory-pipeline-only."
decisions: [DEC-0452, DEC-0453, DEC-0454, DEC-0455, DEC-0456, DEC-0457, DEC-0458, DEC-0459, DEC-0460, DEC-0461, DEC-0462, DEC-0463, DEC-0464, DEC-0465, DEC-0466, DEC-0467, DEC-0468]
---

# QMX - Epic Breakdown

## Overview

This document is the epic and story breakdown for the **pack-and-grant kit** increment (FEAT-0058..FEAT-0063): absorb the 2026-09-23 child spine (`architecture-QMX-2026-09-23`, kit AD-1..AD-9) so a pack author can declare operations, optional views, requested access, and an optional copilot; so home/main chat can sit with no instance until invoke; so every pack is diagnosable headless; so ordinary `none`/`read` flakes retry in the host; so a workflow starts another as one nested Mission.

It decomposes the **docs-authority** 2026-09-23 corpus — ADR-0025, DEC-0452..DEC-0468, SCN-0023..SCN-0027, kit `CONTRACTS.md` / `JOURNEYS.md`, and brownfield defects at `integration@34c148b` — into implementable stories for the factory lanes.

The Phase-1 file (`epics.md`, Epics 1–23 and trading-node Epics 24–30) stays untouched. CONNECT (`epics-CONNECT-2026-09-11.md`, Epic 31) stays untouched. WORKBENCH (`epics-WORKBENCH-2026-09-14.md`, Epics 32–38) stays untouched. QMA (`epics-QMA-2026-08-29.md`, Epics 40–48) stays untouched. QML-RESEARCH (`epics-QML-RESEARCH-2026-09-16.md`, Epics 49–52) stays untouched. WORKFLOWS (`epics-WORKFLOWS-2026-09-19.md`, Epics 53–59) stays untouched. **Epic numbering starts at Epic 60**, a reserved block so this increment never collides with those files. Epic 39 remains unused as a buffer.

Requirement prefixes carry the **PG** marker because these requirements derive from the pack-and-grant docs corpus and child spine, not from a PRD rewrite. The 2026-08-21 PRD has no pack-and-grant / `caller_kind` / optional authoring instance FRs. GAP-0061 stays deferred. FR-PG-* live on GAP-0101..GAP-0108 as **answered sitting law** (DEC-0468) whose delivery is FEAT-0058..FEAT-0063. Rules carried forward from `epics.md`: each FR's cited artifact is the epic boundary and the source of its acceptance criteria; FR granularity is deliberately coarser than story granularity — never size a lane by counting FRs.

This increment **extends** Epic 54 (InvocationEnvelope / GrantRecord), Epic 55 (`product_session` CAS), Epic 53 (ContributionHit listing axes), Epic 57 (durable Task Graph / outbox / JobHandle), Epic 58 (Workflows thin fixtures including change-request), Epic 42 (daemon substrate), and Epic 41 (CT-40 wire). It does not duplicate those stories. It **closes** optional pack `copilot_profile`, authoring `app_instance_id` optionality, `selected_refs` kind `instance_id`, envelope `caller_kind`, daemon JSON-lines, kit `failure_class`, default host retry for `none`/`read`, nested Mission invoke, instance `health()`, and the thin honesty fixtures those stories left open. It **forbids** claiming those kit field changes exist as wired product surface at `34c148b`, claiming envelope/grant/`product_session` types are absent there, filling GAP-0081 chrome / GAP-0100 dashboard, inventing the retry ceiling number, a sixth COMP, a new CT, a third `ProductSessionProfile`, or a live Task Graph merge.

Preflight verdict (ADR-0025 / DEC-0462): **reuse** existing applications. **new COMP: none. new CT: none.** Named parent amendments are DEC-0463 (parent AD-8 / DEC-0421) and DEC-0464 (parent AD-24 / DEC-0437). Do not set those parents `superseded_by`. Do not rewrite ADR-0024 Decision. Cheap-veto A7–A9 (DEC-0467) are sitting machinery — stories may cite them; they are not operator-spoken schemas.

`validate_inventory.py --next` still prints FEAT-0001 because earlier features remain `planned`. This sitting **picks FEAT-0058..FEAT-0063 explicitly**. First epic is FEAT-0058.

Nothing in this document grants implementation, credential, order, paper-mode, promotion, live-money or destructive authority; that arrives only through the factory pipeline (ADR-0025; DEC-0461). **This session does not launch factory lanes.**

Cite parent 09-18 ADs as `parent AD-n`. Cite this sitting as `kit AD-n`. Local `kit AD-8` is presentation adapters; `parent AD-8` is product_session.

## Requirements Inventory

### Functional Requirements

**A. Host SDK — pack request, optional copilot, authoring instance, caller_kind (DEC-0452 / DEC-0453 / DEC-0454 / DEC-0463 / DEC-0464; FEAT-0058)**

- FR-PG-01: A pack manifest **requests** operation `contributes` as `{point, local_id}` objects (parent AD-2), optional `view:*` wire DTOs (parent AD-17), optional `copilot_profile` request blob, and `requested_capabilities`. Kit `requested_capabilities` is the AMEND/alias of inspect `PluginManifest.permissions`. (kit AD-1; DEC-0452)
- FR-PG-02: The host **grants** GrantRecords into a `psess:`. Installing is not granting. Enabling after validate is not granting. (DEC-0452; SCN-0024)
- FR-PG-03: A pack may omit `copilot_profile`. Absence is valid. Headless packs are first-class reusable parent-AD-3 steps with no navigation and no copilot panel. (DEC-0454; GAP-0103; SCN-0024)
- FR-PG-04: `view:*` remains a wire DTO. It is not a contribution point and not a json-render runtime id. Widgets never own invoke. (DEC-0452; DEC-0453)
- FR-PG-05: Mini-app, widget, and workflow are kit nouns over the whole platform. Bytes of a pack live in the plugin tree plus daemon install/instance rows. Execution of each `op_id` is owned by the COMP named on the descriptor. Broker/venue stays QMN. (DEC-0453)
- FR-PG-06: QMA is host/runtime, not owner of every op. A new idea that no existing COMP can execute is a named connect/extend of that COMP. Closed QMA store classes stay closed. (DEC-0453)
- FR-PG-07: QuantMind/QMX Copilot is one product identity. Tool availability is the parent AD-9 intersection (published ContributionHits ∩ host grants ∩ session GrantRecords ∩ health). An instance may omit an in-app panel. (DEC-0454)
- FR-PG-08: `ProductSessionProfile` remains closed `{authoring, app-use}`, immutable at create. Home/main is authoring with `app_instance_id` absent. No third profile. (DEC-0463; SCN-0023)
- FR-PG-09: `app_instance_id` MAY be absent when `profile=authoring`. It remains required when `profile=app-use`. (DEC-0463; GAP-0102)
- FR-PG-10: Closed `selected_refs` kinds gain `instance_id` in addition to parent AD-8 kinds. Layout, widget, and json-render trees remain forbidden. (DEC-0463)
- FR-PG-11: Authoring with absent session instance may not invoke until exactly one `selected_refs` kind `instance_id` is present. Envelope `instance_id` is taken from that ref. Zero or many such refs is typed `INVALID_INPUT`. The host does not guess latest, first, or all. (DEC-0463; SCN-0023)
- FR-PG-12: Envelope `instance_id` remains required on every invoke. (DEC-0464)
- FR-PG-13: Nested invoke does not union grants. Running work is not cancelled by panel dispose. Context transfer is explicit `selected_refs` or `change_request` only. QMA `sess:` remains the engine run, not a third chat. (DEC-0454)
- FR-PG-14: App-use may inspect, invoke granted ops, and mint `change_request`. It must not apply, edit package source, install code, elevate grants, or retarget accounts. (DEC-0454; DEC-0442; SCN-0024)
- FR-PG-15: Every public call carries parent AD-24 InvocationEnvelope including closed `caller_kind` `user | agent | workflow`. (DEC-0464; GAP-0101)
- FR-PG-16: Load-bearing surfaces are descriptors, GrantRecords, `input_schema`, typed refusals, and host-intercepted tool calls. Skills describe; they do not grant. ContributionHit ≠ grant. Hooks cannot override a failed privilege gate. (DEC-0458)
- FR-PG-17: MCP App HTML and json-render catalog entries cannot add ops or fields. json-render catalog `action` names an existing `op_id`. MCP App `tools/call` is intercepted by the host against the session GrantRecord. (DEC-0458; DEC-0459)
- FR-PG-18: JSON Render and MCP Apps stay unpinned presentation adapters. Native QMX panes remain first. Do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps`. (DEC-0459)

**B. Daemon JSON-lines + diagnosis (DEC-0456 / DEC-0467; FEAT-0059)**

- FR-PG-19: Closed `failure_class` is `grant | workflow | view | dependency | host`. `view` means the wire DTO failed to mount, was stale, or was unhealthy — it is not an invoke. (DEC-0456; cheap-veto A7; GAP-0105)
- FR-PG-20: Headless diagnosis query returns `failure_class`, `job_handle` (or null), `correlation_id`, and `healthy`. How-it-failed is the log line plus JobHandle `attempt_id` plus typed refusal. No fourth store. (DEC-0456; SCN-0027)
- FR-PG-21: `qma-daemon` emits stdlib JSON-lines. Required fields: `ts`, `level`, `event`, `correlation_id`. When present: `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Never secret values. Never a journal. (DEC-0456; cheap-veto A8; GAP-0104)
- FR-PG-22: Logs are not evidence. Mini-app typed failures, when first ids ship, live in that owning package's FAILURES.md — never on the QMN alert allow-list. Do not extend `qmn/FAILURES.md`. Agents must not author QMA telemetry. OTel remains export-port only. (DEC-0456; SCN-0027)

**C. Default host retry none/read (DEC-0457 / DEC-0467; FEAT-0060)**

- FR-PG-23: Default host retry is **on** for effect `none` and `read` until success, typed `retryability=NO`, or the host-registered attempt ceiling (registry row; this sitting mints no number — GAP-0108). Attempts increment `attempt_id` on the same `logical_invocation_id`. (DEC-0457; SCN-0026)
- FR-PG-24: Parent AD-24 / SCN-0021 remain the matrix: `append-evidence` dedupes; `mutate-config` is CAS (`conflict` is not a retry); `place-run` uses `logical_invocation_id` as run identity (outbox replay is not a second dispatch); `external-egress` obtains a receipt or becomes `unknown` and MUST NOT blind-retry. (DEC-0457)
- FR-PG-25: `reconcile_policy` `never-retry` and `unknown-manual` win. Parent AD-25 `unknown-blocked` is never auto-retried. (DEC-0457)
- FR-PG-26: A pack may set attempts to zero. A pack MUST NOT exceed the host ceiling or the effect-class matrix. No per-pack retry dialect. (DEC-0457)
- FR-PG-27: Implementation edits (code, graph, grants, account target) are `change_request`: app-use may mint; authoring plus operator apply. Alerts never authorize. HMR and hot-apply stay dead. (DEC-0457)

**D. Nested Mission invoke (DEC-0455; FEAT-0061)**

- FR-PG-28: Widgets bind or display ops. They do not introduce a fifth composition mode. (DEC-0455; SCN-0025)
- FR-PG-29: Workflow-to-workflow at runtime is parent-AD-3 invoke of the callee template `start | query-state | cancel | await` (`qualified_id`+version) creating **one nested Mission / one Task Graph / one JobHandle**. Occupancy and cancel follow that JobHandle. Nested invoke does not union grants. (DEC-0455; GAP-0107; SCN-0025)
- FR-PG-30: Include-at-author is a **new versioned Graph Template**, not a runtime merge. (DEC-0455)
- FR-PG-31: Merging two live Task Graphs is refused (`INVALID_INPUT` or the owner COMP's illegal-topology refusal). Partial failure does not silently substitute another instance, version, or account. (DEC-0455; SCN-0025)
- FR-PG-32: Nested invoke depth is envelope `call_depth` against the host-registered **recursion** ceiling. Exceeding it is `INVALID_INPUT`. This sitting mints no number. That row is not GAP-0108 (GAP-0108 is the **retry attempt** ceiling under FEAT-0060). (DEC-0455)

**E. Listing axes + instance health() (DEC-0456 / DEC-0428; FEAT-0062)**

- FR-PG-33: The host exposes five independent listing booleans including `healthy`. Story 53.4 CONNECT at `34c148b` names the third axis `granted`. Kit sitting law names that axis `authorized` (parent AD-15) and says it is not a session GrantRecord. Story 64.1 is the AMEND: one live third-axis name after the story, with tests that `authorized` ≠ `product_session.granted_ops`. Published is not healthy. (DEC-0456; DEC-0428; DEC-0465)
- FR-PG-34: Instance `health()` is the existing component typed-report (DEC-0112), distinct from pack `published`. Copilot and CLI consume the same headless queries. (DEC-0456)

**F. Thin kit-journey fixtures (DEC-0452..DEC-0460 / DEC-0465; FEAT-0063)**

- FR-PG-35: Daily idea path is yap at authoring → Graph Template → runs with JobHandles → pack export after validate. A Loop remains node state. Graduation does not skip parent AD-18/AD-30. (DEC-0460)
- FR-PG-36: Thin fixture J-KIT-01: headless pack with no copilot; CLI/wire invoke produces a JobHandle; no in-app panel exists. (SCN-0024)
- FR-PG-37: Thin fixture J-KIT-02: optional panel cannot apply; v1 instance stays; panel dispose does not cancel running work. (SCN-0024)
- FR-PG-38: Thin fixture J-KIT-03: home authoring exactly-one `instance_id`; zero or many refuse; nested call does not widen tools. (SCN-0023)
- FR-PG-39: Thin fixture J-KIT-04/05: widget binds `start`; nested Mission is not a live merge; include-at-author is a new version. (SCN-0025)
- FR-PG-40: Thin fixture J-KIT-06: `read` retries in the host; `external-egress` without a receipt is `unknown`; stories invent no ceiling number. (SCN-0026)
- FR-PG-41: Thin fixture J-KIT-07: a weaker model fills descriptor schemas; missing dep fails closed; prose cannot add an op. (SCN-0027; DEC-0458)
- FR-PG-42: Fixtures must not claim e2e adoption at `34c148b`. Class/test existence is not e2e (DEC-0286; DEC-0465). Do not fill GAP-0081 chrome or GAP-0100 dashboard.

### NonFunctional Requirements

- NFR-PG-01: No sixth COMP; no new CT number; additive CT-40 family annotations only. Public types in this increment (`caller_kind`, `failure_class`, optional authoring `app_instance_id`, `selected_refs` kind `instance_id`, `copilot_profile`) are specified in prose and CT **usage annotations**. They are not new `schema.fields` and they are not a new CT number. Factory implementation lands those fields as CT-40 / owner-contract format mints. (DEC-0462)
- NFR-PG-02: No new sqlite class. No fourth observability product. QMA telemetry store stays. Daemon JSON-lines are stdlib logging, not a journal. (DEC-0456; DEC-0429)
- NFR-PG-03: Inspect SHA honesty at `integration@34c148b` (DEC-0465). Parent freeze `270e992` for ADR-0024 original Decision (DEC-0450). Fixtures are not e2e (DEC-0286).
- NFR-PG-04: CONNECT at `34c148b` (types/fixtures exist; not e2e): InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, effect-class plus `reconcile_policy`, `call_depth` / `parent_logical_invocation_id`, `OperationDescriptor` lifecycle verbs, `PluginManifest.permissions`, Workflows 53–59 fixtures including listing axes (`granted` as the third axis) and pack `contributes`. AMEND: `ProductSession.app_instance_id` is required `str`; `SELECTED_REF_KINDS` lacks `instance_id`; envelope has no `caller_kind`; listing third axis `granted` → kit `authorized`; `permissions` → kit `requested_capabilities`. ABSENT as product surface: pack `copilot_profile`; `qma-daemon` stdlib JSON-lines operator logger; kit `failure_class`; default host retry loop; nested Mission invoke as a first-class occupancy; CheckpointManifest.
- NFR-PG-05: Do not claim `caller_kind` / optional authoring instance / daemon JSON-lines exist at `34c148b`. Do not claim envelope / grant / `product_session` types are absent at `34c148b`.
- NFR-PG-06: Cheap-veto A7–A9 may be cited as sitting machinery; must not be treated as operator-spoken schemas. (DEC-0467)
- NFR-PG-07: GAP-0101..GAP-0108 are **answered sitting law** (DEC-0468). Delivery is FEAT-0058..FEAT-0063. GAP-0081 and GAP-0100 are **out-of-scope as kit holes**. GAP-0093 and GAP-0096 stay for a later operator look — this increment does not reopen them as kit design holes.
- NFR-PG-08: Named parent amendments DEC-0463 (parent AD-8 / DEC-0421) and DEC-0464 (parent AD-24 / DEC-0437) stay dated follow-ups. Do not set those parents `superseded_by`. Do not rewrite ADR-0024 Decision.
- NFR-PG-09: Stories specify factory work; they do not authorize live trading, credentials, or go-live. (DEC-0461)
- NFR-PG-10: Dead list honored: DEC-0084 / 0085 / 0086, DEC-0361 marketplace, DEC-0362 solver, DEC-0366 HMR, DEC-0408..0413 mill deaths. Screen-kit and automation-kit as the center stay dead. Third ProductSessionProfile stays un-minted. Merged live Task Graphs stay refused. JSON Render / MCP Apps as identity, persistence, runtime, or authority stay dead. (DEC-0466)
- NFR-PG-11: Headless / CLI / library semantic parity across an operation's supported doors. UI chrome is a later sitting.
- NFR-PG-12: Weak / older models operate through schemas and grants. (DEC-0458)
- NFR-PG-13: Retry ceiling number is a later registry fill under FEAT-0060. Stories must not invent a cap (GAP-0108; cheap-veto A9).
- NFR-PG-14: QMN `failure_class` on alerts is a different noun. Kit diagnosis `failure_class` must not extend `qmn/FAILURES.md`.

### Additional Requirements

- AR-PG-01: Starter template: none. This increment extends existing packages (`qma-core`, `qma-wire`, `qma-daemon`).
- AR-PG-02: Blockers (inventory): FEAT-0058 ← 0052/0053; 0059 ← 0058/0042; 0060 ← 0058/0052; 0061 ← 0055/0058; 0062 ← 0058/0051; 0063 ← 0058..0062 + 0056. Inventory still marks those parents `planned`; stories extend prior *story law*, they do not re-author it.
- AR-PG-03: Factory touch ownership is COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON. No QMB/QML core fork. No new `depends_on` edge.
- AR-PG-04: Golden scenarios SCN-0023..SCN-0027 are specification oracles. BDD is specification, not executed proof.
- AR-PG-05: Out of this increment: GAP-0081 chrome, GAP-0100 dashboard, GAP-0085, GAP-0063, GAP-0061, GAP-0062, GAP-0058, sixth COMP, new CT, mill FEAT-0047, FEAT-0001, pinning json-render/MCP Apps, UI sitting `architecture-QMX-UI-2026-09-23`.
- AR-PG-06: `--next` still prints FEAT-0001; the operator picks FEAT-0058..FEAT-0063 explicitly. First epic is FEAT-0058.
- AR-PG-07: Wave numbers from `validate_inventory.py --handoff`: FEAT-0058 wave 11; FEAT-0059 wave 12; FEAT-0060 wave 12; FEAT-0061 wave 19; FEAT-0062 wave 17; FEAT-0063 wave 20.
- AR-PG-08: This increment extends Epics 53–59. It does not duplicate ContributionHit, envelope/GrantRecord field catalogues, `product_session` CAS, DAG validation, outbox/JobHandle, or Workflows thin proofs.
- AR-PG-09: Brownfield at `34c148b` to forbid claiming done: `PluginManifest` has `contributes` and `permissions` (empty-collection request) and no `copilot_profile` / no `requested_capabilities` field; `InvocationEnvelope` required fields omit `caller_kind` and keep `instance_id`; `ProductSession.app_instance_id: str`; `SELECTED_REF_KINDS` is `{artifact, research_ref, contribution, template, dataset, run, attempt, node_ids}`; listing axes exist as Story 53.4 fixtures with third axis `granted`; QMN alerts have a different `failure_class`; no daemon JSON-lines logger; no host retry loop; no nested Mission verb; `OperationDescriptor` already has `start | query-state | cancel | await`.
- AR-PG-10: Tests may inject a retry-ceiling value for a fixture. Production code must read a host-registered registry row and must not hardcode a sitting-invented default such as `3`. Recursion ceiling is a different host-registered row from GAP-0108.
- AR-PG-11: Workflows FEAT-0056 is Epic 58 with Stories 58.1–58.5. This sitting’s FEAT-0058 is Epic 60. Never write a bare `Story 58`. Cite **Workflows Story 58.4 / FEAT-0056** for the change-request apply fixture.

### UX Design Requirements

The 2026-09-01 UX spine (`DESIGN.md` / `EXPERIENCE.md`) is an empty scaffold and is **not** a contract. The 2026-09-23 UI sitting folder is out of this kit. GAP-0081 chrome and GAP-0100 dashboard are out-of-scope as kit holes (DEC-0468). Only kit **contracts** that later UI will consume fold:

- UX-DR-PG-01: Optional in-app panel is a **contract** (a pack may omit `copilot_profile`; an instance may omit a panel). It is not GAP-0081 chrome and not a second copilot product. (DEC-0454; FEAT-0058)
- UX-DR-PG-02: Native pane / JSON Render / MCP Apps own neither identity nor permission. Mount/dispose must not start or kill durable work. Adapters stay unpinned. Delivery of intercept honesty is FEAT-0063 / Story 65.6, not FEAT-0058 IN. (DEC-0459)
- UX-DR-PG-03: Home/main is authoring with absent `app_instance_id` — not a third seat and not chrome. (DEC-0463; FEAT-0058)
- UX-DR-PG-04: GAP-0081 chrome and GAP-0100 dashboard are explicitly out of this epic set.

### FR Coverage Map

FR-PG-01: Epic 60 — pack request surface
FR-PG-02: Epic 60 — install ≠ grant
FR-PG-03: Epic 60 — omit copilot_profile
FR-PG-04: Epic 60 — view:* wire DTO
FR-PG-05: Epic 60 — kit nouns; COMP owns op
FR-PG-06: Epic 60 — QMA host not owner
FR-PG-07: Epic 60 — one copilot; panel optional
FR-PG-08: Epic 60 — closed profiles; home is authoring
FR-PG-09: Epic 60 — authoring instance optional
FR-PG-10: Epic 60 — selected_refs kind instance_id
FR-PG-11: Epic 60 — exactly-one instance on invoke
FR-PG-12: Epic 60 — envelope instance_id required
FR-PG-13: Epic 60 — nested grants / dispose / sess:
FR-PG-14: Epic 60 — app-use cannot apply
FR-PG-15: Epic 60 — caller_kind
FR-PG-16: Epic 60 — schemas not prose
FR-PG-17: Epic 65 — adapters cannot add ops
FR-PG-18: Epic 65 — adapters unpinned
FR-PG-19: Epic 61 — closed failure_class
FR-PG-20: Epic 61 — diagnosis query
FR-PG-21: Epic 61 — daemon JSON-lines
FR-PG-22: Epic 61 — logs ≠ journals; no QMN reuse
FR-PG-23: Epic 62 — default none/read retry
FR-PG-24: Epic 62 — effect-class matrix
FR-PG-25: Epic 62 — never-retry / unknown-blocked
FR-PG-26: Epic 62 — pack may zero attempts
FR-PG-27: Epic 62 — repair is change_request
FR-PG-28: Epic 63 — widget binds, does not own invoke
FR-PG-29: Epic 63 — nested Mission one JobHandle
FR-PG-30: Epic 63 — include-at-author new version
FR-PG-31: Epic 63 — live merge refused
FR-PG-32: Epic 63 — call_depth ceiling
FR-PG-33: Epic 64 — listing axes including healthy
FR-PG-34: Epic 64 — instance health()
FR-PG-35: Epic 65 — graduation does not skip AD-18/30
FR-PG-36: Epic 65 — J-KIT-01
FR-PG-37: Epic 65 — J-KIT-02
FR-PG-38: Epic 65 — J-KIT-03
FR-PG-39: Epic 65 — J-KIT-04/05
FR-PG-40: Epic 65 — J-KIT-06
FR-PG-41: Epic 65 — J-KIT-07
FR-PG-42: Epic 65 — fixtures not e2e; no chrome

## Epic List

Six epics, one per inventory feature, in inventory order. They stay separate because named parent amendments of envelope/session (60) are a different type-system risk from daemon operator logs (61); because a retry loop that could double-send (62) is a genuine money-path risk boundary from SDK field mints; because nested Mission occupancy (63) assumes durable outbox from Epic 57 and must not be “completed” by adding `caller_kind` alone; because listing/`health()` (64) is a query surface on Story 53.4 axes, not a logger; and because thin proofs (65) are honesty oracles against already-specified machines.

Consolidation considered and rejected: 61+64 share “observability” in English and both cite GAP-0105, but diagnosis JSON-lines is IMPLEMENTATION-SEQUENCE step 2 / FEAT-0059 and listing/`health()` is step 5 / FEAT-0062 — different records, different blockers (0042 vs 0051). 60+62 share envelope/effects files, but retry must not loosen parent AD-24; folding it into the SDK mint would let a builder ship `caller_kind` and call retry done. 60+63 share `caller_kind=workflow`, but nested Mission is graph occupancy, not an envelope field.

Weight tags route factory lanes: **H** heavy (`args.build_model = grok-4.6`), **L** light (`grok-4.5`). Wave numbers are the inventory waves from `validate_inventory.py --handoff`, not a required build order beyond `blocked_by` and file-disjointness.

### Epic 60: A pack can request ops and an optional copilot; home chat picks one instance before invoke (Wave 11, H)

A pack author declares operations, optional views, requested access, and an optional copilot profile. The host grants. Home/main is authoring with no instance until invoke names exactly one `selected_refs` kind `instance_id`. Every public call carries `caller_kind`. Envelope `instance_id` stays required.

**FRs covered:** FR-PG-01..FR-PG-16
**Feature:** FEAT-0058
**Notes:** Blocked by FEAT-0052, FEAT-0053. GAP-0101, GAP-0102, GAP-0103. SCN-0023, SCN-0024. Named amendments DEC-0463, DEC-0464. Delivers for FEAT-0059..0063.

### Epic 61: A failed run says grant vs workflow vs view vs dependency vs host, in JSON-lines (Wave 12, H)

Copilot or CLI asks why a run failed and gets a closed `failure_class` plus JobHandle. `qma-daemon` emits stdlib JSON-lines. Logs are not evidence.

**FRs covered:** FR-PG-19..FR-PG-22
**Feature:** FEAT-0059
**Notes:** Blocked by FEAT-0058, FEAT-0042. GAP-0104, GAP-0105. SCN-0027. Cheap-veto A7/A8. Delivers for FEAT-0063.

### Epic 62: Ordinary none/read flakes retry in the host; live sends never get a blind second try (Wave 12, H)

A flaky `read` retries in the host. The operator is not the hiccup loop. `external-egress` without a receipt becomes `unknown`. Stories invent no ceiling number.

**FRs covered:** FR-PG-23..FR-PG-27
**Feature:** FEAT-0060
**Notes:** Blocked by FEAT-0058, FEAT-0052. GAP-0106, GAP-0108. SCN-0026. Cheap-veto A9. Delivers for FEAT-0063.

### Epic 63: A workflow starts another as one nested Mission; two live graphs never splice (Wave 19, H)

Template A starts template B as one nested Mission with its own JobHandle. Include-at-author writes a new Graph Template version. Live merge is refused. Widgets bind `start`; they do not own invoke.

**FRs covered:** FR-PG-28..FR-PG-32
**Feature:** FEAT-0061
**Notes:** Blocked by FEAT-0055, FEAT-0058. GAP-0107. SCN-0025. Delivers for FEAT-0063.

### Epic 64: Copilot and CLI list published vs healthy and read instance health() (Wave 17, H)

Headless listing keeps five independent booleans. Story 53.4’s third axis `granted` is AMENDed to kit `authorized` (not a session GrantRecord). Instance `health()` is the typed-report, distinct from pack `published`. Copilot and CLI share the queries. No dashboard.

**FRs covered:** FR-PG-33, FR-PG-34
**Feature:** FEAT-0062
**Notes:** Blocked by FEAT-0058, FEAT-0051. GAP-0105 (health half). Inventory size is multi-pass — **H**, not L: 64.2 is a new pack-instance report. Delivers for FEAT-0063.

### Epic 65: Thin fixtures prove the kit journeys without claiming they already ran at 34c148b (Wave 20, H)

Thin fixtures prove J-KIT-01..07. They do not fill chrome. They do not claim e2e at `34c148b`.

**FRs covered:** FR-PG-17, FR-PG-18, FR-PG-35..FR-PG-42
**Feature:** FEAT-0063
**Notes:** Blocked by FEAT-0058..0062, FEAT-0056. SCN-0023..0027.

### Stories in other increment files that this increment extends (do not duplicate)

| Existing story | What it already delivered | What PACK-AND-GRANT must not redo | What PACK-AND-GRANT closes |
|---|---|---|---|
| 54.2–54.4 | InvocationEnvelope field catalogue; GrantRecord immutable; nested `call_depth` | A second envelope; making `instance_id` optional on invoke | `caller_kind` format mint (60.3) |
| 55.1–55.4 | `psess:` journal projection; closed `{authoring, app-use}`; CAS; grant intersection | A third profile; folding `psess:` into `sess:` | Optional authoring `app_instance_id`; `selected_refs` kind `instance_id` (60.2) |
| 53.2 / 48.1 | Pack `contributes` `{point, local_id}`; `permissions` request tuple; plugin loader | A new manifest type; a second live request field beside `permissions` | Optional `copilot_profile`; `requested_capabilities` as AMEND/alias of `permissions` (60.1) |
| 53.4 | Listing axes published/configured/**granted**/reachable/healthy; hit ≠ grant | Dual-live third-axis names; treating `authorized` as `granted_ops` | Kit AMEND third axis → `authorized`; instance `health()` typed-report (64) |
| 54.3 | Effect-class outcomes; `none`/`read` *may* retry | Loosening the matrix; per-pack retry enum | Default host retry *loop* for none/read (62) |
| 57.1–57.3 | Durable edges, outbox, JobHandle vocab | A second scheduler; `succeeded` on a handle | Nested Mission as first-class invoke (63) |
| Workflows 58.4 / FEAT-0056 / 55.4 | Change-request three-record path; app-use never applies | A new apply path; a bare `Story 58` cite | Kit journey fixture that the optional panel cannot apply (65.2) |
| 42.1–42.4 | Sole-writer journal; closed store list | A new sqlite class; a fourth observability store | Daemon JSON-lines on stdlib logging (61.1) |
| 41.1–41.3 | CT-40 additive-only | New CT number | Usage-annotation format mints of kit fields (60–64) |

---

## Epic 60: A pack can request ops and an optional copilot; home chat picks one instance before invoke

A pack author declares operations, optional views, requested access, and an optional copilot profile without rewriting QMX. The host grants GrantRecords. Home/main is `ProductSessionProfile=authoring` with `app_instance_id` absent until invoke. Invoke is legal only when exactly one `selected_refs` kind `instance_id` is present; envelope `instance_id` is still required. Every public call names `caller_kind` `user | agent | workflow`.

**Factory touch ownership:** exclusive writable surfaces are COMP-QMA-CORE (`PluginManifest` optional `copilot_profile`; kit `requested_capabilities` as the AMEND/alias of existing `permissions`; envelope `caller_kind` type), COMP-QMA-WIRE (additive CT-40 family **format mint** of `caller_kind`; selected-ref kind `instance_id`), and COMP-QMA-DAEMON (`product_session` authoring instance optionality and exactly-one invoke rule). Must not rewrite Stories 54.2–54.4’s envelope catalogue, Stories 55.1–55.4’s `psess:` CAS, or Story 53.2’s `{point, local_id}` contributes. Must not mint a new CT. Must not mint a third profile. Must not make envelope `instance_id` optional. Must not pin json-render/MCP Apps (FR-PG-17/18 land as forbids in Story 65.6, not as FEAT-0058 IN).

**Traceability for the epic:** FR-PG-01..FR-PG-16, UX-DR-PG-01, UX-DR-PG-03, NFR-PG-01, NFR-PG-03, NFR-PG-04, NFR-PG-05, NFR-PG-08, SCN-0023, SCN-0024, GAP-0101, GAP-0102, GAP-0103.

**What must already exist:** FEAT-0052 / Epic 54 (InvocationEnvelope / GrantRecord / operation descriptor); FEAT-0053 / Epic 55 (`product_session` CAS). Inventory still marks those `planned` — this epic **extends** their story law; it does not re-author them.

**What this delivers:** host SDK field changes. FEAT-0059..0063 wait on them. GAP-0101, GAP-0102, GAP-0103.

### Story 60.1: Pack manifest requests ops and an optional copilot; install is not a grant

As a pack author,
I want to declare operations, optional views, requested access, and an optional copilot profile,
So that a headless pack can ship without a copilot and installing it still grants nothing.

**Traceability:** FR-PG-01, FR-PG-02, FR-PG-03, FR-PG-04, FR-PG-05, FR-PG-06, GAP-0103, SCN-0024, UX-DR-PG-01.

**Acceptance Criteria:**

**Given** Story 53.2’s `PluginManifest.contributes` as `{point, local_id}` objects and inspect `permissions` as the empty-collection request tuple
**When** FEAT-0058 lands the pack SDK request surface
**Then** the manifest **requests** operation contributes, optional `view:*` wire DTOs, optional `copilot_profile` request blob, and `requested_capabilities`
**And** `copilot_profile` is not a contribution point and not a grant. Kit `requested_capabilities` is the AMEND/alias of existing `permissions` (same request-not-grant law). Do not leave two live request fields. Claiming `permissions` were absent at `34c148b` fails the story. (FR-PG-01; kit AD-1; DEC-0452; AR-PG-09)

**Given** a pack that omits `copilot_profile` and omits `view:*`
**When** enable after validate succeeds
**Then** absence of `copilot_profile` is valid
**And** enable still does not mint a GrantRecord. Headless packs appear as reusable parent-AD-3 steps with no navigation and no copilot panel. (FR-PG-03; SCN-0024 Then 4; Branch A forbidden)

**Given** install or enable of that pack
**When** a session later invokes
**Then** installing is not granting and enabling after validate is not granting
**And** a session GrantRecord is granting (Story 54.4). (FR-PG-02; SCN-0024)

**Given** optional `view:*`
**When** it appears on the pack
**Then** it is a parent AD-17 wire DTO
**And** it is not a plugin contribution point and not a json-render runtime id. Widgets never own invoke. (FR-PG-04; UX-DR-PG-02)

**Given** execution of an `op_id`
**When** the owner is named
**Then** it is the COMP on the descriptor among QMA/QMB/QML/QMN
**And** QMA remains host/runtime; QMF remains the toolbox, not an application-layer owner; broker/venue stays QMN; closed QMA store classes stay closed. Mini-app, widget, and workflow stay kit nouns over the whole platform. (FR-PG-05; FR-PG-06; DEC-0453)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove optional `copilot_profile` after this story
**And** claiming `copilot_profile` already existed at that SHA fails the story. Claiming `contributes` or `permissions` were absent there also fails the story (Story 53.2 CONNECT). (NFR-PG-04; NFR-PG-05; SCN-0024 Branch D)

### Story 60.2: Authoring may omit app_instance_id; invoke needs exactly one selected instance_id

As an operator talking to the main copilot with nothing selected,
I want home to be authoring with no instance on the session row until I pick exactly one,
So that chat without invoke is legal and invoke cannot silently guess an instance.

**Traceability:** FR-PG-08, FR-PG-09, FR-PG-10, FR-PG-11, FR-PG-12, GAP-0102, SCN-0023, UX-DR-PG-03, NFR-PG-08.

**Acceptance Criteria:**

**Given** Story 55.1’s `ProductSession` with `profile` ∈ `{authoring, app-use}`
**When** FEAT-0058 amends authoring instance optionality
**Then** `app_instance_id` MAY be absent when `profile=authoring`
**And** it remains required when `profile=app-use`. No third `ProductSessionProfile` is minted. Home/main is authoring with `app_instance_id` absent. (FR-PG-08; FR-PG-09; DEC-0463; SCN-0023 Then 1, Then 4; Branch A forbidden)

**Given** `selected_refs`
**When** kinds are validated
**Then** closed kinds gain `instance_id` in addition to Story 55.1’s parent AD-8 kinds (`artifact`, `research_ref`, `contribution`, `template`, `dataset`, `run`, `attempt`, `node_ids`)
**And** layout JSON, positions, widgets, and json-render trees remain refused. (FR-PG-10; DEC-0463)

**Given** an authoring session with `app_instance_id` absent
**When** invoke runs with exactly one `selected_refs` kind `instance_id`
**Then** envelope `instance_id` is taken from that ref and the callee GrantRecords of that instance bind
**And** envelope `instance_id` remains required on the invoke. (FR-PG-11; FR-PG-12; SCN-0023 Then 2; Branch C forbidden)

**Given** the same authoring session
**When** invoke is attempted with zero `instance_id` refs, or with two or more
**Then** the host returns typed `INVALID_INPUT` (ambiguous instance)
**And** it does not resolve to latest, first, or all. (FR-PG-11; SCN-0023 Then 3; Branch B forbidden)

**Given** DEC-0421
**When** this named amendment is recorded
**Then** DEC-0463 is a dated follow-up
**And** DEC-0421 is not set `superseded_by`. ADR-0024 Decision is not rewritten. (NFR-PG-08)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove optional authoring `app_instance_id` and `selected_refs` kind `instance_id` after this story
**And** claiming they already existed at that SHA fails the story (`ProductSession.app_instance_id` is required `str` there; `SELECTED_REF_KINDS` lacks `instance_id`). Claiming `product_session` types were absent there also fails the story. (NFR-PG-04; NFR-PG-05; SCN-0023 Branch D)

### Story 60.3: InvocationEnvelope gains caller_kind; instance_id stays required

As a host,
I want every public call to name whether the caller is a user, an agent, or a workflow,
So that a nested workflow call cannot pretend to be a user and an invoke cannot drop `instance_id`.

**Traceability:** FR-PG-12, FR-PG-15, GAP-0101, NFR-PG-01, NFR-PG-08.

**Acceptance Criteria:**

**Given** Story 54.2’s InvocationEnvelope required field catalogue
**When** FEAT-0058 lands the named amendment
**Then** the envelope gains closed `caller_kind` ∈ `user | agent | workflow`
**And** there is no other caller kind. Additive CT-40 family format mint only — no new CT number. (FR-PG-15; DEC-0464; GAP-0101; NFR-PG-01)

**Given** that envelope
**When** a public call is dispatched (in-process, CLI, wire, or nested)
**Then** `caller_kind` is present and valid
**And** envelope `instance_id` remains required. Making `instance_id` optional fails the story. (FR-PG-12; DEC-0464; SCN-0023 Branch C)

**Given** Story 54.2 hop revalidation
**When** `caller_kind` is compared
**Then** the host still resolves contribution, descriptor, and GrantRecord from authoritative stores before execution
**And** the envelope remains signed/bound request context, not authority. Transport never bypasses it. (FR-PG-15; FR-WF-18 restated; Story 54.2)

**Given** DEC-0437
**When** this named amendment is recorded
**Then** DEC-0464 is a dated follow-up
**And** DEC-0437 is not set `superseded_by`. (NFR-PG-08)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove `caller_kind` on the envelope after this story
**And** claiming it already existed at that SHA fails the story (`INVOCATION_ENVELOPE_FIELDS` there omits `caller_kind`). Claiming InvocationEnvelope was absent there also fails the story. (NFR-PG-04; NFR-PG-05)

### Story 60.4: One copilot identity; nested invoke does not union grants; app-use cannot apply

As an operator using one QuantMind copilot across home and an optional in-app panel,
I want tools to stay the grant intersection and running work to survive panel dispose,
So that a nested call cannot widen tools and a tab close cannot kill a Mission.

**Traceability:** FR-PG-07, FR-PG-13, FR-PG-14, FR-PG-16, UX-DR-PG-01, SCN-0024.

**Acceptance Criteria:**

**Given** QuantMind/QMX Copilot
**When** seats are compared
**Then** there is one product identity over independently scoped `psess:` sessions
**And** the in-app panel is an optional **contract** over an app-use `psess:`, not GAP-0081 chrome and not a second copilot product. A pack may omit a copilot profile; an instance may omit a panel. (FR-PG-07; UX-DR-PG-01; DEC-0454; SCN-0024)

**Given** tool availability
**When** it is computed
**Then** it is published ContributionHits ∩ host grants ∩ session GrantRecords ∩ health (parent AD-9)
**And** skills describe; they do not grant. ContributionHit ≠ grant. Hooks cannot override a failed privilege gate. (FR-PG-07; FR-PG-16; DEC-0458)

**Given** a nested public call
**When** it is dispatched
**Then** nested invoke does not union grants
**And** the child runs under the callee instance’s GrantRecords, not the caller’s plus the callee’s. (FR-PG-13; parent AD-10; SCN-0023 Then 2)

**Given** a running JobHandle
**When** a future UI tab or panel is disposed
**Then** running work is not cancelled
**And** reconnect resumes queries/events; it does not replay unacked intent. QMA `sess:` remains the engine run, not a third chat. Context transfer is explicit `selected_refs` or `change_request` only. (FR-PG-13; SCN-0024 Then 3; Branch C forbidden)

**Given** an app-use session
**When** a repair is needed
**Then** app-use may mint `change_request` and must not apply
**And** it must not edit package source, install code, elevate grants, or retarget accounts. Authoring plus operator principal applies (Workflows Story 58.4 / FEAT-0056 remains the apply oracle). (FR-PG-14; SCN-0024 Then 2; Branch B forbidden; AR-PG-11)

---

## Epic 61: A failed run says grant vs workflow vs view vs dependency vs host, in JSON-lines

Every public operation and every Task Graph run is diagnosable headless. Copilot or CLI receives closed `failure_class` plus JobHandle plus `correlation_id`. `qma-daemon` emits stdlib JSON-lines. Logs are not journals. QMN’s alert allow-list stays QMN.

**Factory touch ownership:** COMP-QMA-DAEMON stdlib JSON-lines operator logger and diagnosis query; COMP-QMA-WIRE diagnosis DTO on additive CT-40. Must not mint a fourth observability product. Must not extend `qmn/FAILURES.md`. Must not add a new sqlite class. Must not let agents author QMA telemetry. QMA telemetry store remains the trace/metric plane.

**Traceability:** FR-PG-19..FR-PG-22, NFR-PG-02, NFR-PG-06, NFR-PG-14, SCN-0027, GAP-0104, GAP-0105.

**What must already exist:** FEAT-0058 / Epic 60 (envelope `instance_id` / `op_id` / `logical_invocation_id`); FEAT-0042 / Epic 42 (daemon journal / sqlite; no new store class).

**What this delivers:** diagnosis and daemon logs. FEAT-0063 diagnosis journey waits on it. GAP-0104. GAP-0105 (failure_class half).

### Story 61.1: qma-daemon emits stdlib JSON-lines operator logs

As an operator reading daemon logs headless,
I want one JSON object per line with `ts`, `level`, `event`, and `correlation_id`,
So that I can join a failed run without treating logs as evidence.

**Traceability:** FR-PG-21, FR-PG-22, GAP-0104, NFR-PG-02, cheap-veto A8.

**Acceptance Criteria:**

**Given** a public operation or Task Graph run
**When** `qma-daemon` emits an operator log line
**Then** the line is stdlib JSON-lines logging with required fields `ts`, `level`, `event`, `correlation_id`
**And** when known it also includes `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Extra fields when present are cheap-veto A8 sitting machinery. (FR-PG-21; DEC-0456; DEC-0467)

**Given** those log lines
**When** they are stored or queried
**Then** they are never a journal and never secret values
**And** they do not enter `fp1` identity. Logs are not evidence (parent AD-16). (FR-PG-22; SCN-0027 Branch B forbidden)

**Given** a new observability COMP or sqlite class for mini-app logs
**When** proposed
**Then** it is refused
**And** QMA telemetry store remains the trace/metric plane; OTel remains export-port only. (NFR-PG-02; SCN-0027 Branch A forbidden)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove daemon JSON-lines after this story
**And** claiming the operator logger already existed at that SHA fails the story. (NFR-PG-04; SCN-0027 Branch E)

### Story 61.2: Diagnosis query returns closed failure_class plus JobHandle

As a copilot or CLI asking why the last run failed,
I want a closed `failure_class` of grant, workflow, view, dependency, or host,
So that “it broke” is never an untyped string and a stale widget is not an invoke failure.

**Traceability:** FR-PG-19, FR-PG-20, GAP-0105, cheap-veto A7, SCN-0027.

**Acceptance Criteria:**

**Given** a failed public operation or Task Graph run
**When** diagnosis is queried headless
**Then** the result includes `failure_class`, `job_handle` (or null), `correlation_id`, and `healthy`
**And** how-it-failed is the log line plus JobHandle `attempt_id` plus typed refusal. No fourth store. (FR-PG-20; CONTRACTS §5; SCN-0027 Then 1)

**Given** `failure_class`
**When** it is emitted
**Then** it is closed `grant | workflow | view | dependency | host`
**And** `view` means the wire DTO failed to mount, was stale, or was unhealthy — it is not an invoke. Spellings are cheap-veto A7 sitting machinery. (FR-PG-19; DEC-0467)

**Given** `correlation_id`
**When** it is used to join
**Then** it is the join key (never fp1)
**And** JobHandle stays on QMA AD-17 vocabulary (Story 57.3) — never `succeeded` or `awaiting_approval`. (FR-PG-20)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove kit `failure_class` after this story
**And** claiming it already existed as this diagnosis query at that SHA fails the story. QMN alert `failure_class` is a different noun and is not this pass. (NFR-PG-04; NFR-PG-14)

### Story 61.3: Logs are not evidence; QMN allow-list stays QMN; agents do not write telemetry

As a host,
I want mini-app failures to stay off the QMN alert allow-list and off agent-authored telemetry,
So that a pack cannot page the node with a fake alert and a model cannot write the trace plane.

**Traceability:** FR-PG-22, NFR-PG-14, SCN-0027.

**Acceptance Criteria:**

**Given** a mini-app typed failure
**When** first ids ship
**Then** they live in that owning package's FAILURES.md
**And** they are never added to `qmn/FAILURES.md`. (FR-PG-22; SCN-0027 Then 3; Branch C forbidden)

**Given** QMA telemetry
**When** it is authored
**Then** it is harness-authored
**And** a model-authored hook that emits QMA telemetry fails the story. Agents must not write it. (FR-PG-22; SCN-0027 Branch D forbidden)

**Given** Story 61.1 log lines
**When** compared to journals and to QMB LogSink
**Then** logs remain logs
**And** QMB LogSink may remain; new daemon code does not invent a third logger. (FR-PG-22; kit AD-5)

---

## Epic 62: Ordinary none/read flakes retry in the host; live sends never get a blind second try

Retry is host/SDK behaviour. Default **on** means effect `none` and `read` retry until success, typed `retryability=NO`, or the host-registered attempt ceiling. The parent AD-24 matrix does not loosen. Stories invent no ceiling number.

**Factory touch ownership:** COMP-QMA-CORE effect-class retry policy; COMP-QMA-DAEMON host retry loop on the envelope. Must not invent a per-pack retry enum. Must not blind-retry `external-egress`. Must not auto-retry `unknown-blocked`. Must not hardcode a sitting-invented ceiling such as `3`.

**Traceability:** FR-PG-23..FR-PG-27, NFR-PG-13, SCN-0026, GAP-0106, GAP-0108, cheap-veto A9.

**What must already exist:** FEAT-0058 / Epic 60; FEAT-0052 / Epic 54 (effect-class idempotency matrix and `reconcile_policy`).

**What this delivers:** default host retry. FEAT-0063 retry journey waits on it. GAP-0106. GAP-0108 design closed (registry row; no number).

### Story 62.1: Host retries none/read on the same logical_invocation_id

As an operator running a mini-app whose `read` op flakes,
I want the host to retry without paging me,
So that ordinary hiccups are not my recovery loop.

**Traceability:** FR-PG-23, GAP-0106, GAP-0108, NFR-PG-13, SCN-0026 Then 1.

**Acceptance Criteria:**

**Given** a public call whose `effect_class` is `none` or `read` and whose typed `retryability` is not `NO`
**When** it flakes
**Then** the host retries until success, until typed `retryability=NO`, or until the host-registered attempt ceiling
**And** attempts increment `attempt_id` on the same `logical_invocation_id`. The operator is not the recovery loop. (FR-PG-23; DEC-0457; SCN-0026 Then 1)

**Given** the attempt ceiling
**When** it is read
**Then** it is a host-registered registry row
**And** this story mints no number. Tests may inject a ceiling for a fixture (AR-PG-10). Production code must not hardcode a sitting-invented default such as `3`. (GAP-0108; cheap-veto A9; SCN-0026 Branch C forbidden; NFR-PG-13)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove the host retry **loop** after this story
**And** claiming the loop already existed at that SHA fails the story. Claiming effect-class / `reconcile_policy` types were absent there also fails the story (CONNECT fixtures). (NFR-PG-04; SCN-0026 Branch D)

### Story 62.2: Effect-class matrix does not loosen; no blind external-egress retry

As a host facing an unsure live or external action,
I want the parent effect-class matrix to win,
So that a missing receipt cannot become a second send and a CAS conflict cannot become a retry.

**Traceability:** FR-PG-24, FR-PG-25, SCN-0026 Then 2–4.

**Acceptance Criteria:**

**Given** `effect_class=external-egress` with no receipt
**When** retry/reconcile is considered
**Then** the outcome is `unknown`
**And** the host MUST NOT blind-retry. There is no second send. (FR-PG-24; SCN-0026 Then 2; Branch B forbidden)

**Given** `effect_class=mutate-config` CAS result `conflict`
**When** retry is considered
**Then** `conflict` is not a retry
**And** `append-evidence` still dedupes; `place-run` still uses `logical_invocation_id` as run identity; outbox replay is not a second dispatch (Story 57.2). (FR-PG-24; Story 54.3)

**Given** `reconcile_policy` `never-retry` or `unknown-manual`
**When** it is set
**Then** it wins over default host retry
**And** parent AD-25 `unknown-blocked` is never auto-retried. (FR-PG-25; SCN-0026 Then 4; Story 59.3)

### Story 62.3: A pack may zero attempts; repair is change_request, not hot-apply

As a pack author who wants no automatic retry,
I want to set attempts to zero without inventing a retry dialect,
So that implementation edits still go through change-request and app-use still cannot apply.

**Traceability:** FR-PG-26, FR-PG-27, SCN-0026 Then 5.

**Acceptance Criteria:**

**Given** a pack
**When** it sets retry attempts to zero
**Then** the host does not retry that op
**And** the pack MUST NOT exceed the host ceiling or the effect-class matrix. A per-pack retry enum is refused. (FR-PG-26; SCN-0026 Branch A forbidden)

**Given** an implementation edit after a failure (code, graph, grants, account target)
**When** repair is requested
**Then** it is a `change_request`: app-use may mint; authoring plus operator apply
**And** alerts never authorize. HMR and hot-apply stay dead (DEC-0366). (FR-PG-27; SCN-0026 Then 5; Workflows Story 58.4 / FEAT-0056)

---

## Epic 63: A workflow starts another as one nested Mission; two live graphs never splice

Workflow-to-workflow at runtime is parent-AD-3 invoke of the callee template creating one nested Mission / one Task Graph / one JobHandle. Include-at-author writes a new versioned Graph Template. Merging two live Task Graphs is refused. Widgets bind `start`; they do not own invoke.

**Factory touch ownership:** COMP-QMA-DAEMON nested Mission invoke on durable Task Graph / outbox (Epic 57); COMP-QMA-CORE lifecycle verbs on the callee template. Must not splice live graphs. Must not add a fifth composition mode. Must not let a widget execute without an envelope. Must not union nested grants.

**Traceability:** FR-PG-28..FR-PG-32, SCN-0025, GAP-0107.

**What must already exist:** FEAT-0055 / Epic 57 (durable edges, outbox, JobHandle); FEAT-0058 / Epic 60 (`caller_kind=workflow`, envelope `instance_id`).

**What this delivers:** nested Mission invoke. FEAT-0063 nested-workflow journey waits on it. GAP-0107.

### Story 63.1: Nested Mission invoke is start/query-state/cancel/await with its own JobHandle

As a Graph Template author whose node starts another template,
I want that start to be one nested Mission with its own JobHandle,
So that occupancy and cancel follow the callee and crash of A cannot copy B’s nodes into A.

**Traceability:** FR-PG-29, FR-PG-13, GAP-0107, SCN-0025 Then 2.

**Acceptance Criteria:**

**Given** registered Graph Templates A and B, each `(qualified_id, version)`
**When** a node of A starts B at runtime
**Then** the call is parent-AD-3 invoke of B’s existing `start | query-state | cancel | await` (CONNECT: those verbs already exist on `OperationDescriptor` at `34c148b`)
**And** the result is **one nested Mission / one Task Graph / one JobHandle**. Envelope `caller_kind=workflow`. Envelope `instance_id` remains required. Do not mint a second verb set. (FR-PG-29; DEC-0455; Story 60.3; AR-PG-09)

**Given** that nested JobHandle
**When** occupancy or cancel is considered
**Then** they follow that JobHandle
**And** nested invoke does not union grants (Story 60.4). (FR-PG-29; FR-PG-13; SCN-0025 Then 2; Branch C forbidden)

**Given** a crash of A while B is running
**When** recovery runs
**Then** B’s Task Graph is not spliced into A’s
**And** A does not copy B’s nodes. This is nested-Mission occupancy (FR-PG-29; SCN-0025 Branch A), not the live-merge refuse in Story 63.2. This story does not implement include-at-author or the recursion-ceiling row. (FR-PG-29; SCN-0025 Branch A forbidden)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove nested Mission invoke as a first-class occupancy after this story
**And** claiming that occupancy already existed at that SHA fails the story. Claiming `call_depth` / `parent_logical_invocation_id` / lifecycle verbs were absent there also fails the story (CONNECT). (NFR-PG-04; SCN-0025 Branch D; AR-PG-09)

### Story 63.2: Include-at-author writes a new version; live merge and over-budget depth refuse

As an author composing two workflows,
I want include-at-author to create a new Graph Template version,
So that runtime cannot merge two live Task Graphs and recursion cannot run forever.

**Traceability:** FR-PG-30, FR-PG-31, FR-PG-32, SCN-0025 Then 3–4.

**Acceptance Criteria:**

**Given** authoring that includes B’s subgraph into A
**When** it is saved
**Then** the result is a **new versioned** Graph Template
**And** it is not a runtime merge of live Task Graphs. (FR-PG-30; DEC-0455)

**Given** an attempt to merge two live Task Graphs
**When** it is dispatched
**Then** the host refuses with `INVALID_INPUT` or the owner COMP’s illegal-topology refusal
**And** partial failure does not silently substitute another instance, version, or account. (FR-PG-31; SCN-0025 Then 4)

**Given** envelope `call_depth` against the host-registered recursion ceiling
**When** the ceiling is exceeded
**Then** the call is `INVALID_INPUT`
**And** this story mints no recursion-ceiling number. That host-registered row is **not** GAP-0108 (GAP-0108 is the retry-attempt ceiling under Story 62.1 / FEAT-0060). Do not reuse the retry registry row for `call_depth`. (FR-PG-32; DEC-0455; AR-PG-10)

### Story 63.3: A widget binds start; it does not own invoke; dispose does not cancel

As a user or agent pressing a widget bound to template T,
I want that press to be an enveloped `start` with `caller_kind=user` or `agent`,
So that disposing the widget cannot cancel the Mission and a widget cannot become a fifth composition mode.

**Traceability:** FR-PG-28, SCN-0025 Then 1, UX-DR-PG-02.

**Acceptance Criteria:**

**Given** a widget bound to `start` of template T
**When** a user or agent presses it
**Then** the envelope carries `caller_kind=user` or `agent` and required `instance_id`
**And** the widget does not introduce a fifth composition mode. Parent AD-10 four modes remain. (FR-PG-28; SCN-0025 Then 1)

**Given** that Mission’s JobHandle
**When** the widget is disposed
**Then** the Mission is not cancelled
**And** a widget contribution point that executes without an envelope is refused. (FR-PG-28; SCN-0025 Branch B forbidden; UX-DR-PG-02)

---

## Epic 64: Copilot and CLI list published vs healthy and read instance health()

The host exposes five independent listing booleans including `healthy`. Story 53.4 CONNECT names the third axis `granted`. This epic AMENDs that axis to kit `authorized` (parent AD-15), which is not a session GrantRecord. Instance `health()` is the existing component typed-report, distinct from pack `published`. Copilot and CLI consume the same headless queries. No chrome dashboard.

**Factory touch ownership:** COMP-QMA-DAEMON instance `health()` query for pack instances; COMP-QMA-WIRE listing DTO minted in Story 53.4. Must not re-author ContributionHit identity or pin/tombstone. Must not leave two live third-axis names (`granted` and `authorized`). Must not treat published as healthy. Must not treat `authorized` as `product_session.granted_ops`. Must not ship GAP-0081 / GAP-0100 chrome. Inventory size is multi-pass — this epic is **H**.

**Traceability:** FR-PG-33, FR-PG-34, UX-DR-PG-04, DEC-0428, GAP-0105.

**What must already exist:** FEAT-0058 / Epic 60 (pack instance rows and GrantRecords); FEAT-0051 / Epic 53 (ContributionHit concatenate and listing axes).

**What this delivers:** listing and health queries for copilot/CLI. FEAT-0063 headless listing/health journey waits on it.

### Story 64.1: Listing axes stay independent; published is not healthy

As a copilot or CLI listing contributions,
I want published, configured, authorized, reachable, and healthy to stay independent booleans,
So that seeing a published hit cannot be mistaken for a healthy authorized instance.

**Traceability:** FR-PG-33, Story 53.4, DEC-0428.

**Acceptance Criteria:**

**Given** Story 53.4’s `CONTRIBUTION_LISTING_STATUS_AXES` at `34c148b` (`published`, `configured`, `granted`, `reachable`, `healthy`)
**When** FEAT-0062 lands the kit AMEND
**Then** five independent booleans remain, and the third axis’s live kit name is `authorized` (parent AD-15)
**And** this story does not re-author ContributionHit identity or pin/tombstone (Epic 53). Claiming those axes were absent at `34c148b` fails the story. Leaving both `granted` and `authorized` as live third-axis names also fails. (FR-PG-33; Story 53.4; DEC-0465)

**Given** kit `authorized`
**When** it is rendered
**Then** it is not a session GrantRecord and not `product_session.granted_ops`
**And** a ContributionHit is not a grant even when published and healthy. (FR-PG-33; parent AD-15; FR-WF-06 restated)

**Given** `published` vs `healthy`
**When** they differ
**Then** published is not healthy
**And** collapsing them into one `status` field remains refused (Story 53.4). (FR-PG-33)

**Given** GAP-0081 chrome or GAP-0100 dashboard
**When** proposed as this story
**Then** it is refused
**And** copilot and CLI consume the same **headless** queries. (UX-DR-PG-04; DEC-0468)

### Story 64.2: Instance health() is a typed-report distinct from pack published

As an operator asking whether instance A is healthy,
I want `health()` as the existing component typed-report,
So that pack `published` cannot stand in for instance health.

**Traceability:** FR-PG-34, GAP-0105, DEC-0112.

**Acceptance Criteria:**

**Given** a mini-app instance
**When** `health()` is queried
**Then** the result is the existing component typed-report (DEC-0112)
**And** it is distinct from pack `published`. (FR-PG-34; DEC-0456)

**Given** copilot and CLI
**When** they read listing and health
**Then** they consume the same headless queries
**And** neither path invents a dashboard. (FR-PG-34; UX-DR-PG-04)

**Given** inspect SHA `34c148b`
**When** this story is accepted
**Then** tests prove instance `health()` for pack instances after this story
**And** claiming listing axes were absent there fails the story (Story 53.4 CONNECT). Claiming QMN/QMF component `health()` already was this instance report also fails the story. (NFR-PG-04; AR-PG-09)

---

## Epic 65: Thin fixtures prove the kit journeys without claiming they already ran at 34c148b

Thin fixtures prove J-KIT-01 headless pack with no copilot; J-KIT-02 optional panel cannot apply; J-KIT-03 home exactly-one instance; J-KIT-04/05 nested Mission not live merge; J-KIT-06 host retry none/read and no invented ceiling; J-KIT-07 weak model fills schemas. They do not fill chrome. They do not claim e2e at `34c148b`.

**Factory touch ownership:** fixture packages under COMP-QMA-CORE / COMP-QMA-DAEMON / COMP-QMA-WIRE tests. Must trail Workflows Epic 58 / FEAT-0056 so change-request and pack export stay the same envelopes. Must not invent chrome. Must not close GAP-0081 / GAP-0100.

**Traceability:** FR-PG-17, FR-PG-18, FR-PG-35..FR-PG-42, SCN-0023..SCN-0027, NFR-PG-03, NFR-PG-09.

**What must already exist:** FEAT-0058..FEAT-0062; FEAT-0056 / Workflows Epic 58 (change-request and pack export fixtures).

**What this delivers:** honesty oracles for the kit journeys. Implementation authorization remains factory-pipeline-only.

### Story 65.1: J-KIT-01 — headless pack with no copilot still invokes

As an operator enabling a pack with operations and no views and no copilot profile,
I want main authoring to invoke via CLI/wire and receive a JobHandle,
So that a pack does not need a screen or a copilot to ship.

**Traceability:** FR-PG-36, FR-PG-03, SCN-0024 Then 1, J-KIT-01.

**Acceptance Criteria:**

**Given** a pack that omits `view:*` and omits `copilot_profile`, enabled after Story 60.1
**When** the main authoring session invokes an op via CLI/wire
**Then** the run produces a JobHandle
**And** no in-app panel exists. Main authoring can still reference the pack. (FR-PG-36; SCN-0024 Then 1)

**Given** SCN-0024 Branch A
**When** enable is attempted
**Then** requiring a copilot to ship fails the fixture
**And** install remains not a grant. (FR-PG-02; FR-PG-03)

### Story 65.2: J-KIT-02 — optional panel cannot apply; dispose does not cancel

As an app-use session on instance A with an optional panel,
I want the panel to ask why the last run failed and mint a change-request,
So that the panel cannot apply v2 and closing it cannot kill the work.

**Traceability:** FR-PG-37, FR-PG-14, FR-PG-13, SCN-0024 Then 2–3, J-KIT-02.

**Acceptance Criteria:**

**Given** an app-use session on instance A with an optional panel, after Stories 60.4 and 61.2
**When** the panel asks why the last run failed
**Then** the host returns `failure_class` plus JobHandle (or null)
**And** the panel cannot edit the pack. (FR-PG-37; SCN-0024 Then 2)

**Given** that panel
**When** a `change_request` is minted
**Then** app-use mints and must not apply
**And** authoring plus operator applies; v1 instance stays until apply (Workflows Story 58.4 / FEAT-0056 remains the apply oracle). (FR-PG-14; SCN-0024 Branch B forbidden; AR-PG-11)

**Given** running work
**When** the panel or a future UI tab is closed
**Then** the JobHandle is not cancelled
**And** reconnect does not replay unacked intent. (FR-PG-13; SCN-0024 Branch C forbidden)

### Story 65.3: J-KIT-03 — home authoring exactly-one instance_id

As an operator on the main copilot with nothing selected,
I want invoke to work only after exactly one `instance_id` is selected,
So that zero or two refs refuse and a nested call cannot widen tools.

**Traceability:** FR-PG-38, FR-PG-11, SCN-0023, J-KIT-03.

**Acceptance Criteria:**

**Given** Story 60.2’s authoring session with `app_instance_id` absent
**When** the operator selects exactly one `selected_refs` kind `instance_id` and invokes
**Then** envelope `instance_id` is that ref and that instance’s GrantRecords bind
**And** every Then branch of SCN-0023 holds. (FR-PG-38; SCN-0023)

**Given** zero or two `instance_id` refs
**When** invoke is attempted
**Then** typed `INVALID_INPUT`
**And** implementing a Failure branch (third profile, silent latest, optional envelope `instance_id`, claiming wired at `34c148b`) fails the fixture. (FR-PG-11; SCN-0023 Branches A–D)

**Given** a nested call from that invoke
**When** tools are computed
**Then** nested call does not widen tools
**And** grants do not union. (FR-PG-13; SCN-0023 Then 2)

### Story 65.4: J-KIT-04/05 — widget binds start; nested Mission is not a live merge

As an author whose template A starts template B,
I want B to be one nested Mission,
So that include-at-author is a new version and a live merge is refused.

**Traceability:** FR-PG-39, FR-PG-28, FR-PG-29, FR-PG-30, FR-PG-31, SCN-0025, J-KIT-04, J-KIT-05.

Inventory FEAT-0063 names J-KIT-05 as the nested journey. J-KIT-04 (widget binds `start`) is SCN-0025 Then 1 on the same fixture — keep both; do not drop the widget bind.

**Acceptance Criteria:**

**Given** Stories 63.1–63.3
**When** a user or agent presses a widget bound to `start` of template T
**Then** envelope `caller_kind` is `user` or `agent` and widget dispose does not cancel
**And** every Then branch of SCN-0025 holds. (FR-PG-39; SCN-0025 Then 1)

**Given** template A starting template B as a nested Mission
**When** the fixture runs
**Then** B has its own JobHandle and crash of A does not splice B’s Task Graph into A
**And** include-at-author produces a new versioned Graph Template. Live merge is refused. (FR-PG-29; FR-PG-30; FR-PG-31; SCN-0025 Branches A–C forbidden)

### Story 65.5: J-KIT-06 — read retries; external-egress does not; no invented ceiling

As an operator whose `read` op flakes,
I want the host to retry and an unsure live send to become `unknown`,
So that I am not paged for hiccups and stories cannot invent the ceiling number.

**Traceability:** FR-PG-40, FR-PG-23, FR-PG-24, SCN-0026, J-KIT-06, GAP-0108.

**Acceptance Criteria:**

**Given** Stories 62.1–62.3
**When** a `read` op flakes with typed `retryability` that is not `NO`
**Then** the host retries and the operator is not paged
**And** an `external-egress` without a receipt becomes `unknown` with no second send. (FR-PG-40; SCN-0026 Then 1–2)

**Given** GAP-0108
**When** this fixture is accepted
**Then** it invents no ceiling number
**And** implementing SCN-0026 Branch C (hardcoding `3` or another cap as the sitting’s number) fails the fixture. Tests may inject a registry value (AR-PG-10). (NFR-PG-13; SCN-0026 Branch C)

### Story 65.6: J-KIT-07 — weak model fills schemas; diagnosis is honest; graduation does not skip enable

As a weaker/older model authoring a pack,
I want host validate to fail closed on a missing dependency,
So that prose cannot add an op and fixtures cannot claim e2e at `34c148b`.

**Traceability:** FR-PG-17, FR-PG-18, FR-PG-41, FR-PG-42, FR-PG-16, FR-PG-35, SCN-0027 Then 4, J-KIT-07.

**Acceptance Criteria:**

**Given** a weaker/older model filling descriptor schemas and requested capabilities (Story 60.1 / 60.4)
**When** host validate is missing a dependency
**Then** validate fails closed
**And** model prose cannot add an op. Skills describe; they do not grant. JSON Render catalog `action` names an existing `op_id`; MCP App `tools/call` is intercepted by the host against the session GrantRecord. Neither adapter can add ops or fields. `@json-render/*` and `@modelcontextprotocol/ext-apps` stay unpinned. (FR-PG-41; FR-PG-16; FR-PG-17; FR-PG-18; SCN-0027 Then 4; DEC-0458; DEC-0459)

**Given** pack export of those operations after validate
**When** graduation runs
**Then** it does not skip parent AD-18/AD-30 enable/validate
**And** a Loop remains node state at runtime (parent AD-4). (FR-PG-35; DEC-0460)

**Given** SCN-0027 diagnosis + JSON-lines after Epic 61
**When** this fixture is accepted
**Then** every Then branch of SCN-0027 holds
**And** implementing a Failure branch (fourth observability product, logs as evidence, QMN allow-list reuse, agents writing telemetry, claiming daemon JSON-lines at `34c148b`) fails the fixture. (FR-PG-42; SCN-0027 Branches A–E)

**Given** GAP-0081 chrome or GAP-0100 dashboard
**When** proposed as this epic
**Then** it is refused
**And** class/test existence is not e2e (DEC-0286). Claiming kit field changes were wired at `34c148b` fails the epic. (FR-PG-42; UX-DR-PG-04; DEC-0465)

---

## Final validation (Step 4)

- **FR coverage:** FR-PG-01..42 each appear in the coverage map and in at least one story AC.
- **UX-DR coverage:** UX-DR-PG-01 and 03 appear in Epic 60. UX-DR-PG-02 (adapters unpinned) appears in Story 65.6. UX-DR-PG-04 is explicitly out (GAP-0081 / GAP-0100).
- **Starter template:** none. Epic 60 Story 60.1 extends existing `PluginManifest` / CT-40 family; it does not scaffold a new distribution.
- **Entities:** no new sqlite class. `copilot_profile` is a request blob on the existing manifest. Kit `requested_capabilities` AMENDs existing `permissions`. Authoring `app_instance_id` optionality amends the existing `product_session` projection. Daemon JSON-lines are stdlib logging, not a journal. Retry ceiling is a registry row, not a new store. Recursion ceiling is a different registry row. Nested Mission uses Epic 57 `task_graph_state` / outbox. Instance `health()` is the existing typed-report, not a new table. Listing third axis AMENDs Story 53.4 `granted` to kit `authorized`.
- **Forward dependencies:** none inside an epic. 60.2 uses 60.1’s grant law; 60.3 uses 54.2 catalogue plus 60.2’s required envelope `instance_id`; 60.4 uses 60.1–60.3. 61.2 uses 61.1 join fields; 61.3 uses 61.1–61.2. 62.2–62.3 use 62.1. 63.2–63.3 use 63.1. 64.2 uses 64.1. 65.* are independent fixtures on prior epics (Workflows 58 / FEAT-0056 plus 60–64).
- **Epic independence:** Epic 60 is valuable without 61 (SDK fields work without JSON-lines). Epic 61 needs 60’s envelope ids (declared blocker) and is valuable without 62. Epic 62 needs 60’s envelope/effect_class (declared) and is valuable without 61. Epic 63 needs 60’s `caller_kind` and Epic 57’s outbox (declared) and is valuable without 61/62. Epic 64 needs 60’s instance rows and Epic 53’s listing (declared) and is valuable without 61’s `failure_class`. Epic 65 needs 60–64 plus Workflows Epic 58 / FEAT-0056 (declared).
- **File churn:** 60+62 share COMP-QMA-CORE **intentionally** (envelope field vs retry loop — different risk: named amendment vs money-path double-send). 61+64 share COMP-QMA-DAEMON/WIRE **intentionally** (JSON-lines logger vs listing/`health()` query — GAP-0105 spans both; sequence steps 2 vs 5). 60+61+63+64 share COMP-QMA-DAEMON **intentionally** (session amendment vs logger vs nested Mission vs health — NFR-PG-02 closed list, different records). Consolidation of 61+64 and of 60+62 was considered and rejected in the Epic List.
- **Architecture:** reuse-only; no new COMP; no new CT; GAP-0081 chrome / GAP-0100 dashboard unfilled; no sixth COMP; no third profile; no live-graph merge; json-render/MCP unpinned; retry ceiling number not invented; mill FEAT-0047 not started; FEAT-0001 not started.
- **Honesty:** inspect `integration@34c148b` (DEC-0465). Parent freeze `270e992` for ADR-0024 original Decision (DEC-0450). Fixtures are not e2e (DEC-0286). Envelope `instance_id` stays required on invoke. Authoring may omit `app_instance_id`. `caller_kind` is `user|agent|workflow`.
- **Factory:** this document does not launch factory lanes. Implementation authorization remains factory-pipeline-only (DEC-0461). `main` moves only by the operator’s squash-merge click.
