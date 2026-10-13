"""Additions to qmx_control/server.py (sketch, signatures only).

1. OPERATIONS rows gain a `who` column. One list still drives every door, and the
   column decides which doors a row gets, so "operator-only" is declared, not implied
   by leaving a route out of the list (today's /sign precedent):

       who=ANY       REST (operator or client principal), MCP export, agent link (qmx tools)
       who=OPERATOR  REST with the operator principal only; never MCP; never the link

   create_mcp() and AgentOps.catalog() both derive from rows where who is ANY, so no
   second list exists to drift.

2. Three principals, resolved per request:
       operator  console cookie from one-time pairing (qma2.operator)
       client    the existing bearer control token (mini apps, scripts, MCP over HTTP)
       agent     never over HTTP: engine hosts reach control only through their stdio link

3. Async rows: `_mcp_method` gains an async variant (HOW Gotcha 11).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from enum import StrEnum
from typing import Any, NamedTuple

from fastapi import FastAPI, Request
from fastapi.sse import ServerSentEvent

from qma2 import Harness
from qma2.model import OperatorProof


class Who(StrEnum):
    ANY = "any"
    OPERATOR = "operator"


class Op(NamedTuple):
    name: str
    method: str
    path: str
    destructive: bool
    who: Who = Who.ANY


# Existing 52 rows convert mechanically to Op(...) with who=ANY. The harness rows live in
# agent_ops.HARNESS_OPERATIONS and are concatenated here:
#   OPERATIONS: tuple[Op, ...] = (*CONTROL_OPERATIONS, *HARNESS_OPERATIONS)


class Principal(StrEnum):
    OPERATOR = "operator"
    CLIENT = "client"


async def resolve_principal(request: Request) -> tuple[Principal, OperatorProof | None]:
    """Cookie `qmx_operator` -> qma2.operator.verify -> OPERATOR + proof.
    Bearer token (compare_digest) -> CLIENT. Neither -> 401 (BearerGate keeps its role
    for MCP and the rest; the console's same-origin calls carry the cookie instead)."""
    raise NotImplementedError


def require(who: Who) -> Callable[..., Any]:
    """FastAPI dependency per row: OPERATOR rows return 403 to CLIENT, and inject the
    OperatorProof into methods that declare a `proof: OperatorProof` parameter."""
    raise NotImplementedError


def create_mcp(service: object, agent_ops: object) -> object:
    """Exports only rows with who=ANY; wraps async methods with an async wrapper."""
    raise NotImplementedError


def create_app(service: object, harness: Harness, token: str | None = None, ui_origin: str = "http://127.0.0.1:5173") -> FastAPI:
    """As today, plus:
    - lifespan opens `Harness.open(HarnessOptions(...))` and closes it;
    - binds HARNESS_OPERATIONS to an AgentOpsRoutes(harness) instance;
    - routes outside OPERATIONS (transport, not operations):
        GET  /console                          static temporary console (one HTML file)
        POST /api/operator/pair                {code} -> Set-Cookie qmx_operator (HttpOnly, SameSite=Strict)
        GET  /api/threads/{thread_id}/live     SSE over harness.live(); snapshot first; keepalive 10 s
        GET  /api/accounts/chatgpt/callback    OAuth redirect -> harness.accounts.chatgpt_complete
    - the existing /api/apps/{id}/sign becomes an OPERATOR row instead of a hidden route.
    """
    raise NotImplementedError


async def live_events(harness: Harness, thread_id: str) -> AsyncIterator[ServerSentEvent]:
    raise NotImplementedError
