"""The node journal's, the market journal's and reading history's kinds (AD-208).

Part C owns most of these bodies and may add kinds; none is redefined. The writer checks
``node_lifecycle``'s event and the reading body's ``source``, so a node's and the MIS app's
readings never share a partition.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from qmf.data.journal_envelope import JournalStream
from qmf.data.journal_kinds.spec import IdRule, KindSpec, one_of

__all__ = ["NODE_EVENTS", "READING_ORIGINS", "SPECS"]

NODE_EVENTS: Final[frozenset[str]] = frozenset({"start", "stop"})
READING_ORIGINS: Final[frozenset[str]] = frozenset({"node", "mis"})


def _node_lifecycle(body: Mapping[str, object]) -> str | None:
    return one_of(body, "event", NODE_EVENTS)


def _reading(body: Mapping[str, object]) -> str | None:
    return one_of(body, "source", READING_ORIGINS)


_NODE_KINDS: Final[tuple[str, ...]] = (
    "passport",
    "reconcile",
    "kill_level",
    "clock_band",
    "feed_health",
    "disk_guard",
    "gap",
    "stand_down",
    "spec_change",
)

SPECS: Final[tuple[KindSpec, ...]] = (
    KindSpec(JournalStream.NODE, "node_lifecycle", IdRule.SEQUENCE, ("event",), _node_lifecycle),
    *(KindSpec(JournalStream.NODE, kind, IdRule.SEQUENCE) for kind in _NODE_KINDS),
    KindSpec(JournalStream.MARKET, "minute", IdRule.SEQUENCE),
    KindSpec(JournalStream.MARKET, "offset", IdRule.SEQUENCE),
    KindSpec(JournalStream.READINGS, "reading", IdRule.SEQUENCE, ("source",), _reading),
)
