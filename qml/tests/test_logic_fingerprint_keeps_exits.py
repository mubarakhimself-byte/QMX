"""A held position keeps its per-bar exits when only the risk half moves (AD-3).

COMPARE's probe inverted. A position opened under one risk section, then hosted under the same
logic with a new `risk_fraction`, reads one time exit over the 60 bars after the recompile. At
the parent it reads none, because `exits` keys the position by the compiled fingerprint the
recompile moved.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.risk.unit_intent import UnitExitIntent
from qml.protocol.unit import OwnPosition, UnitStep
from qml.unit.model import Side
from test_compile_dummy import (
    _compiled,
    _document,
    _drive,
    _host,
    _instants,
    _slice,
    _surfaces,
)

_BARS = 60
"""The bars after the recompile that the position is held over."""


def _raised() -> dict[str, object]:
    """The dummy with its one sizer number raised, which moves the risk half alone."""
    document = _document()
    numbers = document["numbers"]
    assert isinstance(numbers, dict)
    spec = numbers["risk_fraction"]
    assert isinstance(spec, dict)
    spec["default"] = "0.01"
    return document


def _held(by: Fingerprint, at: Instant) -> Callable[[str, Instant], OwnPosition | None]:
    position = OwnPosition("pos-1", Side.LONG, Decimal("0.10"), Decimal("1.08000"), by, at)

    def answer(market: str, _instant: Instant) -> OwnPosition | None:
        return position if market == "fx.eurusd" else None

    return answer


def _exits(steps: list[UnitStep]) -> list[tuple[UnitExitIntent, Instant]]:
    return [
        (intent, step.instant)
        for step in steps
        for intent in step.intents
        if isinstance(intent, UnitExitIntent)
    ]


def test_exits_fire_after_a_risk_only_recompile() -> None:
    bars = _slice()
    instants = _instants(bars)[:_BARS]
    before = _compiled()
    after = _compiled(_raised())
    assert after.logic_fingerprint.value == before.logic_fingerprint.value, "the edit moved logic"
    assert after.risk_fingerprint.value != before.risk_fingerprint.value, "the edit moved no risk"

    steps = _drive(
        _host(after, _surfaces(bars, positions=_held(before.logic_fingerprint, instants[0]))),
        instants,
    )
    exits = _exits(steps)

    assert len(exits) == 1
    intent, at = exits[0]
    assert intent.kind.value == "close_full"
    assert intent.position_ref.opened_by == before.logic_fingerprint
    assert at == instants[47], "the 48th bar the position is held"
