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


def _words(row: OperationSpec) -> set[str]:
    """Every word of a row's operation, target and REST path, so a door cannot hide in one name."""
    named = [row.op, row.target, "" if row.rest is None else row.rest.path]
    return {word for name in named for word in re.split(r"[^a-z0-9]+", name.casefold()) if word}


def test_k9_8_no_agent_path_to_money() -> None:
    reachable = frozenset(word for row in rows() if row.agent for word in _words(row))

    assert reachable & DOORS == frozenset(), f"a tool row reaches {sorted(reachable & DOORS)}"
    assert frozenset({"floor", "kill_level", "never_self_tune", "plan_hash"}) == PROTECTED_FIELDS
