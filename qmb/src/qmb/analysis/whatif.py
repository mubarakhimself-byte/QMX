"""What-if scenarios over a unit run's trades, each declaring whether it can improve the result.

QB-22 splits what-ifs in two (`judge.md` §4). A scenario that can only worsen a result is a view
and is not counted; one that removes trades by a rule can improve it, so the core counts it as a
`whatif_rerun` try. This tester declares each scenario's direction here, in one table, and the
core refuses a result where a scenario declared ``worsen_only`` came out better than its base:
the label is never trusted on its word.

Every scenario reads the base run's trades and answers the trades left, so its measure, the
expectancy in R, compares like with like.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from qmf.core.refusal import Ok, Result

from qmb._refuse import invalid
from qmb.host.unit_handler import UnitTrade

__all__ = ["MEASURE", "SCENARIOS", "Direction", "Outcome", "Scenario", "expectancy", "what_if"]

Direction: TypeAlias = Literal["worsen_only", "may_improve"]
Apply: TypeAlias = Callable[[Sequence[UnitTrade], Mapping[str, object]], Result[list[Decimal]]]

MEASURE: Final = "expectancy_r"
_NS: Final = 1_000_000_000
_DAYS: Final = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _decimal(params: Mapping[str, object], name: str, default: str) -> Decimal | None:
    raw = params.get(name, default)
    try:
        value = Decimal(raw) if isinstance(raw, str) else None
    except InvalidOperation:
        return None
    return value if value is not None and value.is_finite() else None


def _opened(trade: UnitTrade) -> datetime:
    return datetime.fromtimestamp(trade.opened_at.value_ns // _NS, UTC)


def _drop_top(trades: Sequence[UnitTrade], params: Mapping[str, object]) -> Result[list[Decimal]]:
    fraction = _decimal(params, "fraction", "0.05")
    if fraction is None or not 0 <= fraction <= 1:
        return invalid("scenarios", "drop_top_trades' fraction is decimal text from 0 to 1")
    ordered = sorted((t.r for t in trades), reverse=True)
    return Ok(ordered[math.ceil(fraction * len(ordered)) :])


def _cost_shock(trades: Sequence[UnitTrade], params: Mapping[str, object]) -> Result[list[Decimal]]:
    extra = _decimal(params, "extra_r", "0.05")
    if extra is None:
        return invalid("scenarios", "cost_shock's extra_r is decimal text, the R each trade pays")
    return Ok([t.r - extra for t in trades])


def _skip_days(trades: Sequence[UnitTrade], params: Mapping[str, object]) -> Result[list[Decimal]]:
    days = params.get("days")
    if not isinstance(days, list) or not set(cast("list[object]", days)) <= set(_DAYS):
        return invalid("scenarios", f"skip_weekdays' days name some of {', '.join(_DAYS)}")
    skipped = {_DAYS.index(str(day)) for day in cast("list[object]", days)}
    return Ok([t.r for t in trades if _opened(t).weekday() not in skipped])


def _hours(trades: Sequence[UnitTrade], params: Mapping[str, object]) -> Result[list[Decimal]]:
    start, end = params.get("from"), params.get("to")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= 24:
        return invalid("scenarios", "session_hours' from and to are UTC hours, from before to")
    return Ok([t.r for t in trades if start <= _opened(t).hour < end])


@dataclass(frozen=True, slots=True)
class Scenario:
    direction: Direction
    apply: Apply


SCENARIOS: Final[Mapping[str, Scenario]] = MappingProxyType(
    {
        "drop_top_trades": Scenario("worsen_only", _drop_top),
        "cost_shock": Scenario("worsen_only", _cost_shock),
        "skip_weekdays": Scenario("may_improve", _skip_days),
        "session_hours": Scenario("may_improve", _hours),
    }
)
"""Every scenario this tester runs and its declared direction, as `capabilities` lists them."""


def expectancy(rs: Sequence[Decimal]) -> Decimal:
    return sum(rs, Decimal(0)) / len(rs) if rs else Decimal(0)


@dataclass(frozen=True, slots=True)
class Outcome:
    name: str
    direction: Direction
    base: Decimal
    value: Decimal
    trades: int

    def fields(self) -> dict[str, object]:
        return {
            "name": self.name,
            "direction": self.direction,
            "measure": MEASURE,
            "base": str(self.base),
            "value": str(self.value),
            "trades": self.trades,
        }


def what_if(trades: Sequence[UnitTrade], asked: object) -> Result[tuple[Outcome, ...]]:
    """Each asked scenario, ``{"name", "params"}``, over the base run's trades."""
    if not isinstance(asked, list) or not asked:
        return invalid("scenarios", "a what-if run names one scenario at least")
    base = expectancy([t.r for t in trades])
    made: list[Outcome] = []
    for entry in cast("list[object]", asked):
        named = cast("Mapping[str, object]", entry) if isinstance(entry, Mapping) else {}
        name = str(named.get("name"))
        scenario = SCENARIOS.get(name)
        if scenario is None:
            return invalid(
                "scenarios", f"this tester runs no scenario {name}", known=list(SCENARIOS)
            )
        params = named.get("params", {})
        left = scenario.apply(
            trades, cast("Mapping[str, object]", params) if isinstance(params, Mapping) else {}
        )
        if not isinstance(left, Ok):
            return left
        rs = cast("list[Decimal]", left.value)
        made.append(Outcome(name, scenario.direction, base, expectancy(rs), len(rs)))
    return Ok(tuple(made))
