"""An ask is pinned and carries a profile (AD-64): the node hands both to the pinned dispatcher,
and the supervisor revalidates the pin before the app runs."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import cast

from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_control import ControlService
from qmx_control.models import Document

from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import Failed, JsonObject, NodeJob, Ok

ROOT = Path(__file__).resolve().parents[4]
JOB = "from pathlib import Path\ndef run():\n    Path('data/job.txt').write_text('1')\n"


def job(app: str, name: str, **parameters: object) -> NodeJob:
    given: JsonObject = {"app": app, "job": name}
    given.update({key: cast("JsonValue", value) for key, value in parameters.items()})
    definition: JsonObject = {"type": "app_op", "parameters": given}
    return NodeJob(
        run_id="r",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition=definition,
        inputs={},
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
    (target / "job.py").write_text(JOB, encoding="utf-8")
    manifest = target / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
    )
    manifest.write_text(
        text + '\n[suggested_trigger]\nkind = "interval"\nseconds = 60\n', encoding="utf-8"
    )
    return target


def test_a_pinned_node_hands_its_pin_and_profile_to_the_dispatcher() -> None:
    calls: list[tuple[str, str, object, object]] = []

    def run_job(app: str, name: str) -> Document:
        calls.append((app, name, None, None))
        return {"job": name}

    def dispatch(app: str, name: str, *, pin: object, profile: object) -> Document:
        calls.append((app, name, pin, profile))
        return {"job": name, "version": "1.0.0"}

    node = AppOp(run_job, dispatch)
    plain = asyncio.run(node.run(job("macro-daily-bias", "daily.py")))
    pinned = asyncio.run(
        node.run(
            job(
                "macro-daily-bias",
                "daily.py",
                pin={"pack": "macro-daily-bias", "version": "1.0.0"},
                profile="research",
            )
        )
    )
    assert isinstance(plain, Ok) and isinstance(pinned, Ok)
    assert calls == [
        ("macro-daily-bias", "daily.py", None, None),
        (
            "macro-daily-bias",
            "daily.py",
            {"pack": "macro-daily-bias", "version": "1.0.0"},
            "research",
        ),
    ]

    unsupported = asyncio.run(
        AppOp(run_job).run(
            job("macro-daily-bias", "daily.py", pin={"pack": "macro-daily-bias", "version": "1.0"})
        )
    )
    assert isinstance(unsupported, Failed)
    assert unsupported.code == "pin_unsupported"
    malformed = asyncio.run(
        AppOp(run_job, dispatch).run(job("macro-daily-bias", "daily.py", pin={"pack": 7}))
    )
    assert isinstance(malformed, Failed)
    assert (malformed.code, malformed.message) == (
        "app_op_refused",
        "parameters.pin.pack is a string",
    )


def test_a_pin_that_moved_under_a_queued_ask_is_refused_before_the_app_runs(
    tmp_path: Path,
) -> None:
    control = ControlService(tmp_path / "home")
    node = AppOp(control.app_job, dispatch=control.app_runtime().run_job)
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        control.apps_start("exchange-status")
        right = asyncio.run(
            node.run(
                job(
                    "exchange-status",
                    "job.py",
                    pin={"pack": "exchange-status", "version": "1.0.0"},
                )
            )
        )
        moved = asyncio.run(
            node.run(
                job(
                    "exchange-status",
                    "job.py",
                    pin={"pack": "exchange-status", "version": "0.9.0"},
                )
            )
        )
        elsewhere = asyncio.run(node.run(job("exchange-status", "job.py", profile="research")))
    finally:
        control.close()
    assert isinstance(right, Ok)
    assert cast(Document, right.outputs["main"])["version"] == "1.0.0"
    assert isinstance(moved, Failed)
    assert (moved.code, moved.message) == (
        "pin_stale",
        "pinned exchange-status 0.9.0; exchange-status 1.0.0 is what runs",
    )
    assert isinstance(elsewhere, Failed)
    assert elsewhere.code == "undeclared_profile"


def test_a_ring_past_the_host_setting_never_reaches_the_app(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    try:
        control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
        control.apps_start("exchange-status")
        supervisor = control.app_runtime()
        supervisor.call_depth = 1
        answered = supervisor.call("exchange-status", "ping", {}, depth=1)
        refused = None
        try:
            supervisor.call("exchange-status", "ping", {}, depth=2)
        except Exception as error:
            refused = error
    finally:
        control.close()
    assert answered["result"] == {"pong": True}
    assert isinstance(refused, AppError)
    assert refused.code == "call_depth_exceeded"
