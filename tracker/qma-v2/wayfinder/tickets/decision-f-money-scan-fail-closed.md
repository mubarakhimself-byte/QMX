---
title: Decision F: a money scan that fails closed with no allow-list
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-18
---

## Question

Accept the AD-36 scan with 36's conditions: the verb predicate `name_money_act_called` shared with the harness gate in `qma-core`; prose matched only in prompts, node notes, parameter values and proposal actions; the whole template pack passing E36 before it ships. A false positive is fixed by rewording.

## Recommended answer

Yes. If no: a reviewed allow-list of phrases, one more thing a model could try to widen.

## Sources

`../../architecture/workflow-engine/OPEN-DECISIONS.md` F; engine AD-36; 39 R.7, F.4; `40-retriage.md` §3.1 row 2 (SEC-1).
