"""Heartbeats (AD-65): one row schema for hosts and apps, a log pruned to its window, preflight
holding a node whose host lacks its kind, and a consumer's refusal filed on the producer."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from qmx_apps.supervisor import Supervisor
from scheduled import Clock, enabled, fires_of

from qmx_engine.heartbeat import (
    ClassUse,
    ClockFacts,
    Heartbeat,
    HeartbeatLog,
    host_kinds,
    kinds_digest,
    latest,
    node_kinds,
    read_row,
)
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)


def host_row(at: datetime, kinds: tuple[str, ...] = (), host: str = "pc") -> Heartbeat:
    return Heartbeat(
        subject="host",
        id=host,
        at=at.isoformat(),
        cpu_seconds=1.5,
        rss_bytes=1_000,
        machine_minutes=2.0,
        qmx_version="0.1.0",
        node_kinds=kinds,
        kinds_digest=kinds_digest(kinds),
        paused=False,
    )


def test_a_row_round_trips_through_the_log_and_unknown_fields_are_refused(tmp_path: Path) -> None:
    log = HeartbeatLog(tmp_path, 7)
    log.write([host_row(T0, ("script", "trigger"))])
    log.write([host_row(T0 + timedelta(seconds=30), ("script", "trigger"))])

    found = log.rows()
    newest = latest(tmp_path)

    assert [r.at for r in found] == ["2026-10-17T09:00:00+00:00", "2026-10-17T09:00:30+00:00"]
    assert list(newest) == ["host:pc"]
    assert newest["host:pc"].at == "2026-10-17T09:00:30+00:00"
    assert host_kinds(tmp_path) == {"pc": frozenset({"script", "trigger"})}
    assert len(found[0].model_dump_json()) < 4_096
    with pytest.raises(ValidationError):
        Heartbeat.model_validate({**found[0].model_dump(), "budget": 5})


CLOCK = ClockFacts(
    zone="Europe/London",
    offset_ms=-3,
    delay_ms=21,
    source="0.pool.ntp.org",
    source_kind="w32time",
    synced=True,
    tzdata="2025b",
    band="ok",
    probed_at="2026-10-17T08:59:30+00:00",
)


def test_a_row_with_clock_facts_round_trips_and_an_older_row_without_them_loads(
    tmp_path: Path,
) -> None:
    log = HeartbeatLog(tmp_path, 7)
    older = host_row(T0).model_dump(mode="json")
    del older["clock"]
    log.write([host_row(T0 + timedelta(seconds=30)).model_copy(update={"clock": CLOCK})])

    [found] = log.rows()

    assert found.clock == CLOCK
    assert latest(tmp_path)["host:pc"].clock == CLOCK
    assert read_row(older).clock is None


def test_a_newer_row_with_unknown_fields_loads_and_a_malformed_known_field_is_refused(
    tmp_path: Path,
) -> None:
    newer = host_row(T0).model_dump(mode="json") | {
        "clock": CLOCK.model_dump(mode="json") | {"leap": "none"},
        "gpu_seconds": 4.0,
    }
    newer["capacity"] = {"chat": {"used": 1, "size": 4, "queued_by_kind": {}}}
    day = tmp_path / "logs" / "heartbeat-2026-10-17.jsonl"
    day.parent.mkdir(parents=True)
    day.write_text(json.dumps(newer) + "\n", encoding="utf-8")
    (tmp_path / "logs" / "heartbeat-latest.json").write_text(
        json.dumps({"host:pc": newer}), encoding="utf-8"
    )

    [row] = HeartbeatLog(tmp_path, 7).rows()

    assert (row.id, row.cpu_seconds, row.clock) == ("pc", 1.5, CLOCK)
    assert row.capacity == {"chat": ClassUse(used=1, size=4)}
    assert latest(tmp_path)["host:pc"].clock == CLOCK
    with pytest.raises(ValidationError, match="offset_ms"):
        read_row(newer | {"clock": CLOCK.model_dump(mode="json") | {"offset_ms": "three"}})
    with pytest.raises(ValidationError, match="cpu_seconds"):
        read_row(json.dumps(newer | {"cpu_seconds": "busy"}))


def test_the_supervisors_app_rows_complete_into_the_one_schema(tmp_path: Path) -> None:
    supervisor = Supervisor(tmp_path)
    app = SimpleNamespace(
        state="running",
        definition=SimpleNamespace(manifest=SimpleNamespace(id="pricer")),
        cpu=2.5,
        memory=4_096,
        started=time.monotonic() - 120,
    )
    supervisor._instances["pricer"] = app  # pyright: ignore[reportPrivateUsage, reportArgumentType]

    [row] = supervisor.heartbeats()
    completed = Heartbeat.model_validate(
        {**row, "qmx_version": "0.1.0", "kinds_digest": kinds_digest(()), "paused": True}
    )

    assert (completed.subject, completed.id, completed.cpu_seconds, completed.rss_bytes) == (
        "app",
        "pricer",
        2.5,
        4_096,
    )
    assert round(completed.machine_minutes) == 2


def test_prune_drops_exactly_the_rows_older_than_the_window(tmp_path: Path) -> None:
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    log = HeartbeatLog(tmp_path, 7)
    ages = [timedelta(days=9), timedelta(days=7, hours=1), timedelta(days=6, hours=23)]
    log.write([host_row(now - age) for age in ages])

    gone = log.prune(now)

    assert gone == 2
    assert [r.at for r in log.rows()] == ["2026-10-12T13:00:00+00:00"]
    assert sorted(p.name for p in (tmp_path / "logs").glob("*.jsonl")) == [
        "heartbeat-2026-10-12.jsonl"
    ]


def test_a_node_whose_host_lacks_its_kind_waits_placement(tmp_path: Path) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        stale = tuple(k for k in node_kinds() if k != "script")
        HeartbeatLog(tmp_path, 7).write([host_row(T0, stale)])
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=Cron("0 * * * *", "UTC"),
            caller=OPERATOR,
            now=clock.now(),
        )
        clock.move(hours=1)
        ticker = Scheduler(svc.ctx)

        async def go() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(go())
        found = fires_of(tmp_path, trigger.id)

    held = (
        "placement: node needs update (Numbers: pc lacks script)"
        " until 2026-10-17T10:00:30.000000+00:00"
    )
    assert [(f.status, f.detail, f.run_id) for f in found] == [("held", held, None)]


def test_a_consumers_schema_refusal_is_a_dependency_incident_on_the_producer(
    tmp_path: Path,
) -> None:
    with InboxTable.open(tmp_path) as inbox:
        first = inbox.refused_output(
            "digest", "pricer", "quotes", "field price is missing at row 12", at="t1"
        )
        again = inbox.refused_output(
            "digest", "pricer", "quotes", "field price is missing at row 40", at="t2"
        )
        [incident] = inbox.app_incidents()
        with pytest.raises(sqlite3.IntegrityError):
            inbox.app_incident("pricer", "budget", "sig", "t", "c", at="t3")  # pyright: ignore[reportArgumentType]

    assert first == again
    assert (incident.app_id, incident.kind, incident.count) == ("pricer", "dependency", 2)
    assert incident.title == "digest refused pricer's quotes"
    assert (incident.first_seen, incident.last_seen) == ("t1", "t2")
