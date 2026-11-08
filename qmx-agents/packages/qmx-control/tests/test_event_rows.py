"""A running app that nothing is asking writes few rows, and the rows that are only noise leave at
the next start while his chats stay."""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path
from typing import cast

import pytest
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor

from qmx_control.models import Document
from qmx_control.service import ControlService, SessionBlock, SessionInput

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
FIXTURE = Path(__file__).resolve().parents[2] / "qmx-apps/tests/fixture_server.py"
APP = "exchange-status"


def this_interpreter(_self: Supervisor, _definition_hash: str) -> Path:
    return Path(sys.executable)


def no_build(_self: Supervisor, _definition: Definition, _image: Path) -> None:
    pass


def test_a_quiet_app_writes_few_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Supervisor, "python", this_interpreter)
    monkeypatch.setattr(Supervisor, "_install_environment", no_build)
    folder = tmp_path / "app"
    shutil.copytree(EXAMPLE, folder, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(FIXTURE, folder / "server.py")
    control = ControlService(tmp_path / "QMX" / "data", secret_getter=lambda _s, _u: "fixture")
    try:
        runtime = control.app_runtime()
        runtime.install(folder, trust="first_party")
        started = runtime.start(APP)
        apps = len(control.events("apps", limit=1000))
        totals = len(control.events("aggregates", limit=1000))
        time.sleep(10)
        status = runtime.status(APP)
        apps_after = len(control.events("apps", limit=1000))
        totals_after = len(control.events("aggregates", limit=1000))
    finally:
        control.close()

    assert status["pid"] == started["pid"]
    assert status["status"] == "running"
    assert apps_after - apps <= 2
    assert totals_after - totals <= 2


def test_old_app_rows_leave_at_the_next_start_and_his_chats_stay(tmp_path: Path) -> None:
    home = tmp_path / "QMX" / "data"
    control = ControlService(home)
    session_id = str(control.sessions_create(SessionInput(title="his chat"))["id"])
    control.sessions_append(session_id, SessionBlock(type="text", content={"text": "hello"}))
    control.notify_app(APP, {"status": "stopped"})
    control.close()

    kept = ControlService(home)
    apps_kept = [cast(Document, event["data"])["status"] for event in kept.events("apps")]
    kept.close()

    (home / "settings.toml").write_text("[apps]\nevents_keep_days = 0\n", encoding="utf-8")
    pruned = ControlService(home)
    chats = [cast(Document, event["data"])["type"] for event in pruned.events("sessions")]
    apps = pruned.events("apps")
    totals = pruned.events("aggregates")
    pruned.close()

    assert apps_kept == ["stopped"]
    assert chats == ["created", "block"]
    assert apps == []
    assert totals == []
