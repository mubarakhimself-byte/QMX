"""Bounded synthetic lifecycle for factory repair proof. Not product stories."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ui_factory.config import load_config
from ui_factory.evidence import read_evidence
from ui_factory.merge_gate import ff_merge
from ui_factory.quality import applicable_profiles, run_profiles
from ui_factory.state import StateStore, UnitRecord


def _git(cwd: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def run_synthetic(root: Path) -> dict[str, Any]:
    repo = root / "synth-repo"
    repo.mkdir(parents=True)
    _git(repo, ["init", "-b", "main"])
    _git(repo, ["config", "user.name", "Mubarak"])
    _git(repo, ["config", "user.email", "himselfmubarak@gmail.com"])
    (repo / "README.md").write_text("FACTORY-TEST\n", encoding="utf-8")
    _git(repo, ["add", "README.md"])
    _git(repo, ["commit", "-m", "base"])
    _git(repo, ["branch", "ui-integration"])
    _git(repo, ["checkout", "-b", "ui-epic/ft-1"])
    (repo / "note.txt").write_text("story\n", encoding="utf-8")
    _git(repo, ["add", "note.txt"])
    _git(repo, ["commit", "-m", "story ft.1: factory test"])
    _git(repo, ["checkout", "ui-integration"])
    cfg = load_config()
    evidence_dir = root / "evidence"
    names = applicable_profiles(
        repo, [], user_facing=True, needs_backend=False
    )
    _record, ok, reason = run_profiles(
        config=cfg,
        worktree=repo,
        unit_id="ft.1",
        story_hash="hash-ft.1",
        candidate_sha="deadbeef",
        profile_names=["factory-selftest"],
        user_facing=True,
        evidence_dir=evidence_dir,
        factory_mode="fixture",
    )
    reticle_blocked = (ok is False) and ("reticle" in reason.lower() or "Reticle" in reason)
    loaded = read_evidence(evidence_dir / "quality-ft.1.json")
    roundtrip_zero = loaded.commands[0].exit_code == 0
    store = StateStore(root / "state")
    store.upsert_unit(
        UnitRecord(
            unit_id="ft.1",
            kind="factory-test",
            status="verifying",
            head_sha="deadbeef",
            story_hash="hash-ft.1",
            worktree=str(repo),
        )
    )
    resumed = store.load().units["ft.1"].status == "verifying"
    ff_merge(
        repo=repo,
        dest="ui-integration",
        branch="ui-epic/ft-1",
        tmp=root / "merge-tmp",
        lease=root / "merge.lease",
    )
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    occupied_merged = "story ft.1" in log.stdout
    ui_required = "ui-reticle" in names
    report = {
        "reticle_blocked": reticle_blocked,
        "reason": reason,
        "roundtrip_zero": roundtrip_zero,
        "resumed": resumed,
        "occupied_merged": occupied_merged,
        "user_facing_profiles_include_reticle": ui_required,
        "evidence_path": str(evidence_dir / "quality-ft.1.json"),
        "factory_mode": "fixture",
        "product_host_used": False,
        "ci": "local synthetic; live GitHub not queried",
    }
    (root / "lifecycle.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
