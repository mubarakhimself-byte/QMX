"""The engine host refuses a home whose record names a live host, before it touches anything."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psutil
import pytest

from qmx_engine.host import STATE, main, recorded_host


def record(home: Path, pid: int, created: float) -> None:
    (home / STATE).write_text(
        json.dumps({"pid": pid, "port": 8766, "created": created}), encoding="utf-8"
    )


def test_a_live_recorded_host_is_refused_by_pid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    me = psutil.Process()
    record(tmp_path, me.pid, me.create_time())

    code = main(["serve", "--home", str(tmp_path), "--port", "0"])

    assert code == 1
    assert f"already has a live host, PID {os.getpid()}" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == [STATE]


def test_a_record_whose_process_is_gone_names_no_host(tmp_path: Path) -> None:
    me = psutil.Process()
    record(tmp_path, me.pid, me.create_time() - 1000)

    assert recorded_host(tmp_path) is None
