"""Price data a newer QMX marked too new opens read-only (design 62 B2 rule 4): reads are served,
and nothing is written into the store."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import is_ok, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TypedWriter
from qmx_home import Label, resolve

from qmx_host.market_data import MarketDoor

DAY = 86_400 * 1_000_000_000
JAN = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp()) * 1_000_000_000
FEB = int(datetime(2026, 2, 1, tzinfo=UTC).timestamp()) * 1_000_000_000
SERIES = "dukascopy/EURUSD/bar-m1/-"


def door_at(root: Path) -> MarketDoor:
    built = MarketDoor.open(root, {})
    assert is_ok(built)
    return built.value


def staged(staging: Path, month: int) -> Path:
    key = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", 2026, month)
    assert is_ok(key)
    path = staging / key.value.series / f"2026-{month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    start = JAN if month == 1 else FEB
    rows: list[tuple[object, ...]] = [((start + DAY) // 1_000_000, 1, 2, 0, 2, 1.0)]
    TypedWriter(path, key.value.text, key.value.rule.columns).add(rows).finish()
    return path


def tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_price_data_too_new_for_this_release_is_read_and_never_written(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    root = layout.data / "market"
    staging = tmp_path / "staging"
    assert is_ok(door_at(root).commit([staged(staging, 1)], staging=staging))
    label = Label.parse(layout.label.read_text(encoding="utf-8"))
    stores = {**label.stores, "market": {"version": 2, "min_reader": 2}}
    layout.label.write_text(
        Label(label.home_id, 2, "0.1.0", "0.7.0", stores=stores).dump(), encoding="utf-8"
    )
    before = tree(root)

    door = door_at(root)
    served = door.read(SERIES, start_ns=JAN, end_ns=FEB, run="run-1")
    refused = door.commit([staged(staging, 2)], staging=staging)

    assert is_ok(served)
    assert len(served.value.rows) == 1
    assert is_refusal(refused)
    assert str(refused.context["reason"]).startswith(
        "the price data is read-only: This QMX folder's price data was written by QMX 0.7.0"
    )
    assert tree(root) == before
