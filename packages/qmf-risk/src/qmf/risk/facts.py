"""The one fact surface's types (AD-15): a value, its age, its source, its supply, its fail mode.

Every fact reads the same way in both hosts: ``value`` in the unit its reader expects, ``ts``
the instant it was read, ``source`` who supplied it, ``fail_mode`` what a missing value means
for the market, and ``state`` how good the supply is. One naming function keeps the two host
adapters on one key (``market.rate:<quote>``, ``account.equity``), so one fact is never computed
under two names.

The account surface is here because both hosts supply it: the node re-reads the venue's cash on a
timer and QMB reads its own book, and both turn their reading into the same seven facts through
:func:`account_facts`. Open risk is summed once, from the positions a host holds at their stops.

This module imports ``qmf-core`` only. Nothing here runs a block (AD-21).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Literal, cast

from qmf.core import Instant, is_refusal

__all__ = [
    "ACCOUNT_NAMES",
    "ACCOUNT_PREFIX",
    "RATE_PREFIX",
    "AccountFacts",
    "AccountReading",
    "Fact",
    "Stake",
    "account_facts",
    "account_name",
    "money_at_stake",
    "open_risk",
    "rate_name",
]

RATE_PREFIX: Final[str] = "market.rate:"
"""The fact-name prefix of a market's rate into the account's currency (AD-10, AD-15)."""
ACCOUNT_PREFIX: Final[str] = "account."
"""The fact-name prefix of the account surface (AD-15)."""
ACCOUNT_NAMES: Final[tuple[str, ...]] = (
    "equity",
    "balance",
    "open_risk",
    "margin_headroom",
    "liquidation_distance",
    "budget_share",
    "realised_since",
)
"""Every account fact, in the order a receipt reads them."""

_NANOS_PER_SECOND: Final[int] = 1_000_000_000


def rate_name(quote: str) -> str:
    """The fact name for one unit of ``quote`` in the account's currency."""
    return f"{RATE_PREFIX}{quote}"


def account_name(field: str) -> str:
    """The fact name for one account number."""
    return f"{ACCOUNT_PREFIX}{field}"


@dataclass(frozen=True, slots=True)
class Fact:
    """One value from one source, with its age and the supply it has right now.

    ``state`` says how good the supply is: ``ok`` read as written, ``stale`` past its reader's
    limit, ``absent`` never supplied, ``uncalibrated`` measured but not yet trusted. ``fail_mode``
    says what a missing value means for the market: ``open`` keeps trading, ``closed`` stops
    entries, ``neutral`` treats it as absent without a fault.
    """

    value: Decimal | Fraction | None
    ts: Instant | None
    fail_mode: Literal["open", "closed", "neutral"]
    source: str
    state: Literal["ok", "stale", "absent", "uncalibrated"] = "ok"

    def is_stale(self, now: Instant, stale_s: Decimal) -> bool:
        """True when this fact was read more than ``stale_s`` seconds before ``now``.

        A fact with no read time cannot be shown fresh, so it reads stale.
        """
        if self.ts is None:
            return True
        span = now.difference(self.ts)
        if is_refusal(span):
            return True
        age = Fraction(span.value.value_ns)
        return age > Fraction(*stale_s.as_integer_ratio()) * _NANOS_PER_SECOND


@dataclass(frozen=True, slots=True)
class Stake:
    """One position a host holds, as the money it loses if its stop fills.

    ``entry``, ``stop``, ``quantity`` and the record's ``value_per_point`` are the four numbers the
    sizer divides by, and ``rate`` is the ``market.rate:<quote>`` fact that converts the figure
    into the account's currency. A host assembles one per position it holds; nothing here reads a
    venue, and a position with no stop is a stake that cannot be priced.
    """

    entry: Decimal
    stop: Decimal | None
    quantity: Decimal
    value_per_point: Decimal
    rate: Fact | None = None


def money_at_stake(stake: Stake) -> Decimal | None:
    """The money one position loses if its stop fills, in its quote currency.

    ``|entry - stop| * quantity * value_per_point``: the same arithmetic the sizer's loss per lot
    uses, so the account's open risk and its sizes never disagree about what one position risks.
    """
    if stake.stop is None:
        return None
    return abs(stake.entry - stake.stop) * stake.quantity * stake.value_per_point


def open_risk(stakes: Iterable[Stake]) -> Decimal | None:
    """The account's open risk at the stops, in the account's currency.

    Each stake's money at its stop at its own rate, summed exactly. None when any stake cannot be
    priced, because a partial sum reads as less risk than the account carries.
    """
    total = Fraction(0)
    for stake in stakes:
        money = money_at_stake(stake)
        if money is None or stake.rate is None or stake.rate.value is None:
            return None
        total += Fraction(money) * Fraction(stake.rate.value)
    return Decimal(total.numerator) / Decimal(total.denominator)


@dataclass(frozen=True, slots=True)
class AccountReading:
    """What one host read of its account, before it is a fact set (AD-15).

    ``read_at`` is when the host last read the venue's cash, and every figure the venue states is
    only as fresh as that read. ``equity_words`` says plainly how the host arrived at its equity,
    and ``holds`` whose positions its open risk counts: the two things ``basis`` reports.
    """

    currency: str
    source: str
    equity_words: str
    holds: str
    read_at: Instant | None = None
    balance: Decimal | None = None
    open_risk: Decimal | None = None
    margin_headroom: Decimal | None = None
    liquidation_distance: Decimal | None = None
    budget_share: Decimal | None = None
    realised_since: Decimal | None = None


@dataclass(frozen=True, slots=True)
class AccountFacts:
    """The account as one read of it: seven named facts and the plain words of how they were read.

    ``basis`` is words, not a fact: a ``Fact`` value is a number every reader divides with, so the
    sentence that says marked-or-balance-only and whose positions open risk counts lives here.
    """

    currency: str
    equity: Fact
    balance: Fact
    open_risk: Fact
    margin_headroom: Fact
    liquidation_distance: Fact
    budget_share: Fact
    realised_since: Fact
    basis: str

    def facts(self) -> Mapping[str, Fact]:
        """Every fact by its ``account.*`` name, in one order."""
        return MappingProxyType(
            {account_name(name): cast(Fact, getattr(self, name)) for name in ACCOUNT_NAMES}
        )

    def document(self) -> Mapping[str, object]:
        """The surface as JSON-able text: each fact's value, read time, source and supply."""
        return {
            "currency": self.currency,
            "basis": self.basis,
            "facts": {
                name: {
                    "value": None if fact.value is None else f"{fact.value}",
                    "ts": None if fact.ts is None else fact.ts.value_ns,
                    "source": fact.source,
                    "state": fact.state,
                    "fail_mode": fact.fail_mode,
                }
                for name, fact in self.facts().items()
            },
        }


def _stated(value: Decimal | None, ts: Instant | None, source: str) -> Fact:
    """A figure the venue stated: as fresh as the instant the host read it."""
    return Fact(
        value,
        ts,
        "open",
        source,
        state="ok" if value is not None and ts is not None else "absent",
    )


def _computed(value: Decimal | None, now: Instant, source: str) -> Fact:
    """A figure the host worked out at this read: it is as fresh as the read itself."""
    return Fact(
        value,
        None if value is None else now,
        "open",
        source,
        state="absent" if value is None else "ok",
    )


def account_facts(reading: AccountReading, *, now: Instant, stale_s: Decimal) -> AccountFacts:
    """One account reading as the seven named facts, stamped at ``now``.

    The venue's cash and the equity built on it take the read's own time, so a balance the host
    has not re-read within ``stale_s`` reads ``stale`` with that time still on it. A number the
    host cannot supply reads ``absent``, never zero. Every fact's fail mode is ``open``: a missing
    account figure never blocks an exit.
    """
    balance = _stated(reading.balance, reading.read_at, reading.source)
    if balance.state == "ok" and balance.is_stale(now, stale_s):
        balance = replace(balance, state="stale")
    clauses = [
        f"equity is {reading.equity_words}",
        f"account.open_risk counts only {reading.holds} at their stops, never a position an agent"
        " opened at the venue",
    ]
    missing = [
        words
        for words, value in (
            ("margin headroom", reading.margin_headroom),
            ("liquidation distance", reading.liquidation_distance),
        )
        if value is None
    ]
    if missing:
        clauses.append(f"{' and '.join(missing)} read absent, because the host states neither")
    return AccountFacts(
        currency=reading.currency,
        equity=balance,
        balance=balance,
        open_risk=_computed(reading.open_risk, now, reading.source),
        margin_headroom=_computed(reading.margin_headroom, now, reading.source),
        liquidation_distance=_computed(reading.liquidation_distance, now, reading.source),
        budget_share=_computed(reading.budget_share, now, reading.source),
        realised_since=_computed(reading.realised_since, now, reading.source),
        basis="; ".join(clauses),
    )
