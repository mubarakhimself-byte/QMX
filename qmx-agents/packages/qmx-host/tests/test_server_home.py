"""The host's store follows the flip and the primary, its doctor names the store's health, and its
door admits another host of the home on the routes that check their own key (WU9)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient
from qmx_control.primary import Flip
from qmx_control.server import BearerGate
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal

from qmx_host.door import PrincipalDoor
from qmx_host.host import HomeHub, library_line, open_store

OPERATOR = Principal("operator")
LOCAL = "local-bearer"


def note(item: str) -> Draft:
    return Draft("note", item, title=item)


def test_a_save_during_a_held_flip_is_refused(tmp_path: Path) -> None:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as store:
        store.put(OPERATOR, note("before"), on="main", expected_head=None)
        store.flip = Flip(store, cast("Any", None), tmp_path, "http://100.64.0.9:8766")
        store.flip.announce()
        store.flip.quiesce()
        with pytest.raises(LibraryRefused) as refused:
            store.put(OPERATOR, note("during"), on="main", expected_head=None)
        assert refused.value.code == "primary_moving"
        assert store.head("before", "main") is not None


def test_the_server_refuses_main_while_the_pc_is_primary(tmp_path: Path) -> None:
    with open_store(tmp_path, tmp_path / "library", serving=True, floor=0) as store:
        with pytest.raises(LibraryRefused) as refused:
            store.put(OPERATOR, note("on-main"), on="main", expected_head=None)
        landed = store.put(
            Principal("run", "r1"), note("on-run"), on="refs/runs/r1", expected_head=None
        )
        hub = HomeHub(store, home=tmp_path)
        hub.refuse_owned("main")
        with pytest.raises(LibraryRefused):
            hub.refuse_owned("refs/hub/health")
        assert (refused.value.code, landed.ref) == ("ref_not_owned", "refs/runs/r1")
        assert hub.health()["primary"] == "pc"


def test_the_doctor_row_names_the_store_health(tmp_path: Path) -> None:
    with open_store(tmp_path, tmp_path / "library", serving=True, floor=0) as store:
        line = library_line(store)
    assert (line.name, line.ok, line.detail) == (
        "library",
        True,
        "store server (writer) is open; alarms: none",
    )


def door_app() -> TestClient:
    router = APIRouter()

    @router.get("/healthz")
    def healthz(request: Request) -> dict[str, str]:
        return {"seen": request.headers["authorization"]}

    @router.post("/api/engine/forward")
    def forward() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/api/other")
    def other() -> dict[str, bool]:
        return {"ok": True}

    _ = healthz, forward, other
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(BearerGate, token=LOCAL)
    library_routes = [route for route in router.routes if getattr(route, "path", "") == "/healthz"]
    app.add_middleware(
        PrincipalDoor,
        chat_routes=[],
        bearer=LOCAL,
        library_key="pairing-key",
        library_routes=library_routes,
    )
    return TestClient(app)


def test_the_door_admits_the_pairing_key_only_on_the_library_routes() -> None:
    client = door_app()
    pairing = {"Authorization": "Bearer pairing-key"}
    assert client.get("/healthz", headers=pairing).json() == {"seen": f"Bearer {LOCAL}"}
    assert client.get("/api/other", headers=pairing).status_code == 401
    assert client.get("/healthz", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_the_door_admits_a_host_pass_on_the_forward_route() -> None:
    client = door_app()
    assert client.post("/api/engine/forward", headers={"X-QMX-Host-Pass": "p"}).json() == {
        "ok": True
    }
    assert client.post("/api/engine/forward").status_code == 401
