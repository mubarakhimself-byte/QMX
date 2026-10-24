"""Shared plumbing for the data round's PC probes.

Two things every probe here needs and neither should re-invent:

* one scratch root, `D:/Temp/prb-dp` unless `QMX_PROBE_SCRATCH` says otherwise, removed
  when the probe finishes (DATA-PLAN lane 7 checks that it is gone);
* one verdict shape, so a probe's log quotes the same words its `FINDINGS.md` row does.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

PASSED: Final[str] = "PASS"
FAILED: Final[str] = "FAIL"

SCRATCH: Final[Path] = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/prb-dp"))


def scratch_folder(probe: str) -> Path:
    """The probe's own folder under the scratch root, created if missing."""
    path = SCRATCH / probe
    path.mkdir(parents=True, exist_ok=True)
    return path


def drop_scratch() -> None:
    """Remove the scratch root. Idempotent, so either probe may be run first."""
    shutil.rmtree(SCRATCH, ignore_errors=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def package_version(name: str) -> str:
    """Installed version of `name`, or `absent` when the environment lacks it."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "absent"


@dataclass(slots=True)
class Report:
    """One probe's verdict and the numbers its FINDINGS row quotes.

    `problems` is empty exactly when the verdict is PASS; `details` carries the
    per-column or per-source lines a FAIL row needs in order to name what differed.
    """

    probe: str
    verdict: str = PASSED
    numbers: dict[str, object] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.details.append(text)

    def fail(self, problem: str) -> None:
        self.problems.append(problem)
        self.verdict = FAILED

    def render(self) -> int:
        print(f"{self.probe} {self.verdict}")
        for key, value in self.numbers.items():
            print(f"  {key}: {value}")
        for detail in self.details:
            print(f"  {detail}")
        for problem in self.problems:
            print(f"  problem: {problem}")
        return 0 if self.verdict == PASSED else 1
