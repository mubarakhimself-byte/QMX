"""qmx_control/agent_ops.py (new). The only file in qmx_control that imports qma2.

Two kinds of route, by principal:
- HARNESS_OPERATIONS: appended to `OPERATIONS`, so REST and MCP both get them under the agent
  bearer token (as today). Agents may start turns in threads, list them, and read usage.
- OPERATOR_ROUTES: declared outside OPERATIONS (the `/sign` precedent) AND additionally gated
  by `X-QMX-Operator` → `harness.operator.verify`. These never reach MCP and a bearer-only
  caller gets 403. `/api/apps/{id}/sign` moves under the same gate (one operator door).

Both lists live here, nowhere else: `server.py` does `OPERATIONS + harness_operations()` and
`for route in operator_routes(harness): app.add_api_route(...)`. No hand-synced copy.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from qma2 import BlockSink, Harness
from qma2.config import SettingsLayer
from qma2.types import (
    Account,
    ApprovalAnswer,
    ApprovalId,
    Effort,
    EngineKind,
    Json,
    ModelRef,
    OperatorProof,
    PermissionMode,
    ThreadId,
    TurnId,
    TurnInput,
)

from qmx_control.service import ControlService, SessionBlock, SessionInput

# --------------------------------------------------------------- sink (control.db stays the UI truth)


class ControlBlockSink(BlockSink):
    """Adapts ControlService to qma2.BlockSink. Runs sync SQLite on a worker thread so the
    event loop is not blocked (Gotcha: stream_turn blocked the loop)."""

    def __init__(self, service: ControlService) -> None: ...

    def create_session(self, title: str, parent_id: ThreadId | None) -> ThreadId:
        """service.sessions_create(SessionInput(title, origin="qma2", parent_id))"""
        raise NotImplementedError

    def append(self, thread_id: ThreadId, kind: str, content: Json) -> int:
        """service.sessions_append(thread_id, SessionBlock(type=kind, content=content))["seq"]
        `kind` must be one of the 14; qma2's projector only emits those. A contract test in
        qmx_control asserts `set(qma2.session.BLOCK_KINDS) <= SessionBlock.type args`."""
        raise NotImplementedError

    def blocks(self, thread_id: ThreadId, after: int = 0) -> Sequence[tuple[int, str, Json]]:
        """service.events("sessions", after, thread_id, limit=1000) → (seq, type, content)"""
        raise NotImplementedError


# --------------------------------------------------------------- request bodies (boundary types)


class ThreadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    cwd: str
    engine: EngineKind | None = None
    model: str | None = None
    provider: str | None = None
    profile: str | None = None
    parent_id: str | None = None
    background: bool = False


class TurnStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    client_key: str | None = None
    attachments: list[str] = Field(default_factory=list)


class TurnSteer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    expected_turn: str


class ThreadSwitch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str | None = None
    provider: str | None = None
    effort: Effort | None = None
    mode: PermissionMode | None = None
    confirm: bool = False


class ApprovalAnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str  # Answer enum value
    message: str = ""
    edited_input: dict[str, Any] | None = None
    text: str | None = None


class OperatorLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passphrase: str


# --------------------------------------------------------------- agent-reachable operations


class HarnessOps:
    """Bound methods registered through OPERATIONS. Same calling convention as ControlService
    methods (sync or async def → REST route and MCP tool)."""

    def __init__(self, harness: Harness) -> None: ...

    async def threads_create(self, thread: ThreadCreate) -> Json: ...
    async def threads_list(self, archived: bool = False) -> list[Json]: ...
    async def threads_get(self, thread_id: str) -> Json: ...
    async def turns_start(self, thread_id: str, turn: TurnStart) -> Json:
        """Returns the Turn at once; blocks stream over the existing SSE `sessions` topic."""
        ...
    async def turns_steer(self, thread_id: str, steer: TurnSteer) -> Json: ...
    async def turns_stop(self, thread_id: str) -> Json: ...
    async def turns_get(self, turn_id: str) -> Json: ...
    async def threads_switch_preview(self, thread_id: str, switch: ThreadSwitch) -> Json:
        """Always `confirm=False` on this door; applying a switch is operator-only below."""
        ...
    async def approvals_list(self, thread_id: str = "") -> list[Json]:
        """Read-only. Agents can see what is pending; they cannot answer."""
        ...
    async def usage_summary(self, since: str = "") -> Json: ...
    async def accounts_list(self) -> list[Json]: ...
    async def harness_settings_get(self, layer: SettingsLayer, cwd: str = "") -> Json: ...


def harness_operations() -> tuple[tuple[str, str, str, bool], ...]:
    """Rows in OPERATIONS format: (name, method, path, destructive)."""
    return (
        ("threads_create", "POST", "/api/threads", False),
        ("threads_list", "GET", "/api/threads", False),
        ("threads_get", "GET", "/api/threads/{thread_id}", False),
        ("turns_start", "POST", "/api/threads/{thread_id}/turns", False),
        ("turns_steer", "POST", "/api/threads/{thread_id}/steer", False),
        ("turns_stop", "POST", "/api/threads/{thread_id}/stop", True),
        ("turns_get", "GET", "/api/turns/{turn_id}", False),
        ("threads_switch_preview", "POST", "/api/threads/{thread_id}/switch/preview", False),
        ("approvals_list", "GET", "/api/approvals", False),
        ("usage_summary", "GET", "/api/usage", False),
        ("accounts_list", "GET", "/api/accounts", False),
        ("harness_settings_get", "GET", "/api/harness/settings/{layer}", False),
    )


# --------------------------------------------------------------- operator-only routes


def operator_only(harness: Harness) -> Callable[..., OperatorProof]:
    """FastAPI dependency: `X-QMX-Operator` header → OperatorProof or 403.
    The bearer dependency still applies first (BearerGate wraps the app)."""

    def dependency(x_qmx_operator: str | None = Header(default=None)) -> OperatorProof:
        proof = harness.operator.verify(x_qmx_operator)
        if proof is None:
            raise HTTPException(status_code=403, detail="Operator session required")
        return proof

    return dependency


class OperatorRoutes:
    """Declared with app.add_api_route outside OPERATIONS; each takes `proof` from the
    dependency above, so the handler signature itself demands an OperatorProof."""

    def __init__(self, harness: Harness, service: ControlService) -> None: ...

    async def operator_login(self, body: OperatorLogin) -> Json:
        """POST /api/operator/login → {session_token}. The one route that takes the
        passphrase; bearer-protected like everything else; never logged."""
        ...
    async def operator_set_passphrase(self, body: Json) -> Json:
        """POST /api/operator/passphrase; first set needs no proof, rotation needs one."""
        ...
    async def approvals_answer(self, approval_id: str, body: ApprovalAnswerBody, proof: OperatorProof) -> Json:
        """POST /api/approvals/{approval_id}/answer"""
        ...
    async def threads_switch(self, thread_id: str, body: ThreadSwitch, proof: OperatorProof) -> Json:
        """POST /api/threads/{thread_id}/switch (confirm=True applies)"""
        ...
    async def threads_compact(self, thread_id: str, body: Json, proof: OperatorProof) -> Json: ...
    async def threads_export(self, thread_id: str, body: Json, proof: OperatorProof) -> Json: ...
    async def threads_archive(self, thread_id: str, proof: OperatorProof) -> Json: ...
    async def accounts_add(self, body: Json, proof: OperatorProof) -> Json: ...
    async def secrets_put(self, body: Json, proof: OperatorProof) -> Json:
        """POST /api/secrets {ref, value}: console `add-key`. Value never echoed or stored
        outside SecretStore."""
        ...
    async def harness_settings_put(self, layer: SettingsLayer, body: Json, proof: OperatorProof, cwd: str = "") -> Json: ...
    async def apps_sign(self, app_id: str, body: Json, proof: OperatorProof) -> Json:
        """The existing /sign door, now behind the operator proof as well."""
        ...


def operator_routes(routes: OperatorRoutes) -> tuple[tuple[str, str, Callable[..., Any]], ...]:
    return (
        ("POST", "/api/operator/login", routes.operator_login),
        ("POST", "/api/operator/passphrase", routes.operator_set_passphrase),
        ("POST", "/api/approvals/{approval_id}/answer", routes.approvals_answer),
        ("POST", "/api/threads/{thread_id}/switch", routes.threads_switch),
        ("POST", "/api/threads/{thread_id}/compact", routes.threads_compact),
        ("POST", "/api/threads/{thread_id}/export", routes.threads_export),
        ("POST", "/api/threads/{thread_id}/archive", routes.threads_archive),
        ("POST", "/api/accounts", routes.accounts_add),
        ("POST", "/api/secrets", routes.secrets_put),
        ("PUT", "/api/harness/settings/{layer}", routes.harness_settings_put),
        ("POST", "/api/apps/{app_id}/sign", routes.apps_sign),
    )


def build(service: ControlService, home: Path) -> tuple[Harness, HarnessOps, OperatorRoutes]:
    """Called once from create_app. Harness.start() runs in the app lifespan; close() on exit."""
    raise NotImplementedError
