"""A small replacement host door: start, status, stop and foreground serve."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

import httpx
import psutil
import uvicorn

from qmx_control.server import create_app, default_home, local_token
from qmx_control.service import ControlService


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx-control")
    parser.add_argument("command", choices=["serve", "start", "status", "stop", "weekly-backup"])
    parser.add_argument(
        "--dry-run", action="store_true", help="Rehearse backup against a local bare repo"
    )
    parser.add_argument("--home", type=Path, default=default_home())
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    args = parser.parse_args()
    home: Path = args.home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    if args.command == "weekly-backup":
        print(json.dumps(ControlService(home).backup_weekly(dry_run=args.dry_run)))
        return 0
    token = local_token()
    if args.command == "serve":
        uvicorn.run(
            create_app(ControlService(home), token, args.ui_origin),
            host="127.0.0.1",
            port=args.port,
        )
        return 0
    state = home / "control-process.json"
    if args.command == "start":
        if state.exists():
            print("A host is already recorded; use status or stop first.", file=sys.stderr)
            return 1
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", args.port))
            except OSError:
                print("Host port is already occupied.", file=sys.stderr)
                return 1
        with (home / "control.log").open("ab") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "qmx_control",
                    "serve",
                    "--home",
                    str(home),
                    "--port",
                    str(args.port),
                    "--ui-origin",
                    args.ui_origin,
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        for _ in range(100):
            if process.poll() is not None:
                print("Host failed to start; see control.log.", file=sys.stderr)
                return 1
            try:
                response = httpx.get(
                    f"http://127.0.0.1:{args.port}/api/health",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=0.5,
                )
                reported_pid = response.json().get("pid") if response.status_code == 200 else None
                owned = {process.pid}
                owned.update(
                    child.pid for child in psutil.Process(process.pid).children(recursive=True)
                )
                if reported_pid in owned:
                    state.write_text(
                        json.dumps(
                            {
                                "pid": reported_pid,
                                "port": args.port,
                                "created": psutil.Process(reported_pid).create_time(),
                            }
                        ),
                        encoding="utf-8",
                    )
                    print(f"Started qmx-control on port {args.port}.")
                    return 0
            except httpx.HTTPError, psutil.NoSuchProcess:
                pass
            time.sleep(0.1)
        _terminate_tree(psutil.Process(process.pid))
        print("Host did not become ready; see control.log.", file=sys.stderr)
        return 1
    if not state.exists():
        print("qmx-control is stopped.")
        return 0
    data = json.loads(state.read_text(encoding="utf-8"))
    if args.command == "status":
        try:
            response = httpx.get(
                f"http://127.0.0.1:{data['port']}/api/health",
                headers={"Authorization": f"Bearer {token}"},
                timeout=2,
            )
            response.raise_for_status()
            if response.json().get("pid") != data["pid"]:
                print("Recorded host has been replaced by another process.", file=sys.stderr)
                return 1
        except httpx.HTTPError:
            print("Recorded host is unreachable.", file=sys.stderr)
            return 1
        print("qmx-control is running.")
        return 0
    try:
        process = psutil.Process(data["pid"])
        if process.create_time() != data["created"]:
            raise RuntimeError("Recorded PID belongs to a different process; refusing to stop it.")
        _terminate_tree(process)
    except psutil.NoSuchProcess:
        pass
    state.unlink()
    print("Stopped qmx-control.")
    return 0


def _terminate_tree(process: psutil.Process) -> None:
    children = process.children(recursive=True)
    for child in reversed(children):
        with suppress(psutil.NoSuchProcess):
            child.terminate()
    process.terminate()
    _, alive = psutil.wait_procs([*children, process], timeout=10)
    for remaining in alive:
        remaining.kill()
    psutil.wait_procs(alive, timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
