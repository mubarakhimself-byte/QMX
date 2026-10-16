---
title: Lab OPEN-5: enabling Lab-scoped schedules
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
---

## Question

One standing Lab allow rule switched on once in Settings, or MANAGE per schedule?

## Recommended answer

One standing Lab allow rule he switches on once; a schedule whose outputs leave the Lab still asks. Note: the 'bounded by the engine's budgets' wording must lose any spend cap (ruling 27).

## Sources

`architecture/lab-and-pods/`OPEN-DECISIONS.md OPEN-5; Lab AD-13; rulings 57, 77.

## Resolution

Resolved by ruling 80 with engine AD-22: a Lab schedule is a workflow; he says yes once at publish/enable, then it runs without asking; no standing Lab allow rule; runaway guard instead of budgets (Lab AD-13, 27c fix 15).
