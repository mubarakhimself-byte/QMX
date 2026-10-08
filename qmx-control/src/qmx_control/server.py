"""Transport adapters over the same bound service methods."""

import asyncio
import json
import os
import secrets
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from functools import wraps
from pathlib import Path
from typing import Annotated, Any

import keyring
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from qmx_apps.errors import AppError
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_control.service import ControlError, ControlService, EventTopic

# These descriptors wire both doors; there is no second implementation to drift.
OPERATIONS = (
    ("apps_list", "GET", "/api/apps", False),
    ("apps_registry", "GET", "/api/apps/registry", False),
    ("apps_get", "GET", "/api/apps/{app_id}", False),
    ("apps_create", "POST", "/api/apps", True),
    ("apps_update", "PUT", "/api/apps/{app_id}", True),
    ("apps_versions", "GET", "/api/apps/{app_id}/versions", False),
    ("apps_test", "POST", "/api/apps/{app_id}/test", False),
    ("apps_publish", "POST", "/api/apps/{app_id}/publish", True),
    ("apps_start", "POST", "/api/apps/{app_id}/start", True),
    ("apps_stop", "POST", "/api/apps/{app_id}/stop", True),
    ("apps_restart", "POST", "/api/apps/{app_id}/restart", True),
    ("apps_call", "POST", "/api/apps/{app_id}/tools/{tool}", True),
    ("apps_resource", "GET", "/api/apps/{app_id}/resources", False),
    ("apps_logs", "GET", "/api/apps/{app_id}/logs", False),
    ("apps_evidence", "GET", "/api/apps/{app_id}/evidence", False),
    ("apps_backup", "POST", "/api/apps/{app_id}/backup", False),
    ("apps_restore", "POST", "/api/apps/{app_id}/restore", True),
    ("workflows_get", "GET", "/api/workflows/{workflow_id}", False),
    ("workflows_put", "PUT", "/api/workflows/{workflow_id}", True),
    ("workflows_validate", "POST", "/api/workflows/validate", False),
    ("workflows_run", "POST", "/api/workflows/{workflow_id}/run", True),
    ("runs_list", "GET", "/api/runs", False),
    ("runs_get", "GET", "/api/runs/{run_id}", False),
    ("runs_cancel", "POST", "/api/runs/{run_id}/cancel", True),
    ("jobs_list", "GET", "/api/jobs", False),
    ("jobs_cancel", "POST", "/api/jobs/{job_id}/cancel", True),
    ("library_search", "GET", "/api/library", False),
    ("library_save", "POST", "/api/library", False),
    ("library_get", "GET", "/api/library/{artifact_id}", False),
    ("library_versions", "GET", "/api/library/{artifact_id}/versions", False),
    ("library_links", "GET", "/api/library/{artifact_id}/links", False),
    ("library_link", "POST", "/api/library/links", False),
    ("aggregates_get", "GET", "/api/aggregates", False),
    ("backup_weekly", "POST", "/api/backup/weekly", True),
    ("settings_get", "GET", "/api/settings/{section}", False),
    ("settings_put", "PUT", "/api/settings/{section}", True),
    ("portfolio_proposals", "GET", "/api/portfolio/proposals", False),
    ("sessions_create", "POST", "/api/sessions", False),
    ("sessions_list", "GET", "/api/sessions", False),
    ("sessions_append", "POST", "/api/sessions/{session_id}/blocks", False),
    ("sessions_stream", "GET", "/api/sessions/{session_id}/events", False),
)


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
    for name, method, _, destructive in OPERATIONS:
        mcp.tool(
            name=name,
            annotations={"readOnlyHint": method == "GET", "destructiveHint": destructive},
            meta={"interrupt_on": destructive},
        )(_mcp_method(getattr(service, name)))
    return mcp


def _mcp_method(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def call(*args: Any, **kwargs: Any) -> Any:
        try:
            return method(*args, **kwargs)
        except (ControlError, AppError) as error:
            raise ToolError(json.dumps(error.document())) from error

    return call


def create_app(
    service: ControlService, token: str | None = None, ui_origin: str = "http://127.0.0.1:5173"
) -> FastAPI:
    token = token or local_token()
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

    @app.exception_handler(ControlError)
    @app.exception_handler(AppError)
    async def control_error(request: Request, error: ControlError | AppError) -> JSONResponse:
        return JSONResponse(error.document(), status_code=error.status)

    for name, method, path, _ in OPERATIONS:
        app.add_api_route(
            path,
            getattr(service, name),
            methods=[method],
            operation_id=name,
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

    # Keep decorated callables visible to strict type checking.
    _ = control_error, stream_events, health

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
