"""The node's alarms read the market calendars and take new keys (C-30, LOOSE-ENDS F6 and A3).

Every destination is a fake HTTP service on 127.0.0.1 made at runtime: nothing reaches ntfy,
Healthchecks.io or a phone. The calendars are the shipped ``qmx.calendar/1`` files, and a
market's calendar is the one the dummy's deployment snapshot names (``fx-24x5@1`` for
``fx.eurusd``, ``metals-24x5@1`` for ``metal.xauusd``).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from qmb.data.gap_check import OpenTime, open_time
from qmn.app.alarms import WAITING, PushSender, View, calendar_notes, market_hours
from qmn.app.alarms import Position as Held
from qmn.app.server import Node, open_node
from qmn.app.store import Store
from qmn.time.calendars import market_calendars
from test_app_alarms import (
    EARLY,
    STALE,
    Fake,
    at,
    clock_hold,
    publisher_to,
    risk_stop,
    wait_for,
)
from test_app_runtime import ACCOUNT, Rig, deploy, deployment, rig, value

RISK_STOP = "Risk stop with open trades on fx.eurusd: the daily loss limit is reached."
EARLY_PUSH = (
    "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-EARLY, so the "
    "node closed it reduce-only."
)
FOREX_FILES = (
    Path(__file__).resolve().parents[2]
    / "extensions/qmf-calendar-forex/src/qmf/calendar_forex/calendars"
)


@pytest.fixture
def fake() -> Iterator[Fake]:
    made = Fake()
    try:
        yield made
    finally:
        made.close()


def deployed(root: Path) -> Rig:
    node = rig(root)
    value(deploy(node, deployment(node.data)))
    return node


def held_on(market: str, *stand_downs: dict[str, object]) -> View:
    return View(
        stand_downs=stand_downs,
        positions=(Held("dep-1", market),),
        accounts={"dep-1": ACCOUNT},
        traded=frozenset({"fx.eurusd", "metal.xauusd"}),
    )


def bodies(fake: Fake) -> list[tuple[str | None, str]]:
    return [(got[3], got[4]) for got in fake.landed if got[0] == "POST"]


def test_a_risk_stop_on_a_tuesday_at_ten_london_pushes_once_and_a_saturday_stale_feed_does_not(
    tmp_path: Path, fake: Fake
) -> None:
    node = deployed(tmp_path)
    open_at = market_hours(node.node.context.store)
    stopped = held_on("fx.eurusd", {**risk_stop("fx.eurusd"), "since_ns": at("2026-11-10T09:58")})
    tuesday = PushSender(
        lambda: stopped, publisher_to(fake, tmp_path), open_at, lambda: at("2026-11-10T10:00:00")
    )
    tuesday.pass_once()
    tuesday.pass_once()
    saturday = PushSender(
        lambda: STALE, publisher_to(fake, tmp_path), open_at, lambda: at("2026-11-07T12:00:00")
    )
    saturday.pass_once()

    assert fake.tried == [
        ("POST", "/qmx-c18-topic", "QMX node a4dqobyh: protection-escalation", "4", RISK_STOP)
    ]
    assert (tuesday.sent, saturday.sent, saturday.failed) == (1, 0, 0)


def test_a_minute_after_fridays_close_both_wait_and_the_risk_stop_goes_at_sundays_open(
    tmp_path: Path, fake: Fake
) -> None:
    node = deployed(tmp_path)
    open_at = market_hours(node.node.context.store)
    stopped = {**risk_stop("fx.eurusd"), "since_ns": at("2026-11-13T22:00:30")}
    stale = {**STALE.stand_downs[0], "since_ns": at("2026-11-13T21:55:00")}
    now = [at("2026-11-13T22:01:00")]
    sender = PushSender(
        lambda: held_on("fx.eurusd", stopped, stale),
        publisher_to(fake, tmp_path),
        open_at,
        lambda: now[0],
    )
    sender.pass_once()
    assert fake.tried == []

    now[0] = at("2026-11-15T22:02:00")
    sender.read = lambda: held_on("fx.eurusd", stopped)
    sender.pass_once()
    assert bodies(fake) == [("4", RISK_STOP)]


def test_a_calendar_that_raises_still_lets_escalation_the_clock_and_a_risk_stop_push(
    tmp_path: Path, fake: Fake
) -> None:
    def broken(market: str, at_ns: int) -> bool:
        raise LookupError(f"no shipped calendar for {market} ({at_ns})")

    view = View(
        alarms=(EARLY,),
        stand_downs=(clock_hold("2026-11-10T09:54:00"), risk_stop("metal.xauusd")),
        positions=(Held("dep-1", "metal.xauusd"),),
        accounts={"dep-1": ACCOUNT},
        traded=frozenset({"metal.xauusd"}),
    )
    sender = PushSender(
        lambda: view, publisher_to(fake, tmp_path), broken, lambda: at("2026-11-10T10:00:00")
    )
    sender.pass_once()

    assert bodies(fake) == [
        ("5", EARLY_PUSH),
        ("4", "The clock has held new entries for 6 minutes: clock offset 700000000 ns."),
        ("4", "Risk stop with open trades on metal.xauusd: the daily loss limit is reached."),
    ]


def test_an_escalation_not_pushed_before_a_restart_is_pushed_after_it_and_a_pushed_one_is_not(
    tmp_path: Path, fake: Fake
) -> None:
    store = Store(tmp_path / "volume.sqlite")
    later = {**EARLY, "position": "qa4dqobyh-LATER"}
    view = [View(alarms=(EARLY,))]

    def sender() -> PushSender:
        return PushSender(
            lambda: view[0],
            publisher_to(fake, tmp_path),
            never_open,
            lambda: at("2026-11-07T12:00:00"),
            store=store,
            pass_s=0.05,
        )

    first = sender()
    first.pass_once()
    fake.mode = "refuses"
    view[0] = View(alarms=(EARLY, later))
    first.pass_once()
    assert (first.sent, first.failed) == (1, 1)

    fake.mode = "ok"
    restarted = sender()
    restarted.start()
    try:
        wait_for(lambda: restarted.sent == 1)
    finally:
        restarted.stop()
    assert bodies(fake) == [
        ("5", EARLY_PUSH),
        (
            "5",
            "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-LATER, "
            "so the node closed it reduce-only.",
        ),
    ]


def never_open(market: str, at_ns: int) -> bool:
    del market, at_ns
    return False


def test_the_status_names_a_calendar_near_or_past_its_last_day_or_not_shipped_at_all(
    tmp_path: Path,
) -> None:
    node = deployed(tmp_path)
    open_at = market_hours(node.node.context.store)

    def calendar_reasons(when: str) -> list[str]:
        node.now[0] = at(when)
        reasons = value(node.node.call("status", {}))["reasons"]
        assert isinstance(reasons, list)
        return [str(r) for r in reasons if str(r).startswith("The market calendar")]

    assert calendar_reasons("2026-11-10T10:00:00") == []
    assert calendar_reasons("2027-12-10T10:00:00") == [
        "The market calendar fx-24x5@1 covers days up to 2027-12-31, 21 days from now.",
        "The market calendar metals-24x5@1 covers days up to 2027-12-31, 21 days from now.",
    ]
    assert calendar_reasons("2028-01-05T10:00:00") == [
        "The market calendar fx-24x5@1 ended on 2027-12-31, 5 days ago; its weekly sessions "
        "still hold, but no closure after it is known.",
        "The market calendar metals-24x5@1 ended on 2027-12-31, 5 days ago; its weekly "
        "sessions still hold, but no closure after it is known.",
    ]
    assert [
        open_at("fx.eurusd", at(when)) for when in ("2028-01-05T12:00", "2028-01-08T12:00")
    ] == [
        True,
        False,
    ]
    assert calendar_notes(node.node.context.store, at("2026-11-10T10:00:00"), {}, nothing) == [
        "The market calendar fx-24x5@1 has no readable file on this node, so the alarms that "
        "follow it push at any hour.",
        "The market calendar metals-24x5@1 has no readable file on this node, so the alarms that "
        "follow it push at any hour.",
    ]


def nothing(ref: str) -> OpenTime | None:
    del ref
    return None


def installed_qmb(ref: str) -> OpenTime | None:
    """QMB's calendars as an installed node env sees them: only its built-in forex week."""
    return open_time(ref) if ref == "fx-24x5@1" else None


def test_with_an_empty_calendar_folder_forex_follows_qmbs_week_and_the_status_names_both(
    tmp_path: Path,
) -> None:
    node = deployed(tmp_path)
    store = node.node.context.store
    (tmp_path / "calendars").mkdir()
    none_shipped = market_calendars(tmp_path / "calendars")
    open_at = market_hours(store, none_shipped, installed_qmb)

    assert none_shipped == {}
    assert [open_at("fx.eurusd", at(when)) for when in ("2026-11-07T12:00", "2026-11-10T10:00")] == [
        False,
        True,
    ]
    with pytest.raises(LookupError, match=r"no market calendar metals-24x5@1 for metal\.xauusd"):
        open_at("metal.xauusd", at("2026-11-10T10:00"))
    assert calendar_notes(store, at("2026-11-10T10:00:00"), none_shipped, installed_qmb) == [
        "The market calendar fx-24x5@1 has no readable file on this node, so the alarms that "
        "follow it read QMB's copy of its week.",
        "The market calendar metals-24x5@1 has no readable file on this node, so the alarms that "
        "follow it push at any hour.",
    ]


def test_a_calendar_file_that_cannot_be_read_is_left_out_and_named_and_the_rest_still_load(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    node = deployed(tmp_path)
    shipped = tmp_path / "extensions"
    for package, name, text in (
        ("forex", "fx-24x5@1.json", (FOREX_FILES / "fx-24x5@1.json").read_text(encoding="utf-8")),
        ("cme", "metals-24x5@1.json", '{"calendar_ref": "metals-24x5@1", "issued": '),
    ):
        folder = shipped / f"qmf-calendar-{package}/src/qmf/calendar_{package}/calendars"
        folder.mkdir(parents=True)
        (folder / name).write_text(text, encoding="utf-8")

    calendars = market_calendars(shipped)

    assert sorted(calendars) == ["fx-24x5@1"]
    assert capsys.readouterr().err.splitlines() == [
        '{"event": "calendar_unreadable", "file": "metals-24x5@1.json", "error": '
        '"JSONDecodeError"}'
    ]
    assert calendar_notes(node.node.context.store, at("2026-11-10T10:00:00"), calendars, nothing) == [
        "The market calendar metals-24x5@1 has no readable file on this node, so the alarms that "
        "follow it push at any hour."
    ]


def posts(landed: list[tuple[str, str, str | None, str | None, str]]) -> list[tuple[str, str]]:
    return [(got[1], got[4]) for got in landed if got[0] == "POST"]


def test_an_escalation_never_pushed_survives_two_restarts_and_lands_once_when_ntfy_answers(
    tmp_path: Path, fake: Fake
) -> None:
    (tmp_path / "data").mkdir()

    def run(then: Callable[[Node], None]) -> None:
        node = open_node(
            tmp_path / "data", here="fp-pc-1", machine="pc", keys=lambda: keys_to(fake, "c30")
        )
        node.start()
        try:
            then(node)
        finally:
            node.stop()
            if node.journal is not None:
                node.journal.close()

    def escalate(node: Node) -> None:
        assert node.runtime is not None
        node.runtime.alarms.append(EARLY)
        node.runtime.wake()
        wait_for(lambda: len(posts(fake.tried)) == 1, 30)

    fake.mode = "refuses"
    run(escalate)
    run(lambda _: wait_for(lambda: len(posts(fake.tried)) == 2, 30))
    fake.mode = "ok"
    run(lambda _: wait_for(lambda: posts(fake.landed) != [], 30))

    assert posts(fake.tried) == [("/qmx-c30-topic", EARLY_PUSH)] * 3
    assert posts(fake.landed) == [("/qmx-c30-topic", EARLY_PUSH)]
    assert Store(tmp_path / "data/node.sqlite").observed(WAITING) == []


def keys_to(fake: Fake, name: str) -> str:
    return json.dumps(
        {
            "schema_version": "qmx.node.keys/1",
            "alarms": {
                "ntfy_topic_url": fake.url(f"/qmx-{name}-topic"),
                "healthchecks_ping_url": fake.url(f"/ping/{name}"),
            },
        }
    )


def test_rotate_keys_moves_the_running_senders_to_the_new_keys_without_a_restart(
    tmp_path: Path,
) -> None:
    old, new = Fake(), Fake()
    current = [keys_to(old, "old")]
    (tmp_path / "data").mkdir()
    node = open_node(tmp_path / "data", here="fp-pc-1", machine="pc", keys=lambda: current[0])
    runtime = node.runtime
    assert runtime is not None
    node.start()
    try:
        runtime.alarms.append(EARLY)
        runtime.wake()
        wait_for(lambda: bodies(old) != [], 30)
        current[0] = keys_to(new, "new")

        assert node.call("rotate_keys", {"op_id": "op-rotate-1"}) == {
            "ok": True,
            "value": {"state": "accepted"},
            "op_id": "op-rotate-1",
        }
        wait_for(lambda: ("GET", "/ping/new", None, None, "") in new.landed)
        runtime.alarms.append({**EARLY, "position": "qa4dqobyh-LATER"})
        runtime.wake()
        wait_for(lambda: bodies(new) != [], 30)
        time.sleep(0.3)
    finally:
        node.stop()
        if node.journal is not None:
            node.journal.close()
        old.close()
        new.close()
    assert sorted(got[1] for got in old.landed) == ["/ping/old", "/qmx-old-topic"]
    assert [(got[1], got[4]) for got in new.landed if got[0] == "POST"] == [
        (
            "/qmx-new-topic",
            "Protection escalation on metal.xauusd: the venue held no stop on qa4dqobyh-LATER, "
            "so the node closed it reduce-only.",
        )
    ]
