"""The node link (Part C AD-303): the one host module that asks a node app anything.

A node app's home is a place row (`[engine.placement.<name>]`) whose `apps` list names it, or this
machine when no row does. When the home is this machine the link calls the local supervisor;
otherwise it asks the home's host route (Level 0 AD-46, `qmx_host.host_route`) with one host pass
per call, minted with the real caller's principal and never a constant (Part C `BLAST-RADIUS.md`
C1).

Reads keep the newest answer per place and how many asks in a row it missed. A `manage` change
passes the per-node outbox in this host's store, keyed by its op id and stamped `issued_at` from
this host's clock, whether the node is reachable or not; a node that is down keeps it waiting, it
is retried with back-off, and it applies once (connections X1). The node, not the outbox, keeps
the order between changes (R1-C-05).

Before a trading node homed here is asked `deploy`, the link stages the deployment's files: each
file the document names by fingerprint is copied from this machine's Library into
`data/deployments/<deployment_id>/in/` of the node's volume and verified, with no size limit. A
file this Library does not hold yet answers `files_missing` with its paths, so the outbox keeps
the change waiting until the hub brings it (AD-303).

Four callers use it: the core `node` rows (through `node_read`), `app_op`'s `Placements.remote`,
and later the UI's node routes and the promote action.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, cast

import httpx
from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_control.models import Document
from qmx_engine.admission import setting
from qmx_engine.control_door import PRINCIPAL
from qmx_engine.nodes.app_op import Placements
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.forward import (
    PASS_HEADER,
    HostKeys,
    mint_host_pass,
    owned_instances,
    placement_rows,
)

NODE_APP: Final = "trading-node"
NODE_READS: Final = frozenset(
    {"status", "units", "positions", "journal_tail", "passport", "deployments"}
)
"""The node operations this link reads; none of them changes anything (AD-302)."""
ROW_READS: Final = frozenset({"units", "deployments"})
"""The reads that answer one row per deployment, where a refused deploy reads too."""
SCHEMA: Final = "qmx.host.forward/1"
ROUTE_PATH: Final = "/api/host/forward"
OUTBOX: Final = "node-link.db"
WAITING_CODES: Final = frozenset({"not_running", "files_missing", "budget_exceeded"})
"""Answers after which a change keeps waiting: the node app is down or not ready yet."""
INTERVAL_S: Final = 60.0
"""`[engine] node_link.interval_s`: seconds between reads of each node's heartbeats."""
UNREACHABLE_AFTER: Final = 3.0
"""`[engine] node_link.unreachable_after`: missed reads before a node shows "unreachable since"."""
RETRY_FIRST_S: Final = 5.0
"""`[engine] node_link.retry_first_s`: the first wait before a waiting change is sent again."""
RETRY_MOST_S: Final = 120.0
"""`[engine] node_link.retry_most_s`: the longest wait between two sends of a waiting change."""
CALL_TIMEOUT_S: Final = 10.0
"""How long a read or a change waits for its answer; a job waits as long as it runs."""

type State = Literal["waiting", "applied", "refused"]
type Post = Callable[[str, Mapping[str, JsonValue], Mapping[str, str], float | None], JsonValue]
type Blobs = Callable[[str], Iterable[bytes] | None]
"""This machine's Library bytes by fingerprint (`sha256:<hex>`), or None when it holds none."""


class Unreachable(Exception):
    """The far host did not answer at all."""


def post_json(
    url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], timeout: float | None
) -> JsonValue:
    """One JSON POST to a host route. A refusal answers JSON with a 4xx status, and is returned."""
    try:
        answer = httpx.post(
            url,
            json=dict(body),
            headers=dict(headers),
            timeout=httpx.Timeout(timeout, connect=CALL_TIMEOUT_S),
        )
    except httpx.TransportError as error:
        raise Unreachable(f"{type(error).__name__}: {error}") from error
    try:
        return cast("JsonValue", answer.json())
    except ValueError as error:
        raise Unreachable(f"answered HTTP {answer.status_code} with no JSON") from error


def wall(at: float) -> str:
    return datetime.fromtimestamp(at, UTC).isoformat()


@dataclass(frozen=True, slots=True)
class Place:
    """One owned machine this host may ask: its place name, its host's base URL and the apps
    homed there."""

    name: str
    url: str
    apps: tuple[str, ...]


def places(values: Mapping[str, object], *, here: str) -> dict[str, Place]:
    """The owned places other than `here` that can run work, from the flat engine settings."""
    found: dict[str, Place] = {}
    for instance in owned_instances(placement_rows(values), home=here):
        listed = values.get(f"placement.{instance.name}.apps")
        apps = (
            tuple(str(app) for app in cast("Sequence[object]", listed))
            if isinstance(listed, list | tuple)
            else ()
        )
        found[instance.name] = Place(instance.name, instance.url, apps)
    return found


@dataclass(slots=True)
class Seen:
    """What one place last answered, and how its asks have gone since."""

    misses: int = 0
    since: str | None = None
    latest: JsonValue = None
    retry_at: float = 0.0
    delay: float = 0.0
    read_at: float = float("-inf")


@dataclass(frozen=True, slots=True)
class Change:
    """One `manage` change in the outbox."""

    op_id: str
    place: str
    app: str
    operation: str
    arguments: Document
    principal: str
    issued_at: str
    state: State
    answer: JsonValue

    def document(self) -> Document:
        shown: Document = {
            "op_id": self.op_id,
            "place": self.place,
            "app": self.app,
            "operation": self.operation,
            "issued_at": self.issued_at,
            "state": self.state,
        }
        if self.state == "waiting":
            shown["detail"] = f"waiting for {self.place}"
        else:
            shown["answer"] = self.answer
        return shown


class Outbox:
    """The per-node outbox: one row per op id, in the order it was issued (AD-303)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with self._db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS outbox (seq INTEGER PRIMARY KEY AUTOINCREMENT,"
                " op_id TEXT NOT NULL UNIQUE, place TEXT NOT NULL, app TEXT NOT NULL,"
                " operation TEXT NOT NULL, arguments TEXT NOT NULL, principal TEXT NOT NULL,"
                " issued_at TEXT NOT NULL, state TEXT NOT NULL, answer TEXT)"
            )

    def _db(self) -> closing[sqlite3.Connection]:
        return closing(sqlite3.connect(self.path, isolation_level=None, timeout=30))

    def put(self, change: Change) -> None:
        """Queue a change once: a repeated op id keeps the first."""
        with self._db() as db:
            db.execute(
                "INSERT OR IGNORE INTO outbox (op_id, place, app, operation, arguments, principal,"
                " issued_at, state) VALUES (?, ?, ?, ?, ?, ?, ?, 'waiting')",
                (
                    change.op_id,
                    change.place,
                    change.app,
                    change.operation,
                    json.dumps(change.arguments, sort_keys=True),
                    change.principal,
                    change.issued_at,
                ),
            )

    def settle(self, op_id: str, state: State, answer: JsonValue) -> None:
        with self._db() as db:
            db.execute(
                "UPDATE outbox SET state = ?, answer = ? WHERE op_id = ?",
                (state, json.dumps(answer, sort_keys=True), op_id),
            )

    def get(self, op_id: str) -> Change | None:
        with self._db() as db:
            row = db.execute(f"{_SELECT} WHERE op_id = ?", (op_id,)).fetchone()
        return None if row is None else _change(row)

    def refused_deploys(self, place: str) -> list[Change]:
        """Every deploy the place's node refused, in the order he clicked them."""
        with self._db() as db:
            rows = db.execute(
                f"{_SELECT} WHERE place = ? AND operation = 'deploy' AND state = 'refused'"
                " ORDER BY seq",
                (place,),
            ).fetchall()
        return [_change(row) for row in rows]

    def waiting(self, place: str) -> list[Change]:
        with self._db() as db:
            rows = db.execute(
                f"{_SELECT} WHERE place = ? AND state = 'waiting' ORDER BY seq", (place,)
            ).fetchall()
        return [_change(row) for row in rows]

    def places(self) -> list[str]:
        with self._db() as db:
            rows = db.execute("SELECT DISTINCT place FROM outbox WHERE state = 'waiting'")
            return [str(row[0]) for row in rows.fetchall()]


_SELECT: Final = (
    "SELECT op_id, place, app, operation, arguments, principal, issued_at, state, answer"
    " FROM outbox"
)


def _change(row: tuple[object, ...]) -> Change:
    answer = row[8]
    return Change(
        op_id=str(row[0]),
        place=str(row[1]),
        app=str(row[2]),
        operation=str(row[3]),
        arguments=cast(Document, json.loads(str(row[4]))),
        principal=str(row[5]),
        issued_at=str(row[6]),
        state=cast(State, row[7]),
        answer=None if answer is None else cast("JsonValue", json.loads(str(answer))),
    )


class NodeLink:
    """How this host asks the node apps of its home, here or on another machine."""

    def __init__(
        self,
        home: Path,
        *,
        here: str,
        apps: Supervisor,
        settings: Callable[[], Mapping[str, object]],
        pass_keys: Callable[[], HostKeys],
        tuning: Callable[[], Mapping[str, object]] = dict,
        clock: Callable[[], float] = time.time,
        post: Post = post_json,
        blobs: Blobs | None = None,
    ) -> None:
        """`settings` are the flat engine settings the place rows live in; `tuning` is the
        `[engine.node_link]` table; `pass_keys` reads this home's pass keys, none before pairing;
        `blobs` reads this machine's Library, which a deployment's files are staged from."""
        self.here = here
        self.apps = apps
        self.blobs = blobs
        self.settings = settings
        self.pass_keys = pass_keys
        self.tuning = tuning
        self.clock = clock
        self.post = post
        self.outbox = Outbox(home / OUTBOX)
        self.seen: dict[str, Seen] = {}
        self._sending = threading.Lock()

    def places(self) -> dict[str, Place]:
        return places(self.settings(), here=self.here)

    def home_of(self, app: str) -> str:
        """The place whose row lists `app`, or this machine when no row does."""
        return next((p.name for p in self.places().values() if app in p.apps), self.here)

    def reachable(self, place: str) -> bool:
        """This machine always; another place unless its last ask went unanswered."""
        return place == self.here or self._seen(place).misses == 0

    def set_up(self) -> bool:
        """Whether a trading node exists: a place row lists it, or it is installed here."""
        if self.home_of(NODE_APP) != self.here:
            return True
        try:
            self.apps.get(NODE_APP)
        except AppError:
            return False
        return True

    def call(
        self,
        app: str,
        operation: str,
        arguments: Document,
        *,
        principal: str,
        pin: Document | None = None,
    ) -> JsonValue:
        """One operation of `app` at its home. A refusal raises `AppError` with its code."""
        home = self.home_of(app)
        if home == self.here:
            return self.call_here(app, operation, arguments, pin=pin)
        asked: Document = {"app": app, "operation": operation, "arguments": arguments}
        if pin is not None:
            asked["pin"] = pin
        return _value(self._ask(home, "apps.ask", asked, principal=principal))

    def call_here(
        self, app: str, operation: str, arguments: Document, *, pin: Document | None = None
    ) -> JsonValue:
        """The local supervisor's call; its answer is the operation's own. A trading node's
        `deploy` is asked only once every file it names is staged."""
        if app == NODE_APP and operation == "deploy":
            missing = self.stage(arguments)
            if missing:
                return {
                    "ok": False,
                    "code": "files_missing",
                    "message": f"this machine's Library does not hold {missing[0]} yet",
                    "value": {"missing": cast("list[JsonValue]", missing)},
                }
        return self.apps.call(app, operation, arguments, pin=pin).get("result")

    def stage(self, arguments: Document) -> list[str]:
        """Copy each file of the deployment into the node's staging folder, verified by its
        fingerprint, and answer the paths this Library could not supply. A file already there
        with its fingerprint is kept; a document the node cannot read stages nothing and is
        refused by the node itself."""
        document = arguments.get("deployment")
        if not isinstance(document, dict):
            return []
        deployment_id, files = document.get("deployment_id"), document.get("files")
        if not isinstance(deployment_id, str) or not isinstance(files, list):
            return []
        root = Volume(self.apps.home, NODE_APP).root / "data" / "deployments" / deployment_id
        folder = root / "in"
        missing: list[str] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            path, fingerprint = item.get("path"), item.get("fingerprint")
            if not isinstance(path, str) or not isinstance(fingerprint, str):
                continue
            target = (folder / path).resolve()
            if not target.is_relative_to(folder.resolve()):
                continue
            if target.is_file() and _fingerprint(target) == fingerprint:
                continue
            if not self._copy(fingerprint, target):
                missing.append(path)
        return missing

    def _copy(self, fingerprint: str, target: Path) -> bool:
        chunks = None if self.blobs is None else self.blobs(fingerprint)
        if chunks is None:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(f"{target.name}.part")
        digest = hashlib.sha256()
        with part.open("wb") as handle:
            for chunk in chunks:
                digest.update(chunk)
                handle.write(chunk)
        if f"sha256:{digest.hexdigest()}" != fingerprint:
            part.unlink()
            return False
        os.replace(part, target)
        return True

    def read(self, operation: str, arguments: Document, *, principal: str) -> JsonValue | None:
        """One of the trading node's reads, or None when no trading node is set up yet."""
        if operation not in NODE_READS:
            raise AppError("not_a_read", f"{operation} is not one of the node's reads", 400)
        if not self.set_up():
            return None
        answer = self.call(NODE_APP, operation, arguments, principal=principal)
        if operation not in ROW_READS:
            return answer
        wanted = arguments.get("deployment_id")
        refused = self.outbox.refused_deploys(self.home_of(NODE_APP))
        return _with_refused(operation, answer, refused, wanted)

    def node_read(self, operation: str, arguments: Document) -> JsonValue | None:
        """`read` as the caller the door named, for the core `node` rows (`qmx_tools.NodeReads`)."""
        return self.read(operation, arguments, principal=PRINCIPAL.get().principal)

    def heartbeats(self, place: str, *, principal: str) -> JsonValue:
        """A place's newest heartbeat rows, kept as its latest values."""
        value = _value(self._ask(place, "heartbeats", {}, principal=principal))
        self._seen(place).latest = value
        return value

    def remote_job(
        self,
        place: str,
        app: str,
        job: str,
        pin: Document | None,
        profile: str | None,
        inputs: Document | None = None,
    ) -> Document:
        """`app_op`'s `Placements.remote`: run a job at its home as the run that asked."""
        asked: Document = {"app": app, "job": job}
        for name, given in (("pin", pin), ("profile", profile), ("inputs", inputs)):
            if given is not None:
                asked[name] = given
        principal = PRINCIPAL.get().principal
        answer = self._ask(place, "apps.job", asked, principal=principal, timeout=None)
        return cast(Document, _value(answer))

    def placements(self) -> Placements:
        """Where `app_op` runs a job (Level 0 AD-46): a job belongs to its app's home."""
        return Placements(
            state_of=lambda _app, _job: "instance",
            home_of=self.home_of,
            here=self.here,
            reachable=self.reachable,
            remote=self.remote_job,
        )

    def change(
        self, app: str, operation: str, arguments: Document, *, principal: str, op_id: str
    ) -> Change:
        """Queue one `manage` change for `app`'s home and send what waits there now. A repeated
        op id answers the first change's state. Only the operator changes a node, so another
        principal is refused before the outbox holds anything, wherever the node is homed."""
        if principal != OPERATOR.principal:
            raise AppError(
                "refused_principal",
                f"{operation} on {app} is a manage operation and answers only to the operator,"
                f" not {principal}",
                403,
            )
        home = self.home_of(app)
        issued_at = wall(self.clock())
        stamped: Document = {**arguments, "op_id": op_id, "issued_at": issued_at}
        self.outbox.put(
            Change(op_id, home, app, operation, stamped, principal, issued_at, "waiting", None)
        )
        self.flush(home)
        return cast(Change, self.outbox.get(op_id))

    def flush(self, place: str) -> int:
        """Send the place's waiting changes in order until one finds the node away. Answers how
        many settled."""
        settled = 0
        with self._sending:
            for change in self.outbox.waiting(place):
                try:
                    state, answer = self._send(change)
                except Unreachable, AppError:
                    self._backoff(place)
                    break
                if state == "waiting":
                    self._backoff(place)
                    break
                self.outbox.settle(change.op_id, state, answer)
                settled += 1
            else:
                self._seen(place).delay = 0.0
        return settled

    def _send(self, change: Change) -> tuple[State, JsonValue]:
        if change.place == self.here:
            try:
                value = self.call_here(change.app, change.operation, change.arguments)
            except AppError as error:
                refusal: Document = {"ok": False, "code": error.code, "message": str(error)}
                return ("waiting" if error.code in WAITING_CODES else "refused"), refusal
            refused = isinstance(value, dict) and value.get("ok") is False
            if refused and cast("Document", value).get("code") in WAITING_CODES:
                return "waiting", value
            return ("refused" if refused else "applied"), value
        asked: Document = {
            "app": change.app,
            "operation": change.operation,
            "arguments": change.arguments,
        }
        answer = self._send_to(
            change.place, "apps.ask", asked, principal=change.principal, op_id=change.op_id
        )
        if answer.get("ok") is True:
            return "applied", answer.get("value")
        if answer.get("code") in WAITING_CODES:
            return "waiting", dict(answer)
        return "refused", dict(answer)

    def _ask(
        self,
        place: str,
        verb: str,
        args: Document,
        *,
        principal: str,
        timeout: float | None = CALL_TIMEOUT_S,
    ) -> Mapping[str, JsonValue]:
        try:
            return self._send_to(place, verb, args, principal=principal, timeout=timeout)
        except Unreachable as error:
            raise AppError(
                "placement_unreachable", f"{place} did not answer: {error}", 503
            ) from error

    def _send_to(
        self,
        place: str,
        verb: str,
        args: Document,
        *,
        principal: str,
        op_id: str | None = None,
        timeout: float | None = CALL_TIMEOUT_S,
    ) -> Mapping[str, JsonValue]:
        """One ask of `place`'s host route; a missed answer counts against the place."""
        found = self.places().get(place)
        key = self.pass_keys().get(place)
        if found is None or not key:
            raise AppError(
                "placement_unreachable",
                f"{place} has no owned place row with a host URL, or this home holds no pass key"
                f" for {place}; set {place} up again in Connect to pair it",
                409,
            )
        held = mint_host_pass(
            key, source=self.here, target=place, principal=principal, now=self.clock()
        )
        body: Document = {"schema_version": SCHEMA, "verb": verb, "args": args}
        if op_id is not None:
            body["op_id"] = op_id
        seen = self._seen(place)
        try:
            answer = self.post(f"{found.url}{ROUTE_PATH}", body, {PASS_HEADER: held}, timeout)
        except Unreachable:
            seen.misses += 1
            seen.since = seen.since or wall(self.clock())
            raise
        seen.misses, seen.since = 0, None
        if not isinstance(answer, dict) or "schema_version" not in answer:
            raise AppError("bad_answer", f"{place} answered no host-route answer", 502)
        return answer

    def _seen(self, place: str) -> Seen:
        return self.seen.setdefault(place, Seen())

    def _backoff(self, place: str) -> None:
        tuning = self.tuning()
        first = setting(tuning, "retry_first_s", RETRY_FIRST_S)
        most = setting(tuning, "retry_most_s", RETRY_MOST_S)
        seen = self._seen(place)
        seen.delay = min(most, seen.delay * 2) if seen.delay else first
        seen.retry_at = self.clock() + seen.delay

    def state(self, place: str) -> Document:
        """A place's latest values, marked "unreachable since" after enough missed reads."""
        seen = self._seen(place)
        shown: Document = {"place": place, "latest": seen.latest}
        after = setting(self.tuning(), "unreachable_after", UNREACHABLE_AFTER)
        if seen.since is not None and seen.misses >= after:
            shown["detail"] = f"unreachable since {seen.since}"
        return shown

    def tick(self) -> float:
        """One round: read each place's heartbeats when they are due, then send the changes
        waiting for it once its back-off has passed or it has just answered. Answers how many
        seconds to wait before the next round."""
        interval = setting(self.tuning(), "interval_s", INTERVAL_S)
        waiting = set(self.outbox.places())
        wake = interval
        for place in sorted({*self.places(), *waiting} - {self.here}):
            seen, now = self._seen(place), self.clock()
            answered = False
            if now >= seen.read_at + interval:
                seen.read_at = now
                try:
                    self.heartbeats(place, principal=f"host:{self.here}")
                    answered = True
                except AppError:
                    pass
            if place in waiting and (answered or now >= seen.retry_at):
                self.flush(place)
            wake = min(wake, seen.read_at + interval - now)
            if self.outbox.waiting(place):
                wake = min(wake, seen.retry_at - now)
        if self.here in waiting:
            self.flush(self.here)
        return max(wake, 1.0)

    async def keep(self) -> None:
        """`tick` until cancelled, waking for the next heartbeat read or the next retry."""
        while True:
            await asyncio.sleep(await asyncio.to_thread(self.tick))


def _refused_row(operation: str, change: Change) -> tuple[str, Document]:
    """A refused deploy as the node's own row for it reads: its id, then the row, whose state
    says refused and whose detail is the node's code and message."""
    document = cast(Document, change.arguments.get("deployment") or {})
    answer = cast(Document, change.answer or {})
    unit = document.get("unit")
    detail = f"{answer.get('code')}: {answer.get('message')}"
    deployment_id = str(document.get("deployment_id"))
    if operation == "deployments":
        return deployment_id, {
            "deployment_id": deployment_id,
            "unit": unit,
            "state": "refused",
            "detail": detail,
            "accepted_at": None,
        }
    return deployment_id, {
        "deployment_id": deployment_id,
        "unit_id": cast(Document, unit).get("id") if isinstance(unit, dict) else None,
        "state": "refused",
        "detail": detail,
        "warm": None,
        "kill_level": "GREEN",
    }


def _with_refused(
    operation: str, answer: JsonValue, refused: Sequence[Change], wanted: JsonValue
) -> JsonValue:
    """The node's rows, then a row for each deploy it refused. A deployment the node holds reads
    as the node has it, since an ask that timed out files as refused and may have reached it. A
    node here answers its envelope and a node elsewhere its value, and each keeps its shape."""
    enveloped = isinstance(answer, dict)
    if enveloped and cast(Document, answer).get("ok") is not True:
        return answer
    found = cast(Document, answer).get("value") if enveloped else answer
    if not isinstance(found, list):
        return answer
    held = {cast(Document, row).get("deployment_id") for row in found if isinstance(row, dict)}
    rows: list[JsonValue] = list(found)
    for deployment_id, row in (_refused_row(operation, change) for change in refused):
        if deployment_id not in held and wanted in (None, deployment_id):
            rows.append(row)
    return {**cast(Document, answer), "value": rows} if enveloped else rows


def _fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _value(answer: Mapping[str, JsonValue]) -> JsonValue:
    if answer.get("ok") is True:
        return answer.get("value")
    raise AppError(
        str(answer.get("code") or "refused"), str(answer.get("message") or "refused"), 409
    )
