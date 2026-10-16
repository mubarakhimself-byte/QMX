---
title: Trial ledger, sealed holdout and live cost model (C9)
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Ledger and holdout stand; the live cost model from T9 is node depth (ruling 14) and the wave wording is stale (ruling 33)."
closed: 2026-10-16
---

## Question

Specify the family ledger that records every trial (passed or not, dead ones included) and serves the trial count and the deflated Sharpe; the sealed holdout per family created by `spec-compile` and unlocked once by `holdout-touch`; and the live cost model written by T9 and read by backtests and audits.

## Why it matters

Central piece C9 in `19`. Multiple testing is the way solo quants fool themselves; the ledger is the brake. The holdout touched once is the only honest out-of-sample test. Backtests on guessed costs kill scalpers; the live cost model fixes that.

## What the session does

AFK task. Write the ledger schema (family id, trial id, spec hash, parent, change label, verdict, run id), the holdout registry (window, created, touched count, who, why), the rule that a second touch is a new counted trial with a new window, the cost model schema (instrument, hour, order type, spread, slippage, commission, version), and the service calls `qmb.family.*`, `qmb.holdout.*`, `qmb.memo.get`. Map onto the QMB ledger and `qmx_ledger.experiments` that exist today. Hand back the spec.

## Unblocks

Wave 2 pilot templates (B, L1, D2, D3, RK4), the overnight Lab loop, variants and comparison.

## Sources

`17-templates-dev-pm-lab.md` D2, D3, §family-ledger, §holdout-touch, §What the Lab backend must provide; `16-templates-trader-risk.md` §4.4, T9; `05-qmx-today.md` §4 QMB ledger; `19` C9.

## Resolution

Resolved. Lab AD-6: families, trials and holdouts are Library edges; the holdout is touched once per family. The live cost model is node depth (ruling 14). (Map rewrite 2026-10-16.)
