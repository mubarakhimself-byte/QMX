# T3 News and macro calendar watch

Built from card T3 in `research/methodology/16-templates-trader-risk.md`, script-first. Every day at 00:05 UTC it reads the day's economic calendar and builds the calendar strip for the watchlist: each release that touches a watched currency, a blackout window around each high-impact release, and one alert line per high-impact release or surprise, each with its source link. Only a surprise costs tokens: one cheap note from the `scanner` role on what moved and what it means.

## Steps

1. `Calendar changed?` is a monitor on `scripts/calendar.py`, the zero-token pre-check. It wakes the rest only when the calendar changes.
2. `Calendar strip` maps currencies to the watchlist, sets the blackout windows (30 minutes either side of a high-impact release), and scores each release with an actual: a miss of 1.5 typical misses or more is a surprise, at most 10 a day.
3. `Any surprise?` sends a quiet day straight to the check, with no model call.
4. `Surprise note` (role `scanner`) writes two lines per surprise; `Add the notes` puts them in the strip.
5. `Render and grade` (the shared `render-and-grade` block) checks the strip against `schemas/output.json`, every alert's source link, and every number in the notes against the strip. A failed check stops the run as failed. `Deliver` hands on the strip as the run's result.

## Watchlist and guard

The watchlist is static, `EURUSD` and `USDJPY`, in `scripts/strip.py`. It stands in for the active units until the trading node exists. The guard cross-check reads `could not check: trading node` for the same reason.

## Test runs

A run started with `{"fixture": "quiet"}` or `{"fixture": "surprise"}` replays the matching synthetic day in `fixtures/` instead of the network. Install tests the template on the surprise day on real models, so the note step is tested; the quiet day makes no model call. The answer in `fixtures/recorded/` serves the `--fake` switch.

## Left out, and why

- Live actuals: the free calendar at nfs.faireconomy.media gives forecasts and previous values only, so a live run lists the day and its blackouts and finds no surprise until a source with actuals is added.
- Official central-bank and statistics-agency feeds cross-checked against the aggregator: one source is wired.
- Event fires at T-30, T-5 and T+1 minutes per release: the engine does not create per-event trigger rows from a template yet.
- Headline RSS every 2 minutes during sessions, and the urgent push on an unscheduled move: no headline source or push channel is wired.
- Blackout windows from each unit's conditions and the account's prop-firm news rule: those live with the trading node.
- Surprise history per series for the z-score: the typical miss comes with each release in the fixture; workflow memory rows are not used yet.
- The 06:00 "calendar missing" alert: it needs an urgent alert channel.
