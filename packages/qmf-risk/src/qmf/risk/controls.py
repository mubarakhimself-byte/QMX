"""A brake as a control row: what it reads, where it acts, what it does when it fires (AD-12).

A control row is the seat a halt binding lands in. The row is data. ``scope`` says where it acts;
``reads`` names the facts its block reads, derived from the block's face at compile; ``verb`` is
what the unit runs when the block fires; ``on_fire`` is what the fire does beside the verb;
``restore`` says how the row comes back; ``until_n`` is what it does before it has data; and
``shadow`` keeps a row that records a fire without running it.

The runner lives in ``qml.protocol.controls``. This module holds the types and the one pure rule
that decides whether a fired row refuses an entry, so a host or the fold reads a row without
importing ``qml`` (AD-21). It imports nothing from ``qml`` and nothing from a host.

``Verb`` has four words. ``no_new_entries`` is the one this build runs: a brake stops entries and
nothing else, so it can never reach an exit. ``reduce`` and ``flatten`` are stated and refused at
compile until their executor lands, and ``none`` fires without refusing anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Final

__all__ = [
    "ENTRY_SCOPES",
    "Answer",
    "ColdRule",
    "ControlRow",
    "OnFire",
    "Restore",
    "Verb",
    "gate_open",
    "refuses_entries",
]


class Verb(StrEnum):
    """What a fired row does. ``reduce`` and ``flatten`` land with their executor."""

    NONE = "none"
    NO_NEW_ENTRIES = "no_new_entries"
    REDUCE = "reduce"
    FLATTEN = "flatten"


class Restore(StrEnum):
    """How a row that fired comes back: a rule of its own, or his hand."""

    HAND = "hand"
    RULE = "rule"


class ColdRule(StrEnum):
    """What a row does before the facts it reads exist: warn, or run in shadow."""

    WARN = "warn"
    SHADOW = "shadow"


@dataclass(frozen=True, slots=True)
class OnFire:
    """What a fire does beside its verb: stand a scope down, raise a kill level, raise a card."""

    stand_down: str | None = None
    raise_kill: str | None = None
    card: bool = False


@dataclass(frozen=True, slots=True)
class ControlRow:
    """One brake, as the unit runs it. ``code`` is the brake's own word on its risk-event row."""

    name: str
    pin: str
    code: str
    scope: str
    reads: tuple[str, ...] = ()
    verb: Verb = Verb.NO_NEW_ENTRIES
    on_fire: OnFire = field(default_factory=OnFire)
    restore: Restore = Restore.HAND
    until_n: ColdRule = ColdRule.WARN
    shadow: bool = False
    enabled: bool | str = True
    """True, False, or the name of a fact that gates the row. A false row never runs."""

    @property
    def key(self) -> str:
        """The row's identity in one run: its scope and its name, unique per compiled unit."""
        return f"{self.scope}.{self.name}"


@dataclass(frozen=True, slots=True)
class Answer:
    """What one fired row answers: its verb, the factor a ``reduce`` carries, why, and its code."""

    verb: Verb
    factor: Decimal | None
    reason: str
    code: str


ENTRY_SCOPES: Final[frozenset[str]] = frozenset({"unit", "account"})
"""The scopes whose ``no_new_entries`` answer stops the unit's entries. A position-scope brake
acts on one position, so it never refuses a new entry."""


def refuses_entries(row: ControlRow, *, shadowed: bool) -> bool:
    """Whether a row that fired refuses this step's entries.

    Only a live ``no_new_entries`` row at unit or account scope refuses. A shadowed row never
    refuses, and neither does a position-scope row. This is the whole rule, kept here so the unit
    and any later reader decide it the same way.
    """
    return not shadowed and row.verb is Verb.NO_NEW_ENTRIES and row.scope in ENTRY_SCOPES


def gate_open(row: ControlRow, facts: dict[str, object]) -> bool:
    """Whether the row's ``enabled`` gate lets it run: a bool, or the fact it names is true."""
    if isinstance(row.enabled, bool):
        return row.enabled
    return bool(facts.get(row.enabled))
