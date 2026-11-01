"""The shared unit handler: lot rounding at the fill, own positions only, no bot door (B5b).

A stand-in unit answers one fixed step so a test can name the sizer receipt's quantity. The
handler is driven the way QMB and the node drive it, through ``run_slice``.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path

from qmb.host.unit_handler import (
    Fill,
    FillKind,
    ListJournal,
    NextOpenExecution,
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
from qml.numbers import parse_record
from qml.protocol.unit import OHLC, OwnPosition, QuoteBar, UnitStep, accept_unit_intents
from qml.unit.model import Side
from test_unit_runner import make_run_folder, request

_REPO = Path(__file__).resolve().parents[2]
_RECORD = _REPO / "qml" / "tests" / "fixtures" / "records" / "eurusd.json"
_HOST = _REPO / "qmb" / "src" / "qmb" / "host"
_MINE = Fingerprint("fp1:sha256:" + "a" * 64)
_OTHER = Fingerprint("fp1:sha256:" + "b" * 64)
_M = "fx.eurusd"
_T0, _T1 = 1_741_000_000_000_000_000, 1_741_000_900_000_000_000


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


def _close(position_id: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": "close_full",
        "position_ref": {
            "position_id": position_id,
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "opened_by": _OTHER.value,
        },
        "reason_code": {"code": "time-exit", "book_family": "unit"},
        "decision_row_id": "row-2",
    }


class _OneStep:
    """A unit that emits ``wire`` at the first instant and nothing after."""

    def __init__(self, wire: Mapping[str, object]) -> None:
        intents = accept_unit_intents([wire])
        assert not isinstance(intents, TypedRefusal), intents
        self._intents = intents.value
        self._first = True

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        intents, self._first = (self._intents if self._first else ()), False
        return Ok(UnitStep(instant, intents, (), (), ()))


def _drive(
    wire: Mapping[str, object], seeded: Mapping[str, OwnPosition] | None = None
) -> tuple[UnitSliceHandler, ListJournal, Sequence[Result[SliceOutcome]]]:
    record = parse_record(json.loads(_RECORD.read_text("utf-8")))
    assert not isinstance(record, TypedRefusal)
    journal = ListJournal()
    bars = {_T0: _bar(_T0, "1.08500"), _T1: _bar(_T1, "1.08520")}
    started = UnitSliceHandler.start(
        lambda _surfaces: Ok(_OneStep(wire)),
        stream="m15",
        records={_M: record.value},
        bars={_M: bars},
        opened_by=_MINE,
        equity=Decimal("10000.00"),
        execution=NextOpenExecution(),
        journal=journal,
        seeded=seeded,
    )
    assert not isinstance(started, TypedRefusal), started
    streams = StreamSet((DeclaredStream(_M, _M),))
    resting: tuple[RestingIntent, ...] = ()
    outcomes: list[Result[SliceOutcome]] = []
    frontier: Instant | None = None
    for at in bars:
        outcome = run_slice(
            [SliceObservation(_M, Instant(at))],
            stream_set=streams,
            current_frontier=frontier,
            handler=started.value,
            resting=resting,
        )
        outcomes.append(outcome)
        if is_refusal(outcome):
            break
        frontier, resting = outcome.value.frontier, outcome.value.resting
    return started.value, journal, outcomes


def test_a_receipt_of_0_037_lots_fills_0_03_and_journals_the_0_007_residue_in_r() -> None:
    handler, journal, _ = _drive(_entry("0.037"))

    assert [
        (f.kind, f.quantity, f.receipt_quantity, f.residue_r, f.price) for f in handler.fills
    ] == [
        (FillKind.ENTRY, Decimal("0.03"), Decimal("0.037"), Decimal("0.1892"), Decimal("1.08530"))
    ]
    assert [r for r in journal.records if isinstance(r, Fill)] == list(handler.fills)


def test_a_receipt_of_0_004_lots_is_below_the_minimum_lot_and_skips() -> None:
    handler, journal, _ = _drive(_entry("0.004"))

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

    handler, _, outcomes = _drive(_close("foreign-1"), seeded)

    refused = outcomes[-1]
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "position_ref"
    assert handler.open_positions == seeded
    assert handler.fills == ()


def test_the_dummy_never_closes_a_seeded_position_it_did_not_open(tmp_path: Path) -> None:
    seeded = {
        "fx.eurusd": OwnPosition(
            "foreign-1", Side.LONG, Decimal("1.00"), Decimal("1.04"), _OTHER, Instant(_T0)
        )
    }
    folder = make_run_folder(tmp_path)

    result = run_unit(folder, request(folder), seeded=seeded)

    assert not isinstance(result, TypedRefusal), result
    assert result.value.open_positions["fx.eurusd"] == seeded["fx.eurusd"]
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
