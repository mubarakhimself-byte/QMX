"""The QMB host door delegates process ownership to qmx-control."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner
from qmb.doors.cli import host, main
from qmf.core.refusal import is_refusal


@pytest.mark.parametrize("command", ["start", "status", "stop"])
def test_host_delegates_to_control(
    command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        assert kwargs["timeout"] == 180
        return subprocess.CompletedProcess(argv, 0, "control result", "")

    monkeypatch.setattr(host.subprocess, "run", run)
    result = CliRunner().invoke(
        main, ["host", command, "--home", str(tmp_path), "--python", "control-python"]
    )
    assert result.exit_code == 0, result.output
    assert calls == [
        ["control-python", "-m", "qmx_control", command, "--port", "8766", "--home", str(tmp_path)]
    ]
    assert json.loads(result.output)["message"] == "control result"


@pytest.mark.parametrize("command", ["pair", "configure", "rotate-control", "recover-control"])
def test_removed_protocol_commands_are_absent(command: str) -> None:
    result = CliRunner().invoke(main, ["host", command])
    assert result.exit_code == 2
    assert "No such command" in result.output


def test_failed_control_is_a_typed_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "recorded host is unreachable")

    monkeypatch.setattr(host.subprocess, "run", run)
    result = host.control_host("status", python="control-python")
    assert is_refusal(result)


def test_invalid_port_cannot_spawn() -> None:
    assert is_refusal(host.control_host("start", port=0))
