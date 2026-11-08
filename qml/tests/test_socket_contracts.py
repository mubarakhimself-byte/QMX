"""The risk socket's four slot contracts, which every block in a slot must pass (A15, AD-116).

Every shipped block whose entry names a sizer, exit or halt component is enrolled here
automatically, so a risk-session block that lands in the stdlib meets its slot's contract
before anything binds it. The cross-unit hook is the host's, so its stand-in is checked by name.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.core.refusal import is_refusal
from qmf.risk.unit_intent import UnitIntent, parse_unit_intent
from qml.blocks.api import (
    PASS_EVERY_ORDER,
    Block,
    CrossUnitHook,
    EntryFace,
    Halt,
    HaltAction,
    OutputType,
    Refuse,
    Side,
    Signal,
    Size,
    parse_entry,
)
from qml.catalogue import Loaded, LockEntry, load
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.protocol.unit import OwnPosition
from qml.unit.model import Scope

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_RECORDS = _QML / "tests" / "fixtures" / "records"
_SLOTS = ("sizer", "exit", "halt")
_CEILING = Decimal("0.005")
"""His risk_fraction ceiling in these trades; a test bound, equal to the dummy's 0.5%."""


def _record(name: str) -> InstrumentRecord:
    parsed = parse_record(json.loads((_RECORDS / f"{name}.json").read_text("utf-8")))
    assert not is_refusal(parsed), parsed
    return parsed.value


_EURUSD, _XAUUSD = _record("eurusd"), _record("xauusd")


@dataclass(frozen=True)
class _Trade:
    name: str
    record: InstrumentRecord
    equity: Decimal
    entry: Decimal
    stop: Decimal


_TRADES = (
    _Trade("eurusd 20 pips", _EURUSD, Decimal(10000), Decimal("1.08500"), Decimal("1.08300")),
    _Trade("xauusd 14.50", _XAUUSD, Decimal(10000), Decimal("2650.00"), Decimal("2635.50")),
    _Trade(
        "eurusd below the minimum lot", _EURUSD, Decimal(100), Decimal("1.085"), Decimal("1.075")
    ),
    _Trade("stop at the entry", _EURUSD, Decimal(10000), Decimal("1.08500"), Decimal("1.08500")),
)


@dataclass(frozen=True)
class _Shipped:
    face: EntryFace
    block: Block
    params: Mapping[str, Decimal]


def _shipped() -> dict[str, _Shipped]:
    """Every stdlib block in a socket slot, loaded through the one loader."""
    found: dict[str, _Shipped] = {}
    for entry in sorted(_STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        if face.component_type not in _SLOTS:
            continue
        lock = [LockEntry(face.entry_id, face.version, face.fingerprint)]
        loaded = load(lock, {face.pin: (entry.parent / "block.py").read_bytes()})
        assert isinstance(loaded, Loaded), loaded
        raw = cast("dict[str, dict[str, str]]", json.loads(entry.read_text("utf-8"))["parameters"])
        params = {name: Decimal(spec["default"]) for name, spec in raw.items()}
        found[face.pin] = _Shipped(face, loaded.blocks[face.pin], params)
    return found


_SHIPPED = _shipped()


def _sized(answer: object, trade: _Trade) -> list[str]:
    if not isinstance(answer, Size):
        return [f"answered {answer!r}, not a Size"]
    size = cast("object", answer.lots)
    if size is None:
        return [] if answer.skip_reason else ["skipped with no reason"]
    if not isinstance(size, Decimal):
        return [f"the size {size!r} is a {type(size).__name__}, not an exact Decimal"]
    if answer.skip_reason is not None:
        return ["answered both a size and a skip"]
    risk = abs(trade.entry - trade.stop) * trade.record.value_per_point
    if risk == 0:
        return [f"sized {size} lots with the stop at the entry"]
    ceiling = lots(trade.equity * _CEILING / risk, trade.record)
    if is_refusal(ceiling):
        return [f"sized {size} lots where the lot rule skips"]
    most = Decimal(ceiling.value.value).scaleb(-ceiling.value.scale)
    if size > most:
        return [f"{size} lots is above {most}, the lot rule's output at his risk ceiling"]
    own = lots(size, trade.record)
    if is_refusal(own) or Decimal(own.value.value).scaleb(-own.value.scale) != size:
        return [f"{size} lots is off {trade.record.symbol}'s lot rule"]
    return []


def _sizer_breaks(block: Block, params: Mapping[str, Decimal]) -> list[str]:
    breaks: list[str] = []
    for trade in _TRADES:
        evidence = {
            "equity": trade.equity,
            "entry_price": trade.entry,
            "stop_price": trade.stop,
            "record": trade.record,
            **params,
        }
        answer = block.make(params, {}).update(evidence)
        breaks += [f"sizer contract, {trade.name}: {b}" for b in _sized(answer, trade)]
    return breaks


def _bars() -> list[dict[str, Decimal]]:
    """Twelve M15 bars that make a swing low and then a swing high."""
    closes = ("1.0850", "1.0840", "1.0830", "1.0820", "1.0830", "1.0840", "1.0850", "1.0860")
    closes += ("1.0870", "1.0860", "1.0850", "1.0840")
    return [
        {
            "open": Decimal(c),
            "high": Decimal(c) + Decimal("0.0005"),
            "low": Decimal(c) - Decimal("0.0005"),
            "close": Decimal(c),
        }
        for c in closes
    ]


_ANSWERS = {OutputType.LEVEL: "a price level", OutputType.EXIT_ACTION: "a Signal"}


def _exit_breaks(output: OutputType, block: Block, params: Mapping[str, Decimal]) -> list[str]:
    wanted = _ANSWERS.get(output)
    if wanted is None:
        return [f"exit contract: its entry declares {output.value}, not level or exit_action"]
    breaks: list[str] = []
    for side in (Side.LONG, Side.SHORT):
        instance = block.make(params, {"series": "m15"}, side)
        for i, bar in enumerate(_bars()):
            answer = instance.update(
                {"series": bar, "entry_price": Decimal("1.0850"), "stop_price": Decimal("1.0820")}
                | dict(params)
            )
            level = isinstance(answer, Decimal) and answer.is_finite()
            signal = isinstance(answer, Signal) and isinstance(cast("object", answer.state), bool)
            if answer is None or (level and output is OutputType.LEVEL):
                continue
            if signal and output is OutputType.EXIT_ACTION:
                continue
            breaks.append(f"exit contract, {side.value} bar {i}: {answer!r} is not {wanted}")
    return breaks


def _run(side: Side) -> list[dict[str, Decimal]]:
    """A position that runs its way from 1.0000 for 30 bars, 3% a bar with a 7% pullback every
    fifth bar, then comes back 2% a bar for 30: any exit should close it or set a level on it."""
    sign = 1 if side is Side.LONG else -1
    closes = [Decimal("1.0000")]
    for i in range(60):
        step = Decimal("-0.02") if i >= 30 else Decimal("-0.07" if i % 5 == 4 else "0.03")
        closes.append(closes[-1] * (1 + sign * step))
    return [
        {
            "open": a,
            "high": max(a, b) + Decimal("0.0005"),
            "low": min(a, b) - Decimal("0.0005"),
            "close": b,
        }
        for a, b in zip(closes, closes[1:], strict=False)
    ]


def _never_acts(output: OutputType, block: Block, params: Mapping[str, Decimal]) -> list[str]:
    """An exit that never closes, or never answers a level, on a position it should close."""
    breaks: list[str] = []
    for side in (Side.LONG, Side.SHORT):
        instance = block.make(params, {"series": "m15"}, side)
        stop = Decimal("0.95") if side is Side.LONG else Decimal("1.05")
        answers = [
            instance.update(
                {"series": bar, "entry_price": Decimal("1.0000"), "stop_price": stop} | dict(params)
            )
            for bar in _run(side)
        ]
        acted = (
            any(isinstance(a, Signal) and a.state for a in answers)
            if output is OutputType.EXIT_ACTION
            else any(isinstance(a, Decimal) for a in answers)
        )
        if not acted:
            breaks.append(
                f"exit contract, {side.value}: never acted on a position that ran its way and "
                "came back"
            )
    return breaks


def _halt_breaks(
    block: Block, params: Mapping[str, Decimal], statistics: Sequence[Mapping[str, object]]
) -> list[str]:
    instance = block.make(params, {})
    breaks: list[str] = []
    acted = False
    for i, evidence in enumerate(statistics):
        answer = instance.update(evidence)
        if answer is None:
            continue
        acted = True
        if not isinstance(answer, Halt):
            breaks.append(f"halt contract, update {i}: {answer!r} is not None or a Halt")
        elif not answer.reason:
            breaks.append(f"halt contract, update {i}: {answer.action.value} with no reason")
    if not acted:
        breaks.append("halt contract: never acted on a session that broke every limit")
    return breaks


_SESSION = (
    {
        "session_loss_r": Decimal(0),
        "loss_streak": 0,
        "losing_day_streak": 0,
        "session_fills": 0,
        "equity": Decimal(10000),
        "day_start_equity": Decimal(10000),
    },
    {
        "session_loss_r": Decimal(-1),
        "loss_streak": 1,
        "losing_day_streak": 1,
        "session_fills": 5,
        "equity": Decimal(9800),
        "day_start_equity": Decimal(10000),
    },
    {
        "session_loss_r": Decimal(-3),
        "loss_streak": 3,
        "losing_day_streak": 3,
        "session_fills": 21,
        "equity": Decimal(9000),
        "day_start_equity": Decimal(10000),
    },
)
"""A session that ends past every shipped halt's default limit; the values are test bounds."""


def _breaks(shipped: _Shipped) -> list[str]:
    match shipped.face.component_type:
        case "sizer":
            return _sizer_breaks(shipped.block, shipped.params)
        case "exit":
            output = shipped.face.output.type
            return _exit_breaks(output, shipped.block, shipped.params) + _never_acts(
                output, shipped.block, shipped.params
            )
        case _:
            return _halt_breaks(shipped.block, shipped.params, _SESSION)


def _intent() -> UnitIntent:
    parsed = parse_unit_intent(
        {
            "contract_format_version": 3,
            "intent_family": "entry",
            "unit": {
                "unit_id": "dummy-trend-pullback",
                "version_ref": "fp1:sha256:" + "a" * 64,
                "compiled_fingerprint": "fp1:sha256:" + "b" * 64,
            },
            "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            "market_id": "fx.eurusd",
            "direction": "long",
            "reason_code": {"code": "trend-pullback", "book_family": "unit"},
            "execution_target": {"role": "demo", "venue_id": "ctrader", "account_id": "acct-1"},
            "order": {"type": "market"},
            "quantity": "0.25",
            "sizer_receipt": {"inputs_used": ["equity"], "rounding_residue_r": "0/1"},
            "protection": {"stop": "1.08300", "targets": []},
            "not_before": 1_740_952_800_000_000_000,
            "placeholder_labels": ["fixed_fraction"],
            "decision_row_id": "row-1",
        }
    )
    assert not is_refusal(parsed), parsed
    return parsed.value


def _hook_breaks(hook: CrossUnitHook) -> list[str]:
    answer = cast("object", hook.before_order(_intent(), (), None))
    if answer is None:
        return []
    if not isinstance(answer, Refuse):
        return [f"cross-unit hook contract: {answer!r} is not None or a Refuse"]
    return [] if answer.reason else ["cross-unit hook contract: refused with no reason"]


class _Instance:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    warm_up_bars = 0
    state_bound = 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        return self._answer(evidence) if callable(self._answer) else self._answer

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Fake:
    """A block whose instance answers ``answer``, or ``answer(evidence)`` when it is callable."""

    def __init__(self, answer: object) -> None:
        self._answer = answer

    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _Instance:
        return _Instance(self._answer)


def _half_risk(evidence: Mapping[str, object]) -> Size:
    """A risk-session sizer that is not a placeholder: half the dummy's risk, 0.25% at the stop."""
    record = cast("InstrumentRecord", evidence["record"])
    entry, stop = cast("Decimal", evidence["entry_price"]), cast("Decimal", evidence["stop_price"])
    if entry == stop:
        return Size(lots=None, skip_reason="no distance to the stop")
    wanted = cast("Decimal", evidence["equity"]) * Decimal("0.0025")
    sized = lots(wanted / (abs(entry - stop) * record.value_per_point), record)
    if is_refusal(sized):
        return Size(lots=None, skip_reason="below the minimum lot")
    return Size(lots=Decimal(sized.value.value).scaleb(-sized.value.scale))


def _rounds_up(evidence: Mapping[str, object]) -> Size:
    record = cast("InstrumentRecord", evidence["record"])
    entry, stop = cast("Decimal", evidence["entry_price"]), cast("Decimal", evidence["stop_price"])
    if entry == stop:
        return Size(lots=None, skip_reason="no distance to the stop")
    wanted = cast("Decimal", evidence["equity"]) * _CEILING
    steps = math.ceil(wanted / (abs(entry - stop) * record.value_per_point) / record.lot_step)
    return Size(lots=steps * record.lot_step)


def test_the_socket_enrols_every_shipped_sizer_exit_and_halt() -> None:
    slots = {
        slot: sorted(pin for pin, s in _SHIPPED.items() if s.face.component_type == slot)
        for slot in _SLOTS
    }
    origins = {pin: (s.face.origin, s.face.owner) for pin, s in _SHIPPED.items()}

    assert slots == {
        "sizer": ["fixed-fraction-at-stop@1"],
        "exit": [
            "offset-gated-trailing-stop@1",
            "peak-holdings-giveback-exit@1",
            "profit-fraction-trailing-stop@1",
            "roi-table-exit@1",
            "stepped-profit-stop@1",
            "swing-stop-buffer@1",
            "target-r-multiple@1",
            "time-exit-bars@1",
            "unrealised-profit-cap@1",
        ],
        "halt": [
            "account-daily-loss-halt@1",
            "equity-drawdown-halt@1",
            "losing-days-halt@1",
            "session-fill-limit-halt@1",
            "session-loss-limit-halt@1",
        ],
    }
    assert {pin for pin, o in origins.items() if o == ("placeholder", "risk-session")} == {
        "fixed-fraction-at-stop@1",
        "swing-stop-buffer@1",
        "target-r-multiple@1",
        "time-exit-bars@1",
    }
    assert {o for o in origins.values() if o[0] != "placeholder"} == {("qml", None)}


@pytest.mark.parametrize("pin", sorted(_SHIPPED))
def test_every_shipped_socket_block_meets_its_slot_contract(pin: str) -> None:
    assert _breaks(_SHIPPED[pin]) == []


def test_the_dummys_sizer_answers_the_lot_rule_at_half_a_percent() -> None:
    shipped = _SHIPPED["fixed-fraction-at-stop@1"]
    answers = [
        shipped.block.make(shipped.params, {}).update(
            {"equity": t.equity, "entry_price": t.entry, "stop_price": t.stop, "record": t.record}
        )
        for t in _TRADES
    ]

    assert [a.lots if isinstance(a, Size) else a for a in answers] == [
        Decimal("0.25"),
        Decimal("0.03"),
        None,
        None,
    ]


def test_a_sizer_answering_a_float_breaks_the_sizer_contract() -> None:
    assert _sizer_breaks(_Fake(0.25), {}) == [
        f"sizer contract, {t.name}: answered 0.25, not a Size" for t in _TRADES
    ]
    assert _sizer_breaks(_Fake(Size(lots=0.25)), {})[:2] == [  # pyright: ignore[reportArgumentType]
        "sizer contract, eurusd 20 pips: the size 0.25 is a float, not an exact Decimal",
        "sizer contract, xauusd 14.50: the size 0.25 is a float, not an exact Decimal",
    ]


def test_a_sizer_above_the_lot_rules_output_breaks_the_sizer_contract() -> None:
    assert _sizer_breaks(_Fake(_rounds_up), {}) == [
        "sizer contract, xauusd 14.50: 0.04 lots is above 0.03, the lot rule's output at his "
        "risk ceiling",
        "sizer contract, eurusd below the minimum lot: sized 0.01 lots where the lot rule skips",
    ]


def test_a_risk_session_sizer_that_is_not_a_placeholder_meets_the_sizer_contract() -> None:
    assert _sizer_breaks(_Fake(_half_risk), {}) == []


def test_an_exit_must_answer_what_its_entry_declares() -> None:
    assert _exit_breaks(OutputType.LEVEL, _Fake(1.082), {})[:1] == [
        "exit contract, long bar 0: 1.082 is not a price level"
    ]
    assert _exit_breaks(OutputType.LEVEL, _Fake(Signal(state=True)), {})[:1] == [
        "exit contract, long bar 0: Signal(state=True, value=None) is not a price level"
    ]
    assert _exit_breaks(OutputType.EXIT_ACTION, _Fake(Signal(state=1)), {})[:1] == [  # pyright: ignore[reportArgumentType]
        "exit contract, long bar 0: Signal(state=1, value=None) is not a Signal"
    ]
    assert _exit_breaks(OutputType.QUANTITY, _Fake(None), {}) == [
        "exit contract: its entry declares quantity, not level or exit_action"
    ]


def test_an_exit_that_never_acts_on_a_position_it_should_close_breaks_the_exit_contract() -> None:
    never = [
        "exit contract, long: never acted on a position that ran its way and came back",
        "exit contract, short: never acted on a position that ran its way and came back",
    ]

    assert _never_acts(OutputType.LEVEL, _Fake(None), {}) == never
    assert _never_acts(OutputType.EXIT_ACTION, _Fake(Signal(state=False)), {}) == never
    assert _never_acts(OutputType.LEVEL, _Fake(Decimal("0.95")), {}) == []
    assert _never_acts(OutputType.EXIT_ACTION, _Fake(Signal(state=True)), {}) == []


def test_a_halt_answers_none_or_a_halt_with_its_reason() -> None:
    def three_r(evidence: Mapping[str, object]) -> Halt | None:
        if cast("Decimal", evidence["session_loss_r"]) <= -3:
            return Halt(HaltAction.NO_NEW_ENTRIES, Scope.UNIT, "lost 3R this session")
        return None

    assert _halt_breaks(_Fake(three_r), {}, _SESSION) == []
    assert _halt_breaks(_Fake("flatten"), {}, _SESSION[:1]) == [
        "halt contract, update 0: 'flatten' is not None or a Halt"
    ]
    assert _halt_breaks(_Fake(Halt(HaltAction.FLATTEN, Scope.ACCOUNT, "")), {}, _SESSION[:1]) == [
        "halt contract, update 0: flatten with no reason"
    ]
    assert _halt_breaks(_Fake(None), {}, _SESSION) == [
        "halt contract: never acted on a session that broke every limit"
    ]


class _Answers:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    def before_order(
        self, intent: UnitIntent, open_positions: Sequence[OwnPosition], dispersion: Decimal | None
    ) -> Refuse | None:
        return cast("Refuse | None", self._answer)


def test_the_cross_unit_hook_placeholder_passes_and_a_bad_hook_breaks_the_contract() -> None:
    assert PASS_EVERY_ORDER.before_order(_intent(), (), None) is None
    assert _hook_breaks(PASS_EVERY_ORDER) == []
    assert _hook_breaks(_Answers(Refuse("same bet as an open unit"))) == []
    assert _hook_breaks(_Answers(False)) == [
        "cross-unit hook contract: False is not None or a Refuse"
    ]
    assert _hook_breaks(_Answers(Refuse(""))) == [
        "cross-unit hook contract: refused with no reason"
    ]
