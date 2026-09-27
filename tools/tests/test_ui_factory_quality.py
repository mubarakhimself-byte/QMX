"""Profile runner: missing host, skip, and factory-selftest pass."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ui_factory.config import FactoryConfig
from ui_factory.quality import applicable_profiles, run_profiles


def _cfg(root: Path) -> FactoryConfig:
    return FactoryConfig(
        destination_branch="ui-integration",
        backend_branch="integration",
        repo_root=root,
        state_dir=root / "state",
        worktree_root=root / "wts",
        epic_globs=(),
        python_quality={},
        host_app_roots=("apps/host", "tools/ui_factory/fixtures/factory-test-app"),
        shared_serial_paths=("pnpm-lock.yaml",),
        max_parallel_epics=2,
        max_repair_rounds=3,
        ci_timeout_seconds=30,
        product_host="apps/qmx-ui",
        fixture_host="tools/ui_factory/fixtures/factory-test-app",
        required_ci_checks=("Skylos", "QA Battery", "UI quality"),
    )


def test_applicable_profiles_keep_python() -> None:
    names = applicable_profiles(
        Path("."),
        ["apps/qmx-ui/src/lib/Rail.svelte"],
        user_facing=True,
        needs_backend=True,
    )
    assert "python" in names
    assert "ui-reticle" in names
    assert "ui-playwright" in names
    assert "ui-contract" in names


def test_user_facing_without_files_still_requires_ui() -> None:
    names = applicable_profiles(
        Path("."),
        [],
        user_facing=True,
        needs_backend=False,
    )
    assert "ui-reticle" in names
    assert "ui-build" in names


def test_missing_host_is_incomplete(tmp_path: Path) -> None:
    fake = {
        "ui-lint": {
            "cwd": "host",
            "timeout_seconds": 5,
            "commands": [{"name": "lint", "argv": ["pnpm", "run", "lint"]}],
        }
    }
    with patch("ui_factory.quality.load_profiles", return_value=fake):
        record, ok, reason = run_profiles(
            config=_cfg(tmp_path),
            worktree=tmp_path,
            unit_id="ft-host",
            story_hash="h",
            candidate_sha="sha",
            profile_names=["ui-lint"],
            user_facing=False,
            evidence_dir=tmp_path / "ev",
            factory_mode="product",
        )
    assert ok is False
    assert record.commands[0].missing_tool is True
    assert "missing" in reason


def test_user_facing_without_reticle_is_not_ok(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    record, ok, reason = run_profiles(
        config=_cfg(tmp_path),
        worktree=tmp_path,
        unit_id="ft-ret",
        story_hash="h",
        candidate_sha="sha",
        profile_names=["factory-selftest"],
        user_facing=True,
        evidence_dir=tmp_path / "ev",
        factory_mode="fixture",
    )
    assert ok is False
    assert "Reticle" in reason or "reticle" in reason.lower()
    assert record.reticle_verdict == "missing"


def test_factory_selftest_profile_passes(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    record, ok, reason = run_profiles(
        config=_cfg(tmp_path),
        worktree=tmp_path,
        unit_id="ft-self",
        story_hash="h",
        candidate_sha="sha",
        profile_names=["factory-selftest"],
        user_facing=False,
        evidence_dir=tmp_path / "ev",
    )
    assert ok is True, reason
    assert record.commands[0].exit_code == 0


def test_backend_wait_on_unmerged_feat(tmp_path: Path) -> None:
    from ui_factory.validate_inputs import validate_inputs

    folder = tmp_path / "_bmad-output" / "planning-artifacts"
    folder.mkdir(parents=True)
    (folder / "epics-UI.md").write_text(
        """### Epic 71: Pairing (H)
**Feature:** FEAT-0066
**Notes:** Blocked by FEAT-0065
**Components:** COMP-QMA-DAEMON

### Story 71.1: Pairing proof
As an operator I want to pair.

**Traceability:** ADR-0026, SCN-0028
**Acceptance Criteria:**
**Given** a stopped daemon
**When** I pair
**Then** Origin never issues a proof
**Design:** docs/lenses/ui/screens/bootstrap.md
**Components:** COMP-QMA-DAEMON
**Needs:** FEAT-0065
""",
        encoding="utf-8",
    )
    cfg = _cfg(tmp_path)
    object.__setattr__(cfg, "epic_globs", ("_bmad-output/planning-artifacts/epics-UI.md",))
    report = validate_inputs(cfg, merged_features=set())
    assert report.status == "waiting_for_backend"
    assert any("FEAT-0065" in w for w in report.waiting)
