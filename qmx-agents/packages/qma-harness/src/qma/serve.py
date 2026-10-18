"""`python -m qma.serve`: the QMA host. The same commands as `qmx_control`.

Order is the invariant. Parse the arguments, read the UI keep list with the standard library,
scrub this process's environment, and only then import the harness. What must hold is
"scrubbed before the first `connect()`", because the SDK reads `os.environ` there.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

from qma.boot import read_keep_names, scrub_process_env

STATE: Final = "control-process.json"
"""The same record `qmx_control` keeps, so one home never runs two hosts."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qma.serve")
    parser.add_argument("command", choices=["serve", "start", "status", "stop"])
    parser.add_argument("--home", type=Path, default=Path.home() / ".qmx")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    args = parser.parse_args(argv)
    home: Path = args.home.resolve()
    keep = read_keep_names(home / "settings.toml")
    scrubbed = scrub_process_env(os.environ, keep)
    home.mkdir(parents=True, exist_ok=True)
    if args.command == "serve":
        from qma import harness  # noqa: PLC0415

        harness.serve(
            root=home,
            port=args.port,
            ui_origin=args.ui_origin,
            scrubbed=scrubbed,
            keep=sorted(keep),
        )
        return 0
    if args.command == "start":
        return _start(home, args.port, args.ui_origin)
    if args.command == "status":
        return _status(home)
    return _stop(home)


def _health(port: int) -> int | None:
    """The pid the host on `port` reports, or None."""
    import httpx  # noqa: PLC0415
    from qmx_control.server import local_token  # noqa: PLC0415

    try:
        response = httpx.get(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Authorization": f"Bearer {local_token()}"},
            timeout=2,
        )
    except httpx.HTTPError:
        return None
    pid = response.json().get("pid") if response.status_code == 200 else None
    return pid if isinstance(pid, int) else None


def _start(home: Path, port: int, ui_origin: str) -> int:
    import psutil  # noqa: PLC0415

    state = home / STATE
    if state.exists():
        print("A host is already recorded; use status or stop first.", file=sys.stderr)
        return 1
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            print(f"Port {port} is already occupied.", file=sys.stderr)
            return 1
    command = [sys.executable, "-m", "qma.serve", "serve", "--home", str(home)]
    command += ["--port", str(port), "--ui-origin", ui_origin]
    with (home / "control.log").open("ab") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print("The host failed to start; see control.log.", file=sys.stderr)
            return 1
        pid = _health(port)
        owned = {process.pid, *(child.pid for child in psutil.Process(process.pid).children(True))}
        if pid in owned:
            created = psutil.Process(pid).create_time()
            record = {"pid": pid, "port": port, "created": created}
            state.write_text(json.dumps(record), encoding="utf-8")
            print(f"Started qma.serve as PID {pid} on port {port}.")
            return 0
        time.sleep(0.1)
    _terminate(process.pid)
    print("The host did not become ready; see control.log.", file=sys.stderr)
    return 1


def _status(home: Path) -> int:
    state = home / STATE
    if not state.exists():
        print("qma.serve is stopped.")
        return 0
    record = json.loads(state.read_text(encoding="utf-8"))
    pid = _health(record["port"])
    if pid is None:
        print(f"Recorded PID {record['pid']} is unreachable.", file=sys.stderr)
        return 1
    if pid != record["pid"]:
        print(f"Recorded PID {record['pid']} was replaced by PID {pid}.", file=sys.stderr)
        return 1
    print(f"qma.serve is running as PID {pid} on port {record['port']}.")
    return 0


def _stop(home: Path) -> int:
    import psutil  # noqa: PLC0415

    state = home / STATE
    if not state.exists():
        print("qma.serve is stopped.")
        return 0
    record = json.loads(state.read_text(encoding="utf-8"))
    try:
        if psutil.Process(record["pid"]).create_time() != record["created"]:
            print("The recorded PID belongs to another process; not stopping it.", file=sys.stderr)
            return 1
        _terminate(record["pid"])
    except psutil.NoSuchProcess:
        pass
    state.unlink()
    print(f"Stopped qma.serve PID {record['pid']}.")
    return 0


def _terminate(pid: int) -> None:
    import psutil  # noqa: PLC0415

    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    tree = [*reversed(process.children(recursive=True)), process]
    for member in tree:
        try:
            member.terminate()
        except psutil.NoSuchProcess:
            continue
    _, alive = psutil.wait_procs(tree, timeout=10)
    for member in alive:
        try:
            member.kill()
        except psutil.NoSuchProcess:
            continue


if __name__ == "__main__":
    raise SystemExit(main())
