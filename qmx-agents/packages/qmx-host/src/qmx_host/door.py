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

The observer (AD-69, HARNESS-REQUESTS H61). A token the operator minted in Settings is not the
local bearer, and this door is the outermost middleware, so it recognizes the token before
`BearerGate` sees it. An observer call that is allowed is restamped with the local bearer and with
the observer's id, so the rows behind it answer, and any other path is refused here with a typed
403. The allowed set is derived from the catalog and never kept by hand: every REST row of an `ops`
toolset, plus the doctor. A `broker_read` row and a Library content row are refused because no
toolset names them, not because someone remembered to leave them out. The principal stays
`agent:observer:<id>`, never `user`, so the acts only the operator may take stay refused.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final
from urllib.parse import urlencode

from qmx_control.catalog import OBSERVER_PATHS, OBSERVER_TOOLSETS, rest_routes, rows
from qmx_control.service import Observer, observers
from qmx_engine.control_door import PRINCIPAL
from qmx_engine.service.context import Caller
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Receive, Scope, Send

USER: Final = Caller("user")
MCP_CLIENT: Final = Caller("agent", "mcp")
MCP: Final = "/mcp"
SECRET_INTAKE: Final = "/v1/secret"  # noqa: S105  a route path, not a credential
"""Where a home receives a secret once, for itself: an OAuth code exchanged on its own machine, or
a static key whose connection lives here. `user` only, and the route table never names an agent
for it."""
OBSERVER_PARAM: Final = "observer"
"""The query parameter the door appends, naming the observer it vouched for. The note row reads
it; every other row ignores it."""
_PARAM: Final = re.compile(r"\{[^/}]+\}")
"""One route path parameter, such as `{run_id}`: it matches one segment and never a slash."""


def _pattern(path: str) -> re.Pattern[str]:
    """A catalog route path as a matcher: a parameter matches one segment, the rest is literal."""
    parts = [("[^/]+" if _PARAM.fullmatch(part) else re.escape(part)) for part in path.split("/")]
    return re.compile("^" + "/".join(parts) + "$")


def observer_routes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Every REST route an observer may reach, with its verb: the `ops` toolset, the doctor."""
    found = [
        (rest.verb, _pattern(rest.path))
        for row, rest in rest_routes(rows())
        if row.toolset in OBSERVER_TOOLSETS
    ]
    return (*found, *(("GET", _pattern(path)) for path in OBSERVER_PATHS))


OBSERVER_ROUTES: Final = observer_routes()
"""The observer's allow-list, read from the catalog once at import (AD-69, H61)."""


def observer_allows(scope: Scope) -> bool:
    """Whether an observer may reach this request's route: an `ops` row or the doctor."""
    method = str(scope["method"]).upper()
    path = str(scope["path"])
    return any(verb == method and pattern.fullmatch(path) for verb, pattern in OBSERVER_ROUTES)


def _presented(scope: Scope) -> str:
    authorization = dict(scope["headers"]).get(b"authorization", b"").decode("latin-1")
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" else ""


def presented_observer(scope: Scope) -> Observer | None:
    """The observer a request's bearer names, or None for the local bearer or no observer store."""
    store = observers()
    if store is None:
        return None
    token = _presented(scope)
    return None if not token else store.verify(token)


def _restamped(scope: Scope, observer: Observer, bearer: str) -> Scope:
    """The same request as the local user's: the local bearer, and the observer's id appended.

    Any `authorization` or `x-qmx-observer` a client sent is dropped first, so an observer's call
    cannot name another observer and a local-token call cannot claim one.
    """
    headers = [
        (name, value)
        for name, value in scope["headers"]
        if name.lower() not in (b"authorization", b"x-qmx-observer")
    ]
    headers.append((b"authorization", f"Bearer {bearer}".encode("latin-1")))
    query = scope.get("query_string", b"")
    extra = urlencode({OBSERVER_PARAM: observer.id}).encode("latin-1")
    rewritten = extra if not query else query + b"&" + extra
    return {**scope, "headers": headers, "query_string": rewritten}


def _local_bearer() -> str:
    from qmx_control.server import local_token  # noqa: PLC0415 - the host's own gate token

    return local_token()


async def _refused(scope: Scope, receive: Receive, send: Send) -> None:
    path = str(scope["path"])
    response = JSONResponse(
        {
            "error": {
                "code": "observer_refused",
                "message": (
                    "an observer token lists the ops rows and the doctor; "
                    f"{path} is not one of them"
                ),
            }
        },
        status_code=403,
    )
    await response(scope, receive, send)


def principal_of(
    scope: Scope, chat_routes: Sequence[BaseRoute], observer: Observer | None = None
) -> Caller:
    if observer is not None:
        return Caller("agent", f"observer:{observer.id}")
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

    def __init__(
        self, app: ASGIApp, *, chat_routes: Sequence[BaseRoute], bearer: str | None = None
    ) -> None:
        self.app = app
        self.chat_routes = chat_routes
        self.bearer = bearer
        """The local bearer an observer's call is restamped with. None reads the host's own token
        from the OS vault on the first observer call, which is what a host in production uses."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        observer = presented_observer(scope)
        if observer is not None:
            if not observer_allows(scope):
                await _refused(scope, receive, send)
                return
            scope = _restamped(scope, observer, self.bearer or _local_bearer())
        token = PRINCIPAL.set(principal_of(scope, self.chat_routes, observer))
        try:
            await self.app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)
