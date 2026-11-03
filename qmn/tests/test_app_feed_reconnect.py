"""No entry measures its stop from a quote held from before a feed drop (C-12e, LOOSE-ENDS B4).

A dropped session takes its last quotes with it. Until the venue quotes again after the
reconnect, an entry is held back with its reason; the first one sent after that measures its
stop distance from the fresh quote. Conformance venue only.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from qmf.core import Account, AccountRole, TypedRefusal, VenueId
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from qml.numbers import lots, parse_record
from qmn.app.feed_keeper import Bar, FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.reconciler import journal_sends
from qmn.app.runtime import Blocked, ConformanceAccount, OrderPath, Placed, Venue
from test_app_runtime import LIVE_FROM, RECORDS, month, play, unit_rows
from test_app_unknown_drill import cut_and_reconnect
from test_protection_every_order import FIRST_SEND, trading

T0 = 1_742_500_000_000_000_000
DAY = 86_400_000_000_000
MARKET = "fx.eurusd"
NO_QUOTE = (
    "venue not ready: no quote since its feed connected, so the stop distance cannot be"
    " measured yet"
)


def path_on(
    tmp_path: Path, source: RecordedSource, now: list[int]
) -> tuple[OrderPath, ConformanceAccount]:
    account = Account("demo-1", VenueId("icmarkets-ctrader"), AccountRole.DEMO)
    client = ConformanceAccount.open(account, Decimal("10000.00"))
    assert not isinstance(client, TypedRefusal), client
    feed = FeedKeeper("ctrader", "demo", source, (MARKET,), lambda: now[0], Recording(None))
    scope = WriterScope(JournalStream.NODE, "a4dqobyh", JournalWorld.DEMO, "pc", "node", "0.1.0")
    journal = JournalWriter.open(tmp_path, scope, clock=lambda: now[0], boot_epoch_id="b1")
    assert not isinstance(journal, TypedRefusal), journal

    def sleep(seconds: float) -> None:
        now[0] += int(seconds * 1e9)

    venue = Venue(client.value, feed)
    return OrderPath("a4dqobyh", venue, journal.value, lambda: now[0], sleep, lambda _: None), (
        client.value
    )


def enter(path: OrderPath, name: str) -> Placed | Blocked:
    record = parse_record(json.loads((RECORDS / "eurusd.json").read_text("utf-8")))
    assert not isinstance(record, TypedRefusal), record
    quantity = lots(Decimal("0.05"), record.value)
    assert not isinstance(quantity, TypedRefusal), quantity
    return path.entry(
        deployment_id="dep-1",
        client_order_id=name,
        label="qmx:a4dqobyh:dummy-trend-pullback",
        wire={
            "order": {"type": "market"},
            "direction": "long",
            "market_id": MARKET,
            "protection": {"stop": "1.07500"},
            "quantity": "0.05",
            "decision_row_id": f"row-{name[-1]}",
        },
        record=record.value,
        quantity=quantity.value,
        blocked_by=None,
    )


def test_after_a_30_second_silence_the_first_entry_waits_for_a_fresh_quote(
    tmp_path: Path,
) -> None:
    now = [T0]
    source = RecordedSource([])
    path, venue = path_on(tmp_path, source, now)
    feed = path.venue.feed
    source.play([Quote(MARKET, T0, Decimal("1.08000"), Decimal("1.08012"), "both")])
    feed.pump()
    source.silence(2)
    now[0] += 31_000_000_000
    feed.pump()
    dropped = feed.reason
    feed.pump()
    held_back = enter(path, "qa4dqobyh-first-1")
    source.play([Quote(MARKET, now[0], Decimal("1.08050"), Decimal("1.08062"), "both")])
    feed.pump()
    placed = enter(path, "qa4dqobyh-second-2")
    sends = journal_sends(tmp_path)
    assert not isinstance(sends, TypedRefusal), sends

    assert dropped == "silent for more than 30 s"
    assert (feed.reconnects, feed.ready) == (1, True)
    assert held_back == Blocked(NO_QUOTE)
    assert placed == Placed(Decimal("1.08062"))
    assert [(t.tags.client_order_id, t.reference) for t in venue.received if t.tags] == [
        ("qa4dqobyh-second-2", Decimal("1.08062"))
    ]
    assert {name: row["stop_distance"] for name, row in sends.value.items()} == {
        "qa4dqobyh-second-2": "0.00562"
    }


def test_the_dummy_entry_on_the_first_bar_after_a_reconnect_with_no_quote_is_held_back(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    play(node, FIRST_SEND)
    cut_and_reconnect(node)
    node.now[0] = FIRST_SEND
    node.source.play([Bar(market, bar) for at, market, bar in month().bars if at == FIRST_SEND])
    node.runtime.tick()
    sent_on_the_bar = list(node.account.received)
    play(node, LIVE_FROM + 2 * DAY, start=FIRST_SEND + 1)
    held_back = [g["detail"] for g in unit_rows(node, "guard")]

    assert node.feed.reconnects == 1
    assert sent_on_the_bar == []
    assert held_back[:1] == [NO_QUOTE]
    assert len(node.account.received) > 0
