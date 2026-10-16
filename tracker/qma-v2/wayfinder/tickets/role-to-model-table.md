---
title: Model tiers and reviewer settings (assumption A5; spec)
type: task
mode: AFK
status: closed
blocked_by: [decision-3-spend-number]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Blocked on superseded decision 3 (ruling 27); add accounts and the load balancer (ruling 26)."
closed: 2026-10-16
---

## Question

The Settings panel where he configures which model runs which role, per workflow and per step, which family reviews what, and which keys are used. No roster is hard-coded.

## Why it matters

Corrections 7 and H: per-workflow model configuration is paramount, often through API keys; reviewers on a different family where possible; today Claude has most usage, ChatGPT comes through the GPT lane later, Chinese models later as workflow workhorses; long workflows go to a server. Profiles exist (`settings.toml [providers]`, `resolve_model`, `delegate({profile})`); roles and per-workflow overrides do not.

## Recommended answer

Three layers in Settings, all UI-editable: a role table (copilot, lab-worker, builder, researcher, judge, review-panel, scanner, grader, validator) mapped to profiles with `inherit-parent` and `auto` fallbacks; a per-workflow override (model and effort per step, budget, `runs_on`); a reviewer rule ("a different family from the author where one is configured; otherwise a fresh context"). Skills and workflow files name roles only. Resolved models are written on every span. Plan roles show window percent; key roles show USD. The defaults are his; the charting draft is only a starting suggestion.

## What the session does

Grilling on which roles may use keys and on the first defaults. Output: the Settings fields and the resolution rule.

## Unblocks

First templates, research harness design, evals harness, system-prompt design, methodology umbrella.

## Sources

`02-pocock-pstack.md` setup-pstack; `HARNESS-PLAN.md` HP7, HP12, HP13, HP16; `BACKLOG.md` B35; `UI-NOTES.md` §6; corrections 7, H.

## Resolution

Resolved. Engine AD-13 (roles map to models in Settings, ruling 15) and AD-12 (account pool and load balancer). (Map rewrite 2026-10-16.)
