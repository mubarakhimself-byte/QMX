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


@dataclasses.dataclass(frozen=True)
class TestRun:
    run: RunResult
    junit_ok: bool
    outcomes: dict[str, Outcome]

    def red(self) -> set[str]:
        return {k for k, v in self.outcomes.items() if v in (Outcome.ASSERTION, Outcome.FAILED, Outcome.ERROR)}

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


def run_packages(checkout: Path, packages: list[Package], out_dir: Path, timeout_s: float, settings: Settings,
                 tmp_root: Path, heartbeat: Path | None = None) -> dict[str, TestRun]:
    """Each package's setup, then its whole test command, at `checkout`. The CI seam."""
    runs: dict[str, TestRun] = {}
    for package in packages:
        if package.setup:
            run_timed(list(package.setup), checkout / package.root, out_dir / f"setup-{package.label}.log",
                      timeout_s, settings, tmp_root, heartbeat)
        runs[package.root] = run_tests(checkout, package, [], out_dir / f"test-{package.label}.log", timeout_s,
                                       settings, tmp_root, heartbeat)
    return runs


KNOWN_REDS = "ci/baselines/known-reds.txt"  # CI's list (tools/ci/pull_reds.py writes it): system|unit|class::name
SYSTEMS = ("linux", "windows")
MIRROR_HEADER = "# Generated by ship from"


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


@dataclasses.dataclass(frozen=True)
class Baseline:
    """The reds that do not block. With `ci/baselines/known-reds.txt` at the commit, that file is the
    one list for CI and for these scripts (baseline-reds.txt becomes its mirror and is never edited
    here); without it, baseline-reds.txt as before."""

    keys: frozenset[str]  # canonical
    source: str
    mirrored: bool

    def new(self, reds: set[str] | list[str]) -> list[str]:
        return sorted(r for r in reds if canon(r) not in self.keys)

    def known(self, ids: set[str] | list[str]) -> list[str]:
        return sorted(r for r in ids if canon(r) in self.keys)


def baseline_for(program: Program, repo: Path, at: str, timeout: float) -> Baseline:
    if git_rc(repo, "cat-file", "-e", f"{at}:{KNOWN_REDS}", timeout=timeout) == 0:
        text = git(repo, "show", f"{at}:{KNOWN_REDS}", timeout=timeout)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        old = program.baseline_reds.read_text("utf-8") if program.baseline_reds.exists() else ""
        if not old.startswith(MIRROR_HEADER) or read_baseline(program.baseline_reds) != set(lines):
            header = f"{MIRROR_HEADER} {KNOWN_REDS} at {at}. Edit that file (tools/ci/pull_reds.py), not this one."
            write_baseline(program.baseline_reds, set(lines), header)
        return Baseline(frozenset(canon(ln) for ln in lines), f"{KNOWN_REDS} at {at[:8]}", True)
    lines = read_baseline(program.baseline_reds)
    return Baseline(frozenset(canon(ln) for ln in lines), program.baseline_reds.name, False)


def read_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text("utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


def write_baseline(path: Path, reds: set[str], header: str = "") -> None:
    head = f"{header}\n" if header else ""
    path.write_text(head + "".join(f"{r}\n" for r in sorted(reds)), "utf-8", newline="\n")
