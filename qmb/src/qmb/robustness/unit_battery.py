"""A unit run's robustness evidence: its entries against random entries, and its costs stressed.

Both read one finished unit run's trades and the bars it ran over (B14, the judge's chain steps 2
and 3, `judge.md` §3):

- ``entry_edge``: the entry edge ratio, the trades' summed favourable excursion over their summed
  adverse excursion in the ``horizon`` bars after each fill, both in R of the trade's own stop
  distance. The same ratio of ``resamples`` sets of random entries (same markets, sides and stop
  distances, at seeded random bars) is the null, and the kept
  :func:`~qmb.robustness.summary.summarize_distribution` gives the one-tailed p.
- ``cost_stress``: each trade's R with its costs paid ``multiplier`` times: the spread of the bar
  it filled in (the bars carry both sides, so the run paid it once), plus its market's profiled
  slippage and commission when the run had a cost profile.

Every amount is exact; p and the ratio leave as decimal text.
"""

from __future__ import annotations

import bisect
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Final

from qmf.core.refusal import Ok, Result, is_refusal
from qml.protocol.unit import QuoteBar
from qml.unit.model import Side

from qmb._refuse import invalid
from qmb.execution.cost import CostProfile
from qmb.host.unit_handler import UnitTrade
from qmb.robustness.summary import DIRECTION_HIGHER_IS_BETTER, summarize_distribution

__all__ = [
    "EDGE_HORIZON_BARS",
    "EDGE_RESAMPLES",
    "STRESS_MULTIPLIER",
    "CostStress",
    "EntryEdge",
    "cost_stress",
    "entry_edge",
]

EDGE_HORIZON_BARS: Final = 20
"""Starting default of a robustness run's ``horizon_bars``: the bars after a fill it measures."""
EDGE_RESAMPLES: Final = 200
"""Starting default of a robustness run's ``resamples``: random entry sets behind the null."""
STRESS_MULTIPLIER: Final = Decimal("1.5")
"""Starting default of a robustness run's ``cost_multiplier``, the shipped preset's stress."""
_PLACES: Final = Decimal("0.0001")


def _text(value: Fraction | Decimal) -> str:
    exact = value if isinstance(value, Decimal) else Decimal(value.numerator) / value.denominator
    return str(exact.quantize(_PLACES, rounding=ROUND_HALF_EVEN))


@dataclass(frozen=True, slots=True)
class EntryEdge:
    edge_ratio: str
    p: str
    trades: int
    horizon_bars: int
    resamples: int

    def evidence(self) -> dict[str, object]:
        return {
            "edge_ratio": self.edge_ratio,
            "p": self.p,
            "trades": self.trades,
            "horizon_bars": self.horizon_bars,
            "resamples": self.resamples,
        }


@dataclass(frozen=True, slots=True)
class CostStress:
    multiplier: str
    expectancy_r: str
    base_expectancy_r: str
    trades: int

    def evidence(self) -> dict[str, object]:
        return {
            "multiplier": self.multiplier,
            "expectancy_r": self.expectancy_r,
            "base_expectancy_r": self.base_expectancy_r,
            "trades": self.trades,
        }


def _fill_bar(bars: Sequence[QuoteBar], opened_at: int) -> int:
    """The index of the bar a fill at ``opened_at`` traded in: the first closing after it."""
    return bisect.bisect_right([b.knowable_at.value_ns for b in bars], opened_at)


def _excursions(
    bars: Sequence[QuoteBar], start: int, side: Side, entry: Decimal, risk: Decimal, horizon: int
) -> tuple[Fraction, Fraction]:
    ahead = bars[start : start + horizon]
    if side is Side.LONG:
        favourable = max(b.bid.high for b in ahead) - entry
        adverse = entry - min(b.bid.low for b in ahead)
    else:
        favourable = entry - min(b.ask.low for b in ahead)
        adverse = max(b.ask.high for b in ahead) - entry
    return Fraction(max(favourable, Decimal(0)) / risk), Fraction(max(adverse, Decimal(0)) / risk)


def _ratio(pairs: Sequence[tuple[Fraction, Fraction]]) -> Fraction | None:
    adverse = sum((a for _, a in pairs), Fraction(0))
    return None if adverse == 0 else sum((f for f, _ in pairs), Fraction(0)) / adverse


def entry_edge(
    trades: Sequence[UnitTrade],
    bars: Mapping[str, Sequence[QuoteBar]],
    *,
    horizon: int = EDGE_HORIZON_BARS,
    resamples: int = EDGE_RESAMPLES,
    seed: int = 0,
) -> Result[EntryEdge]:
    """The run's entry edge ratio and its p against ``resamples`` sets of seeded random entries."""
    if horizon < 1 or resamples < 1:
        return invalid("robustness", "horizon_bars and resamples are whole numbers above zero")
    measured: list[tuple[UnitTrade, Decimal, tuple[Fraction, Fraction]]] = []
    for trade in trades:
        held = bars.get(trade.market_id, ())
        start = _fill_bar(held, trade.opened_at.value_ns)
        risk = abs(trade.entry_price - trade.stop)
        if risk == 0 or start + horizon > len(held):
            continue
        pair = _excursions(held, start, trade.side, trade.entry_price, risk, horizon)
        measured.append((trade, risk, pair))
    observed = _ratio([pair for _, _, pair in measured])
    if observed is None:
        return invalid(
            "robustness",
            f"no trade has {horizon} bars after its fill and an adverse move to measure",
        )
    draw = random.Random(seed)  # noqa: S311 - a seeded null, not a secret
    null: list[Fraction] = []
    for _ in range(resamples):
        pairs: list[tuple[Fraction, Fraction]] = []
        for trade, risk, _pair in measured:
            held = bars[trade.market_id]
            at = draw.randrange(0, len(held) - horizon + 1)
            entry = held[at].ask.open if trade.side is Side.LONG else held[at].bid.open
            pairs.append(_excursions(held, at, trade.side, entry, risk, horizon))
        null.append(_ratio(pairs) or Fraction(0))
    summary = summarize_distribution(null, observed, DIRECTION_HIGHER_IS_BETTER)
    if is_refusal(summary):
        return summary
    return Ok(
        EntryEdge(_text(observed), _text(summary.value.p_value), len(measured), horizon, resamples)
    )


def _trade_cost_r(
    trade: UnitTrade, held: Sequence[QuoteBar], profile: CostProfile | None
) -> Decimal:
    """One trade's costs in its own R: the fill bar's spread, plus profiled slippage and
    commission on both fills."""
    risk = abs(trade.entry_price - trade.stop)
    start = _fill_bar(held, trade.opened_at.value_ns)
    if risk == 0 or start >= len(held):
        return Decimal(0)
    bar = held[start]
    paid = (bar.ask.open - bar.bid.open) / risk
    if profile is None:
        return paid
    for ns in (trade.opened_at.value_ns, trade.closed_at.value_ns):
        hour = profile.at(ns)
        if hour is None:
            continue
        paid += hour.slippage / risk
        if trade.r != 0:
            paid += hour.commission_per_lot * trade.quantity / abs(trade.money / trade.r)
    return paid


def cost_stress(
    trades: Sequence[UnitTrade],
    bars: Mapping[str, Sequence[QuoteBar]],
    profiles: Mapping[str, CostProfile],
    *,
    multiplier: Decimal = STRESS_MULTIPLIER,
) -> Result[CostStress]:
    """The run's expectancy in R with every trade's costs paid ``multiplier`` times."""
    if multiplier < 1:
        return invalid(
            "cost_multiplier", "a cost stress pays costs at least once", given=str(multiplier)
        )
    if not trades:
        return invalid("robustness", "a cost stress needs trades to stress")
    extra = multiplier - 1
    stressed = [
        t.r - extra * _trade_cost_r(t, bars.get(t.market_id, ()), profiles.get(t.market_id))
        for t in trades
    ]
    count = len(trades)
    return Ok(
        CostStress(
            str(multiplier),
            _text(sum(stressed, Decimal(0)) / count),
            _text(sum((t.r for t in trades), Decimal(0)) / count),
            count,
        )
    )
