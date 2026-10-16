---
title: Gate and threshold store, read-only to agents (C8)
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Still needed; only the wave wording is stale (ruling 33)."
closed: 2026-10-16
---

## Question

Specify where gate thresholds live (Settings, versioned, logged), how a verdict binds to the graph's and the candidate's content hashes, how the engine lint refuses any step that writes Settings, how variants may tighten and never loosen, and the shipped defaults.

## Why it matters

Central piece C8 in `19`. "The model proposes, the pipeline decides." Every overfit audit, watchdog threshold and paper rule reads this store. The strategy-pipeline-gates ticket decides the numbers with him; this ticket builds the store and the lint so the numbers cannot be argued with by a prompt.

## What the session does

AFK task. Write the store schema (gate id, parameter, value, unit, direction, version, changed by, changed at), the `hash-bind` rule, the lint rule, the variant tighten-only check, the run-chrome display of the active version, and the default table from `19` C8 and section 9. Hand back the spec and a test plan on the fake model.

## Unblocks

Wave 2 pilot templates (RK4, B, L1), the overnight Lab loop, the trader-agent methodology.

## Sources

`16-templates-trader-risk.md` RK4, §4.5; `17-templates-dev-pm-lab.md` §Gates and settings; `19` C8 and section 9; clipping "The Loop Runs While You Sleep".

## Resolution

Resolved. Lab AD-13: thresholds are Settings data bound to the draft hash; an agent may tighten, never loosen. Engine SettingsPort (SOLUTION-DESIGN 8.3) and section 17 defaults. (Map rewrite 2026-10-16.)
