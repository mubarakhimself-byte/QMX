# Backend work exposed by the UI — scope for a follow-up architecture pass

2026-09-24. Review advice, not an approved architecture or generated backlog. The user asked whether a separate BMAD architecture session is viable while existing epics continue. **Yes, with explicit contract dependencies.** No new task, architecture run or factory job was started here.

## What is already represented

| Area | Existing planning anchor | Follow-up treatment |
| --- | --- | --- |
| Optional copilot profile; authoring session without an instance until invocation; `selected_refs.instance_id`; `caller_kind` | Pack-and-Grant FEAT-0058 / **Epic 60** | Existing planned work. Reconcile the new UI DTO against that schema; do not create duplicate epics |
| Daemon JSON-lines and failure classification | FEAT-0059 / **Epic 61** | Existing planned work; UI consumes the results |
| Effect-aware host retry | FEAT-0060 / **Epic 62** | Existing planned work; preserve its authority and external-effect restrictions |
| Nested workflow/Mission lifecycle | FEAT-0061 / **Epic 63** | Existing planned work; reconcile UI cancel and graph examples with its owner |
| Headless listing and instance health | FEAT-0062 / **Epic 64** | Existing planned work. Correct CHANGE-IMPACT's `FEAT-0059-class` health attribution |
| Thin adoption proofs for the kit | FEAT-0063 / **Epic 65** | Existing planned proof work, not automatically UI/browser/installer acceptance |
| Wire protocol/authentication/idempotency and daemon persistence | QMA **Epics 41–42**, with reachability/proxy work in Epic 44 and downstream runtime work | Inspect implementation/adoption against the existing acceptance obligations before declaring a new feature. The UI candidate explicitly reports a types/fixtures versus live-serving gap at its pinned inspect revision |

Primary anchors: `../../_bmad-output/planning-artifacts/epics-PACK-AND-GRANT-2026-09-23.md` (overview :61–179, epic list :228 onward); `../../_bmad-output/planning-artifacts/epics-QMA-2026-08-29.md` (Epic 41 :614 onward, Epic 42 :806 onward, Epic 44 :1251 onward). Those documents are planning evidence. This review does not claim every listed story is currently executing, delivered or accepted.

## UI-driven additions or amendments to resolve

| Contract group | Named owner/direction in the candidate | Architecture question still required |
| --- | --- | --- |
| Browser bootstrap and pairing | COMP-QMB `qmb host start/status/stop/pair`; daemon authentication; COMP-QMA-WIRE boundary | One implementable browser proof, static-origin/remote topology and authenticated transition. Existing generic auth law does not supply the browser implementation |
| Product conversation history | Reuse daemon mailbox; add CT-40 `list_mailbox` and session-indexed projection | Persisted routing source and reply inheritance; query by a pre-ack identity; retention/rebuild/admission rules |
| Cancel command | CT-40 `cancel_job` into existing JobHandle owner | Starter versus observer authority; stored admission binding; state races, retries and nested runs |
| Attachment staging | Daemon `stage_artifact` and existing artifact registration | Initial possession versus execution placement; byte transport and bounds; partial cleanup/resume/refusal |
| UI request and action context | Versioned PackUiRequest consumed by host | Compatibility with Epic 60 manifest; nav/view relation; grant selection; native/json-render/MCP parity |
| Saved authoring work and first Run | Daemon-owned draft/revision; plugin enable; existing template/instance/job identities | Storage/update contract, concurrent saves, first local registration, later distributable export, validation and rollback |
| Provider setup and installed-product operation | Existing credential broker plus proposed host setup/native layer | Separate selected v1 requirements from later Tauri packaging; identify any OS-store write/setup APIs and clean-machine obligations |

The new names above did not appear in the inspected canonical `epics*.md` files by exact-name search (`list_mailbox`, `stage_artifact`, `cancel_job`, `qmb host`, `pairing_session_id`). This is a scoping lead, not proof that all equivalent behavior is absent. The follow-up must check semantic overlap and current code before assigning new work.

## How parallel work stays coherent

1. Pin the then-current integration baseline and inventory the factory's actual selected/pending stories. This review did not inspect or control its live queue.
2. Map each new requirement to **reuse / already planned / implementation-adoption gap / new amendment**, with the owning COMP, source contract and affected epic/story where one exists. Do not mint feature ids just from this review.
3. Mark conflicting contracts explicitly. Immediate example: UI nesting/forbidding `copilot_profile` versus Epic 60's existing manifest field. Reconcile before a dependent implementation assumes a schema. A separate UI branch does not isolate a shared wire or manifest change.
4. Keep independent epics moving. Hold or resequence only dependent work whose contract is unsettled. The appropriate unit is the dependency, not all backend work and not an arbitrary Saturday deadline.
5. Return a contract/amendment and dependency map for review. Then use the user's existing Documentation Factory → epics/stories → coding workflow for the accepted delta. Merge backend and UI into a tested deployment candidate according to the established process.

## Portable input set

- Current closure report and preserved amended candidate: this directory.
- Candidate START-HERE, spine, companions, CHANGE-IMPACT, TRACE-MATRIX and CLOSURE-MAP.
- Parent QMX architectures `architecture-QMX-2026-09-18` and `architecture-QMX-2026-09-23`, plus the QMA parent contracts relevant to wire/runtime ownership.
- Existing Pack-and-Grant/QMA epics and current feature inventory: reconcile, do not regenerate by default.
- `../qmx-ui-architecture-handoff-2026-09-23/` for session, original storyboard images/dictation and source provenance. Preserve visual/headless/mixed capabilities, separate conversations, original layout families and graph/code ML work.

Copying/extracting this bounded context is feasible; it should supplement the current architecture, not create a competing backend design. UI details that do not affect these contracts can continue to be refined. A fully styled UI is not a prerequisite for this backend pass.
