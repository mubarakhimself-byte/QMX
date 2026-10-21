"""The host's one-instance rule, its door's principal for each kind of caller, and the `user` acts
that every other caller gets back as a card."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from qmx_engine.control_door import PRINCIPAL, EngineDoor, as_run
from qmx_engine.ports.library import Bundle

from qmx_host.door import PrincipalDoor
from qmx_host.host import compose, record, single_instance

KEY = "host-check"
BEARER = {"Authorization": f"Bearer {KEY}"}
CHAIN = Path(__file__).parents[2] / "qmx-engine/tests/fixtures/workflows/script-chain"


def test_a_second_host_on_the_same_home_refuses_with_one_line(tmp_path: Path) -> None:
    with single_instance(tmp_path):
        record(tmp_path, 8766)
        second = subprocess.run(
            [sys.executable, "-m", "qmx_host", "serve", "--home", str(tmp_path), "--port", "1"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    assert second.returncode == 1
    assert second.stderr.splitlines() == [
        f"refused: {tmp_path.resolve()} already has a host, PID {os.getpid()}; stop it first."
    ]


def test_the_lock_is_free_again_once_its_holder_lets_go(tmp_path: Path) -> None:
    with single_instance(tmp_path):
        pass
    with single_instance(tmp_path):
        record(tmp_path, 8766)

    assert not (tmp_path / "control-process.json").exists()


def door_app() -> FastAPI:
    chats = APIRouter()

    @chats.post("/api/sessions/{sid}/turns")
    def turn(sid: str) -> str:
        return PRINCIPAL.get().principal

    @chats.post("/api/chats")
    def new_chat() -> str:
        return PRINCIPAL.get().principal

    app = FastAPI()
    for path in ("/api/workflows/{workflow_id}", "/mcp/"):
        app.add_api_route(path, lambda: PRINCIPAL.get().principal, methods=["PUT", "POST"])
    app.include_router(chats)
    _ = turn, new_chat
    app.add_middleware(PrincipalDoor, chat_routes=chats.routes)
    return app


def test_the_door_names_the_principal_of_each_kind_of_caller() -> None:
    with TestClient(door_app()) as rest:
        seen = {
            "ui bearer": rest.put("/api/workflows/chain").json(),
            "chat turn": rest.post("/api/sessions/chat-7/turns").json(),
            "new chat": rest.post("/api/chats").json(),
            "mcp client": rest.post("/mcp/").json(),
        }
    seen["in-process tool"] = PRINCIPAL.get().principal
    seen["run's work"] = as_run("run-9").run(lambda: PRINCIPAL.get().principal)

    assert seen == {
        "ui bearer": "operator",
        "chat turn": "agent:chat-7",
        "new chat": "operator",
        "mcp client": "agent:mcp",
        "in-process tool": "agent:unnamed",
        "run's work": "run:run-9",
    }


def chain() -> dict[str, Any]:
    bundle = Bundle.read(CHAIN)
    files = {ref: data.decode() for ref, data in bundle.files.items()}
    return {"definition": bundle.definition | {"id": "chain"}, "files": files}


@contextmanager
def hosted(home: Path) -> Generator[tuple[TestClient, EngineDoor]]:
    """The host's app on a throwaway home, with the engine on its own loop thread as in `serve`."""
    from qma.harness import QmxHome, control_service

    control = control_service(QmxHome(home))
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def run() -> None:
        async with EngineDoor.open(control) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(run(),))
    thread.start()
    assert ready.wait(30)
    try:
        with TestClient(compose(control, opened[0], [], KEY, "")) as rest:
            yield rest, opened[0]
    finally:
        stop.set()
        thread.join(30)


def test_an_agent_gets_a_card_for_publish_enable_and_a_live_run_and_the_ui_bearer_acts(
    tmp_path: Path,
) -> None:
    with hosted(tmp_path) as (rest, door):
        rest.put("/api/workflows/chain/draft", json=chain(), headers=BEARER)
        rest.post("/api/workflows/chain/test", headers=BEARER)
        as_agent = door.control.workflows_put("chain", {"semver": "1.0.0"})
        before = rest.get("/api/workflows/chain/versions", headers=BEARER).json()
        published = rest.put("/api/workflows/chain", json={"semver": "1.0.0"}, headers=BEARER)
        made = rest.post(
            "/api/triggers",
            params={"workflow_id": "chain"},
            json={"kind": "manual"},
            headers=BEARER,
        ).json()
        enable_card = door.control.workflow_triggers_enable(made["id"])
        run_card = door.control.workflows_run("chain")

    assert as_agent == {
        "card": "publish",
        "title": "Publish chain",
        "message": "Only you can publish this. Press the button to publish it.",
        "button": {"method": "PUT", "path": "/api/workflows/chain", "body": {"semver": "1.0.0"}},
    }
    assert before == []
    assert (published.json()["semver"], published.json()["state"]) == ("1.0.0", "published")
    assert enable_card["button"] == {
        "method": "POST",
        "path": f"/api/triggers/{made['id']}/enable",
        "body": {},
    }
    assert run_card["button"] == {"method": "POST", "path": "/api/workflows/chain/run", "body": {}}
