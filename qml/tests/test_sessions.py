"""A unit keeps to its session's hours on the session's own clock, goes flat before the close, and
reads each market's own number.

The section's Verify, unit block, at the unit door. The session tests compile a one-market unit
that signals every bar (``test_many_positions``' document) with a London session, and drive it
through ``construct_unit`` and ``on_instant`` on bars stamped at the minutes each test names. The
same local minutes run on 28 March 2025, when London keeps GMT, and on 31 March 2025, after the
clocks went forward to BST, so a session that read UTC would answer differently on the two days.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

import pytest
from qmf.core.chrono import Instant
from qml.compile import CompiledUnit, compile_unit
from qml.protocol.unit import UnitStep
from test_compile_dummy import _compiled as _dummy_compiled
from test_compile_dummy import _document, _drive, _instants, _slice
from test_compile_dummy import _host as _dummy_host
from test_compile_dummy import _surfaces as _dummy_surfaces
from test_many_positions import (
    _closes,
    _context_holding,
    _entries,
    _holding_document,
    _host,
    _one_bar,
    _position,
    _surfaces,
)

_S = 1_000_000_000
_LONDON: dict[str, object] = {
    "name": "london",
    "calendar_ref": "fx-24x5@1",
    "zone": "Europe/London",
    "windows": [{"from": "08:00", "to": "16:00"}],
}
_FLAT_BUFFER = {
    "kind": "fixed",
    "measure": "seconds",
    "range": {"min": "0", "max": "3600", "step": "60"},
    "default": "900",
    "motion": {"mode": "fixed"},
    "authority": "motion_inside_range",
    "origin": "placeholder",
    "owner": "numbers talk",
    "reason": "how long before the close a held trade goes flat, a starting buffer",
}
_GMT_DAY = {"15:55": 1_743_177_300, "16:05": 1_743_177_900, "15:30": 1_743_175_800}
"""Friday 28 March 2025, London on GMT: the local minute is the UTC minute."""
_BST_DAY = {"15:55": 1_743_432_900, "16:05": 1_743_433_500}
"""Monday 31 March 2025, London on BST: the local minute is the UTC minute plus one hour."""


def _session_unit(
    session: Mapping[str, object], numbers: Mapping[str, object] | None = None
) -> CompiledUnit:
    document = _holding_document(limit=1)
    document["sessions"] = [session]
    cast("dict[str, object]", document["numbers"]).update(numbers or {})
    compiled = compile_unit(document, _context_holding())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _rows(step: UnitStep) -> list[tuple[str, str]]:
    return [(row.outcome, row.reason) for row in step.decisions]


@pytest.mark.parametrize("day", [_GMT_DAY, _BST_DAY], ids=["gmt", "bst"])
def test_a_session_refuses_outside_its_hours(day: dict[str, int]) -> None:
    """London 08:00 to 16:00 in the session's zone: a signal at 15:55 London enters, and one at
    16:05 London answers ``outside_session``, on either side of the clock change."""
    compiled = _session_unit(_LONDON)
    early, late = Instant(day["15:55"] * _S), Instant(day["16:05"] * _S)
    bars = [_one_bar("1.09700", at=early.value_ns), _one_bar("1.09700", at=late.value_ns)]

    inside, outside = _drive(_host(compiled, _surfaces(bars, [])), [early, late])

    assert ("taken", "all slots hold") in _rows(inside)
    assert [one.market_id for one in _entries(inside)] == ["fx.eurusd"]
    assert _rows(outside) == [
        ("blocked", "outside_session: 16:05 Europe/London is outside london 08:00 to 16:00")
    ]
    assert outside.intents == ()


def test_flat_before_the_close() -> None:
    """A buffer of 15 minutes closes a held trade on the bar at 15:45 with reason
    ``forced_flat``, and leaves it alone on the bar at 15:30."""
    session = {**copy.deepcopy(_LONDON), "flat_before_close": "flat_buffer"}
    compiled = _session_unit(session, {"flat_buffer": _FLAT_BUFFER})
    held = _position("own-1", "1.09500", "1.09700", compiled)
    at_1530, at_1545 = Instant(_GMT_DAY["15:30"] * _S), Instant((_GMT_DAY["15:30"] + 900) * _S)
    bars = [_one_bar("1.09700", at=at_1530.value_ns), _one_bar("1.09700", at=at_1545.value_ns)]

    before, buffer = _drive(_host(compiled, _surfaces(bars, [held])), [at_1530, at_1545])

    assert _closes(before) == []
    assert [
        (one.position_ref.position_id, one.kind.value, one.reason_code.code)
        for one in _closes(buffer)
    ] == [("own-1", "close_full", "forced_flat")]
    assert (
        "blocked",
        "outside_session: 15:45 Europe/London is inside london's last 900 seconds",
    ) in _rows(buffer)


def test_a_market_keeps_its_own_number() -> None:
    """``stop_buffer`` 0.0002 on EURUSD and 0.0030 on XAUUSD (2 and 30 basis points, the
    measure being a percent written as a fraction) each read their own, over a unit default of
    0.0010 neither market reads.

    The stop shows it was built on the market's own number. EURUSD's first proposal is a short
    beyond the swing high 1.06867: 1.06867 x 1.0002 = 1.068883734, rounded away from the entry to
    the 0.00001 tick, 1.06889 (the default would give 1.06974). XAUUSD's first is a long under the
    swing low 3241.22: 3241.22 x 0.997 = 3231.49634, to the 0.01 tick, 3231.49 (the default would
    give 3237.97).
    """
    document = _document()
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["stop_buffer"]["default"] = "0.0010"
    markets = cast("list[dict[str, object]]", document["markets"])
    markets[0]["settings"] = {"stop_buffer": "0.0002"}
    markets[1]["settings"] = {"stop_buffer": "0.0030"}
    bars = _slice()

    steps = _drive(_dummy_host(_dummy_compiled(document), _dummy_surfaces(bars)), _instants(bars))

    read = {
        (row.market_id, row.numbers_in_force["stop_buffer"])
        for step in steps
        for row in step.decisions
        if row.outcome == "taken"
    }
    assert read == {("fx.eurusd", Decimal("0.0002")), ("metal.xauusd", Decimal("0.0030"))}
    first: dict[str, tuple[str, Decimal]] = {}
    for step in steps:
        for proposal in step.proposals:
            first.setdefault(proposal.market_id, (proposal.row.side.value, proposal.stop))
    assert first == {
        "fx.eurusd": ("short", Decimal("1.06889")),
        "metal.xauusd": ("long", Decimal("3231.49")),
    }


@pytest.mark.parametrize(
    ("name", "value", "warm_up", "state_bound"),
    [
        ("ema_period", "300", 2721, 1059),
        ("roc_lookback", "100", 1001, 1219),
        ("ema_period", "50", 921, 1059),
    ],
    ids=["ema-300", "roc-100", "ema-50"],
)
def test_a_market_waits_for_its_own_warm_up(
    name: str, value: str, warm_up: int, state_bound: int
) -> None:
    """XAUUSD's own number sizes the unit's warm-up and state bound, because the run builds
    XAUUSD's blocks on it and the entry gate reads one unit-wide count.

    The dummy at its defaults needs 921 m15 bars (EMA(100) settles at 900, then ROC(20) 21 more)
    and a bound of 1059. EMA(300) settles at 2700, so 2721. ROC(100) needs 101 after the EMA's 900,
    so 1001, and holds 160 more observations. A setting below the default leaves EURUSD's 921.
    """
    document = _document()
    cast("list[dict[str, object]]", document["markets"])[1]["settings"] = {name: value}

    compiled = _dummy_compiled(document)

    assert dict(compiled.warm_up) == {"m15": warm_up}
    assert compiled.state_bound == state_bound
