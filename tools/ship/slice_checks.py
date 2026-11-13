"""slice_checks: every check a ready slice must pass at its head, on this machine.

Writes checks/<id>/<head8>/: one log per check, each ending in its PASS, FAIL or NOTRUN line, and
summary.txt with the same lines. One FAIL anywhere moves the slice to `red`; otherwise `checked`.

Checks: `git diff --check`, case-only path collisions, then per touched package its setup, lint,
types and tests at the head; fail-at-parent: each new test case must fail at the parent on an
assertion (an import, collection or other error does not count) and pass at the head; Vulture and
Skylos, failing only on a finding in the slice's files that is neither at the parent nor in the
baseline (see quality.py). Last, the brief's SAFETY fact at the head. A touched package's test run
fails only on a red missing from the shared baseline (CI's known-reds.txt at the head, see suite.py),
so a red qmx-ci accepts is accepted here too.

With `ci = "github"`, the Linux line is qmx-ci's slice run on the pushed head: PASS, FAIL (red), or
PENDING while it queues or runs; land reads it again before landing (ci.linux_gate).
"""

from __future__ import annotations

import dataclasses
import shutil
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

from ship import ci
from ship import state as st
from ship.dispatch import run_facts
from ship.gitx import changed_files, git, git_rc
from ship.layout import Program
from ship.plan import PlanError, read_brief_facts
from ship.quality import check_package
from ship.settings import Settings
from ship.state import Status
from ship.suite import Outcome, Package, baseline_for, load_packages, package_of, run_tests, touched
from ship.wrapper import run_timed
from ship.worktree import checkout_copy

CHECKABLE = frozenset({Status.READY, Status.CHECKED, Status.RED})


def is_test_module(path: str) -> bool:
    name = PurePosixPath(path).name
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def is_test_support(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return path.endswith(".py") and (is_test_module(path) or parts[-1] == "conftest.py"
                                     or any(p in ("tests", "test") for p in parts[:-1]))


class Recorder:
    def __init__(self, out: Path, slice_id: str, head: str):
        self.out, self.slice_id, self.head8 = out, slice_id, head[:8]
        self.lines: list[str] = []

    def record(self, verdict: str, check: str, detail: str = "", log: Path | None = None) -> None:
        line = f"{verdict} {check} {self.slice_id} {self.head8}" + (f" {detail}" if detail else "")
        self.lines.append(line)
        target = log or self.out / f"{check}.log"
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")

    @property
    def red(self) -> bool:
        return any(ln.startswith("FAIL ") for ln in self.lines)


def fail_at_parent(rec: Recorder, package: Package, modules: list[str], support: list[str], repo: Path,
                   head: str, parent: str, head_copy: Path, parent_copy: Path, settings: Settings,
                   program: Program, heartbeat: Path) -> None:
    name = f"fail-at-parent-{package.label}"
    log = rec.out / f"{name}.log"
    t = settings.git_timeout_s
    rel = [package.rel(m) for m in modules]
    at_parent = [package.rel(m) for m in modules if git_rc(repo, "cat-file", "-e", f"{parent}:{m}", timeout=t) == 0]
    before = run_tests(parent_copy, package, at_parent, rec.out / f"{name}-parent-own.log",
                       settings.check_timeout_s, settings, program.runs, heartbeat).outcomes if at_parent else {}
    for path in support:
        target = parent_copy / path
        if git_rc(repo, "cat-file", "-e", f"{head}:{path}", timeout=t) == 0:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git(repo, "show", f"{head}:{path}", timeout=t).encode("utf-8"))
        else:
            target.unlink(missing_ok=True)
    parent_run = run_tests(parent_copy, package, rel, rec.out / f"{name}-parent.log", settings.check_timeout_s,
                           settings, program.runs, heartbeat)
    head_run = run_tests(head_copy, package, rel, rec.out / f"{name}-head.log", settings.check_timeout_s,
                         settings, program.runs, heartbeat)
    if not head_run.junit_ok or not parent_run.junit_ok:
        rec.record("FAIL", name, "no JUnit report from the test command", log)
        return
    new = sorted(k for k in head_run.outcomes if k not in before and "::::" not in k)
    if not new:
        rec.record("NOTRUN", name, "no new test cases in the changed test files", log)
        return
    bad = []
    with open(log, "a", encoding="utf-8", newline="\n") as fh:
        for test_id in new:
            at_p = parent_run.outcomes.get(test_id)
            at_h = head_run.outcomes[test_id]
            fh.write(f"{test_id} parent={at_p or 'not collected'} head={at_h}\n")
            if at_p != Outcome.ASSERTION:
                bad.append(f"{test_id} at parent: {at_p or 'not collected (import or collection error)'}")
            if at_h != Outcome.PASSED:
                bad.append(f"{test_id} at head: {at_h}")
    if bad:
        rec.record("FAIL", name, f"{len(bad)} of {len(new)} new tests: " + "; ".join(bad), log)
    else:
        rec.record("PASS", name, f"{len(new)} new tests fail at the parent on an assertion and pass at the head", log)


def safety_at_head(program: Program, slice_id: str, head_copy: Path, out: Path,
                   settings: Settings) -> tuple[str, str, str]:
    """The brief's SAFETY fact, rerun at the head: the fixed line the slice depends on still holds."""
    try:
        facts = [f for f in read_brief_facts(program.brief(slice_id)) if f.id == "SAFETY"]
    except PlanError as exc:
        return "FAIL", "safety", f"brief unreadable: {exc}"
    if not facts:
        return "NOTRUN", "safety", "the brief has no SAFETY fact"
    (line,) = run_facts(facts, head_copy, settings)
    (out / "safety.log").write_text(line + "\n", "utf-8", newline="\n")
    if line.startswith("PASS"):
        return "PASS", "safety", "the SAFETY fact gives the brief's output at the head"
    return "FAIL", "safety", "the SAFETY fact differs at the head, see safety.log"


def slice_checks(program: Program, slice_id: str, settings: Settings) -> tuple[bool, list[str]]:
    state = st.load(program)
    sl = state.slices[slice_id]
    if sl.status not in CHECKABLE or not sl.head or not sl.parent:
        return False, [f"{slice_id} is {sl.status}; checks run on a ready slice"]
    repo, head, parent = Path(state.repo), sl.head, sl.parent
    out = program.checks(slice_id, head)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    rec = Recorder(out, slice_id, head)
    beat = program.heartbeat(slice_id)
    t = settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)

    whitespace = git(repo, "diff", "--check", parent, head, timeout=t, check=False)
    (out / "diff-check.log").write_text(whitespace, "utf-8", newline="\n")
    rec.record("FAIL" if whitespace.strip() else "PASS", "diff-check")

    names = git(repo, "ls-tree", "-r", "--name-only", head, timeout=t).splitlines()
    clashes = sorted(n for n, c in Counter(x.casefold() for x in names).items() if c > 1)
    rec.record("FAIL" if clashes else "PASS", "case-collision", ", ".join(clashes))

    files = changed_files(repo, parent, head, t)
    packages = load_packages(program)
    head_copy = checkout_copy(repo, program.tmp / f"check-{slice_id}-head", head, settings)
    parent_copy = checkout_copy(repo, program.tmp / f"check-{slice_id}-parent", parent, settings)
    support = [f for f in files if is_test_support(f)]
    baseline = baseline_for(program, repo, head, t)
    for package in touched(packages, files):
        for copy in (head_copy, parent_copy):
            if package.setup:
                where = "head" if copy == head_copy else "parent"
                done = run_timed(list(package.setup), copy / package.root, out / f"setup-{package.label}-{where}.log",
                                 settings.check_timeout_s, settings, program.runs, beat)
                rec.record("PASS" if done.rc == 0 else "FAIL", f"setup-{package.label}-{where}",
                           f"rc={done.rc}", done.log)
        for kind in ("lint", "types"):
            argv = getattr(package, kind)
            name = f"{kind}-{package.label}"
            if not argv:
                rec.record("NOTRUN", name, "no command in checks.toml")
                continue
            done = run_timed(list(argv), head_copy / package.root, out / f"{name}.log", settings.check_timeout_s,
                             settings, program.runs, beat)
            rec.record("PASS" if done.rc == 0 else "FAIL", name, f"rc={done.rc}", done.log)
        name = f"test-{package.label}"
        run = run_tests(head_copy, package, [], out / f"{name}.log", settings.check_timeout_s, settings,
                        program.runs, beat)
        known = baseline.known(run.red())
        detail = (f"rc={run.run.rc} red={len(run.red())}" + (f" known={len(known)}" if known else "")
                  + ("" if run.junit_ok else " no JUnit report"))
        green = run.junit_ok and not baseline.new(run.red()) and (run.run.rc == 0 or bool(known))
        rec.record("PASS" if green else "FAIL", name, detail, run.run.log)
        modules = [f for f in files if is_test_module(f) and package_of(packages, f) == package
                   and git_rc(repo, "cat-file", "-e", f"{head}:{f}", timeout=t) == 0]
        if modules:
            fail_at_parent(rec, package, modules, support, repo, head, parent, head_copy, parent_copy,
                           settings, program, beat)
        mine = [f for f in files if package_of(packages, f) == package]
        for tool in ("vulture", "skylos"):
            verdict, detail = check_package(tool, package, head_copy, parent_copy, mine, out, "slice", settings,
                                            program, beat)
            rec.record(verdict, f"quality-{tool}-{package.label}", detail)
    rec.record(*safety_at_head(program, slice_id, head_copy, out, settings))
    other = "linux" if sys.platform == "win32" else "windows"
    linux = None
    if settings.ci == "github":
        sha = sl.ci.get("sha") if sl.ci.get("rebased") == head else head
        linux = ci.slice_linux(state, settings, dataclasses.replace(sl, ci={"sha": sha}))
        rec.record(linux[0], "linux", " ".join(x for x in linux[1:] if x))
    if other == "windows" or linux is None:
        rec.record("NOTRUN", other, f"this machine is {sys.platform}; {other} checks run in CI later")
    rec.record("NOTRUN", "mutation", "mutmut runs on the changed functions at the checkpoint (ship quality)")
    (out / "summary.txt").write_text("\n".join(rec.lines) + "\n", "utf-8", newline="\n")

    with st.locked(program) as fresh:
        now = fresh.slices[slice_id]
        if now.head == head and linux is not None:
            sha = now.ci.get("sha") if now.ci.get("rebased") == head else head
            now.ci = {**now.ci, "sha": sha, "linux": linux[0].lower(), "url": linux[2]}
        if now.head == head and now.status in CHECKABLE:
            fails = [ln for ln in rec.lines if ln.startswith("FAIL ")]
            if fails:
                fresh.move(slice_id, Status.RED, f"slice_checks: {len(fails)} FAIL at {head[:8]}")
            else:
                fresh.move(slice_id, Status.CHECKED, f"slice_checks green at {head[:8]}")
    return not rec.red, rec.lines

