---
title: Async delegation and fan-out
type: task
mode: AFK
status: closed
blocked_by: [workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Fold into the one engine (ruling 22); fan-out may now span several accounts (ruling 26)."
closed: 2026-10-16
---

## Question

How does a run fan out to many workers and join their results, and does `delegate` need job handles, or does the engine own all concurrency?

## Why it matters

`delegate` is synchronous, depth 1, no job handle, no mailbox (`05` gap 6). Long research loops, parallel arms and days-long trader agents have no primitive. The 06 candidate pick says the engine owns fan-out and `delegate` stays a helper.

## What the session does

AFK task. Specify the `fanout` modifier: one task per item, per-item state and timeout, `all` or `any` join, reducer merge, finished items kept on partial failure. Specify a message filter so each worker sees only its inputs (AutoGen's execution graph vs message graph). Decide whether a worker is a `Child` chat or a `Workflow` tool agent, per role. Keep `delegate` as is. Hand back the spec and a fake-model test plan.

## Unblocks

Feeds first templates and the build plan.

## Sources

`03-workflow-engines.md` §6 AutoGen, §8 items 5 and 14, §9.2 fanout; `05-qmx-today.md` §6 hook point 2; `01-bmad.md` subagent patterns (filesystem blackboard, parent reads last).

## Resolution

Resolved. Engine AD-5 (`broadcast` edges and `join`) and AD-4 (sub-agents inside an agent node, ruling 52). Chunked fan-out (ruling 78) is in 'Engine amendment: chunked fan-out, compaction, caching, hooks'. (Map rewrite 2026-10-16.)
