"""The measure vocabulary and its one table onto QMF's ``UnitKind`` (AD-103, CONTRACTS.md 2.2).

QML's measures are richer than QMF's closed ``UnitKind`` enum, which is not amended (L0 AD-9).
Each measure maps to exactly one member, or to none for a category or a flag, and declares the
form its values take and the bounds every value of that measure lies inside.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from qmf.core.exact import UnitKind

from qml.unit.model import Measure

__all__ = ["MEASURES", "Form", "MeasureRule"]


class Form(StrEnum):
    DECIMAL = "decimal"
    WHOLE = "whole"
    CATEGORY = "category"
    FLAG = "flag"


@dataclass(frozen=True)
class MeasureRule:
    unit_kind: UnitKind | None
    form: Form
    converts_through: str
    lowest: Decimal | None = None
    highest: Decimal | None = None


_NONE = "none"

MEASURES: Final[Mapping[Measure, MeasureRule]] = MappingProxyType(
    {
        Measure.PRICE_DISTANCE: MeasureRule(
            UnitKind.PRICE_DELTA, Form.DECIMAL, "the record's tick size and digits", Decimal(0)
        ),
        Measure.TICKS: MeasureRule(
            UnitKind.COUNT, Form.WHOLE, "the record's tick size", Decimal(0)
        ),
        Measure.PIPS: MeasureRule(
            UnitKind.PRICE_DELTA, Form.DECIMAL, "the record's pip, when it defines one", Decimal(0)
        ),
        Measure.ATR_MULTIPLE: MeasureRule(
            UnitKind.DIMENSIONLESS_RATIO, Form.DECIMAL, "the bound ATR block's value", Decimal(0)
        ),
        # Percent is stored as a fraction: 0.5% is written "0.005", so every value lies
        # between -1 and 1. A multiple above one is a ratio.
        Measure.PERCENT: MeasureRule(
            UnitKind.DIMENSIONLESS_RATIO, Form.DECIMAL, _NONE, Decimal(-1), Decimal(1)
        ),
        Measure.RATIO: MeasureRule(UnitKind.DIMENSIONLESS_RATIO, Form.DECIMAL, _NONE),
        Measure.PROBABILITY: MeasureRule(
            UnitKind.DIMENSIONLESS_RATIO, Form.DECIMAL, _NONE, Decimal(0), Decimal(1)
        ),
        Measure.BARS: MeasureRule(UnitKind.COUNT, Form.WHOLE, _NONE, Decimal(0)),
        Measure.COUNT: MeasureRule(UnitKind.COUNT, Form.WHOLE, _NONE, Decimal(0)),
        Measure.SECONDS: MeasureRule(UnitKind.DURATION, Form.DECIMAL, _NONE, Decimal(0)),
        Measure.MONEY: MeasureRule(
            UnitKind.MONEY, Form.DECIMAL, "the record's value per point and the account currency"
        ),
        Measure.R: MeasureRule(UnitKind.R_MULTIPLE, Form.DECIMAL, "the trade's initial risk"),
        Measure.LOTS: MeasureRule(
            UnitKind.QUANTITY, Form.DECIMAL, "the record's lot step and minimum lot", Decimal(0)
        ),
        Measure.CATEGORY: MeasureRule(None, Form.CATEGORY, _NONE),
        Measure.FLAG: MeasureRule(None, Form.FLAG, _NONE),
    }
)
