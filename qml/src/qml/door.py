"""QML's door: five pure verbs over data the host passes (Part A AD-101).

``new``, ``check``, ``compile``, ``find`` and ``explain``. No verb reads a file, a clock, the
network or the Library: the host gathers the pinned entries, their block sources and the
instrument records into a ``CompileContext`` and passes it in. Backtest is QMB's and promote
is his click, so neither is a verb.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from qml.check import CheckResult, check_and_compile
from qml.check import check as _check
from qml.compile import CompileContext, CompiledUnit
from qml.unit.model import MirrorSide, NumberParam, NumberSpec, Side, SlotsSide, ValueParam
from qml.unit.parse import Problem, ProblemKind, parse

__all__ = ["Match", "check", "compile", "explain", "find", "new"]


def _tokens(pointer: str) -> list[str]:
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer.split("/")[1:]]


def _set(document: object, pointer: str, value: object) -> bool:
    tokens = _tokens(pointer)
    if not tokens:
        return False
    parent = document
    for token in tokens[:-1]:
        if isinstance(parent, dict):
            parent = cast("dict[str, object]", parent).get(token)
        elif isinstance(parent, list) and token.isdigit():
            items = cast("list[object]", parent)
            parent = items[int(token)] if int(token) < len(items) else None
        else:
            return False
    last = tokens[-1]
    if isinstance(parent, dict):
        cast("dict[str, object]", parent)[last] = copy.deepcopy(value)
        return True
    if isinstance(parent, list) and last.isdigit():
        items = cast("list[object]", parent)
        if int(last) < len(items):
            items[int(last)] = copy.deepcopy(value)
            return True
    return False


def new(
    template: Mapping[str, object], overrides: Mapping[str, object] | None = None
) -> dict[str, object] | tuple[Problem, ...]:
    """A new document: a copy of ``template`` with each override set at its JSON pointer.

    A pointer whose parent does not exist is a problem; every one is named at once.
    """
    document = copy.deepcopy(dict(template))
    problems = tuple(
        Problem(
            ProblemKind.UNKNOWN_FIELD,
            (pointer,),
            f"{pointer} names no place in the template",
            "point at an existing field, or at a new key of an existing object",
        )
        for pointer, value in (overrides or {}).items()
        if not _set(document, pointer, value)
    )
    return problems or document


def check(
    document: object, context: CompileContext, previous_problem_set: str | None = None
) -> CheckResult:
    """Layers A to F, every problem at once, counts first (``qmx.check/1``)."""
    return _check(document, context, previous_problem_set)


def compile(document: object, context: CompileContext) -> CompiledUnit | CheckResult:
    """The compiled unit, or the failing check: nothing unchecked ever compiles (AD-111)."""
    result, compiled = check_and_compile(document, context)
    return compiled if compiled is not None else result


@dataclass(frozen=True)
class Match:
    """One entry ``find`` returned: its pin, its type and its one-line definition."""

    pin: str
    component_type: str
    line: str


def _words(raw: Mapping[str, object]) -> set[str]:
    parts: list[str] = []
    for key in ("entry_id", "family", "component_type", "definition"):
        value = raw.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("eligible_roles", "aliases"):
        value = raw.get(key)
        if isinstance(value, list):
            parts.extend(v for v in cast("list[object]", value) if isinstance(v, str))
    return {w for part in parts for w in part.lower().replace("-", " ").split()}


def find(query: str, index: Mapping[str, bytes]) -> tuple[Match, ...]:
    """The entries of ``index`` (``entry.json`` bytes by pin) that share words with ``query``,
    most shared words first."""
    wanted = set(query.lower().replace("-", " ").split())
    scored: list[tuple[int, Match]] = []
    for pin, data in index.items():
        try:
            raw = cast("dict[str, object]", json.loads(data.decode("utf-8")))
        except (UnicodeDecodeError, ValueError):
            continue
        score = len(wanted & _words(raw))
        if score:
            definition = raw.get("definition")
            kind = raw.get("component_type")
            scored.append(
                (
                    score,
                    Match(
                        pin,
                        kind if isinstance(kind, str) else "",
                        definition if isinstance(definition, str) else "",
                    ),
                )
            )
    scored.sort(key=lambda s: (-s[0], s[1].pin))
    return tuple(match for _, match in scored)


def _param(value: NumberParam | ValueParam) -> str:
    return value.number if isinstance(value, NumberParam) else str(value.value)


def _span(spec: NumberSpec) -> str:
    span = spec.range
    if span is None:
        return "range none"
    return f"range {span.min} to {span.max} by {span.step}"


def _why(spec: NumberSpec) -> str:
    """Where the value comes from, who argues it, and why it holds. AD-14's four answers."""
    said = f"owner {spec.owner or 'unstated'}, because {spec.reason or 'it states no reason'}"
    return said if spec.derivation is None else f"{said}, from {spec.derivation}"


def explain(document: object, context: CompileContext) -> tuple[str, ...]:
    """The unit in plain lines: what it trades, each side's slots, exits, sizer and numbers,
    and its check counts."""
    result = _check(document, context)
    counts = f"check: {len(result.errors)} errors, {len(result.warnings)} warnings"
    unit = parse(document).unit
    if unit is None:
        return ("this document does not read as a unit", counts)
    lines = [
        f"{unit.title or unit.unit_id}: {unit.claim_card.idea}",
        f"trades {unit.direction.value} on {', '.join(m.market_id for m in unit.markets)}",
    ]
    for side, given in ((Side.LONG, unit.logic.long), (Side.SHORT, unit.logic.short)):
        if isinstance(given, MirrorSide):
            lines.append(f"{side.value}: mirrors the {given.mirror_of.value} side")
        elif isinstance(given, SlotsSide):
            for name, slot in given.slots.items():
                bound = "; ".join(
                    f"{b.name} = {b.block}("
                    + ", ".join(f"{k}={_param(v)}" for k, v in b.params.items())
                    + ")"
                    for b in slot.bindings
                )
                lines.append(f"{side.value} {name} ({slot.combiner.kind.value}): {bound}")
    lines += [f"exit {b.name} = {b.block} on the {b.scope.value}" for b in unit.exit_set]
    if unit.sizer is not None:
        lines.append(f"sizer {unit.sizer.name} = {unit.sizer.block}")
    lines += [
        f"number {name}: {spec.kind.value} {spec.measure.value}, default {spec.default}, "
        f"{_span(spec)}, moves by {spec.motion.mode.value}, origin {spec.origin.value}, "
        f"{_why(spec)}"
        for name, spec in unit.numbers.items()
    ]
    lines.append(counts)
    return tuple(lines)
