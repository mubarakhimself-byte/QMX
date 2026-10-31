"""SY2's one fact: no secret reaches a command line, and the remote still works. A `crypt`
remote over a local folder (a test vehicle only; the dialog never offers it) is connected
through rclone's question loop with rclone behind a shim that records every command line, its
password answered through the key route with a planted value; then a file is copied through the
remote and listed back."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from test_connect import BEARER, app_of, connected, qmx_folder, rows, world

from qmx_host.connect import KINDS, Connect

REAL = shutil.which("rclone")
PLANTED = "planted-crypt-Pass-4410"


@pytest.mark.skipif(REAL is None, reason="rclone is not on PATH")
def test_a_crypt_remote_connects_and_works_with_its_password_in_no_command_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert REAL is not None
    log = tmp_path / "shim.jsonl"
    shim = tmp_path / "rclone.cmd"
    script = Path(__file__).with_name("rclone_shim.py")
    shim.write_text(f'@"{sys.executable}" -I "{script}" %*\n', encoding="utf-8")
    monkeypatch.setenv("QMX_SHIM_LOG", str(log))
    monkeypatch.setenv("QMX_SHIM_REAL", REAL)
    layout = qmx_folder(tmp_path / "QMX")
    base = tmp_path / "base"
    base.mkdir()
    there = world(layout)
    there.rclone.path = str(shim)
    seen: list[dict[str, Any]] = []
    with TestClient(app_of(Connect(there, KINDS))) as rest:
        job = connected(
            rest, "rclone", "vault", {"fields": {"type": "crypt", "root": "QMX-backup"}}
        )
        seen.append(job)
        while job["state"] == "finished" and job["needs"] is not None:
            needs = job["needs"]
            name = needs["fields"][0]["Name"]
            if needs["card"] == "secret" and name == "password":
                put = rest.put(f"/api/keys/{needs['key']}", json={"value": PLANTED}, headers=BEARER)
                assert put.status_code == 204
                answer: dict[str, object] = {"state": needs["state"], "key": needs["key"]}
            elif name == "remote":
                answer = {"state": needs["state"], "result": str(base)}
            else:
                answer = {"state": needs["state"], "result": ""}
            job = connected(rest, "rclone", "vault", answer)
            seen.append(job)
    remote = rows(layout)["vault"]["remote"]
    sent = tmp_path / "hello.txt"
    sent.write_text("kept through the remote", encoding="utf-8")
    copied = there.rclone.run(["copyto", str(sent), f"{remote}:QMX-backup/hello.txt"])
    listed = there.rclone.run(["lsf", f"{remote}:QMX-backup"])
    dumped = there.rclone.run(["config", "dump"]).out
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert job["state"] == "finished", job["line"]
    assert copied.code == 0
    assert listed.out.split() == ["hello.txt"]
    assert len(lines) == len(there.rclone.record)
    assert any("--non-interactive" in line for line in lines)
    assert all(PLANTED not in arg for line in lines for arg in line)
    assert PLANTED not in json.dumps(seen)
    assert PLANTED not in log.read_text(encoding="utf-8")
    assert PLANTED not in dumped
    assert PLANTED not in (layout.data / "rclone.conf").read_text(encoding="utf-8")
    assert list(base.iterdir())
