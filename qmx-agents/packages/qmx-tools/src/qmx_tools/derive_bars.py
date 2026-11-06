"""Fold a landed tick month into its `bar-m1` bid and ask months, through the market door (R09).

A run reads a month's bid and ask minute bars before its ticks, because a month holds about 30,000
of them against millions of ticks. This is the door's derived-data step: it reads the tick month
through `materialise`, folds each side at the month's own integer scale, and commits both sides as
`<source>/<subject>/bar-m1/bid` and `/ask`. The same ticks fold to the same rows, so a rerun lands
the same fingerprints and only lets the month freeze.

`materialise` copies a sealed month into a folder it is given, so a holdout does not stop a download
deriving. The bars land sealed too, because a seal reads the month and not the series.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Final, cast

import pyarrow.parquet as pq  # pyright: ignore[reportMissingTypeStubs]
from qmf.core import Ok, Result, is_refusal
from qmf.data.series import BAR_KIND, TICKS_KIND, CommitReceipt, SeriesKey
from qmf.data.store.engines.typed import BAR_COLUMNS, TICK_COLUMNS, TypedWriter
from qmf.data.store.refusals import invalid_input, missing_artifact

if TYPE_CHECKING:
    from qmx_host.market_data import MarketDoor  # pyright: ignore[reportMissingTypeStubs]

__all__ = ["derive_month"]

MINUTE_MS: Final = 60_000
BATCH_ROWS: Final = 50_000
SIDES: Final = ("bid", "ask")


@dataclass(slots=True)
class _Minute:
    """One side of one minute, built tick by tick at the store's integer scale."""

    open: int
    high: int
    low: int
    close: int
    volume: float

    def add(self, price: int, volume: float) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += volume


def _folded(path: Path) -> tuple[dict[int, _Minute], dict[int, _Minute]]:
    """The bid and the ask minutes of one tick file, keyed by each minute's open in ms."""
    bids: dict[int, _Minute] = {}
    asks: dict[int, _Minute] = {}
    with pq.ParquetFile(path) as ticks:
        for batch in ticks.iter_batches(batch_size=BATCH_ROWS, columns=list(TICK_COLUMNS)):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            columns = cast(
                "list[list[Any]]",
                [batch.column(name).to_pylist() for name in TICK_COLUMNS],  # pyright: ignore[reportUnknownMemberType]
            )
            for at, bid, ask, bid_volume, ask_volume in zip(*columns, strict=True):
                opens = at - at % MINUTE_MS
                for minutes, price, volume in ((bids, bid, bid_volume), (asks, ask, ask_volume)):
                    found = minutes.get(opens)
                    if found is None:
                        minutes[opens] = _Minute(price, price, price, price, volume)
                    else:
                        found.add(price, volume)
    return bids, asks


def derive_month(
    door: MarketDoor, series: str, year: int, month: int, *, staging: Path, hold: str | None = None
) -> Result[tuple[CommitReceipt, ...]]:
    """Land one tick month's `bar-m1` pair at its stated scale, kept open by the same `hold`.

    `series` is the tick series, `<source>/<subject>/ticks/-`. A month or a scale the door does not
    hold is refused by name, because a pair at no stated scale could never be read."""
    source, subject, kind, *_ = (*series.split("/"), "", "")
    key = SeriesKey.try_create(source, subject, kind, year, month)
    if is_refusal(key):
        return key
    if kind != TICKS_KIND:
        return invalid_input("series", "a month's minute bars fold from its ticks", given=series)
    scale = door.price_scale(series)
    if scale is None:
        return invalid_input("series", f"{series} states no price scale", given=series)
    state = door.series_store().state(key.value)
    if state is None:
        return missing_artifact(
            "month", f"{series} holds no {year:04d}-{month:02d} to derive", key=key.value.text
        )
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, ignore_cleanup_errors=True) as work:
        folder = Path(work)
        copied = door.materialise((state.fingerprint,), into=folder / "ticks")
        if is_refusal(copied):
            return copied
        staged: list[Path] = []
        for side, minutes in zip(SIDES, _folded(copied.value[0]), strict=True):
            bars = SeriesKey.try_create(source, subject, BAR_KIND, year, month, side)
            if is_refusal(bars):
                return bars
            path = folder / source / subject / BAR_KIND / side / f"{year:04d}-{month:02d}.parquet"
            path.parent.mkdir(parents=True)
            rows = (
                (at, bar.open, bar.high, bar.low, bar.close, bar.volume)
                for at, bar in sorted(minutes.items())
            )
            TypedWriter(path, bars.value.text, BAR_COLUMNS).add(rows).finish()
            staged.append(path)
        landed = door.commit(staged, staging=folder, hold=hold)
    if is_refusal(landed):
        return landed
    for receipt in landed.value:
        stated = door.state_scale(receipt.key.series, scale)
        if is_refusal(stated):
            return stated
    return Ok(landed.value)
