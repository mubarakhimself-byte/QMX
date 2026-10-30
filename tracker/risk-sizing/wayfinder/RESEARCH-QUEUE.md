# Research queue for Codex

Written 2026-10-30 with the map's re-chart. Fourteen open research tickets in six groups. One Codex run takes one group. He starts each run himself; nothing here runs on its own.

## How to start a run

Give Codex this, with the group letter filled in:

> Work group X of `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/wayfinder/RESEARCH-QUEUE.md`. Read `STANDING-ORDERS.md` and `STATE.md` in that folder first. For each ticket in the group, read the ticket file in `wayfinder/tickets/` in full and follow its "How to run it" section. Write only the output file each ticket names. Do not edit the tickets, the map or any code. Do not commit.

When a file lands, the lead reads it, closes the ticket with a one-line resolution and a pointer, and adds it to the map's Decisions so far. Codex does not close tickets.

## Order and groups

Suggested order: A to F. A is small and feeds the walkthrough he wants most. B unblocks the most grilling tickets. The rest follow by how much each unblocks.

### Group A. Inside a unit (small)

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: what self-configuring trading systems read and change](tickets/research-self-configuring-systems.md) | `research/20-self-configuring-systems.md` | the self-configuration prototype, then the risk socket |
| [Research: old-system loose ends (WF4, the pillars, the tick-data fix)](tickets/research-old-system-loose-ends.md) | `research/21-old-system-loose-ends.md` | the QML and dictionary ticket |

### Group B. The MIS

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: which market states a 1m or 5m scalper can use in time](tickets/research-mis-sensor-speed.md) | `research/22-mis-sensor-speed.md` | units and the MIS; how the MIS is organised |
| [Research: how market-state systems are organised, and the shared-indicator question](tickets/research-mis-organisation.md) | `research/23-mis-organisation.md` | the same two, plus the QML and dictionary ticket |

Through "units and the MIS", group B also opens the placement ticket and the node and PC split.

### Group C. Specialists and judging

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: earning a per-market specialist without luck](tickets/research-earning-a-specialist.md) | `research/24-earning-a-specialist.md` | System 1 and System 2, then expansion |
| [Research: when an earned specialist's market changes](tickets/research-specialist-drift.md) | `research/25-specialist-drift.md` | System 1 and System 2 |
| [Research: how quant desks judge and iterate without overfitting](tickets/research-quant-judging.md) | `research/26-quant-judging.md` | where default numbers come from |

### Group D. Money across units

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: how many independent bets a set of units really holds](tickets/research-correlation-and-bets.md) | `research/27-correlation-and-bets.md` | the correlation control |
| [Research: what a $300 account can trade, and whether breadth amplifies a weak edge](tickets/research-small-account-universe.md) | `research/28-small-account-universe.md` | what QMX does first; which instruments come first |

### Group E. Agents as analysts

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: how analysis agents are confidently wrong, and which checks catch it](tickets/research-agent-failure-modes.md) | `research/29-agent-failure-modes.md` | agent proof |
| [Research: how trading desks analyse markets and strategies, by style and rhythm](tickets/research-desk-analysis.md) | `research/30-desk-analysis.md` | which analyst workflows come first |

Group E's failure-mode study runs model calls. Use the cheapest model that can do the task.

### Group F. Live path, venues, data

| Ticket | Output | Unblocks |
| --- | --- | --- |
| [Research: the live path (node gaps, feed fan-out, time per step, first paper unit)](tickets/research-live-path.md) | `research/31-live-path.md` | the node and PC split; where default numbers come from |
| [Research: the slow broker and instrument facts a unit must have checked](tickets/research-terrain-and-venues.md) | `research/32-terrain-and-venues.md` | which instruments come first, then data recording |
| [Research: data depth per class, quality checks, and keeping downloaded history](tickets/research-data-depth-and-terms.md) | `research/33-data-depth-and-terms.md` | data recording |

## Two things every run needs to know

- Price data: the Library's partitions or Binance Vision. Dukascopy downloads need his go first (its site terms forbid bots and databases; STATE "For his awareness").
- Old Hermes logs and the old vault can contain credentials. Never print or copy them.
