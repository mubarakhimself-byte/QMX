"""The ratchet's guard: outside a baseline retake, no change may loosen what CI holds.

Two kinds of loosening count:

- **Baseline growth.** Every file under `ci/baselines/` is compared as counted rows, read from git
  (`git show`-style blob reads), so no diff setting can hide a row. A row the base did not have is
  growth. So is a baseline file that is not a regular file (a symlink, a submodule), holds a NUL
  byte, or is marked `-diff` or `binary` in `.gitattributes`, and so is deleting one. A new
  baseline file is allowed only while the base has no `ci/baselines/` at all (the change that
  brings the ratchet in).
- **Suppressions.** More type-ignore, pyright-ignore, noqa, skylos or ambient-scan allow markers
  in Python files than the base had, a pyright or ruff rule turned down or ignored in a pyproject,
  a new Skylos or Vulture exclude or ignore entry, a looser Skylos gate, or a new line in a
  Vulture whitelist.

A `baseline/**` branch may grow baseline files only when its change touches nothing outside
`ci/baselines/`. Everything here reads git objects only, so it runs the same from the gate's
trusted checkout as from a test.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

import tomllib

BASELINE_DIR = "ci/baselines/"
BASELINE_BRANCH = "baseline/"
REGULAR_MODES = frozenset({"100644", "100755"})
GIT = shutil.which("git") or "git"
GIT_TIMEOUT_S = 600

# The suppression markers, each in its comment form. Built from parts so this file does not
# carry the markers itself.
MARKERS = {
    "type-ignore": re.compile("#" + r"\s*type:\s*ignore"),
    "pyright-ignore": re.compile("#" + r"\s*pyright:\s*ignore"),
    "noqa": re.compile("#" + r"\s*noqa", re.IGNORECASE),
    "skylos": re.compile("#" + r"\s*skylos:", re.IGNORECASE),
    "ambient-scan-allow": re.compile("#" + r"\s*ambient-scan:\s*allow", re.IGNORECASE),
}
PYTHON = (".py", ".pyi")
SEVERITY: dict[object, int] = {
    "error": 3,
    True: 3,
    "warning": 2,
    "information": 1,
    "none": 0,
    False: 0,
}
CHECKING_MODE: dict[object, int] = {"strict": 3, "standard": 2, "basic": 1, "off": 0}
# Lists whose new entries switch something off, by table.
LOOSENING_LISTS: dict[tuple[str, ...], tuple[str, ...]] = {
    ("tool", "pyright"): ("exclude", "ignore"),
    ("tool", "ruff"): ("ignore", "extend-ignore", "exclude", "extend-exclude"),
    ("tool", "ruff", "lint"): ("ignore", "extend-ignore"),
    ("tool", "skylos"): ("exclude", "ignore"),
    ("tool", "vulture"): ("exclude", "ignore_names", "ignore_decorators"),
}
PER_FILE_IGNORES = (
    ("tool", "ruff", "per-file-ignores"),
    ("tool", "ruff", "lint", "per-file-ignores"),
)


class GuardError(Exception):
    pass


def _git(root: Path, *args: str, check: bool = True) -> str:
    done = subprocess.run(
        [GIT, *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT_S,
        check=False,
    )
    if check and done.returncode != 0:
        raise GuardError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def tree_entries(root: Path, rev: str, prefix: str) -> dict[str, tuple[str, str]]:
    """path -> (mode, object id) for every entry under `prefix` at `rev`."""
    found: dict[str, tuple[str, str]] = {}
    for line in _git(root, "ls-tree", "-r", "--full-tree", rev, "--", prefix).splitlines():
        meta, _, path = line.partition("\t")
        mode, _kind, oid = meta.split()
        found[path] = (mode, oid)
    return found


def blob(root: Path, oid: str) -> str:
    return _git(root, "cat-file", "blob", oid)


def rows(text: str) -> Counter[str]:
    """A baseline's rows, counted: every non-empty line that is not a `#` comment."""
    found = (line.rstrip("\r") for line in text.split("\n"))
    return Counter(line for line in found if line and not line.startswith("#"))


def no_diff(root: Path, rev: str, path: str) -> bool:
    """Whether `.gitattributes` at `rev` marks the path binary or -diff."""
    out = _git(root, "check-attr", "--source", rev, "diff", "binary", "--", path)
    values = {
        parts[1]: parts[2]
        for parts in (line.rsplit(": ", 2) for line in out.splitlines())
        if len(parts) == 3
    }
    return values.get("diff") == "unset" or values.get("binary") == "set"


def baseline_growth(root: Path, base: str, at: str) -> list[str]:
    """Every way the change from `base` to `at` grows a baseline, one line each."""
    before = tree_entries(root, base, BASELINE_DIR)
    after = tree_entries(root, at, BASELINE_DIR)
    bootstrap = not before
    grown: list[str] = []
    for path in sorted(set(before) | set(after)):
        if path not in after:
            grown.append(f"{path}: deleted")
            continue
        mode, oid = after[path]
        if mode not in REGULAR_MODES:
            grown.append(f"{path}: not a regular file (mode {mode})")
            continue
        if no_diff(root, at, path):
            grown.append(f"{path}: marked binary or -diff in .gitattributes")
            continue
        text = blob(root, oid)
        if "\0" in text:
            grown.append(f"{path}: holds a NUL byte")
            continue
        if path not in before:
            if not bootstrap:
                grown.append(f"{path}: new baseline file")
            continue
        added = rows(text) - rows(blob(root, before[path][1]))
        grown += [f"{path}: + {row}" for row in sorted(added.elements())]
    return grown


def changed_files(root: Path, base: str, at: str) -> list[str]:
    out = _git(root, "diff", "--name-only", "--no-renames", base, at)
    return [p for p in out.splitlines() if p]


def show(root: Path, rev: str, path: str) -> str | None:
    """A file's text at `rev`, or None when it is not there or not a regular file."""
    entries = tree_entries(root, rev, path)
    entry = entries.get(path)
    if entry is None or entry[0] not in REGULAR_MODES:
        return None
    return blob(root, entry[1])


def markers(text: str | None) -> Counter[str]:
    if text is None:
        return Counter()
    return Counter({name: len(rx.findall(text)) for name, rx in MARKERS.items()})


def _table(data: Mapping[str, object], keys: Sequence[str]) -> dict[str, object]:
    current: dict[str, object] = dict(data)
    for key in keys:
        found = current.get(key, {})
        if not isinstance(found, dict):
            return {}
        current = cast("dict[str, object]", found)
    return current


def _entries(value: object) -> Counter[str]:
    if isinstance(value, list):
        return Counter(str(v) for v in cast("list[object]", value))
    return Counter()


def _rank(key: str, value: object) -> int | None:
    ranks = CHECKING_MODE if key == "typeCheckingMode" else SEVERITY
    return ranks.get(value) if isinstance(value, str | bool) else None


def _pyright_table(path: str, text: str | None) -> dict[str, object]:
    if text is None:
        return {}
    if path.endswith("pyrightconfig.json"):
        data: object = json.loads(text)
        return cast("dict[str, object]", data) if isinstance(data, dict) else {}
    return _table(tomllib.loads(text), ("tool", "pyright"))


def pyright_loosening(path: str, before: str | None, after: str) -> list[str]:
    """A pyright rule or checking mode turned down, added below error, or removed."""
    found: list[str] = []
    old_t, new_t = _pyright_table(path, before), _pyright_table(path, after)
    for key in sorted(set(old_t) | set(new_t)):
        if key != "typeCheckingMode" and not key.startswith("report"):
            continue
        old = _rank(key, old_t[key]) if key in old_t else None
        new = _rank(key, new_t[key]) if key in new_t else None
        if key not in new_t:
            if old:
                found.append(f"{path}: pyright {key} removed (was {old_t[key]!r})")
        elif new is None or (key not in old_t and new < 3) or (old is not None and new < old):
            found.append(f"{path}: pyright {key} set to {new_t[key]!r}")
    return found


def config_loosening(path: str, before: str | None, after: str) -> list[str]:
    """Rule downgrades and new ignore or exclude entries in one pyproject or pyright config."""
    found = pyright_loosening(path, before, after)
    if path.endswith("pyrightconfig.json"):
        return found
    old_data = tomllib.loads(before) if before is not None else {}
    new_data = tomllib.loads(after)
    for table, keys in LOOSENING_LISTS.items():
        old_t, new_t = _table(old_data, table), _table(new_data, table)
        for key in keys:
            added = _entries(new_t.get(key)) - _entries(old_t.get(key))
            found += [f"{path}: [{'.'.join(table)}].{key} + {e}" for e in sorted(added.elements())]
    for table in PER_FILE_IGNORES:
        old_t, new_t = _table(old_data, table), _table(new_data, table)
        for pattern in sorted(new_t):
            added = _entries(new_t[pattern]) - _entries(old_t.get(pattern))
            name = ".".join(table)
            found += [f"{path}: [{name}] {pattern} + {e}" for e in sorted(added.elements())]
    old_gate = _table(old_data, ("tool", "skylos", "gate"))
    new_gate = _table(new_data, ("tool", "skylos", "gate"))
    for key in sorted(new_gate):
        old, new = old_gate.get(key), new_gate[key]
        numbers = isinstance(old, int) and isinstance(new, int)
        looser = (
            numbers and not isinstance(new, bool) and cast("int", new) > cast("int", old)
        ) or (old is True and new is False)
        if looser:
            found.append(f"{path}: [tool.skylos.gate].{key} loosened {old!r} -> {new!r}")
    old_min = _table(old_data, ("tool", "vulture")).get("min_confidence")
    new_min = _table(new_data, ("tool", "vulture")).get("min_confidence")
    if isinstance(old_min, int) and isinstance(new_min, int) and new_min > old_min:
        found.append(f"{path}: [tool.vulture].min_confidence raised {old_min} -> {new_min}")
    return found


def suppressions(root: Path, base: str, at: str, changed: Iterable[str]) -> list[str]:
    """Every new suppression the change makes, one line each."""
    found: list[str] = []
    before: Counter[str] = Counter()
    after: Counter[str] = Counter()
    gained: dict[str, list[str]] = {}
    for path in changed:
        name = path.rsplit("/", 1)[-1]
        old, new = show(root, base, path), show(root, at, path)
        if path.endswith(PYTHON):
            m_old, m_new = markers(old), markers(new)
            before += m_old
            after += m_new
            for kind in MARKERS:
                if m_new[kind] > m_old[kind]:
                    gained.setdefault(kind, []).append(path)
        if new is None:
            continue
        if name in ("pyproject.toml", "pyrightconfig.json"):
            try:
                found += config_loosening(path, old, new)
            except (tomllib.TOMLDecodeError, json.JSONDecodeError) as error:
                found.append(f"{path}: cannot be read ({error})")
        elif "whitelist" in name.lower():
            added = rows(new) - rows(old or "")
            found += [f"{path}: whitelist + {row}" for row in sorted(added.elements())]
    for kind in MARKERS:
        if after[kind] > before[kind]:
            files = ", ".join(sorted(gained.get(kind, [])))
            found.append(f"{after[kind] - before[kind]} more {kind} marker(s), in {files}")
    return found


def exempt(branch: str, changed: Sequence[str]) -> bool:
    """A baseline retake: a baseline/** branch whose change stays inside ci/baselines/."""
    return branch.startswith(BASELINE_BRANCH) and all(p.startswith(BASELINE_DIR) for p in changed)


def problems(root: Path, base: str, at: str, branch: str) -> list[str]:
    """Everything the change loosens, unless it is a baseline retake."""
    changed = changed_files(root, base, at)
    if exempt(branch, changed):
        return []
    bootstrap = not tree_entries(root, base, BASELINE_DIR)
    found = baseline_growth(root, base, at)
    if not bootstrap:
        found += suppressions(root, base, at, changed)
    return found
