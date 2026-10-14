"""Approvals and the operator principal.

Two things live here because they are one decision: who may answer, and how an answer reaches
the waiting engine.

Operator principal (design.md tension 2): the operator has a passphrase. Its argon2id
verifier is in agents.db; the passphrase itself is in his head. `login(passphrase)` yields an
in-memory session token (random, never written anywhere by QMX) that the console or UI holds
and presents on operator-only routes as `X-QMX-Operator`. The agent bearer token stays as
today for everything else. Engine child envs never contain the operator token. `verify`
returns an `OperatorProof`, the only way to construct one.

Answer path: `request()` writes a PENDING row and parks a Future keyed by approval id.
`answer()` is the single writer of the decision: CAS PENDING → ANSWERED in the store, then
resolves the Future (Claude) or returns the stored RunState (OpenAI) for the actor to resume.
Idempotent: same answer twice → same row; different answer → AlreadyAnswered.

Restart: Futures die with the process. `expire_orphans` marks their rows EXPIRED and the
actor shows "re-run from here". OpenAI rows keep `engine_state`, so those can resume.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from qma2.store import Store
from qma2.types import (
    AgentPath,
    Approval,
    ApprovalAnswer,
    ApprovalId,
    ApprovalRequest,
    OperatorProof,
    ThreadId,
    TurnId,
)


class AlreadyAnswered(Exception): ...


class NotPaired(Exception):
    """No verifier exists yet: the console must run `set-passphrase` first."""


class OperatorAuth:
    def __init__(self, store: Store, *, session_ttl_s: int = 12 * 3600) -> None:
        raise NotImplementedError

    def set_passphrase(self, new: str, current: str | None) -> None:
        """First set needs no `current`. Rotation needs the current passphrase. Writes the
        verifier; never the passphrase."""
        raise NotImplementedError

    def login(self, passphrase: str) -> str:
        """Verify against the stored verifier; mint a session token held only in memory
        (and by the caller). Also unseals the SEALED secret tier."""
        raise NotImplementedError

    def verify(self, session_token: str | None) -> OperatorProof | None:
        """Constant-time compare against live sessions. None → the route answers 403."""
        raise NotImplementedError

    def logout_all(self) -> None: ...


class ApprovalBroker:
    def __init__(self, store: Store, operator: OperatorAuth) -> None:
        raise NotImplementedError

    async def request(
        self,
        thread_id: ThreadId,
        turn_id: TurnId,
        agent_path: AgentPath,
        request: ApprovalRequest,
        *,
        engine_state: bytes | None = None,
        timeout_s: float | None = None,
    ) -> ApprovalAnswer:
        """Durable row + parked Future. Returns when the operator answers. The caller (gate or
        AskUser tool) is already inside the engine's callback, so awaiting here is what pauses
        the model. `timeout_s=None` means "wait for days" (long-lived sessions)."""
        raise NotImplementedError

    async def answer(self, approval_id: ApprovalId, answer: ApprovalAnswer, proof: OperatorProof) -> Approval:
        raise NotImplementedError

    async def expire_orphans(self, live_turns: Sequence[TurnId], at: datetime) -> Sequence[Approval]:
        raise NotImplementedError

    def pending(self, thread_id: ThreadId | None = None) -> Sequence[Approval]:
        raise NotImplementedError

    def engine_state(self, approval_id: ApprovalId) -> bytes | None:
        raise NotImplementedError
