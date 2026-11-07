"""The proof runner's own proof: the table names real tests, and a failing check reads FAIL.

The table is a relation across rows. The relation is read from the files, not by importing them:
this test runs in the whole-repo lane, and a `pytest --collect-only` of `qml`, `qmb` and the agents
packages costs minutes on a loaded machine. That the table collects and runs is lane 3's
`--only 1-17`, which is the run that matters.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import proof_foundation
import pytest

REPO: Final = Path(__file__).resolve().parents[2]


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

    absent = {test.node_id for check in table for test in check.tests if not defines(test.node_id)}
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
