# DC Decay and limit report

Waits for the trading node: its unit adapter and guard reader (`needs: trading-node`).

Built from card R3 (strategy decay detection) in `research/methodology/16-templates-trader-risk.md` and card P3 (decay and limit report) in `17-templates-dev-pm-lab.md`. Daily after the end-of-day wrap it tells real decay from bad luck per unit, flags units close to their limits, and drafts tighten-only cards. A loosening is never an option, and nothing changes without his click.

## Steps

1. `Load journals and baselines` reads each unit's journal in R and costs, its backtest baselines and Monte Carlo band, its term sheet's kill criterion, and its limit use.
2. `Decay tests and levels` runs the CUSUM, the rolling expectancy interval, the band, the win-rate, payoff, frequency and cost tests. Red needs a CUSUM breach, two failed tests or the kill criterion; amber is one failed test, ten trades outside the band, or a limit at 80%. Missing data reads "could not check". The definition is pluggable until the risk session settles it.
3. `Any amber or red?` wakes `Explain each flagged unit` (role `scanner`, the cards' cheap explainer) only when a unit is flagged.
4. `Tighten-only cards` gives every red unit a card: keep watching (the default), shrink within the declared range, back to demo, or bench.
5. `Render and grade` checks every number in the explanations against the journals and the tests.

## Left out, and why

- The event every 10 closed trades and the event when a limit reaches 80% of budget: the trigger is a daily cron until event triggers from the node exist.
- MIS hit-rate drift from the pre-session read and the regime label: they need the node's MIS state.
- Decay history per unit, linking a unit that died live back to its Lab family, and the Lab rehab loop: they need memory rows, the Library's lineage and the Lab.
- The `[SILENT]` digest line on an all-green day: the result is the run's output; notifications are UI-side.
- Test fixtures: they come with the node's read model, whose real shape they must match.
