# Download Dukascopy ticks

One run, one partition: a symbol and a month of ticks, written whole or not at all and handed to
the market-data door's `commit` (Library AD-28). The series key is
`dukascopy / <symbol> / ticks / - / <YYYY-MM>`, which is the key DR3C's importer wrote, so the
first real download continues the same series instead of starting a second one.

## What a run does

1. Claims the partition key: a `.claims/` file created with `O_EXCL` under the store root. A
   second run on the same key reports `claimed` and writes nothing.
2. Fetches the month's hourly files from `datafeed.dukascopy.com`, eight at a time, caching each
   hour that answers under the workflow's shared work folder so a re-run resumes. A refusal is
   retried on a **fresh** connection, and an hour still refused after its retries stops the
   month: a refused hour is never read as an hour with no ticks.
3. Checks free disk against `[data] disk_floor_gb` (Claude's default 3 GB) before it writes.
4. Writes the month's rows with the typed writer (`t`, `bid`, `ask`, `bid_volume`,
   `ask_volume`), stages them as
   `<root>/staging/dukascopy/<symbol>/ticks/-/<YYYY-MM>.parquet`, and commits through the door.
   The store decides the file's name and fingerprint; the open month is replaced, a frozen month
   takes a different file only as a correction.
5. Writes the series card's fields as `library/cards/<series>.json` and labels the volume:
   **Dukascopy's volume is Dukascopy's own liquidity**, its book, not a consolidated tape.
6. Keeps `logs/download-dukascopy.json` current on its own thread while it runs, so the Machines
   list shows the hour count and the partition in flight.

## The fetcher

QMX's own, through `qmf.data.dukascopy`. Probe P-DUKA failed: `dukascopy-node` 1.50.0 fetches
nothing (the provider answers `202` with an empty body), while QMX's fetch agrees with the
operator's old raw bi5 files on every hour the provider served. The fallback is in force, so the
node is not what this template runs. `qmf.data.dukascopy.decode_node_csv` keeps the node's own
output readable for the cross-check adapter.

## Left out, and why

- `[data] root`, `[data] seal_boundary_ns` and `[data] placement` come from the home's settings;
  a home that names no root fails rather than writing somewhere else.
- The card's Library item is written by the series-card writer outside this template; the run
  emits the same fields (`qmx_library.cards.card_fields`) as its artifact.
