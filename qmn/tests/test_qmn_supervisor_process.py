"""Provider-free supervised process smoke tests for the installed module entrypoint."""

from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from qmf.core import World, is_ok
from qmf.data import JournalReader
from qmf.data.store import EvidenceStore
from qmn.host.configured_runtime import assess_configured_runtime
from test_qmn_configured_composition import offline_profile, valid_deployment, write_v2_deployment


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _launch(
    root: Path,
    state: Path,
    port: int,
    *,
    deployment_file: Path | None = None,
) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env.update(
        {
            "QMX_ROOT": str(root),
            "QMX_STATE": str(state),
            "QMN_EVIDENCE_BIND": f"127.0.0.1:{port}",
        }
    )
    if deployment_file is not None:
        env["QMN_DEPLOYMENT_CONFIG"] = str(deployment_file)
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
            # Windows terminate() calls TerminateProcess (forced code 1), while
            # POSIX sends SIGTERM and exercises the supervisor's clean drain.
            assert process.returncode == (1 if os.name == "nt" else 0)
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


def test_disconnected_status_clients_do_not_stall_supervisor(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    initial = assess_configured_runtime(valid_deployment(tmp_path), qmx_root=tmp_path)
    assert is_ok(initial)
    deployment = write_v2_deployment(tmp_path, offline_profile(initial.value, tmp_path))
    port = _port()
    process = _launch(tmp_path, state, port, deployment_file=deployment)
    try:
        deadline = time.monotonic() + 8
        aborted = 0
        while time.monotonic() < deadline and aborted < 12:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2) as sock:
                    # RST the connection after issuing GET, before consuming a
                    # reply. The linger struct uses Windows' ushort ABI.
                    sock.setsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_LINGER,
                        struct.pack("HH" if os.name == "nt" else "ii", 1, 0),
                    )
                    sock.sendall(b"GET /healthz HTTP/1.0\r\n\r\n")
                aborted += 1
            except OSError:
                time.sleep(0.05)
        assert aborted == 12
        _wait_status(port, process)
    finally:
        process.terminate()
        _stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == (1 if os.name == "nt" else 0)
    assert stderr is not None
    assert b"Traceback" not in stderr


def test_supervisor_loads_operator_config_and_stays_stand_down_on_refusal(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    deployment = tmp_path / "deployment.json"
    deployment.write_text("{}", encoding="utf-8")
    port = _port()
    process = _launch(tmp_path, state, port, deployment_file=deployment)
    try:
        _wait_status(port, process)
        try:
            with urlopen(f"http://127.0.0.1:{port}/readiness", timeout=2) as response:
                raise AssertionError(f"invalid deployment unexpectedly returned {response.status}")
        except HTTPError as response:
            assert response.code == 503
            readiness = json.loads(response.read())
            assert readiness["trading"] == "unavailable"
            assert "versioned configured-runtime fields" in readiness["reason"]
    finally:
        process.terminate()
        _stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == (1 if os.name == "nt" else 0)
        assert stderr is not None and b"RuntimeWarning" not in stderr


def test_supervisor_default_resolver_durably_stands_down_for_checked_v1_profile(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    initial = assess_configured_runtime(valid_deployment(tmp_path), qmx_root=tmp_path)
    assert is_ok(initial)
    deployment = write_v2_deployment(tmp_path, offline_profile(initial.value, tmp_path))
    port = _port()
    process = _launch(tmp_path, state, port, deployment_file=deployment)
    try:
        _wait_status(port, process)
        try:
            with urlopen(f"http://127.0.0.1:{port}/readiness", timeout=2) as response:
                raise AssertionError(f"replay-only profile unexpectedly returned {response.status}")
        except HTTPError as response:
            assert response.code == 503
            readiness = json.loads(response.read())
            assert readiness["trading"] == "unavailable"
            assert "QMB replay evidence" in readiness["reason"]
    finally:
        process.terminate()
        _stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == (1 if os.name == "nt" else 0)
        assert stderr is not None and b"RuntimeWarning" not in stderr

    evidence = EvidenceStore(state / "evidence")
    live = evidence.for_world(World.LIVE)
    assert is_ok(live)
    attempts = JournalReader(live.value.journal).read_checked(
        "boot-lifecycle", for_world=World.LIVE
    )
    assert is_ok(attempts)
    last_payload = attempts.value[-1].payload
    assert isinstance(last_payload, Mapping)
    attempt = last_payload.get("attempt")
    assert isinstance(attempt, Mapping)
    assert attempt["stage"] == "preflight"
    assert attempt["failure_id"] == ("configured_runtime.hosted_resources_missing")
