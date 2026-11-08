"""The unit document's two halves, and one fingerprint each (AD-2).

``sections`` is the one partition. The logic half holds ``markets``, ``streams``,
``direction``, ``logic``, ``exit_set``, ``sessions``, ``position_limit``, every number a logic
slot or an exit binds, and every pin those blocks use. The risk half holds ``sizer``,
``modifiers``, ``gates``, ``halts``, ``reads``, ``tolerations`` and ``stages``, every number
bound only there, and their pins. Anything the risk list does not name is logic, so a new or
forgotten field cannot fall between the two; only ``recipe`` sits outside both, because a pod
stamp must not move a fingerprint.

A number bound by a logic slot or an exit is logic even when the risk half binds it too, and a
pin both halves use is logic for the same reason. A ``reads`` row is logic when a logic slot's
input names its surface, ``reading:<id>:<market>`` (WALKS 7). A ``stages`` block is logic when
its selector or a stage row's numbers name a number the logic half binds, so a risk edit can
never move an exit number or a logic number unproven.

Each fingerprint hashes the half as the document writes it and the compiler format version, so
a format bump moves both halves on purpose (AD-3, AD-19). Nothing is rebuilt from the typed
model: the input is the decoded document, the same input the whole-document fingerprint takes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.core.refusal import is_refusal

__all__ = ["OUTSIDE_BOTH", "RISK_FIELDS", "Section", "sections"]

RISK_FIELDS: Final[frozenset[str]] = frozenset(
    {"sizer", "modifiers", "gates", "halts", "reads", "tolerations", "stages"}
)
"""AD-2's risk section. Every other field but ``recipe`` is logic."""

OUTSIDE_BOTH: Final[frozenset[str]] = frozenset({"recipe"})
"""Only a pod stamp sits outside both halves, so a stamp moves no fingerprint."""


@dataclass(frozen=True, slots=True)
class Section:
    """One half of a document: its fields as written, and their fingerprint."""

    fields: Mapping[str, object]
    fingerprint: Fingerprint


def sections(
    document: Mapping[str, object], compiler_format_version: int
) -> tuple[Section, Section]:
    """The logic half and the risk half of ``document``, in that order."""
    numbers = _map(document.get("numbers"))
    logic_numbers, risk_numbers = _number_halves(document, numbers)
    risk_pins = _risk_pins(document, logic_numbers, risk_numbers)
    logic_inputs = _input_values(document.get("logic"))
    stages_is_logic = bool((_selector(document) | _staged(document)) & logic_numbers)

    logic: dict[str, object] = {}
    risk: dict[str, object] = {}
    for key, value in document.items():
        if key in OUTSIDE_BOTH:
            continue
        if key == "numbers":
            logic[key] = {name: spec for name, spec in numbers.items() if name in logic_numbers}
            risk[key] = {name: spec for name, spec in numbers.items() if name in risk_numbers}
        elif key == "pins":
            logic[key], risk[key] = _split_pins(value, risk_pins)
        elif key == "reads":
            logic[key], risk[key] = _split_reads(value, logic_inputs)
        elif key == "stages" and stages_is_logic:
            logic[key] = value
        elif key in RISK_FIELDS:
            risk[key] = value
        else:
            logic[key] = value
    return (
        Section(logic, _fingerprint(logic, compiler_format_version, "logic")),
        Section(risk, _fingerprint(risk, compiler_format_version, "risk")),
    )


def _fingerprint(
    fields: Mapping[str, object], compiler_format_version: int, half: str
) -> Fingerprint:
    made = fingerprint(
        {
            "section": half,
            "compiler_format_version": compiler_format_version,
            "fields": fields,
        }
    )
    if is_refusal(made):  # pragma: no cover - the document reaching here is decoded JSON
        raise ValueError(f"the {half} half is not hashable: {made}")
    return made.value


def _map(value: object) -> Mapping[str, object]:
    """The object as a JSON object, or nothing when it is not one."""
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _items(value: object) -> list[tuple[str, object]]:
    return list(_map(value).items())


def _values(value: object) -> list[object]:
    return cast("list[object]", value) if isinstance(value, list) else []


def _number_halves(
    document: Mapping[str, object], numbers: Mapping[str, object]
) -> tuple[frozenset[str], frozenset[str]]:
    """Each number's half. A number bound in both is logic; an unbound number is logic."""
    logic = _number_refs(document.get("logic")) | _number_refs(document.get("exit_set"))
    risk = set(_staged(document))
    for field in RISK_FIELDS:
        risk |= _number_refs(document.get(field))
    bound = frozenset(name for name in numbers if name in logic or name not in risk)
    return bound, frozenset(numbers) - bound


def _risk_pins(
    document: Mapping[str, object],
    logic_numbers: frozenset[str],
    risk_numbers: frozenset[str],
) -> frozenset[str]:
    """The pins only the risk half uses, by its bindings and its numbers' motion rules."""
    logic = _block_refs(document.get("logic")) | _block_refs(document.get("exit_set"))
    risk: set[str] = set()
    for field in RISK_FIELDS:
        risk |= _block_refs(document.get(field))
    for name, number in _map(document.get("numbers")).items():
        if name in logic_numbers:
            logic |= _rule_refs(number)
        elif name in risk_numbers:
            risk |= _rule_refs(number)
    return frozenset(risk) - logic


def _split_pins(value: object, risk: frozenset[str]) -> tuple[list[object], list[object]]:
    """Each pin goes with the half that uses it. A pin in both, or in neither, is logic."""
    pins = _values(value)
    return (
        [pin for pin in pins if _pin_ref(pin) not in risk],
        [pin for pin in pins if _pin_ref(pin) in risk],
    )


def _pin_ref(pin: object) -> str:
    body = _map(pin)
    return f"{body.get('entry_id')}@{body.get('version')}"


def _split_reads(value: object, logic_inputs: frozenset[str]) -> tuple[list[object], list[object]]:
    """Each reading goes with the half that reads it. A logic slot names it by its surface."""
    rows = _values(value)
    return (
        [row for row in rows if _read_surface(row) in logic_inputs],
        [row for row in rows if _read_surface(row) not in logic_inputs],
    )


def _read_surface(row: object) -> str | None:
    reading, market = _map(row).get("reading"), _map(row).get("market")
    if isinstance(reading, str) and isinstance(market, str):
        return f"reading:{reading.rsplit('@', 1)[0]}:{market}"
    return None


def _input_values(node: object) -> frozenset[str]:
    """Every string a binding under ``node`` names as one of its inputs."""
    found: set[str] = set()
    for key, value in _items(node):
        if key == "inputs":
            found |= {item for item in _map(value).values() if isinstance(item, str)}
        found |= _input_values(value)
    for value in _values(node):
        found |= _input_values(value)
    return frozenset(found)


def _number_refs(node: object) -> frozenset[str]:
    """Every number a binding under ``node`` names in its params."""
    found: set[str] = set()
    for key, value in _items(node):
        if key == "number" and isinstance(value, str) and len(_items(node)) == 1:
            found.add(value)
        found |= _number_refs(value)
    for value in _values(node):
        found |= _number_refs(value)
    return frozenset(found)


def _block_refs(node: object) -> frozenset[str]:
    """Every block a binding under ``node`` names."""
    found: set[str] = set()
    for key, value in _items(node):
        if key == "block" and isinstance(value, str):
            found.add(value)
        found |= _block_refs(value)
    for value in _values(node):
        found |= _block_refs(value)
    return frozenset(found)


def _rule_refs(number: object) -> frozenset[str]:
    """The motion rule a number names, which is the number's own pin."""
    rule = _map(_map(number).get("motion")).get("rule")
    return frozenset({rule}) if isinstance(rule, str) else frozenset()


def _selector(document: Mapping[str, object]) -> frozenset[str]:
    selector = _map(document.get("stages")).get("selector")
    return frozenset({selector}) if isinstance(selector, str) else frozenset()


def _staged(document: Mapping[str, object]) -> frozenset[str]:
    """Every number a stage row sets a value for."""
    found: set[str] = set()
    for row in _map(_map(document.get("stages")).get("rows")).values():
        found |= set(_map(_map(row).get("numbers")))
    return frozenset(found)
