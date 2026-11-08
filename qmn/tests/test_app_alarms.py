"""The node's push and liveness senders (Part C slice C-18, AD-318), against local fakes.

Every destination here is a fake HTTP service on 127.0.0.1 made at runtime: nothing reaches
ntfy, Healthchecks.io or a phone. The trading rig is C-12a's node on the conformance venue.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

import pytest
from qmf.core import TypedRefusal
from qmf.venue.commands import CommandKind
from qmn.app.alarms import (
    LivenessSender,
    PushSender,
    View,
    attach,
    https_send,
)
from qmn.app.alarms import Position as Held
from qmn.app.server import from_environment
from qmn.app.store import Store
from qmn.observability.alerts import (
    AlertPublisher,
)
from qmn.observability.liveness import LivenessHeartbeat
from test_app_runtime import DAY, LIVE_FROM, play, value
from test_protection_every_order import FIRST_SEND, trading

NEW_YORK = ZoneInfo("America/New_York")
FRIDAY_CLOSE = 4 * 1440 + 17 * 60
SUNDAY_OPEN = 6 * 1440 + 17 * 60
SEND_TIMEOUT_S = 0.3
"""A test bound: how long one send to a hanging fake may take."""
PASS_S = 0.05
"""A test bound: the push sender's pass."""


def forex_week(market: str, at_ns: int) -> bool:
    """The forex week, Sunday 17:00 to Friday 17:00 New York, for the `fx.` markets."""
    local = datetime.fromtimestamp(at_ns / 1e9, NEW_YORK)
    minute = local.weekday() * 1440 + local.hour * 60 + local.minute
    return market.startswith("fx.") and not FRIDAY_CLOSE <= minute < SUNDAY_OPEN


def never_open(market: str, at_ns: int) -> bool:
    del market, at_ns
    return False


def at(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp()) * 1_000_000_000


class Fake:
    """One fake HTTP service on 127.0.0.1. ``mode`` is ``ok``, ``refuses`` (HTTP 500) or
    ``hangs`` (no answer until released, then 500). ``tried`` is every request, ``landed`` the
    ones answered 200."""

    def __init__(self) -> None:
        self.mode = "ok"
        self.tried: list[tuple[str, str, str | None, str | None, str]] = []
        self.landed: list[tuple[str, str, str | None, str | None, str]] = []
        self.release = threading.Event()
        fake = self

        class Answer(BaseHTTPRequestHandler):
            def answer(self) -> None:
                mode = fake.mode
                length = int(self.headers.get("Content-Length") or 0)
                got = (
                    self.command,
                    self.path,
                    self.headers.get("Title"),
                    self.headers.get("Priority"),
                    self.rfile.read(length).decode("utf-8"),
                )
                fake.tried.append(got)
                if mode == "hangs":
                    fake.release.wait(10)
                ok = mode == "ok"
                if ok:
                    fake.landed.append(got)
                self.send_response(200 if ok else 500)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = answer

            def log_message(self, format: str, *args: object) -> None:
                del format, args

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Answer)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}{path}"

    def close(self) -> None:
        self.release.set()
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def fake() -> Iterator[Fake]:
    made = Fake()
    try:
        yield made
    finally:
        made.close()


def keys(fake: Fake) -> str:
    return json.dumps(
        {
            "schema_version": "qmx.node.keys/1",
            "alarms": {
                "ntfy_topic_url": fake.url("/qmx-c18-topic"),
                "healthchecks_ping_url": fake.url("/ping/c18-check"),
            },
        }
    )


def wait_for(done: object, seconds: float = 10.0) -> None:
    deadline = time.monotonic() + seconds
    while not cast("bool", done() if callable(done) else done):
        assert time.monotonic() < deadline, "the condition did not hold in time"
        time.sleep(0.02)


def publisher_to(fake: Fake, root: Path) -> AlertPublisher:
    senders = attach(
        Store(root / "node.sqlite"),
        "a4dqobyh",
        json.dumps(
            {
                "schema_version": "qmx.node.keys/1",
                "alarms": {"ntfy_topic_url": fake.url("/qmx-c18-topic")},
            }
        ),
        open_at=never_open,
        clock_ns=lambda: 0,
        steady_ns=lambda: 0,
    )
    assert senders.push is not None
    return senders.push.publisher


def test_a_protection_escalation_reaches_ntfy_once_with_priority_5_on_a_shut_market(
    tmp_path: Path, fake: Fake
) -> None:
    node = trading(tmp_path, holds_stops=False)
    play(node, FIRST_SEND + 1)
    senders = attach(
        node.node.context.store,
        "a4dqobyh",
        keys(fake),
        open_at=never_open,
        clock_ns=lambda: node.now[0],
        steady_ns=time.monotonic_ns,
    )
    push = cast("PushSender", senders.push)

    push.pass_once()
    push.pass_once()

    position = node.account.received[0].tags
    assert position is not None
    assert fake.landed == [
        (
            "POST",
            "/qmx-c18-topic",
            "QMX node a4dqobyh: protection-escalation",
            "5",
            f"Protection escalation on fx.eurusd: the venue held no stop on "
            f"{position.client_order_id}, so the node closed it reduce-only.",
        )
    ]
    assert (push.sent, push.failed, push.waiting) == (1, 0, [])
    node.runtime.stop()


STALE = View(
    stand_downs=(
        {
            "stand_down": "stale_feed",
            "scope": "instrument:fx.eurusd",
            "word": "Stopped by a health check",
            "cause": "last quote 600 s ago",
            "clears": "itself",
            "since_ns": at("2026-11-07T11:50:00"),
        },
    ),
    positions=(Held("dep-1", "fx.eurusd"),),
    accounts={"dep-1": "demo-1"},
    traded=frozenset({"fx.eurusd"}),
)


def test_a_weekend_stale_feed_sends_nothing_even_at_the_open_and_a_weekday_one_wakes_him(
    tmp_path: Path, fake: Fake
) -> None:
    saturday = PushSender(
        lambda: STALE, publisher_to(fake, tmp_path), forex_week, lambda: at("2026-11-07T12:00:00")
    )
    saturday.pass_once()
    sunday_open = PushSender(
        lambda: STALE, publisher_to(fake, tmp_path), forex_week, lambda: at("2026-11-08T22:01:00")
    )
    sunday_open.pass_once()
    assert fake.tried == []
    assert (saturday.sent, saturday.failed, sunday_open.sent) == (0, 0, 0)

    wednesday_row = {**STALE.stand_downs[0], "since_ns": at("2026-11-04T11:50:00")}
    wednesday = PushSender(
        lambda: replace(STALE, stand_downs=(wednesday_row,)),
        publisher_to(fake, tmp_path),
        forex_week,
        lambda: at("2026-11-04T12:00:00"),
    )
    wednesday.pass_once()
    assert fake.landed == [
        (
            "POST",
            "/qmx-c18-topic",
            "QMX node a4dqobyh: protection-escalation",
            "4",
            "The feed is stale with open trades on fx.eurusd (instrument:fx.eurusd): "
            "last quote 600 s ago.",
        )
    ]


def clock_hold(since: str) -> dict[str, object]:
    return {
        "stand_down": "clock_band",
        "scope": "all",
        "cause": "clock offset 700000000 ns",
        "since_ns": at(since),
    }


def risk_stop(market: str) -> dict[str, object]:
    return {
        "stand_down": "risk_stop",
        "scope": f"instrument:{market}",
        "cause": "the daily loss limit is reached",
        "since_ns": at("2026-11-04T11:58:00"),
    }


def test_a_risk_stop_and_failing_healing_wake_him_and_a_tradeless_feed_or_short_hold_do_not(
    tmp_path: Path, fake: Fake
) -> None:
    mixed = View(
        stand_downs=(
            {**STALE.stand_downs[0], "since_ns": at("2026-11-04T11:50:00")},
            clock_hold("2026-11-04T11:56:00"),
            risk_stop("fx.gbpusd"),
            {
                "stand_down": "repeated_fault",
                "scope": "all",
                "cause": "the feed restarted 3 times in 10 minutes",
                "since_ns": at("2026-11-04T11:59:00"),
            },
        ),
        positions=(Held("dep-1", "fx.gbpusd"),),
        accounts={"dep-1": "demo-1"},
        traded=frozenset({"fx.eurusd", "fx.gbpusd"}),
    )
    sender = PushSender(
        lambda: mixed, publisher_to(fake, tmp_path), forex_week, lambda: at("2026-11-04T12:00:00")
    )
    sender.pass_once()
    title = "QMX node a4dqobyh: protection-escalation"
    assert fake.tried == [
        (
            "POST",
            "/qmx-c18-topic",
            title,
            "4",
            "Risk stop with open trades on fx.gbpusd: the daily loss limit is reached.",
        ),
        (
            "POST",
            "/qmx-c18-topic",
            title,
            "4",
            "Healing keeps failing and the node stood down: the feed restarted 3 times in "
            "10 minutes.",
        ),
    ]


def test_a_clock_hold_wakes_him_once_it_passes_five_minutes_while_every_market_is_shut(
    tmp_path: Path, fake: Fake
) -> None:
    now = [at("2026-11-07T12:04:59")]
    held = View(stand_downs=(clock_hold("2026-11-07T12:00:00"),), traded=frozenset({"fx.eurusd"}))
    sender = PushSender(lambda: held, publisher_to(fake, tmp_path), never_open, lambda: now[0])

    sender.pass_once()
    assert fake.tried == []

    now[0] = at("2026-11-07T12:05:00")
    sender.pass_once()
    sender.pass_once()
    assert fake.landed == [
        (
            "POST",
            "/qmx-c18-topic",
            "QMX node a4dqobyh: protection-escalation",
            "4",
            "The clock has held new entries for 5 minutes: clock offset 700000000 ns.",
        )
    ]


EARLY = {
    "alarm": "protection_escalation",
    "position": "qa4dqobyh-EARLY",
    "market_id": "metal.xauusd",
    "tries": 3,
    "action": "closed_reduce_only",
    "origin": "placeholder",
}
"""A push already waiting when the day starts, so every order below is sent while it fails."""


@pytest.mark.parametrize("failing", ["refuses", "hangs", "raises"])
def test_a_failed_send_is_counted_and_retried_and_trading_and_the_kill_switch_carry_on(
    tmp_path: Path, fake: Fake, failing: str
) -> None:
    node = trading(tmp_path)
    store = node.node.context.store
    mode = {"now": failing}
    fake.mode = "ok" if failing == "raises" else failing

    def send(
        method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float
    ) -> int:
        if mode["now"] == "raises":
            raise RuntimeError("injected send failure")
        return https_send(method, url, headers, body, SEND_TIMEOUT_S)

    senders = attach(
        store,
        "a4dqobyh",
        keys(fake),
        open_at=forex_week,
        clock_ns=lambda: node.now[0],
        steady_ns=time.monotonic_ns,
        send=send,
        pass_s=PASS_S,
    )
    push = cast("PushSender", senders.push)

    started = [False]

    def read() -> View:
        view = View.read(store)
        return replace(view, alarms=(*view.alarms, EARLY)) if started[0] else view

    push.read = read
    push.start()
    started[0] = True
    try:
        wait_for(lambda: push.failed >= 1)
        play(node, LIVE_FROM + 2 * DAY)
        node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
        node.runtime.tick()
        node.runtime.tick()
        status = value(node.node.call("status", {}))
        tickets = [(t.command.kind, t.market_id, t.side.value) for t in node.account.received]

        assert tickets == [
            (CommandKind.PLACE_ORDER, "fx.eurusd", "short"),
            (CommandKind.PLACE_ORDER, "fx.eurusd", "short"),
            (CommandKind.PLACE_ORDER, "fx.eurusd", "short"),
            (CommandKind.CLOSE_POSITION, "fx.eurusd", "short"),
        ]
        assert status["kill_level"] == "RED"
        assert push.sent == 0
        assert push.failed >= 1
        assert [item.summary for item in push.waiting] == [
            "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-EARLY, "
            "so the node closed it reduce-only."
        ]

        mode["now"], fake.mode = "ok", "ok"
        fake.release.set()
        wait_for(lambda: push.sent == 1)
        assert push.waiting == []
        assert [got[1:4] for got in fake.landed] == [
            ("/qmx-c18-topic", "QMX node a4dqobyh: protection-escalation", "5")
        ]
    finally:
        push.stop()
        node.runtime.stop()


def test_a_calendar_that_raises_pushes_anyway_and_names_its_market_once(
    tmp_path: Path, fake: Fake, capsys: pytest.CaptureFixture[str]
) -> None:
    def calendar(market: str, at_ns: int) -> bool:
        if market == "metal.xauusd":
            raise LookupError("no calendar for metal.xauusd")
        return forex_week(market, at_ns)

    view = View(
        alarms=(EARLY,),
        stand_downs=(
            risk_stop("metal.xauusd"),
            {**STALE.stand_downs[0], "since_ns": at("2026-11-04T11:50:00")},
        ),
        positions=(Held("dep-1", "metal.xauusd"), Held("dep-1", "fx.eurusd")),
        accounts={"dep-1": "demo-1"},
        traded=frozenset({"fx.eurusd", "metal.xauusd"}),
    )
    sender = PushSender(
        lambda: view, publisher_to(fake, tmp_path), calendar, lambda: at("2026-11-04T12:00:00")
    )
    capsys.readouterr()

    sender.pass_once()
    sender.pass_once()

    assert [(got[3], got[4]) for got in fake.landed] == [
        (
            "5",
            "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-EARLY, "
            "so the node closed it reduce-only.",
        ),
        ("4", "Risk stop with open trades on metal.xauusd: the daily loss limit is reached."),
        (
            "4",
            "The feed is stale with open trades on fx.eurusd (instrument:fx.eurusd): "
            "last quote 600 s ago.",
        ),
    ]
    assert [json.loads(line) for line in capsys.readouterr().err.splitlines()] == [
        {"event": "alarm_calendar_failed", "market_id": "metal.xauusd", "error": "LookupError"}
    ]
    assert (sender.sent, sender.waiting) == (3, [])


def test_past_the_waiting_bound_the_oldest_failed_push_is_dropped_and_counted(
    tmp_path: Path, fake: Fake, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.mode = "refuses"
    escalations = tuple({**EARLY, "position": f"qa4dqobyh-{n}"} for n in (1, 2, 3))
    sender = PushSender(
        lambda: View(alarms=escalations),
        publisher_to(fake, tmp_path),
        never_open,
        lambda: 0,
        waiting_max=2,
    )
    capsys.readouterr()

    sender.pass_once()

    assert [item.summary for item in sender.waiting] == [
        "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-2, so the "
        "node closed it reduce-only.",
        "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-3, so the "
        "node closed it reduce-only.",
    ]
    assert (sender.dropped, sender.failed, sender.sent, len(fake.tried)) == (1, 2, 0, 2)
    assert json.loads(capsys.readouterr().err) == {
        "event": "alarm_dropped",
        "wake": "protection escalation",
        "dropped": 1,
    }


def test_a_node_started_from_its_environment_pushes_an_escalation_and_pings_liveness(
    tmp_path: Path, fake: Fake, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "data").mkdir()
    monkeypatch.setenv("QMX_VOLUME", str(tmp_path))
    monkeypatch.setenv("QMX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("NODE_KEYS", keys(fake))
    node = from_environment()
    try:
        wait_for(lambda: ("GET", "/ping/c18-check", None, None, "") in fake.landed)
        assert node.runtime is not None
        node.runtime.alarms.append(EARLY)
        node.runtime.wake()
        wait_for(lambda: any(got[0] == "POST" for got in fake.landed), 30)
        tag = node.context.standing().tag
        assert [got for got in fake.landed if got[0] == "POST"] == [
            (
                "POST",
                "/qmx-c18-topic",
                f"QMX node {tag}: protection-escalation",
                "5",
                "Protection escalation on metal.xauusd: the venue held no stop on "
                "qa4dqobyh-EARLY, so the node closed it reduce-only.",
            )
        ]
    finally:
        node.stop()
        if node.journal is not None:
            node.journal.close()


def test_liveness_pings_reach_the_watcher_on_cadence_and_stop_with_the_node(
    tmp_path: Path, fake: Fake
) -> None:
    steady = [0]
    senders = attach(
        Store(tmp_path / "node.sqlite"),
        "a4dqobyh",
        keys(fake),
        open_at=never_open,
        clock_ns=lambda: 0,
        steady_ns=lambda: steady[0],
    )
    liveness = cast("LivenessSender", senders.liveness)
    for second in (0, 30, 60, 125, 150):
        steady[0] = second * 1_000_000_000
        liveness.ping_once()
    assert fake.landed == [("GET", "/ping/c18-check", None, None, "")] * 3
    assert liveness.failed == 0

    fake.landed.clear()
    heartbeat = LivenessHeartbeat.try_create(
        endpoint="healthchecks",
        cadence_ns=50_000_000,
        token_reference="qmx/trading-node-keys#alarms.healthchecks_ping_url",
        sink=liveness.heartbeat.sink,
    )
    assert not isinstance(heartbeat, TypedRefusal), heartbeat
    running = LivenessSender(heartbeat.value, time.monotonic_ns)
    running.start()
    wait_for(lambda: len(fake.landed) >= 3)
    running.stop()
    stopped_at = len(fake.landed)
    time.sleep(0.3)
    assert len(fake.landed) == stopped_at


def test_the_keys_document_turns_each_sender_on_and_a_bad_one_turns_them_off_unshown(
    tmp_path: Path, fake: Fake, capsys: pytest.CaptureFixture[str]
) -> None:
    def made(text: str | None) -> tuple[bool, bool]:
        senders = attach(
            Store(tmp_path / "node.sqlite"),
            "a4dqobyh",
            text,
            open_at=never_open,
            clock_ns=lambda: 0,
            steady_ns=lambda: 0,
        )
        return senders.push is not None, senders.liveness is not None

    plain = "http://198.51.100.7/qmx-plain-topic"
    assert made(keys(fake)) == (True, True)
    on = attach(
        Store(tmp_path / "node.sqlite"),
        "a4dqobyh",
        keys(fake),
        open_at=never_open,
        clock_ns=lambda: 0,
        steady_ns=lambda: 0,
    )
    shown = repr(cast("PushSender", on.push).publisher) + repr(
        cast("LivenessSender", on.liveness).heartbeat
    )
    assert "NtfyChannel(node_tag='a4dqobyh'" in shown
    assert "HealthchecksSink(send=" in shown
    assert fake.url("") not in shown
    assert made(json.dumps({"schema_version": "qmx.node.keys/1"})) == (False, False)
    assert made(None) == (False, False)
    capsys.readouterr()
    assert made(json.dumps({"alarms": {"ntfy_topic_url": plain}})) == (False, False)
    said = capsys.readouterr().err
    assert json.loads(said) == {
        "event": "alarms_off",
        "reason": "alarms.ntfy_topic_url is not an https address",
    }
    assert plain not in said
