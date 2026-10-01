"""QMF CT-13 persistence for QMN entry reservations."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmf.core import Instant, Result, World, WriterId, fingerprint, is_ok
from qmf.data import JournalReader
from qmf.data.store import JournalStore
from qmf.data.store.engines.jsonl import jsonl_opener
from qmn.ledger import EntryReservationEvent
from qmn.ledger.reservation_journal import QmfEntryReservationJournal

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_reservation_transition_recovers_from_checked_ct13_stream(tmp_path: Path) -> None:
    store = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_id = _ok(WriterId.try_create("node-test", "risk", "entry-reservations", "boot-1"))
    epoch = _ok(fingerprint({"binding": "ct28-test"}))
    identity = _ok(fingerprint({"command": "entry-test"}))
    adapter = _ok(
        QmfEntryReservationJournal.resume(
            store,
            writer_id,
            stream_name="risk-reservations",
            instant=lambda: _ok(Instant.try_create(1_800_000_000_000_000_000)),
        )
    )
    reserved = EntryReservationEvent(
        binding_epoch=epoch,
        sequence=1,
        instrument="EURUSD",
        command_identity=identity,
        event="reserved",
    )

    assert is_ok(adapter.append(reserved.as_mapping()))
    recovery = _ok(adapter.recover(epoch))
    assert recovery.complete is True
    assert recovery.committed_high_water == 1
    assert recovery.events == (reserved,)
    assert is_ok(JournalReader(store).read_checked("risk-reservations", for_world=World.LIVE))
    store.close()


def test_reservation_adapter_rejects_untyped_input(tmp_path: Path) -> None:
    store = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_id = _ok(WriterId.try_create("node-test", "risk", "entry-reservations", "boot-1"))
    adapter = _ok(
        QmfEntryReservationJournal.resume(
            store,
            writer_id,
            stream_name="risk-reservations",
            instant=lambda: _ok(Instant.try_create(1_800_000_000_000_000_000)),
        )
    )
    assert not is_ok(adapter.append({"class": "not-a-reservation"}))
    assert not is_ok(adapter.recover("opaque epoch"))
    store.close()
