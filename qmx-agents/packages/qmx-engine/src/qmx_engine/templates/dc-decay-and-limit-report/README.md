# Decay check: each unit's recent trades against its own record

The slow lane's decay check (STATE midday ruling 44, Part B `workflows.md` section 3). Each night it reads every unit's closed trades in R through `journal_query`, judges the recent ones against the unit's own record before them, and says OK, Watch or Alarm. It informs only: each Watch and Alarm gets one tighten-only proposal card for his click, and nothing moves a unit (Level 0 AD-23: the action after an alarm is the risk session's).

Built from card R3 in `research/methodology/16-templates-trader-risk.md` and card P3 in `17-templates-dev-pm-lab.md`, with its old read script replaced: it no longer waits for the trading node, because the records job files every unit journal home (B15).

## Steps

1. `Judge each unit's recent trades` (`scripts/read.py`) reads the trades of the last `record_days` days and, per unit, compares the last `recent_trades` with the trades before them. Alarm when the recent expectancy falls to `alarm_at_r` or below while the record's is above it, or at `alarm_streak` losses in a row. Watch when it sits `watch_drop_r` or more below the record's, or at `watch_streak` losses in a row. A unit with too few trades on either side is listed as thin and not judged. It lands the judgement as one `decay-check` artifact.
2. `Nothing flagged?` lands the script's own note on a night with no Watch or Alarm: zero tokens.
3. `Explain each flagged unit` (role `writer`) explains each flagged unit from the script's numbers and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the note and the tighten cards` (`scripts/land.py`) lands the note and one `proposal-card` per flagged unit with ask `tighten`, each marked `proposal: true` and resting on the landed `decay-check` artifact.

## Settings

Every number is a card setting with a starting default, never a cap: `record_days` 90, `recent_trades` 20, `min_record_trades` 20, `watch_drop_r` 0.25, `alarm_at_r` 0, `watch_streak` 5, `alarm_streak` 8. The cron runs at 00:30 UTC, after the unit review.

## Left out, and why

- The baseline card from the unit's backtest and its Monte Carlo band: a workflow script cannot read Library items, so the record is the unit's own journal before its recent trades.
- CUSUM, win-rate, payoff, frequency and cost tests, and limit use against budget: the risk session settles the decay definition (Part B ARCHITECTURE-SPINE, the open-points table); these two rules are the starting form.
- The trigger every 10 closed trades: the records job's landing event names no unit.
