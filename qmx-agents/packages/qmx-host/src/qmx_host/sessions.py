"""The session recorder (Library AD-21): every chat the harness creates gets one `session` item.

The host writes it with its own principal `engine:<store>` on `refs/sessions/<session_id>` and
lands each version on `main`. The item id is the session id, so a host restarted mid-session
keeps writing the same item. Identity is `session_id`, `home` and `created`. A turn end only
annotates the head (title, last turn time, turn and token counts, models, profiles, packs and the
surface digest, engine AD-62), so no version is minted per turn (AD-2). A close by its owner, or a
chat idle past `IDLE`, puts a new version whose `transcript` blob is the harness's redacted export
(engine AD-37). The live transcript stays the CLI's JSONL; the Library copy is never read back.

`RecordedHarness` is the harness the host serves. It tells the recorder of each chat's birth,
each turn's end and each close. A hook sink cannot do it: only Background and Child chats may
name one, and engine chats already name `engine`.
"""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast, override

from pydantic import JsonValue
from qma.harness import Harness, NewChat, QmxHome, SessionId, TurnHandle, TurnResult
from qma.harness.chat import ChatDeps, Prompt
from qma.harness.harness import PlanWatch
from qma.harness.home import ChatRecord, list_records, read_record
from qma.harness.tools import HostRead
from qmx_library.port import Draft, JsonObject, LibraryRefused
from qmx_library.principal import MAIN, sessions_ref
from qmx_library.store import Store

if TYPE_CHECKING:
    from qma.harness.launch import TestMode
    from qmx_control.service import ControlService

KIND: Final = "session"
IDLE: Final = timedelta(hours=24)
"""Claude's default: a chat idle this long gets its daily export."""
IDLE_TICK_S: Final = 3600.0
TRANSCRIPT: Final = "transcript.jsonl"

type Exporter = Callable[[SessionId], Awaitable[Path]]


def _list(value: JsonValue, add: str) -> list[JsonValue]:
    found = list(value) if isinstance(value, list) else []
    return found if add in found else [*found, add]


def _int(value: JsonValue) -> int:
    return value if isinstance(value, int) else 0


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

    @override
    async def start_chat(self, spec: NewChat) -> SessionId:
        chat = await super().start_chat(spec)
        record = self._record(chat)
        if self.recorder is not None and record is not None:
            self._titles[chat] = spec.title
            await asyncio.to_thread(self.recorder.born, record, spec.title)
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
            await asyncio.to_thread(recorder.turn_ended, record, result, title)
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
            await self.recorder.export(chat, self.export)

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
            except (OSError, LibraryRefused) as error:
                print(f"session export skipped: {type(error).__name__}: {error}", file=sys.stderr)

    @override
    async def close(self) -> None:
        for task in list(self._watching):
            task.cancel()
        await super().close()
