"""K9 8: no agent path to money, by tool table (AD-20, K5; slice 5).

The catalog is the tool table every model-facing call comes from. His click alone promotes a unit
toward paper or live, lowers a kill level, sets the floor, and binds to a plan hash. This test
holds that no row a model may call reaches one of those doors, and that the protected list names
the four fields only his click writes.
"""

from __future__ import annotations

import re

from qmx_control.catalog import OperationSpec, rows
from qmx_host.promote import PROTECTED_FIELDS  # pyright: ignore[reportMissingTypeStubs]

DOORS = frozenset({"promote"}) | PROTECTED_FIELDS
"""What only his click reaches: the promote move and the fields he alone writes (AD-20, K5)."""

_SEPARATORS = re.compile(r"[^a-z0-9]+")
"""A name is read as one string with its underscores kept, not split into words. Splitting turns
`kill_level` into `kill` and `level`, which matches no door and hides the row."""


def _names(row: OperationSpec) -> set[str]:
    """Every name a row carries, lowercased with its underscores kept, so a door cannot hide in
    one."""
    raw = (row.name, row.op, row.target, "" if row.rest is None else row.rest.path)
    return {_SEPARATORS.sub("_", name.casefold()).strip("_") for name in raw}


def test_k9_8_no_agent_path_to_money() -> None:
    found = rows()

    assert any(row.agent for row in found), "no agent row to test: the catalog answered nothing"
    reached = sorted(
        f"{door} in {name}"
        for row in found
        if row.agent
        for name in _names(row)
        for door in DOORS
        if door in name
    )
    assert not reached, f"a tool row reaches {reached}"
    assert frozenset({"floor", "kill_level", "never_self_tune", "plan_hash"}) == PROTECTED_FIELDS
