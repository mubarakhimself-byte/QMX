"""The session recorder (Library AD-21): every chat the harness creates gets one `session` item.

The host writes it with its own principal `engine:<store>` on `refs/sessions/<session_id>` and
lands each version on `main`. The item id is the session id, so a host restarted mid-session
keeps writing the same item. Identity is `session_id`, `home` and `created`. A turn end only
annotates the head (title, last turn time, turn and token counts, models, profiles, packs and the
surface digest, engine AD-62), so no version is minted per turn (AD-2). A close by its owner, or a
chat idle past `IDLE`, puts a new version whose `transcript` blob is the harness's redacted export
(engine AD-37). The live transcript stays the CLI's JSONL; the Library copy is never read back.

The recorder also mirrors the chat record's attached context references (engine AD-63) onto the
item: each attached object becomes an `item:<object_id>` tag and a `mentions` edge, so the Library
answers "what did this session use" without a second list (Library AD-21).

`RecordedHarness` is the harness the host serves. It tells the recorder of each chat's birth,
each turn's end and each close, and it serves the `context` toolset from the same store: one read
per catalog target per chat, because attaching writes that chat's own record.

A hook sink cannot do any of it: only Background and Child chats may name one, and engine chats
already name `engine`.
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, cast, override

from pydantic import JsonValue
from qma.harness import Harness, NewChat, QmxHome, SessionId, TurnHandle, TurnResult
from qma.harness.chat import ChatDeps, Prompt
from qma.harness.harness import PlanWatch
from qma.harness.home import ChatRecord, list_records, read_record
from qma.harness.surface import excerpt_budget
from qma.harness.tools import HostRead
from qmx_control.context import (
    AttachedRef,
    ContextRefused,
    LibraryHit,
    LibraryObject,
    Resolvers,
    listing,
)
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectView
from qmx_library.principal import MAIN, sessions_ref, state_ref
from qmx_library.store import Store

if TYPE_CHECKING:
    from qma.harness.launch import TestMode
    from qmx_control.service import ControlService

KIND: Final = "session"
IDLE: Final = timedelta(hours=24)
"""Claude's default: a chat idle this long gets its daily export."""
IDLE_TICK_S: Final = 3600.0
TRANSCRIPT: Final = "transcript.jsonl"
MENTIONS: Final = "mentions"
"""The edge from a session item to each object it attached (Library AD-14's vocabulary)."""

type Exporter = Callable[[SessionId], Awaitable[Path]]

RECORDING_FAILED: Final = (OSError, LibraryRefused)
"""A recorder write that fails is reported and skipped, never raised into the chat."""


def _skipped(what: str, error: Exception) -> None:
    print(f"session {what} skipped: {type(error).__name__}: {error}", file=sys.stderr)


def _list(value: JsonValue, add: str) -> list[JsonValue]:
    found = list(value) if isinstance(value, list) else []
    return found if add in found else [*found, add]


def _int(value: JsonValue) -> int:
    return value if isinstance(value, int) else 0


class StoreReads:
    """`qmx_control.context.LibraryReads` over the host's store: reads only, no policy. A
    missing object reads as an empty one, so a resolver refuses it by name."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def head(self, item: str, ref: str = MAIN) -> str | None:
        found = self.store.head(item, ref)
        return None if found is None else found[0]

    def state(self, item: str) -> str | None:
        """An item's state is a move on its own state ref (Library AD-6), so no private read."""
        found = self.store.head(item, state_ref(item))
        return None if found is None else found[0]

    def get(self, object_id: str, slots: Sequence[str] = ()) -> LibraryObject:
        try:
            found = self.store.get(self.store.engine, object_id)
        except LibraryRefused:
            return LibraryObject("", "", "")
        data = {
            slot: self.store.read_blob(found.blobs[slot].blob_id)
            for slot in slots
            if slot in found.blobs
        }
        return _library_object(found, data)

    def search(self, text: str, *, kind: str | None = None, limit: int = 20) -> list[LibraryHit]:
        found = self.store.search(self.store.engine, text, kind=kind, limit=limit)
        return [LibraryHit(hit.object_id, hit.item, hit.kind, hit.title) for hit in found]

    def versions(self, item: str, kind: str) -> list[str]:
        return [object_id for object_id, _ in self.store.placed(item, kind, None)]

    def produced(self, producer: str) -> list[str]:
        """The artifacts a run object produced, in the order the edges were written."""
        return [from_id for from_id, name, _, _, _ in self.store.edges_of(producer, reverse=True)
                if name == "produced-by"]  # fmt: skip

    def outputs(self, producer: str, name: str) -> list[str]:
        """The artifacts the app `producer` landed under `name`, oldest first. An output names
        itself by the artifact's `type` or the `output` of `qmx_apps.artifacts.ArtifactRef`, and
        the app owns it by a `produced-by` edge from one of its versions or by the reference's
        `producer_app`."""
        produced = {
            edge
            for version in self.versions(producer, "mini-app")
            for edge in self.produced(version)
        }
        found = [
            object_id
            for object_id in self.store.with_field("artifact", "type", name)
            if object_id in produced
            or _by_app(self.store.get(self.store.engine, object_id), producer)
        ]
        for object_id in sorted(produced - set(found)):
            if _named(self.store.get(self.store.engine, object_id), name):
                found.append(object_id)
        return found


def _named(found: ObjectView, name: str) -> bool:
    if found.fields.get("type") == name:
        return True
    metadata = found.fields.get("metadata")
    return isinstance(metadata, dict) and metadata.get("output") == name


def _by_app(found: ObjectView, producer: str) -> bool:
    metadata = found.fields.get("metadata")
    return isinstance(metadata, dict) and metadata.get("producer_app") == producer


def _library_object(found: ObjectView, data: Mapping[str, bytes]) -> LibraryObject:
    return LibraryObject(
        object_id=found.object_id,
        item=found.item,
        kind=found.kind,
        title=found.title,
        summary=found.summary,
        fields=dict(found.fields),
        annotations=dict(found.annotations),
        relations=tuple(found.relations),
        data=MappingProxyType(dict(data)),
    )


def _refusal(error: ContextRefused) -> Exception:
    """`tools._host_def` maps `KeyError` to `not_found` and `ValueError` to `invalid_arguments`;
    a refusal keeps its own code by choosing the one that carries it."""
    return (KeyError if error.code == "not_found" else ValueError)(error.message)


def chat_reads(harness: RecordedHarness, store: Store, chat: SessionId) -> Mapping[str, HostRead]:
    """The five `context` reads for one chat (AD-63), over the store the host owns. Each one
    reads the chat record's list, acts through `Harness.set_attached`, and returns what the tool
    hands the model."""

    resolvers = Resolvers(StoreReads(store), excerpt_budget(harness.control.settings_get("agents")))

    def entries() -> tuple[AttachedRef, ...]:
        record = harness.record(chat)
        return () if record is None else record.attached

    def entry(ref: str) -> AttachedRef:
        found = next((item for item in entries() if item.ref == ref), None)
        if found is None:
            raise KeyError(f"{ref!r} is not attached to this chat")
        return found

    async def add(arguments: dict[str, object]) -> Mapping[str, object]:
        ref = str(arguments.get("ref", ""))
        pin = "follow" if arguments.get("pin") == "follow" else "version"
        try:
            found = await asyncio.to_thread(resolvers.add, ref, pin)
        except ContextRefused as error:
            raise _refusal(error) from None
        kept = [item for item in entries() if item.ref != found.ref]
        await harness.set_attached(chat, [*kept, found])
        excerpt = await asyncio.to_thread(resolvers.excerpt, found)
        return {**found.document(), "excerpt": excerpt}

    async def listed(_arguments: dict[str, object]) -> Mapping[str, object]:
        page = await asyncio.to_thread(listing, entries(), resolvers)
        return {
            "entries": [item.document() for item in page.entries],
            "lines": page.lines(),
            "ready": page.ready,
            "pending": page.pending,
        }

    async def refresh(arguments: dict[str, object]) -> Mapping[str, object]:
        ref = str(arguments.get("ref", ""))
        current = entry(ref)
        try:
            moved = await asyncio.to_thread(resolvers.refresh, current)
        except ContextRefused as error:
            raise _refusal(error) from None
        await harness.set_attached(chat, [moved if item.ref == ref else item for item in entries()])
        return moved.document()

    async def drop(arguments: dict[str, object]) -> Mapping[str, object]:
        ref = str(arguments.get("ref", ""))
        kept = [item for item in entries() if item.ref != ref]
        if len(kept) == len(entries()):
            raise KeyError(f"{ref!r} is not attached to this chat")
        await harness.set_attached(chat, kept)
        return {"dropped": ref, "attached": len(kept)}

    async def read(arguments: dict[str, object]) -> Mapping[str, object]:
        ref = str(arguments.get("ref", ""))
        span = arguments.get("range")
        try:
            current = await asyncio.to_thread(resolvers.refresh, entry(ref))
            text = await asyncio.to_thread(
                resolvers.read, current, span if isinstance(span, str) else None
            )
        except ContextRefused as error:
            raise _refusal(error) from None
        return {"ref": ref, "text": text}

    return MappingProxyType(
        {
            "context_add": add,
            "context_list": listed,
            "context_refresh": refresh,
            "context_drop": drop,
            "context_read": read,
        }
    )


class SessionRecorder:
    def __init__(self, store: Store, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))

    def head(self, chat: str) -> str | None:
        found = self.store.head(chat, sessions_ref(chat))
        return None if found is None else found[0]

    def _put(self, draft: Draft, expected: str | None) -> str:
        who, ref = self.store.engine, sessions_ref(str(draft.item))
        commit = self.store.put(who, draft, on=ref, expected_head=expected)
        self.store.merge(who, commit.item, from_ref=ref, into=MAIN, strategy="ff-only")
        return commit.object_id

    def born(self, record: ChatRecord, title: str) -> str:
        """The chat's item, put once; a second call finds it."""
        chat = record.session_id
        found = self.head(chat)
        if found is not None:
            return found
        home = record.config.home
        fields: JsonObject = {
            "session_id": chat,
            "home": {"kind": home.kind, "project_id": home.project_id},
            "created": self.clock().isoformat(),
        }
        title = title or f"Chat {chat[:8]}"
        object_id = self._put(Draft(KIND, item=chat, title=title, fields=fields), None)
        self.store.annotate(self.store.engine, object_id, {"title": title, "turns": 0})
        return object_id

    def turn_ended(self, record: ChatRecord, result: TurnResult | None, title: str = "") -> None:
        object_id = self.born(record, title)
        before = self.store.get(self.store.engine, object_id).annotations
        config = record.config
        tokens = 0 if result is None else result.usage.input_tokens + result.usage.output_tokens
        values: JsonObject = {
            "last_turn_at": self.clock().isoformat(),
            "turns": _int(before.get("turns")) + 1,
            "tokens": _int(before.get("tokens")) + tokens,
            "models": _list(before.get("models"), config.model),
            "profiles": _list(before.get("profiles"), config.profile),
            "packs": list(config.packs),
            "surface_digest": record.digests[-1] if record.digests else None,
        }
        self.store.annotate(self.store.engine, object_id, values)
        if record.attached:
            self.attached(record.session_id, record.attached)

    def attached(self, chat: str, entries: Sequence[AttachedRef]) -> str | None:
        """Mirror the chat record's attached references onto its item (AD-63, Library AD-21):
        one `item:<object_id>` tag and one `mentions` edge per resolved reference. Idempotent,
        so an attach and the turn end after it both land the same mirror. None when the chat has
        no item yet."""
        head = self.head(chat)
        if head is None:
            return None
        current = self.store.get(self.store.engine, head).annotations.get("tags")
        tags = [str(tag) for tag in current] if isinstance(current, list) else []
        for item in entries:
            tag = f"item:{item.object_id}"
            if tag not in tags:
                tags.append(tag)
            with contextlib.suppress(LibraryRefused):
                self.store.relate(self.store.engine, head, MENTIONS, item.object_id)
        self.store.annotate(self.store.engine, head, cast("JsonObject", {"tags": sorted(tags)}))
        return head

    def exported(self, chat: str, transcript: bytes) -> str:
        """A new version holding `transcript`, carrying the head's annotations forward."""
        head = self.head(chat)
        if head is None:
            raise LibraryRefused("not_found", f"no session item for chat {chat}")
        view = self.store.get(self.store.engine, head)
        draft = Draft(
            KIND,
            item=chat,
            title=view.title,
            summary=view.summary,
            fields=view.fields,
            blobs={"transcript": transcript},
        )
        object_id = self._put(draft, head)
        carried = {k: v for k, v in view.annotations.items() if k not in {"author", "created"}}
        self.store.annotate(
            self.store.engine, object_id, {**carried, "exported_at": self.clock().isoformat()}
        )
        return object_id

    def idle_due(self, chat: str) -> bool:
        """True when the chat's last turn is older than `IDLE` and came after its last export."""
        head = self.head(chat)
        if head is None:
            return False
        notes = self.store.get(self.store.engine, head).annotations
        last, exported = notes.get("last_turn_at"), notes.get("exported_at")
        if not isinstance(last, str):
            return False
        if isinstance(exported, str) and exported >= last:
            return False
        return self.clock() - datetime.fromisoformat(last) > IDLE

    async def export(self, chat: SessionId, exporter: Exporter) -> str:
        folder = await exporter(chat)
        path = folder / TRANSCRIPT
        data = await asyncio.to_thread(path.read_bytes) if path.is_file() else b""
        return await asyncio.to_thread(self.exported, chat, data)


class RecordedHarness(Harness):
    """The harness, telling `recorder` of every chat's birth, turn ends and close."""

    def __init__(
        self, deps: ChatDeps, watch: PlanWatch, host_reads: Mapping[str, HostRead] | None = None
    ) -> None:
        super().__init__(deps, watch, host_reads)
        self.recorder: SessionRecorder | None = None
        self.turn_end_ms: list[float] = []
        """What the recorder added at each turn end, for the perf trail."""
        self._titles: dict[SessionId, str] = {}
        self._watching: set[asyncio.Task[None]] = set()

    @override
    @classmethod
    async def open(
        cls,
        home: QmxHome,
        *,
        control: ControlService,
        test: TestMode | None = None,
        host_reads: Mapping[str, HostRead] | None = None,
    ) -> RecordedHarness:
        opened = await super().open(home, control=control, test=test, host_reads=host_reads)
        return cast("RecordedHarness", opened)

    def record_into(self, recorder: SessionRecorder) -> None:
        self.recorder = recorder

    def _record(self, chat: SessionId) -> ChatRecord | None:
        found = self._chats.get(chat)
        return found.record if found is not None else read_record(self.home, chat)

    def record(self, chat: SessionId) -> ChatRecord | None:
        """The chat's record as this process holds it, for the reads that act on the chat."""
        return self._record(chat)

    @override
    def context_reads(self, chat: SessionId) -> Mapping[str, HostRead]:
        """The `context` toolset this host serves: the store's resolvers, bound to `chat`."""
        recorder = self.recorder
        if recorder is None:
            return MappingProxyType({})
        return chat_reads(self, recorder.store, chat)

    @override
    async def set_attached(self, chat: SessionId, refs: Sequence[AttachedRef]) -> None:
        """Attach through the harness, then mirror the list onto the chat's session item."""
        await super().set_attached(chat, refs)
        recorder = self.recorder
        if recorder is None:
            return
        try:
            await asyncio.to_thread(recorder.attached, chat, tuple(refs))
        except RECORDING_FAILED as error:
            _skipped("context mirror", error)

    @override
    async def start_chat(self, spec: NewChat) -> SessionId:
        chat = await super().start_chat(spec)
        record = self._record(chat)
        if self.recorder is not None and record is not None:
            self._titles[chat] = spec.title
            try:
                await asyncio.to_thread(self.recorder.born, record, spec.title)
            except RECORDING_FAILED as error:
                _skipped("item", error)
        return chat

    def _watch(self, chat: SessionId, handle: TurnHandle) -> None:
        recorder = self.recorder
        if recorder is None:
            return

        async def ended() -> None:
            result = await handle.result()
            record = self._record(chat)
            if record is None:
                return
            began = time.perf_counter()
            title = self._titles.get(chat, "")
            try:
                await asyncio.to_thread(recorder.turn_ended, record, result, title)
            except RECORDING_FAILED as error:
                _skipped("turn end", error)
                return
            self.turn_end_ms.append((time.perf_counter() - began) * 1000)

        task = asyncio.create_task(ended())
        self._watching.add(task)
        task.add_done_callback(self._watching.discard)

    @override
    async def run_turn(self, chat: SessionId, prompt: Prompt, *, priority: int = 0) -> TurnHandle:
        handle = await super().run_turn(chat, prompt, priority=priority)
        self._watch(chat, handle)
        return handle

    @override
    async def send(self, chat: SessionId, prompt: Prompt, *, priority: int = 0) -> None:
        handle = TurnHandle(prompt.text)
        await self._dispatch(chat, prompt, handle, priority)
        self._watch(chat, handle)

    @override
    async def close_chat(self, chat: SessionId) -> None:
        await super().close_chat(chat)
        if self.recorder is not None and self.recorder.head(chat) is not None:
            try:
                await self.recorder.export(chat, self.export)
            except RECORDING_FAILED as error:
                _skipped("export", error)

    async def export_idle(self) -> list[SessionId]:
        """Export every chat idle past `IDLE` since its last export; the chats exported."""
        recorder = self.recorder
        if recorder is None:
            return []
        done: list[SessionId] = []
        for record in await asyncio.to_thread(list_records, self.home):
            chat = record.session_id
            if await asyncio.to_thread(recorder.idle_due, chat):
                await recorder.export(chat, self.export)
                done.append(chat)
        return done

    async def idle_exports(self) -> None:
        """`export_idle` every `IDLE_TICK_S` until cancelled. A failed pass is retried next
        tick."""
        while True:
            await asyncio.sleep(IDLE_TICK_S)
            try:
                await self.export_idle()
            except RECORDING_FAILED as error:
                _skipped("daily export", error)

    @override
    async def close(self) -> None:
        for task in list(self._watching):
            task.cancel()
        await super().close()
