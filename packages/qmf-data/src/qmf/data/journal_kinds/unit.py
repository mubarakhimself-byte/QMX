"""The unit journal's kinds (AD-208; ``journals.md`` §3).

``signal``, ``calibration``, ``state`` and ``lifecycle`` carry Part A's shapes: the decision
row, the calibration row, the runtime state events and the ``qmx.lifecycle/1`` move. The
other kinds' bodies are settled by the slices that write them; until then the writer checks
only the fields their record id needs.
"""

from __future__ import annotations

import re
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
        "placeholder_refusal_never",  # mock-data-scan: allow (refusal kind, domain word)
        # A hosted unit's own skips, which QML words as text (B9).
        "no_entry_order",
        "stop_wrong_side",
        "above_max_lot",
        "sizer_skip",
        # The node's placement read: a fresh board reads the market in a word it does not favour.
        "not_favoured",
        # A live journal's text with no code yet, so a new word costs a label and not the journal.
        "unlisted",
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
_RATIONAL: Final[re.Pattern[str]] = re.compile(r"\A-?\d+/\d+\Z")
"""An exact rational as text: a rate reads ``1/1`` or ``1/150``, never a rounded decimal."""


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
    return _receipt(body)


def _receipt(body: Mapping[str, object]) -> str | None:
    """The decision row's size trail, where the row carries one: the sizer that answered, the
    facts it read, the positions of the size, each link's verdict and the two fingerprints.
    Each field is checked only when it is there, so a row from before the receipt stays
    readable and a row that carries it is typed."""
    for name in ("binding", "logic_fp", "risk_fp"):
        value = body.get(name)
        if value is not None and not isinstance(value, str):
            return f"{name} is a string"
    written = body.get("written_before_send")
    if written is not None and not isinstance(written, bool):
        return "written_before_send is true or false"
    for name in ("verdicts", "placeholders"):
        words = body.get(name)
        if words is not None and (
            not isinstance(words, list)
            or not all(isinstance(word, str) for word in cast("list[object]", words))
        ):
            return f"{name} is a list of words"
    inputs = body.get("inputs")
    if inputs is not None and not isinstance(inputs, Mapping):
        return "inputs is an object of the facts the size read"
    steps = body.get("steps")
    if steps is not None:
        if not isinstance(steps, Mapping):
            return "steps is an object of the positions of the size"
        for name, step in cast("Mapping[object, object]", steps).items():
            if not isinstance(step, Mapping):
                return f"the step {name} is an object of kind, value and basis"
            wrong = missing(cast("Mapping[str, object]", step), ("kind", "value", "basis"))
            if wrong is not None:
                return f"the step {name}: {wrong}"
    return None


def _trade(body: Mapping[str, object]) -> str | None:
    """A close's two rate stamps, where it carries them: the account-currency rate its money
    converts by, exact as ``n/d``, and how old that read was in seconds."""
    rate = body.get("rate")
    if rate is not None and (not isinstance(rate, str) or _RATIONAL.fullmatch(rate) is None):
        return "rate is an exact rational, n/d"
    age = body.get("rate_age_s")
    if age is not None and not isinstance(age, str):
        return "rate_age_s is a decimal string"
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
    KindSpec(JournalStream.UNIT, "trade", IdRule.TRADE, ("closing_deal_id",), _trade),
    KindSpec(JournalStream.UNIT, "guard", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "risk_event", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "would_have", IdRule.SEQUENCE),
    KindSpec(JournalStream.UNIT, "data_event", IdRule.SEQUENCE),
    # A replay's swap, financing, funding, dividend or commission line (B10, QB-04, QB-03).
    KindSpec(JournalStream.UNIT, "cash", IdRule.FILL, ("deal_id", "kind", "money")),
)
