"""The shipped exits read their number from evidence, and the make value only seeds it (AD-14).

The stop, target and time-exit placeholders held the ``make`` value and ignored a number that
moved, so a calibrated exit number could never reach an exit. These tests call the three ``@2``
versions the way the host does: the parameter arrives in ``evidence`` on every update, and a
call without it answers the seeded value. The third test puts the section's six exits on one
unit and reads what the compiler does with each.

Every instance is loaded through the one loader, so a wrong entry fingerprint or a block that
does not meet the protocol fails here rather than in a host.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmf.risk.unit_intent import UnitExitIntent
from qml.blocks.api import Block, EntryFace, ExitAction, Instance, Side, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.compile import CompiledUnit, compile_unit
from qml.protocol.unit import OwnPosition
from test_compile_dummy import (
    _compiled,
    _context,
    _document,
    _drive,
    _host,
    _slice,
    _surfaces,
)

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_MARKET = "fx.eurusd"
_PINS = ("swing-stop-buffer@2", "target-r-multiple@2", "time-exit-bars@2")
"""The versions this PR adds, in the order the dummy binds them."""

_SIX = (
    "offset-gated-trailing-stop@1",
    "profit-fraction-trailing-stop@1",
    "peak-holdings-giveback-exit@1",
    "roi-table-exit@1",
    "stepped-profit-stop@1",
    "time-exit-bars@2",
)
"""The section's six exits on one unit: the five trails the compiler refuses, and the time exit."""

_PARAMS: Mapping[str, Mapping[str, str]] = {
    "swing-stop-buffer@2": {"buffer": "0.0002"},
    "target-r-multiple@2": {"multiple": "2.0"},
    "offset-gated-trailing-stop@1": {"offset": "0.03", "distance": "0.02"},
    "profit-fraction-trailing-stop@1": {
        "offset": "0.03",
        "share": "0.5",
        "min_distance": "0.001",
        "max_distance": "0.05",
    },
    "peak-holdings-giveback-exit@1": {"giveback": "0.5"},
    "roi-table-exit@1": {
        "roi_0": "0.1",
        "bars_1": "10",
        "roi_1": "0.05",
        "bars_2": "20",
        "roi_2": "0.02",
        "bars_3": "30",
        "roi_3": "0",
    },
    "stepped-profit-stop@1": {
        "trigger_1": "0.01",
        "lock_1": "0.001",
        "trigger_2": "0.02",
        "lock_2": "0.005",
        "trigger_3": "0.03",
        "lock_3": "0.01",
    },
    "time-exit-bars@2": {"bars": "48"},
}
"""Each pin at the parameters it is called with: the shipped defaults, written out."""

_LOWS = (Decimal("1.0850"), Decimal("1.0840"), Decimal("1.0820"), Decimal("1.0830"), Decimal("1.0840"))
"""Five lows whose middle is the swing: below the two before it, and not above the two after."""


def _folder(pin: str) -> Path:
    entry_id, _, version = pin.partition("@")
    return _STDLIB / entry_id / version


def _face(pin: str) -> EntryFace:
    face = parse_entry((_folder(pin) / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


def _block(pin: str) -> Block:
    """One pinned block, loaded the one way QMX loads block source."""
    face = _face(pin)
    loaded = load(
        [LockEntry(face.entry_id, face.version, face.fingerprint)],
        {pin: (_folder(pin) / "block.py").read_bytes()},
    )
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks[pin]


def _made(pin: str, side: Side = Side.LONG) -> Instance:
    params = {name: Decimal(value) for name, value in _PARAMS[pin].items()}
    return _block(pin).make(params, {}, side)


def _bars(lows: Sequence[Decimal] = _LOWS) -> list[Mapping[str, Decimal]]:
    """One closed bar per low, with a high and close beside it for the exits that read them."""
    return [
        {"high": low + Decimal("0.0010"), "low": low, "close": low + Decimal("0.0005")}
        for low in lows
    ]


def _short_only() -> dict[str, object]:
    """The shipped dummy on one market, trading the short side alone."""
    document = _document()
    document["direction"] = "short"
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    return document


def _six_exits() -> dict[str, object]:
    """The dummy's logic, sizer and numbers, with the section's six exits written instead."""
    document = _document()
    numbers = document["numbers"]
    assert isinstance(numbers, dict)
    for gone in ("stop_buffer", "target_r", "time_out_bars"):
        del numbers[gone]
    document["exit_set"] = [
        {
            "name": pin.partition("@")[0].replace("-", "_"),
            "scope": "position",
            "block": pin,
            "params": {name: {"value": value} for name, value in _PARAMS[pin].items()},
            "inputs": {
                port.port: "m15" for port in _face(pin).inputs if port.stream_kind == "bars"
            },
        }
        for pin in _SIX
    ]
    return document


def test_target_reads_a_moved_multiple() -> None:
    moved = _made("target-r-multiple@2").update(
        {
            "entry_price": Decimal("1.1000"),
            "stop_price": Decimal("1.0950"),
            "multiple": Decimal("1.9"),
        }
    )
    seeded = _made("target-r-multiple@2").update(
        {"entry_price": Decimal("1.1000"), "stop_price": Decimal("1.0950")}
    )

    assert (moved, seeded) == (Decimal("1.1095"), Decimal("1.1100"))


def test_the_stop_reads_a_moved_buffer() -> None:
    def driven(buffer: Decimal | None) -> object:
        stop = _made("swing-stop-buffer@2")
        answer: object = None
        for bar in _bars():
            evidence: dict[str, object] = {"series": bar}
            if buffer is not None:
                evidence["buffer"] = buffer
            answer = stop.update(evidence)
        return answer

    assert (driven(Decimal("0.01")), driven(None)) == (
        Decimal("1.07118"),
        Decimal("1.0817836"),
    )


def test_time_exit_answers_its_own_reason() -> None:
    bars = _slice()[_MARKET]
    compiled = _compiled(_short_only())
    held = OwnPosition(
        "pos-1",
        Side.SHORT,
        Decimal("0.10"),
        Decimal("1.08000"),
        compiled.compiled_fingerprint,
        bars[0].knowable_at,
    )
    surfaces = _surfaces(
        {_MARKET: bars},
        positions=lambda market, _i: held if market == _MARKET else None,
    )
    unit = _host(
        compiled,
        {key: surface for key, surface in surfaces.items() if "metal.xauusd" not in key},
    )

    steps = _drive(unit, [bar.knowable_at for bar in bars[:48]])

    closes = [
        (one.kind.value, one.reason_code.code)
        for step in steps
        for one in step.intents
        if isinstance(one, UnitExitIntent)
    ]
    assert closes == [("close_full", "time")]


def test_the_time_exit_closes_on_the_bar_a_moved_count_names() -> None:
    time_exit = _made("time-exit-bars@2")
    answers = [time_exit.update({"bars": Decimal("3")}) for _ in range(4)]

    assert answers[:3] == [None, None, ExitAction(kind="close_full", reason_code="time")]


def test_six_exits_on_one_unit_are_each_run_or_named() -> None:
    """The section's six exits on one unit, each either run or refused by name.

    The seam is the compiler's answer, because the five trails are refused by shape at this
    head: a trail reads the position, and an exit only gets the amend path at AD-13 step 3. No
    exit is dropped silently, and the three @2 versions compile on one unit together.
    """
    refused = compile_unit(_six_exits(), _context())
    assert isinstance(refused, tuple), refused
    assert [(problem.kind, problem.where) for problem in refused] == [
        ("exit_not_built", f"/exit_set/{index}") for index in range(len(_SIX) - 1)
    ]

    runs = compile_unit(_document(), _context())
    assert isinstance(runs, CompiledUnit), runs
    assert [exit_plan.binding.pin for exit_plan in runs.plan.exits] == list(_PINS)
