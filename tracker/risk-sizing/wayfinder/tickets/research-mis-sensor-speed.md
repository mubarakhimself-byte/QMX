---
title: Research: which market states a 1m or 5m scalper can use in time
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L03-03, C9, Q20, Q21, Q22, L03-19, L03-07, L03-04, L03-05, L05-08, L03-22]
---

## Question

Which market states (trend or mean reversion, volatility against its usual level, spread and liquidity, tick rate, session, scheduled events) can be read fast enough to help a 1m or 5m scalper's trades, and which only as a session or daily list? Which fast proxies beat the slow reading (cross-section of many markets, higher timeframe, tick or volume bars, order flow)? Does order flow show mean reversion sooner where a venue has it, and what stands in for it on spot FX, which has no tape? Should a scalper's sensors be plain indicators and slower styles use models? Are Hurst, variance ratio and efficiency ratio sensors or a family of their own? Which sensor and venue combinations are impossible because the data does not exist?

## Why it matters

Research 15 and 16 found a trend or mean-reversion state takes about 8 hours to show on 1m bars. He objects: "you can put multiple indicators inside a scalper's MIS" (T2:216). Whether units can use the MIS per trade or only per session decides the tickets on units and the MIS and on how the MIS is organised.

## Start from

- `research/funnel3/cis/problem-solving.md` knot (a): 14 options and the morphological box.
- `research/16-fable-advice-system1-context.md` §1.2, §7.1, §7.10; `research/15-party-system1-context.md`; `research/05-academic.md` (information per bar).
- `research/02-instruments-and-traders.md` (which venues have depth or a tape).
- Stats context entries: `C:/Users/Mubarak/Desktop/Stats/dictionary/context-regime-and-intermarket/context-filters-confirmations.md`.
- Seeds since this ticket was written: `research/funnel5-mis/party-brainstorm/mis-field.md` (three labels per reading: its alarm clock, time base and data level; look-back history; fallback steps; dispersion; the shuffled-readings test) and `research/43-convergence.md` (the MIS only points units at markets and is never needed to trade, a lead call, not a ruling). Treat both as seeds to test, not answers.
- Literature on change-point detection, variance ratio, Hurst, efficiency ratio, order-flow imbalance, tick and volume bars.

## What would settle it

Per sensor and asset class: lag and false-alarm rate at 1m and 5m, measured on real data or taken from a cited study. A replay check of whether a label known at entry lifts results compared with the same label known only afterwards. A table of which knot (a) options survive and why.

## Output

`research/22-mis-sensor-speed.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
