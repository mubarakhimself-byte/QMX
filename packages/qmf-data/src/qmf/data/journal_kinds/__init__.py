"""The typed journal kinds, one table keyed by stream and kind (AD-208).

A new kind is one :class:`KindSpec` row here; a kind is added, never redefined.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from qmf.data.journal_envelope import JournalStream
from qmf.data.journal_kinds import node, unit
from qmf.data.journal_kinds.spec import IdRule, KindSpec
from qmf.data.journal_kinds.unit import REASON_CODES

__all__ = ["KINDS", "REASON_CODES", "IdRule", "KindSpec", "kinds_of", "spec_for"]

KINDS: Final[Mapping[tuple[JournalStream, str], KindSpec]] = MappingProxyType(
    {(spec.stream, spec.kind): spec for spec in (*unit.SPECS, *node.SPECS)}
)


def spec_for(stream: JournalStream, kind: str) -> KindSpec | None:
    """The kind's declaration, or None when the stream has no such kind."""
    return KINDS.get((stream, kind))


def kinds_of(stream: JournalStream) -> tuple[KindSpec, ...]:
    """Every kind a stream holds, in declaration order."""
    return tuple(spec for (owner, _kind), spec in KINDS.items() if owner is stream)
