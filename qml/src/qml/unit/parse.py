"""Layer A of the unit check: the document's shape, every problem at once (AD-102).

``parse`` walks the same shape tree ``schema()`` is written from, so it accepts exactly the
documents the committed schema accepts, and also turns decimal strings into exact values
and ``entry_id@version`` strings into :class:`EntryRef`. It never stops at the first
problem: each one carries a kind and the JSON pointer of the value it is about.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final, cast

from qml.unit.model import EntryRef, Unit
from qml.unit.schema import (
    DECIMAL_PATTERN,
    ENTRY_REF_PATTERN,
    Array,
    Boolean,
    Choice,
    DecimalText,
    Integer,
    Map,
    OneOf,
    Record,
    Ref,
    Shape,
    Text,
    shape_of,
)

__all__ = ["Parsed", "Problem", "ProblemKind", "parse", "parse_text"]


class ProblemKind(StrEnum):
    NOT_JSON = "not_json"
    MISSING_FIELD = "missing_field"
    UNKNOWN_FIELD = "unknown_field"
    WRONG_TYPE = "wrong_type"
    NOT_IN_VOCABULARY = "not_in_vocabulary"
    NOT_DECIMAL = "not_decimal"
    BAD_REF = "bad_ref"
    BAD_FORMAT = "bad_format"
    TOO_SMALL = "too_small"
    NO_SHAPE_MATCHES = "no_shape_matches"
    # Layer C, the numbers (qml.numbers.check)
    MOTION_NOT_ALLOWED = "motion_not_allowed"
    MOTION_INCOMPLETE = "motion_incomplete"
    RANGE_MISSING = "range_missing"
    RANGE_NOT_ALLOWED = "range_not_allowed"
    BAD_RANGE = "bad_range"
    OUTSIDE_RANGE = "outside_range"
    OUTSIDE_MEASURE = "outside_measure"
    NOT_IN_MEASURE = "not_in_measure"
    UNDECLARED_NUMBER = "undeclared_number"
    NO_RECORD = "no_record"
    NO_PIP = "no_pip"
    UNSETTLED_ORIGIN = "unsettled_origin"
    MEASURE_MISMATCH = "measure_mismatch"
    PERCENT_LOOKS_WHOLE = "percent_looks_whole"
    CADENCE_NOT_BUILT = "cadence_not_built"
    # Layer B, the references (qml.check)
    PIN_UNRESOLVED = "pin_unresolved"
    PIN_FINGERPRINT = "pin_fingerprint"
    ENTRY_FACE = "entry_face"
    BLOCK_SOURCE_MISSING = "block_source_missing"
    BLOCK_NOT_PINNED = "block_not_pinned"
    PARAMETER_MISSING = "parameter_missing"
    UNKNOWN_PARAMETER = "unknown_parameter"
    UNKNOWN_INPUT = "unknown_input"
    UNKNOWN_PORT = "unknown_port"
    INPUT_MISSING = "input_missing"
    UNKNOWN_MARKET = "unknown_market"
    UNKNOWN_STREAM = "unknown_stream"
    DUPLICATE_NAME = "duplicate_name"
    BAD_MIRROR = "bad_mirror"
    BAD_COMBINER = "bad_combiner"
    # Layer D, data levels and calendars
    DATA_LEVEL_MISSING = "data_level_missing"
    DATA_LEVELS_UNKNOWN = "data_levels_unknown"
    CALENDAR_NOT_HELD = "calendar_not_held"
    # Layer E, completeness
    NO_MARKET = "no_market"
    SIDE_MISSING = "side_missing"
    SIDE_UNUSED = "side_unused"
    NO_TRIGGER = "no_trigger"
    NO_EXIT = "no_exit"
    SIZER_MISSING = "sizer_missing"
    NO_SOURCE = "no_source"
    NO_ROLL = "no_roll"
    PLACEHOLDER = "placeholder"  # mock-data-scan: allow (the risk session's label, AD-116)
    NO_HALTS = "no_halts"
    NO_TIME_EXIT = "no_time_exit"
    # Layer F, code safety
    BLOCK_SYNTAX = "block_syntax"
    UNSAFE_CODE = "unsafe_code"
    LITERAL_IN_COMPARISON = "literal_in_comparison"
    # Across layers: a layer that could not run, and what only the compiler refuses
    LAYER_SKIPPED = "layer_skipped"
    NOT_COMPILED = "not_compiled"
    # Layer G's behaviour report, warnings only
    NO_TRADES = "no_trades"
    ONE_SIDE_ONLY = "one_side_only"
    EXITS_UNFIRED = "exits_unfired"
    SIGNAL_CONSTANT = "signal_constant"
    SHUFFLED_DAY_MATCHES = "shuffled_day_matches"


@dataclass(frozen=True)
class Problem:
    """One check problem, in the Problem shape of ``qmx.check/1`` (CONTRACTS.md 3.1)."""

    kind: ProblemKind
    where: tuple[str, ...]
    message: str
    hint: str
    layer: str = "A"
    nearest: tuple[str, ...] = ()


@dataclass(frozen=True)
class Parsed:
    """The typed unit when the shape holds, and every problem found either way."""

    unit: Unit | None
    problems: tuple[Problem, ...]


class _Failed:
    pass


_FAILED: Final = _Failed()
_TYPE_NAMES: Final[Mapping[type, str]] = {
    dict: "an object",
    list: "a list",
    str: "a string",
    int: "an integer",
    bool: "true or false",
}


def _pointer(parent: str, key: str | int) -> str:
    token = str(key).replace("~", "~0").replace("/", "~1")
    return f"{parent}/{token}"


def _given(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return "a JSON number with a fraction"
    for kind, name in _TYPE_NAMES.items():
        if type(value) is kind:
            return name
    return type(value).__name__


class _Walker:
    def __init__(self) -> None:
        self.problems: list[Problem] = []

    def problem(self, kind: ProblemKind, where: str, message: str, hint: str) -> _Failed:
        self.problems.append(Problem(kind, (where,), message[:300], hint[:300]))
        return _FAILED

    def wrong_type(self, where: str, wanted: str, value: object) -> _Failed:
        return self.problem(
            ProblemKind.WRONG_TYPE,
            where,
            f"expected {wanted}, found {_given(value)}",
            f"write {wanted} here",
        )

    def walk(self, shape: Shape, value: object, where: str) -> object:
        match shape:
            case Text(pattern=pattern):
                if not isinstance(value, str):
                    return self.wrong_type(where, "a string", value)
                if pattern is not None and re.fullmatch(pattern, value) is None:
                    return self.problem(
                        ProblemKind.BAD_FORMAT,
                        where,
                        f"{value!r} does not match {pattern}",
                        "a clock time is written HH:MM",
                    )
                return value
            case Integer(minimum=minimum):
                if type(value) is not int:
                    return self.wrong_type(where, "an integer", value)
                if minimum is not None and value < minimum:
                    return self.problem(
                        ProblemKind.TOO_SMALL,
                        where,
                        f"{value} is below the smallest allowed value {minimum}",
                        f"use {minimum} or more",
                    )
                return value
            case Boolean():
                if not isinstance(value, bool):
                    return self.wrong_type(where, "true or false", value)
                return value
            case DecimalText():
                if not isinstance(value, str):
                    return self.wrong_type(where, 'a decimal string such as "0.5"', value)
                if re.fullmatch(DECIMAL_PATTERN, value) is None:
                    return self.problem(
                        ProblemKind.NOT_DECIMAL,
                        where,
                        f"{value!r} is not a decimal string",
                        'write digits with an optional point, such as "0.02" or "100"',
                    )
                return Decimal(value)
            case Ref():
                if not isinstance(value, str):
                    return self.wrong_type(where, 'a reference such as "ema@1"', value)
                if re.fullmatch(ENTRY_REF_PATTERN, value) is None:
                    return self.problem(
                        ProblemKind.BAD_REF,
                        where,
                        f"{value!r} is not entry_id@version",
                        'name the entry and its version, such as "ema@1"',
                    )
                entry_id, version = value.rsplit("@", 1)
                return EntryRef(entry_id, int(version))
            case Choice(vocabulary=vocabulary):
                allowed = [member.value for member in vocabulary]
                if not isinstance(value, str):
                    return self.wrong_type(where, "a string", value)
                if value not in allowed:
                    return self.problem(
                        ProblemKind.NOT_IN_VOCABULARY,
                        where,
                        f"{value!r} is not one of {', '.join(allowed)}"[:300],
                        f"pick one of {', '.join(allowed)}",
                    )
                return vocabulary(value)
            case Array(item=item):
                if not isinstance(value, list):
                    return self.wrong_type(where, "a list", value)
                items = cast(list[object], value)
                walked = [
                    self.walk(item, entry, _pointer(where, i)) for i, entry in enumerate(items)
                ]
                return _FAILED if any(w is _FAILED for w in walked) else tuple(walked)
            case Map(value=inner):
                if not isinstance(value, dict):
                    return self.wrong_type(where, "an object", value)
                entries = cast(dict[str, object], value)
                walked_map = {
                    k: self.walk(inner, v, _pointer(where, k)) for k, v in entries.items()
                }
                return _FAILED if any(w is _FAILED for w in walked_map.values()) else walked_map
            case Record():
                return self.record(shape, value, where)
            case OneOf(choices=choices):
                return self.one_of(choices, value, where)

    def record(self, shape: Record, value: object, where: str) -> object:
        if not isinstance(value, dict):
            return self.wrong_type(where, "an object", value)
        given = cast(dict[str, object], value)
        known = {item.key for item in shape.fields}
        failed = False
        for key in given:
            if key not in known:
                failed = True
                self.problem(
                    ProblemKind.UNKNOWN_FIELD,
                    _pointer(where, key),
                    f"{key!r} is not a field here",
                    f"the fields here are {', '.join(sorted(known))}",
                )
        built: dict[str, object] = {}
        for item in shape.fields:
            if item.key not in given:
                if item.required:
                    failed = True
                    self.problem(
                        ProblemKind.MISSING_FIELD,
                        _pointer(where, item.key),
                        f"the required field {item.key!r} is missing",
                        f"add {item.key!r}",
                    )
                continue
            walked = self.walk(item.shape, given[item.key], _pointer(where, item.key))
            failed = failed or walked is _FAILED
            built[item.name] = walked
        return _FAILED if failed else shape.model(**built)

    def one_of(self, choices: tuple[Record, ...], value: object, where: str) -> object:
        if not isinstance(value, dict):
            return self.wrong_type(where, "an object", value)
        given = cast(dict[str, object], value)
        keys = set(given)
        fitting = [
            choice
            for choice in choices
            if keys <= {item.key for item in choice.fields}
            and {item.key for item in choice.fields if item.required} <= keys
        ]
        if len(fitting) == 1:
            return self.record(fitting[0], given, where)
        forms = " or ".join(
            "{" + ", ".join(item.key for item in choice.fields if item.required) + "}"
            for choice in choices
        )
        return self.problem(
            ProblemKind.NO_SHAPE_MATCHES,
            where,
            f"this object fits none of its forms, which are {forms}",
            "keep exactly the keys of one form",
        )


def parse(document: object) -> Parsed:
    """Check a decoded JSON document against ``qmx.unit/1``'s shape and build the model."""
    walker = _Walker()
    built = walker.walk(shape_of(), document, "")
    unit = built if isinstance(built, Unit) else None
    return Parsed(unit, tuple(walker.problems))


def parse_text(text: str) -> Parsed:
    """``parse`` for JSON text; text that is not JSON is one ``not_json`` problem."""
    try:
        document: object = json.loads(text)
    except json.JSONDecodeError as error:
        problem = Problem(
            ProblemKind.NOT_JSON,
            ("",),
            f"not JSON: {error.msg} at line {error.lineno} column {error.colno}",
            "fix the JSON syntax first",
        )
        return Parsed(None, (problem,))
    return parse(document)
