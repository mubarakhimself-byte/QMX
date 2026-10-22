"""Forwarding: the PC's engine service answers for another owned instance (AD-21, AD-65).

Nothing replicates. A run's ledger stays its home's, so this module carries a question over the
tailnet and the answer back, and never writes the other store. A read that cannot be fetched
leaves the last rows this side saw, and marks them "server unreachable since ..." with those
values. An inbox answer travels the same way, and only the run's home folds it.

A host pass is neither a credential nor a run pass. It is one HMAC over the two instance names,
the calling principal and an expiry, keyed with the pairing key both machines hold (AD-12). It
names the PC and the principal, carries no key, and grants nothing beyond these verbs.

Two sides live here: `Forwarder` asks (on the PC), `Remote` answers (on any node), and
`forward_router` is the one route each node serves for the other.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
import urllib.request
from collections.abc import AsyncIterator, Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Final, Literal, Protocol, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import JsonValue

from qmx_engine.ports.inbox import Action
from qmx_engine.ports.settings import SettingsPort

HOME_ENGINE: Final = "home_engine"
"""The field every merged row carries: the host whose ledger owns it."""
UNREACHABLE: Final = "server unreachable since"
PASS_HEADER: Final = "X-QMX-Host-Pass"  # noqa: S105 (a header name, not a secret)
PASS_TTL_S: Final = 30.0
"""One pass per call, minted at the call: nothing on the wire outlives the question."""
CALL_TIMEOUT_S: Final = 10.0
"""A node that does not answer in ten seconds is unreachable now; the cache keeps its rows."""
STREAM_INTERVAL_S: Final = 1.0
"""How often a node's stream looks at its open items. One second is a stream round (AD-65)."""

type Verb = Literal[
    "runs.list",
    "runs.get",
    "cards",
    "spans",
    "inbox.list",
    "inbox.resolve",
    "incidents",
    "explain_trigger",
]
READ_VERBS: Final[frozenset[str]] = frozenset(
    {"runs.list", "runs.get", "cards", "spans", "inbox.list", "incidents", "explain_trigger"}
)
ANSWER_VERBS: Final[frozenset[str]] = frozenset({"inbox.resolve"})


class ForwardRefused(Exception):
    """A pass, the wire or the far side refused the question. `code` is the closed word."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HostPass:
    source: str
    target: str
    principal: str
    expires_at: float


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def mint_host_pass(
    key: str,
    *,
    source: str,
    target: str,
    principal: str,
    now: float | None = None,
    ttl: float = PASS_TTL_S,
) -> str:
    """One signed pass from `source` to `target` for `principal`. It carries no key value."""
    at = time.time() if now is None else now
    claims = {
        "v": 1,
        "from": source,
        "to": target,
        "principal": principal,
        "at": int(at),
        "exp": int(at + ttl),
    }
    body = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    mac = hmac.new(key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"


def verify_host_pass(key: str, token: str, *, target: str, now: float | None = None) -> HostPass:
    """The pass the caller minted, or a refusal. `target` is this instance's name."""
    at = time.time() if now is None else now
    if token.count(".") != 1:
        raise ForwardRefused("bad_pass", "the host pass is not one signed body")
    body, given = token.split(".", 1)
    expected = hmac.new(key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_unb64(given), expected):
        raise ForwardRefused("bad_pass", "the host pass does not verify")
    try:
        claims = cast("dict[str, JsonValue]", json.loads(_unb64(body)))
    except ValueError as error:
        raise ForwardRefused("bad_pass", "the host pass is not JSON") from error
    if claims.get("v") != 1:
        raise ForwardRefused("bad_pass", "another host pass version")
    if str(claims.get("to")) != target:
        raise ForwardRefused("wrong_engine", f"{claims.get('to')} is not {target}")
    expires = float(cast(float, claims.get("exp")))
    if expires <= at:
        raise ForwardRefused("expired_pass", "the host pass outlived its call")
    return HostPass(
        source=str(claims.get("from")),
        target=str(claims.get("to")),
        principal=str(claims.get("principal")),
        expires_at=expires,
    )


@dataclass(frozen=True, slots=True)
class Instance:
    """One owned engine instance this home may ask: its placement name and its engine base URL."""

    name: str
    url: str


def owned_instances(rows: Iterable[Mapping[str, JsonValue]], *, home: str) -> list[Instance]:
    """The owned placements with an engine URL, minus this home (AD-30's registry rows)."""
    found: list[Instance] = []
    for row in rows:
        name, url = str(row.get("name") or ""), str(row.get("engine_url") or "")
        if row.get("kind") != "owned" or not name or not url or name == home:
            continue
        found.append(Instance(name, url.rstrip("/")))
    return found


def placement_rows(settings: Mapping[str, object] | SettingsPort) -> list[Mapping[str, JsonValue]]:
    """The `[placement]` registry as rows: one per name, with the fields AD-30 gives it."""
    values: Mapping[str, object] = settings if isinstance(settings, Mapping) else settings.values()
    names = {
        key.split(".")[1] for key in values if key.startswith("placement.") and key.count(".") >= 2
    }
    return [
        cast(
            "Mapping[str, JsonValue]",
            {
                "name": name,
                "kind": values.get(f"placement.{name}.kind"),
                "engine_url": values.get(f"placement.{name}.engine_url"),
            },
        )
        for name in sorted(names)
    ]


@dataclass(frozen=True, slots=True)
class Homerow:
    """One row of a merged read and the host that owns it. `stale` means it is the last value
    seen, and `detail` says since when."""

    home_engine: str
    row: Mapping[str, JsonValue]
    stale: bool = False


def homerowed(home_engine: str, row: Mapping[str, JsonValue], *, stale: bool = False) -> Homerow:
    return Homerow(home_engine, {**row, HOME_ENGINE: home_engine}, stale)


def wall() -> str:
    """One RFC 3339 stamp in UTC, the shape every row carries."""
    return datetime.now(UTC).isoformat()


def plain(value: object) -> JsonValue:
    """One row as the wire carries it: a dataclass, a StrEnum and a tuple all become JSON."""
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in cast("Mapping[str, object]", value).items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [plain(item) for item in cast("Sequence[object]", value)]
    if is_dataclass(value) and not isinstance(value, type):
        return {key: plain(item) for key, item in asdict(value).items()}
    return cast("JsonValue", value)


def marked(home_engine: str, last: Sequence[Mapping[str, JsonValue]], since: str) -> list[Homerow]:
    """The rows of an instance that stopped answering, each saying since when, with last values."""
    detail = f"{UNREACHABLE} {since}"
    if not last:
        return [Homerow(home_engine, {HOME_ENGINE: home_engine, "detail": detail}, True)]
    return [Homerow(home_engine, {**row, "detail": detail}, True) for row in last]


class Down:
    """What one instance last said, and since when it has not said anything."""

    def __init__(self) -> None:
        self.seen: dict[str, list[Mapping[str, JsonValue]]] = {}
        self.at: str | None = None
        self.since: str | None = None

    def answered(self, verb: str, rows: list[Mapping[str, JsonValue]], at: str) -> None:
        self.seen[verb] = rows
        self.at = at
        self.since = None

    def failed(self, at: str) -> None:
        self.since = self.since or at

    def cache(self, verb: str) -> list[Mapping[str, JsonValue]]:
        return self.seen.get(verb, [])


def post_json(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
    """One JSON POST through the standard library: the engine names no HTTP client of its own."""
    request = urllib.request.Request(  # noqa: S310 (the home's own placement row)
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as answer:  # noqa: S310
        return cast("JsonValue", json.loads(answer.read()))


class Forwarder:
    """One instance, asked over the tailnet with a host pass minted per call."""

    def __init__(
        self,
        instance: Instance,
        *,
        key: str,
        source: str,
        principal: str,
        clock: Callable[[], float] = time.time,
        now: Callable[[], str] = wall,
        post: Callable[[str, Mapping[str, JsonValue], Mapping[str, str]], JsonValue] = post_json,
    ) -> None:
        self.instance = instance
        self.key = key
        self.source = source
        self.principal = principal
        self._clock = clock
        self._now = now
        self._post = post
        self.down = Down()

    def pass_for(self) -> str:
        return mint_host_pass(
            self.key,
            source=self.source,
            target=self.instance.name,
            principal=self.principal,
            now=self._clock(),
        )

    def read(self, verb: Verb, args: Mapping[str, JsonValue] | None = None) -> JsonValue:
        """One read. A failure leaves the last answer cached, marked unreachable by `rows`."""
        at = self._now()
        try:
            answer = self._post(
                f"{self.instance.url}/api/engine/forward",
                {"verb": verb, "args": dict(args or {})},
                {PASS_HEADER: self.pass_for()},
            )
        except OSError as error:
            self.down.failed(at)
            raise ForwardRefused("unreachable", str(error)) from error
        body = cast("Mapping[str, JsonValue]", answer)
        if not body.get("ok"):
            code = str(body.get("code") or body.get("detail") or "refused")
            raise ForwardRefused(code, str(body.get("message") or ""))
        value = body.get("value")
        if isinstance(value, list):
            self.down.answered(verb, cast("list[Mapping[str, JsonValue]]", value), at)
        return value

    def rows(self, verb: Verb, args: Mapping[str, JsonValue] | None = None) -> list[Homerow]:
        """The instance's rows, or its last rows marked unreachable since a failure began."""
        try:
            value = self.read(verb, args)
        except ForwardRefused:
            return marked(self.instance.name, self.down.cache(verb), self.down.since or self._now())
        return [
            homerowed(self.instance.name, row)
            for row in cast("list[Mapping[str, JsonValue]]", value)
        ]

    def answer(self, item_id: str, action: Action) -> JsonValue:
        """Send his answer to the run's home. The home folds it into its own ledger."""
        return self.read("inbox.resolve", {"item_id": item_id, "action": action})


class Answered(Protocol):
    """What the answering side must offer. `EngineService` is one; nothing else is imported."""

    name: str

    def answer(self, verb: str, args: Mapping[str, JsonValue], *, principal: str) -> JsonValue: ...

    def open_items(self) -> list[Mapping[str, JsonValue]]: ...


class Remote:
    """The verbs one instance answers for a forwarding caller, and its held stream."""

    def __init__(self, answered: Answered) -> None:
        self.answered = answered

    def answer(self, verb: str, args: Mapping[str, JsonValue], *, principal: str) -> JsonValue:
        if verb not in READ_VERBS and verb not in ANSWER_VERBS:
            raise ForwardRefused("no_verb", f"no verb {verb!r}")
        return self.answered.answer(verb, args, principal=principal)

    async def frames(self) -> AsyncIterator[dict[str, JsonValue]]:
        """`inbox` whenever the open set changes; a `keepalive` in between."""
        last: list[Mapping[str, JsonValue]] | None = None
        while True:
            items = self.answered.open_items()
            if items != last:
                yield {"kind": "inbox", "items": cast("JsonValue", [dict(row) for row in items])}
                last = items
            else:
                yield {"kind": "keepalive"}
            await asyncio.sleep(STREAM_INTERVAL_S)


def forward_router(remote: Remote, key: str) -> APIRouter:
    """The one route a node serves for the PC, and the held stream beside it (AD-65)."""
    router = APIRouter()

    @router.post("/api/engine/forward")
    def forward(body: dict[str, JsonValue], request: Request) -> dict[str, JsonValue]:
        token = request.headers.get(PASS_HEADER, "")
        try:
            pass_ = verify_host_pass(key, token, target=remote.answered.name)
            asked = cast("Mapping[str, JsonValue]", body.get("args") or {})
            value = remote.answer(str(body.get("verb")), asked, principal=pass_.principal)
        except ForwardRefused as refused:
            raise HTTPException(
                status_code=401 if refused.code.endswith("pass") else 400,
                detail={"code": refused.code, "message": str(refused)},
            ) from refused
        return {"ok": True, "value": value}

    @router.get("/api/engine/forward/stream")
    async def stream(request: Request) -> StreamingResponse:
        token = request.headers.get(PASS_HEADER, "")
        try:
            verify_host_pass(key, token, target=remote.answered.name)
        except ForwardRefused as refused:
            raise HTTPException(status_code=401, detail={"code": refused.code}) from refused

        async def frames() -> AsyncIterator[bytes]:
            async for frame in remote.frames():
                yield f"data: {json.dumps(frame, sort_keys=True)}\n\n".encode()

        return StreamingResponse(frames(), media_type="text/event-stream")

    _ = forward, stream
    return router
