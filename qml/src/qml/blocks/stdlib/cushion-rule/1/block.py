"""cushion-rule@1: house money and reverse house money as one sizing modifier (AD-11, D13).

The rule reads one cushion ledger, the unit's closed trades in R since an anchor, which the fold
keeps and the unit hands every modifier as ``cushion.<clock>.realised``, the total since the
clock's anchor, and ``cushion.<clock>.peak``, the highest running total since it. The factor is
``1 + strength x cushion / reach``: ``reach`` is the cushion that moves the size by one whole
``strength``, and the factor is never below zero, because a negative size would turn the trade
around.

``anchor`` is the one switch between his two ideas. A fixed anchor (0) counts from the anchor
itself, so the rule presses with winnings and brakes with losses: house money. A running-peak
anchor (1) counts from the highest running total since the anchor, so the cushion is never above
zero and the rule only brakes: reverse house money. ``clock`` says when the anchor moves: each UTC
day (0) or each Monday-start week (1). Only closed trades reach the ledger, so an open profit
never presses.

Every number is read from ``evidence`` first, so a moved number reaches the factor; ``make`` only
seeds it (AD-14 step 3). The rule names no ceiling of its own: a press gate in front of it decides
when a raise may stand.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Factor, Side

_ANCHORS = ("fixed", "running peak")
_CLOCKS = ("day", "week")
_FLOOR = Decimal(0)


def _text(value: Decimal) -> str:
    return format(value, "f")


def _code(choices: tuple[str, ...], code: Decimal) -> str | None:
    if code != code.to_integral_value() or not 0 <= code < len(choices):
        return None
    return choices[int(code)]


def _ledger(evidence: Mapping[str, object], clock: str, field: str) -> Decimal | None:
    """One figure of one clock's cushion ledger, or None when the unit handed none."""
    value = evidence.get(f"cushion.{clock}.{field}")
    return value if isinstance(value, Decimal) and value.is_finite() else None


class _CushionRule:
    __slots__ = ("_seeded",)

    def __init__(self, seeded: Mapping[str, Decimal]) -> None:
        self._seeded = dict(seeded)

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def _number(self, evidence: Mapping[str, object], name: str) -> Decimal | None:
        moved = evidence.get(name)
        value = moved if isinstance(moved, Decimal) else self._seeded.get(name)
        return value if value is not None and value.is_finite() else None

    def update(self, evidence: Mapping[str, object]) -> Factor | None:
        strength = self._number(evidence, "strength")
        reach = self._number(evidence, "reach")
        anchor_code = self._number(evidence, "anchor")
        clock_code = self._number(evidence, "clock")
        if strength is None or reach is None or anchor_code is None or clock_code is None:
            return None
        anchor = _code(_ANCHORS, anchor_code)
        clock = _code(_CLOCKS, clock_code)
        if anchor is None or clock is None or reach <= 0:
            return None
        realised, peak = _ledger(evidence, clock, "realised"), _ledger(evidence, clock, "peak")
        if realised is None or peak is None:
            return None
        cushion = realised if anchor == "fixed" else realised - peak
        value = max(_FLOOR, 1 + strength * cushion / reach)
        return Factor(
            value=value,
            range=(_FLOOR, max(Decimal(1), value)),
            reason=(
                f"a cushion of {_text(cushion)} R since the {clock} anchor, {anchor}, "
                f"moves the size by {_text(value)}"
            ),
        )

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _CushionRule:
        return _CushionRule(params)


BLOCK = _Block()
