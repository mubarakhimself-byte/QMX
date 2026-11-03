# Brainstorm intent: X4 scenario catalogue (Stage B, headless)

Topic: the scenario catalogue for the unit risk-and-sizing template: families F to M, the combinations, and the harness that runs every scenario against every template version. Goal: hybrids for the template, every scenario with every brake, exposure rule and drawdown rule switched on. Mode: headless, intent artifact only (no HTML, per his M31). Memlog: `.memlog.md` beside this file.

## What came out

- 52 new scenarios (38 to 89) in eight families: costs and execution, infrastructure, units and agents, edge and regime, account and capital, operator, instrument-specific, and eight combinations. Each states what every level does, which brakes, accelerators and ledger variables engage, what correct looks like, what a simulation must prove, and a likelihood and severity.
- The harness (90) with its parts: scenario as data (96), the scorecard (97), reverse stress (98) and the interactive bench (99); and the five design ideas the draft leaned on: the event window (91), same bet by bet key (92), effective units (93), the isolation lifecycle (94), sectoring (95).
- Ten problems with at least two options each, sixteen collisions, nine restructure proposals, eleven gaps, four questions for him.

## Techniques, and what each produced

Morphological Analysis gave the family grid and the empty cells (infrastructure, operator, capital boundary acts). Concept Blending gave the event window, the harness as a release gate, the priced re-seed and slow start after every version. Forced Relationships gave the settling time before the next change, the tick-order rank and the account lease. Cross-Pollination gave pages with deadlines, the mandatory scenario set, the per-instrument grid, burn rates and the precision record. Trait Transfer gave the per-product pause with a market-wide stop, tier dwell, and cut fast grow slow. Evolutionary Pressure culled every "correct outcome" that survived by trading less or by leaning on the edge number. The Solution Matrix wrote Part 5.

## The directions that matter

1. The harness runs QMX's own brakes inside every scenario path and backtests itself nightly; the bare sim stays as the zero-brake row.
2. Near the floor the brakes are not the defence; feasibility is.
3. Everything that waits for his click needs an absence policy with a conservative default.
4. Accumulation per shared dependency is a survival gate of its own and the argument for a second venue and feed.

Deliverables: `expansion/X4-scenarios.md`, `ledger/additions/X4-scenarios.yaml`.
