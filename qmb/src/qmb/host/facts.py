"""One rate fact from one price, and the two ways QMB reads it back (AD-10 "Currency", AD-15).

The rate into the account's currency is the mid of the conversion market's two sides, read as an
exact ``Fraction``. It has to be exact: the converter floors at the lot step, and a ``Decimal``
1/150 in between floors a 1.50-lot USDJPY entry to 1.49. QMB reads the fact from the run folder's
conversion-market bars; the node reads it from its feed, and both compute it here, so one fact is
never spelled two ways.

A run streams its bars, so ``ReplayRates`` walks one feed forward per conversion market and holds
one bar each however long the run. The G check's slice is bounded and is driven five times over,
so ``SliceRates`` reads its bars where they sit. Both answer the same ``rate`` question the
handler's ``RatePort`` asks.

This module imports ``qml`` and ``qmf`` only. It never imports the node, and never raises out of
``rate``: a bar it cannot price is a fact it does not answer.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from fractions import Fraction
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.refusal import TypedRefusal
from qmf.risk.facts import Fact, rate_name
from qml.numbers import ConversionRef, InstrumentRecord
from qml.protocol.unit import QuoteBar

__all__ = [
    "RATE_ABSENT",
    "BarFeed",
    "ReplayRates",
    "SliceRates",
    "conversions",
    "provided",
    "rate_fact",
]

RATE_ABSENT: Final[str] = "rate_absent"
"""The skip name, and the run stamp, of a market whose conversion bars the host cannot read.
``qml/numbers/convert.py`` names the skip and the label repeats the word, so one word reads both."""

BarFeed = Callable[[], Iterator[QuoteBar | TypedRefusal]]
"""One conversion market's closed bars, opened afresh each call, as a run folder keeps them."""


def rate_fact(bar: QuoteBar, invert: bool, source: str) -> Fact:
    """One conversion bar's mid as the account-currency rate, exact, or its reciprocal."""
    mid = (Fraction(bar.bid.close) + Fraction(bar.ask.close)) / 2
    if mid == 0:
        return Fact(None, bar.knowable_at, "open", source, state="absent")
    return Fact(1 / mid if invert else mid, bar.knowable_at, "open", source)


def conversions(records: Iterable[InstrumentRecord], currency: str) -> dict[str, ConversionRef]:
    """Each quote currency's conversion market, by the account currency it converts into."""
    found: dict[str, ConversionRef] = {}
    for record in records:
        ref = record.conversions.get(currency)
        if ref is not None and record.currency != currency:
            found[record.currency] = ref
    return found


def provided(records: Iterable[InstrumentRecord], currency: str) -> tuple[str, ...]:
    """The ``market.rate:<quote>`` fact names a host supplies for these records. One list for both
    hosts: the node imports this function rather than spelling a second one."""
    return tuple(rate_name(quote) for quote in sorted(conversions(records, currency)))


class ReplayRates:
    """A run's rate facts, from the conversion markets' bars read once, forward.

    ``refs`` is keyed by quote currency and ``feeds`` by the conversion market's id. Each feed is
    opened on first use and walked only as far as the instant being priced, so the run holds one
    bar per conversion market and never a bar knowable after that instant. A feed that answers a
    refusal is kept in ``refused`` for the run to answer instead of carrying on.
    """

    def __init__(
        self, currency: str, refs: Mapping[str, ConversionRef], feeds: Mapping[str, BarFeed]
    ) -> None:
        self.currency = currency
        self.refs = dict(refs)
        self.feeds = dict(feeds)
        self.refused: TypedRefusal | None = None
        self._cursors: dict[str, Iterator[QuoteBar | TypedRefusal]] = {}
        self._held: dict[str, QuoteBar] = {}
        self._pending: dict[str, QuoteBar | None] = {}

    def rate(self, record: InstrumentRecord, instant: Instant) -> Fact | None:
        ref = self.refs.get(record.currency)
        if ref is None:
            return None
        bar = self._at_or_before(ref.market_id, instant)
        return None if bar is None else rate_fact(bar, ref.invert, "qmb:replay")

    def _at_or_before(self, market: str, instant: Instant) -> QuoteBar | None:
        """The market's last bar knowable at ``instant``, walked from where the last call stopped.

        The handler prices at a frontier that only moves forward, so one cursor per market is
        enough, and it never reads past the instant it is asked about.
        """
        feed = self.feeds.get(market)
        if feed is None:
            return None
        cursor = self._cursors.get(market)
        if cursor is None:
            cursor = self._cursors[market] = feed()
            self._pending[market] = self._next(cursor)
        pending = self._pending.get(market)
        while pending is not None and pending.knowable_at.value_ns <= instant.value_ns:
            self._held[market] = pending
            pending = self._next(cursor)
        self._pending[market] = pending
        return self._held.get(market)

    def _next(self, cursor: Iterator[QuoteBar | TypedRefusal]) -> QuoteBar | None:
        """The next bar, or nothing at the end; a refusal is kept for the run to answer."""
        item = next(cursor, None)
        if isinstance(item, TypedRefusal):
            if self.refused is None:
                self.refused = item
            return None
        return item


class SliceRates:
    """A bounded slice's rate facts, read where its conversion bars sit (the G check)."""

    def __init__(
        self,
        currency: str,
        refs: Mapping[str, ConversionRef],
        bars: Mapping[str, Sequence[QuoteBar]],
    ) -> None:
        self.currency = currency
        self.refs = dict(refs)
        self._bars = {market: tuple(series) for market, series in bars.items()}
        self._stamps = {
            market: tuple(bar.knowable_at.value_ns for bar in series)
            for market, series in self._bars.items()
        }

    def rate(self, record: InstrumentRecord, instant: Instant) -> Fact | None:
        ref = self.refs.get(record.currency)
        if ref is None:
            return None
        series = self._bars.get(ref.market_id, ())
        index = bisect.bisect_right(self._stamps.get(ref.market_id, ()), instant.value_ns)
        return None if not index else rate_fact(series[index - 1], ref.invert, "qmb:g")
