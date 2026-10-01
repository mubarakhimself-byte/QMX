---
id: SCN-0035
title: Cancel survives queued-to-running
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-WIRE]
decisions: [DEC-0489, DEC-0496, DEC-0490]
sources: [DEC-0489, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0035: Cancel survives queued-to-running

A UI cancel of the originating session does not die when the handle advances `queued`→`running` (DEC-0489, DEC-0496).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

UI-admitted JobHandle stores `originating_product_session_ref`. Connection principal equals that session principal. `handle_id` equals `job_id`. Client uses unique `dispatchCancel` and a stable `command_id`.

## When

Operator cancels while `queued`. Handle advances to `running` before the cancel is recorded. Repeat uses the same `command_id`. Already-terminal handle is a second case. Headless admit with omitted originating field is a third case.

## Then

`queued`→`running` does not invalidate that `command_id` (DEC-0496). First durable terminal wins. Already-terminal is a recorded no-op. `unknown` is not cancellable. Headless omit makes UI `cancel_job` unavailable; Story 36.5 remains the abort door. Not `stop_run`. Not an InvocationEnvelope invoke.

## Worked numbers

One `producer_id` per tab (DEC-0490). Exact equality of `handle_id`/`job_id`, `logical_run_id`, and `attempt_id`.
