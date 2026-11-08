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
403. The allowed set is derived from the catalog and never kept by hand: every REST read of an
`ops` toolset, plus the doctor and the one diagnosis-note row. A `broker_read` row, a Library
content row and every ops write but the note are refused because the catalog says so, not because
someone remembered to leave them out. The principal stays `agent:observer:<id>`, never `user`, so
the acts only the operator may take stay refused.

A run pass (engine AD-70, Lib AD-28). A remote attempt's bearer is the run pass this host minted
for it. The door admits one only on `POST /api/data/read`, and only when its MAC verifies, it has
not expired and neither it nor its run is revoked. The request is restamped with the local bearer
and the verified pass is left in the request's state under `RUN_PASS`, so the read takes its
`data_scope` from the pass and never from the body. Any other route, and any pass that fails a
check, answers 401 here. The principal is `workflow:<run_id>`.

A host pass (engine AD-65, AD-67, Level 0 AD-46). Another host of this home calls the cTrader
begin and code routes, the engine's two forwarding routes and the host route with a host pass and
no bearer. The door restamps those five routes with the local bearer and nothing else; each route
verifies the pass itself and refuses without one. The door's principal is `user`, as for every
route no chat owns; the host route acts as the principal its pass carries, never as that `user`.

The Library service (Library AD-11, AD-19). On the server the host serves the Hub's routes in
process, and the PC calls them with the pairing key as its bearer. The door restamps a call that
reaches one of those routes with exactly that key to the local bearer, which the in-process Hub is
built to check; the pairing key opens no other route.

The template install door (`templates_router`) lives here too: the host mounts it behind the same
bearer as its other routers, and the engine's CLI posts to it whenever the home has a host.
"""

from __future__ import annotations

import asyncio
import contextvars
import re
import secrets
from collections.abc import Sequence
from typing import Final
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from qmx_control.catalog import (
    OBSERVER_PATHS,
    OBSERVER_TOOLSETS,
    OBSERVER_WRITES,
    rest_routes,
    rows,
)
from qmx_control.service import Observer, observers
from qmx_engine.__main__ import INSTALL_ROUTE
from qmx_engine.control_door import FAILURES, PRINCIPAL, EngineDoor, control_error
from qmx_engine.ledger.redact import redact
from qmx_engine.service.context import OPERATOR, Caller
from qmx_engine.service.forward import PASS_HEADER
from qmx_engine.templates.catalog import CATALOG, Template, find
from qmx_engine.templates.install import Installed, install_one
from qmx_router.passes import PREFIX, Ask, Pass, PassAuthority
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_host.host_route import HOST_ROUTE
from qmx_host.jobs import Job, Jobs, Progress, Stopped
from qmx_host.venue_session import HOST_PASS_ROUTES

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
RUN_PASS: Final = "run_pass"  # noqa: S105 - a request state key, not a credential
"""The request state key the verified run pass rides under to the one route that reads it."""
RUN_PASS_ROUTE: Final = ("POST", "/api/data/read")
"""The only route a run pass reaches."""
_PARAM: Final = re.compile(r"\{[^/}]+\}")
"""One route path parameter, such as `{run_id}`: it matches one segment and never a slash."""


def _pattern(path: str) -> re.Pattern[str]:
    """A catalog route path as a matcher: a parameter matches one segment, the rest is literal."""
    parts = [("[^/]+" if _PARAM.fullmatch(part) else re.escape(part)) for part in path.split("/")]
    return re.compile("^" + "/".join(parts) + "$")


def observer_routes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Every REST route an observer may reach, with its verb: the `ops` reads, the note, the
    doctor."""
    found = [
        (rest.verb, _pattern(rest.path))
        for row, rest in rest_routes(rows())
        if row.toolset in OBSERVER_TOOLSETS
        and (row.approval == "read" or row.name in OBSERVER_WRITES)
    ]
    return (*found, *(("GET", _pattern(path)) for path in OBSERVER_PATHS))


OBSERVER_ROUTES: Final = observer_routes()
"""The observer's allow-list, read from the catalog once at import (AD-69, H61)."""


def observer_allows(scope: Scope) -> bool:
    """Whether an observer may reach this request's route: an ops read, the note or the doctor."""
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
    """The same request as the local user's: the local bearer, and the observer's id appended."""
    headers = [
        (name, value) for name, value in scope["headers"] if name.lower() != b"authorization"
    ]
    headers.append((b"authorization", f"Bearer {bearer}".encode("latin-1")))
    query = scope.get("query_string", b"")
    extra = urlencode({OBSERVER_PARAM: observer.id}).encode("latin-1")
    rewritten = extra if not query else query + b"&" + extra
    return {**scope, "headers": headers, "query_string": rewritten}


def _pass_restamped(scope: Scope, minted: Pass, bearer: str) -> Scope:
    """The same request behind the local bearer, carrying the verified pass in its state."""
    headers = [
        (name, value) for name, value in scope["headers"] if name.lower() != b"authorization"
    ]
    headers.append((b"authorization", f"Bearer {bearer}".encode("latin-1")))
    state = {**scope.get("state", {}), RUN_PASS: minted}
    return {**scope, "headers": headers, "state": state}


FORWARD_ROUTES: Final = frozenset(
    {("POST", "/api/engine/forward"), ("GET", "/api/engine/forward/stream"), HOST_ROUTE}
)
"""The engine's forwarding routes (AD-65) and the host route (AD-46), which another host of this
home calls the same way."""


def host_pass_call(scope: Scope) -> bool:
    """Another host of this home calling a venue, forwarding or host route with a host pass. The
    route verifies the pass itself; the door lets it past the local bearer, which that host does
    not hold."""
    route = (str(scope["method"]).upper(), str(scope["path"]))
    return route in HOST_PASS_ROUTES | FORWARD_ROUTES and PASS_HEADER.lower().encode(
        "latin-1"
    ) in dict(scope["headers"])


def _with_bearer(scope: Scope, bearer: str) -> Scope:
    headers = [
        (name, value) for name, value in scope["headers"] if name.lower() != b"authorization"
    ]
    headers.append((b"authorization", f"Bearer {bearer}".encode("latin-1")))
    return {**scope, "headers": headers}


async def _pass_refused(scope: Scope, receive: Receive, send: Send, reason: str) -> None:
    response = JSONResponse(
        {"error": {"code": "run_pass_refused", "message": reason}},
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )
    await response(scope, receive, send)


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
                    "an observer token lists the ops reads, the doctor and one note; "
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
        self,
        app: ASGIApp,
        *,
        chat_routes: Sequence[BaseRoute],
        bearer: str | None = None,
        passes: PassAuthority | None = None,
        library_key: str = "",
        library_routes: Sequence[BaseRoute] = (),
    ) -> None:
        self.app = app
        self.chat_routes = chat_routes
        self.library_key = library_key
        """The pairing key the Library routes admit; empty mounts none."""
        self.library_routes = library_routes
        self.passes = passes
        """The authority that minted this host's run passes; None admits no run pass."""
        self.bearer = bearer
        """The local bearer an observer's call is restamped with. None reads the host's own token
        from the OS vault on the first observer call, which is what a host in production uses."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = _presented(scope)
        if self.passes is not None and token.startswith(f"{PREFIX}."):
            minted, refused = self.passes.check(token, Ask())
            route = (str(scope["method"]).upper(), str(scope["path"]))
            if refused is not None:
                await _pass_refused(scope, receive, send, str(refused))
                return
            if route != RUN_PASS_ROUTE:
                await _pass_refused(scope, receive, send, "a run pass reaches only the data read")
                return
            scope = _pass_restamped(scope, minted, self.bearer or _local_bearer())
            token_set = PRINCIPAL.set(Caller("workflow", minted.run))
            try:
                await self.app(scope, receive, send)
            finally:
                PRINCIPAL.reset(token_set)
            return
        if host_pass_call(scope) or self._library_call(scope, token):
            scope = _with_bearer(scope, self.bearer or _local_bearer())
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

    def _library_call(self, scope: Scope, token: str) -> bool:
        if not self.library_key or not token:
            return False
        if not secrets.compare_digest(token, self.library_key):
            return False
        return any(route.matches(scope)[0] is Match.FULL for route in self.library_routes)


class InstallIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    templates: list[str] | None = None
    """Template ids, or any id one had before; None installs the whole catalogue."""


INSTALL: Final = "templates-install"
"""The kind of the install's job."""


def _row(found: Installed) -> dict[str, str]:
    template = found.template
    return {
        "id": template.id,
        "folder": template.folder,
        "action": found.action,
        "detail": found.detail,
    }


def templates_router(engine: EngineDoor) -> APIRouter:
    """`POST /api/templates/install`: install templates disabled through this host's engine, so
    `python -m qmx_engine templates install` on a home with a running host lands in the Library
    store this host serves, and never opens a second writer beside it.

    The install is a job (loose strings P5): the POST answers 202 with its view at once, and
    `GET /api/templates/install/{job_id}` reads which template it is on, how many are done and
    each finished row, under `result.rows`. Each template is one `install_one` hop on the
    engine's loop in an empty context, as `EngineDoor` runs its doors, so its test runs inherit no
    request principal. An unknown id refuses 404 by name before any job starts; a second install
    while one runs answers 409, because both would write the same drafts. A hop that raises ends
    the job `stopped` with its code and the rows finished before it."""
    router = APIRouter()
    jobs = Jobs()
    rows_by_job: dict[str, list[dict[str, str]]] = {}
    """Each job's rows, appended by its own thread only."""

    def view(job: Job) -> dict[str, object]:
        shown = job.document()
        if job.state == "running":
            shown["result"] = {"rows": rows_by_job.get(job.id, [])[: job.done]}
        return shown

    def hop(template: Template) -> Installed:
        future = contextvars.Context().run(
            asyncio.run_coroutine_threadsafe,
            install_one(engine.svc, template, OPERATOR),
            engine.loop,
        )
        return future.result()

    @router.post(INSTALL_ROUTE, status_code=202)
    def install_templates(body: InstallIn) -> dict[str, object]:
        try:
            picked = list(CATALOG) if body.templates is None else [find(t) for t in body.templates]
        except KeyError as unknown:
            raise HTTPException(404, f"no template {unknown.args[0]!r} in the catalogue") from None
        rows: list[dict[str, str]] = []

        def work(progress: Progress) -> dict[str, object]:
            for done, template in enumerate(picked):
                progress(f"installing {template.id}", done=done, total=len(picked))
                try:
                    rows.append(_row(hop(template)))
                except FAILURES as error:
                    refused = control_error(error)
                    why = str(refused).removeprefix(f"{refused.code}: ")
                    raise Stopped(
                        f"the install stopped at {template.id}: {why}; the templates before it "
                        "are installed, so fix that and run the install again",
                        {"code": refused.code, "rows": list(rows)},
                    ) from None
                except Exception as error:  # a disk, database or loop error ends with its line
                    why = redact(str(error)) or "no message"
                    raise Stopped(
                        f"the install stopped at {template.id} with an unexpected "
                        f"{type(error).__name__}: {why}; the templates before it are installed, "
                        "so run the install again",
                        {"rows": list(rows)},
                    ) from None
            progress("all templates done", done=len(picked), total=len(picked))
            return {"rows": list(rows)}

        started = jobs.start(INSTALL, work)
        if not started.new:
            raise HTTPException(
                409,
                f"a template install is already running (job {started.job.id}); "
                "wait for it to end, then run the install again",
            )
        rows_by_job[started.job.id] = rows
        return view(started.job)

    @router.get(f"{INSTALL_ROUTE}/{{job_id}}")
    def read_install(job_id: str) -> dict[str, object]:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(
                404,
                f"no template install job {job_id} on this host; the host started again since it "
                "began, so run the install again",
            )
        return view(job)

    _ = install_templates, read_install
    return router
