"""New version or new unit, decided by one table (Part A AD-115, Level 0 AD-23)."""

from __future__ import annotations

from qml.identity.diff import Classification, Edit, classify, diff
from qml.identity.table import (
    EditLabel,
    IdentityRow,
    IdentityTable,
    IdentityTableError,
    Result,
    parse_table,
)

__all__ = [
    "Classification",
    "Edit",
    "EditLabel",
    "IdentityRow",
    "IdentityTable",
    "IdentityTableError",
    "Result",
    "classify",
    "diff",
    "parse_table",
]
