"""The engine's service: the calls SOLUTION-DESIGN 13 gives the control door, named as it names them
(`drafts.put`, `tests.run`, `versions.publish`, `runs.start`, `runs.explain`, `inbox.list`,
`registry()`). EP13 wires them to `ControlService` and REST.

A refusal is a `Refused` from the service or a `LibraryRefused` from the Library, each with a
`code`. Every write names its caller, which the Library records as its principal.
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import ExitStack, contextmanager
from pathlib import Path

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Ledger, Reader, ledger_path
from qmx_engine.ports.clock import Clock, WallClock
from qmx_engine.ports.library import JsonObject, LibraryPort
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.memory import MemoryPort, MemoryStub
from qmx_engine.ports.settings import SettingsPort, StaticSettings
from qmx_engine.runner import Doctor, Engine
from qmx_engine.service.context import Context, Refused
from qmx_engine.service.drafts import Drafts
from qmx_engine.service.explain import explain
from qmx_engine.service.inbox import Inbox
from qmx_engine.service.registry import palette
from qmx_engine.service.runs import Runs
from qmx_engine.service.tests import Tests
from qmx_engine.service.versions import Versions
from qmx_engine.workers.local import AnyExecutor


class EngineService:
    def __init__(self, ctx: Context, memory: MemoryPort) -> None:
        self.ctx = ctx
        self.memory = memory
        self.drafts = Drafts(ctx)
        self.runs = Runs(ctx)
        self.tests = Tests(ctx, self.drafts)
        self.versions = Versions(ctx, self.drafts, self.runs)
        self.inbox = Inbox(ctx.inbox, ctx.clock)

    @classmethod
    @contextmanager
    def open(
        cls,
        home: Path,
        *,
        library: LibraryPort | None = None,
        settings: SettingsPort | None = None,
        clock: Clock | None = None,
        executors: Mapping[str, AnyExecutor] | None = None,
        doctor: Doctor | None = None,
    ) -> Generator[EngineService]:
        """The service on one QMX home: it holds the ledger writer while it is open. The Library
        is the fake (ruling 91) unless one is given."""
        clock = clock or WallClock()
        settings = settings or StaticSettings()
        with ExitStack() as stack:
            ledger = stack.enter_context(Ledger.open(home))
            inbox = stack.enter_context(InboxTable.open(home))
            if library is None:
                library = stack.enter_context(LibraryFake.open(home, wall=clock.now))
            engine = Engine(
                home,
                ledger,
                settings=settings.values(),
                wall=clock.now,
                executors=executors,
                doctor=doctor,
                inbox=inbox,
            )
            ctx = Context(home, library, inbox, settings, clock, engine)
            yield cls(ctx, MemoryStub(library))

    def explain(self, run_id: str) -> JsonObject:
        return explain_run(self.ctx.home, run_id)

    def registry(self) -> list[JsonObject]:
        return palette()


def explain_run(home: Path, run_id: str) -> JsonObject:
    if not ledger_path(home).exists():
        raise Refused("unknown_run", f"no ledger in {home}")
    with Reader.open(home) as reader:
        events = reader.events(run_id)
        spans = reader.spans(run_id)
    if not events:
        raise Refused("unknown_run", f"no run {run_id}")
    return explain(events, spans)
