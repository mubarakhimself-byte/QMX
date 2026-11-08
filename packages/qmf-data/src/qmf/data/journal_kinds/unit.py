"""The unit journal's kinds (AD-208; ``journals.md`` §3).

``signal``, ``calibration``, ``state`` and ``lifecycle`` carry Part A's shapes: the decision
row, the calibration row, the runtime state events and the ``qmx.lifecycle/1`` move. The
other kinds' bodies are settled by the slices that write them; until then the writer checks
only the fields their record id needs.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qmf.data.journal_envelope import JournalStream
from qmf.data.journal_kinds.spec import IdRule, KindSpec, missing, one_of

__all__ = [
    "BY_KINDS",
    "LIFECYCLE_SCHEMA",
    "LIFECYCLE_STATES",
    "READING_SOURCES",
    "REASON_CODES",
    "SIGNAL_OUTCOMES",
    "SPECS",
    "STATE_EVENTS",
]

SIGNAL_OUTCOMES: Final[frozenset[str]] = frozenset(
    {
        # Part A's decision outcomes.
        "taken",
        "skipped",
        "no_signal",
        "suppressed_warming",
        "suppressed_limit",
        "dropped_opposite",
        # Part B's: CT-13's door outcomes and a guard's block.
        "blocked",
        "suppressed",
        "refused_by_door",
    }
)
REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "no_signal",
        "outside_session",
        "market_shut",
        "spread_wide",
        "feed_stale",
        "clock_band",
        "max_positions",
        "cross_unit_hook",
        "kill_switch",
        "halt_slot",
        "below_min_lot",
        "margin",
        "warming_up",
        "data_gap",
        "reading_absent",
        "close_only",
        "spec_change_pause",
        "risk_stop",
        "health_stop",
        "placeholder_refusal_never",
    }
)
"""Why a decision was ``skipped`` or ``blocked``. Closed and appendable: add, never redefine."""
READING_SOURCES: Final[frozenset[str]] = frozenset({"unit", "node", "mis"})
STATE_EVENTS: Final[frozenset[str]] = frozenset({"warming", "ready", "cold_start", "seam_flag"})
LIFECYCLE_SCHEMA: Final[str] = "qmx.lifecycle/1"
LIFECYCLE_STATES: Final[frozenset[str]] = frozenset(
    {"draft", "tested", "parked", "paper", "live", "stopped", "retired"}
)
BY_KINDS: Final[frozenset[str]] = frozenset({"judge", "his_click", "risk_rule", "system"})
_NEEDS_REASON: Final[frozenset[str]] = frozenset({"skipped", "blocked"})


def _signal(body: Mapping[str, object]) -> str | None:
    wrong = one_of(body, "outcome", SIGNAL_OUTCOMES)
    if wrong is not None:
        return wrong
    if body["outcome"] in _NEEDS_REASON:
        wrong = one_of(body, "reason", REASON_CODES)
        if wrong is not None:
            return wrong
    readings = body.get("readings_used", [])
    if not isinstance(readings, list):
        return "readings_used is a list"
    for reading in cast("list[object]", readings):
        if not isinstance(reading, Mapping):
            return "each reading used is an object"
        entry = cast("Mapping[str, object]", reading)
        wrong = missing(entry, ("reading", "version", "value", "source")) or one_of(
            entry, "source", READING_SOURCES
        )
        if wrong is not None:
            return f"a reading used: {wrong}"
    return None


def _state(body: Mapping[str, object]) -> str | None:
    wrong = one_of(body, "event", STATE_EVENTS)
    if wrong is not None:
        return wrong
    match body["event"]:
        case "cold_start":
            return missing(body, ("reason",))
        case "seam_flag":
            return missing(body, ("stream", "jump"))
        case _:
            return None


def _lifecycle(body: Mapping[str, object]) -> str | None:
    if body.get("schema") != LIFECYCLE_SCHEMA:
        return f"schema is {LIFECYCLE_SCHEMA}"
    wrong = one_of(body, "from", LIFECYCLE_STATES) or one_of(body, "to", LIFECYCLE_STATES)
    if wrong is not None:
        return wrong
    by = body.get("by")
    if not isinstance(by, Mapping):
        return "by is an object with kind and principal"
    actor = cast("Mapping[str, object]", by)
    return one_of(actor, "kind", BY_KINDS) or missing(actor, ("principal",))


SPECS: Final[tuple[KindSpec, ...]] = (
    KindSpec(
        JournalStream.UNIT,
        "signal",
        IdRule.ROW_ID,
        ("row_id", "instant", "outcome"),
        _signal,
    ),
    KindSpec(
        JournalStream.UNIT,
        "calibration",
        IdRule.ROW_ID,
        ("row_id", "number", "old", "new", "rule", "read_trades", "statistic", "watermark"),
    ),
    KindSpec(
        JournalStream.UNIT,
        "state",
        IdRule.STATE,
        ("event", "scope_id", "instant", "ordinal"),
        _state,
    ),
    KindSpec(
        JournalStream.UNIT,
        "lifecycle",
        IdRule.EVENT_ID,
        (
            "schema",
            "event_id",
            "unit_id",
            "version_ref",
            "compiled_fingerprint",
            "market_id",
            "from",
            "to",
            "by",
            "reason",
            "at",
        ),
        _lifecycle,
    ),
    KindSpec(JournalStream.UNIT, "order", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "fill", IdRule.FILL, ("deal_id",)),
    KindSpec(JournalStream.UNIT, "trade", IdRule.TRADE, ("closing_deal_id",)),
    KindSpec(JournalStream.UNIT, "guard", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "risk_event", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "would_have", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "data_event", IdRule.SEQUENCE),
)
