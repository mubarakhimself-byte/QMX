# Tag each unit to the markets its record holds on

The slow lane's weekly market tags (STATE midday ruling 44, Part B `workflows.md` section 3). Each Sunday before Asia opens it reads each unit's record on every market it trades, with the MIS's reading states beside each trade, and proposes dropping a market whose record has fallen to the drop line. Every proposal is a card for his click; nothing changes a unit's markets.

## Steps

1. `Read each unit's record per market and reading state` (`scripts/read.py`) reads the lookback's closed trades through `journal_query`, and each traded market's reading history through `readings_query`, whose holdout refuses a held-out window by name. Each trade is set beside the word each reading said last before it opened. It prints, per unit and market, the trades, their expectancy and total in R, and the trades and R under each word, and lands them as one `market-tags` artifact.
2. `No market to drop?` lands the script's own note on a week with no proposal: zero tokens.
3. `Explain each proposal` (role `writer`) explains every proposal from the script's numbers and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the note and the market cards` (`scripts/land.py`) lands the note and one `drop_market` card per proposal, naming the market, each marked `proposal: true`.

## Settings

Starting defaults, never caps: `lookback_days` 28, `min_trades` 20, `drop_at_r` 0, and `readings`, the MIS's default packs' reading ids. The cron runs Sunday at 20:00 UTC, before the Sydney session opens.

## Left out, and why

- Admit proposals: admitting a market rests on a backtest of the unit there, which `u1-run-on-every-market` runs and judges.
- The judge's shrunk verdicts per market and a `paper_pick` try per proposal: a workflow script cannot read Library verdicts or write try-ledger rows. The record here is the unit's own journal.
- Scoring the tags at Friday's close: the record the next Sunday's run reads is the score.
