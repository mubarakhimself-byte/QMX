"""The edge maps that fan a node out into partitions (AD-5): `broadcast`, `chunk`, `zip`,
`keyed-join` and `cartesian` (explicit only, which validation enforces). A `one` edge never fans
out: `core.ready` adds its value to every partition, or runs the target once per partition of a
source that fanned out.

`fan` takes the fanning edges into one node with the list each carried and returns one `Part` per
partition, in partition-id order: its inputs by port and the plan recorded on `node_scheduled`.
A node takes one kind of fanning map; `broadcast` and `chunk` take one edge, the others one or more.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Final, NamedTuple

from pydantic import JsonValue
from qmx_ledger.journal import encoded

from qmx_engine.core.partitions import chunks
from qmx_engine.core.state import JsonObject
from qmx_engine.definition.model import Target

type Lists = list[tuple[Target, list[JsonValue]]]


class FanError(ValueError):
    """The edges cannot be fanned: mixed maps, a value that is not a list, unequal zip lengths, a
    duplicate key."""


class Part(NamedTuple):
    inputs: JsonObject
    plan: JsonObject


def _broadcast(lists: Lists, _: Mapping[str, JsonValue]) -> list[Part]:
    ((target, items),) = lists
    return [Part({target.port: item}, {"item": i}) for i, item in enumerate(items)]


def _chunk(lists: Lists, settings: Mapping[str, JsonValue]) -> list[Part]:
    ((target, items),) = lists
    spec = target.chunk
    if spec is None:
        raise FanError("a chunk edge needs chunk: {by, ...}")
    return [
        Part(
            {target.port: items[span.start : span.end]},
            {"chunk": {"by": spec.by, "items": [span.start, span.end], "tokens": span.tokens}},
        )
        for span in chunks(items, spec, settings)
    ]


def _ports(lists: Lists, values: Sequence[JsonValue]) -> JsonObject:
    """One value per edge, by target port; edges into one port give a list in edge order."""
    found: dict[str, list[JsonValue]] = {}
    for (target, _), value in zip(lists, values, strict=True):
        found.setdefault(target.port, []).append(value)
    return {port: group[0] if len(group) == 1 else group for port, group in found.items()}


def _zip(lists: Lists, _: Mapping[str, JsonValue]) -> list[Part]:
    lengths = {len(items) for _, items in lists}
    if len(lengths) > 1:
        raise FanError(f"zip edges carry lists of unequal lengths {sorted(lengths)}")
    return [
        Part(_ports(lists, [items[i] for _, items in lists]), {"item": i})
        for i in range(lengths.pop())
    ]


def _cartesian(lists: Lists, _: Mapping[str, JsonValue]) -> list[Part]:
    combos: list[list[int]] = [[]]
    for _target, items in lists:
        combos = [[*combo, i] for combo in combos for i in range(len(items))]
    return [
        Part(
            _ports(lists, [items[i] for (_, items), i in zip(lists, combo, strict=True)]),
            {"items": list[JsonValue](combo)},
        )
        for combo in combos
    ]


def _keyed(lists: Lists, _: Mapping[str, JsonValue]) -> list[Part]:
    """Keys sort by their canonical JSON, which the plan records."""
    by_edge: list[dict[bytes, JsonValue]] = []
    for target, items in lists:
        key = target.key or ""
        found: dict[bytes, JsonValue] = {}
        for item in items:
            if not isinstance(item, dict) or key not in item:
                raise FanError(f"an item on port {target.port!r} has no key {key!r}")
            name = encoded(item[key])
            if name in found:
                raise FanError(f"two items on port {target.port!r} share one {key!r}")
            found[name] = item
        by_edge.append(found)
    keys = set[bytes]().union(*by_edge)
    matched = sorted(k for k in keys if all(k in found for found in by_edge))
    unmatched: list[JsonValue] = [k.decode() for k in sorted(keys) if k not in matched]
    return [
        Part(
            _ports(lists, [found[key] for found in by_edge]),
            {"key": key.decode(), "unmatched": unmatched},
        )
        for key in matched
    ]


MAPS: Final[Mapping[str, Callable[[Lists, Mapping[str, JsonValue]], list[Part]]]] = {
    "broadcast": _broadcast,
    "chunk": _chunk,
    "zip": _zip,
    "cartesian": _cartesian,
    "keyed-join": _keyed,
}
SINGLE: Final = frozenset({"broadcast", "chunk"})


def fan(edges: Sequence[tuple[Target, JsonValue]], settings: Mapping[str, JsonValue]) -> list[Part]:
    maps = {target.map for target, _ in edges}
    if len(maps) != 1 or not maps <= MAPS.keys():
        raise FanError(f"a node takes one fanning map, not {sorted(maps)}")
    (kind,) = maps
    if kind in SINGLE and len(edges) != 1:
        raise FanError(f"a node takes one {kind} edge, not {len(edges)}")
    lists: Lists = []
    for target, value in edges:
        if not isinstance(value, list):
            raise FanError(f"the {kind} edge into port {target.port!r} carries no list")
        lists.append((target, value))
    return MAPS[kind](lists, settings)
