"""Executable tests for the coverage-floor enforcer (M1; AR-20).

Pins both floors the enforcer adds on top of the aggregate ``--cov-fail-under=80``:
the per-package 80% floor (so one package cannot hide behind another's fully-covered
scaffold) and the 100%-branch contract-module rule for ``qmf/core/exact.py`` and
``qmf/core/chrono.py``. Also exercises the fail-closed file-loading entry point and
asserts the enforcer passes on the workspace's real ``coverage.json`` when present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import coverage_report as cov
import pytest

FileEntry = dict[str, dict[str, int]]
Report = dict[str, dict[str, FileEntry]]
SUMMARY_COUNTERS = ("covered_lines", "num_statements", "covered_branches", "num_branches")


def _file(
    covered_lines: int, num_statements: int, covered_branches: int, num_branches: int
) -> FileEntry:
    return {
        "summary": {
            "covered_lines": covered_lines,
            "num_statements": num_statements,
            "covered_branches": covered_branches,
            "num_branches": num_branches,
        }
    }


def _report(files: dict[str, FileEntry]) -> Report:
    return {"files": files}


def _clean_report() -> Report:
    return _report(
        {
            "packages/qmf-core/src/qmf/core/refusal.py": _file(90, 100, 40, 40),
            "packages/qmf-core/src/qmf/core/exact.py": _file(10, 10, 8, 8),
            "packages/qmf-core/src/qmf/core/chrono.py": _file(10, 10, 8, 8),
            "packages/qmf-data/src/qmf/data/__init__.py": _file(5, 5, 0, 0),
            "extensions/qmf-calendar-forex/src/qmf/calendar_forex/_bench.py": _file(20, 20, 2, 2),
        }
    )


# --- a clean report passes --------------------------------------------------


def test_clean_report_has_no_violations() -> None:
    assert cov.evaluate(_clean_report()) == []


# --- per-package floor ------------------------------------------------------


def test_package_below_floor_is_flagged() -> None:
    report = _clean_report()
    # Drop qmf-data well under 80% combined line+branch.
    report["files"]["packages/qmf-data/src/qmf/data/big.py"] = _file(10, 100, 0, 0)
    violations = cov.evaluate(report)
    assert any("qmf-data" in v and "per-package floor" in v for v in violations)


def test_package_floor_uses_combined_line_and_branch() -> None:
    # 80/100 lines but 0/100 branches => 80/200 = 40% combined, below the floor.
    report = _report({"packages/qmf-venue/src/qmf/venue/m.py": _file(80, 100, 0, 100)})
    violations = cov.evaluate(report)
    assert any("qmf-venue" in v for v in violations)


def test_package_exactly_at_floor_passes() -> None:
    report = _report({"packages/qmf-risk/src/qmf/risk/m.py": _file(80, 100, 0, 0)})
    # exact.py/chrono.py absent -> those violations appear, but no qmf-risk floor breach.
    violations = cov.evaluate(report)
    assert not any("qmf-risk" in v for v in violations)


def test_application_root_qml_is_its_own_package() -> None:
    report = _report(
        {
            "qml/src/qml/__init__.py": _file(7, 10, 0, 0),
            "packages/qmf-core/src/qmf/core/exact.py": _file(10, 10, 8, 8),
            "packages/qmf-core/src/qmf/core/chrono.py": _file(10, 10, 8, 8),
        }
    )
    violations = cov.evaluate(report)
    assert any("qml" in v and "per-package floor" in v for v in violations)


def test_application_root_qmb_is_its_own_package() -> None:
    report = _report(
        {
            "qmb/src/qmb/__init__.py": _file(7, 10, 0, 0),
            "packages/qmf-core/src/qmf/core/exact.py": _file(10, 10, 8, 8),
            "packages/qmf-core/src/qmf/core/chrono.py": _file(10, 10, 8, 8),
        }
    )
    violations = cov.evaluate(report)
    assert any("qmb" in v and "per-package floor" in v for v in violations)


def test_application_root_qmn_is_its_own_package() -> None:
    report = _report(
        {
            "qmn/src/qmn/__init__.py": _file(7, 10, 0, 0),
            "packages/qmf-core/src/qmf/core/exact.py": _file(10, 10, 8, 8),
            "packages/qmf-core/src/qmf/core/chrono.py": _file(10, 10, 8, 8),
        }
    )
    violations = cov.evaluate(report)
    assert any("qmn" in v and "per-package floor" in v for v in violations)


# --- contract-module full-branch rule ---------------------------------------


def test_exact_with_uncovered_branch_is_flagged() -> None:
    report = _clean_report()
    report["files"]["packages/qmf-core/src/qmf/core/exact.py"] = _file(10, 10, 6, 8)
    violations = cov.evaluate(report)
    assert any("qmf/core/exact.py" in v and "branches covered" in v for v in violations)


def test_chrono_with_uncovered_branch_is_flagged() -> None:
    report = _clean_report()
    report["files"]["packages/qmf-core/src/qmf/core/chrono.py"] = _file(10, 10, 7, 8)
    violations = cov.evaluate(report)
    assert any("qmf/core/chrono.py" in v for v in violations)


def test_missing_contract_module_fails_closed() -> None:
    # A report that never measured chrono.py must fail rather than pass by omission.
    report = _report({"packages/qmf-core/src/qmf/core/exact.py": _file(10, 10, 8, 8)})
    violations = cov.evaluate(report)
    assert any("qmf/core/chrono.py" in v and "not measured" in v for v in violations)


def test_windows_backslash_paths_are_matched() -> None:
    report = _report(
        {
            "packages\\qmf-core\\src\\qmf\\core\\exact.py": _file(10, 10, 8, 8),
            "packages\\qmf-core\\src\\qmf\\core\\chrono.py": _file(10, 10, 4, 8),
        }
    )
    violations = cov.evaluate(report)
    assert any("qmf/core/chrono.py" in v for v in violations)
    assert not any("exact.py" in v for v in violations)


# --- the file-loading entry point -------------------------------------------


def test_main_passes_on_clean_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(_clean_report()), encoding="utf-8")
    assert cov.main(report_path, expected_packages=()) == 0
    assert "clean" in capsys.readouterr().out


def test_main_fails_on_breached_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = _clean_report()
    report["files"]["packages/qmf-core/src/qmf/core/exact.py"] = _file(10, 10, 1, 8)
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    assert cov.main(report_path, expected_packages=()) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "exact.py" in out


def test_main_fails_closed_when_report_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cov.main(tmp_path / "nope.json") == 1
    assert "no coverage report" in capsys.readouterr().out


def test_main_fails_closed_on_a_non_regular_report_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A directory where the report should be is "no report" as truly as a missing file.
    directory = tmp_path / "coverage.json"
    directory.mkdir()
    assert cov.main(directory) == 1
    assert "no coverage report" in capsys.readouterr().out


def test_main_fails_closed_on_malformed_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_path = tmp_path / "coverage.json"
    report_path.write_text("{not json", encoding="utf-8")
    assert cov.main(report_path, expected_packages=()) == 1
    assert "FAIL" in capsys.readouterr().out


@pytest.mark.parametrize("report", [None, [], 7, "text", {}, {"files": []}, {"files": {}}])
def test_invalid_document_shapes_fail_closed(report: object) -> None:
    assert cov.evaluate(report)


@pytest.mark.parametrize("path", ["", 42])
def test_invalid_file_paths_fail_closed(path: object) -> None:
    report: Any = _clean_report()
    report["files"][path] = _file(10, 10, 8, 8)
    assert any("file paths" in violation for violation in cov.evaluate(report))


@pytest.mark.parametrize("field", SUMMARY_COUNTERS)
@pytest.mark.parametrize("value", [None, True, False, -1, 1.5, "8", [], {}])
def test_invalid_summary_counters_fail_closed(field: str, value: object) -> None:
    report: Any = _clean_report()
    path = "packages/qmf-core/src/qmf/core/exact.py"
    report["files"][path]["summary"][field] = value
    assert any(field in violation for violation in cov.evaluate(report))


@pytest.mark.parametrize("field", SUMMARY_COUNTERS)
def test_missing_summary_counters_fail_closed(field: str) -> None:
    report = _clean_report()
    del report["files"]["packages/qmf-core/src/qmf/core/exact.py"]["summary"][field]
    assert any(field in violation for violation in cov.evaluate(report))


@pytest.mark.parametrize("info", [None, [], {}, {"summary": []}, {"summary": None}])
def test_invalid_file_summaries_fail_closed(info: object) -> None:
    report: Any = _clean_report()
    report["files"]["packages/qmf-data/src/qmf/data/bad.py"] = info
    assert any("bad.py" in violation for violation in cov.evaluate(report))


@pytest.mark.parametrize(
    "covered,total", [("covered_lines", "num_statements"), ("covered_branches", "num_branches")]
)
def test_covered_counter_cannot_exceed_total(covered: str, total: str) -> None:
    report = _clean_report()
    summary = report["files"]["packages/qmf-core/src/qmf/core/exact.py"]["summary"]
    summary[covered] = summary[total] + 1
    assert any("exceeds" in violation for violation in cov.evaluate(report))


def test_empty_package_does_not_pass_as_one_hundred_percent() -> None:
    report = _clean_report()
    report["files"]["packages/qmf-data/src/qmf/data/__init__.py"] = _file(0, 0, 0, 0)
    assert any("qmf-data: no measurable" in violation for violation in cov.evaluate(report))


def test_empty_file_in_nonempty_package_is_valid() -> None:
    report = _clean_report()
    report["files"]["packages/qmf-core/src/qmf/core/__init__.py"] = _file(0, 0, 0, 0)
    assert cov.evaluate(report) == []


@pytest.mark.parametrize("suffix", cov.FULL_BRANCH_MODULES)
def test_zero_contract_branches_are_not_evidence_of_full_coverage(suffix: str) -> None:
    report = _clean_report()
    report["files"][f"packages/qmf-core/src/{suffix}"] = _file(10, 10, 0, 0)
    assert any("no measured branches" in violation for violation in cov.evaluate(report))


@pytest.mark.parametrize(
    "path",
    [
        "packages/qmf-data/tests/test_data.py",
        "packages/qmf-data/examples/demo.py",
        "packages/qmf-data/build.py",
        "notpackages/qmf-data/src/padding.py",
        "packages/qmf-data/src/../tests/test_data.py",
        "tests/packages/qmf-data/src/padding.py",
    ],
)
def test_non_source_cannot_inflate_package_coverage(path: str) -> None:
    report = _clean_report()
    report["files"]["packages/qmf-data/src/qmf/data/__init__.py"] = _file(1, 10, 0, 0)
    report["files"][path] = _file(1000, 1000, 1000, 1000)
    assert any(
        "qmf-data" in violation and "per-package floor" in violation
        for violation in cov.evaluate(report)
    )


@pytest.mark.parametrize(
    "path",
    [
        "tests/qmf/core/exact.py",
        "packages/qmf-core/tests/qmf/core/exact.py",
        "packages/qmf-data/src/qmf/core/exact.py",
        "packages/qmf-core/src/notqmf/core/exact.py",
    ],
)
def test_contract_suffix_spoof_cannot_replace_actual_module(path: str) -> None:
    report = _clean_report()
    del report["files"]["packages/qmf-core/src/qmf/core/exact.py"]
    report["files"][path] = _file(10, 10, 8, 8)
    assert any(
        "exact.py" in violation and "not measured" in violation
        for violation in cov.evaluate(report)
    )


@pytest.mark.parametrize("prefix,separator", [("/home/runner/QMX/", "/"), ("C:/work/QMX/", "\\")])
def test_absolute_paths_remain_portable(prefix: str, separator: str) -> None:
    report = _clean_report()
    report["files"] = {
        (prefix + path).replace("/", separator): info for path, info in report["files"].items()
    }
    assert cov.evaluate(report) == []


def test_duplicate_path_alias_cannot_overwrite_uncovered_contract() -> None:
    report = _clean_report()
    path = "packages/qmf-core/src/qmf/core/exact.py"
    report["files"][path] = _file(10, 10, 1, 8)
    report["files"]["/work/QMX/" + path] = _file(10, 10, 8, 8)
    assert any("duplicate source path" in violation for violation in cov.evaluate(report))


def test_expected_inventory_detects_entirely_omitted_package() -> None:
    violations = cov.evaluate(_clean_report(), {"qmf-core", "qmf-data", "qmf-risk"})
    assert any("qmf-risk: package was not measured" in violation for violation in violations)


def test_workspace_inventory_is_derived_from_manifests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for path in ("packages/qmf-core", "extensions/qmf-custom", "qml"):
        directory = tmp_path / path
        directory.mkdir(parents=True)
        (directory / "pyproject.toml").write_text(
            f'[project]\nname = "{directory.name}"\n', encoding="utf-8"
        )
    monkeypatch.setattr(cov, "ROOT", tmp_path)
    assert cov.workspace_packages() == {"qmf-core", "qmf-custom", "qml"}


def test_empty_workspace_inventory_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cov, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="inventory is empty"):
        cov.workspace_packages()


def test_path_dot_alias_cannot_pad_package() -> None:
    report = _clean_report()
    report["files"]["packages/qmf-core/src/./qmf/core/exact.py"] = _file(10, 10, 8, 8)
    assert any("duplicate source path" in violation for violation in cov.evaluate(report))


def test_main_uses_workspace_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cov, "workspace_packages", lambda: {"qmf-risk"})
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(_clean_report()), encoding="utf-8")
    assert cov.main(report_path) == 1
    assert "qmf-risk: package was not measured" in capsys.readouterr().out


def test_main_fails_closed_when_inventory_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken_inventory() -> set[str]:
        raise ValueError("broken manifest")

    monkeypatch.setattr(cov, "workspace_packages", broken_inventory)
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(_clean_report()), encoding="utf-8")
    assert cov.main(report_path) == 1
    assert "could not read workspace inventory" in capsys.readouterr().out


@pytest.mark.parametrize("document", ["null", "[]", "true", "123", '{"files": []}'])
def test_main_fails_cleanly_on_valid_json_with_wrong_shape(
    document: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_path = tmp_path / "coverage.json"
    report_path.write_text(document, encoding="utf-8")
    assert cov.main(report_path, expected_packages=()) == 1
    assert "FAIL" in capsys.readouterr().out


@pytest.mark.parametrize("path", ["qmn/deploy/switch.py", "C:\\work\\QMX\\qmn\\deploy\\switch.py"])
def test_operational_deployment_code_counts_toward_qmn_floor(path: str) -> None:
    report = _clean_report()
    report["files"]["qmn/src/qmn/__init__.py"] = _file(100, 100, 0, 0)
    report["files"][path] = _file(0, 100, 0, 0)
    assert any("qmn" in v and "per-package floor" in v for v in cov.evaluate(report))


def test_operational_deployment_and_runtime_share_one_floor() -> None:
    report = _clean_report()
    report["files"]["qmn/src/qmn/__init__.py"] = _file(100, 100, 0, 0)
    report["files"]["qmn/deploy/switch.py"] = _file(60, 100, 0, 0)
    assert cov.evaluate(report) == []


@pytest.mark.parametrize(
    "path",
    [
        "qmn/deploy/tests/test_switch.py",
        "qmn/deploy/examples/sample.py",
        "qmn/examples/padding.py",
        "notqmn/deploy/switch.py",
        "qmn/deployment/switch.py",
        "qmn/deploy/../tests/test_switch.py",
    ],
)
def test_nonoperational_paths_cannot_pad_qmn_coverage(path: str) -> None:
    report = _clean_report()
    report["files"]["qmn/src/qmn/__init__.py"] = _file(10, 100, 0, 0)
    report["files"][path] = _file(1000, 1000, 1000, 1000)
    assert any("qmn" in v and "per-package floor" in v for v in cov.evaluate(report))


def test_omitted_source_fails_even_when_package_is_present() -> None:
    report = _clean_report()
    assert any(
        "worker.py: source file was not measured" in item
        for item in cov.evaluate(report, (), {"qmb/src/qmb/orchestrator/worker.py"})
    )


def test_untracked_source_cannot_pad_tracked_inventory() -> None:
    report = _clean_report()
    sources = set(report["files"])
    report["files"]["qmb/src/fake.py"] = _file(9999, 9999, 9999, 9999)
    assert any(
        "outside the tracked inventory" in item for item in cov.evaluate(report, (), sources)
    )


@pytest.mark.parametrize("prefix", ["/unrelated/", "C:/unrelated/", "other-checkout/"])
def test_unrelated_checkout_is_not_candidate(tmp_path: Path, prefix: str) -> None:
    report = _clean_report()
    sources = set(report["files"])
    report["files"] = {prefix + path: info for path, info in report["files"].items()}
    assert any(
        "outside the candidate" in item for item in cov.evaluate(report, (), sources, tmp_path)
    )


@pytest.mark.parametrize("absolute", [False, True])
def test_current_candidate_paths_remain_valid(tmp_path: Path, absolute: bool) -> None:
    report = _clean_report()
    sources = set(report["files"])
    prefix = tmp_path.as_posix() + "/" if absolute else "./"
    report["files"] = {prefix + path: info for path, info in report["files"].items()}
    assert cov.evaluate(report, (), sources, tmp_path) == []
