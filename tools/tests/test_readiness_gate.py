"""The established CI check cannot pass with a missing or unsuccessful native suite."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "readiness_gate.py"
MANDATORY = ("backend", "agent-suites", "vulture")


def run_gate(raw: str, required: tuple[str, ...] = MANDATORY) -> int:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *required],
        env=dict(os.environ, NEEDS_JSON=raw),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    ).returncode


def test_both_native_matrices_and_dead_code_scan_must_complete() -> None:
    payload = {name: {"result": "success"} for name in MANDATORY}
    assert run_gate(json.dumps(payload)) == 0
    assert run_gate(json.dumps({"agent-suites": {"result": "success"}}), ("agent-suites",)) == 0


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


@pytest.mark.parametrize("raw", ["", "not-json", "[]", "null", '{"backend": true}'])
def test_unreadable_or_malformed_results_are_never_green(raw: str) -> None:
    assert run_gate(raw) == 1
