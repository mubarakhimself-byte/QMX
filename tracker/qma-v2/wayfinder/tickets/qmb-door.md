---
title: QMB-session dependencies
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Owned by the QMB session; ignore the B-lite and wave wording (ruling 33)."
---

## Rewrite (2026-10-16, map rewrite)

Re-scoped to what the QMB session must deliver for this map: the `qmb.compile` door and qmb node pack (Lab AD-5); the `qmb` CLI inside the worker bundle (Lab DOC-CHANGES, P21 row); the one dedicated QMB machine agents call (engine AD-31, ruling 68); a spread instrument before pairs (Lab OPEN-6); retiring `run_backtest(config_ref)`. Owned by the QMB session; this ticket closes when that session records its answers.

The text below is the earlier charting; where it disagrees with this section or with `26`, they win.

## Question

QMB must accept an agent-written experiment spec through a host validator (`qmb.spec.compile / validate / register`) and run backtests, sweeps, walk-forward and robustness from a spec, not a stored config. QMB is the operator's tamper-proof tool, edited only by its own session (BACKLOG B7). This ticket records that session's answer and the measured compute (probe 9).

## What the session does

HITL placeholder for the QMB session: open the door, time 200 trials and one gate battery on his PC, record the result here and close. Until it closes, L1 runs on pre-registered configs ("B-lite") and B, D3 and the full gates wait.

## Unblocks

Funnel B in full, D3, the overfit gates beyond the defaults, wave 3.

## Sources

`20-review-b` finding 14 and probe 9; `21` B10; `05-qmx-today.md` §2.
