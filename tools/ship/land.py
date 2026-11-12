"""land: put a batch of checked, reviewed slices on the build branch.

In a detached landing copy at the build tip, each slice in dependency order is squashed into one
commit. A uv.lock conflict is resolved by regenerating the lock, never by hand-merging. The slice's
review carries over only when its `git patch-id` is unchanged and no file it touches was changed by
a slice that landed after its dispatch; otherwise the script writes the range-diff and waits for a
range verdict. Then it runs the tests of every package the batch and the slices landed since touched,
blocks only on reds missing from baseline-reds.txt, fast-forwards the build branch, rewrites the
baseline, marks the slices landed, closes their PRs, and removes each slice worktree once its remote
branch equals its local head (never --force).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path, PurePosixPath

from ship import state as st
from ship.evidence import verdict_problem
from ship.gitx import GitError, changed_files, git, git_rc, patch_id, remote_sha, run
from ship.layout import Program
from ship.settings import Settings
from ship.state import Status
from ship.suite import load_packages, read_baseline, run_packages, touched, write_baseline
from ship.worktree import checkout_copy, drop_copy, note_leftover, remove_worktree
from ship.wrapper import run_timed

LOCK_INPUTS = ("pyproject.toml", "uv.lock")


def _order(state: st.State, ids: list[str]) -> list[str]:
    """Dependencies first; ties by id, so the same batch always lands in the same order."""
    ordered: list[str] = []
    pending = sorted(set(ids))
    while pending:
        ready = [i for i in pending if not any(d in pending for d in state.slices[i].depends_on)]
        ordered.extend(ready or pending)
        pending = [i for i in pending if i not in ordered]
    return ordered


def _lock_dirs(files: list[str]) -> set[str]:
    return {str(PurePosixPath(f).parent) for f in files if PurePosixPath(f).name in LOCK_INPUTS}


class Landing:
    def __init__(self, program: Program, settings: Settings):
        self.program, self.settings = program, settings
        self.lines: list[str] = []
        self.batch = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.out = program.landing(self.batch)
        self.out.mkdir(parents=True, exist_ok=True)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def regenerate_locks(self, copy: Path, dirs: set[str]) -> bool:
        for d in sorted(dirs):
            if not (copy / d / "uv.lock").exists() and not (copy / d / "pyproject.toml").exists():
                continue
            done = run_timed(list(self.settings.lock_cmd), copy / d, self.out / f"lock-{d.replace('/', '-')}.log",
                             self.settings.check_timeout_s, self.settings, self.program.tmp)
            if done.rc != 0:
                return False
            git(copy, "add", "--", str(PurePosixPath(d) / "uv.lock"), timeout=self.settings.git_timeout_s)
        return True

    def squash(self, state: st.State, sl: st.Slice, copy: Path, cur: str) -> str | None:
        """Squash one slice onto `cur`. Returns the new commit, or None after recording why not."""
        t = self.settings.git_timeout_s
        merged = git_rc(copy, "merge", "--squash", "--no-commit", sl.head, timeout=t)
        lock_dirs = _lock_dirs(changed_files(copy, sl.parent, sl.head, t))
        if merged != 0:
            unmerged = git(copy, "diff", "--name-only", "--diff-filter=U", timeout=t).split()
            if unmerged and all(PurePosixPath(f).name == "uv.lock" for f in unmerged):
                git(copy, "checkout", "--ours", "--", *unmerged, timeout=t)
                git(copy, "add", "--", *unmerged, timeout=t)
                lock_dirs |= _lock_dirs(unmerged)
            else:
                git(copy, "reset", "-q", "--hard", cur, timeout=t)
                self._red(sl.id, f"land: conflict in {unmerged or 'merge'} on {cur[:8]}")
                return None
        if lock_dirs and not self.regenerate_locks(copy, lock_dirs):
            git(copy, "reset", "-q", "--hard", cur, timeout=t)
            self._red(sl.id, f"land: uv.lock regeneration failed, see {self.out}")
            return None
        if not git(copy, "diff", "--cached", "--name-only", timeout=t).strip():
            git(copy, "reset", "-q", "--hard", cur, timeout=t)
            self.say(f"SKIP {sl.id}: nothing left to apply on {cur[:8]}")
            return None
        message = f"{sl.id}: {sl.name}\n\nSlice {sl.id}, head {sl.head}, PR {sl.pr or 'none'}.\n"
        git(copy, "commit", "-q", "--no-verify", "-m", message, timeout=t)
        return git(copy, "rev-parse", "HEAD", timeout=t).strip()

    def review_holds(self, state: st.State, sl: st.Slice, copy: Path, cur: str, new: str) -> bool:
        repo, t = Path(state.repo), self.settings.git_timeout_s
        before = patch_id(repo, sl.parent, sl.head, t)
        after = patch_id(copy, cur, new, t)
        since = set(changed_files(repo, sl.parent, cur, t))
        mine = set(changed_files(repo, sl.parent, sl.head, t))
        overlap = sorted(since & mine)
        if before == after and not overlap:
            return True
        range_verdict = self.program.range_verdict(sl.id, after)
        if not verdict_problem(range_verdict, sl.head, sl.holder.dispatch_id):
            self.say(f"RANGE-OK {sl.id}: range verdict {range_verdict.name} is CLEAN")
            return True
        diff = git(copy, "range-diff", f"{sl.parent}..{sl.head}", f"{cur}..{new}", timeout=t)
        self.program.review_dir.mkdir(parents=True, exist_ok=True)
        path = self.program.review_dir / f"{sl.id}-range-{after[:8]}.diff"
        path.write_text(diff, "utf-8", newline="\n")
        why = "patch-id changed" if before != after else "same patch-id"
        why += f", overlap with slices landed since: {overlap}" if overlap else ""
        self.say(f"REVIEW {sl.id}: {why}; range-diff at {path}; a CLEAN verdict at {range_verdict} lands it")
        return False

    def _red(self, slice_id: str, reason: str) -> None:
        with st.locked(self.program) as state:
            state.move(slice_id, Status.RED, reason)
        self.say(f"FAIL land-{slice_id} {reason}")

    def run(self, ids: list[str] | None) -> bool:
        program, settings, t = self.program, self.settings, self.settings.git_timeout_s
        state = st.load(program)
        repo = Path(state.repo)
        wanted = ids or [s.id for s in state.slices.values() if s.status == Status.CHECKED]
        candidates = []
        for sid in _order(state, wanted):
            sl = state.slices[sid]
            problem = None
            if sl.status != Status.CHECKED or not sl.head:
                problem = f"is {sl.status}, not checked"
            else:
                problem = verdict_problem(program.verdict(sid, sl.head), sl.head, sl.holder.dispatch_id)
            if problem:
                self.say(f"SKIP {sid}: {problem}")
            else:
                candidates.append(sid)
        if not candidates:
            return self.finish(False)

        git(repo, "fetch", "-q", state.remote, timeout=t)
        tip = remote_sha(repo, state.remote, state.build_branch, t)
        copy = checkout_copy(repo, program.tmp / "landing", tip, settings)
        cur, included, commits = tip, [], {}
        for sid in candidates:
            sl = state.slices[sid]
            if any(d in candidates and d not in included for d in sl.depends_on):
                self.say(f"SKIP {sid}: a dependency did not land in this batch")
                continue
            new = self.squash(state, sl, copy, cur)
            if not new:
                continue
            if not self.review_holds(state, sl, copy, cur, new):
                git(copy, "reset", "-q", "--hard", cur, timeout=t)
                continue
            included.append(sid)
            commits[sid] = new
            cur = new
        if not included:
            drop_copy(repo, copy, settings)
            return self.finish(False)

        files = sorted({f for sid in included for f in changed_files(repo, state.slices[sid].parent, cur, t)})
        packages = touched(load_packages(program), files)
        runs = run_packages(copy, packages, self.out, settings.land_timeout_s, settings, program.tmp)
        reds = set().union(*(r.red() for r in runs.values())) if runs else set()
        broken = [root for root, r in runs.items() if not r.junit_ok]
        baseline = read_baseline(program.baseline_reds)
        new_reds = sorted(reds - baseline)
        if new_reds or broken:
            self.say(f"FAIL land-tests {self.batch} batch {included}: new reds {new_reds}"
                     + (f", no JUnit report from {broken}" if broken else ""))
            drop_copy(repo, copy, settings)
            return self.finish(False)
        self.say(f"PASS land-tests {self.batch} batch {included} packages {[p.root for p in packages]}")

        try:
            git(copy, "push", "-q", state.remote, f"HEAD:refs/heads/{state.build_branch}", timeout=t)
        except GitError as exc:
            self.say(f"FAIL land-push {self.batch}: {exc}")
            drop_copy(repo, copy, settings)
            return self.finish(False)
        if remote_sha(repo, state.remote, state.build_branch, t) != cur:
            self.say(f"FAIL land-push {self.batch}: remote {state.build_branch} is not {cur}")
            drop_copy(repo, copy, settings)
            return self.finish(False)
        passed = set().union(*(set(r.outcomes) - r.red() for r in runs.values())) if runs else set()
        fixed = baseline & passed
        if fixed:
            write_baseline(program.baseline_reds, baseline - fixed)
            self.say(f"BASELINE removed {sorted(fixed)}")
        drop_copy(repo, copy, settings)

        with st.locked(program) as fresh:
            for sid in included:
                sl = fresh.slices[sid]
                sl.landed_sha = commits[sid]
                sl.patch_id = patch_id(repo, commits[sid] + "~1", commits[sid], t)
                fresh.move(sid, Status.LANDED, f"landed as {commits[sid][:8]} on {fresh.build_branch}")
        for sid in included:
            sl = state.slices[sid]
            self.say(f"PASS land-{sid} landed as {commits[sid]}")
            if sl.pr:
                run([*settings.gh, "pr", "close", sl.pr, "--comment",
                     f"Landed on {state.build_branch} as {commits[sid]}."], repo, t, check=False)
            problem = remove_worktree(repo, state.worktree(sid), sl.branch, state.remote, settings)
            if problem:
                note_leftover(program.leftovers, problem)
                self.say(f"LEFT {problem}")
            for side in ("head", "parent"):
                drop_copy(repo, program.tmp / f"check-{sid}-{side}", settings)
        return self.finish(len(included) == len(wanted))

    def finish(self, ok: bool) -> bool:
        (self.out / "summary.txt").write_text("\n".join(self.lines) + "\n", "utf-8", newline="\n")
        return ok


def land(program: Program, ids: list[str] | None, settings: Settings) -> tuple[bool, list[str]]:
    landing = Landing(program, settings)
    ok = landing.run(ids)
    return ok, landing.lines
