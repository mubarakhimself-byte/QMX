---
id: SCN-0030
title: Lost host_control recovery without the lost token
type: scenario
status: ratified
component: COMP-QMB
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0503, DEC-0494]
sources: [DEC-0503, SRC-28]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0030: Lost host_control recovery without the lost token

Recovery replaces the token file without reminting the operator or wiping journals (DEC-0503).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

`local_operator` exists. `host_control` file is missing. Journals exist. The OS user owns `QMA_DAEMON_ROOT`.

## When

Positive: daemon is stopped. Owning OS user runs `qmb host recover-control` without presenting the lost token. A one-shot daemon recover entry acquires `.daemon_writer`, appends the new `host_control_fp1`, exits without binding 8765 (DEC-0494). Then `qmb host start`.

Negative A: other OS user runs `recover-control`.

Negative B: token file still readable and caller uses `recover-control`.

Negative C: daemon still live and caller uses `recover-control`.

## Then

Positive: new owner-only file; previous fingerprint dead; same `local_operator`; journals intact (DEC-0503).

Negative A: refuse; data root untouched.

Negative B: refuse; use `rotate-control`.

Negative C: refuse; OS owner may `stop` without the token because the file is missing, then recover (DEC-0494). That stop exception is not a general unauthenticated stop path.

## Worked numbers

Principal count remains 1. Port 8765 is not bound during recover.
