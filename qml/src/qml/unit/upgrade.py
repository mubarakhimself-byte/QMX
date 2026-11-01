"""Every stored shape QML wrote still loads (UT-19, AD-119).

Each schema family names its current version and one upgrader per older version, from ``n``
to ``n + 1``. ``upgrade`` walks a stored document up to the current version, and refuses by
name a family it does not know or a version newer than this QML reads. A family whose
upgraders do not cover every older version fails at import, so a new version cannot ship
without its upgrader. A hosted unit's state snapshot is not here: a snapshot of another state
schema restores cold (UT-09).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qmf.core.refusal import Ok, Result

from qml._refuse import invalid, unsupported
from qml.blocks.api import ENTRY_SCHEMA
from qml.check.layer_g import BEHAVIOUR_SCHEMA
from qml.check.result import CHECK_SCHEMA
from qml.unit.model import Marker

__all__ = ["FAMILIES", "Family", "Upgrader", "upgrade"]

Upgrader = Callable[[dict[str, object]], dict[str, object]]
"""Takes a document at version ``n`` and returns it at version ``n + 1``."""

_MARKER: Final = re.compile(r"^(?P<family>[a-z][a-z.]*)/(?P<version>[1-9][0-9]*)$")


@dataclass(frozen=True, slots=True)
class Family:
    name: str
    current: int
    steps: Mapping[int, Upgrader]


def _family(marker: str, steps: Mapping[int, Upgrader] | None = None) -> Family:
    found = _MARKER.fullmatch(marker)
    if found is None:
        raise ValueError(f"{marker!r} is not a family/version marker")
    name, current = found["family"], int(found["version"])
    given = dict(steps or {})
    if set(given) != set(range(1, current)):
        raise ValueError(f"{name}/{current} needs an upgrader from each of 1 to {current - 1}")
    return Family(name, current, MappingProxyType(given))


FAMILIES: Final[Mapping[str, Family]] = MappingProxyType(
    {
        family.name: family
        for family in (
            _family(Marker.UNIT_1.value),
            _family(ENTRY_SCHEMA),
            _family(CHECK_SCHEMA),
            _family(BEHAVIOUR_SCHEMA),
        )
    }
)


def upgrade(document: object) -> Result[dict[str, object]]:
    """``document`` at its family's current version, or a refusal that names why not."""
    if not isinstance(document, Mapping):
        return invalid("document", "a stored document is a JSON object")
    body = dict(cast("Mapping[str, object]", document))
    marker = body.get("schema")
    found = _MARKER.fullmatch(marker) if isinstance(marker, str) else None
    if found is None:
        return invalid("schema", "a stored document names its schema as family/version")
    family = FAMILIES.get(found["family"])
    if family is None:
        return unsupported(
            "schema", f"{marker} is not a family this QML reads", known=tuple(sorted(FAMILIES))
        )
    version = int(found["version"])
    if version > family.current:
        return unsupported(
            "schema",
            f"{marker} is newer than this QML reads ({family.name}/{family.current}); update QML",
        )
    while version < family.current:
        body = family.steps[version](body)
        version += 1
        body["schema"] = f"{family.name}/{version}"
    return Ok(body)
