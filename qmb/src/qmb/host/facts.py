"""One rate fact from one price, the account's facts, and the ways QMB reads them back.

The rate into the account's currency is the mid of the conversion market's two sides, read as an
exact ``Fraction``. It has to be exact: the converter floors at the lot step, and a ``Decimal``
1/150 in between floors a 1.50-lot USDJPY entry to 1.49. QMB reads the fact from the run folder's
conversion-market bars; the node reads it from its feed, and both compute it here, so one fact is
never spelled two ways.

The account surface is the second host fact here: ``ReplayAccount`` states the run's own cash and
the risk its positions carry, through the same :func:`~qmf.risk.facts.account_facts` the node's
adapter uses, so one host cannot report an account the other would not.

A run streams its bars, so ``ReplayRates`` walks one feed forward per conversion market and holds
one bar each however long the run. The G check's slice is bounded and is driven five times over,
so ``SliceRates`` reads its bars where they sit. Both answer the same ``rate`` question the
handler's ``RatePort`` asks.

The cost cells are the third host fact here (AD-15, "Costs are observed facts"). Each fill the one
handler records is priced against its arrival quote and its commission, and lands in the cell of
its market, venue and UTC hour. A cell reads ``uncalibrated`` until it has measured
``COST_CELL_MIN_FILLS`` fills, and until then its value is the measured cost blended with the
stressed one: the class's pooled cost, never below what the record states, times ``COST_STRESS``.
One handler serves one host's world, so a handler's cells never mix worlds. The node reads the same
cells, because it runs the same handler.

This module imports ``qml`` and ``qmf`` only. It never imports the node, and never raises out of
``rate``: a bar it cannot price is a fact it does not answer.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.refusal import TypedRefusal
from qmf.risk.facts import (
    AccountFacts,
    AccountReading,
    Fact,
    Stake,
    account_facts,
    open_risk,
    rate_name,
)
from qml.numbers import ConversionRef, InstrumentRecord
from qml.numbers.records import COST_STRESS, InstrumentClass, stated_cost
from qml.protocol.unit import QuoteBar

__all__ = [
    "COST_CELL_MIN_FILLS",
    "RATE_ABSENT",
    "BarFeed",
    "CostCell",
    "CostCells",
    "ReplayAccount",
    "ReplayRates",
    "SliceRates",
    "conversions",
    "cost_cell_name",
    "funding_name",
    "gap_factor_name",
    "provided",
    "rate_fact",
]

RATE_ABSENT: Final[str] = "rate_absent"
"""The skip name, and the run stamp, of a market whose conversion bars the host cannot read.
``qml/numbers/convert.py`` names the skip and the label repeats the word, so one word reads both."""

COST_CELL_MIN_FILLS: Final[int] = 50
"""`[costs] cell_min_fills`, starting at 50: the fills a cost cell measures before its own mean is
read as the cost, the same starting count as `[qmb] calibrated_min_fills`. A labelled placeholder
for the risk session, owner numbers talk. Range: 1 to 1000."""
_HOUR_NS: Final[int] = 3_600_000_000_000

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


@dataclass(frozen=True, slots=True)
class ReplayAccount:
    """QMB's account facts: the run's own book, read at the instant the run asks (AD-15).

    A replay has no venue to re-read, so its balance is its own cash book and it reads as fresh as
    the question; the margin and the stop-out price are the venue's, and a replay states neither,
    so they read absent rather than guessed. Open risk is the positions the run holds at their
    stops, priced by the same :class:`~qmf.risk.facts.Stake` arithmetic the node's adapter uses.
    """

    currency: str
    balance: Decimal
    budget_share: Decimal
    holds: str = "the positions this run holds"
    """Whose positions ``account.open_risk`` counts, as ``basis`` says it."""

    def read(
        self, instant: Instant, *, stakes: Iterable[Stake], realised_since: Decimal | None
    ) -> AccountFacts:
        """The account's facts at ``instant``: no venue stands behind a run's book."""
        return account_facts(
            AccountReading(
                currency=self.currency,
                source="qmb:replay",
                equity_words="the run's own balance, with no open profit marked",
                holds=self.holds,
                read_at=instant,
                balance=self.balance,
                open_risk=open_risk(stakes),
                budget_share=self.budget_share,
                realised_since=realised_since,
            ),
            now=instant,
            stale_s=Decimal(0),
        )


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


def cost_cell_name(market: str) -> str:
    """The fact name of one market's cost per fill, in price."""
    return f"market.cost_cell:{market}"


def gap_factor_name(market: str) -> str:
    """The fact name of the worst loss a stop on one market has filled at, in R of that stop."""
    return f"market.gap_factor:{market}"


def funding_name(market: str) -> str:
    """The fact name of the money one lot paid or took at one market's last carry booking."""
    return f"market.funding:{market}"


@dataclass(frozen=True, slots=True)
class CostCell:
    """What one market cost at one venue in one hour of the day, from the fills measured there."""

    fills: int = 0
    total: Decimal = Decimal(0)
    """Every measured fill's cost added up, in price: its spread past the arrival quote and its
    commission over one lot's value per point."""


class CostCells:
    """One host's cost cells, by market, venue and UTC hour, written from fills (AD-15).

    ``min_fills`` is ``[costs] cell_min_fills`` and ``stress`` is ``[costs] stress_factor``. A host
    builds one per handler; nothing here reads a venue or a journal.
    """

    def __init__(
        self, *, min_fills: int = COST_CELL_MIN_FILLS, stress: Decimal = COST_STRESS
    ) -> None:
        self.min_fills = min_fills
        self.stress = stress
        self._cells: dict[tuple[str, str, int], CostCell] = {}
        self._classes: dict[tuple[str, str, int], InstrumentClass] = {}

    @staticmethod
    def _key(market: str, record: InstrumentRecord, instant: Instant) -> tuple[str, str, int]:
        return (market, record.venue, instant.value_ns // _HOUR_NS % 24)

    def observe(
        self, market: str, record: InstrumentRecord, instant: Instant, cost: Decimal
    ) -> None:
        """Add one fill's cost, in price, to its cell."""
        key = self._key(market, record, instant)
        cell = self._cells.get(key, CostCell())
        self._cells[key] = CostCell(cell.fills + 1, cell.total + cost)
        self._classes[key] = record.instrument_class

    def cell(self, market: str, record: InstrumentRecord, instant: Instant) -> CostCell:
        """The cell a fill on ``market`` at ``instant`` lands in, empty before its first fill."""
        return self._cells.get(self._key(market, record, instant), CostCell())

    def stressed(self, record: InstrumentRecord) -> Decimal:
        """The cost this host reads for a market it has not measured enough of: every measured
        fill of the record's class pooled, never below the record's stated cost, stressed."""
        pooled = [
            cell
            for key, cell in self._cells.items()
            if self._classes[key] is record.instrument_class
        ]
        fills = sum(cell.fills for cell in pooled)
        stated = stated_cost(record)
        total = sum((cell.total for cell in pooled), Decimal(0))
        base = stated if not fills else max(stated, total / fills)
        return base * self.stress

    def fact(self, market: str, record: InstrumentRecord, instant: Instant) -> Fact:
        """``market.cost_cell:<market>`` at ``instant``: the cell's own mean once it has measured
        ``min_fills`` fills, and before that its fills blended with the stressed cost for the
        fills it still lacks, labelled ``uncalibrated``. A count below one reads as one, because
        the step that mints a held position's exits reads every cell and must never raise."""
        cell = self.cell(market, record, instant)
        need = max(self.min_fills, 1)
        source = f"{cell.fills} of {need} fills measured at this hour"
        if cell.fills >= need:
            return Fact(cell.total / cell.fills, instant, "open", source)
        missing = need - cell.fills
        value = (cell.total + missing * self.stressed(record)) / need
        return Fact(value, instant, "open", source, state="uncalibrated")
