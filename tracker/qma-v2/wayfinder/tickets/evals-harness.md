---
title: Evals harness for skills and workflows
type: task
mode: AFK
status: closed
blocked_by: [skill-format-and-verbs, role-to-model-table]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Model-agnostic re-checks (ruling 3)."
closed: 2026-10-16
---

## Question

Build the small eval harness that proves a skill or template before it joins the Library and re-checks it when the model changes.

## Why it matters

Model-agnostic means re-checking per model (`01` §Q5). BMad's eval runner is Claude-specific, so QMX needs its own on its adapter. pstack's eval playbook gives the method: blind candidates, one organic prompt, candidates on different families, a blinded judge on another family, verify from transcripts. Anthropic's skill-creator gives the with-and-without loop and a viewer where he clicks good or bad.

## What the session does

AFK task. Specify and build: trigger evals (does the description fire on the right prompts), artifact evals (with skill versus without, two or three realistic prompts, assertions drafted while runs go), a clean-room runner on the fake model and on two real families through the role table, a grader that cites evidence, and an HTML viewer with Outputs and Benchmark tabs. Hand back the harness and one eval of the `strategy-gates` skill.

## Unblocks

Self-improvement loop.

## Sources

`01-bmad.md` evals, §Q5 weak spot; `02-pocock-pstack.md` eval playbook, skill-creator, §8 idea 11; `HARNESS-PLAN.md` `fake_model.py`.

## Resolution

Resolved. Engine AD-11 (test gate on real cheap models, ruling 51) and AD-26 (champion and challenger replay). Skill evals belong to 'QMX skill set and builder (B28)'. (Map rewrite 2026-10-16.)
