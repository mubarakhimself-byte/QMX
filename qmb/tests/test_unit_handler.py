"""The shared unit handler: lot rounding at the fill, own positions only, no bot door (B5b).

A stand-in unit answers scripted steps so a test can name the sizer receipt's quantity and
each exit. The handler is driven the way QMB and the node drive it, through ``run_slice``.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmb.execution.fill import BarExecution
from qmb.host.unit_handler import (
    Fill,
    FillKind,
    ListJournal,
    Skip,
    UnitSliceHandler,
)
from qmb.host.unit_runner import run_unit
from qmb.runloop.loop import (
    DeclaredStream,
    RestingIntent,
    SliceObservation,
    SliceOutcome,
    StreamSet,
    run_slice,
)
from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, RefusalCategory, Result, TypedRefusal, is_refusal
from qmf.risk.unit_intent import UnitIntent
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.exits import PositionFacts
from qml.protocol.unit import (
    EXIT_FAULT,
    OHLC,
    DecisionRow,
    OwnPosition,
    QuoteBar,
    SlotOutput,
    UnitStep,
    accept_unit_intents,
)
from qml.unit.model import Side
from test_unit_runner import make_run_folder, request

_REPO = Path(__file__).resolve().parents[2]
_RECORDS = _REPO / "qml" / "tests" / "fixtures" / "records"
_HOST = _REPO / "qmb" / "src" / "qmb" / "host"
_MINE = Fingerprint("fp1:sha256:" + "a" * 64)
_OTHER = Fingerprint("fp1:sha256:" + "b" * 64)
_M = "fx.eurusd"
_X = "metal.xauusd"
_RECORD_FILE = {_M: "eurusd.json", _X: "xauusd.json"}
_OWN = "aaaaaaaaaaaa-1"
_T0, _T1, _T2, _T3 = (1_741_000_000_000_000_000 + i * 900_000_000_000 for i in range(4))


def _bar(at: int, mid: str) -> QuoteBar:
    bid = Decimal(mid)
    ask = bid + Decimal("0.00010")
    return QuoteBar(
        Instant(at),
        OHLC(bid, bid + Decimal("0.0001"), bid - Decimal("0.0001"), bid),
        OHLC(ask, ask + Decimal("0.0001"), ask - Decimal("0.0001"), ask),
    )


def _entry(quantity: str) -> dict[str, object]:
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
        "quantity": quantity,
        "sizer_receipt": {"inputs_used": ["equity"], "rounding_residue_r": "0/1"},
        "protection": {"stop": "1.08000", "targets": []},
        "not_before": _T0,
        "placeholder_labels": [],
        "decision_row_id": "row-1",
    }


def _exit(
    position_id: str,
    kind: str = "close_full",
    row_id: str = "row-2",
    opened_by: Fingerprint = _OTHER,
    **action: object,
) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": kind,
        "position_ref": {
            "position_id": position_id,
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "opened_by": opened_by.value,
        },
        "reason_code": {"code": "time-exit", "book_family": "unit"},
        "decision_row_id": row_id,
        **action,
    }


def _own_exit(kind: str, row_id: str, **action: object) -> dict[str, object]:
    return _exit(_OWN, kind, row_id, _MINE, **action)


Script = Mapping[int, tuple[Sequence[Mapping[str, object]], Sequence[DecisionRow]]]


class _Scripted:
    """A unit that answers each scripted instant with its intents and decision rows."""

    def __init__(self, script: Script) -> None:
        self._steps: dict[int, tuple[tuple[UnitIntent, ...], tuple[DecisionRow, ...]]] = {}
        for at, (wires, rows) in script.items():
            intents = accept_unit_intents(wires)
            assert not isinstance(intents, TypedRefusal), intents
            self._steps[at] = (intents.value, tuple(rows))

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        intents, rows = self._steps.get(instant.value_ns, ((), ()))
        return Ok(UnitStep(instant, intents, rows, (), ()))


def _at_start(wire: Mapping[str, object]) -> Script:
    return {_T0: ([wire], ())}


def _start(
    script: Script,
    bars: Mapping[str, Mapping[int, QuoteBar]],
    seeded: Mapping[str, OwnPosition] | None = None,
) -> tuple[UnitSliceHandler, ListJournal]:
    records: dict[str, InstrumentRecord] = {}
    for market in bars:
        record = parse_record(json.loads((_RECORDS / _RECORD_FILE[market]).read_text("utf-8")))
        assert not isinstance(record, TypedRefusal)
        records[market] = record.value
    journal = ListJournal()
    started = UnitSliceHandler.start(
        lambda _surfaces: Ok(_Scripted(script)),
        stream="m15",
        records=records,
        bars=bars,
        opened_by=_MINE,
        equity=Decimal("10000.00"),
        execution=BarExecution(900_000_000_000),
        journal=journal,
        seeded=seeded,
    )
    assert not isinstance(started, TypedRefusal), started
    return started.value, journal


def _drive(
    script: Script,
    bars: Mapping[str, Mapping[int, QuoteBar]] | None = None,
    seeded: Mapping[str, OwnPosition] | None = None,
) -> tuple[UnitSliceHandler, ListJournal, Sequence[Result[SliceOutcome]]]:
    bars = bars or {_M: {_T0: _bar(_T0, "1.08500"), _T1: _bar(_T1, "1.08520")}}
    handler, journal = _start(script, bars, seeded)
    streams = StreamSet(tuple(DeclaredStream(m, m) for m in bars))
    resting: tuple[RestingIntent, ...] = ()
    outcomes: list[Result[SliceOutcome]] = []
    frontier: Instant | None = None
    for at in sorted({at for market in bars.values() for at in market}):
        outcome = run_slice(
            [SliceObservation(m, Instant(at)) for m in bars if at in bars[m]],
            stream_set=streams,
            current_frontier=frontier,
            handler=handler,
            resting=resting,
        )
        outcomes.append(outcome)
        if is_refusal(outcome):
            break
        frontier, resting = outcome.value.frontier, outcome.value.resting
    return handler, journal, outcomes


def test_a_receipt_of_0_037_lots_fills_0_03_and_journals_the_0_007_residue_in_r() -> None:
    handler, journal, _ = _drive(_at_start(_entry("0.037")))

    assert [
        (f.kind, f.quantity, f.receipt_quantity, f.residue_r, f.price) for f in handler.fills
    ] == [
        (FillKind.ENTRY, Decimal("0.03"), Decimal("0.037"), Decimal("0.1892"), Decimal("1.08530"))
    ]
    assert [r for r in journal.records if isinstance(r, Fill)] == list(handler.fills)


def test_the_own_position_surface_answers_the_facts_an_exit_reads() -> None:
    """SWAP E15: a held position reaches the unit as its facts, not its identity alone, so a
    per-bar exit reads its stop, the bars held and its excursions in R from one surface."""
    handler, _, _ = _drive(_at_start(_entry("0.037")))

    facts = cast(
        "tuple[object, ...]", handler.read_surfaces()[f"own_position:{_M}"].at(Instant(_T1))
    )

    assert len(facts) == 1, facts
    one = facts[0]
    assert isinstance(one, PositionFacts), one
    assert (one.position_id, one.side, one.quantity, one.entry_price) == (
        _OWN,
        Side.LONG,
        Decimal("0.03"),
        Decimal("1.08530"),
    )
    assert (one.stop, one.targets, one.bars_held) == (Decimal("1.08000"), (), 1)
    assert (one.mae_r, one.mfe_r) == (Decimal("0.0377"), Decimal(0))
    assert one.opened_by == _MINE


def test_a_receipt_of_0_004_lots_is_below_the_minimum_lot_and_skips() -> None:
    handler, journal, _ = _drive(_at_start(_entry("0.004")))

    skips = [r for r in journal.records if isinstance(r, Skip)]
    assert handler.fills == ()
    assert [(s.decision_row_id, s.residue_r) for s in skips] == [("row-1", Decimal(1))]
    assert "below" in skips[0].reason and "0.01" in skips[0].reason


def test_a_close_for_a_position_the_unit_did_not_open_is_refused_and_it_stays_open() -> None:
    seeded = {
        _M: OwnPosition(
            "foreign-1", Side.SHORT, Decimal("1.00"), Decimal("1.09"), _OTHER, Instant(_T0 - 1)
        )
    }

    handler, _, outcomes = _drive(_at_start(_exit("foreign-1")), seeded=seeded)

    refused = outcomes[-1]
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "position_ref"
    assert handler.open_positions == {"foreign-1": seeded[_M]}
    assert handler.fills == ()


def test_an_entry_keeps_its_minting_rows_stamps_when_another_market_steps_the_unit_first() -> None:
    minting_row = DecisionRow(
        "row-1",
        Instant(_T0),
        _M,
        Side.LONG,
        "enter",
        (SlotOutput("trigger", "trend", "1.08510"), SlotOutput("filter", "label", "up")),
        {},
        "test",
    )
    bars = {
        _M: {_T0: _bar(_T0, "1.08500"), _T2: _bar(_T2, "1.08520"), _T3: _bar(_T3, "1.07990")},
        _X: {at: _bar(at, "2900.00") for at in (_T0, _T1, _T2, _T3)},
    }

    handler, _, outcomes = _drive({_T0: ([_entry("0.50")], [minting_row])}, bars)

    assert all(not is_refusal(o) for o in outcomes)
    closed = cast("Sequence[ClosedTrade]", handler.read_surfaces()["own_journal"].at(Instant(_T3)))
    assert [(t.trade_id, t.market_id, t.entry_stamps) for t in closed] == [
        (_OWN, _M, {"trend": Decimal("1.08510")})
    ]
    assert [(f.kind, f.instant.value_ns) for f in handler.fills] == [
        (FillKind.ENTRY, _T2),
        (FillKind.STOP, _T3),
    ]


def _four_bars(t2_mid: str, t3_mid: str = "1.08400") -> dict[str, dict[int, QuoteBar]]:
    mids = {_T0: "1.08500", _T1: "1.08520", _T2: t2_mid, _T3: t3_mid}
    return {_M: {at: _bar(at, mid) for at, mid in mids.items()}}


def test_a_partial_close_closes_its_lot_rounded_quantity_and_the_rest_stays_held() -> None:
    script: Script = {
        _T0: ([_entry("0.50")], ()),
        _T1: ([_own_exit("close_partial", "row-2", quantity="0.207")], ()),
        _T2: ([_own_exit("close_full", "row-3")], ()),
    }

    handler, _, outcomes = _drive(script, _four_bars("1.08600"))

    assert all(not is_refusal(o) for o in outcomes)
    assert [(f.kind, f.quantity, f.price, f.decision_row_id) for f in handler.fills] == [
        (FillKind.ENTRY, Decimal("0.50"), Decimal("1.08530"), "row-1"),
        (FillKind.CLOSE, Decimal("0.20"), Decimal("1.08600"), "row-2"),
        (FillKind.CLOSE, Decimal("0.30"), Decimal("1.08400"), "row-3"),
    ]
    assert [(t.quantity, t.money, t.r) for t in handler.trades] == [
        (Decimal("0.20"), Decimal("14.00"), Decimal("0.0528")),
        (Decimal("0.30"), Decimal("-39.00"), Decimal("-0.1472")),
    ]
    closed = cast("Sequence[ClosedTrade]", handler.read_surfaces()["own_journal"].at(Instant(_T3)))
    assert [(t.trade_id, t.r_after_costs) for t in closed] == [(_OWN, Decimal("-0.0944"))]


def test_a_tightened_stop_is_held_and_fills_without_closing_at_the_amendment() -> None:
    script: Script = {
        _T0: ([_entry("0.50")], ()),
        _T1: ([_own_exit("amend_protection", "row-2", stop="1.08400", targets=[])], ()),
    }

    handler, _, outcomes = _drive(script, _four_bars("1.08405"))

    assert all(not is_refusal(o) for o in outcomes)
    assert [(f.kind, f.quantity, f.price) for f in handler.fills] == [
        (FillKind.ENTRY, Decimal("0.50"), Decimal("1.08530")),
        (FillKind.STOP, Decimal("0.50"), Decimal("1.08400")),
    ]
    assert [(t.stop, t.money, t.r) for t in handler.trades] == [
        (Decimal("1.08000"), Decimal("-65.00"), Decimal("-0.2453"))
    ]


def test_an_amendment_that_widens_the_stop_is_refused_and_the_position_stays_open() -> None:
    script: Script = {
        _T0: ([_entry("0.50")], ()),
        _T1: ([_own_exit("amend_protection", "row-2", stop="1.07900", targets=[])], ()),
    }

    handler, _, outcomes = _drive(script, _four_bars("1.08405"))

    refused = outcomes[2]
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["violation"] == "widen-stop"
    assert "from 1.08000 to 1.07900" in str(refused.context["reason"])
    assert [(f.kind, f.quantity) for f in handler.fills] == [(FillKind.ENTRY, Decimal("0.50"))]
    assert handler.open_positions[_OWN].quantity == Decimal("0.50")


def test_the_close_scope_port_closes_every_held_market_at_its_next_bar() -> None:
    bars = {
        _M: {_T0: _bar(_T0, "1.08500"), _T1: _bar(_T1, "1.08520")},
        _X: {_T0: _bar(_T0, "2900.00"), _T1: _bar(_T1, "2901.00")},
    }
    handler, _ = _start({}, bars)
    for market, entry, stop, row_id in (
        (_M, "1.08500", "1.09500", "row-1"),
        (_X, "2900.00", "2950.00", "row-2"),
    ):
        adopted = handler.adopt(
            market,
            OwnPosition(
                f"{market}-short",
                Side.SHORT,
                Decimal("0.50"),
                Decimal(entry),
                _MINE,
                Instant(_T0),
            ),
            stop=Decimal(stop),
            entry_stop=Decimal(stop),
            target=None,
            decision_row_id=row_id,
        )
        assert not is_refusal(adopted), adopted

    handler.close_scope(object(), EXIT_FAULT)
    outcome = run_slice(
        [SliceObservation(m, Instant(_T1)) for m in bars],
        stream_set=StreamSet(tuple(DeclaredStream(m, m) for m in bars)),
        current_frontier=Instant(_T0),
        handler=handler,
    )

    assert not is_refusal(outcome), outcome
    assert sorted((f.market_id, f.kind, f.price) for f in handler.fills) == [
        (_M, FillKind.CLOSE, Decimal("1.08530")),
        (_X, FillKind.CLOSE, Decimal("2901.00010")),
    ]
    assert handler.open_positions == {}


def test_the_dummy_never_closes_a_seeded_position_it_did_not_open(tmp_path: Path) -> None:
    seeded = {
        "fx.eurusd": OwnPosition(
            "foreign-1", Side.LONG, Decimal("1.00"), Decimal("1.04"), _OTHER, Instant(_T0)
        )
    }
    folder = make_run_folder(tmp_path)

    result = run_unit(folder, request(folder), seeded=seeded)

    assert not isinstance(result, TypedRefusal), result
    assert result.value.open_positions["foreign-1"] == seeded["fx.eurusd"]
    assert all(f.position_id != "foreign-1" for f in result.value.fills)
    assert all(f.market_id != "fx.eurusd" for f in result.value.fills)


def test_no_unit_path_file_imports_the_bot_door() -> None:
    imported: dict[str, set[str]] = {}
    for name in ("unit_handler.py", "unit_runner.py", "behaviour.py"):
        tree = ast.parse((_HOST / name).read_text("utf-8"))
        imported[name] = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }

    assert all("construct_bot" not in names for names in imported.values())
    assert "construct_unit" in imported["unit_runner.py"]
