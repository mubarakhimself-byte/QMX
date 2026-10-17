"""Loop stops (SOLUTION-DESIGN 3.5). A `loop` node iterates its body, the induced subgraph of nodes
its `body` port reaches; the body hands each iteration's value back on the loop's `next` port, and
each iteration's slots carry `iteration = k`.

Before iteration k the core decides from the ledger whether a typed stop fires, checked in this
order: `max_iterations` (k has reached it), `budget` (the body's attempts have reported that many
tokens), `predicate` (a `qmx_engine.definition.expr` expression over the last value handed back,
true means stop) and `no_progress_rounds` (the `metric` key of the values handed back has not risen
for that many rounds in a row). The decision is an input of the loop's slot, so it is memoised and
recorded, and iteration state never lives in a node result.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from qmx_engine.definition.expr import RuleError, RuleRefused, evaluate


class LoopError(ValueError):
    """The predicate is refused or fails on a value, or the metric is not a number."""


class LoopSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_iterations: int | None = Field(default=None, ge=0)
    budget: int | None = Field(default=None, gt=0)
    predicate: str | None = None
    no_progress_rounds: int | None = Field(default=None, gt=0)
    metric: str | None = None

    @model_validator(mode="after")
    def _stops(self) -> Self:
        if (self.no_progress_rounds is None) != (self.metric is None):
            raise ValueError("no_progress_rounds and metric are given together")
        if (self.max_iterations, self.budget, self.predicate, self.metric) == (None,) * 4:
            raise ValueError("a loop needs at least one stop")
        return self


def _metric(value: JsonValue, name: str) -> float:
    found = value.get(name) if isinstance(value, dict) else None
    if not isinstance(found, int | float) or isinstance(found, bool):
        raise LoopError(f"metric {name!r} is not a number in a value handed back")
    return found


def flat_rounds(metrics: Sequence[float]) -> int:
    """Rounds in a row, counted back from the last, in which the metric did not rise."""
    count = 0
    for before, after in zip(metrics[-2::-1], metrics[::-1], strict=False):
        if after > before:
            break
        count += 1
    return count


def stop(spec: LoopSpec, k: int, values: Sequence[JsonValue], spent: int) -> str | None:
    """`values` holds what the body handed back after each of the k iterations so far."""
    if spec.max_iterations is not None and k >= spec.max_iterations:
        return "max_iterations"
    if spec.budget is not None and spent >= spec.budget:
        return "budget"
    if spec.predicate is not None and values:
        try:
            if evaluate(spec.predicate, {"in": values[-1]}):
                return "predicate"
        except (RuleRefused, RuleError) as error:
            raise LoopError(f"predicate: {error}") from None
    if spec.no_progress_rounds is not None and spec.metric is not None:
        metrics = [_metric(value, spec.metric) for value in values]
        if flat_rounds(metrics) >= spec.no_progress_rounds:
            return "no_progress_rounds"
    return None
