"""A service on a settable clock with one enabled version of the script chain, for the scheduler
tests."""

from __future__ import annotations

import asyncio
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from flows import CHAIN

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import SettingsPort
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS, Setting
from qmx_engine.triggers.rows import Fire, fires


class Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def move(self, **step: float) -> None:
        self.current += timedelta(**step)


class Flags:
    """Settings a test changes while the engine runs, as he would in the UI."""

    def __init__(self, **changed: Setting) -> None:
        self.current: dict[str, Setting] = dict(DEFAULTS)
        self.set(**changed)

    def set(self, **changed: Setting) -> None:
        self.current |= {key.replace("__", "."): value for key, value in changed.items()}

    def values(self) -> Mapping[str, Setting]:
        return self.current


@contextmanager
def enabled(
    home: Path,
    clock: Clock,
    bundle: Path | Bundle = CHAIN,
    settings: SettingsPort | None = None,
) -> Generator[tuple[EngineService, str]]:
    found = bundle if isinstance(bundle, Bundle) else Bundle.read(bundle)
    with EngineService.open(home, clock=clock, settings=settings) as svc:
        item = svc.drafts.put(None, found, 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        svc.versions.enable(version, caller=OPERATOR)
        yield svc, version


def fires_of(home: Path, trigger_id: str) -> list[Fire]:
    with Reader.open(home) as reader:
        return fires(reader.connection, trigger_id)
