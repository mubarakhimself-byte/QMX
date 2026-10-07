"""The established CI check cannot pass with a missing or unsuccessful native suite."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/battery.yml"
MANDATORY = ("backend",)


def run_gate(raw: str, required: tuple[str, ...] = MANDATORY) -> int:
    job = "agents" if required == ("agent-suites",) else "check"
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    definition = document["jobs"][job]
    event = "==" if job == "agents" else "!="
    assert definition["if"] == f"${{{{ always() && github.event_name {event} 'schedule' }}}}"
    assert definition["needs"] == list(required)
    assert len(definition["steps"]) == 1
    step = definition["steps"][0]
    assert step["if"] == "${{ always() }}"
    assert step["env"]["NEEDS_JSON"] == "${{ toJSON(needs) }}"
    assert step["env"]["REQUIRED_JOBS"].split() == list(required)
    # Execute the actual workflow Python body using this host's interpreter.
    prefix, body = step["run"].split("python3 - <<'PY'\n", 1)
    assert prefix == ""
    code, suffix = body.rsplit("\nPY", 1)
    assert not suffix.strip()
    return subprocess.run(
        [sys.executable, "-B", "-c", code],
        env=dict(os.environ, NEEDS_JSON=raw, REQUIRED_JOBS=" ".join(required)),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    ).returncode


def test_native_pr_matrix_and_nightly_agent_matrix_must_complete() -> None:
    payload = {name: {"result": "success"} for name in MANDATORY}
    assert run_gate(json.dumps(payload)) == 0
    assert run_gate(json.dumps({"agent-suites": {"result": "success"}}), ("agent-suites",)) == 0


def test_nested_test_environment_uses_frozen_workspace_without_retired_extra() -> None:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = document["jobs"]["agent-suites"]["steps"]
    sync = next(step for step in steps if step.get("id") == "sync")
    command = shlex.split(sync["run"])
    assert command[:2] == ["uv", "sync"]
    assert "--frozen" in command and "--all-packages" in command
    assert "--extra" not in command
    for step in steps:
        run = shlex.split(step.get("run", ""))
        if run[:2] == ["uv", "run"]:
            assert "--no-sync" in run, step["name"]


@pytest.mark.parametrize("job", MANDATORY)
@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", "unknown"])
def test_unsuccessful_prerequisite_is_never_green(job: str, result: str) -> None:
    payload = {name: {"result": "success"} for name in MANDATORY}
    payload[job]["result"] = result
    assert run_gate(json.dumps(payload)) == 1


@pytest.mark.parametrize("job", MANDATORY)
def test_missing_native_suite_or_scan_is_never_green(job: str) -> None:
    payload = {name: {"result": "success"} for name in MANDATORY if name != job}
    assert run_gate(json.dumps(payload)) == 1


@pytest.mark.parametrize(
    "raw", ["", "not-json", "[]", "null", '{"backend": true}', '{"extra": {"result": "success"}}']
)
def test_unreadable_or_malformed_results_are_never_green(raw: str) -> None:
    assert run_gate(raw) == 1
