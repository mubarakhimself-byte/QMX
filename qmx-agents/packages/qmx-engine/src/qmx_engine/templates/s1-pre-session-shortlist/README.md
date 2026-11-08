# Shortlist the markets before each session opens

The slow lane's pre-session shortlist (STATE midday ruling 44, Part B `workflows.md` section 3): before a market's session opens, which markets fit the units that trade them today, so he is not left "picking the luckiest". It is a read for him. Units trade their admitted markets on their own conditions whatever arrives (MIS-09), and nothing here changes a unit or a market.

## Steps

1. `Read the markets that open soon` (`scripts/read.py`) reads the units' closed trades over `record_days` through `journal_query` and finds each market they traded whose next session starts within `lead_minutes`, from the shipped calendar its class names: the calendar's next open while it is shut, the next `day_start_utc` while it is open. Only for those does it read the MIS's reading history through `readings_query`, whose holdout refuses a held-out window by name: today's words are the last each reading said, and each trade is set beside the words each reading said when it opened. A unit fits when its R under today's words is above zero. It lands the shortlist as one `shortlist` artifact.
2. `Nothing to shortlist?` lands the script's own note on a run with no opening market that a unit fits: zero tokens. Most half-hours are this.
3. `Explain the shortlist and make the calls` (role `writer`) explains each market and makes one dated direction call per shortlisted market.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number in the note the read step did not print.
5. `Hand on the dated calls` (`scripts/calls.py`) keeps the calls for shortlisted markets, each with its market's horizon from the read step, and `Land the calls in the forecast ledger` (the shared `forecast` block, carried in `forecast/`) lands them dated by the run's clock. The block refuses a call that could not be scored.
6. `Land the shortlist as a proposal` (`scripts/land.py`) lands one `note` artifact, marked `proposal: true`, on the run's own ref.

## Settings

Starting defaults, never caps: `lead_minutes` 30, `calendars` (`fx` and `metal` on `fx-24x5@1`, `crypto` on `crypto-24x7@1`), `day_start_utc` 00:00, `session_hours` 8, `record_days` 28, and `readings`, the MIS's default packs' reading ids. The cron runs every half hour in UTC and reads the calendars itself, so no session time is written here. A missed run catches up once, as every trigger does (WF-14), and reads the calendars at the run's own time, so a session already open is never shortlisted late.

## Left out, and why

- Scoring the calls: the `forecast` block's score step is ready, and needs the session's open and close read from the market's price series. A workflow script has no way yet to name a market's price series on This PC, so the calls wait in the ledger, dated, for a scoring template.
- The board (the MIS's `board` operation): it is an app operation, not a job, so a workflow's `app_op` cannot read it. Today's words come from the same reading history the board shows.
- A `shortlist` try per market in the try ledger: a workflow script cannot write try-ledger rows.
- The sessions inside a market's day (Sydney, Tokyo, London, New York): the shipped calendars hold a market's open and close, not those sessions.
