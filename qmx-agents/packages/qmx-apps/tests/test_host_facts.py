"""AD-33 change 5: the host writes its facts into every app volume, before the app starts and on
every Settings change.

The fixture app is a real subprocess under the host's own supervisor (`ControlService`'s), with
the host's composer attached and its Settings watcher running, so a holdout turned on through
`settings_put` reaches the running app's copy the way it does in a served host.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import threading
import time
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import psutil
import pytest
from qma.harness import QmxHome, control_service
from qmx_control.service import ControlService
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    host_facts,
    keep_facts,
    market_door,
    placement_name,
)

from qmx_apps.errors import AppError
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "facts-reader"
REWRITE_BOUND_S = 10.0
"""Test bound: how long a test waits for the watcher's rewrite before it fails."""

SERVER = """
import os
from pathlib import Path

from fastmcp import FastMCP

FACTS = Path(os.environ["QMX_VOLUME"]) / "road/host/facts.json"
AT_IMPORT = FACTS.read_text(encoding="utf-8") if FACTS.exists() else None

mcp = FastMCP("host facts fixture")


@mcp.tool()
def at_import() -> dict:
    return {"text": AT_IMPORT}


@mcp.tool()
def facts() -> dict:
    return {"text": FACTS.read_text(encoding="utf-8")}


@mcp.tool()
def write(path: str) -> dict:
    Path(path).write_text("forged", encoding="utf-8")
    return {"written": True}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
"""

STARTED = {
    "schema_version": "qmx.host.facts/1",
    "placement": "pc",
    "role": "pc",
    "trading_profile": False,
    "chats": True,
    "agent_steps": True,
    "holdout": {"on": False},
}


def source(root: Path) -> Path:
    target = root / "source"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (target / "server.py").write_text(SERVER, encoding="utf-8")
    manifest = target / "app.toml"
    manifest.write_text(
        manifest.read_text().replace('id = "exchange-status"', f'id = "{APP}"'), encoding="utf-8"
    )
    return target


def attach(control: ControlService, home: Path) -> Supervisor:
    """The host's own wiring of its facts, as `serve` does it for This PC."""
    door = market_door(home, control, "pc")
    name = placement_name(control, "pc")
    runtime = control.app_runtime()
    runtime.attach_facts(lambda: host_facts(control, "pc", name, door))
    return runtime


async def watch(control: ControlService) -> asyncio.Task[None]:
    return asyncio.get_running_loop().create_task(keep_facts(control))


async def settled(task: asyncio.Task[None]) -> None:
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@pytest.fixture(scope="module")
def host(tmp_path_factory: pytest.TempPathFactory) -> Generator[tuple[ControlService, Supervisor]]:
    root = tmp_path_factory.mktemp("host-facts")
    home = root / "home"
    control = control_service(QmxHome(home))
    runtime = attach(control, home)
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    watching = asyncio.run_coroutine_threadsafe(watch(control), loop).result(timeout=10)
    try:
        runtime.install(source(root), trust="first_party")
        runtime.start(APP)
        yield control, runtime
    finally:
        asyncio.run_coroutine_threadsafe(settled(watching), loop).result(timeout=10)
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=10)
        control.close()


def facts_file(runtime: Supervisor) -> Path:
    return Volume(runtime.home, APP).root / "road/host/facts.json"


def read(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def tool(runtime: Supervisor, name: str, **arguments: str) -> dict[str, Any]:
    return cast(dict[str, Any], runtime.call(APP, name, dict(arguments))["result"])


def rewritten(path: Path, holdout: dict[str, Any]) -> dict[str, Any]:
    deadline = time.monotonic() + REWRITE_BOUND_S
    while time.monotonic() < deadline:
        try:
            found = read(path)
        except OSError, ValueError:
            found = {}
        if found.get("holdout") == holdout:
            return found
        time.sleep(0.05)
    raise AssertionError(f"facts not rewritten to {holdout} within {REWRITE_BOUND_S}s")


def test_the_facts_are_in_the_volume_before_the_app_process_exists(
    host: tuple[ControlService, Supervisor],
) -> None:
    _, runtime = host
    seen = tool(runtime, "at_import")["text"]
    assert seen is not None
    facts = json.loads(seen)
    at = facts.pop("at")
    assert facts == STARTED
    pid = cast(int, runtime.status(APP)["pid"])
    assert datetime.fromisoformat(at).timestamp() < psutil.Process(pid).create_time()


def test_a_settings_change_to_the_holdout_rewrites_the_running_apps_copy(
    host: tuple[ControlService, Supervisor],
) -> None:
    control, runtime = host
    path = facts_file(runtime)
    control.settings_put("data", {"holdout": True, "holdout_boundary": "2025-01"})
    sealed = rewritten(path, {"on": True, "boundary": "2025-01", "months": 12})
    assert json.loads(tool(runtime, "facts")["text"]) == sealed
    assert {key: value for key, value in sealed.items() if key not in {"at", "holdout"}} == {
        key: value for key, value in STARTED.items() if key != "holdout"
    }
    control.settings_put("data", {"holdout": False})
    opened = rewritten(path, {"on": False})
    assert json.loads(tool(runtime, "facts")["text"]) == opened


def test_the_apps_own_write_under_road_is_refused(
    host: tuple[ControlService, Supervisor],
) -> None:
    _, runtime = host
    path = facts_file(runtime)
    before = path.read_text(encoding="utf-8")
    with pytest.raises(AppError, match="owned by the host"):
        runtime.call(APP, "write", {"path": str(path)})
    with pytest.raises(AppError, match="owned by the host"):
        runtime.call(APP, "write", {"path": str(path.with_name("planted.json"))})
    assert path.read_text(encoding="utf-8") == before
    assert not path.with_name("planted.json").exists()


@pytest.mark.parametrize(("role", "expected"), [("pc", False), ("node", True)])
def test_this_pc_never_reports_the_trading_profile_on(
    tmp_path: Path, role: str, expected: bool
) -> None:
    home = tmp_path / "home"
    control = control_service(QmxHome(home))
    try:
        control.settings_put(cast(Any, "host"), {"trading_profile": True})
        door = market_door(home, control, "pc")
        facts = host_facts(control, cast(Any, role), "pc", door)
        assert facts["trading_profile"] is expected
    finally:
        control.close()
