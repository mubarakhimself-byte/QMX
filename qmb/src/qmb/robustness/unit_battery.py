"""A unit run's robustness evidence: its entries against random entries, and its costs stressed.

Both read one finished unit run's trades and the bars it ran over (B14, the judge's chain steps 2
and 3, `judge.md` §3):

- ``entry_edge``: the entry edge ratio, the trades' summed favourable excursion over their summed
  adverse excursion in the ``horizon`` bars after each fill, both in R of the trade's own stop
  distance. The same ratio of ``resamples`` sets of random entries (same markets, sides and stop
  distances, at seeded random bars) is the null. The one-tailed p counts the observed set among
  the draws, ``(k + 1) / (resamples + 1)`` where ``k`` null ratios reach the observed one
  (Phipson and Smyth), so a few draws can never give a p near 0.
- ``cost_stress``: each trade's R with its costs paid ``multiplier`` times: the spread of the bar
  it filled in (the bars carry both sides, so the run paid it once), plus its market's profiled
  slippage and commission when the run had a cost profile.

Every amount is exact; p and the ratio leave as decimal text.
"""

from __future__ import annotations

import bisect
import random
from array import array
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Final, cast

from qmf.core.refusal import Ok, Result, TypedRefusal
from qml.protocol.unit import QuoteBar
from qml.unit.model import Side

from qmb._refuse import invalid
from qmb.execution.cost import CostProfile
from qmb.host.unit_handler import UnitTrade

__all__ = [
    "EDGE_HORIZON_BARS",
    "EDGE_RESAMPLES",
    "EDGE_RESAMPLES_LEAST",
    "STRESS_MULTIPLIER",
    "CompactBars",
    "CostStress",
    "EntryEdge",
    "compact_bars",
    "cost_stress",
    "entry_edge",
]

EDGE_HORIZON_BARS: Final = 20
"""Starting default of a robustness run's ``horizon_bars``: the bars after a fill it measures."""
EDGE_RESAMPLES: Final = 200
"""Starting default of a robustness run's ``resamples``: random entry sets behind the null."""
EDGE_RESAMPLES_LEAST: Final = 20
"""Starting default of the fewest ``resamples`` a robustness run takes: the smallest p 20 draws
can give, 1/21, lies below the shipped presets' ``signal_p`` of 0.05."""
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


@dataclass(slots=True)
class CompactBars:
    """One market's bars as columns of whole numbers at one price scale: only what the battery
    reads, at 56 bytes a bar, because it reads random spans of the whole window."""

    scale: int = 0
    closes_ns: array[int] = field(default_factory=lambda: array("q"))
    bid_open: array[int] = field(default_factory=lambda: array("q"))
    bid_high: array[int] = field(default_factory=lambda: array("q"))
    bid_low: array[int] = field(default_factory=lambda: array("q"))
    ask_open: array[int] = field(default_factory=lambda: array("q"))
    ask_high: array[int] = field(default_factory=lambda: array("q"))
    ask_low: array[int] = field(default_factory=lambda: array("q"))

    def __len__(self) -> int:
        return len(self.closes_ns)

    def price(self, whole: int) -> Decimal:
        return Decimal(whole).scaleb(-self.scale)

    def add(self, bar: QuoteBar) -> None:
        """One bar more. Finer prices than the scale so far raise every column, so none rounds."""
        prices = (bar.bid.open, bar.bid.high, bar.bid.low, bar.ask.open, bar.ask.high, bar.ask.low)
        finest = max(-cast("int", price.as_tuple().exponent) for price in prices)
        columns = (
            self.bid_open,
            self.bid_high,
            self.bid_low,
            self.ask_open,
            self.ask_high,
            self.ask_low,
        )
        if finest > self.scale:
            raised = 10 ** (finest - self.scale)
            for column in columns:
                column[:] = array("q", (whole * raised for whole in column))
            self.scale = finest
        self.closes_ns.append(bar.knowable_at.value_ns)
        for column, price in zip(columns, prices, strict=True):
            column.append(int(price.scaleb(self.scale)))


def compact_bars(
    feeds: Mapping[str, Callable[[], Iterable[QuoteBar | TypedRefusal]]],
) -> Result[dict[str, CompactBars]]:
    """Each market's bars from its feed into columns, or the refusal that stopped a feed."""
    held: dict[str, CompactBars] = {}
    for market, feed in feeds.items():
        bars = CompactBars()
        for item in feed():
            if isinstance(item, TypedRefusal):
                return item
            bars.add(item)
        held[market] = bars
    return Ok(held)


_NO_BARS: Final = CompactBars()


def _fill_bar(bars: CompactBars, opened_at: int) -> int:
    """The index of the bar a fill at ``opened_at`` traded in: the first closing after it."""
    return bisect.bisect_right(bars.closes_ns, opened_at)


def _excursions(
    bars: CompactBars, start: int, side: Side, entry: Decimal, risk: Decimal, horizon: int
) -> tuple[Fraction, Fraction]:
    end = start + horizon
    if side is Side.LONG:
        favourable = bars.price(max(bars.bid_high[start:end])) - entry
        adverse = entry - bars.price(min(bars.bid_low[start:end]))
    else:
        favourable = entry - bars.price(min(bars.ask_low[start:end]))
        adverse = bars.price(max(bars.ask_high[start:end])) - entry
    return Fraction(max(favourable, Decimal(0)) / risk), Fraction(max(adverse, Decimal(0)) / risk)


def _ratio(pairs: Sequence[tuple[Fraction, Fraction]]) -> Fraction | None:
    adverse = sum((a for _, a in pairs), Fraction(0))
    return None if adverse == 0 else sum((f for f, _ in pairs), Fraction(0)) / adverse


def entry_edge(
    trades: Sequence[UnitTrade],
    bars: Mapping[str, CompactBars],
    *,
    horizon: int = EDGE_HORIZON_BARS,
    resamples: int = EDGE_RESAMPLES,
    seed: int = 0,
) -> Result[EntryEdge]:
    """The run's entry edge ratio and its p against ``resamples`` sets of seeded random entries."""
    if horizon < 1 or resamples < EDGE_RESAMPLES_LEAST:
        return invalid(
            "robustness",
            f"horizon_bars is a whole number above zero and resamples one of "
            f"{EDGE_RESAMPLES_LEAST} or more",
        )
    measured: list[tuple[UnitTrade, Decimal, tuple[Fraction, Fraction]]] = []
    for trade in trades:
        held = bars.get(trade.market_id, _NO_BARS)
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
            entry = held.price(held.ask_open[at] if trade.side is Side.LONG else held.bid_open[at])
            pairs.append(_excursions(held, at, trade.side, entry, risk, horizon))
        null.append(_ratio(pairs) or Fraction(0))
    reached = sum(1 for ratio in null if ratio >= observed)
    p = Fraction(reached + 1, resamples + 1)
    return Ok(EntryEdge(_text(observed), _text(p), len(measured), horizon, resamples))


def _trade_cost_r(trade: UnitTrade, held: CompactBars, profile: CostProfile | None) -> Decimal:
    """One trade's costs in its own R: the fill bar's spread, plus profiled slippage and
    commission on both fills."""
    risk = abs(trade.entry_price - trade.stop)
    start = _fill_bar(held, trade.opened_at.value_ns)
    if risk == 0 or start >= len(held):
        return Decimal(0)
    paid = held.price(held.ask_open[start] - held.bid_open[start]) / risk
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
    bars: Mapping[str, CompactBars],
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
        t.r - extra * _trade_cost_r(t, bars.get(t.market_id, _NO_BARS), profiles.get(t.market_id))
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
