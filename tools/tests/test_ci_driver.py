"""The CI driver's planning: which tests a change selects, how shards split, which findings are new
against a baseline, which functions mutmut mutates, how JUnit outcomes are read, which run facts it
takes from GitHub Actions or a laptop, and when the pull-request gate and a release pass."""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

import ci_host
import ci_mutate
import ci_units
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
        "jobs": [{"name": "suite-linux 1", "result": "failure", "seconds": 512}],
        "reds": [
            {"id": "qmn|t::new", "system": "linux", "kind": "new"},
            {"id": "qmn|t::old", "system": "linux", "kind": "known"},
            {"id": "qmn|t::flaky", "system": "linux", "kind": "flaky"},
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
    assert "| suite-linux 1 | failure | 512 |" in text


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


def test_the_guard_fails_on_an_added_baseline_row(tmp_path: Path) -> None:
    root, base = _repo(tmp_path)
    at = _commit(root, "v.txt", "# header changed\na|r|1\nb|r|2\nc|r|3\n")
    assert qci.baseline_growth(base, at, root) == ["ci/baselines/v.txt: c|r|3"]


def test_the_guard_passes_on_a_removed_row_and_on_a_new_baseline_file(tmp_path: Path) -> None:
    root, base = _repo(tmp_path)
    _commit(root, "v.txt", "# header\nb|r|2\n")
    at = _commit(root, "pyright.txt", "# new tool\nx|r|1\n")
    assert qci.baseline_growth(base, at, root) == []


def test_no_baseline_file_gains_a_row_outside_a_baseline_branch() -> None:
    """The ratchet only tightens: outside a baseline/** branch, no change since engine/base adds a
    row to a ci/baselines file (`qci.py ratchet --prune` only ever removes rows)."""
    branch = os.environ.get("QMX_REF") or qci.git("branch", "--show-current").strip()
    if branch.startswith("baseline/"):
        pytest.skip(f"{branch} retakes baselines")
    engine = f"refs/remotes/origin/{qci.ENGINE}"
    if not qci.git_ok("rev-parse", "--verify", "--quiet", engine):
        pytest.skip(f"{engine} is not fetched in this checkout")
    base = qci.merge_base("HEAD", engine)
    assert base is not None
    assert qci.baseline_growth(base, "HEAD") == []


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
    (tmp_path / "baselines").mkdir()
    (tmp_path / "baselines" / "vulture.txt").write_text(
        "# header\nz.py|v|1\na.py|v|gone\nm.py|v|2\n", "utf-8"
    )
    out = tmp_path / "out" / "ci-out-vulture"
    out.mkdir(parents=True)
    (out / "vulture-ratchet.json").write_text(
        json.dumps({"tool": "vulture", "new": [], "gone": ["a.py|v|gone"]}), "utf-8"
    )
    assert qci.ratchet_prune(["vulture"], tmp_path / "out") == 0
    assert (tmp_path / "baselines" / "vulture.txt").read_text("utf-8") == (
        "# header\nz.py|v|1\nm.py|v|2\n"
    )
    assert "PRUNED vulture 1" in capsys.readouterr().out


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
