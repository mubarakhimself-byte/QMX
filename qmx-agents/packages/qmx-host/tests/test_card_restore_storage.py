"""Restore from my storage on the first-start card, and keep a new folder's work in another storage
too (design 06 sections 8 and 10). Every folder, storage and profile is in pytest's tmp folder;
storages are folders or rclone's `local` backend, keys go to an in-memory store, and no host,
browser, Credential Manager or pg0 is started."""

from __future__ import annotations

import json
import shutil
import tomllib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_home import Layout, resolve
from qmx_home.backup.plan import parse
from qmx_home.backup.round import run_round
from qmx_home.rclone import Rclone
from test_card_restore import ended, folder, home_id, notes
from test_connect import Store

from qmx_host import first_start
from qmx_host.first_start import Connected, first_start_router, offer, restore_into, settled

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")
COPY_AT = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
PLANTED = "sk-sy5plantedvalue0123456789abcdef"


def profile(at: Path, monkeypatch: pytest.MonkeyPatch) -> first_start.Places:
    """A scratch Windows profile at `at`: the pointer file and the card's lock land there."""
    for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (at / part).mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(name, str(at / part))
    monkeypatch.setenv("USERPROFILE", str(at))
    monkeypatch.setenv("HOME", str(at))
    monkeypatch.delenv("QMX_HOME", raising=False)
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    monkeypatch.setattr(first_start, "_fixed_drives", list)
    return first_start.Places({"APPDATA": str(at / "Roaming")})


@pytest.fixture
def card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, Store]]:
    keys = Store()
    places = profile(tmp_path / "second-profile", monkeypatch)
    app = FastAPI()
    app.include_router(
        first_start_router(places, tmp_path / "old", drives=[], port=8799, key_store=keys)
    )
    with TestClient(app) as client:
        yield client, keys


def job(client: TestClient, route: str, body: dict[str, object]) -> dict[str, Any]:
    asked = client.post(route, json=body)
    assert asked.status_code == 202, asked.text
    return ended(client, asked.json()["id"])


def connected_on_card(client: TestClient, route: str, body: dict[str, Any]) -> dict[str, Any]:
    """A storage kind run on the card until it ends, each rclone question answered with its
    default."""
    found = job(client, route, body)
    while found["state"] == "finished" and found["needs"] is not None:
        asked = {"state": found["needs"]["state"], "result": ""}
        found = job(client, route, {**body, "answer": asked})
    assert found["state"] == "finished", found["line"]
    return found


def rclone_children() -> list[psutil.Process]:
    return [p for p in psutil.Process().children(recursive=True) if p.name() != "conhost.exe"]


def test_the_card_offers_restore_from_my_storage_and_a_new_folder_the_keep_your_work_card(
    card: tuple[TestClient, Store], tmp_path: Path
) -> None:
    client, _ = card
    shown = client.get("/api/first-start").json()
    made = client.post("/api/first-start/new", json={"folder": str(tmp_path / "QMX")}).json()

    assert shown["choices"] == ["new", "open", "restore-storage", "restore"]
    assert made["kept"]["line"] == "Your work is kept on this PC"
    assert made["kept"]["card"] == "Keep your work in another storage too"
    assert made["kept"]["optional"] is True
    assert {kind["id"] for kind in made["kept"]["kinds"]} == {
        "folder",
        "drive",
        "r2",
        "rclone",
    }
    assert all(kind["can"] == ["keep"] for kind in made["kept"]["kinds"])
    words = str(client.get("/api/first-start").json()).lower()
    assert not any(word in words for word in ("deep logs", "openobserve", "server", "gpu"))


def test_the_keep_your_work_card_connects_a_folder_storage_and_makes_its_first_copy(
    card: tuple[TestClient, Store], tmp_path: Path
) -> None:
    client, _ = card
    root = tmp_path / "QMX"
    client.post("/api/first-start/new", json={"folder": str(root)})
    (Layout(root).data / "notes.txt").write_text("a note", encoding="utf-8")
    usb = tmp_path / "usb"
    usb.mkdir()
    body = {"folder": str(root), "kind": "folder", "place": "usb", "answer": {}}
    asked = {"fields": {"path": str(usb)}}

    first = job(client, "/api/first-start/keep", body)
    done = job(client, "/api/first-start/keep", {**body, "answer": asked})

    rows = tomllib.loads((root / "data" / "settings.toml").read_text(encoding="utf-8"))
    assert first["needs"]["card"] == "folder"
    assert done["state"] == "finished", done["line"]
    assert rows["engine"]["placement"]["usb"]["path"] == str(usb)
    assert len(list(usb.rglob("manifest.jsonl"))) == 1


@needs_rclone
def test_a_drive_restore_with_no_shipped_client_stops_at_the_client_card_naming_the_console(
    card: tuple[TestClient, Store], tmp_path: Path
) -> None:
    client, _ = card
    root = tmp_path / "QMX"
    body = {"folder": str(root), "kind": "drive", "place": "gdrive", "answer": {}}

    found = job(client, "/api/first-start/connect", body)

    assert found["state"] == "finished"
    assert found["needs"]["card"] == "fields"
    assert [f["Name"] for f in found["needs"]["fields"]] == ["client_id", "client_secret", "root"]
    assert "https://console.cloud.google.com/apis/credentials" in found["needs"]["line"]
    assert "same Google Cloud client" in found["needs"]["line"]
    assert rclone_children() == []
    assert not (root / "data" / "settings.toml").exists()


def test_a_fresh_card_offers_again_a_failed_restore_into_any_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    places = profile(tmp_path / "profile", monkeypatch)
    elsewhere = tmp_path / "Elsewhere" / "QMX"
    restore_into(elsewhere, places, make=True)

    again = offer(tmp_path / "old", places, drives=[])

    assert again.restoring is not None
    assert again.restoring["folder"] == str(elsewhere.absolute().resolve())
    assert again.choices[0] == "restore"


def test_the_storage_restored_from_takes_the_copys_row_id_and_this_machines_keys_come_back(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    (layout.data / "settings.toml").write_text(
        '[telemetry]\nsend_to = "this-pc"\n\n[engine]\n"disk.floor_gb" = 50\n\n'
        '[engine.placement.cloud]\nid = "OLDCLOUD"\nvia = "rclone"\ncan = ["keep"]\n'
        'remote = "qmx_oldcloud"\ntype = "local"\nroot = "E:/store"\n\n'
        '[engine.placement.other]\nid = "OTHER"\nvia = "rclone"\ncan = ["keep"]\n'
        'remote = "qmx_other"\ntype = "s3"\nroot = "bucket"\n\n'
        '[backup.place.OLDCLOUD]\nevery = "1w"\n',
        encoding="utf-8",
    )
    aside = tmp_path / "aside"
    (aside / "data").mkdir(parents=True)
    (aside / "data" / "settings.toml").write_text(
        '[telemetry]\nsend_to = "off"\n', encoding="utf-8"
    )
    storage = Connected(
        "lane",
        {
            "via": "rclone",
            "can": ["keep"],
            "remote": "qmx_new",
            "type": "local",
            "root": "E:/store",
        },
    )

    ident = settled(layout, aside, storage)

    settings = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    rows = settings["engine"]["placement"]
    assert ident == "OLDCLOUD"
    assert rows["cloud"] == {
        "id": "OLDCLOUD",
        "via": "rclone",
        "can": ["keep"],
        "remote": "qmx_new",
        "type": "local",
        "root": "E:/store",
    }
    assert rows["other"]["remote"] == "qmx_other"
    assert settings["backup"]["place"]["OLDCLOUD"] == {"every": "1w"}
    assert settings["telemetry"] == {"send_to": "off"}
    assert "disk.floor_gb" not in settings["engine"]


@needs_rclone
def test_a_second_pc_restores_from_an_rclone_storage_on_the_card_and_syncs_there_again(
    card: tuple[TestClient, Store], tmp_path: Path
) -> None:
    client, keys = card
    first, storage = folder(tmp_path / "first" / "QMX"), tmp_path / "storage"
    storage.mkdir()
    first_keys = Store()
    made = Rclone(first, keys=first_keys).run(
        ["config", "create", "qmx_firstcloud", "local", "--non-interactive"]
    )
    assert made.code == 0, made.line
    (first.data / "settings.toml").write_text(
        '[engine.placement.cloud]\nid = "CLOUD1"\nvia = "rclone"\ncan = ["keep"]\n'
        f'remote = "qmx_firstcloud"\ntype = "local"\nroot = {json.dumps(str(storage))}\n\n'
        f'[providers.kimi]\napi_key = "{PLANTED}"\n',
        encoding="utf-8",
    )
    settings = tomllib.loads((first.data / "settings.toml").read_text(encoding="utf-8"))
    plan = parse({}, first, settings["engine"])
    sent = run_round(first, plan, now=COPY_AT, floor=0, rclone=Rclone(first, keys=first_keys))
    assert [p.result for p in sent.places] == ["copied", "copied"], sent.lines
    root = tmp_path / "second" / "QMX"

    shown = client.get("/api/first-start").json()
    joined = connected_on_card(
        client,
        "/api/first-start/connect",
        {
            "folder": str(root),
            "kind": "rclone",
            "place": "lane",
            "answer": {"fields": {"type": "local", "root": str(storage)}},
        },
    )
    source = joined["result"]["source"]
    listed = client.post("/api/first-start/copies", json={"source": source}).json()
    stamp = listed["copies"][0]["stamp"]
    checked = client.post(
        "/api/first-start/restore/check",
        json={"source": source, "folder": str(root), "copy": stamp},
    ).json()
    done = job(
        client,
        "/api/first-start/restore",
        {"source": source, "folder": str(root), "copy": stamp, "confirmed": True},
    )
    handed = client.post("/api/first-start/handover").json()

    layout = Layout(root)
    restored = tomllib.loads((layout.data / "settings.toml").read_text(encoding="utf-8"))
    row = restored["engine"]["placement"]["cloud"]
    conf = (layout.data / "rclone.conf").read_text(encoding="utf-8")
    again = run_round(
        layout,
        parse({}, layout, restored["engine"]),
        now=datetime.now(UTC),
        floor=0,
        rclone=Rclone(layout, keys=keys),
    )
    assert "restore-storage" in shown["choices"]
    assert listed["copies"][0]["machine"] and listed["copies"][0]["files"] > 0
    assert checked["new"] is True
    assert done["state"] == "finished", done["line"]
    assert handed["folder"] == str(layout.root)
    assert notes(layout) == notes(first)
    assert home_id(layout.root) == home_id(first.root)
    assert (row["id"], row["remote"]) == ("CLOUD1", source["remote"])
    assert "RCLONE_ENCRYPT_V0:" in conf
    assert PLANTED not in (layout.data / "settings.toml").read_text(encoding="utf-8")
    sync = next(p for p in again.places if p.id == "CLOUD1")
    assert sync.result in ("copied", "unchanged"), sync.line
