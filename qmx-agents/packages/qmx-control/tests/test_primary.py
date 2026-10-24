"""The flip is his click, and nothing else raises the epoch (MIGRATION step 8; AD-14, AD-19)."""

from __future__ import annotations

from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_hub.replicate import StorePeer, sync_since
from qmx_library.client import OwnerTable
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_control.primary import MOVE, Flip, lost_without_a_bucket, server_lost

OPERATOR = Principal("operator")
HUB = "http://100.64.0.2:18100"


def two_stores(root: Path) -> tuple[Store, Store]:
    return (
        Store.open(root / "pc", redactor=redact, name="pc"),
        Store.open(root / "server", redactor=redact, name="server"),
    )


def test_the_flip_without_his_click_leaves_the_epoch_alone(tmp_path: Path) -> None:
    pc, server = two_stores(tmp_path)
    with pc, server:
        flip = Flip(pc, StorePeer(server), tmp_path, HUB)
        card = flip.announce()
        saved = pc.put(
            OPERATOR,
            Draft("note", "a-note", title="before the move"),
            on="main",
            expected_head=None,
        )
        flip.quiesce()
        with pytest.raises(LibraryRefused, match="primary_moving"):
            flip.save(
                OPERATOR,
                Draft("note", "b-note", title="during the move"),
                on="main",
                expected_head=None,
            )
        flip.push_until_equal()
        assert (card.stage, card.button, card.title) == ("waiting", MOVE, MOVE)
        assert flip.equal() == ()
        assert flip.synced is not None
        assert flip.synced.pushed_refs == ["main"]
        assert pc.epoch is None
        assert server.head("a-note", "main") == (saved.object_id, 1)
        assert pc.head("a-note", "main") == (saved.object_id, 1)
        assert flip.card is not None and flip.card.stage == "waiting"


def test_his_click_raises_the_epoch_by_one_and_writes_the_setting(tmp_path: Path) -> None:
    pc, server = two_stores(tmp_path)
    with pc, server:
        flip = Flip(pc, StorePeer(server), tmp_path, HUB)
        flip.announce()
        pc.put(
            OPERATOR,
            Draft("note", "a-note", title="before the move"),
            on="main",
            expected_head=None,
        )
        flip.quiesce()
        flip.push_until_equal()
        with pytest.raises(LibraryRefused, match="ui_only"):
            flip.press(Principal("agent", "chat-1"))
        assert flip.press(OPERATOR).stage == "raised"
        learned = pc.epoch
        assert learned is not None
        assert (learned.primary, learned.epoch) == ("server", 1)
        settings = (tmp_path / "settings.toml").read_text(encoding="utf-8")
        assert '[library]\nprimary = "server"\nhub_url = "http://100.64.0.2:18100"' in settings
        assert flip.card is not None
        assert (flip.card.stage, flip.card.epoch) == ("raised", 1)


def test_what_is_lost_without_a_bucket_is_the_blob_never_opened(tmp_path: Path) -> None:
    pc, server = two_stores(tmp_path)
    with pc, server:
        opened = server.put(
            OPERATOR,
            Draft(
                "source",
                "opened",
                title="a document the PC opened",
                blobs={"content": b"bytes", "transcript": b"the words of the opened one"},
            ),
            on="main",
            expected_head=None,
        )
        unopened = server.put(
            OPERATOR,
            Draft(
                "source",
                "unopened",
                title="a document the PC never opened",
                blobs={"content": b"other bytes", "transcript": b"the words of the other one"},
            ),
            on="main",
            expected_head=None,
        )
        opened_blobs = server.get(OPERATOR, opened.object_id).blobs
        unopened_blobs = server.get(OPERATOR, unopened.object_id).blobs
        sync_since(StorePeer(pc), StorePeer(server), OwnerTable("pc"), cursor=0)
        data = server.read_blob(opened_blobs["content"].blob_id)
        assert data is not None
        pc.store_blob(data)
        lost = lost_without_a_bucket(pc)
        assert lost.blobs == (unopened_blobs["content"].blob_id,)
        assert lost.slots == ("content",)
        assert unopened_blobs["transcript"].blob_id not in lost.blobs
        assert pc.has_blob(unopened_blobs["transcript"].blob_id)
        assert lost.said.startswith(
            "blobs born on the server and never opened on the PC, now lost: 1 (content)"
        )


def test_the_old_host_is_asked_to_stop_before_the_pc_is_promoted(tmp_path: Path) -> None:
    pc, server = two_stores(tmp_path)
    with pc, server:
        pc.record_primary(OPERATOR, "server")
        recovery = server_lost(pc, who=OPERATOR, reachable=True)
        assert recovery.done == (1, 2, 3)
        assert recovery.steps[0].said.startswith("Stop the old host first")
        assert (recovery.epoch, recovery.steps[1].said) == (
            2,
            "refs the server owned that may be behind: 1; the inbox shows them",
        )
        learned = pc.epoch
        assert learned is not None
        assert (learned.primary, learned.epoch) == ("pc", 2)
        assert recovery.card is not None and recovery.card.stage == "lost"
        with pytest.raises(LibraryRefused, match="ui_only"):
            server_lost(pc, who=Principal("agent", "chat-1"))


def test_the_bucket_branch_rebuilds_and_re_pairs_while_step_four_waits(tmp_path: Path) -> None:
    pc, server = two_stores(tmp_path)
    with pc, server:
        recovery = server_lost(
            pc,
            who=OPERATOR,
            bucket=True,
            rebuild=lambda: {"restored": True, "objects": 3},
            repair=lambda: "paired",
        )
        assert recovery.done == (1, 2, 3, 5)
        assert recovery.steps[2].said == "{'restored': True, 'objects': 3}"
        assert recovery.steps[3].done is False
        assert recovery.steps[3].said.startswith("model keys, qmx/read/* and qmx/data/*")
        assert recovery.steps[4].said == "paired"
        assert recovery.lost is None
