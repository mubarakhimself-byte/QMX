"""The Library's last giving-way rule (F22, D-11): below the machine's floor no write is taken at
all, so a save is refused whole and never half written."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
MIB = 1024 * 1024


def note() -> Draft:
    return Draft("note", "n1", title="below the floor", blobs={"body.md": b"half a note"})


def test_a_save_below_the_floor_is_refused_whole_and_leaves_no_file(tmp_path: Path) -> None:
    root = tmp_path / "library"
    floor = shutil.disk_usage(tmp_path).free + MIB
    with (
        Store.open(root, redactor=redact, floor_bytes=floor) as store,
        pytest.raises(LibraryRefused, match=r"^disk_full:"),
    ):
        store.put(OPERATOR, note(), on="refs/drafts/n1", expected_head=None)

    assert sorted(path.name for path in (root / "objects").rglob("*")) == []
    assert not (root / "blobs").exists()
    assert not (root / "refs" / "log.jsonl").exists()


def test_a_store_with_room_takes_the_save(tmp_path: Path) -> None:
    root = tmp_path / "library"
    with Store.open(root, redactor=redact, floor_bytes=1) as store:
        kept = store.put(OPERATOR, note(), on="refs/drafts/n1", expected_head=None)

    assert kept.ref == "refs/drafts/n1"
    assert len(list((root / "objects").rglob("*.json"))) == 1
