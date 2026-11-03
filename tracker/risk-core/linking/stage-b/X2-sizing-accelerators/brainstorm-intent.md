# X2 brainstorm intent: sizing, allocation, accelerators and costs

Source: `.memlog.md` in this folder (101 ideas, seven techniques, the roundtable). Full hybrids: `expansion/X2-sizing-accelerators.md`. Headless run; no ranking; the funnel judge picks.

## What the template should be able to express (the critical discoveries)

1. **A baseline amount derived from survival, not from the edge.** Per-trade risk = usable cushion ÷ (s × z × √H × √(N(1 + (N − 1)ρ))): his floor and touch tolerance, the unit's result spread with FI cuts, a horizon, the unit count and correlation. It trades at zero edge; the edge only relaxes it through a declared dial (zero, low, mid). Model sim: zero floor touches in all twelve cases, 2.8x the 1/N split's growth at equal safety (X2-H01, H02, H03).
2. **His two contradictions dissolve in that formula.** One working unit gets its full survival size; ten units get 1/√(N(1 + (N − 1)ρ)) each, which is his day-budget split corrected for breadth. Per-trade risk falls with √(trade rate) and daily growth rises with it.
3. **The GitBook ladder, house money, reverse house money and CPPI are one rule with a declared anchor.** Fixed anchor = brake-accelerator pair; trailing anchor = pure brake. The Book's $42.86 per R was 1/7 of the cushion: surviving about 7-10 trades at zero edge (X2-H10).
4. **Below baseline is probation, above baseline is acceleration.** Levels, titration and restores are brakes with a release; only tiers, persistence presses, pyramiding, calm-volatility boosts and fixed-anchor cushion leverage are accelerators, and each switches on only after a resize-replay proof card against an equal-average constant (X2-H13, H14, H18, H19, H20).
5. **A raise must leave headroom to the next trip.** Any brake blocks every raise; budget burn must be healthy; m full losses must fit before the nearest trip; remember the trip level; settle before the next change; a restore never crosses baseline (X2-H24, H15).
6. **Costs enter size in exactly three places:** the denominator, a cost-and-gap Kelly ceiling, and an edge-to-cost gate, per instrument, hour and world. Per-timeframe effects fall out of cost over stop. Session multipliers go (X2-H39, H40).
7. **Equity basis is four rows, not one:** size from committed cushion (lower of balance and marked), brakes on marked equity, accelerators on realised profit, the floor clip at worst case (X2-H44).
8. **Demo and live alike:** the deployment carries budget share, cost model and level; the demo balance is never read; the paper twin's gap prices live slippage (X2-H50).
9. **Feasibility first at $500:** admission depends on the minimum lot at the derived size, so the first units go to FX micro lots and crypto spot (X2-H45).
10. **Self-configuring = fixed formula, moving inputs:** each input has a learner with bounds, an applier mode, direction-split motion and a guard that falls back and freezes (X2-H51).

## Directions to carry into the funnel

- Strongest for performance: honest breadth sizing (H01, H02, H28), not accelerators.
- Strongest for survival: the N-1 and probable-maximum-loss reserve off the cushion before sizing (H07).
- Restructures: replace the ladder's price of R, April's nine multipliers, frozen paper balances, the 2.5x sweep cliff and session multipliers; widen the sizer contract.

## Unresolved, kept open

Zero-edge default against wasted edge (X2-C01); breadth against the minimum lot at $500 (X2-C02); automatic raises above baseline (X2-C12); house-money scope (X2-C04); missing cost cell, refuse or default (X2-C25).

## Only he can answer

ε (how rare "almost never" is); the first floor level; house-money scope; whether any rule may raise above baseline without his click; the ratchet share of new highs.
