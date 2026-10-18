# GW Guard watchdogs

Waits for the trading node: its read-only guard reader (`needs: trading-node`).

Built from cards R1 (kill-line distance watchdog) and R6 (tighten-only self-tuning check) in `research/methodology/16-templates-trader-risk.md`. Script-only: no model node, zero tokens. Every 5 minutes it reads the account and the guard, works out how far the account is from its kill line and its daily loss budget counting what open positions could still cost, checks that the guard is alive and configured as signed, and proves that every unit's self-tune stayed tighter or inside what he signed. The guard acts. GW only watches and tells; no step writes to the guard or the node.

## Steps

1. `Read account and guard` (`scripts/guard.py`) is the one read: equity, kill line, budgets, open positions, slippage and gap allowances, the guard heartbeat and config hashes, and each unit's profile versions with its signed profile and the direction table.
2. `Kill-line distance` computes the cushion, its worst case, the budget distances and the distance in R, and sets green, amber, red or black.
3. `Tighten-only check` marks black any change that loosens a parameter without a signature, or leaves its signed range.
4. `Gauge and alerts` writes the gauge and one alert line per finding. `Render and grade` checks every number in the alerts against the gauge.

## Left out, and why

- A 30-second monitor while risk is open and an event on each equity update: the trigger is a 5-minute cron until interval and event triggers from the node exist.
- The push on red and black, and the engine watchdog that pushes "kill-line watchdog down" when GW is late: notifications are UI-side (ruling 77) and that watchdog is engine work.
- The day's minimum cushion for the wrap and alert dedupe by signature: workflow memory rows are not used yet.
- Loosen cards and incidents for R8: they come with the inbox's decision cards and RK8's trigger.
- Test fixtures: they come with the node's read model, whose real shape they must match.
