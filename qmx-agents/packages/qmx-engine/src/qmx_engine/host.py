"""`python -m qmx_engine.host serve --home <home> --port <port>`: the engine host, the interim
composition root (AD-3, Appendix F) until `qma.serve` composes the engine itself (L1).

It serves the same control app as `qma.serve`, with the engine attached to its workflow doors and
the engine's own routes added, but not the harness's chat routes. Order is `qma.serve`'s: refuse
on a live recorded host, scrub this process's environment, and only then import the harness.
The host records itself in `control-process.json`, the record `qma.serve` keeps, so one home
never runs two hosts; a record whose process is gone is replaced.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Final

import psutil
from qma.boot import read_keep_names, scrub_process_env

STATE: Final = "control-process.json"


def recorded_host(home: Path) -> int | None:
    """The pid of the live host the home's record names, or None."""
    try:
        record = json.loads((home / STATE).read_text(encoding="utf-8"))
        pid, created = record["pid"], record["created"]
    except OSError, ValueError, KeyError, TypeError:
        return None
    if not isinstance(pid, int):
        return None
    try:
        return pid if psutil.Process(pid).create_time() == created else None
    except psutil.Error:
        return None


@contextmanager
def recorded(home: Path, port: int) -> Generator[None]:
    me = psutil.Process()
    record = {"pid": me.pid, "port": port, "created": me.create_time()}
    path = home / STATE
    path.write_text(json.dumps(record), encoding="utf-8")
    try:
        yield
    finally:
        if recorded_host(home) == me.pid:
            path.unlink(missing_ok=True)


async def serve(home: Path, port: int, ui_origin: str) -> None:
    import uvicorn  # noqa: PLC0415
    from qma.harness import Harness, QmxHome  # noqa: PLC0415
    from qmx_control.server import create_app, local_token  # noqa: PLC0415
    from qmx_control.service import ControlService  # noqa: PLC0415

    from qmx_engine.control_door import EngineDoor  # noqa: PLC0415
    from qmx_engine.ports.harness_adapter import HarnessAdapter  # noqa: PLC0415
    from qmx_engine.service.rest import engine_router  # noqa: PLC0415

    control = ControlService(home)
    harness = await Harness.open(QmxHome(home), control=control)
    harness.control_port = port
    try:
        async with EngineDoor.open(control, harness=HarnessAdapter(harness)) as door:
            app = create_app(control, local_token(), ui_origin, extra_routers=[engine_router(door)])
            server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port))
            with recorded(home, port):
                await server.serve()
    finally:
        await harness.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_engine.host")
    parser.add_argument("command", choices=["serve"])
    parser.add_argument("--home", type=Path, default=Path.home() / ".qmx")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    args = parser.parse_args(argv)
    home: Path = args.home.resolve()
    pid = recorded_host(home)
    if pid is not None:
        print(
            f"refused: {home} already has a live host, PID {pid}; stop it first.", file=sys.stderr
        )
        return 1
    scrub_process_env(os.environ, read_keep_names(home / "settings.toml"))
    home.mkdir(parents=True, exist_ok=True)
    asyncio.run(serve(home, args.port, args.ui_origin))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
