"""The JSON Schema 2020-12 of ``qmx.unit/1``, generated from the typed model (AD-102).

``shape_of`` reads the model's type hints once into a small shape tree. ``schema()`` writes
that tree as JSON Schema and ``qml.unit.parse`` walks the same tree, so the committed
schema and the parser accept the same documents. Everything is inlined, with no ``$ref``,
so the schema still works when the Library embeds it as the ``unit`` kind's ``fields``.
"""

from __future__ import annotations

import json
import types
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, fields, is_dataclass
from decimal import Decimal
from enum import StrEnum
from functools import cache
from typing import TypeAlias, Union, get_args, get_origin, get_type_hints

from qml.unit.model import EntryRef, Unit

__all__ = [
    "DECIMAL_PATTERN",
    "ENTRY_REF_PATTERN",
    "Array",
    "Boolean",
    "Choice",
    "DecimalText",
    "Field",
    "Integer",
    "Map",
    "OneOf",
    "Record",
    "Ref",
    "Shape",
    "Text",
    "schema",
    "schema_text",
    "shape_of",
]

DECIMAL_PATTERN = r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"
ENTRY_REF_PATTERN = r"^[a-z0-9][a-z0-9._-]*@[1-9][0-9]*$"


@dataclass(frozen=True)
class Text:
    pattern: str | None = None


@dataclass(frozen=True)
class Integer:
    minimum: int | None = None


@dataclass(frozen=True)
class Boolean:
    pass


@dataclass(frozen=True)
class DecimalText:
    pass


@dataclass(frozen=True)
class Ref:
    """``entry_id@version``, parsed to :class:`EntryRef`."""


@dataclass(frozen=True)
class Choice:
    vocabulary: type[StrEnum]


@dataclass(frozen=True)
class Array:
    item: Shape


@dataclass(frozen=True)
class Map:
    value: Shape


@dataclass(frozen=True)
class Field:
    name: str
    key: str
    shape: Shape
    required: bool


@dataclass(frozen=True)
class Record:
    model: type
    fields: tuple[Field, ...]


@dataclass(frozen=True)
class OneOf:
    choices: tuple[Record, ...]


Shape: TypeAlias = (
    Text | Integer | Boolean | DecimalText | Ref | Choice | Array | Map | Record | OneOf
)


def _shape(hint: object, metadata: Mapping[str, object]) -> Shape:
    origin = get_origin(hint)
    if origin in (Union, types.UnionType):
        members = [arg for arg in get_args(hint) if arg is not type(None)]
        if len(members) == 1:
            return _shape(members[0], metadata)
        return OneOf(tuple(_record(member) for member in members))
    if origin is tuple:
        return Array(_shape(get_args(hint)[0], {}))
    if origin is Mapping:
        return Map(_shape(get_args(hint)[1], {}))
    if hint is str:
        pattern = metadata.get("pattern")
        return Text(pattern if isinstance(pattern, str) else None)
    if hint is bool:
        return Boolean()
    if hint is int:
        minimum = metadata.get("minimum")
        return Integer(minimum if isinstance(minimum, int) else None)
    if hint is Decimal:
        return DecimalText()
    if hint is EntryRef:
        return Ref()
    if isinstance(hint, type) and issubclass(hint, StrEnum):
        return Choice(hint)
    if isinstance(hint, type) and is_dataclass(hint):
        return _record(hint)
    raise TypeError(f"the unit model uses a type the schema cannot express: {hint!r}")


@cache
def _record(model: object) -> Record:
    if not (isinstance(model, type) and is_dataclass(model)):
        raise TypeError(f"not a model dataclass: {model!r}")
    hints = get_type_hints(model)
    return Record(
        model,
        tuple(
            Field(
                name=item.name,
                key=str(item.metadata.get("key", item.name)),
                shape=_shape(hints[item.name], item.metadata),
                required=item.default is MISSING and item.default_factory is MISSING,
            )
            for item in fields(model)
        ),
    )


def shape_of() -> Record:
    """The shape tree of the whole unit document."""
    return _record(Unit)


def _json(shape: Shape) -> dict[str, object]:
    match shape:
        case Text(pattern=None):
            return {"type": "string"}
        case Text(pattern=pattern):
            return {"type": "string", "pattern": pattern}
        case Integer(minimum=None):
            return {"type": "integer"}
        case Integer(minimum=minimum):
            return {"type": "integer", "minimum": minimum}
        case Boolean():
            return {"type": "boolean"}
        case DecimalText():
            return {"type": "string", "pattern": DECIMAL_PATTERN}
        case Ref():
            return {"type": "string", "pattern": ENTRY_REF_PATTERN}
        case Choice(vocabulary=vocabulary):
            return {"type": "string", "enum": [member.value for member in vocabulary]}
        case Array(item=item):
            return {"type": "array", "items": _json(item)}
        case Map(value=value):
            return {"type": "object", "additionalProperties": _json(value)}
        case Record(fields=record_fields):
            body: dict[str, object] = {
                "type": "object",
                "properties": {item.key: _json(item.shape) for item in record_fields},
            }
            required = [item.key for item in record_fields if item.required]
            if required:
                body["required"] = required
            body["additionalProperties"] = False
            return body
        case OneOf(choices=choices):
            return {"oneOf": [_json(choice) for choice in choices]}


def schema() -> dict[str, object]:
    """The JSON Schema 2020-12 of ``qmx.unit/1``. Shape only: types, required keys, enums."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "qmx.unit/1",
        "description": (
            "A QMX unit: one complete trading algorithm. Generated from qml.unit.model; "
            "completeness and cross-field rules are later check layers."
        ),
    } | _json(shape_of())


def schema_text() -> str:
    """``schema()`` as the committed file's text."""
    return json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"
