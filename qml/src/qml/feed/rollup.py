"""Roll an account feed's base bars up to one unit's stream (AD-25)."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from qmf.core.chrono import Instant

from qml.protocol.unit import OHLC, QuoteBar

__all__ = ["roll_up"]

_NS = 1_000_000_000


def roll_up(base_bars: Sequence[QuoteBar], seconds: int) -> QuoteBar | None:
    """The closed ``seconds`` bucket ``base_bars`` builds, or None.

    ``base_bars`` is one bucket's base bars, oldest first, as the feed recorded them. The bucket
    is the epoch-aligned one that holds the first bar, as the feed aligns its own
    (``ctrader_account.py`` ``_bar``). It answers a bar only when the first base bar starts that
    bucket, so a bucket joined part way through (a restart, a reconnect) is dropped and never
    emitted, and only when a bar reaches or passes the bucket's end, so an open bucket is not
    emitted. Both quote sides roll: the first bar's open, the highest high, the lowest low and the
    last bar's close inside the bucket. A bar past the bucket's end belongs to the next bucket and
    is ignored.

    The base interval is read from the run's own spacing. A single bar is taken as the whole
    bucket, which a host passes only when the unit's stream is the feed's own base.
    """
    if not base_bars or seconds <= 0:
        return None
    first = base_bars[0]
    bucket_ns = seconds * _NS
    start_ns = first.knowable_at.value_ns - _base_ns(base_bars, bucket_ns)
    bucket_start = start_ns - start_ns % bucket_ns
    if start_ns != bucket_start:
        return None
    bucket_end = bucket_start + bucket_ns
    if not any(bar.knowable_at.value_ns >= bucket_end for bar in base_bars):
        return None
    inside = [bar for bar in base_bars if bar.knowable_at.value_ns <= bucket_end]
    return QuoteBar(
        Instant(bucket_end),
        _roll(inside, lambda bar: bar.bid),
        _roll(inside, lambda bar: bar.ask),
    )


def _base_ns(base_bars: Sequence[QuoteBar], bucket_ns: int) -> int:
    """The spacing between the run's bars, or the whole bucket when the run is one bar."""
    if len(base_bars) < 2:
        return bucket_ns
    return base_bars[1].knowable_at.value_ns - base_bars[0].knowable_at.value_ns


def _roll(bars: Sequence[QuoteBar], side: Callable[[QuoteBar], OHLC]) -> OHLC:
    return OHLC(
        side(bars[0]).open,
        max(side(bar).high for bar in bars),
        min(side(bar).low for bar in bars),
        side(bars[-1]).close,
    )
