# ruff: noqa: S101
"""`run_all.py` over a folder of planted checks: its exit code and the table it prints."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RUN_ALL = Path(__file__).with_name("run_all.py")
PASSES = "raise SystemExit(0)\n"
FAILS = "print('FAIL planted'); raise SystemExit(3)\n"


def run_all(tmp_path: Path, checks: dict[str, str]) -> tuple[int, str]:
    folder = tmp_path / "checks"
    folder.mkdir()
    for name, body in checks.items():
        (folder / name).write_text(body, encoding="utf-8")
    guard = tmp_path / "settings.toml"
    if not guard.exists():
        guard.write_text("[budgets]\n", encoding="utf-8")
    done = subprocess.run(
        [
            sys.executable,
            str(RUN_ALL),
            "--checks",
            str(folder),
            "--evidence",
            str(tmp_path / "evidence"),
            "--guard",
            str(guard),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode, done.stdout


def test_one_failing_check_exits_non_zero_and_is_named(tmp_path: Path) -> None:
    code, out = run_all(
        tmp_path, {"ep2_lanes.py": PASSES, "x03_validate.py": FAILS, "x04_ledger.py": PASSES}
    )
    assert code == 1
    assert "2 PASS, 1 FAIL" in out
    assert "FAILED: x03_validate" in out
    assert "x03_validate             FAIL exit 3" in out


def test_all_passing_prints_zero_fail_in_plan_order(tmp_path: Path) -> None:
    code, out = run_all(
        tmp_path, {"x13_doors.py": PASSES, "ep2_lanes.py": PASSES, "x99_new.py": PASSES}
    )
    assert code == 0
    assert "3 PASS, 0 FAIL" in out
    running = [line.split()[-1] for line in out.splitlines() if " running " in line]
    assert running == ["ep2_lanes", "x13_doors", "x99_new"]


def test_a_check_that_changes_the_guarded_file_fails_and_stops_the_run(tmp_path: Path) -> None:
    guard = tmp_path / "settings.toml"
    guard.write_text("[budgets]\n", encoding="utf-8")
    edits = f"from pathlib import Path\nPath({str(guard)!r}).write_text('[roles]\\n')\n"
    code, out = run_all(tmp_path, {"ep2_lanes.py": edits, "x03_validate.py": PASSES})
    assert code == 1
    assert "ep2_lanes                FAIL changed settings.toml" in out
    assert "x03_validate             FAIL not run" in out
    assert "0 PASS, 2 FAIL" in out
