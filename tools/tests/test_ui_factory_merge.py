"""Merge gate writes only to the UI destination branch."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from ui_factory.config import load_config
from ui_factory.merge_gate import MergeBlocked, ff_merge, rebase_onto_destination


def _git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, ["init", "-b", "main"])
    _git(repo, ["config", "user.name", "Mubarak"])
    _git(repo, ["config", "user.email", "himselfmubarak@gmail.com"])
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, ["add", "README.md"])
    _git(repo, ["commit", "-m", "base"])
    _git(repo, ["branch", "ui-integration"])
    _git(repo, ["branch", "integration"])
    _git(repo, ["checkout", "-b", "ui-epic/70-shell"])
    (repo / "note.txt").write_text("story\n", encoding="utf-8")
    _git(repo, ["add", "note.txt"])
    _git(repo, ["commit", "-m", "story 70.1: factory test"])
    return repo


def test_config_destination_is_not_integration() -> None:
    cfg = load_config()
    assert cfg.destination_branch == "ui-integration"
    assert cfg.destination_branch != cfg.backend_branch
    assert cfg.destination_branch != "integration"
    assert cfg.destination_branch != "main"


def test_ff_merge_lands_on_ui_integration(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    tmp = tmp_path / "merge-tmp"
    ff_merge(
        repo=repo,
        dest="ui-integration",
        branch="ui-epic/70-shell",
        tmp=tmp,
    )
    dest_has = _git(repo, ["log", "ui-integration", "--oneline"])
    backend = _git(repo, ["log", "integration", "--oneline"])
    assert "story 70.1" in dest_has.stdout
    assert "story 70.1" not in backend.stdout


def test_rebase_conflict_blocks(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, ["checkout", "ui-integration"])
    (repo / "note.txt").write_text("dest\n", encoding="utf-8")
    _git(repo, ["add", "note.txt"])
    _git(repo, ["commit", "-m", "dest change"])
    _git(repo, ["checkout", "ui-epic/70-shell"])
    with pytest.raises(MergeBlocked):
        rebase_onto_destination(repo, "ui-integration")
