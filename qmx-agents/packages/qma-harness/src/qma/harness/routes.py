"""HTTP doors for the console now and the UI later. Thin: parse, call, return.

Mounted on the qmx-control app behind its `BearerGate`. None of these routes join
`qmx_control.server.OPERATIONS`, so none is exported over `/mcp`, and no agent can start turns
through MCP. Every handler is `async def`, so it runs on the harness's event loop; blocking
work goes to a thread.

Routes:
    POST /api/chats                     NewChat  -> {session_id}
    GET  /api/chats                              the resume list: Interactive chats, newest
                                                 first, with title, config and turn state
    GET  /api/chats/{sid}                        one chat's entry of that list
    POST /api/sessions/{sid}/turns      {text}   -> 202, always `OperatorText`
    POST /api/sessions/{sid}/interrupt           -> 202
    POST /api/sessions/{sid}/quote      ChangeIn -> the quote; 400 for a change the chat
                                                 cannot take
    POST /api/sessions/{sid}/apply      {quote_id} -> the applied quote; 409 when it is
                                                 stale or the launch is refused
    POST /api/sessions/{sid}/export              -> {folder, files}; the redacted bundle
    GET  /api/sessions/{sid}/rewind              -> the prompts with a file checkpoint
    POST /api/sessions/{sid}/rewind     {message_id} -> 202; 409 mid-turn or for a prompt
                                                 with no checkpoint
    GET  /api/sessions/{sid}/live                SSE of deltas, never stored; 404 first for an
                                                 unknown chat
    POST /api/approvals/{ask_id}        AnswerIn -> {status}; ask_id is
                                                 `<sid>.<seq of the permission or question block>`
    GET  /api/usage                              the usage page: plan windows, readings, token
                                                 sums per profile, cap, overage stop, money
                                                 posture and the stored exposure report
    POST /api/usage/meter                        read `/usage` in a plan chat, then the page
    GET  /api/doctor                             DoctorLine list from stored results; never
                                                 runs the exposure probe
    POST /api/doctor/probe                       runs the exposure probe, then the list
    GET  /api/claude-settings                    settings.toml [claude]
    PUT  /api/claude-settings                    `home.parse_claude_settings`, then
                                                 `ControlService.settings_put`
Durable blocks keep using `GET /api/events/sessions?subject=<sid>`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Literal, cast

import uvicorn
from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from qmx_control.models import ControlError, Document
from qmx_control.server import create_app, local_token
from qmx_control.service import ControlService

from qma.boot import KeepListRefused, parse_keep_names
from qma.harness.chat import (
    AllowAlways,
    AllowOnce,
    Answer,
    Answers,
    AskId,
    OperatorText,
    Quote,
    QuoteStale,
    Reject,
    RewindRefused,
    describe,
)
from qma.harness.harness import ChatTableFull, Harness, NewChat, UnknownChat
from qma.harness.home import (
    ChatRecord,
    DoctorLine,
    QmxHome,
    SessionId,
    claude_section,
    doctor,
    list_records,
    read_record,
    record_path,
    session_id,
)
from qma.harness.launch import (
    LAUNCHER,
    ConfigChange,
    Effort,
    Interactive,
    LaunchRefused,
    PermissionMode,
)
from qma.harness.profiles import ProfileName
from qma.harness.project import Delta, InChild
from qma.harness.usage import token_sums


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
    profile: str = "claude"


class TurnIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)


class ChangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: str | None = None
    model: str | None = None
    effort: Effort | None = None
    mode: PermissionMode | None = None


class ApplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote_id: str = Field(min_length=1)


def quote_document(quote: Quote) -> dict[str, Any]:
    return {
        "id": quote.id,
        "warning": quote.warning,
        "steps": [step.value for step in quote.steps],
        "recomputed_tokens": quote.recomputed_tokens,
        "background_tasks": quote.background_tasks,
        "old": describe(quote.old),
        "new": describe(quote.new),
    }


class AllowOnceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["allow_once"]
    edited_input: dict[str, JsonValue] | None = None


class AllowAlwaysIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["allow_always"]


class RejectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["reject"]
    message: str = ""


class AnswersIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["answers"]
    answers: dict[str, str]


type AnswerIn = Annotated[
    AllowOnceIn | AllowAlwaysIn | RejectIn | AnswersIn, Field(discriminator="decision")
]


def to_answer(body: AllowOnceIn | AllowAlwaysIn | RejectIn | AnswersIn) -> Answer:
    match body:
        case AllowOnceIn(edited_input=edited):
            return AllowOnce(None if edited is None else cast("dict[str, Any]", edited))
        case AllowAlwaysIn():
            return AllowAlways()
        case RejectIn(message=message):
            return Reject(message)
        case AnswersIn(answers=answers):
            return Answers(answers)


class RewindIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: str = Field(min_length=1)


def chat_entry(record: ChatRecord, title: str) -> dict[str, Any]:
    return {
        "session_id": record.session_id,
        "title": title,
        "workspace": str(record.config.workspace),
        "started": record.started,
        "turn": record.turn,
        **describe(record.config),
    }


def resume_list(home: QmxHome, control: ControlService) -> list[dict[str, Any]]:
    """Interactive chats, most recently written first. Background, Child and doctor chats are
    not the operator's to resume."""
    titles: dict[str, str] = {}
    offset = 0
    while page := control.sessions_list(offset, 1000):
        titles |= {str(row["id"]): str(row.get("title", "")) for row in page}
        offset += len(page)
    records = [
        record
        for record in list_records(home)
        if isinstance(record.config.kind, Interactive) and record.session_id in titles
    ]
    records.sort(key=lambda record: record_path(home, record.session_id).stat().st_mtime)
    return [chat_entry(record, titles[record.session_id]) for record in reversed(records)]


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
            profile=body.profile,
        )
        try:
            chat = await harness.start_chat(spec)
        except LaunchRefused as error:
            raise ControlError("invalid_chat", str(error), 400) from error
        return {"session_id": chat}

    @api.get("/api/chats")
    async def chats() -> list[dict[str, Any]]:
        return await asyncio.to_thread(resume_list, harness.home, harness.control)

    @api.get("/api/chats/{sid}")
    async def one_chat(sid: str) -> dict[str, Any]:
        chat = chat_id(sid)
        record = await asyncio.to_thread(read_record, harness.home, chat)
        if record is None:
            raise UnknownChat(sid)
        tokens = await asyncio.to_thread(token_sums, harness.home.root / "runs", chat)
        return chat_entry(record, "") | {"tokens": tokens}

    @api.post("/api/sessions/{sid}/turns", status_code=202)
    async def turn(sid: str, body: TurnIn) -> dict[str, str]:
        try:
            await harness.send(chat_id(sid), OperatorText(body.text))
        except LaunchRefused as error:
            raise ControlError("launch_refused", str(error), 409) from error
        except ChatTableFull as error:
            raise ControlError("chat_table_full", str(error), 409) from error
        return {"status": "sent"}

    @api.post("/api/sessions/{sid}/interrupt", status_code=202)
    async def interrupt(sid: str) -> dict[str, str]:
        await harness.interrupt(chat_id(sid))
        return {"status": "interrupted"}

    @api.post("/api/sessions/{sid}/quote")
    async def quote(sid: str, body: ChangeIn) -> dict[str, Any]:
        change = ConfigChange(
            profile=None if body.profile is None else ProfileName(body.profile),
            model=body.model,
            effort=body.effort,
            mode=body.mode,
        )
        try:
            return quote_document(await harness.quote(chat_id(sid), change))
        except LaunchRefused as error:
            raise ControlError("change_refused", str(error), 400) from error

    @api.post("/api/sessions/{sid}/apply")
    async def apply(sid: str, body: ApplyIn) -> dict[str, Any]:
        try:
            return quote_document(await harness.apply(chat_id(sid), body.quote_id))
        except QuoteStale as error:
            raise ControlError("quote_stale", str(error), 409) from error
        except LaunchRefused as error:
            raise ControlError("launch_refused", str(error), 409) from error

    @api.post("/api/sessions/{sid}/export")
    async def export(sid: str) -> dict[str, Any]:
        folder = await harness.export(chat_id(sid))
        files = sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*.*"))
        return {"folder": str(folder), "files": files}

    @api.get("/api/sessions/{sid}/rewind")
    async def rewind_points(sid: str) -> list[dict[str, str]]:
        return [asdict(point) for point in await harness.rewind_points(chat_id(sid))]

    @api.post("/api/sessions/{sid}/rewind", status_code=202)
    async def rewind(sid: str, body: RewindIn) -> dict[str, str]:
        try:
            await harness.rewind(chat_id(sid), body.message_id)
        except (RewindRefused, LaunchRefused) as error:
            raise ControlError("rewind_refused", str(error), 409) from error
        except ChatTableFull as error:
            raise ControlError("chat_table_full", str(error), 409) from error
        return {"status": "rewound"}

    def live_deltas(sid: str) -> AsyncIterator[Delta]:
        return harness.live(chat_id(sid))

    @api.get("/api/sessions/{sid}/live", response_class=EventSourceResponse)
    async def live(
        deltas: AsyncIterator[Delta] = Depends(live_deltas),  # noqa: B008
    ) -> AsyncIterator[ServerSentEvent]:
        async for delta in deltas:
            child = delta.target.tool_use_id if isinstance(delta.target, InChild) else None
            data = {"kind": delta.kind, "text": delta.text, "tool_use_id": child}
            yield ServerSentEvent(data=data, event="delta")

    @api.post("/api/approvals/{ask_id}")
    async def approve(ask_id: str, body: AnswerIn) -> dict[str, str]:
        try:
            ask = AskId.parse(ask_id)
        except ValueError:
            return {"status": "unknown"}
        return {"status": harness.answer(ask, to_answer(body))}

    @api.get("/api/usage")
    async def read_usage() -> dict[str, Any]:
        return (await harness.usage()).document()

    @api.post("/api/usage/meter")
    async def read_meter() -> dict[str, Any]:
        try:
            await harness.meter()
        except LaunchRefused as error:
            raise ControlError("launch_refused", str(error), 409) from error
        except ChatTableFull as error:
            raise ControlError("chat_table_full", str(error), 409) from error
        return (await harness.usage()).document()

    _ = new_chat, chats, one_chat, turn, interrupt, quote, apply, export, rewind_points, rewind
    _ = live, approve, read_usage, read_meter
    return api


def router(
    home: QmxHome,
    control: ControlService,
    *,
    scrubbed: Sequence[str],
    keep: Sequence[str],
    harness_lines: Callable[[bool], Awaitable[list[DoctorLine]]] | None = None,
) -> APIRouter:
    """`harness_lines(probe)` adds `Harness.doctor`'s lines; only the POST probes."""
    api = APIRouter()

    async def lines(*, probe: bool) -> dict[str, list[dict[str, object]]]:
        found = await asyncio.to_thread(
            doctor, home, control, scrubbed=scrubbed, keep=keep, launcher=LAUNCHER
        )
        if harness_lines is not None:
            found += await harness_lines(probe)
        return {"lines": [asdict(line) for line in found]}

    @api.get("/api/doctor")
    async def read_doctor() -> dict[str, list[dict[str, object]]]:
        return await lines(probe=False)

    @api.post("/api/doctor/probe")
    async def run_probe() -> dict[str, list[dict[str, object]]]:
        return await lines(probe=True)

    @api.get("/api/claude-settings")
    async def read_claude_settings() -> Document:
        return await asyncio.to_thread(control.settings_get, "claude")

    @api.put("/api/claude-settings")
    async def write_claude_settings(values: Document) -> Document:
        return await asyncio.to_thread(control.settings_put, "claude", values)

    _ = read_doctor, run_probe, read_claude_settings, write_claude_settings
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
    harness.control_port = port
    extra = router(
        home,
        control,
        scrubbed=scrubbed,
        keep=keep,
        harness_lines=lambda probe: harness.doctor(probe=probe),
    )
    app = create_app(control, local_token(), ui_origin, extra_routers=[extra, chat_router(harness)])
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port))
    try:
        await server.serve()
    finally:
        await harness.close()
