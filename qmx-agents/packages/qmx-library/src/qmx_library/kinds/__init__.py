"""The kinds registry (Library AD-3, AD-17): one `<kind>.schema.json` per roster entry, each with a
`class`. The roster is data; code reads a kind's class, never a list of kinds.

A kind file may also list `checks` (Part A AD-112): each names a checker, the event it runs on
(`put` or `publish`) and an optional `applies_when` (a JSON pointer and the value it must hold).
The host registers checker functions by name; a check that applies with no registered checker
refuses `checker_unavailable`, so a missing checker never passes silently. A refusal carries every
problem and keeps the first problem's message as its text.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path
from typing import Any, Final, Literal, cast

from jsonschema import Draft202012Validator, ValidationError
from pydantic import JsonValue

from qmx_library.port import Class, JsonObject, LibraryRefused

HERE: Final = Path(__file__).parent

type Event = Literal["put", "publish"]


@dataclass(frozen=True, slots=True)
class Problem:
    """One thing wrong with an object's fields: what, the JSON pointers it sits at, the refusal
    code it raises, and the checker's own name for it (QML's layer and problem kind, say)."""

    message: str
    where: tuple[str, ...] = ("",)
    code: str = "schema_invalid"
    rule: str = ""

    def as_json(self) -> JsonObject:
        return {
            "code": self.code,
            "rule": self.rule,
            "message": self.message,
            "where": list(self.where),
        }


type Checker = Callable[[JsonObject], Sequence[Problem]]
"""A registered checker: every problem it finds in one object's fields, none when it passes."""


class KindRefused(LibraryRefused):
    """A refusal by a kind or its checks: the text is the first problem's, `problems` is all."""

    def __init__(self, code: str, message: str, problems: Sequence[Problem]) -> None:
        super().__init__(code, message)
        self.problems = tuple(problems)


@dataclass(frozen=True, slots=True)
class Check:
    checker: str
    on: Event
    pointer: str | None = None
    equals: JsonValue = None

    def applies(self, fields: JsonObject) -> bool:
        if self.pointer is None:
            return True
        found: object = fields
        for token in self.pointer.split("/")[1:]:
            if not isinstance(found, dict):
                return False
            key = token.replace("~1", "/").replace("~0", "~")
            found = cast(dict[str, object], found).get(key)
        return found == self.equals


@dataclass(frozen=True, slots=True)
class Slot:
    pattern: str
    media_type: str
    required: bool
    transient: bool


def _pointer(error: ValidationError) -> str:
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in error.absolute_path
    )


@dataclass(frozen=True, slots=True)
class Kind:
    name: str
    schema_version: int
    klass: Class
    retired: bool
    slots: tuple[Slot, ...]
    annotations: frozenset[str]
    validator: Draft202012Validator
    checks: tuple[Check, ...] = ()

    def slot(self, name: str) -> Slot:
        for slot in self.slots:
            if fnmatchcase(name, slot.pattern):
                return slot
        raise LibraryRefused("schema_invalid", f"a {self.name} has no blob slot {name!r}")

    def check(
        self, fields: JsonObject, slots: set[str], checkers: Mapping[str, Checker] | None = None
    ) -> None:
        """The put check: the kind's JSON Schema, its required blobs and its `put` checks."""
        if self.retired:
            raise LibraryRefused("unknown_kind", f"{self.name} is retired")
        found: Iterable[ValidationError] = self.validator.iter_errors(fields)  # pyright: ignore[reportUnknownMemberType]
        shape = [Problem(error.message, (_pointer(error),)) for error in sorted(found, key=str)]
        blobs = [
            Problem(f"a {self.name} needs the blob {s.pattern}")
            for s in self.slots
            if s.required and s.pattern not in slots
        ]
        checked = self._run("put", fields, checkers or {})
        texts = [f"{self.name}: {p.message}" for p in shape] + [p.message for p in blobs]
        texts += [f"{self.name}: {p.message}" for p in checked]
        problems = [*shape, *blobs, *checked]
        if problems:
            raise KindRefused(problems[0].code, texts[0], problems)

    def admit(self, fields: JsonObject, checkers: Mapping[str, Checker]) -> None:
        """The publish check: every `publish` check that applies, before `main` moves."""
        problems = self._run("publish", fields, checkers)
        if problems:
            raise KindRefused(problems[0].code, f"{self.name}: {problems[0].message}", problems)

    def _run(
        self, event: Event, fields: JsonObject, checkers: Mapping[str, Checker]
    ) -> list[Problem]:
        problems: list[Problem] = []
        for check in self.checks:
            if check.on != event or not check.applies(fields):
                continue
            checker = checkers.get(check.checker)
            if checker is None:
                problems.append(
                    Problem(
                        f"no checker {check.checker!r} is registered on this host",
                        ("",),
                        "checker_unavailable",
                    )
                )
                continue
            problems += checker(fields)
        return problems


def _check(raw: dict[str, Any]) -> Check:
    when = cast(dict[str, Any] | None, raw.get("applies_when"))
    return Check(
        str(raw["checker"]),
        cast(Event, raw["on"]),
        None if when is None else str(when["pointer"]),
        None if when is None else cast(JsonValue, when["equals"]),
    )


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
        tuple(_check(c) for c in cast(list[dict[str, Any]], doc.get("checks", []))),
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
