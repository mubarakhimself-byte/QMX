# Watch demo trades and check fill quality

The slow lane's unit review for demo units (STATE midday ruling 44, Part B `workflows.md` section 3, with `t7-trade-journal-review`). Each morning a short note on how every demo unit's fills went, read from the unit journal's `demo` world through `journal_query`. Scripts make every number, the writer explains them, and the receipts grader holds each number to the step that made it. It never acts on a unit.

Built from cards T5 and T9 in `research/methodology/16-templates-trader-risk.md`, with its old read script replaced: it no longer waits for the trading node, because the records job files every unit journal home (B15).

## Steps

1. `Count each demo unit's fills and trades` (`scripts/read.py`) reads the day's demo `fill` rows, and its `trade` rows with the market journal's minute beside each one. Per unit and market it counts fills, the sizing residue in R, trades and their R, stops a price gapped through, exits by kind, and trades with a market minute recorded. It lands the counts as one `fill-quality` artifact.
2. `No demo rows?` lands the script's own note on a day with no demo rows: zero tokens.
3. `Write the fill-quality note` (role `writer`) explains the counts and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the note as a proposal` (`scripts/land.py`) lands one `note` artifact, marked `proposal: true`, on the run's own ref.

## Left out, and why

- Partial fills: no fill row says a fill was partial. The gap between a fill's `receipt_quantity` (the sizer's ask) and its `quantity` is lot rounding, which the note reports as the sizing residue (`residue_r`).
- Slippage against the intended price and latency: the fill rows the node writes carry the price filled, not the price asked or the time asked, so a script has nothing to measure them against.
- The expectancy band from the backtest and a bench proposal on a drawdown: the band is a Library item a workflow script cannot read, and the decay check (`dc-decay-and-limit-report`) owns the record and its tighten cards.
- The trigger on every closed deal: a cron runs at 00:20 UTC on the day before.
