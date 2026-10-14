"""Crash-safe plants in the ship home, restored settings first, on exit and on the next start."""

from __future__ import annotations

import json
import msvcrt
import os
import shutil
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Final

LOGIN: Final = ".credentials.json"


class Locked(Exception):
    def __init__(self, lock: Path) -> None:
        super().__init__(f"{lock} is held by another running probe")


@contextmanager
def exclusive(lock: Path) -> Generator[None]:
    """An OS lock on the first byte of `lock`, which Windows drops when the holder dies."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_CREAT | os.O_RDWR)
    try:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            raise Locked(lock) from None
        try:
            yield
        finally:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


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
