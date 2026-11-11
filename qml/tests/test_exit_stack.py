"""The exit stack: every per-bar exit runs each bar, on its side's bars, in a fixed order.

The section's Verify, unit block, less the import test, which has its own file. A short's
protective stop reads the ask bars, so it feels the spread. Three per-bar exits answering on one
bar run the full one, by its reason code, and nothing runs before a full close answers. A raising
exit is skipped for the next one and becomes a ``Fault`` with phase ``exit``.

Each test compiles a document whose per-bar exits are blocks pinned in the test's own bytes, the
way a Library block is pinned, and drives the unit door with the shipped slice's bars or with
bars written for the case.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qmf.core.chrono import Instant
from qmf.risk.unit_intent import UnitExitIntent
from qml.catalogue import block_fingerprint
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.protocol.unit import (
    OHLC,
    Account,
    HostedUnit,
    HostPort,
    OwnPosition,
    QuoteBar,
    Surface,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side
from test_compile_dummy import _context, _document, _ok, _slice, _target

_MARKET = "fx.eurusd"
_EQUITY = Decimal("100000")
_START = 1_740_952_800_000_000_000  # 2025-03-02 22:00 UTC, the shipped slice's first bar
_BAR_NS = 900_000_000_000

_ANSWER = '''"""One per-bar exit that answers one action, with its reason code."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import ExitAction, Side

_KIND = KIND_PLACEHOLDER
_CODE = CODE_PLACEHOLDER


class _Answer:
    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> ExitAction:
        del evidence
        return ExitAction(kind=_KIND, reason_code=_CODE)

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Answer:
        del params, inputs, side
        return _Answer()


BLOCK = _Block()
'''

_LATER_FULL = '''"""One per-bar exit that closes on its second held bar, so a bar can run without it."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import ExitAction, Side


class _Answer:
    def __init__(self) -> None:
        self._bars = 0

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> ExitAction | None:
        del evidence
        self._bars += 1
        if self._bars < 2:
            return None
        return ExitAction(kind="close_full", reason_code="rc11-full")

    def export_state(self) -> Mapping[str, object]:
        return {"bars": self._bars}

    def import_state(self, state: Mapping[str, object]) -> None:
        self._bars = int(state["bars"])


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Answer:
        del params, inputs, side
        return _Answer()


BLOCK = _Block()
'''

_RAISES = '''"""A Library block with a bug: every call raises, so the exit step must skip it."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side


class _Answer:
    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        raise RuntimeError("the Library block's own bug")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Answer:
        del params, inputs, side
        return _Answer()


BLOCK = _Block()
'''


def _answering(kind: str, code: str) -> str:
    return _ANSWER.replace("KIND_PLACEHOLDER", f'"{kind}"').replace("CODE_PLACEHOLDER", f'"{code}"')


class _Latest:
    """The last bar of the series knowable at the instant, as a host serves it."""

    def __init__(self, bars: Sequence[QuoteBar]) -> None:
        self._bars = bars

    def at(self, instant: Instant, /) -> object:
        held = [bar for bar in self._bars if bar.knowable_at.value_ns <= instant.value_ns]
        return held[-1] if held else None


class _Fixed:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        del instant
        return self._answer


class _Asks:
    """A host's last fall-through, asked to close a position its exits could not."""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def close_scope(self, unit: object, why: str) -> None:
        del unit
        self.asked.append(why)


def _entry(pin: str, source: str) -> str:
    entry_id, _, version = pin.partition("@")
    face: dict[str, object] = {
        "schema": "qmx.entry/1",
        "entry_id": entry_id,
        "version": int(version),
        "component_type": "exit",
        "origin": "library",
        "inputs": [],
        "output": {"type": "exit_action", "measure": "ratio"},
        "parameters": {},
        "mirroring": "not_applicable",
        "fingerprint": block_fingerprint(source.encode()).value,
    }
    return json.dumps(face, indent=1)


def _context_with(blocks: Mapping[str, str]) -> CompileContext:
    base = _context()
    sources = dict(base.sources)
    entries = dict(base.entries)
    for pin, source in blocks.items():
        sources[pin] = source.encode()
        entries[pin] = _entry(pin, source).encode()
    return CompileContext(sources=sources, entries=entries, records=base.records)


def _document_with(
    exits: Sequence[Mapping[str, object]], blocks: Mapping[str, str]
) -> dict[str, object]:
    """The shipped dummy on one market, its long side, and the exits this case writes."""
    document = _document()
    document["direction"] = "long"
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    document["exit_set"] = [
        {
            "name": "swing_stop",
            "scope": "position",
            "block": "swing-stop-buffer@1",
            "params": {"buffer": {"number": "stop_buffer"}},
            "inputs": {"series": "m15"},
        },
        *exits,
    ]
    numbers = cast("dict[str, object]", document["numbers"])
    for gone in ("target_r", "time_out_bars"):
        numbers.pop(gone, None)
    pins = cast("list[dict[str, object]]", document["pins"])
    for pin, source in blocks.items():
        entry_id, _, version = pin.partition("@")
        pins.append(
            {
                "entry_id": entry_id,
                "version": int(version),
                "fingerprint": block_fingerprint(source.encode()).value,
            }
        )
    return document


def _built(exits: Sequence[Mapping[str, object]], blocks: Mapping[str, str]) -> CompiledUnit:
    compiled = compile_unit(_document_with(exits, blocks), _context_with(blocks))
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _short_document() -> dict[str, object]:
    """The shipped dummy's short side alone, with one entry order and a stop at zero buffer."""
    document = _document()
    document["direction"] = "short"
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    document["logic"] = {
        "short": {
            "slots": {
                "trigger": {
                    "role": "trigger",
                    "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
                    "bindings": [
                        {
                            "name": "next_open",
                            "block": "market-next-open@1",
                            "params": {},
                            "inputs": {},
                        }
                    ],
                }
            }
        }
    }
    document["exit_set"] = [
        {
            "name": "swing_stop",
            "scope": "position",
            "block": "swing-stop-buffer@1",
            "params": {"buffer": {"value": "0"}},
            "inputs": {"series": "m15"},
        }
    ]
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    document["numbers"] = {"risk_fraction": numbers["risk_fraction"]}
    return document


def _short_bars() -> list[QuoteBar]:
    """Eight bars whose bid swing high is 1.0995 and whose ask swing high is 1.1002."""
    highs = ("1.0980", "1.0990", "1.0995", "1.0990", "1.0985", "1.0980", "1.0982", "1.0984")
    base = Decimal("1.0975")
    spread = Decimal("0.0007")
    bars: list[QuoteBar] = []
    for index, high in enumerate(highs):
        bid = OHLC(base, Decimal(high), base - Decimal("0.0005"), base)
        ask = OHLC(bid.open + spread, bid.high + spread, bid.low + spread, bid.close + spread)
        bars.append(QuoteBar(Instant(_START + index * _BAR_NS), bid, ask))
    return bars


def _surfaces(bars: Sequence[QuoteBar], position: OwnPosition | None = None) -> dict[str, Surface]:
    return {
        "account": _Fixed(Account(_EQUITY)),
        "own_journal": _Fixed(()),
        f"bars:m15:{_MARKET}": _Latest(bars),
        f"own_position:{_MARKET}": _Fixed(() if position is None else (position,)),
    }


def _host(
    compiled: CompiledUnit,
    surfaces: Mapping[str, Surface],
    port: HostPort | None = None,
) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-rc-11",
            execution_target=_target(),
            port=port,
        )
    )


def _step(unit: HostedUnit, instant: Instant) -> UnitStep:
    return _ok(unit.on_instant(instant))


def _held(compiled: CompiledUnit, at: Instant) -> OwnPosition:
    return OwnPosition(
        "pos-1", Side.LONG, Decimal("0.10"), Decimal("1.08000"), compiled.logic_fingerprint, at
    )


def _closes(step: UnitStep) -> list[UnitExitIntent]:
    return [intent for intent in step.intents if isinstance(intent, UnitExitIntent)]


def test_a_short_reads_ask_bars() -> None:
    bars = _short_bars()
    compiled = compile_unit(_short_document(), _context())
    assert isinstance(compiled, CompiledUnit), compiled
    unit = _host(compiled, _surfaces(bars))

    stops = [proposal.stop for bar in bars for proposal in _step(unit, bar.knowable_at).proposals]

    assert stops == [Decimal("1.1002")] * 4


def test_full_beats_partial_beats_amend() -> None:
    blocks = {
        "rc11-amend@1": _answering("amend_protection", "rc11-amend"),
        "rc11-partial@1": _answering("close_partial", "rc11-partial"),
        "rc11-full@1": _LATER_FULL,
    }
    exits: list[Mapping[str, object]] = [
        {"name": "amend", "scope": "position", "block": "rc11-amend@1", "params": {}, "inputs": {}},
        {
            "name": "partial",
            "scope": "position",
            "block": "rc11-partial@1",
            "params": {},
            "inputs": {},
        },
        {"name": "full", "scope": "position", "block": "rc11-full@1", "params": {}, "inputs": {}},
    ]
    compiled = _built(exits, blocks)
    bars = _slice()[_MARKET][:3]
    unit = _host(compiled, _surfaces(bars, _held(compiled, bars[0].knowable_at)))

    first = _step(unit, bars[0].knowable_at)
    second = _step(unit, bars[1].knowable_at)

    assert _closes(first) == [], "the amend and the partial answer here and run nothing"
    assert [(one.kind.value, one.reason_code.code) for one in _closes(second)] == [
        ("close_full", "rc11-full")
    ]


def test_a_raising_exit_falls_to_the_next() -> None:
    blocks = {"rc11-raises@1": _RAISES}
    exits: list[Mapping[str, object]] = [
        {
            "name": "boom",
            "scope": "position",
            "block": "rc11-raises@1",
            "params": {},
            "inputs": {},
        },
        {
            "name": "time_out",
            "scope": "position",
            "block": "time-exit-bars@1",
            "params": {"bars": {"value": "1"}},
            "inputs": {},
        },
    ]
    compiled = _built(exits, blocks)
    bars = _slice()[_MARKET][:2]
    port = _Asks()
    unit = _host(compiled, _surfaces(bars, _held(compiled, bars[0].knowable_at)), port)

    step = _step(unit, bars[0].knowable_at)

    assert [(fault.block, fault.phase.value) for fault in step.faults] == [
        ("rc11-raises@1", "exit")
    ]
    assert [(one.kind.value, one.reason_code.code) for one in _closes(step)] == [
        ("close_full", "time-exit")
    ]
    assert port.asked == [], "the time exit ran, so the host's last fall-through is not asked"
