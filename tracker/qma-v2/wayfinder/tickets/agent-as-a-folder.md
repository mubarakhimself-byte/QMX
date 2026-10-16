---
title: Agents and workflows as clean folders
type: grilling
mode: HITL
status: open
blocked_by: [skill-format-and-verbs, plugin-unit-and-loading]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Folders match ruling 19; study 14 has landed, fold it in."
---

## Question

What an agent and a workflow are on disk: one clean folder each, holding persona or recipe, capabilities, scripts, tests, settings, dominion (read, write, deny zones) and a memory pointer, and how a folder becomes a Claude sub-agent file, a relay agent or an engine run from the same source.

## Why it matters

Correction E: organisation is paramount; agent-as-a-folder (B32) applies to workflows too. BMad's shipped agent is three files plus a sanctum outside the skill so the agent cannot rewrite itself; Pocock's skills carry host sidecars. Study 14 will cover the Vercel-style folder framework (pending).

## Recommended answer

`agents/<name>/`: `SKILL.md` (persona, menu, capabilities, verbs), `agent.toml` (type stateless, memory or autonomous with a `PULSE.md`; dominion; model role), `references/`, `scripts/`, host sidecars; memory in a sanctum outside the folder. `workflows/<name>/`: `workflow.yaml`, `scripts/`, `prechecks/`, `tests/`, `settings.toml`, `README.md`. One writer per folder; versions by content hash in the registry; both installable as part of a pack. Money-path agents terse and evidence-led.

## What the session does

Present the layout, grill on names, and fold in study 14's framework when it lands. Output: the two folder specs and one worked example each (a scanner agent, the watchdog workflow).

## Unblocks

Methodology builder, trader-agent methodology; feeds the build plan.

## Sources

`01-bmad.md` §Q1 agent, memory agents, idea 14; `02-pocock-pstack.md` §1 sidecars, §2 layout; `BACKLOG.md` B32, B52; `12` sections (b), (c); correction E.
