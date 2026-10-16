---
title: Self-improvement loop
type: grilling
mode: HITL
status: open
blocked_by: [memory-scopes-and-lessons, skill-format-and-verbs, evals-harness, methodology-builder]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Backlog B41."
---

## Question

How QMX turns repeated mistakes into checks, skills and prompt changes, behind a human gate, without an agent editing its own instructions.

## Why it matters

"I don't want it to do the same mistake" (B41). The loop-engineering clipping calls this the fourth loop: an analysis agent reads traces and rewrites prompts, tools or graders. Pocock's `retro` and pstack's `correct` rank the fix: deterministic check first, standard second, steering text last. Revision 1 of the architecture had a `lessons` table, a weekly mining job, a skill draft as a new plugin version, an eval gate, an approval row, and undo by the previous plugin hash.

## Recommended answer

Recover the revision 1 design. A weekly mining job reads traces and lessons, clusters repeats, proposes a fix at the highest level (architecture, type, lint, test, docs), drafts a skill or check as a new plugin version, runs the eval gate against "no skill", and parks an approval card. Activation is his click; undo is the previous hash. The agent never writes to its own sanctum or its active plugin.

## What the session does

Grilling on cadence and on what he wants to approve. Output: the loop header for the improver loop and the approval card shape.

## Unblocks

Nothing on this map; feeds H2 of the build plan.

## Sources

`BACKLOG.md` B41, B53; `05-qmx-today.md` §7 lessons; `02-pocock-pstack.md` retro, correct, §8 idea 12; `03-workflow-engines.md` §5 loop levels, §10 idea 15.
