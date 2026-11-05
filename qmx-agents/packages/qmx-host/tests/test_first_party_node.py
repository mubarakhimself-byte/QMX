"""The apps his connect steps enable come back at every host start, on any machine (C-38).

The supervisor here records what it is asked; the real restart runs as `c38-restart` on a real
host."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import path_sources

import qmx_host.connect  # noqa: F401 - connect_node loads through it  # pyright: ignore[reportUnusedImport]
from qmx_host.connect_node import (
    MIS_APP,
    NODE_APP,
    _enable,  # pyright: ignore[reportPrivateUsage]
    _enabled,  # pyright: ignore[reportPrivateUsage]
)
from qmx_host.first_start import APP_FOLDERS, FIRST_PARTY, enable_first_party


class FakeSupervisor:
    """A machine's apps, each installed from what ships today and built from the libraries as they
    stand, so a host start finds nothing to refresh: what is installed, what runs, and every
    install and start it was asked."""

    def __init__(self, *installed: str) -> None:
        self.installed = list(installed)
        self.running: set[str] = set()
        self.asked: list[tuple[str, str]] = []
        self.told: list[str] = []

    def status(self, app_id: str) -> Document:
        return {"status": "running" if app_id in self.running else "stopped"}

    def get(self, app_id: str) -> Document:
        if app_id not in self.installed:
            raise AppError("not_found", "The app is not installed.", 404)
        shipped = Definition.load(APP_FOLDERS[app_id])
        return {
            "definition": {"id": app_id, "risk": shipped.manifest.risk},
            "definition_hash": shipped.hash,
            "runtime": self.status(app_id),
        }

    def built_from(self, definition_hash: str) -> Document:
        folder = next(
            folder
            for folder in APP_FOLDERS.values()
            if Definition.load(folder).hash == definition_hash
        )
        return cast(Document, path_sources(folder))

    def notice(self, app_id: str, text: str | None) -> None:
        if text is not None:
            self.told.append(f"{app_id}: {text}")

    def install(self, folder: Path, *, trust: str) -> Document:
        assert trust == "first_party"
        self.asked.append(("install", folder.name))
        self.installed.append(folder.name)
        return {}

    def start(self, app_id: str) -> Document:
        self.asked.append(("start", app_id))
        self.running.add(app_id)
        return {}

    def restarted(self) -> FakeSupervisor:
        """The host died and came back: every app stopped, every install kept."""
        return FakeSupervisor(*self.installed)


def say_nothing(_line: str) -> None:
    pass


def run_on(home: Path, apps: FakeSupervisor) -> Any:
    return SimpleNamespace(
        kind=SimpleNamespace(id="this-pc"),
        place="pc",
        world=SimpleNamespace(
            layout=SimpleNamespace(home=home),
            control=SimpleNamespace(app_runtime=lambda: apps),
        ),
        say=say_nothing,
    )


def enabled(home: Path) -> list[str]:
    return cast(list[str], json.loads((home / FIRST_PARTY).read_text("utf-8"))["enable"])


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path


def test_the_node_enable_starts_comes_back_at_the_next_host_start(home: Path) -> None:
    apps = FakeSupervisor(NODE_APP, MIS_APP)
    _enable((NODE_APP, MIS_APP), run_on(home, apps))

    back = apps.restarted()
    started = enable_first_party(home, cast(Any, back))

    assert started == [NODE_APP, MIS_APP]
    assert back.running == {NODE_APP, MIS_APP}
    assert back.asked == [("start", NODE_APP), ("start", MIS_APP)]
    assert back.told == []


def test_an_existing_first_party_list_is_kept_with_its_order(home: Path) -> None:
    (home / FIRST_PARTY).write_text(json.dumps({"enable": ["qmb", "mis"]}), "utf-8")

    _enable((NODE_APP, MIS_APP), run_on(home, FakeSupervisor(NODE_APP, MIS_APP)))

    assert enabled(home) == ["qmb", "mis", NODE_APP]


def test_a_node_not_installed_at_a_host_start_is_installed_from_the_shipped_folder(
    home: Path,
) -> None:
    (home / FIRST_PARTY).write_text(json.dumps({"enable": [NODE_APP]}), "utf-8")
    apps = FakeSupervisor()

    enable_first_party(home, cast(Any, apps))

    assert apps.asked == [("install", NODE_APP), ("start", NODE_APP)]
    assert APP_FOLDERS[NODE_APP].name == NODE_APP
    assert (APP_FOLDERS[NODE_APP] / "pyproject.toml").is_file()


def test_the_enable_step_is_not_done_until_a_restart_would_start_them(home: Path) -> None:
    apps = FakeSupervisor(NODE_APP)
    run = run_on(home, apps)
    apps.running.add(NODE_APP)
    check = partial(_enabled, (NODE_APP,))

    before = check(run)
    _enable((NODE_APP,), run)

    assert (before, check(run)) == (False, True)
    assert apps.asked == []


def test_a_list_that_does_not_read_is_replaced_by_the_apps_enable_ran(home: Path) -> None:
    (home / FIRST_PARTY).write_text("{not json", "utf-8")

    _enable((NODE_APP,), run_on(home, FakeSupervisor(NODE_APP)))

    assert enabled(home) == [NODE_APP]
