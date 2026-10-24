"""The six `library` rows over the store: the six rows (AD-30)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, agent_ref

from qmx_control.catalog import control_rows
from qmx_control.service import ControlService

OPERATOR = Principal("operator")
ALICE = Principal("agent", "alice")
BOB = Principal("agent", "bob")
MARKED = "one\n<<<<<<< ours\nTWO\n||||||| base\ntwo\n=======\n2\n>>>>>>> theirs\n"


def note(text: str, item: str | None = None) -> Draft:
    return Draft("note", item, title="note", blobs={"body.md": text.encode()})


def edit(service: ControlService, who: Principal, base: str, text: str, item: str) -> str:
    return service.library.store.put(
        who,
        Draft("note", item, title="note", blobs={"body.md": text.encode()}, parents=[base]),
        on=agent_ref(str(who.id), item),
        expected_head=None,
    ).object_id


def test_the_six_library_rows_are_declared() -> None:
    rows = {row.name: row for row in control_rows() if row.toolset == "library"}
    expected = {
        "library_branch": ("domain_write", "POST", "/api/library/{artifact_id}/branch"),
        "library_merge": ("domain_write", "POST", "/api/library/{artifact_id}/merge"),
        "library_conflicts": ("read", "GET", "/api/library/conflicts"),
        "library_resolve": ("domain_write", "POST", "/api/library/{artifact_id}/resolve"),
        "library_history": ("read", "GET", "/api/library/{artifact_id}/history"),
        "library_blame": ("read", "GET", "/api/library/{artifact_id}/blame"),
    }
    found: dict[str, tuple[str, str, str]] = {}
    for name in expected:
        row = rows[name]
        assert row.rest is not None
        found[name] = (row.approval, row.rest.verb, row.rest.path)
    assert found == expected


def test_merge_lands_both_chats_edits_and_blame_names_each_line(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    store = service.library.store
    base = store.put(OPERATOR, note("one\ntwo\nthree\n"), on=MAIN, expected_head=None)
    item = base.item
    alice = edit(service, ALICE, base.object_id, "ONE\ntwo\nthree\n", item)
    bob = edit(service, BOB, base.object_id, "one\ntwo\nTHREE\n", item)

    first = service.library_merge(base.object_id, agent_ref("alice", item))
    merged = service.library_merge(base.object_id, agent_ref("bob", item))

    assert first["outcome"] == "fast-forward"
    assert merged["outcome"] == "merged"
    landed = store.get(OPERATOR, str(merged["object_id"]), blobs="fetch")
    assert landed.data["body.md"] == b"ONE\ntwo\nTHREE\n"
    assert landed.parents == (alice, bob)
    blamed = service.library_blame(str(merged["object_id"]), "body.md")
    assert [(line["number"], line["text"], line["principal"]) for line in blamed] == [
        (1, "ONE", "agent:alice"),
        (2, "two", "operator"),
        (3, "THREE", "agent:bob"),
    ]
    assert [line["object_id"] for line in blamed][1] == base.object_id
    moved = service.library_history(str(merged["object_id"]))
    assert [(entry["ref"], entry["principal"], entry["new_head"]) for entry in moved] == [
        ("main", "operator", base.object_id),
        (agent_ref("alice", item), "agent:alice", alice),
        (agent_ref("bob", item), "agent:bob", bob),
        ("main", "operator", alice),
        ("main", "operator", merged["object_id"]),
    ]
    assert moved[3]["reason"] == f"merge {agent_ref('alice', item)}"


def test_a_clashing_line_mints_one_conflict_and_resolve_closes_it(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    store = service.library.store
    base = store.put(OPERATOR, note("one\ntwo\n"), on=MAIN, expected_head=None)
    item = base.item
    alice = edit(service, ALICE, base.object_id, "one\nTWO\n", item)
    bob = edit(service, BOB, base.object_id, "one\n2\n", item)
    service.library_merge(base.object_id, agent_ref("alice", item))

    clashed = service.library_merge(base.object_id, agent_ref("bob", item))

    assert clashed["outcome"] == "conflict"
    (conflict,) = service.library_conflicts(base.object_id)
    assert {
        "id": conflict["id"],
        "item": conflict["item"],
        "into": conflict["into"],
        "base": conflict["base"],
        "ours": conflict["ours"],
        "theirs": conflict["theirs"],
    } == {
        "id": clashed["object_id"],
        "item": item,
        "into": "main",
        "base": base.object_id,
        "ours": alice,
        "theirs": bob,
    }
    (entry,) = cast(list[dict[str, Any]], conflict["entries"])
    assert entry["text"] == MARKED
    assert store.head(item, MAIN) is not None

    resolved = service.library_resolve(str(clashed["object_id"]), text="one\nTWO\n")

    assert resolved["outcome"] == "merged"
    assert service.library_conflicts(base.object_id) == []
    assert store.get(OPERATOR, str(resolved["object_id"]), blobs="fetch").data["body.md"] == (
        b"one\nTWO\n"
    )
    assert store.get(OPERATOR, str(resolved["object_id"])).parents == (alice, bob)
    assert [entry["new_head"] for entry in service.library_history(str(resolved["object_id"]))][
        -1
    ] == resolved["object_id"]
