"""The connect dialog's routes and step runner, with the folder storage (design 06 section 9):
one row written last, a rerun that skips what is done, a kill after any step that converges,
and the name and target refusals."""

from __future__ import annotations

import dataclasses
import secrets
import time
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.server import create_app
from qmx_control.service import ControlService
from qmx_home import Layout, resolve
from qmx_home.rclone import Rclone
from test_backups_service import Clock, service

from qmx_host.connect import KINDS, Connect, World, run_kind
from qmx_host.host import dialog_routers, storage_dialog
from qmx_host.jobs import Jobs

TOKEN = secrets.token_urlsafe(32)
BEARER = {"Authorization": f"Bearer {TOKEN}"}
SETTINGS = '[engine]\nhost_name = "pc-1"\n\n[engine.scheduler]\ntick = 5\n'


class Store:
    """An in-memory key store, so no test reaches Credential Manager."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        return self.values.get(name)

    def replace(self, name: str, value: str) -> None:
        self.values[name] = value

    def delete(self, name: str) -> None:
        self.values.pop(name, None)


def qmx_folder(root: Path) -> Layout:
    layout = resolve(root, create=True)
    (layout.home / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    return layout


def world(layout: Layout, synced: list[str] | None = None, keys: Store | None = None) -> World:
    store = keys or Store()
    control = ControlService(layout.home, secret_getter=lambda _s, _n: None)

    def first_sync(place_id: str) -> str:
        if synced is not None:
            synced.append(place_id)
        return f"the first sync started (job for {place_id})"

    return World(layout, store, Rclone(layout, keys=store), Jobs(), control, first_sync)


def app_of(connect: Connect) -> FastAPI:
    control = cast("ControlService", connect.world.control)
    return create_app(control, TOKEN, extra_routers=dialog_routers(connect, control))


def ended(rest: TestClient, job_id: str) -> dict[str, Any]:
    for _ in range(1200):
        job = cast("dict[str, Any]", rest.get(f"/api/connect/jobs/{job_id}", headers=BEARER).json())
        if job["state"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError("the connect job did not end within 60 s")


def connected(rest: TestClient, kind: str, place: str, answer: dict[str, object]) -> dict[str, Any]:
    asked = rest.post(
        "/api/connect/jobs", json={"kind": kind, "place": place, "answer": answer}, headers=BEARER
    )
    assert asked.status_code == 202, asked.text
    return ended(rest, asked.json()["id"])


def rows(layout: Layout) -> dict[str, Any]:
    stored = tomllib.loads((layout.home / "settings.toml").read_text(encoding="utf-8"))
    return cast("dict[str, Any]", stored["engine"].get("placement", {}))


def test_a_folder_storage_connects_through_the_host_routes_with_one_row_and_its_first_sync(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    store = tmp_path / "usb"
    store.mkdir()
    backups = service(layout, Clock())
    connect = storage_dialog(layout, backups.control, backups, keys=Store())
    with TestClient(app_of(connect)) as rest:
        job = connected(rest, "folder", "usb", {"fields": {"path": str(store)}})
    stored = tomllib.loads((layout.home / "settings.toml").read_text(encoding="utf-8"))
    row = stored["engine"]["placement"]["usb"]
    assert job["state"] == "finished", job["line"]
    assert job["needs"] is None
    assert {k: row[k] for k in ("via", "can", "path")} == {
        "via": "folder",
        "can": ["keep"],
        "path": str(store),
    }
    assert len(row["id"]) == 26
    assert (stored["engine"]["host_name"], stored["engine"]["scheduler"]) == ("pc-1", {"tick": 5})
    assert job["result"]["lines"][-1].startswith("usb: the first sync")
    assert list(store.iterdir()) == []


def test_the_kinds_name_what_each_can_do_and_every_route_needs_the_bearer(tmp_path: Path) -> None:
    connect = Connect(world(qmx_folder(tmp_path / "QMX")), KINDS)
    with TestClient(app_of(connect)) as rest:
        kinds = rest.get("/api/connect/kinds", headers=BEARER).json()["kinds"]
        bare = [
            rest.get("/api/connect/kinds").status_code,
            rest.post("/api/connect/jobs", json={"kind": "folder", "place": "x"}).status_code,
            rest.get("/api/connect/jobs/x").status_code,
            rest.post("/api/connect/jobs/x/cancel").status_code,
        ]
    assert [(k["id"], k["can"], k["rclone"]) for k in kinds] == [
        ("folder", ["keep"], False),
        ("drive", ["keep"], True),
        ("r2", ["keep"], True),
        ("sftp", ["keep"], True),
        ("rclone", ["keep"], True),
        ("server", ["run"], False),
        ("server-keep", ["keep"], True),
        ("modal", ["run"], False),
        ("e2b", ["run"], False),
        ("deep-logs-pc", [], False),
        ("deep-logs-server", [], False),
        ("trading-node-pc", [], False),
    ]
    assert bare == [401] * 4


def test_a_folder_job_with_no_answer_ends_at_the_folder_card_and_writes_nothing(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    with TestClient(app_of(Connect(world(layout), KINDS))) as rest:
        job = connected(rest, "folder", "usb", {})
    assert job["state"] == "finished"
    assert job["needs"]["card"] == "folder"
    assert [f["Name"] for f in job["needs"]["fields"]] == ["path"]
    assert rows(layout) == {}


def test_a_rerun_skips_every_step_that_is_done_and_starts_no_second_sync(tmp_path: Path) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    (tmp_path / "usb").mkdir()
    synced: list[str] = []
    with TestClient(app_of(Connect(world(layout, synced), KINDS))) as rest:
        connected(rest, "folder", "usb", {"fields": {"path": str(tmp_path / "usb")}})
        before = (layout.home / "settings.toml").read_bytes()
        again = connected(rest, "folder", "usb", {"fields": {"path": str(tmp_path / "usb")}})
    assert again["state"] == "finished"
    assert again["result"]["lines"][-3:] == [
        "test: already done, skipped",
        "row: already done, skipped",
        "first-sync: already done, skipped",
    ]
    assert (layout.home / "settings.toml").read_bytes() == before
    assert synced == [rows(layout)["usb"]["id"]]


@pytest.mark.parametrize("killed_after", [1, 2, 3])
def test_a_kill_after_any_step_converges_on_one_row(tmp_path: Path, killed_after: int) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    (tmp_path / "usb").mkdir()
    kind = KINDS["folder"]
    cut = dataclasses.replace(kind, steps=kind.steps[:killed_after])
    answer: dict[str, object] = {"fields": {"path": str(tmp_path / "usb")}}

    def ignore(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
        del step, done, total, counts

    run_kind(cut, "usb", answer, report=ignore, world=world(layout))
    first = dict(rows(layout))
    run_kind(kind, "usb", answer, report=ignore, world=world(layout))
    found = rows(layout)
    assert list(found) == ["usb"]
    assert found["usb"]["path"] == str(tmp_path / "usb")
    if first:
        assert found["usb"]["id"] == first["usb"]["id"]


def refused(rest: TestClient, place: str, path: Path) -> tuple[int, str]:
    answer = rest.post(
        "/api/connect/jobs",
        json={"kind": "folder", "place": place, "answer": {"fields": {"path": str(path)}}},
        headers=BEARER,
    )
    return answer.status_code, str(answer.json().get("detail", ""))


def test_a_taken_name_a_second_row_on_one_folder_and_the_qmx_folder_are_refused(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    for name in ("usb", "other"):
        (tmp_path / name).mkdir()
    with TestClient(app_of(Connect(world(layout), KINDS))) as rest:
        connected(rest, "folder", "usb", {"fields": {"path": str(tmp_path / "usb")}})
        before = (layout.home / "settings.toml").read_bytes()
        answers = [
            refused(rest, "usb", tmp_path / "other"),
            refused(rest, "second", tmp_path / "usb"),
            refused(rest, "inside", layout.root / "backups"),
        ]
    assert [code for code, _ in answers] == [409, 409, 409]
    assert "the name usb is taken by another place" in answers[0][1]
    assert "the storage usb already keeps copies at" in answers[1][1]
    assert "is inside the QMX folder" in answers[2][1]
    assert (layout.home / "settings.toml").read_bytes() == before


def test_a_folder_on_the_qmx_folders_drive_is_kept_with_a_warning_and_a_missing_one_stops(
    tmp_path: Path,
) -> None:
    layout = qmx_folder(tmp_path / "QMX")
    (tmp_path / "usb").mkdir()
    with TestClient(app_of(Connect(world(layout), KINDS))) as rest:
        kept = connected(rest, "folder", "usb", {"fields": {"path": str(tmp_path / "usb")}})
        gone = connected(rest, "folder", "gone", {"fields": {"path": str(tmp_path / "unplugged")}})
    assert any(
        "is on the same drive as your QMX folder" in line for line in kept["result"]["lines"]
    )
    assert gone["state"] == "stopped"
    assert "is not there (is its drive plugged in?)" in gone["line"]
    assert list(rows(layout)) == ["usb"]


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({"kind": "tape", "place": "usb"}, 400),
        ({"kind": "folder", "place": "pc"}, 400),
        ({"kind": "folder", "place": "bad name"}, 400),
    ],
)
def test_an_unknown_kind_and_a_bad_place_name_answer_400(
    tmp_path: Path, body: dict[str, object], status: int
) -> None:
    with TestClient(app_of(Connect(world(qmx_folder(tmp_path / "QMX")), KINDS))) as rest:
        answer = rest.post("/api/connect/jobs", json=body, headers=BEARER)
    assert answer.status_code == status
