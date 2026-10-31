"""QMX's own maintenance, listed apart from his workflows (design 06 section 6): the host's jobs
and the shipped workflows marked `meta.kind = "maintenance"`, each with its own switch; turning
one off stops it and nothing else; and each host job lands a `maintenance-result` artifact that an
event trigger can follow. Every folder is in pytest's tmp folder."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Ledger
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import event, rows
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store
from test_backups_service import Clock, ended, finished, folder, service

from qmx_host.backups import Backups
from qmx_host.maintenance import maintenance_router

T0 = datetime(2026, 10, 29, 9, 0, tzinfo=UTC)


def test_the_list_names_the_host_jobs_and_the_marked_workflows_each_with_its_switch(
    tmp_path: Path,
) -> None:
    layout = folder(tmp_path / "QMX")
    backups = service(layout, Clock())
    backups.control.settings_put("backup", {"upkeep": {"on": False}})
    app = FastAPI()
    app.include_router(maintenance_router(backups, lambda _workflow: []))

    listed = TestClient(app).get("/api/maintenance").json()

    assert [(j["id"], j["on"], j["switch"]) for j in listed["host"]] == [
        ("sync", True, {"section": "backup", "key": "on"}),
        ("upkeep", False, {"section": "backup", "key": "upkeep.on"}),
        ("drill", True, {"section": "backup", "key": "upkeep.drill"}),
    ]
    assert {w["id"] for w in listed["workflows"]} == {"connections-health", "gw-guard-watchdogs"}
    assert all(w["kind"] == "workflow" for w in listed["workflows"])


def test_the_upkeep_switched_off_never_runs_while_rounds_and_the_drill_still_do(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    backups.control.settings_put("backup", {"upkeep": {"on": False}})
    first = finished(backups, backups.sweep())
    clock.advance(days=32)
    second = finished(backups, backups.sweep())
    drill = backups.sweep()
    drilled = None if drill is None else ended(backups, drill.id)

    assert (first.kind, first.state, second.kind, second.state) == (
        "backup",
        "finished",
        "backup",
        "finished",
    )
    assert drilled is not None and drilled.kind == "drill"
    assert backups.sweep() is None
    assert backups.jobs.latest("upkeep:quick") is None


def test_a_host_job_lands_one_maintenance_result_that_an_event_trigger_follows(
    tmp_path: Path,
) -> None:
    layout = folder(tmp_path / "QMX")
    engine_home = tmp_path / "engine"
    engine_home.mkdir()
    with (
        Store.open(layout.home / "library", redactor=redact) as store,
        Ledger.open(engine_home) as ledger,
    ):
        backups = Backups(
            layout, service(layout, Clock()).control, clock=Clock(), floor=0, store=store
        )
        library = EngineLibraryAdapter(store)
        rows.create(
            ledger,
            workflow_item="wf-maintenance",
            pinned_object="obj-1",
            spec=rows.Event({"kind": "artifact", "output": "maintenance-result"}),
            caller=OPERATOR,
            now=T0,
        )
        before = event.drain(ledger, library, home=engine_home, engine="pc", now=T0)
        round_job = finished(backups, backups.start(None, asked=True).job)
        after = event.drain(ledger, library, home=engine_home, engine="pc", now=T0)
        results = [
            library.get(e.object_id)
            for e in library.events(0)
            if library.get(e.object_id).fields.get("type") == "maintenance-result"
        ]
        made = [(r.kind, cast("dict[str, Any]", r.fields["metadata"])) for r in results]

    assert round_job.state == "finished"
    assert (before.fired, len(after.fired)) == ((), 1)
    assert [(kind, m["job"], m["state"]) for kind, m in made] == [("artifact", "sync", "finished")]
