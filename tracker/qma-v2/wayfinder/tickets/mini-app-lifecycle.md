---
title: Mini-app lifecycle: archive, DevOps, Lab dependency
type: grilling
mode: HITL
status: closed
blocked_by: [plugin-unit-and-loading, skill-format-and-verbs, mini-app-data-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Matches ruling 9; align creation with workflows (ruling 23) and archive with DEC-0443 (26 section E)."
closed: 2026-10-16
---

## Question

How the copilot creates, builds, maintains, edits, improves and archives mini apps through their plugins, what observability and logging each app has, and how apps depend on the Lab.

## Why it matters

Correction 3: mini apps are archived, never deleted; they have DevOps (observability, logging); most depend on the Lab. The runtime, road to live and control door exist; skills are empty; there is no archive or disable; trust is caller-chosen (`05` §1). The UI's Remove only edits browser state (`10` §5).

## Recommended answer

The lifecycle table in `12` section (g): create (interview, variants, tests-first build, review on another family; no ask), test (road stages; no ask), publish and install (install card; always asks; trust from approval; agent-built apps install disabled), maintain (retro and correct; no ask), edit (new immutable version; publish asks), improve (weekly review proposes; a card parks), archive or disable (a card with door type and blast radius; asks; versions, evidence, logs and artifacts kept). DevOps: road evidence, box, logs as spans in the shared trace store, breaker trips as incidents, "ask why" through the hub, backups. Apps declare what they feed on from Lab kinds. No per-app copilot.

## What the session does

Grilling on the install card and the archive card. Output: the lifecycle table, the three skill briefs (`build-mini-app`, `build-workflow`, `debug-app`), and the small backend fixes (archive, disable, trust-from-approval). Platform analogues pending study 14.

## Unblocks

Build plan.

## Sources

`05-qmx-today.md` §1; `10-ui-depth.md` §5, §6 mismatches 10 and 11; `BACKLOG.md` B23, B16, B42; `12` section (g); correction 3.

## Resolution

Resolved. Engine AD-11 and AD-19 (same create, test, publish flow as workflows, ruling 23) and Library AD-6 (archive, never delete, ruling 9). (Map rewrite 2026-10-16.)
