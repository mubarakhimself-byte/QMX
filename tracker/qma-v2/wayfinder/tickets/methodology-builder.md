---
title: QMX skill set and builder (B28)
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 18 (new versions, BMad builder plus skill writer)."
---

## Rewrite (2026-10-16, map rewrite)

Re-scoped to B28 (26 section C: researched, not designed). Question: which BMad, Pocock and pstack skills become QMX skills, in what format (Agent Skills format with QMX verbs; the old 'Skill format and QMX verbs' ticket is folded in here), and how he and the copilot build a new skill or a new version of a workflow from a rough description (ruling 18). Skill evals land here too. Recommended answer: one QMX skill format (Agent Skills plus a `qmx.toml`), a builder skill that reuses engine AD-22's loop-me interview and AD-11's test gate, stored as Library `skill` objects. Handled tomorrow (ruling 82).

The text below is the earlier charting; where it disagrees with this section or with `26`, they win.

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
