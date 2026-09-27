"""UI merge gate. Destination is config.destination_branch, never main."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from ui_factory.config import FactoryConfig
from ui_factory.evidence import EvidenceRecord, evidence_ok
from ui_factory.quality import applicable_profiles, run_profiles


class MergeBlocked(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class MergeResult:
    merged: bool
    destination: str
    branch: str
    sha: str
    reason: str


def _git(
    worktree: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=check,
    )


def current_sha(worktree: Path) -> str:
    proc = _git(worktree, ["rev-parse", "HEAD"])
    return proc.stdout.strip()


def rebase_onto_destination(worktree: Path, dest: str) -> None:
    fetch = _git(worktree, ["fetch", "origin", dest], check=False)
    if fetch.returncode != 0:
        # Destination may exist only locally during factory tests.
        local = _git(worktree, ["rev-parse", "--verify", dest], check=False)
        if local.returncode != 0:
            raise MergeBlocked(f"destination {dest} is missing locally and on origin")
        onto = dest
    else:
        onto = f"origin/{dest}"
    rebase = _git(worktree, ["rebase", onto], check=False)
    if rebase.returncode != 0:
        _git(worktree, ["rebase", "--abort"], check=False)
        raise MergeBlocked(
            "rebase conflict: "
            + (rebase.stdout or "")
            + (rebase.stderr or "")
        )


def ff_merge(
    *,
    repo: Path,
    dest: str,
    branch: str,
    tmp: Path,
) -> None:
    if tmp.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tmp)],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    add = subprocess.run(
        ["git", "worktree", "add", str(tmp), dest],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if add.returncode != 0:
        raise MergeBlocked(add.stderr or "worktree add failed")
    try:
        merge = _git(tmp, ["merge", "--ff-only", branch], check=False)
        if merge.returncode != 0:
            raise MergeBlocked(
                "ff-only merge refused: " + (merge.stderr or merge.stdout)
            )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(tmp)],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )


def evaluate_promotion(
    *,
    quality: EvidenceRecord,
    user_facing: bool,
    review_blocking: list[str],
) -> tuple[bool, str]:
    if review_blocking:
        return False, "blocking review findings"
    return evidence_ok(quality, require_reticle=user_facing)


def run_merge_gate(
    *,
    config: FactoryConfig,
    worktree: Path,
    branch: str,
    unit_id: str,
    story_hash: str,
    changed_files: list[str],
    user_facing: bool,
    needs_backend: bool,
    evidence_dir: Path,
    review_blocking: list[str],
    push: bool,
) -> MergeResult:
    dest = config.destination_branch
    if dest == config.backend_branch:
        raise MergeBlocked("refusing to merge UI work onto the backend branch")
    if dest == "main":
        raise MergeBlocked("refusing to merge onto main")
    rebase_onto_destination(worktree, dest)
    sha = current_sha(worktree)
    names = applicable_profiles(
        worktree,
        changed_files,
        user_facing=user_facing,
        needs_backend=needs_backend,
    )
    record, ok, reason = run_profiles(
        config=config,
        worktree=worktree,
        unit_id=unit_id,
        story_hash=story_hash,
        candidate_sha=sha,
        profile_names=names,
        user_facing=user_facing,
        evidence_dir=evidence_dir,
    )
    record.review_blocking = list(review_blocking)
    if review_blocking:
        ok = False
        reason = "blocking review findings"
    if not ok:
        return MergeResult(
            merged=False,
            destination=dest,
            branch=branch,
            sha=sha,
            reason=reason,
        )
    tmp = config.worktree_root / config.merge_tmp_name
    ff_merge(repo=config.repo_root, dest=dest, branch=branch, tmp=tmp)
    if push:
        pushed = subprocess.run(
            ["git", "push", "origin", dest],
            cwd=config.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if pushed.returncode != 0:
            return MergeResult(
                merged=True,
                destination=dest,
                branch=branch,
                sha=sha,
                reason="merged locally; origin push failed: "
                + (pushed.stderr or pushed.stdout),
            )
    return MergeResult(
        merged=True,
        destination=dest,
        branch=branch,
        sha=sha,
        reason="ff-merged to " + dest,
    )
