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

The store's freeze rules live in `qmf.data.series`. `trades` and `book` are rows there: a trade
row is `t`, `price`, `volume`, a book row `t`, `value`, `volume`, and both freeze on a checksum,
which is how a bulk month closes, since the bucket published a digest for every file it served.
The decoder's columns come from those same constants, so the door's re-streamed commit and the
decoder agree by construction. The script still refuses if the two ever drift, naming both column
lists.

## Binance's own limits

Binance limits per client address, so the connection's slowdown wait is shared per egress
address (`qmx_broker.registry.Slowdowns`, AD-67). Probe P-BAN holds two connections to one
address against a stub that answers `429` then `418`, and neither may send inside the wait.
