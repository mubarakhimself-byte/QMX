"""A service on a settable clock with one enabled version of the script chain, for the scheduler
tests."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from flows import CHAIN

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers.rows import Fire, fires


class Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def move(self, **step: float) -> None:
        self.current += timedelta(**step)


@contextmanager
def enabled(home: Path, clock: Clock, bundle: Path = CHAIN) -> Generator[tuple[EngineService, str]]:
    with EngineService.open(home, clock=clock) as svc:
        item = svc.drafts.put(None, Bundle.read(bundle), 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        svc.versions.enable(version, caller=OPERATOR)
        yield svc, version


def fires_of(home: Path, trigger_id: str) -> list[Fire]:
    with Reader.open(home) as reader:
        return fires(reader.connection, trigger_id)
