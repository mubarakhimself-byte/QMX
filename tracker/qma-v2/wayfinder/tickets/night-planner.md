---
title: Night planner (one heavy job per night)
type: task
mode: AFK
status: open
blocked_by: [workflow-engine-contract, decision-1-lab-self-scheduling]
claimed_by: ""
created: 2026-10-16
rubric: "SUPERSEDED. Premise of one Claude Max at 50% per window is overridden (rulings 26-27); the load balancer replaces it."
---

## Question

Specify the script that picks at most one heavy job per night from the queue under the governor's headroom, shows the rest in the job panel, and orders the queue by his priorities.

## Why it matters

One Claude Max, 50% of each window for background work. A, L4 and T4 all want the same nights; without a planner they collide and the cap closes early. Review A finding 14; `21` A13.

## What the session does

AFK task. Write the planner's inputs (queue, headroom reading, `resets_at`, each job's cost tier and last run), its rule (one heavy, then small jobs while headroom lasts), its outputs (the night's plan as a job-panel view and a morning line) and the fake-model test.

## Unblocks

Wave 2 pilots' exit gate (one clean night).

## Sources

`19` C4 and 5.1; `20-review-a` finding 14; `21` A13.
