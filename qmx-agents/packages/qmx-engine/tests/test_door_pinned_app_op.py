"""The engine door's own `app_op` executor dispatches a pinned ask to the supervisor, which runs it
when the pin is the version that runs and refuses it when the pin moved."""

from __future__ import annotations

import asyncio
import shutil
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from fake_library import fake_door
from qmx_control import ControlService
from qmx_control.models import Document

from qmx_engine.control_door import EngineDoor
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import Failed, JsonObject, NodeJob, Ok
from qmx_engine.service.context import OPERATOR

ROOT = Path(__file__).resolve().parents[4]
JOB = "from pathlib import Path\ndef run():\n    Path('data/job.txt').write_text('1')\n"


def fixture_app(tmp_path: Path) -> Path:
    target = tmp_path / "app"
    shutil.copytree(
        ROOT / "examples/apps/exchange-status",
        target,
        ignore=shutil.ignore_patterns(".venv", "__pycache__"),
    )
    shutil.copyfile(
        ROOT / "qmx-agents/packages/qmx-apps/tests/fixture_server.py", target / "server.py"
    )
    (target / "job.py").write_text(JOB, encoding="utf-8")
    manifest = target / "app.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
        ),
        encoding="utf-8",
    )
    return target


@contextmanager
def door_executor(control: ControlService) -> Generator[AppOp]:
    """The `app_op` executor the engine door composes, with the door open on its own thread."""
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        async with fake_door(control, principal=lambda: OPERATOR) as found:
            opened.append(found)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),))
    thread.start()
    assert ready.wait(30)
    try:
        yield cast(AppOp, opened[0].svc.ctx.engine.executors["app_op"])
    finally:
        stop.set()
        thread.join(30)


def pinned(version: str) -> NodeJob:
    parameters: JsonObject = {
        "app": "exchange-status",
        "job": "job.py",
        "pin": {"pack": "exchange-status", "version": version},
    }
    return NodeJob(
        run_id="r",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={"type": "app_op", "parameters": parameters},
        inputs={},
        now=None,
    )


def test_the_doors_app_op_runs_a_pinned_node_and_refuses_a_moved_pin(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        control.apps_start("exchange-status")
        with door_executor(control) as node:
            right = asyncio.run(node.run(pinned("1.0.0")))
            moved = asyncio.run(node.run(pinned("0.9.0")))
    finally:
        control.close()
    assert isinstance(right, Ok)
    main = cast(Document, right.outputs["main"])
    assert (main["app_id"], main["job"], main["version"]) == ("exchange-status", "job.py", "1.0.0")
    assert isinstance(moved, Failed)
    assert (moved.code, moved.message) == (
        "pin_stale",
        "pinned exchange-status 0.9.0; exchange-status 1.0.0 is what runs",
    )
