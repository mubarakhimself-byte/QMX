# Backend combined candidate work ledger

Owner: controlled backend integrator. Date: 2026-10-04. Status: composition in progress; platform acceptance false.

Candidate: `backend-candidate`, branch `backend/combined-integration-20261004`. Independent local clone; no shared git directory or hardlinks. No push, merge, publish, deployment, credentials, paid calls or real trading authorized. UI stays Claude-owned.

## Source and ownership

| Requirement/source | Module owner | Status/evidence | Dependencies and next bounded work |
|---|---|---|---|
| Delegated combined checkpoint | Integrator | Four exact clean HEADs verified: native `1f3b98f6b6f268e98f0f14edbb918b727069eb9c`; skills `bf3c6b592e89917c17747eb1072203a28241e74a`; data `4122420d685a36499bd30ff15d343d0c97e7a291`; spot `8bee17d4a49985894ed17b4d3eba2348baf1acb9` | Skills direct child of native; data/spot share `ffb7590b`; apply only 3 data and 2 spot commits |
| Shared runtime composition | Integrator exclusively | Own `qma/daemon/process.py`, `request_runtime/provider_config.py`, operator routing, composition and integration tests | Semantic review of startup, cleanup, admission, read/query authority, dependency manifests |
| CI/quality/dead-code scope | Parent quality lane `01a106eb-6a9e-709c-82a5-b69783a08072` | Assigned; no patches received | Review commits only; announce shared-file changes through parent |
| Durable scoped memory | Parent memory lane `01a106ec-31ea-7011-acea-aeb6ab5c706d` | Assigned from `bf3c6b`; shared seams proposal required | New module owned by lane; integrator accepts reviewed patches |
| Reusable core, roles/actors/delegation/workflows | QMA; future lane via parent | Original Oct3 task-3 reconciliation and task-2 brief read; preserve reusable core and specialist hierarchy | Identify clean actor/dispatch seams after composition |
| Memory/context/agent-authored ledger distinct | QMA memory/context/ledger owners | Original reconciliation records distinct contracts, not interchangeable telemetry | Durable backend from memory lane; context/compaction and authored ledger remain separate |
| SDK skills/hooks/native/API providers | QMA runtime | Reviewed `bf3c6b` ancestry; prior 157 focused + 37 bridge, independent 155 recorded in SDK_SKILLS_HOOKS_EVIDENCE.md | New candidate rerun; full native auth unverified, ordinary native tools restricted; DeepSeek policy/key pending |
| Governed data/QMB persistence | QMF-data/QMB | Prior 650 affected/1879 QMA; independent review approved bounded `4122420`; prior broad 14 failures retained | Compose and verify locking/replay/query seams; paired Dukascopy observations and correction folding remain |
| Legitimate CT47 authoring/public projection | QMA/QMB integrator | Task-8 handoff: no fabricated provenance; canonical actor creation/dispatch ingress and projection bridge absent | Inspect dispatched-owner route; compatible host-derived provenance only; document contract decision |
| Multiaccount/node spot risk, FX/crypto | QMN/QMF-venue | Reviewed spot `8bee17d4`: 35 focused + actual CT40 query; full QMN 1070 pass/39 fail/23 skip, baseline 40 failures | Read-only daemon binding; no execution agent tools; spot FX/live venue work remains |
| QMF/QML/QMB/QMN, analytics/API/DevOps | Respective components; integration owner | Backend vision retained; QMA counts do not certify platform | Crossmodule journeys and appropriate component gates after stable composition |
| Operator/API handoff for Claude, docs drafts | Integrator | Pending | Reproducible scripts, pinned evidence, startup/API authority limits; canonical docs remain drafts |
| Canonical backlog | Parent/integrator | Desktop QMX BACKLOG.md read; inherited CI/security gate rules retained | No raising security zeros, no fabricated coverage, no broad deletion; later user scope supersedes historical pauses |

## Verification policy

Focused conflict-seam tests, review, then coherent integration journeys and full appropriate component gates once composition stabilizes. Preserve every failure and skip. Existing lane evidence is historical and is not final combined-candidate proof. Remote endurance, native authenticated provider operation, cold restore/release packaging remain unproven.

## Activity

- Verified identities, clean status and ancestry without modifying originals. Local fetches imported reviewed object identities only.
- Created isolated skills/native candidate. No dependency install or remote call performed.
