"""The zero-token watchdog (AD-16, SOLUTION-DESIGN 10.3). The runner calls it on every tick while
attempts are in flight; it reads only what the run already recorded and never calls a model.

- An attempt with no event past its idle timeout is stalled: the runner cancels it and it fails
  `stalled`, retryable, into the ladder.
- A ledger write error stops the engine claiming new work and raises a `black` `system_fault`.

The other rules of 10.3 live where they decide: the runaway guard and "the same node failing twice
with one signature goes to the doctor" are checked by the core (`core.ladder`), before each rung
and before any new attempt starts, so a breach never lets one more attempt through.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from qmx_engine.ledger.signature import signature
from qmx_engine.ports.inbox import Category, Raise

STALLED: Final = "stalled"
STALLED_MESSAGE: Final = "the attempt stalled: no heartbeat or event past its idle timeout"


@dataclass(frozen=True, slots=True)
class Open:
    """One attempt in flight: its idempotency key, when it last wrote an event, and its idle
    timeout (None when it has none)."""

    key: str
    last_seen: datetime
    idle_seconds: int | None


def stalled(attempts: Iterable[Open], now: datetime) -> list[str]:
    """The keys of the attempts silent past their idle timeout."""
    return [
        a.key
        for a in attempts
        if a.idle_seconds is not None and now - a.last_seen > timedelta(seconds=a.idle_seconds)
    ]


def ledger_fault(run_id: str, error: Exception) -> Raise:
    message = str(error)
    return Raise(
        run_id,
        signature("ledger_write", message),
        Category.SYSTEM_FAULT,
        "the run ledger cannot be written; the engine stopped claiming work",
        message,
        severity="black",
        blocks_run=True,
    )
