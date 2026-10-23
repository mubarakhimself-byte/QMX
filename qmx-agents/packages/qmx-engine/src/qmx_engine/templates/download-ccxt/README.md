# Top up recent crypto days

The fallback for the days a bulk file has not been published for yet: CCXT reads the exchange's
own public API for one minute bars, and the month lands through the market-data door's `commit`.

## What a run does

1. Claims the partition key `<exchange> / <symbol> / bar-m1 / trade / <YYYY-MM>` with an `O_EXCL`
   file under the store root.
2. Asks the exchange for the month's bars, one thousand at a time from the month's start.
3. Checks free disk, stages `<root>/staging/<exchange>/<symbol>/bar-m1/trade/<YYYY-MM>.parquet`
   and commits it through the door. The bar month freezes on the store's checksum rule and takes
   its one re-fetch when the provider's file arrives.
4. Writes the series card's fields as `library/cards/<series>.json`, saying the bars are
   trade-built from the public API and not a one-sided quote series.

A bulk file replaces this month when it is published, which is why the card's `quality` says so
and why the partition is marked redownloadable.

## Left out, and why

- A run that finds no bars in the month writes nothing and reports `empty`; it does not write a
  zero-row partition.
- The exchange's own rate limit is the exchange's: the run does not add a QMX limit (ruling 106).
