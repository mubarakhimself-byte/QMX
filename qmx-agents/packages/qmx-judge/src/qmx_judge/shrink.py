"""Every market pulled toward the unit's whole result (Part B AD-207, the luckiest-market trap).

A market's mean trade R is shrunk toward the unit's mean over every market by n/(n+k): a market
with few trades keeps little of its own result, one with many keeps most of it. The study spec
fixes k's estimator before any run. The default, `spread`, is the empirical Bayes ratio of the
spread of trades inside a market to the spread between markets, so when the markets differ no more
than noise would make them, every market takes the unit's whole result and the best-looking one
is not believed. With one market there is no spread to read, and k falls back to the spec's k
(half weight at 100 trades, `judge.md` §6).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

__all__ = ["FALLBACK_K", "Shrunk", "estimate_k", "shrink"]

FALLBACK_K: Final = Decimal(100)


@dataclass(frozen=True, slots=True)
class Shrunk:
    market: str
    trades: int
    raw_r: Decimal
    """The market's own mean trade R."""
    shrunk_r: Decimal
    weight: Decimal
    """n/(n+k): the share of its own result the market keeps."""


def _mean(values: Sequence[Decimal]) -> Decimal:
    return sum(values, Decimal(0)) / len(values)


def estimate_k(markets: Mapping[str, Sequence[Decimal]], fallback: Decimal) -> Decimal | None:
    """k from the spread between markets; None when that spread is no bigger than noise, which
    sends every market to the whole result. Fewer than two markets with two trades: `fallback`."""
    judged = [rs for rs in markets.values() if len(rs) >= 2]
    if len(judged) < 2:
        return fallback
    total = sum(len(rs) for rs in judged)
    means = [_mean(rs) for rs in judged]
    within = sum(
        (sum(((r - m) ** 2 for r in rs), Decimal(0)) for rs, m in zip(judged, means, strict=True)),
        Decimal(0),
    ) / (total - len(judged))
    centre = _mean(means)
    between = sum(((m - centre) ** 2 for m in means), Decimal(0)) / (len(means) - 1)
    noise = _mean([within / len(rs) for rs in judged])
    spread = between - noise
    if spread <= 0:
        return None
    return within / spread


def shrink(markets: Mapping[str, Sequence[Decimal]], k: Decimal | None) -> tuple[Shrunk, ...]:
    """Each market with trades, shrunk toward the mean trade R over every market's trades."""
    everything = [r for rs in markets.values() for r in rs]
    if not everything:
        return ()
    whole = _mean(everything)
    found: list[Shrunk] = []
    for market, rs in sorted(markets.items()):
        if not rs:
            continue
        n = Decimal(len(rs))
        weight = Decimal(0) if k is None else n / (n + k)
        raw = _mean(rs)
        found.append(Shrunk(market, len(rs), raw, whole + weight * (raw - whole), weight))
    return tuple(found)
