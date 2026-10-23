"""The one door (AD-52, H24): which principal each call to the host acts as.

The door names the principal from the route a request reaches; `BearerGate` behind it checks the
bearer. A REST call with the UI bearer is `user`. A call to a chat's own route, such as sending a
turn, is `agent:<session_id>`: the chat that request starts inherits it, so every `qmx` tool call
that chat makes in-process acts as that agent and never as the operator who typed the turn. A
client of `/mcp` over HTTP is an agent too. Work a workflow run starts is `workflow:<run_id>`,
which the engine sets on the run's own task (`qmx_engine.control_door.as_run`).

The one exception is `SECRET_INTAKE`, the route that receives a secret once for this home (AD-28,
N5): it is named `user` before any chat route is matched, so no chat's route pattern can shadow it
into `agent:<session_id>` and a key is never entered on a machine as an agent. A handler mounted
there must still refuse a caller that is not `user`; the door's part is that no other principal can
be named for that path.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from qmx_engine.control_door import PRINCIPAL
from qmx_engine.service.context import Caller
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Receive, Scope, Send

USER: Final = Caller("user")
MCP_CLIENT: Final = Caller("agent", "mcp")
MCP: Final = "/mcp"
SECRET_INTAKE: Final = "/v1/secret"  # noqa: S105 — a route path, not a credential
"""Where a home receives a secret once, for itself: an OAuth code exchanged on its own machine, or
a static key whose connection lives here. `user` only, and the route table never names an agent
for it."""


def principal_of(scope: Scope, chat_routes: Sequence[BaseRoute]) -> Caller:
    path = str(scope["path"])
    if path == SECRET_INTAKE or path.startswith(f"{SECRET_INTAKE}/"):
        return USER
    if path == MCP or path.startswith(f"{MCP}/"):
        return MCP_CLIENT
    for route in chat_routes:
        match, child = route.matches(scope)
        if match is Match.FULL:
            sid = child.get("path_params", {}).get("sid")
            return USER if sid is None else Caller("agent", str(sid))
    return USER


class PrincipalDoor:
    """ASGI middleware that sets `PRINCIPAL` for the length of each HTTP request."""

    def __init__(self, app: ASGIApp, *, chat_routes: Sequence[BaseRoute]) -> None:
        self.app = app
        self.chat_routes = chat_routes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = PRINCIPAL.set(principal_of(scope, self.chat_routes))
        try:
            await self.app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)
