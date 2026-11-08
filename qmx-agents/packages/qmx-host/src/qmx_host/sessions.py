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
from typing import TYPE_CHECKING, Final, Protocol, cast, override

from pydantic import JsonValue
from qma.harness import Harness, NewChat, QmxHome, SessionId, TurnHandle, TurnResult, packs
from qma.harness.chat import ChatDeps, Prompt
from qma.harness.harness import PlanWatch
from qma.harness.home import ChatRecord, list_records, read_record
from qma.harness.packs import PackSource
from qma.harness.surface import MEMORY, excerpt_budget
from qma.harness.tools import HostRead
from qmx_control.context import (
    AttachedRef,
    ContextRefused,
    LibraryHit,
    LibraryObject,
    MemoryRowHit,
    Resolvers,
    listing,
)
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectView
from qmx_library.principal import MAIN, Principal, drafts_ref, sessions_ref, state_ref
from qmx_library.store import Store
from qmx_memory.engine import RecallEngine
from qmx_memory.retain import RetainWorker
from qmx_memory.rows import SCOPES

if TYPE_CHECKING:
    from qma.harness.demo_only import AccountWorlds
    from qma.harness.launch import TestMode
    from qmx_control.service import ControlService
    from qmx_tools.service import MarketPort

KIND: Final = "session"
MINI_APP: Final = "mini-app"
PUBLISHER: Final = Principal.parse("operator")
"""Who lands a published pack: the operator, whose card click the publish is."""
"""Where a publish writes its `mini-app` item before landing it on `main`."""
BUNDLE: Final = "bundle.tar"
IDLE: Final = timedelta(hours=24)
"""Claude's default: a chat idle this long gets its daily export."""
IDLE_TICK_S: Final = 3600.0
TRANSCRIPT: Final = "transcript.jsonl"
MENTIONS: Final = "mentions"
"""The edge from a session item to each object it attached (Library AD-14's vocabulary)."""
HUB_HOME: Final = "hub"
"""The home scope the copilot's own digest rows land in (§11.1's `refs/memory/home/<home>`)."""
PAGE: Final = 1000
"""One page of the control service's session log, the harness's own read size."""
_DIGESTS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "turn-end": "turn_ended",
        "compaction": "compacted",
        "idle": "idle",
        "close": "closed",
    }
)
"""The retain worker's verb for each trigger (§28.6's four)."""

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


class StoreMemory:
    """`qmx_control.context.MemoryReads` over the host's memory engine (MEM): an `@memory`
    question becomes a recall, and each row comes back with its tag and the objects it cites."""

    def __init__(self, engine: RecallEngine) -> None:
        self.engine = engine

    def memory(self, question: str, limit: int = 10) -> list[MemoryRowHit]:
        found = self.engine.recall(question, SCOPES, 4_000)
        return [
            MemoryRowHit(
                hit.row_id,
                hit.text,
                hit.tag,
                hit.refs,
                str(hit.provenance.get("when_to_use", "")),
                bool(hit.provenance.get("tainted")),
            )
            for hit in found[:limit]
        ]


def memory_reads(engine: RecallEngine, chat: SessionId) -> Mapping[str, HostRead]:
    """The five `memory` reads for one chat (AD-18, AD-27). Each answers from the engine the host
    installed, so a store the host cannot open serves none of them."""

    async def recall(arguments: dict[str, object]) -> Mapping[str, object]:
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("a recall needs a query")
        now = _moment(arguments.get("as_of"))
        found = await asyncio.to_thread(
            engine.recall,
            query,
            SCOPES,
            _whole(arguments.get("budget_tokens"), 2_000),
            tuple(_strings(arguments.get("tags"))),
            now=now,
            regime=tuple(_strings(arguments.get("regime"))),
        )
        return {
            "rows": [
                {
                    "row_id": hit.row_id,
                    "tag": hit.tag,
                    "text": hit.text,
                    "score": round(hit.score, 4),
                    "refs": list(hit.refs),
                    **{k: v for k, v in hit.provenance.items() if k not in {"tag", "when_to_use"}},
                }
                for hit in found
            ],
            "count": len(found),
        }

    async def note(arguments: dict[str, object]) -> Mapping[str, object]:
        row = {
            key: arguments[key]
            for key in ("tag", "content", "when_to_use", "refs", "intent_key", "regime", "valid_to")
            if arguments.get(key) not in (None, "", [])
        }
        if "content" not in row:
            raise ValueError("a note needs its content")
        written = await asyncio.to_thread(engine.write, "home", "copilot", row)
        await remember(engine, written)
        return {"row_id": written.object_id, "tag": written.tag, "scope": written.scope}

    async def check(arguments: dict[str, object]) -> Mapping[str, object]:
        key = str(arguments.get("intent_key", "")).strip()
        query = str(arguments.get("query", "")).strip()
        if not key and not query:
            raise ValueError("a check needs an intent_key or a query")
        built = await asyncio.to_thread(engine.check_built, key) if key else []
        dead = await asyncio.to_thread(engine.check_dead_end, key or query)
        return {
            "built": built,
            "dead_ends": [
                {"row_id": hit.row_id, "text": hit.text, "refs": list(hit.refs)} for hit in dead
            ],
        }

    async def forget(arguments: dict[str, object]) -> Mapping[str, object]:
        rows = tuple(_strings(arguments.get("row_ids")))
        if not rows:
            raise ValueError("forget needs the row ids recall returned")
        forgotten = await asyncio.to_thread(engine.forget, rows)
        return {"forgotten": forgotten, "rows": list(rows)}

    async def rebuild(arguments: dict[str, object]) -> Mapping[str, object]:
        scope = str(arguments.get("scope", "all"))
        op = await asyncio.to_thread(engine.rebuild, scope)
        return {"scope": scope, "operation": op}

    _ = chat
    return MappingProxyType(
        {
            "memory_recall": recall,
            "memory_note": note,
            "memory_check": check,
            "memory_forget": forget,
            "memory_rebuild": rebuild,
        }
    )


async def remember(engine: RecallEngine, row: object) -> None:
    """Re-render the memory snapshot slot after a write, so the next launch reads it (AD-18)."""
    del row
    await asyncio.to_thread(write_snapshot, engine)


HOME_KINDS: Final[tuple[str, ...]] = ("general", "lab", "portfolio", "library", "app", "agent")
"""Every home kind a chat can be born in (AD-35), so every launch finds its slot."""

SNAPSHOT_TOKENS: Final = 4_000
"""The snapshot's own bound, in tokens: `[agents] slot_budgets` leaves it unset because it is
bounded where it is built (AD-18's sizes are lines; this is what a launch can afford)."""


def write_snapshot(engine: RecallEngine, root: Path | None = None) -> list[Path]:
    """Render the memory snapshot slot from the engine's rows, one file per home kind, at
    `<home>/memory/<kind>.md`: the slot `qma.harness.surface.HomeSlots` reads (AD-18). Written
    after every retain, every forget and at start, so a launch is at most one turn behind."""
    frozen = engine.snapshot(("operator", "home"), SNAPSHOT_TOKENS)
    folder = (root or engine.home) / MEMORY
    folder.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind in HOME_KINDS:
        path = folder / f"{kind}.md"
        path.write_text(frozen.text + "\n" if frozen.text else "", encoding="utf-8")
        written.append(path)
    return written


def _moment(value: object) -> datetime | None:
    """An ISO date or instant, as `@memory` and `memory_recall` take one."""
    if not isinstance(value, str) or not value.strip():
        return None
    found = datetime.fromisoformat(value.strip())
    return found if found.tzinfo is not None else found.replace(tzinfo=UTC)


def _table(value: object) -> Mapping[str, object]:
    """A JSON document as a table, or an empty one: the control service answers `JsonValue`."""
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _whole(value: object, default: int) -> int:
    return value if isinstance(value, int) and value > 0 else default


def _strings(value: object) -> list[str]:
    found = cast("Sequence[object]", value) if isinstance(value, list | tuple) else ()
    return [str(one) for one in found]


def published_packs(store: Store) -> tuple[PackSource, ...]:
    """Every `mini-app` on `main`, as the pack tree its `bundle.tar` blob holds."""
    found: list[PackSource] = []
    for item, object_id in store.heads_on(MAIN):
        view = store.get(store.engine, object_id)
        blob = view.blobs.get(BUNDLE)
        if view.kind != MINI_APP or blob is None:
            continue
        found.append(packs.source(object_id, item, {BUNDLE: store.read_blob(blob.blob_id)}))
    return tuple(found)


def materialise_packs(home: QmxHome, store: Store) -> tuple[str, ...]:
    """Write every published pack's view under this home's plugin folder, so a chat's surface
    loads it (AD-55). A second start rewrites the same views, so it converges."""
    return tuple(view.name for view in packs.materialise(home.packs_dir, published_packs(store)))


class Landed(Protocol):
    """What a publish hands the Library: `qmx_apps.road.Pack`, typed here by its shape so the
    host keeps no dependency on the apps package."""

    @property
    def app_id(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def definition_hash(self) -> str: ...

    @property
    def operations(self) -> Sequence[str]: ...

    @property
    def bundle(self) -> bytes: ...


class PackLanding:
    """`qmx_apps.road.PackSink` over the host's store. A publish is the operator's own card
    click, so the operator writes its `mini-app` item on `refs/drafts/<id>` and merges it onto
    `main`, then the published packs are materialised, so the next chat loads the new view
    without a restart."""

    def __init__(self, store: Store, home: QmxHome) -> None:
        self.store = store
        self.home = home

    def __call__(self, pack: Landed) -> str:
        ref = drafts_ref(pack.app_id)
        found = self.store.head(pack.app_id, ref)
        commit = self.store.put(
            PUBLISHER,
            Draft(
                MINI_APP,
                item=pack.app_id,
                title=pack.app_id,
                summary=f"{pack.version} serves {len(pack.operations)} operations",
                fields={
                    "version": pack.version,
                    "definition_hash": pack.definition_hash,
                    "operations": list(pack.operations),
                },
                blobs={BUNDLE: pack.bundle},
            ),
            on=ref,
            expected_head=None if found is None else found[0],
        )
        merged = self.store.merge(
            PUBLISHER, pack.app_id, from_ref=ref, into=MAIN, strategy="ff-only"
        )
        if merged.outcome == "conflict":
            raise LibraryRefused(
                "stale_head", f"{pack.app_id} on main moved past its draft; publish again"
            )
        try:
            materialise_packs(self.home, self.store)
        except (OSError, ValueError, LibraryRefused) as error:
            _skipped("pack views", error)
        return commit.object_id


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
    hands the model. `@memory` resolves through the host's memory engine when one is installed."""
    memory = getattr(harness, "memory", None)
    resolvers = Resolvers(
        StoreReads(store),
        excerpt_budget(harness.control.settings_get("agents")),
        None if memory is None else StoreMemory(memory),
    )

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
        self.memory: RecallEngine | None = None
        self.retainer: RetainWorker | None = None
        self.turn_end_ms: list[float] = []
        """What the recorder added at each turn end, for the perf trail."""
        self.memory_ms: list[float] = []
        """What one digest cost at each turn end, for the perf block (P-MEM's 30 s line)."""
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
        market: MarketPort | None = None,
        accounts: AccountWorlds | None = None,
    ) -> RecordedHarness:
        opened = await super().open(
            home,
            control=control,
            test=test,
            host_reads=host_reads,
            market=market,
            accounts=accounts,
        )
        return cast("RecordedHarness", opened)

    def record_into(self, recorder: SessionRecorder) -> None:
        """Take the recorder, then the two things a start owes the mini apps: their published
        packs materialised as views, and the road's sink that lands a publish in the Library."""
        self.recorder = recorder
        store = recorder.store
        try:
            materialise_packs(self.home, store)
        except (OSError, ValueError, LibraryRefused) as error:
            _skipped("pack views", error)
        try:
            self._deps.control.app_runtime().attach_packs(PackLanding(store, self.home))
        except (OSError, ValueError, LibraryRefused) as error:
            _skipped("pack sink", error)

    def remember_into(self, engine: RecallEngine) -> None:
        """The host's memory engine, and the retain worker that feeds it (AD-18, §28.6)."""
        self.memory = engine
        self.retainer = RetainWorker(
            engine,
            blocks=self._blocks,
            session_item=self._session_item,
            home=HUB_HOME,
        )

    def _blocks(self, chat: str) -> Sequence[Mapping[str, object]]:
        """The chat's recorded blocks, oldest first, read from the control service's session log:
        the same record `memory_note` writes into and the export holds at close."""
        found: list[Mapping[str, object]] = []
        after = 0
        while True:
            page = self.control.events("sessions", after, chat, PAGE)
            for event in page:
                record = _table(event)
                data = _table(record.get("data"))
                if data.get("type") != "block":
                    continue
                block = _table(data.get("block"))
                if block:
                    found.append(block)
            if len(page) < PAGE:
                return found
            after = _whole(_table(page[-1]).get("id"), 0)

    def _session_item(self, chat: str) -> str | None:
        recorder = self.recorder
        return None if recorder is None else recorder.head(chat)

    def _record(self, chat: SessionId) -> ChatRecord | None:
        found = self._chats.get(chat)
        return found.record if found is not None else read_record(self.home, chat)

    def record(self, chat: SessionId) -> ChatRecord | None:
        """The chat's record as this process holds it, for the reads that act on the chat."""
        return self._record(chat)

    @override
    def context_reads(self, chat: SessionId) -> Mapping[str, HostRead]:
        """The `context` and `memory` toolsets this host serves, bound to `chat`."""
        recorder = self.recorder
        if recorder is None:
            return MappingProxyType({})
        found = dict(chat_reads(self, recorder.store, chat))
        memory = self.memory
        if memory is not None:
            found.update(memory_reads(memory, chat))
        return MappingProxyType(found)

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
            await self._retain(chat, began)

        task = asyncio.create_task(ended())
        self._watching.add(task)
        task.add_done_callback(self._watching.discard)

    async def _retain(self, chat: SessionId, began: float, event: str = "turn-end") -> None:
        """Feed the retain worker and re-render the snapshot slot. A memory write never fails a
        chat: it is reported and the turn stands."""
        retainer, engine = self.retainer, self.memory
        if retainer is None or engine is None:
            return
        try:
            await asyncio.to_thread(getattr(retainer, _DIGESTS[event]), chat)
            await asyncio.to_thread(write_snapshot, engine)
        except (OSError, ValueError, LibraryRefused) as error:
            _skipped("digest", error)
            return
        self.memory_ms.append((time.perf_counter() - began) * 1000)

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
        await self._retain(chat, time.perf_counter(), "close")

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
