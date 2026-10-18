"""The E23 task set: ten small coding and data tasks.

Each task is a folder `NN-slug/` with `prompt.md`, an optional `seed/` copied into the work
folder before the agent starts, a `reference/` answer laid over the seed, and `check.py`, run as
`python check.py <work folder>`, which exits 0 when the folder holds a right answer.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Task:
    slug: str
    folder: Path

    @property
    def prompt(self) -> str:
        return (self.folder / "prompt.md").read_text(encoding="utf-8").strip()

    def seed(self, work: Path) -> None:
        """Make `work` the task's starting folder: empty, then the seed files."""
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        if (self.folder / "seed").is_dir():
            shutil.copytree(self.folder / "seed", work, dirs_exist_ok=True)

    def check(self, work: Path) -> tuple[bool, str]:
        """Run the checker on `work`; returns pass and its message."""
        done = subprocess.run(
            [sys.executable, str(self.folder / "check.py"), str(work)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return done.returncode == 0, (done.stderr or done.stdout).strip()[-300:]


def load() -> list[Task]:
    return [Task(p.name, p) for p in sorted(ROOT.iterdir()) if (p / "check.py").is_file()]
