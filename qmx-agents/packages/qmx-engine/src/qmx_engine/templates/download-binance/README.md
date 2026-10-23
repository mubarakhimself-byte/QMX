# Download Binance bulk files

One run, one partition: a dataset, a symbol and a month, landed through the market-data door's
`commit`. The series key is `binance / <symbol> / <kind> / <variant> / <YYYY-MM>`.

| dataset | kind | variant |
|---|---|---|
| `trades` | `trades` | `-` |
| `aggTrades` | `trades` | `aggTrades` |
| `bookDepth` | `book` | `depth` |
| `bookTicker` | `book` | `ticker` |

## What a run does

1. Claims the partition key with an `O_EXCL` file under the store root.
2. Reads every day of the month from `data.binance.vision`, each zip with the `.CHECKSUM`
   published beside it. A file that does not hash to its checksum **refuses the month**: it is
   never read as a month with fewer rows (probe P-BAN's stub and this check are the two guards
   on the bulk path). A day the bucket does not serve stops the month too, with the day named.
3. Decodes the rows to the kind's columns: a trade print is `(t, price, volume)` at eight
   decimals read through `Decimal`, a book level `(t, value, volume)`.
4. Checks free disk, stages `<root>/staging/binance/<symbol>/<kind>/<variant>/<YYYY-MM>.parquet`
   and commits through the door.
5. Writes the series card's fields as `library/cards/<series>.json`, carrying the checksum
   policy and the day count.

## The kind registry

The store's freeze rules live in `qmf.data.series` (`FD/series.py`), which this PR's files do not
name. It declares `ticks`, `bar-m1` and `fill`; it declares no `trades` and no `book` row. Until
those rows exist, this template refuses to land with a message naming that file, because the
alternative is a two-column partition that silently drops the price and the size. The refusal is
the honest state, and it is in `findings-backlog.md`.

## Binance's own limits

Binance limits per client address, so the connection's slowdown wait is shared per egress
address (`qmx_broker.registry.Slowdowns`, AD-67). Probe P-BAN holds two connections to one
address against a stub that answers `429` then `418`, and neither may send inside the wait.
