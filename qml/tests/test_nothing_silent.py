"""Foundation check 3: every stdlib block acts or refuses, as a trigger and as an exit, through the
real door over the shipped month. Never "check pass, zero signal, no reason" (UT-01, QML-08)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, Final, cast

from qmf.risk.unit_intent import UnitEntryIntent, UnitExitIntent
from qml.check import check
from qml.compile import CompiledUnit, compile_unit
from qml.protocol.unit import OwnPosition, TraceLevel, construct_unit
from qml.unit.model import Side
from test_compile_dummy import (
    _context,
    _document,
    _instants,
    _ok,
    _slice,
    _surfaces,
    _target,
)

Document = dict[str, Any]

_STDLIB = Path(__file__).resolve().parents[1] / "src" / "qml" / "blocks" / "stdlib"
_MARKET = "fx.eurusd"
_REFUSED, _FIRED, _READ, _SILENT = "refused", "fired", "read", "silent"
_DUMMYS_OWN = frozenset(
    {
        "ema",
        "fixed-fraction-at-stop",
        "market-next-open",
        "percentile-of-own-history",
        "roc-of-series",
        "rsi-cross-back",
        "swing-stop-buffer",
        "target-r-multiple",
        "time-exit-bars",
        "trend-floor-from-record",
    }
)
"""The test helper pins every stdlib block, and layer F scans each pin, so a sweep pins these."""

_FEEDS = "its output is no condition, and R05's feeder rule or binding_not_read answers it"
_CLOSE = "a price series fed whole bars, and R05 compares the bar's close"
_CLOCK = "the runtime passes no time, and R05 feeds it, then binding_not_read answers a lone one"
_HALT = "a halt reads a surface no slot is fed, so R05 must answer it as a binding it cannot read"

PENDING_R05: Final[Mapping[str, str]] = {
    "accelerator-oscillator": _FEEDS,
    "account-daily-loss-halt": _HALT,
    "adx": _FEEDS,
    "alligator-line": _CLOSE,
    "aroon-down": _FEEDS,
    "aroon-oscillator": _FEEDS,
    "aroon-up": _FEEDS,
    "atr-simple": _FEEDS,
    "atr-wilder": _FEEDS,
    "awesome-oscillator": _FEEDS,
    "bar-range-pressure": _FEEDS,
    "bar-true-range": _FEEDS,
    "bears-power": _FEEDS,
    "bulls-power": _FEEDS,
    "cci": _FEEDS,
    "chande-momentum-oscillator": _FEEDS,
    "choppiness-index": _FEEDS,
    "close-to-close-volatility": _FEEDS,
    "demarker": _FEEDS,
    "dickey-fuller-statistic": _FEEDS,
    "efficiency-ratio": _FEEDS,
    "eia-natural-gas-storage-report-clock": _CLOCK,
    "eia-petroleum-status-report-clock": _CLOCK,
    "equity-drawdown-halt": _HALT,
    "fixed-fraction-at-stop": _FEEDS,
    "fractal-high-level": _FEEDS,
    "fractal-low-level": _FEEDS,
    "garman-klass-volatility": _FEEDS,
    "gator-oscillator": _FEEDS,
    "half-life-of-mean-reversion": _FEEDS,
    "heikin-ashi-close": _CLOSE,
    "heikin-ashi-open": _CLOSE,
    "hurst-exponent": _FEEDS,
    "ichimoku-senkou-a": _CLOSE,
    "lbma-gold-auction-clock": _CLOCK,
    "lbma-silver-auction-clock": _CLOCK,
    "linear-regression-slope": _FEEDS,
    "lo-mackinlay-z-statistic": _FEEDS,
    "losing-days-halt": _HALT,
    "macd-histogram": _FEEDS,
    "macd-line": _FEEDS,
    "macd-signal": _FEEDS,
    "minus-directional-indicator": _FEEDS,
    "momentum-ratio": _FEEDS,
    "momersion": _FEEDS,
    "moving-average-fractal-adaptive": _CLOSE,
    "offset-gated-trailing-stop": _FEEDS,
    "parabolic-sar": _FEEDS,
    "parkinson-volatility": _FEEDS,
    "peak-holdings-giveback-exit": _FEEDS,
    "percentage-price-oscillator": _FEEDS,
    "percentile-of-own-history": _FEEDS,
    "permutation-entropy": _FEEDS,
    "perp-funding-settlement-clock": _CLOCK,
    "plus-directional-indicator": _FEEDS,
    "price-channel-midpoint": _CLOSE,
    "profit-fraction-trailing-stop": _FEEDS,
    "relative-vigor-index": _FEEDS,
    "relative-vigor-signal": _FEEDS,
    "return-autocorrelation": _FEEDS,
    "rogers-satchell-volatility": _FEEDS,
    "roi-table-exit": _FEEDS,
    "rolling-standard-deviation": _FEEDS,
    "rsi-series": _FEEDS,
    "session-fill-limit-halt": _HALT,
    "session-loss-limit-halt": _HALT,
    "stepped-profit-stop": _FEEDS,
    "stochastic-d": _FEEDS,
    "stochastic-k": _FEEDS,
    "swing-stop-buffer": _FEEDS,
    "target-r-multiple": _FEEDS,
    "trend-floor-from-record": _FEEDS,
    "trix": _FEEDS,
    "ultimate-oscillator": _FEEDS,
    "unrealised-profit-cap": _FEEDS,
    "variance-ratio": _FEEDS,
    "williams-percent-r": _FEEDS,
    "z-score": _FEEDS,
}
"""Each silent today as a lone trigger, with what ends that. R05 deletes this table."""

READ_NEVER_FIRED: Final[list[str]] = []
"""Read as a condition on the shipped month and never held. A change here is on purpose."""

_CONTEXT = _context()
_BARS = {_MARKET: _slice()[_MARKET]}
_INSTANTS = _instants(_BARS)


def _faces() -> dict[str, Document]:
    return {
        path.parent.parent.name: cast("Document", json.loads(path.read_text("utf-8")))
        for path in sorted(_STDLIB.glob("*/1/entry.json"))
    }


def _probe(face: Document) -> Document:
    """A binding of `face` at its default parameters, feeding a bars port the stream and a series
    port its close."""
    fed = {"bars": "m15", "series": "m15.close"}
    return {
        "name": "probe",
        "block": f"{face['entry_id']}@1",
        "params": {
            name: {"value": str(spec["default"])} for name, spec in face["parameters"].items()
        },
        "inputs": {
            port["port"]: fed[port["stream_kind"]]
            for port in face["inputs"]
            if port["stream_kind"] in fed
        },
    }


def _base(probe: str) -> Document:
    document = cast("Document", _document())
    document["pins"] = [
        pin
        for pin in document["pins"]
        if pin["entry_id"] in _DUMMYS_OWN or pin["entry_id"] == probe
    ]
    document["markets"] = [m for m in document["markets"] if m["market_id"] == _MARKET]
    return document


def _trigger_document(face: Document) -> Document:
    document = _base(face["entry_id"])
    for side in ("long", "short"):
        document["logic"][side]["slots"]["trigger"]["bindings"] = [_probe(face)]
    for number in ("rsi_low", "rsi_high", "rsi_period"):
        del document["numbers"][number]
    return document


def _exit_index(face: Document) -> int | None:
    """Which of the dummy's exits `face` stands in for: its stop, its target or its time exit."""
    output = face["output"]
    if output["type"] == "exit_action":
        return 2
    if output["type"] == "level" and output.get("measure") == "price":
        return 1 if any(port["port"] == "stop_price" for port in face["inputs"]) else 0
    return None


def _exit_document(face: Document) -> Document:
    document = _base(face["entry_id"])
    binding = _probe(face) | {"scope": "position"}
    index = _exit_index(face)
    if index is None:
        document["exit_set"].append(binding)
    else:
        document["exit_set"][index] = binding
    return document


def _compiled(document: Document) -> CompiledUnit | None:
    """The compiled unit, or None when check names a pointer for why it refuses."""
    result = check(document, _CONTEXT)
    if result.verdict.value == "fail":
        assert all(p.where and all(p.where) for p in result.errors), result.errors
        return None
    built = compile_unit(document, _CONTEXT)
    assert isinstance(built, CompiledUnit), built
    return built


def _surfaces_for(position: OwnPosition | None = None) -> dict[str, Any]:
    surfaces = _surfaces(_BARS, positions=lambda _m, _i: position)
    return {key: at for key, at in surfaces.items() if "metal.xauusd" not in key}


def _as_trigger(face: Document) -> str:
    compiled = _compiled(_trigger_document(face))
    if compiled is None:
        return _REFUSED
    unit = _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces_for(),
            scope_id="sweep",
            execution_target=_target(),
            trace_level=TraceLevel.EVERY_BAR,
        )
    )
    read = False
    for instant in _INSTANTS:
        for row in _ok(unit.on_instant(instant)).decisions:
            if "trigger:" not in row.reason:
                return _FIRED
            read = read or "trigger: does not hold" in row.reason
    return _READ if read else _SILENT


def _as_exit(face: Document) -> str:
    compiled = _compiled(_exit_document(face))
    if compiled is None:
        return _REFUSED
    index = _exit_index(face)
    position = (
        OwnPosition(
            "pos-1",
            Side.LONG,
            Decimal("0.10"),
            Decimal("1.08000"),
            compiled.compiled_fingerprint,
            _INSTANTS[0],
        )
        if index == 2
        else None
    )
    unit = _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces_for(position),
            scope_id="sweep",
            execution_target=_target(),
        )
    )
    for instant in _INSTANTS:
        for intent in _ok(unit.on_instant(instant)).intents:
            if isinstance(intent, UnitExitIntent):
                return _FIRED
            if isinstance(intent, UnitEntryIntent) and (index == 0 or intent.protection.targets):
                return _FIRED
    return _SILENT


def test_every_stdlib_block_acts_or_refuses() -> None:
    faces = _faces()

    triggers = {name: _as_trigger(face) for name, face in faces.items()}
    exits = {name: _as_exit(face) for name, face in faces.items()}

    silent = sorted(name for name, found in triggers.items() if found == _SILENT)
    silent += sorted(f"{name} as an exit" for name, found in exits.items() if found == _SILENT)
    assert silent == sorted(PENDING_R05)
    assert [name for name, found in triggers.items() if found == _READ] == READ_NEVER_FIRED
    assert sorted(name for name, found in exits.items() if found != _REFUSED) == [
        "swing-stop-buffer",
        "target-r-multiple",
        "time-exit-bars",
    ]
    assert len(faces) == 112
