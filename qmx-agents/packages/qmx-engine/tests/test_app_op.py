"""An app's schedule is an engine trigger on an `app_op` workflow (AD-57): his enable creates the
trigger, and the `app_op` node runs the job in the app's supervised process."""

from __future__ import annotations

import asyncio
import shutil
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from fake_library import fake_door
from qmx_control import ControlService

from qmx_engine.control_door import EngineDoor
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.service.context import OPERATOR

ROOT = Path(__file__).resolve().parents[4]
JOB = (
    "from pathlib import Path\n"
    "def run():\n"
    "    path = Path('data/job.txt')\n"
    "    path.write_text(str(int(path.read_text()) + 1) if path.exists() else '1')\n"
)


def fixture_app(tmp_path: Path) -> Path:
    """The exchange-status example with the supervisor test server, one job and a 60 s
    suggested trigger."""
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
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
    )
    manifest.write_text(
        text + '\n[suggested_trigger]\nkind = "interval"\nseconds = 60\n', encoding="utf-8"
    )
    return target


@contextmanager
def door(control: ControlService) -> Generator[EngineDoor]:
    """The engine door on its own loop thread, as in the host, acting as the operator."""
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
        yield opened[0]
    finally:
        stop.set()
        thread.join(30)


def job(app: str, name: str) -> NodeJob:
    return NodeJob(
        run_id="r",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={"type": "app_op", "parameters": {"app": app, "job": name}},
        inputs={},
        now=None,
    )


def test_app_op_runs_and_operation_types_stay_off() -> None:
    app_op = REGISTRY.kind("app_op")
    operation = REGISTRY.kind("qmx.apps_admin_list")
    assert app_op is not None
    assert operation is not None
    assert (app_op.available, operation.available) == (True, False)


def test_enable_creates_one_trigger_whose_test_run_ran_the_job(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        with door(control):
            first = control.apps_enable("exchange-status")
            again = control.apps_enable("exchange-status")
            triggers = control.workflow_triggers_list("exchange-status-schedule")
            runs = control.workflow_runs_list("exchange-status-schedule")
        trigger = first["trigger"]
        assert isinstance(trigger, dict)
        assert [(t["kind"], t["spec"], t["enabled"]) for t in triggers] == [
            ("interval", {"seconds": 60}, True)
        ]
        assert again["trigger"] == trigger
        assert [run["status"] for run in runs] == ["passed"]
        marker = control.home / "apps/exchange-status/data/job.txt"
        assert marker.read_text() == "1"
    finally:
        control.close()


def test_app_op_calls_the_running_app_and_fails_with_the_supervisor_reason(
    tmp_path: Path,
) -> None:
    control = ControlService(tmp_path / "home")
    node = AppOp(control.app_job)
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        stopped = asyncio.run(node.run(job("exchange-status", "job.py")))
        control.apps_start("exchange-status")
        ran = asyncio.run(node.run(job("exchange-status", "job.py")))
        missing = asyncio.run(node.run(job("exchange-status", "nope.py")))
    finally:
        control.close()
    assert isinstance(stopped, Failed)
    assert (stopped.code, stopped.message) == ("not_running", "The app is stopped.")
    assert isinstance(ran, Ok)
    main = ran.outputs["main"]
    assert isinstance(main, dict)
    assert (main["app_id"], main["job"]) == ("exchange-status", "job.py")
    assert (control.home / "apps/exchange-status/data/job.txt").read_text() == "1"
    assert isinstance(missing, Failed)
    assert missing.code == "job_not_found"
