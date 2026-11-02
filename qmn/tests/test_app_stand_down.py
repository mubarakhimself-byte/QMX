"""Every stand-down stops entries, keeps exits and broker stops, and clears by its rule (AD-38).

Table-driven over the seven rows of Level 0 AD-38, on the conformance venue only. The dummy's
recorded days hold a unit close at minute 1243 and a broker stop at minute 5638 of the played
days, so each row is held across one and then the other, and the entry it would have let out
is kept back. A risk stop is the one automatic move in trading: one ``lifecycle`` row by
``risk_rule``, then nothing until his resume (standing order 7).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import groupby
from pathlib import Path
from typing import cast

import pytest
from qmf.core import TypedRefusal
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.store.refusals import storage_failure
from qmf.venue.commands import CommandKind
from qml.lifecycle import Actor, ActorKind, Event, Folded, MarketKey, State, fold
from qmn.app import stand_down
from qmn.app.feed_keeper import Bar, Quote
from qmn.app.runtime import NodeUnit
from qmn.app.stand_down import Kind, StandDowns
from test_app_runtime import (
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

MINUTE = 60_000_000_000


def at(minute: int) -> int:
    return LIVE_FROM + minute * MINUTE


@dataclass
class Probes:
    """What each row's cause is read from: the clock offset, the free bytes, the quotes."""

    offset: int | None = None
    free: int = 50 * 1024**3
    silent: frozenset[str] = frozenset()


def played(node: Rig, probes: Probes, until: int) -> None:
    """The recorded bars from the last tick to ``until``, one tick per bar, with no quotes for
    the markets in ``probes.silent``, so their feed goes stale while their bars still close."""
    start = max(node.now[0] + 1, LIVE_FROM)
    live = [item for item in month().bars if start <= item[0] < until]
    for moment, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        node.now[0] = moment
        quotes = [
            Quote(market, moment, bar.bid.close, bar.ask.close, "both")
            for _, market, bar in closed
            if market not in probes.silent
        ]
        node.source.play([*(Bar(market, bar) for _, market, bar in closed), *quotes])
        node.runtime.tick()


def resume(node: Rig, scope: object) -> None:
    """His resume, under an op id of its own: the rig's random source mints the same one."""
    op_id = f"op-resume-{node.now[0]}"
    value(node.node.call("resume", {"op_id": op_id, "scope": cast("dict[str, object]", scope)}))


@dataclass(frozen=True)
class Case:
    kind: Kind
    enter: Callable[[Rig, Probes], None]
    clear: Callable[[Rig, Probes], None]
    detail: str


def _silent(*markets: str) -> Callable[[Rig, Probes], None]:
    def flip(node: Rig, probes: Probes) -> None:
        del node
        probes.silent = frozenset(markets)

    return flip


def _offset(offset: int | None) -> Callable[[Rig, Probes], None]:
    def set_(node: Rig, probes: Probes) -> None:
        del node
        probes.offset = offset

    return set_


def _free(free: int) -> Callable[[Rig, Probes], None]:
    def set_(node: Rig, probes: Probes) -> None:
        del node
        probes.free = free

    return set_


def _drop(node: Rig, probes: Probes) -> None:
    del probes
    node.source.refuse_verify = True
    node.source.drop()
    node.runtime.tick()


def _ready(node: Rig, probes: Probes) -> None:
    del probes
    node.source.refuse_verify = False


def _held(kind: Kind, scope: str) -> Callable[[Rig, Probes], None]:
    def hold(node: Rig, probes: Probes) -> None:
        del probes
        assert node.runtime.stand_down(kind, scope, "the fixture's cause") is True

    return hold


def _risk(node: Rig, probes: Probes) -> None:
    del probes
    stopped = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    assert stopped is not None


def _resume(scope: object) -> Callable[[Rig, Probes], None]:
    def clear(node: Rig, probes: Probes) -> None:
        del probes
        resume(node, scope)

    return clear


CASES = (
    Case(
        Kind.STALE_FEED,
        _silent("fx.eurusd"),
        _silent(),
        "stood down, stale feed: the node cannot prove a fresh price (last quote 900 s ago)",
    ),
    Case(
        Kind.CLOCK_BAND,
        _offset(600_000_000),
        _offset(0),
        "stood down, clock band: the node cannot prove its clock (clock offset 600000000 ns)",
    ),
    Case(
        Kind.DISK,
        _free(1024**3),
        _free(4 * 1024**3),
        "stood down, disk: free space is below the node journal guard (1073741824 bytes free)",
    ),
    Case(
        Kind.VENUE_NOT_READY,
        _drop,
        _ready,
        "venue not ready: connected, capabilities not re-verified (unavailable dependency)",
    ),
    Case(
        Kind.REPEATED_FAULT,
        _held(Kind.REPEATED_FAULT, "all"),
        _resume("all"),
        "stood down, repeated fault: the node cannot prove its runtime is sound until his resume"
        " (the fixture's cause)",
    ),
    Case(
        Kind.SPEC_CHANGE,
        _held(Kind.SPEC_CHANGE, "instrument:fx.eurusd"),
        _resume({"instrument": "fx.eurusd"}),
        "stood down, spec change: the node cannot prove its orders against the broker's changed"
        " record until his click (the fixture's cause)",
    ),
    Case(
        Kind.RISK_STOP,
        _risk,
        _resume({"deployment_id": "dep-1"}),
        "risk stop: a risk rule holds this unit's entries, as the kill switch would, until his"
        " resume (kill-line: the kill line is crossed)",
    ),
)


SELF_CLEARING = frozenset({Kind.STALE_FEED, Kind.CLOCK_BAND, Kind.DISK, Kind.VENUE_NOT_READY})


def tickets(node: Rig, after: int) -> list[tuple[CommandKind, str, str]]:
    return [(t.command.kind, t.market_id, t.side.value) for t in node.account.received[after:]]


@pytest.mark.parametrize("case", CASES, ids=[case.kind.value for case in CASES])
def test_each_row_stops_entries_keeps_exits_and_broker_stops_and_clears_by_its_rule(
    tmp_path: Path, case: Case
) -> None:
    node = rig(tmp_path)
    probes = Probes()
    node.runtime.stand_downs.clock_offset_ns = lambda: probes.offset
    node.runtime.stand_downs.free_bytes = lambda: probes.free
    deploy(node, deployment(node.data))
    assert settle(node) == "trading"
    played(node, probes, at(530))

    first = len(node.account.received)
    case.enter(node, probes)
    played(node, probes, at(1300))
    held_first = node.runtime.stand_downs.document()
    exits = tickets(node, first)
    case.clear(node, probes)
    played(node, probes, at(1320))
    cleared_first = node.runtime.stand_downs.document()

    played(node, probes, at(5570))
    second = len(node.account.received)
    case.enter(node, probes)
    played(node, probes, at(5730))
    stops = [(t["exit_kind"], t["quantity"]) for t in unit_rows(node, "trade")]
    kept_back = tickets(node, second)
    guards = [row["detail"] for row in unit_rows(node, "guard")]
    case.clear(node, probes)
    played(node, probes, at(5760))
    cleared_second = node.runtime.stand_downs.document()
    journalled = [
        (body["event"], body["stand_down"], body.get("cleared_by"))
        for row in cast(
            "list[dict[str, object]]",
            value(node.node.call("journal_tail", {"streams": ["node"]}))["rows"],
        )
        if row["kind"] == "stand_down"
        for body in [cast("dict[str, object]", row["body"])]
    ]

    assert [held["stand_down"] for held in held_first] == [case.kind.value]
    assert exits == [(CommandKind.CLOSE_POSITION, "fx.eurusd", "short")]
    assert cleared_first == []
    assert kept_back == []
    assert stops[:5] == [
        ("stop", "1.72"),
        ("stop", "1.08"),
        ("close", "0.75"),
        ("close", "0.91"),
        ("stop", "1.60"),
    ]
    assert guards == [case.detail]
    assert cleared_second == []
    by = "itself" if case.kind in SELF_CLEARING else "operator"
    assert (
        journalled
        == [
            ("start", case.kind.value, None),
            ("clear", case.kind.value, by),
        ]
        * 2
    )
    node.runtime.stop()


def lifecycle_rows(node: Rig) -> list[dict[str, object]]:
    rows = value(node.node.call("journal_tail", {"streams": ["unit"]}))["rows"]
    return [row for row in cast("list[dict[str, object]]", rows) if row["kind"] == "lifecycle"]


def folded(rows: list[dict[str, object]], earlier: list[Event]) -> Folded:
    """The node's moves folded after the PC's own, as the PC folds them once harvested."""
    events = list(earlier)
    for row in rows:
        body = cast("dict[str, object]", row["body"])
        by = cast("dict[str, str]", body["by"])
        clears = body.get("clears")
        events.append(
            Event(
                event_id=str(body["event_id"]),
                unit_id=str(body["unit_id"]),
                version_ref=str(body["version_ref"]),
                compiled_fingerprint=str(body["compiled_fingerprint"]),
                market_id=str(body["market_id"]),
                from_state=State(str(body["from"])),
                to_state=State(str(body["to"])),
                by=Actor(ActorKind(by["kind"]), by["principal"]),
                reason=str(body["reason"]),
                evidence_ref=None,
                at=datetime.fromisoformat(str(body["at"])),
                writer=str(row["writer_id"]),
                sequence=cast("int", row["seq"]),
                clears=None if clears is None else str(clears),
            )
        )
    return fold(events)


def test_a_risk_stop_lands_one_lifecycle_event_and_waits_for_his_resume(tmp_path: Path) -> None:
    node = rig(tmp_path)
    probes = Probes()
    deploy(node, deployment(node.data))
    settle(node)
    played(node, probes, at(5570))
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    again = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "crossed again")
    sent = len(node.account.received)
    played(node, probes, at(5 * 1440 + 5570))
    held = node.runtime.stand_downs.document()
    after_a_day = tickets(node, sent)
    rows_held = lifecycle_rows(node)
    resume(node, {"deployment_id": "dep-1"})
    node.runtime.tick()
    rows = lifecycle_rows(node)
    unit = cast("NodeUnit", node.runtime.hosted["dep-1"].unit)
    key = MarketKey("dummy-trend-pullback", unit.compiled.document_fingerprint.value, "fx.eurusd")
    earlier = [
        Event(
            f"pc-{sequence}",
            key.unit_id,
            key.version_ref,
            unit.compiled.compiled_fingerprint.value,
            "fx.eurusd",
            start,
            end,
            Actor(kind, principal),
            "before the deployment",
            None,
            datetime(2025, 3, 20, sequence, tzinfo=UTC),
            "host@pc",
            sequence,
        )
        for sequence, (start, end, kind, principal) in enumerate(
            (
                (State.DRAFT, State.TESTED, ActorKind.JUDGE, "judge"),
                (State.TESTED, State.PAPER, ActorKind.HIS_CLICK, "operator"),
                (State.PAPER, State.LIVE, ActorKind.HIS_CLICK, "operator"),
            )
        )
    ]
    moves = folded(rows, earlier)

    assert stop is not None
    assert again == stop
    assert [(h["stand_down"], h["word"], h.get("lifecycle_event")) for h in held] == [
        ("risk_stop", "Stopped by a risk rule", stop)
    ]
    assert [t for t in after_a_day if t[1] == "fx.eurusd" and t[0] is CommandKind.PLACE_ORDER] == []
    assert len(rows_held) == 1
    assert [
        (
            row["world"],
            body["event_id"],
            body["from"],
            body["to"],
            body["by"],
            body.get("clears"),
            body["reason"],
        )
        for row in rows
        for body in [cast("dict[str, object]", row["body"])]
    ] == [
        (
            "demo",
            stop,
            "live",
            "stopped",
            {"kind": "risk_rule", "principal": "kill-line"},
            None,
            "the kill line is crossed",
        ),
        (
            "demo",
            cast("dict[str, object]", rows[1]["body"])["event_id"],
            "stopped",
            "live",
            {"kind": "his_click", "principal": "operator"},
            stop,
            "his resume",
        ),
    ]
    assert moves.rejected == ()
    assert moves.state(key) is State.LIVE
    assert node.runtime.stand_downs.document() == []
    node.runtime.stop()


class RefusedWriter:
    """A journal whose lifecycle stream will not open, as a full or locked volume answers."""

    @staticmethod
    def open(*args: object, **kwargs: object) -> TypedRefusal:
        del args, kwargs
        return storage_failure("the fixture's volume refuses the lifecycle stream")


def held_now(node: Rig) -> list[tuple[object, object]]:
    return [(h["stand_down"], h.get("lifecycle_event")) for h in node.runtime.stand_downs.document()]


def test_a_risk_stop_whose_row_cannot_land_still_holds_entries_and_raises_an_alarm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = rig(tmp_path)
    probes = Probes()
    deploy(node, deployment(node.data))
    settle(node)
    played(node, probes, at(5570))
    monkeypatch.setattr(stand_down, "JournalWriter", RefusedWriter)
    sent = len(node.account.received)
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    played(node, probes, at(5730))
    entries = [t for t in tickets(node, sent) if t[0] is CommandKind.PLACE_ORDER]
    guards = [row["detail"] for row in unit_rows(node, "guard")]

    assert stop is None
    assert held_now(node) == [("risk_stop", None)]
    assert len(entries) == 0
    assert guards == [CASES[-1].detail]
    assert lifecycle_rows(node) == []
    assert node.runtime.alarms == [
        {
            "alarm": "risk_stop_unrecorded",
            "deployment_id": "dep-1",
            "market_id": "fx.eurusd",
            "rule": "kill-line",
            "action": "no_new_entries",
            "why": "the stop's lifecycle row could not be written, so only the node shows it",
        }
    ]
    node.runtime.stop()


def test_a_resume_he_sent_before_a_risk_stop_does_not_clear_it(tmp_path: Path) -> None:
    node = rig(tmp_path)
    probes = Probes()
    deploy(node, deployment(node.data))
    settle(node)
    played(node, probes, at(5570))
    arrived = node.now[0]
    ahead = datetime.fromtimestamp(arrived // 1_000_000_000 + 4, UTC).isoformat()
    early = node.node.call("resume", {"op_id": "op-resume-early", "scope": "all", "issued_at": ahead})
    node.now[0] = arrived + 1_000_000_000
    stop = node.runtime.risk_stop("dep-1", "fx.eurusd", "kill-line", "the kill line is crossed")
    node.runtime.tick()

    assert early["ok"] is True
    assert stop is not None
    assert held_now(node) == [("risk_stop", stop)]
    node.runtime.stop()


def test_a_health_stop_clears_only_after_its_cause_stays_gone_its_named_time(
    tmp_path: Path,
) -> None:
    now = [LIVE_FROM]
    offset: list[int | None] = [600_000_000]
    free = [50 * 1024**3]
    alarms: list[Mapping[str, object]] = []
    scope = WriterScope(JournalStream.NODE, "a4dqobyh", JournalWorld.DEMO, "pc", "node", "0.1.0")
    journal = JournalWriter.open(tmp_path, scope, clock=lambda: now[0], boot_epoch_id="e1")
    assert not isinstance(journal, TypedRefusal), journal
    downs = StandDowns(
        journal.value,
        journal_root=tmp_path,
        machine="pc",
        build="0.1.0",
        boot_epoch_id="e1",
        clock_ns=lambda: now[0],
        free_bytes=lambda: free[0],
        on_alarm=alarms.append,
        clock_offset_ns=lambda: offset[0],
    )
    seen: list[list[str]] = []
    for minute, reading, space in (
        (0, 600_000_000, 1024**3),
        (1, 50_000_000, int(2.5 * 1024**3)),
        (4, 300_000_000, int(3.5 * 1024**3)),
        (8, 50_000_000, int(3.5 * 1024**3)),
        (13, 50_000_000, 1024**3),
        (14, 50_000_000, int(3.5 * 1024**3)),
    ):
        now[0], offset[0], free[0] = at(minute), reading, space
        downs.watch_node()
        seen.append([str(held["stand_down"]) for held in downs.document()])
    downs.hold(Kind.REPEATED_FAULT, "all", "5 restarts in 10 minutes")
    now[0] = at(14 + 1440)
    downs.watch_node()
    held_a_day = [str(held["stand_down"]) for held in downs.document()]

    assert seen == [
        ["clock_band", "disk"],
        ["clock_band", "disk"],
        ["clock_band"],
        ["clock_band"],
        ["disk"],
        [],
    ]
    assert held_a_day == ["repeated_fault"]
    downs.close()
    journal.value.close()
