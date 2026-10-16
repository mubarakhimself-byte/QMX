"""HTTP doors for the console now and the UI later. Thin: parse, call, return.

Mounted on the qmx-control app behind its `BearerGate`. None of these routes join
`qmx_control.server.OPERATIONS`, so none is exported over `/mcp`. Every handler is
`async def`, so it runs on the host's event loop; blocking work goes to a thread.

Routes:
    GET  /api/doctor            DoctorLine list
    GET  /api/claude-settings   settings.toml [claude]
    PUT  /api/claude-settings   `home.parse_claude_settings`, then `ControlService.settings_put`
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

import uvicorn
from fastapi import APIRouter
from pydantic import JsonValue
from qmx_control.models import ControlError, Document
from qmx_control.server import create_app, local_token
from qmx_control.service import ControlService

from qma.boot import KeepListRefused, parse_keep_names
from qma.harness.home import QmxHome, claude_section, doctor, ensure_homes
from qma.harness.launch import LAUNCHER, LaunchRefused


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
    """Called by `qma.serve` after the boot scrub. A refused home does not stop the host, so
    `/api/doctor` can name the reason; every launch re-checks it."""
    home = QmxHome(root)
    try:
        ensure_homes(home)
    except LaunchRefused as error:
        print(f"qma.serve: {error}", file=sys.stderr, flush=True)
    control = control_service(home)
    extra = router(home, control, scrubbed=scrubbed, keep=keep)
    app = create_app(control, local_token(), ui_origin, extra_routers=[extra])
    uvicorn.run(app, host="127.0.0.1", port=port)
