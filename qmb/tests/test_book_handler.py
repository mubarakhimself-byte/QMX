"""Book-owned order admission and exact replay risk sizing regressions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
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
    FINANCING_CALIBRATION_KEY,
    FINANCING_SCHEDULE_KEY,
    SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    SLIPPAGE_ADAPTER_KEY,
    SLIPPAGE_CALIBRATION_KEY,
    CommissionCalibration,
    SlippageCalibration,
    bind_execution_ports,
)
from qmb.execution.fill import FILL_BASIS_OPTIMISTIC_EXACT, OrderType
from qmb.execution.financing import SwapCalibration, SwapRate
from qmb.execution.ports import CostedFill, SlicePath
from qmb.host.book_handler import (
    BOOK_POSITION_CLASS,
    BookAdmissionContext,
    BookExecutionSliceHandler,
    BookOrderPolicy,
    EntryTerminalReason,
    ReplayPosition,
    derive_replay_quantity,
    read_replay_positions,
)
from qmb.results.measures import TradeSide
from qmb.runloop.loop import ExecutionDisposition, SliceObservation, run
from qmf.core import (
    AccountRole,
    CalendarIdentity,
    CivilDate,
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
    TradingDate,
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


def _resolved(financing_calibration: SwapCalibration | None = None) -> ResolvedRunConfig:
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
    if financing_calibration is not None:
        keys[FINANCING_CALIBRATION_KEY] = financing_calibration
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
        self.responses: tuple[tuple[EntryIntent | ExitIntent, ...], ...] | None = None
        self.calls = 0

    def on_instant(self, instant: object, /) -> Result[tuple[EntryIntent | ExitIntent, ...]]:
        del instant
        if self.responses is not None:
            response = self.responses[min(self.calls, len(self.responses) - 1)]
            self.calls += 1
            return Ok(response)
        return Ok(self.proposals)


class _NeverRolloverCalendar:
    def is_rollover_instant(self, instant: Instant) -> Result[bool]:
        del instant
        return Ok(False)

    def trading_date_of(self, instant: Instant) -> Result[TradingDate]:
        del instant
        return storage("calendar", "unexpected trading-date lookup in non-rollover fixture")

    def weekday_of(self, trading_date: TradingDate) -> Result[str]:
        del trading_date
        return storage("calendar", "unexpected weekday lookup in non-rollover fixture")

    def is_weekend_or_holiday(self, trading_date: TradingDate) -> Result[bool]:
        del trading_date
        return storage("calendar", "unexpected holiday lookup in non-rollover fixture")


@dataclass(frozen=True, slots=True)
class _RecordedRolloverCalendar:
    rollover_ns: int
    trading_date: TradingDate

    def is_rollover_instant(self, instant: Instant) -> Result[bool]:
        return Ok(instant.value_ns == self.rollover_ns)

    def trading_date_of(self, instant: Instant) -> Result[TradingDate]:
        del instant
        return Ok(self.trading_date)

    def weekday_of(self, trading_date: TradingDate) -> Result[str]:
        del trading_date
        return Ok("monday")

    def is_weekend_or_holiday(self, trading_date: TradingDate) -> Result[bool]:
        del trading_date
        return Ok(False)


def _price(value: int) -> Price:
    return _ok(Price.try_create(value, _instrument(), 5))


def _path(*values: int) -> SlicePath:
    return _ok(SlicePath.try_create("eurusd", tuple(_price(value) for value in values)))


def _quote_path(*values: int, bid: int, ask: int) -> SlicePath:
    return _ok(
        SlicePath.try_create(
            "eurusd",
            tuple(_price(value) for value in values),
            bid=_price(bid),
            ask=_price(ask),
        )
    )


def _handler(
    tmp_path: Path,
    *,
    financing_calibration: SwapCalibration | None = None,
    rollover_calendar: object | None = None,
) -> tuple[BookExecutionSliceHandler, _ScriptedHostedBot, JournalReader, WriterId]:
    config = _resolved(financing_calibration)
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
        "exit:family:protective_stop": BookOrderPolicy(OrderType.STOP, stop_price=_price(109_500)),
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
            close_reason_by_code={
                "exit:family:target": CloseReason.TARGET_FILL,
                "exit:family:protective_stop": CloseReason.PROTECTIVE_STOP_FILL,
            },
            order_policy_by_code=policy_by_code,
            journal_writer=journal_writer,
            rollover_calendar=rollover_calendar or _NeverRolloverCalendar(),
            protective_stop_reason=_ok(ReasonCode.try_create("protective_stop", "family")),
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
        "protective_stop": _price(105_000).fp1_identity(),
        "entry_terminal_reason": EntryTerminalReason.REPLAY_COMPLETE.value,
        "declared_plan_quantity": quantity.fp1_identity(),
        "declared_plan_risk_amount": risk_amount.fp1_identity(),
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
        protective_stop=_price(105_000),
        entry_terminal_reason=EntryTerminalReason.REPLAY_COMPLETE,
        quantity=quantity,
        faces=faces,
        entry_fill_ref=fill_ref,
        entry_costs=(),
        declared_plan_quantity=quantity,
        declared_plan_risk_amount=risk_amount,
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
    close_at = _ok(Instant.try_create(instant.value_ns + 1_000_000_000))
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
    _ok(
        handler.bind_paths(
            (
                (instant, _path(110_000, 110_100, 109_900)),
                (close_at, _path(110_000, 110_100, 109_800)),
            )
        )
    )
    resting_entry = _ok(handler.mint_intents("eurusd", instant))
    entry_outcome = _ok(handler.execute_resting(resting_entry[0], None, instant))
    assert entry_outcome == ExecutionDisposition(filled=True, terminal=True), handler.receipts[
        -1
    ].fill
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


def test_partial_entry_no_fill_later_fill_rebases_once_and_reopens(tmp_path: Path) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    rules = dict(handler.admission.order_policy_by_code)
    rules["entry:family:breakout"] = BookOrderPolicy(
        OrderType.MARKET, liquidity=_ok(Quantity.try_create(2, "lot", 0))
    )
    handler.admission = replace(
        handler.admission,
        requested_r=_ok(ExactRational.try_create(5, 1, UnitKind.R_MULTIPLE)),
        order_policy_by_code=MappingProxyType(rules),
    )
    target = handler.admission.execution_target
    proposal = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            target,
        )
    )
    t0 = _ok(Instant.try_create(1_700_000_000_000_000_000))
    t1 = _ok(Instant.try_create(t0.value_ns + 1_000_000_000))
    t2 = _ok(Instant.try_create(t0.value_ns + 2_000_000_000))
    bot.proposals = (proposal,)

    _ok(handler.bind_path(_path(110_000, 110_100, 109_900)))
    first = _ok(handler.mint_intents("eurusd", t0))[0]
    assert _ok(handler.execute_resting(first, None, t0)) == ExecutionDisposition(True, False)
    assert len(handler.pending_entry_tickets) == 1
    ticket = handler.pending_entry_tickets[0]
    assert is_refusal(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=handler.admission.binding.fingerprint,
            result_label=handler.admission.result_label,
        )
    )

    closed_path = _ok(SlicePath.try_create("eurusd", (_price(110_000),), market_closed=True))
    _ok(handler.bind_path(closed_path))
    no_fill = _ok(handler.mint_intents("eurusd", t1))[0]
    assert _ok(handler.execute_resting(no_fill, None, t1)) == ExecutionDisposition(False, False)
    assert handler.pending_entry_tickets == (ticket,)

    _ok(handler.bind_path(_path(110_000, 110_100, 109_900)))
    later = _ok(handler.mint_intents("eurusd", t2))[0]
    assert _ok(handler.execute_resting(later, None, t2)) == ExecutionDisposition(True, False)
    assert handler.positions == ()
    finalized = _ok(
        handler.finalize_entry(ticket, at=t2, terminal_reason=EntryTerminalReason.REPLAY_COMPLETE)
    )
    assert finalized.quantity == _ok(Quantity.try_create(4, "lot", 0))
    assert finalized.declared_plan_quantity == _ok(Quantity.try_create(5, "lot", 0))
    assert finalized.declared_plan_risk_amount == _ok(Money.try_create(50_000, "USD", 2))
    assert finalized.faces.original_risk_amount == _ok(Money.try_create(400, "USD", 0))
    assert finalized.risk_rebased is True
    assert finalized.risk_rebase_lineage is not None
    assert len(finalized.entry_fills) == 2
    assert handler.pending_entry_tickets == ()

    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=finalized.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert recovered.positions[0].fp1_identity() == finalized.fp1_identity()
    assert recovered.positions[0].risk_rebased is True


def test_cancelled_partial_entry_rebases_and_reopens_once(tmp_path: Path) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    rules = dict(handler.admission.order_policy_by_code)
    rules["entry:family:breakout"] = BookOrderPolicy(
        OrderType.MARKET, liquidity=_ok(Quantity.try_create(2, "lot", 0))
    )
    handler.admission = replace(
        handler.admission,
        requested_r=_ok(ExactRational.try_create(5, 1, UnitKind.R_MULTIPLE)),
        order_policy_by_code=MappingProxyType(rules),
    )
    proposal = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            handler.admission.execution_target,
        )
    )
    bot.proposals = (proposal,)
    instant = _ok(Instant.try_create(1_700_000_000_000_000_000))
    _ok(handler.bind_path(_path(110_000, 110_100, 109_900)))
    resting = _ok(handler.mint_intents("eurusd", instant))[0]
    assert _ok(handler.execute_resting(resting, None, instant)) == ExecutionDisposition(True, False)

    position = _ok(handler.cancel_pending_entries(at=instant))[0]
    assert position.quantity == _ok(Quantity.try_create(2, "lot", 0))
    assert position.faces.original_risk_amount == _ok(Money.try_create(200, "USD", 0))
    assert position.risk_rebased is True
    assert position.entry_terminal_reason is EntryTerminalReason.CANCELLED
    reopened = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=position.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert reopened.positions[0].fp1_identity() == position.fp1_identity()
    sequence = handler.admission.journal_writer.next_sequence
    assert _ok(handler.cancel_pending_entries(at=instant)) == ()
    assert handler.admission.journal_writer.next_sequence == sequence
    assert handler.finalized_resting_intent_ids == (resting.intent_id,)


def test_recorded_rollover_financing_is_journaled_and_netted_at_close(tmp_path: Path) -> None:
    rollover = _ok(Instant.try_create(1_700_000_000_001_000_000))
    trading_date = _ok(
        TradingDate.try_create(
            _ok(CalendarIdentity.try_create("broker-hours", "v1", "2026a")),
            _ok(CivilDate.try_create(2026, 10, 5)),
        )
    )
    calendar = _RecordedRolloverCalendar(rollover.value_ns, trading_date)
    rate = _ok(SwapRate.try_create("eurusd", Direction.LONG, _ok(Money.try_create(-100, "USD", 2))))
    calibration = _ok(
        SwapCalibration.try_create(
            "replay-broker",
            rates=(rate,),
            weekend_holiday_handling="skip",
            calendar_identity=calendar.trading_date.calendar.fp1_identity(),
        )
    )
    handler, bot, reader, writer = _handler(
        tmp_path,
        financing_calibration=calibration,
        rollover_calendar=calendar,
    )
    target = handler.admission.execution_target
    entry = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            target,
        )
    )
    opened_at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    bot.proposals = (entry,)
    _ok(
        handler.bind_paths(
            (
                (opened_at, _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001)),
                (rollover, _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001)),
            )
        )
    )
    resting = _ok(handler.mint_intents("eurusd", opened_at))[0]
    assert _ok(handler.execute_resting(resting, None, opened_at)) == ExecutionDisposition(
        True, True
    )
    position = handler.positions[0]

    _ok(handler.scheduled_position_event("eurusd", opened_at))
    assert handler.admission.journal_writer.next_sequence == 1
    _ok(handler.scheduled_position_event("eurusd", rollover))
    assert handler.admission.journal_writer.next_sequence == 2
    assert len(handler.positions[0].financing_costs) == 1
    assert handler.positions[0].financing_costs[0].name == "financing"

    close_at = _ok(Instant.try_create(rollover.value_ns + 1_000_000_000))
    exit_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("target", "family")),
            position.position_ref,
        )
    )
    bot.proposals = (exit_intent,)
    _ok(handler.bind_path(_path(110_000, 110_100, 109_800)))
    closing = _ok(handler.mint_intents("eurusd", close_at))[0]
    assert _ok(handler.execute_resting(closing, None, close_at)) is True
    record = handler.receipts[-1].exit_record
    assert record is not None
    finance = [component for component in record.cost_components if component.name == "financing"]
    assert len(finance) == 1
    assert finance[0].amount == _ok(Money.try_create(-100, "USD", 2))
    expected_net = record.realized_pnl
    for component in record.cost_components:
        expected_net = _ok(expected_net.subtract(component.amount))
    assert _ok(record.net_realized_pnl()) == expected_net
    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=position.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert len(recovered.positions[0].financing_costs) == 1


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


def test_run_loop_selected_bot_entry_fills_then_recorded_bid_stops_and_closes(
    tmp_path: Path,
) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    entry_at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    fill_at = _ok(Instant.try_create(entry_at.value_ns + 1_000_000_000))
    stop_at = _ok(Instant.try_create(entry_at.value_ns + 2_000_000_000))
    entry = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            handler.admission.execution_target,
        )
    )
    bot.responses = ((entry,), (), ())
    _ok(
        handler.bind_paths(
            (
                (
                    entry_at,
                    _quote_path(110_000, 110_050, 109_950, bid=109_999, ask=110_001),
                ),
                (
                    fill_at,
                    _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001),
                ),
                (
                    stop_at,
                    _quote_path(110_000, 109_500, 109_400, bid=109_400, ask=109_402),
                ),
            )
        )
    )
    outcome = _ok(
        run(
            slices=(
                (_ok(SliceObservation.try_create("eurusd", entry_at, True)),),
                (_ok(SliceObservation.try_create("eurusd", fill_at, True)),),
                (_ok(SliceObservation.try_create("eurusd", stop_at, True)),),
            ),
            stream_set=("eurusd",),
            handler=handler,
        )
    )
    assert len(outcome.filled) == 1
    assert outcome.resting == ()
    assert len(handler.receipts) == 2
    opened, closed = handler.receipts
    assert opened.position is not None
    assert closed.exit_record is not None
    assert closed.exit_record.close_reason is CloseReason.PROTECTIVE_STOP_FILL
    assert closed.exit_record.realized_pnl.value < 0
    assert _ok(closed.exit_record.net_realized_pnl()).value < 0
    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=opened.position.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert len(recovered.positions) == 1
    assert recovered.positions[0].closed is True


def test_run_loop_keeps_partial_entry_across_nofill_and_rebases_at_terminal(
    tmp_path: Path,
) -> None:
    handler, bot, reader, writer = _handler(tmp_path)
    rules = dict(handler.admission.order_policy_by_code)
    rules["entry:family:breakout"] = BookOrderPolicy(
        OrderType.MARKET, liquidity=_ok(Quantity.try_create(2, "lot", 0))
    )
    handler.admission = replace(
        handler.admission,
        requested_r=_ok(ExactRational.try_create(5, 1, UnitKind.R_MULTIPLE)),
        order_policy_by_code=MappingProxyType(rules),
    )
    start = _ok(Instant.try_create(1_700_000_000_000_000_000))
    instants = tuple(_ok(Instant.try_create(start.value_ns + i * 1_000_000_000)) for i in range(4))
    entry = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            handler.admission.execution_target,
        )
    )
    bot.responses = ((entry,), (), (), ())
    paths = (
        _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001),
        _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001),
        _ok(SlicePath.try_create("eurusd", (_price(110_000),), market_closed=True)),
        _quote_path(110_000, 110_100, 109_900, bid=109_999, ask=110_001),
    )
    _ok(handler.bind_paths(tuple(zip(instants, paths, strict=True))))
    outcome = _ok(
        run(
            slices=tuple(
                (_ok(SliceObservation.try_create("eurusd", instant, True)),) for instant in instants
            ),
            stream_set=("eurusd",),
            handler=handler,
        )
    )
    assert len(outcome.filled) == 1
    assert len(outcome.resting) == 1
    assert len(handler.pending_entry_tickets) == 1
    assert len(handler.receipts) == 3
    terminal = _ok(handler.finalize_pending_entries(at=instants[-1]))
    assert len(terminal) == 1
    assert terminal[0].quantity == _ok(Quantity.try_create(4, "lot", 0))
    assert terminal[0].faces.original_risk_amount == _ok(Money.try_create(400, "USD", 0))
    assert handler.finalized_resting_intent_ids == (outcome.resting[0].intent_id,)
    reopened = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=terminal[0].binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert reopened.positions[0].fp1_identity() == terminal[0].fp1_identity()
