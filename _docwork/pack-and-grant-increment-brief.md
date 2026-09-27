# QMX pack-and-grant kit — documentation-factory Stage 9 brief (2026-09-23)

Route e, change mode, Stage 9. Do not restart Stages 1–8. Do not implement code, UI, n8n, Hermes, or OpenBB. Do not rewrite the 2026-09-16 QML fold or the 2026-09-19 Workflows fold. Do **not** emit a BMAD epics-and-stories prompt.

Planning checkout: `main` @ `92279dfe43922d60fabe38e29284ca52956ab75c`. Implementation inspect: `integration@34c148b` via worktree `C:\Users\Mubarak\Desktop\QMX\.worktrees\integration-inspect` (HEAD matches). Parent freeze for ADR-0024 original Decision: `270e992`. Do not switch branches.

## Authority

1. **Operator rider (ratified this session):** `_docwork/riders/pack-and-grant-kit-2026-09-23.md`.
2. **Architecture package (folded):** `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/` — citation surface is `ARCHITECTURE-SPINE.md` (local AD-1..AD-9), `REQUIREMENTS-ADDENDUM.md`, `CONTRACTS.md`, `JOURNEYS.md`, `COPILOT-AND-APPS.md`, `IMPLEMENTATION-SEQUENCE.md`, `.memlog.md`, `reviews/gate-summary.md`, `research/SDK-HYBRID-AND-CORE.md`.
3. **Parent (do not reopen as a new kit):** ADR-0024 / DEC-0414..DEC-0451. Named amendments only of parent AD-8 and parent AD-24.
4. **Operator words this sitting:** pack-and-grant is the core; one copilot, many sessions, in-app panel optional; home = authoring with nothing selected; retry in the host; composition via operations; JSON Render / MCP Apps paint; UI later. Operator accepted the sitting as the plan to fold.

**Do not fold as current law:** spine YAML `status: draft` / `not operator-accepted` leftover in the sitting folder (operator launch + this rider win); donor research as product pins; json-render v0.21.0 as a required runtime.

## Standing of claims

| Set | Stamp |
|---|---|
| Rider standing corrections | ratified (`authority: rider`) |
| kit AD-1..AD-9 | ratified |
| Named parent AD-8 / AD-24 amendments | ratified (do not whole-supersede DEC-0421 / DEC-0437) |
| ADR-0025 + SCN-0023..0027 | ratified (docs authority only; not implementation) |
| ADR-0024 original Decision | unchanged; dated follow-up only |
| ADR-0023 mill package | stays **provisional** |
| New normative sentences on already-ratified parent docs | cite new DECs; dated follow-up or annotation |

`verified: 2026-09-23` on every doc you touch.

## ID block

| Kind | Range | Use |
|---|---|---|
| SRC | SRC-24, SRC-25 | architecture-QMX-2026-09-23 folder; this rider |
| EXT | EXT-2286..EXT-2302 | rider + local ADs + umbrella + preflight + amendments + honesty + dead-list + cheap-veto |
| DEC | DEC-0452..DEC-0460 = kit AD-1..AD-9; DEC-0461 umbrella; DEC-0462 preflight; DEC-0463 parent AD-8 amendment; DEC-0464 parent AD-24 amendment; DEC-0465 wiring @ 34c148b; DEC-0466 dead-list; DEC-0467 cheap-veto A7–A9 |
| GAP | GAP-0101..GAP-0108 new; notes on GAP-0081/0100/0093/0096 in place |
| FEAT | FEAT-0058..FEAT-0063 |
| ADR | ADR-0025 |
| SCN | SCN-0023..SCN-0027 |
| CT | **no new id** | additive CT-40 family annotations |
| COMP | **none** | **no sixth application** |

DEC-0421 and DEC-0437 stay live; DEC-0463/DEC-0464 are named amendments.

## Preflight verdict (record in ADR-0025)

**reuse** existing applications. **new COMP: none. new CT: none.**

| Work | Owner | Class |
|---|---|---|
| Pack SDK (optional `copilot_profile`, request≠grant) | COMP-QMA-CORE + COMP-QMA-DAEMON plugin lifecycle | extend parent AD-18/AD-30 |
| Authoring `app_instance_id` optional; `selected_refs` kind `instance_id` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named amend DEC-0421 |
| Envelope `caller_kind` `user\|agent\|workflow` | COMP-QMA-CORE + COMP-QMA-WIRE | named amend DEC-0437 |
| Daemon JSON-lines + diagnosis query | COMP-QMA-DAEMON + COMP-QMA-WIRE | connect; QMA telemetry store stays |
| Default host retry none/read | COMP-QMA-CORE effects + COMP-QMA-DAEMON | extend parent AD-24 matrix |
| Nested Mission invoke | COMP-QMA-DAEMON | extend parent AD-7/AD-10 |
| Listing axes + instance `health()` | COMP-QMA-DAEMON + COMP-QMA-WIRE | extend parent AD-15 |
| Views / MCP Apps / json-render | COMP-QMA-WIRE DTOs | parent AD-17; unpinned |

Candidates refused: COMP-WF / sixth COMP; new CT-*; third ProductSessionProfile; merged live Task Graphs; json-render/MCP as identity; QMB/QML core fork; fourth observability product; extending `qmn/FAILURES.md`; HMR/hot-apply; app-use applying `change_request`.

No existing component's authority shrinks. No new `depends_on` edge. No new contract id.

## Cheap-veto (DEC-0467) — operator may overturn in one line

| Id | Item | Default if no veto |
|---|---|---|
| A7 | Diagnosis `failure_class` closed set `grant \| workflow \| view \| dependency \| host` | proceed — class is sitting law; spellings are machinery |
| A8 | Daemon JSON-lines extra fields when present (`instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`) | proceed — required fields `ts`, `level`, `event`, `correlation_id` are operator-direct |
| A9 | Host retry attempt ceiling is a registry row; this sitting mints no number | proceed |

Not vetoable here: no sixth COMP; no new CT; no third profile; envelope `instance_id` required on invoke; nested live-graph merge refused; app-use cannot apply; no blind `external-egress` retry; logs ≠ journals; json-render/MCP unpinned; GAP-0081 chrome later.

## Feature slices (implementation still factory-pipeline-only)

| FEAT | Name | Primary DECs | Blocked by |
|---|---|---|---|
| FEAT-0058 | Host SDK pack-and-grant (optional copilot_profile; authoring instance optional; caller_kind) | DEC-0452, 0453, 0454, 0463, 0464 | FEAT-0052, FEAT-0053 |
| FEAT-0059 | Daemon JSON-lines + diagnosis query | DEC-0456, 0465 | FEAT-0058, FEAT-0042 |
| FEAT-0060 | Default host retry none/read | DEC-0457, 0464 | FEAT-0058, FEAT-0052 |
| FEAT-0061 | Nested Mission invoke (workflow-to-workflow) | DEC-0455 | FEAT-0055, FEAT-0058 |
| FEAT-0062 | Listing axes + instance health() | DEC-0456, 0428 | FEAT-0058, FEAT-0051 |
| FEAT-0063 | Thin fixtures for kit journeys J-KIT-01..07 | DEC-0452..0460, 0465 | FEAT-0058..0062, FEAT-0056 |

First epic after this fold = FEAT-0058. Do not launch it from this sitting.

## Gaps (answered sitting law — DEC-0468)

These are the work to build (FEAT-0058..FEAT-0063). They are not open design questions.

| GAP | Question | Status |
|---|---|---|
| GAP-0101 | Closed `caller_kind` `user\|agent\|workflow` | answered; delivery FEAT-0058 |
| GAP-0102 | Authoring may omit `app_instance_id`; `selected_refs` kind `instance_id` | answered; delivery FEAT-0058 |
| GAP-0103 | Pack may omit `copilot_profile` | answered; delivery FEAT-0058 |
| GAP-0104 | `qma-daemon` JSON-lines operator logs | answered; delivery FEAT-0059 |
| GAP-0105 | Diagnosis `failure_class` + instance `health()` | answered; delivery FEAT-0059, FEAT-0062 |
| GAP-0106 | Default host retry `none`/`read` | answered; delivery FEAT-0060 |
| GAP-0107 | Nested Mission invoke | answered; delivery FEAT-0061 |
| GAP-0108 | Retry ceiling is a registry row; sitting minted no number | answered as design; FEAT-0060 must not invent a cap |

GAP-0081 and GAP-0100 are out-of-scope as kit holes (UI is not designed). GAP-0093/GAP-0096 stay for a later operator look.

## Honesty at 34c148b (DEC-0465)

**CONNECT (types/fixtures exist; not e2e):** InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, effect-class + `reconcile_policy`, `call_depth` / `parent_logical_invocation_id`, Workflows 53–59 fixtures.

**AMEND:** `ProductSession.app_instance_id` is required `str`; `SELECTED_REF_KINDS` lacks `instance_id`; envelope has no `caller_kind`.

**ABSENT:** `copilot_profile`; daemon JSON-lines operator logger; kit `failure_class`; default host retry loop; nested Mission invoke as first-class; CheckpointManifest.

## Drafting rules

- Cite new DECs on every new normative sentence. Self-contained sections. No hedges. No TODO without a GAP id.
- Product nouns: pack / mini-app / widget / workflow; one copilot; panel optional; SDK = pack-and-grant host contract.
- Banned: sixth COMP; third profile; merged live Task Graphs; pinning json-render/MCP; claiming daemon JSON-lines / `caller_kind` / optional authoring instance exist at `34c148b`; claiming envelope/grant/`product_session` types are absent at `34c148b`; rewriting ADR-0024 Decision. UI screens are a later sitting (GAP-0081 / GAP-0100 out-of-scope as kit holes, DEC-0468).
- Wiring honesty: inherit DEC-0286. Parent freeze `270e992` for ADR-0024 original text. Current inspect `34c148b`.

## Docs to touch

**New:** `docs/decisions/ADR-0025-pack-and-grant-kit.md`; `docs/scenarios/SCN-0023-home-instance-pick.md`; `SCN-0024-optional-copilot-headless.md`; `SCN-0025-nested-mission.md`; `SCN-0026-host-retry.md`; `SCN-0027-diagnosis-json-lines.md`.

**Update:** constitution L7 annotation; AGENTS.md; qma-core, qma-daemon, qma-wire; overview, stack, dependencies (notes only); glossary; gap-report; traceability; index; changelog; ADR-0024 **dated follow-up only**; ADR-0020 dated follow-up; CT-40 annotation; observability logging-spec QMA daemon row; GAP-0081/0100/0093/0096 notes.

## What not to do

- Do not mint COMP-WF, CT-52, or a sixth store.
- Do not fill GAP-0085 / 0063 / 0061 / 0062 / 0058 / 0081 chrome / 0100 dashboard.
- Do not rewrite ADR-0020/0023/0024 original Decision sections.
- Do not claim implementation.
- Do not start epics.
