"""The host route (Level 0 AD-46, Part C AD-304): `POST /api/host/forward`, where another host of
this home asks this one through a closed set of verbs.

The caller mints one host pass per call with the pairing key, carrying its real principal:
`operator` for his click, `agent:<id>` for a chat, `run:<id>` for a workflow. The door lets the
call past the local bearer (`qmx_host.door.host_pass_call`); this route verifies the pass against
this host's place name before it reads anything else, and a host that holds no pairing key answers
no pass at all. The principal rides the pass and never an argument: a `manage` operation and a job
of a `money` app answer only to `operator`. Every answer carries `schema_version`.

On This PC the route is mounted too, so one host build serves every role; nothing connects into
This PC (Level 0 AD-44), so there it answers nobody.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
from collections.abc import Awaitable, Callable, Mapping
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from fastapi import APIRouter, Request
from pydantic import JsonValue
from qmf.core import is_refusal
from qmf.data.series import OPEN_NAME, STATE_NAME
from qmx_apps.errors import AppError
from qmx_control.models import Document
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.forward import PASS_HEADER, ForwardRefused, verify_host_pass
from starlette.responses import FileResponse, JSONResponse, Response

from qmx_host.node_link import ROUTE_PATH, SCHEMA, NodeLink

if TYPE_CHECKING:
    from qmx_host.market_data import MarketDoor

HOST_ROUTE: Final = ("POST", ROUTE_PATH)
"""The one host-pass route this module serves, admitted by the door beside the other four."""
VERBS: Final = frozenset({"apps.ask", "apps.job", "heartbeats", "data.list", "data.fetch"})
"""The closed verb set. A new verb is a spine amendment (AD-46)."""
ANSWERS: Final = "host-route.db"
STATUS: Final[Mapping[str, int]] = {
    "bad_pass": 401,
    "wrong_engine": 401,
    "expired_pass": 401,
    "refused_principal": 403,
    "no_verb": 400,
    "bad_args": 400,
    "not_home": 409,
    "not_running": 409,
    "pin_stale": 409,
    "app_refused": 422,
}
KEPT_CODES: Final = frozenset({"not_running", "pin_stale"})
"""Supervisor refusals the route answers by their own code; any other is `app_refused`."""


class Refused(Exception):
    """One refusal, answered as `{schema_version, ok: false, code, message, value?}`."""

    def __init__(self, code: str, message: str, value: JsonValue = None) -> None:
        super().__init__(message)
        self.code = code
        self.value = value

    def answer(self) -> Document:
        found: Document = {
            "schema_version": SCHEMA,
            "ok": False,
            "code": self.code,
            "message": str(self),
        }
        if self.value is not None:
            found["value"] = self.value
        return found


def answered(value: JsonValue) -> Document:
    return {"schema_version": SCHEMA, "ok": True, "value": value}


def admits(principal: str, *, manage: bool = False, money: bool = False) -> bool:
    """Whether a pass principal may make an ask: a `manage` operation and a `money` app's job
    answer only to his principal (AD-46, R1-C-12); everything else answers every principal."""
    return principal == OPERATOR.principal or not (manage or money)


class Answers:
    """The first answer to each `manage` ask by op id, so a repeated ask applies once."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        with self._db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS answers (op_id TEXT PRIMARY KEY, answer TEXT NOT NULL)"
            )

    def _db(self) -> closing[sqlite3.Connection]:
        return closing(sqlite3.connect(self.path, isolation_level=None, timeout=30))

    def first(self, op_id: str) -> Document | None:
        with self._db() as db:
            row = db.execute("SELECT answer FROM answers WHERE op_id = ?", (op_id,)).fetchone()
        return None if row is None else cast(Document, json.loads(str(row[0])))

    def keep(self, op_id: str, answer: Document) -> None:
        with self._db() as db:
            db.execute(
                "INSERT OR IGNORE INTO answers VALUES (?, ?)",
                (op_id, json.dumps(answer, sort_keys=True)),
            )


def _no_door() -> MarketDoor | None:
    return None


@dataclass(frozen=True, slots=True)
class Answering:
    """What one host answers with: its node link (its place name, its supervisor and where each
    app is homed), its pairing key read per call, its heartbeat read and its price store. ``door``
    is the price store's market-data door, whose `verify` clears the pins This PC confirms; a host
    without one lists its partitions and clears nothing."""

    link: NodeLink
    key: Callable[[], str | None]
    heartbeats: Callable[[], Awaitable[Mapping[str, object]]]
    store_root: Callable[[], Path | None]
    answers: Answers
    door: Callable[[], MarketDoor | None] = _no_door


def _text(args: Mapping[str, JsonValue], name: str) -> str:
    found = args.get(name)
    if not isinstance(found, str) or not found:
        raise Refused("bad_args", f"args.{name} is a non-empty string")
    return found


def _table(args: Mapping[str, JsonValue], name: str) -> Document | None:
    found = args.get(name)
    if found is None:
        return None
    if not isinstance(found, dict):
        raise Refused("bad_args", f"args.{name} is a table")
    return found


def _strings(args: Mapping[str, JsonValue], name: str) -> list[str] | None:
    found = args.get(name)
    if found is None:
        return None
    if not isinstance(found, list) or not all(isinstance(item, str) for item in found):
        raise Refused("bad_args", f"args.{name} is a list of strings")
    return cast(list[str], found)


def _app_refused(error: AppError) -> Refused:
    if error.code in KEPT_CODES:
        return Refused(error.code, str(error))
    return Refused("app_refused", str(error), {"code": error.code})


class HostRoute:
    def __init__(self, answering: Answering) -> None:
        self.answering = answering
        self.link = answering.link

    def verify(self, token: str) -> str:
        """The pass's principal, or the refusal. No pairing key here answers no pass at all."""
        key = self.answering.key()
        if not key:
            raise Refused("bad_pass", "this host holds no pairing key, so it answers no host pass")
        try:
            return verify_host_pass(key, token, target=self.link.here).principal
        except ForwardRefused as refused:
            raise Refused(refused.code, str(refused)) from refused

    def definition(self, app: str) -> Document:
        """The installed manifest of an app homed here, or `not_home`."""
        if self.link.home_of(app) != self.link.here:
            raise Refused("not_home", f"{app} is homed on {self.link.home_of(app)}, not here")
        try:
            return cast(Document, self.link.apps.get(app)["definition"])
        except AppError as error:
            raise Refused("not_home", f"{app} is not installed on {self.link.here}") from error

    def ask(self, args: Document, op_id: str | None, principal: str) -> Document:
        app, operation = _text(args, "app"), _text(args, "operation")
        arguments = _table(args, "arguments") or {}
        pin = _table(args, "pin")
        operations = cast(Mapping[str, Document], self.definition(app).get("operations") or {})
        declared = operations.get(operation)
        if declared is None:
            raise Refused("no_verb", f"{app} declares no operation {operation}")
        manage = declared.get("approval") == "manage"
        if not admits(principal, manage=manage):
            raise Refused(
                "refused_principal",
                f"{operation} on {app} is a manage operation and answers only to the operator,"
                f" not {principal}",
            )
        if not manage:
            return answered(self._call(app, operation, arguments, pin))
        if not op_id:
            raise Refused("bad_args", "a manage ask carries its op_id")
        with self.answering.answers.lock:
            first = self.answering.answers.first(op_id)
            if first is not None:
                return first
            try:
                answer = answered(self._call(app, operation, arguments, pin))
            except Refused as refused:
                if refused.code != "app_refused":
                    raise
                answer = refused.answer()
            self.answering.answers.keep(op_id, answer)
            return answer

    def _call(
        self, app: str, operation: str, arguments: Document, pin: Document | None
    ) -> JsonValue:
        try:
            value = self.link.call_here(app, operation, arguments, pin=pin)
        except AppError as error:
            raise _app_refused(error) from error
        if isinstance(value, dict) and value.get("ok") is False:
            raise Refused("app_refused", f"{app} refused {operation}", value)
        return value

    def job(self, args: Document, principal: str) -> Document:
        app, job = _text(args, "app"), _text(args, "job")
        inputs, pin = _table(args, "inputs"), _table(args, "pin")
        profile = args.get("profile")
        if profile is not None and not isinstance(profile, str):
            raise Refused("bad_args", "args.profile is a string")
        if not admits(principal, money=self.definition(app).get("risk") == "money"):
            raise Refused(
                "refused_principal",
                f"{app} is a money app; its jobs answer only to the operator, not {principal}",
            )
        try:
            ran = self.link.apps.run_job(
                app, job, pin=pin, profile=profile, inputs=inputs, principal=principal
            )
        except AppError as error:
            raise _app_refused(error) from error
        return answered(ran)

    async def beats(self, args: Document) -> Document:
        found = dict(await self.answering.heartbeats())
        subjects = _strings(args, "subjects")
        latest = cast(Mapping[str, JsonValue], found.get("latest") or {})
        if subjects is not None:
            found["latest"] = {key: row for key, row in latest.items() if key in subjects}
        return answered(cast("JsonValue", found))

    def states(self) -> list[tuple[Path, Document]]:
        root = self.answering.store_root()
        if root is None:
            raise Refused("not_running", f"the price store on {self.link.here} is closed")
        found: list[tuple[Path, Document]] = []
        for path in sorted(root.glob(f"*/*/*/*/*/{STATE_NAME}")):
            found.append((path.parent, cast(Document, json.loads(path.read_text("utf-8")))))
        return found

    def listed(self, args: Document) -> Document:
        """The partitions committed here after the watermark. The fingerprints This PC lists as
        `confirmed` first go to the door's `verify`, and the answer says what it unpinned and
        what the door still pins; a door that cannot verify leaves `unpinned` out, so This PC
        confirms them again."""
        after = _table(args, "after") or {}
        mark = str(after.get("committed_at") or "")
        kinds, subjects = _strings(args, "kinds"), _strings(args, "subjects")
        confirmed = _strings(args, "confirmed") or []
        door = self.answering.door()
        pins: Document = {}
        if door is not None:
            cleared = door.verify(confirmed)
            if not is_refusal(cleared):
                pins["unpinned"] = list(cleared.value)
            pins["pinned"] = list(door.pinned())
        rows: list[JsonValue] = []
        newest = mark
        for folder, state in self.states():
            series = folder.parent.relative_to(cast(Path, self.answering.store_root())).parts
            at = str(state["at"])
            if at <= mark:
                continue
            if kinds is not None and series[2] not in kinds:
                continue
            if subjects is not None and series[1] not in subjects:
                continue
            newest = max(newest, at)
            rows.append(
                {
                    "key": state["key"],
                    "fingerprint": state["fingerprint"],
                    "bytes": state["bytes"],
                    "frozen": state["frozen"],
                    "born_on": self.link.here,
                    "committed_at": at,
                }
            )
        return answered({"partitions": rows, "watermark": {"committed_at": newest}, **pins})

    def fetched(self, args: Document) -> Response:
        fingerprint = _text(args, "fingerprint")
        for folder, state in self.states():
            if state["fingerprint"] != fingerprint:
                continue
            name = f"{fingerprint}.parquet" if state["frozen"] else OPEN_NAME
            return FileResponse(
                folder / name,
                media_type="application/octet-stream",
                headers={"X-QMX-Fingerprint": fingerprint, "X-QMX-Key": str(state["key"])},
            )
        raise Refused("bad_args", f"no partition on {self.link.here} has fingerprint {fingerprint}")

    async def answer(self, request: Request) -> Response:
        principal = self.verify(request.headers.get(PASS_HEADER, ""))
        try:
            body = await request.json()
        except ValueError as error:
            raise Refused("bad_args", "the body is one JSON table") from error
        if not isinstance(body, dict):
            raise Refused("bad_args", "the body is one JSON table")
        asked = cast(Document, body)
        if asked.get("schema_version") != SCHEMA:
            raise Refused("bad_args", f"this host reads schema_version {SCHEMA}")
        verb = asked.get("verb")
        if verb not in VERBS:
            raise Refused("no_verb", f"no verb {verb!r}; the verbs are {sorted(VERBS)}")
        args = _table(asked, "args") or {}
        op_id = asked.get("op_id")
        if op_id is not None and not isinstance(op_id, str):
            raise Refused("bad_args", "op_id is a string")
        match verb:
            case "apps.ask":
                found = await asyncio.to_thread(self.ask, args, op_id, principal)
            case "apps.job":
                found = await asyncio.to_thread(self.job, args, principal)
            case "heartbeats":
                found = await self.beats(args)
            case "data.list":
                found = await asyncio.to_thread(self.listed, args)
            case _:
                return await asyncio.to_thread(self.fetched, args)
        return JSONResponse(found, status_code=200 if found.get("ok") else _status(found))


def _status(answer: Document) -> int:
    return STATUS.get(str(answer.get("code")), 400)


def host_router(answering: Answering) -> APIRouter:
    """`POST /api/host/forward` on every host (AD-46)."""
    router = APIRouter()
    route = HostRoute(answering)

    @router.post(ROUTE_PATH)
    async def forward(request: Request) -> Response:
        try:
            return await route.answer(request)
        except Refused as refused:
            found = refused.answer()
            return JSONResponse(found, status_code=_status(found))

    _ = forward
    return router
