---
title: Autonomy policy (spec; the asks are decisions 1, 2, 5)
type: task
mode: AFK
status: open
blocked_by: [decision-1-lab-self-scheduling, decision-2-strats-promotion-notify, decision-5-checks-bind-agents-only]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Blocked on superseded decisions 1 and 2; Strats (ruling 28) and inside-the-cap wording (ruling 27) are stale."
---

## Question

One table that says, per home and per pack, what an agent does without asking, what parks with a default, and what never runs.

## Why it matters

Correction 4: the Lab is QMX's core feature with total creative freedom; nothing in the Lab asks except money (always read-only) and publishing outside the Lab. Correction 6: Portfolio is human-driven. The rulings exist in pieces (money hook; publish, install, schedule and manage ask; 50% cap). Nothing joins them into one rule the engine, templates and approval UI read.

## Recommended answer

| Home or pack | Without asking | Parks with a default | Never |
|---|---|---|---|
| lab | Everything: build strategies, components, variants, MIS versions, indicators, ML and neural nets, run workflows, write Lab memory, schedule Lab-scoped runs inside the cap | Publish outside the Lab (to Portfolio, to Strats as a governed object, to an app) | Money; changing trust; editing its own plugin; the account guard |
| portfolio | Reads, read-only simulations, drafting cards | Every write and every proposal (his approval) | Money; limits; kill switch; the account guard |
| general and combined sessions | Lab rules on Lab objects, Portfolio rules on Portfolio objects; the stricter row wins on overlap | As above | As above |
| background and child | Inherit the parent's row; unattended asks expire to `needs_you` | | Cannot create triggers |

Standing rules: the reviewer of an artifact is a fresh context on another model family where one exists; a gate is a script no prompt may skip; a run at the cap drains and parks. Conflict flagged: Lab-scoped schedules run under a standing allow rule, which bends the letter of ruling Q1 (schedule asks) for the Lab only.

## What the session does

Grilling on the Lab rule in his words, on the Portfolio row, and on expiry times. Output: the autonomy table as data.

## Unblocks

Triggers and scheduler, capability packs, Lab agent tools, trader-agent methodology, browser, methodology umbrella.

## Sources

`BACKLOG.md` rulings table, B26; `02-pocock-pstack.md` autonomy; `03-workflow-engines.md` Hermes safety rules; `05-qmx-today.md` §6 effects; `12` section (l); corrections 4, 6, F, G.
