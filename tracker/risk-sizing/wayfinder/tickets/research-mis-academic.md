---
title: Research: what academic work says about market-state systems, per style, timeframe, data and asset class
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [his 30 Oct ask: "let's also look at academic research specifically... a lot of research towards the MIS variants"]
---

## Question

What does the academic and serious practitioner literature (arXiv q-fin, SSRN, journals, central-bank and exchange research) say about reading market state, organised the way he seeded it: first by trading style (scalping, intraday, swing), then by timeframe or bar type (seconds, 1m, 5m, 15m to 4h, tick and volume bars), then by the data a market offers (price only; price and real volume; order book; trades tape; open interest and funding), then by asset class (FX, gold, indices, futures, crypto spot, perps)? For each cell: which methods are tested (indicators, statistical tests such as Hurst, variance ratio and efficiency ratio, change-point methods, hidden Markov and switching models, volatility models, order-flow imbalance, market-microstructure and "market physics" measures, ensembles), on what data, with what out-of-sample evidence, lag and false-alarm behaviour? Where do the papers disagree, and which cells have no serious evidence at all? Do any studies show that the market-state reading itself reveals tradeable inefficiencies (his 28 Oct point), and is that a source of units?

## Why it matters

The MIS was designed in conversation, then judged slow by Fable and party mode. He asked for the academic side of the MIS specifically, so its contents come from evidence per style, timeframe, data and class, not from the lead's opinion. The two MIS grilling tickets and the QML and dictionary ticket wait on it, beside research 22 and 23.

## Start from

- `operator/transcript-2026-10-20-to-28.md` from his 28 Oct dictations (after the second explainer site) to the end, and `operator/transcript-2026-10-29-to-30.md`: his words on the MIS, the style, timeframe and data ordering, and the "models vs indicators" question.
- `research/05-academic.md` (detection limits), `research/11-papers-llm-quant.md`, `research/16-fable-advice-system1-context.md` §1.2.
- Seeds since this ticket was written: `research/funnel5-mis/party-brainstorm/mis-field.md` (three labels per reading: its alarm clock, time base and data level; look-back history; fallback steps; dispersion; the shuffled-readings test) and `research/43-convergence.md` (the MIS only points units at markets and is never needed to trade, a lead call, not a ruling). Treat both as seeds to test, not answers.
- `research/19-grounding-old-system.md` §2 (the old HMM, BOCPD, MS-GARCH ensembler and market physics).

## What would settle it

A matrix: rows = style × bar type, columns = data class × asset class, each cell listing the methods with evidence, the citation, the sample and period, the out-of-sample result, and the stated lag. A list of empty cells. A list of method families that recur across cells (candidates for one shared sensor library) and those that only make sense in one cell.

## Output

`research/37-mis-academic.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in the verbatim transcripts, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Papers: read the paper itself (arXiv abstract and PDF pages through Exa), not a blog about it. Search in several framings; a single query misses most of the field.
- Label every claim CHECKED (URL) or INFERRED; take each paper's results as that paper's claim, note costs, sample and look-ahead risks.
- Never read, print or copy keys, tokens or passwords.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute.

## Resolution (2026-10-30)

49 sources sorted by style, data and class; 11 empty cells; published patterns lose about 58% after publication (research 37, Claude agent 30 Oct).
