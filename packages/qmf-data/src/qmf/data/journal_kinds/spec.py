"""What one journal kind declares: its body's schema, its version and its record-id rule."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from qmf.data.journal_envelope import JournalStream

__all__ = ["BodyCheck", "IdRule", "KindSpec", "missing", "one_of"]

BodyCheck = Callable[[Mapping[str, object]], str | None]
"""Returns what is wrong with a body, or None."""


class IdRule(StrEnum):
    """How a kind's record id is made, so a re-run writes the same row under the same id.

    Rows that read the machine's state at the time keep sequence ids, because a natural id
    would refuse a true second reading.
    """

    ROW_ID = "row_id"
    """Part A's ``row_id`` in the body (fp1 over scope id, instant and ordinal)."""
    STATE = "state"
    """fp1 over the body's ``scope_id``, ``instant`` and ``ordinal``."""
    EVENT_ID = "event_id"
    """The lifecycle move's ``event_id``."""
    FILL = "fill"
    """``<venue>:<deal_id>``."""
    TRADE = "trade"
    """``<venue>:<closing_deal_id>``."""
    SEQUENCE = "sequence"
    """``<writer_id>/<seq>``."""


@dataclass(frozen=True, slots=True)
class KindSpec:
    """One kind ``qmx.journal.<stream>.<kind>/<version>``. A kind is added, never redefined."""

    stream: JournalStream
    kind: str
    id_rule: IdRule
    required: tuple[str, ...] = ()
    check: BodyCheck | None = None
    schema_version: int = 1

    @property
    def schema(self) -> str:
        return f"qmx.journal.{self.stream.value}.{self.kind}/{self.schema_version}"

    def problem(self, body: Mapping[str, object]) -> str | None:
        """What is wrong with ``body`` for this kind, or None when it is well formed."""
        absent = missing(body, self.required)
        if absent is not None:
            return absent
        return None if self.check is None else self.check(body)


def missing(body: Mapping[str, object], fields: tuple[str, ...]) -> str | None:
    absent = [name for name in fields if body.get(name) is None]
    return f"the body lacks {', '.join(absent)}" if absent else None


def one_of(body: Mapping[str, object], field: str, allowed: frozenset[str]) -> str | None:
    value = body.get(field)
    if value not in allowed:
        return f"{field} is one of {', '.join(sorted(allowed))}, not {value!r}"
    return None
