"""The observer's door (AD-69, HARNESS-REQUESTS H61).

An observer token reaches the ops rows, the doctor, the data health read and one note; a
`broker_read` row and a Library content row are refused, and the local bearer still passes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from qmx_control.models import Document
from qmx_control.service import Observers, adopt_observers
from qmx_engine.control_door import PRINCIPAL

from qmx_host.door import PrincipalDoor

LOCAL = "local-token"
"""The host's gate token for this test; the door restamps an observer's call with it."""
RUN = "run-7"


def observer_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/ops/spans/{run_id}")
    def trace(run_id: str, request: Request) -> Document:
        return {
            "run_id": run_id,
            "authorization": request.headers.get("authorization", ""),
            "observer": request.query_params.get("observer", ""),
            "principal": PRINCIPAL.get().principal,
        }

    @app.get("/api/doctor")
    def doctor() -> Document:
        return {"lines": []}

    @app.get("/api/portfolio/proposals")
    def proposals() -> Document:
        return {"proposals": []}

    @app.get("/api/library")
    def library() -> Document:
        return {"items": []}

    _ = trace, doctor, proposals, library
    app.add_middleware(PrincipalDoor, chat_routes=[], bearer=LOCAL)
    return app


def test_an_observer_reads_the_ops_rows_and_the_doctor_and_is_refused_the_rest(
    tmp_path: Path,
) -> None:
    made = Observers(tmp_path).create("outside")
    adopt_observers(tmp_path)
    observer = {"Authorization": f"Bearer {made['token']}"}
    try:
        with TestClient(observer_app()) as rest:
            seen = rest.get(f"/api/ops/spans/{RUN}", headers=observer)
            doctor = rest.get("/api/doctor", headers=observer)
            broker = rest.get("/api/portfolio/proposals", headers=observer)
            library = rest.get("/api/library", headers=observer)
            local = rest.get("/api/library", headers={"Authorization": f"Bearer {LOCAL}"})
    finally:
        adopt_observers(None)

    assert seen.status_code == 200
    assert seen.json() == {
        "run_id": RUN,
        "authorization": f"Bearer {LOCAL}",
        "observer": made["id"],
        "principal": f"agent:observer:{made['id']}",
    }
    assert (doctor.status_code, doctor.json()) == (200, {"lines": []})
    assert (broker.status_code, broker.json()["error"]["code"]) == (403, "observer_refused")
    assert (library.status_code, library.json()["error"]["code"]) == (403, "observer_refused")
    assert local.status_code == 200
