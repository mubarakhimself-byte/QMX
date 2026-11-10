"""The one price call: a moved fraction, the size band, and account facts out of the exit pass.

The three seams are the section's Verify, unit block: the band catches a 5,000-lot answer, the
sizer reads a moved fraction from evidence, and `on_instant` reads no account fact while a
position is open.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qml.blocks.api import Amount, Block, EntryFace, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol import unit as hosted
from qml.protocol.unit import HostedUnit, Surface, TraceLevel, construct_unit
from qml.unit.model import Side

from test_compile_dummy import _MARKETS, _compiled, _instants, _slice

_QML = Path(__file__).resolve().parents[1]
_RECORDS = _QML / "tests" / "fixtures" / "records"
_EQUITY = Decimal("100000")
_START = Instant(1_740_952_800_000_000_000)
_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert not isinstance(result, TypedRefusal), result
    return result.value


@cache
def _dummy() -> CompiledUnit:
    return _compiled()


def _record(name: str) -> InstrumentRecord:
    parsed = parse_record(json.loads((_RECORDS / f"{name}.json").read_text("utf-8")))
    assert not is_refusal(parsed), parsed
    return parsed.value


def _target() -> ExecutionTarget:
    return _ok(
        ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "price-call")
    )


def _sizer_2() -> Block:
    """The shipped `@2`, loaded through the one loader."""
    folder = _QML / "src" / "qml" / "blocks" / "stdlib" / "fixed-fraction-at-stop" / "2"
    face = parse_entry((folder / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    loaded = load(
        [LockEntry(face.entry_id, face.version, face.fingerprint)],
        {face.pin: (folder / "block.py").read_bytes()},
    )
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks[face.pin]


class _Answering:
    """A sizer that answers one fixed Amount, as a Library block in the slot could."""

    def __init__(self, answer: Amount) -> None:
        self._answer = answer

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Amount:
        del evidence
        return self._answer

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _At:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        del instant
        return self._answer


class _RecordingAccount:
    """The account surface, recording that its one fact was asked for."""

    def __init__(self, reads: set[str]) -> None:
        self._reads = reads

    def at(self, instant: Instant, /) -> object:
        del instant
        self._reads.add("equity")
        return hosted.Account(_EQUITY)


def _surfaces() -> dict[str, Surface]:
    surfaces: dict[str, Surface] = {
        "account": _At(hosted.Account(_EQUITY)),
        "own_journal": _At(()),
    }
    for market in _MARKETS:
        surfaces[f"bars:m15:{market}"] = _At(None)
        surfaces[f"own_position:{market}"] = _At(lambda _i: ())
    return surfaces


def _host(compiled: CompiledUnit, surfaces: Mapping[str, Surface]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-price",
            execution_target=_target(),
            trace_level=TraceLevel.EVERY_BAR,
        )
    )


def _with_sizer(compiled: CompiledUnit, sizer: object) -> HostedUnit:
    """The dummy hosted with `sizer` standing in the slot on XAUUSD."""
    unit = _host(compiled, _surfaces())
    for market in unit._core.markets:  # pyright: ignore[reportPrivateUsage]
        market.instances["sizer"] = sizer  # pyright: ignore[reportArgumentType]
    return unit


def _proposal(fraction: str) -> hosted.Proposal:
    return hosted.Proposal(
        wire={},
        row=hosted.DecisionRow(
            row_id="row-5000",
            instant=_START,
            market_id="metal.xauusd",
            side=Side.LONG,
            outcome="taken",
            slot_trail=(),
            numbers_in_force={"risk_fraction": Decimal(fraction)},
            reason="all slots hold",
        ),
        market_id="metal.xauusd",
        side=Side.LONG,
        entry_price=Decimal("2650.00"),
        stop=Decimal("2635.50"),
        params={"fraction": Decimal(fraction)},
        record=_record("xauusd"),
    )


def test_the_band_catches_5000_lots() -> None:
    band = hosted.SizeBand(max_lots=Decimal("100"))
    five_thousand = Amount("quantity", Decimal(5000), "gross_at_stop")
    unit = _with_sizer(_dummy(), _Answering(five_thousand))

    priced = unit.price(_proposal("0.05"), hosted.Account(_EQUITY), band)

    assert priced.code == "size_band"
    assert priced.intent is None
    assert priced.row.outcome == "skipped"

    too_much_money = Amount("money_at_risk", Decimal(200001), "gross_at_stop")
    capped = _with_sizer(_dummy(), _Answering(too_much_money)).price(
        _proposal("0.05"), hosted.Account(_EQUITY), band
    )

    assert capped.code == "per_trade_cap"
    assert capped.intent is None


def test_the_sizer_reads_a_moved_fraction() -> None:
    sizer = _sizer_2().make({"fraction": Decimal("0.005")}, {})
    evidence = {
        "equity": _EQUITY,
        "entry_price": Decimal("1.10000"),
        "stop_price": Decimal("1.09500"),
        "record": _record("eurusd"),
    }

    moved = cast("Amount", sizer.update(evidence | {"fraction": Decimal("0.0049")}))
    seeded = cast("Amount", sizer.update(evidence))

    assert moved == Amount(kind="money_at_risk", value=Decimal(490), basis="gross_at_stop")
    assert seeded == Amount(kind="money_at_risk", value=Decimal(500), basis="gross_at_stop")


def test_account_facts_never_reach_the_exit_pass() -> None:
    compiled = _dummy()
    bars = _slice()
    instants = _instants(bars)
    reads: set[str] = set()
    held = hosted.OwnPosition(
        "p1",
        Side.LONG,
        Decimal("1.00"),
        Decimal("1.10000"),
        compiled.logic_fingerprint,
        instants[0],
    )
    surfaces: dict[str, Surface] = {"account": _RecordingAccount(reads), "own_journal": _At(())}
    for market, series in bars.items():
        surfaces[f"bars:m15:{market}"] = _At(series[0])
        surfaces[f"own_position:{market}"] = _At((held,) if market == "fx.eurusd" else ())
    unit = _host(compiled, surfaces)

    step = _ok(unit.on_instant(instants[0]))

    assert step.decisions, "the unit ran its exits pass"
    assert reads == set()
