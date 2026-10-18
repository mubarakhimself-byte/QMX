# T4 Research desk overnight

Built from card T4 in `research/methodology/16-templates-trader-risk.md`. Sunday to Thursday at 03:00 London, before the desk brief, a desk of analysts reads the night's news for the watchlist in chunks, code applies the cut rules, and a coordinator writes a ranked brief: HIGH, MEDIUM, CALENDAR, POSITIONING, CROSS-ASSET, and what was cut and why. Every line carries the links of the claims it rests on and a label, retrieved or inferred. No source, no claim.

## Steps

1. `Anything new?` is a monitor on `scripts/news.py`, the zero-token pre-check. It reads the Fed, ECB and Bank of Japan press feeds from the last 24 hours and today's high-impact releases, and wakes the desk only when something changed.
2. `Watchlist items` keeps the items that touch a watched currency (`EURUSD` and `USDJPY`, static until the trading node exists). With none, `Desk: nothing new` writes the brief the desk brief reads as "desk: nothing new".
3. `Analyse each chunk of news` (role `searcher`) runs one analyst per chunk of 6 items. Each claim names an instrument, a direction, a quote copied from the item, a label and a mechanism.
4. `Quotes check` (the shared citation grader) fails the run if any quote is not in its item.
5. `Cut rules` is code, not the coordinator's discretion: one item behind a claim is cut, unless it is a scheduled tier-one release or a positioning reading of 5 standard deviations or more; two items agreeing make it HIGH. Every cut names its analyst and why. Claim ids and analyst names are letters (`ca`, `analyst A`), because the grade reads every digit in the brief's prose as a number that must come from the news.
6. `Coordinator` (role `synthesiser`) ranks the surviving claims into lines. `Every line sourced` fails the run if a line rests on no kept claim, sits in the wrong section, or a HIGH claim is left out.
7. `Ranked brief` adds each line's links and turns HIGH lines with a mechanism into hint-card proposals, parked and not written to the Library. `Render and grade` checks the brief against `schemas/output.json` and every number in its prose, its cuts and its hint cards against the news items themselves.

## Test runs

A run started with `{"fixture": true}` replays `fixtures/news.json`, a synthetic night of sixteen items; fourteen touch the watchlist, make three analyst chunks, and leave fourteen kept claims. `fixtures/recorded/` holds the answers for the `--fake` switch and the unit tests.

## Roles

The card's analysts are the `searcher` role and its coordinator is the `synthesiser` role, the nearest roles in Settings. Roles come from Settings; no model is named here.

## Left out, and why

- Beats (c) to (f) live: CFTC COT and broker retail sentiment, technical structure from price data, DXY, yields, oil and equities, and headline volume against a baseline. Only the central-bank feeds and the calendar are wired; the fixture night shows what the other beats add.
- The coordinator as an agent that may do a failed beat itself, and the doctor's retry on the next model tier: the coordinator is one `llm` call over the kept claims, and a failed chunk retries once.
- Ranges with 90% coverage for forecast numbers: the coordinator forecasts no number, so every number in the brief traces to a news item.
- The last brief and the per-beat lessons (repeats skipped, known false positives): workflow memory rows are not used yet.
- The model-tier floor in Settings and reserve-then-refund budgeting: the runaway guard caps tokens, chunks and wall time instead.
