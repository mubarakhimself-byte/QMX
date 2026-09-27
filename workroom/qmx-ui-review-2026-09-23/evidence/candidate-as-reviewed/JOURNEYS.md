---
name: Journeys
sitting: architecture-QMX-UI-2026-09-23
---

# Journeys

Three namespaces. Do not collapse them.

| Namespace | What | Execution |
| --- | --- | --- |
| `P1-*` / `P2-*` | Frozen 85 challenge IDs | Specification only. SHA-256 `1c2c865d1cef50076682a737472174fa307cf1fc8eb3663b122ed04ab6f39fd8` |
| `SCN-NNNN` | Canonical docs scenarios | SCN-0001..0022 committed; SCN-0023..0027 pack-and-grant on disk, untracked on main, absent at integration inspect |
| `J-KIT-*` / `J-UI-*` | Sitting journeys | Prose traces |

Full 85 mapping: `research/08-bdd-reconciliation.md`.

## J-UI-01 — Switch apps during an ML run

Visible app B is selected while ML run R started under session S continues. Tokens, questions, and completion still bind to S. Closing B does not cancel R. Retains `P1-SES-001`, `P1-PLC-004`.

## J-UI-02 — Headless invoke, no pane

Pack omits `view:*` and `copilot_profile`. Enable is not grant. Operator invokes via qmb CLI or future wire. JobHandle exists. No navigation pane. Matches SCN-0024 / J-KIT-01.

## J-UI-03 — Open a code node and return

Select node N on graph G (draft V, viewport recorded). Open/Expand shows code for V. Validation names V. Return restores G. Editing V2 is not running V1.

## J-UI-04 — Cross-app reference, separate conversations

Composer on S_A references instance/artifact of B. Histories stay separate. Authority stays S_A grants. Unavailable B is labelled; draft remains.

## J-UI-05 — Missing resource

Library or composer shows missing/unavailable/deleted. Invoke refuses that identity. No silent substitute (tombstone).

## J-UI-06 — Stale data / reconnect

After transport loss: reconnecting vs stale vs failed are distinct. Reconnect restores context without replaying intent or implying approval.

## J-UI-07 — Duplicate submit

Double-activate of a side-effecting op does not create a second send. Lost ack → `unknown` until reconcile. `read` may host-retry.

## J-UI-08 — Cancel racing success

One race-safe terminal. Cancelled **display** is not proof the worker stopped. Interrupt is not labelled cancelled.

## J-UI-09 — Local file used remotely

Attach local path to a remote job: stage a content-identified artifact or refuse. Remote failure does not silently retarget locally.

## J-UI-10 — Backend incompatibility

Incompatible pack/host version refuses at enable. Prior roster remains. Shell stays usable.

## J-UI-11 — First-run provider failure

Splash, then usable window. One provider fails. Other work remains. Retry is actionable. Not an indefinite full-app block.

## J-UI-12 — Install / update / rollback

Installed vs enabled vs granted stay distinct. Failed activation does not retarget in-flight pinned runs. Grant unchanged until explicit re-grant.

## Vertical slice (proposal, not a cap)

1. Differentiated shell + Home instance-pick (J-UI-01, SCN-0023).
2. One widget expand/return (AD-8; with J-UI-03 if graph-backed).
3. Headless invoke (J-UI-02).
4. Reconnect restoration (J-UI-06).

Paper-then-live + L17 remains for trading seats only. No universal paper gate.
