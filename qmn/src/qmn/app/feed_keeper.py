"""The feed keeper: one long market-data session per venue and environment (Part C AD-309).

It lives inside the node app, so the node's lifeline depends on no other app. It owns the
session to one venue and environment, one subscription per market, and fans every event out
in process: the venue's account sees each bar, the runtime drives its units on each closed
bar, and the recorder keeps every bar in the node's market journal, which is what a unit warms
up from when it is deployed.

Every source is normalised into the events of ``CONTRACTS.md`` section 6. A bar carries both
quote sides, as QML's ``QuoteBar`` does, because the shared unit handler fills on both.

Three rules keep a reader safe across a reconnect:

- "Connected" is not ready. The session is ready only once it is authenticated, subscribed
  and its capabilities are re-verified; until then :attr:`FeedKeeper.ready` is false and the
  order path places no entry (TN-19).
- After every reconnect each market's book is ``rebuilding`` until a fresh snapshot arrives.
  A delta that comes first is dropped, so no reader ever sees half a book (EX-02). The last
  quotes go with the dropped session, so no entry measures its stop from a price held from
  before the drop; until a fresh quote arrives the order path places no entry.
- A session that stays silent past ``silent_after_ns`` is dropped and opened again, so a dead
  socket that never says so is noticed.
- A socket the venue refuses is not retried on every turn. The first retry is immediate, so a
  dropped session still reopens at once, and after it the wait doubles to ``FEED_RETRY_CAP_S``,
  so a refused internet connection cannot sign in thousands of times an hour.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from qmf.core import Instant, Ok, Result, is_refusal
from qmf.data.journal_envelope import JournalStream, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter
from qml.protocol.unit import OHLC, QuoteBar

from qmn.app.healing import Backoff
from qmn.venue.conformance import submit_not_ready_refusal

__all__ = [
    "FEED_RETRY_CAP_S",
    "SILENT_AFTER_NS",
    "Bar",
    "Book",
    "BookState",
    "BookView",
    "Dropped",
    "FeedEvent",
    "FeedKeeper",
    "FeedSource",
    "Heartbeat",
    "Level",
    "Quote",
    "RecordedSource",
    "Recording",
    "SessionState",
]

SILENT_AFTER_NS: Final = 30_000_000_000
"""`[node] feed_silent_after_s`, starting at 30 s: how long a session may say nothing before
the keeper drops it and opens it again. cTrader asks for a heartbeat every 10 s, so a live
session that is silent for three of them is dead."""
FEED_RETRY_CAP_S: Final = 300.0
"""`[node] feed_retry_cap_s`, starting at 300 s: the longest wait between sign-ins after the
venue refuses the socket. `Backoff`'s 60 s default gives about 66 sign-ins an hour from the node's
200 ms tick, above the rule of 40."""
RECORDING_KEPT: Final = 10_000
"""`[node] recording_kept_bars`: the newest bars per market the recorder keeps in memory for
warm-up, the `local_queue_bound` default (NODE.md section 9)."""


class SessionState(StrEnum):
    DOWN = "down"
    CONNECTED = "connected"
    """Authenticated and subscribed, capabilities not yet re-verified: not ready."""
    READY = "ready"


class BookState(StrEnum):
    REBUILDING = "rebuilding"
    READY = "ready"


@dataclass(frozen=True, slots=True)
class Level:
    side: Literal["bid", "ask"]
    price: Decimal
    size: Decimal


@dataclass(frozen=True, slots=True)
class Quote:
    """A quote; ``filled_side`` says which side this event carried. The other side keeps its
    last value, as a one-sided cTrader spot event does."""

    market_id: str
    receive_time: int
    bid: Decimal | None
    ask: Decimal | None
    filled_side: Literal["bid", "ask", "both"]


@dataclass(frozen=True, slots=True)
class Book:
    market_id: str
    receive_time: int
    levels: tuple[Level, ...]
    kind: Literal["snapshot", "delta"]


@dataclass(frozen=True, slots=True)
class Bar:
    """One closed bar of a market, both quote sides."""

    market_id: str
    bar: QuoteBar


@dataclass(frozen=True, slots=True)
class Dropped:
    """The venue closed the session."""

    reason: str


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """The venue's keep-alive: the session is alive though nothing traded."""


FeedEvent = Quote | Book | Bar | Dropped | Heartbeat


class FeedSource(Protocol):
    """One venue's market-data session, as the feed keeper drives it."""

    def connect(self) -> Result[None]:
        """Open and authenticate the session."""
        ...

    def subscribe(self, markets: Sequence[str], /) -> Result[None]: ...

    def verify(self) -> Result[None]:
        """Re-verify the venue's capabilities on this session."""
        ...

    def read(self) -> Sequence[FeedEvent]:
        """What arrived since the last read; nothing when the session is silent."""
        ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class BookView:
    """What a reader sees of one market's book: no levels while it rebuilds."""

    market_id: str
    book_state: BookState
    levels: tuple[Level, ...]


def _sides(ohlc: OHLC) -> list[str]:
    return [str(ohlc.open), str(ohlc.high), str(ohlc.low), str(ohlc.close)]


def _ohlc(cells: object) -> OHLC:
    values = [Decimal(str(cell)) for cell in cast("Sequence[object]", cells)]
    return OHLC(values[0], values[1], values[2], values[3])


class Recording:
    """The node's own recording of closed bars: the market journal, read back for warm-up.

    Each bar is one ``bar`` row of the market journal, written through Part B's writer as it
    arrives. :meth:`open` reads the newest ``kept`` bars of each market back, so a unit
    deployed after a restart warms up from what this node recorded before it.
    """

    def __init__(self, writer: JournalWriter | None, kept: int = RECORDING_KEPT) -> None:
        self._writer = writer
        self._kept = kept
        self._bars: dict[str, deque[QuoteBar]] = {}

    @classmethod
    def open(
        cls, root: Path, writer: JournalWriter | None, kept: int = RECORDING_KEPT
    ) -> Recording:
        recording = cls(writer, kept)
        for folder in stream_folders(root):
            if not folder.name.startswith(f"{JournalStream.MARKET.source}."):
                continue
            lines = read_committed(folder)
            if is_refusal(lines):
                continue
            for line in lines.value:
                if isinstance(line, JournalLine) and line.record.get("kind") == "bar":
                    body = cast("Mapping[str, object]", line.record.get("body", {}))
                    recording.keep(str(body["market_id"]), _bar_of(body))
        return recording

    def keep(self, market: str, bar: QuoteBar) -> None:
        held = self._bars.setdefault(market, deque(maxlen=self._kept))
        if not held or bar.knowable_at.value_ns > held[-1].knowable_at.value_ns:
            held.append(bar)

    def add(self, market: str, bar: QuoteBar) -> Result[None]:
        """Write the bar to the market journal, then keep it for warm-up."""
        if self._writer is not None:
            body: dict[str, object] = {
                "market_id": market,
                "knowable_at": bar.knowable_at.value_ns,
                "bid": _sides(bar.bid),
                "ask": _sides(bar.ask),
            }
            written = self._writer.append(
                "bar",
                body,
                RowFacts(ts_recv=bar.knowable_at.value_ns, clock_ok=False, market_id=market),
            )
            if is_refusal(written):
                return written
        self.keep(market, bar)
        return Ok(None)

    def recent(self, market: str, count: int, before_ns: int | None = None) -> tuple[QuoteBar, ...]:
        """The newest ``count`` recorded bars of ``market``, oldest first."""
        held = [
            bar
            for bar in self._bars.get(market, ())
            if before_ns is None or bar.knowable_at.value_ns < before_ns
        ]
        return tuple(held[-count:]) if count > 0 else ()


def _bar_of(body: Mapping[str, object]) -> QuoteBar:
    return QuoteBar(
        Instant(int(cast("int", body["knowable_at"]))), _ohlc(body["bid"]), _ohlc(body["ask"])
    )


@dataclass
class FeedKeeper:
    """One venue and environment's market-data session on this machine."""

    venue: str
    environment: str
    source: FeedSource
    markets: tuple[str, ...]
    clock_ns: Callable[[], int]
    recording: Recording
    silent_after_ns: int = SILENT_AFTER_NS
    state: SessionState = SessionState.DOWN
    reconnects: int = 0
    last_heard_ns: int = 0
    reason: str = "not opened yet"
    retry_at_ns: int = 0
    """When the next sign-in may be tried; 0 while none is waiting."""
    _failures: int = 0
    _backoff: Backoff = field(default_factory=lambda: Backoff(cap_s=FEED_RETRY_CAP_S))
    _books: dict[str, tuple[BookState, tuple[Level, ...]]] = field(
        default_factory=dict[str, tuple[BookState, tuple[Level, ...]]]
    )
    _quotes: dict[str, Quote] = field(default_factory=dict[str, Quote])
    _listeners: list[Callable[[Bar], None]] = field(default_factory=list[Callable[[Bar], None]])
    _opened: bool = False

    @property
    def ready(self) -> bool:
        """Authenticated, subscribed and re-verified: only then may an entry be placed."""
        return self.state is SessionState.READY

    def listen(self, listener: Callable[[Bar], None]) -> None:
        """``listener`` sees every closed bar, before the runtime drives its units on it."""
        self._listeners.append(listener)

    def book(self, market: str) -> BookView:
        state, levels = self._books.get(market, (BookState.REBUILDING, ()))
        return BookView(market, state, levels if state is BookState.READY else ())

    def quote(self, market: str) -> Quote | None:
        return self._quotes.get(market)

    def pump(self) -> tuple[Bar, ...]:
        """One turn: reopen a session that is down, re-verify one that is only connected, then
        take what arrived. A read that brings nothing past ``silent_after_ns`` since the last
        word drops the session, and the next turn opens it again.

        Answers the closed bars this turn brought, after every listener saw each of them.
        """
        now = self.clock_ns()
        if self.state is SessionState.DOWN:
            if now < self.retry_at_ns:
                return ()
            if not self._open(now):
                self._wait(now)
                return ()
        if self.state is SessionState.CONNECTED:
            self._verify()
        events = self.source.read()
        if events:
            self.last_heard_ns = now
        elif now - self.last_heard_ns > self.silent_after_ns:
            self._drop(f"silent for more than {self.silent_after_ns / 1e9:g} s")
            return ()
        bars: list[Bar] = []
        for event in events:
            match event:
                case Heartbeat():
                    pass
                case Dropped(reason=reason):
                    self._drop(f"the venue closed the session: {reason}")
                    break
                case Book(kind="snapshot"):
                    self._books[event.market_id] = (BookState.READY, event.levels)
                case Book():
                    state, levels = self._books.get(event.market_id, (BookState.REBUILDING, ()))
                    if state is BookState.READY:
                        self._books[event.market_id] = (state, _apply(levels, event.levels))
                case Quote():
                    self._quotes[event.market_id] = _merge(self._quotes.get(event.market_id), event)
                case Bar():
                    recorded = self.recording.add(event.market_id, event.bar)
                    if is_refusal(recorded):
                        self.reason = f"a bar could not be recorded ({recorded.category.value})"
                    for listener in self._listeners:
                        listener(event)
                    bars.append(event)
        return tuple(bars)

    def drop(self, reason: str, /) -> None:
        """Drop the session now, so the next pump opens it again: a deployment that added a
        market widens through this, the reconnect path the reconcile already resets."""
        self._drop(reason)

    def _open(self, now: int) -> bool:
        if self._opened:
            self.reconnects += 1
        self._opened = True
        for market in self.markets:
            self._books[market] = (BookState.REBUILDING, ())
        for step, done in (
            ("connect", self.source.connect),
            ("subscribe", lambda: self.source.subscribe(self.markets)),
        ):
            answered = done()
            if is_refusal(answered):
                self.reason = f"{step} refused ({answered.category.value})"
                self.source.close()
                return False
        self.state = SessionState.CONNECTED
        self.last_heard_ns = now
        self.retry_at_ns = 0
        self._failures = 0
        self._backoff.attempts = 0
        self._verify()
        return True

    def _wait(self, now: int) -> None:
        """Arm the next sign-in after a refused one. The first retry is immediate, so a dropped
        session keeps reopening on the next turn; after it the wait doubles to the cap."""
        wait = 0.0 if self._failures == 0 else self._backoff.next(now)
        self._failures += 1
        self.retry_at_ns = now + int(wait * 1e9)
        if wait:
            self.reason = f"{self.reason}; the next sign-in waits {wait:g} s"

    def _verify(self) -> None:
        verified = self.source.verify()
        if is_refusal(verified):
            self.reason = f"connected, capabilities not re-verified ({verified.category.value})"
            return
        self.state = SessionState.READY
        self.reason = "ready"

    def _drop(self, reason: str) -> None:
        self.source.close()
        self.state = SessionState.DOWN
        self.reason = reason
        self._quotes.clear()
        for market in self.markets:
            self._books[market] = (BookState.REBUILDING, ())

    def document(self) -> dict[str, object]:
        return {
            "venue": self.venue,
            "environment": self.environment,
            "session": self.state.value,
            "reason": self.reason,
            "reconnects": self.reconnects,
            "last_contact_ns": self.last_heard_ns or None,
            "books": {market: self.book(market).book_state.value for market in self.markets},
        }


def _apply(levels: tuple[Level, ...], changes: Iterable[Level]) -> tuple[Level, ...]:
    """A delta's levels replace the same side and price; size zero removes the level."""
    book = {(level.side, level.price): level for level in levels}
    for change in changes:
        if change.size == 0:
            book.pop((change.side, change.price), None)
        else:
            book[(change.side, change.price)] = change
    return tuple(sorted(book.values(), key=lambda level: (level.side, level.price)))


def _merge(last: Quote | None, event: Quote) -> Quote:
    if last is None or event.filled_side == "both":
        return event
    bid = event.bid if event.filled_side == "bid" else last.bid
    ask = event.ask if event.filled_side == "ask" else last.ask
    return Quote(event.market_id, event.receive_time, bid, ask, event.filled_side)


@dataclass
class RecordedSource:
    """The conformance venue's market data: a recorded day played back, one step per read.

    Each step is the events one read answers, and a read with no step left answers the venue's
    :class:`Heartbeat`. :meth:`drop` makes the next read answer :class:`Dropped`, and
    :meth:`silence` makes the next reads answer nothing, as a dead socket does. No network and
    no credentials.
    """

    steps: list[tuple[FeedEvent, ...]]
    connects: int = 0
    verified: int = 0
    subscribed: tuple[str, ...] = ()
    refuse_verify: bool = False
    _silent: int = 0
    _dropping: bool = False
    _open: bool = False

    def connect(self) -> Result[None]:
        self.connects += 1
        self._open = True
        return Ok(None)

    def subscribe(self, markets: Sequence[str], /) -> Result[None]:
        self.subscribed = tuple(markets)
        return Ok(None)

    def verify(self) -> Result[None]:
        if self.refuse_verify:
            return submit_not_ready_refusal()
        self.verified += 1
        return Ok(None)

    def read(self) -> Sequence[FeedEvent]:
        if not self._open:
            return ()
        if self._dropping:
            self._dropping = False
            return (Dropped("conformance drop"),)
        if self._silent > 0:
            self._silent -= 1
            return ()
        return self.steps.pop(0) if self.steps else (Heartbeat(),)

    def close(self) -> None:
        self._open = False

    def drop(self) -> None:
        self._dropping = True

    def silence(self, reads: int) -> None:
        self._silent = reads

    def play(self, events: Iterable[FeedEvent]) -> None:
        self.steps.append(tuple(events))
