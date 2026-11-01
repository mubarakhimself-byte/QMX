"""The role-neutral roles table (Part A AD-104, AD-113).

A role is the job a slot gives the blocks bound in it. An entry lists the roles it can play and
never writes its job into itself; the unit's binding assigns the job. The vocabulary is QML's one
``Role`` enum, so a slot and an entry can never spell a role two ways.
"""

from __future__ import annotations

import difflib
from collections.abc import Mapping
from typing import Final

from qml.unit.model import Role

__all__ = ["NEAREST_SUGGESTIONS", "ROLES", "nearest", "role_problem"]

NEAREST_SUGGESTIONS: Final[int] = 3
"""Starting default of the ``nearest_suggestions`` setting (CONTRACTS.md section 9)."""

ROLES: Final[Mapping[Role, str]] = {
    Role.CONTEXT: "the market state a decision is made in",
    Role.LOCATION: "the price area where a trade may start",
    Role.SETUP: "the pattern that must be in place before a trigger counts",
    Role.TRIGGER: "the event that starts a trade",
    Role.CONFIRMATION: "a second event that must agree with the trigger",
    Role.FILTER: "a condition that must hold for a trade to be allowed",
    Role.VETO: "a condition that stops a trade the others allowed",
    Role.ENTRY_ORDER: "how the entry order is placed",
    Role.INVALIDATION: "what makes the idea wrong before entry",
    Role.REGIME_DETECTOR: "which kind of market this is, trend against range",
    Role.SIZING_MODIFIER: "a change to the size the sizer chose",
    Role.ARMING: "a condition that arms the trigger for a while",
    Role.TIMEOUT: "how long an armed or open idea may wait",
    Role.COOLDOWN: "how long to wait after a trade before the next",
    Role.RE_ENTRY: "when a stopped idea may enter again",
    Role.EXIT: "when and where a trade closes",
    Role.SIZER: "how big a trade is",
    Role.HALT: "when trading stops for a position, a unit or the account",
}


def nearest(word: str, limit: int = NEAREST_SUGGESTIONS) -> tuple[str, ...]:
    """The roles closest in spelling to ``word``, closest first."""
    normal = word.strip().lower().replace("-", "_").replace(" ", "_")
    names = [role.value for role in Role]
    return tuple(difflib.get_close_matches(normal, names, n=limit, cutoff=0.0))


def role_problem(word: object, limit: int = NEAREST_SUGGESTIONS) -> str | None:
    """None for a role in the vocabulary, otherwise the message naming the nearest roles."""
    if isinstance(word, str) and word in {role.value for role in Role}:
        return None
    if not isinstance(word, str):
        return "a role is a word from the roles table"
    return f"{word!r} is not a role; the nearest are {', '.join(nearest(word, limit))}"
