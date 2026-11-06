"""The proof runner's own proof: the table names real tests, and a failing check reads FAIL.

The table is a relation across rows. Checks 7 to 16 are proven by tests on R06, R07, R08, R10 and
R12, which are not joined into this provisional parent, so `NOT_ON_THIS_STACK_YET` names each of
those ids with the PR that adds it. A missing id outside that literal fails this test, and the
runner still runs every named id and prints FAIL for one that is not there.

The relation is read from the files, not by importing them: this test runs in the whole-repo lane,
and a `pytest --collect-only` of `qml`, `qmb` and the agents packages costs minutes on a loaded
machine. That the table collects and runs is lane 3's `--only 1-17`, which is the run that matters.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import proof_foundation
import pytest

REPO: Final = Path(__file__).resolve().parents[2]

NOT_ON_THIS_STACK_YET: Final[dict[str, str]] = {
    "qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py": "R06",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_fresh_home_with_ticks_in_the_store_lands_a_result": "R08",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_no_month_is_refused_naming_the_month_and_the_template": "R08",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_month_through_a_csv_and_through_the_store_gives_the_same_trades": "R08",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_record_moved_on_main_shows_in_the_next_run": "R07",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_study_forbidding_gaps_beats_a_chat_allowing_them": "R07",
    "qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_sealed_month_is_refused_and_no_sealed_file_sits_in_a_run_folder": "R08",
    "qmx-agents/apps/qmb/tests/test_run_honesty.py::test_a_stated_cost_profile_changes_money_and_not_r": "R10",
    "qmb/tests/test_windowed_reader.py::test_a_real_backtest_of_200000_steps_stays_flat": "R10",
    "qmx-agents/packages/qmx-engine/tests/test_templates.py::test_b_real_qmb_real_referee_real_scorecard": "R12",
    "qmx-agents/packages/qmx-engine/tests/test_templates.py::test_a_forged_pass_routes_as_fail": "R12",
}


def defines(node_id: str) -> bool:
    """Whether the file exists and the id names a module-level test function, or any test in it."""
    path_text, _, name = node_id.partition("::")
    path = REPO / path_text
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    tests = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test")
    }
    return name in tests if name else bool(tests)


def test_every_check_names_a_test_that_exists() -> None:
    table = proof_foundation.TABLE

    assert [check.number for check in table] == list(range(1, 19))
    for check in table:
        assert check.tests, f"check {check.number} names no test"
        assert check.limit_s > 0, f"check {check.number} has no time limit"
        for test in check.tests:
            assert test.environment in {"root", "agents"}, test.node_id

    named = {test.node_id for check in table for test in check.tests}
    assert set(NOT_ON_THIS_STACK_YET) <= named
    assert all(pr.startswith("R") for pr in NOT_ON_THIS_STACK_YET.values())

    absent = {
        test.node_id
        for check in table
        for test in check.tests
        if test.node_id not in NOT_ON_THIS_STACK_YET and not defines(test.node_id)
    }
    assert absent == set()


def test_a_failing_check_prints_fail_and_exits_non_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = tmp_path / "test_fake_node.py"
    fake.write_text(
        "import pytest\n"
        "\n"
        "def test_it_fails() -> None:\n"
        "    assert False, 'this fake check is made to fail'\n"
        "\n"
        "def test_it_skips() -> None:\n"
        "    pytest.skip('this fake check is made to skip')\n",
        encoding="utf-8",
    )

    for case, node in (("fails", "test_it_fails"), ("skips", "test_it_skips")):
        check = proof_foundation.Check(
            number=1,
            name=f"a fake node that {case}",
            tests=(proof_foundation.Test("root", f"{fake}::{node}"),),
            limit_s=120.0,
        )

        code = proof_foundation.main([], table=(check,))
        printed = capsys.readouterr().out

        assert code == 1
        assert "FAIL 1 " in printed
        assert "PASS 1 " not in printed
