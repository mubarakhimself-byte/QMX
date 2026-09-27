"""UI merge gate. Destination is config.destination_branch, never main."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ui_factory.ci_wait import REQUIRED_CHECKS, watch_sha
from ui_factory.config import FactoryConfig
from ui_factory.evidence import EvidenceRecord, evidence_ok
from ui_factory.gitops import destination_checkout, git
from ui_factory.lock import FileLock
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
    ci: str = ""


def current_sha(worktree: Path) -> str:
    proc = git(worktree, ["rev-parse", "HEAD"])
    return proc.stdout.strip()


def rebase_onto_destination(worktree: Path, dest: str) -> None:
    fetch = git(worktree, ["fetch", "origin", dest])
    if fetch.returncode != 0:
        local = git(worktree, ["rev-parse", "--verify", dest])
        if local.returncode != 0:
            raise MergeBlocked(f"destination {dest} is missing locally and on origin")
        onto = dest
    else:
        onto = f"origin/{dest}"
    rebase = git(worktree, ["rebase", onto])
    if rebase.returncode != 0:
        git(worktree, ["rebase", "--abort"])
        raise MergeBlocked(
            "rebase conflict: " + (rebase.stdout or "") + (rebase.stderr or "")
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


def _merge_ff(dest_path: Path, branch: str) -> None:
    merge = git(dest_path, ["merge", "--ff-only", branch])
    if merge.returncode != 0:
        raise MergeBlocked("ff-only merge refused: " + (merge.stderr or merge.stdout))


def ff_merge(
    *,
    repo: Path,
    dest: str,
    branch: str,
    tmp: Path,
    lease: Path,
) -> None:
    occupied = destination_checkout(repo, dest)
    if occupied is not None:
        _merge_ff(occupied, branch)
        return
    owner = f"pid:{os.getpid()}:{branch}"
    if tmp.exists():
        if not lease.is_file() or lease.read_text(encoding="utf-8").strip() != owner:
            raise MergeBlocked(
                f"merge temp {tmp} exists and is not owned by this factory run"
            )
        subprocess.run(
            ["git", "worktree", "remove", str(tmp)],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text(owner, encoding="utf-8")
    add = subprocess.run(
        ["git", "worktree", "add", str(tmp), dest],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if add.returncode != 0:
        lease.unlink(missing_ok=True)
        raise MergeBlocked(add.stderr or "worktree add failed")
    try:
        _merge_ff(tmp, branch)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(tmp)],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        lease.unlink(missing_ok=True)


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
    factory_mode: str = "product",
    wait_ci: bool = True,
    reticle: dict[str, str] | None = None,
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
    record, _ok, _reason = run_profiles(
        config=config,
        worktree=worktree,
        unit_id=unit_id,
        story_hash=story_hash,
        candidate_sha=sha,
        profile_names=names,
        user_facing=user_facing,
        evidence_dir=evidence_dir,
        factory_mode=factory_mode,
        reticle=reticle,
    )
    record.review_blocking = list(review_blocking)
    ok, reason = evaluate_promotion(
        quality=record,
        user_facing=user_facing,
        review_blocking=review_blocking,
    )
    if not ok:
        return MergeResult(False, dest, branch, sha, reason)
    ci_note = "ci not required for fixture local promotion"
    if wait_ci:
        if factory_mode != "product":
            ci_note = "fixture mode: GitHub CI not used for promotion"
        else:
            watch = watch_sha(
                sha,
                branch=branch,
                timeout_seconds=config.ci_timeout_seconds,
                required=list(config.required_ci_checks or REQUIRED_CHECKS),
            )
            ci_note = watch.conclusion + ": " + watch.detail
            if watch.simulated:
                raise MergeBlocked("simulated CI cannot promote")
            if watch.conclusion != "success":
                return MergeResult(
                    False, dest, branch, sha, "CI incomplete: " + watch.detail, ci_note
                )
            dest_now = git(worktree, ["rev-parse", dest])
            origin = git(worktree, ["rev-parse", f"origin/{dest}"])
            if origin.returncode == 0 and dest_now.stdout.strip() != origin.stdout.strip():
                return MergeResult(
                    False,
                    dest,
                    branch,
                    sha,
                    "destination moved during CI; rebase and re-run",
                    ci_note,
                )
    lock_path = config.state_dir / "promote.lock"
    with FileLock(lock_path):
        tmp = config.worktree_root / config.merge_tmp_name
        lease = config.state_dir / f"{config.merge_tmp_name}.lease"
        ff_merge(repo=config.repo_root, dest=dest, branch=branch, tmp=tmp, lease=lease)
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
                    True,
                    dest,
                    branch,
                    sha,
                    "merged locally; origin push failed: "
                    + (pushed.stderr or pushed.stdout),
                    ci_note,
                )
    return MergeResult(True, dest, branch, sha, "ff-merged to " + dest, ci_note)
