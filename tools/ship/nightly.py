"""nightly: the whole suite at the build tip, and on a new red, `git bisect run` over the landed slices.

Without baseline-reds.txt, the first run writes it from the reds it finds. A red not in the baseline
starts a bisect from the last green tip (or the first landed slice's parent) to the tip, running only
the test modules that went red. The first bad commit is mapped to its slice; that slice's pending
dependents become blocked-by it, and the result goes to state.json and checks/_nightly/<tip8>/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ship import state as st
from ship.gitx import GitError, git, remote_sha, run
from ship.layout import Program
from ship.settings import Settings
from ship.suite import (Package, load_packages, read_baseline, run_packages, run_tests, write_baseline)
from ship.worktree import checkout_copy, drop_copy

PACKAGE_DIR = Path(__file__).resolve().parent
FIRST_BAD = re.compile(r"^([0-9a-f]{40}) is the first '?bad'? commit", re.M)  # newer git writes 'bad' in quotes


def module_of(checkout: Path, package: Package, test_id: str) -> str | None:
    """The test file a JUnit classname came from: `pkg.tests.test_x.TestY` -> pkg/tests/test_x.py."""
    classname = test_id.split("::")[1]
    parts = classname.split(".")
    for end in range(len(parts), 0, -1):
        rel = "/".join(parts[:end]) + ".py"
        if (checkout / package.root / rel).is_file():
            return rel
    return None


def bisect_step(program: Program, checkout: Path, ids_file: Path, settings: Settings) -> int:
    """Exit 0 when none of the ids is red at this commit, 1 when one is, 125 when it cannot tell."""
    ids = [ln.strip() for ln in ids_file.read_text("utf-8").splitlines() if ln.strip()]
    packages = {p.root: p for p in load_packages(program)}
    out = program.tmp / "bisect-logs"
    sha = git(checkout, "rev-parse", "HEAD", timeout=settings.git_timeout_s).strip()
    red = False
    for root in sorted({i.split("::")[0] for i in ids}):
        package = packages.get(root)
        if package is None:
            return 125
        mine = [i for i in ids if i.split("::")[0] == root]
        modules = sorted({m for m in (module_of(checkout, package, i) for i in mine) if m})
        if package.setup:
            from ship.wrapper import run_timed

            if run_timed(list(package.setup), checkout / package.root, out / f"{sha[:8]}-setup-{package.label}.log",
                         settings.bisect_step_timeout_s, settings, program.tmp).rc != 0:
                return 125
        result = run_tests(checkout, package, modules, out / f"{sha[:8]}-{package.label}.log",
                           settings.bisect_step_timeout_s, settings, program.tmp)
        if not result.junit_ok:
            return 125
        red = red or bool(set(mine) & result.red())
    return 1 if red else 0


def nightly(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)
    tip = remote_sha(repo, state.remote, state.build_branch, t)
    out = program.nightly(tip)
    out.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    copy = checkout_copy(repo, program.tmp / "nightly", tip, settings)
    try:
        runs = run_packages(copy, load_packages(program), out, settings.nightly_timeout_s, settings, program.tmp)
        broken = sorted(root for root, r in runs.items() if not r.junit_ok)
        reds = set().union(*(r.red() for r in runs.values())) if runs else set()
        if broken:
            lines.append(f"FAIL nightly {tip[:8]} no JUnit report from {broken}")
        if not program.baseline_reds.exists():
            write_baseline(program.baseline_reds, reds)
            lines.append(f"BASELINE written with {len(reds)} reds at {tip[:8]}")
        new = sorted(reds - read_baseline(program.baseline_reds))
        verdict: dict = {"tip": tip, "new_reds": new}
        if not new and not broken:
            lines.append(f"PASS nightly {tip[:8]} {len(reds)} baseline reds, no new red")
            with st.locked(program) as fresh:
                fresh.last_green = tip
                fresh.nightly = verdict
                fresh.log("nightly", None, tip=tip, result="green")
            return True, _write(out, lines)
        if new:
            verdict.update(bisect(program, state, copy, tip, new, settings, lines))
        with st.locked(program) as fresh:
            fresh.nightly = verdict
            fresh.log("nightly", None, tip=tip, result="red", culprit=verdict.get("culprit"))
            culprit = verdict.get("culprit")
            if culprit:
                blocked = fresh.block_dependents(culprit, f"nightly red bisected to {culprit}")
                lines.append(f"BLOCKED {blocked} by {culprit}")
        return False, _write(out, lines)
    finally:
        drop_copy(repo, copy, settings)


def bisect(program: Program, state: st.State, copy: Path, tip: str, new: list[str], settings: Settings,
           lines: list[str]) -> dict:
    t = settings.git_timeout_s
    landed = [s for s in state.slices.values() if s.landed_sha]
    good = state.last_green or (min((s for s in landed), key=_landed_order(state)).parent if landed else None)
    if not good:
        lines.append(f"FAIL nightly {tip[:8]} new reds {new}; no known good commit to bisect from")
        return {}
    ids_file = program.nightly(tip) / "bisect-ids.txt"
    ids_file.write_text("".join(f"{i}\n" for i in new), "utf-8", newline="\n")
    git(copy, "bisect", "reset", timeout=t, check=False)
    git(copy, "bisect", "start", tip, good, timeout=t)
    try:
        done = run(["git", "bisect", "run", sys.executable, str(PACKAGE_DIR), "bisect-step",
                    "--program", str(program.dir), "--ids", str(ids_file)],
                   copy, settings.nightly_timeout_s, check=False)
    except GitError as exc:
        lines.append(f"FAIL nightly {tip[:8]} new reds {new}; bisect did not finish: {exc}")
        return {}
    finally:
        git(copy, "bisect", "reset", timeout=t, check=False)
    (program.nightly(tip) / "bisect.log").write_text(done.stdout + done.stderr, "utf-8", newline="\n")
    found = FIRST_BAD.search(done.stdout)
    if not found:
        lines.append(f"FAIL nightly {tip[:8]} new reds {new}; bisect named no commit, see bisect.log")
        return {}
    sha = found.group(1)
    culprit = next((s.id for s in landed if s.landed_sha == sha), None)
    lines.append(f"FAIL nightly {tip[:8]} new reds {new}; first bad commit {sha} slice {culprit or 'none'}")
    return {"culprit": culprit, "culprit_sha": sha}


def _landed_order(state: st.State):
    order = {e["slice"]: i for i, e in enumerate(state.events) if e.get("to") == "landed"}
    return lambda s: order.get(s.id, 0)


def _write(out: Path, lines: list[str]) -> list[str]:
    (out / "summary.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
    return lines
