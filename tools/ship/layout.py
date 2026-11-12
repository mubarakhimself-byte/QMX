"""Where every run-time file lives inside a program folder. Nothing else builds these paths."""

from __future__ import annotations

import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Program:
    dir: Path

    @property
    def state(self) -> Path:
        return self.dir / "state.json"

    @property
    def lock(self) -> Path:
        return self.dir / "state.lock"

    @property
    def armed(self) -> Path:
        return self.dir / "ARMED.md"

    @property
    def hold(self) -> Path:
        return self.dir / "HOLD"

    @property
    def power(self) -> Path:
        return self.dir / "power.json"

    @property
    def slices_md(self) -> Path:
        return self.dir / "SLICES.md"

    @property
    def checks_toml(self) -> Path:
        return self.dir / "checks.toml"

    @property
    def baseline_reds(self) -> Path:
        return self.dir / "baseline-reds.txt"

    @property
    def main_snapshot(self) -> Path:
        return self.dir / "main-status.txt"

    @property
    def report(self) -> Path:
        return self.dir / "RUN-REPORT.md"

    @property
    def leftovers(self) -> Path:
        return self.dir / "leftovers.md"

    @property
    def tmp(self) -> Path:
        return self.dir / "tmp"

    @property
    def review_dir(self) -> Path:
        return self.dir / "review"

    @property
    def notes_dir(self) -> Path:
        return self.dir / "notes"

    @property
    def evidence_root(self) -> Path:
        return self.dir / "evidence"

    @property
    def checks_root(self) -> Path:
        return self.dir / "checks"

    def brief(self, slice_id: str) -> Path:
        return self.dir / "slices" / slice_id / "BRIEF.md"

    def evidence(self, slice_id: str, attempt: int) -> Path:
        return self.evidence_root / slice_id / str(attempt)

    def checks(self, slice_id: str, head: str) -> Path:
        return self.checks_root / slice_id / head[:8]

    def nightly(self, tip: str) -> Path:
        return self.checks_root / "_nightly" / tip[:8]

    def landing(self, batch: str) -> Path:
        return self.checks_root / "_land" / batch

    def heartbeat(self, slice_id: str) -> Path:
        return self.dir / "heartbeat" / slice_id

    def verdict(self, slice_id: str, head: str) -> Path:
        return self.review_dir / f"{slice_id}-{head[:8]}.md"

    def range_verdict(self, slice_id: str, patch_id: str) -> Path:
        return self.review_dir / f"{slice_id}-range-{patch_id[:8]}.md"
