"""Run Python suites in their owning workspace; keep reports in a temporary directory."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_suite(name: str, cwd: Path, command: list[str], report: Path) -> tuple[int, str]:
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to run the workspace suites")
    started = time.monotonic()  # ambient-scan: allow - test duration measurement
    result = subprocess.run([uv, "run", *command, "--junitxml", str(report)], cwd=cwd, check=False)
    counts = dict.fromkeys(("passed", "failed", "skipped", "xfailed"), 0)
    if report.exists():
        for case in ET.parse(report).iter("testcase"):  # noqa: S314 - pytest wrote this temporary report
            skip = case.find("skipped")
            if case.find("failure") is not None or case.find("error") is not None:
                counts["failed"] += 1
            elif skip is not None:
                counts["xfailed" if skip.get("type") == "pytest.xfail" else "skipped"] += 1
            else:
                counts["passed"] += 1
    else:
        counts["failed"] += 1
    values = " | ".join(str(value) for value in counts.values())
    elapsed = time.monotonic() - started  # ambient-scan: allow - test duration measurement
    row = f"| {name} | {values} | {elapsed:.1f}s |"
    return result.returncode, row


def main() -> int:
    suites: list[tuple[str, Path, list[str], list[str]]] = [
        (
            "QMF/QML/QMB/QMN",
            ROOT,
            ["python", "-m", "pytest", "packages", "extensions", "qml", "qmb", "qmn", "-q"],
            ["packages", "extensions", "qml", "qmb", "qmn"],
        ),
        ("tools", ROOT, ["python", "-m", "pytest", "tools/tests", "-q"], ["tools/tests"]),
        ("adws", ROOT, ["python", "-m", "pytest", "adws/tests", "-q"], ["adws/tests"]),
        (
            "QMA",
            ROOT / "qmx-agents",
            ["python", "-m", "pytest", "packages", "tests", "-q"],
            ["packages", "tests"],
        ),
        (
            "qmx-agents",
            ROOT / "qmx-agents/packages/qmx-agents",
            ["python", "-m", "pytest", "tests", "-q"],
            ["tests"],
        ),
    ]
    qa = ROOT / "qa/tests"
    top_level = sorted(qa.glob("test_*.py"))
    if top_level:
        paths = [str(path.relative_to(ROOT)) for path in top_level]
        suites.append(("QA gates", ROOT, ["python", "-m", "pytest", *paths, "-q"], paths))
    for directory in sorted(qa.glob("epic_*")):
        if directory.is_dir():
            path = str(directory.relative_to(ROOT))
            suites.append(
                (f"QA {directory.name}", ROOT, ["python", "-m", "pytest", path, "-q"], [path])
            )
    rows: list[str] = []
    failed = False
    with tempfile.TemporaryDirectory(prefix="qmx-test-all-") as temporary:
        for index, (name, cwd, command, paths) in enumerate(suites):
            print(f"Running {name}", flush=True)
            code, row = run_suite(
                name, cwd, [*command, "-m", "not serial"], Path(temporary) / f"{index}.xml"
            )
            failed |= code != 0
            rows.append(row)
            print(row, flush=True)
            # Serial tests get exclusive access after their parallel suite finishes.
            code, row = run_suite(
                f"{name} serial",
                cwd,
                ["python", "-m", "pytest", *paths, "-q", "-n", "0", "--no-cov", "-m", "serial"],
                Path(temporary) / f"{index}-serial.xml",
            )
            failed |= code not in (0, 5)
            if code != 5:
                rows.append(row)
    print("\n| Suite | Passed | Failed | Skipped | Xfailed | Duration |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    print("\n".join(rows), flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
