"""Costs observed from fills, net and gross R kept apart, and a sizer that reads a cost (RC-28).

The handler here is the one QMB and the node both drive, so a cost it measures from a fill is the
cost either host measures. A cell stays ``uncalibrated`` until it has seen its count of fills.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmb.execution.fill import BarExecution
from qmb.execution.financing import CashEvent, CashKind
from qmb.host.facts import CostCells, cost_cell_name
from qmb.host.unit_handler import Fill, FillKind, ListJournal, UnitSliceHandler
from qmb.runloop.loop import DeclaredStream, RestingIntent, StreamSet, run_slice
from qmb.runloop.loop import SliceObservation as Seen
from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.facts import Fact
from qmf.risk.unit_intent import UnitIntent
from qml.blocks.api import Amount, EntryFace, Instance, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, parse_record
from qml.numbers.convert import RoundRule, to_quantity
from qml.protocol.unit import OHLC, Account, OwnPosition, QuoteBar, UnitStep, accept_unit_intents

_REPO = Path(__file__).resolve().parents[2]
_RECORD = _REPO / "qml" / "tests" / "fixtures" / "records" / "eurusd.json"
_SIZER = _REPO / "qml" / "src" / "qml" / "blocks" / "stdlib" / "fixed-fraction-at-stop" / "3"
_MINE = Fingerprint("fp1:sha256:" + "a" * 64)
_M = "fx.eurusd"
_T0, _T1, _T2 = (1_741_000_000_000_000_000 + i * 900_000_000_000 for i in range(3))


def _record(**extra: str) -> InstrumentRecord:
    parsed = parse_record(json.loads(_RECORD.read_text("utf-8")) | extra)
    assert not isinstance(parsed, TypedRefusal), parsed
    return parsed.value


def _bar(at: int, bid: str, ask: str) -> QuoteBar:
    b, a = Decimal(bid), Decimal(ask)
    return QuoteBar(Instant(at), OHLC(b, b, b, b), OHLC(a, a, a, a))


def _entry(stop: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "entry",
        "unit": {"unit_id": "u", "version_ref": _MINE.value, "compiled_fingerprint": _MINE.value},
        "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
        "market_id": _M,
        "direction": "long",
        "reason_code": {"code": "test", "book_family": "unit"},
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
        "order": {"type": "market"},
        "quantity": "1.00",
        "sizer_receipt": {"inputs_used": ["equity"], "rounding_residue_r": "0/1"},
        "protection": {"stop": stop, "targets": []},
        "not_before": _T0,
        "placeholder_labels": [],
        "decision_row_id": "row-1",
    }


def _close(position_id: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": "close_full",
        "position_ref": {
            "position_id": position_id,
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "opened_by": _MINE.value,
        },
        "reason_code": {"code": "time-exit", "book_family": "unit"},
        "decision_row_id": "row-2",
    }


class _Scripted:
    def __init__(self, script: Mapping[int, Sequence[Mapping[str, object]]]) -> None:
        self._steps: dict[int, tuple[UnitIntent, ...]] = {}
        for at, wires in script.items():
            intents = accept_unit_intents(wires)
            assert not isinstance(intents, TypedRefusal), intents
            self._steps[at] = intents.value

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        return Ok(UnitStep(instant, self._steps.get(instant.value_ns, ()), (), (), ()))


class _Commission:
    """A cash port that charges 7 USD on each closing fill and nothing else."""

    def held(
        self, market: str, position: OwnPosition, since: Instant, until: Instant, bar: QuoteBar, /
    ) -> Result[tuple[CashEvent, ...]]:
        return Ok(())

    def filled(self, fill: Fill, /) -> tuple[CashEvent, ...]:
        if fill.kind is not FillKind.CLOSE:
            return ()
        return (
            CashEvent(
                fill.instant,
                fill.market_id,
                fill.position_id,
                CashKind.COMMISSION,
                Decimal("-7.00"),
                "1 lot",
                "commission.close",
            ),
        )


def _drive(
    script: Mapping[int, Sequence[Mapping[str, object]]],
    bars: Mapping[int, QuoteBar],
    record: InstrumentRecord,
    *,
    cash: _Commission | None = None,
) -> tuple[UnitSliceHandler, ListJournal]:
    journal = ListJournal()
    started = UnitSliceHandler.start(
        lambda _surfaces: Ok(_Scripted(script)),
        stream="m15",
        records={_M: record},
        bars={_M: bars},
        opened_by=_MINE,
        equity=Decimal("100000.00"),
        execution=BarExecution(900_000_000_000),
        journal=journal,
        cash=cash,
    )
    assert not isinstance(started, TypedRefusal), started
    handler = started.value
    streams = StreamSet((DeclaredStream(_M, _M),))
    resting: tuple[RestingIntent, ...] = ()
    frontier: Instant | None = None
    for at in sorted(bars):
        outcome = run_slice(
            [Seen(_M, Instant(at))],
            stream_set=streams,
            current_frontier=frontier,
            handler=handler,
            resting=resting,
        )
        assert not is_refusal(outcome), outcome
        frontier, resting = outcome.value.frontier, outcome.value.resting
    return handler, journal


def test_k9_10_known_answer_cost() -> None:
    """A long filled 2 pips over its decision quote, 7 USD a lot commission, 1 lot on EURUSD."""
    record = _record(commission_per_lot="7")
    bars = {_T0: _bar(_T0, "1.10000", "1.10000"), _T1: _bar(_T1, "1.09980", "1.10020")}

    handler, journal = _drive({_T0: [_entry("1.09500")]}, bars, record)

    fills = [r for r in journal.records if isinstance(r, Fill)]
    assert [
        (f.kind, f.price, f.decision_quote, f.arrival_quote, f.spread, f.commission, f.partial)
        for f in fills
    ] == [
        (
            FillKind.ENTRY,
            Decimal("1.10020"),
            Decimal("1.10000"),
            Decimal("1.10000"),
            Decimal("20.00"),
            Decimal("7.00"),
            False,
        )
    ]
    assert handler.costs.cell(_M, record, Instant(_T1)).fills == 1
    account = cast("Account", handler.read_surfaces()["account"].at(Instant(_T1)))
    cell = account.facts[cost_cell_name(_M)]
    assert (cell.state, cell.value) == ("uncalibrated", Decimal("0.0005346"))


def test_gross_and_net_stay_apart() -> None:
    """Money 500, cash -7, risk 500: gross R 1.00 and net R 0.986."""
    record = _record()
    bars = {
        _T0: _bar(_T0, "1.10000", "1.10000"),
        _T1: _bar(_T1, "1.10000", "1.10000"),
        _T2: _bar(_T2, "1.10500", "1.10500"),
    }
    script = {_T0: [_entry("1.09500")], _T1: [_close("aaaaaaaaaaaa-1")]}

    handler, _ = _drive(script, bars, record, cash=_Commission())

    assert [(t.money, t.cash, t.r, t.net_r) for t in handler.trades] == [
        (Decimal("500.00"), Decimal("-7.00"), Decimal("1.0000"), Decimal("0.9860"))
    ]
    closed = cast("Sequence[ClosedTrade]", handler.read_surfaces()["own_journal"].at(Instant(_T2)))
    assert [(t.gross_r, t.net_r) for t in closed] == [(Decimal("1.0000"), Decimal("0.9860"))]


def _sizer_v3() -> Instance:
    face = parse_entry((_SIZER / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    lock = [LockEntry(face.entry_id, face.version, face.fingerprint)]
    loaded = load(lock, {face.pin: (_SIZER / "block.py").read_bytes()})
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks[face.pin].make({"fraction": Decimal("0.005")}, {})


def _lots(cost: object) -> Decimal | None:
    """The lots fixed-fraction-at-stop@3 gives on 100000 equity at 0.005, a 0.0050 stop."""
    record = _record()
    sizer = _sizer_v3()
    evidence: dict[str, object] = {
        "equity": Decimal("100000.00"),
        "entry_price": Decimal("1.10000"),
        "stop_price": Decimal("1.09500"),
        "record": record,
        "fraction": Decimal("0.005"),
    }
    if cost is not None:
        evidence["cost_cell"] = cost
    answer = sizer.update(evidence)
    assert isinstance(answer, Amount), answer
    now = Instant(_T0)
    rate = Fact(Decimal(1), now, "open", "the account is in the record's quote currency")
    converted = to_quantity(
        answer, Decimal("1.10000"), Decimal("1.09500"), record, rate, RoundRule(now=now)
    )
    return converted.quantity


def test_the_sizer_reads_a_measured_cell() -> None:
    """A measured 0.0002 cost beside a 0.0050 stop gives 0.96 lots from 500 money at risk, and a
    measured zero gives 1.00. A missing, malformed or negative cell reads the stressed cost, never
    zero: a negative cost is drift or a bad fill price, not a fill that paid nothing."""
    measured = Fact(Decimal("0.0002"), Instant(_T0), "open", "test", "ok")
    nothing = Fact(Decimal(0), Instant(_T0), "open", "test", "ok")

    assert _lots(measured) == Decimal("0.96")
    assert _lots(nothing) == Decimal("1.00")
    assert _lots(None) == Decimal("0.96")
    assert _lots("0.0002") == Decimal("0.96")
    assert _lots(Fact(Decimal("-0.0010"), Instant(_T0), "open", "test", "ok")) == Decimal("0.96")


def test_a_cell_moves_off_uncalibrated_at_its_count() -> None:
    """At a count of 2, the second 2-pip fill makes the cell measured at 0.0002."""
    record = _record()
    cells = CostCells(min_fills=2)
    at = Instant(_T1)

    cells.observe(_M, record, at, Decimal("0.0002"))
    first = cells.fact(_M, record, at)
    cells.observe(_M, record, at, Decimal("0.0002"))
    second = cells.fact(_M, record, at)

    assert (first.state, first.value) == ("uncalibrated", Decimal("0.0003"))
    assert (second.state, second.value) == ("ok", Decimal("0.0002"))


def test_a_count_below_one_reads_as_one_fill() -> None:
    """The account the exits' step builds reads every cell, so a count of 0 must not divide by
    zero: an empty cell reads the stressed 0.0002, and one 0.0003 fill is measured."""
    record = _record()
    cells = CostCells(min_fills=0)
    at = Instant(_T1)

    empty = cells.fact(_M, record, at)
    cells.observe(_M, record, at, Decimal("0.0003"))
    measured = cells.fact(_M, record, at)

    assert (empty.state, empty.value) == ("uncalibrated", Decimal("0.0002"))
    assert (measured.state, measured.value) == ("ok", Decimal("0.0003"))
