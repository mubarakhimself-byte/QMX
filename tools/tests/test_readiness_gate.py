"""The CI checkpoint cannot be green with a missing or unsuccessful deep job.

qmx-ci's deep-verdict job writes the verdict the pull-request gate reads. GitHub runs a job whose
`if` names no status function only when every job it needs succeeded, so a failed, cancelled or
skipped deep job leaves no verdict and the gate refuses the pull request.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/qmx-ci.yml"
DEEP_JOBS = {
    "lint",
    "vulture",
    "skylos",
    "suite-linux",
    "suite-windows",
    "mutmut",
    "docker-node",
    "qmn-lane",
}
STATUS_FUNCTIONS = ("always()", "success()", "failure()", "cancelled()")


def _document() -> dict[object, object]:
    return cast("dict[object, object]", yaml.safe_load(WORKFLOW.read_text(encoding="utf-8")))


def _jobs() -> dict[str, dict[str, object]]:
    return cast("dict[str, dict[str, object]]", _document()["jobs"])


def test_the_verdict_needs_every_deep_job_and_each_of_them_runs_at_deep() -> None:
    jobs = _jobs()
    assert set(cast("list[str]", jobs["deep-verdict"]["needs"])) == {"level", *DEEP_JOBS}
    running_at_deep = {
        name
        for name, job in jobs.items()
        if name != "deep-verdict" and '"deep"' in str(job.get("if", ""))
    }
    assert running_at_deep == DEEP_JOBS


def test_the_verdict_is_written_only_when_every_needed_job_succeeded() -> None:
    condition = str(_jobs()["deep-verdict"]["if"])
    assert condition == "needs.level.outputs.level == 'deep'"
    assert not any(function in condition for function in STATUS_FUNCTIONS)


def test_the_gate_runs_on_pull_requests_into_engine_base_and_reads_the_verdict() -> None:
    # YAML 1.1 reads the bare key `on` as True.
    triggers = cast("dict[str, dict[str, list[str]]]", _document()[True])
    assert triggers["pull_request"]["branches"] == ["engine/base"]
    jobs = _jobs()
    gate_steps = cast("list[dict[str, str]]", jobs["gate"]["steps"])
    assert [s["run"] for s in gate_steps if "run" in s] == ["python tools/ci/qci.py gate"]
    verdict_steps = cast("list[dict[str, dict[str, str]]]", jobs["deep-verdict"]["steps"])
    uploads = [s["with"]["name"] for s in verdict_steps if "name" in s.get("with", {})]
    assert uploads == ["deep-verdict"]
