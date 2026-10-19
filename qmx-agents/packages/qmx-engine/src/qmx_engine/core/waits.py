"""Waits (SOLUTION-DESIGN 2.3, 3.2). A `wait` node is held until a recorded `clock_tick` reaches
its `resume_at`, or until an `event_received` names its `event` after the hold. The core asks for
the hold (`Hold`); the driver writes it with `resume_at` on the run's clock; the core then starts
the node only once the hold is due. No compute runs while it is held.

Instants are compared as text. Both the clock and `resume_at` are ISO-8601 instants in UTC written
the same way, so text order is time order; the core does no date arithmetic (AD-6).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qmx_engine.core.state import Held


class WaitSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    seconds: int | None = Field(default=None, ge=0)
    until: str | None = None
    event: str | None = None

    @model_validator(mode="after")
    def _one(self) -> Self:
        if [self.seconds, self.until, self.event].count(None) != 2:
            raise ValueError("a wait names exactly one of seconds, until and event")
        return self


def due(held: Held, now: str | None, received: Sequence[tuple[str, int]]) -> bool:
    if held.event is not None:
        return any(name == held.event and seq > held.seq for name, seq in received)
    return held.resume_at is not None and now is not None and now >= held.resume_at
