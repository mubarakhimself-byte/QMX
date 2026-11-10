"""The canary's one moving number, on the hosted unit the node and QMB share (RC-17, K9 6).

The template keeps `min_trend_strength` on `trend-floor-from-record@2` with motion on and a
count cadence, so the 20th closed trade moves it one step of its range. The journal is the
dummy's own golden one: weak trends lose and strong ones win, so the floor has something to
read. The unit is driven through `HostedUnit`, the evaluator both hosts call.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Result, TypedRefusal
from qmf.risk.paper import ExecutionTarget
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    Account,
    HostedUnit,
    MotionSwitch,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_CANARY = _QML / "src" / "qml" / "unit" / "templates" / "canary.json"
_RECORDS = _QML / "tests" / "fixtures" / "records"
_MARKETS = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
_START = 1_740_952_800_000_000_000  # 2025-03-02 22:00 UTC
_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert not isinstance(result, TypedRefusal), result
    return result.value


def _document() -> dict[str, object]:
    """The canary as it ships, with every QML block it names pinned at its own fingerprint."""
    document = cast("dict[str, object]", json.loads(_CANARY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for entry in sorted(_STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    document["pins"] = pins
    return document


def _context() -> CompileContext:
    folders = [path.parent for path in _STDLIB.glob("*/*/block.py")]
    records: dict[str, InstrumentRecord] = {}
    for market_id, name in _MARKETS.items():
        raw = json.loads((_RECORDS / f"{name}.json").read_text("utf-8"))
        records[market_id] = _ok(parse_record(raw))
    return CompileContext(
        sources={f"{path.parent.name}@{path.name}": (path / "block.py").read_bytes() for path in folders},
        entries={f"{path.parent.name}@{path.name}": (path / "entry.json").read_bytes() for path in folders},
        records=records,
    )


def _compiled() -> CompiledUnit:
    compiled = compile_unit(_document(), _context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


def _trade(n: int, strength: str, r: str) -> ClosedTrade:
    return ClosedTrade(
        trade_id=f"t{n:02d}",
        opened_at=Instant(_START + n * 900_000_000_000),
        closed_at=Instant(_START + (n + 1) * 900_000_000_000),
        side=Side.LONG,
        market_id="fx.eurusd",
        world="replay",
        r_after_costs=Decimal(r),
        entry_stamps={"strength": Decimal(strength)},
    )


def _journal(count: int) -> list[ClosedTrade]:
    return [
        _trade(n, "0.0003", "-1") if n % 3 == 0 else _trade(n, "0.0015", "1.5")
        for n in range(1, count + 1)
    ]


def _instant_after(trade: int) -> Instant:
    return Instant(_START + (trade + 1) * 900_000_000_000)


def _surfaces(journal: Sequence[ClosedTrade]) -> dict[str, _At]:
    surfaces = {
        "account": _At(lambda _instant: Account(Decimal("10000.00"))),
        "own_journal": _At(
            lambda instant: [t for t in journal if t.closed_at.value_ns <= instant.value_ns]
        ),
    }
    for market in _MARKETS:
        surfaces[f"bars:m15:{market}"] = _At(lambda _instant: None)
        surfaces[f"own_position:{market}"] = _At(lambda _instant: None)
    return surfaces


def _target() -> ExecutionTarget:
    return _ok(
        ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "acct-rc17")
    )


def _host(surfaces: Mapping[str, _At]) -> HostedUnit:
    return _ok(
        construct_unit(
            _compiled(),
            read_surfaces=surfaces,
            scope_id="run-rc17",
            execution_target=_target(),
            motion=MotionSwitch.ON,
        )
    )


def _drive(unit: HostedUnit, instants: Sequence[Instant]) -> list[UnitStep]:
    return [_ok(unit.on_instant(instant)) for instant in instants]


def test_canary_moves_its_filter_number() -> None:
    unit = _host(_surfaces(_journal(25)))

    steps = _drive(unit, [_instant_after(n) for n in range(1, 26)])

    rows = [(i + 1, row) for i, step in enumerate(steps) for row in step.calibrations]
    assert len(rows) == 1
    after, row = rows[0]
    assert after == 20
    assert (row.number, row.old, row.new) == ("min_trend_strength", Decimal(0), Decimal("0.0001"))
    assert (row.from_trade_id, row.to_trade_id, row.count) == ("t01", "t20", 20)
    assert row.rule == "trend-floor-from-record@2"
    assert unit.calibrated_values == {"min_trend_strength": Decimal("0.0001")}
