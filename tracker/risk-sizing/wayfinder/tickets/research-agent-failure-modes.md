---
title: Research: how analysis agents are confidently wrong, and which checks catch it
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [Q31, L12-01, L12-02, L12-07, Q33, Q57, L12-09, L08-13, Q59, Q47]
---

## Question

Which of the fifteen ways an analysis agent can be confidently wrong (F1 to F15 in the CIS file) actually happen when agents analyse a recorded day? Which checks catch which failure: receipts recorded by the engine, typed claims, a forecast ledger scored later by the market, recompute hooks, a reviewer from a different model family, sealed inputs, named windows ("landmarks")? Does model memory of past markets matter for backtests of agent-built units, while live forward data stays safe? Should agents read chart images, numbers, or both? Can agents replicate or check the MIS well enough that their disagreement is a useful training signal?

## Why it matters

He: "We also need to know in which ways they can be wrong before we define the tools" (T2:382). Feeds the agent-proof ticket.

## Start from

- `research/funnel3/cis/problem-solving.md` knot (b) (F1 to F15 and 14 options).
- `research/19-grounding-old-system.md` §8 (opinion nodes, the Cartographer judged on calibration, the Coroner); `research/11-papers-llm-quant.md` (training-memory look-ahead).
- `research/18-grounding-today.md` §1.1 and §1.4 (the engine ledger and run zones already record what a run did); `C:/Users/Mubarak/Desktop/QMX/docs/glossary.md:570`.

## What would settle it

A small replay study: two agents on the same recorded day, one required to cite receipts and typed claims, one not; failures counted by a script, not by eye. Run on the cheapest model that can do the task.

## Output

`research/29-agent-failure-modes.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
