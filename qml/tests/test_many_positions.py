"""A unit holds more than one position on one market, and each keeps its own exits and its bet.

The section's Verify, unit block, at the unit door. Every test compiles a document that asks for
two positions per market, with the per-bar exit it measures pinned in the test's own bytes, the
way a Library block is pinned, and drives the unit through ``construct_unit`` and ``on_instant``.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast

from qmf.core.chrono import Instant
from qmf.risk.unit_intent import UnitEntryIntent, UnitExitIntent
from qml.catalogue import block_fingerprint
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.protocol.exits import PositionFacts
from qml.protocol.unit import (
    OHLC,
    Account,
    HostedUnit,
    QuoteBar,
    Surface,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side

from test_compile_dummy import _context, _document, _drive, _ok, _target

_MARKET = "fx.eurusd"

_EQUITY = Decimal("100000")
_START = 1_740_952_800_000_000_000  # 2025-03-02 22:00 UTC, the shipped slice's first bar
_BAR_NS = 900_000_000_000

_STOP_HIT = '''"""One per-bar exit that closes when the bar reaches the position's own stop."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import ExitAction, Side


class _StopHit:
    def __init__(self, side: Side) -> None:
        self._side = side

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> ExitAction | None:
        stop = evidence.get("stop")
        series = evidence.get("series")
        if not isinstance(stop, Decimal) or not isinstance(series, Mapping):
            return None
        low = series.get("low")
        high = series.get("high")
        if not isinstance(low, Decimal) or not isinstance(high, Decimal):
            return None
        reached = low <= stop if self._side is Side.LONG else high >= stop
        return ExitAction(kind="close_full", reason_code="stop-hit") if reached else None

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _StopHit:
        del params, inputs
        return _StopHit(side)


BLOCK = _Block()
'''

_FIXED_STOP = '''"""One stop exit that answers two ticks under the bar for a long and over it for a short."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side

_TICKS = Decimal("0.0020")


class _FixedStop:
    """The stop level: two ticks under the last bar a long read, and over it for a short.

    The unit reads a stop twice, once each bar with the bar and once at the entry with nothing,
    so the block keeps the close it last read.
    """

    def __init__(self, side: Side) -> None:
        self._side = side
        self._close: Decimal | None = None

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 1

    def update(self, evidence: Mapping[str, object]) -> Decimal:
        series = evidence.get("series")
        close = series.get("close") if isinstance(series, Mapping) else None
        if isinstance(close, Decimal):
            self._close = close
        level = self._close if self._close is not None else Decimal("1")
        return level - _TICKS if self._side is Side.LONG else level + _TICKS

    def export_state(self) -> Mapping[str, object]:
        return {} if self._close is None else {"close": str(self._close)}

    def import_state(self, state: Mapping[str, object]) -> None:
        kept = state.get("close")
        self._close = Decimal(kept) if isinstance(kept, str) else None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _FixedStop:
        del params, inputs
        return _FixedStop(side)


BLOCK = _Block()
'''

_BETS = '''"""One brake that names the bets this unit holds open, so a test can read the fact."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Halt, HaltAction, Scope, Side


class _Bets:
    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> Halt:
        held = evidence.get("open_risk_by_bet_key")
        bets = held if isinstance(held, Mapping) else {}
        total = sum((money for money in bets.values() if isinstance(money, Decimal)), Decimal(0))
        keys = ",".join(sorted(str(key) for key in bets))
        return Halt(
            HaltAction.NO_NEW_ENTRIES, Scope.UNIT, f"{len(bets)} bets at {total} {keys}"
        )

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Bets:
        del params, inputs, side
        return _Bets()


BLOCK = _Block()
'''

_BLOCKS = {"stop-hit@1": _STOP_HIT, "fixed-stop@1": _FIXED_STOP, "bet-report@1": _BETS}


def _face(
    pin: str, source: str, *, component_type: str, output: str, measure: str | None = None
) -> bytes:
    entry_id, _, version = pin.partition("@")
    inputs: list[dict[str, object]] = []
    if component_type == "halt":
        inputs = [{"port": "open_risk_by_bet_key", "stream_kind": "trades", "data_level": None}]
    elif output == "level":
        inputs = [{"port": "series", "stream_kind": "bars", "measure": "price", "data_level": 1}]
    face: dict[str, object] = {
        "schema": "qmx.entry/1",
        "entry_id": entry_id,
        "version": int(version),
        "component_type": component_type,
        "origin": "library",
        "inputs": inputs,
        "output": {"type": output, "measure": measure},
        "parameters": {},
        "mirroring": "not_applicable",
        "fingerprint": block_fingerprint(source.encode()).value,
    }
    return json.dumps(face, indent=1).encode()


_FACES = {
    "stop-hit@1": _face("stop-hit@1", _STOP_HIT, component_type="exit", output="exit_action"),
    "fixed-stop@1": _face(
        "fixed-stop@1", _FIXED_STOP, component_type="exit", output="level", measure="price"
    ),
    "bet-report@1": _face("bet-report@1", _BETS, component_type="halt", output="state"),
}


def _context_holding() -> CompileContext:
    """The shipped blocks, this test's three, and a venue that keeps positions apart."""
    base = _context()
    sources = dict(base.sources)
    entries = dict(base.entries)
    for pin, source in _BLOCKS.items():
        sources[pin] = source.encode()
        entries[pin] = _FACES[pin]
    return CompileContext(
        sources=sources, entries=entries, records=base.records, nets_positions=False
    )


def _holding_document(*, limit: int = 2, bets: bool = False) -> dict[str, object]:
    """One market, an entry order every bar, this test's exits, and a limit of ``limit``."""
    document = _document()
    document["markets"] = [
        market
        for market in cast("list[dict[str, object]]", document["markets"])
        if market["market_id"] == _MARKET
    ]
    document["direction"] = "long"
    document["position_limit"] = {"per_instrument": limit}
    document["logic"] = {
        "long": {
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
                },
                "entry_order": {
                    "role": "entry_order",
                    "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
                    "bindings": [
                        {
                            "name": "at_open",
                            "block": "market-next-open@1",
                            "params": {},
                            "inputs": {},
                        }
                    ],
                },
            }
        }
    }
    document["exit_set"] = [
        {
            "name": "fixed_stop",
            "scope": "position",
            "block": "fixed-stop@1",
            "params": {},
            "inputs": {"series": "m15"},
        },
        {"name": "stop_hit", "scope": "position", "block": "stop-hit@1", "params": {}, "inputs": {}},
    ]
    numbers = cast("dict[str, object]", document["numbers"])
    document["numbers"] = {
        name: numbers[name]
        for name in ("risk_fraction",)
        if name in numbers
    }
    if bets:
        document["halts"] = {
            "position": [],
            "unit": [
                {
                    "name": "bets",
                    "block": "bet-report@1",
                    "params": {},
                    "inputs": {},
                    "scope": "unit",
                }
            ],
            "account": [],
        }
    pins = cast("list[dict[str, object]]", document["pins"])
    for pin, source in _BLOCKS.items():
        entry_id, _, version = pin.partition("@")
        pins.append(
            {
                "entry_id": entry_id,
                "version": int(version),
                "fingerprint": block_fingerprint(source.encode()).value,
            }
        )
    return document


def _compiled(**kwargs: object) -> CompiledUnit:
    compiled = compile_unit(_holding_document(**kwargs), _context_holding())  # type: ignore[arg-type]
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _position(position_id: str, stop: str, entry: str, compiled: CompiledUnit) -> PositionFacts:
    return PositionFacts(
        position_id=position_id,
        side=Side.LONG,
        quantity=Decimal("0.10"),
        entry_price=Decimal(entry),
        opened_by=compiled.logic_fingerprint,
        stop=Decimal(stop),
    )


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


def _one_bar(low: str, *, at: int = _START) -> QuoteBar:
    bid = OHLC(Decimal("1.09700"), Decimal("1.09720"), Decimal(low), Decimal("1.09690"))
    ask = OHLC(
        bid.open + Decimal("0.00010"),
        bid.high + Decimal("0.00010"),
        bid.low + Decimal("0.00010"),
        bid.close + Decimal("0.00010"),
    )
    return QuoteBar(Instant(at), bid, ask)


def _surfaces(bars: Sequence[QuoteBar], positions: Sequence[PositionFacts]) -> dict[str, Surface]:
    """The one market's surface, its position tuple, as a host answers them."""
    return {
        "account": _Fixed(Account(_EQUITY)),
        "own_journal": _Fixed(()),
        f"bars:m15:{_MARKET}": _Latest(bars),
        f"own_position:{_MARKET}": _Fixed(tuple(positions)),
    }


def _host(compiled: CompiledUnit, surfaces: Mapping[str, Surface]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id="run-many",
            execution_target=_target(),
        )
    )


def _step(unit: HostedUnit, instant: Instant) -> UnitStep:
    return _ok(unit.on_instant(instant))


def _closes(step: UnitStep) -> list[UnitExitIntent]:
    return [intent for intent in step.intents if isinstance(intent, UnitExitIntent)]


def _entries(step: UnitStep) -> list[UnitEntryIntent]:
    return [intent for intent in step.intents if isinstance(intent, UnitEntryIntent)]


def test_two_positions_get_their_own_exits() -> None:
    """Two longs on one market, stops 1.0950 and 1.0960, on a bar that reaches 1.0955: the
    second closes, by its own ``position_ref``, and the first stays open."""
    compiled = _compiled()
    first = _position("own-1", "1.09500", "1.09700", compiled)
    second = _position("own-2", "1.09600", "1.09750", compiled)
    unit = _host(compiled, _surfaces([_one_bar("1.09550")], [first, second]))

    step = _step(unit, Instant(_START))

    assert [(one.position_ref.position_id, one.kind.value) for one in _closes(step)] == [
        ("own-2", "close_full")
    ]


def test_position_limit_counts_every_open() -> None:
    """A limit of two refuses a third entry with ``suppressed_limit``, and takes the second."""
    compiled = _compiled(limit=2)
    first = _position("own-1", "1.09500", "1.09700", compiled)
    second = _position("own-2", "1.09600", "1.09750", compiled)
    bars = [_one_bar("1.09700")]

    at_limit = _drive(_host(compiled, _surfaces(bars, [first, second])), [Instant(_START)])[0]
    one_open = _drive(_host(compiled, _surfaces(bars, [first])), [Instant(_START)])[0]

    assert [(row.outcome, row.reason) for row in at_limit.decisions] == [
        ("suppressed_limit", "2 of 2 positions are open")
    ]
    assert _entries(at_limit) == []
    assert [(row.outcome, row.reason) for row in one_open.decisions] == [
        ("taken", "all slots hold")
    ]
    assert [one.market_id for one in _entries(one_open)] == [_MARKET]


def test_same_bet_counts_once() -> None:
    """Two units on one family and one market share a bet key, and a unit holding two positions
    there reads one bet whose money is both positions' risk at their stops."""
    compiled = _compiled(bets=True)
    first = _position("own-1", "1.09500", "1.09700", compiled)
    second = _position("own-2", "1.09600", "1.09750", compiled)
    unit = _host(compiled, _surfaces([_one_bar("1.09700")], [first, second]))

    step = _step(unit, Instant(_START))

    assert [(event.code, event.reason) for event in step.controls] == [
        ("bet-report", "1 bets at 35 trend-pullback:fx.eurusd")
    ]

    entering = _compiled()
    entry = _drive(_host(entering, _surfaces([_one_bar("1.09700")], [])), [Instant(_START)])[0]
    assert [(one.bet_key, one.driver_tags) for one in _entries(entry)] == [
        ("trend-pullback:fx.eurusd", ("trigger",))
    ]
