"""The practice venue: QMX's own shipped month played back over the conformance account.

A stranger has no broker on day one, so paper needs a binding whose prices answer and whose stops
are proven, with no sign-in and no socket (SPINE section 6, "Day one for a stranger"; FIXES S8).
This module builds that binding: :class:`ConformanceAccount` (the double the node already trades
in its tests) over a :class:`Replay` feed that answers the month in ``practice_bars/`` and then
falls quiet, heartbeat by heartbeat, as a venue whose session is open but silent.

Every card and every row this venue produces says what it is. The rows say ``world: paper`` in
their envelope, because a practice deployment runs on the paper lane; this module answers
:func:`stated`, and the runtime stamps ``venue_kind: practice`` and ``world: paper`` beside it, so
no card or row of the practice venue can be read as a broker's.

The account's role is ``PAPER_VALIDATION``, so a live lane on this binding stays refused by the
runtime's own check: practice is wired to where no money is, never to where some is.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Final

from qmf.core import Account, AccountRole, Instant, Ok, Result, VenueId, is_refusal
from qmf.data.journal_envelope import JournalWorld
from qml.protocol.unit import OHLC, QuoteBar

from qmn.app import runtime
from qmn.app.feed_keeper import Bar, FeedEvent, FeedKeeper, Heartbeat, Quote, Recording

__all__ = [
    "ACCOUNT",
    "BARS",
    "MARKETS",
    "PRACTICE",
    "SHIPPED_VENUE",
    "STATED",
    "Month",
    "Replay",
    "Refused",
    "account",
    "stated",
    "venue",
]

PRACTICE: Final = "practice"
"""The venue kind, stated on every card and row this binding produces."""
ACCOUNT: Final = "practice-1"
"""The account id the practice venue binds. No broker holds an account of this name."""
SHIPPED_VENUE: Final = "icmarkets-ctrader"
"""The venue QMX's shipped instrument records name, and the venue a practice account binds.

A command's stream is ``(VenueId, account)`` and an order is provable only on the stream of the
venue its instrument record names (``Command._validate_stream``), so a practice binding answers as
the venue the unit's own record names. What makes it practice is the kind, not the venue id: the
bars are QMX's shipped month, and no session to that venue is ever opened.
"""
ENVIRONMENT: Final = "paper"
"""The environment the practice session reads as: the paper world, stated on its status row."""
STATED: Final[Mapping[str, object]] = MappingProxyType(
    {"world": JournalWorld.PAPER.value, "venue_kind": PRACTICE}
)
"""What every card and row of this venue states about it."""
BAR_SECONDS: Final = 900
"""The shipped month is 15-minute bars, which is the stream the canary reads."""
BARS: Final = Path(__file__).with_name("practice_bars")
"""The month QMX ships (RC-17), the same series a first backtest reads."""
MARKETS: Final = ("fx.eurusd", "metal.xauusd")
"""The two markets the shipped month covers."""
SYMBOLS: Final = {"fx.eurusd": "EURUSD", "metal.xauusd": "XAUUSD"}
EQUITY: Final = Decimal("10000.00")
"""The practice account's starting balance: a labelled placeholder, owner numbers talk. Range:
above zero. It models fills and stops, not money (``ConformanceAccount`` says the same)."""
PRICES: Final = ("open", "high", "low", "close")
NO_STATEMENT: Final[Mapping[str, object]] = MappingProxyType({})
"""What a venue that is not the practice venue states: nothing, so its cards never change."""


class Refused(Exception):
    """Why the shipped month does not read as a month: a pair of files that disagree, or a bar
    file with no bar in it."""


@dataclass(frozen=True, slots=True)
class Month:
    """The shipped month, read once: every bar of every market, oldest close first."""

    bars: tuple[tuple[int, str, QuoteBar], ...]
    """``(close_ns, market_id, bar)``: the instant the bar closes, which is when a feed that
    played it would have handed it over."""

    @classmethod
    def ship(cls, folder: Path = BARS) -> Month:
        """Read ``folder``'s bid and ask month per symbol into both sides of each 15-minute bar."""
        found: list[tuple[int, str, QuoteBar]] = []
        for market, symbol in sorted(SYMBOLS.items()):
            bid, ask = _side(folder, symbol, "bid"), _side(folder, symbol, "ask")
            if [at for at, _ in bid] != [at for at, _ in ask]:
                raise Refused(f"{symbol}'s bid and ask months do not cover the same bars")
            for (opened, one), (_, other) in zip(bid, ask, strict=True):
                close = (opened + BAR_SECONDS) * 1_000_000_000
                found.append(
                    (close, market, QuoteBar(Instant(close), OHLC(*one), OHLC(*other)))
                )
        if not found:
            raise Refused(f"{folder} holds no month of bars")
        return cls(tuple(sorted(found, key=lambda item: item[0])))


def _side(folder: Path, symbol: str, side: str) -> list[tuple[int, tuple[Decimal, ...]]]:
    """One side's bars: the bar's opening time in whole seconds, and its four prices."""
    found = sorted(folder.glob(f"{symbol.lower()}-m15-{side}-*.csv"))
    if len(found) != 1:
        raise Refused(f"{folder} holds {len(found)} {symbol} {side} months, not one")
    try:
        with found[0].open(encoding="utf-8", newline="") as handle:
            rows = [
                (int(row["timestamp"]) // 1000, tuple(Decimal(row[price]) for price in PRICES))
                for row in csv.DictReader(handle)
            ]
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise Refused(f"{found[0].name} does not read as a month of bars: {error}") from error
    if not rows:
        raise Refused(f"{found[0].name} holds no bars")
    return rows


@dataclass
class Replay:
    """The shipped month as a venue's market data: no socket, no key, no clock of its own.

    A read answers every bar whose close the clock has reached since the last read, each as the
    closed bar and the quote that closed it, so an order measured on it reads a price. With no
    bar to give it answers a heartbeat, as an open session that is merely quiet does. Nothing
    here can reach a host: there is no client, no address and no session behind it.
    """

    month: Month
    clock_ns: Callable[[], int]
    after_ns: int = 0
    """The bars that closed at or before this instant are the venue's history, not its session."""
    opens: int = 0
    reads: int = 0
    _next: int = 0
    _opened: bool = False

    def __post_init__(self) -> None:
        self._next = next(
            (n for n, (at, _, _) in enumerate(self.month.bars) if at > self.after_ns),
            len(self.month.bars),
        )

    def connect(self) -> Result[None]:
        self.opens += 1
        self._opened = True
        return Ok(None)

    def subscribe(self, markets: Sequence[str], /) -> Result[None]:
        del markets
        return Ok(None)

    def verify(self) -> Result[None]:
        return Ok(None)

    def read(self) -> Sequence[FeedEvent]:
        self.reads += 1
        if not self._opened:
            return ()
        now = self.clock_ns()
        events: list[FeedEvent] = []
        while self._next < len(self.month.bars) and self.month.bars[self._next][0] <= now:
            at, market, bar = self.month.bars[self._next]
            events.append(Quote(market, at, bar.bid.close, bar.ask.close, "both"))
            events.append(Bar(market, bar))
            self._next += 1
        return tuple(events) if events else (Heartbeat(),)

    def close(self) -> None:
        self._opened = False


def account(venue_id: str = SHIPPED_VENUE) -> Account:
    """The practice account: a paper-validation account at the venue its records name."""
    return Account(ACCOUNT, VenueId(venue_id), AccountRole.PAPER_VALIDATION)


def venue(
    *,
    clock_ns: Callable[[], int],
    started_ns: int | None = None,
    equity: Decimal = EQUITY,
    month: Month | None = None,
    venue_id: str = SHIPPED_VENUE,
) -> Result[runtime.Venue]:
    """The practice venue, ready for the node's runtime: its account, its feed, its history.

    Every bar that closed at or before ``started_ns`` is the venue's history, so a unit deployed
    after it warms up from the shipped month instead of waiting for the month to play; the bars
    after it are the session, handed over as the clock passes their close.
    """
    shipped = Month.ship() if month is None else month
    start = 0 if started_ns is None else started_ns
    made = runtime.ConformanceAccount.open(account(venue_id), equity, venue_kind=PRACTICE)
    if is_refusal(made):
        return made
    recording = Recording(None)
    for at, market, bar in shipped.bars:
        if at <= start:
            recording.keep(market, bar)
    feed = FeedKeeper(
        venue_id,
        ENVIRONMENT,
        Replay(shipped, clock_ns, after_ns=start),
        MARKETS,
        clock_ns,
        recording,
    )
    feed.listen(made.value.on_bar)
    return Ok(runtime.Venue(made.value, feed))


def stated(client: object) -> Mapping[str, object]:
    """What every card and row of this binding states about it, or nothing for any other binding.

    ``client`` is a venue's account, or the paper lane that sits beside one and holds it as its
    binding. Empty for a broker, so a card that names a venue says only what that venue says.
    """
    held = getattr(client, "binding", client)
    return STATED if getattr(held, "venue_kind", "") == PRACTICE else NO_STATEMENT
