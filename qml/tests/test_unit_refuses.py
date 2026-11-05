"""What compiler format 2 does not run refuses with a pointer, through `check` and `compile_unit`,
and a unit trades only the sides its `direction` says."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any, cast

import pytest
from qmf.risk.unit_intent import UnitExitIntent
from qml.check import check
from qml.compile import compile_unit
from qml.door import new
from qml.protocol.unit import OwnPosition
from qml.unit.model import Side
from test_compile_dummy import (
    _compiled,
    _context,
    _document,
    _drive,
    _entries,
    _host,
    _instants,
    _slice,
    _surfaces,
)

Document = dict[str, Any]
Edit = Callable[[Document], None]


def _sides(document: Document) -> dict[str, int]:
    bars = _slice()
    steps = _drive(_host(_compiled(document), _surfaces(bars)), _instants(bars))
    directions = [intent.direction.value for _, intent in _entries(steps)]
    return {side: directions.count(side) for side in ("long", "short")}


def test_a_long_only_dummy_enters_long_only() -> None:
    long_only = cast("Document", new(_document(), {"/direction": "long"}))
    short_only = cast("Document", new(_document(), {"/direction": "short"}))

    assert _sides(_document()) == {"long": 2, "short": 23}
    assert _sides(long_only) == {"long": 2, "short": 0}
    assert _sides(short_only) == {"long": 0, "short": 23}

    del long_only["logic"]["short"]
    bound_on_no_stated_side = compile_unit(long_only, _context())
    assert isinstance(bound_on_no_stated_side, tuple)
    assert {(p.kind, p.where) for p in bound_on_no_stated_side} == {
        ("motion_source", "/numbers/rsi_high/motion/source")
    }


def _put(path: str, value: object) -> Edit:
    def edit(document: Document) -> None:
        node: Any = document
        steps = path.split("/")
        for step in steps[:-1]:
            node = node[int(step)] if step.isdigit() else node[step]
        node[steps[-1]] = copy.deepcopy(value)

    return edit


def _defaults(block: str) -> Document:
    parameters = json.loads(_context().entries[block])["parameters"]
    return {name: {"value": str(spec["default"])} for name, spec in parameters.items()}


def _exit_at(index: int, block: str, inputs: Document | None = None) -> Edit:
    """`block` at its default parameters in place of `exit_set[index]`, or beside the three."""

    def edit(document: Document) -> None:
        binding = {
            "name": "probe",
            "scope": "position",
            "block": block,
            "params": _defaults(block),
            "inputs": inputs or {},
        }
        document["exit_set"][index : index + 1] = [binding]

    return edit


def _gate(block: str) -> Edit:
    """`block` at its default parameters beside the long side's two context bindings."""

    def edit(document: Document) -> None:
        document["logic"]["long"]["slots"]["context"]["bindings"].append(
            {
                "name": "probe",
                "block": block,
                "params": _defaults(block),
                "inputs": {"series": "m15"},
            }
        )

    return edit


def _no_stop(document: Document) -> None:
    del document["exit_set"][0]
    del document["numbers"]["stop_buffer"]


def _mirrored(document: Document) -> None:
    document["logic"]["short"] = {"mirror_of": "long"}
    del document["numbers"]["rsi_high"]


_SESSION = {
    "name": "london",
    "calendar_ref": "fx-24x5@1",
    "zone": "Europe/London",
    "windows": [{"from": "08:00", "to": "16:00"}],
}
_BARS = {"series": "m15"}
_PARTS: dict[str, tuple[Edit, str, str]] = {
    "sessions": (_put("sessions", [_SESSION]), "sessions_not_built", "/sessions"),
    "settings": (
        _put("markets/0/settings", {"ema_period": "20"}),
        "settings_not_built",
        "/markets/0/settings",
    ),
    "settings record": (
        _put("markets/0/settings_record", "eurusd-settings@1"),
        "settings_not_built",
        "/markets/0/settings_record",
    ),
    "a number on open positions": (
        _put("numbers/stop_buffer/applies_to_open_positions", True),
        "open_positions_not_built",
        "/numbers/stop_buffer/applies_to_open_positions",
    ),
    "limit": (_put("position_limit", {"per_instrument": 3}), "limit_not_built", "/position_limit"),
    "price": (_put("streams/0/price", "mid"), "price_not_built", "/streams/0/price"),
    "input quotes": (_put("streams/0/input", "quotes"), "input_not_built", "/streams/0/input"),
    "bar kind tick": (
        _put("streams/0/bar", {"kind": "tick", "size": "100"}),
        "bar_not_built",
        "/streams/0/bar",
    ),
    "bar size against the stream's name": (
        _put("streams/0/bar/size", "3600"),
        "bar_not_built",
        "/streams/0/bar",
    ),
    "sole cadence at": (
        _put("numbers/min_trend_strength/motion/cadence", {"at": "market_day_close"}),
        "cadence_not_built",
        "/numbers/min_trend_strength/motion/cadence",
    ),
    "role veto": (
        _put("logic/long/slots/context/role", "veto"),
        "role_not_built",
        "/logic/long/slots/context/role",
    ),
    "two stops": (_exit_at(3, "swing-stop-buffer@1", _BARS), "exit_not_built", "/exit_set/3"),
    "two targets": (_exit_at(3, "target-r-multiple@1"), "exit_not_built", "/exit_set/3"),
    "two per-bar exits": (_exit_at(3, "time-exit-bars@1"), "exit_not_built", "/exit_set/3"),
    "unrealised-profit-cap": (
        _exit_at(2, "unrealised-profit-cap@1", _BARS),
        "exit_not_built",
        "/exit_set/2",
    ),
    "roi-table-exit": (_exit_at(2, "roi-table-exit@1", _BARS), "exit_not_built", "/exit_set/2"),
    "peak-holdings-giveback-exit": (
        _exit_at(2, "peak-holdings-giveback-exit@1", _BARS),
        "exit_not_built",
        "/exit_set/2",
    ),
    "offset-gated-trailing-stop": (
        _exit_at(0, "offset-gated-trailing-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "stepped-profit-stop": (
        _exit_at(0, "stepped-profit-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "profit-fraction-trailing-stop": (
        _exit_at(0, "profit-fraction-trailing-stop@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "an indicator level as the stop": (
        _exit_at(0, "parabolic-sar@1", _BARS),
        "exit_not_built",
        "/exit_set/0",
    ),
    "no stop": (_no_stop, "stop_not_built", "/exit_set"),
    "a volume block": (
        _gate("money-flow-index@1"),
        "block_not_built",
        "/logic/long/slots/context/bindings/2/block",
    ),
    "a session block": (
        _gate("session-running-high@1"),
        "block_not_built",
        "/logic/long/slots/context/bindings/2/block",
    ),
    "period 0": (
        _put("logic/long/slots/context/bindings/0/params/period", {"value": "0"}),
        "bad_params",
        "/logic/long/slots/context/bindings/0",
    ),
    "a rule with a setting missing": (
        _put("numbers/min_trend_strength/motion/rule_params", {}),
        "bad_params",
        "/numbers/min_trend_strength/motion",
    ),
    "a mirror of side-neutral blocks": (_mirrored, "bad_mirror", "/logic/short/mirror_of"),
}


@pytest.mark.parametrize("part", sorted(_PARTS))
def test_each_part_format_2_does_not_run_refuses_with_a_pointer(part: str) -> None:
    edit, kind, where = _PARTS[part]
    document = cast("Document", _document())
    edit(document)

    problems = compile_unit(document, _context())
    checked = check(document, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert {(p.kind, p.where) for p in problems} == {(kind, where)}
    assert checked.verdict.value == "fail"
    assert {pointer for p in checked.errors for pointer in p.where} == {where}


def test_an_hourly_bar_needs_the_hourly_name_because_the_name_is_what_replays() -> None:
    labelled_m15 = new(_document(), {"/streams/0/bar/size": "3600"})
    named_h1 = cast("Document", json.loads(json.dumps(labelled_m15).replace('"m15', '"h1')))

    problems = compile_unit(labelled_m15, _context())

    assert isinstance(problems, tuple), "it compiled"
    assert [p.message for p in problems] == [
        "m15 replays as 900 second bars, and this stream says 3600"
    ]
    assert _compiled(named_h1).plan.stream == "h1"


def test_a_mirror_of_a_side_neutral_block_says_state_both_sides() -> None:
    document = cast("Document", _document())
    _mirrored(document)

    checked = check(document, _context())

    assert {(p.kind.value, p.hint) for p in checked.errors} == {("bad_mirror", "state both sides")}


def test_two_refusals_are_listed_at_once() -> None:
    document = cast("Document", _document())
    _put("sessions", [_SESSION])(document)
    _gate("vwap-session-anchored@1")(document)

    checked = check(document, _context())

    assert {pointer for p in checked.errors for pointer in p.where} == {
        "/sessions",
        "/logic/long/slots/context/bindings/2/block",
    }


def test_a_unit_with_no_time_exit_steps_and_holds_its_position() -> None:
    document = cast("Document", _document())
    del document["exit_set"][2]
    del document["numbers"]["time_out_bars"]
    bars = _slice()
    instants = _instants(bars)[:100]
    compiled = _compiled(document)
    position = OwnPosition(
        "pos-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.08000"),
        compiled.compiled_fingerprint,
        instants[0],
    )

    steps = _drive(
        _host(
            compiled,
            _surfaces(bars, positions=lambda m, _i: position if m == "fx.eurusd" else None),
        ),
        instants,
    )

    assert len(steps) == 100
    assert [i for s in steps for i in s.intents if isinstance(i, UnitExitIntent)] == []
    assert "no_time_exit" in {p.kind.value for p in check(document, _context()).warnings}
