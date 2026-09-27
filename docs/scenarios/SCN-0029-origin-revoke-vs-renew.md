---
id: SCN-0029
title: Origin-revoke versus renew orderings
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMB, COMP-QMA-WIRE]
decisions: [DEC-0492, DEC-0491]
sources: [DEC-0492, SRC-28]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0029: Origin-revoke versus renew orderings

Origin-revoke is a `journal_seq` barrier. Both commit orders have a defined outcome (DEC-0492).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

An Origin has a live `pairing_proof` P1 with `pairing_record_id` R1. Daemon journal is sole writer.

## When

Ordering A: `POST /pair/renew` with P1 commits first (new proof P2, R1 revoked), then `qmb host pair revoke --origin <origin>` commits at `journal_seq` R.

Ordering B: `--origin <origin>` commits first at R, then `POST /pair/renew` with P1.

`--session R1` after a renew is a separate case: it is a recorded no-op on the old id; P2 stays live until origin-revoke.

## Then

Ordering A: P2 is revoked because its `journal_seq` is less than R (DEC-0492). Origin-revoke is never discarded because a renew appended first.

Ordering B: renew of P1 refuses. `/pair/confirm` of pre-R pendings cannot issue.

After R, a **new** `/pair/start` is legal and may be QMB-confirmed (re-pair) (DEC-0492). `--session` never origin-wide-cuts.

## Worked numbers

Barrier identity is `journal_seq` R, not wall clock. No TTL number is used (`GAP-0109`).
