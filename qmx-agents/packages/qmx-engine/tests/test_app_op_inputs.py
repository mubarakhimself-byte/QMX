"""A workflow tells an app's job what to do and reads its answer (Level 0 AD-33 change 1, engine
AD-64), and a job asked by name alone runs exactly as before."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import cast

from pydantic import JsonValue
from qmx_control import ControlService
from qmx_control.models import Document

from qmx_engine.nodes.app_op import AppOp, Placements
from qmx_engine.nodes.base import Failed, JsonObject, NodeJob, Ok

ROOT = Path(__file__).resolve().parents[4]
JOBS = {
    "echo.py": "def run(inputs):\n    return {'seen': inputs}\n",
    "old.py": "from pathlib import Path\ndef run():\n    Path('data/old.txt').write_text('1')\n",
    "opaque.py": "def run(inputs):\n    return object()\n",
}


def job(name: str, ports: JsonValue = None, **parameters: object) -> NodeJob:
    given: JsonObject = {"app": "exchange-status", "job": name}
    given.update({key: cast("JsonValue", value) for key, value in parameters.items()})
    return NodeJob(
        run_id="r1",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={"type": "app_op", "parameters": given},
        inputs={} if ports is None else ports,
        now=None,
    )


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
    for name, body in JOBS.items():
        (target / name).write_text(body, encoding="utf-8")
    manifest = target / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', f'mcp = "server.py"\njobs = {json.dumps(list(JOBS))}'
    )
    manifest.write_text(text, encoding="utf-8")
    return target


def logged(home: Path) -> list[Document]:
    path = home / "apps/exchange-status/logs/supervisor.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    return [entry for entry in map(json.loads, lines) if entry["event"] == "job_completed"]


def test_a_job_gets_its_inputs_and_its_result_comes_back(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    node = AppOp(control.app_job, dispatch=control.app_job)
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        control.apps_start("exchange-status")
        told = asyncio.run(
            node.run(job("echo.py", {"in": {"x": 0, "window": "2024-01"}}, inputs={"x": 1}))
        )
        bare = asyncio.run(node.run(job("echo.py", {"in": {"x": 0}})))
        old = asyncio.run(node.run(job("old.py")))
        opaque = asyncio.run(node.run(job("opaque.py", inputs={})))
        marker = (tmp_path / "home/apps/exchange-status/data/old.txt").read_text()
        completed = logged(tmp_path / "home")
    finally:
        control.close()
    assert isinstance(told, Ok)
    assert cast(Document, told.outputs["main"])["result"] == {"seen": {"x": 1, "window": "2024-01"}}
    assert isinstance(bare, Ok)
    assert cast(Document, bare.outputs["main"])["result"] == {"seen": {}}
    assert isinstance(old, Ok)
    assert sorted(cast(Document, old.outputs["main"])) == [
        "app_id",
        "instance_id",
        "job",
        "profile",
        "version",
    ]
    assert marker == "1"
    assert isinstance(opaque, Failed)
    assert (opaque.code, opaque.message) == ("job_failed", "Job opaque.py raised TypeError.")
    assert [entry.get("principal") for entry in completed] == ["run:r1", None, None, "run:r1"]


def test_a_node_without_inputs_calls_the_two_argument_runner() -> None:
    plain: list[tuple[str, str]] = []
    pinned: list[Document] = []
    remote: list[tuple[object, ...]] = []

    def run_job(app: str, name: str) -> Document:
        plain.append((app, name))
        return {"job": name}

    def dispatch(app: str, name: str, **asked: JsonValue) -> Document:
        pinned.append({"app": app, "job": name, **asked})
        return {"job": name, "result": asked.get("inputs")}

    def ask_home(*sent: object) -> Document:
        remote.append(sent)
        return {"job": "echo.py"}

    node = AppOp(run_job, dispatch)
    asyncio.run(node.run(job("old.py")))
    asked = asyncio.run(node.run(job("echo.py", {"in": {"x": 0}}, inputs={"x": 1})))
    away = Placements(
        state_of=lambda app, op: "instance",
        home_of=lambda app: "pc",
        here="contabo",
        reachable=lambda placement: True,
        remote=ask_home,
    )
    elsewhere = AppOp(run_job, dispatch, placements=away)
    asyncio.run(elsewhere.run(job("old.py")))
    asyncio.run(elsewhere.run(job("echo.py", inputs={"x": 1})))
    refused = asyncio.run(node.run(job("echo.py", {"in": [1]}, inputs={"x": 1})))

    assert plain == [("exchange-status", "old.py")]
    assert pinned == [
        {
            "app": "exchange-status",
            "job": "echo.py",
            "pin": None,
            "profile": None,
            "inputs": {"x": 1},
            "principal": "run:r1",
        }
    ]
    assert isinstance(asked, Ok)
    assert asked.outputs == {"main": {"job": "echo.py", "result": {"x": 1}}}
    assert remote == [
        ("pc", "exchange-status", "old.py", None, None),
        ("pc", "exchange-status", "echo.py", None, None, {"x": 1}),
    ]
    assert isinstance(refused, Failed)
    assert (refused.code, refused.message) == (
        "app_op_refused",
        "the in port carries a table for parameters.inputs to merge over",
    )
