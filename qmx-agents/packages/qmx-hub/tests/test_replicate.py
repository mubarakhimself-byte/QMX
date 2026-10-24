"""Replication: parent-hash order, ref ownership from the setting, the alarm instead of a
merge, the selective sync that copies text slots only, and a mirror refused for a ref the server
owns (Library AD-10, AD-11, AD-14, AD-19, AD-26)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.client import OwnerTable, Ref, owners, primary
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.replicate import Plan, StorePeer, order, plan, sync, sync_since
from qmx_hub.server import Hub

OPERATOR = Principal("operator")
RUN = Principal("run", "r1")


@pytest.fixture
def pair(tmp_path: Path) -> Iterator[tuple[Store, Store]]:
    with (
        Store.open(tmp_path / "pc", redactor=redact, name="pc") as pc,
        Store.open(tmp_path / "server", redactor=redact, name="server", role="replica") as hub,
    ):
        yield pc, hub


@pytest.fixture
def primary_server(tmp_path: Path) -> Iterator[tuple[Store, Store]]:
    """The PC as a replica and the server as the one writer: the state DR2D's flip creates."""
    with (
        Store.open(tmp_path / "pc", redactor=redact, name="pc", role="replica") as pc,
        Store.open(tmp_path / "server", redactor=redact, name="server") as server,
    ):
        yield pc, server


def note(title: str, item: str, *, parents: list[str] | None = None) -> Draft:
    return Draft("note", item, title=title, parents=parents)


def test_a_child_never_copies_before_its_parent() -> None:
    parent = "fp1:sha256:" + "a" * 64
    child = "fp1:sha256:" + "b" * 64
    grandchild = "fp1:sha256:" + "c" * 64
    shuffled = {child: [parent], grandchild: [child], parent: []}

    assert order(shuffled) == [parent, child, grandchild]


def test_a_sync_copies_objects_in_parent_order_and_mirrors_the_owners_ref(
    pair: tuple[Store, Store],
) -> None:
    pc, hub = pair
    first = pc.put(OPERATOR, note("one", "n1"), on="main", expected_head=None)
    second = pc.put(
        OPERATOR,
        Draft("note", "n1", title="two", parents=[first.object_id]),
        on="main",
        expected_head=first.object_id,
    )

    done = sync(StorePeer(pc), StorePeer(hub), OwnerTable("pc"))

    assert done.ok
    assert done.pushed == [first.object_id, second.object_id]
    assert hub.head("n1", "main") == (second.object_id, 1)
    assert hub.get(OPERATOR, second.object_id).title == "two"


def test_the_owner_table_is_read_from_the_setting(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "settings.toml").write_text('[library]\nprimary = "pc"\n', encoding="utf-8")
    before = owners(home)

    (home / "settings.toml").write_text('[library]\nprimary = "server"\n', encoding="utf-8")
    after = owners(home)

    assert before.owner("main") == "pc"
    assert after.owner("main") == "server"
    assert after.owner("refs/drafts/brief") == "server"
    assert after.owner("refs/hub/health") == "server"
    assert after.owner("refs/runs/r1") == "either"
    assert primary(home) == "server"


def test_the_owner_wins_either_way() -> None:
    local = [Ref("n1", "main", "bbb", "", "operator")]
    remote = [Ref("n1", "main", "aaa", "", "operator")]

    def behind(older: str, newer: str) -> bool:
        return older == "aaa"

    pushed = plan(local, remote, OwnerTable("pc"), name="pc", ancestor=behind)
    mirrored = plan(local, remote, OwnerTable("server"), name="pc", ancestor=behind)

    assert [row.head for row in pushed.push] == ["bbb"]
    assert pushed.mirror == ()
    assert mirrored.push == ()
    assert [row.head for row in mirrored.mirror] == ["aaa"]


def test_a_push_of_a_ref_this_store_owns_is_fast_forward_only() -> None:
    here = Ref("n1", "main", "new", "", "operator")
    there = Ref("n1", "main", "old", "", "operator")

    def one_step(older: str, newer: str) -> bool:
        return older == "old" and newer == "new"

    def never(older: str, newer: str) -> bool:
        return False

    forwards = plan([here], [there], OwnerTable("pc"), name="pc", ancestor=one_step)
    stranded = plan([here], [there], OwnerTable("pc"), name="pc", ancestor=never)

    assert [row.head for row in forwards.push] == ["new"]
    assert stranded.push == ()
    assert stranded.alarms == (
        "n1 main: old is not an ancestor of new; a push of an owned ref is fast-forward only",
    )


def test_a_run_ref_that_diverged_is_an_alarm_not_a_merge() -> None:
    here = Ref("r1", "refs/runs/r1", "aaa")
    there = Ref("r1", "refs/runs/r1", "bbb")

    routes = plan([here], [there], OwnerTable("server"), name="pc", ancestor=lambda _a, _b: False)

    assert isinstance(routes, Plan)
    assert (routes.push, routes.mirror) == ((), ())
    assert routes.alarms == ("r1 refs/runs/r1: aaa and bbb have no ancestry",)


def test_a_mirror_refuses_a_head_the_caller_did_not_read(pair: tuple[Store, Store]) -> None:
    pc, hub = pair
    first = pc.put(OPERATOR, note("one", "n1"), on="main", expected_head=None)
    sync(StorePeer(pc), StorePeer(hub), OwnerTable("pc"))
    second = pc.put(OPERATOR, note("two", "n1"), on="main", expected_head=first.object_id)

    with pytest.raises(LibraryRefused, match=r"^stale_head:"):
        hub.mirror("n1", "main", second.object_id, expected_head=None)


def test_a_selective_sync_copies_text_slots_and_no_other_blob(
    primary_server: tuple[Store, Store],
) -> None:
    pc, server = primary_server
    done = server.put(
        OPERATOR,
        Draft(
            "source",
            "paper",
            title="A paper",
            blobs={"transcript": b"the phrase only the server extracted", "content": b"\x00pdf"},
        ),
        on="main",
        expected_head=None,
    )

    synced = sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=0)

    view = pc.get(OPERATOR, done.object_id)
    assert synced.ok
    assert (synced.text_blobs, len(synced.pulled)) == (1, 1)
    assert pc.has_blob(view.blobs["transcript"].blob_id)
    assert not pc.has_blob(view.blobs["content"].blob_id)
    assert [hit.object_id for hit in pc.search(OPERATOR, "extracted")] == [done.object_id]


def test_a_selective_sync_asks_only_for_the_moves_after_its_cursor(
    primary_server: tuple[Store, Store],
) -> None:
    pc, server = primary_server
    server.put(OPERATOR, note("one", "n1"), on="main", expected_head=None)
    first = sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=0)
    second = server.put(OPERATOR, note("two", "n2"), on="main", expected_head=None)

    synced = sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=first.cursor)

    assert (len(first.pulled), len(synced.pulled)) == (1, 1)
    assert synced.pulled == [second.object_id]
    assert synced.cursor == 2


def test_the_server_refuses_a_mirror_of_a_ref_it_owns(tmp_path: Path) -> None:
    head = "fp1:sha256:" + "a" * 64
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        writer = Hub(store, home=tmp_path / "home")
        with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
            writer.op("mirror", OPERATOR, {"item": "n1", "ref": "main", "head": head})
    with Store.open(tmp_path / "replica", redactor=redact, name="server", role="replica") as store:
        replica = Hub(store, home=tmp_path / "home")
        replica.op("mirror", OPERATOR, {"item": "n1", "ref": "main", "head": head})
        assert store.head("n1", "main") == (head, 1)


def test_a_sync_learns_the_peers_higher_epoch_and_parks_the_pcs_own_move(
    tmp_path: Path,
) -> None:
    """A PC restored at `primary = pc` syncs with the server that is primary at epoch 2."""
    with (
        Store.open(tmp_path / "pc", redactor=redact, name="pc") as pc,
        Store.open(tmp_path / "server", redactor=redact, name="server") as server,
    ):
        pc.record_primary(OPERATOR, "pc")
        offline = pc.put(OPERATOR, note("offline", "n1"), on="main", expected_head=None)
        server.record_primary(OPERATOR, "server", epoch=2)
        theirs = server.put(
            OPERATOR, note("the server's own", "shared"), on="main", expected_head=None
        )

        synced = sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=0)

        learned = pc.epoch
        assert learned is not None
        assert (learned.primary, learned.epoch, learned.stale) == ("server", 2, True)
        assert learned.parked == ("refs/conflicts/n1/1",)
        parked = pc.get(OPERATOR, pc.resolve(OPERATOR, "n1", "refs/conflicts/n1/1"))
        assert parked.fields["ours"] == offline.object_id
        assert pc.alarms == ("library:epoch:pc",)
        assert synced.pushed_refs == []
        assert any("library:epoch:pc" in alarm for alarm in synced.alarms)
        assert server.head("shared", "main") == (theirs.object_id, 1)
        assert pc.head("n1", "main") == (offline.object_id, 1)
        with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
            pc.put(OPERATOR, note("after", "n1"), on="main", expected_head=offline.object_id)

        again = sync_since(
            StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=synced.cursor
        )

        assert (pc.epoch, again.pushed_refs) == (learned, [])
