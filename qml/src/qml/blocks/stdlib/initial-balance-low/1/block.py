"""initial-balance-low@1: the low of the session's initial balance, once it is complete.

The initial balance is the high and low of the bars that close within the first ``ib_seconds``
of the session. ``session_start`` is the second of the UTC day a session opens, and a session
lasts a day. Each bar's ``time`` is its close in nanoseconds UTC; a bar without one is missing.
The value is missing until the initial balance is complete, which is at the first bar that
closes at or after its end, and for the whole session when no bar closed inside it.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_DAY_NS = 86_400 * 10**9


class _Balance:
    __slots__ = ("_day", "_done", "_extreme", "_high", "_ib", "_low", "_side", "_start")

    def __init__(self, start_ns: int, ib_ns: int, side: int) -> None:
        self._start = start_ns
        self._ib = ib_ns
        self._side = side
        self._day: int | None = None
        self._high: Decimal | None = None
        self._low: Decimal | None = None
        self._extreme: Decimal | None = None
        self._done = False

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 3

    def retained(self) -> int:
        return 0 if self._day is None else 3

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return None
        closed, high, low = bar.get("time"), bar.get("high"), bar.get("low")
        if (
            not isinstance(closed, int)
            or isinstance(closed, bool)
            or not isinstance(high, Decimal)
            or not isinstance(low, Decimal)
        ):
            return None
        day = (closed - 1 - self._start) // _DAY_NS
        if day != self._day:
            self._day, self._high, self._low, self._extreme, self._done = (
                day,
                None,
                None,
                None,
                False,
            )
        into = closed - (day * _DAY_NS + self._start)
        if not self._done and into <= self._ib:
            self._high = high if self._high is None else max(self._high, high)
            self._low = low if self._low is None else min(self._low, low)
            self._done = into == self._ib
        else:
            self._done = True
            if self._side > 0:
                self._extreme = high if self._extreme is None else max(self._extreme, high)
            else:
                self._extreme = low if self._extreme is None else min(self._extreme, low)
        if not self._done or self._high is None or self._low is None:
            return None
        return quantise(self._low)

    def export_state(self) -> Mapping[str, object]:
        return {
            "day": self._day,
            "done": self._done,
            "range": [None if v is None else str(v) for v in (self._high, self._low)],
            "extreme": None if self._extreme is None else str(self._extreme),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        day, held, extreme = state.get("day"), state.get("range"), state.get("extreme")
        self._day = day if isinstance(day, int) else None
        self._done = state.get("done") is True
        pair = held if isinstance(held, list) else [None, None]
        self._high, self._low = (None if v is None else Decimal(str(v)) for v in pair)
        self._extreme = None if extreme is None else Decimal(str(extreme))


def _params(params: Mapping[str, Decimal]) -> tuple[int, int, int]:
    seconds = int(params["session_start"])
    if not 0 <= seconds < 86_400:
        raise ValueError(
            "initial-balance-low@1 session_start is a second of the UTC day, 0 to 86399"
        )
    ib = int(params["ib_seconds"])
    if not 0 < ib < 86_400:
        raise ValueError("initial-balance-low@1 ib_seconds is above 0 and below a day")
    side = int(params.get("side", Decimal(1)))
    if side not in (1, -1):
        raise ValueError("initial-balance-low@1 side is 1 for above the balance or -1 for below")
    return seconds * 10**9, ib * 10**9, side


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Balance:
        return _Balance(*_params(params))


BLOCK = _Block()
