"""The node heals itself and never lets a heal undo a stop (Part C slice C-13, AD-315, AD-38).

On the conformance venue only. A fault inside the runtime's pass is injected at the feed, the
way a venue client or a store that raises would reach it. A process restart is a second node
opened on the same volume after the first one stopped, as the apps supervisor starts it again.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from itertools import groupby
from pathlib import Path
from typing import cast

import pytest
from qmf.core import Ok, TypedRefusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_kinds.unit import LIFECYCLE_SCHEMA
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.store.refusals import storage_failure
from qmf.venue.commands import CommandKind
from qmn.app import stand_down
from qmn.app.feed_keeper import Bar, Quote
from qmn.app.healing import RUNTIME_STUCK_EXIT_CODE, Backoff
from qmn.app.runtime import ConformanceAccount, NodeUnit
from qmn.app.server import BUILD
from test_app_runtime import (
    DAY,
    LIVE_FROM,
    Rig,
    deploy,
    deployment,
    month,
    rig,
    settle,
    unit_rows,
    value,
)
from test_app_stand_down import RefusedWriter, at, lifecycle_rows
from test_protection_every_order import FIRST_SEND, node_rows

SECOND = 1_000_000_000


def driven(node: Rig, until: int, *, start: int = LIVE_FROM) -> None:
    """The recorded bars in ``[start, until)``, one supervised pass per bar."""
    live = [item for item in month().bars if start <= item[0] < until]
    for moment, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        node.now[0] = max(node.now[0], moment)
        node.source.play(
            [
                *(Bar(market, bar) for _, market, bar in closed),
                *(Quote(market, moment, bar.bid.close, bar.ask.close, "both") for _, market, bar in closed),
            ]
        )
        node.runtime.step()


def faults(node: Rig, count: int) -> list[int]:
    """The feed raises on its next ``count`` reads, then reads again as before."""
    pump = node.feed.pump
    left = [count]

    def failing() -> object:
        if left[0] > 0:
            left[0] -= 1
            raise RuntimeError("the feed read failed")
        return pump()

    node.feed.pump = failing  # type: ignore[method-assign]
    return left


def status(node: Rig) -> dict[str, object]:
    return cast("dict[str, object]", value(node.node.call("status", {})))


def entries(node: Rig, after: int = 0) -> list[tuple[str, Decimal | None]]:
    return [
        (t.market_id, t.quantity)
        for t in node.account.received[after:]
        if t.command.kind is CommandKind.PLACE_ORDER
    ]


def restarted(node: Rig, root: Path) -> Rig:
    """The process stops and the apps supervisor starts it again on the same volume."""
    node.runtime.stop()
    again = rig(root)
    assert settle(again) == "trading"
    return again


@pytest.mark.parametrize(
    "moment", [FIRST_SEND - 900 * SECOND, at(300)], ids=["flat", "a position open"]
)
def test_an_exception_restarts_the_runtime_with_back_off_and_it_trades_as_before(
    tmp_path: Path, moment: int
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, moment)
    open_at_fault = sorted(node.account.positions())
    faults(node, 1)
    node.runtime.step()
    during = status(node)
    driven(node, LIVE_FROM + 2 * DAY, start=moment)
    after = status(node)
    heals = cast("list[dict[str, object]]", after["heals"])
    lifecycle = [(r["event"], r.get("what")) for r in node_rows(node, "node_lifecycle")]

    assert during["word"] == "Healing"
    assert after["word"] == "Trading"
    assert [(h["why"], h["restart"], h["backoff_ms"]) for h in heals] == [
        ("RuntimeError('the feed read failed')", 1, 1000)
    ]
    assert lifecycle == [("start", None), ("stop", "runtime"), ("start", "runtime")]
    assert [r["why"] for r in node_rows(node, "reconcile")] == ["start", "start"]
    assert [r for r in unit_rows(node, "state") if r["event"] == "cold_start"] == []
    assert [(t.command.kind, t.quantity) for t in node.account.received] == [
        (CommandKind.PLACE_ORDER, Decimal("1.72")),
        (CommandKind.PLACE_ORDER, Decimal("1.08")),
        (CommandKind.PLACE_ORDER, Decimal("0.75")),
        (CommandKind.CLOSE_POSITION, None),
    ]
    assert len(open_at_fault) == (0 if moment < FIRST_SEND else 1)
    assert cast("dict[str, object]", after["safe_to_restart"]) == {"ok": True, "reasons": []}
    node.runtime.stop()


def test_five_heals_in_ten_minutes_stand_the_node_down_alive_until_his_resume(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    faults(node, 5)
    for _ in range(5):
        node.runtime.step()
    stood = status(node)
    driven(node, at(1440))
    held_a_day = entries(node)
    still = status(node)
    value(node.node.call("resume", {"op_id": "op-resume-1", "scope": "all"}))
    node.runtime.step()
    cleared = status(node)
    driven(node, at(4500), start=at(1440))

    waits = [h["backoff_ms"] for h in cast("list[dict[str, object]]", stood["heals"])]
    assert waits == [1000, 2000, 4000, 8000, 16000]
    assert stood["word"] == "Stopped by a health check"
    assert cast("list[object]", stood["reasons"])[0] == (
        "Stopped by a health check: 5 restarts in 10 minutes. It waits for your resume."
    )
    assert node.runtime.alarms[0] == {
        "alarm": "repeated_fault",
        "restarts": 5,
        "action": "no_new_entries",
        "why": "5 restarts in 10 minutes, the last: RuntimeError('the feed read failed')",
    }
    assert held_a_day == []
    assert still["word"] == "Stopped by a health check"
    assert cleared["word"] == "Trading"
    assert node.node.context.store.observed("healing.boots") == []
    assert entries(node) == [("fx.eurusd", Decimal("0.92"))]
    node.runtime.stop()


def test_a_frozen_runtime_exits_the_process_and_the_restart_keeps_the_kill_level(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, FIRST_SEND - 900 * SECOND)
    release = threading.Event()
    frozen = threading.Event()

    def stuck() -> None:
        frozen.set()
        release.wait(30)

    node.runtime.tick = stuck  # type: ignore[method-assign]
    pass_thread = threading.Thread(target=node.runtime.step)
    pass_thread.start()
    assert frozen.wait(10)
    kill = node.node.call("kill", {"op_id": "op-kill-1", "level": "yellow", "scope": "all"})
    began = cast("int", node.runtime.watch.began)
    exits: list[int] = []
    node.runtime.watch.exit = exits.append
    node.runtime.watch.steady_ns = lambda: began + 30 * SECOND
    sound = node.runtime.watch.check()
    node.runtime.watch.steady_ns = lambda: began + 31 * SECOND
    why = node.runtime.watch.check()
    release.set()
    pass_thread.join(10)
    again = restarted(node, tmp_path)
    healing = status(again)
    driven(again, LIVE_FROM + 2 * DAY, start=FIRST_SEND - 900 * SECOND)
    back = status(again)
    heals = cast("list[dict[str, object]]", back["heals"])

    assert value(kill) == {"level_in_force": "YELLOW"}
    assert (sound, why, exits) == (None, "runtime_stuck", [RUNTIME_STUCK_EXIT_CODE])
    assert healing["word"] == "Healing"
    assert back["kill_level"] == "YELLOW"
    assert back["word"] == "Paused"
    assert [(h["why"], h["restart"]) for h in heals] == [("runtime_stuck", 1)]
    assert entries(again) == []
    assert [r["detail"] for r in unit_rows(again, "guard")][-1] == (
        "the kill switch is at YELLOW for all"
    )
    again.runtime.stop()


def held(node: Rig) -> list[tuple[object, object]]:
    return [(h["stand_down"], h.get("lifecycle_event")) for h in node.runtime.stand_downs.document()]


def moves(node: Rig) -> list[tuple[object, object, object]]:
    return [
        (body["from"], body["to"], body.get("clears"))
        for row in lifecycle_rows(node)
        for body in [cast("dict[str, object]", row["body"])]
    ]


def test_a_risk_stop_survives_a_restart_and_only_his_later_resume_clears_it(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    again = restarted(node, tmp_path)
    after_restart = held(again)
    sent = len(again.account.received)
    driven(again, at(5 * 1440), start=at(5570))
    held_five_days = [m for m, _ in entries(again, sent) if m == "fx.eurusd"]
    value(again.node.call("resume", {"op_id": "op-resume-1", "scope": {"deployment_id": "dep-1"}}))
    again.runtime.step()

    assert stop is not None
    assert after_restart == [("risk_stop", stop)]
    assert held_five_days == []
    assert held(again) == []
    assert moves(again) == [("live", "stopped", None), ("stopped", "live", stop)]
    again.runtime.stop()


def test_a_resume_he_sent_while_the_node_was_down_clears_the_restored_stop_once(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    node.runtime.stop()
    node.now[0] += SECOND
    value(node.node.call("resume", {"op_id": "op-resume-1", "scope": "all"}))
    again = rig(tmp_path)
    settle(again)

    assert stop is not None
    assert held(again) == []
    assert moves(again) == [("live", "stopped", None), ("stopped", "live", stop)]
    again.runtime.stop()


def test_a_resume_issued_before_the_stop_does_not_clear_it_after_a_restart(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    arrived = node.now[0]
    ahead = datetime.fromtimestamp(arrived // SECOND + 4, UTC).isoformat()
    value(node.node.call("resume", {"op_id": "op-early", "scope": "all", "issued_at": ahead}))
    node.now[0] = arrived + SECOND
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    again = restarted(node, tmp_path)
    again.runtime.step()

    assert held(again) == [("risk_stop", stop)]
    assert moves(again) == [("live", "stopped", None)]
    again.runtime.stop()


def test_a_stop_whose_lifecycle_row_did_not_land_survives_a_restart_and_lands_after(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    with monkeypatch.context() as refused:
        refused.setattr(stand_down, "JournalWriter", RefusedWriter)
        stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
        node.runtime.step()
        before = held(node)
        unrecorded = lifecycle_rows(node)
    again = restarted(node, tmp_path)
    landed = held(again)
    sent = len(again.account.received)
    driven(again, at(5730), start=at(5570))

    assert stop is None
    assert before == [("risk_stop", None)]
    assert unrecorded == []
    assert len(landed) == 1
    assert landed[0][0] == "risk_stop"
    assert moves(again) == [("live", "stopped", None)]
    assert cast("dict[str, object]", lifecycle_rows(again)[0]["body"])["event_id"] == landed[0][1]
    assert [m for m, _ in entries(again, sent) if m == "fx.eurusd"] == []
    again.runtime.stop()


class _NoStandDownRows:
    """The node journal, refusing only its ``stand_down`` rows."""

    def __init__(self, inner: object) -> None:
        self.inner = inner

    def append(self, kind: str, body: object, facts: object) -> object:
        if kind == "stand_down":
            return storage_failure("the fixture's volume refuses the stand_down row")
        append = cast("Callable[[str, object, object], object]", self.inner.append)  # type: ignore[attr-defined]
        return append(kind, body, facts)


def test_a_stop_no_journal_took_reads_unsafe_to_restart_and_holds_through_a_heal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    downs = node.runtime.stand_downs
    downs.journal = _NoStandDownRows(downs.journal)  # type: ignore[assignment]
    monkeypatch.setattr(stand_down, "JournalWriter", RefusedWriter)
    node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    faults(node, 1)
    node.runtime.step()
    node.runtime.step()
    safe = cast("dict[str, object]", status(node)["safe_to_restart"])
    (opened,) = node.account.positions()

    assert held(node) == [("risk_stop", None)]
    assert safe == {
        "ok": False,
        "reasons": [
            f"position {opened} is open at the venue",
            "Stopped by a risk rule at unit:dep-1:fx.eurusd is held in memory only: no journal"
            " took it"
        ],
    }
    node.runtime.stop()


def test_safe_to_restart_reads_false_while_an_order_is_in_flight(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    node.account.lose_answers = 1
    driven(node, FIRST_SEND + 1)
    first = node.account.received[0].tags
    assert first is not None
    in_flight = cast("dict[str, object]", status(node)["safe_to_restart"])
    node.source.drop()
    node.runtime.step()
    node.runtime.step()
    resolved = cast("dict[str, object]", status(node)["safe_to_restart"])

    assert in_flight == {
        "ok": False,
        "reasons": [f"order {first.client_order_id} is in flight: the venue's answer is unknown"],
    }
    assert resolved == {
        "ok": False,
        "reasons": [f"position {first.client_order_id} is open at the venue"],
    }
    node.runtime.stop()


def stuck_exit(node: Rig) -> None:
    """The watchdog finds the pass stuck and exits the process, as ``StuckWatch.check`` does."""
    watch = node.runtime.watch
    exits: list[int] = []
    watch.exit = exits.append
    watch.began = 0
    watch.steady_ns = lambda: 31 * SECOND
    assert (watch.check(), exits) == ("runtime_stuck", [RUNTIME_STUCK_EXIT_CODE])
    node.runtime.stop()


def test_five_stuck_exits_in_ten_minutes_stand_the_next_start_down_until_his_resume(
    tmp_path: Path,
) -> None:
    for cycle in range(5):
        node = rig(tmp_path)
        if cycle == 0:
            deploy(node, deployment(node.data))
        settle(node)
        stuck_exit(node)
    again = rig(tmp_path)
    settle(again)
    stood = status(again)
    driven(again, at(1440))
    held_a_day = entries(again)
    value(again.node.call("resume", {"op_id": "op-resume-1", "scope": "all"}))
    again.runtime.step()
    cleared = status(again)
    driven(again, at(4500), start=at(1440))

    assert stood["word"] == "Stopped by a health check"
    assert cast("list[object]", stood["reasons"])[0] == (
        "Stopped by a health check: 5 restarts in 10 minutes. It waits for your resume."
    )
    assert again.runtime.alarms[0] == {
        "alarm": "repeated_fault",
        "restarts": 5,
        "action": "no_new_entries",
        "why": "5 restarts in 10 minutes, the last: runtime_stuck",
    }
    assert held_a_day == []
    assert cleared["word"] == "Trading"
    assert again.node.context.store.observed("healing.boots") == []
    assert entries(again) == [("fx.eurusd", Decimal("0.92"))]
    again.runtime.stop()


def keep_venue(monkeypatch: pytest.MonkeyPatch, venue: ConformanceAccount) -> None:
    """The restarted node finds the same venue account, which kept its positions, as a broker
    does."""

    def opened(
        cls: type[ConformanceAccount], *args: object, **kwargs: object
    ) -> Ok[ConformanceAccount]:
        del cls, args, kwargs
        return Ok(venue)

    monkeypatch.setattr(ConformanceAccount, "open", classmethod(opened))


def test_a_process_restart_with_a_position_open_manages_it_and_sends_what_an_unhealed_run_sends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(300))
    venue = node.account
    (opened,) = venue.positions()
    open_before = cast("dict[str, object]", status(node)["safe_to_restart"])
    node.runtime.stop()
    keep_venue(monkeypatch, venue)
    again = rig(tmp_path)
    settle(again)
    driven(again, at(316), start=at(300))
    shown = again.node.context.store.observed("runtime.positions")
    managed = [p["position"] for p in cast("list[dict[str, object]]", shown)]
    while_open = cast("dict[str, object]", status(again)["safe_to_restart"])
    driven(again, LIVE_FROM + 2 * DAY, start=at(316))
    names = [t.tags.client_order_id for t in venue.received if t.tags is not None]

    assert again.account is venue
    assert [(t.command.kind, t.quantity) for t in venue.received] == [
        (CommandKind.PLACE_ORDER, Decimal("1.72")),
        (CommandKind.PLACE_ORDER, Decimal("1.08")),
        (CommandKind.PLACE_ORDER, Decimal("0.75")),
        (CommandKind.CLOSE_POSITION, None),
    ]
    assert opened == names[1]
    assert open_before == {"ok": False, "reasons": [f"position {opened} is open at the venue"]}
    assert managed == [opened]
    assert while_open == {"ok": False, "reasons": [f"position {opened} is open at the venue"]}
    assert [(t["trade_id"], t["exit_kind"], t["quantity"]) for t in unit_rows(again, "trade")] == [
        (names[0], "stop", "1.72"),
        (names[1], "stop", "1.08"),
        (names[2], "close", "0.75"),
    ]
    assert venue.positions() == {}
    assert cast("dict[str, object]", status(again)["safe_to_restart"]) == {"ok": True, "reasons": []}
    again.runtime.stop()


def test_the_guard_refuses_an_entry_where_a_position_of_ours_no_unit_holds_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(300))
    venue = node.account
    (opened,) = venue.positions()
    node.runtime.stop()
    keep_venue(monkeypatch, venue)

    def unheld(self: NodeUnit, found: object) -> None:
        del self, found

    monkeypatch.setattr(NodeUnit, "adopt", unheld)
    again = rig(tmp_path)
    settle(again)
    driven(again, at(316), start=at(300))
    guard = again.runtime.guard(again.runtime.hosted["dep-1"])
    safe = cast("dict[str, object]", status(again)["safe_to_restart"])

    assert guard("fx.eurusd") == (
        f"a position of ours that no unit holds is open on fx.eurusd: {opened}"
    )
    assert guard("metal.xauusd") is None
    assert safe == {
        "ok": False,
        "reasons": [f"position {opened} of ours is open and no unit holds it"],
    }
    again.runtime.stop()


def test_a_kill_he_sends_during_the_back_off_ends_the_wait(tmp_path: Path) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    node.runtime.healer.backoff = Backoff(base_s=16.0)
    slept: list[float] = []
    sleep = node.runtime.sleep

    def counted(seconds: float) -> None:
        slept.append(seconds)
        sleep(seconds)

    node.runtime.sleep = counted
    faults(node, 2)
    node.runtime.step()
    quiet = list(slept)
    slept.clear()

    def killed(seconds: float) -> None:
        counted(seconds)
        if len(slept) == 1:
            value(node.node.call("kill", {"op_id": "op-kill-1", "level": "yellow", "scope": "all"}))

    node.runtime.sleep = killed
    node.runtime.step()
    cut_short = list(slept)
    node.runtime.step()

    assert (len(quiet), sum(quiet)) == (80, 16.0)
    assert cut_short == [0.2]
    assert status(node)["kill_level"] == "YELLOW"
    node.runtime.stop()


def test_a_start_reads_stop_rows_written_before_c13_and_a_cleared_one_stays_cleared(
    tmp_path: Path,
) -> None:
    node = rig(tmp_path)
    deploy(node, deployment(node.data))
    settle(node)
    driven(node, at(5570))
    unit = node.runtime.hosted["dep-1"].unit
    assert unit is not None
    now = node.now[0]
    facts = RowFacts(ts_recv=now, clock_ok=False)
    word = stand_down.TABLE[stand_down.Kind.REPEATED_FAULT]
    journal = node.node.journal
    assert journal is not None
    journal.append(
        "stand_down",
        {
            "event": "start",
            "stand_down": "repeated_fault",
            "scope": "all",
            "word": word.word.value,
            "cause": "5 restarts in 10 minutes",
            "clears": word.clears.value,
            "since_ns": now,
        },
        facts,
    )
    scope = WriterScope(
        JournalStream.UNIT, "dummy-trend-pullback", JournalWorld.DEMO, "pc", "node", BUILD
    )
    writer = JournalWriter.open(
        node.node.context.journal_root, scope, clock=lambda: now, boot_epoch_id="before-c13"
    )
    assert not isinstance(writer, TypedRefusal)
    writer.value.append(
        "lifecycle",
        {
            "schema": LIFECYCLE_SCHEMA,
            "event_id": "lifecycle-before-c13",
            "unit_id": "dummy-trend-pullback",
            "version_ref": unit.compiled.document_fingerprint.value,
            "compiled_fingerprint": unit.compiled.compiled_fingerprint.value,
            "market_id": "fx.eurusd",
            "from": "live",
            "to": "stopped",
            "reason": "the kill line is crossed",
            "at": "2025-03-24T16:36:40+00:00",
            "by": {"kind": "risk_rule", "principal": "kill-line"},
        },
        RowFacts(ts_recv=now, clock_ok=False, unit_id="dummy-trend-pullback", market_id="fx.eurusd"),
    )
    writer.value.close()
    second = restarted(node, tmp_path)
    after_restart = held(second)
    second.now[0] = now + 60 * SECOND
    value(second.node.call("resume", {"op_id": "op-resume-1", "scope": "all"}))
    second.runtime.step()
    after_resume = held(second)
    third = restarted(second, tmp_path)

    assert after_restart == [("repeated_fault", None), ("risk_stop", "lifecycle-before-c13")]
    assert after_resume == []
    assert held(third) == []
    third.runtime.stop()


def test_the_back_off_doubles_to_its_cap_and_starts_again_after_a_healthy_run() -> None:
    backoff = Backoff()
    waits = [backoff.next(n * SECOND) for n in range(8)]
    after_ten_quiet_minutes = backoff.next(7 * SECOND + 600 * SECOND)
    then = backoff.next(8 * SECOND + 600 * SECOND)

    assert waits == [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0]
    assert (after_ten_quiet_minutes, then) == (1.0, 2.0)
