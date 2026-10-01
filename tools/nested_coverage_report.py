"""Enforce the QMA workspace's own tracked source inventory and package floors."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from coverage_report import evaluate

ROOT = Path(__file__).resolve().parents[1] / "qmx-agents"
PACKAGES = {"qma-core", "qma-wire", "qma-daemon"}


def main() -> int:
    """Root QMF exact/chrono coverage is gated separately by coverage_report."""
    try:
        git = shutil.which("git")
        if git is None:
            raise ValueError("git is required for the tracked source inventory")
        tracked = subprocess.run(
            [git, "ls-files", "-z", "--", "packages"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split("\0")
        sources = {
            path
            for path in tracked
            if path.endswith(".py")
            and any(path.startswith(f"packages/{name}/src/") for name in PACKAGES)
        }
        if not sources:
            raise ValueError("nested tracked source inventory is empty")
        report = json.loads((ROOT / "coverage.json").read_text())
        violations = evaluate(report, PACKAGES, sources, ROOT, contract_modules=())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"nested source coverage: FAIL: {exc}")
        return 1
    for violation in violations:
        print(f"nested source coverage: FAIL: {violation}")
    if not violations:
        print("nested source coverage: PASS; tracked source and each package >=80%")
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
