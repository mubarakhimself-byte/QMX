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
    def runs(self) -> Path:
        """Per-run temp and data folders the timed wrapper makes and deletes."""
        return self.dir / "runs"

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

    def quality(self, tip: str) -> Path:
        return self.checks_root / "_quality" / tip[:8]

    def landing(self, batch: str) -> Path:
        return self.checks_root / "_land" / batch

    def heartbeat(self, slice_id: str) -> Path:
        return self.dir / "heartbeat" / slice_id

    def verdict(self, slice_id: str, head: str) -> Path:
        return self.review_dir / f"{slice_id}-{head[:8]}.md"

    def range_verdict(self, slice_id: str, patch_id: str) -> Path:
        return self.review_dir / f"{slice_id}-range-{patch_id[:8]}.md"

    @property
    def project_file(self) -> Path:
        """PROGRAM.yaml, the program's one index (ship.program reads it)."""
        return self.dir / "PROGRAM.yaml"

    @property
    def phase_file(self) -> Path:
        """phase.json, written only by `ship phase --set`."""
        return self.dir / "phase.json"

    @property
    def chain_lock(self) -> Path:
        """One conveyor per program; alive while its pid runs."""
        return self.dir / "chain.lock"

    @property
    def waiting(self) -> Path:
        """Questions for him while a planning gate is open, as `- [ ]` lines."""
        return self.dir / "WAITING.md"

    @property
    def waits(self) -> Path:
        """Questions for him during the run, as `- [ ]` lines."""
        return self.notes_dir / "WAITS-ON-YOU.md"

    @property
    def workers(self) -> Path:
        """One folder per headless run."""
        return self.dir / "workers"

    def stop_note(self, stop: str) -> Path:
        """Written by `ship run` when a stop is built: from, tip, landed, parked."""
        return self.notes_dir / f"stop-{stop}.json"

    def stop_review(self, stop: str) -> Path:
        return self.dir / "stop-review" / stop

    def merge_note(self, stop: str) -> Path:
        return self.dir / "merge" / f"{stop}.md"

    @property
    def kit_dir(self) -> Path:
        """`.kit/`: files only the kit writes; the hook refuses every worker role there (D-L22)."""
        return self.dir / ".kit"

    def review_run(self, stop: str) -> Path:
        """`ship review`'s bookkeeping for a stop; its `result` 0 and `tip` are what `ship merge` trusts."""
        return self.kit_dir / stop / "review-run.json"

    def merge_base(self, stop: str) -> Path:
        """The merge commit of the target `ship merge` pushed onto the build branch, one 40-char sha."""
        return self.kit_dir / stop / "MERGE-BASE"

    @property
    def gates_log(self) -> Path:
        """One JSON line per `ship gate`; PROGRAM.yaml's gates must equal the log's last word on each."""
        return self.kit_dir / "gates.log"


@dataclasses.dataclass(frozen=True)
class Records:
    """The shared records on branch `plans`, under `<plans>/_records/`."""

    dir: Path

    @property
    def backlog(self) -> Path:
        return self.dir / "BACKLOG.tsv"

    @property
    def backlog_md(self) -> Path:
        return self.dir / "BACKLOG.md"

    @property
    def removed(self) -> Path:
        return self.dir / "REMOVED.md"

    @property
    def prefixes(self) -> Path:
        return self.dir / "PREFIXES.md"

    @property
    def claims(self) -> Path:
        return self.dir / "CLAIMS.tsv"

    @property
    def lock(self) -> Path:
        return self.dir / "records.lock"


def records_of(plans: Path) -> Records:
    return Records(plans / "_records")
