"""One send job per storage (design 06 section 5): a slow storage never holds This PC's copies,
a second send to one storage is refused while the first runs, This PC off with no storage says
his work has no copy anywhere, and a storage connected through the dialog gets its first copy."""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from qmx_control.server import create_app
from qmx_home.backup.repository import FolderRepository
from test_backups_service import Clock, connect, ended, finished, folder, results, service, target
from test_connect import TOKEN, Store, rows
from test_connect_storage import walk

from qmx_host.backups import NO_COPY_LINE, Refusal
from qmx_host.connect import Connect
from qmx_host.host import dialog_routers, storage_dialog

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")


def test_a_slow_send_holds_neither_this_pcs_copies_nor_a_second_send_to_that_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    connect(backups, target(tmp_path / "usb"))
    go = threading.Event()
    real = FolderRepository._step  # pyright: ignore[reportPrivateUsage]

    def slow(self: FolderRepository, op: str) -> None:
        if "usb" in str(self.root) and op == "manifest":
            go.wait(30)
        real(self, op)

    monkeypatch.setattr(FolderRepository, "_step", slow)
    first = ended(backups, backups.start(None, asked=True).job.id)
    sends = cast("dict[str, str]", cast("dict[str, Any]", first.result)["sends"])
    with pytest.raises(Refusal, match=r"QMX is already sending a copy to .*usb"):
        backups.start("usb", asked=True)
    clock.advance(minutes=61)
    started = time.monotonic()
    pc = ended(backups, backups.start(None, asked=False).job.id)
    took = time.monotonic() - started
    sending = backups.jobs.get(sends["usb"])
    go.set()
    sent = ended(backups, sends["usb"])

    assert results(first) == {"quick": "copied"}
    assert (pc.state, pc.result is not None and "sends" in pc.result) == ("finished", True)
    assert results(pc)["quick"] in ("copied", "unchanged")
    assert took < 10
    assert sending is not None and sending.state == "running"
    assert cast("dict[str, Any]", sent.result)["places"][0]["result"] == "copied"


def test_with_this_pcs_copies_off_and_no_storage_the_doctor_says_his_work_has_no_copy(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    backups.control.settings_put("backup", {"place": {"pc": {"on": False}}})

    row = backups.doctor_line()
    swept = backups.sweep()

    assert row.ok is False
    assert row.detail.startswith(NO_COPY_LINE)
    assert swept is None


@needs_rclone
def test_a_storage_connected_through_the_dialog_gets_its_first_copy_as_its_own_send(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    keys = Store()
    backups = service(layout, clock)
    backups.keys = keys
    store = tmp_path / "store"
    store.mkdir()
    dialog: Connect = storage_dialog(layout, backups.control, backups, keys=keys)
    app = create_app(backups.control, TOKEN, extra_routers=dialog_routers(dialog, backups.control))
    with TestClient(app) as rest:
        jobs = walk(rest, "rclone", "lane", {"type": "local", "root": str(store)})
    row = rows(layout)["lane"]
    sent = None
    for _ in range(600):
        sent = backups.jobs.latest(f"send:{row['id']}")
        if sent is not None and sent.state != "running":
            break
        time.sleep(0.05)
    round_job = backups.jobs.latest("backup")

    assert jobs[-1]["state"] == "finished", jobs[-1]["line"]
    assert round_job is not None and finished(backups, round_job).state == "finished"
    assert sent is not None and sent.state == "finished", sent and sent.line
    assert cast("dict[str, Any]", sent.result)["places"][0]["result"] == "copied"
    assert list(store.rglob("manifest.jsonl"))
