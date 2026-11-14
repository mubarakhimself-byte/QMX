"""The pluggable command map (checks.toml) and the one test backend land and nightly call.

checks.toml lists packages. Each has a `root` (a folder in the repo, "." for the whole repo) and any
of `setup`, `lint`, `types`, `test`, each an argv list run from the package root. In `test`, the
argument "{junit}" becomes the JUnit XML path and "{tests}" becomes the test files to run (none
means the whole package). A changed file belongs to the package with the longest matching root.

`run_packages` is the seam for CI: it takes a checkout and packages and returns each package's
outcomes. A CI backend replaces this one function and keeps the same return shape.
"""

from __future__ import annotations

import dataclasses
import enum
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from ship.gitx import git, git_rc
from ship.layout import Program
from ship.settings import Settings
from ship.wrapper import RunResult, run_timed

DEFAULT_TEST = ("python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={junit}", "{tests}")
ASSERTION_PREFIXES = ("assert", "AssertionError", "Failed: DID NOT RAISE", "Failed: DID NOT WARN")


@dataclasses.dataclass(frozen=True)
class Package:
    root: str
    setup: tuple[str, ...] = ()
    lint: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    test: tuple[str, ...] = DEFAULT_TEST
    vulture: tuple[tuple[str, ...], ...] = ()  # quality tools: each a list of argv, run in order
    skylos: tuple[tuple[str, ...], ...] = ()
    mutmut: tuple[tuple[str, ...], ...] = ()

    def quality(self, tool: str) -> tuple[tuple[str, ...], ...]:
        return getattr(self, tool)

    @property
    def label(self) -> str:
        return "root" if self.root == "." else self.root.replace("/", "-")

    def owns(self, path: str) -> bool:
        return self.root == "." or path == self.root or path.startswith(self.root.rstrip("/") + "/")

    def rel(self, path: str) -> str:
        return path if self.root == "." else path[len(self.root.rstrip("/")) + 1 :]


def load_packages(program: Program) -> list[Package]:
    if not program.checks_toml.exists():
        return [Package(".")]
    raw = tomllib.loads(program.checks_toml.read_text("utf-8")).get("package", [])
    packages = []
    for item in raw:
        unknown = set(item) - {"root", "setup", "lint", "types", "test", *QUALITY_KEYS}
        if unknown:
            raise SystemExit(f"checks.toml: unknown keys {sorted(unknown)} in package {item.get('root')}")
        values = {}
        for k, v in item.items():
            if k in QUALITY_KEYS:
                values[k] = tuple(tuple(a) for a in v) if v and isinstance(v[0], list) else (tuple(v),)
            else:
                values[k] = tuple(v) if isinstance(v, list) else v.replace("\\", "/").rstrip("/") or "."
        packages.append(Package(**values))
    return packages


QUALITY_KEYS = ("vulture", "skylos", "mutmut")


def setup_for(program: Program, paths: list[str] | None, logs: Path, heartbeat: Path | None = None):
    """A worktree.Setup for the packages `paths` touch (None: every package), logs under `logs`."""
    from ship.worktree import Setup

    packages = load_packages(program)
    chosen = packages if paths is None else touched(packages, paths)
    return Setup(tuple(p for p in chosen if p.setup), program.runs, logs, heartbeat)


def package_of(packages: list[Package], path: str) -> Package | None:
    owners = [p for p in packages if p.owns(path)]
    return max(owners, key=lambda p: 0 if p.root == "." else len(p.root), default=None)


def touched(packages: list[Package], paths: list[str]) -> list[Package]:
    found = {package_of(packages, p) for p in paths} - {None}
    return sorted(found, key=lambda p: p.root)


class Outcome(enum.StrEnum):
    PASSED = "passed"
    ASSERTION = "assertion-failure"
    FAILED = "failed-not-assertion"  # an exception other than an assertion: ImportError, NameError ...
    ERROR = "error"  # collection, import at module level, fixture setup
    SKIPPED = "skipped"


RED = frozenset({Outcome.ASSERTION, Outcome.FAILED, Outcome.ERROR})


@dataclasses.dataclass(frozen=True)
class TestRun:
    run: RunResult
    junit_ok: bool
    outcomes: dict[str, Outcome]
    again: dict[str, Outcome] = dataclasses.field(default_factory=dict)  # CI's one rerun of the reds

    def red(self) -> set[str]:
        """Every test red on the first run (a flaky one included; `Baseline.judge` tells them apart)."""
        return {k for k, v in self.outcomes.items() if v in RED}

    @property
    def clean(self) -> bool:
        return self.junit_ok and self.run.rc == 0 and not self.red()


def parse_junit(path: Path, prefix: str) -> dict[str, Outcome]:
    outcomes: dict[str, Outcome] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        test_id = f"{prefix}::{case.get('classname', '')}::{case.get('name', '')}"
        failure, error, skipped = case.find("failure"), case.find("error"), case.find("skipped")
        if error is not None or not case.get("classname"):
            outcomes[test_id] = Outcome.ERROR
        elif failure is not None:
            message = (failure.get("message") or "").lstrip()
            outcomes[test_id] = Outcome.ASSERTION if message.startswith(ASSERTION_PREFIXES) else Outcome.FAILED
        elif skipped is not None:
            outcomes[test_id] = Outcome.SKIPPED
        else:
            outcomes[test_id] = Outcome.PASSED
    return outcomes


def expand(argv: tuple[str, ...], junit: Path, tests: list[str]) -> list[str]:
    out: list[str] = []
    for arg in argv:
        if arg == "{tests}":
            out.extend(tests)
        else:
            out.append(arg.replace("{junit}", str(junit)))
    return out


def run_tests(checkout: Path, package: Package, tests: list[str], log: Path, timeout_s: float,
              settings: Settings, tmp_root: Path, heartbeat: Path | None = None) -> TestRun:
    junit = log.with_suffix(".junit.xml")
    junit.unlink(missing_ok=True)
    cwd = checkout / package.root
    result = run_timed(expand(package.test, junit, tests), cwd, log, timeout_s, settings, tmp_root, heartbeat)
    try:
        return TestRun(result, True, parse_junit(junit, package.root))
    except (OSError, ET.ParseError):
        return TestRun(result, False, {})


def red_files(checkout: Path, package: Package, reds: set[str]) -> list[str] | None:
    """The test files the red ids come from (JUnit's dotted class back to a file under the package root), or
    None when one cannot be found: then the whole package runs again."""
    files: set[str] = set()
    for test_id in reds:
        parts = test_id.split("::")
        dotted = parts[1] if len(parts) >= 3 else ""
        names = [x for x in dotted.split(".") if x]
        found = None
        for i in range(len(names), 0, -1):
            rel = "/".join(names[:i]) + ".py"
            if (checkout / package.root / rel).is_file():
                found = rel
                break
        if found is None:
            return None
        files.add(found)
    return sorted(files)


def rerun_reds(checkout: Path, package: Package, run: TestRun, log: Path, timeout_s: float, settings: Settings,
               tmp_root: Path, heartbeat: Path | None = None) -> TestRun:
    """qmx-ci's rerun (`qci.job_tests`): when a run has reds, those tests run once more, in the same place,
    and their second outcomes go in `again`. Their files run (every test of the package when a red's file
    cannot be found); only the reds' second outcomes are kept."""
    reds = run.red()
    if not reds:
        return run
    files = red_files(checkout, package, reds)
    second = run_tests(checkout, package, files or [], log.with_name(f"{log.stem}-rerun.log"), timeout_s, settings,
                       tmp_root, heartbeat)
    return dataclasses.replace(run, again={k: v for k, v in second.outcomes.items() if k in reds})


def run_packages(checkout: Path, packages: list[Package], out_dir: Path, timeout_s: float, settings: Settings,
                 tmp_root: Path, heartbeat: Path | None = None) -> dict[str, TestRun]:
    """Each package's setup, then its whole test command, at `checkout`, its reds run once more as qmx-ci
    does. The CI seam."""
    runs: dict[str, TestRun] = {}
    for package in packages:
        if package.setup:
            run_timed(list(package.setup), checkout / package.root, out_dir / f"setup-{package.label}.log",
                      timeout_s, settings, tmp_root, heartbeat)
        log = out_dir / f"test-{package.label}.log"
        first = run_tests(checkout, package, [], log, timeout_s, settings, tmp_root, heartbeat)
        runs[package.root] = rerun_reds(checkout, package, first, log, timeout_s, settings, tmp_root, heartbeat)
    return runs


KNOWN_REDS = "ci/baselines/known-reds.txt"  # CI's list (tools/ci/pull_reds.py writes it): system|unit|class::name
FLAKY = "ci/baselines/flaky.txt"  # CI's flaky list, the same key: red then green on CI's rerun, never blocks there
SYSTEMS = ("linux", "windows")


def this_system() -> str:
    return "windows" if sys.platform == "win32" else "linux"


def canon(test_id: str, system: str | None = None) -> str:
    """One spelling for a test id from either side: `system|root|class::name`.

    A local id is `<package root>::<class>::<name>` from this machine's JUnit report; a CI key is
    `<system>|<unit root>|<class>::<name>` (qmx-ci's reds files and known-reds.txt). The class loses any
    leading dotted form of its root (`qml.tests.test_x` under root `qml` is `tests.test_x`), because
    CI runs some units from the repo root and checks.toml runs every package from its own root."""
    head, sep, rest = test_id.partition("|")
    if sep and head in SYSTEMS:
        system, (root, _, tid) = head, rest.partition("|")
    else:
        system = system or this_system()
        root, _, tid = test_id.partition("::")
    cls, sep2, name = tid.partition("::")
    parts = [p for p in root.split("/") if p not in ("", ".")]
    for i in range(len(parts)):
        prefix = ".".join(parts[i:]) + "."
        if cls.startswith(prefix):
            cls = cls[len(prefix):]
            break
    return f"{system}|{root}|{cls}{sep2}{name}"


def local_id(test_id: str) -> str:
    """The local spelling (`root::class::name`) of any test id, for bisecting on this machine."""
    _, root, tid = canon(test_id).split("|", 2)
    return f"{root}::{tid}"


def system_of(test_id: str) -> str:
    return canon(test_id).split("|", 1)[0]


def in_touched_module(test_id: str, touched: Iterable[str] | None) -> bool:
    """qmx-ci's `in_touched_module`: the test's module is a file the change touched. The id's dotted class may
    start with any tail of the module's dotted repo path (JUnit names it from pytest's rootdir). `None` means
    the change is not known: every module counts as touched."""
    if touched is None:
        return True
    _, root, tid = canon(test_id).split("|", 2)
    classname = tid.split("::", 1)[0]
    roots = [p for p in root.split("/") if p not in ("", ".")]
    names = {classname, ".".join(roots + [classname])}
    for path in touched:
        owned = not roots or path == root or path.startswith(root.rstrip("/") + "/")  # CI's `unit.owns(path)`
        if not owned or not path.endswith(".py"):
            continue
        parts = path.removesuffix(".py").split("/")
        for i in range(len(parts)):
            dotted = ".".join(parts[i:])
            if any(name == dotted or name.startswith(dotted + ".") for name in names):
                return True
    return False


@dataclasses.dataclass(frozen=True)
class Judged:
    """One verdict on test runs, as qmx-ci's `split_flaky` and `tests_verdict` give it."""

    reds: list[str]  # red, and red again on the rerun (or not rerun)
    flaky: list[str]  # red, then passed on the rerun, in a module the change did not touch
    blocking: list[str]  # reds not in known-reds.txt, and flaky tests not in flaky.txt
    known: list[str]  # reds known-reds.txt names
    calm: list[str]  # flaky tests flaky.txt names


@dataclasses.dataclass(frozen=True)
class Baseline:
    """The reds that do not block, read from the repo (FACTORY-DESIGN 5, "One ratchet"):
    `ci/baselines/known-reds.txt` and `ci/baselines/flaky.txt`, the lists qmx-ci judges by. A commit without
    them has no known reds, so every red blocks. The kit never writes either file; a known red that passes
    is a NOTE (shrink the list with `tools/ci/pull_reds.py`).

    As in qmx-ci (D-L25): a red that stays red on its rerun blocks unless known-reds.txt names it; a red that
    passed on the rerun, in a module the change did not touch, is flaky, which blocks unless flaky.txt names
    it (a flaky red in a module the change touched is a red)."""

    known_reds: frozenset[str]  # canonical
    flaky: frozenset[str]  # canonical
    source: str

    def new(self, reds: set[str] | list[str]) -> list[str]:
        """Reds known-reds.txt does not name: these block (flaky.txt never excuses a red that stayed red)."""
        return sorted(r for r in reds if canon(r) not in self.known_reds)

    def judge(self, runs: Iterable[TestRun], touched: Iterable[str] | None = ()) -> Judged:
        """The verdict on runs whose reds were rerun once (`rerun_reds`; a GitHub shard's `again` holds what
        qmx-ci's flaky list says passed). `touched`: the files the change touched (None: not known)."""
        touched = None if touched is None else list(touched)
        reds, flaky = [], []
        for run in runs:
            for test_id in sorted(run.red()):
                if run.again.get(test_id) == Outcome.PASSED and not in_touched_module(test_id, touched):
                    flaky.append(test_id)
                else:
                    reds.append(test_id)
        blocking = sorted({r for r in reds if canon(r) not in self.known_reds}
                          | {f for f in flaky if canon(f) not in self.flaky})
        return Judged(sorted(reds), sorted(flaky), blocking, sorted(r for r in reds if canon(r) in self.known_reds),
                      sorted(f for f in flaky if canon(f) in self.flaky))

    def passing(self, ids: set[str] | list[str]) -> list[str]:
        """Known reds among tests that passed: the list can shrink."""
        return sorted(r for r in ids if canon(r) in self.known_reds)


def baseline_for(repo: Path, at: str, timeout: float) -> Baseline:
    """The repo's known reds and flaky tests at `at` (slice_checks reads them at the slice's parent, land at
    the batch's base, D-L25); a file missing there reads as empty."""
    def keys(path: str) -> frozenset[str]:
        if git_rc(repo, "cat-file", "-e", f"{at}:{path}", timeout=timeout) != 0:
            return frozenset()
        text = git(repo, "show", f"{at}:{path}", timeout=timeout)
        return frozenset(canon(ln.strip()) for ln in text.splitlines() if ln.strip() and not ln.startswith("#"))

    return Baseline(keys(KNOWN_REDS), keys(FLAKY), f"{KNOWN_REDS} at {at[:8]}")
