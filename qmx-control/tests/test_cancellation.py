from __future__ import annotations

import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qmx_control import ControlService, create_app
from qmx_control.service import WorkKind


@pytest.mark.parametrize("kind", ["runs", "jobs"])
def test_cancel_reaches_the_running_owner(tmp_path: Path, kind: WorkKind) -> None:
    service = ControlService(tmp_path)
    cancel = threading.Event()
    service.record_work(kind, "work-1", {"status": "running"}, cancel=cancel.set)

    def run() -> None:
        if cancel.wait(timeout=10):
            service.record_work(kind, "work-1", {"status": "cancelled"})

    worker = threading.Thread(target=run)
    worker.start()
    try:
        with TestClient(create_app(service, "test")) as client:
            response = client.post(
                f"/api/{kind}/work-1/cancel", headers={"Authorization": "Bearer test"}
            )
            assert response.status_code == 200
            assert response.json()["status"] == "cancel_requested"
        worker.join(timeout=10)
        assert not worker.is_alive()
        rows = service.runs_list() if kind == "runs" else service.jobs_list()
        assert len(rows) == 1
        assert rows[0]["id"] == "work-1"
        assert rows[0]["status"] == "cancelled"
        event_data = service.events(kind)[-1]["data"]
        assert isinstance(event_data, dict)
        assert event_data["status"] in {"cancel_requested", "cancelled"}
    finally:
        cancel.set()
        worker.join(timeout=10)
