"""The one entry point every GitLab CI job calls: `python tools/ci/qci.py <job>`.

`.gitlab-ci.yml` decides which jobs a pipeline holds, from `QMX_LEVEL`. This file decides what each
job does at that level: which commit it compares against, which tests a shard runs, and which
findings are new. Every job writes what it found under `ci-out/`, JUnit XML under `ci-out/junit/`.

It also runs on a laptop: with no GitLab variables the level is `deep` and the head is `HEAD`, so
`python tools/ci/qci.py vulture --write-baseline` rewrites a baseline from the same code CI runs.
"""

from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, cast

import ci_mutate
import ci_units
import ratchet
import tomllib

REPO = Path(__file__).resolve().parents[2]
GIT = shutil.which("git") or "git"
OUT = REPO / "ci-out"
BASELINES = REPO / "ci" / "baselines"
ZERO_SHA = "0" * 40
ENGINE = "engine/base"
GIT_TIMEOUT_S = 600
STEP_TIMEOUT_S = 80 * 60
VULTURE = "vulture==2.16"
SKYLOS = "skylos==5.6.0"
MUTMUT = "mutmut==3.8.1"
VULTURE_PATHS = (
    "packages",
    "extensions",
    "qml",
    "qmb",
    "qmn",
    "tools",
    "qmx-agents/packages",
    "qmx-agents/apps",
)
# The buckets [tool.skylos.gate] holds at zero. Quality and dead code are notes only (his ruling of
# 28 September 2026); Vulture is the dead-code ratchet.
SKYLOS_BLOCKING = frozenset(
    {
        "danger",
        "secrets",
        "reliability",
        "ai_defects",
        "dependency_vulnerabilities",
        "publisher_change_findings",
        "custom_rules",
    }
)
SKYLOS_NOTES_ONLY_PREFIX = ("unused_", "quality", "forgotten", "circular_dependencies")
# The finding lists in Skylos's JSON (skylos/commands/scan_cmd.py, _DIFF_FINDING_CATEGORIES).
# Other top-level lists, such as `whitelisted` and `suppressed`, are not findings.
SKYLOS_FINDING_CATEGORIES = frozenset(
    {
        *("unused_functions", "unused_imports", "unused_classes", "unused_variables"),
        *("unused_parameters", "unused_files", "unused_fixtures", "unused_exports", "forgotten"),
        *("danger", "reliability", "ai_defects", "quality", "secrets", "custom_rules"),
        *("circular_dependencies", "dependency_vulnerabilities", "publisher_change_findings"),
    }
)
SKYLOS_BLOCKING_SEVERITY = frozenset({"critical", "high"})
SMOKE_PORT = 18766


class Level(enum.StrEnum):
    SLICE = "slice"  # push to slice/**
    LAND = "land"  # push to build/**
    DEEP = "deep"  # a checkpoint (stop point), started by hand: `glab ci run -b <branch>`
    GATE = "gate"  # merge request into engine/base
    RELEASE = "release"  # tag v*
    WALK = "walk"  # one part of the scheduled whole-repo mutation walk
    BASELINE = "baseline"  # rewrite ci/baselines from this commit; the files are job artifacts


Scope = Literal["touched", "all"]
TEST_SCOPE: dict[Level, Scope] = {
    Level.SLICE: "touched",
    Level.LAND: "touched",
    Level.DEEP: "all",
    Level.RELEASE: "all",
}


class CiError(Exception):
    pass


# ---- git and processes ------------------------------------------------------------------------


def git(*args: str, cwd: Path = REPO, check: bool = True) -> str:
    done = subprocess.run(
        [GIT, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT_S,
        check=False,
    )
    if check and done.returncode != 0:
        raise CiError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def run(
    argv: Sequence[str],
    cwd: Path,
    timeout: float = STEP_TIMEOUT_S,
    env: Mapping[str, str] | None = None,
    stdout_to: Path | None = None,
    whole_env: bool = False,
) -> int:
    print(
        f"$ ({cwd.relative_to(REPO) if cwd.is_relative_to(REPO) else cwd}) {' '.join(argv)}",
        flush=True,
    )
    started = time.monotonic()  # ambient-scan: allow - CI step duration
    merged = dict(env or {}) if whole_env else {**os.environ, **(env or {})}
    if stdout_to is not None:
        stdout_to.parent.mkdir(parents=True, exist_ok=True)
    with stdout_to.open("w", encoding="utf-8") if stdout_to else open(os.devnull, "w") as fh:
        child = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=merged,
            stdout=fh if stdout_to else None,
            stderr=subprocess.STDOUT if stdout_to else None,
            start_new_session=os.name != "nt",
        )
        try:
            rc = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_tree(child)
            print(f"TIMEOUT after {timeout:.0f}s; stopped the process tree", flush=True)
            rc = 124
    elapsed = time.monotonic() - started  # ambient-scan: allow - CI step duration
    print(f"  -> rc={rc} in {elapsed:.0f}s", flush=True)
    return rc


def kill_tree(child: subprocess.Popen[bytes]) -> None:
    """Stop a timed-out step and everything it started, so no tool outlives its step."""
    if os.name == "nt":
        subprocess.run(
            [shutil.which("taskkill") or "taskkill", "/T", "/F", "/PID", str(child.pid)],
            capture_output=True,
            timeout=60,
            check=False,
        )
    else:
        os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=60)


def uv() -> str:
    found = shutil.which("uv")
    if found is None:
        raise CiError("uv is not on PATH")
    return found


def sync(workspace: str, root: Path = REPO) -> None:
    extra = ["--all-packages", "--all-groups"] if workspace == ci_units.AGENTS_WS else []
    if run([uv(), "sync", "--frozen", *extra], root / workspace) != 0:
        raise CiError(f"uv sync failed in {workspace}")


# ---- level, head and base ---------------------------------------------------------------------


def level() -> Level:
    return Level(os.environ.get("QMX_LEVEL", "deep"))


def head() -> str:
    return os.environ.get("CI_COMMIT_SHA") or git("rev-parse", "HEAD").strip()


def fetch_refs(build_branches: bool) -> None:
    refspecs = [f"+refs/heads/{ENGINE}:refs/remotes/origin/{ENGINE}"]
    if build_branches:
        refspecs.append("+refs/heads/build/*:refs/remotes/origin/build/*")
    if os.environ.get("CI"):
        git("fetch", "--quiet", "origin", *refspecs)


def git_ok(*args: str) -> bool:
    return (
        subprocess.run(
            [GIT, *args], cwd=REPO, capture_output=True, timeout=GIT_TIMEOUT_S, check=False
        ).returncode
        == 0
    )


def merge_base(a: str, b: str) -> str | None:
    done = git("merge-base", a, b, check=False).strip()
    return done or None


def fork_point(at: str) -> str:
    """The build branch (or engine/base) tip a slice was cut from: the nearest merge-base."""
    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/origin/build/",
        f"refs/remotes/origin/{ENGINE}",
    ).split()
    best: tuple[int, str] | None = None
    for ref in refs:
        base = merge_base(at, ref)
        if base is None or base == at:
            continue
        distance = int(git("rev-list", "--count", f"{base}..{at}").strip())
        if best is None or distance < best[0]:
            best = (distance, base)
    if best is None:
        raise CiError(f"no build/* branch or {ENGINE} shares history with {at[:8]}")
    return best[1]


def previous_release(at: str) -> str | None:
    if os.environ.get("CI"):
        git("fetch", "--quiet", "--tags", "origin", check=False)
    found = git("describe", "--tags", "--abbrev=0", "--match", "v*", f"{at}^", check=False).strip()
    return found or None


def base_for(lvl: Level, at: str) -> str | None:
    """The commit this pipeline's changes are measured from. `QMX_BASE` overrides it. A checkpoint
    lands in engine/base, so 'since the last checkpoint' is the merge-base with engine/base."""
    explicit = os.environ.get("QMX_BASE")
    if explicit:
        return git("rev-parse", explicit).strip()
    fetch_refs(build_branches=lvl == Level.SLICE)
    match lvl:
        case Level.SLICE:
            return fork_point(at)
        case Level.LAND:
            before = os.environ.get("CI_COMMIT_BEFORE_SHA", "")
            if before and before != ZERO_SHA and git_ok("cat-file", "-e", before):
                return before
            return merge_base(at, f"refs/remotes/origin/{ENGINE}")
        case Level.DEEP | Level.WALK | Level.GATE | Level.BASELINE:
            return merge_base(at, f"refs/remotes/origin/{ENGINE}")
        case Level.RELEASE:
            return previous_release(at)


def changed_files(base: str | None, at: str) -> list[str]:
    if base is None:
        return []
    return [p for p in git("diff", "--name-only", "--no-renames", base, at).splitlines() if p]


def describe(lvl: Level, base: str | None, at: str, changed: list[str]) -> None:
    print(
        f"level={lvl} head={at[:10]} base={base[:10] if base else None} changed={len(changed)}",
        flush=True,
    )
    OUT.mkdir(parents=True, exist_ok=True)


# ---- pytest and JUnit -------------------------------------------------------------------------


ASSERTION_PREFIXES = ("assert", "AssertionError", "Failed: DID NOT RAISE", "Failed: DID NOT WARN")


def outcomes(junit: Path) -> dict[str, str]:
    """test id -> passed | skipped | assertion | failed | error (collection and setup errors)."""
    if not junit.exists():
        return {}
    found: dict[str, str] = {}
    for case in ET.parse(junit).iter("testcase"):  # noqa: S314 - pytest wrote this report in this job
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        failure, error, skipped = case.find("failure"), case.find("error"), case.find("skipped")
        if error is not None or not case.get("classname"):
            found[test_id] = "error"
        elif failure is not None:
            message = (failure.get("message") or "").lstrip()
            found[test_id] = "assertion" if message.startswith(ASSERTION_PREFIXES) else "failed"
        elif skipped is not None:
            found[test_id] = "skipped"
        else:
            found[test_id] = "passed"
    return found


def pytest(
    cwd: Path, files: list[str], junit: Path, *, serial: bool | None, workers: str = "auto"
) -> int:
    """Run pytest on `files` (relative to `cwd`) through an argument file, so a long shard never
    hits
    the Windows command-line limit. serial=None runs every test with no worker split."""
    junit.parent.mkdir(parents=True, exist_ok=True)
    args = OUT / "tmp" / f"{junit.stem}.args"
    args.parent.mkdir(parents=True, exist_ok=True)
    args.write_text("\n".join(files) + "\n", "utf-8")
    basetemp = Path(tempfile.mkdtemp(prefix="qmx-pt-"))
    split = (
        ["-n", "0"]
        if serial is None
        else ["-n", "0", "-m", "serial"]
        if serial
        else ["-n", workers, "--dist", "worksteal", "-m", "not serial"]
    )
    argv = [
        uv(),
        "run",
        "--frozen",
        "--no-sync",
        "python",
        "-m",
        "pytest",
        f"@{args}",
        "-q",
        "-rfE",
        "-p",
        "no:cacheprovider",
        *split,
        "--basetemp",
        str(basetemp),
        "--junitxml",
        str(junit),
    ]
    return run(argv, cwd, env=test_env(), whole_env=True)


def test_env() -> dict[str, str]:
    """The job's environment without GitLab's own CI_* and GITLAB_* variables. They hold job
    tokens and proxy settings that the code under test rightly refuses to run beside (the agent
    harness refuses any name holding PROXY), and no test needs them. `CI` itself stays."""
    return {k: v for k, v in os.environ.items() if not k.startswith(("CI_", "GITLAB_"))}


# ---- jobs -------------------------------------------------------------------------------------


def job_tests(system: str) -> int:
    """One shard of the tests this level asks for. Every shard plans the same split from the same
    inputs and takes its own part, so shards need no plan job."""
    lvl = level()
    at = head()
    index = int(os.environ.get("CI_NODE_INDEX", "1"))
    total = int(os.environ.get("CI_NODE_TOTAL", "1"))
    units = ci_units.discover(REPO)
    if TEST_SCOPE.get(lvl) == "all":
        base, changed, chosen = None, [], units
    else:
        base = base_for(lvl, at)
        changed = changed_files(base, at)
        chosen = ci_units.select(units, changed)
    describe(lvl, base, at, changed)
    durations = ci_units.load_durations(REPO / "tools" / "ci" / "durations.json")
    files = [f for u in chosen for f in ci_units.test_files(REPO, u, durations)]
    shards = ci_units.shard(files, total) if files else []
    mine = shards[index - 1] if index <= len(shards) else []
    plan = {
        "level": lvl.value,
        "system": system,
        "shard": index,
        "of": total,
        "base": base,
        "units": [u.root for u in chosen],
        "files": [f"{f.unit.cwd}::{f.path}" for f in mine],
    }
    (OUT / f"plan-{system}-{index}.json").write_text(json.dumps(plan, indent=1), "utf-8")
    if not mine:
        print(
            f"shard {index}/{total}: nothing to run "
            f"({len(files)} test files in {len(chosen)} units)"
        )
        return 0
    grouped: dict[ci_units.Unit, list[str]] = {}
    for f in mine:
        grouped.setdefault(f.unit, []).append(f.path)
    for workspace in sorted({w for u in grouped for w in ci_units.workspaces_for(u)}):
        sync(workspace)
    crashed: list[str] = []
    reds: list[str] = []
    for unit, paths in sorted(grouped.items(), key=lambda item: item[0].root):
        stem = f"{system}-{index}-{unit.root.replace('/', '_')}"
        for serial in (False, True):
            junit = OUT / "junit" / f"{stem}{'-serial' if serial else ''}.xml"
            rc = pytest(REPO / unit.cwd, sorted(paths), junit, serial=serial)
            if rc not in (0, 1, 5) or (rc == 1 and not junit.exists()):
                crashed.append(f"{unit.root}{' (serial)' if serial else ''}: pytest rc={rc}")
            reds += [
                red_key(system, unit, test_id)
                for test_id, outcome in outcomes(junit).items()
                if outcome in ("assertion", "failed", "error")
            ]
    return tests_verdict(f"{system}-{index}", reds, crashed)


def red_key(system: str, unit: ci_units.Unit, test_id: str) -> str:
    return f"{system}|{unit.root}|{test_id}"


def tests_verdict(name: str, reds: list[str], crashed: list[str]) -> int:
    """Reds listed in ci/baselines/known-reds.txt (red on engine/base when it was taken) are
    reported and do not block; any other red, or a pytest that crashed, does."""
    known = set(ratchet.read_baseline(BASELINES / "known-reds.txt"))
    new = sorted(r for r in set(reds) if r not in known)
    lines = [f"{len(set(reds))} red tests, {len(new)} not in known-reds.txt"]
    lines += [f"FAIL {c}" for c in crashed]
    lines += [f"NEW RED {r}" for r in new]
    lines += [f"known red {r}" for r in sorted(set(reds) & known)]
    (OUT / f"reds-{name}.txt").write_text("".join(f"{r}\n" for r in sorted(set(reds))), "utf-8")
    print("\n".join(lines))
    return 1 if new or crashed else 0


def job_lint() -> int:
    lvl = level()
    at = head()
    dirs = ci_units.poe_dirs(REPO)
    if lvl == Level.SLICE:
        base = base_for(lvl, at)
        changed = changed_files(base, at)
        targets = ci_units.lint_targets(changed, dirs)
    else:
        base, changed, targets = None, [], dirs
    describe(lvl, base, at, changed)
    if not targets:
        print("no Python or project file changed; nothing to lint")
        return 0
    for workspace in sorted(
        {
            ci_units.AGENTS_WS if d.startswith(ci_units.AGENTS_WS) else ci_units.ROOT_WS
            for d in targets
        }
    ):
        sync(workspace)
    steps = [(d, task) for d in targets for task in ("fmt-check", "lint", "types")]
    if ci_units.ROOT_WS in targets:
        steps += [(ci_units.ROOT_WS, "money-path-scan"), (ci_units.ROOT_WS, "secret-scan")]
    found: list[ratchet.Finding] = []
    for folder, task in steps:
        rc = run(
            [uv(), "run", "--frozen", "--no-sync", "python", "-m", "poethepoet", task],
            REPO / folder,
        )
        if rc != 0:
            found.append(ratchet.Finding(folder, 0, task, f"poe {task} failed (rc={rc})"))
    ratchet.write_junit(OUT / "junit" / "lint.xml", "lint", found)
    for f in found:
        print(f"FAIL {f.text()}")
    return 1 if found else 0


def job_fail_at_parent() -> int:
    """Each new test case must fail at the parent on an assertion and pass at the head. An import,
    collection or setup error at the parent does not count as failing."""
    lvl = level()
    at = head()
    base = base_for(lvl, at)
    changed = changed_files(base, at)
    describe(lvl, base, at, changed)
    if base is None:
        print("no parent to compare with")
        return 0
    present = set(git("ls-tree", "-r", "--name-only", at).splitlines())
    modules = [p for p in changed if ci_units.is_test_module(p) and p in present]
    support = [p for p in changed if ci_units.is_test_support(p) and not ci_units.is_test_module(p)]
    units = ci_units.discover(REPO)
    by_unit: dict[ci_units.Unit, list[str]] = {}
    for m in modules:
        unit = ci_units.owner(units, m)
        if unit is not None:
            by_unit.setdefault(unit, []).append(m)
    if not by_unit:
        print("no changed test module belongs to a test unit; nothing to check")
        ratchet.write_junit(OUT / "junit" / "fail-at-parent.xml", "fail-at-parent", [])
        return 0
    parent_copy = Path(tempfile.mkdtemp(prefix="qmx-parent-")) / "repo"
    git("worktree", "add", "--detach", str(parent_copy), base)
    for workspace in sorted({w for u in by_unit for w in ci_units.workspaces_for(u)}):
        sync(workspace)
        sync(workspace, root=parent_copy)
    problems: list[ratchet.Finding] = []
    log: list[str] = []
    for unit, mods in sorted(by_unit.items(), key=lambda item: item[0].root):
        rel = [m if unit.cwd == ci_units.ROOT_WS else m[len(unit.cwd) + 1 :] for m in mods]
        own = [r for r, m in zip(rel, mods, strict=True) if git_ok("cat-file", "-e", f"{base}:{m}")]
        stem = unit.root.replace("/", "_")
        before = {}
        if own:
            pytest(parent_copy / unit.cwd, own, OUT / "fap" / f"{stem}-parent-own.xml", serial=None)
            before = outcomes(OUT / "fap" / f"{stem}-parent-own.xml")
        for path in [*support, *mods]:
            target = parent_copy / path
            if path in present:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(
                    subprocess.run(
                        [GIT, "show", f"{at}:{path}"],
                        cwd=REPO,
                        capture_output=True,
                        timeout=GIT_TIMEOUT_S,
                        check=True,
                    ).stdout
                )
            else:
                target.unlink(missing_ok=True)
        pytest(parent_copy / unit.cwd, rel, OUT / "fap" / f"{stem}-parent.xml", serial=None)
        pytest(REPO / unit.cwd, rel, OUT / "junit" / f"fap-{stem}-head.xml", serial=None)
        at_parent = outcomes(OUT / "fap" / f"{stem}-parent.xml")
        at_head = outcomes(OUT / "junit" / f"fap-{stem}-head.xml")
        if not at_head:
            problems.append(
                ratchet.Finding(unit.root, 0, "fail-at-parent", "no JUnit report at the head")
            )
            continue
        new = sorted(k for k in at_head if k not in before and "::::" not in k)
        for test_id in new:
            p, h = at_parent.get(test_id, "not collected"), at_head[test_id]
            log.append(f"{test_id} parent={p} head={h}")
            if p != "assertion":
                problems.append(
                    ratchet.Finding(unit.root, 0, "fail-at-parent", f"{test_id} at parent: {p}")
                )
            if h != "passed":
                problems.append(
                    ratchet.Finding(unit.root, 0, "fail-at-parent", f"{test_id} at head: {h}")
                )
        if not new:
            log.append(f"{unit.root}: no new test cases in the changed test files")
    git("worktree", "remove", "--force", str(parent_copy), check=False)
    (OUT / "fail-at-parent.txt").write_text("\n".join(log) + "\n", "utf-8")
    print("\n".join(log))
    ratchet.write_junit(OUT / "junit" / "fail-at-parent.xml", "fail-at-parent", problems)
    for f in problems:
        print(f"FAIL {f.text()}")
    return 1 if problems else 0


def ratchet_verdict(
    tool: str, found: list[ratchet.Finding], scope: list[str] | None, report_as: str = ""
) -> int:
    """New findings beyond `ci/baselines/<tool>.txt`. With a scope (a slice), only new findings in
    the changed files block."""
    fresh = ratchet.new_findings(found, ratchet.read_baseline(BASELINES / f"{tool}.txt"))
    tool = report_as or tool
    if scope is not None:
        wanted = set(scope)
        fresh = [dataclasses.replace(f, blocking=f.blocking and f.path in wanted) for f in fresh]
    blocking = [f for f in fresh if f.blocking]
    report = [
        f"{tool}: {len(found)} findings, {len(fresh)} not in the baseline, {len(blocking)} blocking"
    ]
    report += [("BLOCK " if f.blocking else "note  ") + f.text() for f in fresh]
    (OUT / f"{tool}-new.txt").write_text("\n".join(report) + "\n", "utf-8")
    ratchet.write_junit(OUT / "junit" / f"{tool}.xml", tool, fresh)
    print("\n".join(line for line in report if not line.startswith("note")))
    print(f"(notes, which do not block, are in ci-out/{tool}-new.txt)")
    return 1 if blocking else 0


def vulture_findings() -> list[ratchet.Finding]:
    raw = OUT / "vulture-raw.txt"
    rc = run(
        [
            uv(),
            "tool",
            "run",
            "--python",
            "3.14",
            "--from",
            VULTURE,
            "vulture",
            *VULTURE_PATHS,
            "--min-confidence",
            "80",
        ],
        REPO,
        stdout_to=raw,
        timeout=20 * 60,
    )
    if rc not in (0, 3):
        raise CiError(
            f"vulture exited {rc}: it did not finish its scan (see ci-out/vulture-raw.txt)"
        )
    found: list[ratchet.Finding] = []
    for line in raw.read_text("utf-8", errors="replace").splitlines():
        path, sep, rest = line.partition(":")
        number, sep2, message = rest.partition(": ")
        if not sep or not sep2 or not number.isdigit():
            continue
        if not message.endswith("% confidence)"):
            raise CiError(f"vulture could not read a file, so its scan is incomplete: {line}")
        message = message.rsplit(" (", 1)[0]
        found.append(ratchet.Finding(path.replace("\\", "/"), int(number), "vulture", message))
    return found


def keep_baseline(name: str) -> None:
    """Copy a rewritten baseline into ci-out/baselines, so a CI job hands it over as an artifact."""
    (OUT / "baselines").mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASELINES / name, OUT / "baselines" / name)


def job_vulture(write_baseline: bool) -> int:
    lvl = level()
    at = head()
    found = vulture_findings()
    if write_baseline:
        ratchet.write_baseline(
            BASELINES / "vulture.txt",
            found,
            f"Vulture {VULTURE} --min-confidence 80 over {' '.join(VULTURE_PATHS)}.\n"
            f"Taken at {at[:10]}. Key: path|rule|message; line numbers are left out.",
        )
        keep_baseline("vulture.txt")
        print(f"wrote {len(found)} findings to ci/baselines/vulture.txt")
        return 0
    scope = changed_files(base_for(lvl, at), at) if lvl == Level.SLICE else None
    return ratchet_verdict("vulture", found, scope)


def skylos_scope() -> dict[str, str]:
    """Skylos reads [tool.skylos].exclude in discovery, but its agent-file probe ignores it, so the
    probe files inside excluded trees are deleted from this disposable checkout first. Returns the
    environment naming our own packages, so Skylos does not take them for unknown dependencies."""
    config = tomllib.loads((REPO / "pyproject.toml").read_text("utf-8"))
    probe = {
        "readme.md",
        "readme.rst",
        "readme.txt",
        "security.md",
        "contributing.md",
        "contributing.rst",
        "prompt.md",
        "prompts.md",
        "prompts.yaml",
        "prompts.yml",
        "agents.md",
        "claude.md",
        ".cursorrules",
        ".clinerules",
        ".windsurfrules",
    }
    for name in sorted(config["tool"]["skylos"]["exclude"]):
        tree = REPO / name
        if tree.is_dir():
            for candidate in sorted(tree.rglob("*")):
                if candidate.is_file() and candidate.name.lower() in probe:
                    candidate.unlink()
    namespaces = {
        child.name
        for src in [*REPO.glob("*/src"), *REPO.glob("*/*/src")]
        for child in src.iterdir()
        if child.is_dir() and not child.name.startswith((".", "_"))
    }
    tools = {m.stem for m in REPO.glob("tools/*.py") if not m.stem.startswith("_")}
    allow = sorted(namespaces | tools | {"qmf", "qmb", "qml", "qmn", "qma"})
    return {"SKYLOS_PRIVATE_DEPS_ALLOW": ",".join(allow)}


def skylos_findings(report: Path) -> list[ratchet.Finding]:
    """Every finding in Skylos's JSON: one list per category at the top level."""
    data = cast("dict[str, object]", json.loads(report.read_text("utf-8")))
    root = REPO.as_posix() + "/"
    found: list[ratchet.Finding] = []
    for category, items in sorted(data.items()):
        if category not in SKYLOS_FINDING_CATEGORIES or not isinstance(items, list):
            continue
        for raw in cast("list[object]", items):
            if not isinstance(raw, dict):
                continue
            item = cast("dict[str, object]", raw)
            path = str(item.get("file") or item.get("filename") or "").replace("\\", "/")
            if not path:
                continue
            rel = path[len(root) :] if path.startswith(root) else path.removeprefix("./")
            rule = str(item.get("rule_id") or item.get("rule") or category)
            name = str(item.get("full_name") or item.get("name") or item.get("message") or "")
            severity = str(item.get("severity") or "").lower()
            line = item.get("line")
            notes_only = category.startswith(SKYLOS_NOTES_ONLY_PREFIX)
            blocking = not notes_only and (
                category in SKYLOS_BLOCKING or severity in SKYLOS_BLOCKING_SEVERITY
            )
            found.append(
                ratchet.Finding(
                    rel, line if isinstance(line, int) else 0, f"{category}:{rule}", name, blocking
                )
            )
    return found


def job_skylos(write_baseline: bool) -> int:
    lvl = level()
    at = head()
    base = base_for(lvl, at) if lvl == Level.SLICE else None
    env = skylos_scope()
    report = OUT / "skylos.json"
    argv = [
        uv(),
        "tool",
        "run",
        "--python",
        "3.14",
        "--from",
        SKYLOS,
        "skylos",
        ".",
        "-a",
        "--no-upload",
        "--format",
        "json-ci",
        "-o",
        str(report),
    ]
    if base is not None:
        argv += ["--diff-base", base]
    rc = run(argv, REPO, env=env, timeout=40 * 60)
    if rc not in (0, 1) or not report.exists():
        reason = (
            "timed out"
            if rc == 124
            else "analysis incomplete (exit 2)"
            if rc == 2
            else f"exit {rc}"
        )
        (OUT / "skylos-new.txt").write_text(f"skylos did not finish: {reason}\n", "utf-8")
        raise CiError(f"skylos did not finish: {reason}")
    found = skylos_findings(report)
    if write_baseline:
        ratchet.write_baseline(
            BASELINES / "skylos.txt",
            found,
            f"Skylos {SKYLOS} `skylos . -a --no-upload`, scope from [tool.skylos].\n"
            f"Taken at {at[:10]}. Key: path|category:rule|name; line numbers are left out.",
        )
        keep_baseline("skylos.txt")
        print(f"wrote {len(found)} findings to ci/baselines/skylos.txt")
        return 0
    scope = changed_files(base, at) if base is not None else None
    return ratchet_verdict("skylos", found, scope)


def mutable_packages() -> list[str]:
    roots = [
        *sorted(p.parent for p in REPO.glob("packages/*/src")),
        *sorted(p.parent for p in REPO.glob("extensions/*/src")),
        *[REPO / n for n in ("qml", "qmb", "qmn")],
        *sorted(p.parent for p in REPO.glob("qmx-agents/packages/*/src")),
    ]
    return [
        r.relative_to(REPO).as_posix()
        for r in roots
        if (r / "src").is_dir() and (r / "tests").is_dir()
    ]


def mutate_targets(lvl: Level, at: str) -> list[ci_mutate.Target]:
    packages = mutable_packages()
    named = [m for m in os.environ.get("QMX_MUTATE_MODULES", "").split(",") if m]
    if not named and lvl == Level.BASELINE:
        named = ratchet.read_baseline(BASELINES / "mutmut-modules.txt")
    everything = ci_mutate.all_targets(REPO, packages)
    if named:
        return [t for t in everything if t.module in named]
    if lvl == Level.WALK:
        parts = int(os.environ.get("QMX_WALK_PARTS", str(ci_mutate.WALK_PARTS)))
        part = int(
            os.environ.get(
                "QMX_WALK_PART", str(int(os.environ.get("CI_PIPELINE_IID", "0")) % parts)
            )
        )
        print(f"walk part {part} of {parts} (0-based)")
        return ci_mutate.walk_part(everything, part, parts)
    base = base_for(lvl, at)
    if base is None:
        print("no earlier checkpoint or release to compare with; nothing to mutate")
        return []
    targets: list[ci_mutate.Target] = []
    for path in changed_files(base, at):
        found = ci_mutate.source_package(path)
        if found is None or found[0] not in packages or not (REPO / path).exists():
            continue
        diff = git("diff", "-U0", base, at, "--", path)
        lines = ci_mutate.changed_lines(diff)
        names = ci_mutate.touched_functions((REPO / path).read_text("utf-8"), lines)
        targets += [ci_mutate.Target(found[0], ci_mutate.module_name(found[1]), n) for n in names]
    return sorted(set(targets))


MUTMUT_PYTEST = ["-n", "0", "-p", "no:cacheprovider", "-q"]


def stage_mutmut(package: Path, files: list[str]) -> None:
    """Write [tool.mutmut] (and a pytest anchor, if the package has none) into this disposable
    checkout's package pyproject, so mutmut runs from the package with its own tests.

    mutmut runs the tests from `<package>/mutants/tests`, one level deeper than they live. A
    top-level package's tests that find the repo as `parents[2]` then land on the package itself,
    so each repo folder they may read is linked into the package (Linux CI checkout only)."""
    if package.parent == REPO and os.name != "nt":
        for item in sorted(REPO.iterdir()):
            link = package / item.name
            wanted = item.is_dir() and item != package and not item.name.startswith(".")
            if wanted and not link.exists():
                link.symlink_to(Path("..") / item.name, target_is_directory=True)
    pyproject = package / "pyproject.toml"
    text = pyproject.read_text("utf-8")
    config = tomllib.loads(text)
    if "mutmut" in config.get("tool", {}):
        raise CiError(f"{pyproject} already has [tool.mutmut]")
    extra = [
        "",
        "[tool.mutmut]",
        'source_paths = ["src"]',
        f"only_mutate = {json.dumps(files)}",
        'pytest_add_cli_args_test_selection = ["tests"]',
        f"pytest_add_cli_args = {json.dumps(MUTMUT_PYTEST)}",
    ]
    copy = [n for n in ("examples", "conftest.py", "fixtures") if (package / n).exists()]
    if copy:
        extra.append(f"also_copy = {json.dumps(copy)}")
    if "pytest" not in config.get("tool", {}):
        extra += ["", "[tool.pytest.ini_options]", 'testpaths = ["tests"]']
    pyproject.write_text(text.rstrip("\n") + "\n" + "\n".join(extra) + "\n", "utf-8")


def job_mutmut() -> int:
    lvl = level()
    at = head()
    shard = int(os.environ.get("CI_NODE_INDEX", "1"))
    total = int(os.environ.get("CI_NODE_TOTAL", "1"))
    targets = mutate_targets(lvl, at)
    by_package: dict[str, list[ci_mutate.Target]] = {}
    for t in targets:
        by_package.setdefault(t.package, []).append(t)
    mine = [p for i, p in enumerate(sorted(by_package)) if i % total == shard - 1]
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(targets)} functions in {len(by_package)} packages; this shard: {mine}")
    found: list[ratchet.Finding] = []
    broken: list[str] = []
    for package in mine:
        chosen = by_package[package]
        folder = REPO / package
        workspace = (
            ci_units.AGENTS_WS if package.startswith(ci_units.AGENTS_WS) else ci_units.ROOT_WS
        )
        sync(workspace)
        files = sorted({"src/" + t.module.replace(".", "/") + ".py" for t in chosen})
        stage_mutmut(folder, files)
        name = package.replace("/", "_")
        base_cmd = [uv(), "run", "--frozen", "--no-sync", "--with", MUTMUT, "mutmut"]
        rc = run(
            [*base_cmd, "run", *[t.glob for t in chosen]],
            folder,
            stdout_to=OUT / "mutmut" / f"{name}-run.log",
            timeout=float(os.environ.get("QMX_MUTMUT_TIMEOUT_S", str(70 * 60))),
        )
        results_file = OUT / "mutmut" / f"{name}-results.txt"
        rc2 = run(
            [*base_cmd, "results", "--all", "true"], folder, stdout_to=results_file, timeout=600
        )
        results = ci_mutate.parse_results(results_file.read_text("utf-8", errors="replace"))
        mine_results = {
            k: v
            for k, v in results.items()
            if any(k.startswith(f"{t.module}.{t.mangled}__mutmut_") for t in chosen)
        }
        if rc != 0 or rc2 != 0 or not mine_results:
            broken.append(
                f"{package}: mutmut run rc={rc}, results rc={rc2}, "
                f"{len(mine_results)} mutants classified"
            )
        statuses: dict[str, int] = {}
        for status in mine_results.values():
            statuses[status] = statuses.get(status, 0) + 1
        print(f"{package}: {statuses}")
        for t in chosen:
            stem = f"{t.module}.{t.mangled}__mutmut_"
            for mutant, status in sorted(mine_results.items()):
                if mutant.startswith(stem) and status in ci_mutate.SURVIVING:
                    found.append(
                        ratchet.Finding(package, 0, "mutmut", f"{t.module}.{t.function} {status}")
                    )
        shutil.rmtree(folder / "mutants", ignore_errors=True)
        git("checkout", "--", f"{package}/pyproject.toml", check=False)
    lines = sorted(f.key for f in found)
    (OUT / f"mutmut-findings-{shard}.txt").write_text(
        "\n".join(lines) + ("\n" if lines else ""), "utf-8"
    )
    for line in broken:
        print(f"FAIL {line}")
    if lvl in (Level.WALK, Level.BASELINE) or os.environ.get("QMX_MUTATE_MODULES"):
        print(f"{len(found)} surviving mutants recorded (walk: not a gate)")
        return 1 if broken else 0
    verdict = ratchet_verdict("mutmut", found, None, f"mutmut-{shard}") if found else 0
    return 1 if broken or verdict else 0


def job_verdict() -> int:
    at = head()
    OUT.mkdir(parents=True, exist_ok=True)
    verdict = {
        "sha": at,
        "ref": os.environ.get("CI_COMMIT_REF_NAME", ""),
        "pipeline": os.environ.get("CI_PIPELINE_ID", ""),
        "level": level().value,
    }
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1) + "\n", "utf-8")
    print(json.dumps(verdict))
    return 0


def job_mr_gate() -> int:
    """A merge request into engine/base needs a green deep run on its exact head commit."""
    branch = os.environ["CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"]
    at = os.environ.get("CI_MERGE_REQUEST_SOURCE_BRANCH_SHA") or head()
    url = (
        f"{os.environ['CI_API_V4_URL']}/projects/{os.environ['CI_PROJECT_ID']}/jobs/artifacts/"
        f"{urllib.parse.quote(branch, safe='')}/raw/ci-out/verdict.json?job=deep-verdict"
    )
    token = {"JOB-TOKEN": os.environ["CI_JOB_TOKEN"]}
    request = urllib.request.Request(url, headers=token)  # noqa: S310 - GitLab's own API
    how = f"start one with: glab ci run -b {branch}, then rerun this job"
    try:
        with urllib.request.urlopen(request, timeout=60) as answer:  # noqa: S310 - GitLab's own API
            verdict = json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        print(
            f"FAIL no green deep run is the latest successful pipeline on {branch} "
            f"(HTTP {error.code}); {how}"
        )
        return 1
    if verdict.get("sha") != at:
        print(
            f"FAIL the last green deep run on {branch} tested {str(verdict.get('sha'))[:10]}, "
            f"not the head {at[:10]}; {how}"
        )
        return 1
    print(f"PASS deep run pipeline {verdict.get('pipeline')} is green on {at[:10]}")
    return 0


def job_smoke() -> int:
    """Start the host on a fresh folder, ask its status, stop it: each must exit 0."""
    sync(ci_units.AGENTS_WS)
    home = Path(tempfile.mkdtemp(prefix="qmx-smoke-")) / "home"
    agents = REPO / ci_units.AGENTS_WS
    host = [uv(), "run", "--frozen", "--no-sync", "python", "-m", "qmx_host"]
    steps = [
        ("start", [*host, "start", "--home", str(home), "--create", "--port", str(SMOKE_PORT)]),
        ("status", [*host, "status", "--home", str(home), "--port", str(SMOKE_PORT)]),
        ("stop", [*host, "stop", "--home", str(home), "--port", str(SMOKE_PORT)]),
    ]
    failed = [
        ratchet.Finding("qmx-agents/packages/qmx-host", 0, "smoke", f"{name} exited {rc}")
        for name, argv in steps
        if (rc := run(argv, agents, timeout=300)) != 0
    ]
    ratchet.write_junit(OUT / "junit" / f"smoke-{sys.platform}.xml", "smoke", failed)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "job",
        choices=[
            "tests",
            "lint",
            "fail-at-parent",
            "vulture",
            "skylos",
            "mutmut",
            "verdict",
            "mr-gate",
            "smoke",
        ],
    )
    parser.add_argument("--os", default="linux", choices=["linux", "windows"])
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        match args.job:
            case "tests":
                return job_tests(args.os)
            case "lint":
                return job_lint()
            case "fail-at-parent":
                return job_fail_at_parent()
            case "vulture":
                return job_vulture(args.write_baseline or level() == Level.BASELINE)
            case "skylos":
                return job_skylos(args.write_baseline or level() == Level.BASELINE)
            case "mutmut":
                return job_mutmut()
            case "verdict":
                return job_verdict()
            case "mr-gate":
                return job_mr_gate()
            case _:
                return job_smoke()
    except CiError as error:
        print(f"FAIL {error}", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
