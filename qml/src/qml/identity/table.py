"""The identity table ``units.identity_table`` as data (Part A AD-115, CONTRACTS.md section 7).

QML imports no host, so the table arrives as the setting's rows and is parsed here, once, at
the boundary. A row maps one edit label to its result, whether the edit is a counted try and
whether his click is needed before live.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, cast

__all__ = [
    "EditLabel",
    "IdentityRow",
    "IdentityTable",
    "IdentityTableError",
    "Result",
    "parse_table",
]


class EditLabel(StrEnum):
    MOTION_INSIDE_RANGE = "motion_inside_range"
    LEARNED_RETRAIN_IN_BOUNDS = "learned_retrain_in_bounds"
    LEARNED_RETRAIN_OUT_OF_BOUNDS = "learned_retrain_out_of_bounds"
    RANGE_CHANGE = "range_change"
    MOTION_RULE_CHANGE = "motion_rule_change"
    CADENCE_CHANGE = "cadence_change"
    FIXED_VALUE_CHANGE = "fixed_value_change"
    BAR_CHANGE = "bar_change"
    SESSION_CHANGE = "session_change"
    MARKETS_CHANGE = "markets_change"
    MARKET_SETTINGS_ADOPTED = "market_settings_adopted"
    BLOCK_FIX = "block_fix"
    BLOCK_SWAP = "block_swap"
    ROLE_ADDED = "role_added"
    ROLE_REMOVED = "role_removed"
    COMBINER_CHANGE = "combiner_change"
    TRANSPLANT = "transplant"
    MARKET_LOGIC_CHANGE = "market_logic_change"
    REWRITE = "rewrite"
    AMBIGUITY_RESOLVED = "ambiguity_resolved"
    TITLE_CHANGE = "title_change"
    STRUCTURE_CHANGE = "structure_change"
    """Any other edit to what the unit does. Its default row is a new unit, so an edit the
    other labels do not name is never waved through as a calibration."""


class Result(StrEnum):
    """Ordered lowest to highest; the highest result of an edit's labels wins."""

    NONE = "none"
    CALIBRATION_ROW = "calibration_row"
    NEW_VERSION = "new_version"
    NEW_UNIT = "new_unit"

    @property
    def rank(self) -> int:
        return _RANKS.index(self)


_RANKS: Final = tuple(Result)


@dataclass(frozen=True)
class IdentityRow:
    label: EditLabel
    result: Result
    counted_try: bool
    click_before_live: bool


UNLISTED: Final = IdentityRow(EditLabel.STRUCTURE_CHANGE, Result.NEW_UNIT, True, True)
"""What a label with no row in his table counts as: the strictest answer."""


@dataclass(frozen=True)
class IdentityTable:
    rows: Mapping[EditLabel, IdentityRow]

    def row(self, label: EditLabel) -> IdentityRow | None:
        return self.rows.get(label)


class IdentityTableError(ValueError):
    """The setting's rows are not a table QML can read; the message names the row."""


_FIELDS: Final = ("label", "result", "counted_try", "click_before_live")


def _row(index: int, raw: object) -> IdentityRow:
    where = f"units.identity_table row {index + 1}"
    if not isinstance(raw, Mapping):
        raise IdentityTableError(f"{where} is not a table")
    found = cast("Mapping[str, object]", raw)
    missing = [name for name in _FIELDS if name not in found]
    extra = sorted(set(found) - set(_FIELDS))
    if missing or extra:
        raise IdentityTableError(f"{where} needs exactly {', '.join(_FIELDS)}")
    label, result = found["label"], found["result"]
    try_flag, click = found["counted_try"], found["click_before_live"]
    if label not in set(EditLabel):
        raise IdentityTableError(f"{where} names label {label!r}, which no edit has")
    if result not in set(Result):
        known = ", ".join(Result)
        raise IdentityTableError(f"{where} has result {result!r}; use one of {known}")
    if not isinstance(try_flag, bool) or not isinstance(click, bool):
        raise IdentityTableError(f"{where}: counted_try and click_before_live are true or false")
    return IdentityRow(EditLabel(cast(str, label)), Result(cast(str, result)), try_flag, click)


def parse_table(rows: object) -> IdentityTable:
    """The setting's rows as a table, or :class:`IdentityTableError` naming the first bad row."""
    if not isinstance(rows, Sequence) or isinstance(rows, str | bytes):
        raise IdentityTableError("units.identity_table is a list of rows")
    parsed: dict[EditLabel, IdentityRow] = {}
    for index, raw in enumerate(cast("Sequence[object]", rows)):
        row = _row(index, raw)
        if row.label in parsed:
            raise IdentityTableError(f"units.identity_table names {row.label!s} twice")
        parsed[row.label] = row
    return IdentityTable(parsed)
