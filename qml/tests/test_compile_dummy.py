"""The dummy compiles, runs inside QML over a recorded month, and tunes one number (A5)."""

from __future__ import annotations

import bisect
import csv
import json
import os
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmf.core.chrono import CalendarIdentity, Instant
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import RefusalCategory, Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UnitEntryIntent, UnitExitIntent
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.declaration import BotDefinition, mint_bot_definition, mint_confluence
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qml.motion import ClosedTrade
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol import construct_bot
from qml.protocol.unit import (
    OHLC,
    Account,
    HostedUnit,
    MotionSwitch,
    OwnPosition,
    QuoteBar,
    UnitStep,
    construct_unit,
    restore_unit,
)
from qml.unit.model import Side

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_DUMMY = _QML / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
_SLICES = _QML / "tests" / "fixtures" / "slices"
_REAL = Path(os.environ.get("QML_REAL_SLICE_DIR", "D:/QMX-worktrees/unit-ship/data/dukascopy-node"))
_MARKETS = {"fx.eurusd": ("eurusd", "eurusd"), "metal.xauusd": ("xauusd", "xauusd")}
_FLAT: Mapping[str, OwnPosition] = {}
_START = 1_740_952_800_000_000_000  # 2025-03-02 22:00 UTC


_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert not isinstance(result, TypedRefusal), result
    return result.value


def _document() -> dict[str, object]:
    document = cast("dict[str, object]", json.loads(_DUMMY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for folder in sorted(p for p in _STDLIB.iterdir() if (p / "1" / "entry.json").is_file()):
        face = parse_entry((folder / "1" / "entry.json").read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append({"entry_id": face.entry_id, "version": 1, "fingerprint": face.fingerprint})
    document["pins"] = pins
    return document


def _context() -> CompileContext:
    ids = [p.name for p in _STDLIB.iterdir() if (p / "1" / "block.py").is_file()]
    records: dict[str, InstrumentRecord] = {}
    for market_id, (record_file, _) in _MARKETS.items():
        raw = json.loads(
            (_QML / "tests" / "fixtures" / "records" / f"{record_file}.json").read_text("utf-8")
        )
        records[market_id] = _ok(parse_record(raw))
    return CompileContext(
        sources={f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in ids},
        entries={f"{i}@1": (_STDLIB / i / "1" / "entry.json").read_bytes() for i in ids},
        records=records,
    )


def _compiled(document: dict[str, object] | None = None) -> CompiledUnit:
    compiled = compile_unit(document if document is not None else _document(), _context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _bars(folder: Path, prefix: str, symbol: str) -> list[QuoteBar]:
    def side(name: str) -> dict[int, OHLC]:
        path = folder / f"{prefix}{symbol}-m15-{name}-2025-03-01-2025-04-01.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            return {
                int(row["timestamp"]): OHLC(
                    Decimal(row["open"]),
                    Decimal(row["high"]),
                    Decimal(row["low"]),
                    Decimal(row["close"]),
                )
                for row in csv.DictReader(handle)
            }

    bid, ask = side("bid"), side("ask")
    return [
        QuoteBar(Instant((ms + 900_000) * 1_000_000), bid[ms], ask[ms])
        for ms in sorted(bid.keys() & ask.keys())
    ]


def _slice(folder: Path = _SLICES, prefix: str = "synthetic-") -> dict[str, list[QuoteBar]]:
    return {market: _bars(folder, prefix, symbol) for market, (_, symbol) in _MARKETS.items()}


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


def _latest(bars: Sequence[QuoteBar]) -> _At:
    stamps = [b.knowable_at.value_ns for b in bars]

    def answer(instant: Instant) -> object:
        index = bisect.bisect_right(stamps, instant.value_ns)
        return bars[index - 1] if index else None

    return _At(answer)


def _target() -> ExecutionTarget:
    return _ok(
        ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "acct-a5")
    )


def _surfaces(
    bars: Mapping[str, Sequence[QuoteBar]],
    journal: Sequence[ClosedTrade] = (),
    positions: Callable[[str, Instant], OwnPosition | None] = lambda _m, _i: None,
) -> dict[str, _At]:
    surfaces = {
        "account": _At(lambda _i: Account(Decimal("10000.00"))),
        "own_journal": _At(lambda i: [t for t in journal if t.closed_at.value_ns <= i.value_ns]),
    }
    for market in _MARKETS:
        surfaces[f"bars:m15:{market}"] = _latest(bars.get(market, ()))
        surfaces[f"own_position:{market}"] = _At(lambda i, m=market: positions(m, i))
    return surfaces


def _host(
    compiled: CompiledUnit, surfaces: Mapping[str, _At], motion: MotionSwitch = MotionSwitch.ON
) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-a5",
            execution_target=_target(),
            motion=motion,
        )
    )


def _instants(bars: Mapping[str, Sequence[QuoteBar]]) -> list[Instant]:
    stamps = sorted({b.knowable_at.value_ns for series in bars.values() for b in series})
    return [Instant(ns) for ns in stamps]


def _drive(unit: HostedUnit, instants: Sequence[Instant]) -> list[UnitStep]:
    return [_ok(unit.on_instant(instant)) for instant in instants]


def _entries(steps: Sequence[UnitStep]) -> list[tuple[UnitStep, UnitEntryIntent]]:
    return [(s, i) for s in steps for i in s.intents if isinstance(i, UnitEntryIntent)]


# --- compile ------------------------------------------------------------------------


def test_the_dummy_compiles_to_a_stable_fingerprint_that_moves_with_the_document() -> None:
    first, second = _compiled(), _compiled()
    changed = _document()
    numbers = cast("dict[str, dict[str, object]]", changed["numbers"])
    numbers["ema_period"]["default"] = "99"

    assert first.compiled_fingerprint == second.compiled_fingerprint
    assert _compiled(changed).compiled_fingerprint != first.compiled_fingerprint
    assert first.warm_up == {"m15": 921}  # EMA(100) settles at 900, then ROC(20) needs 21 more
    assert first.placeholders == ("swing_stop", "target_2r", "time_out", "fixed_fraction")


def test_compile_names_every_problem_at_once() -> None:
    document = _document()
    document["pins"] = [
        p for p in cast("list[dict[str, object]]", document["pins"]) if p["entry_id"] != "ema"
    ]
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["rsi_low"]["motion"] = {
        "mode": "percentile_of_own_history",
        "source": "price",
        "rule_params": {"percentile": "20", "window_bars": "500"},
    }

    problems = compile_unit(document, _context())

    assert isinstance(problems, tuple)
    assert {(p.kind, p.where) for p in problems} == {
        ("block_not_pinned", "/logic/long/slots/context/bindings/0/block"),
        ("block_not_pinned", "/logic/short/slots/context/bindings/0/block"),
        ("motion_source", "/numbers/rsi_low/motion/source"),
    }


# --- the month ------------------------------------------------------------------------


def _check_month(bars: dict[str, list[QuoteBar]]) -> None:
    compiled = _compiled()
    instants = _instants(bars)
    first = _drive(_host(compiled, _surfaces(bars)), instants)
    second = _drive(_host(compiled, _surfaces(bars)), instants)
    assert first == second

    entries = _entries(first)
    assert entries, "the dummy entered at least once"
    for step, intent in entries:
        stop = intent.protection.stop
        assert intent.quantity.value > 0
        assert not isinstance(stop, str)
        assert intent.protection.time_exit_bars == 48
        assert intent.not_before.value_ns <= step.instant.value_ns
        assert intent.placeholder_labels == compiled.placeholders
        warm = [
            b for b in bars[intent.market_id] if b.knowable_at.value_ns <= step.instant.value_ns
        ]
        assert len(warm) >= 921, "no entry before the derived warm-up"
    events = [e for s in first for e in s.state_events]
    assert [(e.kind, e.market_id) for e in events] == [
        ("warming", "fx.eurusd"),
        ("warming", "metal.xauusd"),
        ("ready", "fx.eurusd"),
        ("ready", "metal.xauusd"),
    ]
    rows = [d for s in first for d in s.decisions]
    assert all("rsi_low" in d.numbers_in_force for d in rows)
    assert len({d.numbers_in_force["rsi_low"] for d in rows}) > 1, "rsi_low moves with the RSI"
    assert all(not s.calibrations for s in first), "no closed trades, so no calibration"


def test_two_drives_over_the_synthetic_month_give_the_same_steps() -> None:
    _check_month(_slice())


@pytest.mark.skipif(not _REAL.is_dir(), reason="the saved Dukascopy month is not on this machine")
def test_two_drives_over_the_real_month_give_the_same_steps() -> None:
    _check_month(_slice(_REAL, ""))


def test_a_restored_unit_continues_exactly_where_it_stopped() -> None:
    bars = _slice()
    instants = _instants(bars)
    compiled = _compiled()
    whole = _drive(_host(compiled, _surfaces(bars)), instants)
    part = _host(compiled, _surfaces(bars))
    head = _drive(part, instants[:1500])
    resumed = _ok(
        restore_unit(
            part.snapshot(),
            compiled,
            read_surfaces=_surfaces(bars),
            scope_id="run-a5",
            execution_target=_target(),
        )
    )
    assert head + _drive(resumed, instants[1500:]) == whole

    other = _compiled(_with_default("ema_period", "99"))
    cold = _ok(
        restore_unit(
            part.snapshot(),
            other,
            read_surfaces=_surfaces(bars),
            scope_id="run-a5",
            execution_target=_target(),
        )
    )
    first = _ok(cold.on_instant(instants[0]))
    assert [(e.kind, e.reason) for e in first.state_events][:1] == [
        ("cold_start", "the snapshot belongs to another compiled fingerprint")
    ]


def _with_default(name: str, value: str) -> dict[str, object]:
    document = _document()
    cast("dict[str, dict[str, object]]", document["numbers"])[name]["default"] = value
    return document


# --- exits for its own positions ------------------------------------------------------


def test_exits_run_only_for_positions_this_compiled_fingerprint_opened() -> None:
    bars = _slice()
    compiled = _compiled()
    instants = _instants(bars)[:100]
    opened_at = instants[0]

    def held(by: Fingerprint) -> Callable[[str, Instant], OwnPosition | None]:
        position = OwnPosition(
            "pos-1", Side.LONG, Decimal("0.10"), Decimal("1.08000"), by, opened_at
        )
        return lambda market, _i: position if market == "fx.eurusd" else None

    other = _ok(fingerprint({"another": "version"}))
    mine = _drive(
        _host(compiled, _surfaces(bars, positions=held(compiled.compiled_fingerprint))), instants
    )
    theirs = _drive(_host(compiled, _surfaces(bars, positions=held(other))), instants)

    exits = [(i, s.instant) for s in mine for i in s.intents if isinstance(i, UnitExitIntent)]
    assert len(exits) == 1
    intent, at = exits[0]
    assert intent.kind.value == "close_full"
    assert intent.position_ref.opened_by == compiled.compiled_fingerprint
    assert at == instants[47], "the 48th bar the position is held"
    assert not [i for s in theirs for i in s.intents if isinstance(i, UnitExitIntent)]


# --- the slow number ------------------------------------------------------------------


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
    """Weak trends lose and strong ones win, so the edge is 0.0012 (buckets of 0.0006)."""
    return [
        _trade(n, "0.0003", "-1") if n % 3 == 0 else _trade(n, "0.0015", "1.5")
        for n in range(1, count + 1)
    ]


def _instant_after(trade: int) -> Instant:
    return Instant(_START + (trade + 1) * 900_000_000_000)


def _motion_steps(
    motion: MotionSwitch,
    positions: Callable[[str, Instant], OwnPosition | None] = lambda _m, _i: None,
) -> tuple[HostedUnit, list[UnitStep]]:
    unit = _host(_compiled(), _surfaces({}, _journal(25), positions), motion)
    return unit, _drive(unit, [_instant_after(n) for n in range(1, 26)])


def test_min_trend_strength_moves_one_shrunk_step_after_its_20th_trade() -> None:
    unit, steps = _motion_steps(MotionSwitch.ON)

    rows = [(i + 1, row) for i, s in enumerate(steps) for row in s.calibrations]
    assert len(rows) == 1
    after, row = rows[0]
    assert after == 20
    assert (row.number, row.old, row.new) == ("min_trend_strength", Decimal(0), Decimal("0.0001"))
    assert (row.from_trade_id, row.to_trade_id, row.count) == ("t01", "t20", 20)
    assert row.rule == "trend-floor-from-record@1"
    assert unit.calibrated_values == {"min_trend_strength": Decimal("0.0001")}


def test_motion_off_keeps_min_trend_strength_at_its_default() -> None:
    unit, steps = _motion_steps(MotionSwitch.OFF)

    assert not [row for s in steps for row in s.calibrations]
    assert unit.calibrated_values == {"min_trend_strength": Decimal(0)}


def test_min_trend_strength_waits_for_the_unit_to_be_flat() -> None:
    open_until = _instant_after(22).value_ns
    position = OwnPosition(
        "pos-9",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.08000"),
        Fingerprint("fp1:sha256:" + "c" * 64),
        Instant(_START),
    )

    def positions(_market: str, instant: Instant) -> OwnPosition | None:
        return position if instant.value_ns < open_until else None

    _, steps = _motion_steps(MotionSwitch.ON, positions)

    assert [i + 1 for i, s in enumerate(steps) if s.calibrations] == [22]


# --- the wrong door -------------------------------------------------------------------


def _pinned(tag: str) -> ProducerBinding:
    return _ok(ProducerBinding.try_create(_ok(fingerprint({"class": "test-producer", "tag": tag}))))


def _bot_declaration() -> BotDefinition:
    calendar = _ok(CalendarIdentity.try_create("forex-17NY", "v3", "2025.2"))
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": _pinned("zone")}]))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 900}],
                    "stream_role": "trading",
                }
            ],
            [calendar],
            [_pinned("ema")],
        )
    )
    logic = _ok(mint_logic_identity("dummy-as-bot", "1.0.0", {"bot.py": "BOT = None\n"}))
    return _ok(
        mint_bot_definition(
            strategy_family_id="trend-pullback",
            confluence_set=[confluence],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 200},
                    "step": 1,
                    "default": 20,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            permitted_exit_intents=(),
            logic_reference=logic,
        )
    )


def test_construct_bot_on_the_units_factory_refuses_at_its_first_sized_intent() -> None:
    bars = _slice()
    compiled = _compiled()
    instants = _instants(bars)
    through_door = _drive(_host(compiled, _surfaces(bars)), instants)
    first_entry = next(i for i, s in enumerate(through_door) if s.intents)

    factory = compiled.factory.hosting(
        _surfaces(bars), scope_id="run-a5", execution_target=_target()
    )
    bot = _ok(
        construct_bot(
            factory, declaration=_bot_declaration(), assignment={"lookback": 20}, read_surfaces={}
        )
    )
    answers = [bot.on_instant(instant) for instant in instants[: first_entry + 1]]

    assert all(not is_refusal(a) and a.value == () for a in answers[:-1])
    refused = answers[-1]
    assert isinstance(refused, TypedRefusal)
    assert refused.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert refused.context["field"] == "contract_format_version"
    unbound = construct_bot(
        compiled.factory,
        declaration=_bot_declaration(),
        assignment={"lookback": 20},
        read_surfaces={},
    )
    assert isinstance(unbound, TypedRefusal)


def test_a_bar_knowable_after_the_instant_is_refused() -> None:
    bars = _slice()
    early = Instant(bars["fx.eurusd"][0].knowable_at.value_ns - 1)
    surfaces = _surfaces(bars) | {"bars:m15:fx.eurusd": _At(lambda _i: bars["fx.eurusd"][0])}

    refused = _host(_compiled(), surfaces).on_instant(early)

    assert isinstance(refused, TypedRefusal)
    assert refused.context["reason"] == "a bar knowable after the instant is a look-ahead"
