"""Shared parts of the PRB-S probes: the server's probe home, one log, the host's free memory,
and the loader that reuses the PRB-L probe code by path.

Every probe runs on Contabo from the checkout at `/srv/qmx/check/prb-s`, in the throwaway venv
at `homes/prb-s/venv`, for example:

    HOME=/srv/qmx/check/prb-s/homes/prb-s \
        /srv/qmx/check/prb-s/homes/prb-s/venv/bin/python scripts/probes/server/p_ops.py

Nothing here reads the PC's store, the ship home, a key or a model login, and every file the
probes write is under the probe home.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Final, TextIO

HERE: Final = Path(__file__).resolve().parent
PROBES: Final = HERE.parent
LIBRARY: Final = PROBES / "library"
ROOT: Final = PROBES.parents[1]
"""The checkout: `scripts/probes/server` is three levels under it."""
PROBE_HOME: Final = ROOT / "homes" / "prb-s"
"""The throwaway home the venv, the rows, the logs and pg0's data folder live under."""


class Log:
    """Tee to stdout and `homes/prb-s/logs/<PRB_S_LOG_PREFIX><slug>.log` (prefix `owner-` for
    the builder's runs, `check-` for the coordinator's)."""

    def __init__(self, slug: str) -> None:
        folder = PROBE_HOME / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('PRB_S_LOG_PREFIX', 'owner-')}{slug}.log"
        self.file: TextIO = self.path.open("a", encoding="utf-8")
        self.say(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {Path(sys.argv[0]).name}")
        self.say(f"  log: {self.path}")

    def say(self, text: str) -> None:
        print(text, flush=True)
        self.file.write(text + "\n")
        self.file.flush()

    def verdict(self, verdict: object) -> None:
        for note in getattr(verdict, "notes", []):
            self.say(f"  note: {note}")
        self.say(verdict.line())


def meminfo_mb(key: str) -> int:
    """One `/proc/meminfo` figure in MB. The probes run on Linux, so there is no fallback."""
    with Path("/proc/meminfo").open(encoding="ascii") as handle:
        for line in handle:
            if line.startswith(f"{key}:"):
                return int(line.split()[1]) // 1024
    raise ValueError(f"{key} is not in /proc/meminfo")


def free_mb() -> int:
    """The kernel's estimate of memory available to new work: cache the machine can reclaim
    counts as free, which is what a placement budget needs."""
    return meminfo_mb("MemAvailable")


def total_mb() -> int:
    return meminfo_mb("MemTotal")


def load(path: Path, name: str) -> ModuleType:
    """Execute one file as the module `name`, once."""
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def library(name: str) -> ModuleType:
    """`scripts/probes/library/<name>.py`, loaded once as `prb_l_<name>`.

    The library probes are a folder, not a package, and import each other by bare name
    (`from common import Log, Verdict`), so the library folder goes on `sys.path` and the
    library's own `common` is bound while the file loads. This module's `common` is put back
    afterwards, so a later `from common import ...` still finds the server's.
    """
    cached = sys.modules.get(f"prb_l_{name}")
    if cached is not None:
        return cached
    saved_path = list(sys.path)
    saved_common = sys.modules.get("common")
    sys.path.insert(0, str(LIBRARY))
    sys.modules["common"] = load(LIBRARY / "common.py", "prb_l_common")
    try:
        return load(LIBRARY / f"{name}.py", f"prb_l_{name}")
    finally:
        sys.path[:] = saved_path
        if saved_common is None:
            sys.modules.pop("common", None)
        else:
            sys.modules["common"] = saved_common
