"""The rclone storage kinds (design 06 section 9) on rclone's `local` backend: rclone's own
question loop as cards holding only the parsed fields, a row with the remote's type and root,
Drive stopped at its sign-in card with nothing opened, R2's key kept out of the conf, a folder
with no rclone at all, and a conf whose password is gone set aside once."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import psutil
import pytest
from fastapi.testclient import TestClient
from qmx_home.rclone import UNREADABLE, Rclone
from test_connect import BEARER, app_of, connected, ended, qmx_folder, rows, world

from qmx_host.connect import KINDS, Connect

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")
SHOWN = {"Name", "Help", "Examples", "Type"}


def walk(rest: TestClient, kind: str, place: str, fields: dict[str, str]) -> list[dict[str, Any]]:
    """Answer every question card with its default until the job ends; every job seen."""
    jobs = [connected(rest, kind, place, {"fields": fields})]
    while jobs[-1]["state"] == "finished" and jobs[-1]["needs"] is not None:
        needs = jobs[-1]["needs"]
        assert needs["card"] == "question", needs
        jobs.append(connected(rest, kind, place, {"state": needs["state"], "result": ""}))
    return jobs


@needs_rclone
def test_an_rclone_local_storage_connects_through_the_loop_with_its_type_and_root(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    store = tmp_path / "store"
    store.mkdir()
    with TestClient(app_of(Connect(world(layout), KINDS))) as rest:
        jobs = walk(rest, "rclone", "lane", {"type": "local", "root": str(store)})
    row = rows(layout)["lane"]
    cards = [job["needs"] for job in jobs if job["needs"] is not None]
    assert jobs[-1]["state"] == "finished", jobs[-1]["line"]
    assert cards
    assert all(set(field) == SHOWN for card in cards for field in card["fields"])
    assert {k: row[k] for k in ("via", "can", "type", "root")} == {
        "via": "rclone",
        "can": ["keep"],
        "type": "local",
        "root": str(store),
    }
    assert row["remote"] == f"qmx_{row['id'].lower()}"
    assert list((store / "QMX-backup").rglob("*")) == []
    assert "RCLONE_ENCRYPT_V0:" in (layout.data / "rclone.conf").read_text(encoding="utf-8")


def test_a_folder_storage_connects_with_no_rclone_anywhere(tmp_path: Path) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    (tmp_path / "usb").mkdir()
    there = world(layout)
    there.rclone = Rclone(layout, keys=there.keys, which=lambda _name: None)
    with TestClient(app_of(Connect(there, KINDS))) as rest:
        job = connected(rest, "folder", "usb", {"fields": {"path": str(tmp_path / "usb")}})
    assert job["state"] == "finished", job["line"]
    assert there.rclone.record == []
    assert list(rows(layout)) == ["usb"]


def rclone_children() -> list[psutil.Process]:
    return [p for p in psutil.Process().children(recursive=True) if "authorize" in p.cmdline()]


@needs_rclone
def test_drive_asks_for_its_client_then_stops_at_its_sign_in_card_and_cancels(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    there = world(layout)
    with TestClient(app_of(Connect(there, KINDS))) as rest:
        client = connected(rest, "drive", "gdrive", {})
        signing = connected(
            rest,
            "drive",
            "gdrive",
            {
                "fields": {
                    "client_id": "lane.apps.googleusercontent.com",
                    "client_secret": "GOCSPX-lane",
                }
            },
        )
        processes = rclone_children()
        # Windows gives every console program its own conhost.exe; rclone starts nothing else.
        children = [
            [c.name() for c in p.children(recursive=True) if c.name() != "conhost.exe"]
            for p in processes
        ]
        stopped = rest.post(f"/api/connect/jobs/{signing['id']}/cancel", headers=BEARER)
        sign_in = ended(rest, signing["needs"]["job"])
    authorize = [c.args for c in there.rclone.record if "authorize" in c.args]
    assert client["needs"]["card"] == "fields"
    assert "about ten minutes" in client["needs"]["line"]
    assert '"In production"' in client["needs"]["line"]
    assert [f["Name"] for f in client["needs"]["fields"]] == ["client_id", "client_secret", "root"]
    assert signing["needs"]["card"] == "sign-in"
    assert signing["needs"]["link"].startswith("http://127.0.0.1:53682/auth?state=")
    assert authorize and "--auth-no-open-browser" in authorize[0]
    assert len(processes) == 1
    assert children == [[]]
    assert stopped.status_code == 200
    assert sign_in["state"] == "stopped"
    assert "the sign-in was stopped" in sign_in["line"]
    assert rows(layout) == {}
    assert "GOCSPX-lane" not in json.dumps([c.args for c in there.rclone.record])


@needs_rclone
def test_r2_asks_for_its_key_through_the_key_route_and_the_conf_never_holds_it(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    there = world(layout)
    with TestClient(app_of(Connect(there, KINDS))) as rest:
        asking = connected(rest, "r2", "cloud", {"fields": {"root": "lane-bucket"}})
        put = rest.put(
            "/api/keys/qmx/r2-cloud", json={"value": "planted-r2-secret"}, headers=BEARER
        )
        question = connected(rest, "r2", "cloud", {})
    dumped = there.rclone.run(["config", "dump"]).out
    assert asking["needs"] == {
        "card": "secret",
        "line": asking["needs"]["line"],
        "key": "qmx/r2-cloud",
    }
    assert put.status_code == 204
    assert question["needs"]["card"] == "question"
    assert question["needs"]["fields"][0]["Name"] == "access_key_id"
    assert '"provider": "Cloudflare"' in dumped
    assert "planted-r2-secret" not in dumped
    assert "planted-r2-secret" not in json.dumps([[*c.args, *c.env] for c in there.rclone.record])


@needs_rclone
def test_a_conf_whose_password_is_gone_is_set_aside_once_and_a_new_one_connects(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    store = tmp_path / "store"
    store.mkdir()
    with TestClient(app_of(Connect(world(layout), KINDS))) as rest:
        walk(rest, "rclone", "lane", {"type": "local", "root": str(store)})
    emptied = Connect(world(layout), KINDS)
    doctor = emptied.doctor_line()
    again = emptied.doctor_line()
    with TestClient(app_of(emptied)) as rest:
        jobs = walk(rest, "rclone", "lane2", {"type": "local", "root": str(tmp_path)})
    assert (doctor.ok, again.ok) == (False, False)
    assert "connect each rclone storage again" in doctor.detail
    assert len(list(layout.data.glob(UNREADABLE + "*"))) == 1
    assert jobs[-1]["state"] == "finished", jobs[-1]["line"]
    assert "RCLONE_ENCRYPT_V0:" in (layout.data / "rclone.conf").read_text(encoding="utf-8")


def test_a_question_card_never_shows_a_password_default(tmp_path: Path) -> None:
    from qmx_host.connect import Run
    from qmx_host.connect_storage import _question  # pyright: ignore[reportPrivateUsage]

    run = Run(KINDS["rclone"], "lane", {}, world(qmx_folder(tmp_path / "QMX")))
    card = _question(
        run,
        "*all-set,2,false",
        {
            "Name": "password",
            "Help": "Password or pass phrase for encryption.",
            "Default": "do-not-show",
            "DefaultStr": "do-not-show",
            "IsPassword": True,
            "Type": "string",
        },
        "",
    )
    assert card.name == "secret"
    assert card.key == "qmx/connect/lane/password"
    assert "do-not-show" not in json.dumps(card.document())
    assert time.monotonic() > 0
