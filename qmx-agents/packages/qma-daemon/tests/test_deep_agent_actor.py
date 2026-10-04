"""Host selects one specialist in the existing daemon; no extra agent loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import test_actor_workflow as actor_contract
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.deep_agent import DeepAgentSelection


def select(monkeypatch: pytest.MonkeyPatch, profile: str) -> None:
    original = DaemonProcess.configure_agent_requests

    def configure(self: Any, **kwargs: Any) -> Any:
        return original(self, **kwargs, deep_agent=DeepAgentSelection(profile, "analyst:1"))

    monkeypatch.setattr(DaemonProcess, "configure_agent_requests", configure)


def test_one_selected_specialist_two_jobs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    select(monkeypatch, "global")
    actor_contract.test_two_specialists_two_jobs_actor_memory_and_thread_isolation(
        tmp_path, monkeypatch
    )


def test_selected_specialist_disk_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    select(monkeypatch, "global")
    actor_contract.test_disk_restart_explicit_resume_does_not_repeat_completed_child(
        tmp_path, monkeypatch
    )


def test_selected_specialist_grant_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    select(monkeypatch, "app-reader")
    actor_contract.test_narrow_parameter_grant_denies_child_callback(tmp_path, monkeypatch)


def test_selected_specialist_receipts_disk_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    select(monkeypatch, "app-reader")
    actor_contract.test_actual_paired_socket_two_child_tool_effects_are_distinct_and_restart_does_not_replay(
        tmp_path, monkeypatch
    )


def test_deterministic_operation_uses_no_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A deterministic-only graph has no specialist to select. Its owner operation
    # continues directly through the existing admission and receipt path.
    actor_contract.test_deterministic_only_job_executes_domain_read_without_model(
        tmp_path, monkeypatch
    )
