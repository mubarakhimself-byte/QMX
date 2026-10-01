"""QMF CT-13 persistence for QMN entry reservations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmf.core import Instant, Ok, Result, World, WriterId, fingerprint, is_ok
from qmf.data import JournalAppendReceipt, JournalEventType, JournalReader, JournalWriter
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


def test_reservation_physical_sequence_spans_writer_boot_epochs(tmp_path: Path) -> None:
    epoch = _ok(fingerprint({"binding": "ct28-test"}))
    store_one = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_one = _ok(WriterId.try_create("node-test", "risk", "entry-reservations", "boot-1"))
    adapter_one = _ok(
        QmfEntryReservationJournal.resume(
            store_one,
            writer_one,
            stream_name="risk-reservations",
            instant=lambda: _ok(Instant.try_create(1_800_000_000_000_000_000)),
        )
    )
    first = EntryReservationEvent(
        binding_epoch=epoch,
        sequence=1,
        instrument="EURUSD",
        command_identity=_ok(fingerprint({"command": "first"})),
        event="reserved",
    )
    assert is_ok(adapter_one.append(first.as_mapping()))
    store_one.close()

    store_two = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_two = _ok(WriterId.try_create("node-test", "risk", "entry-reservations", "boot-2"))
    adapter_two = _ok(
        QmfEntryReservationJournal.resume(
            store_two,
            writer_two,
            stream_name="risk-reservations",
            instant=lambda: _ok(Instant.try_create(1_800_000_000_000_000_001)),
        )
    )
    second = EntryReservationEvent(
        binding_epoch=epoch,
        sequence=2,
        instrument="GBPUSD",
        command_identity=_ok(fingerprint({"command": "second"})),
        event="reserved",
    )

    appended = adapter_two.append(second.as_mapping())

    assert is_ok(appended)
    assert appended.value.detail["complete"] is True
    events = _ok(JournalReader(store_two).read_checked("risk-reservations", for_world=World.LIVE))
    assert len(events) == 2
    store_two.close()


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


@pytest.mark.parametrize("damage", ["event", "store_receipt", "sequence"])
def test_reservation_append_verifies_full_physical_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
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
    epoch = _ok(fingerprint({"binding": "ct28-test"}))
    identity = _ok(fingerprint({"command": "entry-test"}))
    reservation = EntryReservationEvent(
        binding_epoch=epoch,
        sequence=1,
        instrument="EURUSD",
        command_identity=identity,
        event="reserved",
    )
    original = cast("Callable[..., Result[JournalAppendReceipt]]", JournalWriter.record)

    def damaged_record(
        writer: JournalWriter, *args: object, **kwargs: object
    ) -> Result[JournalAppendReceipt]:
        result = original(writer, *args, **kwargs)
        assert is_ok(result)
        receipt = result.value
        if damage == "event":
            receipt = replace(receipt, event=None)  # type: ignore[arg-type]
        elif damage == "store_receipt":
            receipt = replace(receipt, store_receipt=None)  # type: ignore[arg-type]
        else:
            receipt = replace(
                receipt,
                store_receipt=replace(receipt.store_receipt, sequence=999),
            )
        return cast("Result[JournalAppendReceipt]", Ok(receipt))

    monkeypatch.setattr(JournalWriter, "record", damaged_record)

    refused = adapter.append(reservation.as_mapping())

    assert not is_ok(refused)
    assert refused.context["field"] == "reservation_journal"
    store.close()


def test_recovery_refuses_reservation_rows_from_an_unconfigured_writer(tmp_path: Path) -> None:
    rogue_store = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    rogue_writer_id = _ok(
        WriterId.try_create("rogue", "attacker", "entry-reservations", "boot-rogue")
    )
    rogue_writer = _ok(
        JournalWriter.resume(rogue_store, rogue_writer_id, stream_name="risk-reservations")
    )
    epoch = _ok(fingerprint({"binding": "ct28-test"}))
    identity = _ok(fingerprint({"command": "entry-test"}))
    reserved = EntryReservationEvent(
        binding_epoch=epoch,
        sequence=1,
        instrument="EURUSD",
        command_identity=identity,
        event="reserved",
    )
    _ok(
        rogue_writer.record(
            JournalEventType.DATA_QUALITY,
            {
                "class": "qmn-entry-reservation-journal",
                "reservation": dict(reserved.as_mapping()),
            },
            instant=_ok(Instant.try_create(1_800_000_000_000_000_000)),
        )
    )
    rogue_store.close()

    reopened = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    trusted_writer_id = _ok(
        WriterId.try_create("node-test", "risk", "entry-reservations", "boot-trusted")
    )
    adapter = _ok(
        QmfEntryReservationJournal.resume(
            reopened,
            trusted_writer_id,
            stream_name="risk-reservations",
            instant=lambda: _ok(Instant.try_create(1_800_000_000_000_000_000)),
        )
    )

    recovery = adapter.recover(epoch)

    assert not is_ok(recovery)
    assert recovery.context["field"] == "reservation_writer"
    reopened.close()
