"""Exercise native CT-15 exclusion across OS processes, including a lost holder."""

from __future__ import annotations

import errno
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pytest import MonkeyPatch
from qmf.data import intake_authority
from qmf.data.intake_authority import _ProcessLock  # pyright: ignore[reportPrivateUsage]

_WORKER = """
import sys
from pathlib import Path
from qmf.data.intake_authority import _ProcessLock
lock, waiting, held = map(Path, sys.argv[1:])
waiting.touch()
with _ProcessLock(lock):
    held.touch()
    sys.stdin.readline()
"""


def _wait_for(path: Path, proc: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 15
    while not path.exists():
        if proc.poll() is not None:
            _, stderr = proc.communicate(timeout=1)
            pytest.fail(f"lock worker exited {proc.returncode}: {stderr}")
        if time.monotonic() >= deadline:
            pytest.fail(f"lock worker did not create {path.name}")
        time.sleep(0.02)


@pytest.mark.parametrize("crash,hold_seconds", [(False, 0.2), (True, 0.2), (False, 11)])
def test_native_process_exclusion_and_release(
    tmp_path: Path, crash: bool, hold_seconds: float
) -> None:
    lock = tmp_path / "ct15.lock"
    children: list[subprocess.Popen[str]] = []
    try:
        for index in range(2):
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    _WORKER,
                    str(lock),
                    str(tmp_path / f"waiting-{index}"),
                    str(tmp_path / f"held-{index}"),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            children.append(child)
            _wait_for(tmp_path / f"waiting-{index}", child)
            if index == 0:
                _wait_for(tmp_path / "held-0", child)
        # The second process reached the same native lock, but cannot enter.
        time.sleep(hold_seconds)
        assert children[1].poll() is None
        assert not (tmp_path / "held-1").exists()
        if crash:
            children[0].kill()
            children[0].communicate(timeout=5)
        else:
            _, stderr = children[0].communicate("\n", timeout=5)
            assert children[0].returncode == 0, stderr
        _wait_for(tmp_path / "held-1", children[1])
        _, stderr = children[1].communicate("\n", timeout=5)
        assert children[1].returncode == 0, stderr
        # Preserve the inode/path; unlinking a lock can split exclusion domains.
        assert lock.is_file()
        with _ProcessLock(lock):
            pass
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)


def test_process_lock_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        _ProcessLock(tmp_path)


@pytest.mark.parametrize("on_unlock", [False, True])
def test_native_failure_closes_descriptor(
    tmp_path: Path, monkeypatch: MonkeyPatch, on_unlock: bool
) -> None:
    opened: list[int] = []
    actual_open = os.open

    def capture_open(path: Path, flags: int, mode: int = 0o777) -> int:
        fd = actual_open(path, flags, mode)
        opened.append(fd)
        return fd

    class NativeFailure:
        LOCK_EX = LK_NBLCK = 1
        LOCK_UN = LK_UNLCK = 2

        def flock(self, fd: int, operation: int) -> None:
            del fd
            if (operation == self.LOCK_UN) == on_unlock:
                raise OSError(errno.EINVAL, "non-contention failure")

        def locking(self, fd: int, mode: int, nbytes: int) -> None:
            del nbytes
            self.flock(fd, mode)

    def failing_native(name: str) -> NativeFailure:
        del name
        return NativeFailure()

    monkeypatch.setattr(intake_authority.os, "open", capture_open)
    monkeypatch.setattr(intake_authority, "import_module", failing_native)
    if on_unlock:
        lock = _ProcessLock(tmp_path / "failure.lock")
        with pytest.raises(OSError, match="non-contention"):
            lock.close()
        lock.close()
    else:
        with pytest.raises(OSError, match="non-contention"):
            _ProcessLock(tmp_path / "failure.lock")
    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])
