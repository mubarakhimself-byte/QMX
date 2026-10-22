"""Replication: parent-hash order, ref ownership from the setting, and the alarm instead of a
merge (Library AD-10, AD-11, AD-14, AD-19)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.client import OwnerTable, Ref, owners, primary
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.replicate import Plan, StorePeer, order, plan, sync

OPERATOR = Principal("operator")
RUN = Principal("run", "r1")


@pytest.fixture
def pair(tmp_path: Path) -> Iterator[tuple[Store, Store]]:
    with (
        Store.open(tmp_path / "pc", redactor=redact, name="pc") as pc,
        Store.open(tmp_path / "server", redactor=redact, name="server", role="replica") as hub,
    ):
        yield pc, hub


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
    local = [Ref("n1", "main", "aaa", "", "operator")]
    remote = [Ref("n1", "main", "bbb", "", "operator")]

    pushed = plan(local, remote, OwnerTable("pc"), name="pc", ancestor=lambda _a, _b: False)
    mirrored = plan(local, remote, OwnerTable("server"), name="pc", ancestor=lambda _a, _b: False)

    assert [row.head for row in pushed.push] == ["aaa"]
    assert pushed.mirror == ()
    assert mirrored.push == ()
    assert [row.head for row in mirrored.mirror] == ["bbb"]


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
