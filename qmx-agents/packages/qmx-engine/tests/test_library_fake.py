"""The fake Library keeps the Library's rules: closed edges, drafts off `main`, run branches written
only by their run, and nothing ever deleted or rewritten."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, cast

import pytest
from flows import CHAIN

from qmx_engine.ports.library import Bundle, LibraryRefused
from qmx_engine.ports.library_fake import LibraryFake


def test_an_edge_outside_the_closed_set_is_refused(tmp_path: Path) -> None:
    with LibraryFake.open(tmp_path) as library:
        draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
        report = library.put_test_report(
            "sha256:x", {"workflow_item": draft.item, "run_id": "r1"}, principal="run:r1"
        )
        with pytest.raises(LibraryRefused, match=r"^edge_not_in_set:"):
            library.link(
                draft.object_id, cast(Any, "supersedes"), report.object_id, principal="operator"
            )
        library.link(draft.object_id, "tested-by", report.object_id, principal="run:r1")
        with pytest.raises(sqlite3.IntegrityError):
            library.db.execute(
                "INSERT INTO edges (from_id, edge, to_id, principal, at) "
                "VALUES ('a', 'ran-on', 'b', 'x', 't')"
            )
        edges = [(e.edge, e.to_id) for e in library.edges(draft.object_id)]

    assert edges == [("tested-by", report.object_id)]


@pytest.mark.parametrize("table", ["objects", "blobs", "edges", "refs", "annotations"])
def test_nothing_is_ever_deleted(tmp_path: Path, table: str) -> None:
    with LibraryFake.open(tmp_path) as library:
        draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
        library.link(draft.object_id, "replaces", draft.object_id, principal="operator")
        library.annotate(draft.object_id, "state", "archived", principal="operator")
        (before,) = library.db.execute(f"SELECT count(*) FROM {table}").fetchone()  # noqa: S608
        with pytest.raises(sqlite3.IntegrityError, match="never deletes"):
            library.db.execute(f"DELETE FROM {table}")  # noqa: S608
        (after,) = library.db.execute(f"SELECT count(*) FROM {table}").fetchone()  # noqa: S608

    assert after == before > 0


def test_objects_are_never_rewritten(tmp_path: Path) -> None:
    with LibraryFake.open(tmp_path) as library:
        draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            library.db.execute(
                "UPDATE objects SET fields = '{}' WHERE object_id = ?", (draft.object_id,)
            )
        stored = library.get(draft.object_id)

    assert stored.fields["revision"] == 1


def test_drafts_stay_off_main_and_run_branches_belong_to_their_run(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    with LibraryFake.open(tmp_path) as library:
        with pytest.raises(LibraryRefused, match=r"^not_a_draft_ref:"):
            library.put_draft("script-chain", chain, 0, principal="operator", ref="main")
        draft = library.put_draft(None, chain, 0, principal="operator")
        with pytest.raises(LibraryRefused, match=r"^revision_conflict:"):
            library.put_draft(draft.item, chain, 0, principal="operator")
        with pytest.raises(LibraryRefused, match=r"^wrong_principal:"):
            library.put_artifact(b"x", "trace", {}, run_id="r1", principal="operator")
        trace = library.put_artifact(b"x", "trace", {}, run_id="r1", principal="run:r1")

    assert (draft.ref, draft.revision) == ("refs/drafts/script-chain", 1)
    assert (trace.ref, trace.kind) == ("refs/runs/r1", "artifact")
