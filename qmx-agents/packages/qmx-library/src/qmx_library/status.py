"""A hypothesis's status, computed at read and never stored (Library AD-23).

A result links to a `hypothesis` with `tests` and says what it shows in its own `outcome` field
(`supports`, `refutes` or `inconclusive`), because an edge is about, never true (AD-4). Results
whose evidence is quarantined or corrected (AD-22) are left out; a superseded input still counts,
since the result stays true of the data it ran on (Claude's default). A result with a
`regime:<name>` tag counts in that regime. Prose that says "supported" with no result behind it
counts for nothing.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Literal

from qmx_library.port import LibraryRefused, ObjectId

if TYPE_CHECKING:
    from qmx_library.principal import Principal
    from qmx_library.store import Store

type Verdict = Literal["supported", "refuted", "open", "mixed"]

IGNORED: Final = frozenset({"quarantined", "corrected"})
REGIME: Final = "regime:"


@dataclass(frozen=True, slots=True)
class Status:
    status: Verdict
    by_regime: Mapping[str, Verdict] = field(default_factory=dict[str, Verdict])
    """Each regime's own status, for results tagged `regime:<name>`."""
    counted: tuple[ObjectId, ...] = ()
    ignored: tuple[ObjectId, ...] = ()
    """Results that test the hypothesis but carry a quarantined or corrected mark."""


def verdict(outcomes: Iterable[str]) -> Verdict:
    found = set(outcomes)
    if {"supports", "refutes"} <= found:
        return "mixed"
    if "supports" in found:
        return "supported"
    if "refutes" in found:
        return "refuted"
    return "open"


def status(store: Store, who: Principal, hypothesis: str) -> Status:
    """The status of the `hypothesis` item from the results that test any of its objects."""
    objects = [object_id for object_id, _ in store.placed(hypothesis, "hypothesis", None)]
    if not objects:
        raise LibraryRefused("not_found", f"no hypothesis {hypothesis}")
    steps = store.walk(who, objects, ["tests"], "in", depth=1)
    outcomes: list[str] = []
    regimes: defaultdict[str, list[str]] = defaultdict(list)
    counted: list[ObjectId] = []
    ignored: list[ObjectId] = []
    for step in steps:
        view = store.get(who, step.object_id)
        outcome = view.fields.get("outcome")
        if not isinstance(outcome, str):
            continue
        if store.marks(who, view.object_id).worst in IGNORED:
            ignored.append(view.object_id)
            continue
        counted.append(view.object_id)
        outcomes.append(outcome)
        tags = view.annotations.get("tags")
        for tag in tags if isinstance(tags, list) else []:
            if isinstance(tag, str) and tag.startswith(REGIME):
                regimes[tag.removeprefix(REGIME)].append(outcome)
    by_regime: dict[str, Verdict] = {n: verdict(found) for n, found in sorted(regimes.items())}
    return Status(verdict(outcomes), by_regime, tuple(counted), tuple(ignored))
