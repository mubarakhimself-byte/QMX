from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import run_all

RUN_ALL = Path(__file__).with_name("run_all.py")


def fake_scripts(folder: Path, codes: dict[str, int]) -> Path:
    folder.mkdir()
    for name, code in codes.items():
        (folder / name).write_text(f"print('{name} done')\nraise SystemExit({code})\n")
    return folder


def run_all_process(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUN_ALL), "--evidence", str(tmp_path / "evidence"), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_one_failing_check_script_makes_run_all_exit_non_zero_and_name_it(
    tmp_path: Path,
) -> None:
    scripts = fake_scripts(tmp_path / "s", {"s01_install.py": 0, "s02_login.py": 1})
    done = run_all_process(tmp_path, "--scripts", str(scripts), "--only", "S1", "S2")
    lines = done.stdout.splitlines()
    assert done.returncode == 1
    assert lines[-2:] == ["1 PASS, 1 FAIL, 0 SKIP in 0.0 min", "FAIL: S2"]
    assert [line.split(" | ")[:3] for line in lines if line.startswith("| S")] == [
        ["| S1", "s01_install.py", "PASS"],
        ["| S2", "s02_login.py", "FAIL"],
    ]
    assert "exit 1: s02_login.py done" in done.stdout


def test_every_check_passing_exits_zero_and_logs_each_script_output(tmp_path: Path) -> None:
    scripts = fake_scripts(tmp_path / "s", {"s01_install.py": 0, "s05_permissions.py": 0})
    done = run_all_process(tmp_path, "--scripts", str(scripts), "--only", "S1", "S5")
    assert done.returncode == 0
    assert done.stdout.splitlines()[-1] == "2 PASS, 0 FAIL, 0 SKIP in 0.0 min"
    out = tmp_path / "evidence" / "run_all" / "S5.out"
    assert out.read_text().strip() == "s05_permissions.py done"


def test_a_check_that_hangs_is_killed_and_fails(tmp_path: Path) -> None:
    scripts = tmp_path / "s"
    scripts.mkdir()
    (scripts / "s05_permissions.py").write_text("import time\ntime.sleep(60)\n")
    plan = run_all.Plan(scripts, tmp_path / "evidence", timeout=1)
    [outcome] = run_all.run([run_all.check("S5", "s05_permissions.py")], plan)
    assert (outcome.verdict, outcome.note) == (run_all.Verdict.FAIL, "timed out after 1 s")


def test_s16_is_skipped_and_says_so_when_hp16_is_parked() -> None:
    reasons = run_all.skip_reasons(run_all.CHECKS, gpt_parked=True, no_login=False, skip=["S36"])
    assert reasons == {
        "S16 lanes": "HP16 is parked",
        "S36": "skipped on the command line",
    }


def test_without_a_login_only_fake_model_checks_run() -> None:
    reasons = run_all.skip_reasons(run_all.CHECKS, gpt_parked=False, no_login=True, skip=[])
    run = [found.label for found in run_all.CHECKS if found.label not in reasons]
    assert reasons["S8 rows"] == "needs the OpenRouter key"
    assert reasons["S20 settings"] == "needs a running qma.serve host, this PC's keyring"
    assert run == [
        "S5", "E56 fake", "E56 delete", "S6a", "S6a agent", "S6b", "S9", "S11 nested", "S11 background", "S11 model", "S11 tools",
        "S11 subagent", "S11 full", "S11 allowlist", "S11 unattended", "S12 bash", "S15 wire",
        "S15 restart", "S15 concurrent", "S15 question", "S21", "S21ab", "S21c", "S21e", "S22",
        "S23", "S24 key", "S28", "S29", "S29a", "S31 idle", "S31 busy", "S32", "S33", "S34",
        "S35", "S35u", "S37", "S38", "S39", "S40", "S41",
    ]  # fmt: skip


def test_the_checks_run_in_design_section_5_order_and_each_script_exists() -> None:
    ids = list(dict.fromkeys(found.id for found in run_all.CHECKS))
    assert ids == [
        "S1", "S2", "S3", "S4", "S5", "E56", "S6a", "S6b", "S7", "S8", "S9", "S10", "S11", "S12",
        "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20", "S21", "S21ab", "S21c", "S21d",
        "S21e", "S22", "S23", "S24", "S25", "S28", "S29", "S29a", "S30", "S30b",
        "S31", "S32", "S33", "S34", "S35", "S35u", "S36", "S37", "S38", "S39", "S40", "S41",
    ]  # fmt: skip
    labels = [found.label for found in run_all.CHECKS]
    assert len(labels) == len(set(labels)) == 71
    assert [
        found.script for found in run_all.CHECKS if not (RUN_ALL.parent / found.script).exists()
    ] == []


@pytest.mark.parametrize(
    ("args", "label"),
    [(("fake",), "E56 fake"), (("--bash",), "E56"), ((), "E56")],
)
def test_a_row_is_named_by_its_id_and_first_argument(args: tuple[str, ...], label: str) -> None:
    assert run_all.check("E56", "e56_guard.py", *args).label == label
