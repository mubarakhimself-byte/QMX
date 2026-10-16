---
title: Loop spec as a first-class object
type: grilling
mode: HITL
status: open
blocked_by: [workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Loop engineering (ruling 2)."
---

## Question

What is a loop in QMX, as one object the operator can read: trigger, precheck, goal, state, action, evidence, feedback, stop, on-stop.

## Why it matters

The operator wants loop engineering, graph engineering and harness engineering used on purpose. His clipping lists the anatomy of a loop (trigger, goal, state, action policy, evidence, feedback, stopping rule) and warns that "keep trying" is not a loop. `03` §9.4 sketches the same object. Every overnight loop in `06` (hill-climb, scan, re-validate, overnight builder) is an instance.

## Recommended answer

Adopt `03` §9.4. Stop always includes `max_iterations`, `no_progress_rounds` and `budget_exhausted`. Precheck is a zero-token script that may return `{wake: false}`. Feedback is a grader node, deterministic first, model second. State carries `best_so_far`, `seen_ids` and the trial count. On stop: deliver a brief, open a gate, or stay silent when nothing changed. A loop is a workflow with this header, so it checkpoints and pauses like any run.

## What the session does

Grilling on the words he wants in the UI (trigger, wake, stop, plateau) and on what a loop shows while running. Output: the loop header schema and one example (the hill-climb) filled in.

## Unblocks

Workflow builder, trader-agent methodology, Lab overnight loop, methodology umbrella.

## Sources

Clipping "Agent Harness Engineering vs. Loop Engineering vs. Graph Engineering"; `03-workflow-engines.md` §5, §9.4; `02-pocock-pstack.md` autonomous-run and hillclimb playbooks.
