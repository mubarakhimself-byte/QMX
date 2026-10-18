---
title: Waves 2-4 packet plans
type: task
mode: HITL
status: closed
blocked_by: [wave1-packets, first-templates]
claimed_by: ""
created: 2026-10-16
rubric: "SUPERSEDED. Waves dropped and no build order yet (ruling 33)."
closed: 2026-10-16
---

## Question

Turn the ratified methodology into numbered packets an orchestrator session can dispatch one builder at a time, the way HP3-HP17 shipped, with one build and one check per PR.

## Why it matters

The destination is a methodology plus a sequenced build plan. The operator's shipping model is fixed: an orchestrator session coordinates and never writes code, one pstack builder per packet, light verification per PR, merges into `rebuild/base`, main only by his click.

## What the session does

Read every closed ticket. Write `METHODOLOGY-PLAN.md` beside `HARNESS-PLAN.md` with the same checklist shape: packets for the engine runtime, homes, autonomy table, skill validator, role table, triggers and scheduler, pause at cap, the five templates, roster and modes, memory scopes, Lab tools, trace view, then the H2 packets. Each packet names its depends-on, its one check, and its fake-model lane. Run `check-plan.mjs` if it still applies. He signs off.

## Unblocks

The destination.

## Sources

`README.md` (how the harness plan was made); `HARNESS-PLAN.md` checklist shape; memory `light-verification-per-pr`, `builders-sequential`; `07-central-pieces.md` §6 build waves.

## Resolution

Superseded. Waves dropped (ruling 33). The build plan is `ENGINE-PLAN.md` (ruling 84). (Map rewrite 2026-10-16.)
