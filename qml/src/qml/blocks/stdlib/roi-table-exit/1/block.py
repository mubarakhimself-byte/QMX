"""roi-table-exit@1: close once the open profit reaches the step of a falling profit table.

freqtrade's ``minimal_roi`` keys a minimum profit ratio by the minutes a trade has been open.
Here the keys are bars held, since a block reads no clock: ``roi_0`` applies from the bar the
position is first given (bar 0), ``roi_1`` from ``bars_1`` bars held, and so on, and the step in
force is the one with the most bars not above the bars held. The exit holds while the open
profit ratio at the bar's close is at least the step's ratio, and its value is that ratio.

One instance serves one position on its side. An update with no ``entry_price`` means no
position is given: the exit answers missing and forgets the bars it counted.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise

_STEPS = 3


class _RoiTable:
    __slots__ = ("_entry", "_held", "_side", "_table")

    def __init__(self, table: tuple[tuple[int, Decimal], ...], side: Side) -> None:
        self._table = table
        self._side = side
        self._held = -1
        self._entry: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 2

    def retained(self) -> int:
        return 0 if self._entry is None else 2

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        if not isinstance(entry, Decimal) or entry <= 0:
            self._held, self._entry = -1, None
            return None
        close = bar.get("close") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(close, Decimal):
            return None
        self._entry = entry
        self._held += 1
        wanted = next(roi for bars, roi in reversed(self._table) if bars <= self._held)
        move = close - entry if self._side is Side.LONG else entry - close
        return Signal(state=move / entry >= wanted, value=quantise(wanted))

    def export_state(self) -> Mapping[str, object]:
        return {"held": self._held, "entry": None if self._entry is None else str(self._entry)}

    def import_state(self, state: Mapping[str, object]) -> None:
        held, entry = state["held"], state.get("entry")
        if not isinstance(held, int):
            raise ValueError("roi-table-exit@1 state needs held")
        self._held = held
        self._entry = Decimal(entry) if isinstance(entry, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _RoiTable:
        table = [(0, params["roi_0"])]
        table += [(int(params[f"bars_{k}"]), params[f"roi_{k}"]) for k in range(1, _STEPS + 1)]
        if any(table[k][0] <= table[k - 1][0] for k in range(1, len(table))):
            raise ValueError("roi-table-exit@1 needs 0 < bars_1 < bars_2 < bars_3")
        return _RoiTable(tuple(table), side)


BLOCK = _Block()
