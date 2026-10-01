---
id: SCN-0023
title: Home authoring invoke requires exactly one selected instance_id
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-DAEMON, COMP-QMA-WIRE, COMP-QMA-CORE]
decisions: [DEC-0454, DEC-0463, DEC-0464, DEC-0465]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md, _docwork/pack-and-grant-increment-brief.md, _docwork/riders/pack-and-grant-kit-2026-09-23.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-09-23
verified: 2026-09-23
stale_after: 90d
---

# SCN-0023: Home authoring invoke requires exactly one selected instance_id

This scenario pins J-KIT-03: the main/home copilot is `ProductSessionProfile=authoring` with `app_instance_id` absent until an invoke. Invoke is legal only when exactly one `selected_refs` kind `instance_id` is present; envelope `instance_id` is still required. Zero or many such refs is `INVALID_INPUT`. Nested call does not widen tools. [DEC-0454] [DEC-0463]

This document is a **specification of intended behavior**, not evidence that the code does this today. At `integration@34c148b`, `ProductSession.app_instance_id` is a required string and `SELECTED_REF_KINDS` lacks `instance_id`. [DEC-0465]

## Given

A product_session exists with `profile=authoring` and `app_instance_id` absent (nothing selected). App-use sessions still require an instance. Closed `selected_refs` kinds include `instance_id` in addition to parent AD-8 kinds. Envelope `instance_id` remains required on every invoke. `caller_kind` is `user | agent | workflow`. [DEC-0463] [DEC-0464]

## When

1. The operator talks to the main copilot with no instance on the session row (no invoke).
2. The operator selects exactly one `instance_id` in `selected_refs` and invokes an operation.
3. Separately, invoke is attempted with zero `instance_id` refs, or with two.

## Then

**(1) Chat without invoke is legal.** Authoring with absent `app_instance_id` is the home/main seat. No third `ProductSessionProfile` is minted. [DEC-0454] [DEC-0463]

**(2) Exactly-one instance on invoke.** Envelope `instance_id` is taken from that single `selected_refs` kind `instance_id`. The callee GrantRecords of that instance bind. Nested invoke does not union grants. [DEC-0454] [DEC-0463]

**(3) Zero or many instance refs refuse.** Typed `INVALID_INPUT` (ambiguous instance). The host does not guess latest, first, or all. [DEC-0463]

**(4) App-use still requires instance.** A session with `profile=app-use` cannot omit `app_instance_id`. [DEC-0463]

## Failure branches

**Branch A — third profile.** Home is modelled as a new `ProductSessionProfile`. Forbidden. [DEC-0463]

**Branch B — silent latest instance.** Authoring invoke with no `instance_id` ref resolves to a latest alias. Forbidden. [DEC-0463]

**Branch C — envelope instance_id optional.** Invoke proceeds without envelope `instance_id`. Forbidden; envelope `instance_id` remains required. [DEC-0464]

**Branch D — claiming optional authoring instance is wired at 34c148b.** Treating this scenario as executed proof on the inspect SHA. Forbidden. [DEC-0465]

## Worked numbers

None. This is a registry-independent session-identity scenario. The load-bearing chain is authoring-with-absent-instance → exactly one `selected_refs` kind `instance_id` → envelope `instance_id` required (DEC-0463, DEC-0464).
