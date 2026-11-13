"""The repo's test units: which files each one owns, its test files, and how they shard.

A unit is the smallest thing CI tests on its own: one root-workspace area (`packages/qmf-core`,
`qmn`, `tools`, one `qa/tests/epic_*` folder) or one `qmx-agents` package or app. Its `cwd` is
where pytest runs, and it prefixes every JUnit test id, so the ship scripts can map a result back
to the package that owns it.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath

ROOT_WS = "."
AGENTS_WS = "qmx-agents"
WORKSPACES = (ROOT_WS, AGENTS_WS)
WORKSPACE_FILES = frozenset({"pyproject.toml", "uv.lock", "conftest.py"})
EVERYTHING_FILES = frozenset({".python-version"})
PYTHON_SUFFIXES = (".py", ".pyi")
CI_BASELINES = "ci/baselines/"
SECONDS_PER_TEST = (
    1.0  # wall seconds per test on a 2-vCPU runner with two workers, until durations exist
)
SECONDS_PER_FILE = 2.0  # collection and start-up per test file


@dataclasses.dataclass(frozen=True)
class Unit:
    root: str
    workspace: str
    cwd: str
    tests: tuple[str, ...]

    def owns(self, path: str) -> bool:
        return path == self.root or path.startswith(self.root.rstrip("/") + "/")


@dataclasses.dataclass(frozen=True)
class TestFile:
    unit: Unit
    path: str  # relative to the unit's cwd, forward slashes
    weight: float


def _rel(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()


def _has_tests(folder: Path) -> bool:
    return folder.is_dir() and any(_is_test_file(p.name) for p in folder.rglob("*.py"))


def _is_test_file(name: str) -> bool:
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def discover(repo: Path) -> list[Unit]:
    units: list[Unit] = []
    for parent in ("packages", "extensions"):
        for folder in sorted((repo / parent).glob("*")):
            if _has_tests(folder):
                root = _rel(folder, repo)
                units.append(Unit(root, ROOT_WS, ROOT_WS, (root,)))
    for name in ("qml", "qmb", "qmn"):
        if _has_tests(repo / name):
            units.append(Unit(name, ROOT_WS, ROOT_WS, (name,)))
    if _has_tests(repo / "tools" / "tests"):
        units.append(Unit("tools", ROOT_WS, ROOT_WS, ("tools/tests",)))
    qa = repo / "qa" / "tests"
    gates = sorted(_rel(p, repo) for p in qa.glob("test_*.py"))
    if gates:
        units.append(Unit("qa/tests", ROOT_WS, ROOT_WS, tuple(gates)))
    for folder in sorted(qa.glob("epic_*")):
        if _has_tests(folder):
            root = _rel(folder, repo)
            units.append(Unit(root, ROOT_WS, ROOT_WS, (root,)))
    agents = repo / AGENTS_WS
    for folder in sorted((agents / "packages").glob("*")):
        if _has_tests(folder / "tests"):
            root = _rel(folder, repo)
            units.append(Unit(root, AGENTS_WS, root, ("tests",)))
    for folder in sorted((agents / "apps").glob("*")):
        if _has_tests(folder / "tests"):
            units.append(
                Unit(_rel(folder, repo), AGENTS_WS, AGENTS_WS, (f"apps/{folder.name}/tests",))
            )
    return units


def owner(units: Iterable[Unit], path: str) -> Unit | None:
    owners = [u for u in units if u.owns(path)]
    return max(owners, key=lambda u: len(u.root), default=None)


def select(units: list[Unit], changed: Iterable[str]) -> list[Unit]:
    """The units a change touches. A workspace's own pyproject.toml, uv.lock or conftest.py touches
    every unit in it; `.python-version` touches everything; a file no unit owns touches nothing."""
    chosen: set[Unit] = set()
    for path in changed:
        found = owner(units, path)
        if found is not None:
            chosen.add(found)
            continue
        pure = PurePosixPath(path)
        folder = pure.parent.as_posix()
        if path.startswith(CI_BASELINES):
            # The ratchet guard (a tools test) checks every change to a baseline file.
            chosen.update(u for u in units if u.root == "tools")
        elif pure.name in EVERYTHING_FILES:
            chosen.update(units)
        elif pure.name in WORKSPACE_FILES and folder in WORKSPACES:
            chosen.update(u for u in units if u.workspace == folder)
    return [u for u in units if u in chosen]


def lint_targets(changed: Iterable[str], poe_dirs: list[str]) -> list[str]:
    """The poe folders (a workspace or an agents package) whose Python or project files changed."""
    found: set[str] = set()
    for path in changed:
        pure = PurePosixPath(path)
        if not (path.endswith(PYTHON_SUFFIXES) or pure.name in WORKSPACE_FILES | EVERYTHING_FILES):
            continue
        owners = [d for d in poe_dirs if d == ROOT_WS or path.startswith(d + "/")]
        if owners:
            found.add(max(owners, key=len))
    return [d for d in poe_dirs if d in found]


def test_files(repo: Path, unit: Unit, durations: Mapping[str, float]) -> list[TestFile]:
    files: list[TestFile] = []
    base = repo / unit.cwd
    for entry in unit.tests:
        target = base / entry
        paths = (
            [target]
            if target.is_file()
            else sorted(p for p in target.rglob("*.py") if _is_test_file(p.name))
        )
        for path in paths:
            rel = path.relative_to(base).as_posix()
            key = f"{unit.cwd}::{rel}"
            if key in durations:
                weight = durations[key]
            else:
                text = path.read_text("utf-8", errors="replace")
                weight = SECONDS_PER_FILE + SECONDS_PER_TEST * max(1, text.count("def test_"))
            files.append(TestFile(unit, rel, weight))
    return files


def shard_count(files: list[TestFile], target_s: float, most: int) -> int:
    return max(1, min(most, math.ceil(sum(f.weight for f in files) / target_s)))


def shard(files: list[TestFile], count: int) -> list[list[TestFile]]:
    """Longest-first into the lightest shard, so every shard ends near the same time."""
    shards: list[list[TestFile]] = [[] for _ in range(count)]
    loads = [0.0] * count
    for f in sorted(files, key=lambda f: (-f.weight, f.unit.root, f.path)):
        lightest = loads.index(min(loads))
        shards[lightest].append(f)
        loads[lightest] += f.weight
    return [s for s in shards if s]


def load_durations(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    raw: object = json.loads(path.read_text("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: want an object of file -> seconds")
    return {str(k): float(v) for k, v in raw.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


def poe_dirs(repo: Path) -> list[str]:
    """Folders with their own poe fmt-check, lint and types: both workspaces, agents packages."""
    packages = sorted(
        p.parent.relative_to(repo).as_posix()
        for p in (repo / AGENTS_WS / "packages").glob("*/pyproject.toml")
    )
    return [ROOT_WS, AGENTS_WS, *packages]


def is_test_module(path: str) -> bool:
    return _is_test_file(path.rsplit("/", 1)[-1])


def is_test_support(path: str) -> bool:
    parts = path.split("/")
    return path.endswith(".py") and (
        is_test_module(path)
        or parts[-1] == "conftest.py"
        or any(p in ("tests", "test") for p in parts[:-1])
    )


def workspaces_for(unit: Unit) -> tuple[str, ...]:
    """The environments a unit's tests need. The workspace tools and QA suites also drive the
    agents workspace through `uv run --project qmx-agents --no-sync`, so it must be synced too."""
    if unit.workspace == ROOT_WS and (unit.root == "tools" or unit.root.startswith("qa")):
        return (ROOT_WS, AGENTS_WS)
    return (unit.workspace,)
