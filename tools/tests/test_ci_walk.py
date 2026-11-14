"""The nightly walk's part and the shard times: which part a night walks, and how durations.py
turns a deep run's JUnit reports into the seconds the splitter balances by."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import ci_units
import durations
import pytest
import qci

WORKFLOW = (Path(__file__).resolve().parents[2] / ".github/workflows/qmx-ci.yml").read_text("utf-8")


def _day(date: datetime.date) -> str:
    return str((date - datetime.date(1970, 1, 1)).days)


def test_the_walk_part_is_the_utc_days_ordinal_and_24_nights_cover_every_part() -> None:
    nov14 = datetime.date(2026, 11, 14)
    assert qci.walk_part_of({"QMX_WALK_DAY": _day(nov14)}, 24) == nov14.toordinal() % 24
    nights = [nov14 + datetime.timedelta(days=n) for n in range(24)]
    parts = {qci.walk_part_of({"QMX_WALK_DAY": _day(d)}, 24) for d in nights}
    assert parts == set(range(24))


def test_a_named_walk_part_wins_and_a_walk_with_neither_is_refused() -> None:
    assert qci.walk_part_of({"QMX_WALK_PART": "5", "QMX_WALK_DAY": "20000"}, 24) == 5
    with pytest.raises(qci.CiError, match="QMX_WALK_DAY"):
        qci.walk_part_of({}, 24)


def test_every_walk_shard_reads_the_day_the_level_job_wrote_once() -> None:
    level = WORKFLOW.split("\n  level:\n", 1)[1].split("\n\n", 1)[0]
    assert "day: ${{ steps.pick.outputs.day }}" in level
    assert 'echo "day=$(( $(date -u +%s) / 86400 ))" >> "$GITHUB_OUTPUT"' in level
    walk = WORKFLOW.split("\n  mutmut-walk:\n", 1)[1].split("\n\n", 1)[0]
    assert "QMX_WALK_DAY: ${{ needs.level.outputs.day }}" in walk


# ---- shard times ---------------------------------------------------------------------------------


def _shard(root: Path, system: str, cases: str) -> Path:
    folder = root / system
    (folder / "junit").mkdir(parents=True)
    plan = {
        "system": system,
        "shard": 2,
        "units": ["qmn", "qmx-agents/packages/qmx-host"],
        "files": [".::qmn/tests/test_a.py", "qmx-agents/packages/qmx-host::tests/test_a.py"],
    }
    (folder / f"plan-{system}-2.json").write_text(json.dumps(plan), "utf-8")
    (folder / "junit" / f"{system}-2-qmn.xml").write_text(
        f"<testsuites><testsuite>{cases}</testsuite></testsuites>", "utf-8"
    )
    (folder / "junit" / f"{system}-2-qmx-agents_packages_qmx-host-serial.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.test_a" name="t" time="4.0"/>'
        "</testsuite></testsuites>",
        "utf-8",
    )
    return folder


def test_durations_add_each_files_junit_times_and_keep_the_slower_system(tmp_path: Path) -> None:
    linux = durations.shard_seconds(
        _shard(
            tmp_path,
            "linux",
            '<testcase classname="qmn.tests.test_a" name="x" time="1.5"/>'
            '<testcase classname="qmn.tests.test_a.Case" name="y" time="2.5"/>',
        )
    )
    host = "qmx-agents/packages/qmx-host::tests/test_a.py"
    assert linux == {".::qmn/tests/test_a.py": 4.0, host: 4.0}
    windows = durations.shard_seconds(
        _shard(tmp_path, "windows", '<testcase classname="qmn.tests.test_a" name="x" time="9.0"/>')
    )
    assert durations.durations([linux, windows]) == {
        ".::qmn/tests/test_a.py": 9.0 + ci_units.SECONDS_PER_FILE,
        host: 4.0 + ci_units.SECONDS_PER_FILE,
    }


def test_a_classname_goes_to_the_file_with_the_longest_matching_tail() -> None:
    files = [".::u/tests.py", ".::u/tests/test_a.py"]
    assert durations.matching_file("tests.test_a.TestX", files) == ".::u/tests/test_a.py"
    assert durations.matching_file("tests.test_a.TestX", files[::-1]) == ".::u/tests/test_a.py"
    assert durations.matching_file("other.test_b", files) is None
