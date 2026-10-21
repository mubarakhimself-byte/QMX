# Watch demo trades and check fill quality

Waits for the trading node: its deal feed and unit adapter (`needs: trading-node`).

Built from cards T5 (paper and demo trading monitor) and T9 (execution quality check) in `research/methodology/16-templates-trader-risk.md`. It watches each demo unit against what its backtest promised, catches behaviour faults early, and measures what fills really cost against what the backtest assumed. It never acts on a unit: a bench is a proposal for his click.

## Steps

1. `New deals?` is a monitor on `scripts/deals.py`, the one read: new closed deals joined to the intended price and the quote at signal time, the R journal, the backtest's Monte Carlo band, the unit's sessions, blackouts, expected risk, maximum spread and assumed cost.
2. `Stats and costs` gives trades, expectancy in R with a 90% bootstrap interval, win rate, average win and loss, drawdown, trades per day, cumulative R against the band, worst slippage, median latency and the cost ratio over the last 50 trades.
3. `Faults, band and cost rules` lists behaviour faults, the band verdict, amber and red cost levels, and a bench proposal on a drawdown of 8R or two faults in a day.
4. `Out of band?` wakes `Candidate causes` (role `synthesiser`, the card's analyst) only for a unit outside its band.
5. `Unit tiles` and `Render and grade` check every number the causes cite against the deals and the stats.

## Left out, and why

- The trigger on every closed deal and the 15-minute heartbeat during each unit's sessions: the trigger is a cron until event triggers from the node exist.
- The automatic bench on demo through the tighten interface: no template acts on a unit or the node; it stays a proposal.
- The urgent "demo unit unobserved" alert after three failed reads, the cap of two explanations a day per unit, and the `evidence_ready` event for the promotion pack: they need alerting, memory rows and event triggers.
- The live cost model per instrument, hour and order type, and the broker comparison: workflow memory rows and a second broker are not there yet.
- Test fixtures: they come with the node's read model, whose real shape they must match.
