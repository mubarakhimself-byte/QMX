---
title: Lab overnight loop
type: grilling
mode: HITL
status: closed
blocked_by: [loop-spec, strategy-pipeline-gates, lab-agent-tools, strategy-funnel-template, feasibility-probes, night-planner]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Becomes a configuration of the one engine, not template one (ruling 22); the per-night usage budget and night-planner block are stale (rulings 26-27)."
closed: 2026-10-16
---

## Question

The researcher's night loop: hill-climb one metric with one change per trial, log every trial, keep a holdout the loop never sees, detect the plateau, change the search space once, write negative results, stop on evidence.

## Why it matters

This is the first template and the exit gate of the build plan. pstack's hillclimb playbook gives the loop; ml4t gives the brake (deflated Sharpe over the trial count, untouched holdout, costs on); BuildAlpha gives plateau detection and "move the box" (signals, fitness, filters) and the memory that makes revolution 400 smarter.

## Recommended answer

Loop header: trigger manual or nightly; precheck "new data or new idea since last run"; goal a metric, a direction and a stop predicate (target and minimum attempts); state `best_so_far`, `seen_ids`, `trial_count`, `plateau_rounds`; action one change, one backtest, keep or revert; evidence `metrics.json` and `trades.parquet`; feedback deterministic gates then a cheap judge; stop on goal, `max_iterations`, `no_progress_rounds: 2` (then one search-space move, then stop), budget, deadline. On stop: a result card and a brief; negative results to memory.

## What the session does

Grilling on the metric he wants first and the trial budget per night (usage). Output: the filled loop header and the template brief.

## Unblocks

Feeds first templates and the build plan.

## Sources

`02-pocock-pstack.md` hillclimb, §8 idea 5; clipping "The Loop Runs While You Sleep"; `06` §3.1 and the storyboard.

## Resolution

Resolved. Lab AD-4: every Lab procedure is a template on the one engine. Enabling Lab schedules is 'Lab OPEN-5'. (Map rewrite 2026-10-16.)
