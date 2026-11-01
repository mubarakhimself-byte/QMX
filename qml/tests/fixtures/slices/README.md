# Recorded slices for the dummy unit

The `synthetic-*.csv` files are **not evidence**. They are one synthetic month (2 to 28 March
2025) of EURUSD and XAUUSD M15 bars, bid and ask, written by `make_synthetic_month.py` from a
fixed seed. They let `test_compile_dummy.py` drive the dummy on every machine.

The real month is Dukascopy data saved outside the repo in
`D:/QMX-worktrees/unit-ship/data/dukascopy-node/` (March 2025, the same layout). Dukascopy data
is personal use only (`qmf.data.dukascopy.PERSONAL_USE_LICENSE`, `internal-only`), so it is
never committed. The real-data test reads it when the folder is there and skips otherwise.
