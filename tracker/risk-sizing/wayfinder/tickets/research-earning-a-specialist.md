---
title: Research: earning a per-market specialist without luck
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L02-02, L02-03, L02-09, L02-16, L02-12, Q64, Q27, Q76, Q73, L10-06, Q16]
---

## Question

A System 2 is earned from the record its System 1 parent built on that market (his Path A ruling, `STATE.md:120`). How is that done without luck? Is the market chosen before or after its trail is read? Is a "wins broadly" test still needed? Is "broad" judged on one pooled read or per market, and what does each cost in tries? Can a sequential test replace a fixed trade count? Do retired children's trades stay in the parent's record? Do paper runs on unadmitted matching markets count as evidence or as tries? Can two specialists on correlated markets come from what is really one trail? Can specialists from different parents combine into a new unit? Does the fail branch ("most strategies can work") count every context it tries? Do more research variants still help once live breadth comes from placement?

## Why it matters

Selection bias can move from backtests to journals to agent shortlists (playing-field cross-map row on L02-03). Contradictions C10 and C11 hang on this.

## Start from

- `research/16-fable-advice-system1-context.md` §1.3, §1.4, §4, §7.4 (shrinkage); `research/15-party-system1-context.md` ("context lift", the parent record).
- `research/05-academic.md` (deflated Sharpe, PBO, a stream of tests with a stop rule); `research/08-old-qmx-testing-and-decay.md` (CUSUM, about 240 trades); `research/11-papers-llm-quant.md` (tries per refinement).
- Stats `C:/Users/Mubarak/Desktop/Stats/lineage/` READMEs.
- Literature: empirical Bayes and hierarchical shrinkage, sequential probability ratio tests, multiple testing in strategy selection, survivorship bias.

## What would settle it

Options per question, each with the guard against luck it needs. A list of which questions can be measured today and which need QMB to stamp market state and results in R on every trade. Numbers named with starting defaults only.

## Output

`research/24-earning-a-specialist.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
