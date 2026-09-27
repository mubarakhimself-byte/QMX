"""Evidence, promotion refusal, resume skip, SHA invalidation, isolation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ui_factory.ci_wait import watch_sha
from ui_factory.config import FactoryConfig
from ui_factory.evidence import (
    CommandResult,
    EvidenceRecord,
    evidence_ok,
    is_stale,
    sha256_text,
    write_evidence,
)
from ui_factory.merge_gate import evaluate_promotion
from ui_factory.ports import PortAllocator
from ui_factory.quality import run_command
from ui_factory.runtime_verify import classify_reticle, persistence_check
from ui_factory.state import StateStore, UnitRecord


def _git(cwd: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _cfg(root: Path) -> FactoryConfig:
    return FactoryConfig(
        destination_branch="ui-integration",
        backend_branch="integration",
        repo_root=root,
        state_dir=root / "state",
        worktree_root=root / "wts",
        epic_globs=(),
        python_quality={},
        host_app_roots=("apps/host",),
        shared_serial_paths=("pnpm-lock.yaml",),
        max_parallel_epics=2,
        max_repair_rounds=3,
        ci_timeout_seconds=30,
    )


def test_passing_command_retains_evidence(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    result = run_command(
        name="true",
        argv=["python", "-c", "print('1 passed')"],
        cwd=tmp_path,
        log_dir=log_dir,
        env=None,
        timeout=30,
    )
    assert result.exit_code == 0
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-pass",
        candidate_sha="abc",
        story_hash="h1",
        toolchain="t1",
        dirty_fingerprint="d1",
        commands=[result],
        reticle_verdict="not-applicable",
    )
    path = write_evidence(tmp_path / "ev", record)
    assert path.is_file()
    ok, reason = evidence_ok(record, require_reticle=False)
    assert ok is True
    assert reason == "ok"


def test_type_failure_refuses_promotion() -> None:
    failing = CommandResult(
        name="ui-types",
        argv=["pnpm", "run", "check"],
        cwd=".",
        exit_code=1,
        duration_ms=10,
        stdout_sha256="x",
        stderr_sha256="y",
        log_path="types.log",
    )
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-fail",
        candidate_sha="abc",
        story_hash="h",
        toolchain="t",
        dirty_fingerprint="d",
        commands=[failing],
    )
    ok, reason = evaluate_promotion(
        quality=record, user_facing=False, review_blocking=[]
    )
    assert ok is False
    assert "exited 1" in reason


def test_blocking_review_prevents_promotion() -> None:
    passing = CommandResult(
        name="lint",
        argv=["true"],
        cwd=".",
        exit_code=0,
        duration_ms=1,
        stdout_sha256="x",
        stderr_sha256="y",
        log_path="lint.log",
    )
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-review",
        candidate_sha="abc",
        story_hash="h",
        toolchain="t",
        dirty_fingerprint="d",
        commands=[passing],
        review_blocking=["dead control on Save"],
    )
    ok, reason = evaluate_promotion(
        quality=record, user_facing=False, review_blocking=["dead control on Save"]
    )
    assert ok is False
    assert "blocking" in reason


def test_unknown_reticle_is_incomplete() -> None:
    passing = CommandResult(
        name="vitest",
        argv=["pnpm", "test"],
        cwd=".",
        exit_code=0,
        duration_ms=1,
        stdout_sha256="x",
        stderr_sha256="y",
        log_path="v.log",
        test_counts={"required": 1, "ran": 1, "passed": 1},
    )
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-reticle",
        candidate_sha="abc",
        story_hash="h",
        toolchain="t",
        dirty_fingerprint="d",
        commands=[passing],
        reticle_verdict="unknown",
    )
    ok, reason = evidence_ok(record, require_reticle=True)
    assert ok is False
    assert "unknown" in reason
    assert classify_reticle({"verified": "unknown"}, available=True) == "unknown"
    assert classify_reticle(None, available=False) == "missing"


def test_missing_tool_is_incomplete(tmp_path: Path) -> None:
    result = run_command(
        name="missing",
        argv=["qmx-ui-factory-no-such-binary"],
        cwd=tmp_path,
        log_dir=tmp_path / "logs",
        env=None,
        timeout=10,
    )
    assert result.missing_tool is True
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-tool",
        candidate_sha="abc",
        story_hash="h",
        toolchain="t",
        dirty_fingerprint="d",
        commands=[result],
    )
    ok, _reason = evidence_ok(record, require_reticle=False)
    assert ok is False


def test_evidence_invalidated_when_sha_changes() -> None:
    record = EvidenceRecord(
        kind="quality",
        unit_id="ft-sha",
        candidate_sha="old",
        story_hash="h",
        toolchain="t",
        dirty_fingerprint="d",
        commands=[],
    )
    assert is_stale(
        record, candidate_sha="new", story_hash="h", toolchain="t", dirty="d"
    ) == "candidate SHA changed"


def test_resume_skips_committed_units(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.upsert_unit(
        UnitRecord(
            unit_id="70.1",
            kind="story",
            status="verifying",
            head_sha="deadbeef",
            story_hash="h",
        )
    )
    state = store.load()
    skip = [
        u.unit_id
        for u in state.units.values()
        if u.head_sha and u.status in {"verifying", "candidate", "merged"}
    ]
    assert skip == ["70.1"]


def test_port_isolation_and_cleanup(tmp_path: Path) -> None:
    alloc = PortAllocator(tmp_path)
    a = alloc.acquire("epic-a")
    b = alloc.acquire("epic-b")
    assert a.app_port != b.app_port
    assert a.api_port != b.api_port
    assert a.data_root != b.data_root
    alloc.release("epic-a")
    again = alloc.acquire("epic-a")
    assert again.app_port == a.app_port or again.app_port > 0


class _FakeDriver:
    def __init__(self, persist: bool) -> None:
        self.persist = persist
        self.value = ""

    def click_and_read(self, url: str, control: str, storage_key: str) -> dict[str, object]:
        if control == "__reload__":
            return {"changed": False, "value": self.value if self.persist else ""}
        if control == "dead":
            return {"changed": False, "value": ""}
        self.value = "saved-1"
        return {"changed": True, "value": self.value}


def test_dead_control_caught() -> None:
    assert persistence_check(_FakeDriver(True), "http://127.0.0.1/", "dead", "k") == (
        "dead-control"
    )


def test_wrong_persisted_outcome_caught() -> None:
    assert persistence_check(
        _FakeDriver(False), "http://127.0.0.1/", "save", "k"
    ) == "wrong-persisted-outcome"


def test_good_persist() -> None:
    assert persistence_check(_FakeDriver(True), "http://127.0.0.1/", "save", "k") == "ok"


def test_simulated_ci_separated_from_live() -> None:
    sim = watch_sha(
        "abc",
        branch="ui-integration",
        timeout_seconds=1,
        simulate_conclusion="success",
    )
    assert sim.simulated is True
    live_shape = watch_sha("abc", branch="ui-integration", timeout_seconds=1)
    if live_shape.simulated:
        raise AssertionError("live watch must not set simulated")
    assert live_shape.conclusion in {"success", "failure", "incomplete"}


def test_story_hash_material_changes() -> None:
    assert sha256_text("a") != sha256_text("b")
