---
title: Engine failure ladder, watchdog, doctor and notifications
type: task
mode: AFK
status: closed
blocked_by: [workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Answers ruling 21 and is core to the one engine; its wave 2 wording is stale (ruling 33)."
closed: 2026-10-16
---

## Question

Specify the engine's failure handling: saved step results and the model-call cache, reversibility tiers and idempotency keys, the policies `fail_fast`, `continue` and `escalate`, the ladder (retry, doctor repair by forking at the step and replaying the suffix, escalate with one inbox item), the zero-token watchdog, the run doctor role, the notification router by severity, and the CRO-style test for any logic change.

## Why it matters

Central piece C2 in `19`. `13` answers who writes the engine (QMX code, packet by packet), who monitors it (four layers, cheapest first), how he is notified (urgent, normal, routine; one message per run) and how a failed step is retried without re-spending (replay the saved prefix; cached calls are not paid again). Shepherd and prime-agent are copied as ideas, not taken as dependencies (Windows, in-memory runs).

## What the session does

AFK task. Write the failure spec as tables: effect tiers, policies, the ladder with budget checks before each retry, the watchdog's checks (no event for N minutes, over budget, repeated failure of one step, missed fires, the watchers themselves), the doctor's four buckets and allowed repairs, the inbox item shape, the severity router, and the fix-set and guard-set test for a proposed logic change. Add the fake-model test lanes. Hand back the spec.

## Unblocks

Shared blocks catalogue (`preflight`, `headroom`), wave 2 pilot templates, methodology umbrella.

## Sources

`13-failure-and-rlm.md` §1, §3, §4; `03-workflow-engines.md` §9.5-9.7; `11-references.md` §3; `19` C2.

## Resolution

Resolved. Engine AD-16 (failure ladder and watchdog) and AD-17 (the inbox is the one notification channel). (Map rewrite 2026-10-16.)
