"""``qmb host`` hands process ownership to ``python -m qmx_host``."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner
from qmb.doors.cli import host, main
from qmf.core.refusal import is_refusal

REPO = Path(__file__).resolve().parents[2]


def _record(monkeypatch: pytest.MonkeyPatch, *, code: int = 0, err: str = "") -> list[list[str]]:
    calls: list[list[str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        assert kwargs["timeout"] == 180
        return subprocess.CompletedProcess(argv, code, "host said", err)

    monkeypatch.setattr(host.subprocess, "run", run)
    return calls


@pytest.mark.parametrize("command", ["start", "status", "stop"])
def test_host_commands_run_qmx_host(
    command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record(monkeypatch)
    result = CliRunner().invoke(
        main, ["host", command, "--home", str(tmp_path), "--python", "host-python"]
    )
    assert result.exit_code == 0, result.output
    assert calls == [
        ["host-python", "-m", "qmx_host", command, "--port", "8766", "--home", str(tmp_path)]
    ]
    assert json.loads(result.output) == {"verb": f"host.{command}", "message": "host said"}


def test_checkout_runs_the_qmx_host_workspace_package(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _record(monkeypatch)
    def which(name: str) -> str:
        return f"/bin/{name}"

    monkeypatch.setattr(shutil, "which", which)
    result = CliRunner().invoke(main, ["host", "start", "--port", "9001"])
    assert result.exit_code == 0, result.output
    assert calls == [
        [
            "/bin/uv",
            "run",
            "--project",
            str(REPO / "qmx-agents/packages/qmx-host"),
            "--package",
            "qmx-host",
            "--frozen",
            "python",
            "-m",
            "qmx_host",
            "start",
            "--port",
            "9001",
        ]
    ]


@pytest.mark.parametrize("command", ["pair", "configure", "rotate-control", "recover-control"])
def test_removed_daemon_commands_are_absent(command: str) -> None:
    result = CliRunner().invoke(main, ["host", command])
    assert result.exit_code == 2
    assert "No such command" in result.output


def test_failed_host_command_is_a_refusal_naming_the_host_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _record(monkeypatch, code=1, err="Port 8766 is already occupied.")
    result = host.control_host("start", python="host-python")
    assert is_refusal(result)
    assert "Port 8766 is already occupied." in str(result)


def test_invalid_port_cannot_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _record(monkeypatch)
    assert is_refusal(host.control_host("start", port=0))
    assert calls == []
