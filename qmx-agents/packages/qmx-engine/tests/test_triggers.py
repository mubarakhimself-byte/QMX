"""Trigger rows and fires: a run cannot create a trigger, preflight tells the workflow's own faults
from a provider's, the new kinds migrate, a webhook delivery fires once, priority beats age, the
market holds a weekend fire, the pause flag stops every fire until cleared, and one signature's
failures are one incident with spend-neutral re-runs."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from flows import CHAIN, edited, node, workflow
from scheduled import Clock, Flags, enabled, fires_of

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller, Refused
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.preflight import placement_state, preflight
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
"""A Saturday."""
MONDAY = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)


def test_a_placement_is_configured_by_the_rows_an_attempt_needs_not_by_a_memory_budget() -> None:
    contabo = {
        key: value for key, value in DEFAULTS.items() if key.startswith("placement.contabo.")
    }
    bare = {"placement.contabo.kind": "owned"}

    assert placement_state(contabo, "contabo") == "authorized"
    assert placement_state(bare, "contabo") == "configured"
    assert placement_state({}, "contabo") == "unavailable"


def test_a_workflow_caller_cannot_create_a_trigger(tmp_path: Path) -> None:
    def create(caller: Caller) -> rows.Trigger:
        return rows.create(
            ledger,
            workflow_item="wf-1",
            pinned_object="obj-1",
            spec=Cron("0 * * * *", "Europe/London"),
            caller=caller,
            now=T0,
        )

    with Ledger.open(tmp_path) as ledger:
        with pytest.raises(Refused, match=r"^trigger_refused:"):
            create(Caller("workflow", "run-1"))
        made = create(Caller("agent", "s1"))

    assert (made.created_by, made.next_fire_at) == ("agent:s1", "2026-10-17T10:00:00.000000+00:00")


def test_a_missing_role_is_the_workflows_fault_and_a_missing_key_the_providers() -> None:
    ghost = workflow([node("Ask", "llm") | {"role": "ghost"}], {})
    keyed = workflow([node("Ask", "llm") | {"role": "triage", "credentials": {"key": "qmx/x"}}], {})
    tool = workflow([node("Run", "script") | {"credentials": {"FEED": "qmx/tool/feed"}}], {})

    lost = preflight(ghost, DEFAULTS, profiles={"claude"}, credentials=None, skills=None)
    unkeyed = preflight(keyed, DEFAULTS, profiles={"claude"}, credentials=set(), skills=None)
    scripted = preflight(tool, DEFAULTS, profiles={"claude"}, credentials=set(), skills=None)

    assert lost is not None
    assert (lost.cause, lost.code) == ("config", "role_missing")
    assert unkeyed is not None
    assert (unkeyed.cause, unkeyed.code) == ("provider", "credential_missing")
    assert scripted is None


def test_old_trigger_rows_survive_the_kind_migration_and_new_kinds_store(tmp_path: Path) -> None:
    path = tmp_path / "engine" / "engine.sqlite"
    path.parent.mkdir(parents=True)
    old = sqlite3.connect(path)
    for statement in (*STEPS[0], *STEPS[1]):
        old.execute(statement)
    old.execute("INSERT INTO meta VALUES ('schema_version', '2')")
    old.execute(
        "INSERT INTO triggers VALUES ('trigger-old', 'wf', 'obj', 0, 'pc', 'cron',"
        ' \'{"expr": "0 * * * *", "zone": "UTC"}\', 1, NULL, \'{}\', NULL, \'digest\', 0,'
        " 'merged', 1, 'ticker', 'operator', '2026-10-01T00:00:00.000000+00:00', NULL, 'ok', 0,"
        " NULL, NULL, NULL)"
    )
    old.commit()
    old.close()

    with Ledger.open(tmp_path) as ledger:
        applied = ledger.applied
        for spec in (rows.Webhook(), rows.Session(), rows.Event({"kind": "report"})):
            rows.create(
                ledger, workflow_item="wf", pinned_object="obj", spec=spec, caller=OPERATOR, now=T0
            )
    with Reader.open(tmp_path) as reader:
        found = rows.triggers(reader.connection)

    assert applied == [3]
    old_row = found[0]
    assert (old_row.id, old_row.kind, old_row.priority, old_row.last_status) == (
        "trigger-old",
        "cron",
        0,
        "ok",
    )
    assert sorted(t.kind for t in found[1:]) == ["event", "session", "webhook"]
    assert [t.spec for t in found if t.kind == "event"] == [rows.Event({"kind": "report"})]


def test_a_webhook_delivered_twice_with_one_id_fires_once(tmp_path: Path) -> None:
    clock = Clock(MONDAY)
    with enabled(tmp_path, clock) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Webhook(),
            caller=OPERATOR,
            now=clock.now(),
        )
        ticker = Scheduler(svc.ctx)

        async def go() -> list[tuple[bool, str]]:
            answers = [
                await ticker.deliver(trigger.id, "delivery-1", {"order": 7}) for _ in range(2)
            ]
            await ticker.settle()
            return [(bool(a["duplicate"]), str(a["fire_id"])) for a in answers]

        (first, second) = asyncio.run(go())
        found = fires_of(tmp_path, trigger.id)

    assert (first[0], second[0], first[1] == second[1]) == (False, True, True)
    assert [(f.status, f.delivery_id, f.delivery) for f in found] == [
        ("ok", "delivery-1", "delivered")
    ]


def test_priority_beats_age_and_ready_by_raises_it_as_the_deadline_nears(tmp_path: Path) -> None:
    clock = Clock(MONDAY)
    with enabled(tmp_path, clock) as (svc, version):
        ledger = svc.ctx.engine.ledger
        item = svc.versions.get(version).item

        def manual(priority: int) -> rows.Trigger:
            return rows.create(
                ledger,
                workflow_item=item,
                pinned_object=version,
                spec=rows.Manual(),
                caller=OPERATOR,
                now=clock.now(),
                priority=priority,
            )

        low, high = manual(1), manual(5)
        rows.fire_now(ledger, low.id, clock.now(), {})
        clock.move(seconds=30)
        rows.fire_now(ledger, high.id, clock.now(), {})
        ticker = Scheduler(svc.ctx)

        async def go() -> list[int]:
            tick = await ticker.tick()
            await ticker.settle()
            return [c.trigger.priority for c in tick.claimed]

        order = asyncio.run(go())

    paced = rows.Trigger("t", "wf", "obj", rows.Manual(), "operator", "", ready_by="10:00")
    at = datetime(2026, 10, 19, 8, 0, tzinfo=UTC)
    assert order == [5, 1]
    assert [
        rows.priority_at(paced, at, datetime(2026, 10, 19, h, m, tzinfo=UTC), 3600)
        for h, m in ((8, 30), (9, 30), (10, 5))
    ] == [0, 5, 10]


def test_market_open_holds_a_saturday_fire_and_explain_says_why(tmp_path: Path) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=Cron("0 * * * *", "Europe/London"),
            caller=OPERATOR,
            now=clock.now(),
            precheck_ref="market_open",
        )
        clock.move(hours=1)
        ticker = Scheduler(svc.ctx)

        async def go() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(go())
        explained = ticker.explain(trigger.id)
        found = fires_of(tmp_path, trigger.id)

    shut = "the market is shut in Europe/London until 2026-10-18T23:00:00.000000+00:00"
    assert [(f.status, f.detail, f.run_id) for f in found] == [("held", shut, None)]
    assert explained["verdict"] == f"held: {shut}"


def test_the_pause_flag_stops_every_fire_until_cleared_then_each_fires_once(
    tmp_path: Path,
) -> None:
    clock = Clock(T0)
    flags = Flags(autonomy__paused=1)
    with enabled(tmp_path, clock, settings=flags) as (svc, version):
        made = [
            rows.create(
                svc.ctx.engine.ledger,
                workflow_item=svc.versions.get(version).item,
                pinned_object=version,
                spec=Cron("0 * * * *", "UTC"),
                caller=OPERATOR,
                now=clock.now(),
            )
            for _ in range(3)
        ]
        clock.move(hours=2, minutes=5)
        ticker = Scheduler(svc.ctx)

        async def tick() -> int:
            found = await ticker.tick()
            await ticker.settle()
            return len(found.claimed)

        paused = asyncio.run(tick())
        explained = ticker.explain(made[0].id)
        flags.set(autonomy__paused=0)
        cleared = asyncio.run(tick())
        found = [[f.status for f in fires_of(tmp_path, t.id)] for t in made]

    assert (paused, cleared) == (0, 3)
    assert str(explained["verdict"]).startswith("paused: autonomy.paused is set")
    assert found == [["skipped", "ok"]] * 3


def test_a_live_run_started_while_paused_holds_its_nodes_and_resumes_on_clear(
    tmp_path: Path,
) -> None:
    flags = Flags(autonomy__paused=1)
    clock = Clock(MONDAY)
    with EngineService.open(tmp_path, clock=clock, settings=flags) as svc:
        engine = svc.ctx.engine
        bundle = Bundle.read(CHAIN)
        root = bundle.write(tmp_path / "folder")
        found = checked(root)
        assert not isinstance(found, list)
        ticker = Scheduler(svc.ctx)

        async def go() -> tuple[str, str | None, str]:
            held = await engine.start(root, found[1], mode="live", inputs=None)
            flags.set(autonomy__paused=0)
            tick = await ticker.tick()
            await ticker.settle()
            with Reader.open(tmp_path) as reader:
                ended = reader.events(held.run_id)[-1].data.get("status")
            return held.status, held.reason, f"{len(tick.woken)} {ended}"

        status, reason, after = asyncio.run(go())

    assert (status, reason, after) == ("waiting", "paused", "1 passed")


def test_five_failures_of_one_masked_signature_are_one_incident(tmp_path: Path) -> None:
    with InboxTable.open(tmp_path) as table:
        ids = {
            table.incident(
                "trigger-1",
                signature("script_exit", f"exit 1: feed {n} is down"),
                "trigger-1 failed",
                f"feed {n} is down",
                at=f"2026-10-19T09:0{n}:00+00:00",
            )
            for n in range(5)
        }
        counted = table.open_incident("trigger-1")
        table.resolve_incident("trigger-1", at="2026-10-19T10:00:00+00:00")
        resolved = table.open_incident("trigger-1")

    assert counted is not None
    assert (len(ids), counted.count, counted.first_seen, counted.last_seen) == (
        1,
        5,
        "2026-10-19T09:00:00+00:00",
        "2026-10-19T09:04:00+00:00",
    )
    assert resolved is None


FAILING = """
import json, os
if os.environ["QMX_MODE"] == "live":
    print("[QMX_FAILURE] the feed is down")
else:
    print(json.dumps([1, 2, 3, 4]))
"""


def test_a_failed_fire_delivers_its_failure_and_reruns_at_5_and_15_minutes(
    tmp_path: Path,
) -> None:
    clock = Clock(MONDAY)
    bundle = edited(Bundle.read(CHAIN), "scripts/numbers.py", FAILING)
    with enabled(tmp_path, clock, bundle) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=clock.now(),
        )
        ticker = Scheduler(svc.ctx)

        async def at(minutes: float) -> None:
            clock.current = MONDAY.replace(minute=int(minutes), second=int(minutes % 1 * 60))
            await ticker.tick()
            await ticker.settle()

        async def go() -> None:
            await ticker.run_now(trigger.id)
            await ticker.settle()
            for minutes in (4, 5.5, 14, 15.5):
                await at(minutes)

        asyncio.run(go())
        found = fires_of(tmp_path, trigger.id)
        incident = InboxTable.open(tmp_path).open_incident(trigger.id)
        with Reader.open(tmp_path) as reader:
            (stored,) = rows.triggers(reader.connection, "WHERE id = ?", trigger.id)

    assert [(f.status, f.rerun, f.occurrence_at[11:19]) for f in found] == [
        ("failed", 0, "09:00:00"),
        ("failed", 1, "09:05:00"),
        ("failed", 2, "09:15:00"),
        ("held", 3, "09:30:00"),
    ]
    assert found[0].digest == (f"[QMX_FAILURE] trigger {trigger.id} run_failed: {found[0].detail}")
    assert incident is not None
    assert (incident.count, stored.incident_id) == (3, incident.id)
