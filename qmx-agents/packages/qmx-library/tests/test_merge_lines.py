"""Line merge, key merge, blame and history through the port (AD-30).

Two chats edit one note on their own refs and merge into the item's draft ref, which is the move a
chat makes when it saves into the Library. The tests read the merged bytes, the conflict object and
the blame of each line, never a private helper.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_engine.ledger import redact

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import MAIN, Principal, agent_ref, drafts_ref
from qmx_library.store import Store

OPERATOR = Principal("operator")
ALICE = Principal("agent", "alice")
BOB = Principal("agent", "bob")


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def note(text: str, item: str | None = None) -> Draft:
    return Draft("note", item, title="note", blobs={"body.md": text.encode()})


def setup(spec: dict[str, object], item: str | None = None) -> Draft:
    return Draft("setup", item, title="setup", blobs={"spec": json.dumps(spec).encode()})


def body(store: Store, object_id: str) -> str:
    return store.get(OPERATOR, object_id, blobs="fetch").data["body.md"].decode()


def edit(store: Store, who: Principal, base: str, draft: Draft, item: str) -> str:
    """One chat's version on its own ref, parented on the version it read."""
    commit = store.put(
        who,
        Draft(
            draft.kind,
            item,
            draft.title,
            draft.summary,
            draft.fields,
            draft.blobs,
            parents=[base],
        ),
        on=agent_ref(str(who.id), item),
        expected_head=None,
    )
    return commit.object_id


def test_a_clean_text_merge_keeps_both_edits(store: Store) -> None:
    found = store.put(OPERATOR, note("one\ntwo\nthree\n"), on=MAIN, expected_head=None)
    item = found.item
    alice = edit(store, ALICE, found.object_id, note("ONE\ntwo\nthree\n"), item)
    bob = edit(store, BOB, found.object_id, note("one\ntwo\nTHREE\n"), item)

    first = store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))
    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    assert first.outcome == "fast-forward"
    assert merged.outcome == "merged"
    assert body(store, merged.object_id) == "ONE\ntwo\nTHREE\n"
    assert store.get(OPERATOR, merged.object_id).parents == (alice, bob)
    assert (
        store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item)).outcome
        == "up-to-date"
    )
    held = store.head(item, drafts_ref(item))
    assert held is not None and held[0] == merged.object_id


def test_a_clashing_edit_mints_one_conflict_holding_the_marked_text(store: Store) -> None:
    found = store.put(OPERATOR, note("one\ntwo\nthree\n"), on=MAIN, expected_head=None)
    item = found.item
    alice = edit(store, ALICE, found.object_id, note("one\nTWO\nthree\n"), item)
    edit(store, BOB, found.object_id, note("one\n2\nthree\n"), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    assert merged.outcome == "conflict"
    conflicts = store.conflicts(OPERATOR, item)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.object_id == merged.object_id
    assert conflict.fields["ours"] == alice
    (entry,) = cast(list[dict[str, Any]], conflict.fields["entries"])
    marked = str(entry["text"])
    assert marked.startswith("one\n<<<<<<< ours\n")
    assert "||||||| base\n" in marked
    assert ">>>>>>> theirs\n" in marked
    held = store.head(item, drafts_ref(item))
    assert held is not None and held[0] == alice


def test_a_json_merge_with_one_clashing_key_mints_one_conflict_entry(store: Store) -> None:
    found = store.put(OPERATOR, setup({"a": 0, "b": 0}, "s"), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, setup({"a": 1, "b": 0}, item), item)
    edit(store, BOB, found.object_id, setup({"a": 2, "b": 5}, item), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    assert merged.outcome == "conflict"
    (conflict,) = store.conflicts(OPERATOR, item)
    (entry,) = cast(list[dict[str, Any]], conflict.fields["entries"])
    assert entry == {
        "path": "blobs.spec.a",
        "slot": "spec",
        "media_type": "application/json",
        "key": "a",
        "base": 0,
        "ours": 1,
        "theirs": 2,
    }

    resolved = store.resolve_conflict(ALICE, conflict.object_id, values={"blobs.spec.a": 3})

    assert resolved.outcome == "merged"
    spec = json.loads(store.get(OPERATOR, resolved.object_id, blobs="fetch").data["spec"])
    assert spec == {"a": 3, "b": 5}
    assert store.conflicts(OPERATOR, item) == []


def test_a_binary_slot_changed_on_both_sides_keeps_pick_one(store: Store) -> None:
    def artifact(data: bytes) -> Draft:
        return Draft("artifact", "a", title="blob", blobs={"content": data})

    found = store.put(OPERATOR, artifact(b"base"), on=MAIN, expected_head=None)
    edit(store, ALICE, found.object_id, artifact(b"alice"), "a")
    edit(store, BOB, found.object_id, artifact(b"bob"), "a")
    store.merge(ALICE, "a", from_ref=agent_ref("alice", "a"), into=drafts_ref("a"))

    merged = store.merge(BOB, "a", from_ref=agent_ref("bob", "a"), into=drafts_ref("a"))

    assert merged.outcome == "conflict"
    (conflict,) = store.conflicts(OPERATOR, "a")
    assert conflict.fields["entries"] == [{"path": "blobs.content"}]
    theirs = store.get(OPERATOR, str(conflict.fields["theirs"])).blobs["content"].blob_id

    resolved = store.resolve_conflict(ALICE, conflict.object_id, values={"blobs.content": theirs})

    assert store.get(OPERATOR, resolved.object_id, blobs="fetch").data["content"] == b"bob"


def test_blame_names_the_version_that_last_changed_each_line(store: Store) -> None:
    found = store.put(OPERATOR, note("one\ntwo\nthree\n"), on=MAIN, expected_head=None)
    item = found.item
    second = edit(store, ALICE, found.object_id, note("one\nTWO\nthree\n"), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    blamed = store.blame(BOB, item, "body.md", drafts_ref(item))

    assert [line.text for line in blamed.lines] == ["one", "TWO", "three"]
    assert [line.object_id for line in blamed.lines] == [
        found.object_id,
        second,
        found.object_id,
    ]
    assert [line.principal for line in blamed.lines] == [
        "operator",
        "agent:alice",
        "operator",
    ]
    assert [line.number for line in blamed.lines] == [1, 2, 3]


def test_history_lists_every_move_of_the_item(store: Store) -> None:
    found = store.put(OPERATOR, note("one\n"), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, note("two\n"), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    moved = store.history_of(OPERATOR, item)

    assert [(entry.ref, entry.principal) for entry in moved] == [
        (MAIN, "operator"),
        (agent_ref("alice", item), "agent:alice"),
        (drafts_ref(item), "agent:alice"),
    ]
    assert moved[1].prev_head is None
    assert [entry.new_head for entry in moved][:2] == [found.object_id, moved[1].new_head]
    assert len(store.history_of(OPERATOR, item, drafts_ref(item))) == 1


def test_resolve_refuses_a_conflict_it_cannot_close(store: Store) -> None:
    found = store.put(OPERATOR, note("one\ntwo\n"), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, note("one\nTWO\n"), item)
    edit(store, BOB, found.object_id, note("one\n2\n"), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))
    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))
    assert merged.outcome == "conflict"

    with pytest.raises(
        LibraryRefused, match=r"^merge_conflict: .* needs a value for blobs\.body\.md"
    ):
        store.resolve_conflict(BOB, merged.object_id)

    closed = store.resolve_conflict(BOB, merged.object_id, text="one\ntwo\n")
    with pytest.raises(LibraryRefused, match=r"^merge_conflict: .*already resolved"):
        store.resolve_conflict(BOB, merged.object_id, text="again\n")
    assert store.conflicts(OPERATOR, item) == []
    assert body(store, closed.object_id) == "one\ntwo\n"


@pytest.mark.parametrize(
    ("theirs", "outcome", "text"),
    [
        ("stop: 20 pips\n\nexit: 3R\n", "merged", "stop: 15 pips\n\nexit: 3R\n"),
        (
            "stop: 25 pips\n\nexit: 2R\n",
            "conflict",
            "<<<<<<< ours\nstop: 15 pips\n||||||| base\nstop: 20 pips\n=======\n"
            "stop: 25 pips\n>>>>>>> theirs\n\nexit: 2R\n",
        ),
    ],
)
def test_p_merge_cases_through_the_store(
    store: Store, theirs: str, outcome: str, text: str
) -> None:
    """git merge-file calls edits on adjacent lines one clash, so the two lines sit apart."""
    found = store.put(OPERATOR, note("stop: 20 pips\n\nexit: 2R\n"), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, note("stop: 15 pips\n\nexit: 2R\n"), item)
    edit(store, BOB, found.object_id, note(theirs), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    assert merged.outcome == outcome
    if outcome == "merged":
        assert body(store, merged.object_id) == text
    else:
        conflict = store.get(OPERATOR, merged.object_id)
        (entry,) = cast(list[dict[str, Any]], conflict.fields["entries"])
        assert (entry["text"], entry["conflicts"]) == (text, 1)


def test_a_resolve_keeps_the_clean_changes_of_both_sides(store: Store) -> None:
    found = store.put(OPERATOR, note("one\ntwo\n"), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, note("one\nTWO\n"), item)
    renamed = Draft("note", item, title="renamed", blobs={"body.md": b"one\n2\n"})
    edit(store, BOB, found.object_id, renamed, item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))
    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    closed = store.resolve_conflict(ALICE, merged.object_id, text="one\nTWO\n")

    landed = store.get(OPERATOR, closed.object_id)
    assert (landed.title, body(store, closed.object_id)) == ("renamed", "one\nTWO\n")


def test_a_json_merge_keeps_a_null_and_a_deleted_key(store: Store) -> None:
    found = store.put(OPERATOR, setup({"a": 0, "b": 0, "c": 0}), on=MAIN, expected_head=None)
    item = found.item
    edit(store, ALICE, found.object_id, setup({"a": None, "b": 0, "c": 0}, item), item)
    edit(store, BOB, found.object_id, setup({"a": 0, "b": 0}, item), item)
    store.merge(ALICE, item, from_ref=agent_ref("alice", item), into=drafts_ref(item))

    merged = store.merge(BOB, item, from_ref=agent_ref("bob", item), into=drafts_ref(item))

    assert merged.outcome == "merged"
    spec = json.loads(store.get(OPERATOR, merged.object_id, blobs="fetch").data["spec"])
    assert spec == {"a": None, "b": 0}
