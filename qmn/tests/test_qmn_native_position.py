"""Native PID attribution requires checked CT-13 and CT-19 evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TypeVar

import pytest
from qmf.core import (
    Account,
    AccountRole,
    Fingerprint,
    Instrument,
    Money,
    Ok,
    PriceDelta,
    Quantity,
    Result,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import Instant
from qmf.data import JournalEventType, JournalWriter
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore, jsonl_opener
from qmf.risk.binding import PositionModel
from qmf.risk.paper import ExecutionTarget
from qmf.risk.r_faces import RFaces
from qmf.venue import CommandIdBinding, CommandIdBindingRegistry
from qmn.ledger import (
    AttributedFill,
    BindingVirtualLedger,
    NativePositionEvidence,
    VirtualPosition,
    resolve_native_position_attribution,
    seed_binding_ledger,
    write_native_position_attribution,
)
from qmn.order.identity import NativeExecutionMap, NativeExecutionMapping
from qmn.venue import CloseScope, Command, QmfCommandIdBindingJournal

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _writer(role: str, stream: str) -> WriterId:
    result = WriterId.try_create("native-fixture", role, stream, "boot-1")
    assert is_ok(result)
    return result.value


def _instant(ns: int) -> Instant:
    result = Instant.try_create(ns)
    assert is_ok(result)
    return result.value


def _fp(tag: str) -> Fingerprint:
    result = fingerprint({"fixture": tag})
    assert is_ok(result)
    return result.value


@dataclass(frozen=True, slots=True)
class _NativeFixture:
    journal: JournalStore
    binding_journal: QmfCommandIdBindingJournal
    command_binding: CommandIdBinding
    ledger: BindingVirtualLedger
    position: VirtualPosition
    target: ExecutionTarget
    instrument: Instrument
    binding_epoch: Fingerprint
    native_map: NativeExecutionMap
    evidence: NativePositionEvidence


def _native_fixture(tmp_path: Path) -> _NativeFixture:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    binding_writer = _writer("order", "command-id-bindings")
    binding_sink = QmfCommandIdBindingJournal.resume(
        journal,
        binding_writer,
        instant=lambda: Ok(_instant(100)),
        authorized_writers=(binding_writer,),
    )
    assert is_ok(binding_sink)
    registry = CommandIdBindingRegistry.try_create(binding_sink.value)
    assert is_ok(registry)

    target = _ok(
        ExecutionTarget.try_create(
            AccountRole.LIVE, _ok(VenueId.try_create("venue-native")), "acct-live"
        )
    )
    instrument = _ok(Instrument.try_create(target.venue_id, "EURUSD"))
    epoch = _fp("binding-epoch")
    account = _ok(Account.try_create(target.account_id, target.venue_id, target.role))
    command = _ok(
        Command.close_position(
            target.venue_id,
            account,
            "session-1",
            1,
            CloseScope.ACCOUNT_BINDING,
            "fixture-subject",
        )
    )
    command_fp = _ok(command.fingerprint())
    assert is_ok(
        registry.value.bind_before_submission(
            command, venue_client_id="client-77", injective_total=False
        )
    )
    command_binding = registry.value.binding_for("client-77")
    assert command_binding is not None

    money = _ok(Money.try_create(100_000, "USD", 2))
    distance = _ok(PriceDelta.try_create(50, instrument, 5))
    risk = _ok(RFaces.try_create(distance, _ok(Money.try_create(10_000, "USD", 2))))
    ledger = _ok(
        seed_binding_ledger(
            binding_epoch=epoch,
            seed=money,
            recorded_at=_instant(1),
        )
    )
    quantity = _ok(Quantity.try_create(1, "lot", 0))
    opened = _ok(
        ledger.fold_fill(
            fill=AttributedFill(
                command_identity=command_fp,
                venue_native_id="deal-20",
                instrument="EURUSD",
                quantity=quantity,
                realized_cash=None,
                recorded_at=_instant(2),
            ),
            bot_id="fixture-bot",
            admission_identity=_fp("admission"),
            faces=risk,
            admitted_quantity=quantity,
            entry_terminal=True,
        )
    )

    source_writer = _writer("venue", "native-observations")
    source = JournalWriter.resume(journal, source_writer, stream_name="native-observations")
    source_handle = _ok(source)
    lineage: dict[str, object] = {
        "positionId": 44,
        "accountId": 7,
        "symbolId": 3,
        "clientOrderId": "client-77",
        "orderId": 10,
        "dealId": 20,
        "sessionEpoch": "session-1",
    }
    fill = source_handle.record(
        JournalEventType.FILL,
        {"raw_payload": lineage},
        instant=_instant(3),
    )
    readback = source_handle.record(
        JournalEventType.DATA_QUALITY,
        {"raw_payload": {"positions": [lineage]}},
        instant=_instant(4),
    )
    fill_receipt = _ok(fill)
    readback_receipt = _ok(readback)
    evidence = NativePositionEvidence(
        fill_event=fill_receipt.event,
        readback_event=readback_receipt.event,
        fill_stream="native-observations",
        readback_stream="native-observations",
    )
    native_mapping = NativeExecutionMapping.try_create(
        target,
        instrument,
        native_account_id=7,
        native_symbol_id=3,
    )
    mapping_value = _ok(native_mapping)
    native_map = NativeExecutionMap.try_create(
        [mapping_value],
        registry_as_of_fingerprint=_fp("registry"),
        binding_epoch=epoch,
    )
    map_value = _ok(native_map)
    return _NativeFixture(
        journal=journal,
        binding_journal=binding_sink.value,
        command_binding=command_binding,
        ledger=ledger,
        position=opened.position,
        target=target,
        instrument=instrument,
        binding_epoch=epoch,
        native_map=map_value,
        evidence=evidence,
    )


def test_native_attribution_joins_durable_ct19_fill_readback_and_virtual_position(
    tmp_path: Path,
) -> None:
    fixture = _native_fixture(tmp_path)
    resolved = resolve_native_position_attribution(
        journal=fixture.journal,
        authorized_writers=(_writer("venue", "native-observations"),),
        evidence=fixture.evidence,
        command_binding=fixture.command_binding,
        command_binding_journal=fixture.binding_journal,
        ledger=fixture.ledger,
        position_ref=fixture.position.position_ref,
        target=fixture.target,
        instrument=fixture.instrument,
        native_map=fixture.native_map,
        binding_epoch=fixture.binding_epoch,
        composition_fp=_fp("composition"),
        position_model=PositionModel.HEDGING,
        binding_id="binding-1",
    )
    assert is_ok(resolved)
    assert resolved.value.native_position_id == "44"
    assert resolved.value.opening_command_fp1 == fixture.command_binding.command_fp1
    projection_writer = _writer("risk", "native-projections")
    projection = JournalWriter.resume(
        fixture.journal, projection_writer, stream_name="native-projections"
    )
    assert is_ok(projection)
    stored = write_native_position_attribution(
        journal=fixture.journal,
        writer=projection.value,
        instant=_instant(5),
        attribution=resolved.value,
    )
    assert is_ok(stored)
    fixture.journal.close()

    reopened = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    recovered_bind = QmfCommandIdBindingJournal.resume(
        reopened,
        _writer("order", "command-id-bindings"),
        instant=lambda: Ok(_instant(6)),
        authorized_writers=(_writer("order", "command-id-bindings"),),
    )
    assert is_ok(recovered_bind)
    assert is_ok(recovered_bind.value.binding_for("client-77"))
    rows = JournalReader(reopened).read_checked("native-projections", for_world=World.LIVE)
    assert is_ok(rows)
    assert len(rows.value) == 1
    assert rows.value[0].payload["class"] == "qmn-native-position-attribution"
    reopened.close()


def test_binding_record_sink_refuses_conflicting_rebind_and_unknown_ack_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_id = _writer("order", "command-id-bindings")
    sink = QmfCommandIdBindingJournal.resume(
        journal,
        writer_id,
        instant=lambda: Ok(_instant(10)),
        authorized_writers=(writer_id,),
    )
    assert is_ok(sink)
    first = CommandIdBinding("client-1", _fp("command-1"), "acct-live", "session-1")
    assert is_ok(sink.value.write(first))
    conflict = replace(first, command_fp1=_fp("command-2"))
    assert is_refusal(sink.value.write(conflict))
    journal.close()


def test_record_sink_unknown_ack_refuses_but_reopened_row_is_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_id = _writer("order", "command-id-bindings")
    sink = QmfCommandIdBindingJournal.resume(
        journal,
        writer_id,
        instant=lambda: Ok(_instant(20)),
        authorized_writers=(writer_id,),
    )
    assert is_ok(sink)
    first = CommandIdBinding("client-2", _fp("command-2"), "acct-live", "session-1")
    original = JournalWriter.record_control_action

    def append_then_hide_ack(
        self: JournalWriter,
        subtype: str,
        *,
        instant: Instant,
        payload: Mapping[str, object],
    ) -> object:
        actual = original(self, subtype, instant=instant, payload=payload)
        assert is_ok(actual)
        return Ok(None)

    monkeypatch.setattr(JournalWriter, "record_control_action", append_then_hide_ack)
    assert is_refusal(sink.value.write(first))
    journal.close()
    monkeypatch.undo()

    reopened = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    resumed = QmfCommandIdBindingJournal.resume(
        reopened,
        writer_id,
        instant=lambda: Ok(_instant(21)),
        authorized_writers=(writer_id,),
    )
    assert is_ok(resumed)
    recovered_binding = resumed.value.binding_for("client-2")
    assert is_ok(recovered_binding)
    assert recovered_binding.value == first
    reopened.close()


def test_fresh_binding_registry_uses_reopened_ct13_collision_authority(tmp_path: Path) -> None:
    fixture = _native_fixture(tmp_path)
    writer_id = _writer("order", "command-id-bindings")
    resumed_sink = _ok(
        QmfCommandIdBindingJournal.resume(
            fixture.journal,
            writer_id,
            instant=lambda: Ok(_instant(101)),
            authorized_writers=(writer_id,),
        )
    )
    fresh_registry = _ok(CommandIdBindingRegistry.try_create(resumed_sink))
    account = _ok(
        Account.try_create(fixture.target.account_id, fixture.target.venue_id, fixture.target.role)
    )
    original_command = _ok(
        Command.close_position(
            fixture.target.venue_id,
            account,
            "session-1",
            1,
            CloseScope.ACCOUNT_BINDING,
            "fixture-subject",
        )
    )
    same = fresh_registry.bind_before_submission(
        original_command,
        venue_client_id="client-77",
        injective_total=False,
    )
    assert is_ok(same)
    conflict_command = _ok(
        Command.close_position(
            fixture.target.venue_id,
            account,
            "session-1",
            2,
            CloseScope.ACCOUNT_BINDING,
            "different-subject",
        )
    )
    conflict = fresh_registry.bind_before_submission(
        conflict_command,
        venue_client_id="client-77",
        injective_total=False,
    )
    assert is_refusal(conflict)
