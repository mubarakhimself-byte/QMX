"""verify_ready: run when a builder replies READY <sha>. Six checks, then the PR with an explicit base.

1. the remote slice branch equals the reported sha;
2. the sha descends from the slice's parent;
3. the diff from the parent is not empty;
4. each required evidence file ends `END <sha> <dispatch id>`;
5. the builder's PR body `pr.md` holds `TRACE: <slice> -> <plan ids> -> <ask>`, ending in the slice's
   ask when SLICES.md names one, and neither it nor any commit message carries a credit line;
6. the changed files match the brief's files, and none overlaps another in-flight slice.

Any failure moves the slice to `red` (BLOCKED). On success the script opens the PR (or adopts the open
one), confirms its base is the build branch and its head is the sha, and moves the slice to `ready`.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from ship import state as st
from ship.evidence import body_without_end, end_problem
from ship.gitx import GitError, changed_files, git, is_ancestor, remote_sha, run
from ship.layout import Program
from ship.plan import outside, overlaps
from ship.settings import Settings
from ship.state import IN_FLIGHT, Status


def problems(program: Program, state: st.State, slice_id: str, sha: str, settings: Settings) -> list[str]:
    sl = state.slices[slice_id]
    repo = Path(state.repo)
    t = settings.git_timeout_s
    found = []
    pushed = remote_sha(repo, state.remote, sl.branch, t)
    if pushed != sha:
        return [f"remote {sl.branch} is {pushed}, the builder reported {sha}"]
    git(repo, "fetch", "-q", state.remote, f"+refs/heads/{sl.branch}:refs/remotes/{state.remote}/{sl.branch}",
        timeout=t)
    if not sl.parent or not is_ancestor(repo, sl.parent, sha, t):
        found.append(f"{sha[:8]} does not descend from the parent {str(sl.parent)[:8]}")
        return found
    files = changed_files(repo, sl.parent, sha, t)
    if not files:
        found.append("the diff from the parent is empty")
    evidence = program.evidence(slice_id, sl.attempts)
    for name in settings.evidence_required:
        problem = end_problem(evidence / name, sha, sl.holder.dispatch_id)
        if problem:
            found.append(f"evidence {problem}")
    found += pr_problems(evidence / "pr.md", sl)
    for line in git(repo, "log", "--format=%H%x09%B%x00", f"{sl.parent}..{sha}", timeout=t).split("\0"):
        short, _, body = line.strip().partition("\t")
        found += [f"commit {short[:8]}: credit line {c!r}" for c in credit_lines(body)]
    extra = outside(sl.files, files)
    if extra:
        found.append(f"files outside the brief: {extra}")
    for other in state.slices.values():
        if other.id != slice_id and other.status in IN_FLIGHT:
            clash = overlaps(files, other.files)
            if clash:
                found.append(f"changed files overlap in-flight {other.id}: {clash}")
    return found


CREDIT = re.compile(r"co-authored-by:|generated with", re.I)


def credit_lines(text: str) -> list[str]:
    """Model or tool credit lines. PRs and commits carry none."""
    return [ln.strip() for ln in text.splitlines() if CREDIT.search(ln)]


def pr_problems(path: Path, sl: st.Slice) -> list[str]:
    """The builder's PR body names its chain (`TRACE: <slice> -> <plan ids> -> <ask>`) and credits no model."""
    if not path.is_file():
        return []
    text = path.read_text("utf-8", errors="replace")
    found = []
    trace = [ln.strip() for ln in text.splitlines() if ln.strip().startswith(f"TRACE: {sl.id} -> ")]
    if not trace:
        found.append(f"pr.md: no line 'TRACE: {sl.id} -> <plan ids> -> <ask>'")
    elif sl.ask and trace[0].rsplit("->", 1)[-1].strip() != sl.ask:
        found.append(f"pr.md: TRACE ends in {trace[0].rsplit('->', 1)[-1].strip()!r}, the slice serves {sl.ask!r}")
    found += [f"pr.md: credit line {c!r}" for c in credit_lines(text)]
    return found


def _gh(settings: Settings, repo: Path, *args: str) -> str:
    return run([*settings.gh, *args], repo, settings.git_timeout_s).stdout


def open_pr(program: Program, state: st.State, slice_id: str, sha: str, settings: Settings) -> str:
    sl = state.slices[slice_id]
    repo = Path(state.repo)
    listed = json.loads(_gh(settings, repo, "pr", "list", "--head", sl.branch, "--state", "open",
                            "--json", "url,baseRefName,headRefOid") or "[]")
    if listed:
        url = listed[0]["url"]
    else:
        evidence = program.evidence(slice_id, sl.attempts)
        source = evidence / "pr.md" if (evidence / "pr.md").exists() else evidence / "report.md"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as body:
            body.write(body_without_end(source))
        try:
            url = _gh(settings, repo, "pr", "create", "--base", state.build_branch, "--head", sl.branch,
                      "--title", f"{slice_id}: {sl.name}", "--body-file", body.name).strip().splitlines()[-1]
        finally:
            Path(body.name).unlink(missing_ok=True)
    view = json.loads(_gh(settings, repo, "pr", "view", url, "--json", "baseRefName,headRefOid"))
    if view["baseRefName"] != state.build_branch:
        raise GitError(f"PR {url} targets {view['baseRefName']}, not {state.build_branch}")
    if view["headRefOid"] != sha:
        raise GitError(f"PR {url} head is {view['headRefOid']}, not {sha}")
    return url


def verify_ready(program: Program, slice_id: str, sha: str, settings: Settings) -> tuple[bool, list[str]]:
    with st.locked(program) as state:
        sl = state.slices[slice_id]
        if sl.status != Status.HELD or not sl.holder:
            return False, [f"{slice_id} is {sl.status}, not held"]
        found = problems(program, state, slice_id, sha, settings)
        if not found:
            try:
                sl.pr = open_pr(program, state, slice_id, sha, settings)
            except GitError as exc:
                found = [f"PR: {exc}"]
        if found:
            state.move(slice_id, Status.RED, "verify_ready: " + "; ".join(found))
            return False, found
        sl.head = sha
        state.move(slice_id, Status.READY, f"PR {sl.pr}")
        return True, [f"READY {slice_id} {sha} {sl.pr}"]
