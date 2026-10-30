---
title: Research: how market-state systems are organised, and the shared-indicator question
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L03-02, L03-06, L04-03, L04-14, L03-25, L03-08, Q2, L03-09, L03-11, L03-21]
---

## Question

How do market-state systems group their sensors: by trading style, by timeframe, by data class (bars only versus order flow), by asset class, or by venue? One shared state vocabulary with sensors per class, or a separate set per class? When a unit's own rule uses an indicator the MIS also uses, is that double counting, or one primitive in two roles that makes the unit "already specific" (T2:216)? Who trains market-state models, how often, on whose data? Where do perps funding and market-physics measures fit? Which classes must the dictionary cover before perps and futures work? Can publishing labels change the behaviour they read, and can the MIS add noise rather than remove it?

## Why it matters

His seed: the MIS is shaped by trading style, then timeframe, then the data a market offers (STATE 10-29/30). Contradictions C18 and C19 are open. The Stats dictionary covers FX and crypto spot only (`research/19-grounding-old-system.md` §6 table).

## Start from

- `research/16-fable-advice-system1-context.md` §2, §3, §7.7; `research/19-grounding-old-system.md` §2 (STRATS `requires: mis.*.vN`, the single-computation rule), §6.
- `research/funnel3/cis/glossary-draft.md` entries "context", "market state", "instrument class".
- `research/18-grounding-today.md` §4 (six labelers, the regime pipeline); `C:/Users/Mubarak/Desktop/QMX/docs/glossary.md:556-558`.
- Seeds since this ticket was written: `research/funnel5-mis/party-brainstorm/mis-field.md` (three labels per reading: its alarm clock, time base and data level; look-back history; fallback steps; dispersion; the shuffled-readings test) and `research/43-convergence.md` (the MIS only points units at markets and is never needed to trade, a lead call, not a ruling). Treat both as seeds to test, not answers.
- `research/34-grounding-qml-and-dictionary.md` and `research/funnel4-qml/` (the dictionary is being rebuilt, role-neutral, far beyond FX; a reading is one more role).
- How quant shops share features across strategies (feature stores, factor libraries); regime-model practice.

## What would settle it

An options table, one row per grouping, with the evidence for and against and what breaks if it is chosen. A list of entries each instrument class needs. Worked examples of the shared-indicator case.

## Output

`research/23-mis-organisation.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).

## Resolution (2026-10-30)

One shared set of market words with sensors per class; features carry across assets, trained models do not; group by underlying market, not venue (research 23).
