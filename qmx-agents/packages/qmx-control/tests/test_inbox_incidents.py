"""The UI gaps folded into the sync program (design 06 section 12): the inbox lists every open
incident, the run read says where the run ran, and health names a store opened read-only before
any write is refused. Every folder is in pytest's tmp folder; no host is started."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient
from qmx_engine.ledger import redact
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ports.library import RunSummary
from qmx_home import Label, resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_control.server import create_app
from qmx_control.service import ControlService, WorkflowEngine

PLACED = {"place": "myserver", "place_id": "01JSERVER", "machine": "vm-1", "placed_by": "row"}


class Engine:
    """The two engine reads these routes call."""

    def workflow_inbox_list(self) -> list[dict[str, Any]]:
        return [{"kind": "item", "id": "item-1"}]

    def workflow_runs_get(self, run_id: str) -> dict[str, Any]:
        return {"run_id": run_id, "status": "passed"}


def test_the_inbox_lists_every_open_incident_and_none_resolved(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    with InboxTable.open(layout.home) as inbox:
        inbox.incident(
            "backup:usb", "refused", "Backups: usb", "E:\\ is full", at="2026-10-29T09:00:00+00:00"
        )
        inbox.incident("backup-drill:pc", "drill-failed", "Drill", "x", at="2026-10-29T08:00:00Z")
        inbox.resolve_incident("backup-drill:pc", at="2026-10-29T09:30:00+00:00")
    service = ControlService(layout.home, secret_getter=lambda _s, _n: None)
    service.attach_workflow_engine(cast(WorkflowEngine, Engine()))

    listed = service.workflow_inbox_list()

    assert [(i["kind"], i.get("trigger_id"), i.get("cause")) for i in listed] == [
        ("incident", "backup:usb", "E:\\ is full"),
        ("item", None, None),
    ]


def test_the_run_read_carries_where_the_run_ran(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    with Store.open(layout.home / "library", redactor=redact) as store:
        EngineLibraryAdapter(store).put_run_summary(
            RunSummary(
                run_id="run-1",
                workflow_item="wf-1",
                object_id="obj-1",
                mode="live",
                status="passed",
                reason=None,
                totals={},
                placement=PLACED,
                trace_artifact_hash=None,
                started_by="operator",
                fake=True,
            ),
            principal="run:run-1",
        )
        service = ControlService(layout.home, secret_getter=lambda _s, _n: None)
        service.attach_workflow_engine(cast(WorkflowEngine, Engine()))
        service.attach_library(store)

        read = service.workflow_runs_get("run-1")
        unknown = service.workflow_runs_get("run-2")

    assert read == {"run_id": "run-1", "status": "passed", "placement": PLACED}
    assert unknown["placement"] is None


def test_health_names_a_store_opened_read_only_before_any_write(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    label = Label.parse(layout.label.read_text(encoding="utf-8"))
    stores = {**label.stores, "library": {"version": "3", "min_reader": "2"}}
    layout.label.write_text(
        Label(label.home_id, label.format_version, "0.1.0", "0.8.0", stores=stores).dump(),
        encoding="utf-8",
    )
    service = ControlService(layout.home, secret_getter=lambda _s, _n: None)

    with TestClient(create_app(service, "health-check")) as rest:
        health = rest.get("/api/health", headers={"Authorization": "Bearer health-check"}).json()

    assert [entry["store"] for entry in health["read_only"]] == ["library"]
    assert health["read_only"][0]["line"].endswith("The Library opens read-only until then.")
