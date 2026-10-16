---
title: Skill format and QMX verbs
type: task
mode: AFK
status: open
blocked_by: [folder-format-one-shape]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 4."
---

## Question

Write the one skill format every QMX agent, workflow and tool uses, and the small set of QMX verbs that replace host tool names, so a skill runs on any model.

## Why it matters

Three skills exist and all say "Pending authoring" (`05` §1). BMad, Pocock and pstack all converge on one folder format (SKILL.md plus scripts, references, assets), and the open Agent Skills standard fixes the frontmatter (`01` §Q1; `02` §3, §5). Without a format, the builder, the evals, agent folders and mini-app skills have no target.

## Recommended answer

Adopt the Agent Skills standard (`name`, `description` with what and when, `scripts/`, `references/`, `assets/`, body under 5,000 tokens). Add a `metadata.qmx` block: `invocation: user | model`, `roles_used`, `verbs_used`, `homes`. Replace host tool names with five verbs: `load_skill`, `spawn_worker(role, prompt)`, `ask_operator(question, options, default)`, `schedule(trigger)`, `publish_view(block)`. Host sidecars (`agents/openai.yaml` style) carry Claude or Codex specifics. Scripts are Python with PEP 723 inline dependencies. Every subagent feature declares a sequential fallback.

## What the session does

AFK. Write `SKILL-FORMAT.md` and a validator script (`validate_skill.py`: frontmatter, folder names, verb allow-list, body size, link check). Rewrite the three placeholder skills to the format as worked examples. Hand back the spec and the validator output.

## Unblocks

Agent as a folder, mini-app lifecycle, evals harness, workflow builder, self-improvement loop, methodology umbrella.

## Sources

`01-bmad.md` §Q1 skill, §Q5; `02-pocock-pstack.md` §3 Agent Skills spec, §5, §8 idea 1; `05-qmx-today.md` §1 skills row.
