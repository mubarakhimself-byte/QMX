"""A node's records reach his Library, and no word in a reason can stop them (R15).

The node is C-12a's conformance node on a throwaway folder, trading the dummy unit on the synthetic
March 2025 slices (not evidence about any market). Its journal is the real writer's, and the rounds
are the real records job's, reading the node's real folder. No broker, key or token is read.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import os
import stat
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
import test_feed_relay
from qmf.core import is_refusal
from qmf.data.series import SeriesKey, SeriesStore
from qmf.venue.commands import CommandKind
from qmn.app.attribution import VenuePosition
from qmn.app.runtime import NodeUnit
from qmx_engine.ledger import redact
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store
from test_feed_relay import ACCOUNT, DAY, LIVE_FROM, Rig, guard_rows, play, rig

from qmx_host.market_data import MarketDoor
from qmx_host.records import Cadence, Harvester, Projection, Records, append_roots

BAR = 900_000_000_000
FIRST_TRADE_CLOSED = LIVE_FROM + 3 * 3_600_000_000_000
NOW = datetime(2025, 3, 25, tzinfo=UTC)
"""After every bar a test plays, and inside the rows' month."""
OPERATOR = Principal("operator")
SIGNALS = ("journal-unit", "dummy-trend-pullback", "signal", 2025, 3, "demo.pc")


def harvester(home: Path) -> Harvester:
    door = MarketDoor(root=home / "market")
    return Harvester(lambda: append_roots(home), door, home / "records", journals_open=True)


def rows_on_disk(home: Path, kind: str) -> int:
    journal = home / "apps" / "trading-node" / "data" / "journal"
    streams = journal.glob(f"journal-unit.{kind}.*/*.jsonl")
    return sum(len(path.read_bytes().splitlines()) for path in streams)


def signals_in_the_store(home: Path) -> int:
    key = SeriesKey.try_create(*SIGNALS)
    assert not is_refusal(key)
    state = SeriesStore(home / "market" / "series").state(key.value)
    assert state is not None
    return state.rows


def step(node: Rig) -> None:
    """One more bar, so a test can look between bars."""
    until = max(node.now[0], LIVE_FROM) + BAR
    play(node, until)
    node.now[0] = until


def status(node: Rig) -> dict[str, object]:
    answer = node.node.call("status", {})
    assert answer["ok"] is True, answer
    return cast("dict[str, object]", answer["value"])


def test_a_real_writer_row_lands_a_trade_and_a_paper_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = test_feed_relay.deployment
    monkeypatch.setattr(
        test_feed_relay,
        "deployment",
        lambda data, placement: {**live(data, placement), "lane": "paper"},  # pyright: ignore[reportUnknownLambdaType]
    )
    home = tmp_path / "QMX"
    node = rig(home, None)
    play(node, FIRST_TRADE_CLOSED)
    node.runtime.stop()

    with Store.open(tmp_path / "library", redactor=redact) as store:
        job = Records(
            harvester(home),
            Cadence,
            clock=lambda: NOW,
            projection=Projection(store, home / "records"),
            store=store,
        )
        first = job.round()
        heads = list(store.heads_on(MAIN))
        again = job.round()
        heads_again = list(store.heads_on(MAIN))
        views = [store.get(OPERATOR, object_id) for _item, object_id in heads]

    assert (first.trades, first.paper_runs, first.refusals) == (1, 1, ())
    assert (again.trades, again.paper_runs, again.refusals) == (0, 0, ())
    assert heads_again == heads
    assert sorted(view.kind for view in views) == ["artifact", "paper-run", "trade"]
    trade = next(view for view in views if view.kind == "trade")
    assert (trade.fields["account"], trade.fields["world"], trade.fields["instrument"]) == (
        ACCOUNT,
        "paper",
        "fx.eurusd",
    )


def the_hook_refuses(node: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    """The hook is a placeholder that passes every order, so its refusal has to be set."""
    monkeypatch.setattr(node.runtime._paths[ACCOUNT], "cross_unit_hook", lambda _command: "no")


def an_orphan_is_open(node: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    """One older position of ours on the market, as the reconcile reads it."""
    held = VenuePosition(
        "qold-1", "qmx:x:y", "fx.eurusd", "short", Decimal("0.1"), Decimal("1.07"), Decimal("1.08")
    )
    monkeypatch.setattr(node.runtime, "_orphans", lambda _account, _venue: [held])


def an_answer_is_lost_with_no_stop_held(node: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    """The venue fills the first entry, the answer is lost, and it holds no stop. No patch: the
    session drops and the real reconcile resolves the order."""
    del monkeypatch
    node.account.holds_stops = False
    node.account.lose_answers = 1
    while not node.account.received:
        step(node)
    node.source.drop()
    node.runtime.tick()
    node.runtime.tick()


def a_word_no_table_holds(node: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    monkeypatch.setattr(unit, "guard", lambda _market: "a word no table holds")


@pytest.mark.parametrize(
    ("arrange", "code", "text"),
    [
        (the_hook_refuses, "cross_unit_hook", "the cross-unit hook refused the order"),
        (
            an_orphan_is_open,
            "health_stop",
            "a position of ours that no unit holds is open on fx.eurusd: qold-1",
        ),
        (
            an_answer_is_lost_with_no_stop_held,
            "health_stop",
            "the venue does not hold this order's stop",
        ),
        (a_word_no_table_holds, "unlisted", "a word no table holds"),
    ],
    ids=["runtime-1007", "runtime-2301", "runtime-1609", "no-table"],
)
def test_each_unlisted_text_keeps_rows_landing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arrange: Callable[[Rig, pytest.MonkeyPatch], None],
    code: str,
    text: str,
) -> None:
    home = tmp_path / "QMX"
    node = rig(home, None)
    arrange(node, monkeypatch)

    while (code, text) not in guard_rows(node):
        assert node.now[0] < LIVE_FROM + 5 * DAY, f"no guard row after 5 days: {guard_rows(node)}"
        step(node)
    with_the_block = rows_on_disk(home, "signal")
    harvester(home).round(NOW, Cadence())
    filed_with_the_block = signals_in_the_store(home)
    for _ in range(8):
        step(node)
    node.runtime.stop()
    later = rows_on_disk(home, "signal")
    harvester(home).round(NOW, Cadence())

    assert later == with_the_block + 16, "two rows a bar, one per market, for 8 bars"
    assert filed_with_the_block == with_the_block
    assert signals_in_the_store(home) == later


def test_a_journal_that_cannot_write_stops_entries_and_keeps_exits(tmp_path: Path) -> None:
    home = tmp_path / "QMX"
    node = rig(home, None)
    while sum(t.command.kind is CommandKind.PLACE_ORDER for t in node.account.received) < 3:
        step(node)
    streams = list((home / "apps" / "trading-node" / "data" / "journal").rglob("journal-unit.*"))
    files = [path for stream in streams for path in stream.glob("*.jsonl")]
    for path in files:
        os.chmod(path, stat.S_IREAD)
    try:
        for _ in range(6 * 96):
            step(node)
    finally:
        for path in files:
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    said = status(node)
    kinds = [t.command.kind for t in node.account.received]
    node.runtime.stop()

    assert kinds == [
        CommandKind.PLACE_ORDER,
        CommandKind.PLACE_ORDER,
        CommandKind.PLACE_ORDER,
        CommandKind.CLOSE_POSITION,
    ]
    assert node.account.positions() == {}
    assert said["headline"] == "Stopped by a health check"
    assert said["reasons"] == [
        "The node cannot write its journal: a row of deployment dep-1 was refused"
        " (storage failure)."
    ]
