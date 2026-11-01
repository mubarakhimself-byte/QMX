# Refresh crypto instrument records

Writes one `instrument` record per market and one `venue` record per exchange from CCXT's public
market lists for Hyperliquid and Binance. It needs no key and reads no account (Part C AD-312,
RECORDS.md section 4: venue API facts daily).

## What a run does

1. Reads each exchange's markets with `load_markets` and, where CCXT offers it, the funding
   intervals with `fetch_funding_intervals`. With `{"fixture": true}` it reads
   `fixtures/<exchange>.json` instead, hand-written market lists in CCXT 4.5.85's unified shape.
2. Turns each perp, dated future and spot market into the `instrument` kind's fields: tick size
   and digits, contract size and value per point, lot step and limits, leverage and margin where
   the list states them, the funding interval and its source for a perp, the expiry, root and
   next month for a dated future, and the data levels in `qmx.data-level/1`.
3. Writes them under `library/instruments/` and each exchange's facts under `library/venues/`,
   and reports per exchange what it wrote, what it skipped and why, and the seconds it took.

## Left out, and why

- Inverse contracts and options are skipped and counted by reason: an inverse contract's money
  per price unit is not constant in its quote currency, and no record class here is an option.
- Binance states no leverage on its public market list (its leverage brackets need a signed
  call), so its records carry no `leverage` or `margin`, and the checker names the missing fact.
- A linear contract's value per point is its contract size, and these exchanges state no second
  figure to check it against, so `conversion_check` records one way and `agrees` is null.
- An exchange that fails fails the step, so the records last landed stay in force.
- The exchange's own rate limit is the exchange's: the run adds no QMX limit.
