"""Bad connections and honest words (W12): a refused socket backs off, a weekend reads closed,
a drifting clock stops entries, and a paper position survives a restart (C-12a, TN-06, TN-19,
TN-20, AD-38).

The first three run on the node's own cTrader door and its fake, and on the conformance venue the
other node tests use; the last is the conformance venue only. No account and no network is
reached.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from itertools import groupby
from pathlib import Path
from typing import cast

import test_app_binding as binding
import test_app_runtime as base
from qmf.core import Result
from qmn.app.feed_keeper import Bar, Quote, SessionState
from qmn.app.paper_lane import PaperAccount
from qmn.app.runtime import NodeUnit
from qmn.venue.conformance import submit_not_ready_refusal
from qmn.venue.ctrader_account import Wire
from test_app_binding import FakeCTrader
from test_app_runtime import DAY, LIVE_FROM, Rig

ACCOUNT = binding.ACCOUNT
HOUR_NS = 3_600_000_000_000
TICK_NS = 200_000_000
MAX_SIGN_INS = 40
"""The rule: a refused socket signs in at most 40 times an hour (W12)."""
FRIDAY_BEFORE_CLOSE = int(datetime(2025, 3, 21, 20, 30, tzinfo=UTC).timestamp() * 1e9)
SATURDAY = int(datetime(2025, 3, 22, 12, tzinfo=UTC).timestamp() * 1e9)
TUESDAY = int(datetime(2025, 3, 25, 12, tzinfo=UTC).timestamp() * 1e9)
HOST_FACTS = Path("road") / "host" / "facts.json"


@dataclass
class Flaky(FakeCTrader):
    """cTrader refuses the next sockets while the internet is down."""

    down: bool = False

    def connect(self) -> Result[Wire]:
        if self.down:
            self.opened += 1
            return submit_not_ready_refusal()
        return super().connect()


def test_an_hour_of_refused_socket_stays_under_a_set_count_of_sign_ins(tmp_path: Path) -> None:
    fake = Flaky(binding.codec())
    rig = binding.bound_rig(tmp_path, broker=fake)
    binding.signed_in(rig)
    binding.bind(rig)
    feed = binding.runtime(rig).venues[ACCOUNT].feed

    fake.refuse_sockets = 1
    before = fake.opened
    feed.drop("the fixture's socket is refused")
    feed.pump()
    feed.pump()
    once = (feed.state, feed.ready, fake.opened - before)

    fake.down = True
    before = fake.opened
    feed.drop("the fixture's socket is refused")
    for _ in range(HOUR_NS // TICK_NS):
        rig.now[0] += TICK_NS
        feed.pump()

    assert once == (SessionState.READY, True, 2), "the first retry is immediate"
    assert fake.opened - before <= MAX_SIGN_INS
    assert feed.state is SessionState.DOWN
    assert cast(str, feed.document()["reason"]).startswith("connect refused")


def test_a_weekend_reads_closed_not_stopped(tmp_path: Path) -> None:
    node = base.rig(tmp_path)
    base.deploy(node, base.deployment(node.data))
    assert base.settle(node) == "trading"
    base.play(node, FRIDAY_BEFORE_CLOSE)

    node.now[0] = SATURDAY
    node.runtime.tick()
    weekend = (
        [held["stand_down"] for held in node.runtime.stand_downs.document()],
        base.value(node.node.call("status", {}))["headline"],
    )

    node.now[0] = TUESDAY
    node.runtime.tick()
    held = [held for held in node.runtime.stand_downs.document()]
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)

    assert weekend == ([], "Trading, 1 unit")
    assert [(held["stand_down"], held["scope"]) for held in held] == [
        ("stale_feed", "instrument:fx.eurusd"),
        ("stale_feed", "instrument:metal.xauusd"),
    ]
    assert cast(str, unit.guard("fx.eurusd")).startswith("stood down, stale feed")


def test_a_stale_host_clock_reads_none_and_a_drift_stops_entries(tmp_path: Path) -> None:
    node = base.rig(tmp_path)
    base.deploy(node, base.deployment(node.data))
    assert base.settle(node) == "trading"
    base.play(node, LIVE_FROM + DAY // 4)
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    now = datetime.fromtimestamp(node.now[0] / 1e9, UTC)

    write_clock(node, offset_ms=600, probed_at=now - timedelta(minutes=10))
    node.runtime.tick()
    stale = (unit.guard("fx.eurusd"), node.runtime.stand_downs.document())

    write_clock(node, offset_ms=600, probed_at=now)
    node.runtime.tick()
    drifted = unit.guard("fx.eurusd")

    assert stale == (None, [])
    assert drifted is not None
    assert drifted.startswith("stood down, clock band")
    assert [(held["stand_down"], held["scope"]) for held in node.runtime.stand_downs.document()] == [
        ("clock_band", "all")
    ]


def write_clock(node: Rig, *, offset_ms: int, probed_at: datetime) -> None:
    """The host facts the host writes into the volume, carrying one clock probe."""
    path = node.data.parent / HOST_FACTS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "qmx.host.facts/1",
                "placement": "fp-pc-1",
                "role": "pc",
                "clock": {"offset_ms": offset_ms, "probed_at": probed_at.isoformat()},
            }
        ),
        "utf-8",
    )


def played_until(node: Rig, check: Callable[[], bool], what: str) -> int:
    """Play the recorded bars one tick at a time from the node's clock until ``check`` holds."""
    start = max(node.now[0] + 1, LIVE_FROM)
    live = [item for item in base.month().bars if item[0] >= start]
    for moment, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        node.now[0] = moment
        node.source.play(
            [
                *(Bar(market, bar) for _, market, bar in closed),
                *(
                    Quote(market, moment, bar.bid.close, bar.ask.close, "both")
                    for _, market, bar in closed
                ),
            ]
        )
        node.runtime.tick()
        if check():
            return moment
    raise AssertionError(what)


def test_a_paper_position_survives_a_restart_and_a_crossed_stop_fires_on_the_next_bar(
    tmp_path: Path,
) -> None:
    node = base.rig(tmp_path)
    document = base.deployment(node.data)
    document["lane"] = "paper"
    base.deploy(node, document)
    assert base.settle(node) == "trading"

    def one_stopped_and_one_open() -> bool:
        unit = node.runtime.hosted["dep-1"].unit
        return unit is not None and bool(unit.venue_open()) and bool(base.unit_rows(node, "trade"))

    stopped_at = played_until(
        node, one_stopped_and_one_open, "the recorded month closed no trade into an open one"
    )
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    paper = cast("PaperAccount", unit.orders.venue.client)
    open_before = dict(unit.venue_open())
    booked = {str(row["trade_id"]) for row in base.unit_rows(node, "trade")}
    name = next(iter(open_before))
    stop = paper.stop_of(name)
    assert stop is not None
    assert set(open_before).isdisjoint(booked)
    node.runtime.stop()

    again = base.rig(tmp_path)
    assert base.settle(again) == "trading"
    again.now[0] = stopped_at
    unit_again = cast("NodeUnit", again.runtime.hosted["dep-1"].unit)
    paper_again = cast("PaperAccount", unit_again.orders.venue.client)
    rebuilt = (dict(unit_again.venue_open()), paper_again.stop_of(name))
    assert rebuilt == (open_before, stop)
    assert set(unit_again.venue_open()).isdisjoint(booked)

    played_until(
        again,
        lambda: paper_again.closed(name) is not None,
        "the rebuilt paper position's stop never fired",
    )
    traded = [row for row in base.unit_rows(again, "trade") if str(row["trade_id"]) == name]

    assert [row["exit_kind"] for row in traded] == ["stop"]
    assert paper_again.closed(name) is not None
