---
title: Run logs he and the copilot can inspect
type: task
mode: AFK
status: open
blocked_by: [workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Rulings 9 and 21."
---

## Question

The trace, span and event shape for runs, nodes, jobs and apps, the fields every span carries, how the UI shows a run as a timeline, and how the hub copilot reads a log to explain what happened and how.

## Why it matters

Correction 8: the engine must have logging and observability so he or the copilot can inspect what happened. The self-improvement loop reads traces. The UI has no run or node event kinds (`05` gap 13). Hermes's job panel (status, failure streak, incidents, next fire) is the model for jobs (`11` §3).

## What the session does

AFK task. Specify: a run is a trace, a node a span, the thread the group id; span fields (role, resolved model, provider, tokens, cost estimate, cache hits, duration, attempt, wake decision, gate verdict, artifact references, `runs_on`); run and node event kinds in the durable topics with meaning in `content`; the timeline block with gates and the paused reason; the job panel fields; `runs.explain(run_id)` as a hub tool that reads the log; incidents keyed by error signature. Who writes, monitors and notifies: fold in study 13 when it lands. Hand back the schema and a sample.

## Unblocks

Feeds the build plan, the self-improvement loop and the mini-app DevOps.

## Sources

`03-workflow-engines.md` §6 OpenAI tracing, §9.7; `11-references.md` §3; `02-pocock-pstack.md` show-me-your-work; `UI-NOTES.md` §2; `05-qmx-today.md` gap 13; correction 8.
