"""Provider-free supervised process smoke tests for the installed module entrypoint."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from qmf.core import World, is_ok
from qmf.data import JournalReader
from qmf.data.store import EvidenceStore


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _launch(root: Path, state: Path, port: int) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env.update(
        {
            "QMX_ROOT": str(root),
            "QMX_STATE": str(state),
            "QMN_EVIDENCE_BIND": f"127.0.0.1:{port}",
        }
    )
    return subprocess.Popen(
        [sys.executable, "-m", "qmn.host.supervise"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def _wait_status(port: int, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"supervisor exited early with {process.returncode}")
        try:
            with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=0.2) as response:
                assert response.status == 200
                assert json.loads(response.read()) == {
                    "process": "alive",
                    "trading": "stand-down",
                }
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("supervisor status endpoint did not come up")


def test_supervisor_module_runs_stand_down_and_survives_restart(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    port = _port()
    for _ in range(2):
        process = _launch(tmp_path, state, port)
        try:
            _wait_status(port, process)
            try:
                with urlopen(f"http://127.0.0.1:{port}/readiness", timeout=2) as response:
                    raise AssertionError(
                        f"trading readiness unexpectedly returned {response.status}"
                    )
            except HTTPError as response:
                assert response.code == 503
                readiness = json.loads(response.read())
                assert readiness["state"] == "stand-down-alive"
                assert readiness["trading"] == "unavailable"
        finally:
            process.terminate()
            _stdout, stderr = process.communicate(timeout=5)
            assert process.returncode == 0
            assert stderr is not None and b"RuntimeWarning" not in stderr

    evidence = EvidenceStore(state / "evidence")
    live = evidence.for_world(World.LIVE)
    assert is_ok(live)
    events = JournalReader(live.value.journal).read_checked(
        "node-supervision", for_world=World.LIVE
    )
    assert is_ok(events)
    assert len(events.value) == 2
    assert all(event.payload["process_state"] == "stand-down-alive" for event in events.value)


def test_supervisor_fails_actionably_without_configured_directories(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "QMX_ROOT": str(tmp_path / "missing-root"),
            "QMX_STATE": str(tmp_path / "missing-state"),
            "QMN_EVIDENCE_BIND": f"127.0.0.1:{_port()}",
            "NOTIFY_SOCKET": "",
        }
    )
    completed = subprocess.run(
        [sys.executable, "-m", "qmn.host.supervise"],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert completed.returncode == 2
    assert "qmx_root" in completed.stderr
