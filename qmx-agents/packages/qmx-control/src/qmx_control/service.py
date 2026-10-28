"""Persistent platform operations, independent of either transport."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import sqlite3
import threading
import tomllib
import uuid
from collections.abc import AsyncIterator, Callable, Generator, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Final, Literal, NoReturn, Protocol, cast
from urllib.parse import urlsplit

import keyring
import tomli_w
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from qmx_apps.backup import BackupSettings, backup, restore
from qmx_apps.backup_schedule import BackupSchedule
from qmx_apps.docker import DockerSupervisor
from qmx_apps.errors import AppError
from qmx_apps.manifest import Trust
from qmx_apps.road.models import Stage
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_broker.models import Broker, BrokerSettings
from qmx_broker.sandbox import demo_refusal
from qmx_broker.service import read_proposals
from qmx_home import Layout
from qmx_home.backup.plan import APP_KEYS, PlanRefused
from qmx_home.backup.plan import parse as parse_backup_plan
from qmx_home.versions import open_sqlite, too_new
from qmx_library.cards import SERIES_PREFIX
from qmx_library.port import LibraryRefused
from qmx_library.store import Store

from qmx_control.backup import weekly_backup
from qmx_control.cache import read_cache
from qmx_control.catalog import operation
from qmx_control.library import OPERATOR as LIBRARY_OPERATOR
from qmx_control.library import Library, refused
from qmx_control.models import ControlError as ControlError  # noqa: PLC0414 - public re-export
from qmx_control.models import DelegateCompletion as DelegateCompletion  # noqa: PLC0414
from qmx_control.models import Document, MemoKey
from qmx_control.models import LibraryInput as LibraryInput  # noqa: PLC0414 - public re-export
from qmx_control.runs import RunIndex

type SettingsSection = Literal[
    "providers",
    "mcp_servers",
    "budgets",
    "memory_provider",
    "backup",
    "brokers",
    "connections",
    "claude",
    "environment",
    "agents",
    "engine",
    "roles",
    "rules",
    "observers",
    "telemetry",
    "data",
]
type SettingsParser = Callable[[Document, Document], Document]
"""(values written, section stored now) -> the section to store."""
HOST_SECTIONS: frozenset[SettingsSection] = frozenset({"claude", "environment"})
"""Sections only a host that registers a parser for them can write."""
ENGINE = "an attached workflow engine"
type EventTopic = Literal["runs", "jobs", "sessions", "apps", "library", "settings", "aggregates"]
EVAL_TASK: Final = "eval-task"
"""The tag of a copilot eval battery task (engine AD-66). A new failure becomes a task with one
`library_save` carrying it: content `{id, prompt, grade, source}`, `grade` either
`{by: code, checks}` or `{by: judge, rubric}`."""
EVAL_RUN: Final = "eval-run"
"""The tag of a battery result, the item a change card reads."""
SLOT_KINDS: Final = frozenset({"persona", "methodology", "skill"})
"""The Library kinds whose drafts the battery tests before he publishes them."""
OBSERVERS: Final = "observers.json"
"""The operator's observer tokens under the home. A row keeps a token's hash, never the token."""
OBSERVER_PREFIX: Final = "obs-"
OBSERVER_TTL_DAYS: Final = 30
"""Appendix D: an observer token expires after 30 days (Claude's default, a Settings value)."""
OBSERVER_REF: Final = "refs/agents/{observer}/diagnosis"
"""Where an outside agent's diagnosis note says it belongs: the observer's own ref (AD-69)."""
NOTE_TITLE: Final = "an outside agent left a diagnosis"
"""How the inbox names a diagnosis note. `info` never enters the engine's trouble inbox, so the
note is a control row the inbox lists beside the engine's items."""
CONTROL_SCHEMA: Final = (
    "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS blocks (session_id TEXT NOT NULL, seq INTEGER NOT NULL,"
    " data TEXT NOT NULL, PRIMARY KEY(session_id, seq))",
    "CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT,"
    " topic TEXT NOT NULL, subject TEXT NOT NULL, data TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS delegate_completions (handle TEXT PRIMARY KEY,"
    " parent_session TEXT NOT NULL, data TEXT NOT NULL, delivered_at TEXT)",
    "CREATE INDEX IF NOT EXISTS delegate_pending"
    " ON delegate_completions(parent_session, delivered_at)",
    "CREATE TABLE IF NOT EXISTS operator_cursor (name TEXT PRIMARY KEY,"
    " position INTEGER NOT NULL, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS observer_notes (id TEXT PRIMARY KEY,"
    " observer TEXT NOT NULL, ref TEXT NOT NULL, body TEXT NOT NULL, at TEXT NOT NULL)",
)
"""`control.db` at version 1 (design 62 B1). A later version adds a step; it never edits these."""
LOGS: Final = "logs"
LOG = logging.getLogger(__name__)
LOOK: Final = "last_look"
"""The operator's cursor row. Its stored name carries the store it counts in, `last_look:<store>`;
a row named `last_look` alone was written before the tag and counted in another file."""
"""The home's log folder: heartbeat, connection, feed and telemetry reads live here as JSON."""


def model_subject(current: str | None, new: str) -> str:
    """The battery subject of switching the copilot's default model from `current` to `new`."""
    return f"copilot-model:{current or 'unset'}->{new}"


def draft_subject(artifact_id: str) -> str:
    """The battery subject of a persona, methodology or skill draft."""
    return f"draft:{artifact_id}"


def eval_run_input(result: Document) -> LibraryInput:
    """A battery result as the Library item its change card reads."""
    return LibraryInput(
        title=f"Eval battery: {result['subject']}"[:200],
        kind=EVAL_RUN,
        content=result,
        tags=[EVAL_RUN],
        source="ev-copilot-eval-battery",
    )


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    origin: str = Field(default="copilot", min_length=1)
    parent_id: str | None = None


class SessionBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "user",
        "text",
        "plan",
        "agents",
        "tool",
        "changed",
        "artifact",
        "table",
        "entity",
        "question",
        "permission",
        "panel",
        "handoff",
        "needs_you",
    ]
    content: Document


class NoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=10_000)


def _document(value: str) -> Document:
    return cast(Document, json.loads(value))


def app_workflow_id(app_id: str) -> str:
    """The workflow that runs an app's scheduled job. It lives beside the app until packs hold
    their own workflows (PACK)."""
    return f"{app_id}-schedule"


def app_workflow(item: str, app_id: str, job: str) -> Document:
    """A trigger and one `app_op` node that runs `job` in the app's supervised process."""

    def node(node_id: str, name: str, kind: str, x: int) -> JsonValue:
        return {"id": node_id, "name": name, "type": kind, "typeVersion": 1, "position": [x, 0]}

    run: Document = {"parameters": {"app": app_id, "job": job}}
    edge: JsonValue = {"node": "Run job", "port": "in", "map": "one"}
    return {
        "schema": "qmx.workflow/1",
        "id": item,
        "name": f"{app_id} schedule",
        "nodes": [
            node("t", "Start", "trigger", 0),
            cast(Document, node("a", "Run job", "app_op", 200)) | run,
        ],
        "connections": {"Start": {"main": [[edge]]}},
    }


RULE_LISTS = ("always_allow", "never_allow")
RULE_SOURCES = frozenset({"you", "imported", "suggested"})
RULE_PATTERN = re.compile(r"\s*[^\s()]+\s*(?:\(.*\))?\s*", re.DOTALL)
"""`Tool` or `Tool(glob)`, the shape the harness guard reads (engine AD-43, AD-54)."""


def _rule_lists(values: Document) -> Document:
    """`[rules]`: his always-allow and never-allow lists. Each row is a pattern string or a
    `{pattern, source, added_at}` table, stored as the table; `source` defaults to `you`. The
    guard lets no row lift its floor, so a row is checked for shape only."""
    unknown = set(values) - set(RULE_LISTS)
    if unknown:
        raise ControlError("invalid_rules", f"Rules hold only {', '.join(RULE_LISTS)}.")
    stored: Document = {}
    for name in RULE_LISTS:
        rows = values.get(name, [])
        if not isinstance(rows, list):
            raise ControlError("invalid_rules", f"{name} must be a list.")
        kept: list[JsonValue] = []
        for row in rows:
            table = {"pattern": row} if isinstance(row, str) else row
            if not isinstance(table, dict) or set(table) - {"pattern", "source", "added_at"}:
                raise ControlError("invalid_rules", "A rule is a pattern, source and added_at.")
            pattern, source = table.get("pattern"), table.get("source", "you")
            if not isinstance(pattern, str) or not RULE_PATTERN.fullmatch(pattern):
                raise ControlError("invalid_rules", f"{pattern!r} is not Tool or Tool(pattern).")
            if source not in RULE_SOURCES:
                raise ControlError("invalid_rules", "A source is you, imported or suggested.")
            kept.append({**table, "pattern": pattern.strip(), "source": source})
        stored[name] = kept
    return stored


HOLDOUT_MONTH: Final = re.compile(r"(19[7-9]\d|[2-9]\d{3})-(0[1-9]|1[0-2])")


def _with_holdout(values: Document) -> Document:
    """`[data]` with its switch written out, as the door reads it: off unless set, except that
    a section from before the switch, naming only `seal_boundary_ns`, is on."""
    return {"holdout": "seal_boundary_ns" in values, **values}


def _data_settings(values: Document) -> Document:
    """`[data]`: the market-data door's settings. The holdout is his choice per study and off
    by default (ruling 137); when on, `holdout_boundary` is the month it starts, 1970-01 or
    later, and `holdout_months` the window a new study takes. The door's other keys pass
    through."""
    values = _with_holdout(values)
    holdout = values["holdout"]
    if not isinstance(holdout, bool):
        raise ControlError("invalid_settings", "data.holdout is true or false.")
    boundary = values.get("holdout_boundary")
    if boundary is not None and not (
        isinstance(boundary, str) and HOLDOUT_MONTH.fullmatch(boundary)
    ):
        raise ControlError(
            "invalid_settings",
            "data.holdout_boundary is a month written YYYY-MM, 1970-01 or later, such as "
            f"2025-01; got {boundary!r}.",
        )
    months = values.get("holdout_months", 12)
    if isinstance(months, bool) or not isinstance(months, int) or months < 1:
        raise ControlError(
            "invalid_settings", f"data.holdout_months is a whole number, 1 or more; got {months!r}."
        )
    if holdout and boundary is None and "seal_boundary_ns" not in values:
        raise ControlError(
            "invalid_settings",
            "data.holdout is on, so it needs holdout_boundary, the month it starts.",
        )
    return values


BACKUP_PLAN_KEYS: Final = frozenset({"quick_undo", "targets", "leave_out", "drill", "keys"})
"""The keys of `[backup]` his copies read (`qmx_home.backup.plan`); `APP_KEYS` are the rest."""


def _check_backup_plan(values: Document, layout: Layout) -> None:
    """Refuse a `[backup]` section his copies cannot use, naming the row, before it is saved."""
    unknown = sorted(set(values) - BACKUP_PLAN_KEYS - APP_KEYS)
    if unknown:
        raise ControlError(
            "invalid_backup_settings",
            f"[backup] has {', '.join(unknown)}, which QMX does not know; use "
            f"{', '.join(sorted(BACKUP_PLAN_KEYS | APP_KEYS))}",
        )
    try:
        parse_backup_plan(values, layout)
    except PlanRefused as refused:
        raise ControlError("invalid_backup_settings", str(refused)) from refused


def _volume_keys(values: Document) -> Document:
    """The keys of `[backup]` the mini apps' volume backup reads."""
    return {key: value for key, value in values.items() if key in APP_KEYS - {"repository"}}


def _no_secrets(value: JsonValue) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in {"key", "apikey", "token", "password", "secret", "clientkey"}:
                raise ControlError(
                    "secret_ref_required",
                    "Store secrets in Credential Manager; use credential_ref.",
                )
            _no_secrets(item)
    elif isinstance(value, list):
        for item in value:
            _no_secrets(item)


LEGACY_PROVIDER_KEYS: Final = frozenset({"id", "name", "adapter", "exchange", "connections"})
LEGACY_CONNECTION_KEYS: Final = frozenset(
    {"id", "credential_ref", "environment", "accounts", "protocol_path", "protocol_tag"}
)
LEGACY_ACCOUNT_KEYS: Final = frozenset(
    {"id", "currency", "leverage", "permissions", "credential_ref"}
)


def legacy_brokers(stored: Document) -> Document:
    """The old `[brokers]` shape, read from the one `[connections]` list."""
    if "brokers" in stored:
        return cast(Document, stored.get("brokers", {}))
    rows = stored.get("connections")
    if not isinstance(rows, list):
        return {}
    try:
        settings = BrokerSettings.model_validate({"connections": rows})
    except ValueError:
        return {}
    return {
        "brokers": [
            {
                **{
                    key: value
                    for key, value in provider.model_dump(mode="json", exclude_none=True).items()
                    if key in LEGACY_PROVIDER_KEYS
                },
                "connections": [
                    {
                        **{
                            key: value
                            for key, value in connection.model_dump(
                                mode="json", exclude_none=True
                            ).items()
                            if key in LEGACY_CONNECTION_KEYS
                        },
                        "accounts": [
                            {
                                key: value
                                for key, value in account.model_dump(
                                    mode="json", exclude_none=True
                                ).items()
                                if key in LEGACY_ACCOUNT_KEYS
                            }
                            for account in connection.accounts
                        ],
                    }
                    for connection in provider.connections
                ],
            }
            for provider in settings.providers
        ]
    }


type DemoRow = tuple[str, str, str]
"""A CCXT demo row by provider id, connection id and exchange."""


def _demo_rows(providers: Sequence[Broker]) -> list[DemoRow]:
    """The CCXT demo rows of `providers`, in their order."""
    return [
        (provider.id, connection.id, provider.exchange)
        for provider in providers
        if provider.adapter == "ccxt"
        for connection in provider.connections
        if connection.environment == "demo"
    ]


def _stored_demo_rows(stored: Document) -> set[DemoRow]:
    """The CCXT demo rows `settings.toml` already holds. Each provider is parsed on its own, so a
    row saved before the demo check still counts as saved and never blocks an edit to another
    connection."""
    legacy = stored.get("brokers")
    raw = stored.get("connections") or (legacy.get("brokers") if isinstance(legacy, dict) else [])
    providers: list[Broker] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            providers.append(Broker.model_validate(item))
        except ValueError:
            continue
    return set(_demo_rows(providers))


def _new_demo_refusal(written: list[DemoRow], stored: Document) -> str | None:
    """The line refusing the first written CCXT demo row the stored file does not hold, on an
    exchange with no demo mode. CCXT is asked only about those rows, because the first ask in a
    process imports it while the settings lock is held."""
    saved = _stored_demo_rows(stored) if written else set[DemoRow]()
    return next(
        (line for row in written if row not in saved and (line := demo_refusal(row[2]))), None
    )


@dataclass(frozen=True, slots=True)
class Observer:
    """One live observer token's row, as the door reads it."""

    id: str
    name: str
    expires_at: str


_OBSERVERS_LOCK: Final = threading.Lock()


def _token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def _instant(value: str) -> datetime | None:
    try:
        found = datetime.fromisoformat(value)
    except ValueError:
        return None
    return found if found.tzinfo is not None else found.replace(tzinfo=UTC)


class Observers:
    """The operator's observer tokens: minted in Settings, revocable, expiring (AD-69, H61).

    The file under the home keeps each token's hash and never the token, so reading it gives no
    bearer. A token is refused once its row is revoked or its `expires_at` passed; a minted token
    is shown to the operator once, in the answer that created it.
    """

    def __init__(self, home: Path) -> None:
        self.path = home / OBSERVERS

    def rows(self) -> list[Document]:
        return [self._row(entry) for entry in self._load()]

    def create(self, name: str) -> Document:
        cleaned = name.strip()
        if not cleaned:
            raise ControlError("invalid_observer", "An observer needs a name.")
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        entry: dict[str, Any] = {
            "id": f"{OBSERVER_PREFIX}{uuid.uuid4().hex[:12]}",
            "name": cleaned,
            "token_hash": _token_hash(token),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=OBSERVER_TTL_DAYS)).isoformat(),
            "revoked_at": None,
        }
        with _OBSERVERS_LOCK:
            entries = self._load()
            entries.append(entry)
            self._store(entries)
        return {
            **self._row(entry),
            "token": token,
            "ref": OBSERVER_REF.format(observer=entry["id"]),
        }

    def revoke(self, observer_id: str) -> Document:
        with _OBSERVERS_LOCK:
            entries = self._load()
            found = next((entry for entry in entries if entry.get("id") == observer_id), None)
            if found is None:
                raise ControlError("not_found", f"no observer {observer_id}", 404)
            found["revoked_at"] = datetime.now(UTC).isoformat()
            self._store(entries)
        return self._row(found)

    def verify(self, token: str, *, now: datetime | None = None) -> Observer | None:
        """The observer a presented token names, or None when no live row holds it."""
        digest = _token_hash(token)
        for entry in self._load():
            held = entry.get("token_hash")
            if not isinstance(held, str) or not secrets.compare_digest(held, digest):
                continue
            if entry.get("revoked_at"):
                return None
            expires = _instant(str(entry.get("expires_at") or ""))
            if expires is None or expires <= (now or datetime.now(UTC)):
                return None
            return Observer(str(entry["id"]), str(entry.get("name") or ""), expires.isoformat())
        return None

    def _row(self, entry: Mapping[str, Any]) -> Document:
        return {
            "id": entry["id"],
            "name": entry.get("name") or "",
            "created_at": entry.get("created_at") or "",
            "expires_at": entry.get("expires_at") or "",
            "revoked_at": entry.get("revoked_at"),
            "ref": OBSERVER_REF.format(observer=entry["id"]),
        }

    def _load(self) -> list[dict[str, Any]]:
        try:
            raw: object = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError, ValueError:
            return []
        if not isinstance(raw, dict):
            return []
        rows = cast("dict[str, object]", raw).get("observers")
        if not isinstance(rows, list):
            return []
        return [cast("dict[str, Any]", row) for row in cast("list[object]", rows)]

    def _store(self, entries: Sequence[Mapping[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        scratch = self.path.with_suffix(".tmp")
        scratch.write_text(json.dumps({"observers": list(entries)}, indent=2), encoding="utf-8")
        scratch.replace(self.path)


_TABLE_HEADER = re.compile(r"^\s*(\[\[?)\s*(.+?)\s*(\]\]?)\s*(?:#.*)?$")


def _top_key(header: re.Match[str]) -> str | None:
    """The top-level key a `[a.b]` or `[[a.b]]` header line opens, read by TOML itself."""
    opening, name, closing = header.groups()
    try:
        parsed = tomllib.loads(f"{opening}{name}{closing}\n")
    except tomllib.TOMLDecodeError:
        return None
    return next(iter(parsed), None)


def kept_word_for_word(text: str, stored: Document, settings: Document) -> str:
    """`settings.toml` rewritten to hold `settings`, keeping every section that did not change
    as its own lines, comments and all (design 62 B2 rule 3): an older release never drops or
    reshapes what a newer one wrote. Only the sections whose values changed are written again,
    in the place of their old lines. When the old text does not split cleanly into sections
    (a top-level key of a changed section, a header inside a multi-line string), every key is
    still kept, written whole by `tomli_w`. Raises TypeError or ValueError for a value TOML
    cannot hold."""
    changed = {key for key in {*stored, *settings} if stored.get(key) != settings.get(key)}
    fresh = tomli_w.dumps({key: settings[key] for key in settings if key in changed})
    if not text.strip():
        return tomli_w.dumps(settings)
    kept: list[str] = []
    at: int | None = None
    owner: str | None = None
    above: list[str] = []
    """Comment and blank lines at the end of a changed section: they sit above the next header
    and belong to it, so they are kept."""
    for line in text.splitlines(keepends=True):
        header = _TABLE_HEADER.match(line)
        if header is not None:
            owner = _top_key(header)
        if owner is not None and owner in changed:
            at = len(kept) if at is None else at
            bare = line.strip()
            above = [*above, line] if not bare or bare.startswith("#") else []
            continue
        kept += [*above, line]
        above = []
    if kept and not kept[-1].endswith("\n"):
        kept[-1] += "\n"
    if fresh and at is None:
        kept.append(f"\n{fresh}" if kept else fresh)
    elif fresh and at is not None:
        kept.insert(at, fresh)
    result = "".join(kept)
    try:
        if tomllib.loads(result) == settings:
            return result
    except tomllib.TOMLDecodeError:
        pass
    return tomli_w.dumps(settings)


class _Adopted:
    """The home this process's one door reads observer rows from."""

    home: Path | None = None


_adopted = _Adopted()


def adopt_observers(home: Path | None) -> None:
    """Point this process at the home whose observer rows its door reads.

    A host builds one `ControlService`, for its own home, and the one door it mounts asks this
    module. A process that builds no service adopts nothing, so no door recognizes a token.
    """
    _adopted.home = None if home is None else home.resolve()


def observers() -> Observers | None:
    """This process's observer store, or None while no home adopted one."""
    found = _adopted.home
    return None if found is None else Observers(found)


class ControlService:
    def __init__(
        self,
        home: Path,
        *,
        tier: Literal["T1", "T2"] = "T1",
        node: str = "laptop",
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
        settings_parsers: Mapping[SettingsSection, SettingsParser] | None = None,
    ) -> None:
        self.home = home.resolve()
        self.settings_parsers = dict(settings_parsers or {})
        self.home.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._app_hooks: dict[str, Callable[[str, Document], None]] = {}
        self._apps: Supervisor | None = None
        self._backup_lock = threading.Lock()
        self._backup_schedule: BackupSchedule | None = None
        self.tier = tier
        self.node = node
        self.secret_getter = secret_getter
        self.library = Library(self.home)
        self.run_index = RunIndex(self.home)
        self._aggregate = read_cache(ttl=5)(self._aggregate_read)
        adopt_observers(self.home)
        with closing(
            sqlite3.connect(self.home / "control.db", isolation_level=None, timeout=5)
        ) as db:
            open_sqlite(db, "control", (CONTROL_SCHEMA,))
            for statement in CONTROL_SCHEMA:
                db.execute(statement)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.home / "control.db", timeout=5)) as db, db:
            yield db

    def _event(
        self, db: sqlite3.Connection, topic: EventTopic, subject: str, data: Document
    ) -> None:
        self._aggregate.cache_clear()
        cursor = db.execute(
            "INSERT INTO events(topic,subject,data) VALUES(?,?,?)",
            (topic, subject, json.dumps(data)),
        )
        if topic in {"runs", "jobs", "apps", "library"}:
            summary = self._aggregate_counts(cursor.lastrowid or 0)
            db.execute(
                "INSERT INTO events(topic,subject,data) VALUES('aggregates','',?)",
                (json.dumps(summary),),
            )

    def events(
        self, topic: EventTopic, after: int = 0, subject: str = "", limit: int = 100
    ) -> list[Document]:
        if after < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_cursor", "Use after >= 0 and limit between 1 and 1000.")
        with self._connect() as db:
            rows = db.execute(
                "SELECT seq,subject,data FROM events WHERE topic=? AND seq>? "
                "AND (?='' OR subject=?) ORDER BY seq LIMIT ?",
                (topic, after, subject, subject, limit),
            ).fetchall()
        return [
            {"id": row[0], "topic": topic, "subject": row[1], "data": _document(row[2])}
            for row in rows
        ]

    async def stream(
        self, topic: EventTopic, after: int = 0, subject: str = "", max_events: int = 0
    ) -> AsyncIterator[Document]:
        count = 0
        while True:
            for event in self.events(topic, after, subject):
                after = cast(int, event["id"])
                yield event
                count += 1
                if max_events and count >= max_events:
                    return
            await asyncio.sleep(0.05)

    def last_look(self, store: str = "library", last_seq: int | None = None) -> Document:
        """The operator's "last look" cursor: the position in `store`'s log his last digest read
        to.

        It is a position (the `seq` of a landing), never a clock, so a digest run reads exactly
        the items that landed after the last one he saw (46 K-32). Zero until he looks once. A
        cursor written before it named its store, or one above `last_seq` (the store's newest
        position), was counted in another file: it resets to zero once, with a log line.
        """
        name = f"{LOOK}:{store}"
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT position, at FROM operator_cursor WHERE name=?", (name,)
            ).fetchone()
            legacy = db.execute("SELECT 1 FROM operator_cursor WHERE name=?", (LOOK,)).fetchone()
            untagged = row is None and legacy is not None
            above = row is not None and last_seq is not None and int(row[0]) > last_seq
            if untagged or above:
                why = "it names no store" if untagged else f"it is above {store}'s {last_seq}"
                LOG.warning("the last-look cursor reset to 0: %s", why)
                db.execute(
                    "INSERT INTO operator_cursor(name,position,at) VALUES(?,0,?) "
                    "ON CONFLICT(name) DO UPDATE SET position=0, at=excluded.at",
                    (name, now),
                )
                row = (0, now)
        return {
            "name": LOOK,
            "store": store,
            "position": 0 if row is None else int(row[0]),
            "at": None if row is None else str(row[1]),
        }

    def mark_looked(self, position: int, store: str = "library") -> Document:
        """Move `store`'s cursor to `position`, and never back, then return the row as it stands.

        The digest advances it only after the digest passed its own check, so a failed run shows
        the same items again rather than hiding them.
        """
        if position < 0:
            raise ControlError("invalid_cursor", "Use the Library log's seq, 0 or more.")
        name = f"{LOOK}:{store}"
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO operator_cursor(name,position,at) VALUES(?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET position=max(position, excluded.position), "
                "at=CASE WHEN excluded.position>position THEN excluded.at ELSE at END",
                (name, position, now),
            )
            row = db.execute(
                "SELECT position, at FROM operator_cursor WHERE name=?", (name,)
            ).fetchone()
        return {"name": LOOK, "store": store, "position": int(row[0]), "at": str(row[1])}

    @operation("settings_read", "get", "read", rest=("GET", "/api/settings/{section}"))
    def settings_get(self, section: SettingsSection) -> Document:
        """Read UI-editable provider, MCP, budget, memory or observer settings."""
        if section == "observers":
            return cast("Document", {"observers": Observers(self.home).rows()})
        with self._lock:
            path = self.home / "settings.toml"
            values: Document = {}
            stored: Document = {}
            if path.exists():
                with path.open("rb") as file:
                    stored = cast(Document, tomllib.load(file))
                    values = cast(Document, stored.get(section, {}))
            if section == "brokers":
                values = legacy_brokers(stored)
            if section == "data":
                values = _with_holdout(values)
            if section == "connections":
                rows = stored.get("connections")
                values = {"connections": rows if isinstance(rows, list) else []}
            if section == "mcp_servers":
                firecrawl = values.get("firecrawl", {})
                if not isinstance(firecrawl, dict):
                    raise ControlError("invalid_settings", "Firecrawl settings must be a table.")
                values["firecrawl"] = {
                    "url": "https://mcp.firecrawl.dev/v2/mcp",
                    "enabled": False,
                    "credential_ref": "qmx/firecrawl",
                    **firecrawl,
                }
            return values

    def settings_update(
        self, section: SettingsSection, change: Callable[[Document], Document]
    ) -> Document:
        """Read, change and write one section under the settings lock, so concurrent updates
        all land. Writes nothing when the change returns the section as it was."""
        with self._lock:
            current = self.settings_get(section)
            values = change(current)
            return values if values == current else self.settings_put(section, values)

    @operation(
        "settings_read",
        "put",
        "manage",
        rest=("PUT", "/api/settings/{section}"),
        agent=False,
        left_out="an agent that edits a provider row could send a stored key to a host",
    )
    def settings_put(self, section: SettingsSection, values: Document) -> Document:
        """Replace a settings section; credentials must be vault references."""
        with self._lock:
            return self._settings_put(section, values)

    def _observers_put(self, values: Document) -> Document:
        """Mint or revoke one observer token, as a Settings write by the operator (AD-69).

        A mint sends a `name` and answers once with the token; a revoke sends the row's `revoke`
        id. The token never lands in `settings.toml`, and the answer lists every row without one.
        """
        store = Observers(self.home)
        name = values.get("name")
        revoke = values.get("revoke")
        if isinstance(revoke, str) and revoke:
            return cast("Document", {"revoked": store.revoke(revoke), "observers": store.rows()})
        if isinstance(name, str) and name.strip():
            return cast("Document", {"created": store.create(name), "observers": store.rows()})
        raise ControlError(
            "invalid_observer",
            "Send a name to mint an observer token, or a revoke id to end one.",
        )

    def _settings_put(self, section: SettingsSection, values: Document) -> Document:
        if section == "observers":
            return self._observers_put(values)
        _no_secrets(values)
        stored_rows: list[dict[str, Any]] | None = None
        demo_rows: list[DemoRow] = []
        if section in HOST_SECTIONS:
            parser = self.settings_parsers.get(section)
            if parser is None:
                raise ControlError(
                    "invalid_settings", f"The {section} section is written only by the QMA host."
                )
            values = parser(values, self.settings_get(section))
        if section == "rules":
            values = _rule_lists(values)
        if section == "data":
            values = _data_settings(values)
        if section == "mcp_servers" and "firecrawl" in values:
            firecrawl = values["firecrawl"]
            if not isinstance(firecrawl, dict) or set(firecrawl) - {
                "url",
                "enabled",
                "credential_ref",
            }:
                raise ControlError(
                    "invalid_settings", "Use Firecrawl url, enabled and credential_ref only."
                )
            try:
                url = urlsplit(str(firecrawl.get("url", "https://mcp.firecrawl.dev/v2/mcp")))
            except ValueError as error:
                raise ControlError("invalid_settings", "Firecrawl URL is malformed.") from error
            if (
                not isinstance(firecrawl.get("enabled", False), bool)
                or firecrawl.get("credential_ref", "qmx/firecrawl") != "qmx/firecrawl"
                or url.scheme != "https"
                or not url.hostname
                or any((url.username, url.password, url.query, url.fragment))
            ):
                raise ControlError(
                    "invalid_settings",
                    "Firecrawl needs HTTPS, an enabled boolean and qmx/firecrawl.",
                )
        if section == "backup":
            if "repository" in values:
                repository = values["repository"]
                if not isinstance(repository, str) or not repository.strip():
                    raise ControlError(
                        "invalid_settings", "Backup repository must be nonempty text."
                    )
            _check_backup_plan(values, Layout.from_home(self.home))
            app_settings = _volume_keys(values)
            if app_settings:
                BackupSettings.model_validate(app_settings).destination("validation", "validation")
        elif section in ("brokers", "connections"):
            try:
                parsed = BrokerSettings.model_validate(values)
            except ValueError as error:
                raise ControlError(
                    "invalid_brokers",
                    "Use valid brokers, connections, providers and accounts with qmx/* vault"
                    " references.",
                ) from error
            rows = [
                provider.model_dump(mode="json", exclude_none=True) for provider in parsed.providers
            ]
            if section == "brokers":
                # The old section is read once into `connections`; its shape is served from there.
                values = legacy_brokers(cast(Document, {"connections": rows}))
            else:
                values = cast(Document, {"connections": rows})
            stored_rows, demo_rows = rows, _demo_rows(parsed.providers)
        else:
            stored_rows = None

        with self._lock:
            path = self.home / "settings.toml"
            refused = too_new(path, "settings")
            if refused is not None:
                raise ControlError("settings_too_new", refused, 409)
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            stored = cast(Document, tomllib.loads(text))
            if no_demo := _new_demo_refusal(demo_rows, stored):
                raise ControlError("invalid_brokers", no_demo)
            settings = dict(stored)
            if stored_rows is not None:
                settings["connections"] = cast(JsonValue, stored_rows)
                settings.pop("brokers", None)
            else:
                settings[section] = values
            try:
                encoded = kept_word_for_word(text, stored, settings)
            except (TypeError, ValueError) as error:
                raise ControlError(
                    "invalid_settings", "Settings must contain TOML-compatible values (no nulls)."
                ) from error
            temporary = path.with_suffix(".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            temporary.replace(path)
            with self._connect() as db:
                self._event(db, "settings", section, {"section": section})
        return values

    @operation(
        "broker_read", "proposals", "read", rest=("GET", "/api/portfolio/proposals"), cursor=True
    )
    def portfolio_proposals(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """Read unsigned broker proposals awaiting the operator's Portfolio signature."""
        return cast(list[Document], read_proposals(self.home, offset, limit))

    @operation(
        "ops",
        "sessions_create",
        "domain_write",
        rest=("POST", "/api/sessions"),
        agent=False,
        left_out="chats are created by the harness",
    )
    def sessions_create(self, session: SessionInput) -> Document:
        """Create a durable Copilot session, optionally a child session."""
        with self._lock, self._connect() as db:
            if (
                session.parent_id
                and db.execute("SELECT 1 FROM sessions WHERE id=?", (session.parent_id,)).fetchone()
                is None
            ):
                raise ControlError("not_found", "Parent session does not exist.", 404)
            session_id = str(uuid.uuid4())
            data: Document = {"id": session_id, **session.model_dump(mode="json")}
            db.execute("INSERT INTO sessions VALUES(?,?)", (session_id, json.dumps(data)))
            self._event(db, "sessions", session_id, {"type": "created", "session": data})
        return data

    @operation("ops", "sessions", "read", rest=("GET", "/api/sessions"), cursor=True)
    def sessions_list(self, offset: int = 0, limit: int = 100) -> list[Document]:
        """List saved sessions, including their origin and parent."""
        self._page(offset, limit)
        with self._connect() as db:
            rows = db.execute(
                "SELECT data FROM sessions ORDER BY rowid LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
        return [_document(row[0]) for row in rows]

    @operation(
        "ops",
        "sessions_append",
        "domain_write",
        rest=("POST", "/api/sessions/{session_id}/blocks"),
        agent=False,
        left_out="an agent could forge permission or needs_you blocks",
    )
    def sessions_append(self, session_id: str, block: SessionBlock) -> Document:
        """Append a typed block; history is never rewritten."""
        with self._lock, self._connect() as db:
            if db.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                raise ControlError("not_found", "Session does not exist.", 404)
            seq = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM blocks WHERE session_id=?", (session_id,)
            ).fetchone()[0]
            data: Document = {"seq": seq, **block.model_dump(mode="json")}
            db.execute("INSERT INTO blocks VALUES(?,?,?)", (session_id, seq, json.dumps(data)))
            self._event(db, "sessions", session_id, {"type": "block", "block": data})
        return data

    @operation(
        "ops",
        "sessions_stream",
        "read",
        rest=("GET", "/api/sessions/{session_id}/events"),
        agent=False,
        left_out="a live event stream, not a tool",
    )
    def sessions_stream(self, session_id: str, after: int = 0, limit: int = 100) -> list[Document]:
        """Read a page of session events. REST also offers a continuous SSE stream."""
        with self._connect() as db:
            if db.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                raise ControlError("not_found", "Session does not exist.", 404)
        return self.events("sessions", after, session_id, limit)

    def delegate_completion_save(self, completion: DelegateCompletion) -> Document:
        """Store one helper's answer before it is announced or delivered (AD-41). Saving the
        same handle twice keeps one row and one delivery."""
        with self._lock, self._connect() as db:
            data: Document = {
                "created": datetime.now(UTC).isoformat(),
                **completion.model_dump(mode="json"),
            }
            db.execute(
                "INSERT INTO delegate_completions(handle,parent_session,data,delivered_at) "
                "VALUES(?,?,?,NULL) ON CONFLICT(handle) DO UPDATE SET data=excluded.data",
                (completion.handle, completion.parent_session, json.dumps(data)),
            )
            self._event(
                db,
                "sessions",
                completion.parent_session,
                {
                    "type": "delegate_completion",
                    "handle": completion.handle,
                    "state": completion.state,
                },
            )
        return data

    def delegate_completions_pending(self, parent_session: str) -> list[Document]:
        """The answers this parent has not been handed yet, oldest first."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT data FROM delegate_completions WHERE parent_session=? "
                "AND delivered_at IS NULL ORDER BY rowid",
                (parent_session,),
            ).fetchall()
        return [_document(row[0]) for row in rows]

    def delegate_completions_all(self, parent_session: str) -> list[Document]:
        """Every answer stored for this parent, oldest first, each with its `delivered_at`."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT data,delivered_at FROM delegate_completions WHERE parent_session=? "
                "ORDER BY rowid",
                (parent_session,),
            ).fetchall()
        return [{**_document(row[0]), "delivered_at": row[1]} for row in rows]

    def delegate_completions_claim(self, handles: Sequence[str]) -> int:
        """Mark these answers delivered in one write, and say how many that was. A second claim
        marks nothing, so a completion reaches its parent once even across a restart."""
        with self._lock, self._connect() as db:
            now = datetime.now(UTC).isoformat()
            marked = 0
            for handle in handles:
                cursor = db.execute(
                    "UPDATE delegate_completions SET delivered_at=? "
                    "WHERE handle=? AND delivered_at IS NULL",
                    (now, handle),
                )
                marked += cursor.rowcount
        return marked

    def attach_library(self, store: Store) -> None:
        """This home's store is the one Library from here on (MIGRATION step 6): every `library_*`
        row, the copilot's search and the apps' landings read and write it."""
        self.library.attach(store)

    @operation("library", "save", "domain_write", rest=("POST", "/api/library"))
    def library_save(self, item: LibraryInput) -> Document:
        """Save an immutable object, optionally a new version or URL/date result."""
        with self._lock, self._connect() as db:
            data = self.library.save(item)
            self._event(db, "library", str(data["id"]), {"type": "saved", "item_id": data["id"]})
        return data

    @operation("library", "search", "read", rest=("GET", "/api/library"), cursor=True)
    def library_search(self, query: str = "", offset: int = 0, limit: int = 100) -> list[Document]:
        """FTS5 search over title, tags and extracted text, ordered by relevance."""
        return self.library.search(query, offset, limit)

    @operation("library", "get", "read", rest=("GET", "/api/library/{artifact_id}"))
    def library_get(self, artifact_id: str) -> Document:
        """Read an artifact with its verified blob content."""
        return self.library.get(artifact_id)

    def _tagged(self, tag: str) -> list[Document]:
        """The latest version of every item carrying `tag`."""
        return self.library.tagged(tag)

    @operation("library", "eval_tasks", "read", rest=("GET", "/api/eval/tasks"))
    def library_eval_tasks(self) -> list[Document]:
        """The copilot eval battery's tasks: the latest version of every item tagged eval-task.
        A new failure becomes a task with one library_save tagged eval-task."""
        return [cast(Document, item["content"]) for item in self._tagged(EVAL_TASK)]

    def _battery(self, subject: str) -> Document:
        """The card's battery field: the latest result for `subject`, or `not run`. Reading it
        never starts or waits on a battery."""
        ran = [
            i
            for i in self._tagged(EVAL_RUN)
            if cast(Document, i["content"]).get("subject") == subject
        ]
        if not ran:
            return {"battery": {"status": "not run", "subject": subject}, "surface_digest": None}
        result = cast(Document, ran[-1]["content"])
        sides = {name: cast(Document, result[name]) for name in ("candidate", "baseline")}
        field: Document = {
            "status": "ran",
            "subject": subject,
            "result_id": ran[-1]["id"],
            "mode": result.get("mode"),
            "judge": result.get("judge"),
            "per_task": result.get("per_task"),
        }
        for name, side in sides.items():
            field[name] = {
                key: side.get(key)
                for key in ("model", "run_id", "status", "fell_back", "passed", "total")
            }
        before, after = sides["baseline"]["surface_digest"], sides["candidate"]["surface_digest"]
        digest: Document = {"from": before, "to": after, "changed": before != after}
        return {"battery": field, "surface_digest": digest}

    @operation(
        "settings_read", "model_card", "read", rest=("GET", "/api/settings/agents/model-card")
    )
    def settings_model_card(self, model: str) -> Document:
        """The Settings change card for switching the copilot's default model
        (`[agents] copilot_model`) to `model`: the eval battery's pass^3 per task on the new
        model and the current one, and the surface digest on each side. Writes nothing."""
        current = self.settings_get("agents").get("copilot_model")
        current = current if isinstance(current, str) else None
        change: Document = {
            "section": "agents",
            "key": "copilot_model",
            "from": current,
            "to": model,
        }
        return {"change": change, **self._battery(model_subject(current, model))}

    @operation(
        "library", "publish_card", "read", rest=("GET", "/api/library/{artifact_id}/publish-card")
    )
    def library_publish_card(self, artifact_id: str) -> Document:
        """The publish card of a persona, methodology or skill draft: the eval battery's pass^3
        per task with the draft against the published text, both on the copilot's default
        model, and the surface digest change. Publishing stays his click."""
        item = self.library.get(artifact_id)
        if item["kind"] not in SLOT_KINDS:
            raise ControlError(
                "not_a_slot_item", "Only persona, methodology and skill drafts have a publish card."
            )
        change: Document = {
            "kind": item["kind"],
            "item": artifact_id,
            "replaces": item["previous_id"],
        }
        return {"change": change, **self._battery(draft_subject(artifact_id))}

    def memoized_backtest(self, identity: MemoKey, produce: Callable[[], LibraryInput]) -> Document:
        """Reuse a deterministic backtest artifact, recording newly computed results."""
        produced = False

        def compute() -> LibraryInput:
            nonlocal produced
            item = produce()
            produced = True
            return item

        with self._lock:
            result = self.library.memoized(identity, compute)
            if produced:
                with self._connect() as db:
                    event: Document = {
                        "type": "saved",
                        "item_id": result["id"],
                        "memo_key": result["memo_key"],
                    }
                    self._event(db, "library", str(result["id"]), event)
        return result

    @operation("library", "versions", "read", rest=("GET", "/api/library/{artifact_id}/versions"))
    def library_versions(self, artifact_id: str) -> list[Document]:
        """Read an artifact's immutable version chain."""
        return self.library.versions(artifact_id)

    @operation("library", "link", "domain_write", rest=("POST", "/api/library/links"))
    def library_link(self, source_id: str, target_id: str, relation: str = "related") -> Document:
        """Link two existing objects without changing their contents."""
        with self._lock, self._connect() as db:
            data = self.library.link(source_id, target_id, relation)
            self._event(db, "library", source_id, {"type": "linked", **data})
        return data

    @operation("library", "links", "read", rest=("GET", "/api/library/{artifact_id}/links"))
    def library_links(self, artifact_id: str) -> list[Document]:
        """Read incoming and outgoing artifact links."""
        return self.library.links(artifact_id)

    def _item_of(self, artifact_id: str) -> str:
        """The item the object `artifact_id` names belongs to."""
        try:
            return self.library.store.get(LIBRARY_OPERATOR, artifact_id).item
        except LibraryRefused as error:
            raise refused(error) from error

    @operation(
        "library", "branch", "domain_write", rest=("POST", "/api/library/{artifact_id}/branch")
    )
    def library_branch(self, artifact_id: str, name: str, from_ref: str = "main") -> Document:
        """Put one item's ref under a new name, so a chat edits it there and nothing else moves."""
        try:
            commit = self.library.store.branch(
                LIBRARY_OPERATOR, self._item_of(artifact_id), from_ref=from_ref, name=name
            )
        except LibraryRefused as error:
            raise refused(error) from error
        with self._lock, self._connect() as db:
            self._event(db, "library", commit.object_id, {"type": "branched", "ref": commit.ref})
        return {"item": commit.item, "ref": commit.ref, "object_id": commit.object_id}

    @operation(
        "library", "merge", "domain_write", rest=("POST", "/api/library/{artifact_id}/merge")
    )
    def library_merge(
        self,
        artifact_id: str,
        from_ref: str,
        into: str = "main",
        strategy: Literal["auto", "ff-only"] = "auto",
    ) -> Document:
        """Merge one ref of an item into another; a clash mints a conflict and picks no side.

        A text slot merges line by line and a JSON slot key by key."""
        try:
            merged = self.library.store.merge(
                LIBRARY_OPERATOR,
                self._item_of(artifact_id),
                from_ref=from_ref,
                into=into,
                strategy=strategy,
            )
        except LibraryRefused as error:
            raise refused(error) from error
        with self._lock, self._connect() as db:
            self._event(
                db,
                "library",
                merged.object_id,
                {"type": merged.outcome, "into": into, "from_ref": from_ref},
            )
        return {"outcome": merged.outcome, "object_id": merged.object_id}

    @operation("library", "conflicts", "read", rest=("GET", "/api/library/conflicts"))
    def library_conflicts(self, artifact_id: str | None = None) -> list[Document]:
        """Read the open merge conflicts of one item, or of the Library when no item is named."""
        try:
            item = None if artifact_id is None else self._item_of(artifact_id)
            found = self.library.store.conflicts(LIBRARY_OPERATOR, item)
        except LibraryRefused as error:
            raise refused(error) from error
        return [
            {
                "id": view.object_id,
                "item": str(view.fields.get("item")),
                "into": str(view.fields.get("into")),
                "base": view.fields.get("base"),
                "ours": view.fields.get("ours"),
                "theirs": view.fields.get("theirs"),
                "entries": view.fields.get("entries"),
            }
            for view in found
        ]

    @operation(
        "library", "resolve", "domain_write", rest=("POST", "/api/library/{artifact_id}/resolve")
    )
    def library_resolve(
        self,
        artifact_id: str,
        text: str | None = None,
        values: Document | None = None,
    ) -> Document:
        """Close one merge conflict by answering each of its entries; an open entry refuses it.

        `values` answers each entry by its path, and `text` is the resolved text when the
        conflict holds one text slot."""
        try:
            merged = self.library.store.resolve_conflict(
                LIBRARY_OPERATOR, artifact_id, text=text, values=values
            )
        except LibraryRefused as error:
            raise refused(error) from error
        with self._lock, self._connect() as db:
            self._event(db, "library", merged.object_id, {"type": "resolved"})
        return {"outcome": merged.outcome, "object_id": merged.object_id}

    @operation("library", "history", "read", rest=("GET", "/api/library/{artifact_id}/history"))
    def library_history(self, artifact_id: str, ref: str | None = None) -> list[Document]:
        """Read an item's ref log: every move of a ref, who made it, when and to what."""
        try:
            moved = self.library.store.history_of(LIBRARY_OPERATOR, self._item_of(artifact_id), ref)
        except LibraryRefused as error:
            raise refused(error) from error
        return [
            {
                "seq": entry.seq,
                "ref": entry.ref,
                "principal": entry.principal,
                "prev_head": entry.prev_head,
                "new_head": entry.new_head,
                "at": entry.at,
                "reason": entry.reason,
            }
            for entry in moved
        ]

    @operation("library", "blame", "read", rest=("GET", "/api/library/{artifact_id}/blame"))
    def library_blame(self, artifact_id: str, slot: str, ref: str = "main") -> list[Document]:
        """Read which version and principal last changed each line of a text slot."""
        try:
            blamed = self.library.store.blame(
                LIBRARY_OPERATOR, self._item_of(artifact_id), slot, ref
            )
        except LibraryRefused as error:
            raise refused(error) from error
        return [
            {
                "number": line.number,
                "text": line.text,
                "object_id": line.object_id,
                "principal": line.principal,
                "at": line.at,
            }
            for line in blamed.lines
        ]

    @operation(
        "ops",
        "backup_weekly",
        "manage",
        rest=("POST", "/api/backup/weekly"),
        agent=False,
        left_out="a host maintenance job, not an agent act",
    )
    def backup_weekly(self, dry_run: bool = False) -> Document:
        """Snapshot small stores to the private backup repo in Settings, at most weekly."""
        settings = self.settings_get("backup")
        repository = settings.get("repository")
        if not isinstance(repository, str) or not repository:
            raise ControlError("backup_not_configured", "Set backup.repository in Settings.")
        try:
            result = weekly_backup(self.home, repository, dry_run=dry_run)
        except (OSError, sqlite3.Error) as error:
            raise ControlError(
                "backup_failed", "Snapshot creation failed; backup was not published.", 409
            ) from error
        return result

    def _aggregate_read(self, revision: int) -> Document:
        return self._aggregate_counts(revision)

    def _aggregate_counts(self, revision: int) -> Document:
        count = self.library.count()
        with closing(sqlite3.connect(self.home / "runs.db")) as index:
            runs = index.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        engine = self._workflow_engine
        active = 0
        if engine is not None:
            active = sum(
                1 for run in engine.workflow_runs_list(None) if run.get("status") == "running"
            )
        return {
            "revision": revision,
            "library_items": count,
            "runs": runs,
            "active_jobs": active,
        }

    @operation("ops", "aggregates", "read", rest=("GET", "/api/aggregates"))
    def aggregates_get(self) -> Document:
        """Read short-lived UI totals; event revisions invalidate the cached view."""
        self._refresh_runs()
        with self._lock, self._connect() as db:
            revision = db.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
            return cast(Document, self._aggregate(revision)).copy()

    @staticmethod
    def _page(offset: int, limit: int) -> None:
        if offset < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_page", "Use offset >= 0 and limit between 1 and 1000.")

    def _refresh_runs(self) -> None:
        with self._lock, self._connect() as db:
            for data in self.run_index.refresh():
                self._event(db, "runs", str(data["id"]), data)

    @staticmethod
    def _unavailable(operation: str, packet: str = "P12-P14") -> NoReturn:
        raise ControlError(
            "not_implemented", f"{operation} is not available yet; requires {packet}.", 501
        )

    @operation("apps_admin", "list", "read", rest=("GET", "/api/apps"))
    def apps_list(self) -> list[Document]:
        """List installed definitions and their actual runtime state."""
        return self.app_runtime().list()

    @operation("apps_admin", "get", "read", rest=("GET", "/api/apps/{app_id}"))
    def apps_get(self, app_id: str) -> Document:
        """Read an app definition and runtime status."""
        return self.app_runtime().get(app_id)

    @operation("apps_admin", "create", "manage", rest=("POST", "/api/apps"))
    def apps_create(self, path: str, trust: Trust = "agent") -> Document:
        """Install an app definition from a local package directory."""
        return self.app_runtime().install(Path(path), trust=trust)

    @operation("apps_admin", "update", "manage", rest=("PUT", "/api/apps/{app_id}"))
    def apps_update(
        self, app_id: str, path: str, trust: Trust = "agent", expected_hash: str | None = None
    ) -> Document:
        """Install a new immutable version of an app."""
        return self.app_runtime().install(
            Path(path), trust=trust, expected_id=app_id, expected_hash=expected_hash
        )

    @operation("apps_admin", "versions", "read", rest=("GET", "/api/apps/{app_id}/versions"))
    def apps_versions(self, app_id: str) -> list[Document]:
        """List immutable app definitions."""
        return self.app_runtime().versions(app_id)

    @operation(
        "apps_admin",
        "test",
        "domain_write",
        rest=("POST", "/api/apps/{app_id}/test"),
        forced={"auto_publish": False},
    )
    def apps_test(
        self,
        app_id: str,
        expected_hash: str | None = None,
        stage: Stage | None = None,
        auto_publish: bool = True,
    ) -> Document:
        """Run the next actual test, recorded sandbox or isolated shadow stage."""
        owner = self.app_runtime()
        current = str(owner.get(app_id)["definition_hash"])
        return owner.road.advance(
            app_id, expected_hash or current, stage, auto_publish=auto_publish
        )

    @operation("apps_admin", "publish", "manage", rest=("POST", "/api/apps/{app_id}/publish"))
    def apps_publish(
        self,
        app_id: str,
        expected_hash: str | None = None,
        expected_active: str | None = None,
        signature: str | None = None,
    ) -> Document:
        """Activate current proven code using publication CAS and risk rules."""
        owner = self.app_runtime()
        current = str(owner.get(app_id)["definition_hash"])
        return owner.road.publish(app_id, expected_hash or current, expected_active, signature)

    @operation("apps_admin", "rollback", "manage", rest=("POST", "/api/apps/{app_id}/rollback"))
    def apps_rollback(
        self, app_id: str, expected_active: str, signature: str | None = None
    ) -> Document:
        """Reactivate the previous publication as a new evidenced transition."""
        owner = self.app_runtime()
        return owner.road.publish(
            app_id,
            str(owner.get(app_id)["definition_hash"]),
            expected_active,
            signature,
            rollback=True,
        )

    @operation("apps_admin", "start", "manage", rest=("POST", "/api/apps/{app_id}/start"))
    def apps_start(self, app_id: str) -> Document:
        """Start an installed app instance."""
        return self.app_runtime().start(app_id)

    @operation("apps_admin", "stop", "manage", rest=("POST", "/api/apps/{app_id}/stop"))
    def apps_stop(self, app_id: str) -> Document:
        """Stop an app's process tree."""
        return self.app_runtime().stop(app_id)

    @operation("apps_admin", "logs", "read", rest=("GET", "/api/apps/{app_id}/logs"))
    def apps_logs(self, app_id: str, limit: int = 100) -> list[Document]:
        """Read structured app logs."""
        return self.app_runtime().logs(app_id, limit)

    @operation("apps_admin", "restart", "manage", rest=("POST", "/api/apps/{app_id}/restart"))
    def apps_restart(self, app_id: str) -> Document:
        """Restart the selected immutable definition, retaining its volume."""
        return self.app_runtime().restart(app_id)

    @operation(
        "apps_admin",
        "enable",
        "manage",
        rest=("POST", "/api/apps/{app_id}/enable"),
        agent=False,
        left_out="his act from the UI: it publishes and enables a workflow (engine AD-11)",
    )
    def apps_enable(self, app_id: str) -> Document:
        """Start an app and turn its suggested trigger into an enabled engine trigger."""
        owner = self.app_runtime()
        manifest = cast(Document, owner.get(app_id)["definition"])
        app = owner.start(app_id)
        suggested = manifest.get("suggested_trigger")
        if not isinstance(suggested, dict):
            return {"app": app, "trigger": None}
        engine = self._engine("apps.enable")
        item = app_workflow_id(app_id)
        found = engine.workflow_triggers_list(item)
        if found:
            trigger_id = str(found[0]["id"])
        else:
            entrypoints = cast(Document, manifest["entrypoints"])
            job = suggested.get("job") or cast(list[JsonValue], entrypoints["jobs"])[0]
            engine.workflow_drafts_put(item, app_workflow(item, app_id, str(job)))
            tested = cast(Document, engine.workflow_tests_run(item, None, False)["run"])
            if tested.get("status") != "passed":
                raise ControlError(
                    "app_test_failed",
                    f"The test run {tested.get('run_id')} of {item} reads {tested.get('status')}; "
                    "enable again once it passes.",
                    409,
                )
            published = engine.workflows_put(item, {})
            if "card" in published:
                return published
            spec = {key: suggested[key] for key in ("kind", "seconds", "expr", "zone")}
            trigger_id = str(engine.workflow_triggers_create(item, spec)["id"])
        return {"app": app, "trigger": engine.workflow_triggers_enable(trigger_id)}

    def app_job(
        self,
        app_id: str,
        job: str,
        *,
        pin: Document | None = None,
        profile: str | None = None,
    ) -> Document:
        """Run one of an app's jobs in its supervised process; the engine's `app_op` node
        calls this when the app's trigger fires (engine AD-57). The supervisor revalidates a
        `pin` and refuses a run aimed at another `profile` (AD-64)."""
        try:
            return self.app_runtime().run_job(app_id, job, pin=pin, profile=profile)
        except AppError as error:
            raise ControlError(error.code, str(error), error.status) from error

    @operation("apps_admin", "registry", "read", rest=("GET", "/api/apps/registry"))
    def apps_registry(self) -> list[Document]:
        """Discover connected MCP servers and their tools and resources."""
        return self.app_runtime().registry()

    @operation(
        "apps_admin",
        "call",
        "manage",
        rest=("POST", "/api/apps/{app_id}/tools/{tool}"),
        agent=False,
        left_out="a REST door for the UI; apps ask each other through their own operations",
    )
    def apps_call(self, app_id: str, tool: str, arguments: Document) -> Document:
        """Call a connected app; feed arguments must be registered artifact refs."""
        result = self.app_runtime().call(app_id, tool, arguments)
        reference = result.get("artifact_ref")
        output = result.get("result")
        if isinstance(reference, dict) and isinstance(output, dict) and "data" in output:
            saved = self.library_save(
                LibraryInput(
                    title=f"{app_id}: {reference['output']}"[:200],
                    kind="app-output",
                    tags=[app_id, str(reference["output"])],
                    source=f"app://{app_id}/{reference['output']}/{reference['sha256']}",
                    content={"artifact_ref": reference, "data": output["data"]},
                )
            )
            result["library_id"] = saved["id"]
            result["library_ref"] = saved["ref"]
        return result

    @operation("apps_admin", "resource", "read", rest=("GET", "/api/apps/{app_id}/resources"))
    def apps_resource(self, app_id: str, uri: str) -> list[Document]:
        """Read an app's MCP resource, including ui:// panels."""
        return self.app_runtime().resource(app_id, uri)

    def app_runtime(self) -> Supervisor:
        with self._lock:
            if self._apps is None:
                if self.tier == "T2":
                    providers = self.settings_get("providers")
                    replica_settings = providers.get("litestream", {})
                    replicas = (
                        {
                            name: url
                            for name, url in replica_settings.items()
                            if isinstance(url, str)
                        }
                        if isinstance(replica_settings, dict)
                        else {}
                    )
                    self._apps = DockerSupervisor(
                        self.home,
                        node=self.node,
                        replicas=replicas,
                        event_sink=self._app_event,
                        secret_getter=self.secret_getter,
                    )
                else:
                    self._apps = Supervisor(
                        self.home,
                        event_sink=self._app_event,
                        secret_getter=self.secret_getter,
                    )
                self._backup_schedule = BackupSchedule(
                    self._backup_settings,
                    self._backup_apps,
                    self.apps_backup,
                    self._backup_failed,
                )
                self._apps.attach_library(self.library.landed)
            return self._apps

    def _backup_settings(self) -> BackupSettings | None:
        values = _volume_keys(self.settings_get("backup"))
        return BackupSettings.model_validate(values) if values else None

    def _backup_apps(self) -> list[str]:
        return [
            str(item["definition"]["id"])
            for item in self.apps_list()
            if isinstance(item["definition"], dict)
            and Volume(self.home, str(item["definition"]["id"])).root.joinpath("app.db").is_file()
        ]

    def _backup_failed(self, app_id: str, error: Exception) -> None:
        with self._lock, self._connect() as db:
            self._event(
                db, "apps", app_id, {"type": "backup_failed", "error": type(error).__name__}
            )

    @operation("apps_admin", "backup", "domain_write", rest=("POST", "/api/apps/{app_id}/backup"))
    def apps_backup(self, app_id: str) -> Document:
        """Back up now using the UI-editable remote and verify a downloaded restore."""
        self.app_runtime().get(app_id)
        settings = self._backup_settings()
        if settings is None:
            raise ControlError(
                "backup_unconfigured", "Configure the backup remote in Settings.", 409
            )
        with self._backup_lock:
            result = backup(Volume(self.home, app_id), settings)
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, {"type": "backup", **result})
        return result

    @operation("apps_admin", "restore", "manage", rest=("POST", "/api/apps/{app_id}/restore"))
    def apps_restore(self, app_id: str, snapshot_id: str) -> Document:
        """Verify and replace a stopped app's volume from a backup snapshot."""
        self.app_runtime().get(app_id)
        settings = self._backup_settings()
        if settings is None:
            raise ControlError(
                "backup_unconfigured", "Configure the backup remote in Settings.", 409
            )
        with self._backup_lock:
            result = restore(self.home, app_id, settings, snapshot_id)
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, {"type": "restored", **result})
        return result

    def _app_event(self, app_id: str, data: Document) -> None:
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, data)
        with self._lock:
            for hook in list(self._app_hooks.values()):
                hook(app_id, data)

    def watch_app_events(self, session_id: str, hook: Callable[[str, Document], None]) -> None:
        """Keep one subscription per session across agent rebuilds."""
        with self._lock:
            self._app_hooks.setdefault(session_id, hook)

    def notify_app(self, app_id: str, data: Document) -> None:
        """Publish an actionable operator notification on the existing app stream."""
        with self._lock, self._connect() as db:
            self._event(db, "apps", app_id, data)

    def close(self) -> None:
        if self._backup_schedule is not None:
            self._backup_schedule.close()
            self._backup_schedule = None
        if self._apps is not None:
            self._apps.close()
            self._apps = None
        self._app_hooks.clear()

    @operation("apps_admin", "evidence", "read", rest=("GET", "/api/apps/{app_id}/evidence"))
    def apps_evidence(self, app_id: str) -> list[Document]:
        """Read verified version and stage evidence from the app volume."""
        return self.app_runtime().road.evidence(app_id)

    _workflow_engine: WorkflowEngine | None = None

    def attach_workflow_engine(self, engine: WorkflowEngine | None) -> None:
        """Serve the workflow doors from `engine`; None detaches it and they answer 501 again."""
        self._workflow_engine = engine

    def _engine(self, operation: str) -> WorkflowEngine:
        engine = self._workflow_engine
        if engine is None:
            self._unavailable(operation, ENGINE)
        return engine

    @operation("workflows", "get", "read", rest=("GET", "/api/workflows/{workflow_id}"))
    def workflows_get(self, workflow_id: str) -> Document:
        """Read a workflow definition."""
        return self._engine("workflows.get").workflows_get(workflow_id)

    @operation("workflows", "put", "manage", rest=("PUT", "/api/workflows/{workflow_id}"))
    def workflows_put(self, workflow_id: str, graph: Document) -> Document:
        """Publish a workflow graph as a new version. Saving a draft is workflows_drafts_put."""
        return self._engine("workflows.put").workflows_put(workflow_id, graph)

    @operation("workflows", "validate", "read", rest=("POST", "/api/workflows/validate"))
    def workflows_validate(self, graph: Document) -> Document:
        """Validate a workflow graph."""
        return self._engine("workflows.validate").workflows_validate(graph)

    @operation("workflows", "run", "manage", rest=("POST", "/api/workflows/{workflow_id}/run"))
    def workflows_run(
        self, workflow_id: str, inputs: dict[str, JsonValue] | None = None
    ) -> Document:
        """Start a live run of a published workflow on inputs its schema accepts. A test run is
        workflows_tests_run."""
        return self._engine("workflows.run").workflows_run(workflow_id, inputs)

    @operation(
        "workflows", "drafts_get", "read", rest=("GET", "/api/workflows/{workflow_id}/draft")
    )
    def workflow_drafts_get(self, workflow_id: str) -> Document:
        """Read a workflow's draft."""
        return self._engine("workflow_drafts.get").workflow_drafts_get(workflow_id)

    @operation(
        "workflows",
        "drafts_put",
        "domain_write",
        rest=("PUT", "/api/workflows/{workflow_id}/draft"),
    )
    def workflow_drafts_put(self, workflow_id: str, graph: Document) -> Document:
        """Save a workflow draft. Nothing is published."""
        return self._engine("workflow_drafts.put").workflow_drafts_put(workflow_id, graph)

    @operation(
        "workflows", "tests_run", "domain_write", rest=("POST", "/api/workflows/{workflow_id}/test")
    )
    def workflow_tests_run(
        self, workflow_id: str, subgraph: list[str] | None = None, fake: bool = False
    ) -> Document:
        """Test-run a workflow's draft, whole or only the named nodes, on fake models if asked."""
        return self._engine("workflow_tests.run").workflow_tests_run(workflow_id, subgraph, fake)

    @operation(
        "workflows", "versions_list", "read", rest=("GET", "/api/workflows/{workflow_id}/versions")
    )
    def workflow_versions_list(self, workflow_id: str) -> list[Document]:
        """List a workflow's published versions."""
        return self._engine("workflow_versions.list").workflow_versions_list(workflow_id)

    @operation(
        "workflows",
        "versions_archive",
        "manage",
        rest=("POST", "/api/workflows/{workflow_id}/archive"),
    )
    def workflow_versions_archive(self, workflow_id: str, version: int) -> Document:
        """Archive one published version of a workflow."""
        return self._engine("workflow_versions.archive").workflow_versions_archive(
            workflow_id, version
        )

    @operation("workflows", "runs_list", "read", rest=("GET", "/api/workflow-runs"))
    def workflow_runs_list(self, workflow_id: str | None = None) -> list[Document]:
        """List workflow runs, newest first, optionally for one workflow."""
        return self._engine("workflow_runs.list").workflow_runs_list(workflow_id)

    @operation("workflows", "runs_get", "read", rest=("GET", "/api/workflow-runs/{run_id}"))
    def workflow_runs_get(self, run_id: str) -> Document:
        """Read one workflow run and its node states."""
        return self._engine("workflow_runs.get").workflow_runs_get(run_id)

    @operation(
        "workflows", "runs_explain", "read", rest=("GET", "/api/workflow-runs/{run_id}/explain")
    )
    def workflow_runs_explain(self, run_id: str) -> Document:
        """Explain what a workflow run did and why it stopped."""
        return self._engine("workflow_runs.explain").workflow_runs_explain(run_id)

    @operation("ops", "spans", "read", rest=("GET", "/api/ops/spans/{run_id}"))
    def ops_spans(self, run_id: str) -> Document:
        """Read a workflow run's spans: per node attempt, its model, tokens, cost and duration."""
        explained = self._engine("ops.spans").workflow_runs_explain(run_id)
        nodes = cast("list[Document]", explained.get("nodes") or [])
        return {
            "run_id": explained.get("run_id"),
            "status": explained.get("status"),
            "cost": explained.get("cost"),
            "spans": [
                {"node_id": node.get("node_id"), **span}
                for node in nodes
                for span in cast("list[Document]", node.get("spans") or [])
            ],
        }

    @operation("ops", "health", "read", rest=("GET", "/api/ops/health"))
    def ops_health(self) -> Document:
        """Read the data health: card freshness, feeds, connections, free disk and telemetry."""
        return data_health(self.home, self.library)

    @operation("ops", "note", "domain_write", rest=("POST", "/api/ops/notes"))
    def ops_note(self, note: NoteInput, observer: str = "") -> Document:
        """Save a diagnosis note on an observer's own ref; the inbox says it arrived.

        `observer` is the id the door vouched for, appended to the query it forwards; a call
        without one (a local-token client) has no observer ref to write on and is refused.
        """
        if not observer.strip():
            raise ControlError(
                "observer_required", "A diagnosis note is saved by an observer token's call.", 403
            )
        return self._save_note(observer.strip(), note.body)

    def _save_note(self, observer: str, body: str) -> Document:
        note_id = f"note-{uuid.uuid4().hex[:12]}"
        at = datetime.now(UTC).isoformat()
        ref = OBSERVER_REF.format(observer=observer)
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO observer_notes(id,observer,ref,body,at) VALUES(?,?,?,?,?)",
                (note_id, observer, ref, body, at),
            )
        return {
            "id": note_id,
            "kind": "info",
            "title": NOTE_TITLE,
            "observer": observer,
            "ref": ref,
            "body": body,
            "at": at,
        }

    def _notes(self) -> list[Document]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,observer,ref,body,at FROM observer_notes ORDER BY at"
            ).fetchall()
        return [
            {
                "id": row[0],
                "kind": "info",
                "title": NOTE_TITLE,
                "observer": row[1],
                "ref": row[2],
                "body": row[3],
                "at": row[4],
            }
            for row in rows
        ]

    @operation(
        "workflows", "runs_cancel", "manage", rest=("POST", "/api/workflow-runs/{run_id}/cancel")
    )
    def workflow_runs_cancel(self, run_id: str) -> Document:
        """Cancel a workflow run."""
        return self._engine("workflow_runs.cancel").workflow_runs_cancel(run_id)

    @operation(
        "workflows", "runs_resume", "manage", rest=("POST", "/api/workflow-runs/{run_id}/resume")
    )
    def workflow_runs_resume(self, run_id: str) -> Document:
        """Resume a paused or failed workflow run."""
        return self._engine("workflow_runs.resume").workflow_runs_resume(run_id)

    @operation("workflows", "triggers_list", "read", rest=("GET", "/api/triggers"))
    def workflow_triggers_list(self, workflow_id: str | None = None) -> list[Document]:
        """List workflow triggers, optionally for one workflow."""
        return self._engine("workflow_triggers.list").workflow_triggers_list(workflow_id)

    @operation("workflows", "triggers_create", "manage", rest=("POST", "/api/triggers"))
    def workflow_triggers_create(self, workflow_id: str, trigger: Document) -> Document:
        """Create a trigger for a published workflow. It starts disabled."""
        return self._engine("workflow_triggers.create").workflow_triggers_create(
            workflow_id, trigger
        )

    @operation(
        "workflows", "triggers_enable", "manage", rest=("POST", "/api/triggers/{trigger_id}/enable")
    )
    def workflow_triggers_enable(self, trigger_id: str) -> Document:
        """Enable a workflow trigger."""
        return self._engine("workflow_triggers.enable").workflow_triggers_enable(trigger_id)

    @operation(
        "workflows", "triggers_inputs", "manage", rest=("PUT", "/api/triggers/{trigger_id}/inputs")
    )
    def workflow_triggers_inputs(self, trigger_id: str, inputs: Document) -> Document:
        """Replace the inputs a workflow trigger passes to each run it fires."""
        return self._engine("workflow_triggers.inputs").workflow_triggers_inputs(trigger_id, inputs)

    @operation(
        "workflows",
        "triggers_disable",
        "manage",
        rest=("POST", "/api/triggers/{trigger_id}/disable"),
    )
    def workflow_triggers_disable(self, trigger_id: str) -> Document:
        """Disable a workflow trigger."""
        return self._engine("workflow_triggers.disable").workflow_triggers_disable(trigger_id)

    @operation(
        "workflows",
        "triggers_run_now",
        "manage",
        rest=("POST", "/api/triggers/{trigger_id}/run-now"),
    )
    def workflow_triggers_run_now(self, trigger_id: str) -> Document:
        """Fire a workflow trigger once, now."""
        return self._engine("workflow_triggers.run_now").workflow_triggers_run_now(trigger_id)

    @operation("workflows", "inbox_list", "read", rest=("GET", "/api/inbox"))
    def workflow_inbox_list(self) -> list[Document]:
        """List open workflow inbox items, then the diagnoses outside agents left."""
        return [*self._notes(), *self._engine("workflow_inbox.list").workflow_inbox_list()]

    @operation("apps_admin", "archive", "manage", rest=("POST", "/api/apps/{app_id}/archive"))
    def apps_archive(self, app_id: str) -> Document:
        """Archive a mini app."""
        return self._unavailable("apps.archive", ENGINE)


def _json_file(path: Path) -> object | None:
    """One log file as JSON, or None when it is absent or unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


def _age_s(at: object, now: datetime) -> float | None:
    found = _instant(at) if isinstance(at, str) else None
    return None if found is None else round((now - found).total_seconds(), 1)


def _host_rows(latest: object) -> list[Document]:
    """Each machine's newest heartbeat row: free disk, Library facts, Lab facts."""
    if not isinstance(latest, dict):
        return []
    found: list[Document] = []
    for row in cast("dict[str, object]", latest).values():
        if not isinstance(row, dict):
            continue
        fields = cast("dict[str, object]", row)
        if fields.get("subject") != "host":
            continue
        found.append(
            cast(
                "Document",
                {
                    "id": fields.get("id"),
                    "at": fields.get("at"),
                    "paused": fields.get("paused"),
                    "pause_state": fields.get("pause_state"),
                    "free_disk_bytes": fields.get("free_disk_bytes"),
                    "disk_floor_bytes": fields.get("disk_floor_bytes"),
                    "free_ram_bytes": fields.get("free_ram_bytes"),
                    "library": fields.get("library"),
                    "lab": fields.get("lab"),
                },
            )
        )
    return sorted(found, key=lambda row: str(row.get("id")))


def _card_rows(library: Library, now: datetime) -> list[Document]:
    """Every series card on `main`: its coverage, quality, and how long ago it was written."""
    found: list[Document] = []
    for item, object_id in library.store.heads_on("main"):
        if not item.startswith(SERIES_PREFIX):
            continue
        try:
            view = library.store.get(LIBRARY_OPERATOR, object_id)
        except LibraryRefused:
            continue
        coverage = view.fields.get("coverage")
        months = cast("dict[str, object]", coverage) if isinstance(coverage, dict) else {}
        at = view.annotations.get("created")
        found.append(
            cast(
                "Document",
                {
                    "item": item,
                    "kind": view.kind,
                    "title": view.title,
                    "at": at,
                    "age_s": _age_s(at, now),
                    "months": months.get("months"),
                    "last_month": months.get("last"),
                    "quality": view.fields.get("quality") or {},
                },
            )
        )
    return found


def _feed_rows(raw: object) -> Document:
    """DR6's feeds file: each feed's last run and its downloads. Absent until a feed writes it."""
    if raw is None:
        return cast("Document", {"present": False, "feeds": [], "downloads": []})
    if isinstance(raw, dict):
        fields = cast("dict[str, object]", raw)
        feeds = fields.get("feeds")
        downloads = fields.get("downloads")
        return cast(
            "Document",
            {
                "present": True,
                "at": fields.get("at"),
                "feeds": feeds if isinstance(feeds, list) else [],
                "downloads": downloads if isinstance(downloads, list) else [],
            },
        )
    return cast("Document", {"present": True, "feeds": [], "downloads": []})


def _connection_rows(raw: object) -> Document:
    """The health workflow's newest reading per external connection (AD-67)."""
    if raw is None:
        return cast("Document", {"present": False, "readings": []})
    fields = cast("dict[str, object]", raw) if isinstance(raw, dict) else {}
    readings = fields.get("readings")
    return cast(
        "Document",
        {
            "present": True,
            "at": fields.get("at"),
            "readings": readings if isinstance(readings, list) else [],
        },
    )


def _telemetry_row(raw: object) -> Document:
    """The exporter's counters (sent, dropped, failed, the last error) under `logs/`."""
    if not isinstance(raw, dict):
        return cast("Document", {"present": False})
    return cast("Document", {"present": True, **cast("dict[str, object]", raw)})


def _bucket_row(home: Path) -> Document:
    """The bucket remote `hub.toml` names, and what this home records about the last push."""
    said = "the server's host holds the last push in memory; no copy age is written to the home"
    try:
        document = tomllib.loads((home / "hub.toml").read_text(encoding="utf-8"))
    except OSError, UnicodeDecodeError, tomllib.TOMLDecodeError:
        return cast(
            "Document",
            {
                "configured": False,
                "remote": None,
                "copies": 1,
                "last_push_at": None,
                "age_s": None,
                "said": said,
            },
        )
    section = document.get("bucket")
    remote = cast("dict[str, object]", section).get("remote") if isinstance(section, dict) else None
    named = remote if isinstance(remote, str) and remote else None
    return cast(
        "Document",
        {
            "configured": named is not None,
            "remote": named,
            "copies": 2 if named is not None else 1,
            "last_push_at": None,
            "age_s": None,
            "said": said,
        },
    )


def data_health(home: Path, library: Library) -> Document:
    """The data health read (AD-69): facts from the home's JSON logs and the Library's cards.

    A host without an engine reads the files the engine's own write points leave, never the
    engine's models, because QMX control depends on no engine. An absent file is absent, never a
    zero: the read says so and the UI shows that.
    """
    now = datetime.now(UTC)
    logs = home / LOGS
    latest = _json_file(logs / "heartbeat-latest.json")
    return cast(
        "Document",
        {
            "at": now.isoformat(),
            "home": str(home),
            "hosts": _host_rows(latest),
            "cards": _card_rows(library, now),
            "feeds": _feed_rows(_json_file(logs / "feeds.json")),
            "connections": _connection_rows(_json_file(logs / "connections-health.json")),
            "telemetry": _telemetry_row(_json_file(logs / "telemetry.json")),
            "bucket": _bucket_row(home),
        },
    )


class WorkflowEngine(Protocol):
    """What `attach_workflow_engine` takes: the workflow doors, named and typed as on
    `ControlService`. The engine package implements it; this package never imports the engine.
    Every MANAGE door here was already asked of the operator (or came over REST with his
    bearer), so the engine may act on it as his."""

    def workflows_get(self, workflow_id: str) -> Document: ...
    def workflows_put(self, workflow_id: str, graph: Document) -> Document: ...
    def workflows_validate(self, graph: Document) -> Document: ...
    def workflows_run(self, workflow_id: str, inputs: Document | None) -> Document: ...
    def workflow_drafts_get(self, workflow_id: str) -> Document: ...
    def workflow_drafts_put(self, workflow_id: str, graph: Document) -> Document: ...
    def workflow_tests_run(
        self, workflow_id: str, subgraph: list[str] | None, fake: bool
    ) -> Document: ...
    def workflow_versions_list(self, workflow_id: str) -> list[Document]: ...
    def workflow_versions_archive(self, workflow_id: str, version: int) -> Document: ...
    def workflow_runs_list(self, workflow_id: str | None) -> list[Document]: ...
    def workflow_runs_get(self, run_id: str) -> Document: ...
    def workflow_runs_explain(self, run_id: str) -> Document: ...
    def workflow_runs_cancel(self, run_id: str) -> Document: ...
    def workflow_runs_resume(self, run_id: str) -> Document: ...
    def workflow_triggers_list(self, workflow_id: str | None) -> list[Document]: ...
    def workflow_triggers_create(self, workflow_id: str, trigger: Document) -> Document: ...
    def workflow_triggers_inputs(self, trigger_id: str, inputs: Document) -> Document: ...
    def workflow_triggers_enable(self, trigger_id: str) -> Document: ...
    def workflow_triggers_disable(self, trigger_id: str) -> Document: ...
    def workflow_triggers_run_now(self, trigger_id: str) -> Document: ...
    def workflow_inbox_list(self) -> list[Document]: ...
