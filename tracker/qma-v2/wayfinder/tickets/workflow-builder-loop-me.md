---
title: Workflow builder from a rough description
type: prototype
mode: HITL
status: open
blocked_by: [loop-spec, skill-format-and-verbs, methodology-builder]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Fits rulings 18 and 23; creation must also work in the node editor with a test run."
---

## Question

How the operator describes a routine roughly and gets a built workflow: the interview, the spec it must reach, and the hand-off to a builder.

## Why it matters

He wants to give a rough picture and have it built (B28). Pocock's `loop-me` is the closest pattern: grill until the spec has a Trigger, Checkpoints pushed as late as possible, and a Brief, and an implementer could build it with zero questions. Anthropic's skill-creator adds the test loop with and without the skill.

## Recommended answer

A `build-workflow` skill: rounds of numbered questions with recommended answers; the spec is the loop header plus the graph; checkpoints default to the autonomy table; the builder is a worker role that writes the workflow file, its prechecks and a fake-model test; a with-and-without eval runs before the template is published to the Library. Done when the loop runs once on the fake model and the brief renders.

## What the session does

Prototype: a click-through of the interview as cards (not text), ending in a rendered workflow file and a brief. He reacts. Output: the interview script and the spec fields.

## Unblocks

Feeds the build plan and the self-improvement loop.

## Sources

`02-pocock-pstack.md` loop-me, skill-creator, §6, §8 ideas 10 and 11; `BACKLOG.md` B28; `05-qmx-today.md` §1 `build-workflow` placeholder.
