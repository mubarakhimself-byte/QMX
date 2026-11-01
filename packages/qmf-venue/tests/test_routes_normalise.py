"""Recorded Hyperliquid, Binance USD-M and Bybit frames normalise into one event format.

The frames in `fixtures/routes/` were recorded from each venue's public websocket on
2026-11-01 (built by evidence/c07/owner-build-fixtures.py): level lists cut to three entries,
Hyperliquid's trade `users` addresses replaced by the zero address.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from qmf.venue.routes import (
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
    Route,
    Side,
    UnreadFrame,
)

FRAMES = Path(__file__).parent / "fixtures" / "routes"
LISTINGS = {
    "hyperliquid": Listing("BTC", "BTC/USDC:USDC", "btc"),
    "binance": Listing("BTCUSDT", "BTC/USDT:USDT", "btc"),
    "bybit": Listing("BTCUSDT", "BTC/USDT:USDT", "btc"),
}


def replay(venue: str) -> list[Event]:
    listing = LISTINGS[venue]
    route = Route(venue, [listing])
    events: list[Event] = []
    for line in (FRAMES / f"{venue}.jsonl").read_text("utf-8").splitlines():
        row = json.loads(line)
        if "rest" in row:
            events += route.snapshot(listing.native, row["rest"], row["receive_time_ns"])
        else:
            events += route.normalise(row["frame"], row["receive_time_ns"])
    return events


def prints(venue: str) -> list[tuple[str, str, Aggressor, str | None]]:
    return [
        (str(e.price), str(e.size), e.aggressor, e.trade_id)
        for e in replay(venue)
        if isinstance(e, Print)
    ]


def test_hyperliquid_trades_become_prints_with_the_aggressor_side() -> None:
    first = next(e for e in replay("hyperliquid") if isinstance(e, Print))
    assert first == Print(
        market_id="btc",
        instrument="BTC/USDC:USDC",
        venue_time=1793574574589000000,
        receive_time=1793574581127836100,
        price=Decimal("77992.0"),
        size=Decimal("0.00567"),
        aggressor=Aggressor.SELL,
        trade_id="935255941109813",
        source_level=TAPE,
    )
    assert prints("hyperliquid") == [
        ("77992.0", "0.00567", Aggressor.SELL, "935255941109813"),
        ("77992.0", "0.00038", Aggressor.SELL, "225802533567638"),
        ("77985.0", "0.13089", Aggressor.BUY, "138669895195547"),
        ("77984.0", "0.20676", Aggressor.SELL, "512202432646714"),
        ("77984.0", "0.09613", Aggressor.SELL, "241661161068285"),
    ]


def test_binance_and_bybit_trades_become_prints_with_the_aggressor_side() -> None:
    assert prints("binance") == [
        ("78011.70", "0.131", Aggressor.BUY, "3504035771"),
        ("78011.60", "0.034", Aggressor.SELL, "3504035772"),
        ("78011.70", "0.017", Aggressor.BUY, "3504035773"),
    ]
    assert prints("bybit") == [
        ("77981.80", "0.020", Aggressor.BUY, "298d02e2-2897-5c05-8808-14ba545b8bce"),
        ("77981.70", "0.014", Aggressor.SELL, "a69e5bc3-4f43-5449-8d34-973d1c532137"),
        ("77981.80", "0.004", Aggressor.BUY, "20ddb3b1-807c-54ba-a135-d644a2c13cf0"),
    ]
    bybit = next(e for e in replay("bybit") if isinstance(e, Print))
    assert (bybit.market_id, bybit.instrument, bybit.venue_time, bybit.source_level) == (
        "btc",
        "BTC/USDT:USDT",
        1793574582821000000,
        4,
    )


def test_hyperliquid_book_is_one_snapshot_in_the_one_format() -> None:
    books = [e for e in replay("hyperliquid") if isinstance(e, Book)]
    level = BookLevel
    assert books == [
        Book(
            instrument="BTC/USDC:USDC",
            receive_time=1793574581136821500,
            levels=(
                level(Side.BID, Decimal("77984.0"), Decimal("3.4648")),
                level(Side.BID, Decimal("77983.0"), Decimal("0.83706")),
                level(Side.BID, Decimal("77982.0"), Decimal("0.20691")),
                level(Side.ASK, Decimal("77985.0"), Decimal("3.0379")),
                level(Side.ASK, Decimal("77986.0"), Decimal("0.00064")),
                level(Side.ASK, Decimal("77990.0"), Decimal("0.32061")),
            ),
            kind=BookKind.SNAPSHOT,
            book_state=BookState.READY,
        )
    ]


@pytest.mark.parametrize(
    ("venue", "expected"),
    [
        (
            "binance",
            [
                ("snapshot", "ready", ("bid", "77983.60", "1.703")),
                ("delta", "rebuilding", ("bid", "7798.40", "0.000")),
                ("delta", "rebuilding", ("bid", "1000.00", "120.188")),
                ("snapshot", "ready", ("bid", "77983.60", "6.569")),
                ("delta", "ready", ("bid", "1000.00", "120.188")),
                ("delta", "ready", ("bid", "7798.40", "0.000")),
                ("delta", "ready", ("bid", "1000.00", "120.188")),
            ],
        ),
        (
            "bybit",
            [
                ("snapshot", "ready", ("bid", "77981.70", "1.729")),
                ("delta", "ready", ("bid", "77978.50", "0.150")),
                ("delta", "ready", ("bid", "77981.70", "1.173")),
                ("delta", "rebuilding", ("bid", "77972.90", "0.585")),
            ],
        ),
    ],
)
def test_book_deltas_are_ready_only_while_they_follow_the_last_snapshot(
    venue: str, expected: list[tuple[str, str, tuple[str, str, str]]]
) -> None:
    """Binance: the diff stream is rebuilding until the REST snapshot, the two deltas older than
    the snapshot are dropped, and the first that covers it is ready. Bybit: the fixture leaves
    out the delta with `u` 58528006, so the next one shows the lost frame."""
    books = [e for e in replay(venue) if isinstance(e, Book)]
    firsts = [b.levels[0] for b in books]
    assert [
        (b.kind.value, b.book_state.value, (top.side.value, str(top.price), str(top.size)))
        for b, top in zip(books, firsts, strict=True)
    ] == expected
    assert {len(b.levels) for b in books} == {6}


def test_quotes_and_bars_from_the_three_venues() -> None:
    quotes = {v: [e for e in replay(v) if isinstance(e, Quote)] for v in LISTINGS}
    assert quotes["bybit"][1] == Quote(
        instrument="BTC/USDT:USDT",
        venue_time=1793574580729000000,
        receive_time=1793574581484289300,
        bid=None,
        ask=Decimal("77981.80"),
        bid_size=None,
        ask_size=Decimal("6.198"),
        filled_side=FilledSide.ASK,
    )
    assert [(q.bid, q.ask, q.filled_side) for q in (quotes["hyperliquid"] + quotes["binance"])] == [
        (Decimal("77984.0"), Decimal("77985.0"), FilledSide.BOTH),
        (Decimal("77983.60"), Decimal("77983.70"), FilledSide.BOTH),
    ]
    bars = {v: next(e for e in replay(v) if isinstance(e, Bar)) for v in LISTINGS}
    assert bars["binance"] == Bar(
        instrument="BTC/USDT:USDT",
        period="PT1M",
        open_time=1793574600000000000,
        close_time=1793574659999000000,
        open=Decimal("78012.60"),
        high=Decimal("78016.00"),
        low=Decimal("78011.60"),
        close=Decimal("78011.70"),
        volume=Decimal("14.798"),
        tick_count=385,
        basis=Basis.TRADE,
        closed=False,
    )
    assert [
        (b.period, b.tick_count, b.close, b.closed) for b in (bars["hyperliquid"], bars["bybit"])
    ] == [
        ("PT1M", 384, Decimal("77984.0"), False),
        ("PT1M", None, Decimal("77981.8"), False),
    ]


def test_a_frame_the_route_cannot_read_is_refused_by_name() -> None:
    route = Route("hyperliquid", [LISTINGS["hyperliquid"]])
    with pytest.raises(UnreadFrame, match="hyperliquid frame not read: KeyError: 'ETH'"):
        route.normalise(
            {"channel": "bbo", "data": {"coin": "ETH", "time": 1, "bbo": [None, None]}}, 1
        )
    with pytest.raises(UnreadFrame, match="the venue sent an error: Invalid subscription"):
        route.normalise({"channel": "error", "data": "Invalid subscription"}, 1)
    with pytest.raises(UnreadFrame, match="sends its book snapshots in the stream itself"):
        route.snapshot("BTC", {}, 1)
    with pytest.raises(ValueError, match="no data route reads kraken"):
        Route("kraken", [])
