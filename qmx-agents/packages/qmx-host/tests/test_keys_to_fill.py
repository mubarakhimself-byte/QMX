"""Keys to fill in after a restore, and a restore from Settings out of an rclone storage (design 06
section 8, plan review SHOULD 6). Keys never travel: the list holds names and `settings.toml` paths
only, shrinks as he writes them, and the fill route writes a listed path back at its place and
refuses any other. Every folder is in pytest's tmp folder; keys go to an in-memory store."""

from __future__ import annotations

import json
import shutil
import tomllib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.models import Document
from qmx_home import Layout
from qmx_home.backup import restore
from qmx_home.backup.plan import parse
from qmx_home.backup.round import run_round
from qmx_home.rclone import Rclone
from test_backups_restore import clock_now
from test_backups_service import Clock, connect, ended, finished, folder, service, target
from test_connect import Store

from qmx_host.backups import Backups, backups_router
from qmx_host.first_start import keep_fill_record

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")
PLANTED = "sk-sy5plantedvalue0123456789abcdef"
SETTINGS = """\
[providers.kimi]
model = "kimi-k2"

[[connections]]
name = "lane"

[engine.placement.r2]
id = "R2ID"
via = "rclone"
can = ["keep"]
remote = "qmx_r2id"
type = "s3"
root = "bucket"
credential_ref = "qmx/r2-r2"
"""


def test_keys_to_fill_list_names_only_shrink_as_written_and_refuse_an_unlisted_path(
    tmp_path: Path,
) -> None:
    layout = folder(tmp_path / "QMX")
    (layout.data / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    keep_fill_record(layout, "20261027T030000000000Z", ["providers.kimi.api_key"])
    backups, keys = service(layout, Clock()), Store()
    backups.keys = keys
    app = FastAPI()
    app.include_router(backups_router(backups))
    client = TestClient(app)

    listed = client.get("/api/backups/keys-to-fill").json()
    keys.replace("qmx/r2-r2", "an R2 key")
    refused = client.put(
        "/api/backups/keys-to-fill", json={"path": "engine.placement.r2.remote", "value": "x"}
    )
    filled = client.put(
        "/api/backups/keys-to-fill", json={"path": "providers.kimi.api_key", "value": PLANTED}
    )
    after = client.get("/api/backups/keys-to-fill")

    written = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    assert listed == {
        "copy": "20261027T030000000000Z",
        "keys": ["qmx/r2-r2"],
        "settings": ["providers.kimi.api_key"],
    }
    assert refused.status_code == 409
    assert "engine.placement.r2.remote" in refused.json()["detail"]
    assert filled.status_code == 204
    assert after.json() == {"copy": "20261027T030000000000Z", "keys": [], "settings": []}
    assert PLANTED not in after.text
    assert written["providers"]["kimi"] == {"model": "kimi-k2", "api_key": PLANTED}
    assert written["engine"]["placement"]["r2"]["remote"] == "qmx_r2id"
    assert written["connections"] == [{"name": "lane"}]


def test_an_array_entry_the_copy_left_out_goes_back_at_its_index(tmp_path: Path) -> None:
    layout = folder(tmp_path / "QMX")
    (layout.data / "settings.toml").write_text(
        '[[providers]]\nname = "one"\n\n[[providers]]\nname = "two"\n', encoding="utf-8"
    )
    keep_fill_record(layout, "20261027T030000000000Z", ["providers[1].api_key"])
    backups = service(layout, Clock())
    backups.keys = Store()

    backups.fill("providers[1].api_key", PLANTED)

    written = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    assert written["providers"] == [{"name": "one"}, {"name": "two", "api_key": PLANTED}]


def test_an_array_index_past_the_list_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    layout = folder(tmp_path / "QMX")
    text = '[[providers]]\nname = "one"\n\n[[providers]]\nname = "two"\n'
    (layout.data / "settings.toml").write_text(text, encoding="utf-8")
    keep_fill_record(layout, "20261027T030000000000Z", ["providers[5].api_key"])
    backups = service(layout, Clock())
    backups.keys = Store()
    app = FastAPI()
    app.include_router(backups_router(backups))

    refused = TestClient(app).put(
        "/api/backups/keys-to-fill", json={"path": "providers[5].api_key", "value": PLANTED}
    )

    assert (refused.status_code, refused.json()["detail"]) == (
        409,
        "'providers[5].api_key' names entry 5 of a list that holds 2; nothing was written.",
    )
    assert (layout.data / "settings.toml").read_text(encoding="utf-8") == text
    assert backups.keys_to_fill()["settings"] == ["providers[5].api_key"]


def staged_restore(tmp_path: Path) -> tuple[Layout, Backups, Clock]:
    """A folder whose copy at `usb` left out `providers.kimi.api_key` and holds telemetry
    `this-pc`, then this machine's telemetry `off` and that copy's restore staged."""
    layout, clock = folder(tmp_path / "QMX"), clock_now()
    (layout.data / "settings.toml").write_text(
        '[telemetry]\nsend_to = "this-pc"\n\n'
        f'[providers.kimi]\nmodel = "kimi-k2"\napi_key = "{PLANTED}"\n',
        encoding="utf-8",
    )
    backups = service(layout, clock)
    backups.keys = Store()
    connect(backups, target(tmp_path / "usb"))
    assert finished(backups, backups.start("usb", asked=True).job).state == "finished"
    (stamp,) = [c["stamp"] for c in backups.copies("usb")]
    backups.control.settings_update("providers", lambda _c: {"kimi": {"model": "kimi-k2"}})
    backups.control.settings_put("telemetry", {"send_to": "off"})
    staged = ended(
        backups, backups.stage_restore({"target": "usb", "copy": stamp, "confirmed": True}).id
    )
    assert staged.state == "finished", staged.line
    return layout, backups, clock


def test_a_key_filled_while_a_restore_is_staged_is_refused_and_after_the_finish_it_lands(
    tmp_path: Path,
) -> None:
    layout, backups, clock = staged_restore(tmp_path)
    app = FastAPI()
    app.include_router(backups_router(backups))
    body = {"path": "providers.kimi.api_key", "value": PLANTED}

    listed = TestClient(app).get("/api/backups/keys-to-fill").json()
    early = TestClient(app).put("/api/backups/keys-to-fill", json=body)
    finished_restore = restore.finish(layout)
    restarted = service(layout, clock)
    restarted.keys = Store()
    again = FastAPI()
    again.include_router(backups_router(restarted))
    later = TestClient(again).put("/api/backups/keys-to-fill", json=body)
    restarted.carry_on_restore()
    after = TestClient(again).get("/api/backups/keys-to-fill").json()

    assert finished_restore is not None
    aside = (layout.root / finished_restore.aside / "data" / "settings.toml").read_text("utf-8")
    settled = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    assert listed["settings"] == ["providers.kimi.api_key"]
    assert (early.status_code, early.json()["detail"]) == (
        409,
        "a restore is staged: restart QMX to finish it, then fill 'providers.kimi.api_key'; a "
        "key written now would be set aside with the work the restore replaces",
    )
    assert PLANTED not in aside
    assert later.status_code == 204
    assert settled["providers"]["kimi"] == {"model": "kimi-k2", "api_key": PLANTED}
    assert after["settings"] == []


def test_carry_on_settles_each_section_from_what_it_holds_when_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, _backups, clock = staged_restore(tmp_path)
    assert restore.finish(layout) is not None
    restarted = service(layout, clock)
    restarted.keys = Store()
    control = restarted.control
    update = control.settings_update
    merged: list[str] = []

    def merge_lands_first(section: Any, change: Callable[[Document], Document]) -> Document:
        if section == "telemetry" and not merged:
            merged.append(section)
            control.settings_put("telemetry", {"openobserve": {"keep_days": 90}})
        return update(section, change)

    monkeypatch.setattr(control, "settings_update", merge_lands_first)
    restarted.carry_on_restore()

    settled = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    assert merged == ["telemetry"]
    assert settled["telemetry"] == {"send_to": "off", "openobserve": {"keep_days": 90}}


@needs_rclone
def test_a_restore_from_settings_reads_an_rclone_storage_and_carry_on_gives_this_pc_its_keys(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    storage = tmp_path / "storage"
    storage.mkdir()
    keys = Store()
    made = Rclone(layout, keys=keys).run(
        ["config", "create", "qmx_cloud1", "local", "--non-interactive"]
    )
    assert made.code == 0, made.line
    rows = (
        '[engine.placement.cloud]\nid = "CLOUD1"\nvia = "rclone"\ncan = ["keep"]\n'
        f'remote = "qmx_cloud1"\ntype = "local"\nroot = {json.dumps(str(storage))}\n'
    )
    (layout.data / "settings.toml").write_text(
        f'[telemetry]\nsend_to = "this-pc"\n\n{rows}\n[providers.kimi]\napi_key = "{PLANTED}"\n',
        encoding="utf-8",
    )
    settings = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    sent = run_round(
        layout,
        parse({}, layout, settings["engine"]),
        now=datetime(2026, 10, 27, 3, 0, tzinfo=UTC),
        floor=0,
        rclone=Rclone(layout, keys=keys),
    )
    stamp = next(p.stamp for p in sent.places if p.id == "CLOUD1")
    assert stamp is not None, sent.lines
    (layout.data / "settings.toml").write_text(
        f'[telemetry]\nsend_to = "off"\n\n{rows}', encoding="utf-8"
    )
    backups = service(layout, clock)
    backups.keys = keys

    staged = ended(
        backups,
        backups.stage_restore({"target": "CLOUD1", "copy": stamp, "confirmed": True}).id,
    )
    listed_before = backups.keys_to_fill()
    finished = restore.finish(layout)
    held = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    restarted = service(layout, clock)
    restarted.keys = keys
    restarted.carry_on_restore()

    settled = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    assert staged.state == "finished", staged.line
    assert finished is not None
    assert listed_before["settings"] == ["providers.kimi.api_key"]
    assert held["telemetry"] == {"send_to": "this-pc"}
    assert settled["telemetry"] == {"send_to": "off"}
    assert settled["engine"]["placement"]["cloud"]["id"] == "CLOUD1"
    assert "api_key" not in settled.get("providers", {}).get("kimi", {})
