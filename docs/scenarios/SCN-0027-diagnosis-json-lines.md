---
id: SCN-0027
title: Host diagnosis failure_class plus daemon JSON-lines; logs are not evidence
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
decisions: [DEC-0456, DEC-0458, DEC-0465, DEC-0467]
sources: [_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/CONTRACTS.md, _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md, _docwork/pack-and-grant-increment-brief.md, _docwork/riders/pack-and-grant-kit-2026-09-23.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-09-23
verified: 2026-09-23
stale_after: 90d
---

# SCN-0027: Host diagnosis failure_class plus daemon JSON-lines; logs are not evidence

This scenario pins kit AD-5 and J-KIT-07: every public run is diagnosable headless. Copilot (or CLI) distinguishes grant vs workflow vs view vs dependency vs host. `qma-daemon` emits stdlib JSON-lines. Logs are not journals and not a fourth observability product. A weaker model fills descriptor schemas; prose cannot add an op. [DEC-0456] [DEC-0458]

This document is a **specification of intended behavior**, not evidence that the code does this today. Daemon JSON-lines operator logger and kit `failure_class` are absent at `integration@34c148b`. [DEC-0465]

## Given

The host exposes, headless: parent AD-15 listing axes including `healthy`; instance `health()` as the existing component typed-report (DEC-0112), distinct from pack `published`; JobHandle in QMA AD-17 vocabulary; typed refusal; `correlation_id` join (never fp1); harness-authored QMA telemetry (agents must not write it; OTel remains export-port only). Failure class is closed: `grant | workflow | view | dependency | host`. `view` means the wire DTO failed to mount, was stale, or was unhealthy — it is not an invoke. [DEC-0456] [DEC-0467]

## When

1. A public operation or Task Graph run fails.
2. Copilot or CLI queries diagnosis.
3. The daemon emits an operator log line for that run.
4. A weaker/older model authors a pack by filling descriptor schemas; host validate is missing a dependency.

## Then

**(1) Diagnosis query.** Headless result includes `failure_class`, `job_handle` (or null), `correlation_id`, and `healthy`. How-it-failed is the log line plus JobHandle `attempt_id` plus typed refusal. No fourth store. [DEC-0456]

**(2) JSON-lines.** Stdlib logging. Required fields: `ts`, `level`, `event`, `correlation_id`. When known: `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Never secret values. Never a journal. [DEC-0456]

**(3) QMN allow-list stays QMN.** Mini-app typed failures, when first ids ship, live in that owning package's FAILURES.md — never on the QMN alert allow-list. [DEC-0456]

**(4) Weak model fail-closed.** Host validate fails closed on missing dep. Model prose cannot add an op. Skills describe; they do not grant. [DEC-0458]

## Failure branches

**Branch A — fourth observability product.** A new COMP or store is minted for mini-app logs. Forbidden. [DEC-0456]

**Branch B — logs as evidence.** Operator log lines enter `fp1` identity or replace journals. Forbidden. [DEC-0456]

**Branch C — QMN allow-list reuse.** Mini-app failures are added to `qmn/FAILURES.md`. Forbidden. [DEC-0456]

**Branch D — agents write telemetry.** A model-authored hook emits QMA telemetry. Forbidden. [DEC-0456]

**Branch E — claiming daemon JSON-lines exist at 34c148b.** Treating this scenario as executed proof on the inspect SHA. Forbidden. [DEC-0465]

## Worked numbers

None. This is a registry-independent diagnosis scenario. The load-bearing chain is closed `failure_class` → JSON-lines join on `correlation_id` → logs ≠ journals (DEC-0456).
