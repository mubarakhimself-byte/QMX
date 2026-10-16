---
title: Shared building blocks catalogue
type: task
mode: AFK
status: closed
blocked_by: [folder-format-one-shape, workflow-engine-contract, engine-failure-and-doctor]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Blocks become engine nodes and sub-workflow configs (ruling 22); wave 2-4 wording is stale (ruling 33)."
closed: 2026-10-16
---

## Question

Turn `19` section 5 into real folders with stable names: the sub-workflows, pre-checks, graders and rules, script libraries, skills and roles every template assembles from, so no template re-invents a block and every block has one owner and one test.

## Why it matters

`15`, `16` and `17` each proposed blocks with overlapping names (two "R7"s, three "calibrate" callers, "overfit-gates" in two places). `19` deduplicated them into one catalogue. The templates in waves 2 to 4 are assembled from these, so the catalogue must exist first.

## What the session does

AFK task. Create `workflows/_blocks/<name>/` for each sub-workflow (C1 shape), `prechecks/<name>.py`, `graders/<name>.py`, `lib/<name>/` for the script libraries, and `agents/_shared/skills/<name>/` for the skills, each with a fixture test. Port the ml4t skills (Apache-2.0) into `skills/`. Write the role list into the Settings schema. Hand back the folder tree and `qmx workflow info` output for each block.

## Unblocks

Wave 2 pilot templates, wave 3 templates.

## Sources

`19` section 5; `15` §Shared building blocks; `16` §4; `17` §Shared building blocks; `02-pocock-pstack.md` §3 ml4t.

## Resolution

Superseded. Blocks are engine node kinds and sub-workflows (engine AD-5). The template pack is in `ENGINE-PLAN.md`. (Map rewrite 2026-10-16.)
