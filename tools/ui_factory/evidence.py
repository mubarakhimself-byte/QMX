"""Command-backed evidence records. Agent passed=true is never enough."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dirty_fingerprint(worktree: Path) -> str:
    """Cheap dirty-tree fingerprint: tracked status bytes, not a git write."""
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    )
    return sha256_text(proc.stdout or "")


@dataclass
class CommandResult:
    name: str
    argv: list[str]
    cwd: str
    exit_code: int
    duration_ms: int
    stdout_sha256: str
    stderr_sha256: str
    log_path: str
    test_counts: dict[str, int] = field(default_factory=dict)
    skipped: bool = False
    missing_tool: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.skipped and not self.missing_tool


@dataclass
class EvidenceRecord:
    kind: str
    unit_id: str
    candidate_sha: str
    story_hash: str
    toolchain: str
    dirty_fingerprint: str
    commands: list[CommandResult]
    reticle_verdict: str = ""  # yes | no | unknown | missing | not-applicable
    review_blocking: list[str] = field(default_factory=list)
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceRecord:
        commands: list[CommandResult] = []
        for item in data.get("commands") or []:
            if isinstance(item, dict):
                commands.append(
                    CommandResult(
                        name=str(item.get("name") or ""),
                        argv=[str(a) for a in (item.get("argv") or [])],
                        cwd=str(item.get("cwd") or ""),
                        exit_code=int(item.get("exit_code") or 1),
                        duration_ms=int(item.get("duration_ms") or 0),
                        stdout_sha256=str(item.get("stdout_sha256") or ""),
                        stderr_sha256=str(item.get("stderr_sha256") or ""),
                        log_path=str(item.get("log_path") or ""),
                        test_counts={
                            str(k): int(v)
                            for k, v in (item.get("test_counts") or {}).items()
                        },
                        skipped=bool(item.get("skipped")),
                        missing_tool=bool(item.get("missing_tool")),
                    )
                )
        return cls(
            kind=str(data.get("kind") or ""),
            unit_id=str(data.get("unit_id") or ""),
            candidate_sha=str(data.get("candidate_sha") or ""),
            story_hash=str(data.get("story_hash") or ""),
            toolchain=str(data.get("toolchain") or ""),
            dirty_fingerprint=str(data.get("dirty_fingerprint") or ""),
            commands=commands,
            reticle_verdict=str(data.get("reticle_verdict") or ""),
            review_blocking=[str(x) for x in (data.get("review_blocking") or [])],
            created_at=str(data.get("created_at") or ""),
            notes=str(data.get("notes") or ""),
        )


def evidence_ok(record: EvidenceRecord, *, require_reticle: bool) -> tuple[bool, str]:
    if not record.commands:
        return False, "no command results recorded"
    if record.candidate_sha == "":
        return False, "candidate SHA missing"
    for cmd in record.commands:
        if cmd.missing_tool:
            return False, f"missing tool: {cmd.name}"
        if cmd.skipped:
            return False, f"required check skipped: {cmd.name}"
        if cmd.exit_code != 0:
            return False, f"{cmd.name} exited {cmd.exit_code}"
        counts = cmd.test_counts
        if "required" in counts and counts["required"] > 0:
            ran = counts.get("ran", 0)
            if ran == 0:
                return False, f"{cmd.name} ran zero required tests"
    if require_reticle:
        if record.reticle_verdict in ("", "missing"):
            return False, "Reticle evidence missing"
        if record.reticle_verdict == "unknown":
            return False, "Reticle verdict unknown is not a pass"
        if record.reticle_verdict != "yes":
            return False, f"Reticle verdict {record.reticle_verdict}"
    if record.review_blocking:
        return False, "blocking review findings present"
    return True, "ok"


def is_stale(
    record: EvidenceRecord,
    *,
    candidate_sha: str,
    story_hash: str,
    toolchain: str,
    dirty: str,
) -> str:
    if record.candidate_sha != candidate_sha:
        return "candidate SHA changed"
    if record.story_hash != story_hash:
        return "story hash changed"
    if toolchain not in (record.toolchain, ""):
        return "toolchain fingerprint changed"
    if record.dirty_fingerprint != dirty:
        return "worktree dirty fingerprint changed"
    return ""


def write_evidence(directory: Path, record: EvidenceRecord) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    if record.created_at == "":
        record.created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    path = directory / f"{record.kind}-{record.unit_id}.json"
    path.write_text(json.dumps(record.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def read_evidence(path: Path) -> EvidenceRecord:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"corrupt evidence {path}")
    return EvidenceRecord.from_dict(raw)


def write_command_log(directory: Path, name: str, stdout: str, stderr: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.log"
    path.write_text(
        f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n",
        encoding="utf-8",
    )
    return path


def toolchain_fingerprint(pairs: Sequence[tuple[str, str]]) -> str:
    blob = "\n".join(f"{k}={v}" for k, v in pairs)
    return sha256_text(blob)


def current_pid() -> int:
    return os.getpid()
