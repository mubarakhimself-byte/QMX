"""The node's facts: its rates from the feed's record, and its account as the venue states it.

Same formula, same ``provided`` list and same conversion lookup as QMB for the rate: all three are
imported from ``qmb.host.facts`` rather than spelled again, so one fact is never computed two
ways. The node reads the newest bar its recording kept for the conversion market, and never a bar
knowable after the instant being priced.

The account's facts are the node's own adapter over the one construction in ``qmf``
(:func:`~qmf.risk.facts.account_facts`): the venue's cash re-read on this node's timer, the risk
the positions it holds carry at their stops, and the plain words of how each was read. The timer
and the venue call live in :meth:`LiveAccount.refresh` and nowhere else, so a read from inside a
unit's pass never becomes a venue round trip.

A ``ConversionRef`` names the market by its record's id; this node keys its feed and its
recording by the deployment's market id, so ``refs`` maps one to the other once, when the port is
built.

The cost cells are the node's too, with no second adapter to drift: the node runs QMB's handler,
which writes each fill into :class:`~qmb.host.facts.CostCells`, so a fill the venue made reads the
same cost on this node as a replay's fill reads in QMB. The node passes no cash port, so a fill's
commission is the record's stated one until the venue's deal cash is read.

The currency is named by the caller that binds an account, never defaulted here: the venue states
its deposit asset by id and nothing on this node turns that id into a name yet.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Protocol, runtime_checkable

from qmb.host.facts import (
    COST_CELL_MIN_FILLS,
    RATE_ABSENT,
    CostCells,
    conversions,
    cost_cell_name,
    provided,
    rate_fact,
)
from qmf.core.chrono import Instant
from qmf.core.refusal import Result, is_refusal
from qmf.risk.facts import (
    AccountFacts,
    AccountReading,
    Fact,
    Stake,
    account_facts,
    open_risk,
)
from qml.numbers import ConversionRef, InstrumentRecord
from qml.protocol.unit import QuoteBar

__all__ = [
    "BALANCE_READ_S",
    "BALANCE_STALE_S",
    "COST_CELL_MIN_FILLS",
    "RATE_ABSENT",
    "BalanceSource",
    "CostCells",
    "FeedRates",
    "LiveAccount",
    "RecordedBars",
    "conversions",
    "cost_cell_name",
    "provided",
    "rate_fact",
    "refs",
]

BALANCE_READ_S: Final[Decimal] = Decimal(15)
"""`[node] balance_read_s`, starting at 15 s: how often this node asks the venue for the account's
cash again. A labelled placeholder for the risk session, owner numbers talk: inside one 900 s bar
of the shipped record, and a re-read a bar would make the equity as old as the bars it sizes with.
Range: one second to one bar."""
BALANCE_STALE_S: Final[Decimal] = BALANCE_READ_S * 3
"""`[node] balance_stale_s`, starting at 45 s: three missed re-reads, after which the balance reads
``stale`` with the age it carries. A labelled placeholder for the risk session, owner numbers talk;
the read cadence times three, the way the clock fact's 180 s is three missed host probes."""


class RecordedBars(Protocol):
    """The bars this node's feed kept, newest last, as ``Recording`` answers them."""

    def recent(
        self, market: str, count: int, before_ns: int | None = None
    ) -> tuple[QuoteBar, ...]: ...


@runtime_checkable
class BalanceSource(Protocol):
    """A binding that can ask its venue for the account's cash again (AD-15).

    The node's venue answers one request; a paper binding beside it holds no session of its own,
    and a venue that cannot answer refuses, which leaves the last read in place.
    """

    def read_balance(self) -> Result[Decimal]: ...


def refs(records: Mapping[str, InstrumentRecord], currency: str) -> dict[str, ConversionRef]:
    """Each quote's conversion market by the market id this node keys its feed with."""
    by_record = {record.market_id: market for market, record in records.items()}
    return {
        quote: ConversionRef(by_record.get(ref.market_id, ref.market_id), ref.invert)
        for quote, ref in conversions(records.values(), currency).items()
    }


@dataclass(frozen=True, slots=True)
class FeedRates:
    """The rate each quote currency converts at, from the feed's last closed bar.

    ``refs`` is keyed by quote currency, with each market named as this node keys it. A market
    the feed has not closed a bar on yet answers nothing, which the converter names
    ``rate_absent``; a bar older than the converter's ``rate_stale_s`` is ``rate_stale``.
    """

    recording: RecordedBars
    refs: Mapping[str, ConversionRef]
    currency: str

    def rate(self, record: InstrumentRecord, instant: Instant) -> Fact | None:
        ref = self.refs.get(record.currency)
        if ref is None:
            return None
        bars = self.recording.recent(ref.market_id, 1, instant.value_ns + 1)
        if not bars:
            return None
        return rate_fact(bars[-1], ref.invert, "node:feed")


class LiveAccount:
    """The node's account facts: the venue's cash re-read on this node's timer (AD-15).

    ``refresh`` is the only call that asks the venue, and the runtime makes it at one point in its
    tick, after the pass that drives the units. ``read`` answers from the last read and never
    touches the venue, so a decision row written inside a pass cannot start a venue round trip. A
    re-read the venue refuses leaves the last balance standing, and its age then reads the fact
    ``stale`` with that read time still on it. ``supplied_by`` is who the basis names as the
    supplier of the cash: the venue, or the fake standing in for it.
    """

    def __init__(
        self,
        binding: Callable[[], object],
        *,
        currency: str,
        budget_share: Decimal,
        supplied_by: str = "the venue",
        read_s: Decimal = BALANCE_READ_S,
        stale_s: Decimal = BALANCE_STALE_S,
    ) -> None:
        self._binding = binding
        self.supplied_by = supplied_by
        self.currency = currency
        self.budget_share = budget_share
        self.read_s = read_s
        self.stale_s = stale_s
        self.read_at: Instant | None = None
        self.balance: Decimal | None = None
        self.refusals = 0
        """How many due re-reads the venue refused: a number a reader can watch climb."""

    def refresh(self, now: Instant) -> bool:
        """Ask the venue for the cash again when the timer is due; a refusal keeps the last read.

        True when the timer was due, so the caller re-states the account's facts from this read;
        the balance itself moves only when the venue answers. The binding is asked for at the
        call, not held, so a binding replaced under the runtime (the fake broker behind the real
        venue, or a session reopened) is the one read.
        """
        if self.read_at is not None and _nanos(now, self.read_at) < _nanos_of(self.read_s):
            return False
        binding = self._binding()
        if not isinstance(binding, BalanceSource):
            return True
        answered = binding.read_balance()
        if is_refusal(answered):
            self.refusals += 1
            return True
        self.balance, self.read_at = answered.value, now
        return True

    def read(
        self, now: Instant, *, stakes: Iterable[Stake], realised_since: Decimal | None
    ) -> AccountFacts:
        """The account's facts at ``now``, from the last venue read: no venue call is made here."""
        return account_facts(
            AccountReading(
                currency=self.currency,
                source="node:venue",
                equity_words=f"{self.supplied_by}'s balance, with no open profit marked",
                holds="the positions this node holds",
                read_at=self.read_at,
                balance=self.balance,
                open_risk=open_risk(stakes),
                budget_share=self.budget_share,
                realised_since=realised_since,
            ),
            now=now,
            stale_s=self.stale_s,
        )


def _nanos(now: Instant, since: Instant) -> int:
    """``now`` minus ``since`` in nanoseconds: zero when ``since`` is in the future."""
    span = now.difference(since)
    return 0 if is_refusal(span) else span.value.value_ns


def _nanos_of(seconds: Decimal) -> int:
    """A setting in seconds as nanoseconds, exactly."""
    return int(seconds * 1_000_000_000)
