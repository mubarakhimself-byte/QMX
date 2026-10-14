"""HTTP doors for the console now and the UI later. Thin: parse, call, return.

Mounted on the qmx-control app behind its `BearerGate`. None of these routes join
`qmx_control.server.OPERATIONS`, so none is exported over `/mcp`, and no agent can start turns
through MCP. Every handler is `async def`, so it runs on the harness's event loop; blocking
work goes to a thread.

Routes:
    POST /api/chats                     NewChat  -> {session_id}
    POST /api/sessions/{sid}/turns      {text}   -> 202, always `OperatorText`
    POST /api/sessions/{sid}/interrupt           -> 202
    GET  /api/sessions/{sid}/live                SSE of deltas, never stored
    GET  /api/doctor                             DoctorLine list
    GET  /api/claude-settings                    settings.toml [claude]
    PUT  /api/claude-settings                    `home.parse_claude_settings`, then
                                                 `ControlService.settings_put`
Durable blocks keep using `GET /api/events/sessions?subject=<sid>`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

import uvicorn
from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from qmx_control.models import ControlError, Document
from qmx_control.server import create_app, local_token
from qmx_control.service import ControlService

from qma.boot import KeepListRefused, parse_keep_names
from qma.harness.chat import OperatorText
from qma.harness.harness import Harness, NewChat, UnknownChat
from qma.harness.home import QmxHome, SessionId, claude_section, doctor, session_id
from qma.harness.launch import LAUNCHER, Effort, LaunchRefused, PermissionMode
from qma.harness.project import InChild


def parse_claude_document(values: Document, current: Document) -> Document:
    try:
        return cast("Document", claude_section(values, current))
    except LaunchRefused as error:
        raise ControlError("invalid_settings", str(error)) from error


def parse_environment_document(values: Document, _current: Document) -> Document:
    keep = values.get("keep", [])
    if set(values) - {"keep"} or not isinstance(keep, list):
        raise ControlError("invalid_settings", "[environment] holds only a keep list of names.")
    if not all(isinstance(name, str) for name in keep):
        raise ControlError("invalid_settings", "[environment] keep holds names only.")
    try:
        names = parse_keep_names(cast("list[str]", keep))
    except KeepListRefused as error:
        raise ControlError("invalid_settings", f"[environment] keep: {error}") from error
    return {"keep": list[JsonValue](sorted(names))}


def control_service(home: QmxHome) -> ControlService:
    return ControlService(
        home.root,
        settings_parsers={
            "claude": parse_claude_document,
            "environment": parse_environment_document,
        },
    )


class NewChatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    model: str = "opus"
    effort: Effort | None = None
    mode: PermissionMode = "default"
    workspace: str | None = None


class TurnIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)


def chat_id(text: str) -> SessionId:
    try:
        return session_id(text)
    except ValueError as error:
        raise UnknownChat(text) from error


def chat_router(harness: Harness) -> APIRouter:
    api = APIRouter()

    @api.post("/api/chats")
    async def new_chat(body: NewChatIn) -> dict[str, str]:
        spec = NewChat(
            title=body.title,
            model=body.model,
            effort=body.effort,
            mode=body.mode,
            workspace=Path(body.workspace) if body.workspace else None,
        )
        try:
            chat = await harness.start_chat(spec)
        except LaunchRefused as error:
            raise ControlError("invalid_chat", str(error), 400) from error
        return {"session_id": chat}

    @api.post("/api/sessions/{sid}/turns", status_code=202)
    async def turn(sid: str, body: TurnIn) -> dict[str, str]:
        try:
            await harness.send(chat_id(sid), OperatorText(body.text))
        except LaunchRefused as error:
            raise ControlError("launch_refused", str(error), 409) from error
        return {"status": "sent"}

    @api.post("/api/sessions/{sid}/interrupt", status_code=202)
    async def interrupt(sid: str) -> dict[str, str]:
        await harness.interrupt(chat_id(sid))
        return {"status": "interrupted"}

    @api.get("/api/sessions/{sid}/live", response_class=EventSourceResponse)
    async def live(sid: str) -> AsyncIterator[ServerSentEvent]:
        async for delta in harness.live(chat_id(sid)):
            child = delta.target.tool_use_id if isinstance(delta.target, InChild) else None
            data = {"kind": delta.kind, "text": delta.text, "tool_use_id": child}
            yield ServerSentEvent(data=data, event="delta")

    _ = new_chat, turn, interrupt, live
    return api


def router(
    home: QmxHome,
    control: ControlService,
    *,
    scrubbed: Sequence[str],
    keep: Sequence[str],
) -> APIRouter:
    api = APIRouter()

    @api.get("/api/doctor")
    async def read_doctor() -> dict[str, list[dict[str, object]]]:
        lines = await asyncio.to_thread(
            doctor, home, control, scrubbed=scrubbed, keep=keep, launcher=LAUNCHER
        )
        return {"lines": [asdict(line) for line in lines]}

    @api.get("/api/claude-settings")
    async def read_claude_settings() -> Document:
        return await asyncio.to_thread(control.settings_get, "claude")

    @api.put("/api/claude-settings")
    async def write_claude_settings(values: Document) -> Document:
        return await asyncio.to_thread(control.settings_put, "claude", values)

    _ = read_doctor, read_claude_settings, write_claude_settings
    return api


def serve(
    *,
    root: Path,
    port: int,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
) -> None:
    """Called by `qma.serve` after the boot scrub. The harness and the server
    share one event loop, so a route resolves the harness's futures on their own loop."""
    asyncio.run(_serve(root=root, port=port, ui_origin=ui_origin, scrubbed=scrubbed, keep=keep))


async def _serve(
    *,
    root: Path,
    port: int,
    ui_origin: str,
    scrubbed: Sequence[str],
    keep: Sequence[str],
) -> None:
    home = QmxHome(root)
    control = control_service(home)
    harness = await Harness.open(home, control=control)
    extra = router(home, control, scrubbed=scrubbed, keep=keep)
    app = create_app(control, local_token(), ui_origin, extra_routers=[extra, chat_router(harness)])
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port))
    try:
        await server.serve()
    finally:
        await harness.close()
