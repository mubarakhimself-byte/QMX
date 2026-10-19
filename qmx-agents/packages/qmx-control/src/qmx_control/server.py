"""Transport adapters over the same bound service methods."""

import asyncio
import json
import os
import secrets
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager, suppress
from functools import wraps
from pathlib import Path
from typing import Annotated, Any

import keyring
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from qmx_apps.errors import AppError
from qmx_remote.models import RemoteError
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_control.catalog import control_rows, rest_routes
from qmx_control.service import ControlError, ControlService, EventTopic


def local_token() -> str:
    """Keep the laptop token in the OS vault, never in the home directory."""
    token = keyring.get_password("qmx/control-token", "control-token")
    if token is None:
        token = secrets.token_urlsafe(32)
        keyring.set_password("qmx/control-token", "control-token", token)
    return token


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
        async def maintain() -> None:
            while True:
                try:
                    await asyncio.to_thread(service.runs_list)
                    if service.settings_get("backup").get("repository"):
                        await asyncio.to_thread(service.backup_weekly)
                except ControlError as error:
                    await asyncio.to_thread(
                        service.record_work,
                        "jobs",
                        "maintenance",
                        {"status": "failed", "error": error.document()},
                    )
                await asyncio.sleep(60)

        maintenance = asyncio.create_task(maintain())
        try:
            async with mcp_app.lifespan(app):
                yield
        finally:
            maintenance.cancel()
            with suppress(asyncio.CancelledError):
                await maintenance
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
