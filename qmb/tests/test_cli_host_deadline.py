"""Deadline and retained-handle regressions; no daemon or provider is started."""

from __future__ import annotations

# pyright: reportPrivateUsage=false
# These tests exercise the process/framing boundary with deterministic fixtures.
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from qmb.doors.cli import host
from qmf.core import is_refusal


@dataclass
class Clock:
    now: float = 0.0

    def monotonic(self) -> float:
        return self.now


class Owned(subprocess.Popen[bytes]):
    def __init__(self) -> None:
        self.pid = 77800
        self.returncode = None
        self._child_created = False
        self.cleaned = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.returncode = -1
        self.cleaned = True

    def wait(self, timeout: float | None = None) -> int:
        assert self.returncode is not None
        return self.returncode

    def kill(self) -> None:
        self.terminate()


def setup_owned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: Clock) -> Owned:
    owned = Owned()

    def spawn(*args: object, **kwargs: object) -> Owned:
        (tmp_path / host.DAEMON_LOCK_NAME).write_text(json.dumps({"pid": owned.pid}))
        return owned

    monkeypatch.setattr(host, "_default_spawn", spawn)

    def live(pid: int) -> bool:
        return not owned.cleaned

    monkeypatch.setattr(host, "_pid_is_live", live)
    monkeypatch.setattr(host.time, "monotonic", clock.monotonic)
    return owned


class SlowFrame:
    def __init__(self, frame: bytes, clock: Clock) -> None:
        self.frame = frame
        self.clock = clock
        self.offset = 0
        self.timeout = 0.0
        self.timeouts: list[float] = []

    def __enter__(self) -> SlowFrame:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def settimeout(self, timeout: float) -> None:
        assert 0 < timeout <= 0.05 + 1e-10
        self.timeout = timeout
        self.timeouts.append(timeout)

    def sendall(self, data: bytes) -> None:
        assert self.timeout > 0

    def recv(self, size: int) -> bytes:
        if self.timeout <= 0.04:
            self.clock.now += self.timeout
            raise TimeoutError("simulated slow frame")
        self.clock.now += 0.04
        piece = self.frame[self.offset : self.offset + 1]
        self.offset += 1
        return piece


def test_slow_framed_response_is_bounded_and_reaps_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = Clock()
    owned = setup_owned(tmp_path, monkeypatch, clock)
    (tmp_path / host.HOST_CONTROL_FILE).write_text("synthetic-deadline-token")
    (tmp_path / host.HOST_CONTROL_BIND_NAME).write_text(
        json.dumps({"host": "127.0.0.1", "port": 1})
    )
    frame = host._encode_frame(
        {"ok": True, "status": {"lock": "held", "pid": owned.pid}, "padding": " " * 180}
    )
    assert len(frame) == 245
    sockets: list[SlowFrame] = []

    def connect(address: tuple[str, int], *, timeout: float) -> SlowFrame:
        assert 0 < timeout <= 0.05 + 1e-10
        stream = SlowFrame(frame, clock)
        sockets.append(stream)
        return stream

    def sleep(seconds: float) -> None:
        clock.now += seconds

    monkeypatch.setattr(host.socket, "create_connection", connect)
    result = host.invoke_host_start(root=tmp_path, sleeper=sleep)
    assert is_refusal(result)
    assert clock.now <= 5.0 + 1e-10
    assert sockets and all(stream.offset < len(frame) for stream in sockets)
    assert owned.cleaned
    assert result.context["cleanup_error"] is None
    assert not (tmp_path / host.DAEMON_LOCK_NAME).exists()


@pytest.mark.parametrize("late", [5.0, 6.0])
def test_late_true_probe_is_not_start_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, late: float
) -> None:
    clock = Clock()
    owned = setup_owned(tmp_path, monkeypatch, clock)

    def ready(root: Path, *, deadline: float | None = None) -> bool:
        assert deadline == 5.0
        clock.now = late
        return True

    monkeypatch.setattr(host, "_ready", ready)
    assert is_refusal(host.invoke_host_start(root=tmp_path))
    assert owned.cleaned


def test_oversleep_does_not_begin_a_probe_after_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = Clock()
    owned = setup_owned(tmp_path, monkeypatch, clock)
    probes: list[float] = []
    sleeps: list[float] = []

    def ready(root: Path, *, deadline: float | None = None) -> bool:
        probes.append(clock.now)
        clock.now = 4.99
        return False

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.now += seconds + 0.001

    monkeypatch.setattr(host, "_ready", ready)
    assert is_refusal(host.invoke_host_start(root=tmp_path, sleeper=sleep))
    assert probes == [0.0]
    assert sleeps == pytest.approx([0.01])
    assert owned.cleaned


def test_final_report_cannot_commit_readiness_after_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = Clock()
    owned = setup_owned(tmp_path, monkeypatch, clock)

    def ready(root: Path, *, deadline: float | None = None) -> bool:
        clock.now = 4.999
        return True

    def late_redaction(value: object) -> object:
        clock.now += 0.002
        return value

    monkeypatch.setattr(host, "_ready", ready)
    monkeypatch.setattr(host, "redact_host_surface", late_redaction)
    assert is_refusal(host.invoke_host_start(root=tmp_path))
    assert owned.cleaned


@pytest.mark.skipif(os.name != "nt", reason="Windows retained process object")
@pytest.mark.parametrize("exit_code", [0, 259])
def test_exited_owned_handle_releases_its_lock_immediately(tmp_path: Path, exit_code: int) -> None:
    # A harmless interpreter exits immediately; its Popen handle stays retained.
    child = host._default_spawn(
        (sys.executable, "-I", "-B", "-c", f"import sys; sys.exit({exit_code})"),
        env=dict(os.environ),
        root=tmp_path,
    )
    assert child.wait(timeout=10) == exit_code
    (tmp_path / host.DAEMON_LOCK_NAME).write_text(json.dumps({"pid": child.pid}))
    assert not host._pid_is_live(child.pid)
    assert host._cleanup_start_child(child, tmp_path) is None
    # Do not call status here: it would hide an incomplete cleanup by removing stale locks.
    assert not (tmp_path / host.DAEMON_LOCK_NAME).exists()
    assert child.poll() == exit_code


def test_cleanup_never_clears_a_different_live_writers_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owned = Owned()
    owned.returncode = 0
    (tmp_path / host.DAEMON_LOCK_NAME).write_text(json.dumps({"pid": os.getpid()}))
    before = (tmp_path / host.DAEMON_LOCK_NAME).read_bytes()
    assert host._cleanup_start_child(owned, tmp_path) is None
    assert (tmp_path / host.DAEMON_LOCK_NAME).read_bytes() == before
    assert not owned.cleaned


def test_changed_writer_identity_is_not_unlinked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / host.DAEMON_LOCK_NAME).write_text(json.dumps({"pid": 778}))

    def changed(pid: int) -> bool:
        (tmp_path / host.DAEMON_LOCK_NAME).write_text(json.dumps({"pid": os.getpid()}))
        return False

    monkeypatch.setattr(host, "_pid_is_live", changed)
    host._drop_stale_lock(tmp_path, expected_pid=778)
    assert json.loads((tmp_path / host.DAEMON_LOCK_NAME).read_text())["pid"] == os.getpid()


@pytest.mark.parametrize("stage", ["connect", "send", "encode"])
def test_readiness_deadline_covers_connect_send_and_encoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    clock = Clock()
    (tmp_path / host.HOST_CONTROL_FILE).write_text("synthetic-deadline-token")
    (tmp_path / host.HOST_CONTROL_BIND_NAME).write_text(
        json.dumps({"host": "127.0.0.1", "port": 1})
    )
    stream = SlowFrame(b"", clock)
    sends: list[bytes] = []

    def connect(address: tuple[str, int], *, timeout: float) -> SlowFrame:
        assert timeout <= 0.05
        if stage == "connect":
            clock.now += timeout
        return stream

    def send(data: bytes) -> None:
        sends.append(data)
        clock.now += stream.timeout

    real_encode = host._encode_frame

    def encode(payload: dict[str, object]) -> bytes:
        data = real_encode(payload)
        clock.now += 0.06
        return data

    monkeypatch.setattr(host.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(host.socket, "create_connection", connect)
    monkeypatch.setattr(stream, "sendall", send)
    if stage == "encode":
        monkeypatch.setattr(host, "_encode_frame", encode)
    result = host._host_control_call(tmp_path, "status", timeout_s=0.05, deadline=5.0)
    assert is_refusal(result)
    assert stream.offset == 0
    assert bool(sends) is (stage == "send")
