"""Each venue's public websocket frames read into the internal market event format.

A reader takes one parsed frame, its receive time, the route's listings by native id and the
route's book chains, and returns the frame's events. Readers index the frame directly: the
route turns any shape a reader cannot read into one `UnreadFrame` at its boundary.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, TypeAlias

from qmf.venue.routes.model import (
    TAPE,
    Aggressor,
    Bar,
    Basis,
    Book,
    BookKind,
    BookLevel,
    BookState,
    Event,
    FilledSide,
    Listing,
    Print,
    Quote,
    Side,
)
from qmf.venue.spot import exact

Frame: TypeAlias = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Chain:
    """The last update id a ready book holds, and whether it came from a snapshot."""

    last: int
    from_snapshot: bool


Chains: TypeAlias = dict[str, Chain]
Reader: TypeAlias = Callable[[Frame, int, Mapping[str, Listing], Chains], list[Event]]


class UnreadFrame(ValueError):
    """A frame the route cannot read; the message names the venue and why."""


def ns(milliseconds: object) -> int:
    return int(str(milliseconds)) * 1_000_000


def price(text: object) -> Decimal:
    return exact(text)


def size(text: object) -> Decimal:
    return exact(text, positive=False)


PERIODS = {"m": "PT{}M", "h": "PT{}H", "d": "P{}D", "w": "P{}W", "M": "P{}M"}
BYBIT_PERIODS = {"D": "1d", "W": "1w", "M": "1M"}


def period(interval: str) -> str:
    """A venue's bar interval (`1m`, `4h`, `1d`, `1M`, or Bybit's minutes and `D`) as ISO 8601."""
    interval = BYBIT_PERIODS.get(interval, interval)
    if interval.isdigit():
        minutes = int(interval)
        return f"PT{minutes // 60}H" if minutes % 60 == 0 else f"PT{minutes}M"
    count, unit = interval[:-1], interval[-1:]
    if not count.isdigit() or unit not in PERIODS:
        raise ValueError(f"unknown bar interval {interval!r}")
    return PERIODS[unit].format(int(count))


def levels(bids: list[Any], asks: list[Any]) -> tuple[BookLevel, ...]:
    """Bids then asks, each as the venue's `[price, size]` pairs in the venue's order."""
    return tuple(
        BookLevel(side, price(level[0]), size(level[1]))
        for side, rows in ((Side.BID, bids), (Side.ASK, asks))
        for level in rows
    )


def _book(
    listing: Listing, receive_time: int, rows: tuple[BookLevel, ...], kind: BookKind, ready: bool
) -> Book:
    state = BookState.READY if ready else BookState.REBUILDING
    return Book(listing.instrument, receive_time, rows, kind, state)


def _quote(
    listing: Listing,
    venue_time: int | None,
    receive_time: int,
    bid: tuple[object, object] | None,
    ask: tuple[object, object] | None,
) -> list[Event]:
    if bid is None and ask is None:
        return []
    filled = FilledSide.BOTH if bid and ask else FilledSide.BID if bid else FilledSide.ASK
    return [
        Quote(
            listing.instrument,
            venue_time,
            receive_time,
            price(bid[0]) if bid else None,
            price(ask[0]) if ask else None,
            size(bid[1]) if bid else None,
            size(ask[1]) if ask else None,
            filled,
        )
    ]


def hyperliquid(
    frame: Frame, receive_time: int, listings: Mapping[str, Listing], chains: Chains
) -> list[Event]:
    """Hyperliquid's `trades`, `l2Book`, `bbo` and `candle` channels. A trade's `side` is the
    aggressor's: `B` bought, `A` sold. Every `l2Book` frame is a whole snapshot. A candle frame
    is the bar so far; the venue never marks one closed."""
    del chains
    channel = frame["channel"]
    if channel in {"subscriptionResponse", "pong"}:
        return []
    data = frame["data"]
    if channel == "error":
        raise ValueError(f"the venue sent an error: {data}")
    if channel not in {"trades", "l2Book", "bbo", "candle"}:
        raise ValueError(f"no reader for channel {channel!r}")
    if channel == "trades":
        return [
            Print(
                listings[trade["coin"]].market_id,
                listings[trade["coin"]].instrument,
                ns(trade["time"]),
                receive_time,
                price(trade["px"]),
                size(trade["sz"]),
                {"B": Aggressor.BUY, "A": Aggressor.SELL}.get(trade["side"], Aggressor.UNKNOWN),
                str(trade["tid"]),
                TAPE,
            )
            for trade in data
        ]
    listing = listings[data["coin"] if channel != "candle" else data["s"]]
    if channel == "l2Book":
        bids, asks = data["levels"]
        rows = levels([[x["px"], x["sz"]] for x in bids], [[x["px"], x["sz"]] for x in asks])
        return [_book(listing, receive_time, rows, BookKind.SNAPSHOT, True)]
    if channel == "bbo":
        bid, ask = data["bbo"]
        return _quote(
            listing,
            ns(data["time"]),
            receive_time,
            (bid["px"], bid["sz"]) if bid else None,
            (ask["px"], ask["sz"]) if ask else None,
        )
    return [
        Bar(
            listing.instrument,
            period(data["i"]),
            ns(data["t"]),
            ns(data["T"]),
            price(data["o"]),
            price(data["h"]),
            price(data["l"]),
            price(data["c"]),
            size(data["v"]),
            int(data["n"]),
            Basis.TRADE,
            False,
        )
    ]


def _binance_follows(data: Frame, chain: Chain) -> bool | None:
    """Whether a USD-M futures diff-depth event continues the book (True), is older than it
    (None), or shows a lost event (False), per Binance's local order book rules."""
    first, final, previous = int(data["U"]), int(data["u"]), int(data["pu"])
    if final < chain.last or (final == chain.last and not chain.from_snapshot):
        return None
    if chain.from_snapshot:
        return previous == chain.last or first <= chain.last <= final
    return previous == chain.last


def binance(
    frame: Frame, receive_time: int, listings: Mapping[str, Listing], chains: Chains
) -> list[Event]:
    """Binance's combined-stream frames: `aggTrade` and `trade`, `bookTicker`, `kline`, and
    `depthUpdate` from a partial book (`@depth5`, a snapshot) or the diff stream (`@depth`,
    deltas chained by `pu` from a REST snapshot). `m` true means the buyer made the market, so
    the seller was the aggressor."""
    if "result" in frame and "id" in frame:
        return []
    stream, data = str(frame["stream"]), frame["data"]
    listing = listings[data["s"]]
    event = data["e"]
    if event in {"aggTrade", "trade"}:
        maker = data["m"]
        aggressor = (
            Aggressor.SELL
            if maker is True
            else Aggressor.BUY
            if maker is False
            else Aggressor.UNKNOWN
        )
        return [
            Print(
                listing.market_id,
                listing.instrument,
                ns(data["T"]),
                receive_time,
                price(data["p"]),
                size(data["q"]),
                aggressor,
                str(data["a"] if event == "aggTrade" else data["t"]),
                TAPE,
            )
        ]
    if event == "bookTicker":
        return _quote(
            listing,
            ns(data.get("T", data.get("E"))),
            receive_time,
            (data["b"], data["B"]),
            (data["a"], data["A"]),
        )
    if event == "kline":
        bar = data["k"]
        return [
            Bar(
                listing.instrument,
                period(bar["i"]),
                ns(bar["t"]),
                ns(bar["T"]),
                price(bar["o"]),
                price(bar["h"]),
                price(bar["l"]),
                price(bar["c"]),
                size(bar["v"]),
                int(bar["n"]),
                Basis.TRADE,
                bar["x"] is True,
            )
        ]
    if event == "depthUpdate":
        rows = levels(data["b"], data["a"])
        if stream.split("@")[1].removeprefix("depth").isdigit():
            return [_book(listing, receive_time, rows, BookKind.SNAPSHOT, True)]
        chain = chains.get(listing.native)
        follows = None if chain is None else _binance_follows(data, chain)
        if chain is not None and follows is None:
            return []
        if follows:
            chains[listing.native] = Chain(int(data["u"]), from_snapshot=False)
        else:
            chains.pop(listing.native, None)
        return [_book(listing, receive_time, rows, BookKind.DELTA, bool(follows))]
    raise ValueError(f"no reader for event {event!r} on {stream}")


def binance_snapshot(
    answer: Frame, receive_time: int, listing: Listing, chains: Chains
) -> list[Event]:
    """Binance's REST depth answer: the snapshot the diff stream chains from."""
    chains[listing.native] = Chain(int(answer["lastUpdateId"]), from_snapshot=True)
    rows = levels(answer["bids"], answer["asks"])
    return [_book(listing, receive_time, rows, BookKind.SNAPSHOT, True)]


def bybit(
    frame: Frame, receive_time: int, listings: Mapping[str, Listing], chains: Chains
) -> list[Event]:
    """Bybit v5 public frames: `publicTrade`, `orderbook` (a snapshot, then deltas whose `u`
    counts up by one), `tickers` (a snapshot, then deltas carrying only what changed) and
    `kline`. A trade's `S` is the taker's side. Bybit's bars carry no trade count."""
    if "topic" not in frame and "op" in frame:
        return []
    topic = str(frame["topic"])
    channel, native = topic.split(".", 1)[0], topic.rsplit(".", 1)[-1]
    listing = listings[native]
    data = frame["data"]
    if channel == "publicTrade":
        return [
            Print(
                listing.market_id,
                listing.instrument,
                ns(trade["T"]),
                receive_time,
                price(trade["p"]),
                size(trade["v"]),
                {"Buy": Aggressor.BUY, "Sell": Aggressor.SELL}.get(trade["S"], Aggressor.UNKNOWN),
                str(trade["i"]),
                TAPE,
            )
            for trade in data
        ]
    if channel == "orderbook":
        rows, update = levels(data["b"], data["a"]), int(data["u"])
        if frame["type"] == "snapshot":
            chains[native] = Chain(update, from_snapshot=True)
            return [_book(listing, receive_time, rows, BookKind.SNAPSHOT, True)]
        chain = chains.get(native)
        if chain is not None and update <= chain.last:
            return []
        follows = chain is not None and update == chain.last + 1
        if follows:
            chains[native] = Chain(update, from_snapshot=False)
        else:
            chains.pop(native, None)
        return [_book(listing, receive_time, rows, BookKind.DELTA, follows)]
    if channel == "tickers":
        bid = (data["bid1Price"], data["bid1Size"]) if "bid1Price" in data else None
        ask = (data["ask1Price"], data["ask1Size"]) if "ask1Price" in data else None
        return _quote(listing, ns(frame["ts"]), receive_time, bid, ask)
    if channel == "kline":
        return [
            Bar(
                listing.instrument,
                period(str(bar["interval"])),
                ns(bar["start"]),
                ns(bar["end"]),
                price(bar["open"]),
                price(bar["high"]),
                price(bar["low"]),
                price(bar["close"]),
                size(bar["volume"]),
                None,
                Basis.TRADE,
                bar["confirm"] is True,
            )
            for bar in data
        ]
    raise ValueError(f"no reader for topic {topic!r}")


READERS: dict[str, Reader] = {"hyperliquid": hyperliquid, "binance": binance, "bybit": bybit}
"""One reader per venue, keyed by the venue name the instrument records use."""

SNAPSHOT_READERS = {"binance": binance_snapshot}
"""Venues whose diff stream chains from a REST book snapshot."""
