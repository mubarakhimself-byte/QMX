"""Book-owned order admission and exact replay risk sizing regressions."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar

import pytest
from qmb._refuse import storage
from qmb.config import (
    CLOCK_REPLAY,
    PROVENANCE_RECORDED,
    ResolvedRunConfig,
    mint_replay_binding,
)
from qmb.execution import (
    COST_ADAPTER_KEY,
    COST_ADAPTER_PER_LOT,
    COST_CALIBRATION_KEY,
    FILL_ADAPTER_DECLARED_PATH,
    FILL_ADAPTER_KEY,
    FILL_BASIS_KEY,
    FINANCING_SCHEDULE_KEY,
    SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    SLIPPAGE_ADAPTER_KEY,
    SLIPPAGE_CALIBRATION_KEY,
    CommissionCalibration,
    SlippageCalibration,
    bind_execution_ports,
)
from qmb.execution.fill import FILL_BASIS_OPTIMISTIC_EXACT, OrderType
from qmb.execution.ports import CostedFill, SlicePath
from qmb.host.book_handler import (
    BOOK_POSITION_CLASS,
    BookAdmissionContext,
    BookExecutionSliceHandler,
    BookOrderPolicy,
    ReplayPosition,
    derive_replay_quantity,
    read_replay_positions,
)
from qmb.results.measures import TradeSide
from qmf.core import (
    AccountRole,
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Money,
    Ok,
    Price,
    PriceDelta,
    Quantity,
    Result,
    UnitKind,
    ValueFactor,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data import EvidenceStore, JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.store import JournalStore, StoreReceipt
from qmf.risk.door import Direction, EntryIntent, ExitIntent, ExitKind, ExitLogicRef, ReasonCode
from qmf.risk.exit_record import CloseReason, ExitResultLabel
from qmf.risk.paper import ExecutionTarget
from qmf.risk.r_faces import RFaces
from qml.protocol import HostedBot

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instrument() -> Instrument:
    return Instrument(VenueId("replay-venue"), "EURUSD")


def _fp(label: str) -> Fingerprint:
    return _ok(fingerprint({"label": label}))


def _resolved() -> ResolvedRunConfig:
    commission = _ok(
        CommissionCalibration.try_create(
            COST_ADAPTER_PER_LOT,
            "replay-broker",
            currency="USD",
            per_lot=_ok(Money.try_create(100, "USD", 2)),
        )
    )
    slippage = _ok(
        SlippageCalibration.try_create(
            SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
            "replay-broker",
            percent=_ok(ExactRational.try_create(1, 10_000, UnitKind.DIMENSIONLESS_RATIO)),
        )
    )
    keys: dict[str, object] = {
        COST_ADAPTER_KEY: COST_ADAPTER_PER_LOT,
        COST_CALIBRATION_KEY: commission,
        FILL_ADAPTER_KEY: FILL_ADAPTER_DECLARED_PATH,
        FILL_BASIS_KEY: FILL_BASIS_OPTIMISTIC_EXACT,
        FINANCING_SCHEDULE_KEY: "replay-swap-table",
        SLIPPAGE_ADAPTER_KEY: SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
        SLIPPAGE_CALIBRATION_KEY: slippage,
    }
    book, bms, bot = _fp("book"), _fp("bms"), _fp("bot")
    seed = _ok(Money.try_create(1_000_000, "USD", 2))
    binding = _ok(
        mint_replay_binding(
            book_fp1=book,
            bms_fp1=bms,
            bot_fp1=bot,
            starting_capital=seed,
            seed_overridden=False,
            venue_id="replay-venue",
            account_id="account-1",
            clock=CLOCK_REPLAY,
            data_provenance=PROVENANCE_RECORDED,
            keys=keys,
        )
    )
    identity: dict[str, object] = {
        "book_fp1": book.value,
        "bms_fp1": bms.value,
        "bot_fp1": bot.value,
        "class": "resolved-run-config",
        "clock": CLOCK_REPLAY,
        "data_provenance": PROVENANCE_RECORDED,
        "keys": keys,
        "world": World.REPLAY.value,
    }
    return ResolvedRunConfig(
        format_version=1,
        book_fp1=book,
        bms_fp1=bms,
        bot_fp1=bot,
        book_fragment_fp1=_fp("book-fragment"),
        bms_fragment_fp1=_fp("bms-fragment"),
        keys=keys,
        clock=CLOCK_REPLAY,
        data_provenance=PROVENANCE_RECORDED,
        world=World.REPLAY,
        fingerprint=_ok(fingerprint(identity)),
        binding_fp1=binding.fingerprint,
        replay_binding=binding,
    )


class _OffsetStop:
    def derive_full_loss_price(
        self, *, entry_price: Price, direction: Direction, cited_evidence: object
    ) -> Result[Price]:
        del cited_evidence
        value = entry_price.value - 500 if direction is Direction.LONG else entry_price.value + 500
        return Price.try_create(value, entry_price.instrument, entry_price.scale)


class _ScriptedHostedBot(HostedBot):
    def __init__(self) -> None:
        self.proposals: tuple[EntryIntent | ExitIntent, ...] = ()

    def on_instant(self, instant: object, /) -> Result[tuple[EntryIntent | ExitIntent, ...]]:
        del instant
        return Ok(self.proposals)


def _price(value: int) -> Price:
    return _ok(Price.try_create(value, _instrument(), 5))


def _path(*values: int) -> SlicePath:
    return _ok(SlicePath.try_create("eurusd", tuple(_price(value) for value in values)))


def _handler(
    tmp_path: Path,
) -> tuple[BookExecutionSliceHandler, _ScriptedHostedBot, JournalReader, WriterId]:
    config = _resolved()
    bound = _ok(bind_execution_ports(config))
    binding = config.replay_binding
    assert binding is not None
    store = EvidenceStore(tmp_path)
    world_store = _ok(store.for_world(World.REPLAY))
    writer = _ok(WriterId.try_create("qmb", "replay", "positions", "boot-1"))
    journal_writer = JournalWriter(world_store.journal, writer, stream_name="positions")
    reader = JournalReader(world_store.journal)
    result_label = _ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY))
    recovery = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=binding.fingerprint,
            result_label=result_label,
            record_resolver={},
        )
    )
    target = _ok(ExecutionTarget.try_create("demo", VenueId("replay-venue"), "account-1"))
    policy_by_code = {
        "entry:family:breakout": BookOrderPolicy(OrderType.MARKET),
        "exit:family:target": BookOrderPolicy(OrderType.MARKET),
    }
    admission = _ok(
        BookAdmissionContext.try_create(
            binding=binding,
            exit_logic_ref=_ok(ExitLogicRef.try_create("book.stop", {})),
            exit_logic_module=_OffsetStop(),
            requested_r=_ok(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)),
            r_unit_price=_ok(ExactRational.try_create(100, 1, UnitKind.RATE)),
            value_factor=_ok(ValueFactor.try_create(20_000, 1, _instrument(), "USD")),
            money_scale=2,
            lot_step=_ok(Quantity.try_create(1, "lot", 0)),
            position_cap=_ok(Quantity.try_create(5, "lot", 0)),
            execution_target=target,
            result_label=result_label,
            opening_bot_id="bot-1",
            close_reason_by_code={"exit:family:target": CloseReason.TARGET_FILL},
            order_policy_by_code=policy_by_code,
            journal_writer=journal_writer,
        )
    )
    bot = _ScriptedHostedBot()
    handler = _ok(
        BookExecutionSliceHandler.try_create(
            hosted=bot,
            stream_id="eurusd",
            bound_execution=bound,
            admission=admission,
            recovery=recovery,
        )
    )
    return handler, bot, reader, writer


def test_risk_sizing_uses_exact_book_budget_and_refuses_lot_rounding() -> None:
    instrument = _instrument()
    distance = _ok(PriceDelta.try_create(100, instrument, 2))
    value_factor = _ok(ValueFactor.try_create(100, 1, instrument, "USD"))
    requested_r = _ok(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE))
    r_unit_price = _ok(ExactRational.try_create(100, 1, UnitKind.RATE))
    step = _ok(Quantity.try_create(1, "lot", 0))
    cap = _ok(Quantity.try_create(5, "lot", 0))

    sized = derive_replay_quantity(distance, requested_r, r_unit_price, value_factor, 2, step, cap)
    assert _ok(sized) == step

    fractional_step = _ok(Quantity.try_create(3, "lot", 0))
    assert is_refusal(
        derive_replay_quantity(
            distance,
            requested_r,
            r_unit_price,
            value_factor,
            2,
            fractional_step,
            cap,
        )
    )
    two_r = _ok(ExactRational.try_create(2, 1, UnitKind.R_MULTIPLE))
    one_lot_cap = _ok(Quantity.try_create(1, "lot", 0))
    assert is_refusal(
        derive_replay_quantity(distance, two_r, r_unit_price, value_factor, 2, step, one_lot_cap)
    )


def test_book_order_policy_materializes_only_explicit_order_semantics() -> None:
    instrument = _instrument()
    qty = _ok(Quantity.try_create(2, "lot", 0))
    step = _ok(Quantity.try_create(1, "lot", 0))
    target = Price.try_create(110_000, instrument, 5)
    assert is_ok(target)
    policy = BookOrderPolicy(OrderType.LIMIT, limit_price=target.value)

    order = _ok(
        policy.materialize(
            side=Direction.SHORT,
            quantity=qty,
            is_close=True,
            lot_step=step,
            position_quantity=qty,
            intent_id="ct23-exit-1",
        )
    )
    assert order.order_type is OrderType.LIMIT
    assert order.side is Direction.SHORT
    assert order.reduce_only is True
    assert order.quantity == qty
    assert order.position_quantity == qty
    assert order.intent_id == "ct23-exit-1"

    missing_limit = BookOrderPolicy(OrderType.LIMIT).materialize(
        side=Direction.LONG,
        quantity=qty,
        is_close=False,
        lot_step=step,
        position_quantity=None,
        intent_id="ct23-entry-1",
    )
    assert is_refusal(missing_limit)


def test_ct13_position_recovery_preserves_identity_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    label = _ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY))
    instant = _ok(Instant.try_create(1_700_000_000_000_000_000))
    instrument = _instrument()
    entry_price = _ok(Price.try_create(110_000, instrument, 5))
    quantity = _ok(Quantity.try_create(2, "lot", 0))
    distance = _ok(PriceDelta.try_create(100, instrument, 5))
    risk_amount = _ok(Money.try_create(200, "USD", 2))
    faces = _ok(RFaces.try_create(distance, risk_amount))
    epoch = _fp("epoch")
    admission = _fp("admission")
    command = _fp("command")
    fill_ref = _fp("entry-fill")
    body: dict[str, object] = {
        "admission_identity": admission.value,
        "binding_epoch": epoch.value,
        "class": BOOK_POSITION_CLASS,
        "command_identity": command.value,
        "direction": Direction.LONG.value,
        "entry_costs": [],
        "entry_fill_ref": fill_ref.value,
        "entry_price": entry_price.fp1_identity(),
        "faces": faces.fp1_identity(),
        "instrument": instrument.symbol,
        "opened_at": instant.fp1_identity(),
        "opening_bot_id": "bot-1",
        "quantity": quantity.fp1_identity(),
    }
    position_ref = _ok(fingerprint(body))
    position_identity = {**body, "position_ref": position_ref.value}

    store = EvidenceStore(tmp_path)
    world_store = _ok(store.for_world(World.REPLAY))
    writer = _ok(WriterId.try_create("qmb", "replay", "positions", "boot-1"))
    journal_writer = JournalWriter(world_store.journal, writer, stream_name="positions")
    _ok(
        journal_writer.record(
            "risk transition",
            {
                "binding_epoch": epoch.value,
                "replay_position": position_identity,
                "replay_position_ref": position_ref.value,
            },
            instant=instant,
        )
    )

    restored = _ok(
        read_replay_positions(
            journal_reader=JournalReader(world_store.journal),
            stream_name="positions",
            writer=writer,
            binding_epoch=epoch,
            result_label=label,
            record_resolver={},
        )
    )
    expected_position = ReplayPosition(
        position_ref=position_ref,
        binding_epoch=epoch,
        admission_identity=admission,
        command_identity=command,
        opening_bot_id="bot-1",
        instrument=instrument.symbol,
        direction=Direction.LONG,
        opened_at=instant,
        entry_price=entry_price,
        quantity=quantity,
        faces=faces,
        entry_fill_ref=fill_ref,
        entry_costs=(),
    )
    assert len(restored.positions) == 1
    assert restored.positions[0].fp1_identity() == expected_position.fp1_identity()

    tampered_store = EvidenceStore(tmp_path / "tampered")
    tampered_world = _ok(tampered_store.for_world(World.REPLAY))
    tampered_writer = JournalWriter(tampered_world.journal, writer, stream_name="positions")
    tampered_position = {**position_identity, "direction": Direction.SHORT.value}
    _ok(
        tampered_writer.record(
            "risk transition",
            {
                "binding_epoch": epoch.value,
                "replay_position": tampered_position,
                "replay_position_ref": position_ref.value,
            },
            instant=instant,
        )
    )
    assert is_refusal(
        read_replay_positions(
            journal_reader=JournalReader(tampered_world.journal),
            stream_name="positions",
            writer=writer,
            binding_epoch=epoch,
            result_label=label,
            record_resolver={},
        )
    )


def test_book_fill_close_and_ct13_reopen_use_actual_economics(tmp_path: Path) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    instant = _ok(Instant.try_create(1_700_000_000_000_000_000))
    target = _ok(ExecutionTarget.try_create("demo", VenueId("replay-venue"), "account-1"))
    entry = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            target,
        )
    )
    bot.proposals = (entry,)
    _ok(handler.bind_path(_path(110_000, 110_100, 109_900)))
    resting_entry = _ok(handler.mint_intents("eurusd", instant))
    entry_outcome = _ok(handler.execute_resting(resting_entry[0], None, instant))
    assert entry_outcome is True, handler.receipts[-1].fill
    entry_receipt = handler.receipts[-1]
    assert isinstance(entry_receipt.fill, CostedFill)
    assert entry_receipt.position is not None
    assert entry_receipt.fill.fill.pre_slip_price == _price(110_000)
    assert entry_receipt.fill.fill.post_slip_price is not None
    assert entry_receipt.fill.fill.post_slip_price.as_fraction() == _price(110_011).as_fraction()
    assert entry_receipt.position.entry_price == _price(110_011)
    assert entry_receipt.position.faces.original_risk_amount == _ok(
        Money.try_create(10_000, "USD", 2)
    )
    position = entry_receipt.position

    exit_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("target", "family")),
            position.position_ref,
        )
    )
    bot.proposals = (exit_intent,)
    close_at = _ok(Instant.try_create(instant.value_ns + 1_000_000_000))
    _ok(handler.bind_path(_path(110_000, 110_100, 109_800)))
    resting_exit = _ok(handler.mint_intents("eurusd", close_at))
    assert _ok(handler.execute_resting(resting_exit[0], None, close_at)) is True
    close_receipt = handler.receipts[-1]
    assert isinstance(close_receipt.fill, CostedFill)
    assert close_receipt.exit_record is not None
    record = close_receipt.exit_record
    assert record.realized_pnl == _ok(Money.try_create(-440, "USD", 2))
    assert _ok(record.net_realized_pnl()) == _ok(Money.try_create(-640, "USD", 2))
    assert _ok(record.realized_r()) == _ok(ExactRational.try_create(-8, 125, UnitKind.R_MULTIPLE))
    assert len(record.cost_components) == 1
    assert record.cost_components[0].amount == _ok(Money.try_create(200, "USD", 2))
    record_fp = _ok(record.fingerprint())

    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=position.binding_epoch,
            result_label=_ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY)),
        )
    )
    assert len(recovered.positions) == 1
    assert recovered.positions[0].closed is True
    assert recovered.positions[0].position_ref == position.position_ref
    assert recovered.record_resolver[record_fp.value].fp1_identity() == record.fp1_identity()
    assert recovered.position_sides[position.position_ref.value] is TradeSide.LONG

    tampered_store = EvidenceStore(tmp_path / "tampered-close")
    tampered_world = _ok(tampered_store.for_world(World.REPLAY))
    tampered_writer = JournalWriter(tampered_world.journal, writer, stream_name="positions")
    _ok(
        tampered_writer.record(
            "risk transition",
            {
                "binding_epoch": position.binding_epoch.value,
                "replay_position": position.fp1_identity(),
                "replay_position_ref": position.position_ref.value,
            },
            instant=instant,
        )
    )
    modified_record = record.fp1_identity()
    modified_record["realized_pnl"] = _ok(Money.try_create(-439, "USD", 2)).fp1_identity()
    _ok(
        tampered_writer.record(
            "risk transition",
            {
                "binding_epoch": position.binding_epoch.value,
                "exit_record": modified_record,
                "exit_record_ref": record_fp.value,
                "virtual_position_ref": position.position_ref.value,
            },
            instant=close_at,
        )
    )
    assert is_refusal(
        read_replay_positions(
            journal_reader=JournalReader(tampered_world.journal),
            stream_name="positions",
            writer=writer,
            binding_epoch=position.binding_epoch,
            result_label=_ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY)),
        )
    )

    bot.proposals = (exit_intent,)
    duplicate = _ok(handler.mint_intents("eurusd", close_at))
    assert is_refusal(handler.execute_resting(duplicate[0], None, close_at))


def test_unpersistable_open_does_not_advance_memory_and_recovers_from_ct13(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    instant = _ok(Instant.try_create(1_700_000_000_000_000_000))
    target = _ok(ExecutionTarget.try_create("demo", VenueId("replay-venue"), "account-1"))
    bot.proposals = (
        _ok(
            EntryIntent.try_create(
                _instrument(),
                Direction.LONG,
                _ok(ReasonCode.try_create("breakout", "family")),
                target,
            )
        ),
    )
    _ok(handler.bind_path(_path(110_000, 110_100, 109_900)))
    resting = _ok(handler.mint_intents("eurusd", instant))
    append = JournalStore.append
    failures = [1]

    def fail_first_append(
        self: JournalStore,
        stream_name: object,
        event_writer: WriterId,
        event: Mapping[str, object],
        *,
        presented_fingerprint: object = None,
    ) -> Result[StoreReceipt]:
        if failures[0]:
            failures[0] -= 1
            return storage("append", "injected uncertain durable append")
        return append(
            self,
            stream_name,
            event_writer,
            event,
            presented_fingerprint=presented_fingerprint,
        )

    monkeypatch.setattr(JournalStore, "append", fail_first_append)
    refused = handler.execute_resting(resting[0], None, instant)
    assert is_refusal(refused)
    assert handler.positions == ()
    assert handler.receipts == ()
    assert handler.admission.journal_writer.is_blocked is True
    assert handler.admission.journal_writer.next_sequence == 0

    monkeypatch.setattr(JournalStore, "append", append)
    retried = _ok(handler.admission.journal_writer.retry_blocked())
    assert isinstance(retried, JournalAppendReceipt)
    assert handler.positions == ()
    assert handler.admission.journal_writer.next_sequence == 1
    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=handler.admission.binding.fingerprint,
            result_label=handler.admission.result_label,
            record_resolver={},
        )
    )
    assert len(recovered.positions) == 1
    assert recovered.positions[0].closed is False
