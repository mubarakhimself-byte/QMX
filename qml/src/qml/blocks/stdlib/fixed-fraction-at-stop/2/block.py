"""fixed-fraction-at-stop@2: risk ``fraction`` of equity at the stop, as money at risk.

The answer is ``Amount(kind="money_at_risk", value=equity * fraction)``, so no lot is computed
here: the one converter spells the venue's quantity from this amount, the record and the rate
(AD-10). The fraction is read from ``evidence`` on every call, so a number that moves reaches the
size; ``make`` only seeds it (AD-14 step 3).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Amount, Side, Skip


class _FixedFraction:
    __slots__ = ("_fraction",)

    def __init__(self, fraction: Decimal) -> None:
        self._fraction = fraction

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Amount | Skip | None:
        equity = evidence.get("equity")
        if not isinstance(equity, Decimal):
            return None
        moved = evidence.get("fraction")
        fraction = moved if isinstance(moved, Decimal) else self._fraction
        if equity <= 0:
            return Skip(reason="the account holds nothing, so there is nothing to risk")
        if fraction <= 0:
            return Skip(reason="the fraction is zero, so nothing is risked")
        return Amount(kind="money_at_risk", value=equity * fraction, basis="gross_at_stop")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _FixedFraction:
        return _FixedFraction(params["fraction"])


BLOCK = _Block()
