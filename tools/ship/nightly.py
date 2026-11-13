"""nightly: the whole suite at the build tip, and on a new red, `git bisect run` over the landed slices.

With `ci = "github"` (set in ship.toml; the default is "local") the whole suite runs on GitHub: `ci.start` dispatches qmx-ci's
deep run on the tip (or re-attaches to the one already recorded or running for it), and `ci_status`
reads it when it finishes. Its test shards come back in `suite.run_packages`'s shape; every other
job of the run (lint, Vulture, Skylos, mutmut) must be green too, and a deep run must leave a
deep-verdict naming the tip, or the pull-request gate will not pass. When GitHub cannot run it (gh
missing, no network, the workflow not on the branch), the local run below stands in.

Locally: without baseline-reds.txt or CI's known-reds.txt, the first run writes baseline-reds.txt
from the reds it finds. A red not in the baseline starts a bisect from the last green tip (or the
first landed slice's parent) to the tip, running only the test modules that went red. A GitHub run's
new reds are bisected here only when they are red on this machine's system. The first bad commit is
mapped to its slice; that slice's pending dependents become blocked-by it, and the result goes to
state.json and checks/_nightly/<tip8>/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ship import ci
from ship import state as st
from ship.gitx import GitError, git, remote_sha, run
from ship.layout import Program
from ship.settings import Settings
from ship.suite import (Baseline, Package, TestRun, baseline_for, canon, load_packages, local_id, run_packages,
                        run_tests, system_of, this_system, write_baseline)
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
                         settings.bisect_step_timeout_s, settings, program.runs).rc != 0:
                return 125
        result = run_tests(checkout, package, modules, out / f"{sha[:8]}-{package.label}.log",
                           settings.bisect_step_timeout_s, settings, program.runs)
        if not result.junit_ok:
            return 125
        red = red or bool({canon(i) for i in mine} & {canon(r) for r in result.red()})
    return 1 if red else 0


def nightly(program: Program, settings: Settings, wait: bool = True) -> tuple[bool | None, list[str]]:
    """True green, False red, None still running on GitHub (only without `wait`, or past the wait limit)."""
    first: list[str] = []
    if settings.ci == "github":
        try:
            first = ci.start(program, settings)
        except ci.Unavailable as exc:
            first = [f"CI github unavailable: {exc}; the local run stands in"]
        else:
            if not wait:
                return None, first
            rc, lines = ci.wait(lambda: ci_status(program, settings), settings)
            return {0: True, 1: False}.get(rc), first + lines
    ok, lines = local_nightly(program, settings)
    return ok, first + lines


def local_nightly(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)
    tip = remote_sha(repo, state.remote, state.build_branch, t)
    out = program.nightly(tip)
    out.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    copy = checkout_copy(repo, program.tmp / "nightly", tip, settings)
    try:
        runs = run_packages(copy, load_packages(program), out, settings.nightly_timeout_s, settings, program.runs)
        baseline = baseline_for(program, repo, tip, t)
        if not baseline.mirrored and not program.baseline_reds.exists():
            reds = _reds(runs)
            write_baseline(program.baseline_reds, reds)
            lines.append(f"BASELINE written with {len(reds)} reds at {tip[:8]}")
            baseline = baseline_for(program, repo, tip, t)
        broken = sorted(root for root, r in runs.items() if not r.junit_ok)
        ok = conclude(program, state, tip, runs, baseline, broken, [], {"backend": "local"}, lines,
                      lambda: copy, settings)
        return ok, _write(out, lines)
    finally:
        drop_copy(repo, copy, settings)


def ci_status(program: Program, settings: Settings) -> tuple[int, list[str]]:
    """Read the recorded GitHub run: 2 while it runs (with what is red so far), else its verdict,
    written like a local nightly's (0 green, 1 red). Reading a finished run twice changes nothing."""
    state = st.load(program)
    rec = state.ci.get("deep") or {}
    if not rec.get("run_id"):
        return 1, ["FAIL ci: no GitHub run recorded; run ship ci start or ship nightly"]
    tip, run_id, level = rec["tip"], rec["run_id"], rec.get("level", "deep")
    out = program.nightly(tip)
    if rec.get("result") in ("green", "red") and (out / "summary.txt").exists():
        lines = (out / "summary.txt").read_text("utf-8").splitlines()
        return (0 if rec["result"] == "green" else 1), lines
    out.mkdir(parents=True, exist_ok=True)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t, check=False)
    gh = ci.gh_for(state, settings)
    try:
        read = ci.read_run(gh, run_id, out / "ci")
    except GitError as exc:
        return 2, [f"PENDING ci {level} {run_id}: GitHub unreachable ({ci.short(exc)}); the run goes on there"]
    baseline = baseline_for(program, repo, tip, t)
    if ci.outcome(read.run) == "pending":
        return 2, ci.progress(read, baseline.new, f"ci {level} {run_id} on {tip[:8]}")
    lines: list[str] = [f"CI {level} {run_id} {read.run.get('conclusion')}: {read.run.get('url')}"]
    extra = [f"FAIL ci-job {j['name']} {j.get('conclusion')} {j.get('url', '')}".rstrip() for j in read.failed_jobs]
    if level == "deep" and not (read.verdict and read.verdict.get("sha") == tip and read.verdict.get("level") == "deep"):
        extra.append(f"FAIL deep-verdict none names {tip[:8]}, so the pull-request gate will not pass")
    broken = sorted(k for k, r in read.tests.items() if not r.junit_ok)
    if read.run.get("conclusion") != "success" and not extra and not broken and not baseline.new(_reds(read.tests)):
        extra.append(f"FAIL ci-run {read.run.get('conclusion')} with no red test and no failed job named")
    with st.locked(program) as fresh:
        extra += _recheck_pending_slices(fresh, settings, lines)
        for land in fresh.ci.get("land", []):
            if land.get("result") == "red":
                lines.append(f"NOTE land run red at {land['tip'][:8]} batch {land['slices']} {land.get('url', '')}; "
                             "this run decides")
    verdict = {"backend": "github", "run_id": run_id, "url": read.run.get("url")}
    copy_dir = program.tmp / "nightly"
    try:
        ok = conclude(program, state, tip, read.tests, baseline, broken, extra, verdict, lines,
                      lambda: checkout_copy(repo, copy_dir, tip, settings), settings)
    finally:
        drop_copy(repo, copy_dir, settings)
    with st.locked(program) as fresh:
        if (fresh.ci.get("deep") or {}).get("run_id") == run_id:
            fresh.ci["deep"]["result"] = "green" if ok else "red"
    return (0 if ok else 1), _write(out, lines)


def _recheck_pending_slices(state: st.State, settings: Settings, lines: list[str]) -> list[str]:
    """Slices that landed with their Linux slice run still pending: read it again now. Red blocks."""
    fails = []
    for sl in state.slices.values():
        if sl.status != st.Status.LANDED or sl.ci.get("linux") != "pending":
            continue
        verdict, detail, url = ci.slice_linux(state, settings, sl)
        if verdict in ("PASS", "FAIL"):
            sl.ci.update({"linux": verdict.lower(), "url": url})
        if verdict == "FAIL":
            fails.append(f"FAIL linux-slice {sl.id} landed while pending, now red: {detail} {url}".rstrip())
        else:
            lines.append(f"NOTE linux-slice {sl.id} landed while pending, now {verdict.lower()}: {detail} {url}".rstrip())
    return fails


def _reds(runs: dict[str, TestRun]) -> set[str]:
    return set().union(*(r.red() for r in runs.values())) if runs else set()


def conclude(program: Program, state: st.State, tip: str, runs: dict[str, TestRun], baseline: Baseline,
             broken: list[str], extra: list[str], verdict: dict, lines: list[str], copy_at_tip,
             settings: Settings) -> bool:
    """The one verdict for a local or a GitHub run: green only with no new red, every shard or package
    reported, and no extra FAIL line. A new red on this machine's system is bisected locally."""
    reds = _reds(runs)
    if broken:
        lines.append(f"FAIL nightly {tip[:8]} no JUnit report from {broken}")
    lines.extend(extra)
    passed = set().union(*(set(r.outcomes) - r.red() for r in runs.values())) if runs else set()
    lines.extend(f"NOTE known red passes now: {r} (shrink {baseline.source.split(' at ')[0]})"
                 for r in baseline.known(passed))
    new = baseline.new(reds)
    verdict = {"tip": tip, "new_reds": new, **verdict}
    if not new and not broken and not extra:
        lines.append(f"PASS nightly {tip[:8]} {len(reds)} baseline reds, no new red")
        with st.locked(program) as fresh:
            fresh.last_green = tip
            fresh.nightly = verdict
            fresh.log("nightly", None, tip=tip, result="green")
        return True
    if new:
        here = [r for r in new if system_of(r) == this_system()]
        elsewhere = [r for r in new if system_of(r) != this_system()]
        if here:
            ids = [local_id(r) for r in here] if verdict.get("backend") == "github" else here
            verdict.update(bisect(program, state, copy_at_tip, tip, ids, settings, lines))
        if elsewhere:
            lines.append(f"FAIL nightly {tip[:8]} new reds on another system {elsewhere}; not bisected on "
                         f"{this_system()}: the suspects are the slices landed since the last green tip")
    with st.locked(program) as fresh:
        fresh.nightly = verdict
        fresh.log("nightly", None, tip=tip, result="red", culprit=verdict.get("culprit"))
        culprit = verdict.get("culprit")
        if culprit:
            blocked = fresh.block_dependents(culprit, f"nightly red bisected to {culprit}")
            lines.append(f"BLOCKED {blocked} by {culprit}")
    return False


def bisect(program: Program, state: st.State, copy_at_tip, tip: str, new: list[str], settings: Settings,
           lines: list[str]) -> dict:
    t = settings.git_timeout_s
    landed = [s for s in state.slices.values() if s.landed_sha]
    good = state.last_green or (min((s for s in landed), key=_landed_order(state)).parent if landed else None)
    if not good:
        lines.append(f"FAIL nightly {tip[:8]} new reds {new}; no known good commit to bisect from")
        return {}
    copy = copy_at_tip()
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
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
    return lines
