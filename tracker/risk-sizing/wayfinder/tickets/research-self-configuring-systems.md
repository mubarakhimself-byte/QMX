---
title: Research: what self-configuring trading systems read and change
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L01-02]
---

## Question

When a trading system "configures itself", what does it read (its own journal, account equity, a shared budget, the market journal, broker facts) and what does it change (risk per trade, lot size, stop distance, which sessions it trades)? Where does each real example stop and wait for a human? Compare four to six real systems: the MT5 Wizard money modules, freqtrade and Jesse position sizing, adaptive or fractional Kelly in practice, the old enhanced Kelly with house money, and the July "trust-bounded cost-aware Kelly".

## Why it matters

He has never been shown how a unit configures itself, and STATE says this is what he needs most (operator round 10-27, "Account guard and pod"). The answer feeds the self-configuration prototype and the risk socket. The maths stays with the risk session.

## Start from

- `STATE.md` operator round 10-27 ("Account guard and pod", "Risk and sizing") and `HANDOFF-RISK-SIZING.md`.
- `research/04-platform-study.md` (MT5 Wizard modules), `research/19-grounding-old-system.md` §5, `research/07-funnel.md` (the unit shape), `research/08-old-qmx-testing-and-decay.md` (decay check).
- MQL5 reference for `CExpertMoney`; freqtrade and Jesse sizing docs.

## What would settle it

A table: system × what it reads × what it changes × its limits × where a human must approve. No formula chosen.

## Output

`research/20-self-configuring-systems.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
