---
title: Wave 1 packet plan
type: task
mode: HITL
status: open
blocked_by: [decision-1-lab-self-scheduling, decision-3-spend-number, decision-5-checks-bind-agents-only, decision-7-build-order, workflow-engine-contract, plugin-unit-and-loading, session-homes, role-to-model-table, autonomy-policy, folder-format-one-shape, gate-threshold-store, trial-ledger-and-holdout, unit-read-adapter]
claimed_by: ""
created: 2026-10-16
rubric: "SUPERSEDED. Waves dropped (ruling 33) and harness extensions are not allowed (ruling 24)."
---

## Question

Write the wave 1 packets (harness extensions, then the thin engine core inside `qma.serve`, the folder loader, the renderer, the night planner, the inbox) in the `HARNESS-PLAN.md` checklist shape, each one PR with one build and one check, ordered after the prerequisites. This ticket waits on the decisions and the specs only, never on wave 2 or 3 design.

## Why it matters

Review B finding 1: the old build-plan ticket waited on the umbrella, which waited on wave 3 work, so no wave 1 packet could ever be written. Split per `21` B14.

## What the session does

Read the closed decision and spec tickets; write `METHODOLOGY-PLAN-W1.md`; he signs off.

## Unblocks

The orchestrator session's dispatch of wave 1.

## Sources

`19` section 8 wave 1; `20-review-b` finding 1; `21` B14; `HARNESS-PLAN.md`.
