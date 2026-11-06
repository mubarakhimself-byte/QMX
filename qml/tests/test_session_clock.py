"""Session blocks on the market's clock (p1a-6): a session opens at its real local time on both sides
of a clock change, counted on the clock's local date, and on UTC each `@2` gives `@1`'s values."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qml.blocks.api import Block, EntryFace, Instance, parse_entry
from qml.catalogue import Loaded, LockEntry, load

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_GOLDEN = _QML / "tests" / "golden"
_INDICATORS = json.loads((_GOLDEN / "indicators" / "talib-0.7.1.json").read_text("utf-8"))
_PROFILE = json.loads((_GOLDEN / "beyond-fx" / "profile.json").read_text("utf-8"))
_UTC, _LONDON, _NEW_YORK = 0, 1, 2
_HALF_HOUR = timedelta(minutes=30)
_RUNNABLE = (
    "initial-balance-high",
    "initial-balance-low",
    "initial-balance-range-extension",
    "session-running-high",
    "session-running-low",
    "session-running-range",
    "tpo-point-of-control",
    "tpo-value-area-high",
    "tpo-value-area-low",
)


def _block(entry_id: str, version: int) -> Block:
    folder = _STDLIB / entry_id / str(version)
    face = parse_entry((folder / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    pin = f"{entry_id}@{version}"
    loaded = load(
        [LockEntry(entry_id, version, face.fingerprint)], {pin: (folder / "block.py").read_bytes()}
    )
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks[pin]


def _running_high(session_start: int, clock: int) -> Instance:
    return _block("session-running-high", 2).make(
        {"session_start": Decimal(session_start), "clock": Decimal(clock)}, {}
    )


def _bar(closed: datetime, price: int) -> dict[str, object]:
    level = Decimal(price)
    return {
        "time": int(closed.timestamp()) * 10**9,
        "open": level,
        "high": level,
        "low": level,
        "close": level,
    }


def _opens(block: Instance, start: datetime, hours: int) -> list[str]:
    """When a session opened, in UTC. Half-hour bars fall, so the running high equals a bar's own
    high only on a session's first bar, and that bar opened with the session."""
    opens: list[str] = []
    for i in range(hours * 2):
        closed = start + _HALF_HOUR * (i + 1)
        price = 10_000 - i
        if block.update({"series": _bar(closed, price)}) == Decimal(price) and i > 0:
            opens.append((closed - _HALF_HOUR).strftime("%m-%d %H:%M"))
    return opens


def test_a_new_york_open_follows_daylight_saving() -> None:
    """The cash open is 14:30 UTC on 2026-03-06 and 13:30 UTC on 2026-03-13, the dates of p1a's
    `proof_edges.py`. `@1` at a fixed 14:30 is an hour wrong on the second date. A bar that closes
    at an open still belongs to the session before."""
    follows = _running_high(34_200, _NEW_YORK)
    fixed = _block("session-running-high", 1).make({"session_start": Decimal(52_200)}, {})

    read = [
        (at, follows.update({"series": bar}), fixed.update({"series": bar}))
        for at, bar in (
            ("03-06 14:30", _bar(datetime(2026, 3, 6, 14, 30, tzinfo=UTC), 100)),
            ("03-06 15:00", _bar(datetime(2026, 3, 6, 15, 0, tzinfo=UTC), 90)),
            ("03-13 13:30", _bar(datetime(2026, 3, 13, 13, 30, tzinfo=UTC), 100)),
            ("03-13 14:00", _bar(datetime(2026, 3, 13, 14, 0, tzinfo=UTC), 90)),
            ("03-13 14:30", _bar(datetime(2026, 3, 13, 14, 30, tzinfo=UTC), 80)),
            ("03-13 15:00", _bar(datetime(2026, 3, 13, 15, 0, tzinfo=UTC), 70)),
        )
    ]

    assert read == [
        ("03-06 14:30", Decimal(100), Decimal(100)),
        ("03-06 15:00", Decimal(90), Decimal(90)),
        ("03-13 13:30", Decimal(100), Decimal(100)),
        ("03-13 14:00", Decimal(90), Decimal(100)),
        ("03-13 14:30", Decimal(90), Decimal(100)),
        ("03-13 15:00", Decimal(90), Decimal(70)),
    ]


@pytest.mark.parametrize(
    ("session_start", "clock", "start", "expected"),
    [
        pytest.param(
            34_200,
            _NEW_YORK,
            datetime(2026, 3, 7, 12, 0, tzinfo=UTC),
            ["03-07 14:30", "03-08 13:30", "03-09 13:30"],
            id="new-york-spring",
        ),
        pytest.param(
            34_200,
            _NEW_YORK,
            datetime(2026, 10, 31, 12, 0, tzinfo=UTC),
            ["10-31 13:30", "11-01 14:30", "11-02 14:30"],
            id="new-york-autumn",
        ),
        pytest.param(
            5_400,
            _NEW_YORK,
            datetime(2026, 10, 31, 12, 0, tzinfo=UTC),
            ["11-01 05:30", "11-02 06:30"],
            id="new-york-a-start-in-the-repeated-hour-opens-once",
        ),
        pytest.param(
            9_000,
            _NEW_YORK,
            datetime(2026, 3, 7, 12, 0, tzinfo=UTC),
            ["03-08 07:30", "03-09 06:30"],
            id="new-york-a-start-in-the-skipped-hour-opens-once",
        ),
        pytest.param(
            28_800,
            _LONDON,
            datetime(2026, 3, 28, 4, 0, tzinfo=UTC),
            ["03-28 08:00", "03-29 07:00", "03-30 07:00"],
            id="london-spring",
        ),
        pytest.param(
            28_800,
            _LONDON,
            datetime(2026, 10, 24, 4, 0, tzinfo=UTC),
            ["10-24 07:00", "10-25 08:00", "10-26 08:00"],
            id="london-autumn",
        ),
        pytest.param(
            0,
            _LONDON,
            datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            ["07-01 23:00", "07-02 23:00", "07-03 23:00"],
            id="london-a-midnight-open-sits-on-the-utc-day-before",
        ),
        pytest.param(
            34_200,
            _UTC,
            datetime(2026, 3, 7, 12, 0, tzinfo=UTC),
            ["03-08 09:30", "03-09 09:30"],
            id="utc-never-moves",
        ),
    ],
)
def test_a_session_opens_once_a_local_day_across_each_clock_change(
    session_start: int, clock: int, start: datetime, expected: list[str]
) -> None:
    assert _opens(_running_high(session_start, clock), start, 66) == expected


def test_a_clock_outside_the_three_is_refused() -> None:
    with pytest.raises(ValueError, match="clock is 0 for UTC, 1 for London, 2 for New York"):
        _running_high(0, 3)


def _golden_bars(table: Mapping[str, object]) -> list[dict[str, object]]:
    rows = cast("list[dict[str, object]]", table["bars"])
    return [{k: v if k == "time" else Decimal(str(v)) for k, v in b.items()} for b in rows]


def _defaults(entry_id: str) -> dict[str, Decimal]:
    raw = json.loads((_STDLIB / entry_id / "1" / "entry.json").read_text("utf-8"))
    parameters = cast("dict[str, dict[str, str]]", raw["parameters"])
    return {name: Decimal(spec["default"]) for name, spec in parameters.items()}


@pytest.mark.parametrize("entry_id", _RUNNABLE)
@pytest.mark.parametrize("session_start", [0, 28_800])
def test_on_utc_each_new_version_gives_the_old_values(entry_id: str, session_start: int) -> None:
    bars = _golden_bars(_INDICATORS if entry_id.startswith("session") else _PROFILE)
    params = _defaults(entry_id) | {"session_start": Decimal(session_start)}
    old_block = _block(entry_id, 1).make(params, {})
    new_block = _block(entry_id, 2).make(params | {"clock": Decimal(_UTC)}, {})

    old = [old_block.update({"series": bar}) for bar in bars]
    new = [new_block.update({"series": bar}) for bar in bars]

    assert any(value is not None for value in old)
    assert new == old
