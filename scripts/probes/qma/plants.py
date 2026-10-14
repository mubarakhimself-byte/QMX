"""Crash-safe plants in the ship home, restored settings first, on exit and on the next start."""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterable
from pathlib import Path


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
