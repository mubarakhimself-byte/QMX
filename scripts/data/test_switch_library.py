"""The switch script runs only on the data/ of a QMX folder, so an old folder is never switched in
place (design 62 F step 4).

cd qmx-agents
uv run --no-sync python -m pytest ../scripts/data/test_switch_library.py -q -n 2
"""

# ruff: noqa: S101

from __future__ import annotations

import hashlib
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest
from qmx_home import resolve

sys.path.insert(0, str(Path(__file__).resolve().parent))

import switch_library


def library_b(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(home / "library.db")) as db, db:
        db.executescript("""
            CREATE TABLE items(id TEXT PRIMARY KEY, data TEXT NOT NULL, root TEXT NOT NULL,
                version INTEGER NOT NULL, source TEXT NOT NULL, fetched_date TEXT);
            CREATE TABLE links(source TEXT, target TEXT, relation TEXT);
            CREATE TABLE memo(key TEXT PRIMARY KEY, item_id TEXT NOT NULL);
        """)


def test_an_old_folder_outside_a_qmx_folder_is_refused_and_left_as_it_was(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = tmp_path / ".qmx"
    library_b(old)
    before = hashlib.sha256((old / "library.db").read_bytes()).hexdigest()

    code = switch_library.main(["--home", str(old)])

    assert code == switch_library.REFUSED
    assert capsys.readouterr().out.startswith(f"refused: {old} is not the data/ of a QMX folder")
    assert sorted(p.name for p in old.iterdir()) == ["library.db"]
    assert hashlib.sha256((old / "library.db").read_bytes()).hexdigest() == before


def test_a_copy_in_a_qmx_folder_switches(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    library_b(layout.data)

    code = switch_library.main(["--home", str(layout.data)])

    assert code == 0
    assert (layout.data / "migration" / "retired" / "library.db").is_file()
    assert not (layout.data / "library.db").exists()
