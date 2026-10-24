"""The outbox (Library AD-14, AD-26): a lost reply is not a conflict, a moved head is parked, and
an entry the primary cannot read waits instead of landing."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.outbox import Entry, Outbox, enter, replay
from qmx_library.port import Commit, Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")


class Primary:
    """A real store seen the way a replay sees the primary: its ref log decides, not a reply."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def ever_placed(self, object_id: str, item: str, ref: str) -> bool:
        return self.store.ever_placed(object_id, item, ref)

    def head(self, item: str, ref: str) -> str | None:
        found = self.store.head(item, ref)
        return None if found is None else found[0]

    def put(self, draft: Draft, *, on: str, expected_head: str | None) -> Commit:
        return self.store.put(OPERATOR, draft, on=on, expected_head=expected_head)

    def can_read(self, kind: str, version: int) -> bool:
        return self.store.can_read(kind, version)

    def park(self, entry: Entry) -> str:
        return self.store.park_entry(
            entry.item,
            entry.ref,
            expected_head=entry.expected_head,
            intended=entry.object_id,
        )


@pytest.fixture
def server(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as opened:
        yield opened


def note_text(title: str) -> Draft:
    return Draft("note", "n1", title=title)


def lost_reply(
    outbox: Outbox,
    done: Commit,
    draft: Draft,
    *,
    expected_head: str | None,
    schema_version: int = 1,
) -> Entry:
    """The entry a PC keeps when the write landed but the reply never came back."""
    entry = enter(
        draft,
        item=done.item,
        ref=done.ref,
        expected_head=expected_head,
        object_id=done.object_id,
        kind="note",
        schema_version=schema_version,
    )
    outbox.append(entry)
    return entry


def test_a_replay_of_an_entry_already_on_its_ref_succeeds(server: Store, tmp_path: Path) -> None:
    outbox = Outbox(tmp_path / "outbox.jsonl")
    draft = note_text("one")
    done = server.put(OPERATOR, draft, on="main", expected_head=None)
    lost_reply(outbox, done, draft, expected_head=None)

    replayed = replay(outbox, Primary(server))

    assert replayed.applied == [done.object_id]
    assert replayed.parked == []
    assert len(outbox) == 0
    assert server.head("n1", "main") == (done.object_id, 1)


def test_a_replay_after_a_workflow_moved_the_ref_on_still_succeeds(
    server: Store, tmp_path: Path
) -> None:
    outbox = Outbox(tmp_path / "outbox.jsonl")
    draft = note_text("one")
    done = server.put(OPERATOR, draft, on="main", expected_head=None)
    lost_reply(outbox, done, draft, expected_head=None)
    newer = server.put(
        OPERATOR,
        Draft("note", "n1", title="two", parents=[done.object_id]),
        on="main",
        expected_head=done.object_id,
    )

    replayed = replay(outbox, Primary(server))

    assert replayed.applied == [done.object_id]
    assert replayed.parked == []
    assert server.head("n1", "main") == (newer.object_id, 2)
    assert server.catalog.refs_like("refs/conflicts/n1/") == 0


def test_a_moved_head_over_an_unplaced_object_is_parked_not_applied(
    server: Store, tmp_path: Path
) -> None:
    outbox = Outbox(tmp_path / "outbox.jsonl")
    anchor = server.put(OPERATOR, note_text("one"), on="main", expected_head=None)
    draft = Draft("note", "n1", title="mine", parents=[anchor.object_id])
    intended = server.ingest(
        {
            "schema": "qmx.library.object/1",
            "kind": "note",
            "schema_version": 1,
            "item_id": "n1",
            "title": "mine",
            "summary": "",
            "fields": {},
            "blobs": {},
            "parents": [anchor.object_id],
            "relations": [],
            "world": None,
        }
    )
    outbox.append(
        enter(
            draft,
            item="n1",
            ref="main",
            expected_head=anchor.object_id,
            object_id=intended,
            kind="note",
            schema_version=1,
        )
    )
    moved = server.put(
        OPERATOR,
        Draft("note", "n1", title="theirs", parents=[anchor.object_id]),
        on="main",
        expected_head=anchor.object_id,
    )

    replayed = replay(outbox, Primary(server))

    assert replayed.parked == ["refs/conflicts/n1/1"]
    assert replayed.applied == []
    assert server.head("n1", "main") == (moved.object_id, 2)
    parked = server.resolve(OPERATOR, "n1", "refs/conflicts/n1/1")
    assert server.get(OPERATOR, parked).fields["ours"] == intended


def test_an_entry_of_a_version_the_reader_lacks_waits_and_names_the_server(
    server: Store, tmp_path: Path
) -> None:
    outbox = Outbox(tmp_path / "outbox.jsonl")
    draft = note_text("from a newer PC")
    entry = enter(
        draft,
        item="n1",
        ref="main",
        expected_head=None,
        object_id="fp1:sha256:" + "a" * 64,
        kind="note",
        schema_version=99,
    )
    outbox.append(entry)

    replayed = replay(outbox, Primary(server))

    assert replayed.kept == ["n1"]
    assert replayed.refused == [
        "needs_update: the server needs updating: it has no note schema version 99 (n1 on main)"
    ]
    assert len(outbox) == 1
    assert server.head("n1", "main") is None


def test_a_replay_whose_stale_head_cannot_be_parked_keeps_the_entry(
    server: Store, tmp_path: Path
) -> None:
    """A primary that refuses the write keeps the save: a moment's refusal drops nothing."""
    outbox = Outbox(tmp_path / "outbox.jsonl")
    draft = note_text("one")
    entry = enter(
        draft,
        item="n1",
        ref="main",
        expected_head=None,
        object_id="fp1:sha256:" + "b" * 64,
        kind="note",
        schema_version=1,
    )
    outbox.append(entry)

    class Full(Primary):
        def put(self, draft: Draft, *, on: str, expected_head: str | None) -> Commit:
            raise LibraryRefused("disk_full", "below the floor")

    replayed = replay(outbox, Full(server))

    assert replayed.kept == ["n1"]
    assert replayed.refused == ["disk_full: disk_full: below the floor"]
    assert len(outbox) == 1
