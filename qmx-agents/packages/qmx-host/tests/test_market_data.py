"""The market-data door: one writer, open with no holdout, a study's holdout on its own reads,
and the final look on the primary."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from qmf.core import CalendarIdentity, World, is_ok, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.splits import SplitBoundary, SplitManifest
from qmf.data.store.engines.typed import TypedWriter

from qmx_host.market_data import (
    HANDLE_ROWS,
    NO_HOLDOUT,
    SEAL_READ_REASON,
    MarketDoor,
    Placement,
    Purpose,
)

DAY = 86_400 * 1_000_000_000
SERIES = "dukascopy/EURUSD/bar-m1/-"


def _at(year: int, month: int, day: int = 1) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp()) * 1_000_000_000


JAN = _at(2026, 1, 1)
FEB = _at(2026, 2, 1)
MAR = _at(2026, 3, 1)


def _value(result: Any) -> Any:
    assert is_ok(result)
    return result.value


def _boundary(ns: int) -> SplitBoundary:
    return cast("SplitBoundary", _value(SplitBoundary.try_create(ns)))


def _split(gap_ns: int = DAY) -> SplitManifest:
    calendar = CalendarIdentity.try_create("forex-17NY", "v1", "2025a")
    assert is_ok(calendar)
    segments = SplitManifest.default_split_segments([_at(2026, 1, 10), _at(2026, 1, 20), FEB])
    assert is_ok(segments)
    built = SplitManifest.try_create(
        calendar_identity=calendar.value,
        segments=segments.value,
        seal_boundary=_boundary(FEB),
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


def test_a_read_without_data_scope_is_refused_on_the_server(tmp_path: Path) -> None:
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


def _open(tmp_path: Path, data: dict[str, object], **kwargs: Any) -> MarketDoor:
    built = MarketDoor.open(tmp_path / "market", data, **kwargs)
    assert is_ok(built), built
    return built.value


def _land(tmp_path: Path, door: MarketDoor, year: int, month: int) -> int:
    start = _at(year, month)
    staging = tmp_path / "staging"
    staged = _stage(staging, _key(year, month), _bars(start + DAY, start + 2 * DAY))
    assert is_ok(door.commit([staged], staging=staging))
    return start


def _times(answer: Any) -> list[object]:
    assert is_ok(answer), answer
    return [row["t"] for row in answer.value.rows]


def test_door_opens_without_a_holdout_and_serves_1996(tmp_path: Path) -> None:
    door = _open(tmp_path, {})
    start = _land(tmp_path, door, 1996, 1)
    served = door.read(SERIES, start_ns=start, end_ns=_at(1996, 2), purpose="exploration")
    assert _times(served) == [820_540_800_000, 820_627_200_000]


def test_a_study_holdout_seals_only_its_own_reads(tmp_path: Path) -> None:
    door = _open(tmp_path, {})
    _committed(tmp_path, door)
    sealed = door.read(SERIES, start_ns=FEB, end_ns=MAR, holdout={"boundary": "2026-02"}, run="a")
    assert is_refusal(sealed)
    assert SEAL_READ_REASON in str(sealed.context)
    other = door.read(SERIES, start_ns=FEB, end_ns=MAR, run="b")
    assert _times(other) == [(FEB + DAY) // 1_000_000]


def test_a_run_keeps_the_holdout_of_its_first_read(tmp_path: Path) -> None:
    door = _open(tmp_path, {})
    _committed(tmp_path, door)
    first = door.read(SERIES, start_ns=JAN, end_ns=FEB, holdout={"boundary": "2026-02"}, run="a")
    assert is_ok(first)
    mixed = door.read(SERIES, start_ns=FEB, end_ns=MAR, holdout="off", run="a")
    assert is_refusal(mixed)
    assert "fixed on its first read" in str(mixed.context)
    unnamed = door.read(SERIES, start_ns=FEB, end_ns=MAR, run="a")
    assert is_refusal(unnamed)
    assert SEAL_READ_REASON in str(unnamed.context)


def test_a_final_look_with_no_holdout_is_answered_by_name(tmp_path: Path) -> None:
    door = _open(tmp_path, {}, split=_split())
    _committed(tmp_path, door)
    looked = door.read(
        SERIES, start_ns=FEB, end_ns=MAR, purpose=Purpose.FINAL_LOOK, into=tmp_path / "attempt"
    )
    assert is_refusal(looked)
    assert NO_HOLDOUT in str(looked.context)


def test_a_holdout_turned_on_in_settings_reaches_the_next_read(tmp_path: Path) -> None:
    data: dict[str, object] = {}
    door = _open(tmp_path, data, settings=lambda: data)
    old = _land(tmp_path, door, 1996, 1)
    recent = _land(tmp_path, door, 2025, 3)
    data.update(holdout=True, holdout_boundary="2025-01")
    refused = door.read(SERIES, start_ns=recent, end_ns=_at(2025, 4))
    assert is_refusal(refused)
    assert SEAL_READ_REASON in str(refused.context)
    assert _times(door.read(SERIES, start_ns=old, end_ns=_at(1996, 2))) == [
        820_540_800_000,
        820_627_200_000,
    ]
    study_off = door.read(SERIES, start_ns=recent, end_ns=_at(2025, 4), holdout="off")
    assert _times(study_off) == [(recent + DAY) // 1_000_000, (recent + 2 * DAY) // 1_000_000]


def test_a_commit_is_born_on_the_doors_own_place(tmp_path: Path) -> None:
    pc = _open(tmp_path / "pc", {})
    _land(tmp_path / "pc", pc, 1996, 1)
    server = _open(tmp_path / "server", {}, placement=Placement.SERVER)
    _land(tmp_path / "server", server, 1996, 1)
    assert (pc.pinned(), server.pinned()) == (("-/1996-01",), ())
    marker = next((tmp_path / "pc" / "market" / "series").rglob(".pinned"))
    assert '"from": "pc"' in marker.read_text(encoding="utf-8")


def test_the_pc_serves_the_final_look_when_library_primary_is_pc(tmp_path: Path) -> None:
    door = _door(tmp_path)
    _committed(tmp_path, door)
    looked = door.read(
        SERIES, start_ns=FEB, end_ns=MAR, purpose=Purpose.FINAL_LOOK, into=tmp_path / "attempt"
    )
    assert _times(looked) == [(FEB + DAY) // 1_000_000]
