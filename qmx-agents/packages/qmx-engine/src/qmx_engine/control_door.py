"""The engine behind `ControlService`'s workflow doors (SOLUTION-DESIGN 13, AD-21).

`EngineDoor.open` builds the engine service, its scheduler and the Library watcher on the running
loop and attaches the door to a `ControlService`, so REST, `/mcp` and the copilot's `qmx` tools all
reach one engine. The doors are synchronous and arrive on worker threads (FastAPI and fastmcp run
sync handlers there); each one hops onto the engine's loop, where the Library and the runs live.

Callers. A DOMAIN_WRITE door (draft save, test run) acts as an agent. A MANAGE door (publish, live
run, archive, cancel, resume, the trigger writes) acts as the operator: the harness asked him
before the call, or it came over REST with his bearer.

Runs. A start returns when the run ends or after `wait_seconds`, whichever comes first; the run goes
on in the background and `workflow_runs_get` follows it. Every document and error a door returns
has token-shaped text redacted, because explain and failure messages are verbatim (EP9).

Fallback (H17's safety path). A `workflow` object saved with `library_save` is imported into
`refs/drafts/<id>`, and test-run when its `meta.test_requested` nonce changed and it validates.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import enum
import json
import logging
import threading
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Coroutine, Mapping
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError
from qmx_control.models import ControlError, Document
from qmx_control.service import ControlService

from qmx_engine.definition.lint import redact
from qmx_engine.ledger.inbox_table import InboxRefused
from qmx_engine.ledger.store import Operation, Reader, Transaction, ledger_path
from qmx_engine.ports.clock import Clock
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.ports.inbox import Action
from qmx_engine.ports.library import Bundle, Draft, JsonObject, LibraryRefused
from qmx_engine.ports.settings import ControlSettings, SettingsPort
from qmx_engine.runner import Refused as EngineRefused
from qmx_engine.runner import new_run_id
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller, Refused
from qmx_engine.service.runs import status_of, summarize_again
from qmx_engine.trace_export import export
from qmx_engine.triggers import rows
from qmx_engine.triggers.catchup import CatchUp
from qmx_engine.triggers.cron import Cron, Interval
from qmx_engine.triggers.preflight import configured_refs, shipped_skills
from qmx_engine.triggers.ticker import Scheduler

AGENT: Final = Caller("agent", "qmx-control")
LIBRARY: Final = Caller("agent", "library")
WAIT_SECONDS: Final = 20.0
ENDED: Final = frozenset({"passed", "stopped"})
NOT_FOUND: Final = frozenset(
    {"unknown_run", "unknown_workflow", "unknown_trigger", "unknown_version", "no_draft"}
)
EVENT_POLL_S: Final = 0.25
CURSOR: Final = Path("engine") / "library-watch.cursor"
LOG = logging.getLogger(__name__)

type Failure = Refused | LibraryRefused | EngineRefused | InboxRefused | ValueError
FAILURES: Final = (Refused, LibraryRefused, EngineRefused, InboxRefused, ValueError)


def control_error(error: Failure) -> ControlError:
    if isinstance(error, Refused | LibraryRefused):
        code = error.code
    elif isinstance(error, InboxRefused):
        code = "inbox_refused"
    else:
        code = "engine_refused" if isinstance(error, EngineRefused) else "bad_request"
    status = 404 if code in NOT_FOUND else 422 if code in ("invalid", "bad_request") else 409
    return ControlError(code, redact(str(error)), status)


def plain(value: object) -> JsonValue:
    """A JSON value with every string redacted. Dataclasses, named tuples, enums and file bytes
    become what a client reads."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = {f.name: getattr(value, f.name) for f in dataclasses.fields(value)}
    elif isinstance(value, tuple) and hasattr(cast(object, value), "_asdict"):
        value = cast(Any, value)._asdict()
    match value:
        case enum.Enum():
            return plain(value.value)
        case str():
            return redact(value)
        case bool() | int() | float() | None:
            return value
        case bytes():
            return redact(value.decode("utf-8", "replace"))
        case datetime():
            return value.isoformat()
        case Mapping():
            return {str(k): plain(v) for k, v in cast(Mapping[object, object], value).items()}
        case list() | tuple() | set() | frozenset():
            return [plain(v) for v in cast(list[object], value)]
        case _:
            raise TypeError(f"cannot serve a {type(value).__name__}")


def bundle_of(graph: Mapping[str, JsonValue]) -> Bundle:
    """A workflow as a door takes it: its definition alone, or `{definition, files}` with each
    file as text."""
    definition, files = (
        (graph["definition"], graph.get("files", {})) if "definition" in graph else (graph, {})
    )
    if not isinstance(definition, dict) or not isinstance(files, dict):
        raise ValueError("a workflow is its definition, or {definition, files}")
    if not all(isinstance(text, str) for text in files.values()):
        raise ValueError("each file of a workflow is text")
    texts = cast(dict[str, str], files)
    return Bundle(dict(definition), {ref: text.encode() for ref, text in texts.items()})


def nonce(bundle: Bundle) -> JsonValue:
    meta = bundle.definition.get("meta")
    return cast(JsonObject, meta).get("test_requested") if isinstance(meta, dict) else None


def next_semver(taken: list[str]) -> str:
    if not taken:
        return "1.0.0"
    major, minor, patch = max(tuple(int(p) for p in s.split(".")) for s in taken)
    return f"{major}.{minor}.{patch + 1}"


def set_enabled(trigger_id: str, enabled: bool) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "UPDATE triggers SET enabled = ? WHERE id = ?", (int(enabled), trigger_id)
        )

    return operation


def drop_wake(run_id: str) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute("DELETE FROM wakes WHERE run_id = ?", (run_id,))

    return operation


class PublishIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semver: str | None = Field(default=None, pattern=r"^\d+\.\d+\.\d+$")


class TriggerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["cron", "interval", "manual", "after"]
    expr: str | None = None
    zone: str = "UTC"
    seconds: int | None = None
    workflow_item: str | None = None
    """The upstream workflow of an `after` trigger."""
    object_id: str | None = None
    """The version to pin; the workflow's latest when left out."""
    follow_champion: bool = False
    precheck_ref: str | None = None
    delivery: rows.Delivery = "digest"
    continuity: bool = False
    catch_up: CatchUp = "merged"
    max_concurrent: int = Field(default=1, ge=1)

    def spec(self, now: datetime) -> rows.Spec:
        match self.kind:
            case "cron" if self.expr:
                return Cron(self.expr, self.zone)
            case "interval" if self.seconds is not None:
                return Interval(self.seconds, now)
            case "after" if self.workflow_item:
                return rows.After(self.workflow_item)
            case "manual":
                return rows.Manual()
            case _:
                raise ValueError(f"a {self.kind} trigger needs expr, seconds or workflow_item")


class EngineDoor:
    def __init__(
        self,
        control: ControlService,
        svc: EngineService,
        scheduler: Scheduler,
        wait_seconds: float,
    ) -> None:
        self.control = control
        self.svc = svc
        self.scheduler = scheduler
        self.wait_seconds = wait_seconds
        self.loop = asyncio.get_running_loop()
        self.thread = threading.get_ident()
        self.live: dict[str, asyncio.Task[object]] = {}
        """Runs this door started or resumed that are still going."""

    @classmethod
    @asynccontextmanager
    async def open(
        cls,
        control: ControlService,
        *,
        harness: HarnessPort | None = None,
        settings: SettingsPort | None = None,
        clock: Clock | None = None,
        wait_seconds: float = WAIT_SECONDS,
    ) -> AsyncGenerator[EngineDoor]:
        """The engine on `control`'s home, attached for as long as the block runs, with the
        scheduler ticking (a limit-paused run wakes only while it ticks) and the Library watched."""
        with EngineService.open(
            control.home,
            settings=settings or ControlSettings(control),
            harness=harness,
            clock=clock,
        ) as svc:
            scheduler = Scheduler(
                svc.ctx, credentials=configured_refs(control), skills=shipped_skills()
            )
            door = cls(control, svc, scheduler, wait_seconds)
            stop = asyncio.Event()
            workers = [
                asyncio.create_task(scheduler.serve(stop)),
                asyncio.create_task(door.watch(stop)),
            ]
            control.attach_workflow_engine(door)
            try:
                yield door
            finally:
                control.attach_workflow_engine(None)
                stop.set()
                going = [*door.live.values(), *scheduler.fires.values(), *scheduler.waking.values()]
                for task in going:
                    task.cancel()
                await asyncio.gather(*workers, *going, return_exceptions=True)

    def _call[T](self, work: Callable[[], Coroutine[Any, Any, T]]) -> T:
        if threading.get_ident() == self.thread:
            raise ControlError(
                "wrong_thread", "a workflow door was called on the engine's loop", 500
            )
        try:
            return asyncio.run_coroutine_threadsafe(work(), self.loop).result()
        except FAILURES as error:
            raise control_error(error) from error

    def _serve(self, read: Callable[[], object]) -> Document:
        async def hop() -> object:
            return read()

        return cast(Document, plain(self._call(hop)))

    def _serve_all(self, read: Callable[[], list[Any]]) -> list[Document]:
        async def hop() -> list[Any]:
            return read()

        return [cast(Document, plain(found)) for found in self._call(hop)]

    def _spawn(self, run_id: str, work: Coroutine[Any, Any, object]) -> asyncio.Task[object]:
        task = asyncio.create_task(work)
        self.live[run_id] = task
        task.add_done_callback(lambda done: self._ended(run_id, done))
        return task

    def _ended(self, run_id: str, task: asyncio.Task[object]) -> None:
        self.live.pop(run_id, None)
        if not task.cancelled() and (error := task.exception()) is not None:
            LOG.warning("run %s stopped on %s", run_id, redact(repr(error)))

    async def _launch(self, run_id: str, work: Coroutine[Any, Any, object]) -> object:
        """The run's result when it ends within `wait_seconds`, else None while it goes on."""
        task = self._spawn(run_id, work)
        done, _ = await asyncio.wait({task}, timeout=self.wait_seconds)
        return task.result() if done else None

    def _new_run_id(self) -> str:
        return new_run_id(self.svc.ctx.clock.now())

    def _draft(self, item: str) -> Draft | None:
        try:
            return self.svc.drafts.get(item)
        except LibraryRefused as refused:
            if refused.code == "no_draft":
                return None
            raise

    def _draft_view(self, item: str) -> Mapping[str, object]:
        draft = self.svc.drafts.get(item)
        return {
            "workflow_id": item,
            "revision": draft.revision,
            "object_id": draft.object_id,
            "content_hash": draft.content_hash,
            "state": self.svc.drafts.state(item),
            "problems": self.svc.drafts.problems(draft.bundle),
            "definition": draft.bundle.definition,
            "files": dict(draft.bundle.files),
        }

    def _version_id(self, ref: str) -> str:
        """`ref` as a workflow id (its latest version that is not archived) or a version id."""
        versions = [v for v in self.svc.versions.list(ref) if v.state != "archived"]
        return versions[-1].object_id if versions else self.svc.versions.get(ref).object_id

    def _run(self, run_id: str) -> Mapping[str, object]:
        view = self.svc.runs.get(run_id)
        summaries = self.svc.ctx.library.objects(run_id, "workflow-run")
        item = summaries[-1].fields.get("workflow_item") if summaries else None
        return dataclasses.asdict(view) | {"workflow_item": item, "in_flight": run_id in self.live}

    def _trigger_row(self, trigger_id: str) -> rows.Trigger:
        with Reader.open(self.svc.ctx.home) as reader:
            found = rows.triggers(reader.connection, "WHERE id = ?", trigger_id)
        if not found:
            raise Refused("unknown_trigger", f"no trigger {trigger_id}")
        return found[0]

    @staticmethod
    def _trigger_view(trigger: rows.Trigger) -> Mapping[str, object]:
        fields = {f.name: getattr(trigger, f.name) for f in dataclasses.fields(trigger)}
        return fields | {"kind": trigger.kind, "spec": json.loads(rows.spec_json(trigger.spec))}

    def workflows_get(self, workflow_id: str) -> Document:
        def read() -> object:
            versions = self.svc.versions.list(workflow_id)
            draft = self._draft(workflow_id)
            if versions:
                definition = self.svc.ctx.library.get_object(versions[-1].object_id).definition
                state: str = versions[-1].state
            elif draft is not None:
                definition, state = draft.bundle.definition, self.svc.drafts.state(workflow_id)
            else:
                raise Refused("unknown_workflow", f"no workflow {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "state": state,
                "definition": definition,
                "versions": versions,
                "draft_revision": None if draft is None else draft.revision,
            }

        return self._serve(read)

    def workflows_put(self, workflow_id: str, graph: Document) -> Document:
        try:
            wanted = PublishIn.model_validate(graph)
        except ValidationError as error:
            message = (
                "workflows_put publishes the tested draft and takes only {semver}; save a draft "
                "with workflow_drafts_put"
            )
            raise ControlError("publish_only", message, 422) from error

        def publish() -> object:
            versions = self.svc.versions
            semver = wanted.semver or next_semver([v.semver for v in versions.list(workflow_id)])
            return versions.get(versions.publish(workflow_id, semver, caller=OPERATOR))

        return self._serve(publish)

    def workflows_validate(self, graph: Document) -> Document:
        def check() -> object:
            bundle = bundle_of(graph)
            problems = self.svc.drafts.problems(bundle)
            return {
                "valid": not problems,
                "content_hash": None if problems else bundle.content_hash(),
                "problems": problems,
            }

        return self._serve(check)

    def workflows_run(self, workflow_id: str) -> Document:
        async def start() -> object:
            object_id = self._version_id(workflow_id)
            run_id = self._new_run_id()
            runs = self.svc.runs
            await self._launch(run_id, runs.start(object_id, caller=OPERATOR, run_id=run_id))
            return self._run(run_id)

        return cast(Document, plain(self._call(start)))

    def workflow_drafts_get(self, workflow_id: str) -> Document:
        return self._serve(lambda: self._draft_view(workflow_id))

    def workflow_drafts_put(self, workflow_id: str, graph: Document) -> Document:
        def save() -> object:
            bundle = bundle_of(graph)
            expected = graph.get("expected_revision") if "definition" in graph else None
            if expected is None:
                current = self._draft(workflow_id)
                expected = 0 if current is None else current.revision
            if not isinstance(expected, int):
                raise ValueError("expected_revision is a whole number")
            self.svc.drafts.put(workflow_id, bundle, expected, caller=AGENT)
            return self._draft_view(workflow_id)

        return self._serve(save)

    def workflow_tests_run(
        self, workflow_id: str, subgraph: list[str] | None, fake: bool
    ) -> Document:
        async def test() -> object:
            run_id = self._new_run_id()
            work = self.svc.tests.run(
                workflow_id, caller=AGENT, subgraph=subgraph, fake=fake, run_id=run_id
            )
            report = await self._launch(run_id, work)
            return {"run": self._run(run_id), "report": report}

        return cast(Document, plain(self._call(test)))

    def workflow_versions_list(self, workflow_id: str) -> list[Document]:
        return self._serve_all(lambda: self.svc.versions.list(workflow_id))

    def workflow_versions_archive(self, workflow_id: str, version: int) -> Document:
        """`version` counts the workflow's versions from 1, in publish order."""

        def archive() -> object:
            versions = self.svc.versions.list(workflow_id)
            if not 1 <= version <= len(versions):
                raise Refused("unknown_version", f"{workflow_id} has {len(versions)} versions")
            return self.svc.versions.archive(versions[version - 1].object_id, caller=OPERATOR)

        return self._serve(archive)

    def workflow_runs_list(self, workflow_id: str | None) -> list[Document]:
        def listed() -> list[Any]:
            home = self.svc.ctx.home
            if not ledger_path(home).exists():
                return []
            with Reader.open(home) as reader:
                found = reader.connection.execute(
                    "SELECT run_id FROM events WHERE seq = 1"
                    " ORDER BY at DESC, run_id DESC LIMIT 200"
                ).fetchall()
            views = [self._run(str(run_id)) for (run_id,) in found]
            return [v for v in views if workflow_id is None or v["workflow_item"] == workflow_id]

        return self._serve_all(listed)

    def workflow_runs_get(self, run_id: str) -> Document:
        return self._serve(lambda: self._run(run_id))

    def workflow_runs_explain(self, run_id: str) -> Document:
        return self._serve(lambda: self.svc.explain(run_id))

    def workflow_runs_cancel(self, run_id: str) -> Document:
        """Stop the run's attempts and the run here, then end it `stopped` (reason `operator`,
        SOLUTION-DESIGN 3.1) whether it was running, waiting or parked."""

        async def cancel() -> object:
            status = self.svc.runs.get(run_id).status
            if status in ENDED:
                raise Refused("cancel_refused", f"run {run_id} already ended {status}")
            running = self.svc.ctx.engine.worker.running
            going = [t for key, t in running.items() if key.startswith(f"{run_id}:")]
            going += [self.live[run_id]] if run_id in self.live else []
            for task in going:
                task.cancel()
            if going:
                await asyncio.wait(going, timeout=10)
            ledger = self.svc.ctx.engine.ledger
            ledger.write(drop_wake(run_id))
            ledger.append(run_id, "run_cancelled", {"reason": "operator"}, at=self.svc.ctx.at())
            self._summarize(run_id)
            return self._run(run_id)

        return cast(Document, plain(self._call(cancel)))

    def _summarize(self, run_id: str) -> None:
        ctx = self.svc.ctx
        summaries = ctx.library.objects(run_id, "workflow-run")
        if not summaries:
            return
        last = summaries[-1].fields
        with Reader.open(ctx.home) as reader:
            state = status_of(reader.events(run_id))
        export(
            ctx.home,
            run_id,
            ctx.library,
            workflow_item=str(last.get("workflow_item")),
            object_id=str(last.get("object_id")),
            mode="live" if last.get("mode") == "live" else "test",
            status=state.status,
            reason=state.reason,
            started_by=str(last.get("started_by")),
        )

    def workflow_runs_resume(self, run_id: str) -> Document:
        async def resume() -> object:
            if run_id in self.live:
                raise Refused("resume_refused", f"run {run_id} is still going")
            status = self.svc.runs.get(run_id).status
            if status in ENDED:
                raise Refused("resume_refused", f"run {run_id} already ended {status}")
            await self._launch(run_id, self._resumed(run_id))
            return self._run(run_id)

        return cast(Document, plain(self._call(resume)))

    async def _resumed(self, run_id: str) -> None:
        outcome = await self.svc.ctx.engine.resume(run_id)
        summarize_again(self.svc.ctx, outcome)

    def workflow_triggers_list(self, workflow_id: str | None) -> list[Document]:
        def listed() -> list[Any]:
            home = self.svc.ctx.home
            if not ledger_path(home).exists():
                return []
            where, args = ("WHERE workflow_item = ?", (workflow_id,)) if workflow_id else ("", ())
            with Reader.open(home) as reader:
                found = rows.triggers(reader.connection, where, *args)
            return [self._trigger_view(t) for t in found]

        return self._serve_all(listed)

    def workflow_triggers_create(self, workflow_id: str, trigger: Document) -> Document:
        """The trigger starts disabled; enabling it is its own MANAGE door."""

        def create() -> object:
            wanted = TriggerIn.model_validate(trigger)
            object_id = wanted.object_id or self._version_id(workflow_id)
            if self.svc.versions.get(object_id).item != workflow_id:
                raise Refused("trigger_refused", f"{object_id} is not a version of {workflow_id}")
            now = self.svc.ctx.clock.now()
            ledger = self.svc.ctx.engine.ledger
            made = rows.create(
                ledger,
                workflow_item=workflow_id,
                pinned_object=object_id,
                spec=wanted.spec(now),
                caller=OPERATOR,
                now=now,
                follow_champion=wanted.follow_champion,
                precheck_ref=wanted.precheck_ref,
                delivery=wanted.delivery,
                continuity=wanted.continuity,
                catch_up=wanted.catch_up,
                max_concurrent=wanted.max_concurrent,
            )
            ledger.write(set_enabled(made.id, False))
            return self._trigger_view(self._trigger_row(made.id))

        return self._serve(create)

    def workflow_triggers_enable(self, trigger_id: str) -> Document:
        """Enable the trigger and, when it is not yet, its pinned version, which must be tested."""

        def enable() -> object:
            found = self._trigger_row(trigger_id)
            versions = self.svc.versions
            if versions.get(found.pinned_object).state != "enabled":
                versions.enable(found.pinned_object, caller=OPERATOR)
            self.svc.ctx.engine.ledger.write(set_enabled(trigger_id, True))
            return self._trigger_view(self._trigger_row(trigger_id))

        return self._serve(enable)

    def workflow_triggers_disable(self, trigger_id: str) -> Document:
        def disable() -> object:
            self._trigger_row(trigger_id)
            self.svc.ctx.engine.ledger.write(set_enabled(trigger_id, False))
            return self._trigger_view(self._trigger_row(trigger_id))

        return self._serve(disable)

    def workflow_triggers_run_now(self, trigger_id: str) -> Document:
        async def fire() -> object:
            self._trigger_row(trigger_id)
            ledger = self.svc.ctx.engine.ledger
            fire_id = rows.fire_now(ledger, trigger_id, self.svc.ctx.clock.now(), {})
            await self.scheduler.tick()
            return {"trigger_id": trigger_id, "fire_id": fire_id}

        return cast(Document, plain(self._call(fire)))

    def workflow_inbox_list(self) -> list[Document]:
        return self._serve_all(self.svc.inbox.list)

    def inbox_resolve(self, item_id: str, action: Action) -> Document:
        """The operator's, from the UI; no agent tool reaches it."""
        return self._serve(lambda: self.svc.inbox.resolve(item_id, action, caller=OPERATOR))

    async def events(self, run_id: str, after: int, max_events: int) -> AsyncIterator[Document]:
        """The run's ledger events after `after`, in `seq` order, as they are written."""
        home, sent = self.svc.ctx.home, 0

        def read() -> list[Document]:
            if not ledger_path(home).exists():
                return []
            with Reader.open(home) as reader:
                return [cast(Document, plain(e)) for e in reader.events(run_id, after=after)]

        while True:
            for event in await asyncio.to_thread(read):
                after = cast(int, event["seq"])
                yield event
                sent += 1
                if max_events and sent >= max_events:
                    return
            await asyncio.sleep(EVENT_POLL_S)

    async def watch(self, stop: asyncio.Event) -> None:
        """Import each `workflow` object `library_save` stores, from a cursor kept in the home, so
        a restart neither replays old saves nor misses one made while the host was down."""
        cursor = self.svc.ctx.home / CURSOR
        after = int(cursor.read_text(encoding="utf-8")) if cursor.exists() else 0
        while not stop.is_set():
            for event in self.control.events("library", after, limit=1000):
                data = event["data"]
                if isinstance(data, dict) and data.get("type") == "saved":
                    try:
                        await self.import_draft(str(data.get("item_id")))
                    except (ControlError, *FAILURES) as e:
                        LOG.warning("library object %s not imported: %s", data, redact(str(e)))
                after = cast(int, event["id"])
                cursor.parent.mkdir(parents=True, exist_ok=True)
                cursor.write_text(str(after), encoding="utf-8")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=1)

    async def import_draft(self, artifact_id: str) -> None:
        saved = self.control.library_get(artifact_id)
        if saved.get("kind") != "workflow":
            return
        content = saved.get("content")
        if not isinstance(content, dict):
            raise ValueError(f"workflow object {artifact_id} holds no definition")
        bundle = bundle_of(content)
        item = bundle.definition.get("id")
        if not isinstance(item, str) or not item:
            raise ValueError(f"workflow object {artifact_id} has no id")
        current = self._draft(item)
        if current is not None and current.bundle == bundle:
            return
        before = None if current is None else nonce(current.bundle)
        revision = 0 if current is None else current.revision
        self.svc.drafts.put(item, bundle, revision, caller=LIBRARY)
        asked = nonce(bundle)
        if asked is not None and asked != before and not self.svc.drafts.problems(bundle):
            run_id = self._new_run_id()
            self._spawn(run_id, self.svc.tests.run(item, caller=LIBRARY, run_id=run_id))
