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
    "BLOCK_CODE",
    "BLOCK_REASON_FAMILY",
    "BRAKE_CODE",
    "BY_KINDS",
    "LIFECYCLE_SCHEMA",
    "LIFECYCLE_STATES",
    "READING_SOURCES",
    "REASON_CODES",
    "RISK_EVENT_CODES",
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
"""Why a decision was ``skipped`` or ``blocked``. Closed and appendable: add, never redefine.
A user block's own word is not here: it names its code in ``BLOCK_REASON_FAMILY``, so a block a
user adds costs no table row and no journal change."""
BLOCK_REASON_FAMILY: Final[str] = "block:"
"""The head of a user-added block's own reason-code family. A block writes its code as
``block:<its own word>``; the family is declared here once and appends without an edit, so the
closed list above stays the unit's and the hosts' own words."""
BLOCK_CODE: Final[re.Pattern[str]] = re.compile(r"\Ablock:[a-z0-9][a-z0-9._-]*\Z")
BRAKE_CODE: Final[re.Pattern[str]] = re.compile(r"\A[a-z0-9][a-z0-9._-]*\Z")
"""A brake's own word on its risk-event row: its block's entry id, which lands from a document and
so can never be a static list. The form is the family, and the closed codes above are its first
members."""
READING_SOURCES: Final[frozenset[str]] = frozenset({"unit", "node", "mis"})
STATE_EVENTS: Final[frozenset[str]] = frozenset({"warming", "ready", "cold_start", "seam_flag"})
RISK_EVENT_CODES: Final[frozenset[str]] = frozenset({"unit_fault", "link_fault"})
"""What a risk event happened: ``unit_fault`` when a block raised in one of its unit's phases
(AD-23), ``link_fault`` when a chain link or a control row raised and its scope stood down (AD-9).
Closed and appendable; ``qmf-risk`` carries the same family for the code the hosts write. A brake's
own word joins the family by its form (``BRAKE_CODE``) and not by a list, because which brakes run
is a document's."""
LIFECYCLE_SCHEMA: Final[str] = "qmx.lifecycle/1"
LIFECYCLE_STATES: Final[frozenset[str]] = frozenset(
    {"draft", "tested", "parked", "paper", "live", "stopped", "retired"}
)
BY_KINDS: Final[frozenset[str]] = frozenset({"judge", "his_click", "risk_rule", "system"})
_NEEDS_REASON: Final[frozenset[str]] = frozenset({"skipped", "blocked"})
_RATIONAL: Final[re.Pattern[str]] = re.compile(r"\A-?\d+/\d+\Z")
"""An exact rational as text: a rate reads ``1/1`` or ``1/150``, never a rounded decimal."""
_DECIMAL: Final[re.Pattern[str]] = re.compile(r"\A-?\d+(\.\d+)?\Z")


def _reason(body: Mapping[str, object]) -> str | None:
    """The decision's code: one of the closed list, or a user block's own family code."""
    code = body.get("reason")
    if isinstance(code, str) and (code in REASON_CODES or BLOCK_CODE.match(code) is not None):
        return None
    return (
        f"reason is one of {', '.join(sorted(REASON_CODES))}, or a block's own "
        f"{BLOCK_REASON_FAMILY}<word>, not {code!r}"
    )


def _signal(body: Mapping[str, object]) -> str | None:
    wrong = one_of(body, "outcome", SIGNAL_OUTCOMES)
    if wrong is not None:
        return wrong
    if body["outcome"] in _NEEDS_REASON:
        wrong = _reason(body)
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


def _decimals(body: Mapping[str, object], names: tuple[str, ...]) -> str | None:
    """Each named field, where the row carries it, as decimal text."""
    for name in names:
        value = body.get(name)
        if value is not None and (not isinstance(value, str) or _DECIMAL.fullmatch(value) is None):
            return f"{name} is a decimal string"
    return None


def _fill(body: Mapping[str, object]) -> str | None:
    """The fill record (R7), where the row carries it: the decision and arrival quotes, the
    spread and commission the fill paid, and whether the venue filled it only in part."""
    partial = body.get("partial")
    if partial is not None and not isinstance(partial, bool):
        return "partial is true or false"
    return _decimals(body, ("decision_quote", "arrival_quote", "spread", "commission"))


def _trade(body: Mapping[str, object]) -> str | None:
    """A close's two rate stamps, where it carries them: the account-currency rate its money
    converts by, exact as ``n/d``, and how old that read was in seconds. Its ``net_r`` and
    ``cash``, where it carries them, are decimal text beside the gross ``r``."""
    rate = body.get("rate")
    if rate is not None and (not isinstance(rate, str) or _RATIONAL.fullmatch(rate) is None):
        return "rate is an exact rational, n/d"
    age = body.get("rate_age_s")
    if age is not None and not isinstance(age, str):
        return "rate_age_s is a decimal string"
    return _decimals(body, ("net_r", "cash"))


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


def _risk_event(body: Mapping[str, object]) -> str | None:
    """The code that fired, the root cause the one card is filed under, and the alert its reader
    acts on (AD-12, AD-23). ``event_id`` names the incident rather than the row, so a restart that
    writes the same brake's fire again files it under the same incident."""
    wrong = _brake_code(body, "code")
    if wrong is not None:
        return wrong
    root = body["root"]
    if not isinstance(root, str) or not root.strip():
        return "root is a root-cause key, a non-blank string"
    if not isinstance(body.get("event_id"), str) or not body["event_id"]:
        return "event_id is the incident's own non-blank string"
    if not isinstance(body.get("action"), str) or not body["action"]:
        return "action is what its reader does, a non-blank string"
    actionable = body.get("actionable")
    if not isinstance(actionable, bool):
        return "actionable is true or false"
    for name in ("row", "pin", "verb", "detail"):
        value = body.get(name)
        if value is not None and not isinstance(value, str):
            return f"{name} is a string"
    return None


def _brake_code(body: Mapping[str, object], field: str) -> str | None:
    """The closed family: one of the hosts' own words, or a brake's own word by its form."""
    code = body.get(field)
    if isinstance(code, str) and (code in RISK_EVENT_CODES or BRAKE_CODE.match(code) is not None):
        return None
    return (
        f"{field} is one of {', '.join(sorted(RISK_EVENT_CODES))}, or a brake's own word, "
        f"not {code!r}"
    )


def _would_have(body: Mapping[str, object]) -> str | None:
    """The entry a brake would have refused, or did: the row that answered, the decision row it
    refused, the code its words resolve to, and the share of such entries it recorded."""
    wrong = _brake_code(body, "code") or _reason(body)
    if wrong is not None:
        return wrong
    for name in ("row", "decision_row_id"):
        value = body.get(name)
        if not isinstance(value, str) or not value:
            return f"{name} is a non-blank string"
    propensity = body.get("propensity")
    if not isinstance(propensity, str) or _RATIONAL.fullmatch(propensity) is None:
        return "propensity is an exact rational, n/d"
    numerator, _, denominator = propensity.partition("/")
    if int(denominator) == 0 or not 0 < int(numerator) <= int(denominator):
        return "propensity is a share above 0 and at most 1/1"
    for name in ("verb", "detail", "market_id", "side"):
        value = body.get(name)
        if value is not None and not isinstance(value, str):
            return f"{name} is a string"
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
    KindSpec(JournalStream.UNIT, "fill", IdRule.FILL, ("deal_id",), _fill),
    KindSpec(JournalStream.UNIT, "trade", IdRule.TRADE, ("closing_deal_id",), _trade),
    KindSpec(JournalStream.UNIT, "guard", IdRule.SEQUENCE),
    KindSpec(
        JournalStream.UNIT,
        "risk_event",
        IdRule.SEQUENCE,
        ("code", "root", "event_id", "action", "actionable"),
        _risk_event,
    ),
    KindSpec(
        JournalStream.UNIT,
        "would_have",
        IdRule.SEQUENCE,
        ("code", "row", "decision_row_id", "reason", "propensity"),
        _would_have,
    ),
    KindSpec(JournalStream.UNIT, "data_event", IdRule.SEQUENCE),
    # A replay's swap, financing, funding, dividend or commission line (B10, QB-04, QB-03).
    KindSpec(JournalStream.UNIT, "cash", IdRule.FILL, ("deal_id", "kind", "money")),
)
