"""The engine's service: the calls SOLUTION-DESIGN 13 gives the control door, named as it names them
(`drafts.put`, `tests.run`, `versions.publish`, `runs.start`, `runs.explain`, `inbox.list`,
`registry()`). EP13 wires them to `ControlService` and REST.

A refusal is a `Refused` from the service or a `LibraryRefused` from the Library, each with a
`code`. Every write names its caller, which the Library records as its principal.

This service also answers for the home it runs on: `answer` is the verb table another owned
instance reaches through `forward` (AD-65), and the merged reads (`merged_runs`, `merged_inbox`,
`run_card`, `spans_of`, `incident`, `explain_trigger`) put this home's rows beside its nodes',
each naming its `home_engine`.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Ledger, Reader, ledger_path
from qmx_engine.nodes.doctor import LlmDoctor
from qmx_engine.ports.clock import Clock, WallClock
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.ports.inbox import Action
from qmx_engine.ports.library import JsonObject, LibraryPort
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.memory import MemoryPort, MemoryStub
from qmx_engine.ports.settings import SettingsPort, StaticSettings
from qmx_engine.runner import Doctor, Engine
from qmx_engine.service.context import OPERATOR, Context, Refused
from qmx_engine.service.drafts import Drafts
from qmx_engine.service.explain import explain
from qmx_engine.service.forward import Forwarder, Homerow, Remote, plain
from qmx_engine.service.inbox import Inbox
from qmx_engine.service.registry import palette
from qmx_engine.service.runs import Runs
from qmx_engine.service.tests import Tests
from qmx_engine.service.versions import Versions
from qmx_engine.workers.local import AnyExecutor


class EngineService:
    def __init__(
        self,
        ctx: Context,
        memory: MemoryPort,
        *,
        name: str = "pc",
        forwarders: Sequence[Forwarder] = (),
        trigger_story: Callable[[str], JsonObject] | None = None,
    ) -> None:
        self.ctx = ctx
        self.memory = memory
        self.name = name
        self.forwarders = tuple(forwarders)
        self.trigger_story = trigger_story
        self.drafts = Drafts(ctx)
        self.runs = Runs(ctx, name=name, forwarders=self.forwarders)
        self.tests = Tests(ctx, self.drafts)
        self.versions = Versions(ctx, self.drafts, self.runs)
        self.inbox = Inbox(ctx.inbox, ctx.clock, name=name, forwarders=self.forwarders)

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
        harness: HarnessPort | None = None,
        name: str = "pc",
        forwarders: Sequence[Forwarder] = (),
        trigger_story: Callable[[str], JsonObject] | None = None,
    ) -> Generator[EngineService]:
        """The service on one QMX home: it holds the ledger writer while it is open. The Library
        is the fake (ruling 91) unless one is given. With a `harness`, model nodes run and the
        ladder's doctor is an `llm` call unless another `doctor` is given. `name` is this home's
        placement name, and `forwarders` are the owned instances it answers for (AD-65)."""
        clock = clock or WallClock()
        settings = settings or StaticSettings()
        with ExitStack() as stack:
            ledger = stack.enter_context(Ledger.open(home))
            inbox = stack.enter_context(InboxTable.open(home))
            if library is None:
                library = stack.enter_context(LibraryFake.open(home, wall=clock.now))
            memory = MemoryStub(library)
            engine = Engine(
                home,
                ledger,
                settings=settings,
                wall=clock.now,
                executors=executors,
                doctor=doctor,
                inbox=inbox,
                harness=harness,
                memory=memory,
            )
            engine.doctor = engine.doctor or LlmDoctor.of(engine)
            ctx = Context(home, library, inbox, settings, clock, engine)
            yield cls(
                ctx,
                memory,
                name=name,
                forwarders=forwarders,
                trigger_story=trigger_story,
            )

    def remote(self) -> Remote:
        """The answering side of the forwarding route, for the host to mount (AD-65)."""
        return Remote(self)

    def watching(self, *, name: str, forwarders: Sequence[Forwarder]) -> None:
        """Name this home and the instances it answers for, once the host has read them.

        The door builds this service before the placements are read, so the host wires the
        merged reads here. One assignment, so no read can see half a wiring.
        """
        self.name = name
        self.forwarders = tuple(forwarders)
        self.runs.name, self.runs.forwarders = name, self.forwarders
        self.inbox.name, self.inbox.forwarders = name, self.forwarders

    def answer(self, verb: str, args: Mapping[str, JsonValue], *, principal: str) -> JsonValue:
        """One forwarded verb, answered from this home's own stores only."""
        match verb:
            case "runs.list":
                object_id = args.get("object_id")
                return cast(
                    JsonValue,
                    [
                        plain(found)
                        for found in self.runs.list(
                            str(args["workflow_item"]),
                            object_id if isinstance(object_id, str) else None,
                        )
                    ],
                )
            case "runs.get":
                return plain(self.runs.get(str(args["run_id"])))
            case "cards":
                return cast(JsonValue, [plain(self.runs.get(str(args["run_id"])))])
            case "spans":
                run_id = str(args["run_id"])
                if not ledger_path(self.ctx.home).exists():
                    raise Refused("unknown_run", f"no run {run_id} here")
                with Reader.open(self.ctx.home) as reader:
                    if not reader.events(run_id):
                        raise Refused("unknown_run", f"no run {run_id} here")
                    return cast(JsonValue, [plain(span) for span in reader.spans(run_id)])
            case "inbox.list":
                return cast(
                    JsonValue,
                    [
                        plain(item)
                        for item in self.inbox.list(open_only=bool(args.get("open_only", True)))
                    ],
                )
            case "inbox.resolve":
                if principal != OPERATOR.principal:
                    raise Refused("ui_only", "only the operator resolves an inbox item")
                item = self.inbox.resolve(
                    str(args["item_id"]),
                    cast(Action, args["action"]),
                    caller=OPERATOR,
                )
                return plain(item)
            case "incidents":
                found = getattr(self.ctx.inbox, "open_incident", None)
                incident = None if found is None else found(str(args["trigger_id"]))
                return cast(JsonValue, [] if incident is None else [plain(incident)])
            case "explain_trigger":
                return self.explain_trigger(str(args["trigger_id"]))
            case _:
                raise Refused("no_verb", f"no verb {verb!r} on this engine")

    def open_items(self) -> list[Mapping[str, JsonValue]]:
        """This home's open items, the stream's one payload (AD-65)."""
        return [
            cast("Mapping[str, JsonValue]", plain(item)) for item in self.inbox.list(open_only=True)
        ]

    def merged_runs(self, workflow_item: str, object_id: str | None = None) -> list[Homerow]:
        return self.runs.merged(workflow_item, object_id)

    def merged_inbox(self, *, open_only: bool = True) -> list[Homerow]:
        return self.inbox.merged(open_only=open_only)

    def run_card(self, run_id: str) -> Homerow:
        return self.runs.card(run_id)

    def spans_of(self, run_id: str) -> list[Homerow]:
        return self.runs.spans_of(run_id)

    def incident(self, trigger_id: str) -> Homerow | None:
        return self.inbox.incident(trigger_id)

    def explain_trigger(self, trigger_id: str) -> JsonObject:
        """Why a trigger did or did not fire, from the engine that holds it (AD-21, AD-65).

        The answer is the control door's own `explain_trigger`, injected by the host, because the
        facts it reads (the ticker's heartbeat, the settings, the pause flag) are the door's.
        """
        if self.trigger_story is None:
            raise Refused("unsupported", "this engine has no trigger view to forward")
        return self.trigger_story(trigger_id)

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
