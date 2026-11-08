"""Shared parts of the PRB-L probes: the store paths, one verdict shape, the evidence log, a p95,
and read-only copies of his files.

`p_taint.py` runs from the repository root with the root venv, as
`uv run --no-sync python scripts/live/library/p_taint.py`. It opens no ship home and takes no lane
lock, because it runs no plan turn. His files are read only through copies made by `copy_read_only`.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import sys
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal, TextIO

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "prb-l"
HOMES: Final = STORE / "homes" / "prb-l"
HIS_LIBRARY: Final = Path.home() / ".qmx" / "library.db"

Outcome = Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class Verdict:
    """One FINDINGS row: the probe, PASS or FAIL, the numbers that decided it, the reason in
    plain words, and the fallback a FAIL triggers (empty on a PASS)."""

    probe: str
    outcome: Outcome
    numbers: Mapping[str, float | int | str]
    reason: str
    fallback: str = ""
    notes: list[str] = field(default_factory=list[str])

    def line(self) -> str:
        shown = ", ".join(f"{k}={v}" for k, v in self.numbers.items())
        tail = f" Fallback: {self.fallback}" if self.outcome == "FAIL" else ""
        return f"{self.probe}: {self.outcome} ({shown}). {self.reason}{tail}"


def p95(samples: Iterable[float]) -> float:
    """Nearest-rank 95th percentile."""
    ordered = sorted(samples)
    if not ordered:
        raise ValueError("no samples")
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


class Log:
    """Tee to stdout and `evidence/prb-l/<PRB_L_LOG_PREFIX><slug>.log` (prefix `owner-` for the
    builder's runs, `check-` for the coordinator's)."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('PRB_L_LOG_PREFIX', 'owner-')}{slug}.log"
        self.file: TextIO = self.path.open("a", encoding="utf-8")
        self.say(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {Path(sys.argv[0]).name}")

    def say(self, text: str) -> None:
        print(text, flush=True)
        self.file.write(text + "\n")
        self.file.flush()

    def verdict(self, verdict: Verdict) -> None:
        for note in verdict.notes:
            self.say(f"  note: {note}")
        self.say(verdict.line())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_read_only(sources: Iterable[Path], into: Path) -> dict[Path, str]:
    """Copy each source into `into` and return its hash taken before the copy. The caller hashes
    the sources again afterwards to show nothing wrote to them (lane 6)."""
    into.mkdir(parents=True, exist_ok=True)
    hashes: dict[Path, str] = {}
    for source in sources:
        hashes[source] = sha256_file(source)
        shutil.copyfile(source, into / source.name)
    return hashes


KEY_SHAPES: Final = re.compile(
    r"(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{16,}"
    r"|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})"
)


def redact(text: str) -> str:
    return KEY_SHAPES.sub("[redacted]", text)


def timed(call: Callable[[], object]) -> float:
    """Wall milliseconds of one call."""
    started = time.perf_counter()
    call()
    return (time.perf_counter() - started) * 1000
