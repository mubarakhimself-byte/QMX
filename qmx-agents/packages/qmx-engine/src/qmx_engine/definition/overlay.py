"""A variant is an overlay: `extends` names the parent's `workflow_item` and `object_id`, and its
RFC 6902 `add`, `remove` and `replace` patches turn the parent into a full snapshot."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import NamedTuple

from pydantic import JsonValue

from qmx_engine.definition.model import Extends, Patch


class OverlayError(ValueError):
    """A patch that does not apply to the parent."""


class Resolved(NamedTuple):
    snapshot: dict[str, JsonValue]
    variant_of: tuple[str, str]
    """The parent's `(workflow_item, object_id)`, for the publisher's `variant-of` edge."""


def resolve(variant: Mapping[str, JsonValue], parent: Mapping[str, JsonValue]) -> Resolved:
    """The variant keeps its own `schema`, `id` and `name`; everything else is the parent's
    document with the patches applied in order. The snapshot extends nothing."""
    extends = Extends.model_validate(variant.get("extends"))
    snapshot: dict[str, JsonValue] = copy.deepcopy(dict(parent))
    for index, patch in enumerate(extends.patches):
        try:
            apply(snapshot, patch)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise OverlayError(f"patches[{index}] {patch.op} {patch.path}: {error}") from error
    for field in ("schema", "id", "name"):
        if field in variant:
            snapshot[field] = variant[field]
    snapshot["extends"] = None
    return Resolved(snapshot, (extends.workflow_item, extends.object_id))


def pointer(path: str) -> list[str]:
    if not path.startswith("/"):
        raise ValueError("a JSON pointer below the document starts with /")
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


def apply(document: dict[str, JsonValue], patch: Patch) -> None:
    *parents, last = pointer(patch.path)
    container: JsonValue = document
    for part in parents:
        if isinstance(container, list):
            container = container[index(part, len(container))]
        elif isinstance(container, dict):
            container = container[part]
        else:
            raise TypeError("the pointer runs through a scalar")
    value = copy.deepcopy(patch.value)
    if isinstance(container, list):
        if patch.op == "add":
            at = len(container) if last == "-" else index(last, len(container) + 1)
            container.insert(at, value)
        elif patch.op == "remove":
            del container[index(last, len(container))]
        else:
            container[index(last, len(container))] = value
    elif isinstance(container, dict):
        if patch.op != "add" and last not in container:
            raise KeyError(last)
        if patch.op == "remove":
            del container[last]
        else:
            container[last] = value
    else:
        raise TypeError("the pointer runs through a scalar")


def index(part: str, bound: int) -> int:
    if not part.isdigit() or int(part) >= bound:
        raise IndexError(part)
    return int(part)
