"""The composition (SOLUTION-DESIGN 27.1): one process per home serves the copilot's chats, the
workflow engine and the control doors on one port behind one bearer.

`serve` builds, in order: the home's single-instance lock, `ControlService` (the one settings
reader), the `Harness` (which starts the model relay on its own thread), the engine with its
scheduler, and the control app with the chat, engine and control routes behind the principal
door. The Library writer is `ControlService.library` and the apps supervisor is
`ControlService.app_runtime()`, as they are today. On stop the engine drains, then the harness
closes, which stops the relay.

The lock is an OS lock on `<home>/engine.lock` (AD-3, L-64, L-70): the OS releases it when the
process dies, so a crashed host never blocks the next one, and two hosts cannot both take it.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import IO, Final, Literal

import httpx
import psutil
import qmx_control.server
import uvicorn
from fastapi import APIRouter, FastAPI
from qma.harness import Harness, QmxHome, chat_routes, control_service
from qmx_control.service import ControlService
from qmx_engine.control_door import EngineDoor
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.service.rest import engine_router

from qmx_host.door import PrincipalDoor

type Role = Literal["pc", "node"]

LOCK: Final = "engine.lock"
STATE: Final = "control-process.json"
"""The running host's pid, port and start time, for `status`, `stop` and the refusal line."""
START_S: Final = 30.0


class HostRunning(Exception):
    def __init__(self, home: Path, pid: int | None) -> None:
        who = "an unknown process" if pid is None else f"PID {pid}"
        super().__init__(f"refused: {home} already has a host, {who}; stop it first.")


def _lock(handle: IO[bytes]) -> None:
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def single_instance(home: Path) -> Iterator[None]:
    """Hold the home's lock and its record for as long as the block runs. Raises `HostRunning`
    while another process holds it."""
    handle = (home / LOCK).open("a+b")
    try:
        _lock(handle)
    except OSError:
        handle.close()
        raise HostRunning(home, recorded_host(home)) from None
    me = psutil.Process()
    record = home / STATE
    try:
        yield
    finally:
        if recorded_host(home) == me.pid:
            record.unlink(missing_ok=True)
        handle.close()


def record(home: Path, port: int) -> None:
    me = psutil.Process()
    state = {"pid": me.pid, "port": port, "created": me.create_time()}
    (home / STATE).write_text(json.dumps(state), encoding="utf-8")


def recorded_host(home: Path) -> int | None:
    """The pid of the live host the home's record names, or None."""
    try:
        state = json.loads((home / STATE).read_text(encoding="utf-8"))
        pid, created = state["pid"], state["created"]
    except OSError, ValueError, KeyError, TypeError:
        return None
    if not isinstance(pid, int):
        return None
    try:
        return pid if psutil.Process(pid).create_time() == created else None
    except psutil.Error:
        return None


def serve_forever(
    home: Path,
    *,
    port: int,
    role: Role,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
) -> int:
    try:
        with single_instance(home):
            record(home, port)
            asyncio.run(serve(home, port, role, ui_origin, scrubbed, keep))
    except HostRunning as refused:
        print(refused, file=sys.stderr)
        return 1
    return 0


async def serve(
    home: Path, port: int, role: Role, ui_origin: str, scrubbed: Sequence[str], keep: Sequence[str]
) -> None:
    """Assumes the caller scrubbed the environment and holds the home's lock."""
    qmx_home = QmxHome(home)
    control = control_service(qmx_home)
    harness = await Harness.open(qmx_home, control=control)
    harness.control_port = port
    try:
        async with EngineDoor.open(control, harness=HarnessAdapter(harness)) as engine:
            harness_api = chat_routes(harness, scrubbed=scrubbed, keep=keep)
            origin = ui_origin if role == "pc" else ""
            app = compose(control, engine, harness_api, qmx_control.server.local_token(), origin)
            server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port))
            await server.serve()
    finally:
        await harness.close()


def compose(
    control: ControlService,
    engine: EngineDoor,
    harness_api: Sequence[APIRouter],
    bearer: str,
    ui_origin: str,
) -> FastAPI:
    """The one REST app: control, chat and engine routes behind one bearer and the principal
    door. `ui_origin` is the one origin CORS allows, none when empty."""
    app = qmx_control.server.create_app(
        control, bearer, ui_origin, extra_routers=[*harness_api, engine_router(engine)]
    )
    routes = [route for api in harness_api for route in api.routes]
    app.add_middleware(PrincipalDoor, chat_routes=routes)
    return app


def health(port: int) -> int | None:
    """The pid the host on `port` reports, or None."""
    try:
        response = httpx.get(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Authorization": f"Bearer {qmx_control.server.local_token()}"},
            timeout=2,
        )
    except httpx.HTTPError:
        return None
    pid = response.json().get("pid") if response.status_code == 200 else None
    return pid if isinstance(pid, int) else None


def start(home: Path, port: int, role: Role, ui_origin: str) -> int:
    """`serve` in a background process, once it answers `/api/health`."""
    running = recorded_host(home)
    if running is not None:
        print(HostRunning(home, running), file=sys.stderr)
        return 1
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            print(f"Port {port} is already occupied.", file=sys.stderr)
            return 1
    command = [sys.executable, "-m", "qmx_host", "serve", "--home", str(home), "--port", str(port)]
    command += ["--role", role, "--ui-origin", ui_origin]
    with (home / "control.log").open("ab") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    deadline = time.monotonic() + START_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print("The host failed to start; see control.log.", file=sys.stderr)
            return 1
        pid = health(port)
        if pid is not None and pid == recorded_host(home):
            print(f"Started qmx_host as PID {pid} on port {port}.")
            return 0
        time.sleep(0.1)
    terminate(process.pid)
    print("The host did not become ready; see control.log.", file=sys.stderr)
    return 1


def status(home: Path) -> int:
    pid = recorded_host(home)
    if pid is None:
        print("qmx_host is stopped.")
        return 0
    port = json.loads((home / STATE).read_text(encoding="utf-8"))["port"]
    if health(port) != pid:
        print(f"Recorded PID {pid} does not answer on port {port}.", file=sys.stderr)
        return 1
    print(f"qmx_host is running as PID {pid} on port {port}.")
    return 0


def stop(home: Path) -> int:
    pid = recorded_host(home)
    if pid is None:
        (home / STATE).unlink(missing_ok=True)
        print("qmx_host is stopped.")
        return 0
    terminate(pid)
    (home / STATE).unlink(missing_ok=True)
    print(f"Stopped qmx_host PID {pid}.")
    return 0


def terminate(pid: int) -> None:
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    tree = [*reversed(process.children(recursive=True)), process]
    for member in tree:
        with suppress(psutil.NoSuchProcess):
            member.terminate()
    _, alive = psutil.wait_procs(tree, timeout=10)
    for member in alive:
        with suppress(psutil.NoSuchProcess):
            member.kill()
