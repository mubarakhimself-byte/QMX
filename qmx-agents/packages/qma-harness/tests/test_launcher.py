from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import Launch, wait_for

from qma.launcher import BLOCK_CONFIG_CHANGE, EXIT_REFUSED, main, process_started


def test_block_flag_exits_2_with_the_reason_on_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"source": "user_settings"}'))
    assert main([BLOCK_CONFIG_CHANGE]) == 2
    assert "user_settings change is blocked" in capsys.readouterr().err


def test_the_version_probe_path_loads_no_chat_path_modules() -> None:
    probe = (
        "import sys, qma.launcher; print(sorted({'ctypes', 'json', 'pathlib'} & set(sys.modules)))"
    )
    done = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)
    assert done.stdout.strip() == "[]"


def test_inputs_are_stripped_and_the_exit_code_passes_through(
    launch: Launch, tmp_path: Path, procs_dir: Path
) -> None:
    chat = launch("chat-a", code=7)
    _, err = chat.communicate(timeout=60)
    assert chat.returncode == 7, err
    seen = json.loads((tmp_path / "chat-a.seen.json").read_text())
    assert seen["qma"] == []
    assert set(seen["record"]) == {"launcher_pid", "cli_pid", "cli_started"}
    assert seen["record"]["cli_pid"] != seen["record"]["launcher_pid"]
    assert not (procs_dir / "chat-a.json").exists()


def test_no_input_mode_runs_the_cli_without_a_pid_file(
    launch: Launch, tmp_path: Path, procs_dir: Path
) -> None:
    chat = launch("chat-b", code=3, QMA_CHAT_ID="", QMA_PROC_DIR="")
    _, err = chat.communicate(timeout=60)
    assert chat.returncode == 3, err
    assert json.loads((tmp_path / "chat-b.seen.json").read_text())["record"] is None
    assert not procs_dir.exists()


def test_a_chat_id_without_a_pid_directory_is_refused(launch: Launch) -> None:
    chat = launch("chat-c", QMA_PROC_DIR="")
    _, err = chat.communicate(timeout=60)
    assert chat.returncode == EXIT_REFUSED
    assert "must both be set" in err


@pytest.mark.skipif(sys.platform != "win32", reason="the per-chat job name is Windows only")
def test_a_second_launcher_for_a_live_chat_is_refused(launch: Launch, procs_dir: Path) -> None:
    first = launch("chat-d")
    try:
        assert wait_for((procs_dir / "chat-d.json").exists)
        second = launch("chat-d")
        _, err = second.communicate(timeout=60)
        assert second.returncode == EXIT_REFUSED
        assert "already has a live CLI" in err
    finally:
        first.communicate("", timeout=60)
    assert first.returncode == 0


@pytest.mark.skipif(sys.platform != "win32", reason="the parent job is Windows only")
def test_a_cli_that_cannot_join_the_cap_is_killed_before_it_runs(
    launch: Launch, tmp_path: Path, procs_dir: Path
) -> None:
    chat = launch("chat-e", cap="Local\\qma-agents-no-such-job")
    _, err = chat.communicate(timeout=60)
    assert chat.returncode == EXIT_REFUSED, err
    pid = re.search(r"CLI pid (\d+) not started", err)
    assert pid is not None, err
    assert process_started(int(pid.group(1))) is None
    assert not (tmp_path / "chat-e.seen.json").exists()
    assert list(procs_dir.glob("*")) == []
