---
title: Methodology builder (agents, workflows, skills, packs)
type: grilling
mode: HITL
status: open
blocked_by: [skill-format-and-verbs, agent-as-a-folder, loop-spec]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 18 (new versions, BMad builder plus skill writer)."
---

## Question

How he and the copilot create new versions of the methodology: a new agent, workflow, skill or pack (for example macro analysis for one pair), so that nothing in QMX is a fixed set.

## Why it matters

Correction D. BMad's builder (agent, workflow, module builders; six-phase conversational build; lint gate; quality optimise; evals; `customize.toml` layering) and Anthropic's skill-creator are the models. Today the three QMX skills are empty and no builder exists.

## Recommended answer

Four builders behind one `build` skill, each producing a versioned folder installed disabled until he enables it: agent builder (intent by natural questions, capabilities, dominion, memory), workflow builder (loop-me interview, template as base, folder with recipe, scripts, prechecks, tests), skill writer (intent, draft, 2-3 test prompts with and without, a viewer for his thumbs), pack builder (group into one `plugin.toml`, validate orphans and duplicates). A new methodology version is a pack that overrides the constitution's tables by value shape, never a fork. Modes guided, YOLO, headless. Full table in `12` section (i).

## What the session does

Grilling on the first builder he wants and on what "describe it roughly" looks like for him. Output: the builder skill briefs and the override format.

## Unblocks

Self-improvement loop; build plan.

## Sources

`01-bmad.md` builder, customize layering, evals; `02-pocock-pstack.md` §6; `12` section (i); correction D.
