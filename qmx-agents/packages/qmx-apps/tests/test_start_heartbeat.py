"""A start reads the bootstrap's heartbeat file while the bootstrap replaces it every quarter
second, so one read can miss. A miss is no refusal while the start's own deadline runs."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from qmx_apps.supervisor import Instance, Supervisor

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"


def test_a_start_survives_two_missed_heartbeat_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "fixture"
    shutil.copytree(EXAMPLE, app, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), app / "server.py")
    shipped = Supervisor._heartbeat  # noqa: SLF001
    missed: list[str] = []

    def reads(self: Supervisor, instance: Instance) -> None:
        if len(missed) < 2:
            missed.append(instance.id)
            return
        shipped(self, instance)

    monkeypatch.setattr(Supervisor, "_heartbeat", reads)
    owner = Supervisor(tmp_path / "home", secret_getter=lambda service, username: "declared-fixture")
    try:
        owner.install(app, trust="first_party")
        owner.start("exchange-status")
        assert owner.status("exchange-status")["status"] == "running"
    finally:
        owner.close()
    assert len(missed) == 2
