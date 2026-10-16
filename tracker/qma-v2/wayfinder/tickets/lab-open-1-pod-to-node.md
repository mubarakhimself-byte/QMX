---
title: Lab OPEN-1: how a pod reaches the trading node now
type: grilling
mode: HITL
status: open
blocked_by: [risk-sizing-session-outcome]
claimed_by: ""
created: 2026-10-16
---

## Question

Compile a pod to the default Book (CT-22) + BMS (CT-27) through `PodCompilerPort`, naming unplaceable blocks, or wait for the risk session?

## Recommended answer

Compile to Book + BMS now and list `unsupported_blocks`; only the adapter changes when the risk session settles the unit.

## Sources

`architecture/lab-and-pods/`OPEN-DECISIONS.md OPEN-1; Lab AD-11; ruling 14.
