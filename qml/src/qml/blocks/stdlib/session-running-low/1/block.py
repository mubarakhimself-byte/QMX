"""session-running-low@1: the lowest low of the current session so far.

``session_start`` is the second of the UTC day a session opens, 0 for midnight UTC, and a
session lasts a day. Each bar's ``time`` is its close in nanoseconds UTC; a bar without one is
missing. The value comes from the first bar on.
"""
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in raw]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = bar
    found = [v for v in (fields.get(name) for name in names) if isinstance(v, Decimal)]
    return tuple(float(v) for v in found) if len(found) == len(names) else None


_DAY_NS = 86_400 * 10**9


def _session(evidence: Mapping[str, object], start_ns: int) -> tuple[int, tuple[float, ...]] | None:
    """The session a bar closes in and its prices. A bar closing exactly at the session start
    belongs to the session before; ``time`` is the bar's close in nanoseconds UTC."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    closed = bar.get("time")
    found = _bar(evidence, "high", "low", "close")
    if not isinstance(closed, int) or isinstance(closed, bool) or found is None:
        return None
    return (closed - 1 - start_ns) // _DAY_NS, found


def _start(params: Mapping[str, Decimal], entry: str) -> int:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(f"{entry} session_start is a second of the UTC day, 0 to 86399")
    return seconds * 10**9


class _SessionLow:
    __slots__ = ("_day", "_high", "_low", "_start")

    def __init__(self, start_ns: int) -> None:
        self._start = start_ns
        self._day: int | None = None
        self._high = 0.0
        self._low = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 0 if self._day is None else 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        found = _session(evidence, self._start)
        if found is None:
            return None
        day, (high, low, _close) = found
        if day != self._day:
            self._day, self._high, self._low = day, high, low
        else:
            self._high, self._low = max(self._high, high), min(self._low, low)
        return quantise(self._low)

    def export_state(self) -> Mapping[str, object]:
        return {"day": self._day, "range": [self._high.hex(), self._low.hex()]}

    def import_state(self, state: Mapping[str, object]) -> None:
        day = state.get("day")
        self._day = day if isinstance(day, int) else None
        self._high, self._low = _floats(state["range"], "session-running-low@1 state's range")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SessionLow:
        return _SessionLow(_start(params, "session-running-low@1"))


BLOCK = _Block()
