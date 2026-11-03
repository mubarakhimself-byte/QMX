# Brainstorm intent: X0 trading lens

Headless run, 3 Nov 2026. Source of record: `.memlog.md` in this folder (71 entries: 7 technique switches, 60 ideas, 4 insights). Topic: the trading lens for the unit risk-and-sizing template, top-down (portfolio, then style and timeframe, then market structure), per instrument class. Goal: hybrids of Stage A components that set the frame the other layers hang from. Artifacts: intent only, as the brief asked; no HTML.

## What came out

- 55 hybrids, numbered X0-01 to X0-55, each linking two to nine components by id. Full write-up: `expansion/X0-trading-lens.md`.
- The frame: a matrix of three styles (scalping, intraday, swing) by seven instrument classes, where every cell answers five questions: the risk unit; what a stop and a fast-invalidation cut look like; how frequency shapes the brakes; what costs do to size; which accelerators can pay. Every other layer's default is a value in a cell of that matrix.
- Five variants were bred under one selection rule (survive half the believed edge, losing together, and a gap through the stop with brakes on, and still grow on the realistic case). Survivors: the effective-bets day split, money brakes at the unit's own percentile, per-logic stop choice behind a two-arm test, cut-only macro multipliers, the ORB family with the hours clause.
- The solution matrix showed nine empty cells (energy scalping, fast invalidation, pooling, house money's effect, caution widths, swing brake windows, style-boundary transitions, stock shorting, leverage jurisdiction).

## Assumptions made

- Component ids are shortened: `A1-070` means `A1-sizing-allocation-070`, `A2-` is brakes-drift-exits, `A3-` is structure-regimes-scenarios, `A4-` is template-agents-telemetry, `A5-` is topup.
- No human was available; every role (brainstormer, problem-solver, roundtable personas) was played by the agent, as the brief instructed.
- The memlog's "status" is recorded as an entry, not as frontmatter, as the script's own design requires.

## Status

```json
{"status": "complete", "intent": "brainstorm", "memlog": "linking/stage-b/X0-trading-lens/.memlog.md", "intent_doc": "linking/stage-b/X0-trading-lens/brainstorm-intent.md", "assumptions": ["component id short form", "all roles played by the agent"], "external_handoffs": []}
```
