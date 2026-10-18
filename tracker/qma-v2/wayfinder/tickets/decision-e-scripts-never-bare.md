---
title: Decision E: edited and model-written scripts never run bare on the PC
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-18
---

## Question

Only scripts byte-identical to what QMX shipped run on the PC, inside a per-attempt Windows AppContainer; everything else runs in a container. When Docker is off, QMX starts Docker Desktop itself, then spills the attempt to Contabo, and waits only when neither works (engine AD-24).

## Recommended answer

Yes. If no: edited scripts would run on the host inside the AppContainer alone, which trusts it for code nobody reviewed.

## Sources

`../../architecture/workflow-engine/OPEN-DECISIONS.md` E; engine AD-24; 39 R.7, F.4; `40-retriage.md` §3.1 row 3 (SEC-2).
