"""Crash-safe plants in the ship home, restored settings first, on exit and on the next start."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path
from typing import Final

LOGIN: Final = ".credentials.json"


class Locked(Exception):
    def __init__(self, lock: Path, pid: int) -> None:
        super().__init__(f"{lock} is held by live process {pid}")
        self.pid = pid


def _alive(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        access_denied = 5
        return ctypes.get_last_error() == access_denied
    try:
        code = wintypes.DWORD()
        still_active = 259
        return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and (
            code.value == still_active
        )
    finally:
        kernel32.CloseHandle(handle)


def _holder(lock: Path) -> int | None:
    try:
        pid = int(lock.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None
    return pid if _alive(pid) else None


@contextmanager
def exclusive(lock: Path) -> Generator[None]:
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if (pid := _holder(lock)) is not None:
                raise Locked(lock, pid) from None
            lock.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(str(os.getpid()))
        break
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def heal(backup: Path, lock: Path) -> list[str]:
    with exclusive(lock):
        return restore(backup)


def _highest_missing(root: Path, path: Path) -> Path | None:
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if not current.exists():
            return current
    return None


def snapshot(backup: Path, root: Path, files: Iterable[Path], folders: Iterable[Path]) -> None:
    if backup.exists():
        raise FileExistsError(f"{backup} holds an earlier plant; restore it first")
    files = list(files)
    earlier = {str(p): p.read_text(encoding="utf-8") if p.exists() else None for p in files}
    made = {
        str(top)
        for path in [*(p.parent for p in files), *folders]
        if (top := _highest_missing(root, path)) is not None
    }
    backup.parent.mkdir(parents=True, exist_ok=True)
    pending = backup.with_suffix(".tmp")
    pending.write_text(json.dumps({"files": earlier, "made": sorted(made)}), encoding="utf-8")
    os.replace(pending, backup)


def restore(backup: Path) -> list[str]:
    if not backup.exists():
        return []
    state = json.loads(backup.read_text(encoding="utf-8"))
    failures: list[str] = []
    for name, text in state["files"].items():
        if Path(name).name == LOGIN:
            failures.append(f"{name}: the login is never restored")
            continue
        try:
            if text is None:
                Path(name).unlink(missing_ok=True)
            else:
                Path(name).write_text(text, encoding="utf-8")
        except OSError as error:
            failures.append(f"{name}: {error}")
    for name in state["made"]:
        try:
            if Path(name).exists():
                shutil.rmtree(name)
        except OSError as error:
            failures.append(f"{name}: {error}")
    if not failures:
        backup.unlink()
    return failures
