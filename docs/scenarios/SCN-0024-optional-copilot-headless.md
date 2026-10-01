---
id: SCN-0024
title: Headless pack with no copilot; optional in-app panel cannot apply
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-DAEMON, COMP-QMA-WIRE, COMP-QMA-CORE]
decisions: [DEC-0452, DEC-0454, DEC-0442, DEC-0465]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/COPILOT-AND-APPS.md, _docwork/pack-and-grant-increment-brief.md, _docwork/riders/pack-and-grant-kit-2026-09-23.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-09-23
verified: 2026-09-23
stale_after: 90d
---

# SCN-0024: Headless pack with no copilot; optional in-app panel cannot apply

This scenario pins J-KIT-01 and J-KIT-02: a pack may ship operations with no views and no `copilot_profile`. Main authoring can still invoke via CLI/wire. An instance may omit an in-app panel. When a panel exists, app-use may inspect, invoke granted ops, and mint `change_request`; it must not apply. Closing a future UI tab does not cancel running work. [DEC-0452] [DEC-0454]

This document is a **specification of intended behavior**, not evidence that the code does this today. At `integration@34c148b`, pack `copilot_profile` is absent. [DEC-0465]

## Given

A pack declares operations and requested capabilities. It omits `view:*` and omits `copilot_profile`. Installing and enabling still do not grant. A session GrantRecord is granting. Headless packs appear as reusable parent-AD-3 steps with no navigation. Optional in-app panel, when present, is a contract surface over an app-use `psess:`, not GAP-0081 chrome and not a second copilot product. [DEC-0452] [DEC-0454]

## When

1. The operator enables the headless pack and the main authoring session invokes an op via CLI/wire.
2. Separately, an app-use session on instance A has an optional panel; the panel asks why the last run failed; the operator (or panel) mints a `change_request`.
3. A future UI tab or panel is closed while work is running.

## Then

**(1) Headless invoke works.** The run produces a JobHandle. No in-app panel exists. Main authoring can still reference the pack. [DEC-0452] [DEC-0454]

**(2) Optional panel cannot apply.** Host returns diagnosis (`failure_class` plus JobHandle when FEAT-0059 lands) (DEC-0456). Panel cannot edit the pack. App-use mints `change_request`; authoring plus operator principal applies; v1 instance stays until apply. [DEC-0454] [DEC-0442] [DEC-0456]

**(3) Panel dispose does not cancel work.** Running work is not cancelled by panel dispose (parent AD-17). Reconnect resumes queries/events; it does not replay unacked intent. [DEC-0454]

**(4) Install is not grant.** Absence of `copilot_profile` is valid. `copilot_profile` is a request blob, not a contribution point and not a grant. [DEC-0452]

## Failure branches

**Branch A — requiring a copilot to ship.** Enable refuses a pack with no `copilot_profile`. Forbidden. [DEC-0452] [DEC-0454]

**Branch B — panel applies the change-request.** App-use applies v2. Forbidden. [DEC-0454] [DEC-0442]

**Branch C — tab close kills the Mission.** Dispose of chrome cancels the JobHandle. Forbidden. [DEC-0454]

**Branch D — claiming copilot_profile exists at 34c148b.** Treating this scenario as executed proof on the inspect SHA. Forbidden. [DEC-0465]

## Worked numbers

None. This is a registry-independent pack-and-session scenario. The load-bearing chain is omit-copilot-profile is valid → install≠grant → app-use mints and must not apply (DEC-0452, DEC-0454, DEC-0442).
