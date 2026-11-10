"""Generate ``qml/EXTENDING.md``, the developer guide's generated pages.

The socket list, every field of ``qmx.unit/1`` with the refusal the compiler gives it, the
block answer shapes and the journal kinds are read from ``qml`` and written into the guide.
The written pages stay as headings for the slices that fill them. ``--check`` compares the
guide with what the generator would write, so a schema field or a compiler message that
moves fails CI until the guide is regenerated.

    uv run python tools/qml/extending.py
    uv run python tools/qml/extending.py --check

The script imports only ``qml``, so qml's declared package dependencies do not move.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, fields
from importlib.resources import files
from pathlib import Path
from typing import Any, Final, cast, get_args, get_type_hints

from qml.blocks.api import (
    CrossUnitHook,
    EntryOrder,
    ExitInstance,
    Factor,
    Halt,
    HaltInstance,
    ModifierInstance,
    OutputType,
    Refuse,
    Signal,
    Size,
    SizerInstance,
)
from qml.compile import COMPILER_FORMAT_VERSION, CompileContext, CompileProblem, compile_unit
from qml.lifecycle import Event
from qml.protocol.unit import CalibrationRow, DecisionRow, StateEvent
from qml.unit.schema import Array, Map, OneOf, Record, Shape, shape_of

ROOT: Final = Path(__file__).resolve().parents[2]
"""The repository root, two folders above ``tools/qml``."""

GUIDE: Final = ROOT / "qml" / "EXTENDING.md"
"""The guide this script writes and checks."""

_FORMAT: Final = f"compiler format {COMPILER_FORMAT_VERSION}"
"""Every ``_shape_problems`` message starts with this, and no other message does."""

_EMPTY: Final = CompileContext(sources={}, entries={}, records={})
"""The probes need the document's shape, not the host's bytes."""

_Edit = Callable[[dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class _Probe:
    """One document edit that makes the compiler refuse one field."""

    field: str
    where: str
    edit: _Edit


@dataclass(frozen=True, slots=True)
class _Refusal:
    """The compiler's answer for one field."""

    where: str
    code: str
    reason: str


def _document() -> dict[str, Any]:
    """A fresh copy of the shipped dummy, which compiles clean with no probe applied."""
    template = files("qml.unit") / "templates" / "dummy-trend-pullback.json"
    return cast("dict[str, Any]", json.loads(template.read_text("utf-8")))


def _put(path: str, value: object) -> _Edit:
    def edit(document: dict[str, Any]) -> None:
        node: Any = document
        steps = path.split("/")
        for step in steps[:-1]:
            node = node[int(step)] if step.isdigit() else node[step]
        node[steps[-1]] = copy.deepcopy(value)

    return edit


def _two_streams(document: dict[str, Any]) -> None:
    stream = document["streams"][0]
    document["streams"] = [stream, copy.deepcopy(stream)]


def _motion(**motion: object) -> _Edit:
    return _put("numbers/ema_period/motion", {"mode": "fixed", **motion})


_MISFILED_HALT: Final = {
    "name": "probe",
    "scope": "position",
    "block": "equity-drawdown-halt@1",
    "params": {"max_drawdown": {"value": "0.05"}, "trailing": {"value": "0"}},
    "inputs": {},
}
"""One halt row in the unit list whose own scope says position, so the two disagree."""


_SESSION: Final = [
    {
        "name": "london",
        "calendar_ref": "fx-24x5@1",
        "zone": "Europe/London",
        "windows": [{"from": "08:00", "to": "16:00"}],
    }
]
_READ: Final = [
    {
        "reading": "news@1",
        "market": "fx.eurusd",
        "fallback": "treat_as_absent",
        "stale_after_s": 60,
    }
]
_MODIFIER: Final = [
    {
        "name": "probe",
        "block": "ema@1",
        "params": {"period": {"number": "ema_period"}},
        "inputs": {},
    }
]
_STAGES: Final = {
    "selector": "risk_fraction",
    "anchor": "market_day_close",
    "hysteresis": "0.05",
    "move_up": "card",
    "move_down": "rule",
    "rows": {"stage_2": {"numbers": {"risk_fraction": "0.01"}}},
}
_RECIPE: Final = {"pod_id": "trend-pullback", "version": 1, "hash": "fp1:sha256:probe"}

_PROBES: Final[tuple[_Probe, ...]] = (
    _Probe("Unit.streams", "/streams", _two_streams),
    _Probe("Unit.reads", "/reads", _put("reads", _READ)),
    _Probe(
        "ControlBinding.scope",
        "/halts/unit/0/scope",
        _put("halts", {"position": [], "unit": [_MISFILED_HALT], "account": []}),
    ),
    _Probe("Unit.sessions", "/sessions", _put("sessions", _SESSION)),
    _Probe(
        "Unit.context_needs", "/context_needs", _put("context_needs", {"block": [{"word": "fomc"}]})
    ),
    _Probe("Unit.routes", "/routes", _put("routes", {"execution": "paper"})),
    _Probe("Unit.plain_python", "/plain_python", _put("plain_python", {"block": "ema@1"})),
    _Probe("Binding.inputs", "/sizer/inputs/equity", _put("sizer/inputs", {"equity": "m15.close"})),
    _Probe("Market.roll", "/markets/0/roll", _put("markets/0/roll", {"rule": "calendar"})),
    _Probe(
        "Market.settings", "/markets/0/settings", _put("markets/0/settings", {"ema_period": "20"})
    ),
    _Probe(
        "Market.settings_record",
        "/markets/0/settings_record",
        _put("markets/0/settings_record", "eurusd-settings@1"),
    ),
    _Probe(
        "PositionLimit.per_instrument",
        "/position_limit",
        _put("position_limit", {"per_instrument": 2}),
    ),
    _Probe("Stream.market", "/streams/0/market", _put("streams/0/market", "fx.eurusd")),
    _Probe("Stream.price", "/streams/0/price", _put("streams/0/price", "mid")),
    _Probe("Stream.input", "/streams/0/input", _put("streams/0/input", "quotes")),
    _Probe("Bar.kind", "/streams/0/bar", _put("streams/0/bar", {"kind": "tick", "size": "100"})),
    _Probe("Bar.size", "/streams/0/bar", _put("streams/0/bar/size", "3600")),
    _Probe(
        "NumberSpec.applies_to_open_positions",
        "/numbers/stop_buffer/applies_to_open_positions",
        _put("numbers/stop_buffer/applies_to_open_positions", True),
    ),
    _Probe("Motion.source", "/numbers/ema_period/motion/source", _motion(source="trend")),
    _Probe(
        "Motion.rule_params",
        "/numbers/ema_period/motion/rule_params",
        _motion(rule_params={"step": "1"}),
    ),
    _Probe(
        "Motion.cadence",
        "/numbers/ema_period/motion/cadence",
        _motion(cadence={"every_closed_trades": 5}),
    ),
    _Probe("Motion.min_count", "/numbers/ema_period/motion/min_count", _motion(min_count=5)),
    _Probe("Motion.shrink_k", "/numbers/ema_period/motion/shrink_k", _motion(shrink_k=5)),
    _Probe("Motion.step_limit", "/numbers/ema_period/motion/step_limit", _motion(step_limit=5)),
    _Probe(
        "Motion.rule",
        "/numbers/ema_period/motion/rule",
        _motion(rule="trend-floor-from-record@1"),
    ),
    _Probe(
        "Cadence.every_closed_trades",
        "/numbers/rsi_low/motion/cadence",
        _put("numbers/rsi_low/motion/cadence", {"every_closed_trades": 5}),
    ),
    _Probe(
        "Cadence.at",
        "/numbers/min_trend_strength/motion/cadence",
        _put("numbers/min_trend_strength/motion/cadence", {"at": "market_day_close"}),
    ),
    _Probe("Unit.gates", "/gates", _put("gates", _MODIFIER)),
    _Probe("Unit.tolerations", "/tolerations", _put("tolerations", ["news"])),
    _Probe("Unit.stages", "/stages", _put("stages", _STAGES)),
    _Probe("Unit.risk_locks", "/risk_locks", _put("risk_locks", ["sizer"])),
    _Probe("Unit.recipe", "/recipe", _put("recipe", _RECIPE)),
    _Probe("Unit.home_markets", "/home_markets", _put("home_markets", ["fx.eurusd"])),
    _Probe("Unit.tags", "/tags", _put("tags", ["trend"])),
)
"""One probe per refusal the guide lists, labelled with the field it proves."""

_SLOTS: Final = (
    ("sizer", SizerInstance),
    ("sizing modifier", ModifierInstance),
    ("exit", ExitInstance),
    ("halt", HaltInstance),
    ("cross-unit hook", CrossUnitHook),
)

_ANSWERS: Final = (
    (Signal, "a context, trigger, confirmation, filter, veto or per-bar exit slot"),
    (Size, "a sizer slot"),
    (Factor, "a sizing-modifier slot"),
    (Halt, "a halt slot"),
    (Refuse, "the cross-unit hook"),
    (EntryOrder, "an entry-order slot"),
)

_JOURNAL: Final = (
    (DecisionRow, "signal", "the host, when a decision lands"),
    (CalibrationRow, "calibration", "the host, when a number moves"),
    (StateEvent, "state", "the host, when a unit warms, is ready or restarts cold"),
    (Event, "lifecycle", "the host, when the lifecycle machine moves or refuses"),
)


def unit_fields() -> tuple[str, ...]:
    """Every ``Model.field`` of ``qmx.unit/1``, first seen first, without repeats."""
    found: dict[str, None] = {}
    for name in _walk(shape_of()):
        found.setdefault(name, None)
    return tuple(found)


def _walk(shape: Shape) -> Iterator[str]:
    match shape:
        case Array(item=inner) | Map(value=inner):
            yield from _walk(inner)
        case OneOf(choices=choices):
            for choice in choices:
                yield from _walk(choice)
        case Record(model=model, fields=record_fields):
            for item in record_fields:
                yield f"{model.__name__}.{item.key}"
            for item in record_fields:
                yield from _walk(item.shape)
        case _:
            return


def _probe_problems(probe: _Probe) -> tuple[CompileProblem, ...]:
    document = _document()
    probe.edit(document)
    compiled = compile_unit(document, _EMPTY)
    if not isinstance(compiled, tuple):
        raise RuntimeError(f"{probe.field}: the probe compiled, the refusal is gone")
    return tuple(
        problem
        for problem in compiled
        if problem.layer == "compile" and problem.where == probe.where
    )


def _refusals() -> dict[str, _Refusal]:
    found: dict[str, _Refusal] = {}
    for probe in _PROBES:
        problems = _probe_problems(probe)
        if len(problems) != 1:
            raise RuntimeError(f"{probe.field}: {len(problems)} problems at {probe.where}")
        problem = problems[0]
        found[probe.field] = _Refusal(problem.where, problem.kind, problem.message)
    return found


def _type_name(value: object) -> str:
    if value is type(None):
        return "None"
    return value.__name__ if isinstance(value, type) else str(value)


def _type_text(hint: object) -> str:
    members = get_args(hint)
    if not members:
        return _type_name(hint)
    return " or ".join(_type_name(member) for member in members)


def _summary(protocol: object) -> str:
    text = inspect.getdoc(protocol) or ""
    first = text.split("\n\n")[0].split(". ")[0].rstrip(".")
    return f"{first}." if first else ""


def _answer(protocol: object) -> str:
    method = "before_order" if protocol is CrossUnitHook else "update"
    annotation = getattr(protocol, method).__annotations__["return"]
    if isinstance(annotation, str):
        names = [f"`{name.strip()}`" for name in annotation.split("|")]
    else:
        names = [f"`{_type_name(member)}`" for member in get_args(annotation)]
    if not names:
        return f"`{_type_name(annotation)}`"
    return ", ".join(names[:-1]) + f" or {names[-1]}"


def _answer_fields(model: type) -> str:
    hints = get_type_hints(model)
    return "; ".join(
        f"`{item.name}: {_type_text(hints[item.name])}`" for item in fields(cast("Any", model))
    )


def render(field_names: Sequence[str] | None = None) -> str:
    """The guide's text. ``field_names`` adds fields, which is how a test plants a new one."""
    names = tuple(field_names) if field_names is not None else unit_fields()
    refused = _refusals()
    lines = [
        "# Extending QML",
        "",
        "Generated by `tools/qml/extending.py`. Do not edit the generated pages; run",
        "`uv run python tools/qml/extending.py` to write them, and",
        "`uv run python tools/qml/extending.py --check` to fail when they are stale.",
        "",
        "The generated pages say what exists today. The written pages at the end are headings",
        "for later slices to fill.",
        "",
        "## Socket list",
        "",
        "The risk socket is the five slots a host fills. A block in a slot implements the",
        "protocol's `update` method, or `before_order` for the cross-unit hook, and answers with",
        "the shape beside it.",
        "",
        "| Slot | Protocol | Answers | For |",
        "|---|---|---|---|",
    ]
    for slot, protocol in _SLOTS:
        lines.append(
            f"| {slot} | `{protocol.__name__}` | {_answer(protocol)} | {_summary(protocol)} |"
        )
    lines += [
        "",
        "## Refused fields",
        "",
        f"`{_FORMAT}` refuses these fields by name. The code and the reason are the compiler's",
        "own. A dash means the field has no `_shape_problems` refusal: the compiler reads it,",
        "or the census labels it.",
        "",
        "| Field | Where | Code | Reason |",
        "|---|---|---|---|",
    ]
    for name in names:
        refusal = refused.get(name)
        if refusal is None:
            lines.append(f"| `{name}` | - | - | - |")
        else:
            lines.append(f"| `{name}` | `{refusal.where}` | `{refusal.code}` | {refusal.reason} |")
    lines += [
        "",
        "## Block answer shapes",
        "",
        "A block answers with one of these shapes. A block's face declares one output type.",
        "",
        "| Answer | Fields | Answered by |",
        "|---|---|---|",
    ]
    for model, answered_by in _ANSWERS:
        lines.append(f"| `{model.__name__}` | {_answer_fields(model)} | {answered_by} |")
    outputs = ", ".join(f"`{member.value}`" for member in OutputType)
    lines += ["", f"The output types are {outputs}.", "", "## Journal kinds", ""]
    lines += [
        "A unit's rows land under these journal kinds. The host owns the kind name and the",
        "writing. QML owns the row shape.",
        "",
        "| Kind | Row | Written by |",
        "|---|---|---|",
    ]
    for row, kind, writer in _JOURNAL:
        lines.append(f"| `{kind}` | `{row.__name__}` | {writer} |")
    lines += [
        "",
        "The unit journal also accepts host-owned kinds for the wire and for accounting",
        "(`order`, `fill`, `trade`, `guard`, `risk_event`, `would_have`, `data_event`, `cash`).",
        "QML writes none of those rows.",
        "",
        "## Why each seat exists",
        "",
        "## The traps",
        "",
        "## How to add a thing",
        "",
        "## Debugging one size",
        "",
        "## The three tiers of change",
        "",
    ]
    return "\n".join(lines)


def _first_difference(expected: Sequence[str], actual: Sequence[str]) -> tuple[int, str] | None:
    for number, (want, got) in enumerate(zip(expected, actual, strict=False), start=1):
        if want != got:
            return number, f"expected {want!r}, found {got!r}"
    if len(expected) > len(actual):
        return len(actual) + 1, f"missing {expected[len(actual)]!r}"
    if len(actual) > len(expected):
        return len(expected) + 1, f"unexpected {actual[len(expected)]!r}"
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check qml/EXTENDING.md.")
    parser.add_argument("--check", action="store_true", help="fail when the guide is stale")
    parser.add_argument("--guide", type=Path, default=GUIDE, help="the guide file")
    args = parser.parse_args(argv)
    guide = cast("Path", args.guide)
    text = render()
    if not cast("bool", args.check):
        guide.write_text(text, encoding="utf-8")
        print(f"wrote {guide}")
        return 0
    if not guide.is_file():
        print(f"{guide}: missing", file=sys.stderr)
        return 1
    difference = _first_difference(text.splitlines(), guide.read_text("utf-8").splitlines())
    if difference is not None:
        number, message = difference
        print(f"{guide}:{number}: stale, {message}", file=sys.stderr)
        return 1
    print(f"current: {guide}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
