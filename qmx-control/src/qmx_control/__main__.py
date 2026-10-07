"""A small replacement host door: start, status, stop and foreground serve."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import uvicorn

from qmx_control.server import create_app, default_home, local_token
from qmx_control.service import ControlService


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx-control")
    parser.add_argument("command", choices=["serve", "start", "status", "stop"])
    parser.add_argument("--home", type=Path, default=default_home())
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--ui-origin", default="http://localhost:5173")
    args = parser.parse_args()
    home: Path = args.home.resolve()
    home.mkdir(parents=True, exist_ok=True)
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
                if response.status_code == 200 and response.json().get("pid") == process.pid:
                    state.write_text(
                        json.dumps({"pid": process.pid, "port": args.port}), encoding="utf-8"
                    )
                    print(f"Started qmx-control on port {args.port}.")
                    return 0
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        process.terminate()
        process.wait(timeout=10)
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
    # psutil verifies the recorded PID before termination, so PID reuse is safe.
    import psutil  # noqa: PLC0415

    try:
        process = psutil.Process(data["pid"])
        command = process.cmdline()
        if "qmx_control" not in command or "serve" not in command or str(home) not in command:
            raise RuntimeError("Recorded PID belongs to a different process; refusing to stop it.")
        process.terminate()
        process.wait(timeout=10)
    except psutil.NoSuchProcess:
        pass
    state.unlink()
    print("Stopped qmx-control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
