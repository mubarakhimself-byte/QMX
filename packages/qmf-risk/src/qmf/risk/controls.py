"""A brake as a control row: what it reads, where it acts, what it does when it fires (AD-12).

A control row is the seat a halt binding lands in. The row is data. ``scope`` says where it acts;
``reads`` names the facts its block reads, derived from the block's face at compile; ``verb`` is
what the unit runs when the block fires; ``on_fire`` is what the fire does beside the verb;
``restore`` says how the row comes back; ``until_n`` is what it does before it has data; and
``shadow`` keeps a row that records a fire without running it.

The runner lives in ``qml.protocol.controls``. This module holds the types and the one pure rule
that decides whether a fired row refuses an entry, so a host or the fold reads a row without
importing ``qml`` (AD-21). It imports nothing from ``qml`` and nothing from a host.

It also holds the words a brake leaves behind and the shape the fold answers them in (``StateWord``,
``RiskState``), for the same reason: an agent, a card or a host reads a unit's state without
importing the library that derived it. The cushion ledger's shape (``Cushion`` and its
``Clock``) is here for the same reason, and ``gate_open`` reads the switch of any row.

``Verb`` has four words. ``no_new_entries`` is the one this build runs: a brake stops entries and
nothing else, so it can never reach an exit. ``reduce`` and ``flatten`` are stated and refused at
compile until their executor lands, and ``none`` fires without refusing anything.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Final, Protocol

from qmf.core.chrono import Instant

__all__ = [
    "ENTRY_SCOPES",
    "Answer",
    "Clock",
    "ColdRule",
    "ControlRow",
    "Cushion",
    "OnFire",
    "Restore",
    "RiskState",
    "StateWord",
    "Switched",
    "Verb",
    "anchor_id",
    "gate_open",
    "refuses_entries",
    "word_for",
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


class StateWord(StrEnum):
    """What a scope is doing, as the fold reads it from rows (AD-12, AD-18).

    ``RESTORE`` is a word and not only a row: a scope that was released says so, so a reader can
    tell "never fired" from "fired and came back". ``UNKNOWN`` is the fold refusing to answer for a
    state it cannot see: a fact it needs is past its limit.
    """

    ACTIVE = "ACTIVE"
    REDUCING = "REDUCING"
    BENCHED = "BENCHED"
    HALTED = "HALTED"
    RESTORE = "RESTORE"
    UNKNOWN = "UNKNOWN"


_WORDS: Final[Mapping[Verb, StateWord]] = {
    Verb.NONE: StateWord.ACTIVE,
    Verb.NO_NEW_ENTRIES: StateWord.BENCHED,
    Verb.REDUCE: StateWord.REDUCING,
    Verb.FLATTEN: StateWord.HALTED,
}
"""The word each verb leaves behind. ``none`` fired without refusing anything, so the scope is
still ``ACTIVE``; the plan's other two words are a restore row's and a stale read's."""


def word_for(verb: Verb) -> StateWord:
    """The word a fire of ``verb`` leaves on its scope."""
    return _WORDS[verb]


@dataclass(frozen=True, slots=True)
class RiskState:
    """One scope's risk state, as ``qml.fold.fold`` derives it from rows and a clock.

    ``since`` is the instant of the row that began ``word``: a fire of a word the scope already had
    keeps the earlier instant, so a brake that fires every bar does not reset the clock.
    ``unknown`` names the facts whose last read is past their limit at ``stamp``; when it is not
    empty the word is ``UNKNOWN``, because the fold will not answer for what it cannot see.
    """

    scope: str
    word: StateWord
    since: Instant | None
    reason: str
    stamp: Instant
    unknown: tuple[str, ...] = ()


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


class Switched(Protocol):
    """Any row with a switch: a control row, a sizing modifier, a later chain link (AD-8)."""

    @property
    def enabled(self) -> bool | str: ...


def gate_open(row: Switched, facts: Mapping[str, object]) -> bool:
    """Whether the row's ``enabled`` gate lets it run: a bool, or the fact it names is true.

    A fact the row names and the surface does not hold reads closed, so a switch bound to a fact
    that has not arrived leaves the row off rather than on.
    """
    if isinstance(row.enabled, bool):
        return row.enabled
    return bool(facts.get(row.enabled))


class Clock(StrEnum):
    """When a cushion's anchor moves: the start of each UTC day, or of each Monday-start week."""

    DAY = "day"
    WEEK = "week"


_NS_PER_DAY: Final[int] = 86_400 * 10**9
_EPOCH_WEEKDAY: Final[int] = 3
"""1 January 1970 was a Thursday, three days after a Monday."""


def anchor_id(clock: Clock, at: Instant) -> int:
    """The anchor ``at`` falls in: a pure function of the clock and the time (AD-18), so settling
    an anchor twice, or after a restart, lands on the same one."""
    day = at.value_ns // _NS_PER_DAY
    if clock is Clock.DAY:
        return day
    return (day + _EPOCH_WEEKDAY) // 7


@dataclass(frozen=True, slots=True)
class Cushion:
    """One scope's ledger since its anchor, in R after costs (AD-11, AD-18).

    ``realised`` is what closed trades made since the anchor; ``peak`` is the highest running total
    since it, zero at the anchor itself. Only closed trades reach it, so open profit never does.
    """

    realised: Decimal = Decimal(0)
    peak: Decimal = Decimal(0)
