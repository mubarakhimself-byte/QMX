---
title: Research: earning a market's own version of a unit without luck, and noticing when that market changes
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L02-02, L02-03, L02-09, L02-16, L02-12, Q64, Q27, Q76, Q73, L10-06, Q16, L02-04, Q24, Q25, L08-08, L15-05]
---

## Question

"System 1" and "System 2" were explanation names, not QMX terms (his 30 Oct correction). Here: a unit runs one logic broadly, and a market's own version (its own settings, and before live possibly its own logic changes, his 28 Oct "enhancing different logics for different markets") is earned from the record the broad unit built on that market (his Path A ruling, `STATE.md:120`). How is that done without luck? Is the market chosen before or after its trail is read? Is a "wins broadly" test still needed? Is "broad" judged on one pooled read or per market, and what does each cost in tries? Can a sequential test replace a fixed trade count? Do retired children's trades stay in the parent's record? Do paper runs on unadmitted matching markets count as evidence or as tries? Can two specialists on correlated markets come from what is really one trail? Can specialists from different parents combine into a new unit? Does the fail branch ("most strategies can work") count every context it tries? Do more research variants still help once live breadth comes from placement?

Merged from the drift ticket (earning and expiring share one clock): how does an earned version notice that its market changed after it was earned, and what are the options then? Can a short backtest on QMX's own recorded live data (a week, a month) add evidence, or is it too short (his "backtesting across a week makes no sense. Unless I'm wrong", T2:216)? How long is "no rush" before a version is earned? What is the shortest window of QMX's own data worth testing on? Drift detectors with their lag in trades.

## Why it matters

Selection bias can move from backtests to journals to agent shortlists (playing-field cross-map row on L02-03). Contradictions C10 and C11 hang on this.

## Start from

- `research/16-fable-advice-system1-context.md` §1.3, §1.4, §4, §7.4 (shrinkage); `research/15-party-system1-context.md` ("context lift", the parent record).
- `research/05-academic.md` (deflated Sharpe, PBO, a stream of tests with a stop rule); `research/08-old-qmx-testing-and-decay.md` (CUSUM, about 240 trades); `research/11-papers-llm-quant.md` (tries per refinement).
- Stats `C:/Users/Mubarak/Desktop/Stats/lineage/` READMEs.
- `research/43-convergence.md` (the edit type decides "new unit"; a market's own settings earned from that market's record) and `research/44-review-of-convergence.md` (the lead's ruling that per-market logic changes are included).
- `research/12-data-feeds-lookback.md` (QMX recording its own data, the market journal).
- No sizing maths: anything about stakes or budgets goes to the risk session (`RISK-SIZING-PACK.md`).
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

## Resolution (2026-10-30)

Path A's remaining luck trap is picking the best-looking market; judge every market by one rule and shrink toward the unit's pooled result. A week of own data checks costs and replay fidelity, never an edge (research 24, sims in `research/24-study/`).
