# RK2 Correlation and exposure drift

Waits for the trading node: its unit adapter and guard reader (`needs: trading-node`).

Built from card R2 in `research/methodology/16-templates-trader-risk.md`. Every hour it catches the book quietly becoming one bet, for example three USD-short units all leaning risk-on. Agents never touch the guard: any change, even a tightening, is a proposal he signs.

## Steps

1. `Read the book` reads each unit's open risk by instrument, 60 days of daily R, time in trade, the promotion baselines and the guard's per-currency limit.
2. `Exposure, correlation and drift rules` turns positions into currency legs in R, computes the correlation and overlap matrices and the effective number of bets, and trips on a pair drifting more than 0.3 from baseline, effective bets down more than 25%, or one currency above the guard's limit. A unit with too little history counts as fully correlated.
3. `A rule tripped?` wakes `What drives it` (role `synthesiser`, the card's analyst) only on a trip; it names the driver and proposes one tightening.
4. `Drift card` and `Render and grade` check every number the analyst cites against the book and the exposure.

## Left out, and why

- The event on each position change and the full daily run after the wrap: the trigger is hourly until event triggers from the node exist.
- Storing a baseline matrix at each promotion: the promotion pack (PP) and workflow memory rows come first.
- The guard proposal card as an inbox decision: decision cards are a later packet; the proposal is the run's result.
- Test fixtures: they come with the node's read model, whose real shape they must match.
