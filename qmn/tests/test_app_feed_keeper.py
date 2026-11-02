"""The feed keeper: no reader sees half a book, and a silent socket reconnects (EX-02, TN-19)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qmf.core import TypedRefusal
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from test_app_runtime import LIVE_FROM, deploy, deployment, month, play, rig, settle, value

from qmn.app.feed_keeper import (
    Bar,
    Book,
    BookState,
    BookView,
    FeedKeeper,
    Level,
    RecordedSource,
    Recording,
    SessionState,
)

T0 = 1_762_000_000_000_000_000
SECOND = 1_000_000_000


def keeper(source: RecordedSource, now: list[int]) -> FeedKeeper:
    return FeedKeeper("ctrader", "demo", source, ("fx.eurusd",), lambda: now[0], Recording(None))


def level(side: str, price: str, size: str) -> Level:
    return Level("bid" if side == "bid" else "ask", Decimal(price), Decimal(size))


def test_a_session_dropped_mid_book_reads_rebuilding_until_a_fresh_snapshot() -> None:
    now = [T0]
    source = RecordedSource([])
    feed = keeper(source, now)
    snapshot = (level("bid", "1.08000", "5"), level("ask", "1.08010", "3"))
    source.play([Book("fx.eurusd", T0, snapshot, "snapshot")])
    source.play([Book("fx.eurusd", T0, (level("bid", "1.07990", "2"),), "delta")])
    feed.pump()
    feed.pump()
    before = feed.book("fx.eurusd")
    source.drop()
    feed.pump()
    dropped = (feed.state, feed.book("fx.eurusd"))
    source.play([Book("fx.eurusd", T0, (level("ask", "1.08020", "9"),), "delta")])
    feed.pump()
    rebuilding = feed.book("fx.eurusd")
    source.play([Book("fx.eurusd", T0, (level("bid", "1.08100", "1"),), "snapshot")])
    feed.pump()

    assert before == BookView(
        "fx.eurusd",
        BookState.READY,
        (level("ask", "1.08010", "3"), level("bid", "1.07990", "2"), level("bid", "1.08000", "5")),
    )
    assert dropped == (SessionState.DOWN, BookView("fx.eurusd", BookState.REBUILDING, ()))
    assert (feed.reconnects, rebuilding) == (1, BookView("fx.eurusd", BookState.REBUILDING, ()))
    assert feed.book("fx.eurusd") == BookView(
        "fx.eurusd", BookState.READY, (level("bid", "1.08100", "1"),)
    )


def test_a_socket_silent_past_the_bound_reconnects_and_is_not_ready_until_reverified() -> None:
    now = [T0]
    source = RecordedSource([])
    feed = keeper(source, now)
    feed.pump()
    source.silence(1)
    now[0] += 29 * SECOND
    feed.pump()
    within = (feed.state, feed.reconnects)
    source.silence(1)
    now[0] += 31 * SECOND
    feed.pump()
    silent = (feed.state, feed.reason)
    source.refuse_verify = True
    feed.pump()
    connected = (feed.state, feed.ready, feed.reconnects)
    source.refuse_verify = False
    feed.pump()

    assert within == (SessionState.READY, 0)
    assert silent == (SessionState.DOWN, "silent for more than 30 s")
    assert connected == (SessionState.CONNECTED, False, 1)
    assert (feed.state, feed.ready, source.connects, source.verified) == (
        SessionState.READY,
        True,
        2,
        2,
    )


def test_no_entry_is_placed_while_the_session_is_connected_but_not_ready(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    node.source.refuse_verify = True
    node.source.drop()
    play(node, LIVE_FROM + 2 * 86_400_000_000_000)
    blocked = list(node.account.received)
    guards = [
        row
        for row in value(node.node.call("journal_tail", {"streams": ["unit"]}))["rows"]
        if isinstance(row, dict) and row["kind"] == "guard"
    ]

    assert blocked == []
    assert node.feed.state is SessionState.CONNECTED
    assert len(guards) == 10
    assert {row["body"]["reason"] for row in guards if isinstance(row["body"], dict)} == {
        "health_stop"
    }
    assert value(node.node.call("status", {}))["venues"] == [
        {
            "venue": "ctrader",
            "environment": "demo",
            "session": "connected",
            "reason": "connected, capabilities not re-verified (unavailable dependency)",
            "reconnects": 1,
            "last_contact_ns": node.feed.last_heard_ns,
            "books": {"fx.eurusd": "rebuilding", "metal.xauusd": "rebuilding"},
        }
    ]


def test_the_recorded_bars_are_what_a_restarted_node_warms_up_from(tmp_path: Path) -> None:
    scope = WriterScope(JournalStream.MARKET, "ctrader.demo", JournalWorld.DEMO, "pc", "node", "0.1.0")
    now = [T0]
    writer = JournalWriter.open(tmp_path, scope, clock=lambda: now[0], boot_epoch_id="b1")
    assert not isinstance(writer, TypedRefusal), writer
    bars = [bar for _, market, bar in month().bars if market == "fx.eurusd"][:3]
    source = RecordedSource([])
    feed = FeedKeeper(
        "ctrader", "demo", source, ("fx.eurusd",), lambda: now[0], Recording(writer.value)
    )
    source.play([Bar("fx.eurusd", bar) for bar in bars])
    feed.pump()
    writer.value.close()
    reopened = Recording.open(tmp_path, None)

    assert reopened.recent("fx.eurusd", 10) == tuple(bars)
    assert reopened.recent("fx.eurusd", 2) == tuple(bars[1:])
    assert reopened.recent("metal.xauusd", 10) == ()
