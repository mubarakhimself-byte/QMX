"""`service.registry()`: the AD-5 node palette the Lab's Graph mode binds to (SOLUTION-DESIGN
13)."""

from __future__ import annotations

from qmx_engine.definition.registry import NOTE, REGISTRY, Kind, Registry
from qmx_engine.ports.library import JsonObject


def palette(registry: Registry = REGISTRY) -> list[JsonObject]:
    def row(kind: Kind) -> JsonObject:
        return {
            "type": kind.name,
            "inputs": list(kind.inputs),
            "outputs": list(kind.outputs),
            "effect": kind.effect,
            "role": kind.role.value,
            "available": kind.available,
            "model_bearing": kind.model_bearing,
        }

    return [row(kind) for kind in (*registry.kinds.values(), NOTE)]
