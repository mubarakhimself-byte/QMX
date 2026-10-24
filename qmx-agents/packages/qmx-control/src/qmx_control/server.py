"""Transport adapters over the same bound service methods."""

import http.client
import json
import os
import re
import secrets
import ssl
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any, Final
from urllib.parse import urlsplit

import anyio
import keyring
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from qmx_apps.errors import AppError
from qmx_library.client import HubClient
from qmx_library.port import LibraryRefused
from qmx_remote.models import RemoteError
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_control.catalog import control_rows, rest_routes
from qmx_control.service import ControlError, ControlService, EventTopic

CHUNK: Final = 1 << 20
"""Bytes one upload moves at a time on its way through this host (Library AD-27)."""
UPLOAD_ROUTE: Final = "/api/library/upload"
"""The one upload door on the PC (AD-27). The bytes go on to the server as they arrive, and the
staging copy stays here until the server says two durable copies exist (AD-10)."""
STAGING: Final = "uploads"
COPIES_REQUIRED: Final = 2
"""Durable copies an uploaded blob needs before this PC gives up its staging copy (AD-10)."""
UPLOAD_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,128}")


def local_token() -> str:
    """Keep the laptop token in the OS vault, never in the home directory."""
    token = keyring.get_password("qmx/control-token", "control-token")
    if token is None:
        token = secrets.token_urlsafe(32)
        keyring.set_password("qmx/control-token", "control-token", token)
    return token


class Part:
    """One upload staged on the PC while its bytes stream on to the server (Library AD-27).

    The part is the state: a resumed request re-hashes the bytes it holds before it appends one
    more, so the two sides of the door cannot disagree about what offset means. A finished upload
    keeps this copy until the server reports two durable copies, then gives it up (AD-10).
    """

    def __init__(
        self,
        home: Path,
        upload_id: str,
        *,
        offset: int = 0,
        partial_sha256: str | None = None,
    ) -> None:
        if UPLOAD_ID.fullmatch(upload_id) is None:
            raise LibraryRefused("invalid_upload", f"{upload_id!r} is not an upload id")
        self.folder = home / STAGING
        self.path = self.folder / f"{upload_id}.part"
        self.manifest_path = self.folder / f"{upload_id}.json"
        self.hasher = sha256()
        self.held = 0
        if offset == 0:
            self.folder.mkdir(parents=True, exist_ok=True)
            self.path.unlink(missing_ok=True)
        else:
            if not self.path.exists() or self.path.stat().st_size != offset:
                raise LibraryRefused(
                    "offset_mismatch", f"{upload_id} does not hold the {offset} bytes resumed from"
                )
            with self.path.open("rb") as handle:
                while data := handle.read(CHUNK):
                    self.hasher.update(data)
                    self.held += len(data)
            if partial_sha256 is not None and self.hasher.hexdigest() != partial_sha256:
                raise LibraryRefused(
                    "hash_mismatch", f"{upload_id} does not hash to what the client resumed"
                )
        self.handle = self.path.open("ab")

    @property
    def sha256(self) -> str:
        return self.hasher.hexdigest()

    def write(self, chunk: bytes) -> int:
        if chunk:
            self.handle.write(chunk)
            self.hasher.update(chunk)
            self.held += len(chunk)
        return self.held

    def close(self) -> None:
        if not self.handle.closed:
            self.handle.flush()
            os.fsync(self.handle.fileno())
            self.handle.close()

    def keep(self, landed: dict[str, Any], *, name: str, media_type: str) -> bool:
        """Record what the server holds; say whether this staging copy stays (AD-10)."""
        self.close()
        manifest = {
            "upload_id": self.path.stem,
            "blob_id": landed.get("blob_id"),
            "sha256": landed.get("sha256"),
            "offset": self.held,
            "bytes": landed.get("bytes"),
            "copies": landed.get("copies", 0),
            "name": name,
            "media_type": media_type,
        }
        self.manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        if int(manifest["copies"] or 0) >= COPIES_REQUIRED:
            self.release()
            return False
        return True

    def release(self) -> None:
        self.path.unlink(missing_ok=True)
        self.manifest_path.unlink(missing_ok=True)

    @classmethod
    def staged(cls, home: Path, upload_id: str) -> dict[str, Any] | None:
        """What this PC holds for one upload id: its partial, or the finished copy it kept."""
        if UPLOAD_ID.fullmatch(upload_id) is None:
            raise LibraryRefused("invalid_upload", f"{upload_id!r} is not an upload id")
        folder = home / STAGING
        part = folder / f"{upload_id}.part"
        manifest = folder / f"{upload_id}.json"
        if manifest.exists():
            found = json.loads(manifest.read_text(encoding="utf-8"))
            found["staging"] = part.exists()
            return found
        if not part.exists():
            return None
        hasher = sha256()
        held = 0
        with part.open("rb") as handle:
            while data := handle.read(CHUNK):
                hasher.update(data)
                held += len(data)
        return {"upload_id": upload_id, "offset": held, "sha256": hasher.hexdigest(), "staging": True}


def _hub_connection(url: str) -> http.client.HTTPConnection:
    parts = urlsplit(url)
    if parts.scheme == "https":
        return http.client.HTTPSConnection(
            parts.hostname, parts.port, timeout=300, context=ssl.create_default_context()
        )
    return http.client.HTTPConnection(parts.hostname, parts.port, timeout=300)


def _answer(connection: http.client.HTTPConnection) -> tuple[int, dict[str, Any]]:
    answer = connection.getresponse()
    body = answer.read()
    return answer.status, {} if not body else json.loads(body)


def upload_router(home: Path) -> APIRouter:
    """`POST /api/library/upload` on the PC: stream the bytes on, keep the staging copy (AD-27).

    The PC does not hold the Library store after the flip (AD-19), so the bytes go to the server
    the moment they arrive here: one read from the client, one write to the staging part, one
    socket send to the hub. `Content-Length` frames one request; a resumed request carries the
    offset and the hash of what the PC already holds. QMX sets no size limit of its own.
    """
    router = APIRouter()

    @router.post(UPLOAD_ROUTE)
    async def upload(request: Request) -> JSONResponse:
        given = request.headers.get("Content-Length")
        if given is None:
            raise HTTPException(http.client.LENGTH_REQUIRED, detail={"code": "length_required"})
        upload_id = request.headers.get("X-Upload-Id") or secrets.token_hex(16)
        name = request.headers.get("X-Upload-Name", "")
        media_type = request.headers.get("Content-Type", "application/octet-stream")
        try:
            offset = int(request.headers.get("X-Upload-Offset") or 0)
        except ValueError:
            raise HTTPException(
                http.client.BAD_REQUEST, detail={"code": "invalid_offset"}
            ) from None
        try:
            client = await anyio.to_thread.run_sync(HubClient.connect, home)
            part = await anyio.to_thread.run_sync(
                lambda: Part(
                    home,
                    upload_id,
                    offset=offset,
                    partial_sha256=request.headers.get("X-Upload-Partial-Sha256"),
                )
            )
        except LibraryRefused as refused:
            raise HTTPException(
                http.client.CONFLICT, detail={"code": refused.code, "message": str(refused)}
            ) from None
        try:
            connection = _hub_connection(client.url)
        except ValueError as error:
            raise HTTPException(
                http.client.BAD_GATEWAY, detail={"code": "no_hub_url", "message": str(error)}
            ) from None
        partial = part.sha256
        total = request.headers.get("X-Upload-Total")
        try:
            connection.putrequest("POST", UPLOAD_ROUTE)
            connection.putheader("Authorization", f"Bearer {client.key}")
            connection.putheader("Content-Type", media_type)
            connection.putheader("Content-Length", given)
            connection.putheader("X-Upload-Id", upload_id)
            connection.putheader("X-Upload-Offset", str(offset))
            connection.putheader("X-Upload-Partial-Sha256", partial)
            if total is not None:
                connection.putheader("X-Upload-Total", total)
            connection.endheaders()
            async for chunk in request.stream():
                if not chunk:
                    continue
                await anyio.to_thread.run_sync(part.write, chunk)
                await anyio.to_thread.run_sync(connection.send, chunk)
            status, landed = await anyio.to_thread.run_sync(_answer, connection)
        except OSError as error:
            part.close()
            staged = Part.staged(home, upload_id) or {}
            raise HTTPException(
                http.client.BAD_GATEWAY,
                detail={"code": "hub_unreachable", "message": str(error), **staged},
            ) from None
        finally:
            connection.close()
        if status == http.client.OK:
            kept = await anyio.to_thread.run_sync(
                lambda: part.keep(landed, name=name, media_type=media_type)
            )
            return JSONResponse({**landed, "staging_kept": kept})
        part.close()
        if status == http.client.ACCEPTED:
            return JSONResponse(landed, status_code=http.client.ACCEPTED)
        raise HTTPException(status, detail=landed)

    @router.get(UPLOAD_ROUTE + "/{upload_id}")
    def staged(upload_id: str) -> Mapping[str, Any]:
        try:
            found = Part.staged(home, upload_id)
        except LibraryRefused as refused:
            raise HTTPException(http.client.BAD_REQUEST, detail={"code": refused.code}) from None
        if found is None:
            raise HTTPException(http.client.NOT_FOUND, detail={"code": "not_found"})
        return found

    @router.delete(UPLOAD_ROUTE + "/{upload_id}")
    def discard(upload_id: str) -> Mapping[str, Any]:
        if UPLOAD_ID.fullmatch(upload_id) is None:
            raise HTTPException(http.client.BAD_REQUEST, detail={"code": "invalid_upload"})
        folder = home / STAGING
        for path in (folder / f"{upload_id}.part", folder / f"{upload_id}.json"):
            path.unlink(missing_ok=True)
        return {"discarded": upload_id}

    _ = (upload, staged, discard)
    return router


class BearerGate:
    """Protect mounted MCP, OpenAPI and REST with the same local token."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            authorization = dict(scope["headers"]).get(b"authorization", b"").decode("latin-1")
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() != "bearer" or not secrets.compare_digest(token, self.token):
                response = JSONResponse(
                    {
                        "error": {
                            "code": "unauthorized",
                            "message": "A local bearer token is required.",
                        }
                    },
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_mcp(service: ControlService) -> FastMCP:
    """In-process and stdio callers are trusted; HTTP is protected by BearerGate."""
    mcp = FastMCP("qmx-control")
    for row in control_rows():
        asks = row.approval in ("manage", "propose_money")
        mcp.tool(
            name=row.name,
            description=row.description or None,
            annotations={"readOnlyHint": row.approval == "read", "destructiveHint": asks},
            meta={"interrupt_on": asks},
        )(_mcp_method(getattr(service, row.target)))
    return mcp


def _mcp_method(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def call(*args: Any, **kwargs: Any) -> Any:
        try:
            return method(*args, **kwargs)
        except (ControlError, AppError, RemoteError) as error:
            raise ToolError(json.dumps(error.document())) from error

    return call


def create_app(
    service: ControlService,
    token: str | None = None,
    ui_origin: str = "http://127.0.0.1:5173",
    *,
    extra_routers: Sequence[APIRouter] = (),
) -> FastAPI:
    token = token or local_token()
    service.app_runtime().road.signing_key(token)
    mcp_app = create_mcp(service).http_app(path="/")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        try:
            async with mcp_app.lifespan(app):
                yield
        finally:
            service.close()

    app = FastAPI(title="QMX control", version="0.1.0", lifespan=lifespan)
    bearer = HTTPBearer()

    def authenticate(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]) -> None:
        if not secrets.compare_digest(credentials.credentials, token):
            raise HTTPException(status_code=401, detail="Invalid bearer token")

    @app.post("/api/apps/{app_id}/sign", dependencies=[Depends(authenticate)])
    def sign(
        app_id: str,
        definition_hash: str,
        expected_active: str | None = None,
        rollback: bool = False,
    ) -> dict[str, str]:
        """Operator-only door: never exported as an agent MCP tool."""
        return {
            "signature": service.app_runtime().road.sign(
                app_id, definition_hash, expected_active, rollback=rollback
            )
        }

    @app.exception_handler(ControlError)
    @app.exception_handler(AppError)
    @app.exception_handler(RemoteError)
    async def control_error(
        request: Request, error: ControlError | AppError | RemoteError
    ) -> JSONResponse:
        return JSONResponse(error.document(), status_code=error.status)

    for row, rest in rest_routes(control_rows()):
        app.add_api_route(
            rest.path,
            getattr(service, row.target),
            methods=[rest.verb],
            operation_id=row.name,
            dependencies=[Depends(authenticate)],
        )

    @app.get(
        "/api/events/{topic}",
        response_class=EventSourceResponse,
        dependencies=[Depends(authenticate)],
    )
    async def stream_events(
        topic: EventTopic,
        last_event_id: Annotated[int, Header(ge=0)] = 0,
        after: Annotated[int, Query(ge=0)] = 0,
        subject: str = "",
        max_events: Annotated[int, Query(ge=0, le=1000)] = 0,
    ) -> AsyncIterator[ServerSentEvent]:
        async for event in service.stream(topic, max(after, last_event_id), subject, max_events):
            yield ServerSentEvent(data=event["data"], event=topic, id=str(event["id"]))

    @app.get("/api/health", dependencies=[Depends(authenticate)])
    def health() -> dict[str, str | int]:
        return {"status": "ok", "pid": os.getpid()}

    for extra in extra_routers:
        app.include_router(extra, dependencies=[Depends(authenticate)])

    app.include_router(upload_router(service.home), dependencies=[Depends(authenticate)])

    # Keep decorated callables visible to strict type checking.
    _ = control_error, stream_events, health, sign

    app.mount("/mcp", mcp_app)
    app.add_middleware(BearerGate, token=token)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ui_origin],
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Last-Event-ID",
            "Mcp-Session-Id",
            "Mcp-Protocol-Version",
        ],
        expose_headers=["Mcp-Session-Id"],
    )
    return app


def default_home() -> Path:
    return Path.home() / ".qmx"
