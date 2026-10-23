"""The market-data door: one writer, the seal on every read, the final look on the primary."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import CalendarIdentity, Ok, Result, World, is_ok, is_refusal
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store.engines.typed import TypedWriter
from qmf.data.series import SeriesKey
from qmf.data.store.refusals import invalid_input

from qmx_host.market_data import HANDLE_ROWS, SEAL_READ_REASON, MarketDoor, Placement, Purpose

DAY = 86_400 * 1_000_000_000


def _at(year: int, month: int, day: int = 1) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp()) * 1_000_000_000


JAN = _at(2026, 1, 1)
FEB = _at(2026, 2, 1)
MAR = _at(2026, 3, 1)


def _split(gap_ns: int = DAY) -> SplitManifest:
    calendar = CalendarIdentity.try_create("forex-17NY", "v1", "2025a")
    assert is_ok(calendar)
    segments = SplitManifest.default_split_segments([_at(2026, 1, 10), _at(2026, 1, 20), FEB])
    assert is_ok(segments)
    built = SplitManifest.try_create(
        calendar_identity=calendar.value,
        segments=segments.value,
        seal_boundary=SplitBoundary.try_create(FEB).value,
        purge_width=0,
        embargo_width=0,
        gap=gap_ns,
        world=World.REPLAY,
    )
    assert is_ok(built)
    return built.value


def _door(tmp_path: Path, *, placement: Placement = Placement.PC) -> MarketDoor:
    built = MarketDoor.open(
        tmp_path / "market",
        {"seal_boundary_ns": FEB, "holdout_months": 1},
        placement=placement,
        split=_split(),
    )
    assert is_ok(built)
    return built.value


def _key(year: int, month: int) -> SeriesKey:
    built = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", year, month)
    assert is_ok(built)
    return built.value


def _stage(root: Path, key: SeriesKey, rows: list[tuple[object, ...]]) -> Path:
    path = root / key.series / f"{key.year:04d}-{key.month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    TypedWriter(path, key.text, key.rule.columns).add(rows).finish()
    return path


def _bars(*times_ns: int) -> list[tuple[object, ...]]:
    return [(ns // 1_000_000, 1, 2, 0, 2, 1.0) for ns in times_ns]


def _committed(tmp_path: Path, door: MarketDoor) -> Path:
    staging = tmp_path / "staging"
    january = _stage(
        staging,
        _key(2026, 1),
        _bars(JAN + DAY, JAN + 4 * DAY, JAN + 8 * DAY + DAY // 2, JAN + 15 * DAY),
    )
    february = _stage(staging, _key(2026, 2), _bars(FEB + DAY))
    landed = door.commit([january, february], staging=staging)
    assert is_ok(landed), landed
    return staging


def test_a_sealed_month_is_refused_with_its_reason(tmp_path: Path) -> None:
    door = _door(tmp_path)
    _committed(tmp_path, door)
    refused = door.read("dukascopy/EURUSD/bar-m1/-", start_ns=FEB, end_ns=MAR)
    assert is_refusal(refused)
    assert SEAL_READ_REASON in str(refused.context)
    served = door.read("dukascopy/EURUSD/bar-m1/-", start_ns=JAN, end_ns=FEB)
    assert is_ok(served)
    assert [row["t"] for row in served.value.rows] == [
        (JAN + DAY) // 1_000_000,
        (JAN + 4 * DAY) // 1_000_000,
        (JAN + 8 * DAY + DAY // 2) // 1_000_000,
        (JAN + 15 * DAY) // 1_000_000,
    ]


def test_a_train_read_stops_at_the_gap(tmp_path: Path) -> None:
    door = _door(tmp_path)
    _committed(tmp_path, door)
    trained = door.read(
        "dukascopy/EURUSD/bar-m1/-",
        start_ns=JAN,
        end_ns=FEB,
        purpose=Purpose.TRAIN,
    )
    assert is_ok(trained)
    assert [row["t"] for row in trained.value.rows] == [
        (JAN + DAY) // 1_000_000,
        (JAN + 4 * DAY) // 1_000_000,
    ]


def test_a_read_without_data_scope_is_refused_on_the_primary(tmp_path: Path) -> None:
    door = _door(tmp_path, placement=Placement.SERVER)
    _committed(tmp_path, door)
    refused = door.read("dukascopy/EURUSD/bar-m1/-", start_ns=JAN, end_ns=FEB)
    assert is_refusal(refused)
    assert "data_scope" in str(refused.context)
    scoped = door.read(
        "dukascopy/EURUSD/bar-m1/-",
        start_ns=JAN,
        end_ns=FEB,
        data_scope=["dukascopy/EURUSD/bar-m1/-"],
    )
    assert is_ok(scoped)


def test_a_frozen_month_refuses_another_file(tmp_path: Path) -> None:
    door = _door(tmp_path)
    staging = tmp_path / "staging"
    january = _stage(staging, _key(2026, 1), _bars(JAN + DAY))
    assert is_ok(door.commit([january], staging=staging))
    assert is_ok(door.commit([january], staging=staging))
    _stage(staging, _key(2026, 1), _bars(JAN + 5 * DAY))
    refused = door.commit([january], staging=staging)
    assert is_refusal(refused)
    assert "correction" in str(refused.context)


def test_a_big_read_returns_a_handle(tmp_path: Path) -> None:
    door = _door(tmp_path)
    staging = tmp_path / "staging"
    rows = _bars(*[JAN + (index + 1) * 1_000_000_000 for index in range(HANDLE_ROWS + 1)])
    january = _stage(staging, _key(2026, 1), rows)
    assert is_ok(door.commit([january], staging=staging))
    into = tmp_path / "attempt"
    answered = door.read("dukascopy/EURUSD/bar-m1/-", start_ns=JAN, end_ns=FEB, into=into)
    assert is_ok(answered)
    handle = answered.value.handle
    assert handle is not None
    assert handle["rows"] == HANDLE_ROWS + 1
    assert Path(str(handle["path"])).is_file()
    assert answered.value.rows == ()
