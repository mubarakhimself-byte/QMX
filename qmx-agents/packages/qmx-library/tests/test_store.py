"""The Library's rules, through its port: ref ownership, the landing rule per class, redaction at
put, archive instead of delete, content identity, and indexes rebuilt from evidence."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Literal

import pytest
from qmx_engine.ledger import redact

from qmx_library.landing import land
from qmx_library.port import BlobRef, Draft, LibraryPort, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
ALICE = Principal("agent", "alice")
BOB = Principal("agent", "bob")
RUN = Principal("run", "r1")
PLANTED = "sk-or-" + "v1-" + "e5" * 32


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def note(text: str, item: str | None = None) -> Draft:
    return Draft("note", item, title=text, blobs={"body.md": text.encode()})


def workflow(name: str, item: str) -> Draft:
    definition = json.dumps({"id": item, "name": name}).encode()
    return Draft("workflow", item, title=name, blobs={"definition": definition})


def test_each_agent_writes_only_its_own_ref(store: Store) -> None:
    base = store.put(
        OPERATOR, workflow("Brief", "brief"), on="refs/drafts/brief", expected_head=None
    )
    edit = workflow("Brief, Alice's", "brief")
    alice = store.put(
        ALICE,
        replace(edit, parents=[base.object_id]),
        on="refs/agents/alice/brief",
        expected_head=None,
    )
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.put(BOB, workflow("Brief, Bob's", "brief"), on="refs/agents/alice/brief",
                  expected_head=alice.object_id)  # fmt: skip
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.put(BOB, workflow("Brief, Bob's", "brief"), on="refs/drafts/brief",
                  expected_head=base.object_id)  # fmt: skip
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.put(RUN, note("a result"), on="main", expected_head=None)
    merged = store.merge(
        ALICE, "brief", from_ref="refs/agents/alice/brief", into="refs/drafts/brief"
    )

    assert (alice.ref, merged.outcome) == ("refs/agents/alice/brief", "fast-forward")
    assert store.resolve(OPERATOR, "brief", "refs/drafts/brief") == alice.object_id


def test_a_stale_head_is_refused_and_an_identical_put_is_one_object(store: Store) -> None:
    first = store.put(OPERATOR, note("same", "n1"), on="main", expected_head=None)
    with pytest.raises(LibraryRefused, match=r"^stale_head:"):
        store.put(OPERATOR, note("other", "n1"), on="main", expected_head=None)
    again = store.put(OPERATOR, note("same", "n2"), on="main", expected_head=None)
    twin = store.put(OPERATOR, note("same", "n2"), on="refs/variants/x", expected_head=None)

    assert first.object_id.startswith("fp1:sha256:")
    assert twin.object_id == again.object_id != first.object_id


def test_a_passed_live_run_lands_records_on_main_and_definitions_on_drafts(store: Store) -> None:
    result = store.put(RUN, note("the answer", "result"), on="refs/runs/r1", expected_head=None)
    made = store.put(RUN, workflow("Made by a run", "made"), on="refs/runs/r1", expected_head=None)

    landed = land(store, "r1", mode="live", status="passed")

    assert sorted((x.item, x.into, x.result.outcome) for x in landed) == [
        ("made", "refs/drafts/made", "fast-forward"),
        ("result", "main", "fast-forward"),
    ]
    assert store.resolve(OPERATOR, "result") == result.object_id
    assert store.resolve(OPERATOR, "made", "refs/drafts/made") == made.object_id
    with pytest.raises(LibraryRefused, match=r"^not_found:"):
        store.resolve(OPERATOR, "made", "main")


@pytest.mark.parametrize(
    ("mode", "status", "publish"),
    [("test", "passed", "auto"), ("live", "failed", "auto"), ("live", "passed", "hold")],
)
def test_records_stay_off_main_unless_a_live_run_passed_under_auto(
    store: Store, mode: Literal["live", "test"], status: str, publish: str
) -> None:
    store.put(RUN, note("garbage or clean", "result"), on="refs/runs/r1", expected_head=None)

    land(store, "r1", mode=mode, status=status, publish=publish)

    assert store.head("result", "main") is None


def test_the_engine_never_lands_a_definition_on_main(store: Store) -> None:
    store.put(RUN, workflow("Made", "made"), on="refs/runs/r1", expected_head=None)
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.merge(store.engine, "made", from_ref="refs/runs/r1", into="main")


def test_every_put_is_redacted_and_a_binary_secret_is_refused(store: Store) -> None:
    draft = Draft(
        "artifact",
        "a1",
        title=f"key {PLANTED}",
        fields={"type": "log", "metadata": {"env": f"KEY={PLANTED}"}},
        blobs={"content": f"Authorization: Bearer {PLANTED}\n".encode()},
    )
    stored = store.put(RUN, draft, on="refs/runs/r1", expected_head=None)
    view = store.get(RUN, stored.object_id, blobs="fetch")
    evidence = ("objects", "blobs", "refs", "edges", "annotations")
    on_disk = b"".join(
        p.read_bytes() for d in evidence for p in (store.root / d).rglob("*") if p.is_file()
    )
    redact.register("lane", "binary-" + "e5" * 16)
    with pytest.raises(LibraryRefused, match=r"^secret_in_blob:"):
        store.put(RUN, Draft("artifact", "a2", blobs={"content": b"\xff\x00binary-" + b"e5" * 16}),
                  on="refs/runs/r1", expected_head=None)  # fmt: skip

    assert PLANTED not in json.dumps(view.fields) + view.title
    assert PLANTED.encode() not in view.data["content"]
    assert PLANTED.encode() not in on_disk


def test_there_is_no_delete_and_archive_only_hides(store: Store) -> None:
    kept = store.put(OPERATOR, note("old plan", "plan"), on="main", expected_head=None)
    store.archive(OPERATOR, "plan", "superseded")
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.archive(ALICE, "plan", "mine now")

    verbs = {name for name in dir(LibraryPort) if not name.startswith("_")}
    assert not verbs & {"delete", "remove", "purge", "drop"}
    assert not any(hasattr(store, name) for name in ("delete", "remove", "purge"))
    assert store.search(OPERATOR, "old plan") == []
    assert [h.object_id for h in store.search(OPERATOR, "old plan", include_archived=True)] == [
        kept.object_id
    ]
    assert store.get(OPERATOR, kept.object_id).title == "old plan"


def test_a_three_way_merge_takes_both_sides_and_a_clash_becomes_a_conflict(store: Store) -> None:
    base = store.put(
        OPERATOR, Draft("note", "n", title="t", fields={"a": 1, "b": 1}), on="main",
        expected_head=None,
    )  # fmt: skip
    store.branch(OPERATOR, "n", from_ref="main", name="refs/variants/v")
    store.put(OPERATOR, Draft("note", "n", title="t", fields={"a": 2, "b": 1}), on="main",
              expected_head=base.object_id)  # fmt: skip
    theirs = store.put(OPERATOR, Draft("note", "n", title="t", fields={"a": 1, "b": 3}),
                       on="refs/variants/v", expected_head=base.object_id)  # fmt: skip
    merged = store.merge(OPERATOR, "n", from_ref="refs/variants/v", into="main")
    view = store.get(OPERATOR, merged.object_id)
    store.put(OPERATOR, Draft("note", "n", title="t", fields={"a": 9, "b": 3},
              parents=[theirs.object_id]), on="refs/variants/v",
              expected_head=theirs.object_id)  # fmt: skip
    store.put(OPERATOR, Draft("note", "n", title="t", fields={"a": 7, "b": 3}), on="main",
              expected_head=merged.object_id)  # fmt: skip
    clash = store.merge(OPERATOR, "n", from_ref="refs/variants/v", into="main")
    conflict = store.get(OPERATOR, clash.object_id)

    assert (merged.outcome, view.fields) == ("merged", {"a": 2, "b": 3})
    assert ("merged-from", theirs.object_id) in view.relations
    assert (clash.outcome, conflict.kind, conflict.fields["entries"]) == (
        "conflict",
        "merge-conflict",
        [{"path": "fields.a"}],
    )


def test_indexes_rebuild_from_evidence_with_the_same_answers(tmp_path: Path) -> None:
    root = tmp_path / "library"
    with Store.open(root, redactor=redact) as store:
        for n in range(5):
            store.put(OPERATOR, note(f"momentum study {n}", f"s{n}"), on="main", expected_head=None)
        store.annotate(OPERATOR, store.resolve(OPERATOR, "s3"), {"tags": ["breakout"]})
        before = store.search(OPERATOR, "momentum study")
        tagged = store.search(OPERATOR, "breakout")
    for name in ("catalog.db", "catalog.db-wal", "catalog.db-shm"):
        (root / name).unlink(missing_ok=True)
    with Store.open(root, redactor=redact) as store:
        after = store.search(OPERATOR, "momentum study")

        assert [h.item for h in tagged] == ["s3"]
        assert after == before and len(after) == 5
        assert store.search(OPERATOR, "breakout") == tagged


def test_one_process_writes_a_store(tmp_path: Path) -> None:
    with (
        Store.open(tmp_path / "library", redactor=redact),
        pytest.raises(LibraryRefused, match=r"^storage_failure:"),
    ):
        Store.open(tmp_path / "library", redactor=redact)


def test_an_agent_checks_out_into_its_own_ref_and_commits_there(store: Store) -> None:
    base = store.put(OPERATOR, note("v1", "doc"), on="refs/drafts/doc", expected_head=None)
    folder = store.checkout(ALICE, "doc", "refs/drafts/doc")
    (folder / "blobs" / "body.md").write_bytes(b"v2 by alice")
    done = store.commit(ALICE, folder, "edit")
    view = store.get(ALICE, done.object_id, blobs="fetch")

    assert (done.ref, view.parents, view.data["body.md"]) == (
        "refs/agents/alice/doc",
        (base.object_id,),
        b"v2 by alice",
    )
    assert store.resolve(OPERATOR, "doc", "refs/drafts/doc") == base.object_id


def test_a_kind_is_data_and_an_unknown_or_retired_kind_is_refused(store: Store) -> None:
    for kind in ("no-such-kind", "bot-card"):
        with pytest.raises(LibraryRefused, match=r"^unknown_kind:"):
            store.put(OPERATOR, Draft(kind, "x"), on="main", expected_head=None)
    with pytest.raises(LibraryRefused, match=r"^schema_invalid:"):
        store.put(OPERATOR, Draft("workflow", "w"), on="refs/drafts/w", expected_head=None)
    kinds = sorted(p.name for p in (store.root / "kinds").iterdir())

    assert len(kinds) == 38 and "workflow.schema.json" in kinds


def test_a_blob_ref_reuses_stored_bytes(store: Store) -> None:
    first = store.put(OPERATOR, note("shared body", "a"), on="main", expected_head=None)
    blob = store.get(OPERATOR, first.object_id).blobs["body.md"].blob_id
    second = store.put(OPERATOR, Draft("note", "b", blobs={"body.md": BlobRef(blob)}), on="main",
                       expected_head=None)  # fmt: skip

    assert store.get(OPERATOR, second.object_id, blobs="fetch").data["body.md"] == b"shared body"
