"""vwap-session-anchored@1: the volume-weighted average typical price since the session
opened.

The typical price ``(high + low + close) / 3`` of each bar of the session weighted by its
volume, missing while the session's volume is 0.

``session_start`` is the second of the UTC day a session opens, 0 for midnight UTC, and a
session lasts a day. Each bar's ``time`` is its close in nanoseconds UTC; a bar without one or
without volume is missing. The value comes from the first bar on. On FX and CFD bars the
volume is a tick count.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qml.blocks.api import Side, quantise


def _floats(raw: object, what: str) -> list[float]:
    if not isinstance(raw, list):
        raise ValueError(f"{what} is a list of hex floats")
    return [float.fromhex(str(v)) for v in cast("list[object]", raw)]


def _bar(evidence: Mapping[str, object], *names: str) -> tuple[float, ...] | None:
    """The named fields of the bar on the ``series`` port as floats, or None when one is missing."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    fields = cast("Mapping[str, object]", bar)
    found = [fields.get(name) for name in names]
    if not all(isinstance(v, Decimal) for v in found):
        return None
    return tuple(float(cast("Decimal", v)) for v in found)


_DAY_NS = 86_400 * 10**9


def _session(evidence: Mapping[str, object], start_ns: int) -> tuple[int, tuple[float, ...]] | None:
    """The session a bar closes in and its prices. A bar closing exactly at the session start
    belongs to the session before; ``time`` is the bar's close in nanoseconds UTC."""
    bar = evidence.get("series")
    if not isinstance(bar, Mapping):
        return None
    closed = cast("Mapping[str, object]", bar).get("time")
    found = _bar(evidence, "high", "low", "close")
    if not isinstance(closed, int) or isinstance(closed, bool) or found is None:
        return None
    return (closed - 1 - start_ns) // _DAY_NS, found


def _start(params: Mapping[str, Decimal], entry: str) -> int:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(f"{entry} session_start is a second of the UTC day, 0 to 86399")
    return seconds * 10**9


class _Vwap:
    __slots__ = ("_day", "_start", "_volume", "_weighted")

    def __init__(self, start_ns: int) -> None:
        self._start = start_ns
        self._day: int | None = None
        self._weighted = 0.0
        self._volume = 0.0

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
        volume = _bar(evidence, "volume")
        if found is None or volume is None:
            return None
        day, (high, low, close) = found
        if day != self._day:
            self._day, self._weighted, self._volume = day, 0.0, 0.0
        self._weighted += (high + low + close) / 3 * volume[0]
        self._volume += volume[0]
        return quantise(self._weighted / self._volume) if self._volume > 0.0 else None

    def export_state(self) -> Mapping[str, object]:
        return {"day": self._day, "sums": [self._weighted.hex(), self._volume.hex()]}

    def import_state(self, state: Mapping[str, object]) -> None:
        day = state.get("day")
        self._day = day if isinstance(day, int) else None
        self._weighted, self._volume = _floats(state["sums"], "vwap-session-anchored@1 sums")


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Vwap:
        return _Vwap(_start(params, "vwap-session-anchored@1"))


BLOCK = _Block()
