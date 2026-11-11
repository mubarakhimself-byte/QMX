"""Layer C of the unit check: every number has a kind, a measure and a range that agree (AD-103).

Layer C reads a unit that passed layer A and the instrument record of each market it trades,
keyed by the unit's ``market_id``. A record is needed only by a check that reads one, and a
missing one is then an error naming the market, never a guess.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Final

from qml.numbers.measures import MEASURES, Form, MeasureRule
from qml.numbers.records import InstrumentRecord
from qml.unit.model import Market, Measure, MotionMode, NumberKind, NumberSpec, Origin, Range, Unit
from qml.unit.parse import Problem, ProblemKind
from qml.unit.schema import DECIMAL_PATTERN

__all__ = ["KIND_MODES", "NumbersCheck", "check_numbers"]

KIND_MODES: Final[Mapping[NumberKind, frozenset[MotionMode]]] = {
    NumberKind.FIXED: frozenset({MotionMode.FIXED}),
    NumberKind.DERIVED: frozenset(
        {MotionMode.SCALED, MotionMode.PERCENTILE_OF_OWN_HISTORY, MotionMode.STATE_TABLE}
    ),
    NumberKind.CALIBRATED: frozenset({MotionMode.SHRINK_FROM_OWN_TRADES, MotionMode.LEARNED}),
}

_UNSETTLED: Final = frozenset({Origin.BUILDER_CHOSEN, Origin.UNRESOLVED})
_FLAGS: Final = frozenset({"true", "false"})


@dataclass(frozen=True)
class NumbersCheck:
    errors: tuple[Problem, ...]
    warnings: tuple[Problem, ...]


def _at(parent: str, *keys: str | int) -> str:
    for key in keys:
        parent += "/" + str(key).replace("~", "~0").replace("/", "~1")
    return parent


@dataclass
class _Found:
    errors: list[Problem] = field(default_factory=list[Problem])
    warnings: list[Problem] = field(default_factory=list[Problem])

    def error(self, kind: ProblemKind, where: str, message: str, hint: str) -> None:
        self.errors.append(Problem(kind, (where,), message[:300], hint[:300], "C"))

    def warning(self, kind: ProblemKind, where: str, message: str, hint: str) -> None:
        self.warnings.append(Problem(kind, (where,), message[:300], hint[:300], "C"))


def _bounds_hint(measure: Measure, rule: MeasureRule) -> str:
    if measure is Measure.PERCENT:
        return 'percent is stored as a fraction: write 0.5% as "0.005"; use ratio above one'
    highest = "any size" if rule.highest is None else rule.highest
    return f"a {measure.value} value lies from {rule.lowest} to {highest}"


def _value(found: _Found, where: str, value: Decimal, measure: Measure, span: Range | None) -> bool:
    rule = MEASURES[measure]
    if rule.form is Form.WHOLE and value != value.to_integral_value():
        found.error(
            ProblemKind.NOT_IN_MEASURE,
            where,
            f"{value} is not a whole number of {measure.value}",
            "write a whole number",
        )
        return False
    if (rule.lowest is not None and value < rule.lowest) or (
        rule.highest is not None and value > rule.highest
    ):
        found.error(
            ProblemKind.OUTSIDE_MEASURE,
            where,
            f"{value} is outside what a {measure.value} value can be",
            _bounds_hint(measure, rule),
        )
        return False
    if span is not None and not span.min <= value <= span.max:
        found.error(
            ProblemKind.OUTSIDE_RANGE,
            where,
            f"{value} is outside the number's range {span.min} to {span.max}",
            "move the value inside the range, or widen the range in a new version",
        )
        return False
    return True


def _range(found: _Found, where: str, span: Range, measure: Measure) -> bool:
    ends_hold = all(
        [
            _value(found, _at(where, "min"), span.min, measure, None),
            _value(found, _at(where, "max"), span.max, measure, None),
        ]
    )
    if MEASURES[measure].form is Form.WHOLE and span.step != span.step.to_integral_value():
        found.error(
            ProblemKind.NOT_IN_MEASURE,
            _at(where, "step"),
            f"a step of {span.step} is not a whole number of {measure.value}",
            "write a whole step",
        )
        return False
    if span.min > span.max:
        found.error(
            ProblemKind.BAD_RANGE,
            where,
            f"the range's min {span.min} is above its max {span.max}",
            "swap min and max",
        )
        return False
    if span.step <= 0:
        found.error(
            ProblemKind.BAD_RANGE,
            _at(where, "step"),
            f"a step of {span.step} never moves",
            "use a step above zero",
        )
        return False
    if ((Fraction(span.max) - Fraction(span.min)) / Fraction(span.step)).denominator != 1:
        found.error(
            ProblemKind.BAD_RANGE,
            _at(where, "step"),
            f"the step {span.step} does not divide the range {span.min} to {span.max}",
            "pick a step that lands exactly on max from min",
        )
        return False
    return ends_hold


def _motion(found: _Found, where: str, spec: NumberSpec) -> None:
    motion = spec.motion
    if motion.mode not in KIND_MODES[spec.kind]:
        allowed = ", ".join(sorted(mode.value for mode in KIND_MODES[spec.kind]))
        found.error(
            ProblemKind.MOTION_NOT_ALLOWED,
            _at(where, "motion", "mode"),
            f"a {spec.kind.value} number cannot move by {motion.mode.value}",
            f"a {spec.kind.value} number moves by {allowed}",
        )
    if spec.kind is not NumberKind.CALIBRATED:
        return
    cadence = motion.cadence
    if cadence is None or (cadence.every_closed_trades is None and cadence.at is None):
        found.error(
            ProblemKind.MOTION_INCOMPLETE,
            _at(where, "motion", "cadence"),
            "a calibrated number names no cadence, so it would never move",
            "name every_closed_trades, at, or both",
        )
    if motion.shrink_k is None:
        found.error(
            ProblemKind.MOTION_INCOMPLETE,
            _at(where, "motion", "shrink_k"),
            "a calibrated number names no shrink toward its default",
            "set shrink_k, such as 100",
        )


def _number(found: _Found, where: str, spec: NumberSpec) -> None:
    _motion(found, where, spec)
    if not spec.reason.strip():
        found.error(
            ProblemKind.NUMBER_NO_REASON,
            _at(where, "reason"),
            "this number gives no reason for its value",
            "say in one line why it holds this value rather than another",
        )
    if spec.origin in _UNSETTLED:
        found.warning(
            ProblemKind.UNSETTLED_ORIGIN,
            _at(where, "origin"),
            f"this number's value is {spec.origin.value}, not taken from a source",
            "cite a source for the value when one exists",
        )
    form = MEASURES[spec.measure].form
    if form in (Form.CATEGORY, Form.FLAG):
        if spec.range is not None:
            found.error(
                ProblemKind.RANGE_NOT_ALLOWED,
                _at(where, "range"),
                f"a {spec.measure.value} number has no numeric range",
                "remove the range",
            )
        if (form is Form.FLAG and spec.default not in _FLAGS) or not spec.default.strip():
            found.error(
                ProblemKind.NOT_IN_MEASURE,
                _at(where, "default"),
                f"{spec.default!r} is not a {spec.measure.value} value",
                'a flag is "true" or "false"; a category is a non-empty name',
            )
        return
    span_holds = False
    if spec.range is None:
        found.error(
            ProblemKind.NUMBER_NO_RANGE,
            _at(where, "range"),
            f"a {spec.measure.value} number needs a range",
            "add range with min, max and step",
        )
    else:
        span_holds = _range(found, _at(where, "range"), spec.range, spec.measure)
    if re.fullmatch(DECIMAL_PATTERN, spec.default) is None:
        found.error(
            ProblemKind.NOT_IN_MEASURE,
            _at(where, "default"),
            f"{spec.default!r} is not a decimal string",
            'write digits with an optional point, such as "0.02" or "100"',
        )
        return
    _value(
        found,
        _at(where, "default"),
        Decimal(spec.default),
        spec.measure,
        spec.range if span_holds else None,
    )


def _pips(
    found: _Found,
    where: str,
    markets: tuple[Market, ...],
    records: Mapping[str, InstrumentRecord],
) -> None:
    for market in markets:
        record = records.get(market.market_id)
        if record is None:
            found.error(
                ProblemKind.NO_RECORD,
                where,
                f"a number in pips needs the instrument record of {market.market_id}, "
                "and none was given",
                "check against the market's instrument record",
            )
        elif record.pip is None:
            found.error(
                ProblemKind.NO_PIP,
                where,
                f"the record {record.name} defines no pip, so pips mean nothing on "
                f"{market.market_id}",
                "use price_distance, ticks or atr_multiple",
            )


def _setting(
    found: _Found, where: str, name: str, value: Decimal, numbers: Mapping[str, NumberSpec]
) -> None:
    spec = numbers.get(name)
    if spec is None:
        found.error(
            ProblemKind.UNDECLARED_NUMBER,
            where,
            f"{name!r} is not one of the unit's numbers",
            "declare it under numbers, or remove the setting",
        )
        return
    if MEASURES[spec.measure].form in (Form.CATEGORY, Form.FLAG):
        found.error(
            ProblemKind.NOT_IN_MEASURE,
            where,
            f"{name!r} is a {spec.measure.value} number and takes no decimal setting",
            "remove the setting",
        )
        return
    _value(found, where, value, spec.measure, spec.range)


def check_numbers(unit: Unit, records: Mapping[str, InstrumentRecord]) -> NumbersCheck:
    """Every layer C problem in ``unit``, errors and warnings apart, in document order."""
    found = _Found()
    for name, spec in unit.numbers.items():
        where = _at("/numbers", name)
        _number(found, where, spec)
        if spec.measure is Measure.PIPS:
            _pips(found, _at(where, "measure"), unit.markets, records)
    for index, market in enumerate(unit.markets):
        for name, value in market.settings.items():
            _setting(found, _at("/markets", index, "settings", name), name, value, unit.numbers)
    return NumbersCheck(tuple(found.errors), tuple(found.warnings))
