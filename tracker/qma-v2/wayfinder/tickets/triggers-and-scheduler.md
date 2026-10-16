---
title: Triggers and scheduler
type: grilling
mode: HITL
status: open
blocked_by: [workflow-engine-contract, autonomy-policy]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Matches ruling 25 (Hermes cron); add server and cloud triggers."
---

## Question

What starts a run on its own (cron, event, after another workflow, manual), what rules the scheduler obeys, and how scheduling asks for permission.

## Why it matters

No scheduler or trigger starts a chat today; Background chats are a Python API without a REST route (`05` gap 2). Scheduling is MANAGE and always asks, and no standing allow-rule format exists. Hermes gives the rules that fit a subscription cap: no-agent jobs, a `wakeAgent` precheck, quota hold, one merged catch-up, validation before dispatch, a run cannot create schedules, model pins belong to the operator (`03` §6).

## Recommended answer

Triggers are rows in `control.db` (`triggers`, `trigger_fires`), never nodes. Kinds: `cron`, `event` (control-door topics such as `library`, `runs`, `apps`), `after: <workflow>`, `manual`. Every trigger has a precheck script. The scheduler parks at the cap (`quota_hold_until`), merges missed fires into one, validates credentials and skills before dispatch, dedupes incidents by error signature, and nudges after a failure streak. Creating a trigger asks once; an approved trigger carries an allow rule for its own fires. A run cannot create a trigger. Model and effort pins stay his.

## What the session does

Grilling on what he wants to approve (each schedule once, or a standing rule per home) and on how a parked job shows in the UI. Output: the trigger table and the scheduler rules.

## Unblocks

Trader-agent methodology, methodology umbrella.

## Sources

`03-workflow-engines.md` §6 Hermes cron, §9.6, §10 idea 13; `05-qmx-today.md` §6 hook point 1, §7 `trigger_fires`; `BACKLOG.md` B34; clipping "Not Every Agent Workflow Needs AI".
