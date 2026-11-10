# The practice month's bars

These four files are the one synthetic month of March 2025 that QML's own tests drive, saved
under dukascopy-node's names for EURUSD and XAUUSD, 15-minute bars, bid and ask.

They are **not evidence**. `qml/tests/fixtures/slices/make_synthetic_month.py` writes them from a
fixed seed, and these files are byte copies of its output with the `synthetic-` prefix dropped.
The real month is Dukascopy data, personal use only, and is never committed.

`qmx_host.practice_start` copies them into an empty market store as source `practice`, one
`bar-m1` piece per bar inside its own 15-minute bucket, so a first backtest needs no broker and
no download. The `practice` venue in RC-19 replays the same series for the paper lane.

To regenerate the month, run `uv run python qml/tests/fixtures/slices/make_synthetic_month.py`
and copy its output here again.
