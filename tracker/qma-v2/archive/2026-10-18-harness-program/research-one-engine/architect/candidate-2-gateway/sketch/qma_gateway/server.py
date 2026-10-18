"""The gateway process: one loopback HTTP endpoint that speaks Anthropic Messages.

Run as `python -m qma_gateway`, spawned and supervised by qmx-control
(`qmx_harness.gateway_link`). It binds 127.0.0.1 on a fixed, UI-editable port
(default 8767) so a restart comes back on the URL every live CLI already has.

Private channel to qmx-control: the process's own stdin and stdout.
- stdin carries `GatewayDesired` documents (JSON lines). Each one replaces the
  whole in-memory copy. There is no incremental command, so nothing can drift.
- stdout carries `GatewayEvent`s (JSON lines). The gateway writes no database.
No admin port, no admin secret, nothing an agent's Bash can reach.

Paths served:
- POST /v1/messages              the request pipeline below
- POST /v1/messages/count_tokens  same pipeline, non-streaming; 404 for routes without it
- GET  /v1/models                synthesized from the RouteTable, filtered by lease
- GET  /auth/chatgpt/callback    Sign in with ChatGPT loopback callback (translator.py)
Anything else: 404 and an `UnexpectedPath` event carrying only the path.

Request pipeline (one request, three files deep at most: server -> lanes -> translator):

    raw HTTP
      -> split_headers()            credential sealed here, lease and hints parsed
      -> leases.authenticate()      401 without a live lease
      -> peek_route_fields()        reads only `model` and `stream` from a copy
      -> table.resolve() + allowed  400 if the model is not in this lease
      -> cap_gate()                 403 if background and plan window >= cap
      -> lanes.dispatch()           plan relay | key call | gpt translate
      -> response tee               meter (usage, window) + wire gate (money)
      -> CLI
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal

from qma_gateway.contract import (
    AgentHints,
    GatewayDesired,
    GatewayEvent,
    LeaseGrant,
    ModelId,
    Percent,
    Route,
    RouteTable,
)
from qma_gateway.sealed import Sealed

# ------------------------------------------------------------ inbound parsing


@dataclass(frozen=True, slots=True)
class InboundRequest:
    """A request after header splitting. `forward` never contains a credential."""

    path: str
    lease_secret: bytes | None  # x-qmx-lease (set through ANTHROPIC_CUSTOM_HEADERS)
    credential: Sealed | None  # authorization / x-api-key, sealed; None when absent
    hints: AgentHints
    forward: tuple[tuple[bytes, bytes], ...]  # anthropic-version, anthropic-beta, content-type, ...
    body: bytes  # raw; the plan lane forwards these exact bytes


def split_headers(path: str, raw: Sequence[tuple[bytes, bytes]], body: bytes) -> InboundRequest:
    """Pure. The one place request headers are sorted.

    # TODO pseudocode
    # for name, value in raw:
    #     name = name.lower()
    #     if name == b"x-qmx-lease":                 lease_secret = value
    #     elif name in CREDENTIAL_HEADERS:           credential = Sealed(value)
    #         (never inspected, in either lease mode. A key-only CLI sends the
    #          non-secret marker "qmx-key-only" here, a plan-carrying CLI sends its
    #          own login. The gateway treats both the same way: seal, then forward
    #          on the plan lane or discard on every other lane.)
    #     elif name.startswith(b"x-claude-code-"):   hints
    #     elif name in HOP_BY_HOP:                   drop
    #     elif name == b"accept-encoding":           drop (gateway asks upstream for identity,
    #                                                 so the meter can read SSE)
    #     else:                                      forward
    """
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class RouteFields:
    model: ModelId
    stream: bool


def peek_route_fields(body: bytes) -> RouteFields:
    """Parse a copy of the JSON body for `model` and `stream` only. 400 on bad JSON."""
    raise NotImplementedError


# --------------------------------------------------------------- live state


class LiveState:
    """The gateway's replica of `GatewayDesired`, plus the last plan window snapshot.

    Single writer: `apply` (from stdin) replaces routes, leases and cap; the meter
    replaces the window snapshot. Nothing else mutates it.
    """

    def apply(self, desired: GatewayDesired) -> None:
        """Wholesale replace. In-flight requests keep the route they resolved.
        A lease that disappears ends its in-flight streams with an error event."""
        raise NotImplementedError

    def authenticate(self, lease_secret: bytes | None) -> LeaseGrant | None:
        """Constant-time compare of sha256(secret) against live digests."""
        raise NotImplementedError

    @property
    def table(self) -> RouteTable:
        raise NotImplementedError

    def five_hour_utilization(self) -> Percent | None:
        raise NotImplementedError

    @property
    def background_cap(self) -> Percent:
        raise NotImplementedError


# ------------------------------------------------------------------ errors


@dataclass(frozen=True, slots=True)
class GatewayRefusal:
    """Rendered in Anthropic's error JSON so the CLI shows it like any API error.

    Status codes are chosen so the CLI does not retry a refusal that will not
    change on retry: 401 no lease, 400 model not allowed, 403 cap reached.
    """

    status: Literal[400, 401, 403, 404]
    error_type: Literal["authentication_error", "invalid_request_error", "permission_error", "not_found_error"]
    message: str


def resolve_for_lease(table: RouteTable, lease: LeaseGrant, model: ModelId) -> Route | GatewayRefusal:
    """Pure. A model outside the lease's allowed set is refused even if it exists,
    so an agent cannot reach a provider its profile does not name."""
    raise NotImplementedError


def cap_gate(
    route: Route,
    lease: LeaseGrant,
    hints: AgentHints,
    utilization: Percent | None,
    cap: Percent,
) -> GatewayRefusal | None:
    """Pure. The 50% background rule (R6), enforced on every model call.

    # TODO pseudocode
    # only PlanRoute is capped (the cap protects the operator's Claude window)
    # background = lease.placement is BACKGROUND
    #              or hints.request_class in BACKGROUND_REQUEST_CLASSES  (values set by live check L9)
    # if background and utilization is not None and utilization >= cap:
    #     return GatewayRefusal(403, "permission_error",
    #         f"QMX background cap: 5-hour window at {utilization}% (cap {cap}%).")
    # utilization None (no plan response seen yet since start) -> allow; the first
    # response refreshes the snapshot. Stated as best effort for the very first call.
    """
    raise NotImplementedError


# ------------------------------------------------------------------ handler


async def handle_messages(
    state: LiveState,
    request: InboundRequest,
    emit: EventSink,
) -> AsyncIterator[bytes]:
    """The pipeline in the module docstring. Yields response bytes as they arrive.

    Every exit path calls `request.credential.discard()` unless the plan lane
    consumed it, including refusals and exceptions (try/finally).
    """
    raise NotImplementedError


class EventSink:
    """Writes `GatewayEvent`s to stdout as JSON lines. Serializers exist only for the
    event dataclasses, so a `Sealed` cannot be serialized by accident."""

    def __call__(self, event: GatewayEvent) -> None:
        raise NotImplementedError


async def main() -> None:
    """Read the first GatewayDesired from stdin, bind, serve, keep reading stdin.
    Exit when stdin closes (the parent died), so no orphan gateway outlives
    qmx-control."""
    raise NotImplementedError
