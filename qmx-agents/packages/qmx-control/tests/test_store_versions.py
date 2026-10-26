"""The control stores and the settings writer under design 62 B2: a newer store that still allows
this release opens, a raised one is refused by name, and an older release keeps what a newer one
wrote into settings.toml word for word."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from qmx_home import Label, resolve
from qmx_home.versions import StoreRefused

from qmx_control.models import ControlError
from qmx_control.service import ControlService, SessionInput

NEWER_SECTIONS = """\
# written by hand
[budgets]
daily_usd = 5

# pods came with a newer QMX
[lab_pods]  # a section a newer QMX added
window = "24h"   # his choice
regions = [ "eu",
  "us" ]

[lab_pods.gpu]
kind = 'a100'
"""


def home_of(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def test_a_settings_write_keeps_a_section_this_release_does_not_know_word_for_word(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    (home / "settings.toml").write_text(NEWER_SECTIONS, encoding="utf-8")
    service = ControlService(home)

    service.settings_put("budgets", {"daily_usd": 7})

    text = (home / "settings.toml").read_text(encoding="utf-8")
    assert text == NEWER_SECTIONS.replace("daily_usd = 5", "daily_usd = 7")
    assert service.settings_get("budgets") == {"daily_usd": 7}


def test_settings_from_a_folder_whose_settings_are_too_new_are_not_written(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    label_path = home.parent / "qmx-home.toml"
    label = Label.parse(label_path.read_text(encoding="utf-8"))
    stores = {**label.stores, "settings": {"version": 3, "min_reader": 2}}
    label_path.write_text(
        Label(label.home_id, 2, "0.1.0", "0.5.0", stores=stores).dump(), encoding="utf-8"
    )
    (home / "settings.toml").write_text(NEWER_SECTIONS, encoding="utf-8")
    service = ControlService(home)

    with pytest.raises(ControlError) as refused:
        service.settings_put("budgets", {"daily_usd": 7})

    assert (refused.value.code, refused.value.status) == ("settings_too_new", 409)
    assert str(refused.value).startswith(
        "This QMX folder's settings was written by QMX 0.5.0 as settings version 3."
    )
    assert (home / "settings.toml").read_text(encoding="utf-8") == NEWER_SECTIONS
    assert service.settings_get("budgets") == {"daily_usd": 5}


def newer_control_store(home: Path, *, min_reader: int) -> Path:
    ControlService(home)
    path = home / "control.db"
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        db.execute("CREATE TABLE pods (id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO pods VALUES ('pod-1')")
        db.execute("PRAGMA user_version = 2")
        db.execute("UPDATE qmx_meta SET value = ? WHERE key = 'min_reader'", (str(min_reader),))
    return path


def test_a_control_store_one_version_newer_opens_and_keeps_its_new_table(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = newer_control_store(home, min_reader=1)

    service = ControlService(home)
    session = service.sessions_create(SessionInput(title="versions"))

    with closing(sqlite3.connect(path)) as db:
        kept = db.execute("SELECT id FROM pods").fetchall()
        version = db.execute("PRAGMA user_version").fetchone()
    assert (kept, version) == ([("pod-1",)], (2,))
    assert session["title"] == "versions"


def test_a_control_store_whose_min_reader_is_raised_is_refused_by_name(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = newer_control_store(home, min_reader=2)
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        ControlService(home)

    assert str(refused.value).startswith(
        "This QMX folder's control store was written by QMX 0.1.0 as control store version 2. "
        "This QMX reads control store version 1, and this one needs a QMX that reads version 2 "
        "or newer."
    )
    assert path.read_bytes() == before


def test_a_run_index_that_is_not_qmxs_is_refused_and_left_as_it_was(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = home / "runs.db"
    with closing(sqlite3.connect(path, isolation_level=None)) as foreign:
        foreign.execute("PRAGMA application_id = 1095911234")
        foreign.execute("CREATE TABLE runs (id TEXT)")
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        ControlService(home)

    assert str(refused.value) == (
        f"{path} is not a QMX run index: it belongs to another program (application id "
        "0x41524742). QMX leaves it as it is; move it aside and start QMX again to make a new one."
    )
    assert path.read_bytes() == before
