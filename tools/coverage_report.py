"""Tier-1 coverage-floor enforcer (AR-20; enforcing the CT-01/CT-02 branch law).

``poe test`` runs one aggregate ``--cov=qmf --cov-branch --cov-fail-under=80`` over
all workspace packages. That single number is necessary but not sufficient: six
near-empty scaffold packages sit at 100% and can float the aggregate above 80% even
while ``qmf-core`` itself regresses, and the aggregate says nothing about *branch*
coverage on the two contract modules the spine requires to be exhaustively tested —
``qmf/core/exact.py`` (CT-01) and ``qmf/core/chrono.py`` (CT-02).

This script reads the machine-readable ``coverage.json`` that ``poe test`` writes and
mechanically enforces the two story acceptance criteria the aggregate cannot:

* **Per-package floor (AR-20).** Every workspace package's own combined
  line+branch coverage must be at least 80%. A package is derived from each measured
  file's ``packages/<pkg>/src/``, ``extensions/<pkg>/src/``, or application-root
  ``src/`` path, so tests cannot pad the numerator. The CLI derives the expected
  inventory from workspace manifests, making entirely omitted packages fail too.
* **Full-branch contract modules.** ``qmf/core/exact.py`` and ``qmf/core/chrono.py``
  must have **100% branch** coverage — every decision exit taken. These modules must
  be present in the report; a contract module that was never measured fails the gate
  rather than passing by omission (fail-closed). Malformed counters and zero
  measurable package or contract-branch totals are not coverage evidence.

Wired into ``poe check`` right after ``test`` (which produces ``coverage.json``). A
single violation exits nonzero and fails the gate. Stdlib only; the SSSF root gate
(``adws``) is untouched. Run via ``python tools/coverage_report.py`` or ``poe
cov-report``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import cast

from workspace_meta import iter_members

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "coverage.json"

# Every workspace package's own coverage must clear this floor (AR-20).
PACKAGE_MIN_PERCENT = 80.0

# The CT-01/CT-02 contract modules that must be exhaustively branch-covered. Matched
# under the qmf-core source root, independently of absolute/relative report paths.
FULL_BRANCH_MODULES: tuple[str, ...] = (
    "qmf/core/exact.py",
    "qmf/core/chrono.py",
)

# Match shipped package sources and QMN operational deployment code, with
# path-component boundaries on every platform. Examples/tests remain excluded.
_PACKAGE_RE = re.compile(
    r"(?:^|/)(?:(?:packages|extensions)/[^/]+/src/|(?:qml|qmb|qmn)/src/|qmn/deploy/)"
)
_COUNTERS = ("covered_lines", "num_statements", "covered_branches", "num_branches")


def _norm(path: str) -> str:
    """Normalize separators without resolving paths against the current machine."""
    return path.replace("\\", "/")


def _source_path(path: str) -> str | None:
    """Return a portable workspace source path; exclude tests and traversal."""
    norm = _norm(path)
    if any(part in {"..", "tests", "test", "examples"} for part in norm.split("/")):
        return None
    norm = "/".join(part for part in norm.split("/") if part not in {"", "."})
    match = _PACKAGE_RE.search(norm)
    if match is None or not norm[match.end() :]:
        return None
    return norm[match.start() :].lstrip("/")


def _package_of(path: str) -> str | None:
    """The package of a shipped source file, never a test or build script."""
    source = _source_path(path)
    if source is None:
        return None
    parts = source.split("/")
    return parts[1] if parts[0] in {"packages", "extensions"} else parts[0]


def _as_mapping(value: object) -> Mapping[str, object]:
    """Narrow JSON mappings only after checking their shape."""
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _summary(path: str, info: object) -> dict[str, int]:
    """Validate required counters; malformed evidence must never become zero."""
    summary = _as_mapping(_as_mapping(info).get("summary"))
    result: dict[str, int] = {}
    for field in _COUNTERS:
        value = summary.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{path}: {field} must be a non-negative integer")
        result[field] = value
    for covered, total in (
        ("covered_lines", "num_statements"),
        ("covered_branches", "num_branches"),
    ):
        if result[covered] > result[total]:
            raise ValueError(f"{path}: {covered} exceeds {total}")
    return result


def evaluate(
    report: object,
    expected_packages: Collection[str] = (),
    expected_sources: Collection[str] = (),
    source_root: Path | None = None,
) -> list[str]:
    """Check schema, source-only package floors and full-branch contracts.

    Callers with workspace metadata can supply the expected package inventory so
    an entirely omitted package fails too. The CLI always supplies that inventory.
    """
    if not isinstance(report, Mapping):
        return ["coverage report must be an object"]
    files = cast("Mapping[str, object]", report).get("files")
    if not isinstance(files, Mapping) or not files:
        return ["coverage report files must be a non-empty object"]
    summaries: dict[str, dict[str, int]] = {}
    violations: list[str] = []
    for path, info in cast("Mapping[object, object]", files).items():
        if not isinstance(path, str) or not path:
            violations.append("coverage report file paths must be non-empty strings")
            continue
        # Validate every entry, even unmeasured tooling, before filtering scope.
        try:
            summary = _summary(path, info)
        except ValueError as exc:
            violations.append(str(exc))
            continue
        source = _source_path(path)
        if source is None:
            continue
        if expected_sources and source not in expected_sources:
            violations.append(f"{source}: source is outside the tracked inventory")
            continue
        if source_root is not None and (Path(path).is_absolute() or re.match(r"^[A-Za-z]:", path)):
            try:
                Path(path).relative_to(source_root)
            except ValueError:
                violations.append(f"{path}: measured source is outside the candidate")
                continue
        if source in summaries:
            violations.append(f"{source}: duplicate source path in coverage report")
        else:
            summaries[source] = summary
    for source in sorted(set(expected_sources) - summaries.keys()):
        violations.append(f"{source}: source file was not measured (fail-closed)")
    violations.extend(_package_violations(summaries, expected_packages))
    violations.extend(_full_branch_violations(summaries))
    return violations


def _package_violations(
    files: Mapping[str, dict[str, int]], expected_packages: Collection[str]
) -> list[str]:
    """Aggregate line+branch units; empty and omitted packages fail closed."""
    tallies: dict[str, list[int]] = {}
    for path, summary in files.items():
        package = _package_of(path)
        if package is None:
            continue
        covered = summary["covered_lines"] + summary["covered_branches"]
        total = summary["num_statements"] + summary["num_branches"]
        tally = tallies.setdefault(package, [0, 0])
        tally[0] += covered
        tally[1] += total

    violations: list[str] = []
    for package in sorted(set(expected_packages) - tallies.keys()):
        violations.append(f"{package}: package was not measured (fail-closed)")
    for package, (covered, total) in sorted(tallies.items()):
        if total == 0:
            violations.append(f"{package}: no measurable line+branch units (fail-closed)")
            continue
        percent = 100.0 * (covered / total)
        if percent + 1e-9 < PACKAGE_MIN_PERCENT:
            violations.append(
                f"{package}: {percent:.2f}% coverage is below the {PACKAGE_MIN_PERCENT:.0f}% "
                f"per-package floor (AR-20) [{covered}/{total} line+branch units]"
            )
    return violations


def _full_branch_violations(files: Mapping[str, dict[str, int]]) -> list[str]:
    """Require the actual qmf-core contract sources with nonzero branch evidence."""
    violations: list[str] = []
    for suffix in FULL_BRANCH_MODULES:
        summary = files.get(f"packages/qmf-core/src/{suffix}")
        if summary is None:
            violations.append(
                f"{suffix}: contract module was not measured; 100% branch coverage cannot be "
                f"confirmed (fail-closed)"
            )
            continue
        num_branches = summary["num_branches"]
        covered_branches = summary["covered_branches"]
        if num_branches == 0:
            violations.append(f"{suffix}: no measured branches (fail-closed)")
        elif covered_branches < num_branches:
            missing = num_branches - covered_branches
            violations.append(
                f"{suffix}: {covered_branches}/{num_branches} branches covered — {missing} "
                f"uncovered; CT-01/CT-02 contract modules require 100% branch coverage"
            )
    return violations


def workspace_packages() -> set[str]:
    """Derive the CLI inventory from the same manifests as workspace checks."""
    packages = {member.directory.name for member in iter_members(ROOT)}
    if not packages:
        raise ValueError("workspace package inventory is empty")
    return packages


def workspace_sources() -> set[str]:
    """Inventory every shipped Python source, including zero-statement files."""
    tracked = subprocess.run(
        [
            shutil.which("git") or "git",
            "ls-files",
            "-z",
            "--",
            "packages",
            "extensions",
            "qml",
            "qmb",
            "qmn",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    return {path for path in tracked if path.endswith(".py") and _source_path(path) == path}


def main(
    report_path: Path = REPORT_PATH, *, expected_packages: Collection[str] | None = None
) -> int:
    """Load ``coverage.json`` and enforce the floors, exiting nonzero on any breach."""
    # "No usable report" is decided once, before the read, and covers every shape of it:
    # absent, a directory, a dangling symlink, a device. This replaces a
    # `except FileNotFoundError` further down that only ever saw the absent case — and
    # a FIFO, which that branch could not have caught, would have hung the gate on a
    # read that never returned. The check sits immediately before the read it guards.
    if not report_path.is_file():
        sys.stdout.write(
            f"cov-report: FAIL - no coverage report at {report_path}; run `poe test` first "
            f"so the JSON report is produced.\n"
        )
        return 1
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        sys.stdout.write(f"cov-report: FAIL - could not read {report_path}: {exc}\n")
        return 1

    try:
        inventory = workspace_packages() if expected_packages is None else expected_packages
    except (OSError, ValueError, TypeError, AttributeError, subprocess.CalledProcessError) as exc:
        sys.stdout.write(f"cov-report: FAIL - could not read workspace inventory: {exc}\n")
        return 1
    sources = workspace_sources() if expected_packages is None else ()
    violations = evaluate(report, inventory, sources, ROOT if expected_packages is None else None)
    if violations:
        sys.stdout.write("cov-report: FAIL - coverage floors breached:\n")
        for violation in violations:
            sys.stdout.write(f"  {violation}\n")
        return 1
    sys.stdout.write(
        f"cov-report: clean (per-package >= {PACKAGE_MIN_PERCENT:.0f}%; "
        f"{', '.join(FULL_BRANCH_MODULES)} at 100% branch).\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
