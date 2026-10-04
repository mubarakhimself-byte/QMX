"""Observable module startup, sole-writer refusal, stopped recovery and restart."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import cast

import pytest
from qma.daemon.host_control import (
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_FILE,
    host_control_call,
    host_control_fp1,
    read_host_control_bind,
    read_host_control_token,
)
from qmf.core import is_ok, is_refusal


def _seed(root: Path) -> None:
    root.mkdir()
    corpus = root.parent / "corpus"
    corpus.mkdir(exist_ok=True)
    (root / "operator-config.json").write_text(
        json.dumps({"research_corpus_root_path": str(corpus)}), encoding="utf-8"
    )


def _environment(root: Path, **overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    for key in ("QMA_DAEMON_RECOVER_CONTROL", "QMA_DAEMON_CONFIG", "PYTHONPATH"):
        env.pop(key, None)
    env.update(
        QMA_DAEMON_ROOT=str(root),
        QMA_DAEMON_MACHINE="entrypoint-test",
        QMA_DAEMON_BOOT_EPOCH="entrypoint-boot",
        QMA_DAEMON_BIND_PORT="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    env.update(overrides)
    return env


def _run(root: Path, *args: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "qma.daemon", *args],
        env=_environment(root, **overrides),
        capture_output=True,
        text=True,
        timeout=30,
    )


def _refused(result: subprocess.CompletedProcess[str], reason: str) -> None:
    assert result.returncode == 2, result.stderr
    events: list[dict[str, object]] = []
    for line in result.stderr.splitlines():
        if line.startswith("{"):
            raw: object = json.loads(line)
            assert isinstance(raw, dict)
            events.append(cast("dict[str, object]", raw))
    refusals = [row for row in events if row.get("event") == "daemon.startup_refused"]
    assert len(refusals) == 1, result.stderr
    assert reason in str(refusals[0]["reason"]), result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout


@pytest.mark.parametrize("port", ["not-a-port", "-1", "65536"])
def test_invalid_listener_port_refuses_before_durable_bootstrap(tmp_path: Path, port: str) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    _refused(_run(root, QMA_DAEMON_BIND_PORT=port), "port" if port != "not-a-port" else "integer")
    assert {path.name for path in root.iterdir()} == {"operator-config.json"}


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (b"{", "cannot read"),
        (b"\xff", "cannot read"),
        (b"[]", "JSON object"),
        (b"{}", "research_corpus_root_path"),
        (b'{"research_corpus_root_path": true}', "non-empty string"),
        (b'{"research_corpus_root_path": "   "}', "non-empty string"),
    ],
)
def test_invalid_config_refuses_without_writer_or_control_token(
    tmp_path: Path, raw: bytes, reason: str
) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    (root / "operator-config.json").write_bytes(raw)
    _refused(_run(root), reason)
    assert {path.name for path in root.iterdir()} == {"operator-config.json"}


def test_missing_config_recover_path_is_also_structured_refusal(tmp_path: Path) -> None:
    root = tmp_path / "daemon"
    _refused(_run(root, "--recover-control"), "operator configuration is required")
    assert not root.exists()


def test_invalid_local_environment_refuses_before_writer(tmp_path: Path) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    config = root / "operator-config.json"
    raw = json.loads(config.read_text())
    raw["qmb_local_environment"] = {"provider_ref": "local-test", "network": "internet"}
    config.write_text(json.dumps(raw), encoding="utf-8")
    _refused(_run(root), "network=none")
    assert {path.name for path in root.iterdir()} == {"operator-config.json"}


@pytest.mark.parametrize("recover", [False, True])
def test_configuration_permission_failure_refuses_without_entering_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    recover: bool,
) -> None:
    from qma.daemon.__main__ import main

    root = tmp_path / "daemon"
    _seed(root)
    original = Path.read_text

    def denied(
        path: Path,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> str:
        if path == root / "operator-config.json":
            raise PermissionError("test OS permission denial")
        return original(path, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "read_text", denied)
    monkeypatch.setenv("QMA_DAEMON_ROOT", str(root))
    monkeypatch.setenv("QMA_DAEMON_BIND_PORT", "0")
    monkeypatch.delenv("QMA_DAEMON_RECOVER_CONTROL", raising=False)
    monkeypatch.setattr(sys, "argv", ["qma.daemon", *(["--recover-control"] if recover else [])])
    assert main() == 2
    captured = capsys.readouterr()
    row = json.loads(captured.err)
    assert row["event"] == "daemon.startup_refused"
    assert "test OS permission denial" in row["reason"]
    assert not captured.out
    assert {path.name for path in root.iterdir()} == {"operator-config.json"}


@contextmanager
def _live(root: Path, *, boot: str) -> Generator[subprocess.Popen[str]]:
    with (root.parent / f"{boot}.stderr").open("w+", encoding="utf-8") as stderr:
        child = subprocess.Popen(
            [sys.executable, "-m", "qma.daemon"],
            env=_environment(root, QMA_DAEMON_BOOT_EPOCH=boot),
            stdout=subprocess.DEVNULL,
            stderr=stderr,
            text=True,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                status = host_control_call(root, "status", timeout_s=0.2)
                if is_ok(status) and status.value.get("ok") is True:
                    break
                if child.poll() is not None:
                    stderr.seek(0)
                    pytest.fail(stderr.read())
                time.sleep(0.05)
            else:
                pytest.fail("daemon never became ready through authenticated host status")
            yield child
            stopped = host_control_call(root, "stop")
            assert is_ok(stopped) and stopped.value["ok"] is True, stopped
            assert child.wait(timeout=15) == 0
        finally:
            if child.poll() is None:
                host_control_call(root, "stop", timeout_s=0.5)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Windows venv launchers redirect to a child PID. Only terminate
                    # a fixture writer whose exact root/machine/boot identity matches.
                    lock_path = root / ".daemon_writer"
                    if lock_path.is_file():
                        lock = json.loads(lock_path.read_text())
                        assert lock["machine"] == "entrypoint-test"
                        assert lock["boot_epoch_id"] == boot
                        pid = lock["pid"]
                        assert isinstance(pid, int) and pid > 0 and pid != os.getpid()
                        with suppress(ProcessLookupError):
                            os.kill(pid, signal.SIGTERM)
                    child.terminate()
                    child.wait(timeout=15)
            stderr.seek(0)
            assert "Traceback" not in stderr.read()


def test_real_start_stop_restart_and_recover_keep_principal_and_revoke_old_control(
    tmp_path: Path,
) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    with _live(root, boot="first") as child:
        first = read_host_control_token(root)
        assert is_ok(first)
        status = host_control_call(root, "status")
        assert is_ok(status)
        state = cast("dict[str, object]", status.value["status"])
        lock = json.loads((root / ".daemon_writer").read_text())
        assert state["pid"] == lock["pid"]
        assert isinstance(state["pid"], int) and state["pid"] > 0
        assert state["operator_established"] is True
        assert state["lock"] == "held"
        denied = host_control_call(root, "stop", token=host_control_fp1(first.value))
        assert is_ok(denied) and denied.value["ok"] is False
        assert child.poll() is None
        readable = _run(root, "--recover-control")
        _refused(readable, "still readable")
        token_path = root / HOST_CONTROL_FILE
        prior_token = token_path.read_bytes()
        prior_lock = (root / ".daemon_writer").read_bytes()
        token_path.unlink()
        try:
            lost_while_live = _run(root, "--recover-control")
            _refused(lost_while_live, "daemon is live")
            assert child.poll() is None
            assert not token_path.exists()
            assert (root / ".daemon_writer").read_bytes() == prior_lock
        finally:
            token_path.write_bytes(prior_token)
        duplicate = _run(root, QMA_DAEMON_BOOT_EPOCH="duplicate")
        _refused(duplicate, "writer")
        assert child.poll() is None
    assert not (root / ".daemon_writer").exists()
    # The process restart preserves the existing credential, never remints a principal.
    with _live(root, boot="second"):
        second = read_host_control_token(root)
        assert is_ok(second) and host_control_fp1(second.value) == host_control_fp1(first.value)
    (root / HOST_CONTROL_FILE).unlink()
    (root / HOST_CONTROL_BIND_NAME).unlink()
    recovered = _run(root, QMA_DAEMON_RECOVER_CONTROL="1")
    assert recovered.returncode == 0, recovered.stderr
    assert "Traceback" not in recovered.stderr
    assert not (root / HOST_CONTROL_BIND_NAME).exists()
    assert not (root / ".daemon_writer").exists()
    fresh = read_host_control_token(root)
    assert is_ok(fresh) and host_control_fp1(fresh.value) != host_control_fp1(first.value)
    with _live(root, boot="third"):
        stale = host_control_call(root, "status", token=first.value)
        assert is_ok(stale) and stale.value["ok"] is False
        status = host_control_call(root, "status")
        assert is_ok(status) and status.value["ok"] is True
    # Read persisted identity through the existing daemon-owned public composition boundary.
    from qma.daemon.bootstrap_config import load_plugin_load_configs
    from qma.daemon.host_control import principal_count
    from qma.daemon.process import DaemonProcess

    reopened = DaemonProcess.compose(
        root,
        machine="entrypoint-test",
        boot_epoch_id="readback",
        plugin_load_configs=load_plugin_load_configs(root),
    )
    assert is_ok(reopened), reopened
    try:
        assert principal_count(reopened.value.sqlite) == 1
        assert reopened.value.local_operator is not None
        assert reopened.value.local_operator.minted is False
        rows = reopened.value.journal.read_all()
        assert is_ok(rows)
        assert (
            sum(row["event"] == "local_operator.host_control_recovered" for row in rows.value) == 1
        )
    finally:
        reopened.value.close()


def test_occupied_listener_refuses_then_releases_writer_for_retry(tmp_path: Path) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        port = occupied.getsockname()[1]
        _refused(_run(root, QMA_DAEMON_BIND_PORT=str(port)), "loopback listener")
    assert not (root / ".daemon_writer").exists()
    with _live(root, boot="after-bind-failure"):
        assert is_ok(read_host_control_bind(root))


def test_corrupt_control_token_returns_refusal_then_allows_stopped_recovery(tmp_path: Path) -> None:
    root = tmp_path / "daemon"
    _seed(root)
    with _live(root, boot="before-corruption"):
        pass
    (root / HOST_CONTROL_FILE).write_bytes(b"\xff")
    refused = read_host_control_token(root)
    assert is_refusal(refused)
    assert refused.context["field"] == "host_control"
    assert (root / HOST_CONTROL_FILE).read_bytes() == b"\xff"
    assert not (root / ".daemon_writer").exists()
    recovered = _run(root, "--recover-control")
    assert recovered.returncode == 0, recovered.stderr
    assert is_ok(read_host_control_token(root))
    with _live(root, boot="after-corruption"):
        pass


def test_keyboard_interrupt_after_real_bind_closes_before_event_loop_teardown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qma.daemon.__main__ import main
    from qma.daemon.bootstrap_config import load_plugin_load_configs
    from qma.daemon.process import DaemonProcess
    from qmf.core import Result

    root = tmp_path / "daemon"
    _seed(root)
    monkeypatch.setenv("QMA_DAEMON_ROOT", str(root))
    monkeypatch.setenv("QMA_DAEMON_BIND_PORT", "0")
    monkeypatch.delenv("QMA_DAEMON_RECOVER_CONTROL", raising=False)
    monkeypatch.setattr(sys, "argv", ["qma.daemon"])
    addresses: list[tuple[str, int]] = []

    async def interrupted(process: DaemonProcess) -> Result[None]:
        bound = await process.bind()
        assert is_ok(bound), bound
        addresses.append((bound.value.host, bound.value.port))
        control = read_host_control_bind(root)
        assert is_ok(control), control
        addresses.append(control.value)
        raise KeyboardInterrupt

    monkeypatch.setattr(DaemonProcess, "serve", interrupted)
    assert main() == 0
    assert len(addresses) == 2
    assert not (root / ".daemon_writer").exists()
    for address in addresses:
        with socket.socket() as probe:
            assert probe.connect_ex(address) != 0
    reopened = DaemonProcess.compose(
        root,
        machine="entrypoint-test",
        boot_epoch_id="after-interrupt",
        plugin_load_configs=load_plugin_load_configs(root),
    )
    assert is_ok(reopened), reopened
    reopened.value.close()
