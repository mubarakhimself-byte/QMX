"""peak-holdings-giveback-exit@1: close once the position gives back a share of its best value.

QuantConnect LEAN's ``TrailingStopRiskManagementModel`` starts from the holding's cost, keeps
the best absolute holdings value since (the highest for a long, the lowest for a short), and
liquidates when the relative drawdown from it is above ``maximumDrawdownPercent``. With one
position of fixed size that drawdown is the price's, so here the best is the best bar close
since the position was given, starting at ``entry_price``. A bar that makes a new best does not
hold, as in LEAN; otherwise the exit holds while ``|best - close| / best`` is above
``giveback``. Its value is that drawdown.

One instance serves one position on its side. An update with no ``entry_price`` means no
position is given: the exit answers missing and forgets its best.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, Signal, quantise


class _Giveback:
    __slots__ = ("_best", "_giveback", "_side")

    def __init__(self, giveback: Decimal, side: Side) -> None:
        self._giveback = giveback
        self._side = side
        self._best: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 0 if self._best is None else 1

    def update(self, evidence: Mapping[str, object]) -> Signal | None:
        entry, bar = evidence.get("entry_price"), evidence.get("series")
        if not isinstance(entry, Decimal) or entry <= 0:
            self._best = None
            return None
        close = bar.get("close") if isinstance(bar, Mapping) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(close, Decimal):
            return None
        best = entry if self._best is None else self._best
        better = close > best if self._side is Side.LONG else close < best
        if better:
            self._best = close
            return Signal(state=False, value=quantise(Decimal(0)))
        self._best = best
        drawdown = abs(best - close) / best
        return Signal(state=drawdown > self._giveback, value=quantise(drawdown))

    def export_state(self) -> Mapping[str, object]:
        return {"best": None if self._best is None else str(self._best)}

    def import_state(self, state: Mapping[str, object]) -> None:
        best = state.get("best")
        self._best = Decimal(best) if isinstance(best, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Giveback:
        giveback = params["giveback"]
        if not 0 < giveback < 1:
            raise ValueError("peak-holdings-giveback-exit@1 giveback must be between 0 and 1")
        return _Giveback(giveback, side)


BLOCK = _Block()
