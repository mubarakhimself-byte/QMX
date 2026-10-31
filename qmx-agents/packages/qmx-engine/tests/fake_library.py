"""The engine service and the control door over the engine's SQLite Library fake, for tests that
are not about the Library. Production opens both over the host's store and has no default."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

from qmx_control.service import ControlService

from qmx_engine.control_door import EngineDoor
from qmx_engine.ports.clock import Clock
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.service.api import EngineService


@contextmanager
def fake_service(
    home: Path, *, clock: Clock | None = None, **given: Any
) -> Generator[EngineService]:
    wall = None if clock is None else clock.now
    with (
        LibraryFake.open(home, wall=wall) as library,
        EngineService.open(home, library=library, clock=clock, **given) as svc,
    ):
        yield svc


@asynccontextmanager
async def fake_door(control: ControlService, **given: Any) -> AsyncGenerator[EngineDoor]:
    clock: Clock | None = given.get("clock")
    with LibraryFake.open(control.home, wall=None if clock is None else clock.now) as library:
        async with EngineDoor.open(control, library=library, **given) as door:
            yield door
