"""The exit stack: every per-bar exit runs each bar, in the compiled order, and one answer runs.

A held position is protected by the exits in its unit's ``exit_set``. The stop and the target
answer a level once, at the entry. Every ``exit_action`` in the set runs here, once per closed
bar, on the bar of the quote that closes the position: the bid for a long and the ask for a
short, so a short's stop feels the spread (AD-13, CHECK S15). Each exit reads a
:class:`PositionFacts` and the bar, and answers an ``ExitAction`` with its reason code, or a
``Signal`` that closes the position while it holds.

One bar runs one action. ``close_full`` beats ``close_partial`` beats ``amend_protection``, and
the earlier exit in the compiled order breaks a tie. ``target_position`` is reserved for the
venue-resting target and no host runs it. A partial close and an amendment answer here and run
nothing until RC-67 and RC-68 give them a host.

This module is the exit path whole. It imports no chain, no fold and no readings feed, so no exit
can be refused or held by one (AD-9 "Import test"); ``qml/tests/test_exit_imports.py`` parses its
imports and fails on any that would.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Protocol, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint

from qml.blocks.api import ExitAction, Instance, Signal
from qml.unit.model import Side

__all__ = [
    "SIGNAL_CODE",
    "ExitAnswer",
    "ExitSlot",
    "ExitStack",
    "PositionFacts",
    "PositionSource",
    "answer",
    "chosen",
    "facts_from",
]

SIGNAL_CODE: Final[str] = "time-exit"
"""The code a per-bar exit's bare ``Signal`` carries: the shipped time exit's own word, which its
closes have carried since the socket had one, so a block that wants another word answers an
``ExitAction`` with its reason code."""

_RANK: Final[Mapping[str, int]] = MappingProxyType(
    {
        "close_full": 0,
        "close_partial": 1,
        "amend_protection": 2,
        "target_position": 3,
    }
)
"""What beats what on one bar. ``target_position`` is reserved for the venue-resting target: it
may answer, it ranks last, and no host runs it, so alone it mints nothing."""

_RESTING: Final[Mapping[str, Decimal]] = MappingProxyType({})


class PositionSource(Protocol):
    """What a host's ``own_position`` answers when it is not already a ``PositionFacts``: the
    identity of the position, as ``OwnPosition`` holds it."""

    @property
    def position_id(self) -> str: ...

    @property
    def side(self) -> Side: ...

    @property
    def quantity(self) -> Decimal: ...

    @property
    def entry_price(self) -> Decimal: ...

    @property
    def opened_by(self) -> Fingerprint: ...


@dataclass(frozen=True, slots=True)
class PositionFacts:
    """The facts one exit reads about the position it protects (SPINE section 3, "Exits").

    It widens an ``OwnPosition`` with what the handler holds: the live stop and the targets, the
    bars held, the excursions in R of the entry's stop, the stage the position was opened under,
    and the numbers in force when it opened. A host that keeps none of those answers its
    ``OwnPosition`` and the rest rest at zero here.
    """

    position_id: str
    side: Side
    quantity: Decimal
    entry_price: Decimal
    opened_by: Fingerprint
    stop: Decimal | None = None
    targets: tuple[Decimal, ...] = ()
    bars_held: int = 0
    mfe_r: Decimal = Decimal(0)
    mae_r: Decimal = Decimal(0)
    stage: str = ""
    numbers_at_entry: Mapping[str, Decimal] = _RESTING

    def evidence(
        self,
        clock: Instant,
        series: Mapping[str, Decimal],
        params: Mapping[str, Decimal],
    ) -> dict[str, object]:
        """One exit's evidence this bar: every fact by its own name, the closing side's bar under
        ``series``, that bar's close under ``clock``, and the exit's own parameters."""
        facts: dict[str, object] = {
            "position_id": self.position_id,
            "side": self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "opened_by": self.opened_by.value,
            "stop": self.stop,
            "targets": self.targets,
            "bars_held": self.bars_held,
            "mfe_r": self.mfe_r,
            "mae_r": self.mae_r,
            "stage": self.stage,
            "numbers_at_entry": self.numbers_at_entry,
            "series": series,
            "clock": clock,
        }
        return facts | dict(params)


@dataclass(frozen=True, slots=True)
class ExitSlot:
    """One per-bar exit in the stack: its binding key, its pin, and its running instance."""

    key: str
    pin: str
    instance: Instance


@dataclass(frozen=True, slots=True)
class ExitAnswer:
    """One exit's answer on one bar, with the exit that gave it and the words its close row
    carries."""

    pin: str
    key: str
    action: ExitAction
    detail: str


class ExitStack:
    """Every per-bar exit one position runs, in the compiled order, as one instance.

    The unit keeps one per held position. Its state is a table keyed by each exit's binding, so a
    restart carries every exit's own state across without knowing which blocks those are.
    """

    def __init__(self, side: Side, slots: Sequence[ExitSlot]) -> None:
        self.side = side
        self.slots = tuple(slots)
        self._instances = MappingProxyType({slot.key: slot.instance for slot in self.slots})

    def instance(self, key: str) -> Instance:
        return self._instances[key]

    def export_state(self) -> Mapping[str, object]:
        return {slot.key: dict(slot.instance.export_state()) for slot in self.slots}

    def import_state(self, state: Mapping[str, object]) -> None:
        for slot in self.slots:
            saved = state.get(slot.key)
            if isinstance(saved, Mapping):
                slot.instance.import_state(cast("Mapping[str, object]", saved))


def facts_from(position: PositionSource | PositionFacts) -> PositionFacts:
    """The facts an exit reads, from what the host answers: a ``PositionFacts`` whole, or the
    identity of a position from a host that does not track its protection yet."""
    if isinstance(position, PositionFacts):
        return position
    return PositionFacts(
        position_id=position.position_id,
        side=position.side,
        quantity=position.quantity,
        entry_price=position.entry_price,
        opened_by=position.opened_by,
    )


def answer(pin: str, raw: object) -> ExitAction | None:
    """What one exit's answer means this bar.

    An ``ExitAction`` is its own answer, and its kind and reason code must be ones the unit can
    read: a kind no host knows, or a close with no reason, raises, so that exit is this bar's
    ``Fault`` and the next exit still runs. A holding ``Signal`` is a full close under
    :data:`SIGNAL_CODE`. A level, a quiet ``Signal`` and ``None`` are no action.
    """
    if isinstance(raw, ExitAction):
        if raw.kind not in _RANK:
            raise ValueError(f"{pin} answers {raw.kind!r}, which is no exit action")
        if not raw.reason_code:
            raise ValueError(f"{pin} answers {raw.kind} with no reason code")
        return raw
    if isinstance(raw, Signal) and raw.state:
        return ExitAction(kind="close_full", reason_code=SIGNAL_CODE)
    return None


def chosen(answers: Sequence[ExitAnswer]) -> ExitAnswer | None:
    """The one answer this bar runs: full beats partial beats amend, and the earlier exit wins a
    tie, which ``min`` gives by keeping the first of equal ranks."""
    return min(answers, key=lambda one: _RANK[one.action.kind], default=None)
