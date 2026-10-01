"""CT-13 and CT-29 evidence must agree before a trade enters CT-32."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmb.results.ct29 import read_ct29_closed_trades
from qmb.results.measures import TradeSide
from qmf.core import (
    AccountRole,
    Fingerprint,
    Instant,
    Instrument,
    Money,
    PriceDelta,
    Result,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data import EvidenceStore, JournalReader, JournalWriter
from qmf.risk.exit_record import (
    CloseOutcome,
    CloseReason,
    ClosingAuthority,
    ExitRecord,
    ExitResultLabel,
    mint_exit_record,
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(label: str) -> Fingerprint:
    return _ok(fingerprint({"label": label}))


def _record(*, epoch: Fingerprint, at: Instant, pnl: int = 500) -> ExitRecord:
    delta = _ok(
        PriceDelta.try_create(10, Instrument(VenueId("test-venue"), "TEST"), 2)
    )
    amount = _ok(Money.try_create(10000, "USD", 2))
    realized = _ok(Money.try_create(pnl, "USD", 2))
    label = _ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY))
    made = mint_exit_record(
        virtual_position_ref=_fp("position-1"),
        opening_bot_id="bot-1",
        original_risk_distance=delta,
        original_risk_amount=amount,
        fill_references=(_fp("fill-1"),),
        realized_pnl=realized,
        cost_components=(),
        close_reason=CloseReason.TARGET_FILL,
        mechanism=CloseReason.TARGET_FILL,
        outcome=CloseOutcome.GAIN,
        closing_authority=ClosingAuthority.BOOK_POLICY,
        arbitration_record_ref=_fp("arb-1"),
        close_reason_mapping_version=1,
        result_label=label,
        loss_predicate_format_version=1,
        binding_epoch=epoch,
        recorded_at=at,
    )
    return _ok(made)


def _reader(tmp_path: Path, *, payload: dict[str, object], at: Instant):
    store = EvidenceStore(tmp_path)
    world_store = _ok(store.for_world(World.REPLAY))
    writer = _ok(WriterId.try_create("qmb", "replay", "closes", "boot-1"))
    journal_writer = JournalWriter(world_store.journal, writer, stream_name="closes")
    _ok(
        journal_writer.record(
            "risk transition", payload, instant=at, correlation_id="close-1"
        )
    )
    return JournalReader(world_store.journal), writer


def _context(*, epoch: Fingerprint, at: Instant) -> tuple[ExitRecord, ExitResultLabel]:
    return _record(epoch=epoch, at=at), _ok(
        ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY)
    )


def test_durable_ct29_close_projects_exact_trade_and_keeps_both_evidence_refs(
    tmp_path: Path,
) -> None:
    epoch = _fp("epoch-1")
    at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    record, label = _context(epoch=epoch, at=at)
    record_fp = _ok(record.fingerprint())
    reader, writer = _reader(
        tmp_path,
        payload={"exit_record_ref": record_fp.value, "binding_epoch": epoch.value},
        at=at,
    )

    projected = read_ct29_closed_trades(
        journal_reader=reader,
        stream_name="closes",
        writer=writer,
        record_resolver={record_fp.value: record},
        position_sides={record.virtual_position_ref.value: TradeSide.LONG},
        binding_epoch=epoch,
        result_label=label,
    )

    closes = _ok(projected)
    assert len(closes) == 1
    close = closes[0]
    assert close.record_fingerprint == record_fp
    assert close.closed_trade.realized_pnl == _ok(Money.try_create(500, "USD", 2))
    assert close.closed_trade.fees == _ok(Money.try_create(0, "USD", 2))
    assert close.closed_trade.side is TradeSide.LONG
    assert close.closed_trade.closed_at == at
    events = _ok(reader.read_checked("closes", for_world=World.REPLAY))
    assert close.journal_event_fingerprint == events[0].fingerprint


def test_missing_opening_side_refuses_without_inference(tmp_path: Path) -> None:
    epoch = _fp("epoch-1")
    at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    record, label = _context(epoch=epoch, at=at)
    record_fp = _ok(record.fingerprint())
    reader, writer = _reader(
        tmp_path,
        payload={"exit_record_ref": record_fp.value, "binding_epoch": epoch.value},
        at=at,
    )

    projected = read_ct29_closed_trades(
        journal_reader=reader,
        stream_name="closes",
        writer=writer,
        record_resolver={record_fp.value: record},
        position_sides={},
        binding_epoch=epoch,
        result_label=label,
    )

    assert is_refusal(projected)


def test_mismatched_ct29_fingerprint_refuses_tampered_resolution(tmp_path: Path) -> None:
    epoch = _fp("epoch-1")
    at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    record, label = _context(epoch=epoch, at=at)
    record_fp = _ok(record.fingerprint())
    reader, writer = _reader(
        tmp_path,
        payload={"exit_record_ref": record_fp.value, "binding_epoch": epoch.value},
        at=at,
    )
    altered = _record(epoch=epoch, at=at, pnl=501)

    projected = read_ct29_closed_trades(
        journal_reader=reader,
        stream_name="closes",
        writer=writer,
        record_resolver={record_fp.value: altered},
        position_sides={record.virtual_position_ref.value: TradeSide.SHORT},
        binding_epoch=epoch,
        result_label=label,
    )

    assert is_refusal(projected)


def test_conflicting_records_for_same_virtual_position_refuse(tmp_path: Path) -> None:
    epoch = _fp("epoch-1")
    at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    first, label = _context(epoch=epoch, at=at)
    second = _record(epoch=epoch, at=at, pnl=501)
    first_fp = _ok(first.fingerprint())
    second_fp = _ok(second.fingerprint())
    store = EvidenceStore(tmp_path)
    world_store = _ok(store.for_world(World.REPLAY))
    writer = _ok(WriterId.try_create("qmb", "replay", "closes", "boot-1"))
    journal_writer = JournalWriter(world_store.journal, writer, stream_name="closes")
    for record_fp in (first_fp, second_fp):
        _ok(
            journal_writer.record(
                "risk transition",
                {"exit_record_ref": record_fp.value, "binding_epoch": epoch.value},
                instant=at,
            )
        )

    projected = read_ct29_closed_trades(
        journal_reader=JournalReader(world_store.journal),
        stream_name="closes",
        writer=writer,
        record_resolver={first_fp.value: first, second_fp.value: second},
        position_sides={first.virtual_position_ref.value: TradeSide.LONG},
        binding_epoch=epoch,
        result_label=label,
    )

    assert is_refusal(projected)
