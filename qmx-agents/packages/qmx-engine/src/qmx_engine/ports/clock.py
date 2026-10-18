"""The clock port: where the service and the runner read the wall time. Only the recorded clock in
the ledger reaches the core (AD-6); this is what writes it."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class WallClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class SteppingClock:
    """A recorded clock for tests and lanes: each read moves `step` past the last."""

    def __init__(self, start: datetime, step: timedelta = timedelta(seconds=1)) -> None:
        self.current = start
        self.step = step

    def now(self) -> datetime:
        found = self.current
        self.current += self.step
        return found
