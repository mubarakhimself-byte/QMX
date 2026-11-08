"""The control service never holds its lock across a hop onto the engine's loop (C-33): an app
event the supervisor emits and an engine enable that reads settings on the loop, started together,
both finish."""

from __future__ import annotations

import asyncio
import faulthandler
import shutil
import sys
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path

import pytest
from qmx_engine.control_door import EngineDoor
from qmx_engine.service.context import OPERATOR
from qmx_library.adapter import EngineLibraryAdapter

from qmx_control import ControlService
from qmx_control.models import Document

ROOT = Path(__file__).resolve().parents[4]
APP = "exchange-status"
ROUNDS = 500
BOUND_S = 10.0
"""Test bound per round, not a product setting."""


def fixture_app(tmp_path: Path) -> Path:
    target = tmp_path / "app"
    shutil.copytree(
        ROOT / "examples/apps" / APP, target, ignore=shutil.ignore_patterns(".venv", "__pycache__")
    )
    shutil.copyfile(
        ROOT / "qmx-agents/packages/qmx-apps/tests/fixture_server.py", target / "server.py"
    )
    (target / "job.py").write_text("def run():\n    return None\n", encoding="utf-8")
    manifest = target / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
    )
    manifest.write_text(
        text + '\n[suggested_trigger]\nkind = "interval"\nseconds = 60\n', encoding="utf-8"
    )
    return target


@contextmanager
def engine(control: ControlService) -> Generator[EngineDoor]:
    """The engine door on its own loop thread, as `qmx_host` opens it."""
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        library = EngineLibraryAdapter(control.library.store)
        async with EngineDoor.open(control, library=library, principal=lambda: OPERATOR) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),), daemon=True)
    thread.start()
    assert ready.wait(60)
    try:
        yield opened[0]
    finally:
        stop.set()
        thread.join(BOUND_S)


def together(first: Callable[[], object], second: Callable[[], object]) -> bool:
    """Start both on their own threads at once; True when both end inside the bound."""
    gate = threading.Barrier(2)

    def go(work: Callable[[], object]) -> threading.Thread:
        def target() -> None:
            gate.wait()
            work()

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        return thread

    threads = [go(first), go(second)]
    for thread in threads:
        thread.join(BOUND_S)
    return not any(thread.is_alive() for thread in threads)


def test_an_app_event_and_an_engine_enable_never_wait_on_each_other(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    control.apps_create(str(fixture_app(tmp_path)), trust="first_party")
    with engine(control):
        trigger = control.apps_enable(APP)["trigger"]
        assert isinstance(trigger, dict)
        trigger_id = str(trigger["id"])
        supervisor = control.app_runtime()
        event: Document = {"app_id": APP, "status": "running"}
        for round_number in range(ROUNDS):
            finished = together(
                lambda: supervisor.emit(APP, event),
                lambda: control.workflow_triggers_enable(trigger_id),
            )
            if not finished:
                faulthandler.dump_traceback(sys.stderr, all_threads=True)
                pytest.fail(f"round {round_number} deadlocked; stacks on stderr")
        totals = control.aggregates_get()
        triggers = control.workflow_triggers_list(f"{APP}-schedule")
    control.close()
    assert [(t["id"], t["enabled"]) for t in triggers] == [(trigger_id, True)]
    assert totals["active_jobs"] == 0
