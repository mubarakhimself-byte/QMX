"""The Library never opens an empty store beside his old `library.db`, nor a home whose bring-in did
not finish (62a gap L4, design 62 F step 4)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from qmx_control.library import UNFINISHED, Library
from qmx_control.models import ControlError, LibraryInput


def test_a_home_holding_the_old_library_db_refuses_and_names_the_first_start(
    tmp_path: Path,
) -> None:
    with closing(sqlite3.connect(tmp_path / "library.db")) as db:
        db.execute("CREATE TABLE items(id TEXT PRIMARY KEY, data TEXT NOT NULL)")
    library = Library(tmp_path)

    with pytest.raises(ControlError) as refused:
        library.search()

    assert refused.value.code == "old_library"
    assert str(refused.value) == (
        f"{tmp_path} holds your old Library (library.db) and the new Library there is empty, so "
        "QMX will not open it and leave your items out of sight. Bring your old data into a new "
        "QMX folder with the first start, which never changes this one: python -m qmx_host "
        "bring-in --home <new QMX folder> --old <old folder>"
    )
    assert not (tmp_path / "library").exists(), "no empty store was made beside it"


def test_an_unfinished_bring_in_refuses_until_it_is_redone_and_a_switched_home_opens(
    tmp_path: Path,
) -> None:
    unfinished = tmp_path / UNFINISHED
    unfinished.parent.mkdir(parents=True)
    unfinished.write_text("the copy of runs.db does not match your old folder", encoding="utf-8")

    with pytest.raises(ControlError, match=r"did not finish: the copy of runs.db does not match"):
        Library(tmp_path).search()
    unfinished.unlink()
    saved = Library(tmp_path)
    saved.save(LibraryInput(kind="note", title="Carry", content={"text": "carry works"}))
    saved.close()
    (tmp_path / "library.db").write_bytes(b"retired later")

    reopened = Library(tmp_path)
    titles = [found["title"] for found in reopened.search("Carry")]
    reopened.close()
    assert titles == ["Carry"]
