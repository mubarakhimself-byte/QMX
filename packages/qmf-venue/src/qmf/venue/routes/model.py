"""The internal market event format every data route normalises into (Part C CONTRACTS.md §6).

Four events: `Print`, `Quote`, `Book` and `Bar`. Prices and sizes are exact decimals read from
the venue's own decimal text; times are integer nanoseconds since the Unix epoch.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias

TAPE = 4
"""The source level of an exchange's own trade tape (Part C EXTERNAL.md §4)."""


class Aggressor(StrEnum):
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


class Side(StrEnum):
    BID = "bid"
    ASK = "ask"


class FilledSide(StrEnum):
    """Which side a quote event carried; the other side is the last one known."""

    BID = "bid"
    ASK = "ask"
    BOTH = "both"


class BookKind(StrEnum):
    SNAPSHOT = "snapshot"
    DELTA = "delta"


class BookState(StrEnum):
    """`ready` once a snapshot holds and every delta since follows it; `rebuilding` before
    that, and again after a lost delta until the next snapshot."""

    REBUILDING = "rebuilding"
    READY = "ready"


class Basis(StrEnum):
    BID = "bid"
    ASK = "ask"
    MID = "mid"
    TRADE = "trade"


@dataclass(frozen=True, slots=True)
class Listing:
    """One instrument a route reads: the venue's own id for it and the instrument record's
    names (`symbol` as CCXT spells it, and `market_id`)."""

    native: str
    instrument: str
    market_id: str


@dataclass(frozen=True, slots=True)
class Print:
    market_id: str
    instrument: str
    venue_time: int | None
    receive_time: int
    price: Decimal
    size: Decimal
    aggressor: Aggressor
    trade_id: str | None
    source_level: int


@dataclass(frozen=True, slots=True)
class Quote:
    instrument: str
    venue_time: int | None
    receive_time: int
    bid: Decimal | None
    ask: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    filled_side: FilledSide


@dataclass(frozen=True, slots=True)
class BookLevel:
    """In a delta, a size of zero removes the level."""

    side: Side
    price: Decimal
    size: Decimal


@dataclass(frozen=True, slots=True)
class Book:
    instrument: str
    receive_time: int
    levels: tuple[BookLevel, ...]
    kind: BookKind
    book_state: BookState


@dataclass(frozen=True, slots=True)
class Bar:
    """`tick_count` is None when the venue's bar carries no trade count."""

    instrument: str
    period: str
    open_time: int
    close_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    tick_count: int | None
    basis: Basis
    closed: bool


Event: TypeAlias = Print | Quote | Book | Bar
