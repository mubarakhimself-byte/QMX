"""The GitLab CI driver's planning: which tests a change selects, how shards split, which findings
are new against a baseline, which functions mutmut mutates, and how JUnit outcomes are read."""

from __future__ import annotations

from pathlib import Path

import ci_mutate
import ci_units
import pytest
import qci
import ratchet


def _unit(root: str, workspace: str = ".", cwd: str = ".") -> ci_units.Unit:
    return ci_units.Unit(root, workspace, cwd, (root,))


def test_a_changed_file_selects_its_deepest_owner() -> None:
    units = [_unit("packages/qmf-core"), _unit("qa/tests"), _unit("qa/tests/epic_01")]
    chosen = ci_units.select(units, ["qa/tests/epic_01/test_a.py", "docs/readme.md"])
    assert [u.root for u in chosen] == ["qa/tests/epic_01"]


def test_a_workspace_lockfile_selects_every_unit_in_that_workspace_only() -> None:
    root_unit = _unit("packages/qmf-core")
    agents_unit = _unit(
        "qmx-agents/packages/qmx-host", "qmx-agents", "qmx-agents/packages/qmx-host"
    )
    chosen = ci_units.select([root_unit, agents_unit], ["qmx-agents/uv.lock"])
    assert [u.root for u in chosen] == ["qmx-agents/packages/qmx-host"]


def test_shards_take_every_file_once_and_balance_by_weight() -> None:
    unit = _unit("qmn")
    files = [ci_units.TestFile(unit, f"t{i}.py", w) for i, w in enumerate([9, 5, 4, 3, 2, 1])]
    shards = ci_units.shard(files, 2)
    assert sorted(f.path for s in shards for f in s) == sorted(f.path for f in files)
    assert [sum(f.weight for f in s) for s in shards] == [12.0, 12.0]


def test_a_moved_finding_is_not_new_but_a_second_copy_is() -> None:
    known = ratchet.Finding("a.py", 10, "vulture", "unused import 'x'")
    moved = ratchet.Finding("a.py", 42, "vulture", "unused import 'x'")
    copy = ratchet.Finding("a.py", 50, "vulture", "unused import 'x'")
    assert ratchet.new_findings([moved], [known.key]) == []
    assert ratchet.new_findings([moved, copy], [known.key]) == [copy]


def test_the_baseline_file_round_trips_its_keys(tmp_path: Path) -> None:
    found = [
        ratchet.Finding("b.py", 3, "vulture", "unused variable 'y'"),
        ratchet.Finding("a.py", 1, "vulture", "unused import 'x'"),
    ]
    ratchet.write_baseline(tmp_path / "v.txt", found, "header line")
    assert ratchet.read_baseline(tmp_path / "v.txt") == [
        "a.py|vulture|unused import 'x'",
        "b.py|vulture|unused variable 'y'",
    ]


SOURCE = """\
def top(a):
    return a + 1


class Book:
    def entry(self, x):
        if x:
            return 1
        return 2


def other():
    return 0
"""


def test_a_diff_maps_to_the_functions_holding_its_new_lines() -> None:
    diff = "@@ -7 +7 @@\n-            return 0\n+            return 1\n@@ -2,0 +2,1 @@\n+    pass\n"
    lines = ci_mutate.changed_lines(diff)
    assert lines == {7, 2}
    assert ci_mutate.touched_functions(SOURCE, lines) == ["top", "Book.entry"]


def test_mutmut_globs_use_its_mangled_names() -> None:
    method = ci_mutate.Target("qmn", "qmn.ledger.virtual", "Book.entry")
    function = ci_mutate.Target("qmn", "qmn.ledger.virtual", "top")
    assert method.glob == "qmn.ledger.virtual.xǁBookǁentry__mutmut_*"
    assert function.glob == "qmn.ledger.virtual.x_top__mutmut_*"


def test_only_package_source_files_are_mutation_sources() -> None:
    assert ci_mutate.source_package("qmn/src/qmn/ledger/virtual.py") == (
        "qmn",
        "qmn/ledger/virtual.py",
    )
    assert ci_mutate.source_package("qmn/tests/test_virtual.py") is None
    assert ci_mutate.source_package("qmn/src/qmn/__init__.py") is None


def test_the_walk_puts_every_function_in_exactly_one_part() -> None:
    targets = [ci_mutate.Target("p", "m", f"f{i}") for i in range(50)]
    parts = [ci_mutate.walk_part(targets, k, 4) for k in range(4)]
    assert sorted(t.function for p in parts for t in p) == sorted(t.function for t in targets)


def test_mutmut_results_count_survivors_and_untested_per_function() -> None:
    text = (
        "    m.x_f__mutmut_1: killed\n    m.x_f__mutmut_2: survived\n"
        "    m.xǁCǁg__mutmut_1: no tests\n    m.x_h__mutmut_1: survived\n"
    )
    targets = [ci_mutate.Target("p", "m", "f"), ci_mutate.Target("p", "m", "C.g")]
    counts = ci_mutate.survivors_by_function(ci_mutate.parse_results(text), targets)
    assert counts == {"p|m.f": 1, "p|m.C.g": 1}


JUNIT = """<?xml version="1.0"?><testsuites><testsuite>
<testcase classname="tests.test_a" name="test_pass"/>
<testcase classname="tests.test_a" name="test_assert">
<failure message="assert 1 == 2">x</failure></testcase>
<testcase classname="tests.test_a" name="test_crash">
<failure message="NameError: y">x</failure></testcase>
<testcase classname="tests.test_a" name="test_setup"><error message="fixture">x</error></testcase>
<testcase classname="tests.test_a" name="test_skip"><skipped message="no"/></testcase>
</testsuite></testsuites>"""


def test_junit_outcomes_tell_an_assertion_from_any_other_failure(tmp_path: Path) -> None:
    report = tmp_path / "r.xml"
    report.write_text(JUNIT, "utf-8")
    assert qci.outcomes(report) == {
        "tests.test_a::test_pass": "passed",
        "tests.test_a::test_assert": "assertion",
        "tests.test_a::test_crash": "failed",
        "tests.test_a::test_setup": "error",
        "tests.test_a::test_skip": "skipped",
    }


@pytest.mark.parametrize(
    ("level", "scope"),
    [("slice", "touched"), ("land", "touched"), ("deep", "all"), ("release", "all")],
)
def test_each_test_level_has_its_scope(level: str, scope: str) -> None:
    assert qci.TEST_SCOPE[qci.Level(level)] == scope


def test_skylos_blocks_security_and_high_findings_but_only_notes_dead_code(tmp_path: Path) -> None:
    report = tmp_path / "skylos.json"
    report.write_text(
        '{"danger": [{"file": "qmn/src/a.py", "line": 3, "rule_id": "SKY-D211", "message": "eval"}],'
        ' "unused_functions": [{"file": "qmn/src/b.py", "line": 9, "name": "f", "severity": "HIGH"}],'
        ' "quality": [{"file": "qmn/src/c.py", "line": 1, "rule_id": "SKY-Q301", "message": "deep",'
        ' "severity": "MEDIUM"}], "summary": {"total": 3}}',
        "utf-8",
    )
    found = {(f.path, f.rule, f.blocking) for f in qci.skylos_findings(report)}
    assert found == {
        ("qmn/src/a.py", "danger:SKY-D211", True),
        ("qmn/src/b.py", "unused_functions:unused_functions", False),
        ("qmn/src/c.py", "quality:SKY-Q301", False),
    }


def test_skylos_lists_that_are_not_findings_are_ignored(tmp_path: Path) -> None:
    report = tmp_path / "skylos.json"
    report.write_text(
        '{"whitelisted": [{"file": "a.py", "line": 1, "name": "BLOCKED", "severity": "HIGH"}],'
        ' "suppressed": [{"file": "b.py", "line": 2, "name": "x"}], "danger": []}',
        "utf-8",
    )
    assert qci.skylos_findings(report) == []
