# P2 Daily book report

Waits for the read-only broker token he makes himself (`needs: broker-read-token`).

Built from card P2 in `research/methodology/17-templates-dev-pm-lab.md`. Script-only, zero tokens. Weekdays after the last session close it shows what the book did and where it stands against its budgets. It reads money and never moves it: no broker credential is held or named here, and no step can trade.

## Steps

1. `Preflight and broker reads` checks that broker reads answer and today's journals are updated, then reads positions, today's closed trades, the account, and the paper units' bands. A failed preflight retries on the 5, 15 and 30 minute ladder, then the run parks.
2. `Book report` computes equity, PnL in R and USD per unit, exposure by instrument and currency, drawdown against the loss budget and the kill line, and paper units inside or outside their band. Guard fields read "could not check: trading node", as the design says.
3. `Render and grade` checks the card against `schemas/output.json`.

## Left out, and why

- The "explain this" button that wakes the copilot: a UI concern.
- Daily snapshot rows for the decay report: workflow memory rows are not used yet.
- Correlation of today's moves: one day of moves says little; RK2 owns correlation.
- Test fixtures: they come with the broker reads, whose real shape they must match.
