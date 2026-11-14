"""The one entry point every CI job calls: `python tools/ci/qci.py <job>`.

`.github/workflows/qmx-ci.yml` decides which jobs a run holds,
from `QMX_LEVEL`. This file decides what each job does at that level: which commit it compares
against, which tests a shard runs, and which findings are new. Every job writes what it found under
`ci-out/`, JUnit XML under `ci-out/junit/`. The host's own facts (head, shard, run number) come
from ci_host.

It also runs on a laptop: with no host variables the level is `deep` and the head is `HEAD`, so
`python tools/ci/qci.py vulture --write-baseline` rewrites a baseline from the same code CI runs.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import enum
import io
import json
import os
import re
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
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, cast

import ci_host
import ci_mutate
import ci_units
import guard
import ratchet
import tomllib

REPO = Path(__file__).resolve().parents[2]
GIT = shutil.which("git") or "git"
OUT = REPO / "ci-out"
BASELINES = REPO / "ci" / "baselines"
FLAKY_BASELINE = "flaky.txt"
BASELINE_REF = "baseline/"
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
    DEEP = "deep"  # a checkpoint (stop point), started by hand: `gh workflow run qmx-ci.yml`
    GATE = "gate"  # pull request into engine/base
    RELEASE = "release"  # tag v*
    WALK = "walk"  # one part of the scheduled whole-repo mutation walk
    BASELINE = "baseline"  # rewrite ci/baselines from this commit; the files are job artifacts


Scope = Literal["touched", "all"]
# The files a quality scan reported in full: "all", a set of paths, or None when it cannot say.
Covered = Literal["all"] | frozenset[str] | None
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


def facts() -> ci_host.RunFacts:
    return ci_host.read(os.environ)


def head() -> str:
    return facts().head or git("rev-parse", "HEAD").strip()


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


def tree_of(rev: str) -> str:
    """The tree a commit holds: two commits with the same tree test the same code."""
    return git("rev-parse", f"{rev}^{{tree}}").strip()


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
            before = facts().before
            if before and git_ok("cat-file", "-e", before):
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


def junit_cases(junit: Path) -> list[ET.Element]:
    """Every test case of a JUnit report that pytest wrote in CI; none when there is no report."""
    if not junit.exists():
        return []
    return list(ET.parse(junit).iter("testcase"))  # noqa: S314 - pytest wrote it in CI


def collection_errors(junit: Path) -> dict[str, str]:
    """Each test module pytest could not collect, named as JUnit names it (`dotted.module`), with
    its error's message and traceback."""
    found: dict[str, str] = {}
    for case in junit_cases(junit):
        error = case.find("error")
        if error is not None and not case.get("classname"):
            found[case.get("name", "")] = f"{error.get('message') or ''}\n{error.text or ''}"
    return found


MISSING_MODULE = re.compile(r"No module named '([\w.]+)'|cannot import name '\w+' from '([\w.]+)'")


def module_tails(path: str) -> set[str]:
    """Every dotted name a Python file may be imported or reported by: each tail of its path."""
    parts = path.removesuffix(".py").split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return {".".join(parts[i:]) for i in range(len(parts))}


def missing_new_module(error: str, added: Sequence[str]) -> bool:
    """Whether a collection error is a ModuleNotFoundError or ImportError naming a module that a
    file new in the change provides."""
    if "ModuleNotFoundError" not in error and "ImportError" not in error:
        return False
    named = {a or b for a, b in MISSING_MODULE.findall(error)}
    provided = {t for f in added if f.endswith(".py") for t in module_tails(f)}
    return bool(named & provided)


def excused_at_parent(
    test_id: str, new_tests: Sequence[str], errors: Mapping[str, str], added: Sequence[str]
) -> bool:
    """D-L19: a new test the parent could not collect counts as failing there only when its test
    file is new in the change and that file's collection error is a missing module the change
    adds. A test file that already existed and stops collecting at the parent is no excuse."""
    classname = test_id.split("::", 1)[0]
    for path in new_tests:
        tails = module_tails(path)
        if not any(classname == t or classname.startswith(t + ".") for t in tails):
            continue
        return any(
            name in tails and missing_new_module(text, added) for name, text in errors.items()
        )
    return False


def outcomes(junit: Path) -> dict[str, str]:
    """test id -> passed | skipped | assertion | failed | error (collection and setup errors)."""
    found: dict[str, str] = {}
    for case in junit_cases(junit):
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
    cwd: Path,
    files: list[str],
    junit: Path,
    *,
    serial: bool | None,
    workers: str = "auto",
    cache: Path | None = None,
    last_failed: bool = False,
    timeout_s: int | None = None,
    keep_going: bool = False,
) -> int:
    """Run pytest on `files` (relative to `cwd`) through an argument file, so a long shard never
    hits the Windows command-line limit. serial=None runs every test with no worker split. With a
    `cache` folder pytest records there what failed, and `last_failed` reruns only that.
    `timeout_s` stops any one test after that many seconds (pytest-timeout), so a hang is a red.
    `keep_going` runs the files that collect even when others do not (the parent of a change
    that adds a module cannot collect the new test files that import it)."""
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
        *(["-p", "no:cacheprovider"] if cache is None else ["-o", f"cache_dir={cache}"]),
        *(["--last-failed", "--last-failed-no-failures", "none"] if last_failed else []),
        *(["--timeout", str(timeout_s)] if timeout_s is not None else []),
        *(["--continue-on-collection-errors"] if keep_going else []),
        *split,
        "--basetemp",
        str(basetemp),
        "--junitxml",
        str(junit),
    ]
    return run(argv, cwd, env=test_env(), whole_env=True)


def test_env() -> dict[str, str]:
    """The job's environment without the host's own variables (see ci_host.HOST_PREFIXES)."""
    return ci_host.test_env(os.environ)


# ---- jobs -------------------------------------------------------------------------------------


def job_tests(system: str) -> int:
    """One shard of the tests this level asks for. Every shard plans the same split from the same
    inputs and takes its own part, so shards need no plan job."""
    lvl = level()
    at = head()
    index, total = facts().shard, facts().shards
    units = ci_units.discover(REPO)
    if TEST_SCOPE.get(lvl) == "all":
        base, changed, chosen = None, [], units
    else:
        base = base_for(lvl, at)
        changed = changed_files(base, at)
        chosen = ci_units.select(units, changed)
    touched = flaky_scope(lvl, at, changed)
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
    flaky: list[str] = []
    for unit, paths in sorted(grouped.items(), key=lambda item: item[0].root):
        stem = f"{system}-{index}-{unit.root.replace('/', '_')}"
        for serial in (False, True):
            name = f"{stem}{'-serial' if serial else ''}"
            junit = OUT / "junit" / f"{name}.xml"
            cache = Path(tempfile.mkdtemp(prefix="qmx-cache-"))
            rc = pytest(
                REPO / unit.cwd,
                sorted(paths),
                junit,
                serial=serial,
                cache=cache,
                timeout_s=PER_TEST_TIMEOUT_S,
            )
            if rc not in (0, 1, 5) or (rc == 1 and not junit.exists()):
                crashed.append(f"{unit.root}{' (serial)' if serial else ''}: pytest rc={rc}")
            first = outcomes(junit)
            again: dict[str, str] = {}
            if any(o in RED_OUTCOMES for o in first.values()):
                # Once, in this job, only the tests that were red (pytest's own last-failed list).
                rerun = OUT / "rerun" / f"{name}.xml"
                pytest(
                    REPO / unit.cwd,
                    sorted(paths),
                    rerun,
                    serial=serial,
                    cache=cache,
                    last_failed=True,
                    timeout_s=PER_TEST_TIMEOUT_S,
                )
                again = outcomes(rerun)
            red, flake = split_flaky(system, unit, first, again, touched)
            reds += red
            flaky += flake
    return tests_verdict(f"{system}-{index}", reds, crashed, flaky)


RED_OUTCOMES = frozenset({"assertion", "failed", "error"})
PER_TEST_TIMEOUT_S = 300


def flaky_scope(lvl: Level, at: str, changed: Sequence[str]) -> list[str]:
    """The files a flaky test's module must not be among for its rerun to count: what the change
    touched. A slice or landing run has them already; a whole-suite level measures them too."""
    if TEST_SCOPE.get(lvl) != "all":
        return list(changed)
    # The whole suite runs, but a flaky red still blocks in a module this change touched.
    touched = changed_files(base_for(lvl, at), at)
    return touched


def red_key(system: str, unit: ci_units.Unit, test_id: str) -> str:
    return f"{system}|{unit.root}|{test_id}"


def in_touched_module(unit: ci_units.Unit, test_id: str, touched: Sequence[str]) -> bool:
    """Whether a JUnit test id (`dotted.module[.Class]::name`) comes from a test module this change
    touched. JUnit names the module from pytest's rootdir, so any tail of the module's dotted repo
    path may start the id."""
    classname = test_id.split("::", 1)[0]
    for path in touched:
        if not unit.owns(path) or not path.endswith(".py"):
            continue
        parts = path.removesuffix(".py").split("/")
        for i in range(len(parts)):
            dotted = ".".join(parts[i:])
            if classname == dotted or classname.startswith(dotted + "."):
                return True
    return False


def split_flaky(
    system: str,
    unit: ci_units.Unit,
    first: Mapping[str, str],
    again: Mapping[str, str],
    touched: Sequence[str],
) -> tuple[list[str], list[str]]:
    """(reds, flaky) for one pytest run and its rerun. A red that passed on the rerun is flaky and
    does not block, unless its module is one this change touched: then it stays red."""
    reds: list[str] = []
    flaky: list[str] = []
    for test_id, outcome in sorted(first.items()):
        if outcome not in RED_OUTCOMES:
            continue
        key = red_key(system, unit, test_id)
        if again.get(test_id) == "passed" and not in_touched_module(unit, test_id, touched):
            flaky.append(key)
        else:
            reds.append(key)
    return reds, flaky


def tests_verdict(name: str, reds: list[str], crashed: list[str], flaky: Sequence[str] = ()) -> int:
    """Reds listed in ci/baselines/known-reds.txt (red on engine/base when it was taken) are
    reported and do not block; any other red, or a pytest that crashed, does. A flaky test (red,
    then green on its rerun) does not block only when ci/baselines/flaky.txt lists it; a newly
    flaky test blocks. A release allows no red at all: there known reds and flaky tests block too.
    The shard's reds and flaky tests are kept in reds-<name>.txt and flaky-<name>.txt."""
    release = level() == Level.RELEASE
    known: set[str] = set() if release else set(ratchet.read_baseline(BASELINES / "known-reds.txt"))
    calm: set[str] = set() if release else set(ratchet.read_baseline(BASELINES / FLAKY_BASELINE))
    new = sorted(r for r in set(reds) if r not in known)
    new_flaky = sorted(f for f in set(flaky) if f not in calm)
    rule = "release: every red blocks" if release else "the rest are in known-reds.txt"
    lines = [
        f"{len(set(reds))} red tests, {len(new)} blocking ({rule}); {len(set(flaky))} flaky, "
        f"{len(new_flaky)} not in {FLAKY_BASELINE}"
    ]
    lines += [f"FAIL {c}" for c in crashed]
    lines += [f"NEW RED {r}" for r in new]
    lines += [f"known red {r}" for r in sorted(set(reds) & known)]
    lines += [f"NEW FLAKY {r}" for r in new_flaky]
    lines += [f"FLAKY {r}" for r in sorted(set(flaky) & calm)]
    (OUT / f"reds-{name}.txt").write_text("".join(f"{r}\n" for r in sorted(set(reds))), "utf-8")
    (OUT / f"flaky-{name}.txt").write_text("".join(f"{r}\n" for r in sorted(set(flaky))), "utf-8")
    print("\n".join(lines))
    return 1 if new or crashed or new_flaky else 0


PYRIGHT_NUMBER = re.compile(r"\d+")


def pyright_report(text: str) -> dict[str, object]:
    """The JSON object `pyright --outputjson` printed. Anything printed before it (the PyPI
    wrapper's node set-up, a node deprecation warning) is skipped."""
    starts = [0] if text.startswith("{") else []
    starts += [m.end() - 1 for m in re.finditer(r"\n\{", text)]
    for offset in starts:
        try:
            found, _ = json.JSONDecoder().raw_decode(text, offset)
        except json.JSONDecodeError:
            continue
        if isinstance(found, dict) and "generalDiagnostics" in found:
            return cast("dict[str, object]", found)
    raise CiError("pyright printed no JSON report")


def pyright_findings(report: Mapping[str, object], root: Path = REPO) -> list[ratchet.Finding]:
    """Each pyright error as a ratchet finding keyed `path|rule|message`: the path repo-relative,
    the message on one line with every number stripped, so a moved line or a renumbered overload
    does not make an old error new. Warnings and information do not fail pyright and are left
    out."""
    found: list[ratchet.Finding] = []
    for raw in cast("list[object]", report.get("generalDiagnostics") or []):
        if not isinstance(raw, dict):
            continue
        item = cast("dict[str, object]", raw)
        if item.get("severity") != "error":
            continue
        file = Path(str(item.get("file") or ""))
        try:
            path = file.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            path = file.as_posix()
        message = " ".join(str(item.get("message") or "").split())
        start = cast("dict[str, dict[str, int]]", item.get("range") or {}).get("start", {})
        found.append(
            ratchet.Finding(
                path,
                int(start.get("line", -1)) + 1,
                str(item.get("rule") or "pyright"),
                PYRIGHT_NUMBER.sub("#", message),
            )
        )
    return found


def pyright_run(folder: str) -> tuple[list[ratchet.Finding], str | None]:
    """Run the folder's own pyright (the same config `poe types` reads) with JSON output. Returns
    its errors, and a failure line when pyright itself did not finish."""
    name = folder.replace("/", "_").replace(".", "root")
    raw = OUT / "pyright" / f"{name}.json"
    rc = run(
        [uv(), "run", "--frozen", "--no-sync", "python", "-m", "pyright", "--outputjson"],
        REPO / folder,
        stdout_to=raw,
    )
    if rc not in (0, 1):
        return [], f"pyright exited {rc} (see ci-out/pyright/{name}.json)"
    try:
        report = pyright_report(raw.read_text("utf-8", errors="replace"))
    except CiError as error:
        return [], f"{error} (rc={rc}, see ci-out/pyright/{name}.json)"
    return pyright_findings(report), None


def types_verdict(
    found: list[ratchet.Finding], scope: list[str] | None, complete: bool = True
) -> int:
    """pyright errors against ci/baselines/pyright.txt. A folder run twice (a workspace and its
    package) reports the same error once. When a folder's pyright did not finish (`complete` is
    false), nothing can be called gone."""
    unique = sorted(set(found), key=lambda f: (f.path, f.line, f.rule, f.message))
    # A slice's touched folders are checked whole, so its changed files are reported in full.
    covered: Covered = None if not complete else "all" if scope is None else frozenset(scope)
    return ratchet_verdict("pyright", unique, scope, covered=covered).rc


def job_lint(write_baseline: bool = False) -> int:
    """Format, lint and the repo scanners stay strict. Types join the ratchet: only a pyright error
    not in ci/baselines/pyright.txt blocks, and in a slice only one in a file the slice touched.
    At level baseline (or with --write-baseline) only types run, and they rewrite pyright.txt."""
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
    contract = not write_baseline and contract_due(lvl, changed)
    if not targets and not contract:
        print("no Python or project file changed; nothing to lint")
        return 0
    for workspace in sorted(
        {
            ci_units.AGENTS_WS if d.startswith(ci_units.AGENTS_WS) else ci_units.ROOT_WS
            for d in targets
        }
        | ({ci_units.AGENTS_WS} if contract else set())
    ):
        sync(workspace)
    tasks = () if write_baseline else ("fmt-check", "lint")
    steps = [(d, task) for d in targets for task in tasks]
    if ci_units.ROOT_WS in targets and not write_baseline:
        # The scanners the old GitHub battery ran beside lint, all of them over the root workspace.
        steps += [
            (ci_units.ROOT_WS, task)
            for task in ("money-path-scan", "ambient-scan", "mock-data-scan", "secret-scan")
        ]
    found: list[ratchet.Finding] = []
    for folder, task in steps:
        rc = run(
            [uv(), "run", "--frozen", "--no-sync", "python", "-m", "poethepoet", task],
            REPO / folder,
        )
        if rc != 0:
            found.append(ratchet.Finding(folder, 0, task, f"poe {task} failed (rc={rc})"))
    if contract:
        found += contract_findings()
    errors: list[ratchet.Finding] = []
    for folder in targets:
        some, failed = pyright_run(folder)
        errors += some
        if failed is not None:
            found.append(ratchet.Finding(folder, 0, "types", failed))
    ratchet.write_junit(OUT / "junit" / "lint.xml", "lint", found)
    for f in found:
        print(f"FAIL {f.text()}")
    if write_baseline:
        if found:
            return 1
        ratchet.write_baseline(
            BASELINES / "pyright.txt",
            sorted(set(errors), key=lambda f: (f.path, f.line, f.rule, f.message)),
            f"pyright errors from each folder's own config, run on {sys.platform}, over "
            f"{' '.join(targets)}.\nTaken at {at[:10]}. Key: path|rule|message, numbers in the "
            "message replaced by #; line numbers are left out.",
        )
        keep_baseline("pyright.txt")
        print(f"wrote {len(set(errors))} errors to ci/baselines/pyright.txt")
        return 0
    complete = not any(f.rule == "types" for f in found)
    verdict = types_verdict(errors, changed if lvl == Level.SLICE else None, complete)
    return 1 if found or verdict else 0


CONTRACT_INPUTS = ("qmx-agents/", "contracts/", "packages/", "qmn/", "tools/contract_dump.py")


def contract_due(lvl: Level, changed: Sequence[str]) -> bool:
    """Whether the lint job checks contracts/ against the code: in a slice, when the change touches
    the host's code, the packages and node it imports (`packages/`, `qmn/`), the contract files or
    their generator; at every other linting level except a baseline retake, always."""
    if lvl == Level.BASELINE:
        return False
    return lvl != Level.SLICE or any(p.startswith(CONTRACT_INPUTS) for p in changed)


def contract_findings() -> list[ratchet.Finding]:
    """`tools/contract_dump.py --check` in the agents workspace: one finding per stale contract
    line (each operation added, removed or changed), or one for a check that did not finish."""
    report = OUT / "contract.txt"
    argv = [uv(), "run", "--project", ci_units.AGENTS_WS, "--frozen", "--no-sync", "python"]
    rc = run([*argv, "tools/contract_dump.py", "--check"], REPO, stdout_to=report, timeout=900)
    text = report.read_text("utf-8", errors="replace") if report.exists() else ""
    print(text, end="")
    if rc == 0:
        return []
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.startswith("  ") or (line.startswith("contracts/") and not line.endswith(": stale"))
    ]
    if rc != 1 or not lines:
        return [ratchet.Finding("contracts", 0, "contract", f"contract check failed (rc={rc})")]
    return [ratchet.Finding("contracts", 0, "contract", f"stale: {line}") for line in lines]


def job_fail_at_parent() -> int:
    """Each new test case must fail at the parent on an assertion and pass at the head. An import,
    collection or setup error at the parent does not count as failing, with one exception
    (D-L19): a test file new in the change that the parent cannot collect only because a module
    the change adds is missing (`excused_at_parent`)."""
    lvl = level()
    at = head()
    base = base_for(lvl, at)
    changed = changed_files(base, at)
    describe(lvl, base, at, changed)
    if base is None:
        print("no parent to compare with")
        return 0
    present = set(git("ls-tree", "-r", "--name-only", at).splitlines())
    added = [p for p in changed if p in present and not git_ok("cat-file", "-e", f"{base}:{p}")]
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
            own_report = OUT / "fap" / f"{stem}-parent-own.xml"
            pytest(parent_copy / unit.cwd, own, own_report, serial=None, keep_going=True)
            before = outcomes(own_report)
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
        parent_report = OUT / "fap" / f"{stem}-parent.xml"
        pytest(parent_copy / unit.cwd, rel, parent_report, serial=None, keep_going=True)
        pytest(REPO / unit.cwd, rel, OUT / "junit" / f"fap-{stem}-head.xml", serial=None)
        at_parent = outcomes(OUT / "fap" / f"{stem}-parent.xml")
        errors = collection_errors(OUT / "fap" / f"{stem}-parent.xml")
        new_tests = [m for m in mods if m in added]
        at_head = outcomes(OUT / "junit" / f"fap-{stem}-head.xml")
        if not at_head:
            problems.append(
                ratchet.Finding(unit.root, 0, "fail-at-parent", "no JUnit report at the head")
            )
            continue
        new = sorted(k for k in at_head if k not in before and "::::" not in k)
        for test_id in new:
            p, h = at_parent.get(test_id, "not collected"), at_head[test_id]
            excused = p == "not collected" and excused_at_parent(test_id, new_tests, errors, added)
            why = " (a module the change adds)" if excused else ""
            log.append(f"{test_id} parent={p}{why} head={h}")
            if p != "assertion" and not excused:
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


@dataclasses.dataclass(frozen=True)
class Ratchet:
    """A tool's verdict: rc 1 when a new finding blocks, and the baseline keys it did not see."""

    rc: int
    gone: list[str]


def ratchet_verdict(
    tool: str,
    found: list[ratchet.Finding],
    scope: list[str] | None,
    report_as: str = "",
    covered: Covered = None,
) -> Ratchet:
    """New findings beyond `ci/baselines/<tool>.txt`. With a scope (a slice), only new findings in
    the changed files block. `covered` names the files this scan reported in full ("all" for a
    whole-repo scan, None when it cannot say): baseline keys there that it did not see are `gone`,
    printed as notes and written to ci-out/<tool>-ratchet.json for the summary and for prune."""
    baseline = ratchet.read_baseline(BASELINES / f"{tool}.txt")
    fresh = ratchet.new_findings(found, baseline)
    gone = (
        []
        if covered is None
        else ratchet.gone_keys(found, baseline, lambda p: covered == "all" or p in covered)
    )
    name = report_as or tool
    if scope is not None:
        wanted = set(scope)
        fresh = [dataclasses.replace(f, blocking=f.blocking and f.path in wanted) for f in fresh]
    blocking = [f for f in fresh if f.blocking]
    report = [
        f"{name}: {len(found)} findings, {len(fresh)} not in the baseline, {len(blocking)} "
        f"blocking, {len(gone)} baseline rows gone"
    ]
    report += [("BLOCK " if f.blocking else "note  ") + f.text() for f in fresh]
    report += [f"gone  {key}" for key in gone]
    (OUT / f"{name}-new.txt").write_text("\n".join(report) + "\n", "utf-8")
    at = head()
    record = {
        "tool": tool,
        "sha": at,
        "tree": tree_of(at),
        "complete": covered == "all",
        "new": [
            {"key": f.key, "file": f.path, "line": f.line, "blocking": f.blocking} for f in fresh
        ],
        "gone": gone,
    }
    (OUT / f"{name}-ratchet.json").write_text(json.dumps(record, indent=1) + "\n", "utf-8")
    ratchet.write_junit(OUT / "junit" / f"{name}.xml", name, fresh)
    print("\n".join(line for line in report if not line.startswith("note")))
    print(f"(notes, which do not block, are in ci-out/{name}-new.txt)")
    if gone:
        print(f"note: {len(gone)} baseline rows gone; `qci.py ratchet --prune` drops them")
    return Ratchet(1 if blocking else 0, gone)


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
    return ratchet_verdict("vulture", found, scope, covered="all").rc


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
            rel = repo_relative(path)
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


SKYLOS_PART_PREFIX = "skylos-part-"
# The baseline scan's parts, one top-level folder each: every tracked top-level folder holding code
# that [tool.skylos].exclude does not drop (a driver test keeps this list and the workflow's matrix
# complete), plus qmx-agents. qmx-ci.yml's skylos-part matrix lists the same names.
SKYLOS_FOLDERS = (
    "qmb",
    "qmn",
    "qml",
    "packages",
    "qmx-agents",
    "tools",
    "apps",
    "scripts",
    "extensions",
    "examples",
    "release",
)


def skylos_argv(target: str, report: Path, base: str | None) -> list[str]:
    argv = [
        uv(),
        "tool",
        "run",
        "--python",
        "3.14",
        "--from",
        SKYLOS,
        "skylos",
        target,
        "-a",
        "--no-upload",
        "--format",
        "json-ci",
        "-o",
        str(report),
    ]
    return [*argv, "--diff-base", base] if base is not None else argv


def skylos_base(lvl: Level, at: str) -> str | None:
    """A slice and a checkpoint scan only what changed: a slice since its fork point, a deep run
    since the merge-base with engine/base (the same commit mutate_targets measures from). Every
    other level scans the whole tree."""
    return base_for(lvl, at) if lvl in (Level.SLICE, Level.DEEP) else None


def repo_relative(path: str, root: Path = REPO) -> str:
    """A path Skylos reported, without the checkout's own absolute root: the root itself is `.`
    (a finding about the whole repo), a file under it is repo-relative, anything else is kept."""
    path = path.replace("\\", "/")
    base = root.as_posix().rstrip("/")
    if path == base:
        return "."
    if path.startswith(base + "/"):
        return path[len(base) + 1 :]
    return path.removeprefix("./")


def repo_path(folder: str, path: str, root: Path = REPO) -> str:
    """A path Skylos reported while scanning `folder`, made repo-relative: kept when it already
    is (or is the repo itself, `.`), prefixed with the folder when Skylos reported it relative to
    the scan target."""
    if path == "." or path.startswith(folder + "/") or not (root / folder / path).exists():
        return path
    return f"{folder}/{path}"


def job_skylos_part(folder: str) -> int:
    """One top-level folder of the baseline scan, so each part finishes under the step cap. Writes
    ci-out/skylos-part-<folder>.txt; `skylos-merge` joins the parts into ci/baselines/skylos.txt."""
    env = skylos_scope()
    report = OUT / f"skylos-{folder}.json"
    if not (REPO / folder).is_dir():
        print(f"{folder}: no such folder in this commit; empty part")
        found: list[ratchet.Finding] = []
    else:
        rc = run(skylos_argv(folder, report, None), REPO, env=env, timeout=40 * 60)
        if rc not in (0, 1) or not report.exists():
            raise CiError(f"skylos did not finish on {folder}: exit {rc}")
        found = [
            dataclasses.replace(f, path=repo_path(folder, f.path)) for f in skylos_findings(report)
        ]
    keys = sorted(f.key for f in found)
    part = OUT / f"{SKYLOS_PART_PREFIX}{folder}.txt"
    part.write_text("".join(f"{k}\n" for k in keys), "utf-8", newline="\n")
    print(f"{folder}: {len(keys)} findings")
    return 0


def skylos_merge(parts: Path, folders: Sequence[str], at: str) -> int:
    """Join every folder's part (found anywhere under `parts`) into ci/baselines/skylos.txt. A
    missing part is a failure: a baseline that silently skips a folder would let its findings in."""
    found = {
        p.stem.removeprefix(SKYLOS_PART_PREFIX): p
        for p in parts.rglob(f"{SKYLOS_PART_PREFIX}*.txt")
    }
    missing = sorted(set(folders) - set(found))
    if missing:
        raise CiError(f"no Skylos part for {', '.join(missing)}; the baseline is not written")
    # Skylos also reports repo-level files (the workflow, lockfiles) from every part, so a key
    # keeps the largest count any one part saw, not the sum over parts.
    counts: Counter[str] = Counter()
    for name in folders:
        counts |= Counter(ratchet.read_baseline(found[name]))
    keys = sorted(counts.elements())
    header = (
        f"Skylos {SKYLOS} `skylos <folder> -a --no-upload`, one part per top-level folder "
        f"({' '.join(folders)}), scope from [tool.skylos].\n"
        f"Taken at {at[:10]}. Key: path|category:rule|name; line numbers are left out."
    )
    target = BASELINES / "skylos.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"# {line}\n" for line in header.splitlines()) + "".join(f"{k}\n" for k in keys)
    target.write_text(body, "utf-8", newline="\n")
    keep_baseline("skylos.txt")
    print(f"wrote {len(keys)} findings from {len(folders)} parts to ci/baselines/skylos.txt")
    return 0


def job_skylos(write_baseline: bool) -> int:
    lvl = level()
    at = head()
    base = skylos_base(lvl, at)
    env = skylos_scope()
    report = OUT / "skylos.json"
    rc = run(skylos_argv(".", report, base), REPO, env=env, timeout=40 * 60)
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
    # A --diff-base scan may report only changed lines, so it cannot say what is gone.
    return ratchet_verdict("skylos", found, scope, covered="all" if base is None else None).rc


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


EPOCH_ORDINAL = datetime.date(1970, 1, 1).toordinal()


def walk_part_of(env: Mapping[str, str], parts: int) -> int:
    """The part a walk takes: `QMX_WALK_PART` when set, else the UTC day the run started on,
    `toordinal() % parts`, so the whole repo is walked once every `parts` nights. The day comes
    as `QMX_WALK_DAY` (days since 1970-01-01), which the workflow's level job reads from the
    runner's clock once for every shard of the run."""
    if env.get("QMX_WALK_PART"):
        return int(env["QMX_WALK_PART"]) % parts
    day = env.get("QMX_WALK_DAY")
    if not day:
        raise CiError("a walk needs QMX_WALK_DAY (set by the workflow) or QMX_WALK_PART")
    return (EPOCH_ORDINAL + int(day)) % parts


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
        part = walk_part_of(os.environ, parts)
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
    shard, total = facts().shard, facts().shards
    targets = mutate_targets(lvl, at)
    by_package: dict[str, list[ci_mutate.Target]] = {}
    for t in targets:
        by_package.setdefault(t.package, []).append(t)
    mine = [p for i, p in enumerate(sorted(by_package)) if i % total == shard - 1]
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(targets)} functions in {len(by_package)} packages; this shard: {mine}")
    found: list[ratchet.Finding] = []
    broken: list[str] = []
    counts: dict[str, int] = {}
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
        for status, count in statuses.items():
            counts[status] = counts.get(status, 0) + count
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
    (OUT / f"mutmut-counts-{shard}.json").write_text(json.dumps(counts) + "\n", "utf-8")
    (OUT / f"mutmut-findings-{shard}.txt").write_text(
        "\n".join(lines) + ("\n" if lines else ""), "utf-8"
    )
    for line in broken:
        print(f"FAIL {line}")
    if lvl == Level.WALK:
        record_walk(found, shard)
    if lvl in (Level.WALK, Level.BASELINE) or os.environ.get("QMX_MUTATE_MODULES"):
        print(f"{len(found)} surviving mutants recorded (walk: not a gate)")
        return 1 if broken else 0
    verdict = ratchet_verdict("mutmut", found, None, f"mutmut-{shard}").rc if found else 0
    return 1 if broken or verdict else 0


def record_walk(found: Sequence[ratchet.Finding], shard: int) -> None:
    """The walk is no gate. Its survivors beyond ci/baselines/mutmut.txt are recorded as notes
    (mutmut-<shard>-ratchet.json, each `blocking` false), so the run's summary.json lists them in
    `quality` with `blocks` false, where tools/ci/backlog.py reads them as backlog rows."""
    notes = [dataclasses.replace(f, blocking=False) for f in found]
    ratchet_verdict("mutmut", notes, None, f"mutmut-{shard}")


def job_verdict() -> int:
    at = head()
    OUT.mkdir(parents=True, exist_ok=True)
    verdict = {
        "sha": at,
        "tree": tree_of(at),
        "ref": facts().ref,
        "pipeline": facts().run_id,
        "host": facts().host.value,
        "level": level().value,
    }
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1) + "\n", "utf-8")
    print(json.dumps(verdict))
    return 0


WORKFLOW = "qmx-ci.yml"
VERDICT_ARTIFACT = "deep-verdict"


@dataclasses.dataclass(frozen=True)
class DeepRun:
    """One finished run that may vouch for a commit: where it is, and the verdict.json it left
    (None when it left none, as a run at any level other than deep does)."""

    url: str
    verdict: dict[str, object] | None


def gate_decision(
    at: str,
    runs: Sequence[DeepRun],
    how: str,
    head_ref: str = "",
    tree: str | None = None,
) -> tuple[bool, str]:
    """Pass only on a green deep run whose verdict names exactly the head under review (or, given
    `tree`, a commit holding the identical tree). A verdict from a baseline/** run vouches only for
    a pull request whose own head ref is baseline/** too. `runs` are the host's successful runs,
    newest first."""
    for candidate in runs:
        verdict = candidate.verdict
        if verdict is None or verdict.get("level") != "deep":
            continue
        if str(verdict.get("ref", "")).startswith(BASELINE_REF) and not head_ref.startswith(
            BASELINE_REF
        ):
            continue
        if verdict.get("sha") == at:
            return True, f"PASS deep run {candidate.url} is green on {at[:10]}"
        if tree is not None and verdict.get("tree") == tree:
            return True, (
                f"PASS deep run {candidate.url} is green on {str(verdict.get('sha'))[:10]}, "
                f"whose tree is the tree of {at[:10]}"
            )
    if runs:
        return False, (
            f"FAIL {len(runs)} green run(s) on {at[:10]}, but none is a deep run with a verdict "
            f"for that commit; {how}"
        )
    return False, f"FAIL no green deep run tested the head {at[:10]}; {how}"


def github_api(path: str, token: str, raw: bool = False) -> bytes:
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    url = path if path.startswith("https://") else f"{api}{path}"
    request = urllib.request.Request(url)  # noqa: S310 - GitHub's own API
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    # Not forwarded on a redirect: an artifact download redirects to blob storage, which refuses
    # a second credential beside its own signed URL.
    request.add_unredirected_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=120) as answer:  # noqa: S310 - GitHub's own API
        return cast("bytes", answer.read())


def github_deep_runs(repo: str, at: str | None, token: str) -> list[DeepRun]:
    """Successful hand-started runs and their deep verdicts: on commit `at`, or, with `at` None,
    the latest 30 on any commit (a release matches them by tree)."""
    fields = {"event": "workflow_dispatch", "status": "success", "per_page": "20" if at else "30"}
    query = urllib.parse.urlencode({"head_sha": at, **fields} if at else fields)
    listing = json.loads(
        github_api(f"/repos/{repo}/actions/workflows/{WORKFLOW}/runs?{query}", token)
    )
    found: list[DeepRun] = []
    for run_ in cast("list[dict[str, object]]", listing.get("workflow_runs", [])):
        if (at is not None and run_.get("head_sha") != at) or run_.get("conclusion") != "success":
            continue
        arts = json.loads(
            github_api(
                f"/repos/{repo}/actions/runs/{run_['id']}/artifacts?name={VERDICT_ARTIFACT}", token
            )
        )
        verdict: dict[str, object] | None = None
        for art in cast("list[dict[str, object]]", arts.get("artifacts", [])):
            if art.get("name") != VERDICT_ARTIFACT or art.get("expired"):
                continue
            blob = github_api(str(art["archive_download_url"]), token)
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                verdict = json.loads(archive.read("verdict.json").decode("utf-8"))
        found.append(DeepRun(str(run_.get("html_url", run_["id"])), verdict))
    return found


DOCS_ONLY_FILES = frozenset({"contracts/CHANGELOG.md"})


NOT_DOCS_SEGMENTS = frozenset({"src", "tests", "fixtures", "examples"})


def is_docs(path: str) -> bool:
    """Documentation only: under docs/, the contracts changelog, or Markdown, and never inside a
    src, tests, fixtures or examples folder (Markdown there can be code's input or output)."""
    if NOT_DOCS_SEGMENTS & set(path.split("/")[:-1]):
        return False
    return path.startswith("docs/") or path in DOCS_ONLY_FILES or path.endswith(".md")


def gate_checks(changed: Sequence[str]) -> tuple[str, ...]:
    """What the gate needs for a pull request's change: docs-lint alone when it touches only
    documentation, otherwise a green deep run of its exact head (which already ran the suites,
    docker-node and the qmn lane, so the gate reruns none of them)."""
    if changed and all(is_docs(p) for p in changed):
        return ("docs-lint",)
    return ("deep-verdict",)


MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CONFLICT = re.compile(r"^(<{7}|>{7})( |$)", re.M)


def docs_findings(files: Sequence[str], root: Path = REPO) -> list[ratchet.Finding]:
    """For each Markdown file: it reads as UTF-8, holds no merge-conflict marker, and every relative
    link points at a file or folder that exists."""
    found: list[ratchet.Finding] = []
    for rel in files:
        path = root / rel
        if not rel.endswith(".md") or not path.is_file():
            continue
        try:
            text = path.read_text("utf-8")
        except UnicodeDecodeError:
            found.append(ratchet.Finding(rel, 0, "docs-lint", "not UTF-8"))
            continue
        for match in CONFLICT.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            found.append(ratchet.Finding(rel, line, "docs-lint", "merge-conflict marker"))
        for match in MD_LINK.finditer(text):
            target = match.group(1).split("#", 1)[0].split("?", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            where = root / target.lstrip("/") if target.startswith("/") else path.parent / target
            if not where.exists():
                line = text.count("\n", 0, match.start()) + 1
                found.append(ratchet.Finding(rel, line, "docs-lint", f"broken link {target}"))
    return found


def job_docs_lint() -> int:
    lvl = level()
    at = head()
    base = base_for(lvl, at)
    changed = changed_files(base, at)
    describe(lvl, base, at, changed)
    found = docs_findings(changed, REPO)
    ratchet.write_junit(OUT / "junit" / "docs-lint.xml", "docs-lint", found)
    for f in found:
        print(f"FAIL {f.text()}")
    print(f"docs-lint: {len([p for p in changed if p.endswith('.md')])} Markdown files checked")
    return 1 if found else 0


def deep_verdict_runs(at: str, by_tree: bool = False) -> tuple[list[DeepRun], str]:
    run_facts = facts()
    if run_facts.host == ci_host.Host.LAPTOP:
        raise CiError("the gate reads the CI host's runs; it does not run on a laptop")
    how = (
        f"start one with: gh workflow run {WORKFLOW} --ref {run_facts.ref}; when it is green, "
        "rerun this job"
    )
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    repo = os.environ["GITHUB_REPOSITORY"]
    runs = github_deep_runs(repo, at, token)
    if by_tree:
        runs += github_deep_runs(repo, None, token)
    return runs, how


def loosening(base: str, at: str, branch: str) -> list[str]:
    """What the change from `base` loosens (guard.py), printed one FAIL line each."""
    found = guard.problems(REPO, base, at, branch)
    for line in found:
        print(f"FAIL loosens the ratchet: {line}")
    return found


def job_gate() -> int:
    """A pull request into engine/base must loosen nothing the ratchet holds (guard.py, run from the
    base branch's own copy of this driver), and needs a green deep run on its exact head commit,
    or, when it changes documentation only, a clean docs-lint."""
    at = head()
    base = base_for(Level.GATE, at)
    if base is None:
        raise CiError(f"no merge-base with {ENGINE}")
    if loosening(base, at, facts().ref):
        return 1
    checks = gate_checks(changed_files(base, at))
    print(f"gate checks: {', '.join(checks)}")
    if checks == ("docs-lint",):
        return job_docs_lint()
    runs, how = deep_verdict_runs(at)
    ok, message = gate_decision(at, runs, how, head_ref=facts().ref)
    print(message)
    return 0 if ok else 1


def release_problems(at: str, released_from: Sequence[str], deep_ok: bool) -> list[str]:
    """Why a tagged commit may not be released: it is on none of the branches a release may come
    from (engine/base, release/v*), or no green deep run vouches for it."""
    problems: list[str] = []
    if not any(git_ok("merge-base", "--is-ancestor", at, ref) for ref in released_from):
        problems.append(
            f"{at[:10]} is not on {ENGINE} or a release/v* branch "
            f"(checked: {', '.join(released_from) or 'none fetched'})"
        )
    if not deep_ok:
        problems.append(f"no green deep run vouches for {at[:10]}")
    return problems


def job_release_verdict() -> int:
    at = head()
    if os.environ.get("CI"):
        git(
            "fetch",
            "--quiet",
            "origin",
            f"+refs/heads/{ENGINE}:refs/remotes/origin/{ENGINE}",
            "+refs/heads/release/*:refs/remotes/origin/release/*",
        )
    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        f"refs/remotes/origin/{ENGINE}",
        "refs/remotes/origin/release/v*",
    ).split()
    runs, how = deep_verdict_runs(at, by_tree=True)
    deep_ok, message = gate_decision(at, runs, how, tree=tree_of(at))
    print(message)
    problems = release_problems(at, refs, deep_ok)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        print(f"PASS {at[:10]} may be released")
    return 1 if problems else 0


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


# ---- the run summary --------------------------------------------------------------------------

LEVEL_IF = re.compile(
    r"contains\(fromJSON\('\[([^\]]*)\]'\),\s*needs\.level\.outputs\.level\)"
    r"|needs\.level\.outputs\.level\s*==\s*'([a-z]+)'"
)


def workflow_jobs(workflow: str) -> dict[str, str]:
    """Each job id in qmx-ci.yml with its `if:` (empty when it has none)."""
    jobs: dict[str, str] = {}
    body = workflow.split("\njobs:\n", 1)[1]
    current = ""
    for line in body.splitlines():
        if re.fullmatch(r"  [a-z][a-z0-9-]*:", line):
            current = line.strip().rstrip(":")
            jobs[current] = ""
        elif current and line.startswith("    if: ") and not jobs[current]:
            jobs[current] = line.removeprefix("    if: ")
    return jobs


def job_levels(condition: str) -> set[str]:
    """The levels a job's `if:` admits, read from the two forms qmx-ci.yml uses."""
    found: set[str] = set()
    for listed, single in LEVEL_IF.findall(condition):
        found |= {x.strip().strip('"') for x in listed.split(",") if x.strip()} | (
            {single} if single else set()
        )
    return found


def level_jobs(workflow: str, lvl: Level) -> list[str]:
    """The jobs a run at this level holds, from the workflow's own conditions."""
    return [job for job, cond in workflow_jobs(workflow).items() if lvl.value in job_levels(cond)]


def read_lines(path: Path) -> list[str]:
    return [line for line in path.read_text("utf-8").splitlines() if line]


def build_summary(
    *,
    sha: str,
    ref: str,
    run_id: str,
    url: str,
    lvl: Level,
    jobs_of_level: Sequence[str],
    needs: Mapping[str, Mapping[str, object]],
    api_jobs: Sequence[Mapping[str, object]] | None,
    artifacts: Path,
    known_reds: Sequence[str],
    known_flaky: Sequence[str] = (),
) -> dict[str, object]:
    """summary.json (factory design 11.11): every job of the level (named as its artifact is,
    `suite-linux-3`), every red (new, known, flaky, or a test shard that never finished, each with
    `blocks`), every new and gone quality row (`blocks` is false for a note), mutant counts, the
    level's skipped jobs. A red id is `unit|module::name`; an unfinished shard's is
    `shard <system>-<n>`."""
    result = {job: str(needs.get(job, {}).get("result", "missing")) for job in jobs_of_level}
    jobs: list[dict[str, object]]
    if api_jobs is None:
        jobs = [{"name": job, "result": result[job], "seconds": 0} for job in jobs_of_level]
    else:
        jobs = []
        for item in api_jobs:
            name = str(item.get("name", ""))
            if name.split(" ", 1)[0] not in result:
                continue
            seconds = 0
            started, completed = item.get("started_at"), item.get("completed_at")
            if isinstance(started, str) and isinstance(completed, str):
                span = datetime.datetime.fromisoformat(completed) - datetime.datetime.fromisoformat(
                    started
                )
                seconds = max(0, int(span.total_seconds()))
            outcome = item.get("conclusion") or item.get("status") or "unknown"
            jobs.append(
                {"name": name.replace(" ", "-"), "result": str(outcome), "seconds": seconds}
            )
    release = lvl == Level.RELEASE
    known, calm = set(known_reds), set(known_flaky)
    reds: list[dict[str, object]] = []
    finished: set[str] = set()
    for path in sorted(artifacts.rglob("reds-*.txt")):
        finished.add(path.stem.removeprefix("reds-"))
        for key in read_lines(path):
            system, _, rest = key.partition("|")
            kind = "known" if key in known else "new"
            blocks = kind == "new" or release
            reds.append({"id": rest, "system": system, "kind": kind, "blocks": blocks})
    for path in sorted(artifacts.rglob("flaky-*.txt")):
        for key in read_lines(path):
            system, _, rest = key.partition("|")
            blocks = release or key not in calm
            reds.append({"id": rest, "system": system, "kind": "flaky", "blocks": blocks})
    for shard in sorted(unfinished_shards(artifacts, jobs, finished)):
        reds.append(
            {
                "id": f"shard {shard}",
                "system": shard.split("-", 1)[0],
                "kind": "unfinished",
                "blocks": True,
            }
        )
    quality: list[dict[str, object]] = []
    for path in sorted(artifacts.rglob("*-ratchet.json")):
        record = cast("dict[str, object]", json.loads(path.read_text("utf-8")))
        tool = str(record["tool"])
        for item in cast("list[dict[str, object]]", record.get("new", [])):
            key, file = str(item["key"]), str(item["file"])
            blocks = bool(item.get("blocking", True))
            quality.append(
                {"tool": tool, "key": key, "file": file, "kind": "new", "blocks": blocks}
            )
        for key in cast("list[str]", record.get("gone", [])):
            file = key.split("|", 1)[0]
            quality.append(
                {"tool": tool, "key": key, "file": file, "kind": "gone", "blocks": False}
            )
    killed = survived = 0
    for path in sorted(artifacts.rglob("mutmut-counts-*.json")):
        counts = cast("dict[str, int]", json.loads(path.read_text("utf-8")))
        killed += counts.get("killed", 0)
        survived += sum(n for s, n in counts.items() if s in ci_mutate.SURVIVING)
    new_survivors = sum(1 for q in quality if q["tool"] == "mutmut" and q["kind"] == "new")
    return {
        "sha": sha,
        "ref": ref,
        "run_id": int(run_id) if run_id.isdigit() else run_id,
        "url": url,
        "level": lvl.value,
        "green": bool(jobs_of_level) and all(r == "success" for r in result.values()),
        "jobs": jobs,
        "reds": reds,
        "quality": quality,
        "mutants": {"killed": killed, "survived": survived, "new_survivors": new_survivors},
        "skipped": sorted(job for job, r in result.items() if r == "skipped"),
    }


TEST_JOBS = ("suite-linux", "suite-windows", "tests-linux", "tests-windows")


def unfinished_shards(
    artifacts: Path, jobs: Sequence[Mapping[str, object]], finished: set[str]
) -> set[str]:
    """Test shards (`<system>-<n>`) that left no reds file: one that planned tests and stopped, and
    one whose job did not succeed (cancelled, timed out) and wrote nothing."""
    missing: set[str] = set()
    for path in artifacts.rglob("plan-*.json"):
        plan = cast("dict[str, object]", json.loads(path.read_text("utf-8")))
        shard = path.stem.removeprefix("plan-")
        if plan.get("files") and shard not in finished:
            missing.add(shard)
    for job in jobs:
        name = str(job.get("name", ""))
        base, _, index = name.rpartition("-")
        if base in TEST_JOBS and index.isdigit() and job.get("result") != "success":
            shard = f"{base.split('-', 1)[1]}-{index}"
            if shard not in finished:
                missing.add(shard)
    return missing


def summary_markdown(summary: Mapping[str, object]) -> str:
    jobs = cast("list[dict[str, object]]", summary["jobs"])
    reds = cast("list[dict[str, object]]", summary["reds"])
    quality = cast("list[dict[str, object]]", summary["quality"])
    mutants = cast("dict[str, int]", summary["mutants"])
    skipped = cast("list[str]", summary["skipped"])
    verdict = "GREEN" if summary["green"] else "RED"
    lines = [
        f"## CI {summary['level']} {str(summary['sha'])[:10]}: {verdict}",
        "",
        f"Run: {summary['url']}",
        "",
        "| Job | Result | Seconds |",
        "|---|---|---|",
        *[f"| {j['name']} | {j['result']} | {j['seconds']} |" for j in jobs],
        "",
    ]
    kinds = ("new", "known", "flaky", "unfinished")
    by_kind = {k: [r for r in reds if r["kind"] == k] for k in kinds}
    blocking = sum(1 for r in reds if r.get("blocks"))
    lines.append(
        f"Reds: {len(by_kind['new'])} new, {len(by_kind['known'])} known, "
        f"{len(by_kind['flaky'])} flaky, {len(by_kind['unfinished'])} unfinished shards; "
        f"{blocking} block"
    )
    lines += [
        f"- {r['kind']}{' (blocks)' if r.get('blocks') else ''} {r['system']} {r['id']}"
        for r in reds
        if r["kind"] != "known" or r.get("blocks")
    ]
    new_quality = [q for q in quality if q["kind"] == "new"]
    gone = len(quality) - len(new_quality)
    lines += ["", f"Quality: {len(new_quality)} new rows, {gone} baseline rows gone"]
    lines += [f"- {q['tool']} {q['key']}" for q in new_quality]
    lines += [
        "",
        f"Mutants: {mutants['killed']} killed, {mutants['survived']} survived, "
        f"{mutants['new_survivors']} new survivors",
        "",
        f"Skipped: {', '.join(skipped) or 'none'}",
    ]
    return "\n".join(lines) + "\n"


def run_jobs(repo: str, run_id: str) -> list[dict[str, object]] | None:
    """This run's job list from GitHub (names, conclusions, times), or None when it cannot be read;
    the summary then takes results from `needs`."""
    credential = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not (repo and run_id and credential):
        return None
    try:
        raw = github_api(f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100", credential)
    except (urllib.error.URLError, OSError):
        return None
    listing = cast("dict[str, object]", json.loads(raw))
    return cast("list[dict[str, object]]", listing.get("jobs", []))


def job_summary(artifacts: Path) -> int:
    """Always runs, after every job of the run. Writes ci-out/summary.json and summary.md from the
    level's artifacts, `QMX_NEEDS` (the workflow's toJSON(needs)) and the run's job list. It
    reports; it never fails the run (the deep-verdict job is the green stamp the gate reads)."""
    run_facts = facts()
    lvl = level()
    workflow = (REPO / ".github" / "workflows" / WORKFLOW).read_text("utf-8")
    needs = cast("dict[str, dict[str, object]]", json.loads(os.environ.get("QMX_NEEDS") or "{}"))
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    api_jobs = run_jobs(repo, run_facts.run_id)
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    summary = build_summary(
        sha=head(),
        ref=run_facts.ref,
        run_id=run_facts.run_id,
        url=f"{server}/{repo}/actions/runs/{run_facts.run_id}" if repo else "",
        lvl=lvl,
        jobs_of_level=level_jobs(workflow, lvl),
        needs=needs,
        api_jobs=api_jobs,
        artifacts=artifacts,
        known_reds=ratchet.read_baseline(BASELINES / "known-reds.txt"),
        known_flaky=ratchet.read_baseline(BASELINES / FLAKY_BASELINE),
    )
    text = summary_markdown(summary)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", "utf-8")
    (OUT / "summary.md").write_text(text, "utf-8")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


# ---- the ratchet: guard and prune -------------------------------------------------------------


PRUNE_TOOLS = ("vulture", "skylos", "mutmut", "pyright")
SHRINK_AT_BASELINE_ONLY = frozenset({"skylos", "mutmut"})


def prune_gone(tool: str, out: Path) -> tuple[list[str], str]:
    """The gone keys for one tool, and where they came from: every <tool>-ratchet.json under `out`
    taken at this checkout's commit or tree (a key keeps the largest count any one record saw;
    records from another commit are stale and skipped), or else a fresh run of the tool when it
    can run here. Skylos and mutmut shrink only at the baseline level and the scheduled walk;
    pyright's baseline is Linux's, so it reruns only on Linux, and only over the folders the
    change since engine/base touched."""
    if tool in SHRINK_AT_BASELINE_ONLY:
        return [], f"{tool} shrinks only at the baseline level and the scheduled walk"
    at = head()
    current = {at, tree_of(at)}
    gone: Counter[str] = Counter()
    records = stale = 0
    for path in sorted(out.rglob("*-ratchet.json")):
        record = cast("dict[str, object]", json.loads(path.read_text("utf-8")))
        if record.get("tool") != tool:
            continue
        if not current & {record.get("sha"), record.get("tree")}:
            stale += 1
            continue
        records += 1
        gone |= Counter(cast("list[str]", record.get("gone", [])))
    if records or stale:
        return sorted(gone.elements()), (
            f"{records} result file(s) in {out.name}, {stale} stale one(s) skipped"
        )
    if tool == "vulture":
        return ratchet_verdict("vulture", vulture_findings(), None, covered="all").gone, "a run"
    if tool == "pyright" and sys.platform.startswith("linux"):
        fetch_refs(build_branches=False)
        at = head()
        changed = changed_files(merge_base(at, f"refs/remotes/origin/{ENGINE}"), at)
        errors: list[ratchet.Finding] = []
        for folder in ci_units.lint_targets(changed, ci_units.poe_dirs(REPO)):
            some, failed = pyright_run(folder)
            if failed is not None:
                raise CiError(failed)
            errors += some
        found = sorted(set(errors), key=lambda f: (f.path, f.line, f.rule, f.message))
        result = ratchet_verdict("pyright", found, None, covered=frozenset(changed))
        return result.gone, "a run over the changed files"
    return [], f"no {tool} results in {out.name} and no run here"


def ratchet_prune(tools: Sequence[str], out: Path) -> int:
    """Drop gone rows from each baseline file. Prints `PRUNED <tool> <n>`; never adds a row."""
    for tool in tools:
        gone, source = prune_gone(tool, out)
        removed = ratchet.prune(BASELINES / f"{tool}.txt", gone)
        print(f"PRUNED {tool} {removed} (from {source})")
    return 0


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
            "gate",
            "release-verdict",
            "docs-lint",
            "smoke",
            "skylos-part",
            "skylos-merge",
            "summary",
            "ratchet",
        ],
    )
    parser.add_argument("--os", default="linux", choices=["linux", "windows"])
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--part", choices=SKYLOS_FOLDERS, help="skylos-part: the folder to scan")
    parser.add_argument(
        "--parts", type=Path, default=OUT / "parts", help="skylos-merge: where the parts were put"
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=OUT / "artifacts",
        help="summary: where the level's artifacts were downloaded",
    )
    parser.add_argument("--prune", action="store_true", help="ratchet: drop gone baseline rows")
    parser.add_argument(
        "--tools", nargs="+", choices=PRUNE_TOOLS, default=list(PRUNE_TOOLS), help="ratchet"
    )
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        match args.job:
            case "tests":
                return job_tests(args.os)
            case "lint":
                return job_lint(args.write_baseline or level() == Level.BASELINE)
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
            case "gate":
                return job_gate()
            case "release-verdict":
                return job_release_verdict()
            case "docs-lint":
                return job_docs_lint()
            case "skylos-part":
                if args.part is None:
                    raise CiError("skylos-part needs --part <folder>")
                return job_skylos_part(args.part)
            case "skylos-merge":
                return skylos_merge(args.parts, SKYLOS_FOLDERS, head())
            case "summary":
                return job_summary(args.artifacts)
            case "ratchet":
                if not args.prune:
                    raise CiError("ratchet does one thing so far: --prune")
                return ratchet_prune(args.tools, OUT)
            case _:
                return job_smoke()
    except CiError as error:
        print(f"FAIL {error}", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
