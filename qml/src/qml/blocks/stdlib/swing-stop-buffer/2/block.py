"""swing-stop-buffer@2: a stop beyond the last swing, with ``buffer`` read from evidence.

A swing low is a bar whose low is below the lows of the two bars before it and not above the
two after it, so it is confirmed two bars late. The long stop is the last swing low less
``buffer`` of its price; mirrored on the short side, the last swing high plus ``buffer``.

The buffer is read from ``evidence`` on every call, so a number that moves reaches the stop;
``make`` only seeds it (AD-14 step 3). A call with no ``series``, which is how the host reads a
stop before the entry it protects, answers the level the bars already gave and keeps the seed.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise

_WING = 2


class _SwingStop:
    __slots__ = ("_bars", "_buffer", "_side", "_swing")

    def __init__(self, buffer: Decimal, side: Side) -> None:
        self._buffer = buffer
        self._side = side
        self._bars: deque[Decimal] = deque(maxlen=2 * _WING + 1)
        self._swing: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 2 * _WING + 1

    @property
    def state_bound(self) -> int:
        return 2 * _WING + 2

    def retained(self) -> int:
        return len(self._bars) + (0 if self._swing is None else 1)

    def _is_swing(self) -> bool:
        bars = list(self._bars)
        middle = bars[_WING]
        before, after = bars[:_WING], bars[_WING + 1 :]
        if self._side is Side.LONG:
            return all(middle < b for b in before) and all(middle <= a for a in after)
        return all(middle > b for b in before) and all(middle >= a for a in after)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        moved = evidence.get("buffer")
        buffer = moved if isinstance(moved, Decimal) else self._buffer
        bar = evidence.get("series")
        if not isinstance(bar, Mapping):
            return self._stop(buffer)
        key = "low" if self._side is Side.LONG else "high"
        extreme = bar.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(extreme, Decimal):
            return self._stop(buffer)
        self._bars.append(extreme)
        if len(self._bars) == self._bars.maxlen and self._is_swing():
            self._swing = self._bars[_WING]
        return self._stop(buffer)

    def _stop(self, buffer: Decimal) -> Decimal | None:
        if self._swing is None:
            return None
        sign = -1 if self._side is Side.LONG else 1
        return quantise(self._swing * (1 + sign * buffer))

    def export_state(self) -> Mapping[str, object]:
        return {
            "bars": [str(b) for b in self._bars],
            "swing": None if self._swing is None else str(self._swing),
        }

    def import_state(self, state: Mapping[str, object]) -> None:
        bars, swing = state["bars"], state.get("swing")
        if not isinstance(bars, list):
            raise ValueError("swing-stop-buffer@2 state needs bars")
        self._bars.clear()
        self._bars.extend(Decimal(str(b)) for b in bars)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        self._swing = Decimal(swing) if isinstance(swing, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _SwingStop:
        return _SwingStop(params["buffer"], side)


BLOCK = _Block()
