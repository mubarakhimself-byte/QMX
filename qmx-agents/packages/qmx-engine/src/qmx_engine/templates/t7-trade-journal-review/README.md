# Review each unit's day: what it traded, skipped and missed, and why

The slow lane's unit review (STATE midday ruling 44, Part B `workflows.md` section 3). Each morning a short note on every unit's day, read from its journal through `journal_query`. Scripts make every number, the writer explains them, and the receipts grader holds each number to the step that made it. The note lands as a proposal; nothing moves a unit.

Built from card T7 in `research/methodology/16-templates-trader-risk.md`, with its old read script replaced: it no longer waits for the trading node, because the records job files every unit journal home (B15).

## Steps

1. `Count each unit's day` (`scripts/read.py`) reads the unit journal's `digest` view for the UTC day. Per unit and per market it counts the decisions it traded (`taken`), skipped (`skipped`, `no_signal`, `suppressed_warming`) and missed (every other outcome: the unit wanted to act and something stopped it), with the journal's reasons, its trades and their R. Backfilled rows are left out and counted. It lands the counts as one `unit-review` artifact.
2. `Nothing to review?` sends a day with no rows straight to the land step with the script's own note: zero tokens.
3. `Write the review` (role `writer`) writes one paragraph per unit from those counts and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the note as a proposal` (`scripts/land.py`) lands one `note` artifact, marked `proposal: true`, on the run's own ref.

## Settings

- `day`: the UTC day, the day before the run by default. The cron runs at 00:15 UTC, after the 00:00 UTC day close that 24/7 markets use (WF-04). Missed runs follow the trigger's catch-up setting; reviews catch up once (WF-14).
- `units` and `world` narrow the review; every unit and every world by default.

## Left out, and why

- A note per unit per market session close, and every 10 closed trades: a cron trigger has no per-market clock, and an event trigger on the records job's landing has no payload naming the unit. One run reviews every unit's UTC day.
- Missed trades from `replay_check` diffs: the nightly live-day replay (`s5-live-day-replay`) runs them.
- The slice statistics and lessons of the old draft: they need many weeks of trades per slice, and the decay check (`dc-decay-and-limit-report`) owns the record over time.
