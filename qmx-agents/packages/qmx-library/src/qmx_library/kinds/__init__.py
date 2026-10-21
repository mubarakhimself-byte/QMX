"""The kinds registry (Library AD-3, AD-17): one `<kind>.schema.json` per roster entry, each with a
`class`. The roster is data; code reads a kind's class, never a list of kinds.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path
from typing import Any, Final, cast

from jsonschema import Draft202012Validator, ValidationError

from qmx_library.port import Class, JsonObject, LibraryRefused

HERE: Final = Path(__file__).parent


@dataclass(frozen=True, slots=True)
class Slot:
    pattern: str
    media_type: str
    required: bool
    transient: bool


@dataclass(frozen=True, slots=True)
class Kind:
    name: str
    schema_version: int
    klass: Class
    retired: bool
    slots: tuple[Slot, ...]
    annotations: frozenset[str]
    validator: Draft202012Validator

    def slot(self, name: str) -> Slot:
        for slot in self.slots:
            if fnmatchcase(name, slot.pattern):
                return slot
        raise LibraryRefused("schema_invalid", f"a {self.name} has no blob slot {name!r}")

    def check(self, fields: JsonObject, slots: set[str]) -> None:
        if self.retired:
            raise LibraryRefused("unknown_kind", f"{self.name} is retired")
        found: Iterable[ValidationError] = self.validator.iter_errors(fields)  # pyright: ignore[reportUnknownMemberType]
        problems = sorted(found, key=str)
        if problems:
            raise LibraryRefused("schema_invalid", f"{self.name}: {problems[0].message}")
        missing = [s.pattern for s in self.slots if s.required and s.pattern not in slots]
        if missing:
            raise LibraryRefused("schema_invalid", f"a {self.name} needs the blob {missing[0]}")


def _kind(path: Path) -> Kind:
    doc = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    slots = tuple(
        Slot(
            pattern,
            str(spec["media_type"]),
            bool(spec.get("required", False)),
            spec.get("class") == "transient",
        )
        for pattern, spec in cast(dict[str, dict[str, Any]], doc["blobs"]).items()
    )
    return Kind(
        str(doc["kind"]),
        int(doc["schema_version"]),
        cast(Class, doc["class"]),
        bool(doc["retired"]),
        slots,
        frozenset(cast(list[str], doc["annotations"])),
        Draft202012Validator(doc["fields"]),
    )


@cache
def roster(folder: Path = HERE) -> dict[str, Kind]:
    return {kind.name: kind for kind in map(_kind, sorted(folder.glob("*.schema.json")))}


def kind(name: str) -> Kind:
    found = roster().get(name)
    if found is None:
        raise LibraryRefused("unknown_kind", f"{name!r} is not a registered kind")
    return found


def schema_files() -> list[Path]:
    return sorted(HERE.glob("*.schema.json"))
