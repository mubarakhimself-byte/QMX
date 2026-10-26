"""The Library under design 62 B2: one a newer QMX marked too new opens read-only and nothing in
it is written, its index included; an index of another version is rebuilt, and one that is not
QMX's is moved aside, never deleted."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_home import Label, resolve

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")


def note(text: str, item: str) -> Draft:
    return Draft("note", item, title=text, blobs={"body.md": text.encode()})


def library_of(tmp_path: Path) -> Path:
    """A QMX folder's Library holding one note on main."""
    root = resolve(tmp_path / "QMX", create=True, drives=[]).data / "library"
    with Store.open(root, redactor=redact) as store:
        store.put(OPERATOR, note("the first plan", "plan"), on="main", expected_head=None)
    return root


def mark_library(root: Path, *, version: int, min_reader: int) -> None:
    label_path = root.parent.parent / "qmx-home.toml"
    label = Label.parse(label_path.read_text(encoding="utf-8"))
    stores = {**label.stores, "library": {"version": version, "min_reader": min_reader}}
    label_path.write_text(
        Label(label.home_id, 2, "0.1.0", "0.6.0", stores=stores).dump(), encoding="utf-8"
    )


def tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "writer.lock"
    }


def test_a_library_too_new_for_this_release_opens_read_only_and_is_not_written(
    tmp_path: Path,
) -> None:
    root = library_of(tmp_path)
    mark_library(root, version=2, min_reader=2)
    before = tree(root)

    with Store.open(root, redactor=redact) as store:
        found = [hit.title for hit in store.search(OPERATOR, "first plan")]
        with pytest.raises(LibraryRefused) as refused:
            store.put(OPERATOR, note("a second plan", "plan-2"), on="main", expected_head=None)
        health = (store.state.health, store.state.incident)

    assert found == ["the first plan"]
    assert str(refused.value).startswith(
        "storage_failure: put refused: the Library opened read-only. This QMX folder's Library "
        "was written by QMX 0.6.0 as Library version 2."
    )
    assert health[0] == "read_only"
    assert str(health[1]).endswith("The Library opens read-only until then.")
    assert tree(root) == before


def test_a_library_one_version_newer_that_allows_this_release_opens_for_writing(
    tmp_path: Path,
) -> None:
    root = library_of(tmp_path)
    mark_library(root, version=2, min_reader=1)

    with Store.open(root, redactor=redact) as store:
        store.put(OPERATOR, note("a second plan", "plan-2"), on="main", expected_head=None)
        heads = (store.head("plan", "main") is not None, store.head("plan-2", "main") is not None)

    assert heads == (True, True)


@pytest.mark.parametrize("shape", ["another version", "not qmx"])
def test_an_index_this_release_cannot_use_is_rebuilt_and_a_foreign_one_kept_aside(
    tmp_path: Path, shape: str
) -> None:
    root = library_of(tmp_path)
    catalog = root / "catalog.db"
    if shape == "another version":
        with closing(sqlite3.connect(catalog, isolation_level=None)) as db:
            db.execute("PRAGMA user_version = 9")
            db.execute("DELETE FROM objects")
    else:
        for suffix in ("", "-wal", "-shm"):
            Path(f"{catalog}{suffix}").unlink(missing_ok=True)
        catalog.write_text("my own notes\n" * 100, encoding="utf-8")

    with Store.open(root, redactor=redact) as store:
        found = [hit.title for hit in store.search(OPERATOR, "first plan")]

    kept = sorted(path.name for path in root.glob("catalog.db.not-qmx-*"))
    assert found == ["the first plan"]
    if shape == "not qmx":
        assert len(kept) == 1
        assert (root / kept[0]).read_text(encoding="utf-8") == "my own notes\n" * 100
    else:
        assert kept == []
