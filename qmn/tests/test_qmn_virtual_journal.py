"""Provider-free CT-13 persistence and recovery for the binding virtual ledger."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmf.core import (
    Fingerprint,
    Instant,
    Money,
    Ok,
    PriceDelta,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    VenueId,
    WriterId,
    fingerprint,
    is_ok,
)
from qmf.core.exact import Instrument, Quantity
from qmf.core.fingerprint import World
from qmf.data import JournalAppendReceipt, JournalEvent, JournalReader, JournalWriter
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.engines.jsonl import jsonl_opener
from qmf.risk.r_faces import RFaces
from qmn.ledger import (
    AttributedFill,
    QmfEntryReservationJournal,
    QmfVirtualLedgerJournal,
    seed_binding_ledger,
)
from qmn.ledger.virtual import VirtualPositionStatus

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(label: str) -> Fingerprint:
    return _ok(fingerprint({"label": label}))


def _at(value: int) -> Instant:
    return _ok(Instant.try_create(value))


def _quantity(value: int) -> Quantity:
    return _ok(Quantity.try_create(value, "lot", 0))


def _store(path: Path) -> JournalStore:
    return JournalStore(World.LIVE, journal_dir=path, open_stream=jsonl_opener())


def _adapter(store: JournalStore, boot: str) -> QmfVirtualLedgerJournal:
    writer = _ok(WriterId.try_create("node-test", "risk", "virtual-ledger", boot))
    return _ok(
        QmfVirtualLedgerJournal.resume(
            store,
            writer,
            stream_name="binding-virtual-ledger",
            instant=lambda: _at(100),
        )
    )


def _reservation_journal(store: JournalStore, boot: str) -> QmfEntryReservationJournal:
    writer = _ok(WriterId.try_create("node-test", "risk", "entry-reservations", boot))
    return _ok(
        QmfEntryReservationJournal.resume(
            store,
            writer,
            stream_name="binding-entry-reservations",
            instant=lambda: _at(200),
        )
    )


def _faces() -> RFaces:
    instrument = _ok(Instrument.try_create(_ok(VenueId.try_create("ctrader")), "EURUSD"))
    distance = _ok(PriceDelta.try_create(50, instrument, 5))
    return _ok(RFaces.try_create(distance, _ok(Money.try_create(50_000, "USD", 2))))


def test_partial_entry_close_survives_checked_ct13_restart(tmp_path: Path) -> None:
    epoch = _fp("binding-epoch")
    command = _fp("entry-command")
    admission = _fp("admission")
    first_store = _store(tmp_path)
    first_journal = _adapter(first_store, "boot-1")
    first_recovery = _ok(first_journal.recover(epoch))
    first_reservations = _reservation_journal(first_store, "boot-1")
    reservation_recovery = _ok(first_reservations.recover(epoch))
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(100_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=first_journal,
            virtual_ledger_recovery=first_recovery,
            reservation_journal=first_reservations,
            reservation_recovery=reservation_recovery,
        )
    )
    _ok(ledger.reserve_entry("EURUSD", command))
    first = _ok(
        ledger.fold_fill(
            fill=AttributedFill(
                command,
                "deal-1",
                "EURUSD",
                _quantity(2),
                _ok(Money.try_create(100, "USD", 2)),
                _at(2),
            ),
            bot_id="bot-a",
            admission_identity=admission,
            faces=_faces(),
            admitted_quantity=_quantity(5),
            entry_terminal=False,
        )
    )
    assert ledger.has_pending_entry("EURUSD")
    terminal = _ok(
        ledger.fold_fill(
            fill=AttributedFill(
                command,
                "deal-2",
                "EURUSD",
                _quantity(1),
                _ok(Money.try_create(-250, "USD", 2)),
                _at(3),
            ),
            bot_id="bot-a",
            admission_identity=admission,
            faces=_faces(),
            admitted_quantity=_quantity(5),
            entry_terminal=True,
        )
    )
    assert terminal.position.position_ref == first.position.position_ref
    assert terminal.position.filled_quantity == _quantity(3)
    assert terminal.position.rebased is True
    assert not ledger.has_pending_entry("EURUSD")
    assert terminal.position.faces.original_risk_amount == _ok(Money.try_create(30_000, "USD", 2))
    _ok(
        ledger.close_position(
            instrument="EURUSD",
            realized_cash=_ok(Money.try_create(-2_000, "USD", 2)),
            recorded_at=_at(4),
            command_identity=_fp("exit-command"),
        )
    )
    first_store.close()

    second_store = _store(tmp_path)
    second_journal = _adapter(second_store, "boot-2")
    recovered = _ok(second_journal.recover(epoch))
    second_reservations = _reservation_journal(second_store, "boot-2")
    recovered_reservations = _ok(second_reservations.recover(epoch))
    reopened = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(100_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=second_journal,
            virtual_ledger_recovery=recovered,
            reservation_journal=second_reservations,
            reservation_recovery=recovered_reservations,
        )
    )
    position = reopened.position_for("EURUSD")
    assert position is not None
    assert position.status is VirtualPositionStatus.CLOSED
    assert position.position_ref == terminal.position.position_ref
    assert position.filled_quantity == _quantity(3)
    assert position.faces.original_risk_amount == _ok(Money.try_create(30_000, "USD", 2))
    assert reopened.realized_cash == _ok(Money.try_create(97_850, "USD", 2))
    assert not reopened.has_pending_entry("EURUSD")
    assert [record.sequence for record in reopened.records] == [1, 2, 3, 4]
    next_command = _fp("boot-two-entry")
    _ok(reopened.reserve_entry("EURUSD", next_command))
    _ok(
        reopened.fold_fill(
            fill=AttributedFill(
                next_command,
                "deal-boot-two",
                "EURUSD",
                _quantity(1),
                None,
                _at(5),
            ),
            bot_id="bot-b",
            admission_identity=_fp("boot-two-admission"),
            faces=_faces(),
            admitted_quantity=_quantity(1),
            entry_terminal=True,
        )
    )
    assert reopened.records[-1].sequence == 5
    checked_rows = _ok(
        JournalReader(second_store).read_checked("binding-virtual-ledger", for_world=World.LIVE)
    )
    assert len(checked_rows) == 5
    assert checked_rows[-1].sequence == 0
    assert checked_rows[-1].writer.boot_epoch_id == "boot-2"
    outer = checked_rows[-1].payload
    persisted_row = cast("Mapping[str, object]", outer["row"])
    persisted_record = cast("Mapping[str, object]", persisted_row["record"])
    assert persisted_record["sequence"] == 5
    second_store.close()


def test_missing_physical_ack_keeps_fill_state_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    epoch = _fp("ack-binding")
    store = _store(tmp_path)
    journal = _adapter(store, "boot-1")
    recovery = _ok(journal.recover(epoch))
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=journal,
            virtual_ledger_recovery=recovery,
        )
    )

    def missing_ack(
        _writer: JournalWriter, *_args: object, **_kwargs: object
    ) -> Result[JournalAppendReceipt]:
        return cast("Result[JournalAppendReceipt]", Ok(None))

    monkeypatch.setattr(JournalWriter, "record", missing_ack)
    refused = ledger.fold_fill(
        fill=AttributedFill(_fp("ack-command"), "deal", "EURUSD", _quantity(1), None, _at(2)),
        bot_id="bot-a",
        admission_identity=_fp("ack-admission"),
        faces=_faces(),
        admitted_quantity=_quantity(1),
        entry_terminal=True,
    )
    assert not is_ok(refused)
    assert len(ledger.records) == 1
    assert ledger.position_for("EURUSD") is None
    assert ledger.records[0].sequence == 1
    retry_blocked = ledger.fold_fill(
        fill=AttributedFill(_fp("ack-command"), "deal", "EURUSD", _quantity(1), None, _at(2)),
        bot_id="bot-a",
        admission_identity=_fp("ack-admission"),
        faces=_faces(),
        admitted_quantity=_quantity(1),
        entry_terminal=True,
    )
    assert not is_ok(retry_blocked)
    monkeypatch.undo()
    _ok(ledger.recover_virtual_ledger(_ok(journal.recover(epoch))))
    _ok(
        ledger.fold_fill(
            fill=AttributedFill(_fp("ack-command"), "deal", "EURUSD", _quantity(1), None, _at(2)),
            bot_id="bot-a",
            admission_identity=_fp("ack-admission"),
            faces=_faces(),
            admitted_quantity=_quantity(1),
            entry_terminal=True,
        )
    )
    assert len(ledger.records) == 2
    assert ledger.position_for("EURUSD") is not None
    store.close()


def test_committed_fill_with_lost_readback_reconciles_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    epoch = _fp("readback-binding")
    command = _fp("readback-command")
    fill = AttributedFill(command, "deal-once", "EURUSD", _quantity(1), None, _at(2))
    store = _store(tmp_path)
    journal = _adapter(store, "boot-1")
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=journal,
            virtual_ledger_recovery=_ok(journal.recover(epoch)),
        )
    )
    original = JournalReader.read_checked

    def lose_virtual_readback(
        reader: JournalReader,
        stream_name: object,
        *,
        for_world: object,
        expected_start: int | None = None,
    ) -> Result[list[JournalEvent]]:
        if stream_name == "binding-virtual-ledger":
            return cast(
                "Result[list[JournalEvent]]",
                TypedRefusal(
                    RefusalCategory.STORAGE_FAILURE,
                    Retryability.YES,
                    {"field": "virtual_ledger_journal"},
                ),
            )
        return original(
            reader,
            stream_name,
            for_world=for_world,
            expected_start=expected_start,
        )

    monkeypatch.setattr(JournalReader, "read_checked", lose_virtual_readback)
    refused = ledger.fold_fill(
        fill=fill,
        bot_id="bot-a",
        admission_identity=_fp("readback-admission"),
        faces=_faces(),
        admitted_quantity=_quantity(1),
        entry_terminal=True,
    )
    assert not is_ok(refused)
    assert len(ledger.records) == 1
    assert ledger.position_for("EURUSD") is None
    monkeypatch.undo()

    recovered = _ok(journal.recover(epoch))
    _ok(ledger.recover_virtual_ledger(recovered))
    duplicate = _ok(
        ledger.fold_fill(
            fill=fill,
            bot_id="bot-a",
            admission_identity=_fp("readback-admission"),
            faces=_faces(),
            admitted_quantity=_quantity(1),
            entry_terminal=True,
        )
    )
    assert duplicate.idempotent is True
    assert len(ledger.records) == 2
    position = ledger.position_for("EURUSD")
    assert position is not None
    assert position.filled_quantity == _quantity(1)
    store.close()


@pytest.mark.parametrize(
    "damage",
    [
        "engine",
        "format",
        "raw-fingerprint",
        "evidence-flag",
        "bool-sequence",
        "event-world",
        "event-writer",
        "event-bool-sequence",
        "event-correlation",
        "unexpected-edges",
    ],
)
def test_forged_physical_receipt_never_advances_virtual_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    epoch = _fp(f"receipt-{damage}-binding")
    command = _fp(f"receipt-{damage}-command")
    fill = AttributedFill(command, "deal-once", "EURUSD", _quantity(1), None, _at(2))
    store = _store(tmp_path)
    journal = _adapter(store, "boot-1")
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=journal,
            virtual_ledger_recovery=_ok(journal.recover(epoch)),
        )
    )
    original = JournalWriter.record

    def forged_record(
        writer: JournalWriter,
        event_type: object,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        outcome: object | None = None,
        correlation_id: object | None = None,
        display_time: object | None = None,
    ) -> Result[JournalAppendReceipt]:
        result = original(
            writer,
            event_type,
            payload,
            instant=instant,
            outcome=outcome,
            correlation_id=correlation_id,
            display_time=display_time,
        )
        if (
            writer.stream_name != "binding-virtual-ledger"
            or not is_ok(result)
            or payload is None
            or payload.get("class") != "qmn-binding-virtual-ledger-journal"
        ):
            return result
        physical = result.value.store_receipt
        assert isinstance(physical, StoreReceipt)
        changes: dict[str, object]
        if damage == "engine":
            changes = {"engine": "other"}
        elif damage == "format":
            changes = {"format_version": 2}
        elif damage == "raw-fingerprint":
            changes = {"fingerprint": f"fp1:sha256:{'0' * 64}"}
        elif damage == "evidence-flag":
            changes = {"is_evidence_bearing": 0}
        elif damage == "bool-sequence":
            changes = {"sequence": False}
        else:
            event_changes: dict[str, object]
            if damage == "event-world":
                event_changes = {"world": "live"}
            elif damage == "event-writer":
                event_changes = {"writer": None}
            elif damage == "event-correlation":
                event_changes = {"correlation_id": "foreign"}
            else:
                event_changes = {"sequence": True}
            if damage == "unexpected-edges":
                forged = replace(result.value, edge_receipts=(physical,))
                return cast("Result[JournalAppendReceipt]", Ok(forged))
            forged_event = replace(result.value.event, **event_changes)
            forged = replace(result.value, event=forged_event)
            return cast("Result[JournalAppendReceipt]", Ok(forged))
        forged = replace(result.value, store_receipt=replace(physical, **changes))
        return cast("Result[JournalAppendReceipt]", Ok(forged))

    monkeypatch.setattr(JournalWriter, "record", forged_record)
    refused = ledger.fold_fill(
        fill=fill,
        bot_id="bot-a",
        admission_identity=_fp(f"receipt-{damage}-admission"),
        faces=_faces(),
        admitted_quantity=_quantity(1),
        entry_terminal=True,
    )
    assert not is_ok(refused)
    assert len(ledger.records) == 1
    assert ledger.position_for("EURUSD") is None
    monkeypatch.undo()
    _ok(ledger.recover_virtual_ledger(_ok(journal.recover(epoch))))
    idempotent = _ok(
        ledger.fold_fill(
            fill=fill,
            bot_id="bot-a",
            admission_identity=_fp(f"receipt-{damage}-admission"),
            faces=_faces(),
            admitted_quantity=_quantity(1),
            entry_terminal=True,
        )
    )
    assert idempotent.idempotent is True
    assert len(ledger.records) == 2
    store.close()


def test_recovery_refuses_foreign_binding_epoch(tmp_path: Path) -> None:
    epoch = _fp("recovery-binding")
    store = _store(tmp_path)
    journal = _adapter(store, "boot-1")
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=journal,
            virtual_ledger_recovery=_ok(journal.recover(epoch)),
        )
    )
    _ok(
        ledger.fold_fill(
            fill=AttributedFill(
                _fp("recovery-command"), "deal", "EURUSD", _quantity(1), None, _at(2)
            ),
            bot_id="bot-a",
            admission_identity=_fp("recovery-admission"),
            faces=_faces(),
            admitted_quantity=_quantity(1),
            entry_terminal=True,
        )
    )
    refused = journal.recover(_fp("foreign-binding"))
    assert not is_ok(refused)
    store.close()


@pytest.mark.parametrize("append_reservation_before_refusal", [False, True])
def test_virtual_commit_reconciles_a_missing_reservation_terminal_after_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    append_reservation_before_refusal: bool,
) -> None:
    epoch, command = _fp("split-ack-binding"), _fp("split-ack-command")
    first_store = _store(tmp_path)
    virtual = _adapter(first_store, "boot-1")
    reservations = _reservation_journal(first_store, "boot-1")
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=virtual,
            virtual_ledger_recovery=_ok(virtual.recover(epoch)),
            reservation_journal=reservations,
            reservation_recovery=_ok(reservations.recover(epoch)),
        )
    )
    _ok(ledger.reserve_entry("EURUSD", command))
    original = JournalWriter.record

    def fail_filled_reservation(
        writer: JournalWriter,
        event_type: object,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        outcome: object | None = None,
        correlation_id: object | None = None,
        display_time: object | None = None,
    ) -> Result[JournalAppendReceipt]:
        reservation_payload = payload.get("reservation") if isinstance(payload, Mapping) else None
        if (
            writer.stream_name == "binding-entry-reservations"
            and isinstance(payload, Mapping)
            and payload.get("class") == "qmn-entry-reservation-journal"
            and isinstance(reservation_payload, Mapping)
            and cast("Mapping[str, object]", reservation_payload).get("event") == "filled"
        ):
            if append_reservation_before_refusal:
                original(
                    writer,
                    event_type,
                    payload,
                    instant=instant,
                    outcome=outcome,
                    correlation_id=correlation_id,
                    display_time=display_time,
                )
            return TypedRefusal(
                RefusalCategory.STORAGE_FAILURE,
                Retryability.YES,
                {"field": "reservation_journal"},
            )
        return original(
            writer,
            event_type,
            payload,
            instant=instant,
            outcome=outcome,
            correlation_id=correlation_id,
            display_time=display_time,
        )

    monkeypatch.setattr(JournalWriter, "record", fail_filled_reservation)
    outcome = ledger.fold_fill(
        fill=AttributedFill(command, "deal-1", "EURUSD", _quantity(1), None, _at(2)),
        bot_id="bot-a",
        admission_identity=_fp("split-ack-admission"),
        faces=_faces(),
        admitted_quantity=_quantity(1),
        entry_terminal=True,
    )
    assert not is_ok(outcome)
    assert ledger.position_for("EURUSD") is None
    assert ledger.has_pending_entry("EURUSD")
    first_store.close()
    monkeypatch.undo()

    second_store = _store(tmp_path)
    second_virtual = _adapter(second_store, "boot-2")
    second_reservations = _reservation_journal(second_store, "boot-2")
    recovered = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=_ok(Money.try_create(10_000, "USD", 2)),
            recorded_at=_at(1),
            virtual_ledger_journal=second_virtual,
            virtual_ledger_recovery=_ok(second_virtual.recover(epoch)),
            reservation_journal=second_reservations,
            reservation_recovery=_ok(second_reservations.recover(epoch)),
        )
    )
    assert not recovered.has_pending_entry("EURUSD")
    assert recovered.position_for("EURUSD") is not None
    assert len(recovered.records) == 2
    second_store.close()
