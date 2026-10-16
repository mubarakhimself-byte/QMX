---
title: Unit read adapter and account-guard reader (C7)
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. The unit.tighten write and direction table are node depth (ruling 14, removed by 21); keep only read-only facts."
closed: 2026-10-16
---

## Question

Specify the read-only adapter through which every template reads a unit by named facts (never fields), returning `unknown` for facts the unit lacks; the single write `unit.tighten(action)` with its action list and the direction table; and the read-only account and guard reader.

## Why it matters

Central piece C7 in `19`. The unit's parts are still open with the risk session (`09`), so templates must stay loose. This adapter is what lets T1-T10, RK1-RK8 and P1-P4 be designed now and survive whatever the unit becomes. The account guard sits outside the unit by agreement and agents are locked out of it.

## What the session does

AFK task. Write the fact list with types and `unknown` semantics, the `tighten` action list, the direction table format (per parameter, which way is tighter), the guard reader's fields (equity, positions, stops, guard state, config hash, prop-firm rule table) and the rule that it has no write path. Map each fact to what exists today in `qmx-broker`, QMN and the QMB ledger, and mark the rest `unknown` until the risk session rules. Hand back the interface.

## Unblocks

Wave 2 pilot templates (P2, T1, RK1, T5, T9), the Portfolio watcher, the trader-agent methodology.

## Sources

`16-templates-trader-risk.md` §4.1, §4.2, §4.6; `09-self-configuring-unit.md` §2, §3; `05-qmx-today.md` §5; `19` C7.

## Resolution

Resolved. Lab AD-11: a pod reaches trading only through `PodCompilerPort` and `NodePort`. Unit internals belong to the risk session (ruling 14). (Map rewrite 2026-10-16.)
