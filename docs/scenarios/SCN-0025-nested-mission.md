---
id: SCN-0025
title: Workflow-to-workflow is one nested Mission, not a live Task Graph merge
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0455, DEC-0464, DEC-0465]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md, _docwork/pack-and-grant-increment-brief.md, _docwork/riders/pack-and-grant-kit-2026-09-23.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-09-23
verified: 2026-09-23
stale_after: 90d
---

# SCN-0025: Workflow-to-workflow is one nested Mission, not a live Task Graph merge

This scenario pins J-KIT-04 and J-KIT-05: a widget may bind to `start` of template T (it does not own invoke). A Graph Template node may start another template as a nested Mission. The callee has its own JobHandle. Crash of the parent does not splice the child's Task Graph into the parent. Recursion budget is envelope `call_depth` against the host-registered ceiling; this sitting mints no number. [DEC-0455]

This document is a **specification of intended behavior**, not evidence that the code does this today. Nested Mission invoke as a first-class verb is absent at `integration@34c148b`. [DEC-0465]

## Given

Template A is a registered Graph Template `(qualified_id, version)`. Template B is another registered version. Parent AD-10 four modes remain: consume artifact, invoke op, Graph Template coordinate, composite instance graph. `caller_kind` is `user | agent | workflow`. Widgets bind or display ops; they do not add a fifth composition mode. [DEC-0455] [DEC-0464]

## When

1. A user or agent presses a widget bound to `start` of template T (`caller_kind=user` or `agent`).
2. Template A has a node that starts template B as a nested Mission (`caller_kind=workflow`).
3. Separately, authoring includes B's subgraph into a new version of A.
4. A live merge of A's and B's Task Graphs is attempted.

## Then

**(1) Widget starts a workflow.** Envelope carries `caller_kind` and required `instance_id`. Widget dispose does not cancel the Mission. [DEC-0455]

**(2) Nested Mission.** Callee identity is Graph Template `(qualified_id, version)`. Lifecycle verbs: `start | query-state | cancel | await`. Result is a JobHandle. Occupancy and cancel follow that JobHandle. Nested invoke does not union grants. [DEC-0455]

**(3) Include-at-author.** Authoring may compose by including a subgraph into a **new versioned** Graph Template. That is not a runtime merge. [DEC-0455]

**(4) Live merge refused.** Merging two live Task Graphs is `INVALID_INPUT` (or the typed refusal the owner COMP already uses for illegal topology). Partial failure does not silently substitute another instance, version, or account. Exceeding host-registered `call_depth` ceiling is `INVALID_INPUT`. [DEC-0455]

## Failure branches

**Branch A — splice live graphs.** Crash of A copies B's nodes into A's Task Graph. Forbidden. [DEC-0455]

**Branch B — widget owns invoke.** A widget contribution point executes without an envelope. Forbidden. [DEC-0455]

**Branch C — union nested grants.** Nested invoke widens the caller's tools with the callee's. Forbidden. [DEC-0455]

**Branch D — claiming nested Mission invoke is wired at 34c148b.** Treating this scenario as executed proof on the inspect SHA. Forbidden. [DEC-0465]

## Worked numbers

None. This is a registry-independent composition scenario. The load-bearing chain is widget-binds-op → nested Mission one JobHandle → include-at-author is a new version → live merge refused (DEC-0455).
