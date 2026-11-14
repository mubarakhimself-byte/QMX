"""The CI driver's planning: which tests a change selects, how shards split, which findings are new
against a baseline, which functions mutmut mutates, how JUnit outcomes are read, which run facts it
takes from GitHub Actions or a laptop, and when the pull-request gate and a release pass."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import ci_host
import ci_mutate
import ci_units
import guard
import pull_reds
import pytest
import qci
import ratchet
import tomllib


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
        '{"danger": [{"file": "qmn/src/a.py", "line": 3, "rule_id": "SKY-D211",'
        ' "message": "eval"}],'
        ' "unused_functions": [{"file": "qmn/src/b.py", "line": 9, "name": "f",'
        ' "severity": "HIGH"}],'
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


HEAD = "a" * 40
OTHER = "b" * 40


def test_github_facts_take_the_pull_request_head_not_the_merge_commit() -> None:
    facts = ci_host.read(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_SHA": OTHER,
            "QMX_HEAD_SHA": HEAD,
            "QMX_BEFORE_SHA": "",
            "QMX_SHARD": "3",
            "QMX_SHARDS": "8",
            "GITHUB_RUN_NUMBER": "41",
            "GITHUB_REF_NAME": "17/merge",
            "GITHUB_HEAD_REF": "ci/github",
            "GITHUB_RUN_ID": "9001",
        }
    )
    assert facts == ci_host.RunFacts(ci_host.Host.GITHUB, HEAD, None, 3, 8, 41, "ci/github", "9001")


def test_a_github_push_reads_its_sha_and_before_and_a_new_branch_has_no_before() -> None:
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_SHA": HEAD,
        "QMX_BEFORE_SHA": OTHER,
        "GITHUB_REF_NAME": "build/x",
    }
    facts = ci_host.read(env)
    assert (facts.head, facts.before, facts.shard, facts.shards, facts.ref) == (
        HEAD,
        OTHER,
        1,
        1,
        "build/x",
    )
    assert ci_host.read({**env, "QMX_BEFORE_SHA": "0" * 40}).before is None


def test_gitlab_variables_alone_are_a_laptop_now() -> None:
    facts = ci_host.read({"GITLAB_CI": "true", "CI_COMMIT_SHA": HEAD, "CI_NODE_INDEX": "2"})
    assert facts.host == ci_host.Host.LAPTOP


def test_a_laptop_has_one_shard_and_reads_head_from_git() -> None:
    facts = ci_host.read({"CI_COMMIT_SHA": HEAD})
    assert facts == ci_host.RunFacts(ci_host.Host.LAPTOP, None, None, 1, 1, 0, "", "")


def test_tests_run_without_the_hosts_variables_but_keep_ci_and_qmx() -> None:
    env = {
        "CI": "true",
        "CI_JOB_TOKEN": "t",
        "GITLAB_CI": "true",
        "GITHUB_TOKEN": "t",
        "ACTIONS_RUNTIME_TOKEN": "t",
        "RUNNER_TEMP": "runner-temp",
        "QMX_LEVEL": "deep",
        "PATH": "/bin",
    }
    assert ci_host.test_env(env) == {"CI": "true", "QMX_LEVEL": "deep", "PATH": "/bin"}


def _deep(sha: str, level: str = "deep") -> dict[str, object]:
    return {"sha": sha, "level": level, "ref": "ci/github", "pipeline": "1"}


def test_the_gate_passes_on_a_green_deep_run_of_the_exact_head() -> None:
    runs = [qci.DeepRun("u/2", None), qci.DeepRun("u/1", _deep(HEAD))]
    assert qci.gate_decision(HEAD, runs, "how") == (
        True,
        f"PASS deep run u/1 is green on {HEAD[:10]}",
    )


def test_the_gate_fails_with_no_green_run_on_the_head() -> None:
    assert qci.gate_decision(HEAD, [], "start one") == (
        False,
        f"FAIL no green deep run tested the head {HEAD[:10]}; start one",
    )


@pytest.mark.parametrize(
    "verdict", [None, _deep(OTHER), _deep(HEAD, level="release")], ids=["none", "sha", "level"]
)
def test_the_gate_fails_when_no_green_run_is_a_deep_run_of_the_head(
    verdict: dict[str, object] | None,
) -> None:
    ok, message = qci.gate_decision(HEAD, [qci.DeepRun("u/1", verdict)], "how")
    assert (ok, message.split(",")[0]) == (False, f"FAIL 1 green run(s) on {HEAD[:10]}")


def test_pull_reds_reads_each_shard_and_names_the_ones_that_did_not_finish(tmp_path: Path) -> None:
    done = tmp_path / "done"
    done.mkdir()
    (done / "reds-linux-1.txt").write_text("linux|qmn|t::b\nlinux|qmn|t::a\n", "utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "plan-linux-2.json").write_text(json.dumps({"files": []}), "utf-8")
    cut = tmp_path / "cut"
    cut.mkdir()
    (cut / "plan-linux-3.json").write_text(json.dumps({"files": ["qmn::t.py"]}), "utf-8")
    shards = {
        "suite-linux-1": pull_reds.shard_reds(done),
        "suite-linux-2": pull_reds.shard_reds(empty),
        "suite-linux-3": pull_reds.shard_reds(cut),
        "suite-windows-1": None,
    }
    assert pull_reds.known_reds_text("77", shards) == (
        "# Tests red on GitHub Actions run 77. Key: system|unit|test id.\n"
        "# A red listed here does not block; any other red does. This list may only shrink.\n"
        "# Shards read: suite-linux-1, suite-linux-2.\n"
        "# Shards that did not finish, so their reds are not listed: suite-linux-3, "
        "suite-windows-1.\n"
        "linux|qmn|t::a\nlinux|qmn|t::b\n"
    )


# ---- types join the ratchet; Skylos scans the change at deep and folders at baseline -----------


def _pyright(root: Path, *diagnostics: tuple[str, str, str, int]) -> str:
    """pyright --outputjson as the PyPI wrapper prints it: a set-up line, then the report."""
    report = {
        "version": "1.1.400",
        "generalDiagnostics": [
            {
                "file": str(root / path),
                "severity": severity,
                "message": message,
                "range": {"start": {"line": line, "character": 4}},
                "rule": "reportAttributeAccessIssue",
            }
            for path, severity, message, line in diagnostics
        ],
        "summary": {"errorCount": len(diagnostics)},
    }
    return "installing node...\n" + json.dumps(report, indent=4) + "\n"


def test_a_pyright_error_becomes_a_key_without_line_or_numbers(tmp_path: Path) -> None:
    text = _pyright(
        tmp_path,
        ("pkg/a.py", "error", '"WinDLL" is not a known\n  attribute of 2 modules', 41),
        ("pkg/a.py", "warning", "only a warning", 3),
    )
    found = qci.pyright_findings(qci.pyright_report(text), tmp_path)
    assert [(f.key, f.line) for f in found] == [
        ('pkg/a.py|reportAttributeAccessIssue|"WinDLL" is not a known attribute of # modules', 42)
    ]


def test_pyright_with_no_report_is_an_error() -> None:
    with pytest.raises(qci.CiError):
        qci.pyright_report("node: command not found\n")


def _types_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[ratchet.Finding]:
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    (tmp_path / "out").mkdir()
    old = ratchet.Finding("pkg/old.py", 5, "reportX", "known error")
    ratchet.write_baseline(tmp_path / "baselines" / "pyright.txt", [old], "header")
    return [dataclasses.replace(old, line=9)]


def test_a_pyright_error_in_the_baseline_does_not_fail_a_slice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    found = _types_case(tmp_path, monkeypatch)
    assert qci.types_verdict(found, ["pkg/old.py"]) == 0


def test_a_new_pyright_error_in_a_touched_file_fails_a_slice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    found = _types_case(tmp_path, monkeypatch)
    found.append(ratchet.Finding("pkg/new.py", 1, "reportX", "fresh error"))
    assert qci.types_verdict(found, ["pkg/new.py"]) == 1
    assert "BLOCK pkg/new.py:1: [reportX] fresh error" in (
        tmp_path / "out" / "pyright-new.txt"
    ).read_text("utf-8")


def test_a_new_pyright_error_in_an_untouched_file_is_a_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    found = _types_case(tmp_path, monkeypatch)
    found.append(ratchet.Finding("pkg/other.py", 1, "reportX", "fresh error"))
    assert qci.types_verdict(found, ["pkg/old.py"]) == 0
    assert "note  pkg/other.py:1: [reportX] fresh error" in (
        tmp_path / "out" / "pyright-new.txt"
    ).read_text("utf-8")


def test_the_same_pyright_error_from_two_folders_counts_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    found = _types_case(tmp_path, monkeypatch)
    assert qci.types_verdict(found + found, None) == 0


@pytest.mark.parametrize(("level", "diff"), [("slice", True), ("deep", True), ("release", False)])
def test_skylos_scans_only_the_change_at_slice_and_deep(
    level: str, diff: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(qci, "uv", lambda: "uv")

    def base_for(lvl: qci.Level, at: str) -> str:
        return OTHER

    monkeypatch.setattr(qci, "base_for", base_for)
    base = qci.skylos_base(qci.Level(level), HEAD)
    argv = qci.skylos_argv(".", Path("r.json"), base)
    assert ("--diff-base" in argv, argv[-1] == OTHER) == (diff, diff)


def test_a_folder_scan_path_is_made_repo_relative(tmp_path: Path) -> None:
    (tmp_path / "qmn" / "src").mkdir(parents=True)
    (tmp_path / "qmn" / "src" / "a.py").write_text("", "utf-8")
    assert qci.repo_path("qmn", "src/a.py", tmp_path) == "qmn/src/a.py"
    assert qci.repo_path("qmn", "qmn/src/a.py", tmp_path) == "qmn/src/a.py"


def test_the_skylos_parts_join_keeping_each_keys_largest_count_and_a_missing_part_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    parts = tmp_path / "parts"
    (parts / "ci-out-skylos-part-qmn").mkdir(parents=True)
    (parts / "ci-out-skylos-part-qmn" / "skylos-part-qmn.txt").write_text(
        "qmn/b|r|n\nuv.lock|d|x\n", "utf-8"
    )
    (parts / "ci-out-skylos-part-qmb").mkdir(parents=True)
    (parts / "ci-out-skylos-part-qmb" / "skylos-part-qmb.txt").write_text(
        "qmb/a|r|n\nqmb/a|r|n\nuv.lock|d|x\n", "utf-8"
    )
    with pytest.raises(qci.CiError, match="tools"):
        qci.skylos_merge(parts, ("qmn", "qmb", "tools"), HEAD)
    assert qci.skylos_merge(parts, ("qmn", "qmb"), HEAD) == 0
    assert ratchet.read_baseline(tmp_path / "baselines" / "skylos.txt") == [
        "qmb/a|r|n",
        "qmb/a|r|n",
        "qmn/b|r|n",
        "uv.lock|d|x",
    ]


REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".svelte", ".rs")


def test_the_skylos_baseline_parts_cover_every_scanned_folder() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text("utf-8"))
    excluded = set(config["tool"]["skylos"]["exclude"])
    tracked = qci.git("ls-files", cwd=REPO_ROOT).splitlines()
    folders = {
        p.split("/", 1)[0]
        for p in tracked
        if "/" in p and p.endswith(CODE_SUFFIXES) and not p.startswith(".")
    }
    assert folders - excluded <= set(qci.SKYLOS_FOLDERS)
    workflow = (REPO_ROOT / ".github" / "workflows" / "qmx-ci.yml").read_text("utf-8")
    matrix = workflow.split("name: skylos-part", 1)[1].split("folder: [", 1)[1].split("]", 1)[0]
    assert tuple(f.strip() for f in matrix.split(",")) == qci.SKYLOS_FOLDERS


# ---- flaky reruns, the run summary, the ratchet guard and prune ---------------------------------


QMN = _unit("qmn")


def _verdict_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    (tmp_path / "out").mkdir()


def test_a_red_test_that_passes_on_its_rerun_is_flaky_and_the_job_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _verdict_case(tmp_path, monkeypatch)
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "flaky.txt").write_text(
        "# known flaky\nlinux|qmn|qmn.tests.test_clock::test_fast\n", "utf-8"
    )
    first = {"qmn.tests.test_clock::test_fast": "assertion", "qmn.tests.test_a::test_b": "passed"}
    again = {"qmn.tests.test_clock::test_fast": "passed"}
    reds, flaky = qci.split_flaky("linux", QMN, first, again, ["qmn/src/qmn/clock.py"])
    assert (reds, flaky) == ([], ["linux|qmn|qmn.tests.test_clock::test_fast"])
    assert qci.tests_verdict("linux-1", reds, [], flaky) == 0
    assert "FLAKY linux|qmn|qmn.tests.test_clock::test_fast" in capsys.readouterr().out
    assert (tmp_path / "out" / "flaky-linux-1.txt").read_text("utf-8") == (
        "linux|qmn|qmn.tests.test_clock::test_fast\n"
    )
    assert (tmp_path / "out" / "reds-linux-1.txt").read_text("utf-8") == ""


def test_a_flaky_test_in_a_module_the_change_touched_stays_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _verdict_case(tmp_path, monkeypatch)
    first = {"tests.test_clock.TestFast::test_fast": "failed"}
    again = {"tests.test_clock.TestFast::test_fast": "passed"}
    reds, flaky = qci.split_flaky("linux", QMN, first, again, ["qmn/tests/test_clock.py"])
    assert (reds, flaky) == (["linux|qmn|tests.test_clock.TestFast::test_fast"], [])
    assert qci.tests_verdict("linux-1", reds, [], flaky) == 1


def test_a_red_test_that_stays_red_on_its_rerun_is_a_red() -> None:
    first = {"qmn.tests.test_a::test_b": "error"}
    reds, flaky = qci.split_flaky("linux", QMN, first, {"qmn.tests.test_a::test_b": "error"}, [])
    assert (reds, flaky) == (["linux|qmn|qmn.tests.test_a::test_b"], [])


WORKFLOW = (REPO_ROOT / ".github" / "workflows" / "qmx-ci.yml").read_text("utf-8")


def test_the_summary_job_needs_every_job_and_every_job_names_its_levels() -> None:
    jobs = qci.workflow_jobs(WORKFLOW)
    needs = WORKFLOW.split("\n  summary:\n", 1)[1].split("needs: [", 1)[1].split("]", 1)[0]
    assert sorted(n.strip() for n in needs.split(",")) == sorted(set(jobs) - {"summary"})
    for job, condition in jobs.items():
        assert job in ("level", "summary") or qci.job_levels(condition), job


def test_the_deep_level_holds_the_suites_and_the_verdict() -> None:
    deep = qci.level_jobs(WORKFLOW, qci.Level.DEEP)
    assert {"lint", "suite-linux", "suite-windows", "mutmut", "deep-verdict"} <= set(deep)
    assert "tests-linux" not in deep and "summary" not in deep


def _artifacts(root: Path) -> Path:
    shard = root / "ci-out-suite-linux-1"
    shard.mkdir(parents=True)
    (shard / "reds-linux-1.txt").write_text("linux|qmn|t::new\nlinux|qmn|t::old\n", "utf-8")
    (shard / "flaky-linux-1.txt").write_text("linux|qmn|t::flaky\n", "utf-8")
    tools = root / "ci-out-vulture"
    tools.mkdir()
    (tools / "vulture-ratchet.json").write_text(
        json.dumps(
            {
                "tool": "vulture",
                "complete": True,
                "new": [{"key": "a.py|vulture|x", "file": "a.py", "line": 3, "blocking": True}],
                "gone": ["b.py|vulture|y"],
            }
        ),
        "utf-8",
    )
    mut = root / "ci-out-mutmut-1"
    mut.mkdir()
    (mut / "mutmut-counts-1.json").write_text(
        '{"killed": 10, "survived": 1, "no tests": 1}', "utf-8"
    )
    (mut / "mutmut-1-ratchet.json").write_text(
        json.dumps(
            {
                "tool": "mutmut",
                "complete": False,
                "new": [{"key": "qmn|mutmut|m.f survived", "file": "qmn", "line": 0}],
                "gone": [],
            }
        ),
        "utf-8",
    )
    return root


def test_the_summary_of_a_run_with_one_red_job_is_red_and_lists_every_finding(
    tmp_path: Path,
) -> None:
    jobs = ["lint", "suite-linux", "mutmut", "docker-node"]
    needs = {
        "lint": {"result": "success"},
        "suite-linux": {"result": "failure"},
        "mutmut": {"result": "success"},
        "docker-node": {"result": "skipped"},
    }
    api = [
        {
            "name": "suite-linux 1",
            "conclusion": "failure",
            "started_at": "2026-11-13T10:00:00Z",
            "completed_at": "2026-11-13T10:08:32Z",
        },
        {"name": "summary", "conclusion": None, "status": "in_progress"},
        {"name": "tests-linux ${{ matrix.shard }}", "conclusion": "skipped"},
    ]
    summary = qci.build_summary(
        sha=HEAD,
        ref="build/x",
        run_id="77",
        url="https://github.com/o/r/actions/runs/77",
        lvl=qci.Level.DEEP,
        jobs_of_level=jobs,
        needs=needs,
        api_jobs=api,
        artifacts=_artifacts(tmp_path / "artifacts"),
        known_reds=["linux|qmn|t::old"],
    )
    assert summary == {
        "sha": HEAD,
        "ref": "build/x",
        "run_id": 77,
        "url": "https://github.com/o/r/actions/runs/77",
        "level": "deep",
        "green": False,
        "jobs": [{"name": "suite-linux-1", "result": "failure", "seconds": 512}],
        "reds": [
            {"id": "qmn|t::new", "system": "linux", "kind": "new", "blocks": True},
            {"id": "qmn|t::old", "system": "linux", "kind": "known", "blocks": False},
            {"id": "qmn|t::flaky", "system": "linux", "kind": "flaky", "blocks": True},
        ],
        "quality": [
            {"tool": "mutmut", "key": "qmn|mutmut|m.f survived", "file": "qmn", "kind": "new"},
            {"tool": "vulture", "key": "a.py|vulture|x", "file": "a.py", "kind": "new"},
            {"tool": "vulture", "key": "b.py|vulture|y", "file": "b.py", "kind": "gone"},
        ],
        "mutants": {"killed": 10, "survived": 2, "new_survivors": 1},
        "skipped": ["docker-node"],
    }
    text = qci.summary_markdown(summary)
    assert text.startswith(f"## CI deep {HEAD[:10]}: RED\n")
    assert "| suite-linux-1 | failure | 512 |" in text


def test_a_summary_with_no_job_list_takes_results_from_needs(tmp_path: Path) -> None:
    summary = qci.build_summary(
        sha=HEAD,
        ref="r",
        run_id="",
        url="",
        lvl=qci.Level.SLICE,
        jobs_of_level=["lint"],
        needs={"lint": {"result": "success"}},
        api_jobs=None,
        artifacts=tmp_path,
        known_reds=[],
    )
    assert (summary["green"], summary["jobs"]) == (
        True,
        [{"name": "lint", "result": "success", "seconds": 0}],
    )


def _repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    (root / "ci" / "baselines").mkdir(parents=True)
    (root / "ci" / "baselines" / "v.txt").write_text("# header\na|r|1\nb|r|2\n", "utf-8")
    for args in (
        ["init", "-q", "-b", "main"],
        ["add", "-A"],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"],
    ):
        qci.git(*args, cwd=root)
    return root, qci.git("rev-parse", "HEAD", cwd=root).strip()


def _commit(root: Path, name: str, text: str) -> str:
    (root / "ci" / "baselines" / name).write_text(text, "utf-8")
    qci.git("add", "-A", cwd=root)
    qci.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x", cwd=root)
    return qci.git("rev-parse", "HEAD", cwd=root).strip()


def test_this_change_loosens_nothing_the_ratchet_holds() -> None:
    """The ratchet only tightens: the change since engine/base grows no baseline and adds no
    suppression, unless it is a baseline retake (`qci.py ratchet --prune` only ever removes)."""
    branch = os.environ.get("QMX_REF") or qci.git("branch", "--show-current").strip()
    engine = f"refs/remotes/origin/{qci.ENGINE}"
    base = qci.merge_base("HEAD", engine)
    assert base is not None, f"{engine} must be fetched for the guard to measure the change"
    assert guard.problems(REPO_ROOT, base, "HEAD", branch) == []


def test_a_baseline_change_selects_the_tools_tests_that_hold_the_guard() -> None:
    units = [_unit("tools"), _unit("qmn")]
    assert [u.root for u in ci_units.select(units, ["ci/baselines/pyright.txt"])] == ["tools"]


def test_gone_keys_are_counted_and_only_in_covered_files() -> None:
    found = [ratchet.Finding("a.py", 1, "r", "x")]
    baseline = ["a.py|r|x", "a.py|r|x", "b.py|r|y", "c.py|r|z"]
    assert ratchet.gone_keys(found, baseline, lambda p: p != "c.py") == ["a.py|r|x", "b.py|r|y"]


def test_prune_removes_a_gone_key_and_keeps_the_rest_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "head", lambda: "s1")
    monkeypatch.setattr(qci, "tree_of", "t1".format)
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "vulture.txt").write_text(
        "# header\nz.py|v|1\na.py|v|gone\nm.py|v|2\nm.py|v|stale\n", "utf-8"
    )
    out = tmp_path / "out" / "ci-out-vulture"
    out.mkdir(parents=True)
    (out / "vulture-ratchet.json").write_text(
        json.dumps({"tool": "vulture", "sha": "s1", "new": [], "gone": ["a.py|v|gone"]}), "utf-8"
    )
    old = tmp_path / "out" / "ci-out-old"
    old.mkdir()
    (old / "vulture-ratchet.json").write_text(
        json.dumps({"tool": "vulture", "sha": "s0", "tree": "t0", "gone": ["m.py|v|stale"]}),
        "utf-8",
    )
    assert qci.ratchet_prune(["vulture", "skylos"], tmp_path / "out") == 0
    assert (tmp_path / "baselines" / "vulture.txt").read_text("utf-8") == (
        "# header\nz.py|v|1\nm.py|v|2\nm.py|v|stale\n"
    )
    out_text = capsys.readouterr().out
    assert "PRUNED vulture 1 (from 1 result file(s) in out, 1 stale one(s) skipped)" in out_text
    assert "PRUNED skylos 0 (from skylos shrinks only at the baseline level" in out_text


# ---- the gate reruns nothing; a release allows no red --------------------------------------------


@pytest.mark.parametrize(
    ("changed", "checks"),
    [
        (["docs/a.md", "contracts/CHANGELOG.md", "qmn/README.md", "docs/img.png"], ("docs-lint",)),
        (["docs/a.md", "qmn/src/qmn/a.py"], ("deep-verdict",)),
        (["contracts/api.json"], ("deep-verdict",)),
        ([], ("deep-verdict",)),
    ],
    ids=["docs-only", "docs-and-code", "contract", "nothing"],
)
def test_a_docs_only_change_needs_only_docs_lint_at_the_gate(
    changed: list[str], checks: tuple[str, ...]
) -> None:
    assert qci.gate_checks(changed) == checks


def test_the_gate_level_runs_the_gate_alone() -> None:
    assert qci.level_jobs(WORKFLOW, qci.Level.GATE) == ["gate"]
    for lvl in (qci.Level.DEEP, qci.Level.RELEASE):
        assert {"docker-node", "qmn-lane"} <= set(qci.level_jobs(WORKFLOW, lvl))


def test_docs_lint_finds_a_broken_link_and_a_conflict_marker(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "there.md").write_text("# there\n", "utf-8")
    (tmp_path / "docs" / "a.md").write_text(
        "[ok](there.md#top) [web](https://x.org/y) [anchor](#here) [root](/docs/there.md)\n"
        "[gone](missing.md)\n<<<<<<< HEAD\n",
        "utf-8",
    )
    found = qci.docs_findings(["docs/a.md", "docs/there.md", "docs/img.png"], tmp_path)
    assert [f.text() for f in found] == [
        "docs/a.md:3: [docs-lint] merge-conflict marker",
        "docs/a.md:2: [docs-lint] broken link missing.md",
    ]


@pytest.mark.parametrize(("level", "rc"), [("release", 1), ("deep", 0)])
def test_a_known_red_blocks_a_release_but_not_a_deep_run(
    level: str, rc: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _verdict_case(tmp_path, monkeypatch)
    monkeypatch.setenv("QMX_LEVEL", level)
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "known-reds.txt").write_text("linux|qmn|t::old\n", "utf-8")
    assert qci.tests_verdict("linux-1", ["linux|qmn|t::old"], []) == rc


def test_a_release_must_sit_on_engine_base_and_have_a_green_deep_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, base = _repo(tmp_path)
    at = _commit(root, "v.txt", "# header\n")
    qci.git("branch", "side", base, cwd=root)
    monkeypatch.setattr(qci, "REPO", root)
    assert qci.release_problems(at, ["refs/heads/main"], deep_ok=True) == []
    assert qci.release_problems(at, ["refs/heads/side"], deep_ok=False) == [
        f"{at[:10]} is not on engine/base or a release/v* branch (checked: refs/heads/side)",
        f"no green deep run vouches for {at[:10]}",
    ]


# ---- the fix round (factory build log D-L17): guard, trust, flaky, summary, probes --------------

NOQA = "#" + " noqa"
GIT = shutil.which("git") or "git"
T = TypeVar("T")


def _returns(value: T) -> Callable[..., T]:
    """A stand-in for a function, whatever it is called with."""

    def answer(*args: object, **kwargs: object) -> T:
        return value

    return answer


# ---- a throwaway git repository ------------------------------------------------------------------


def _git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    done = subprocess.run(
        [GIT, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", *args],
        cwd=root,
        input=stdin,
        capture_output=True,
        check=True,
        timeout=120,
    )
    return done.stdout.decode("utf-8").strip()


def _write(root: Path, rel: str, data: str | bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_bytes(data.encode("utf-8"))


def _gcommit(root: Path, files: dict[str, str | bytes], delete: tuple[str, ...] = ()) -> str:
    for rel, data in files.items():
        _write(root, rel, data)
    for rel in delete:
        (root / rel).unlink()
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "x")
    return _git(root, "rev-parse", "HEAD")


PYPROJECT = """[tool.pyright]
typeCheckingMode = "strict"
reportUnknownMemberType = "error"

[tool.ruff.lint]
ignore = ["E501"]

[tool.skylos]
exclude = ["docs"]
"""


def _grepo(tmp_path: Path, baselines: bool = True) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    files: dict[str, str | bytes] = {
        "pyproject.toml": PYPROJECT,
        "pkg/a.py": f"import os  {NOQA}: F401\n",
        "pkg/b.py": "x = 1\n",
    }
    if baselines:
        files["ci/baselines/v.txt"] = "# header\na|r|1\nb|r|2\n"
    return root, _gcommit(root, files)


def test_an_added_baseline_row_is_growth_and_a_removed_one_is_not(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    grown = _gcommit(root, {"ci/baselines/v.txt": "# header changed\na|r|1\nb|r|2\nc|r|3\n"})
    assert guard.baseline_growth(root, base, grown) == ["ci/baselines/v.txt: + c|r|3"]
    shrunk = _gcommit(root, {"ci/baselines/v.txt": "# header\nb|r|2\n"})
    assert guard.baseline_growth(root, base, shrunk) == []


def test_a_nul_byte_cannot_hide_a_new_row(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"ci/baselines/v.txt": b"# header\na|r|1\nb|r|2\nc|r|3\x00\n"})
    assert guard.baseline_growth(root, base, at) == ["ci/baselines/v.txt: holds a NUL byte"]


def test_a_minus_diff_attribute_cannot_hide_a_new_row(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(
        root,
        {
            ".gitattributes": "ci/baselines/* -diff\n",
            "ci/baselines/v.txt": "# header\na|r|1\nb|r|2\nc|r|3\n",
        },
    )
    assert guard.baseline_growth(root, base, at) == [
        "ci/baselines/v.txt: marked binary or -diff in .gitattributes"
    ]


def test_a_symlink_cannot_stand_in_for_a_baseline(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    _gcommit(root, {"elsewhere.txt": "a|r|1\nb|r|2\nc|r|3\n"})
    target = _git(root, "hash-object", "-w", "--stdin", stdin=b"../../elsewhere.txt")
    _git(root, "update-index", "--cacheinfo", f"120000,{target},ci/baselines/v.txt")
    _git(root, "commit", "-q", "-m", "link")
    at = _git(root, "rev-parse", "HEAD")
    assert guard.baseline_growth(root, base, at) == [
        "ci/baselines/v.txt: not a regular file (mode 120000)"
    ]


def test_deleting_a_baseline_or_adding_one_is_growth_once_baselines_exist(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"ci/baselines/w.txt": "x|r|1\n"}, delete=("ci/baselines/v.txt",))
    assert guard.baseline_growth(root, base, at) == [
        "ci/baselines/v.txt: deleted",
        "ci/baselines/w.txt: new baseline file",
    ]


def test_the_change_that_brings_the_ratchet_in_may_add_baselines(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path, baselines=False)
    at = _gcommit(root, {"ci/baselines/v.txt": "a|r|1\n", "pkg/c.py": f"x = 1  {NOQA}\n"})
    assert guard.problems(root, base, at, "ci/github") == []


@pytest.mark.parametrize(
    ("branch", "also", "loosened"),
    [
        ("baseline/known-reds", {}, False),
        ("baseline/known-reds", {"pkg/b.py": "x = 2\n"}, True),
        ("ci/github", {}, True),
    ],
    ids=["retake", "retake-with-code", "not-a-retake"],
)
def test_only_a_retake_confined_to_ci_baselines_may_grow_one(
    tmp_path: Path, branch: str, also: dict[str, str | bytes], loosened: bool
) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"ci/baselines/v.txt": "# h\na|r|1\nb|r|2\nc|r|3\n", **also})
    assert bool(guard.problems(root, base, at, branch)) == loosened


def test_a_new_suppression_marker_is_loosening_and_a_moved_one_is_not(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    moved = _gcommit(root, {"pkg/a.py": "import os\n", "pkg/b.py": f"x = 1  {NOQA}: F841\n"})
    assert guard.problems(root, base, moved, "x") == []
    more = _gcommit(root, {"pkg/b.py": f"x = 1  {NOQA}: F841\ny = 2  {NOQA}\n"})
    assert guard.problems(root, base, more, "x") == ["1 more noqa marker(s), in pkg/b.py"]


@pytest.mark.parametrize(
    ("edit", "expected"),
    [
        (
            ('reportUnknownMemberType = "error"', 'reportUnknownMemberType = "none"'),
            "pyproject.toml: pyright reportUnknownMemberType set to 'none'",
        ),
        (
            ('typeCheckingMode = "strict"', 'typeCheckingMode = "basic"'),
            "pyproject.toml: pyright typeCheckingMode set to 'basic'",
        ),
        (('ignore = ["E501"]', 'ignore = ["E501", "F401"]'), "[tool.ruff.lint].ignore + F401"),
        (('exclude = ["docs"]', 'exclude = ["docs", "qmn"]'), "[tool.skylos].exclude + qmn"),
    ],
    ids=["pyright-rule", "pyright-mode", "ruff-ignore", "skylos-exclude"],
)
def test_a_config_that_turns_a_check_down_is_loosening(
    tmp_path: Path, edit: tuple[str, str], expected: str
) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"pyproject.toml": PYPROJECT.replace(*edit)})
    found = guard.problems(root, base, at, "x")
    assert len(found) == 1 and expected in found[0], found


def test_a_config_that_tightens_is_not_loosening(tmp_path: Path) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"pyproject.toml": PYPROJECT.replace('ignore = ["E501"]', "ignore = []")})
    assert guard.problems(root, base, at, "x") == []


# ---- the gate trusts only what it should ---------------------------------------------------------


def _verdict(sha: str, ref: str = "ci/github", tree: str = "t1") -> dict[str, object]:
    return {"sha": sha, "tree": tree, "level": "deep", "ref": ref}


def test_a_baseline_runs_verdict_vouches_only_for_a_baseline_pull_request() -> None:
    runs = [qci.DeepRun("u/1", _verdict(HEAD, ref="baseline/x"))]
    assert qci.gate_decision(HEAD, runs, "how", head_ref="ci/github")[0] is False
    assert qci.gate_decision(HEAD, runs, "how", head_ref="baseline/x")[0] is True


def test_a_release_may_match_a_deep_verdict_by_tree() -> None:
    runs = [qci.DeepRun("u/1", _verdict(OTHER, tree="t9"))]
    assert qci.gate_decision(HEAD, runs, "how")[0] is False
    ok, message = qci.gate_decision(HEAD, runs, "how", tree="t9")
    assert ok and message.startswith(f"PASS deep run u/1 is green on {OTHER[:10]}")


@pytest.mark.parametrize(
    "path",
    ["qmn/tests/fixtures/note.md", "packages/x/src/README.md", "examples/apps/README.md"],
)
def test_markdown_inside_code_folders_is_not_docs_only(path: str) -> None:
    assert qci.gate_checks([path]) == ("deep-verdict",)


def _gate_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, loosened: list[str]) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("[gone](missing.md)\n", "utf-8")
    facts = ci_host.RunFacts(ci_host.Host.GITHUB, HEAD, None, 1, 1, 0, "docs/x", "1")
    monkeypatch.setenv("QMX_LEVEL", "gate")
    monkeypatch.setattr(qci, "REPO", tmp_path)
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    monkeypatch.setattr(qci, "facts", _returns(facts))
    monkeypatch.setattr(qci, "head", lambda: HEAD)
    monkeypatch.setattr(qci, "base_for", _returns(OTHER))
    monkeypatch.setattr(qci, "changed_files", _returns(["docs/a.md"]))
    monkeypatch.setattr(guard, "problems", _returns(loosened))


def test_the_gate_runs_docs_lint_on_a_docs_only_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _gate_case(tmp_path, monkeypatch, [])
    assert qci.job_gate() == 1


def test_the_gate_fails_a_change_that_loosens_the_ratchet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _gate_case(tmp_path, monkeypatch, ["ci/baselines/v.txt: + c|r|3"])
    (tmp_path / "docs" / "a.md").write_text("fine\n", "utf-8")
    assert qci.job_gate() == 1
    assert "FAIL loosens the ratchet: ci/baselines/v.txt: + c|r|3" in capsys.readouterr().out


def test_a_release_on_any_one_allowed_branch_is_enough(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, base = _grepo(tmp_path)
    at = _gcommit(root, {"pkg/b.py": "x = 3\n"})
    _git(root, "branch", "release/v1", base)
    monkeypatch.setattr(qci, "REPO", root)
    assert qci.release_problems(at, ["refs/heads/release/v1", "refs/heads/main"], True) == []


# ---- flaky tests against flaky.txt ---------------------------------------------------------------


def _flaky_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flaky: str = "") -> None:
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    (tmp_path / "out").mkdir()
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "flaky.txt").write_text(f"# flaky\n{flaky}", "utf-8")


def test_a_newly_flaky_test_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _flaky_case(tmp_path, monkeypatch)
    assert qci.tests_verdict("linux-1", [], [], ["linux|qmn|t::x"]) == 1
    assert "NEW FLAKY linux|qmn|t::x" in capsys.readouterr().out


@pytest.mark.parametrize(("level", "rc"), [("deep", 0), ("release", 1)])
def test_a_listed_flaky_test_blocks_only_a_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, level: str, rc: int
) -> None:
    _flaky_case(tmp_path, monkeypatch, "linux|qmn|t::x\n")
    monkeypatch.setenv("QMX_LEVEL", level)
    assert qci.tests_verdict("linux-1", [], [], ["linux|qmn|t::x"]) == rc


def test_a_rerun_that_was_skipped_is_still_red() -> None:
    first = {"qmn.tests.test_a::test_b": "failed"}
    reds, flaky = qci.split_flaky("linux", QMN, first, {"qmn.tests.test_a::test_b": "skipped"}, [])
    assert (reds, flaky) == (["linux|qmn|qmn.tests.test_a::test_b"], [])


def test_a_touched_module_must_belong_to_the_tests_own_unit() -> None:
    first = {"tests.test_clock::test_fast": "failed"}
    again = {"tests.test_clock::test_fast": "passed"}
    reds, flaky = qci.split_flaky("linux", QMN, first, again, ["qmb/tests/test_clock.py"])
    assert (reds, flaky) == ([], ["linux|qmn|tests.test_clock::test_fast"])


def test_a_whole_suite_level_still_knows_what_the_change_touched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qci, "base_for", _returns(OTHER))
    monkeypatch.setattr(qci, "changed_files", _returns(["qmn/tests/test_x.py"]))
    assert qci.flaky_scope(qci.Level.DEEP, HEAD, []) == ["qmn/tests/test_x.py"]
    assert qci.flaky_scope(qci.Level.SLICE, HEAD, ["a.py"]) == ["a.py"]


def test_pull_reds_counts_no_skipped_matrix_job_as_a_shard() -> None:
    jobs: list[dict[str, object]] = [
        {"name": "suite-linux 1", "conclusion": "success"},
        {"name": "suite-windows 2", "conclusion": "cancelled"},
        {"name": "tests-linux ${{ matrix.shard }}", "conclusion": "skipped"},
        {"name": "tests-windows ${{ matrix.shard }}", "conclusion": "skipped"},
        {"name": "lint", "conclusion": "success"},
    ]
    assert pull_reds.shard_jobs(jobs) == ["suite-linux-1", "suite-windows-2"]


def test_pull_reds_records_the_runs_flaky_tests(tmp_path: Path) -> None:
    (tmp_path / "flaky-linux-1.txt").write_text("linux|qmn|t::b\nlinux|qmn|t::a\n", "utf-8")
    flaky = pull_reds.shard_flaky(tmp_path)
    text = pull_reds.flaky_text("77", flaky)
    rows = [line for line in text.splitlines() if line and not line.startswith("#")]
    assert rows == ["linux|qmn|t::a", "linux|qmn|t::b"]


# ---- the summary --------------------------------------------------------------------------------


def _summary(
    artifacts: Path,
    needs: dict[str, dict[str, object]],
    api: list[dict[str, object]],
    lvl: qci.Level = qci.Level.DEEP,
) -> dict[str, object]:
    return qci.build_summary(
        sha=HEAD,
        ref="r",
        run_id="1",
        url="u",
        lvl=lvl,
        jobs_of_level=list(needs),
        needs=needs,
        api_jobs=api,
        artifacts=artifacts,
        known_reds=["linux|qmn|t::old"],
        known_flaky=["linux|qmn|t::calm"],
    )


def test_a_cancelled_job_makes_the_run_red() -> None:
    needs: dict[str, dict[str, object]] = {
        "lint": {"result": "success"},
        "suite-linux": {"result": "cancelled"},
    }
    assert _summary(Path("missing"), needs, [])["green"] is False


def test_a_shard_that_never_finished_is_a_blocking_red(tmp_path: Path) -> None:
    shard = tmp_path / "ci-out-suite-linux-2"
    shard.mkdir()
    (shard / "plan-linux-2.json").write_text(json.dumps({"files": ["qmn::t.py"]}), "utf-8")
    done = tmp_path / "ci-out-suite-linux-1"
    done.mkdir()
    (done / "plan-linux-1.json").write_text(json.dumps({"files": ["qmn::u.py"]}), "utf-8")
    (done / "reds-linux-1.txt").write_text("linux|qmn|t::old\n", "utf-8")
    (done / "flaky-linux-1.txt").write_text("linux|qmn|t::calm\n", "utf-8")
    api: list[dict[str, object]] = [
        {"name": "suite-windows 3", "conclusion": "cancelled"},
        {"name": "suite-linux 1", "conclusion": "failure"},
    ]
    needs: dict[str, dict[str, object]] = {
        "suite-linux": {"result": "failure"},
        "suite-windows": {"result": "cancelled"},
    }
    summary = _summary(tmp_path, needs, api)
    assert summary["reds"] == [
        {"id": "qmn|t::old", "system": "linux", "kind": "known", "blocks": False},
        {"id": "qmn|t::calm", "system": "linux", "kind": "flaky", "blocks": False},
        {"id": "shard linux-2", "system": "linux", "kind": "unfinished", "blocks": True},
        {"id": "shard windows-3", "system": "windows", "kind": "unfinished", "blocks": True},
    ]
    jobs = cast("list[dict[str, object]]", summary["jobs"])
    assert [j["name"] for j in jobs] == ["suite-windows-3", "suite-linux-1"]
    released = _summary(tmp_path, needs, api, qci.Level.RELEASE)
    reds = cast("list[dict[str, object]]", released["reds"])
    assert [r["blocks"] for r in reds][:2] == [True, True]


# ---- wiring the probes reach --------------------------------------------------------------------


def _lint_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    level: str,
    errors: list[ratchet.Finding],
    failed: str | None = None,
) -> None:
    monkeypatch.setenv("QMX_LEVEL", level)
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    (tmp_path / "out").mkdir()
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "pyright.txt").write_text("qmn/src/old.py|r|known\n", "utf-8")
    monkeypatch.setattr(qci, "head", lambda: HEAD)
    monkeypatch.setattr(qci, "tree_of", _returns("t1"))
    monkeypatch.setattr(qci, "base_for", _returns(OTHER))
    monkeypatch.setattr(qci, "changed_files", _returns(["qmn/src/touched.py"]))
    monkeypatch.setattr(ci_units, "poe_dirs", _returns(["."]))
    monkeypatch.setattr(qci, "sync", _returns(None))
    monkeypatch.setattr(qci, "run", _returns(0))
    monkeypatch.setattr(qci, "pyright_run", _returns((errors, failed)))


def _error(path: str) -> ratchet.Finding:
    return ratchet.Finding(path, 1, "r", "fresh")


@pytest.mark.parametrize(
    ("level", "path", "rc"),
    [
        ("slice", "qmn/src/touched.py", 1),
        ("slice", "qmn/src/untouched.py", 0),
        ("deep", "qmn/src/untouched.py", 1),
    ],
    ids=["slice-touched", "slice-untouched", "deep-untouched"],
)
def test_types_block_a_slice_in_its_files_and_a_deep_run_anywhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, level: str, path: str, rc: int
) -> None:
    _lint_case(tmp_path, monkeypatch, level, [_error(path)])
    assert qci.job_lint() == rc


def test_a_folder_pyright_could_not_check_leaves_nothing_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _lint_case(tmp_path, monkeypatch, "deep", [], failed="pyright exited 2")
    assert qci.job_lint() == 1
    record = json.loads((tmp_path / "out" / "pyright-ratchet.json").read_text("utf-8"))
    assert (record["gone"], record["complete"], record["sha"]) == ([], False, HEAD)


def test_skylos_at_deep_scans_the_diff_and_so_calls_nothing_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMX_LEVEL", "deep")
    monkeypatch.setattr(qci, "BASELINES", tmp_path / "baselines")
    monkeypatch.setattr(qci, "OUT", tmp_path / "out")
    (tmp_path / "out").mkdir()
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "skylos.txt").write_text("z.py|danger:x|n\n", "utf-8")
    monkeypatch.setattr(qci, "head", lambda: HEAD)
    monkeypatch.setattr(qci, "tree_of", _returns("t1"))
    monkeypatch.setattr(qci, "uv", lambda: "uv")
    monkeypatch.setattr(qci, "base_for", _returns(OTHER))
    monkeypatch.setattr(qci, "changed_files", _returns(["a.py"]))
    monkeypatch.setattr(qci, "skylos_scope", dict)

    def fake_run(argv: list[str], cwd: Path, **kwargs: object) -> int:
        assert "--diff-base" in argv
        (tmp_path / "out" / "skylos.json").write_text('{"danger": []}', "utf-8")
        return 0

    monkeypatch.setattr(qci, "run", fake_run)
    assert qci.job_skylos(False) == 0
    record = json.loads((tmp_path / "out" / "skylos-ratchet.json").read_text("utf-8"))
    assert record["gone"] == []


def test_prune_never_removes_a_comment_line(tmp_path: Path) -> None:
    path = tmp_path / "v.txt"
    path.write_text("# header\na|r|1\n", "utf-8")
    assert ratchet.prune(path, ["# header", "a|r|1"]) == 1
    assert path.read_text("utf-8") == "# header\n"


# ---- contracts ----------------------------------------------------------------------------------


def test_the_contract_check_runs_when_a_slice_touches_the_host_and_at_every_deep_run() -> None:
    host = ["qmx-agents/packages/qmx-control/src/qmx_control/service.py"]
    assert qci.contract_due(qci.Level.SLICE, host)
    assert qci.contract_due(qci.Level.SLICE, ["contracts/apps.json"])
    assert not qci.contract_due(qci.Level.SLICE, ["qmn/src/qmn/x.py"])
    assert qci.contract_due(qci.Level.DEEP, [])
    assert not qci.contract_due(qci.Level.BASELINE, host)


def test_a_stale_contract_is_a_lint_finding_naming_the_operation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = (
        "contracts/host-openapi.json: stale\n"
        "  added   GET /api/ops/probe (ops_probe)\n"
        "contracts/apps.json: missing\n"
        "FAIL the contract files are stale: run `python tools/contract_dump.py`\n"
    )

    def fake_run(argv: list[str], cwd: Path, **kwargs: object) -> int:
        out = kwargs["stdout_to"]
        assert isinstance(out, Path)
        out.write_text(report, "utf-8")
        assert argv[-2:] == ["tools/contract_dump.py", "--check"]
        return 1

    monkeypatch.setattr(qci, "OUT", tmp_path)
    monkeypatch.setattr(qci, "run", fake_run)
    monkeypatch.setattr(qci, "uv", lambda: "uv")
    found = qci.contract_findings()
    assert [f.text() for f in found] == [
        "contracts:0: [contract] stale: added   GET /api/ops/probe (ops_probe)",
        "contracts:0: [contract] stale: contracts/apps.json: missing",
    ]
