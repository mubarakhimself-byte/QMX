"""Negative controls for complete, successful nightly mutation evidence."""

from pathlib import Path

import mutation_gate
import pytest


def test_partial_run_cannot_pass_from_classified_progress(tmp_path: Path) -> None:
    results = tmp_path / "results.txt"
    results.write_text(
        "qmf.core.exact.x_value__mutmut_1: killed\nqmf.core.exact.x_value__mutmut_2: not checked\n",
        encoding="utf-8",
    )
    run_status = tmp_path / "run.status"
    run_status.write_text("0\n", encoding="utf-8")
    results_status = tmp_path / "results.status"
    results_status.write_text("0\n", encoding="utf-8")
    assert (
        mutation_gate.main(
            [
                "--results",
                str(results),
                "--run-status",
                str(run_status),
                "--results-status",
                str(results_status),
                "--module",
                "qmf.core.exact",
                "--min-kill-rate",
                "68",
            ]
        )
        == 2
    )


def invoke(
    tmp_path: Path,
    listing: str,
    *,
    run_status: str = "0",
    results_status: str = "0",
    floor: int = 68,
) -> int:
    results = tmp_path / "results.txt"
    results.write_text(listing, encoding="utf-8")
    run = tmp_path / "run.status"
    run.write_text(run_status, encoding="utf-8")
    collection = tmp_path / "results.status"
    collection.write_text(results_status, encoding="utf-8")
    return mutation_gate.main(
        [
            "--results",
            str(results),
            "--run-status",
            str(run),
            "--results-status",
            str(collection),
            "--module",
            "qmf.core.exact",
            "--min-kill-rate",
            str(floor),
        ]
    )


def test_complete_run_preserves_floor_and_node_survivor_policy(tmp_path: Path) -> None:
    listing = (
        "qmf.core.exact.x_value__mutmut_1: killed\nqmf.core.exact.x_value__mutmut_2: survived\n"
    )
    assert invoke(tmp_path, listing) == 1
    assert invoke(tmp_path, listing, floor=0) == 0
    assert invoke(tmp_path, listing, floor=50) == 0
    assert invoke(tmp_path, listing, floor=51) == 1


@pytest.mark.parametrize("status", ["1", "2", "130", "", "unknown"])
@pytest.mark.parametrize("command", ["run_status", "results_status"])
def test_failed_command_refuses_even_with_all_kills(
    tmp_path: Path, status: str, command: str
) -> None:
    statuses = {"run_status": "0", "results_status": "0"}
    statuses[command] = status
    assert (
        invoke(
            tmp_path,
            "qmf.core.exact.x_value__mutmut_1: killed",
            run_status=statuses["run_status"],
            results_status=statuses["results_status"],
        )
        == 2
    )


@pytest.mark.parametrize(
    "status",
    [
        "not checked",
        "no tests",
        "timeout",
        "suspicious",
        "skipped",
        "segfault",
        "check was interrupted by user",
        "unknown",
    ],
)
def test_unclassified_results_never_reduce_kill_rate_denominator(
    tmp_path: Path, status: str
) -> None:
    assert (
        invoke(
            tmp_path,
            "qmf.core.exact.x_value__mutmut_1: killed\n"
            f"qmf.core.exact.x_value__mutmut_2: {status}\n",
        )
        == 2
    )


@pytest.mark.parametrize(
    "listing",
    [
        "",
        "\n",
        "Traceback: failed",
        "qmf.core.chrono.x_value__mutmut_1: killed",
        "qmf.core.exact.x_value__mutmut_1: killed\nqmf.core.exact.x_value__mutmut_1: killed\n",
    ],
)
def test_absent_malformed_duplicate_or_wrong_scope_evidence_refuses(
    tmp_path: Path, listing: str
) -> None:
    assert invoke(tmp_path, listing) == 2


def test_missing_evidence_refuses(tmp_path: Path) -> None:
    assert (
        mutation_gate.main(
            [
                "--results",
                str(tmp_path / "missing"),
                "--run-status",
                str(tmp_path / "missing"),
                "--results-status",
                str(tmp_path / "missing"),
                "--module",
                "qmf.core.exact",
            ]
        )
        == 2
    )
