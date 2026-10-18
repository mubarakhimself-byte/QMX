---
title: Engine OPEN-2: is a provider-hosted harness acceptable?
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
---

## Question

May a provider's harness (Cloudroom, Amp threads) hold the loop, transcript and run pass inside its VM as a compute-only leaf node attempt (`host_harness`, engine AD-25, AD-30)?

## Recommended answer

Yes, as a leaf node attempt with key accounts only, never owning schedules or state; refuse it if he wants every transcript on his own machines.

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 2; engine AD-25, AD-30; ruling 69 (Rivet principle in view).

## Resolution (2026-10-18 evening, re-centralize)

Closed by the rerun (engine OPEN-DECISIONS "Closed by the rerun", old 2; `../../research/methodology/39-architecture-rerun.md` §5.3 C M-11): allowed as a leaf attempt with key accounts; he removes a provider from `runs_on` if he wants every transcript on his machines.
