"""A trigger stores the inputs each run it fires starts from. They are set at create, replaced by
`PUT /api/triggers/{trigger_id}/inputs`, and checked against the pinned version's inputs schema;
a trigger whose fire brings no data must hold every required input before it is created, edited
or enabled, and a fire whose stored inputs fail settles `blocked_config` naming the field. The
column arrives by an additive ledger step that the release before this one still opens."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from qmx_home import resolve
from qmx_home.stores import STORES, Version
from qmx_home.versions import open_sqlite
from scheduled import Clock, enabled, fires_of
from test_run_inputs import BEARER, FOLDER_SCHEMA, SOURCE_SCHEMA, published, served, workflow

from qmx_engine.ledger.migrations import STEPS, TRIGGER_COLUMNS
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.library import Bundle, JsonObject
from qmx_engine.service.context import OPERATOR
from qmx_engine.templates.install import add_disabled_trigger
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)


def created(rest: TestClient, item: str, trigger: dict[str, Any]) -> Any:
    return rest.post("/api/triggers", params={"workflow_id": item}, json=trigger, headers=BEARER)


def fired_inputs(rest: TestClient, home: Path, trigger_id: str) -> JsonObject:
    """Fire the trigger now, wait for the fire to end, and read what its run started from."""
    fire_id = rest.post(f"/api/triggers/{trigger_id}/run-now", headers=BEARER).json()["fire_id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        with Reader.open(home) as reader:
            (fire,) = [f for f in rows.fires(reader.connection, trigger_id) if f.id == fire_id]
            events = [] if fire.run_id is None else reader.events(fire.run_id)
        found = [e.data["inputs"] for e in events if e.kind == "run_input"]
        if fire.status in rows.ENDINGS and found and isinstance(found[0], dict):
            return found[0]
        time.sleep(0.05)
    raise AssertionError(f"fire {fire_id} started no run")


def test_a_trigger_passes_its_stored_inputs_and_an_edit_changes_its_next_fire(
    tmp_path: Path,
) -> None:
    with served(tmp_path) as (rest, _):
        published(rest, "chain", FOLDER_SCHEMA)
        made = created(rest, "chain", {"kind": "manual", "inputs": {"folder": "D:/first"}}).json()
        rest.post(f"/api/triggers/{made['id']}/enable", headers=BEARER)
        first = fired_inputs(rest, tmp_path, made["id"])
        edited = rest.put(
            f"/api/triggers/{made['id']}/inputs", json={"folder": "D:/second"}, headers=BEARER
        )
        second = fired_inputs(rest, tmp_path, made["id"])

    assert made["inputs"] == {"folder": "D:/first"}
    assert edited.json()["inputs"] == {"folder": "D:/second"}
    assert (first["folder"], second["folder"]) == ("D:/first", "D:/second")
    block = cast(dict[str, Any], first["trigger"])
    assert (block["id"], block["kind"]) == (made["id"], "manual")


def test_a_webhook_fire_reads_the_stored_folder_and_keeps_its_body_at_webhook_body(
    tmp_path: Path,
) -> None:
    with served(tmp_path) as (rest, door):
        published(rest, "chain", FOLDER_SCHEMA)
        made = created(rest, "chain", {"kind": "webhook", "inputs": {"folder": "D:/stored"}})
        trigger_id = made.json()["id"]
        rest.post(f"/api/triggers/{trigger_id}/enable", headers=BEARER)
        fired = door.workflow_triggers_deliver(trigger_id, "delivery-1", {"folder": "D:/sent"})
        with Reader.open(tmp_path) as reader:
            (inputs,) = [
                e.data["inputs"]
                for e in reader.events(str(fired["run_id"]))
                if e.kind == "run_input"
            ]

    assert isinstance(inputs, dict)
    assert inputs["folder"] == "D:/stored"
    assert inputs["webhook"] == {"delivery_id": "delivery-1", "body": {"folder": "D:/sent"}}


def test_a_trigger_whose_fire_brings_no_data_must_hold_every_required_input(
    tmp_path: Path,
) -> None:
    cron = {"kind": "cron", "expr": "0 2 * * *"}
    missing = "the input 'source' is missing, and the workflow needs it. Set it, then try again."
    with served(tmp_path) as (rest, door):
        published(rest, "download", SOURCE_SCHEMA)
        refused = created(rest, "download", cron)
        kept = created(rest, "download", cron | {"inputs": {"source": {"symbol": "BTCUSDT"}}})
        emptied = rest.put(f"/api/triggers/{kept.json()['id']}/inputs", json={}, headers=BEARER)
        webhook = created(rest, "download", {"kind": "webhook"})
        version = kept.json()["pinned_object"]
        add_disabled_trigger(door.svc, "download", version, Cron("0 2 * * *", "UTC"), OPERATOR)
        (installed,) = [
            t
            for t in rest.get("/api/triggers", headers=BEARER).json()
            if t["inputs"] == {} and t["kind"] == "cron"
        ]
        enabling = rest.post(f"/api/triggers/{installed['id']}/enable", headers=BEARER)

    assert (refused.status_code, refused.json()["error"]["message"]) == (
        422,
        f"inputs_invalid: {missing}",
    )
    assert kept.json()["inputs"] == {"source": {"symbol": "BTCUSDT"}}
    assert (emptied.status_code, emptied.json()["error"]["message"]) == (
        422,
        f"inputs_invalid: {missing}",
    )
    assert (webhook.status_code, webhook.json()["inputs"]) == (200, {})
    assert (enabling.status_code, enabling.json()["error"]["message"]) == (
        422,
        f"inputs_invalid: trigger {installed['id']} cannot be enabled: {missing}",
    )


def test_stored_inputs_the_running_version_rejects_block_the_fire_by_name(
    tmp_path: Path,
) -> None:
    clock = Clock(T0)
    chain = workflow("chain", FOLDER_SCHEMA)
    bundle = Bundle(chain["definition"], {r: t.encode() for r, t in chain["files"].items()})
    with enabled(tmp_path, clock, bundle) as (svc, version):
        trigger = rows.Trigger(
            id="trigger-stale",
            workflow_item="chain",
            pinned_object=version,
            spec=rows.Manual(),
            created_by=OPERATOR.principal,
            created_at="2026-10-27T09:00:00.000000+00:00",
            inputs={"folder": 5},
        )
        svc.ctx.engine.ledger.write(rows.insert(trigger))
        rows.fire_now(svc.ctx.engine.ledger, trigger.id, T0, {})
        ticker = Scheduler(svc.ctx, claimant="a")

        async def tick() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(tick())
        with Reader.open(tmp_path) as reader:
            (stored,) = rows.triggers(reader.connection, "WHERE id = ?", trigger.id)
        fire = fires_of(tmp_path, trigger.id)[0]

    assert (fire.status, fire.run_id) == ("blocked_config", None)
    assert fire.digest == (
        "[QMX_FAILURE] trigger trigger-stale inputs_invalid: the input 'folder' is not valid: 5"
        " is not of type 'string'. Give it a value the workflow's inputs accept."
    )
    assert (stored.last_status, stored.failure_streak) == ("blocked_config", 1)


def version_4_ledger(home: Path) -> Path:
    path = home / "engine" / "engine.sqlite"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as old:
        for statement in (*STEPS[0], *STEPS[1], *STEPS[2], *STEPS[3]):
            old.execute(statement)
        old.execute("INSERT INTO meta VALUES ('schema_version', '4')")
        old.execute(
            f"INSERT INTO triggers ({TRIGGER_COLUMNS}) VALUES"  # noqa: S608
            " ('trigger-old', 'wf', 'obj', 0, 'pc', 'cron',"
            ' \'{"expr": "0 * * * *", "zone": "UTC"}\', 1, NULL, \'{}\', NULL, \'digest\', 0,'
            " 'merged', 1, 'ticker', 'operator', '2026-10-01T00:00:00.000000+00:00', NULL, 'ok',"
            " 2, NULL, NULL, NULL, 5, '07:30')"
        )
    return path


def test_step_5_upgrades_a_version_4_ledger_and_keeps_every_trigger(tmp_path: Path) -> None:
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    version_4_ledger(home)

    with Ledger.open(home) as ledger:
        applied = ledger.applied
    with Reader.open(home) as reader:
        (kept,) = rows.triggers(reader.connection)
        schema = reader.stats().schema_version
    (copy,) = (home.parent / "backups").glob("pre-engine-4-5-*")

    assert (applied, schema) == ([5], 5)
    assert (copy / "data" / "engine" / "engine.sqlite").is_file()
    assert (kept.id, kept.kind, kept.failure_streak, kept.priority, kept.ready_by) == (
        "trigger-old",
        "cron",
        2,
        5,
        "07:30",
    )
    assert kept.inputs == {}


def test_the_parent_release_opens_a_version_5_ledger_and_writes_triggers_without_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    with Ledger.open(home) as ledger:
        made = rows.create(
            ledger,
            workflow_item="wf",
            pinned_object="obj",
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
            inputs={"folder": "D:/clips"},
        )
    monkeypatch.setitem(STORES, "engine", replace(STORES["engine"], release=Version(4, 3)))

    with closing(sqlite3.connect(home / "engine" / "engine.sqlite", isolation_level=None)) as db:
        opened = open_sqlite(db, "engine", STEPS[:4])
        db.execute(
            f"INSERT INTO triggers ({TRIGGER_COLUMNS}) SELECT 'trigger-parent', workflow_item,"  # noqa: S608
            " pinned_object, follow_champion, home_engine, kind, spec, enabled, precheck_ref,"
            " role_pins, effort_pin, delivery, continuity, catch_up, max_concurrent, source,"
            " created_by, created_at, next_fire_at, last_status, failure_streak,"
            " quota_hold_until, incident_id, last_outputs, priority, ready_by FROM triggers"
        )
        read = dict(db.execute("SELECT id, inputs FROM triggers").fetchall())

    assert (opened.found, opened.applied, opened.newer) == (Version(5, 3), (), True)
    assert {trigger_id: json.loads(inputs) for trigger_id, inputs in read.items()} == {
        made.id: {"folder": "D:/clips"},
        "trigger-parent": {},
    }
