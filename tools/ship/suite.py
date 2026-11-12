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
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

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


def read_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text("utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


def write_baseline(path: Path, reds: set[str]) -> None:
    path.write_text("".join(f"{r}\n" for r in sorted(reds)), "utf-8", newline="\n")
