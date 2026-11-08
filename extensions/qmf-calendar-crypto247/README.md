# qmf-calendar-crypto247

The around-the-clock crypto calendar as versioned data, with each venue's funding clock. An
instrument record names it as `crypto-24x7@1`, and the workflow engine's
`market_open:<market_id>` precheck reads it as always open, Saturdays and Sundays included.

## Funding clocks

| Venue | Every | From (UTC) |
| --- | --- | --- |
| `hyperliquid` | `PT1H` | 00:00 |
| `binance` | `PT8H` | 00:00 |
| `bybit` | `PT8H` | 00:00 |
| `okx` | `PT8H` | 00:00 |

A clock is the default for its venue. An instrument record's own `funding_interval` wins for a
contract that pays on another interval.

## The data

`src/qmf/calendar_crypto247/calendars/crypto-24x7@1.json` is one `qmx.calendar/1` document:
`sessions` is `"always"`, `closures` is empty, `funding` lists the clocks, and `issued` with
`max_age_days` (31) dates it. A changed rule is a new version file.
