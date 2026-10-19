"""Effects classed by reversibility (AD-8, SOLUTION-DESIGN 3.4).

A `reversible` attempt writes only into its own overlay (`workers.zones`, AD-51). It is undone by
deleting that overlay, so a retry never touches a sibling attempt's files and no snapshot of the
shared zone is taken.

An `irreversible` attempt receives its idempotency key. After an `unknown` outcome (the engine
died mid-attempt, a timeout or a cancel), `after_unknown` says what happens next: a step that
touched nothing outside the zone reruns, a model call retries once, and any other step never
retries: it waits on a gate that shows its key until someone answers it. The model-call exception
covers a model node only while its definition declares no irreversible effect of its own.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import JsonValue

from qmx_engine.definition.registry import REGISTRY, Effect
from qmx_engine.nodes.base import NodeJob

IRREVERSIBLE: Final = frozenset({"irreversible", "irreversible_external"})

type AfterUnknown = Literal["retry", "inbox"]


def effect_of(definition: dict[str, JsonValue]) -> Effect:
    declared = definition.get("effect")
    if declared in ("none", "reversible", "compensable", "irreversible", "irreversible_external"):
        return declared
    kind = REGISTRY.kind(str(definition.get("type")))
    return "none" if kind is None else kind.effect


def model_bearing(definition: dict[str, JsonValue]) -> bool:
    kind = REGISTRY.kind(str(definition.get("type")))
    return kind is not None and kind.model_bearing


def idempotency_key(job: NodeJob) -> str | None:
    """The key an irreversible attempt passes to the outside world; None for any other effect."""
    return job.idempotency_key if effect_of(job.node_definition) in IRREVERSIBLE else None


def after_unknown(definition: dict[str, JsonValue], earlier_unknowns: int) -> AfterUnknown:
    """`earlier_unknowns` counts this slot's attempts that already ended `unknown`. A model node
    that itself declares an irreversible effect follows that class: it retries only when it also
    declares `idempotent: true` (AD-8, 40 section 5 item 5)."""
    effect = effect_of(definition)
    if effect in ("none", "reversible"):
        return "retry"
    if not model_bearing(definition):
        return "inbox"
    if definition.get("effect") in IRREVERSIBLE:
        return "retry" if definition.get("idempotent") is True else "inbox"
    return "retry" if earlier_unknowns == 0 else "inbox"
