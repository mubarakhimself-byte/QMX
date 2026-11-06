"""Run the 18 foundation checks by name: one PASS or FAIL line each, non-zero on any FAIL.

Each row of `TABLE` is one check: its number, plain name, the pytest node ids that prove it and a
time limit. A node id is collected and run in its own workspace, the root or `qmx-agents`, with
that worktree's own interpreter, as `S/tools/proof_at.sh` does.

A check passes only when every pytest run exits 0, no case failed or errored, no case skipped or
xfailed, and at least one case passed for each node id it names. A skip reads FAIL on purpose:
pytest exits 0 when every test skips, check 18 skips unless `QMX_TEST_LIVE=1` is set, and other
tests here skip on a missing machine fact.

`--list` prints the table, `--only 7` and `--only 1-17` select checks, and `--walls` selects the
wall table, which is empty until R24 fills it.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias, cast

REPO: Final = Path(__file__).resolve().parents[1]
Environment: TypeAlias = Literal["root", "agents"]
ENVIRONMENTS: Final[tuple[Environment, ...]] = ("root", "agents")


@dataclass(frozen=True, slots=True)
class Test:
    """One pytest node id and the workspace whose interpreter and cwd collect it."""

    environment: Environment
    node_id: str


@dataclass(frozen=True, slots=True)
class Check:
    """One foundation check: what it is called, what proves it, and how long it may take."""

    number: int
    name: str
    tests: tuple[Test, ...]
    limit_s: float


@dataclass(frozen=True, slots=True)
class Outcome:
    passed: bool
    detail: str


def _agents(node_id: str) -> Test:
    return Test("agents", node_id)


def _root(node_id: str) -> Test:
    return Test("root", node_id)


TABLE: Final[tuple[Check, ...]] = (
    Check(
        1,
        "A repair lands",
        (
            _agents("qmx-agents/packages/qmx-host/tests/test_repair_lands.py"),
            _root(
                "tools/tests/test_app_env_fresh.py::"
                "test_a_changed_library_reaches_the_app_env_at_the_next_start"
            ),
        ),
        1800.0,
    ),
    Check(
        2,
        "A slow install holds nothing",
        (_agents("qmx-agents/packages/qmx-apps/tests/test_install_holds_nothing.py"),),
        900.0,
    ),
    Check(3, "Nothing silent", (_root("qml/tests/test_nothing_silent.py"),), 900.0),
    Check(
        4,
        "A long-only unit makes zero short fills",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_long_only_unit_makes_no_short_fills"
            ),
        ),
        900.0,
    ),
    Check(
        5,
        "ADX above 25 through unit_new and a QMB job",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_an_agent_writes_adx_above_25_and_a_job_runs_it"
            ),
        ),
        1200.0,
    ),
    Check(
        6,
        "A short run moves the tuned number",
        (
            _root(
                "qmb/tests/test_run_journal.py::"
                "test_a_short_only_run_moves_the_number_and_the_row_shows_why"
            ),
        ),
        900.0,
    ),
    Check(
        7,
        "The dictionary at full size",
        (_agents("qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py"),),
        1800.0,
    ),
    Check(
        8,
        "A fresh home lands a result",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_fresh_home_with_ticks_in_the_store_lands_a_result"
            ),
        ),
        900.0,
    ),
    Check(
        9,
        "No month is refused by name",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_no_month_is_refused_naming_the_month_and_the_template"
            ),
        ),
        900.0,
    ),
    Check(
        10,
        "A month through a CSV and through the store",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_month_through_a_csv_and_through_the_store_gives_the_same_trades"
            ),
        ),
        1200.0,
    ),
    Check(
        11,
        "A record moved on main shows in the next run",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_record_moved_on_main_shows_in_the_next_run"
            ),
        ),
        900.0,
    ),
    Check(
        12,
        "Gaps and sealed months",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_study_forbidding_gaps_beats_a_chat_allowing_them"
            ),
            _agents(
                "qmx-agents/apps/qmb/tests/test_qmb_app.py::"
                "test_a_sealed_month_is_refused_and_no_sealed_file_sits_in_a_run_folder"
            ),
        ),
        1200.0,
    ),
    Check(
        13,
        "A stated cost profile changes money and not R",
        (
            _agents(
                "qmx-agents/apps/qmb/tests/test_run_honesty.py::"
                "test_a_stated_cost_profile_changes_money_and_not_r"
            ),
        ),
        900.0,
    ),
    Check(
        14,
        "200,000 steps stay flat in memory",
        (
            _root(
                "qmb/tests/test_windowed_reader.py::test_a_real_backtest_of_200000_steps_stays_flat"
            ),
        ),
        1200.0,
    ),
    Check(
        15,
        "One paper, the right cause",
        (
            _agents(
                "qmx-agents/packages/qmx-engine/tests/test_templates.py::"
                "test_b_real_qmb_real_referee_real_scorecard"
            ),
        ),
        1800.0,
    ),
    Check(
        16,
        "A forged pass routes as fail",
        (
            _agents(
                "qmx-agents/packages/qmx-engine/tests/test_templates.py::"
                "test_a_forged_pass_routes_as_fail"
            ),
        ),
        1800.0,
    ),
    Check(
        17,
        "The gate and the hook on a Library-only market",
        (
            _agents(
                "qmx-agents/packages/qmx-engine/tests/test_templates.py::"
                "test_b_on_a_library_only_market_reaches_qmb"
            ),
            _agents(
                "qmx-agents/packages/qma-harness/tests/live/test_unit_hook_probe.py::"
                "test_the_hook_tells_the_agent_on_a_library_only_market"
            ),
            _agents(
                "qmx-agents/packages/qmx-tools/tests/test_offline_check.py::"
                "test_a_second_stop_on_gbpusd_keeps_its_error"
            ),
        ),
        1800.0,
    ),
    Check(
        18,
        "His own test",
        (
            _agents(
                "qmx-agents/packages/qma-harness/tests/live/test_his_own_test.py::test_his_own_test"
            ),
        ),
        3600.0,
    ),
)

WALLS: Final[tuple[Check, ...]] = ()
"""R24 fills this table; `--walls` selects it and runs it the same way."""


def _python(environment: Environment) -> Path:
    workspace = REPO if environment == "root" else REPO / "qmx-agents"
    if os.name == "nt":
        return workspace / ".venv" / "Scripts" / "python.exe"
    return workspace / ".venv" / "bin" / "python"


def _relative(environment: Environment, node_id: str) -> str:
    if environment == "root":
        return node_id
    prefix = "qmx-agents/"
    if not node_id.startswith(prefix):
        raise ValueError(f"an agents node id is written under {prefix}, not {node_id!r}")
    return node_id[len(prefix) :]


def command(
    environment: Environment, node_ids: Sequence[str], report: Path
) -> tuple[list[str], Path]:
    """The pytest argv for `node_ids` in one workspace, and the cwd it runs in."""
    workspace = REPO if environment == "root" else REPO / "qmx-agents"
    return (
        [
            str(_python(environment)),
            "-m",
            "pytest",
            *(_relative(environment, node_id) for node_id in node_ids),
            "-q",
            "-n",
            "0",
            "-p",
            "no:cacheprovider",
            f"--junitxml={report}",
        ],
        workspace,
    )


def _counts(report: Path) -> dict[str, int]:
    found = {"passed": 0, "failed": 0, "skipped": 0}
    if not report.is_file():
        found["failed"] = 1
        return found
    for case in ET.parse(report).iter("testcase"):  # noqa: S314 - pytest wrote this report
        if case.find("failure") is not None or case.find("error") is not None:
            found["failed"] += 1
        elif case.find("skipped") is not None:
            found["skipped"] += 1
        else:
            found["passed"] += 1
    return found


def _tail(stdout: str, stderr: str) -> str:
    lines = [
        line.strip() for text in (stdout, stderr) for line in text.splitlines() if line.strip()
    ]
    return " | ".join(lines[-4:])[-400:] or "pytest exited with no output"


def _elapsed(started: float) -> float:
    return time.monotonic() - started  # ambient-scan: allow - a check's own elapsed time


def run_check(check: Check) -> Outcome:
    """Run one check's node ids and read pytest's own counts."""
    started = time.monotonic()  # ambient-scan: allow - the check's time limit
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for environment in ENVIRONMENTS:
        group = [test for test in check.tests if test.environment == environment]
        if not group:
            continue
        remaining = check.limit_s - _elapsed(started)
        if remaining <= 0:
            return Outcome(False, f"timed out after {check.limit_s:.0f} s")
        python = _python(environment)
        if not python.is_file():
            return Outcome(False, f"no environment at {python}; run the boot recipe")
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / f"check-{check.number}-{environment}.xml"
            argv, workspace = command(environment, [test.node_id for test in group], report)
            try:
                done = subprocess.run(
                    argv, cwd=workspace, capture_output=True, text=True, timeout=remaining
                )
            except subprocess.TimeoutExpired:
                return Outcome(False, f"timed out after {check.limit_s:.0f} s")
            found = _counts(report)
            for name, value in found.items():
                counts[name] += value
            if done.returncode != 0:
                return Outcome(False, _tail(done.stdout, done.stderr))
            if found["failed"]:
                return Outcome(False, f"{found['failed']} failed")
            if found["skipped"]:
                return Outcome(
                    False, f"{found['skipped']} skipped, and a skipped test proves nothing"
                )
    if counts["passed"] < len(check.tests):
        return Outcome(False, f"{counts['passed']} passed for {len(check.tests)} named tests")
    return Outcome(True, f"{counts['passed']} passed in {_elapsed(started):.1f} s")


def _numbers(text: str) -> set[int]:
    wanted: set[int] = set()
    for piece in text.split(","):
        part = piece.strip()
        if not part:
            raise argparse.ArgumentTypeError(f"{text!r} names a check")
        if "-" in part:
            low, _, high = part.partition("-")
            try:
                start, stop = int(low), int(high)
            except ValueError as error:
                raise argparse.ArgumentTypeError(f"{part!r} is not a range of checks") from error
            if start > stop or start < 1:
                raise argparse.ArgumentTypeError(f"{part!r} is not a range of checks")
            wanted.update(range(start, stop + 1))
        else:
            try:
                wanted.add(int(part))
            except ValueError as error:
                raise argparse.ArgumentTypeError(f"{part!r} is not a check number") from error
    return wanted


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--list", action="store_true", help="print the table and exit")
    parser.add_argument("--walls", action="store_true", help="run the wall table instead")
    parser.add_argument("--only", type=_numbers, help="7, 1-17, or a comma list of those")
    return parser


def _print_table(table: Sequence[Check]) -> None:
    if not table:
        print("no wall checks yet; R24 fills the walls table")
        return
    for check in table:
        print(f"{check.number:>2}  {check.name}  ({check.limit_s:.0f} s)")
        for test in check.tests:
            print(f"    {test.environment:<6} {test.node_id}")


def main(argv: list[str] | None = None, *, table: tuple[Check, ...] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    selected = WALLS if cast("bool", args.walls) else (TABLE if table is None else table)

    only = cast("set[int] | None", args.only)
    if only is not None:
        unknown = sorted(only - {check.number for check in selected})
        if unknown:
            print(f"no check numbered {unknown}", file=sys.stderr)
            return 2
        selected = tuple(check for check in selected if check.number in only)

    if cast("bool", args.list):
        _print_table(selected)
        return 0
    if not selected:
        print("no wall checks yet; R24 fills the walls table")
        return 0

    started = time.monotonic()  # ambient-scan: allow - the whole proof's total
    failures = 0
    for check in selected:
        outcome = run_check(check)
        line = "PASS" if outcome.passed else "FAIL"
        print(f"{line} {check.number} {check.name} ({outcome.detail})", flush=True)
        failures += 0 if outcome.passed else 1
    total_min = _elapsed(started) / 60
    print(
        f"{len(selected)} checks: {len(selected) - failures} passed, {failures} failed "
        f"in {total_min:.1f} min"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
