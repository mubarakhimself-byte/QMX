"""An `event` trigger fires on Library ref-log rows: a filter matches its kind, output name and
producer; a cursor holds its place across a restart; a re-delivered object fires it once; and
`coalesce: latest` drops the queued fire a newer object replaced."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import JsonValue
from scheduled import Clock, enabled, fires_of

from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.library import LibraryEvent, LibraryRefused, Stored
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.triggers import event, rows
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 21, 9, 0, tzinfo=UTC)


def artifact(object_id: str, output: str, producer: str, principal: str = "engine:pc") -> Stored:
    return Stored(
        object_id=object_id,
        kind="artifact",
        item=f"app-{producer}",
        ref="refs/runs/run-1",
        fields={"type": output, "metadata": {"producer_app": producer, "output": output}},
        principal=principal,
        at="2026-10-21T09:00:00.000000+00:00",
    )


@dataclass(frozen=True)
class Row:
    seq: int
    stored: Stored


class Stub:
    """A Library whose ref log is a list, so a test can land rows and re-deliver one."""

    def __init__(self, *rows: Row) -> None:
        self.rows = list(rows)

    def land(self, *stored: Stored) -> None:
        first = len(self.rows) + 1
        self.rows += [Row(first + i, found) for i, found in enumerate(stored)]

    def events(self, after: int = 0) -> list[LibraryEvent]:
        return [
            LibraryEvent(
                row.seq, f"library.{row.stored.kind}.created", row.stored.object_id, row.stored.ref
            )
            for row in self.rows
            if row.seq > after
        ]

    def get(self, object_id: str) -> Stored:
        for row in self.rows:
            if row.stored.object_id == object_id:
                return row.stored
        raise LibraryRefused("not_found", f"no object {object_id}")


def make(ledger: Ledger, **filter: JsonValue) -> rows.Trigger:
    return rows.create(
        ledger,
        workflow_item="wf-1",
        pinned_object="obj-1",
        spec=rows.Event(dict(filter)),
        caller=OPERATOR,
        now=T0,
    )


def statuses(trigger_id: str, home: Path) -> list[str]:
    return [fire.status for fire in fires_of(home, trigger_id)]


def test_a_row_matches_on_kind_output_and_producer(tmp_path: Path) -> None:
    library = Stub(Row(1, artifact("a1", "bias", "macro-daily-bias")))
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, kind="artifact", output="bias", producer="macro-daily-bias")
        first = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(
            artifact("a2", "bias", "macro-daily-bias"),
            artifact("a3", "bias", "weekend-watcher"),
            artifact("a4", "signals", "macro-daily-bias"),
        )
        second = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)

    assert (first.fired, len(second.fired)) == ((), 1)
    assert [(fire.status, fire.payload) for fire in fires_of(tmp_path, found.id)] == [
        (
            "pending",
            {
                "event": {
                    "object_id": "a2",
                    "seq": 2,
                    "kind": "artifact",
                    "output": "bias",
                    "producer": "macro-daily-bias",
                }
            },
        )
    ]


def test_the_cursor_starts_at_the_tail_and_moves_past_unmatched_rows(tmp_path: Path) -> None:
    library = Stub(Row(1, artifact("a1", "bias", "macro")), Row(2, artifact("a2", "bias", "macro")))
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, output="bias")
        first = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(artifact("a3", "signals", "macro"), artifact("a4", "bias", "macro"))
        second = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        with Reader.open(tmp_path) as reader:
            cursor = event.cursor_of(reader.connection, found.id)

    assert (first.fired, first.cursor) == ((), 2)
    assert (len(second.fired), cursor) == (1, 4)
    assert statuses(found.id, tmp_path) == ["pending"]


def test_a_redelivered_object_fires_the_trigger_once(tmp_path: Path) -> None:
    one = artifact("a1", "bias", "macro")
    library = Stub(Row(1, artifact("a0", "bias", "macro")))
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, output="bias")
        event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(one, one)
        fired = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        again = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)

    assert (len(fired.fired), again.fired) == (1, ())
    assert statuses(found.id, tmp_path) == ["pending"]


def test_coalesce_latest_drops_the_queued_fire_a_newer_object_replaced(tmp_path: Path) -> None:
    library = Stub()
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, output="bias", coalesce="latest")
        event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(artifact("a1", "bias", "macro"))
        event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(artifact("a2", "bias", "macro"), artifact("a3", "bias", "macro"))
        drained = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        queued = fires_of(tmp_path, found.id)

    assert (len(drained.fired), drained.superseded) == (1, 1)
    assert [(fire.status, fire.detail) for fire in queued] == [
        ("skipped", "superseded by object a3"),
        ("pending", None),
    ]
    assert queued[1].payload == {
        "event": {
            "object_id": "a3",
            "seq": 3,
            "kind": "artifact",
            "output": "bias",
            "producer": "macro",
        }
    }


def test_coalesce_each_keeps_one_fire_per_landing(tmp_path: Path) -> None:
    library = Stub()
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, output="bias")
        event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        library.land(artifact("a1", "bias", "macro"), artifact("a2", "bias", "macro"))
        drained = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)

    assert len(drained.fired) == 2
    assert statuses(found.id, tmp_path) == ["pending", "pending"]


def test_a_filter_that_names_nothing_and_an_unknown_key_are_refused() -> None:
    with pytest.raises(Refused, match=r"an event filter names kind, output or producer"):
        event.parse({})
    with pytest.raises(Refused, match=r"an event filter has no rang"):
        event.parse({"rang": "artifact"})
    with pytest.raises(Refused, match=r"coalesce is each or latest"):
        event.parse({"output": "bias", "coalesce": "none"})


def test_a_pause_holds_the_cursor_and_hands_back_one_fire(tmp_path: Path) -> None:
    library = Stub(Row(1, artifact("a1", "bias", "macro")))
    with Ledger.open(tmp_path) as ledger:
        found = make(ledger, output="bias")
        event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        paused = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0, paused=True)
        library.land(artifact("a2", "bias", "macro"), artifact("a3", "bias", "macro"))
        still = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0, paused=True)
        resumed = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        queued = fires_of(tmp_path, found.id)

    assert (paused.fired, still.fired, len(resumed.fired)) == ((), (), 1)
    assert queued[0].payload == {
        "event": {
            "object_id": "a3",
            "seq": 3,
            "kind": "artifact",
            "output": "bias",
            "producer": "macro",
        }
    }


def test_a_trigger_on_another_engine_keeps_no_cursor_here(tmp_path: Path) -> None:
    library = Stub(Row(1, artifact("a1", "bias", "macro")))
    with Ledger.open(tmp_path) as ledger:
        found = rows.create(
            ledger,
            workflow_item="wf-1",
            pinned_object="obj-1",
            spec=rows.Event({"output": "bias"}),
            caller=OPERATOR,
            now=T0,
            place="contabo",
            places={"pc": "pc", "contabo": "contabo"},
        )
        drained = event.drain(ledger, library, home=tmp_path, engine="pc", now=T0)
        with Reader.open(tmp_path) as reader:
            cursor = event.cursor_of(reader.connection, found.id)

    assert (drained.fired, cursor) == ((), None)


def test_a_report_matches_by_its_writer_and_an_artifact_by_its_app() -> None:
    report = Stored(
        object_id="r1",
        kind="test-report",
        item="hub-health",
        ref="refs/hub/health",
        fields={"status": "passed"},
        principal="hub",
        at="2026-10-21T09:00:00.000000+00:00",
    )
    found = event.landing(LibraryEvent(7, "library.test-report.created", "r1", "main"), report)

    assert found == event.Landing(7, "r1", "test-report", None, "hub")
    assert found.matches(event.Filter(producer="hub"))
    assert not found.matches(event.Filter(output="bias"))


def test_a_hand_landed_artifact_names_its_app_under_ref() -> None:
    stored = Stored(
        object_id="h1",
        kind="artifact",
        item="app-macro",
        ref="refs/runs/run-9",
        fields={"type": "bias", "metadata": {"ref": {"producer_app": "macro-daily-bias"}}},
        principal="run:run-9",
        at="2026-10-21T09:00:00.000000+00:00",
    )

    assert event.producer_of(stored) == "macro-daily-bias"


def test_a_tick_fires_a_landing_and_starts_the_run(tmp_path: Path) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Event({"kind": "artifact", "output": "bias"}),
            caller=OPERATOR,
            now=clock.now(),
        )
        ticker = Scheduler(svc.ctx, credentials=set(), skills=set())
        made: list[str] = []

        async def drive() -> None:
            await ticker.tick()
            made.append(
                svc.ctx.library.put_artifact(
                    b'{"bias": 1}',
                    "bias",
                    {"ref": {"producer_app": "macro-daily-bias"}},
                    run_id="run-1",
                    principal="run:run-1",
                    intent_key="bias-1",
                ).object_id
            )
            clock.move(seconds=60)
            await ticker.tick()
            await ticker.settle()

        asyncio.run(drive())

    found = fires_of(tmp_path, trigger.id)
    assert [(fire.status, fire.delivery_id) for fire in found] == [("ok", "event:" + made[0])]
