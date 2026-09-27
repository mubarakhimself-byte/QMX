"""Persisted UI-factory state machine.

Statuses: queued, building, verifying, repairing, reviewing, candidate,
merged, blocked, failed, incomplete. A story commit is built, not verified.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ui_factory.lock import FileLock

VALID_STATUSES = (
    "queued",
    "building",
    "verifying",
    "repairing",
    "reviewing",
    "candidate",
    "merged",
    "blocked",
    "failed",
    "incomplete",
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class UnitRecord:
    unit_id: str
    kind: str  # epic | story | factory-test
    status: str
    story_hash: str = ""
    base_sha: str = ""
    head_sha: str = ""
    worktree: str = ""
    branch: str = ""
    workflow_name: str = ""
    evidence_dir: str = ""
    toolchain: str = ""
    owner_pid: int = 0
    repair_rounds: int = 0
    last_failure: str = ""
    failure_fingerprint: str = ""
    updated_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UnitRecord:
        status = str(data.get("status") or "queued")
        if status not in VALID_STATUSES:
            status = "incomplete"
        return cls(
            unit_id=str(data.get("unit_id") or ""),
            kind=str(data.get("kind") or "story"),
            status=status,
            story_hash=str(data.get("story_hash") or ""),
            base_sha=str(data.get("base_sha") or ""),
            head_sha=str(data.get("head_sha") or ""),
            worktree=str(data.get("worktree") or ""),
            branch=str(data.get("branch") or ""),
            workflow_name=str(data.get("workflow_name") or ""),
            evidence_dir=str(data.get("evidence_dir") or ""),
            toolchain=str(data.get("toolchain") or ""),
            owner_pid=int(data.get("owner_pid") or 0),
            repair_rounds=int(data.get("repair_rounds") or 0),
            last_failure=str(data.get("last_failure") or ""),
            failure_fingerprint=str(data.get("failure_fingerprint") or ""),
            updated_at=str(data.get("updated_at") or ""),
            notes=str(data.get("notes") or ""),
        )


@dataclass
class FactoryState:
    destination_branch: str
    base_sha: str
    units: dict[str, UnitRecord] = field(default_factory=dict)
    waiting_for_input: bool = False
    waiting_reason: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_branch": self.destination_branch,
            "base_sha": self.base_sha,
            "waiting_for_input": self.waiting_for_input,
            "waiting_reason": self.waiting_reason,
            "updated_at": self.updated_at,
            "units": {k: v.to_dict() for k, v in self.units.items()},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FactoryState:
        units_raw = data.get("units") or {}
        units: dict[str, UnitRecord] = {}
        if isinstance(units_raw, dict):
            for key, value in units_raw.items():
                if isinstance(value, dict):
                    units[str(key)] = UnitRecord.from_dict(value)
        return cls(
            destination_branch=str(data.get("destination_branch") or ""),
            base_sha=str(data.get("base_sha") or ""),
            units=units,
            waiting_for_input=bool(data.get("waiting_for_input")),
            waiting_reason=str(data.get("waiting_reason") or ""),
            updated_at=str(data.get("updated_at") or ""),
        )


class StateStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / "state.json"
        self._lock_path = directory / "state.lock"

    def load(self) -> FactoryState:
        if not self.path.is_file():
            return FactoryState(destination_branch="", base_sha="")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"corrupt state at {self.path}")
        return FactoryState.from_dict(raw)

    def save(self, state: FactoryState) -> None:
        state.updated_at = _now()
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def update(self, mutator: Any) -> FactoryState:
        with FileLock(self._lock_path):
            state = self.load()
            mutator(state)
            self.save(state)
            return state

    def upsert_unit(self, record: UnitRecord) -> FactoryState:
        record.updated_at = _now()

        def _apply(state: FactoryState) -> None:
            state.units[record.unit_id] = record

        return self.update(_apply)
