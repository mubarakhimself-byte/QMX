"""Independent Book journeys using the existing labeled local host/store fixture.

The scripted Bot and recorded calendar are test fixtures. Execution, runloop,
CT13 stores, recovery and economic folds are production functions.
"""

from collections.abc import Callable, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TypeVar, cast

import pytest
import test_book_handler as fx
from qmb.execution import SLIPPAGE_ADAPTER_ZERO
from qmb.execution.fill import OrderType
from qmb.host.book_handler import (
    BookExecutionSliceHandler,
    BookOrderPolicy,
    ReplayPositionRecovery,
    read_replay_positions,
)
from qmb.runloop import LoopOutcome, RestingIntent, SliceObservation, run
from qmf.core import (
    ExactRational,
    Instant,
    Money,
    Ok,
    Quantity,
    Result,
    UnitKind,
    WriterId,
    is_ok,
    is_refusal,
)
from qmf.data import JournalReader, JournalWriter
from qmf.risk.door import Direction, EntryIntent, ExitIntent, ExitKind, ReasonCode
from test_book_handler import _handler as fixture_handler  # pyright: ignore[reportPrivateUsage]
from test_book_handler import (
    _instrument as fixture_instrument,  # pyright: ignore[reportPrivateUsage]
)
from test_book_handler import _quote_only_path as quote_path  # pyright: ignore[reportPrivateUsage]
from test_book_handler import (
    _RecordedRolloverCalendar as RecordedCalendar,  # pyright: ignore[reportPrivateUsage]
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _at(n: int) -> Instant:
    return _ok(Instant.try_create(1_700_000_000_000_000_000 + n * 1_000_000_000))


def _entry(
    handler: BookExecutionSliceHandler, direction: Direction = Direction.LONG
) -> EntryIntent:
    return _ok(
        EntryIntent.try_create(
            fixture_instrument(),
            direction,
            _ok(ReasonCode.try_create("breakout", "family")),
            handler.admission.execution_target,
        )
    )


def _run(
    handler: BookExecutionSliceHandler,
    times: Sequence[Instant],
    *,
    initial: tuple[RestingIntent, ...] = (),
) -> Result[LoopOutcome]:
    return run(
        slices=tuple((_ok(SliceObservation.try_create("eurusd", t, True)),) for t in times),
        stream_set=("eurusd",),
        handler=handler,
        initial_resting=initial,
    )


def _recover(
    handler: BookExecutionSliceHandler, reader: JournalReader, writer: WriterId
) -> ReplayPositionRecovery:
    return _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=handler.admission.binding.fingerprint,
            result_label=handler.admission.result_label,
        )
    )


def test_short_quote_entry_ask_stop_and_checked_reopen(tmp_path: Path) -> None:
    handler, bot, reader, writer = fixture_handler(tmp_path, slippage_adapter=SLIPPAGE_ADAPTER_ZERO)
    bot.responses = ((_entry(handler, Direction.SHORT),), (), (), ())
    # Ask below stop is a no-close control; ask crossing closes even while bid is below it.
    _ok(
        handler.bind_paths(
            tuple(
                (t, quote_path(bid=b, ask=a))
                for t, b, a in (
                    (_at(0), 109999, 110001),
                    (_at(1), 109999, 110001),
                    (_at(2), 110497, 110498),
                    (_at(3), 110498, 110501),
                )
            )
        )
    )
    result = _ok(_run(handler, (_at(0), _at(1), _at(2))))
    assert len(handler.positions) == 1 and len(handler.receipts) == 1
    _ok(_run(handler, (_at(3),), initial=result.resting))
    record = handler.receipts[-1].exit_record
    assert record is not None
    assert record.realized_pnl.as_fraction() == -Fraction(502, 5)
    assert _ok(record.net_realized_pnl()).as_fraction() == -Fraction(512, 5)
    recovered = _recover(handler, reader, writer)
    assert recovered.positions[0].closed
    assert next(iter(recovered.position_sides.values())) is fx.TradeSide.SHORT


@pytest.mark.parametrize("physically_written", [False, True])
def test_close_uncertainty_reopens_physical_truth_without_duplicate_cash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, physically_written: bool
) -> None:
    handler, bot, reader, writer = fixture_handler(tmp_path, slippage_adapter=SLIPPAGE_ADAPTER_ZERO)
    bot.proposals = (_entry(handler),)
    _ok(
        handler.bind_paths(
            (
                (_at(0), quote_path(bid=109999, ask=110001)),
                (_at(1), quote_path(bid=109999, ask=110001)),
            )
        )
    )
    token = _ok(handler.mint_intents("eurusd", _at(0)))[0]
    _ok(handler.execute_resting(token, None, _at(0)))
    position = handler.positions[0]
    exit_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("target", "family")),
            position.position_ref,
        )
    )
    bot.proposals = (exit_intent,)
    exit_token = _ok(handler.mint_intents("eurusd", _at(1)))[0]
    original = JournalWriter.record

    def uncertain(writer: JournalWriter, *args: object, **kwargs: object) -> Result[object]:
        if physically_written:
            _ok(cast(Callable[..., Result[object]], original)(writer, *args, **kwargs))
        return Ok(None)

    monkeypatch.setattr(JournalWriter, "record", uncertain)
    assert is_refusal(handler.execute_resting(exit_token, None, _at(1)))
    assert handler.positions[0].position_ref == position.position_ref
    monkeypatch.undo()
    truth = _recover(handler, reader, writer)
    assert truth.positions[0].closed is physically_written
    reopened, reopened_bot, reopened_reader, reopened_writer = fixture_handler(
        tmp_path, writer_boot="boot-2", slippage_adapter=SLIPPAGE_ADAPTER_ZERO
    )
    reopened_bot.proposals = (exit_intent,)
    _ok(reopened.bind_path(quote_path(bid=109999, ask=110001)))
    retry = _ok(reopened.mint_intents("eurusd", _at(2)))[0]
    outcome = reopened.execute_resting(retry, None, _at(2))
    assert is_refusal(outcome) if physically_written else fx.is_ok(outcome), outcome
    final = _recover(reopened, reopened_reader, reopened_writer)
    assert final.positions[0].closed and len(final.record_resolver) == 1


def test_partial_rollover_then_full_fill_keeps_original_actual_cash_charge(tmp_path: Path) -> None:
    date = _ok(
        fx.TradingDate.try_create(
            _ok(fx.CalendarIdentity.try_create("broker-hours", "v1", "2026a")),
            _ok(fx.CivilDate.try_create(2026, 10, 5)),
        )
    )
    calendar = RecordedCalendar(_at(2).value_ns, date)
    rate = _ok(
        fx.SwapRate.try_create("eurusd", Direction.LONG, _ok(Money.try_create(-100, "USD", 2)))
    )
    calibration = _ok(
        fx.SwapCalibration.try_create(
            "replay-broker",
            rates=(rate,),
            weekend_holiday_handling="skip",
            calendar_identity=date.calendar.fp1_identity(),
        )
    )
    handler, bot, reader, writer = fixture_handler(
        tmp_path,
        financing_calibration=calibration,
        rollover_calendar=calendar,
        slippage_adapter=SLIPPAGE_ADAPTER_ZERO,
    )
    rules = dict(handler.admission.order_policy_by_code)
    rules["entry:family:breakout"] = BookOrderPolicy(
        OrderType.MARKET, liquidity=_ok(Quantity.try_create(2, "lot", 0))
    )
    handler.admission = replace(
        handler.admission,
        requested_r=_ok(ExactRational.try_create(5, 1, UnitKind.R_MULTIPLE)),
        order_policy_by_code=MappingProxyType(rules),
    )
    bot.responses = ((_entry(handler),), (), (), ())
    _ok(
        handler.bind_paths(
            tuple(
                (t, quote_path(bid=b, ask=a))
                for t, b, a in (
                    (_at(0), 109999, 110001),
                    (_at(1), 109999, 110001),
                    (_at(2), 109999, 110001),
                    (_at(3), 109000, 109002),
                )
            )
        )
    )
    first = _ok(_run(handler, (_at(0), _at(1))))
    assert handler.positions == () and len(handler.pending_entry_tickets) == 1
    rules["entry:family:breakout"] = BookOrderPolicy(
        OrderType.MARKET, liquidity=_ok(Quantity.try_create(3, "lot", 0))
    )
    handler.admission = replace(handler.admission, order_policy_by_code=MappingProxyType(rules))
    second = _ok(_run(handler, (_at(2),), initial=first.resting))
    position = handler.positions[0]
    assert position.quantity.as_fraction() == 5 and not position.risk_rebased
    before = handler.admission.journal_writer.next_sequence
    _ok(handler.scheduled_position_event("eurusd", _at(2)))
    assert handler.admission.journal_writer.next_sequence == before
    _ok(_run(handler, (_at(3),), initial=second.resting))
    record = handler.receipts[-1].exit_record
    assert record is not None
    financing = [x for x in record.cost_components if x.name == "financing"]
    assert len(financing) == 1 and financing[0].amount.as_fraction() == 2
    assert record.realized_pnl.as_fraction() == -1001
    assert _ok(record.net_realized_pnl()).as_fraction() == -1013
    recovered = _recover(handler, reader, writer)
    assert recovered.positions[0].closed and len(recovered.positions[0].financing_rollovers) == 1


def test_unknown_exit_policy_preserves_actual_open_quantity_and_risk(tmp_path: Path) -> None:
    handler, bot, reader, writer = fixture_handler(tmp_path, slippage_adapter=SLIPPAGE_ADAPTER_ZERO)
    bot.responses = ((_entry(handler),), ())
    _ok(
        handler.bind_paths(
            (
                (_at(0), quote_path(bid=109999, ask=110001)),
                (_at(1), quote_path(bid=109999, ask=110001)),
                (_at(2), quote_path(bid=109999, ask=110001)),
                (_at(3), quote_path(bid=109999, ask=110001)),
            )
        )
    )
    _ok(_run(handler, (_at(0), _at(1))))
    position = handler.positions[0]
    before = handler.admission.journal_writer.next_sequence
    exit_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("unconfigured", "family")),
            position.position_ref,
        )
    )
    bot.responses = ((exit_intent,),)
    bot.calls = 0
    result = _run(handler, (_at(2), _at(3)))
    assert is_refusal(result)
    assert handler.positions[0] == position
    assert handler.admission.journal_writer.next_sequence == before
    truth = _recover(handler, reader, writer)
    assert not truth.positions[0].closed and truth.record_resolver == {}
