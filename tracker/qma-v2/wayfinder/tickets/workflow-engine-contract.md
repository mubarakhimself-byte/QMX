---
title: Workflow engine contract (assumptions A1-A2; spec)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Still the central ticket; rewrite for rulings 22-26: runs apart from the harness, a test step, several accounts, and the docs engine node kinds (study 24 section 3)."
---

## Question

What a QMX workflow is, as a contract the engine, the Lab, the templates, the builder and the UI all read: the folder, the node kinds, state and reducers, checkpoints, human gates, pause and resume, triggers, and the log every run writes so he or the hub copilot can inspect what happened and how.

## Why it matters

The operator approves the direction: an own small engine that combines LangGraph's graph, checkpoints and human gates with Hermes's cron, script-only jobs and pre-checks, with Claude as one worker. Nothing survives the deletion program (`05` gap 1). Ten tickets wait on this one. Logging and observability are a requirement, not an option (correction 8). Every workflow is a clean folder (correction E; study 14 pending for the shared folder framework).

## Recommended answer

The contract in `12` section (c). Node kinds script, rule, model, agent, human, subflow, grader, fanout; `rlm` as an optional kind for data-heavy research, off until a template needs it (correction 11; study 13 pending). Typed state with reducers; SQLite event log plus step snapshots; gates bound to the graph hash; idempotency keys on side-effecting scripts; drain at the cap; triggers as rows with prechecks; memory scopes with one writer each; a trace per run and a span per node with model, cost and gate verdict; `runs.explain(run_id)` for the hub; `runs_on` per node and a portable bundle so a run can move to the server. Chats-as-steps named as the fallback. The Claude `Workflow` tool is one optional node kind.

## What the session does

Grilling in rounds on the words he will see (workflow, run, node, gate, loop, trigger, paused) and on what the run view shows. `domain-modeling` writes the glossary. Red-team before closing. Record two probes for the first packet: the `Workflow` tool from the SDK under a Max login, and whether `SDKUsageReport` arrives on a cadence. Failure recovery and who writes, monitors and notifies: fold in study 13 when it lands.

## Unblocks

Loop spec, triggers and scheduler, pause at cap, async delegation and fan-out, trace shape, first templates, strategy funnel template, research harness design, Experimentation Board, memory scopes, send a workflow to the server, methodology umbrella.

## Sources

`03-workflow-engines.md` §1, §7-§10; `05-qmx-today.md` §6 hook points, gaps 1 and 6; `11-references.md` §3 Hermes; `12` section (c); corrections 8, 11, E.
