---
id: ADR-0025
title: QMX pack-and-grant kit — SDK, optional copilot, host observability, default retry
type: adr
status: ratified
component: COMP-QMA-CORE
depends_on: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON, COMP-QMB, COMP-QML, COMP-QMN]
decisions: [DEC-0452, DEC-0453, DEC-0454, DEC-0455, DEC-0456, DEC-0457, DEC-0458, DEC-0459, DEC-0460, DEC-0461, DEC-0462, DEC-0463, DEC-0464, DEC-0465, DEC-0466, DEC-0467, DEC-0468]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/REQUIREMENTS-ADDENDUM.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/CONTRACTS.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/COPILOT-AND-APPS.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/IMPLEMENTATION-SEQUENCE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/.memlog.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/reviews/gate-summary.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/research/SDK-HYBRID-AND-CORE.md, _docwork/pack-and-grant-increment-brief.md, _docwork/riders/pack-and-grant-kit-2026-09-23.md, _docwork/ledger.yaml, docs/decisions/ADR-0024-workflows-construction-kit.md]
generated: 2026-09-23
verified: 2026-09-23
stale_after: 1y
---

# ADR-0025: QMX pack-and-grant kit — SDK, optional copilot, host observability, default retry

Date: 2026-09-23. Status: accepted (docs authority only).

## Context

The 2026-09-19 Workflows construction kit ([ADR-0024](ADR-0024-workflows-construction-kit.md), DEC-0414..DEC-0451) already bound composition, grants, outbox, JobHandle, and change-request over existing applications. It left unnamed the **SDK relationship**: how a pack author declares operations, optional views, requested access, and an optional copilot; how home/main chat sits with no instance; how an app, workflow, or widget uses another; how every pack is diagnosable; how ordinary failures retry in the host.

The 2026-09-23 architecture sitting (`architecture-QMX-2026-09-23`, local AD-1..AD-9) is a child feature spine inheriting parent 09-18 AD-1..AD-31 read-only. The operator accepted that sitting as the plan to fold. This ADR records the documentation-factory absorption. It does not authorize implementation, credentials, a live session, order submission, promotion, or go-live — those arrive only through the factory pipeline (DEC-0461). ADR-0024 Decision stands as written. ADR-0023 remains provisional. No sixth COMP. No new CT number (DEC-0462).

Planning checkout is `main` @ `92279dfe43922d60fabe38e29284ca52956ab75c`. Implementation was inspected on `integration@34c148b` via `.worktrees/integration-inspect` without switching branches. Parent freeze honesty at `270e992` still applies for ADR-0024 original Decision text (DEC-0450). Fixtures are not e2e (DEC-0286, DEC-0465).

Cite parent 09-18 ADs as `parent AD-n`. Cite this sitting as `kit AD-n`. Local `kit AD-8` is presentation adapters; `parent AD-8` is product_session.

## Options considered

1. **Screen kit (dashboards first)** — rejected because headless packs would be second-class (DEC-0452, DEC-0466).
2. **Automation kit (graphs first)** — rejected because the board starts pretending it is the engine (DEC-0452, DEC-0466).
3. **Mint a sixth COMP or a second copilot product** — rejected because QMF stays one framework (L7) and parent AD-1 already forbids a sixth application (DEC-0414, DEC-0462, DEC-0466).
4. **Third ProductSessionProfile for home/main** — rejected because home is authoring with `app_instance_id` absent (DEC-0463).
5. **Pack-and-grant kit** — chosen. A pack declares operations, optional views, requested access, optional copilot profile. The host grants. Workflows compose operations. Widgets are views of operations (DEC-0452, DEC-0461).

## Decision

The pack-and-grant spine kit AD-1..AD-9 is adopted in full as DEC-0452 through DEC-0460. The umbrella is DEC-0461. Architecture-preflight is DEC-0462. Named parent amendments are DEC-0463 (parent AD-8 / DEC-0421) and DEC-0464 (parent AD-24 / DEC-0437). Wiring honesty at `34c148b` is DEC-0465. Dead-list honors are DEC-0466. Cheap-veto A7–A9 ride DEC-0467.

- **kit AD-1 / DEC-0452 — pack-and-grant is the SDK.** A pack manifest **requests** operation contributions, optional `view:*` wire DTOs (parent AD-17, not a contribution point), optional `copilot_profile` request blob (not a contribution point and not a grant), and `requested_capabilities`. The host **grants** GrantRecords into a `psess:`. Installing is not granting. Enabling after validate is not granting. Headless packs are first-class.
- **kit AD-2 / DEC-0453 — kit nouns span the platform; QMA is host not owner of every op.** Mini-app, widget, and workflow are kit nouns over the whole platform. Bytes of a pack live in the plugin tree plus daemon install/instance rows. Execution of each `op_id` is owned by the COMP named on the descriptor. Widgets never own invoke. Broker/venue stays QMN.
- **kit AD-3 / DEC-0454 — one copilot; many sessions; in-app panel optional.** QuantMind/QMX Copilot is one product identity. `ProductSessionProfile` remains `{authoring, app-use}`. A pack may omit a copilot profile. An instance may omit an in-app panel. Authoring with absent `app_instance_id` may not invoke until exactly one `selected_refs` kind `instance_id` is present (DEC-0463). Nested invoke does not union grants. `sess:` remains the engine run, not a third chat. Running work is not cancelled by panel dispose. Context transfer is explicit `selected_refs` or `change_request` only.
- **kit AD-4 / DEC-0455 — caller is user, agent, or workflow.** Every public call carries parent AD-24 InvocationEnvelope including named-amendment `caller_kind` `user | agent | workflow` (DEC-0464). Envelope `instance_id` remains required on every invoke. Workflow-to-workflow at runtime is parent-AD-3 invoke of the callee template (`start | query-state | cancel | await`) creating **one nested Mission / one Task Graph / one JobHandle**. Include-at-author is a new versioned Graph Template. Merging two live Task Graphs is refused. Nested depth is envelope `call_depth` against the host-registered recursion ceiling; this sitting mints no number.
- **kit AD-5 / DEC-0456 — host observability is a relationship every pack inherits.** Headless: listing axes including `healthy`; instance `health()` (DEC-0112); JobHandle in QMA AD-17 vocabulary; typed refusal; `correlation_id`; harness-authored QMA telemetry. Failure class is closed: `grant | workflow | view | dependency | host`. `view` means the wire DTO failed to mount, was stale, or was unhealthy — it is not an invoke. `qma-daemon` emits stdlib JSON-lines (`ts`, `level`, `event`, `correlation_id` required; `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id` when present). Logs are not evidence. Do not extend `qmn/FAILURES.md`. Do not mint a fourth observability product.
- **kit AD-6 / DEC-0457 — default host retry; implementation repair is change-request.** Default **on** for effect `none` and `read` until success, typed `retryability=NO`, or the host-registered attempt ceiling (registry row; this sitting mints no number — GAP-0108). Parent AD-24 / SCN-0021 remain: no blind `external-egress` retry; CAS `conflict` is not a retry; `unknown-blocked` is never auto-retried. A pack may set attempts to zero and must not exceed the host ceiling. Implementation edits are `change_request`: app-use may mint; authoring plus operator apply. HMR and hot-apply stay dead.
- **kit AD-7 / DEC-0458 — weak models operate through schemas.** Load-bearing surfaces are descriptors, GrantRecords, `input_schema`, typed refusals, and host-intercepted tool calls. Skills describe; they do not grant. MCP App HTML and json-render catalog entries cannot add ops or fields.
- **kit AD-8 / DEC-0459 — presentation adapters stay unpinned.** JSON Render is a catalog-constrained generative view. MCP Apps are an optional sandboxed view. Native QMX panes remain first. Do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps`. Chrome remains GAP-0081 / GAP-0100.
- **kit AD-9 / DEC-0460 — tested work graduates to a pack.** Daily idea path: yap at authoring → Graph Template → runs with JobHandles → pack export after validate. A Loop remains node state. Graduation does not skip parent AD-18/AD-30.
- **Named parent AD-8 / DEC-0463.** `app_instance_id` MAY be absent when `profile=authoring`. It remains required when `profile=app-use`. Closed `selected_refs` kinds gain `instance_id`. Do not set DEC-0421 `superseded_by`. No third profile.
- **Named parent AD-24 / DEC-0464.** InvocationEnvelope gains closed `caller_kind`. Envelope `instance_id` remains required on invoke. Do not set DEC-0437 `superseded_by`. No new CT number.

## Architecture-preflight verdict

**reuse** existing applications. **new COMP: none. new CT: none.** No new `depends_on` edge. No existing component's authority shrinks (DEC-0462).

| Work | Owner | Class |
|---|---|---|
| Pack SDK (optional `copilot_profile`, request≠grant) | COMP-QMA-CORE + COMP-QMA-DAEMON plugin lifecycle | extend parent AD-18/AD-30 |
| Authoring `app_instance_id` optional; `selected_refs` kind `instance_id` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named amend DEC-0421 |
| Envelope `caller_kind` | COMP-QMA-CORE + COMP-QMA-WIRE | named amend DEC-0437 |
| Daemon JSON-lines + diagnosis query | COMP-QMA-DAEMON + COMP-QMA-WIRE | connect; QMA telemetry store stays |
| Default host retry none/read | COMP-QMA-CORE effects + COMP-QMA-DAEMON | extend parent AD-24 matrix |
| Nested Mission invoke | COMP-QMA-DAEMON | extend parent AD-7/AD-10 |
| Listing axes + instance `health()` | COMP-QMA-DAEMON + COMP-QMA-WIRE | extend parent AD-15 |
| Views / MCP Apps / json-render | COMP-QMA-WIRE DTOs | parent AD-17; unpinned |

Candidates refused by id (DEC-0462, DEC-0466): COMP-WF / sixth COMP; new CT-*; third ProductSessionProfile; merged live Task Graphs; json-render/MCP as identity; QMB/QML core fork; fourth observability product; extending `qmn/FAILURES.md`; HMR/hot-apply; app-use applying `change_request`.

Dead list honored: DEC-0084 stays dead, DEC-0085 stays dead, DEC-0086 stays dead, DEC-0361 stays dead, DEC-0362 stays dead, DEC-0366 stays dead, DEC-0408..0413 stay dead (DEC-0466).

## Wiring honesty @ 34c148b (DEC-0465)

**CONNECT (types/fixtures exist; not e2e):** InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, effect-class plus `reconcile_policy`, `call_depth` / `parent_logical_invocation_id`, Workflows 53–59 fixtures.

**AMEND:** `ProductSession.app_instance_id` is required `str`; `SELECTED_REF_KINDS` lacks `instance_id`; envelope has no `caller_kind`.

**ABSENT as product surface:** pack `copilot_profile`; `qma-daemon` stdlib JSON-lines operator logger; kit `failure_class`; default host retry loop; nested Mission invoke as first-class; CheckpointManifest.

Parent freeze `270e992` still applies for ADR-0024 original Decision (DEC-0450). Do not claim envelope/grant/`product_session` types are absent at `34c148b`. Do not claim `caller_kind`, optional authoring instance, or daemon JSON-lines exist as wired product surface at `34c148b`.

## Consequences

Easier: factory units can connect optional copilot, home instance pick, `caller_kind`, daemon diagnosis logs, default none/read retry, and nested Mission invoke without minting a sixth package or a new contract id.

Harder: every pack inherits diagnosis; authoring home chat must pick exactly one instance before invoke; retry must not loosen parent effect classes; nested workflow must not splice live graphs.

Foreclosed: a sixth COMP; a third profile; merged live Task Graphs; pinning json-render/MCP Apps; filling GAP-0081 chrome or GAP-0100 dashboard in this sitting; claiming kit field changes exist at `34c148b`.

Public types in this increment (`caller_kind`, `failure_class`, optional authoring `app_instance_id`, `selected_refs` kind `instance_id`, `copilot_profile`) are specified in prose and CT **usage annotations**; they are not new `schema.fields` and they are not a new CT number (DEC-0462). Factory implementation lands those fields as CT-40 / owner-contract format mints under FEAT-0058..FEAT-0063. GAP-0101..GAP-0108 are **answered sitting law** (DEC-0468), not open design questions. GAP-0081 and GAP-0100 are out-of-scope as kit holes.

Blast radius (change mode): `COMP-QMA-CORE`, `COMP-QMA-WIRE`, `COMP-QMA-DAEMON`, and every doc declaring a dependency on them, plus dated annotations on QMB/QML/QMN (host ≠ owner of every op). Primary edits: this ADR; SCN-0023..SCN-0027; constitution L7 annotation; component specs for COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON; CT-40 annotation; overview, stack, dependencies (notes only); glossary; gap-report; traceability; index; AGENTS.md; changelog; dated follow-up on ADR-0024; observability logging-spec QMA row; and `_docwork/` (ledger DEC-0452..DEC-0468, gaps GAP-0101..GAP-0108 answered, features FEAT-0058..FEAT-0063, SRC-24/SRC-25/SRC-26). Implementation authorization remains factory-pipeline-only (DEC-0461).

Cheap-veto (DEC-0467) — operator may overturn in one line; default if no veto is proceed:

| Id | Item | Default if no veto |
|---|---|---|
| A7 | Diagnosis `failure_class` closed set `grant \| workflow \| view \| dependency \| host` | proceed |
| A8 | Daemon JSON-lines extra fields when present | proceed |
| A9 | Host retry attempt ceiling is a registry row; this sitting mints no number | proceed |

Not vetoable here: no sixth COMP; no new CT; no third profile; envelope `instance_id` required on invoke; nested live-graph merge refused; app-use cannot apply; no blind `external-egress` retry; logs ≠ journals; json-render/MCP unpinned. UI screens are a later sitting; GAP-0081 and GAP-0100 are out-of-scope as kit holes (DEC-0468).

## Follow-up 2026-09-25

The 2026-09-25 UI host plus backend-delta fold ([ADR-0026](ADR-0026-ui-host-and-backend-delta.md), DEC-0509) **answers** GAP-0081 chrome and GAP-0100 observation surfaces as UI sitting law. This ADR's Decision is unchanged: those rows remain out-of-scope **as kit holes**. Delivery is FEAT-0064..FEAT-0071. Do not treat this follow-up as a kit rewrite.
