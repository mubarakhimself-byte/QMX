"""A price door that did not open answers every `/api/data/*` call with its reason, behind the same
bearer as an open door, instead of a 404 (loose strings P6, C14)."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter
from fastapi.testclient import TestClient
from qma.harness import QmxHome, control_service
from qmf.core import is_refusal
from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger import redact
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_host.host import closed_market_router, compose, market_door
from qmx_host.market_data import market_router

KEY = "closed-door-check"
BEARER = {"Authorization": f"Bearer {KEY}"}
SHUT = {
    "refused": "invalid input",
    "retryability": "no",
    "context": {
        "field": "world",
        "reason": "[data] world names a world qmf knows",
        "given": "'nowhere'",
    },
    "line": "QMX's market data did not open because [data] world in Settings cannot be used: "
    "[data] world names a world qmf knows. Fix it in Settings and restart QMX.",
}


@contextmanager
def hosted(folder: Path, data: str) -> Generator[TestClient]:
    """The host's app on a throwaway folder with `data` as its `[data]`, mounting the data routes
    `serve` mounts for the door `market_door` gives."""
    home = resolve(folder / "QMX", create=True, drives=[]).home
    (home / "settings.toml").write_text(f"[data]\n{data}", encoding="utf-8")
    control = control_service(QmxHome(home))
    door = market_door(home, control, "pc")
    data_api: APIRouter = closed_market_router(door) if is_refusal(door) else market_router(door)
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def run() -> None:
        with Store.open(home / "library", redactor=redact) as store:
            async with EngineDoor.open(control, library=EngineLibraryAdapter(store)) as engine:
                opened.append(engine)
                ready.set()
                while not stop.is_set():
                    await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(run(),))
    thread.start()
    assert ready.wait(30)
    try:
        with TestClient(compose(control, opened[0], [], KEY, "", [data_api])) as rest:
            yield rest
    finally:
        stop.set()
        thread.join(30)


def test_a_shut_door_answers_its_reason_on_every_data_route_and_needs_the_bearer(
    tmp_path: Path,
) -> None:
    with hosted(tmp_path, 'world = "nowhere"\n') as rest:
        listed = rest.get("/api/data/instruments", headers=BEARER)
        read = rest.post("/api/data/read", json={"series": "x"}, headers=BEARER)
        anonymous = rest.get("/api/data/instruments")

    assert (listed.status_code, listed.json()) == (503, {"detail": SHUT})
    assert (read.status_code, read.json()) == (503, {"detail": SHUT})
    assert anonymous.status_code == 401


def test_an_open_door_answers_as_before(tmp_path: Path) -> None:
    with hosted(tmp_path, "") as rest:
        listed = rest.get("/api/data/instruments", headers=BEARER)

    assert (listed.status_code, listed.json()) == (200, {"instruments": []})
