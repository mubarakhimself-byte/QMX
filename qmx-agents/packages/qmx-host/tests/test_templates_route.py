"""`POST /api/templates/install` installs through the host's own engine into the Library store the
host writes, and refuses an unknown id by name (WU5, RUN1C)."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from qma.harness import QmxHome, control_service
from qmx_engine import __main__ as cli
from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger import redact
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library import LibraryRefused as EngineRefused
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.templates.catalog import PACK
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_host import host
from qmx_host.door import templates_router
from qmx_host.host import compose, store_role

KEY = "templates-check"
BEARER = {"Authorization": f"Bearer {KEY}"}


@contextmanager
def hosted(home: Path) -> Generator[tuple[TestClient, Store]]:
    """The host's app over a real store, with the engine on its own loop thread."""
    control = control_service(QmxHome(home))
    opened: list[tuple[EngineDoor, Store]] = []
    ready, stop = threading.Event(), threading.Event()

    async def run() -> None:
        with Store.open(home / "library", redactor=redact) as store:
            async with EngineDoor.open(control, library=EngineLibraryAdapter(store)) as door:
                opened.append((door, store))
                ready.set()
                while not stop.is_set():
                    await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(run(),))
    thread.start()
    assert ready.wait(30)
    door, store = opened[0]
    try:
        app = compose(control, door, [], KEY, "", [templates_router(door)])
        with TestClient(app) as rest:
            yield rest, store
    finally:
        stop.set()
        thread.join(30)


def test_an_install_through_the_route_lands_in_the_hosts_store(tmp_path: Path) -> None:
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, store):
        answered = rest.post(
            "/api/templates/install", json={"templates": ["backup-weekly"]}, headers=BEARER
        )
        unknown = rest.post(
            "/api/templates/install", json={"templates": ["no-such-template"]}, headers=BEARER
        )
        heads = [item for item, _ in store.heads_on("main")]

    assert answered.status_code == 200
    assert [(row["id"], row["action"]) for row in answered.json()] == [
        ("backup-weekly", "published")
    ]
    assert "backup-weekly" in heads
    assert (unknown.status_code, unknown.json()["detail"]) == (
        404,
        "no template 'no-such-template' in the catalogue",
    )


def test_the_cli_reads_the_record_the_host_writes() -> None:
    assert (cli.HOST_STATE, cli.INSTALL_ROUTE) == (host.STATE, "/api/templates/install")


def draft_on_a_pc(home: Path, primary: str) -> str:
    """One engine draft put into a store opened the way a `pc` host opens it."""
    home.mkdir(parents=True)
    (home / "settings.toml").write_text(f'[library]\nprimary = "{primary}"\n', "utf-8")
    role = store_role(home, serving=False)
    with (
        Store.open(home / "library", redactor=redact, role=role) as store,
        EngineService.open(home, library=EngineLibraryAdapter(store)) as svc,
    ):
        bundle = Bundle.read(PACK / "backup-weekly")
        return svc.drafts.put("backup-weekly", bundle, 0, caller=OPERATOR).item


def test_a_pc_host_writes_while_the_pc_is_primary_and_refuses_after_the_flip(
    tmp_path: Path,
) -> None:
    landed = draft_on_a_pc(tmp_path / "before", "pc")
    with pytest.raises(EngineRefused) as refused:
        draft_on_a_pc(tmp_path / "after", "server")

    assert landed == "backup-weekly"
    assert refused.value.code == "read_only_replica"
