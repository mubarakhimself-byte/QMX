---
title: Pause at the cap, do not fail
type: task
mode: AFK
status: closed
blocked_by: [workflow-engine-contract, feasibility-probes]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Pause and resume stands (ruling 27) but must work per account with the load balancer (ruling 26) and never park on a human gate; the user:profile probe does not apply to Python (20b finding 9)."
closed: 2026-10-16
---

## Question

Design and prove the drain, park and resume path: when background usage reaches the operator's cap, running nodes finish or checkpoint, no new model node starts, the run shows `paused` with a countdown, and it resumes after the window resets.

## Why it matters

The ruling is "pause, don't fail" (BACKLOG S3, evening ruling 10-13). HP10 and HP11 built the governor and the refusal at the cap, but a refusal is not a pause. The Claude `Workflow` tool's own pause does not work under the SDK (`03` §1). LangGraph's `request_drain` is the model to copy.

## What the session does

AFK task. Probe whether `SDKUsageReport.rate_limits` arrives on a cadence or only on request, and whether the OAuth token has the `user:profile` scope (without it the field is `null`). Then specify: governor headroom formula (an operator setting), admission control before every model node, `drain_requested` at step boundaries, a mid-node 429 marks the node `waiting` not `failed`, scheduler parking, spend-neutral retries before any model call, escalation to a human gate after a capped number of waits. Hand back the spec plus the probe results.

## Unblocks

Nothing directly; it is required by the first templates to run overnight. Feeds the build plan.

## Sources

`03-workflow-engines.md` §2 usage signals, §3 drain, §9.6, open questions; `HARNESS-PLAN.md` HP10, HP11; `BACKLOG.md` S3; `UI-NOTES.md` §6.

## Resolution

Resolved. Engine AD-9 (limits pause the work; nobody is asked) with per-account leases from AD-12. (Map rewrite 2026-10-16.)
